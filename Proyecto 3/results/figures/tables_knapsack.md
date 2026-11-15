# 0/1 Knapsack: result tables

## Experiment setup

- Experiment 1 instance: fixed_n50_s777
- Experiment 2 instances: scale_n100_s9100, scale_n1500_s10500, scale_n15_s9015, scale_n20_s9020, scale_n25_s9025, scale_n3000_s12000, scale_n32_s9032, scale_n500_s9500
- Seeds: 42, 101, 2026
- Fitness evaluations per run: 20000

## Sensitivity to each parameter (one parameter at a time)

| Parameter | Best value (mean) | Worst value (mean) | Difference between means |
|---|---|---|---|
| Mutation rate | 0.01 (691) | 0.4 (650) | 41 |
| Selection | Ranking (695.67) | Roulette (673.67) | 22 |
| Elitism | 5 (694) | 0 (680.67) | 13.33 |
| Population | 20 (695.33) | 400 (686.67) | 8.67 |
| Crossover rate | 0.95 (692.33) | 0.6 (688.33) | 4 |
| Crossover | 2-point (690) | 1-point (689.33) | 0.67 |

## Best combinations (Experiment 1)

| Rank | Configuration | Mean | Standard deviation | Runs |
|---|---|---|---|---|
| 1 | `combo__p20__ranking__two_point__cr0.8__mr0.05__el5` | 696.33 | 0.58 | 3 |
| 2 | `combo__p20__ranking__uniform__cr0.8__mr0.05__el2` | 696.33 | 0.58 | 3 |
| 3 | `combo__p20__tournament__two_point__cr0.95__mr0.05__el5` | 696.33 | 1.15 | 3 |
| 4 | `combo__p20__ranking__two_point__cr0.95__mr0.05__el5` | 696 | 1.00 | 3 |
| 5 | `combo__p20__ranking__two_point__cr0.95__mr0.05__el2` | 696 | 2.65 | 3 |

Configuration used in Experiment 2: `combo__p20__ranking__two_point__cr0.8__mr0.05__el5`

## Experiment 2: genetic algorithm vs exhaustive recursion and DP

| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |
|---|---|---|---|---|---|---|
| 15 | Exhaustive | ok | 163 | - | 0.0045 | 0.0 |
| 15 | DP | ok | 163 | - | 0.0005 | 0.0 |
| 15 | Genetic (mean ± std) | ok | 162.33 ± 1.15 | -0.67 | 0.20 | 0.3 |
| 20 | Exhaustive | ok | 320 | - | 0.12 | 0.0 |
| 20 | DP | ok | 320 | - | 0.0008 | 0.0 |
| 20 | Genetic (mean ± std) | ok | 320 ± 0.00 | 0 | 0.22 | 0.3 |
| 25 | Exhaustive | ok | 325 | - | 3.61 | 0.0 |
| 25 | DP | ok | 325 | - | 0.0011 | 0.0 |
| 25 | Genetic (mean ± std) | ok | 321 ± 1.73 | -4 | 0.25 | 0.3 |
| 32 | Exhaustive | ok | 369 | - | 493.57 | 0.0 |
| 32 | DP | ok | 369 | - | 0.0016 | 0.4 |
| 32 | Genetic (mean ± std) | ok | 367.33 ± 2.08 | -1.67 | 0.25 | 1.0 |
| 100 | Exhaustive | time limit | - | - | 600.00 | - |
| 100 | DP | ok | 1437 | - | 0.04 | 2.5 |
| 100 | Genetic (mean ± std) | ok | 1419.67 ± 8.08 | -17.33 | 0.49 | 0.3 |
| 500 | Exhaustive | skipped | - | - | - | - |
| 500 | DP | ok | 6380 | - | 1.33 | 159.7 |
| 500 | Genetic (mean ± std) | ok | 5869.67 ± 17.79 | -510.33 | 1.92 | 0.3 |
| 1500 | Exhaustive | skipped | - | - | - | - |
| 1500 | DP | ok | 19491 | - | 16.11 | 1531.4 |
| 1500 | Genetic (mean ± std) | ok | 17121.67 ± 46.37 | -2369.33 | 5.79 | 0.6 |
| 3000 | Exhaustive | skipped | - | - | - | - |
| 3000 | DP | memory limit | - | - | 52.20 | 3929.7 |
| 3000 | Genetic (mean ± std) | ok | 34196.67 ± 77.40 | - | 11.46 | 1.1 |

- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.
- Skipped: the method had already reached its limit at a smaller size.
- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the error text; for an exact method this happens when it reaches the memory limit.
- Memory: increase of the resident memory peak during the run. The measurement moves in steps of about 128 KB, so values of 0.1 MB or less are at its resolution.
