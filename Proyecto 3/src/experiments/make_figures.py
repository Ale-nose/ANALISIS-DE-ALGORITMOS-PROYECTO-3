"""Figures and tables for the genetic algorithm experiments.

Reads the files written by runner.py:
    results/<problem>_results.csv
    results/history/<problem>/*.csv
and writes, for every problem found, into results/figures/:
    fig1_convergence_<problem>.png   Figure 1: convergence by selection method
    fig2_operators_<problem>.png     Figure 2: final result by crossover (and mutation)
    fig3_heatmap_<problem>.png       Figure 3: population size x mutation rate
    fig4_exact_vs_ga_<problem>.png   Figure 4: quality and time, genetic vs exhaustive vs DP
    fig5_memory_<problem>.png        Peak memory of each method
    tables_<problem>.md              Markdown tables for the report

Run it from the project folder (the one that contains src/ and results/):
    python3 -m src.experiments.make_figures
    python3 -m src.experiments.make_figures --problem tsp
    python3 -m src.experiments.make_figures --memory-limit 3072

It works for every problem, because it only depends on the CSV format of
runner.py. Requires matplotlib and numpy. The standard deviation is the sample
standard deviation of the runs (3 seeds per configuration).
"""

import argparse
import glob
import os
import statistics
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")  # no window needed: figures are only written to files
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullLocator, ScalarFormatter

from src.experiments.runner import (
  DEFAULT_TIME_LIMIT_SECONDS,
  LIMIT_STATUSES,
  METHOD_DP,
  METHOD_EXHAUSTIVE,
  METHOD_GA,
  STATUS_ERROR,
  STATUS_OK,
  history_file,
  load_history,
  load_rows,
)

RESULTS_DIR = "results"

# Problems whose goal is to maximize the fitness; every other problem is minimized
# This decides which cell is "best" in the heat map and how the tables sort results
MAXIMIZE_KEYWORDS = ("knapsack", "rod")

# Problems without a random instance: a size always means the same problem, so a
# size used in Experiment 1 must not appear in Experiment 2 (different instances)
INSTANCE_FREE_PROBLEMS = {"nqueens"}

# Problems whose Experiment 2 values grow by orders of magnitude with the size (the
# total price grows with the rod length), so Figure 4 draws quality on a log axis
LOG_QUALITY_PROBLEMS = {"rod_cutting"}

# A size axis spanning more than this ratio between its largest and smallest
# size is drawn in logarithmic scale
LOG_AXIS_RATIO = 8

# Figure 1 uses a logarithmic evaluations axis when the curves finish most of their
# improvement early: EARLY_SHARE of the total drop within EARLY_FRACTION of the budget.
EARLY_FRACTION = 0.05
EARLY_SHARE = 0.9
# Round values used as x-axis ticks on the logarithmic size axis.
SIZE_TICKS = [
  1, 2, 3, 5, 10, 20, 30, 50, 100, 200, 300, 500, 1000, 2000, 3000, 5000,
  10000, 20000, 30000, 50000, 100000, 200000,
]

# Display texts shown in the figures and tables. The keys are the
# problem names used in the CSV files
TITLES = {
  "knapsack": "0/1 Knapsack",
  "partition": "Partition",
  "rod_cutting": "Rod cutting",
  "tsp": "TSP",
  "nqueens": "N-Queens",
}
VALUE_LABELS = {
  "knapsack": "Value of the best knapsack",
  "partition": "Difference between subsets",
  "rod_cutting": "Total price",
  "tsp": "Length of the best route",
  "nqueens": "Conflicts between queens",
}
SIZE_LABELS = {
  "knapsack": "Items",
  "partition": "Numbers",
  "rod_cutting": "Rod length",
  "tsp": "Cities",
  "nqueens": "Board size",
}
# Maps from the names stored in the CSV (config_id) to the names shown in the plots
# The order of each dictionary is the order used for colours, bars and legends
SELECTION_NAMES = {"roulette": "Roulette", "ranking": "Ranking", "tournament": "Tournament"}
CROSSOVER_NAMES = {
  "one_point": "1-point",
  "two_point": "2-point",
  "uniform": "Uniform",
  "arithmetic": "Arithmetic",
  "ox": "OX",
  "pmx": "PMX",
}
MUTATION_NAMES = {
  "bit_flip": "Bit flip",
  "gaussian": "Gaussian",
  "gaussian_s0.05": "σ=0.05",
  "gaussian_s0.1": "σ=0.1",
  "gaussian_s0.2": "σ=0.2",
  "swap": "Swap",
  "inversion": "Inversion",
}
# Names of the parameters varied in the one-parameter-at-a-time experiment
PARAMETER_NAMES = {
  "population_size": "Population",
  "selection": "Selection",
  "crossover": "Crossover",
  "mutation": "Mutation",
  "crossover_rate": "Crossover rate",
  "mutation_rate": "Mutation rate",
  "elitism": "Elitism",
}
# Which dictionary translates the values of each parameter (used by display_name)
VALUE_NAME_MAPS = {
  "selection": SELECTION_NAMES,
  "crossover": CROSSOVER_NAMES,
  "mutation": MUTATION_NAMES,
}
# The CSV only keeps the exit code of a child process that died without a result
# ("crashed") and the Python error text ("error"); for the exact methods both
# happen when the run reaches the memory limit, so the text says "probable"
STATUS_TEXT = {
  "ok": "ok",
  "timeout": "time limit",
  "memory": "memory limit",
  "crashed": "ended without a result (probably memory)",
  "recursion_limit": "recursion limit",
  "error": "error",
  "skipped": "skipped",
}
STOP_REASON = {
  "timeout": "time",
  "memory": "memory",
  "crashed": "probably memory",
  "recursion_limit": "recursion",
  "error": "error",
}

# Colors
BLUE = "#0072B2"
GREEN = "#009E73"
VERMILLION = "#D55E00"
SELECTION_COLORS = {"roulette": BLUE, "ranking": VERMILLION, "tournament": GREEN}
METHOD_STYLE = {
  METHOD_GA: {"color": BLUE, "label": "Genetic (mean)", "marker": "o"},
  METHOD_DP: {"color": GREEN, "label": "DP", "marker": "o"},
  METHOD_EXHAUSTIVE: {"color": VERMILLION, "label": "Exhaustive", "marker": "s"},
}

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE_RAMP = LinearSegmentedColormap.from_list(
  "blue_ramp", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)

# Global matplotlib style
plt.rcParams.update(
  {
    "font.size": 10,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.labelcolor": INK_SECONDARY,
    "axes.edgecolor": AXIS,
    "xtick.color": AXIS,
    "ytick.color": AXIS,
    "xtick.labelcolor": INK_SECONDARY,
    "ytick.labelcolor": INK_SECONDARY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "legend.frameon": False,
  }
)


# Helpers
def is_maximize(problem: str) -> bool:
  """True when a larger value is better for this problem (knapsack, rod cutting)."""
  return any(keyword in problem for keyword in MAXIMIZE_KEYWORDS)


def mean_std(values: list[float]) -> tuple[float, float]:
  """Mean and sample standard deviation (0 when there is a single value)."""
  return statistics.mean(values), (statistics.stdev(values) if len(values) > 1 else 0.0)


def to_float(text) -> float | None:
  """Convert a CSV cell to float; empty or invalid cells become None."""
  try:
    return float(text)
  except (TypeError, ValueError):
    return None


def display_name(parameter: str, value: str) -> str:
  """Readable name of a parameter value (for example "ox" -> "OX"); unknown values stay as they are."""
  return VALUE_NAME_MAPS.get(parameter, {}).get(value, value)


def ga_ok_rows(rows: list[dict], experiment: str) -> list[dict]:
  """Genetic algorithm rows of one experiment that finished correctly (status ok)."""
  return [
    row
    for row in rows
    if row["experiment"] == experiment and row["method"] == METHOD_GA and row["status"] == STATUS_OK
  ]


def group_values(rows: list[dict]) -> dict[str, list[float]]:
  """config_id -> list of final values (one per seed)."""
  groups = defaultdict(list)

  for row in rows:
    value = to_float(row["value"])

    if value is not None:
      groups[row["config_id"]].append(value)

  return groups


def save(fig, path: str) -> str:
  """Write the figure as a 200 dpi PNG and free its memory."""
  fig.savefig(path, dpi=200, bbox_inches="tight")
  plt.close(fig)

  return path


def shared_legend(fig, axes, columns: int = 3) -> None:
  """One legend below the plots, so it never covers a curve."""
  # Collect the entries of every axis, skipping repeated labels
  handles, labels = [], []

  for ax in axes:
    for handle, label in zip(*ax.get_legend_handles_labels()):
      if label not in labels:
        handles.append(handle)
        labels.append(label)

  fig.legend(
    handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=columns, fontsize=8.5
  )


def apply_size_axis(axes, sizes: list[int]) -> None:
  """Use a log x axis, with round tick values, when the sizes span a wide range."""
  if not sizes:
    return

  low, high = min(sizes), max(sizes)

  if high / low <= LOG_AXIS_RATIO:
    return  # narrow range: the default linear axis is clearer

  # Ticks: the smallest size, the round values in between and the largest size.
  ticks = []
  # Minimum ratio between neighbouring ticks; a very wide range only gets powers of ten
  spacing = 1.9 if high / low <= 1000 else 9.0

  for tick in [low] + [t for t in SIZE_TICKS if low < t < high] + [high]:
    if not ticks or tick / ticks[-1] >= spacing:  # skip ticks that would overlap
      ticks.append(tick)

  if len(ticks) > 1 and high / ticks[-1] > 1.0:
    ticks[-1] = high  # the largest size is always labelled

  for ax in axes:
    ax.set_xscale("log")
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(NullLocator())


# Figure 1: convergence by selection method
def aligned_curves(runs: list[list[tuple[int, float]]]):
  """Mean and sample standard deviation of several best-so-far curves.

  The best value so far is a step function, so every curve is read on a common
  evaluation grid by taking its last recorded value at or before each point.
  """
  # Common x values: every evaluation count that appears in any run
  grid = sorted({evaluation for run in runs for evaluation, _ in run})
  stacked = []

  for run in runs:
    evaluations = np.array([point[0] for point in run])
    values = np.array([point[1] for point in run])
    # Position of the last recorded point at or before each grid value
    index = np.searchsorted(evaluations, grid, side="right") - 1
    stacked.append(values[np.clip(index, 0, None)])

  y = np.array(stacked)  # one row per run, one column per grid value
  mean = y.mean(axis=0)
  std = y.std(axis=0, ddof=1) if len(runs) > 1 else np.zeros(len(grid))

  return np.array(grid), mean, std


def converges_early(curves: list[tuple]) -> bool:
  """True when every curve has made most of its improvement in the first part of the run.

  Each item of ``curves`` is (x, mean). In that case a linear axis squeezes the interesting
  part against the left border, so the caller switches to a logarithmic axis.
  """
  for x, mean in curves:
    total = abs(mean[0] - mean[-1])

    if total == 0:
      continue  # a flat curve says nothing about the scale

    early = x <= EARLY_FRACTION * x[-1]
    done = abs(mean[0] - mean[early][-1]) if early.any() else 0.0

    if done < EARLY_SHARE * total:
      return False

  return True


def label_line_ends(ax, ends: list[tuple[float, str]], x: float) -> None:
  """Write each curve's name next to its last point, pushing close labels apart."""
  low, high = ax.get_ylim()
  gap = 0.035 * (high - low)  # minimum vertical distance between two labels
  previous = None

  for y, name in sorted(ends):
    if previous is not None and y - previous < gap:
      y = previous + gap

    ax.text(x, y, name, va="center", ha="left", fontsize=9, color=INK_SECONDARY)
    previous = y


def figure_convergence(problem: str, rows: list[dict], results_dir: str, out_dir: str):
  """Figure 1: best value so far against fitness evaluations, one curve per selection method.

  Each curve is the mean of the seeds and the band is one standard deviation.
  """
  history_dir = os.path.join(results_dir, "history", problem)
  curves = {}  # selection method -> list of runs (one history per seed)
  sizes = set()

  for selection in SELECTION_NAMES:
    config_id = f"ofat__selection__{selection}"
    runs = []

    for row in ga_ok_rows(rows, "exp1_ofat"):
      if row["config_id"] != config_id:
        continue

      path = history_file(history_dir, row)

      if os.path.exists(path):
        runs.append(load_history(path))
        sizes.add(row["size"])

    if runs:
      curves[selection] = runs

  if not curves:
    print(f"  [skip] Figure 1: no convergence files found in {history_dir}")
    return None

  fig, ax = plt.subplots(figsize=(7.4, 4.4))
  ends = []
  last_x = 0

  # Aligned curves of every selection method, so the x scale can be chosen before drawing
  aligned = {name: aligned_curves(runs) for name, runs in curves.items()}
  use_log = converges_early([(x, mean) for x, mean, _ in aligned.values()])

  for name in SELECTION_NAMES:
    if name not in curves:
      continue

    x, mean, std = aligned[name]

    if use_log:
      keep = x > 0  # a log axis cannot show evaluation 0
      x, mean, std = x[keep], mean[keep], std[keep]

    color = SELECTION_COLORS[name]
    ax.plot(x, mean, color=color, label=SELECTION_NAMES[name], linewidth=2)
    ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.18, linewidth=0)
    ends.append((float(mean[-1]), SELECTION_NAMES[name]))
    last_x = max(last_x, float(x[-1]))


  if use_log:
    ax.set_xscale("log")
    ax.set_xlim(right=last_x * 2.2)  # empty margin on the right for the end labels
    label_line_ends(ax, ends, last_x * 1.08)
  else:
    ax.set_xlim(left=0, right=last_x * 1.15)  # empty margin on the right for the end labels
    label_line_ends(ax, ends, last_x * 1.012)

  runs_per_curve = min(len(runs) for runs in curves.values())
  ax.set_xlabel("Fitness evaluations (log scale)" if use_log else "Fitness evaluations")
  ax.set_ylabel(VALUE_LABELS.get(problem, "Best value"))
  ax.set_title(
    f"{TITLES.get(problem, problem)}: convergence by selection method "
    f"({runs_per_curve} runs, size {', '.join(sorted(sizes))})\n"
    "line: mean; band: one standard deviation",
    fontsize=10,
  )
  shared_legend(fig, [ax])

  return save(fig, os.path.join(out_dir, f"fig1_convergence_{problem}.png"))


# Figure 2: result by crossover (and mutation)
def figure_operators(problem: str, rows: list[dict], out_dir: str):
  """Figure 2: final result per crossover + mutation pair (or per crossover alone).

  Problems with the crossover x mutation experiment (TSP, N-Queens) get one bar per pair.
  The others fall back to the one-parameter-at-a-time crossover runs.
  """
  pair_groups = group_values(ga_ok_rows(rows, "exp1_cxmut"))
  groups = []  # (label, values)

  if pair_groups:
    for crossover in CROSSOVER_NAMES:
      for mutation in MUTATION_NAMES:
        config_id = f"cxmut__{crossover}__{mutation}"

        if config_id in pair_groups:
          label = f"{CROSSOVER_NAMES[crossover]} + {MUTATION_NAMES[mutation]}"
          groups.append((label, pair_groups[config_id]))

    subtitle = "crossover and mutation"
    if any("__gaussian_s" in config_id for config_id in pair_groups):
      subtitle = "crossover and gaussian mutation sigma"

    if len(groups) > 6:
      # Many pairs (rod cutting: 4 crossovers x 3 gaussian sigmas): two-line labels so they do not overlap
      groups = [(label.replace(" + ", "\n"), values) for label, values in groups]
  else:
    ofat_groups = group_values(ga_ok_rows(rows, "exp1_ofat"))

    for crossover in CROSSOVER_NAMES:
      config_id = f"ofat__crossover__{crossover}"

      if config_id in ofat_groups:
        groups.append((CROSSOVER_NAMES[crossover], ofat_groups[config_id]))

    subtitle = "crossover (one parameter at a time)"

  if not groups:
    print("  [skip] Figure 2: no crossover data found")
    return None

  fig, ax = plt.subplots(figsize=(min(15, max(5.5, 1.5 * len(groups) + 2)), 4.4))
  positions = np.arange(len(groups))
  stats = [mean_std(values) for _, values in groups]
  means = [mean for mean, _ in stats]
  stds = [std for _, std in stats]
  # When values cannot be negative (conflicts, distances), the lower error arm
  # stops at zero instead of drawing an impossible negative result
  nonnegative = all(value >= 0 for _, values in groups for value in values)
  lower = [min(std, mean) if nonnegative else std for mean, std in zip(means, stds)]
  ax.bar(positions, means, color=BLUE, width=0.55, zorder=2)
  ax.errorbar(positions, means, yerr=[lower, stds], fmt="none", ecolor=INK, capsize=4, linewidth=1.4, zorder=3)

  for position, (_, values) in zip(positions, groups):
    # One dot per seed, so the spread of the 3 runs is visible and not only its summary
    ax.scatter([position] * len(values), values, color=SURFACE, edgecolor=INK, s=22, linewidth=1, zorder=4)

  ax.set_xticks(positions)
  ax.set_xticklabels([label for label, _ in groups])
  ax.set_ylabel(VALUE_LABELS.get(problem, "Final value"))
  ax.set_title(
    f"{TITLES.get(problem, problem)}: final result by {subtitle}\n"
    "bar: mean; line: standard deviation; dots: each run",
    fontsize=10,
  )
  ax.grid(axis="x", visible=False)

  return save(fig, os.path.join(out_dir, f"fig2_operators_{problem}.png"))


# Figure 3: heatmap population x mutation rate
def figure_heatmap(problem: str, rows: list[dict], out_dir: str):
  """Figure 3: heat map of the mean final value for each population size x mutation rate."""
  cells = defaultdict(list)

  for row in ga_ok_rows(rows, "exp1_heatmap"):
    parts = row["config_id"].split("__")  # heatmap__pop_20__mut_0.05
    population = int(parts[1].split("_")[1])
    mutation_rate = float(parts[2].split("_")[1])
    value = to_float(row["value"])

    if value is not None:
      cells[(population, mutation_rate)].append(value)

  if not cells:
    print("  [skip] Figure 3: no heatmap data found")
    return None

  # Rows are population sizes, columns are mutation rates; a cell is the mean over the seeds
  populations = sorted({population for population, _ in cells})
  rates = sorted({rate for _, rate in cells})
  matrix = np.full((len(populations), len(rates)), np.nan)

  for i, population in enumerate(populations):
    for j, rate in enumerate(rates):
      if (population, rate) in cells:
        matrix[i, j] = statistics.mean(cells[(population, rate)])

  # The darkest cell is always the best one: the ramp is reversed when smaller is better
  maximize = is_maximize(problem)
  fig, ax = plt.subplots(figsize=(1.2 * len(rates) + 3, 0.8 * len(populations) + 2.4))
  image = ax.imshow(matrix, cmap=BLUE_RAMP if maximize else BLUE_RAMP.reversed(), aspect="auto")
  largest = np.nanmax(np.abs(matrix))
  decimals = 0 if largest >= 100 else 1 if largest >= 10 else 2

  for i in range(len(populations)):
    for j in range(len(rates)):
      if np.isnan(matrix[i, j]):
        continue

      # White text on dark cells and dark text on light cells, from the cell's brightness
      red, green, blue, _ = image.cmap(image.norm(matrix[i, j]))
      text_color = "white" if 0.299 * red + 0.587 * green + 0.114 * blue < 0.5 else INK
      ax.text(j, i, f"{matrix[i, j]:.{decimals}f}", ha="center", va="center", color=text_color, fontsize=9)

  target = np.nanmax(matrix) if maximize else np.nanmin(matrix)

  for i, j in zip(*np.where(matrix == target)):  # every tied best cell gets a box
    ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=VERMILLION, linewidth=3))

  ax.set_xticks(range(len(rates)))
  ax.set_xticklabels([f"{rate:g}" for rate in rates])
  ax.set_yticks(range(len(populations)))
  ax.set_yticklabels([str(population) for population in populations])
  ax.set_xlabel("Mutation rate")
  ax.set_ylabel("Population size")
  ax.grid(False)
  colorbar = fig.colorbar(image, ax=ax)
  colorbar.set_label(f"Mean value ({'higher' if maximize else 'lower'} is better)")
  colorbar.outline.set_visible(False)
  ax.set_title(
    f"{TITLES.get(problem, problem)}: population size and mutation rate\n"
    "darker is better; the box marks the best cell (or the tied cells)",
    fontsize=10,
  )

  return save(fig, os.path.join(out_dir, f"fig3_heatmap_{problem}.png"))


# Figures 4 and 5: genetic algorithm against the exact methods
def exp2_rows(problem: str, rows: list[dict]) -> list[dict]:
  """Experiment 2 rows, without sizes that repeat the Experiment 1 instance."""
  # For N-Queens the instance depends only on the size, so a size that was already
  # used in Experiment 1 would just repeat that instance and is left out
  exp1_sizes = {int(row["size"]) for row in rows if row["experiment"].startswith("exp1")}
  selected = []

  for row in rows:
    if row["experiment"] != "exp2":
      continue

    if problem in INSTANCE_FREE_PROBLEMS and int(row["size"]) in exp1_sizes:
      continue

    selected.append(row)

  return selected


def method_series(rows: list[dict], method: str, column: str, scale: float = 1.0) -> dict[int, list[float]]:
  """size -> values of the runs that finished (status ok)."""
  data = defaultdict(list)

  for row in rows:
    if row["method"] == method and row["status"] == STATUS_OK:
      value = to_float(row[column])

      if value is not None:
        data[int(row["size"])].append(value / scale)

  return dict(sorted(data.items()))


def stop_points(rows: list[dict]) -> dict[str, tuple[int, str]]:
  """For each exact method, the smallest size where it stopped and why."""
  stops = {}

  for method in (METHOD_EXHAUSTIVE, METHOD_DP):
    # Rows that hit a limit (time, memory, recursion) or failed; skipped rows are not counted
    # because they only exist after the method already stopped at a smaller size
    stopped = [
      (int(row["size"]), row["status"])
      for row in rows
      if row["method"] == method and (row["status"] in LIMIT_STATUSES or row["status"] == STATUS_ERROR)
    ]

    if stopped:
      stops[method] = min(stopped)

  return stops


def draw_methods(
  ax, rows: list[dict], column: str, scale: float = 1.0, positive_only: bool = False, log: bool = False
) -> list[int]:
  """Draw genetic (mean and std) and exact methods on ``ax``; return the sizes used.

  The lower error arm of the genetic curve never crosses zero when its values
  cannot be negative (conflicts, times, memory), and stays above zero on a log axis.
  """
  sizes = set()

  for method in (METHOD_GA, METHOD_DP, METHOD_EXHAUSTIVE):
    series = method_series(rows, method, column, scale)

    if positive_only:
      # A log axis cannot show zero, so zero readings (below the memory
      # measurement resolution, for example) are dropped
      series = {size: [v for v in values if v > 0] for size, values in series.items()}
      series = {size: values for size, values in series.items() if values}

    if not series:
      continue

    style = METHOD_STYLE[method]
    xs = list(series)
    sizes.update(xs)
    stats = [mean_std(series[size]) for size in xs]
    means = [mean for mean, _ in stats]
    stds = [std for _, std in stats]

    # Genetic: line with error bars. Exhaustive: dashed line with hollow squares
    # DP: solid line. Colour is never the only cue: marker and line style differ too
    if method == METHOD_GA:
      nonnegative = log or all(v >= 0 for values in series.values() for v in values)
      share = 0.9 if log else 1.0
      lower = [min(std, mean * share) if nonnegative else std for mean, std in zip(means, stds)]
      ax.errorbar(xs, means, yerr=[lower, stds], color=style["color"], marker=style["marker"],
        markersize=4, capsize=3, linewidth=1.8, label=style["label"])
    elif method == METHOD_EXHAUSTIVE:
      ax.plot(xs, means, color=style["color"], marker=style["marker"], markersize=8,
        markerfacecolor="none", linestyle="--", linewidth=1.3, label=style["label"])
    else:
      ax.plot(xs, means, color=style["color"], marker=style["marker"], markersize=4,
        linewidth=1.8, label=style["label"])

  return sorted(sizes)


def draw_stops(axes, stops: dict[str, tuple[int, str]]) -> None:
  """Draw a dotted vertical line where each exact method stopped, with the reason in the legend."""
  for method, (size, status) in stops.items():
    style = METHOD_STYLE[method]
    label = f"{style['label']}: stops at {size} ({STOP_REASON.get(status, status)})"

    for ax in axes:
      ax.axvline(size, color=style["color"], linestyle=":", linewidth=1.3, label=label)


def figure_exact_vs_ga(problem: str, rows: list[dict], out_dir: str, time_limit: float):
  """Figure 4: quality (left) and time (right) of the genetic algorithm against both exact methods."""
  data = exp2_rows(problem, rows)

  if not data:
    print("  [skip] Figure 4: no Experiment 2 data found")
    return None

  fig, (ax_quality, ax_time) = plt.subplots(1, 2, figsize=(11, 4.4))
  log_quality = problem in LOG_QUALITY_PROBLEMS
  sizes = draw_methods(ax_quality, data, "value", positive_only=log_quality, log=log_quality)
  # Time spans many orders of magnitude, so its y axis is logarithmic
  draw_methods(ax_time, data, "time_seconds", positive_only=True, log=True)
  ax_time.set_yscale("log")
  ax_time.axhline(time_limit, color=INK_MUTED, linestyle="--", linewidth=1, label=f"Exact-method limit: {time_limit / 60:g} min")
  draw_stops([ax_quality, ax_time], stop_points(data))
  apply_size_axis([ax_quality, ax_time], sizes)
  ax_quality.margins(y=0.12)

  if log_quality:
    ax_quality.set_yscale("log")
  # Start at zero when no value is negative (otherwise the axis would show empty negative space)
  elif all(v >= 0 for line in ax_quality.get_lines() for v in line.get_ydata() if np.isfinite(v)):
    ax_quality.set_ylim(bottom=0)

  ax_quality.set_ylabel(VALUE_LABELS.get(problem, "Value"))
  ax_time.set_ylabel("Time [s]")

  for ax in (ax_quality, ax_time):
    ax.set_xlabel(SIZE_LABELS.get(problem, "Size"))

  seeds = len({row["seed"] for row in data if row["method"] == METHOD_GA})
  fig.suptitle(f"{TITLES.get(problem, problem)}: genetic algorithm vs exhaustive recursion and DP", fontsize=11, y=1.0)
  fig.text(
    0.5, 0.925,
    f"Each size is a different instance. Genetic: mean and standard deviation of {seeds} runs.",
    ha="center", fontsize=8.5, color=INK_SECONDARY,
  )
  fig.subplots_adjust(top=0.84, wspace=0.22)
  shared_legend(fig, [ax_quality, ax_time], columns=3)

  return save(fig, os.path.join(out_dir, f"fig4_exact_vs_ga_{problem}.png"))


def figure_memory(problem: str, rows: list[dict], out_dir: str, memory_limit: float | None):
  """Figure 5: peak memory of each method (MB, log scale); the limit line needs --memory-limit."""
  data = exp2_rows(problem, rows)

  if not data:
    return None

  fig, ax = plt.subplots(figsize=(6.6, 4.4))
  sizes = draw_methods(ax, data, "peak_memory_kb", scale=1024.0, positive_only=True, log=True)

  if not sizes:
    plt.close(fig)
    return None

  ax.set_yscale("log")

  if memory_limit:
    ax.axhline(memory_limit, color=INK_MUTED, linestyle="--", linewidth=1, label=f"Limit: {memory_limit:g} MB")

  draw_stops([ax], stop_points(data))
  apply_size_axis([ax], sizes)
  ax.set_xlabel(SIZE_LABELS.get(problem, "Size"))
  ax.set_ylabel("Peak memory [MB]")
  ax.set_title(
    f"{TITLES.get(problem, problem)}: memory\n"
    "increase of the resident memory peak (smallest measurable value: about 0.1 MB)",
    fontsize=10,
  )
  shared_legend(fig, [ax], columns=2)

  return save(fig, os.path.join(out_dir, f"fig5_memory_{problem}.png"))


# Tables
def number(value: float) -> str:
  """Integers without decimals, everything else with two."""
  if value == int(value):
    return str(int(value))

  return f"{value:.2f}"


def signed(value: float) -> str:
  """Number with an explicit sign (+1.5, -2), or 0 when it is practically zero."""
  if abs(value) < 0.005:
    return "0"

  return f"{value:+.2f}".rstrip("0").rstrip(".")


def seconds(value: float) -> str:
  """Seconds with 4 decimals when very small, so fast runs do not show as 0.00."""
  return f"{value:.4f}" if value < 0.01 else f"{value:.2f}"


def parameter_value_name(parameter: str, text: str) -> str:
  return display_name(parameter, text)


def write_tables(problem: str, rows: list[dict], path: str) -> str:
  """Write the Markdown tables for the report: setup, parameter sensitivity, best combinations and Experiment 2."""
  maximize = is_maximize(problem)
  title = TITLES.get(problem, problem)
  lines = [f"# {title}: result tables", ""]

  # Setup
  ga_rows = [row for row in rows if row["method"] == METHOD_GA and row["status"] == STATUS_OK]
  exp1_instances = sorted({row["instance"] for row in rows if row["experiment"].startswith("exp1")})
  exp2 = exp2_rows(problem, rows)
  seeds = sorted({int(row["seed"]) for row in ga_rows})
  evaluations = sorted({int(float(row["evaluations"])) for row in ga_rows if to_float(row["evaluations"])})
  lines += [
    "## Experiment setup",
    "",
    f"- Experiment 1 instance: {', '.join(exp1_instances)}",
    f"- Experiment 2 instances: {', '.join(sorted({row['instance'] for row in exp2}))}",
    f"- Seeds: {', '.join(str(seed) for seed in seeds)}",
    f"- Fitness evaluations per run: {', '.join(str(n) for n in evaluations)}",
    "",
  ]

  # Parameter sensitivity (one parameter at a time): for each parameter, compare the mean
  # result of its values. A large difference between best and worst means the parameter matters
  by_parameter = defaultdict(lambda: defaultdict(list))

  for row in ga_ok_rows(rows, "exp1_ofat"):
    _, parameter, value_text = row["config_id"].split("__")
    value = to_float(row["value"])

    if value is not None:
      by_parameter[parameter][value_text].append(value)

  sensitivity = []

  for parameter, values in by_parameter.items():
    means = {text: statistics.mean(runs) for text, runs in values.items()}
    best = (max if maximize else min)(means, key=means.get)
    worst = (min if maximize else max)(means, key=means.get)
    sensitivity.append((abs(means[best] - means[worst]), parameter, means, best, worst))

  sensitivity.sort(reverse=True)  # most influential parameter first
  lines += [
    "## Sensitivity to each parameter (one parameter at a time)",
    "",
    "| Parameter | Best value (mean) | Worst value (mean) | Difference between means |",
    "|---|---|---|---|",
  ]

  for spread, parameter, means, best, worst in sensitivity:
    lines.append(
      f"| {PARAMETER_NAMES.get(parameter, parameter)} "
      f"| {parameter_value_name(parameter, best)} ({number(means[best])}) "
      f"| {parameter_value_name(parameter, worst)} ({number(means[worst])}) "
      f"| {number(spread)} |"
    )

  lines.append("")

  # Best configurations (combinations of the best values of each parameter), ranked by mean
  combos = group_values(ga_ok_rows(rows, "exp1_combo"))
  ranked = sorted(combos.items(), key=lambda item: statistics.mean(item[1]), reverse=maximize)
  lines += [
    "## Best combinations (Experiment 1)",
    "",
    "| Rank | Configuration | Mean | Standard deviation | Runs |",
    "|---|---|---|---|---|",
  ]

  for position, (config_id, values) in enumerate(ranked[:5], start=1):
    mean, std = mean_std(values)
    lines.append(f"| {position} | `{config_id}` | {number(mean)} | {std:.2f} | {len(values)} |")

  used = sorted({row["config_id"] for row in exp2 if row["method"] == METHOD_GA})

  if used:
    lines += ["", f"Configuration used in Experiment 2: `{used[0]}`"]

  lines.append("")

  # Experiment 2: one block per size. The "optimum" is the value of an exact method that
  # finished, and the genetic row reports its mean difference to that value
  lines += [
    "## Experiment 2: genetic algorithm vs exhaustive recursion and DP",
    "",
    "| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |",
    "|---|---|---|---|---|---|---|",
  ]
  sizes = sorted({int(row["size"]) for row in exp2})
  names = {METHOD_EXHAUSTIVE: "Exhaustive", METHOD_DP: "DP", METHOD_GA: "Genetic (mean ± std)"}

  for size in sizes:
    optimum = None  # value proven by an exact method that finished

    for method in (METHOD_EXHAUSTIVE, METHOD_DP):
      for row in exp2:
        if int(row["size"]) == size and row["method"] == method and row["status"] == STATUS_OK:
          optimum = to_float(row["value"])

    for method in (METHOD_EXHAUSTIVE, METHOD_DP, METHOD_GA):
      selected = [row for row in exp2 if int(row["size"]) == size and row["method"] == method]

      if not selected:
        continue

      if method == METHOD_GA:
        finished = [row for row in selected if row["status"] == STATUS_OK]

        if not finished:
          continue

        value_mean, value_std = mean_std([float(row["value"]) for row in finished])
        time_mean = statistics.mean(float(row["time_seconds"]) for row in finished)
        memory_mean = statistics.mean(float(row["peak_memory_kb"]) for row in finished) / 1024
        difference = signed(value_mean - optimum) if optimum is not None else "-"
        lines.append(
          f"| {size} | {names[method]} | ok | {number(value_mean)} ± {value_std:.2f} "
          f"| {difference} | {seconds(time_mean)} | {memory_mean:.1f} |"
        )
      else:
        row = selected[0]
        value = to_float(row["value"])
        elapsed = to_float(row["time_seconds"])
        memory = to_float(row["peak_memory_kb"])
        lines.append(
          f"| {size} | {names[method]} | {STATUS_TEXT.get(row['status'], row['status'])} "
          f"| {number(value) if value is not None else '-'} | - "
          f"| {seconds(elapsed) if elapsed is not None else '-'} "
          f"| {f'{memory / 1024:.1f}' if memory is not None else '-'} |"
        )

  lines += [
    "",
    "- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same "
    "instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.",
    "- Skipped: the method had already reached its limit at a smaller size.",
    "- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the "
    "error text; for an exact method this happens when it reaches the memory limit.",
    "- Memory: increase of the resident memory peak during the run. The measurement moves in steps "
    "of about 128 KB, so values of 0.1 MB or less are at its resolution.",
    "",
  ]

  with open(path, "w", encoding="utf-8") as file:
    file.write("\n".join(lines))

  return path


# Main
def discover_problems(results_dir: str) -> list[str]:
  """Problem names found as <problem>_results.csv files in the results folder."""
  paths = sorted(glob.glob(os.path.join(results_dir, "*_results.csv")))
  return [os.path.basename(path)[: -len("_results.csv")] for path in paths]


def main():
  parser = argparse.ArgumentParser(description="Make the figures and tables of the experiments.")
  parser.add_argument("--problem", default="all", help="Problem name (for example tsp) or 'all'")
  parser.add_argument("--results-dir", default=RESULTS_DIR, help="Folder with the results CSV files")
  parser.add_argument(
    "--time-limit",
    type=float,
    default=DEFAULT_TIME_LIMIT_SECONDS,
    help=f"Time limit used in the experiments, in seconds (default: {DEFAULT_TIME_LIMIT_SECONDS:g})",
  )
  parser.add_argument(
    "--memory-limit",
    type=float,
    default=None,
    help="Memory limit used in the experiments, in MB (draws the limit line in Figure 5)",
  )
  args = parser.parse_args()

  results_dir = args.results_dir
  out_dir = os.path.join(results_dir, "figures")
  os.makedirs(out_dir, exist_ok=True)

  problems = discover_problems(results_dir) if args.problem == "all" else [args.problem]

  if not problems:
    print(f"No *_results.csv files found in {results_dir}")
    return

  for problem in problems:
    csv_path = os.path.join(results_dir, f"{problem}_results.csv")
    rows = [row for row in load_rows(csv_path) if row["problem"] == problem]

    if not rows:
      print(f"{problem}: no rows in {csv_path}")
      continue

    print(f"{problem}: {len(rows)} rows")
    # Each function returns the path it wrote, or None when its data is missing
    # (for example Figure 1 when the history files are not there)
    outputs = [
      figure_convergence(problem, rows, results_dir, out_dir),
      figure_operators(problem, rows, out_dir),
      figure_heatmap(problem, rows, out_dir),
      figure_exact_vs_ga(problem, rows, out_dir, args.time_limit),
      figure_memory(problem, rows, out_dir, args.memory_limit),
      write_tables(problem, rows, os.path.join(out_dir, f"tables_{problem}.md")),
    ]

    for output in outputs:
      if output:
        print(f"  wrote {output}")

if __name__ == "__main__":
  main()