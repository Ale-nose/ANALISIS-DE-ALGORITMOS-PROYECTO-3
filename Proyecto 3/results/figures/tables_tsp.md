# TSP: result tables

## Experiment setup

- Experiment 1 instance: fixed_n30_s777
- Experiment 2 instances: scale_n100_s9100, scale_n10_s9010, scale_n11_s9011, scale_n12_s9012, scale_n13_s9013, scale_n14_s9014, scale_n16_s9016, scale_n18_s9018, scale_n20_s9020, scale_n30_s9030, scale_n50_s9050, scale_n6_s9006, scale_n8_s9008, scale_n9_s9009
- Seeds: 42, 101, 2026
- Fitness evaluations per run: 20000

## Sensitivity to each parameter (one parameter at a time)

| Parameter | Best value (mean) | Worst value (mean) | Difference between means |
|---|---|---|---|
| Crossover | OX (524.67) | PMX (597.33) | 72.67 |
| Mutation rate | 0.4 (523.67) | 0.05 (587.67) | 64 |
| Selection | Tournament (524.67) | Ranking (580.33) | 55.67 |
| Mutation | Inversion (475.67) | Swap (524.67) | 49.00 |
| Elitism | 0 (512.33) | 5 (559.33) | 47 |
| Population | 200 (513.33) | 50 (549.33) | 36 |
| Crossover rate | 0.8 (524.67) | 0.6 (549) | 24.33 |

## Best combinations (Experiment 1)

| Rank | Configuration | Mean | Standard deviation | Runs |
|---|---|---|---|---|
| 1 | `combo__p20__tournament__ox__inversion__cr0.95__mr0.4__el0` | 447.67 | 0.58 | 3 |
| 2 | `combo__p20__roulette__ox__inversion__cr0.95__mr0.2__el2` | 447.67 | 0.58 | 3 |
| 3 | `combo__p200__tournament__ox__inversion__cr0.95__mr0.2__el2` | 454 | 6.56 | 3 |
| 4 | `combo__p20__tournament__pmx__inversion__cr0.95__mr0.4__el2` | 455.67 | 13.28 | 3 |
| 5 | `combo__p20__roulette__ox__inversion__cr0.95__mr0.4__el2` | 455.67 | 8.02 | 3 |

Configuration used in Experiment 2: `combo__p20__tournament__ox__inversion__cr0.95__mr0.4__el0`

## Experiment 2: genetic algorithm vs exhaustive recursion and DP

| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |
|---|---|---|---|---|---|---|
| 6 | Exhaustive | ok | 248 | - | 0.0002 | 0.1 |
| 6 | DP | ok | 248 | - | 0.0011 | 0.1 |
| 6 | Genetic (mean ± std) | ok | 248 ± 0.00 | 0 | 0.33 | 1.0 |
| 8 | Exhaustive | ok | 310 | - | 0.02 | 0.1 |
| 8 | DP | ok | 310 | - | 0.0038 | 0.1 |
| 8 | Genetic (mean ± std) | ok | 310 ± 0.00 | 0 | 0.26 | 1.0 |
| 9 | Exhaustive | ok | 261 | - | 0.07 | 0.1 |
| 9 | DP | ok | 261 | - | 0.0038 | 0.1 |
| 9 | Genetic (mean ± std) | ok | 261 ± 0.00 | 0 | 0.29 | 0.2 |
| 10 | Exhaustive | ok | 312 | - | 0.37 | 0.1 |
| 10 | DP | ok | 312 | - | 0.0080 | 0.1 |
| 10 | Genetic (mean ± std) | ok | 312 ± 0.00 | 0 | 0.23 | 0.2 |
| 11 | Exhaustive | ok | 288 | - | 4.04 | 0.1 |
| 11 | DP | ok | 288 | - | 0.04 | 0.1 |
| 11 | Genetic (mean ± std) | ok | 288 ± 0.00 | 0 | 0.24 | 0.2 |
| 12 | Exhaustive | ok | 312 | - | 42.22 | 0.1 |
| 12 | DP | ok | 312 | - | 0.04 | 0.9 |
| 12 | Genetic (mean ± std) | ok | 312 ± 0.00 | 0 | 0.23 | 0.2 |
| 13 | Exhaustive | ok | 304 | - | 582.16 | 0.1 |
| 13 | DP | ok | 304 | - | 0.08 | 1.8 |
| 13 | Genetic (mean ± std) | ok | 304 ± 0.00 | 0 | 0.25 | 0.2 |
| 14 | Exhaustive | time limit | - | - | 600.00 | - |
| 14 | DP | ok | 314 | - | 0.33 | 5.0 |
| 14 | Genetic (mean ± std) | ok | 317.33 ± 5.77 | +3.33 | 0.24 | 0.2 |
| 16 | Exhaustive | skipped | - | - | - | - |
| 16 | DP | ok | 361 | - | 1.11 | 34.4 |
| 16 | Genetic (mean ± std) | ok | 361 ± 0.00 | 0 | 0.24 | 0.2 |
| 18 | Exhaustive | skipped | - | - | - | - |
| 18 | DP | ok | 340 | - | 5.46 | 153.1 |
| 18 | Genetic (mean ± std) | ok | 342 ± 2.65 | +2 | 0.29 | 0.2 |
| 20 | Exhaustive | skipped | - | - | - | - |
| 20 | DP | ok | 356 | - | 31.27 | 718.7 |
| 20 | Genetic (mean ± std) | ok | 356 ± 0.00 | 0 | 0.32 | 0.2 |
| 30 | Exhaustive | skipped | - | - | - | - |
| 30 | DP | ended without a result (probably memory) | - | - | - | - |
| 30 | Genetic (mean ± std) | ok | 492 ± 6.08 | - | 0.39 | 0.3 |
| 50 | Exhaustive | skipped | - | - | - | - |
| 50 | DP | skipped | - | - | - | - |
| 50 | Genetic (mean ± std) | ok | 693 ± 8.54 | - | 0.35 | 0.2 |
| 100 | Exhaustive | skipped | - | - | - | - |
| 100 | DP | skipped | - | - | - | - |
| 100 | Genetic (mean ± std) | ok | 1701 ± 131.33 | - | 0.54 | 0.2 |

- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.
- Skipped: the method had already reached its limit at a smaller size.
- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the error text; for an exact method this happens when it reaches the memory limit.
- Memory: increase of the resident memory peak during the run. The measurement moves in steps of about 128 KB, so values of 0.1 MB or less are at its resolution.
