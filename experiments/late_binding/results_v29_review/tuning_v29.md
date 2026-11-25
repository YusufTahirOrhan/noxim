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

Not run yet.
