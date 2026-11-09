"""Crash-tolerant experiment runner.

Every run executes in its own child process with a wall-clock limit and a memory
limit, and its result is appended to a CSV and forced to disk as soon as it
finishes. Restarting the script skips every run already stored, so a crash only
loses the run that was in progress.
"""

import csv
import gc
import multiprocessing
import os
import re
import resource
import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass

from src.engine.genetic_engine import GAConfig, run_genetic_algorithm

KEY_COLUMNS = ["experiment", "problem", "instance", "size", "config_id", "method", "seed"]
RESULT_COLUMNS = [
  "status",
  "value",
  "time_seconds",
  "peak_memory_kb",
  "evaluations",
  "generations",
  "solution",
  "message",
]
CSV_COLUMNS = KEY_COLUMNS + RESULT_COLUMNS

STATUS_OK = "ok"
STATUS_TIMEOUT = "timeout"
STATUS_MEMORY = "memory"
STATUS_RECURSION = "recursion_limit"
STATUS_ERROR = "error"
STATUS_CRASHED = "crashed"
STATUS_SKIPPED = "skipped"
LIMIT_STATUSES = {STATUS_TIMEOUT, STATUS_MEMORY, STATUS_RECURSION, STATUS_CRASHED}

METHOD_GA = "ga"
METHOD_EXHAUSTIVE = "exhaustive"
METHOD_DP = "dp"

DEFAULT_TIME_LIMIT_SECONDS = 600
DEFAULT_MEMORY_LIMIT_MB = 4096
DEFAULT_RECURSION_LIMIT = 1_000_000
DEFAULT_HISTORY_STEP = 100
TIMEOUT_GRACE_SECONDS = 5

_FORK = multiprocessing.get_context("fork")


# CSV storage


def make_key(row: dict) -> tuple[str, ...]:
  """Identity of a run: the key columns as text (the CSV gives everything back as text)."""
  return tuple(str(row[column]) for column in KEY_COLUMNS)


def load_rows(csv_path: str) -> list[dict]:
  """Return every complete row of the CSV; a last line cut by a crash is ignored."""
  if not os.path.exists(csv_path):
    return []
  with open(csv_path, newline="") as file:
    lines = file.readlines()
  if lines and not lines[-1].endswith("\n"):
    lines.pop()
  return list(csv.DictReader(lines))


def load_completed_keys(csv_path: str) -> set[tuple[str, ...]]:
  """Return the keys of every run already stored in the CSV."""
  return {make_key(row) for row in load_rows(csv_path)}


def _fsync_write(path: str, write: Callable, mode: str) -> None:
  directory = os.path.dirname(path)
  if directory:
    os.makedirs(directory, exist_ok=True)
  with open(path, mode, newline="") as file:
    write(file)
    file.flush()
    os.fsync(file.fileno())


def _drop_partial_last_line(csv_path: str) -> None:
  """Truncate a last line left without its newline by a crash."""
  size = os.path.getsize(csv_path)
  if size == 0:
    return
  with open(csv_path, "rb+") as file:
    file.seek(-1, os.SEEK_END)
    if file.read(1) == b"\n":
      return
    start = max(0, size - 65536)
    file.seek(start)
    last_newline = file.read().rfind(b"\n")
    file.truncate(0 if last_newline < 0 else start + last_newline + 1)
    file.flush()
    os.fsync(file.fileno())


def _single_line(value):
  if isinstance(value, str):
    return value.replace("\r", " ").replace("\n", " ")
  return value


def append_row(csv_path: str, row: dict) -> None:
  """Append one row and force it to disk; write the header if the file is new.

  A last line cut by an earlier crash is removed first, so it never ends up
  in the results.
  """
  if os.path.exists(csv_path):
    _drop_partial_last_line(csv_path)
  has_content = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
  clean_row = {column: _single_line(value) for column, value in row.items()}

  def write(file):
    writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
    if not has_content:
      writer.writeheader()
    writer.writerow(clean_row)

  _fsync_write(csv_path, write, "a")


# Convergence history (one small CSV per GA run, used by Figure 1)


def history_file(history_dir: str, row: dict) -> str:
  """Path of the convergence file of one run."""
  name = "__".join(re.sub(r"[^A-Za-z0-9._-]", "-", part) for part in make_key(row))
  return os.path.join(history_dir, f"{name}.csv")


def downsample_history(history: list[tuple[int, float]], step: int) -> list[tuple[int, float]]:
  """Keep every ``step``-th evaluation plus the first and the last one."""
  if not history:
    return []
  kept = [point for point in history if point[0] == 1 or point[0] % step == 0]
  if kept[-1] != history[-1]:
    kept.append(history[-1])
  return kept


def write_history(path: str, history: list[tuple[int, float]]) -> None:
  """Write a convergence file atomically (a crash never leaves half a file)."""
  temporary = f"{path}.tmp"

  def write(file):
    writer = csv.writer(file)
    writer.writerow(["evaluation", "best"])
    writer.writerows(history)

  _fsync_write(temporary, write, "w")
  os.replace(temporary, path)


def load_history(path: str) -> list[tuple[int, float]]:
  """Read a convergence file back as (evaluation, best) pairs."""
  with open(path, newline="") as file:
    return [(int(row["evaluation"]), float(row["best"])) for row in csv.DictReader(file)]


# Isolated execution with time and memory limits


def _virtual_memory_bytes() -> int:
  try:
    with open("/proc/self/statm") as file:
      return int(file.read().split()[0]) * os.sysconf("SC_PAGE_SIZE")
  except (OSError, ValueError):
    return 0


def _child_main(target, connection, memory_limit_mb, recursion_limit):
  try:
    limit = _virtual_memory_bytes() + memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    _, hard_stack = resource.getrlimit(resource.RLIMIT_STACK)
    resource.setrlimit(resource.RLIMIT_STACK, (hard_stack, hard_stack))
    sys.setrecursionlimit(recursion_limit)

    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start = time.perf_counter()
    try:
      result = target()
      status, message = STATUS_OK, ""
    except MemoryError:
      result, status, message = {}, STATUS_MEMORY, "memory limit reached"
    except RecursionError:
      result, status, message = {}, STATUS_RECURSION, "recursion limit reached"
    except Exception as error:
      result, status = {}, STATUS_ERROR
      message = f"{type(error).__name__}: {error}"
      traceback.print_exc()
    elapsed = time.perf_counter() - start
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    result = dict(result or {})
    result.update(
      status=status,
      message=message,
      time_seconds=elapsed,
      peak_memory_kb=max(0, rss_after - rss_before),
    )
    connection.send(result)
  finally:
    connection.close()


def run_isolated(
  target: Callable[[], dict],
  time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS,
  memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
  recursion_limit: int = DEFAULT_RECURSION_LIMIT,
) -> dict:
  """Run ``target()`` in a child process and return its result plus measurements.

  ``target`` returns a dict (for example ``{"value": 42}``). The returned dict
  always has ``status``, ``message``, ``time_seconds`` and ``peak_memory_kb``.
  ``peak_memory_kb`` is how much the peak resident memory grew while ``target``
  ran. The child is killed if it exceeds ``time_limit_seconds``; allocating
  more than ``memory_limit_mb`` raises MemoryError inside the child.
  """
  receiver, sender = _FORK.Pipe(duplex=False)
  process = _FORK.Process(
    target=_child_main,
    args=(target, sender, memory_limit_mb, recursion_limit),
    daemon=True,
  )
  process.start()
  sender.close()
  try:
    if receiver.poll(time_limit_seconds + TIMEOUT_GRACE_SECONDS):
      try:
        result = receiver.recv()
      except EOFError:
        result = None
    else:
      process.kill()
      result = {
        "status": STATUS_TIMEOUT,
        "message": f"no result after {time_limit_seconds} s",
        "time_seconds": time_limit_seconds,
        "peak_memory_kb": "",
      }
  finally:
    receiver.close()
    process.join()

  if result is None:
    result = {
      "status": STATUS_CRASHED,
      "message": f"child process exited with code {process.exitcode}",
      "time_seconds": "",
      "peak_memory_kb": "",
    }
  elif result["status"] == STATUS_OK and result["time_seconds"] > time_limit_seconds:
    result["status"] = STATUS_TIMEOUT
    result["message"] = f"finished after the {time_limit_seconds} s limit"
  return result


# Run descriptions


@dataclass
class RunTask:
  """One run to execute: its identity (key columns) and what to execute."""

  experiment: str
  problem: str
  instance: str
  size: int
  config_id: str
  method: str
  seed: int
  target: Callable[[], dict]
  stop_after_limit: bool = False

  def key_row(self) -> dict:
    return {column: getattr(self, column) for column in KEY_COLUMNS}


def ga_task(
  experiment: str,
  problem_name: str,
  instance: str,
  size: int,
  config_id: str,
  problem,
  config: GAConfig,
) -> RunTask:
  """Genetic algorithm run of ``problem`` with ``config`` (the seed comes from the config)."""

  def target():
    result = run_genetic_algorithm(
      problem.chromosome_spec(), problem.fitness, problem.direction(), config
    )
    return {
      "value": result.best_fitness,
      "evaluations": result.evaluations_used,
      "generations": result.generations,
      "solution": problem.decode(result.best_chromosome),
      "history": result.history,
    }

  return RunTask(
    experiment, problem_name, instance, size, config_id, METHOD_GA, config.seed, target
  )


def exact_task(
  experiment: str,
  problem_name: str,
  instance: str,
  size: int,
  problem,
  method: str,
  seed: int = 0,
) -> RunTask:
  """Exhaustive recursion or top-down DP run of ``problem``."""
  if method not in (METHOD_EXHAUSTIVE, METHOD_DP):
    raise ValueError(f"method must be '{METHOD_EXHAUSTIVE}' or '{METHOD_DP}'")
  solve = problem.solve_exhaustive if method == METHOD_EXHAUSTIVE else problem.solve_dp

  def target():
    return {"value": solve()}

  return RunTask(experiment, problem_name, instance, size, "-", method, seed, target, True)


# Main loop


def _limit_sizes(rows: list[dict]) -> dict[tuple[str, str, str], int]:
  """Smallest size at which each (experiment, problem, method) hit a limit."""
  limits = {}
  for row in rows:
    if row["status"] in LIMIT_STATUSES:
      group = (str(row["experiment"]), str(row["problem"]), str(row["method"]))
      size = int(row["size"])
      limits[group] = min(size, limits.get(group, size))
  return limits


def run_tasks(
  tasks: list[RunTask],
  results_csv: str,
  history_dir: str | None = None,
  time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS,
  memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
  recursion_limit: int = DEFAULT_RECURSION_LIMIT,
  cooldown_seconds: float = 0.0,
  history_step: int = DEFAULT_HISTORY_STEP,
  log: Callable[[str], None] = print,
) -> dict[str, int]:
  """Execute every task not yet stored in ``results_csv`` and return status counts.

  Runs already in the CSV are skipped, so the same call resumes an interrupted
  experiment. ``cooldown_seconds`` pauses between executed runs so the CPU can
  cool down before the next time measurement.
  """
  keys = [make_key(task.key_row()) for task in tasks]
  if len(set(keys)) != len(keys):
    raise ValueError("two tasks have the same key columns")

  stored = load_rows(results_csv)
  completed = {make_key(row) for row in stored}
  limits = _limit_sizes(stored)
  counts = {"already_done": 0}
  executed_any = False

  for number, (task, key) in enumerate(zip(tasks, keys, strict=True), start=1):
    if key in completed:
      counts["already_done"] += 1
      continue

    row = task.key_row()
    group = (str(task.experiment), str(task.problem), str(task.method))
    if task.stop_after_limit and group in limits and task.size >= limits[group]:
      row.update(status=STATUS_SKIPPED, message=f"limit already reached at size {limits[group]}")
      append_row(results_csv, row)
      counts[STATUS_SKIPPED] = counts.get(STATUS_SKIPPED, 0) + 1
      log(f"[{number}/{len(tasks)}] {' '.join(key)} -> {STATUS_SKIPPED}")
      continue

    if executed_any and cooldown_seconds > 0:
      time.sleep(cooldown_seconds)
    executed_any = True

    result = run_isolated(task.target, time_limit_seconds, memory_limit_mb, recursion_limit)
    history = result.pop("history", None)
    if history and history_dir:
      write_history(history_file(history_dir, row), downsample_history(history, history_step))
    row.update({column: result.get(column, "") for column in RESULT_COLUMNS})
    append_row(results_csv, row)
    del result, history
    gc.collect()

    status = row["status"]
    counts[status] = counts.get(status, 0) + 1
    if task.stop_after_limit and status in LIMIT_STATUSES:
      limits[group] = min(task.size, limits.get(group, task.size))
    elapsed = row["time_seconds"]
    shown = f"{elapsed:.3f} s" if isinstance(elapsed, float) else "-"
    log(f"[{number}/{len(tasks)}] {' '.join(key)} -> {status} ({shown})")

  return counts
