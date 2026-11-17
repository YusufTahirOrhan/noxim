# v28 Part B: tuning of the early family, `EB_best64` and `EB_down_t` (experiments_v28.py b_rule, b_tune, b_choose)

## The rule (written before any tuning run)

* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged: pipe_all 2, DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3
  takes the 4x4 choice); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet); the ladder
  indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds. 80 runs per configuration.
* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where
  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.
  DeFT-P scores 0. DeFT-P and the main row are the runs of `results_v27_early/tune_runs.csv` (reproduced by this build, `repro_v27.md`).
* **B1, the early family** EBf(S, P, B, T), cost(e) = hops(e) + B (occ_S(e) + P pending(e)) + B T [e is not DeFT-P's entry VL]: S in {vl, route} x P in
  {0, 1} x B in {0.5, 1, 2, 4} x T in {0, 2, 4, 8, 16} (`oracle_bias` = B x T). The 8 configurations with P = 0 and T = 0 are rows of
  `results_v27_early/tune_runs.csv` (`EB_vl_b<B>`, `EB_route_b<B>`) and are taken from there; so is any configuration with P = 0 and T = 0 that an
  extension adds, if round 27 ran its B.
  * Extension, per size and sub-family (S, P): if its best configuration has the largest T run so far (16 at first), T is doubled (32, 64, 128 at most),
    one value at a time, for every B of the sub-family, until the best T is no longer the largest. If its best B is 0.5 or 4, B / 2 or 2 B is added for
    every T of the sub-family, once per sub-family. The best configuration of a set is the one with the largest score; of two equal scores, the one
    with the larger T.
  * **`EB_best`** per size = the configuration with a finite T that has the largest score over the four sub-families (of two equal scores, the larger T).
    If its score is below 0, the best member of the family is DeFT_P itself (T = infinity): that is said first in the answer to question 2, the finite
    configuration stays `EB_best` so that there is a row to run, and every share is also reported against the better of `EB_best` and DeFT_P.
* **B2, `EB_best64`:** S, P and B of `EB_best` (per size), `oracle_period 64`, T in {0, 2, 4, 8, 16, 32}; if the best T is the largest, it is doubled
  (64, 128 at most), one value at a time. The choice as for `EB_best`.
* **B3, `EB_down_t`:** `EB_down` of round 27 with `lut_bias` D in {0, 1, 2, 4, 8, 16}, everything else the frozen main row; if the best D is 16, 32 is added,
  and 64 if then 32 is the best. A `lut_bias` of infinity is DeFT_P's routing (anchor gate). Of two equal scores, the larger D; a best score below 0 is
  treated as for `EB_best`.
* B3 does not depend on B1, so its runs share the batches of B1 (grid and extension steps); B2 starts when B1 is complete.
* Runs: 72 x 80 = 5,760 (B1 grid) + 480 (B2 grid) + 480 (B3 grid) + 40 per configuration and size of an extension. The main row is not tuned; its score
  is reported next to the others (from the runs of round 27).

## Results

Not run yet.
