"""Automated experiment suite for TSP and N-Queens."""

import argparse
from functools import partial
from itertools import product
import os
import random
import statistics

from src.engine.chromosome import Direction, is_better
from src.engine.crossover import ox_crossover, pmx_crossover
from src.engine.genetic_engine import GAConfig
from src.engine.mutation import inversion_mutation, swap_mutation
from src.engine.selection import (
  ranking_selection,
  roulette_selection,
  tournament_selection,
)
from src.experiments.runner import (
  DEFAULT_MEMORY_LIMIT_MB,
  DEFAULT_TIME_LIMIT_SECONDS,
  METHOD_DP,
  METHOD_EXHAUSTIVE,
  STATUS_OK,
  exact_task,
  ga_task,
  load_rows,
  run_tasks,
)
from src.problems.nqueens import NQueens
from src.problems.tsp import TSP, generate_distances

SEEDS = [42, 101, 2026]
EVALUATION_BUDGET = 20_000
EXP1_INSTANCE_SEED = 777
EXP1_SIZE = {"tsp": 30, "nqueens": 30}
EXP2_INSTANCE_BASE_SEED = 9000
EXP2_SIZES = {
  "tsp": [8, 10, 12, 14, 16, 18, 20, 30, 50, 100],
  "nqueens": [8, 10, 12, 13, 14, 15, 16, 20, 30, 50],
}

RESULTS_DIR = "results"

SELECTION_OPTIONS = {
  "roulette": roulette_selection,
  "ranking": partial(ranking_selection, k=5),
  "tournament": partial(tournament_selection, k=3),
}

CROSSOVER_OPTIONS = {
  "ox": ox_crossover,
  "pmx": pmx_crossover,
}

MUTATION_OPTIONS = {
  "swap": swap_mutation,
  "inversion": inversion_mutation,
}

BASE_PARAMS = {
  "population_size": 100,
  "selection": "tournament",
  "crossover": "ox",
  "crossover_rate": 0.8,
  "mutation": "swap",
  # For permutations the rate is checked once per child, so it is higher than
  # the per-gene rates used with binary chromosomes.
  "mutation_rate": 0.2,
  "elitism": 2,
}

OFAT_VALUES = {
  "population_size": [20, 50, 100, 200, 400],
  "selection": ["roulette", "ranking", "tournament"],
  "crossover": ["ox", "pmx"],
  "mutation": ["swap", "inversion"],
  "crossover_rate": [0.6, 0.8, 0.95],
  "mutation_rate": [0.05, 0.1, 0.2, 0.4, 0.8],
  "elitism": [0, 2, 5],
}

HEATMAP_POPULATIONS = [20, 50, 100, 200, 400]
HEATMAP_MUTATION_RATES = [0.05, 0.1, 0.2, 0.4, 0.8]

PROBLEMS = ["tsp", "nqueens"]


def get_csv_path(problem_name: str) -> str:
  return os.path.join(RESULTS_DIR, f"{problem_name}_results.csv")


def get_history_dir(problem_name: str) -> str:
  return os.path.join(RESULTS_DIR, "history", problem_name)


def build_problem(problem_name: str, size: int, instance_seed: int):
  rng = random.Random(instance_seed)
  if problem_name == "tsp":
    return TSP(generate_distances(size, rng))
  if problem_name == "nqueens":
    return NQueens(size)
  raise ValueError(f"Unknown problem: {problem_name}")


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
  # The mutation is part of the id (unlike the binary script) because here it
  # is a parameter that changes between combinations.
  return (
    f"combo__p{params['population_size']}"
    f"__{params['selection']}"
    f"__{params['crossover']}"
    f"__{params['mutation']}"
    f"__cr{params['crossover_rate']}"
    f"__mr{params['mutation_rate']}"
    f"__el{params['elitism']}"
  )


def build_exp1_ofat_tasks(problem_name: str):
  size = EXP1_SIZE[problem_name]
  problem = build_problem(problem_name, size, EXP1_INSTANCE_SEED)
  instance_id = f"fixed_n{size}_s{EXP1_INSTANCE_SEED}"
  tasks = []

  for param_name, values in OFAT_VALUES.items():
    for val in values:
      params = dict(BASE_PARAMS)
      params[param_name] = val
      config_id = f"ofat__{param_name}__{val}"
      for seed in SEEDS:
        cfg = make_ga_config(params, seed)
        tasks.append(
          ga_task("exp1_ofat", problem_name, instance_id, size, config_id, problem, cfg)
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
          ga_task("exp1_heatmap", problem_name, instance_id, size, config_id, problem, cfg)
        )

  return tasks


def select_top2_per_parameter(problem_name: str, direction: Direction) -> dict[str, list]:
  rows = [
    r for r in load_rows(get_csv_path(problem_name))
    if r["experiment"] == "exp1_ofat"
    and r["problem"] == problem_name
    and r["status"] == STATUS_OK
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
  size = EXP1_SIZE[problem_name]
  problem = build_problem(problem_name, size, EXP1_INSTANCE_SEED)
  instance_id = f"fixed_n{size}_s{EXP1_INSTANCE_SEED}"
  top2 = select_top2_per_parameter(problem_name, problem.direction())

  param_names = list(OFAT_VALUES.keys())
  value_lists = [top2[k] for k in param_names]
  tasks = []

  for combo in product(*value_lists):
    params = dict(BASE_PARAMS)
    for k, v in zip(param_names, combo):
      params[k] = v
    config_id = combo_config_id(params)
    for seed in SEEDS:
      cfg = make_ga_config(params, seed)
      tasks.append(
        ga_task("exp1_combo", problem_name, instance_id, size, config_id, problem, cfg)
      )
  return tasks


def find_best_combo_params(problem_name: str, direction: Direction) -> tuple[str, dict]:
  rows = [
    r for r in load_rows(get_csv_path(problem_name))
    if r["experiment"] == "exp1_combo"
    and r["problem"] == problem_name
    and r["status"] == STATUS_OK
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


def build_exp2_tasks(problem_name: str):
  dummy = build_problem(problem_name, 10, EXP2_INSTANCE_BASE_SEED)
  best_cid, best_params = find_best_combo_params(problem_name, dummy.direction())
  tasks = []

  for size in EXP2_SIZES[problem_name]:
    inst_seed = EXP2_INSTANCE_BASE_SEED + size
    instance_id = f"scale_n{size}_s{inst_seed}"
    problem = build_problem(problem_name, size, inst_seed)

    tasks.append(
      exact_task("exp2", problem_name, instance_id, size, problem, METHOD_EXHAUSTIVE)
    )
    tasks.append(
      exact_task("exp2", problem_name, instance_id, size, problem, METHOD_DP)
    )
    for seed in SEEDS:
      cfg = make_ga_config(best_params, seed)
      tasks.append(
        ga_task("exp2", problem_name, instance_id, size, best_cid, problem, cfg)
      )
  return tasks


def main():
  parser = argparse.ArgumentParser(description="Run Ashley's GA experiments (TSP, N-Queens).")
  parser.add_argument("--problem", choices=PROBLEMS + ["all"], default="all")
  parser.add_argument(
    "--stage",
    choices=["exp1_ofat", "exp1_combo", "exp2", "all"],
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
    help=f"Time limit in seconds per run (default: {DEFAULT_TIME_LIMIT_SECONDS})",
  )
  args = parser.parse_args()

  problems = PROBLEMS if args.problem == "all" else [args.problem]

  stages = [
    ("exp1_ofat", "Exp 1 (OFAT + Heatmap)", build_exp1_ofat_tasks),
    ("exp1_combo", "Exp 1 (Top-2 Combinations)", build_exp1_combination_tasks),
    ("exp2", "Exp 2 (GA vs Exhaustive vs DP)", build_exp2_tasks),
  ]

  for prob in problems:
    csv_path = get_csv_path(prob)
    history_dir = get_history_dir(prob)
    for stage_name, title, build in stages:
      if args.stage not in (stage_name, "all"):
        continue
      print(f"\n=== Running {title} for {prob} -> {csv_path} ===")
      run_tasks(
        build(prob),
        csv_path,
        history_dir,
        time_limit_seconds=args.time_limit,
        memory_limit_mb=args.memory_limit,
        cooldown_seconds=args.cooldown,
      )

if __name__ == "__main__":
  main()
