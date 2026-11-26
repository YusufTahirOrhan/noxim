# v29 Part F: tuning of `EB_first`, `EB_best16` and `EB_best256` (experiments_v29.py f_rule, f1_tune, f1_choose, f2_tune, f2_choose)

## The rule (written before any tuning run of this round)

* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged, as rounds 27 and 28 applied it to their early rows: pipe_all 2, DeFT-P VN options,
  `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3 takes the 4x4 choice); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and
  uniform with one faulty VL per chiplet); the ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102. 80 runs per
  configuration.
* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where
  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.
  DeFT-P scores 0. DeFT-P and the main row are run again on the 80 tuning cells with the build of this round (160 runs); their rows must equal those of
  `results_v27_early/tune_runs.csv`, which gave rounds 27 and 28 their scores.
* **F1, `EB_first`:** the main row with `entry_commit first` and `lut_bias` D in {0, 1, 2, 4, 8}, everything else the frozen main row. If the best D is 8, 16 is
  added, then 32 and 64 (at most), one value at a time, until the best D is no longer the largest (the extension rule of `EB_down_t` in round 28). The choice
  per size: the D with the largest score; of two equal scores, the larger D. A `lut_bias` of infinity is DeFT_P's routing (`anchor_first.md`); if the best
  score is below 0, the best member of the family is DeFT_P itself: that is said first where the row is reported, the finite D stays `EB_first` so that there
  is a row to run, and every share is also reported against the better of `EB_first` and DeFT_P.
* **F2, `EB_best16` and `EB_best256`:** S, P and B of `EB_best` (per size, `results_v28_anchor/tuning_choice_v28.json`), `oracle_period` 16 or 256, T in
  {0, 2, 4, 8, 16, 32}; if the best T is the largest, it is doubled (64, 128 at most), one value at a time (B2 of round 28, unchanged). The choice as for
  `EB_best64` there: the largest score; of two equal scores, the larger T; a best score below 0 is treated as for `EB_first`.
* Runs: F1 5 x 80 = 400, plus the 160 runs of DeFT-P and the main row; F2 2 x 6 x 80 = 960; 40 per value and size that an extension adds. (The prompt gives
  800 runs for F1; the grid of five values on two sizes is 400 by this rule. See `DECISIONS.md`.) The main row is not tuned; its score is reported next to the
  others.

## Results

Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P
(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better). DeFT-P scores 0.

### 2x2: F1, `EB_first` (`entry_commit first` with `lut_bias` D)

| D | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| `CI_heurLA_X_LF` (frozen, not tuned here) | 0.5303 | +10.6 % | -33.4 % | -2.3 % | |
| DeFT_P (D = infinity) | 0 | 0 | 0 | 0 | |
| 0 | -0.2402 | +3.1 % | +28.4 % | +2.0 % |  |
| 1 | -0.0218 | +4.7 % | +9.0 % | -1.8 % |  |
| 2 | 0.1878 | +6.3 % | -10.3 % | -1.8 % |  |
| 4 | 0.3322 | +7.8 % | -22.1 % | -0.8 % | **EB_first** |
| 8 | 0.3006 | +6.9 % | -20.6 % | -0.3 % |  |

### 2x2: F2, `EB_best16` (S vl, P 1, B 0.5 of `EB_best`, `oracle_period 16`)

| T | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| 0 | 0.3701 | +8.1 % | -26.4 % | +1.4 % |  |
| 2 | 0.4057 | +8.8 % | -27.6 % | +0.1 % |  |
| 4 | 0.4437 | +9.4 % | -29.3 % | -0.7 % |  |
| 8 | 0.4827 | +10.3 % | -30.7 % | -1.8 % |  |
| 16 | 0.4901 | +10.6 % | -31.1 % | -1.7 % | **EB_best16** |
| 32 | 0.4186 | +9.3 % | -27.6 % | -0.7 % |  |

### 2x2: F2, `EB_best256` (S vl, P 1, B 0.5 of `EB_best`, `oracle_period 256`)

| T | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| 0 | -2.3421 | -17.6 % | +488.9 % | +45.6 % |  |
| 2 | -2.2681 | -17.0 % | +479.6 % | +38.3 % |  |
| 4 | -2.1705 | -17.0 % | +442.8 % | +34.0 % |  |
| 8 | -2.0424 | -16.3 % | +419.1 % | +24.3 % |  |
| 16 | -1.8063 | -15.6 % | +372.4 % | +8.8 % |  |
| 32 | -1.4549 | -12.9 % | +272.5 % | +0.1 % |  |
| 64 | -0.1918 | -2.3 % | +18.4 % | -0.1 % | extension |
| 128 | 0.1047 | +3.7 % | -6.5 % | -0.1 % | **EB_best256**, extension |

### 2x2: the chosen rows by scenario

Score of the scenario (mean over the two seeds) and, in brackets, THR and LAT1.0 against DeFT-P.

| row | configuration | uniform | hotspot | chipperm | chiptrans | uniform+f |
|---|---|---|---|---|---|---|
| main row | `CI_heurLA_X_LF` | +0.291 (+6.5 / -18.9) | +1.045 (+19.9 / -56.4) | +0.530 (+10.1 / -34.0) | +0.359 (+3.5 / -26.9) | +0.426 (+13.9 / -23.0) |
| `EB_first` | `EBfirst_D4` | +0.202 (+5.7 / -13.3) | +0.960 (+21.2 / -53.2) | +0.094 (+0.4 / -7.8) | +0.078 (+0.5 / -6.6) | +0.327 (+12.6 / -17.7) |
| `EB_best16` | `EBf16_vl_P1_B0.5_T16` | +0.277 (+7.9 / -16.9) | +1.061 (+22.4 / -56.7) | +0.438 (+7.8 / -29.4) | +0.291 (+2.3 / -22.8) | +0.384 (+13.8 / -20.5) |
| `EB_best256` | `EBf256_vl_P1_B0.5_T128` | +0.013 (-0.6 / -2.0) | +0.479 (+16.9 / -27.5) | -0.001 (-0.6 / -0.3) | -0.017 (+0.1 / +1.9) | +0.049 (+3.8 / -1.2) |

### 4x4: F1, `EB_first` (`entry_commit first` with `lut_bias` D)

| D | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| `CI_heurLA_X_LF` (frozen, not tuned here) | 0.6479 | +17.5 % | -37.3 % | -2.0 % | |
| DeFT_P (D = infinity) | 0 | 0 | 0 | 0 | |
| 0 | -0.0264 | +7.0 % | +10.0 % | -0.2 % |  |
| 1 | 0.1156 | +9.1 % | -0.7 % | -2.1 % |  |
| 2 | 0.2297 | +10.6 % | -10.6 % | -1.8 % |  |
| 4 | 0.3445 | +11.7 % | -20.4 % | -0.5 % | **EB_first** |
| 8 | 0.3220 | +10.0 % | -20.2 % | -0.1 % |  |

### 4x4: F2, `EB_best16` (S vl, P 1, B 1 of `EB_best`, `oracle_period 16`)

| T | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| 0 | 0.4042 | +11.8 % | -26.8 % | +2.0 % |  |
| 2 | 0.4219 | +11.8 % | -27.5 % | +1.1 % |  |
| 4 | 0.4356 | +11.8 % | -27.9 % | +0.3 % |  |
| 8 | 0.4584 | +12.0 % | -28.6 % | -0.8 % | **EB_best16** |
| 16 | 0.4265 | +11.7 % | -26.3 % | -1.0 % |  |
| 32 | 0.3524 | +10.8 % | -21.9 % | -0.2 % |  |

### 4x4: F2, `EB_best256` (S vl, P 1, B 1 of `EB_best`, `oracle_period 256`)

| T | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|
| 0 | -1.1285 | -4.7 % | +148.2 % | +18.7 % |  |
| 2 | -1.0586 | -4.2 % | +140.8 % | +14.7 % |  |
| 4 | -1.0364 | -4.6 % | +139.1 % | +12.5 % |  |
| 8 | -0.9394 | -3.9 % | +126.6 % | +8.5 % |  |
| 16 | -0.7738 | -2.9 % | +106.8 % | +1.8 % |  |
| 32 | -0.3837 | -0.5 % | +46.0 % | -0.0 % |  |
| 64 | 0.1521 | +6.1 % | -8.9 % | -0.0 % | **EB_best256**, extension |
| 128 | 0.0689 | +5.3 % | -1.7 % | -0.0 % | extension |

### 4x4: the chosen rows by scenario

Score of the scenario (mean over the two seeds) and, in brackets, THR and LAT1.0 against DeFT-P.

| row | configuration | uniform | hotspot | chipperm | chiptrans | uniform+f |
|---|---|---|---|---|---|---|
| main row | `CI_heurLA_X_LF` | +0.642 (+19.4 / -35.9) | +0.729 (+30.5 / -33.4) | +0.361 (+9.5 / -24.3) | +0.777 (+7.7 / -50.3) | +0.730 (+22.0 / -39.5) |
| `EB_first` | `EBfirst_D4` | +0.493 (+14.7 / -29.5) | +0.529 (+28.2 / -24.2) | +0.069 (+0.9 / -5.6) | +0.082 (+0.9 / -6.8) | +0.550 (+16.4 / -32.2) |
| `EB_best16` | `EBf16_vl_P1_B1_T8` | +0.465 (+10.7 / -30.2) | +0.670 (+28.5 / -32.3) | +0.323 (+8.4 / -21.9) | +0.325 (+2.2 / -25.9) | +0.509 (+11.8 / -32.1) |
| `EB_best256` | `EBf256_vl_P1_B1_T64` | +0.102 (+0.2 / -9.5) | +0.525 (+30.4 / -22.8) | +0.018 (-0.5 / -2.2) | -0.020 (-1.1 / +1.0) | +0.136 (+4.3 / -9.0) |

## Chosen configurations

| size | `EB_first`: lut_bias (score) | `EB_best16`: T (score) | `EB_best256`: T (score) | main row (score) |
|---|---|---|---|---|
| 2x2 | 4 (0.3322) | 16 (0.4901) | 128 (0.1047) | 0.5303 |
| 3x3 (the 4x4 choice) | 4 (0.3445) | 8 (0.4584) | 64 (0.1521) | 0.6479 |
| 4x4 | 4 (0.3445) | 8 (0.4584) | 64 (0.1521) | 0.6479 |

Chosen configurations with a score below 0 (DeFT_P is then the best member of the family): none.
DeFT-P and the main row on the tuning cells, run again with the build of this round, against the rows of `results_v27_early/tune_runs.csv` (every column, as text): **160 / 160 identical.**
Hops of the tuning runs of the early rows that offer more than one output after the commit (must be 0): 0. The same for the tuning runs of F2: 0.
Per-run values: `tune_first_runs.csv` (F1, with DeFT-P and the main row) and `tune_age_runs.csv` (F2).
