# Rod cutting: result tables

## Experiment setup

- Experiment 1 instance: fixed_n30_s777
- Experiment 2 instances: scale_n1000_s10000, scale_n100_s9100, scale_n10_s9010, scale_n128000_s137000, scale_n15_s9015, scale_n16000_s25000, scale_n181000_s190000, scale_n20_s9020, scale_n24_s9024, scale_n26_s9026, scale_n28_s9028, scale_n30_s9030, scale_n31_s9031, scale_n32000_s41000, scale_n32_s9032, scale_n33_s9033, scale_n34_s9034, scale_n4000_s13000, scale_n64000_s73000, scale_n90000_s99000
- Seeds: 42, 101, 2026
- Fitness evaluations per run: 20000

## Sensitivity to each parameter (one parameter at a time)

| Parameter | Best value (mean) | Worst value (mean) | Difference between means |
|---|---|---|---|
| Population | 100 (86) | 20 (77) | 9 |
| Selection | Tournament (86) | Ranking (83) | 3 |
| Mutation rate | 0.2 (86.67) | 0.01 (83.67) | 3 |
| Elitism | 2 (86) | 0 (83.67) | 2.33 |
| Crossover rate | 0.8 (86) | 0.95 (84) | 2 |
| Crossover | Uniform (87.33) | 2-point (85.33) | 2 |
| Mutation | σ=0.2 (86.67) | σ=0.05 (85) | 1.67 |

## Best combinations (Experiment 1)

| Rank | Configuration | Mean | Standard deviation | Runs |
|---|---|---|---|---|
| 1 | `combo__p100__roulette__uniform__gaussian_s0.2__cr0.8__mr0.05__el2` | 88 | 0.00 | 3 |
| 2 | `combo__p100__roulette__uniform__gaussian_s0.1__cr0.8__mr0.2__el2` | 88 | 0.00 | 3 |
| 3 | `combo__p100__roulette__uniform__gaussian_s0.1__cr0.6__mr0.05__el2` | 88 | 0.00 | 3 |
| 4 | `combo__p100__roulette__arithmetic__gaussian_s0.2__cr0.8__mr0.2__el2` | 88 | 0.00 | 3 |
| 5 | `combo__p400__tournament__uniform__gaussian_s0.2__cr0.8__mr0.2__el5` | 88 | 0.00 | 3 |

Configuration used in Experiment 2: `combo__p100__roulette__uniform__gaussian_s0.2__cr0.8__mr0.05__el2`

## Experiment 2: genetic algorithm vs exhaustive recursion and DP

| Size | Method | Status | Value | Difference to the optimum | Time [s] | Memory [MB] |
|---|---|---|---|---|---|---|
| 10 | Exhaustive | ok | 28 | - | 0.0003 | 0.2 |
| 10 | DP | ok | 28 | - | 0.0001 | 0.0 |
| 10 | Genetic (mean ± std) | ok | 28 ± 0.00 | 0 | 0.59 | 2.7 |
| 15 | Exhaustive | ok | 42 | - | 0.0096 | 0.2 |
| 15 | DP | ok | 42 | - | 0.0001 | 0.0 |
| 15 | Genetic (mean ± std) | ok | 41.33 ± 1.15 | -0.67 | 0.60 | 1.2 |
| 20 | Exhaustive | ok | 60 | - | 0.33 | 0.2 |
| 20 | DP | ok | 60 | - | 0.0001 | 0.0 |
| 20 | Genetic (mean ± std) | ok | 59.33 ± 0.58 | -0.67 | 0.63 | 0.8 |
| 24 | Exhaustive | ok | 67 | - | 4.98 | 0.2 |
| 24 | DP | ok | 67 | - | 0.0001 | 0.0 |
| 24 | Genetic (mean ± std) | ok | 67 ± 0.00 | 0 | 0.65 | 0.8 |
| 26 | Exhaustive | ok | 78 | - | 19.89 | 0.2 |
| 26 | DP | ok | 78 | - | 0.0001 | 0.0 |
| 26 | Genetic (mean ± std) | ok | 78 ± 0.00 | 0 | 0.67 | 0.8 |
| 28 | Exhaustive | ok | 83 | - | 79.28 | 0.2 |
| 28 | DP | ok | 83 | - | 0.0001 | 0.0 |
| 28 | Genetic (mean ± std) | ok | 80.33 ± 2.52 | -2.67 | 0.67 | 0.8 |
| 30 | Exhaustive | ok | 78 | - | 319.83 | 0.2 |
| 30 | DP | ok | 78 | - | 0.0001 | 0.0 |
| 30 | Genetic (mean ± std) | ok | 68.67 ± 4.51 | -9.33 | 0.67 | 0.8 |
| 31 | Exhaustive | time limit | - | - | 600.00 | - |
| 31 | DP | ok | 93 | - | 0.0001 | 0.0 |
| 31 | Genetic (mean ± std) | ok | 93 ± 0.00 | 0 | 0.68 | 0.8 |
| 32 | Exhaustive | skipped | - | - | - | - |
| 32 | DP | ok | 96 | - | 0.0001 | 0.0 |
| 32 | Genetic (mean ± std) | ok | 96 ± 0.00 | 0 | 0.69 | 0.8 |
| 33 | Exhaustive | skipped | - | - | - | - |
| 33 | DP | ok | 99 | - | 0.0001 | 0.0 |
| 33 | Genetic (mean ± std) | ok | 97.33 ± 0.58 | -1.67 | 0.69 | 0.8 |
| 34 | Exhaustive | skipped | - | - | - | - |
| 34 | DP | ok | 89 | - | 0.0001 | 0.0 |
| 34 | Genetic (mean ± std) | ok | 87.67 ± 1.53 | -1.33 | 0.69 | 0.8 |
| 100 | Exhaustive | skipped | - | - | - | - |
| 100 | DP | ok | 291 | - | 0.0010 | 0.0 |
| 100 | Genetic (mean ± std) | ok | 248.67 ± 7.77 | -42.33 | 0.98 | 0.8 |
| 1000 | Exhaustive | skipped | - | - | - | - |
| 1000 | DP | ok | 3000 | - | 0.16 | 0.1 |
| 1000 | Genetic (mean ± std) | ok | 2542.67 ± 12.34 | -457.33 | 5.74 | 2.3 |
| 4000 | Exhaustive | skipped | - | - | - | - |
| 4000 | DP | ok | 11997 | - | 2.58 | 1.0 |
| 4000 | Genetic (mean ± std) | ok | 7378.67 ± 26.01 | -4618.33 | 21.75 | 17.1 |
| 16000 | Exhaustive | skipped | - | - | - | - |
| 16000 | DP | ok | 47991 | - | 41.98 | 4.1 |
| 16000 | Genetic (mean ± std) | ok | 32941 ± 41.51 | -15050 | 100.38 | 75.5 |
| 32000 | Exhaustive | skipped | - | - | - | - |
| 32000 | DP | ok | 96000 | - | 162.38 | 8.4 |
| 32000 | Genetic (mean ± std) | ok | 82309.67 ± 30.92 | -13690.33 | 214.32 | 148.7 |
| 64000 | Exhaustive | skipped | - | - | - | - |
| 64000 | DP | time limit | - | - | 600.00 | - |
| 64000 | Genetic (mean ± std) | ok | 118354.67 ± 100.28 | - | 450.57 | 300.0 |
| 90000 | Exhaustive | skipped | - | - | - | - |
| 90000 | DP | skipped | - | - | - | - |
| 90000 | Genetic (mean ± std) | ok | 184048.67 ± 100.71 | - | 641.90 | 422.9 |
| 128000 | Exhaustive | skipped | - | - | - | - |
| 128000 | DP | skipped | - | - | - | - |
| 128000 | Genetic (mean ± std) | ok | 296736.33 ± 78.14 | - | 924.29 | 602.8 |
| 181000 | Exhaustive | skipped | - | - | - | - |
| 181000 | DP | skipped | - | - | - | - |
| 181000 | Genetic (mean ± std) | ok | 377015 ± 43.49 | - | 1314.85 | 854.1 |

- Difference to the optimum: mean of the genetic algorithm minus the value of the exact method on the same instance (only where an exact method finished). Zero means the genetic algorithm found the optimum.
- Skipped: the method had already reached its limit at a smaller size.
- Ended without a result and error: the CSV (column `message`) only keeps the exit code or the error text; for an exact method this happens when it reaches the memory limit.
- Memory: increase of the resident memory peak during the run. The measurement moves in steps of about 128 KB, so values of 0.1 MB or less are at its resolution.
