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

Not run yet.
