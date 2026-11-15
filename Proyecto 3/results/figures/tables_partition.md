# Partition: result tables

## Experiment setup

- Experiment 1 instance: fixed_n50_s777
- Experiment 2 instances: scale_n100_s9100, scale_n1500_s10500, scale_n15_s9015, scale_n20_s9020, scale_n25_s9025, scale_n3000_s12000, scale_n32_s9032, scale_n500_s9500
- Seeds: 42, 101, 2026
- Fitness evaluations per run: 20000

## Sensitivity to each parameter (one parameter at a time)

| Parameter | Best value (mean) | Worst value (mean) | Difference between means |
|---|---|---|---|
| Selection | Roulette (1) | Roulette (1) | 0 |
| Population | 20 (1) | 20 (1) | 0 |
| Mutation rate | 0.01 (1) | 0.01 (1) | 0 |
| Elitism | 0 (1) | 0 (1) | 0 |
| Crossover rate | 0.6 (1) | 0.6 (1) | 0 |
| Crossover | 1-point (1) | 1-point (1) | 0 |

## Best combinations (Experiment 1)

| Rank | Configuration | Mean | Standard deviation | Runs |
|---|---|---|---|---|
| 1 | `combo__p20__roulette__one_point__cr0.6__mr0.01__el0` | 1 | 0.00 | 3 |
| 2 | `combo__p20__roulette__one_point__cr0.6__mr0.01__el2` | 1 | 0.00 | 3 |
| 3 | `combo__p20__roulette__one_point__cr0.6__mr0.05__el0` | 1 | 0.00 | 3 |
| 4 | `combo__p20__roulette__one_point__cr0.6__mr0.05__el2` | 1 | 0.00 | 3 |
| 5 | `combo__p20__roulette__one_point__cr0.8__mr0.01__el0` | 1 | 0.00 | 3 |

Configuration used in Experiment 2: `combo__p20__roulette__one_point__cr0.6__mr0.01__el0`

## Experiment 2: genetic algorithm vs exhaustive recursion and DP

| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |
|---|---|---|---|---|---|---|
| 15 | Exhaustive | ok | 0 | - | 0.0037 | 0.0 |
| 15 | DP | ok | 0 | - | 0.0006 | 0.0 |
| 15 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 0.18 | 0.3 |
| 20 | Exhaustive | ok | 1 | - | 0.11 | 0.0 |
| 20 | DP | ok | 1 | - | 0.0018 | 0.0 |
| 20 | Genetic (mean ± std) | ok | 1 ± 0.00 | 0 | 0.20 | 0.3 |
| 25 | Exhaustive | ok | 1 | - | 3.36 | 0.0 |
| 25 | DP | ok | 1 | - | 0.0029 | 0.1 |
| 25 | Genetic (mean ± std) | ok | 1 ± 0.00 | 0 | 0.20 | 0.3 |
| 32 | Exhaustive | ok | 1 | - | 438.22 | 0.0 |
| 32 | DP | ok | 1 | - | 0.0075 | 0.1 |
| 32 | Genetic (mean ± std) | ok | 1 ± 0.00 | 0 | 0.23 | 0.3 |
| 100 | Exhaustive | time limit | - | - | 600.00 | - |
| 100 | DP | ok | 0 | - | 0.13 | 10.7 |
| 100 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 0.42 | 0.3 |
| 500 | Exhaustive | skipped | - | - | - | - |
| 500 | DP | ok | 1 | - | 4.88 | 476.5 |
| 500 | Genetic (mean ± std) | ok | 1 ± 0.00 | 0 | 1.34 | 0.3 |
| 1500 | Exhaustive | skipped | - | - | - | - |
| 1500 | DP | ok | 0 | - | 62.25 | 3978.1 |
| 1500 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 3.95 | 0.4 |
| 3000 | Exhaustive | skipped | - | - | - | - |
| 3000 | DP | error | - | - | 62.44 | 4069.5 |
| 3000 | Genetic (mean ± std) | ok | 1 ± 0.00 | - | 7.76 | 1.0 |

- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.
- Skipped: the method had already reached its limit at a smaller size.
- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the error text; for an exact method this happens when it reaches the memory limit.
- Memory: increase of the resident memory peak during the run. The measurement moves in steps of about 128 KB, so values of 0.1 MB or less are at its resolution.
