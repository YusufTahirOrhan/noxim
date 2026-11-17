# A2: round 27 reproduced by the build of this round (experiments_v28.py a2_repro)

The two rows of `results_v27_early/tune_runs.csv` that the prompt names, run with the arguments of this round at `oracle_pending 0` and
`oracle_bias 0` (given explicitly): `EB_vl_b1` = EBf(vl, 0, 1, 0) and `EB_route_b4` = EBf(route, 0, 4, 0). Also DeFT_P and the main row, whose
runs of that file give every tuning score of this round its denominator and the main row's score. All 40 tuning cells of 2x2 and of 4x4 (five
scenarios, loads 0.5, 1.0, 1.4, 2.0 x Lsat, seeds 101 and 102). Compared: every column of that file, as text.

| size | row | runs | identical |
|---|---|---|---|
| 2x2 | CI_heurLA_X_LF | 40 | 40 |
| 2x2 | DeFT_P | 40 | 40 |
| 2x2 | EB_route_b4 | 40 | 40 |
| 2x2 | EB_vl_b1 | 40 | 40 |
| 4x4 | CI_heurLA_X_LF | 40 | 40 |
| 4x4 | DeFT_P | 40 | 40 |
| 4x4 | EB_route_b4 | 40 | 40 |
| 4x4 | EB_vl_b1 | 40 | 40 |

**320 / 320 runs identical.**
