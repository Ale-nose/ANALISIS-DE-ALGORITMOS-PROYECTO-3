"""Automated experiment suite for Rod Cutting (real-valued chromosome)."""

import argparse
import csv
import glob
import os
import random
import statistics
from functools import partial
from itertools import product

from src.engine.chromosome import Direction, is_better
from src.engine.crossover import (
  arithmetic_crossover,
  one_point_crossover,
  two_point_crossover,
  uniform_crossover,
)
from src.engine.genetic_engine import GAConfig
from src.engine.mutation import gaussian_mutation
from src.engine.selection import (
  ranking_selection,
  roulette_selection,
  tournament_selection,
)
from src.experiments.runner import (
  CSV_COLUMNS,
  DEFAULT_MEMORY_LIMIT_MB,
  DEFAULT_TIME_LIMIT_SECONDS,
  METHOD_DP,
  METHOD_EXHAUSTIVE,
  STATUS_OK,
  exact_task,
  ga_task,
  load_rows,
  make_key,
  run_tasks,
)
from src.problems.rod_cutting import RodCutting, generate_prices

PROBLEM = "rod_cutting"
SEEDS = [42, 101, 2026]
EVALUATION_BUDGET = 20_000
EXP1_INSTANCE_SEED = 777
EXP1_SIZE = 30
EXP2_INSTANCE_BASE_SEED = 9000
# Exhaustive is expected to stop around L = 31-33 and DP around L = 90 000-128 000.
# Larger sizes of a method that already hit the limit are recorded as "skipped".
EXP2_SIZES = [
  10,
  15,
  20,
  24,
  26,
  28,
  30,
  31,
  32,
  33,
  34,
  100,
  1_000,
  4_000,
  16_000,
  32_000,
  64_000,
  90_000,
  128_000,
  181_000,
]
DEFAULT_GA_TIME_LIMIT_SECONDS = 3600

RESULTS_DIR = "results"

SELECTION_OPTIONS = {
  "roulette": roulette_selection,
  "ranking": partial(ranking_selection, k=5),
  "tournament": partial(tournament_selection, k=3),
}

CROSSOVER_OPTIONS = {
  "arithmetic": arithmetic_crossover,
  "one_point": one_point_crossover,
  "two_point": two_point_crossover,
  "uniform": uniform_crossover,
}

MUTATION_OPTIONS = {
  "gaussian_s0.05": partial(gaussian_mutation, sigma=0.05),
  "gaussian_s0.1": partial(gaussian_mutation, sigma=0.1),
  "gaussian_s0.2": partial(gaussian_mutation, sigma=0.2),
}

BASE_PARAMS = {
  "population_size": 100,
  "selection": "tournament",
  "crossover": "arithmetic",
  "crossover_rate": 0.8,
  "mutation": "gaussian_s0.1",
  # Per-gene probability, as with binary chromosomes.
  "mutation_rate": 0.05,
  "elitism": 2,
}

OFAT_VALUES = {
  "population_size": [20, 50, 100, 200, 400],
  "selection": ["roulette", "ranking", "tournament"],
  "crossover": ["arithmetic", "one_point", "two_point", "uniform"],
  "mutation": ["gaussian_s0.05", "gaussian_s0.1", "gaussian_s0.2"],
  "crossover_rate": [0.6, 0.8, 0.95],
  "mutation_rate": [0.01, 0.05, 0.1, 0.2, 0.4],
  "elitism": [0, 2, 5],
}

HEATMAP_POPULATIONS = [20, 50, 100, 200, 400]
HEATMAP_MUTATION_RATES = [0.05, 0.1, 0.2, 0.4, 0.8]


def get_csv_path(problem_name: str, part: str | None = None) -> str:
  suffix = f"_{part}" if part else ""
  return os.path.join(RESULTS_DIR, f"{problem_name}_results{suffix}.csv")


def get_history_dir(problem_name: str) -> str:
  return os.path.join(RESULTS_DIR, "history", problem_name)


def build_problem(size: int, instance_seed: int) -> RodCutting:
  return RodCutting(generate_prices(size, random.Random(instance_seed)))


def make_ga_config(params: dict, seed: int) -> GAConfig:
  return GAConfig(
    population_size=int(params["population_size"]),
    selection=SELECTION_OPTIONS[params["selection"]],
    crossover=CROSSOVER_OPTIONS[params["crossover"]],
    crossover_rate=float(params["crossover_rate"]),
    mutation=MUTATION_OPTIONS[params["mutation"]],
    mutation_rate=float(params["mutation_rate"]),
    elitism=int(params["elitism"]),
    max_evaluations=EVALUATION_BUDGET,
    max_generations_without_improvement=None,
    seed=seed,
  )


def combo_config_id(params: dict) -> str:
  return (
    f"combo__p{params['population_size']}"
    f"__{params['selection']}"
    f"__{params['crossover']}"
    f"__{params['mutation']}"
    f"__cr{params['crossover_rate']}"
    f"__mr{params['mutation_rate']}"
    f"__el{params['elitism']}"
  )


def exp1_instance():
  problem = build_problem(EXP1_SIZE, EXP1_INSTANCE_SEED)
  instance_id = f"fixed_n{EXP1_SIZE}_s{EXP1_INSTANCE_SEED}"
  return problem, instance_id


def build_exp1_ofat_tasks(problem_name: str):
  problem, instance_id = exp1_instance()
  tasks = []

  for param_name, values in OFAT_VALUES.items():
    for val in values:
      params = dict(BASE_PARAMS)
      params[param_name] = val
      config_id = f"ofat__{param_name}__{val}"
      for seed in SEEDS:
        cfg = make_ga_config(params, seed)
        tasks.append(
          ga_task("exp1_ofat", problem_name, instance_id, EXP1_SIZE, config_id, problem, cfg)
        )

  for pop in HEATMAP_POPULATIONS:
    for m_rate in HEATMAP_MUTATION_RATES:
      params = dict(BASE_PARAMS)
      params["population_size"] = pop
      params["mutation_rate"] = m_rate
      config_id = f"heatmap__pop_{pop}__mut_{m_rate}"
      for seed in SEEDS:
        cfg = make_ga_config(params, seed)
        tasks.append(
          ga_task("exp1_heatmap", problem_name, instance_id, EXP1_SIZE, config_id, problem, cfg)
        )

  return tasks


def build_exp1_cxmut_tasks(problem_name: str):
  """Every crossover x sigma pair with the base configuration (Figure 2)."""
  problem, instance_id = exp1_instance()
  tasks = []

  for crossover_name, mutation_name in product(CROSSOVER_OPTIONS, MUTATION_OPTIONS):
    params = dict(BASE_PARAMS)
    params["crossover"] = crossover_name
    params["mutation"] = mutation_name
    config_id = f"cxmut__{crossover_name}__{mutation_name}"
    for seed in SEEDS:
      cfg = make_ga_config(params, seed)
      tasks.append(
        ga_task("exp1_cxmut", problem_name, instance_id, EXP1_SIZE, config_id, problem, cfg)
      )
  return tasks


def select_top2_per_parameter(problem_name: str, direction: Direction) -> dict[str, list]:
  rows = [
    r
    for r in load_rows(get_csv_path(problem_name))
    if r["experiment"] == "exp1_ofat" and r["problem"] == problem_name and r["status"] == STATUS_OK
  ]
  top2 = {}
  for param_name, candidates in OFAT_VALUES.items():
    scored = []
    for val in candidates:
      cid = f"ofat__{param_name}__{val}"
      vals = [float(r["value"]) for r in rows if r["config_id"] == cid]
      if vals:
        scored.append((statistics.mean(vals), val))
    scored.sort(key=lambda pair: pair[0], reverse=direction is Direction.MAXIMIZE)
    top2[param_name] = [val for _, val in scored[:2]]
    if not top2[param_name]:
      # Stage exp1_ofat has not run yet for this parameter: keep the base value.
      top2[param_name] = [BASE_PARAMS[param_name]]
  return top2


def build_exp1_combination_tasks(problem_name: str):
  problem, instance_id = exp1_instance()
  top2 = select_top2_per_parameter(problem_name, problem.direction())
  print(f"Top-2 values per parameter: {top2}")

  param_names = list(OFAT_VALUES.keys())
  value_lists = [top2[k] for k in param_names]
  tasks = []

  for combo in product(*value_lists):
    params = dict(BASE_PARAMS)
    for k, v in zip(param_names, combo, strict=True):
      params[k] = v
    config_id = combo_config_id(params)
    for seed in SEEDS:
      cfg = make_ga_config(params, seed)
      tasks.append(
        ga_task("exp1_combo", problem_name, instance_id, EXP1_SIZE, config_id, problem, cfg)
      )
  return tasks


def find_best_combo_params(problem_name: str, direction: Direction) -> tuple[str, dict]:
  rows = [
    r
    for r in load_rows(get_csv_path(problem_name))
    if r["experiment"] == "exp1_combo" and r["problem"] == problem_name and r["status"] == STATUS_OK
  ]
  if not rows:
    return "base_fallback", dict(BASE_PARAMS)

  by_cid = {}
  for r in rows:
    by_cid.setdefault(r["config_id"], []).append(float(r["value"]))

  best_cid = None
  best_mean = None
  for cid, vals in by_cid.items():
    mean_val = statistics.mean(vals)
    if best_mean is None or is_better(mean_val, best_mean, direction):
      best_mean = mean_val
      best_cid = cid

  parts = best_cid.split("__")
  params = {
    "population_size": int(parts[1][1:]),
    "selection": parts[2],
    "crossover": parts[3],
    "mutation": parts[4],
    "crossover_rate": float(parts[5][2:]),
    "mutation_rate": float(parts[6][2:]),
    "elitism": int(parts[7][2:]),
  }
  return best_cid, params


def exp2_instances():
  for size in EXP2_SIZES:
    inst_seed = EXP2_INSTANCE_BASE_SEED + size
    yield size, f"scale_n{size}_s{inst_seed}", build_problem(size, inst_seed)


def build_exp2_exact_tasks(problem_name: str, methods=(METHOD_EXHAUSTIVE, METHOD_DP)):
  tasks = []
  for size, instance_id, problem in exp2_instances():
    for method in methods:
      tasks.append(exact_task("exp2", problem_name, instance_id, size, problem, method))
  return tasks


def build_exp2_ga_tasks(problem_name: str, seeds=tuple(SEEDS)):
  best_cid, best_params = find_best_combo_params(problem_name, Direction.MAXIMIZE)
  print(f"Best configuration: {best_cid}")
  tasks = []
  for size, instance_id, problem in exp2_instances():
    for seed in seeds:
      cfg = make_ga_config(best_params, seed)
      tasks.append(ga_task("exp2", problem_name, instance_id, size, best_cid, problem, cfg))
  return tasks


def merge_parts(problem_name: str) -> None:
  """Join results/<problem>_results_*.csv into results/<problem>_results.csv."""
  main_path = get_csv_path(problem_name)
  part_paths = sorted(glob.glob(get_csv_path(problem_name, "*")))
  if not part_paths:
    print("No part files found; nothing to merge.")
    return

  merged = {}
  for path in [main_path, *part_paths]:
    for row in load_rows(path):
      key = make_key(row)
      if key in merged and merged[key] != row:
        if merged[key]["value"] != row["value"] or merged[key]["status"] != row["status"]:
          raise SystemExit(f"Conflicting results for {key} in {path}")
      merged.setdefault(key, row)
    print(f"  {path}: read")

  temporary = f"{main_path}.tmp"
  with open(temporary, "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(merged.values())
    file.flush()
    os.fsync(file.fileno())
  os.replace(temporary, main_path)
  print(f"Merged {len(merged)} runs into {main_path}")


def main():
  parser = argparse.ArgumentParser(description="Run the Rod Cutting GA experiments.")
  parser.add_argument(
    "--stage",
    choices=["exp1_ofat", "exp1_cxmut", "exp1_combo", "exp2_exact", "exp2_ga", "all", "merge"],
    default="all",
    help="Experiment stage to run",
  )
  parser.add_argument("--cooldown", type=float, default=1.0, help="Cooldown seconds between runs")
  parser.add_argument(
    "--memory-limit",
    type=int,
    default=DEFAULT_MEMORY_LIMIT_MB,
    help=f"Memory limit in MB per run (default: {DEFAULT_MEMORY_LIMIT_MB})",
  )
  parser.add_argument(
    "--time-limit",
    type=float,
    default=DEFAULT_TIME_LIMIT_SECONDS,
    help=f"Time limit in seconds per exact run (default: {DEFAULT_TIME_LIMIT_SECONDS})",
  )
  parser.add_argument(
    "--ga-time-limit",
    type=float,
    default=DEFAULT_GA_TIME_LIMIT_SECONDS,
    help=f"Time limit in seconds per GA run (default: {DEFAULT_GA_TIME_LIMIT_SECONDS})",
  )
  parser.add_argument(
    "--part",
    help="Experiment 2 only: write to results/rod_cutting_results_<part>.csv (one per machine)",
  )
  parser.add_argument(
    "--method",
    choices=[METHOD_EXHAUSTIVE, METHOD_DP],
    help="exp2_exact only: run a single exact method (default: both)",
  )
  parser.add_argument(
    "--seed",
    type=int,
    choices=SEEDS,
    help="exp2_ga only: run a single GA seed (default: all seeds)",
  )
  args = parser.parse_args()

  if args.method and args.stage != "exp2_exact":
    parser.error("--method can only be used with --stage exp2_exact")
  if args.seed is not None and args.stage != "exp2_ga":
    parser.error("--seed can only be used with --stage exp2_ga")
  if args.part and args.stage not in ("exp2_exact", "exp2_ga"):
    parser.error("--part can only be used with --stage exp2_exact or exp2_ga")

  if args.stage == "merge":
    merge_parts(PROBLEM)
    return

  csv_path = get_csv_path(PROBLEM, args.part)
  history_dir = get_history_dir(PROBLEM)
  methods = (args.method,) if args.method else (METHOD_EXHAUSTIVE, METHOD_DP)
  seeds = (args.seed,) if args.seed is not None else tuple(SEEDS)
  stages = [
    ("exp1_ofat", "Exp 1 (OFAT + Heatmap)", build_exp1_ofat_tasks, args.ga_time_limit),
    ("exp1_cxmut", "Exp 1 (Crossover x Sigma pairs)", build_exp1_cxmut_tasks, args.ga_time_limit),
    ("exp1_combo", "Exp 1 (Top-2 Combinations)", build_exp1_combination_tasks, args.ga_time_limit),
    (
      "exp2_exact",
      "Exp 2 (Exhaustive and DP)",
      partial(build_exp2_exact_tasks, methods=methods),
      args.time_limit,
    ),
    (
      "exp2_ga",
      "Exp 2 (GA with the best configuration)",
      partial(build_exp2_ga_tasks, seeds=seeds),
      args.ga_time_limit,
    ),
  ]

  for stage_name, title, build, time_limit in stages:
    if args.stage not in (stage_name, "all"):
      continue
    print(f"\n=== Running {title} for {PROBLEM} -> {csv_path} ===")
    run_tasks(
      build(PROBLEM),
      csv_path,
      history_dir,
      time_limit_seconds=time_limit,
      memory_limit_mb=args.memory_limit,
      cooldown_seconds=args.cooldown,
    )


if __name__ == "__main__":
  main()