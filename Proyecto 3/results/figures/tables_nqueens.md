# N-Queens: result tables

## Experiment setup

- Experiment 1 instance: fixed_n30_s777
- Experiment 2 instances: scale_n10_s9010, scale_n11_s9011, scale_n12_s9012, scale_n13_s9013, scale_n14_s9014, scale_n15_s9015, scale_n16_s9016, scale_n20_s9020, scale_n50_s9050, scale_n6_s9006, scale_n8_s9008, scale_n9_s9009
- Seeds: 42, 101, 2026
- Fitness evaluations per run: 20000

## Sensitivity to each parameter (one parameter at a time)

| Parameter | Best value (mean) | Worst value (mean) | Difference between means |
|---|---|---|---|
| Mutation rate | 0.1 (0) | 0.05 (2.33) | 2.33 |
| Mutation | Swap (1) | Inversion (2.67) | 1.67 |
| Population | 20 (0.67) | 400 (1.67) | 1 |
| Crossover rate | 0.6 (0) | 0.8 (1) | 1 |
| Selection | Ranking (0.33) | Tournament (1) | 0.67 |
| Crossover | PMX (0.33) | OX (1) | 0.67 |
| Elitism | 0 (0.67) | 2 (1) | 0.33 |

## Best combinations (Experiment 1)

| Rank | Configuration | Mean | Standard deviation | Runs |
|---|---|---|---|---|
| 1 | `combo__p20__ranking__pmx__swap__cr0.6__mr0.1__el0` | 0 | 0.00 | 3 |
| 2 | `combo__p20__ranking__pmx__swap__cr0.6__mr0.4__el0` | 0 | 0.00 | 3 |
| 3 | `combo__p20__ranking__pmx__swap__cr0.95__mr0.4__el0` | 0 | 0.00 | 3 |
| 4 | `combo__p20__ranking__ox__swap__cr0.6__mr0.1__el5` | 0 | 0.00 | 3 |
| 5 | `combo__p20__ranking__ox__swap__cr0.95__mr0.4__el0` | 0 | 0.00 | 3 |

Configuration used in Experiment 2: `combo__p20__ranking__pmx__swap__cr0.6__mr0.1__el0`

## Experiment 2: genetic algorithm vs exhaustive recursion and DP

| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |
|---|---|---|---|---|---|---|
| 6 | Exhaustive | ok | 0 | - | 0.0003 | 0.1 |
| 6 | DP | ok | 0 | - | 0.0004 | 0.1 |
| 6 | Genetic (mean ± std) | ok | 0.67 ± 0.58 | +0.67 | 0.19 | 1.0 |
| 8 | Exhaustive | ok | 0 | - | 0.01 | 0.1 |
| 8 | DP | ok | 0 | - | 0.0017 | 0.2 |
| 8 | Genetic (mean ± std) | ok | 0.33 ± 0.58 | +0.33 | 0.32 | 1.0 |
| 9 | Exhaustive | ok | 0 | - | 0.02 | 0.1 |
| 9 | DP | ok | 0 | - | 0.0096 | 0.2 |
| 9 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 0.22 | 0.2 |
| 10 | Exhaustive | ok | 0 | - | 0.13 | 0.1 |
| 10 | DP | ok | 0 | - | 0.03 | 2.0 |
| 10 | Genetic (mean ± std) | ok | 0.33 ± 0.58 | +0.33 | 0.26 | 0.2 |
| 11 | Exhaustive | ok | 0 | - | 0.75 | 0.0 |
| 11 | DP | ok | 0 | - | 0.12 | 20.4 |
| 11 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 0.25 | 0.2 |
| 12 | Exhaustive | ok | 0 | - | 5.15 | 0.0 |
| 12 | DP | ok | 0 | - | 0.72 | 153.5 |
| 12 | Genetic (mean ± std) | ok | 0.67 ± 0.58 | +0.67 | 0.26 | 0.2 |
| 13 | Exhaustive | ok | 0 | - | 26.34 | 0.1 |
| 13 | DP | ok | 0 | - | 3.67 | 690.1 |
| 13 | Genetic (mean ± std) | ok | 1 ± 0.00 | +1 | 0.29 | 0.2 |
| 14 | Exhaustive | ok | 0 | - | 183.89 | 0.0 |
| 14 | DP | ended without a result (probably memory) | - | - | - | - |
| 14 | Genetic (mean ± std) | ok | 0 ± 0.00 | 0 | 0.41 | 0.2 |
| 15 | Exhaustive | time limit | - | - | 600.00 | - |
| 15 | DP | skipped | - | - | - | - |
| 15 | Genetic (mean ± std) | ok | 0.33 ± 0.58 | - | 0.43 | 0.2 |
| 16 | Exhaustive | skipped | - | - | - | - |
| 16 | DP | skipped | - | - | - | - |
| 16 | Genetic (mean ± std) | ok | 0 ± 0.00 | - | 0.33 | 0.2 |
| 20 | Exhaustive | skipped | - | - | - | - |
| 20 | DP | skipped | - | - | - | - |
| 20 | Genetic (mean ± std) | ok | 0.67 ± 0.58 | - | 0.51 | 0.2 |
| 50 | Exhaustive | skipped | - | - | - | - |
| 50 | DP | skipped | - | - | - | - |
| 50 | Genetic (mean ± std) | ok | 1.67 ± 0.58 | - | 1.72 | 0.2 |

- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.
- Skipped: the method had already reached its limit at a smaller size.
- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the error text; for an exact method this happens when it reaches the memory limit.
- Memory: increase of the resident memory peak during the run. The measurement moves in steps of about 128 KB, so values of 0.1 MB or less are at its resolution.
