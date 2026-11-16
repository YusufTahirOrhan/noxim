# v27 Part B: tuning of `oracle_beta` (experiments_v27.py b_rule, b_tune, b_choose)

## The rule (written before any tuning run)

* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged: pipe_all 2, DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3
  takes the 4x4 value); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet); the ladder
  indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds.
* **Grid.** `oracle_beta` in {0.125, 0.25, 0.5, 1, 2, 4, 8}, separately for `EB_vl`, `EB_route` and `EB_vl64`.
* **Score** of a value on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where
  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.
* **Choice:** per row and size, the value with the largest score. If it lies at an end of the grid, the grid is extended at that end by factors of 2, one value
  at a time, at most three times, until the largest score is no longer at the end.
* **Also run and reported, not tuned:** the main row `CI_heurLA_X_LF` with its frozen parameters on the same loads and seeds (it was tuned by the same rule in
  round 24, with an ideal decision; here it runs as the row is defined, with the lookahead mechanism).
* `EB_down` and `LB_noVLrep` take the frozen parameters of the main row. Nothing is tuned for them.
* Runs: 3 rows x 7 values x 2 sizes x 5 scenarios x 4 loads x 2 seeds = 1,680, plus 80 for DeFT-P and 80 for the main row, plus 40 per extension step of a row on a size.

## Results

Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P
(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better).

### 2x2

| row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|---|
| `CI_heurLA_X_LF` (frozen, not tuned here) | | 0.5303 | +10.6 % | -33.4 % | -2.3 % | |
| `EB_vl` | 0.125 | -1.3330 | -13.9 % | +210.0 % | +5.3 % |  |
| `EB_vl` | 0.25 | -0.9759 | -9.5 % | +131.1 % | +3.9 % |  |
| `EB_vl` | 0.5 | -0.8928 | -8.7 % | +115.7 % | +3.4 % | **chosen** |
| `EB_vl` | 1 | -1.0738 | -10.7 % | +148.7 % | +5.1 % |  |
| `EB_vl` | 2 | -1.2799 | -12.1 % | +188.6 % | +9.6 % |  |
| `EB_vl` | 4 | -1.4388 | -13.2 % | +223.6 % | +13.1 % |  |
| `EB_vl` | 8 | -1.4704 | -13.0 % | +226.6 % | +15.9 % |  |
| `EB_route` | 0.125 | -1.1987 | -11.4 % | +184.4 % | +3.2 % |  |
| `EB_route` | 0.25 | -0.8561 | -8.4 % | +109.8 % | +2.7 % |  |
| `EB_route` | 0.5 | -0.6705 | -6.5 % | +76.2 % | +3.8 % |  |
| `EB_route` | 1 | -0.6511 | -6.3 % | +70.2 % | +5.6 % |  |
| `EB_route` | 2 | -0.5969 | -6.1 % | +58.9 % | +7.4 % | **chosen** |
| `EB_route` | 4 | -0.6544 | -6.1 % | +64.6 % | +9.8 % |  |
| `EB_route` | 8 | -0.6209 | -6.4 % | +58.6 % | +9.8 % |  |
| `EB_vl64` | 0.125 | -1.4434 | -14.4 % | +237.0 % | +7.6 % |  |
| `EB_vl64` | 0.25 | -1.0938 | -10.5 % | +149.9 % | +6.9 % | **chosen** |
| `EB_vl64` | 0.5 | -1.1917 | -10.9 % | +171.5 % | +8.1 % |  |
| `EB_vl64` | 1 | -1.6171 | -14.0 % | +289.2 % | +11.4 % |  |
| `EB_vl64` | 2 | -1.7618 | -15.1 % | +313.4 % | +19.5 % |  |
| `EB_vl64` | 4 | -1.9391 | -16.1 % | +353.2 % | +28.8 % |  |
| `EB_vl64` | 8 | -1.9961 | -16.1 % | +366.0 % | +32.6 % |  |

### 4x4

| row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | note |
|---|---|---|---|---|---|---|
| `CI_heurLA_X_LF` (frozen, not tuned here) | | 0.6479 | +17.5 % | -37.3 % | -2.0 % | |
| `EB_vl` | 0.125 | -1.5675 | -21.2 % | +256.5 % | +5.9 % |  |
| `EB_vl` | 0.25 | -1.5196 | -19.2 % | +251.2 % | +5.1 % |  |
| `EB_vl` | 0.5 | -1.3498 | -14.8 % | +215.3 % | +4.2 % |  |
| `EB_vl` | 1 | -1.2761 | -13.4 % | +201.2 % | +3.0 % | **chosen** |
| `EB_vl` | 2 | -1.3231 | -13.6 % | +212.4 % | +3.9 % |  |
| `EB_vl` | 4 | -1.3293 | -15.5 % | +203.7 % | +5.1 % |  |
| `EB_vl` | 8 | -1.3303 | -14.7 % | +203.1 % | +6.4 % |  |
| `EB_route` | 0.125 | -0.5539 | -5.7 % | +62.3 % | +1.1 % |  |
| `EB_route` | 0.25 | -0.3373 | -2.0 % | +35.5 % | +1.3 % |  |
| `EB_route` | 0.5 | -0.1896 | +0.2 % | +18.7 % | +2.1 % |  |
| `EB_route` | 1 | -0.1618 | +1.4 % | +15.5 % | +3.2 % |  |
| `EB_route` | 2 | -0.1187 | +1.4 % | +9.3 % | +4.4 % |  |
| `EB_route` | 4 | -0.1160 | +2.1 % | +8.9 % | +5.3 % | **chosen** |
| `EB_route` | 8 | -0.1282 | +2.1 % | +9.5 % | +6.0 % |  |
| `EB_vl64` | 0.125 | -1.5678 | -21.0 % | +254.5 % | +6.8 % |  |
| `EB_vl64` | 0.25 | -1.5323 | -19.4 % | +247.6 % | +7.4 % |  |
| `EB_vl64` | 0.5 | -1.4365 | -15.8 % | +232.5 % | +6.6 % |  |
| `EB_vl64` | 1 | -1.4062 | -14.4 % | +232.7 % | +5.0 % | **chosen** |
| `EB_vl64` | 2 | -1.4384 | -16.1 % | +229.4 % | +7.3 % |  |
| `EB_vl64` | 4 | -1.4770 | -16.1 % | +234.6 % | +9.8 % |  |
| `EB_vl64` | 8 | -1.5314 | -16.4 % | +245.4 % | +11.9 % |  |

## Chosen values

| size | `EB_vl` | `EB_route` | `EB_vl64` | score of the main row |
|---|---|---|---|---|
| 2x2 | 0.5 (score -0.8928) | 2 (score -0.5969) | 0.25 (score -1.0938) | 0.5303 |
| 3x3 (the 4x4 values) | 1 (score -1.2761) | 4 (score -0.1160) | 1 (score -1.4062) | 0.6479 |
| 4x4 | 1 (score -1.2761) | 4 (score -0.1160) | 1 (score -1.4062) | 0.6479 |

Grid extensions: none.
Chosen value still at an end of what was run (after three extension steps): none.
Hops of the `EB` tuning runs that offer more than one output (must be 0): 0.
Per-run values: `tune_runs.csv`.
