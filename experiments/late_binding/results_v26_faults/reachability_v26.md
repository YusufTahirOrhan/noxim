# v26 B5: reachability of MTR and RC under VL faults (reach_v26.py; static analysis, no simulation)

The analysis of `reach_v10.py`, unchanged, with the rate 8/16 added. A pair is delivered if a legal path exists under the method: MTR with the turn
restrictions the MTR runs use (`results_v10/mtr_config.json`, md5 12a9126db0b2d898d811ad48fd21164c), a source using any functional boundary router it can reach and a destination
being entered through any functional boundary router that can reach it; RC with its permission tree, a source using only the RC buffer of its nearest
boundary router. Share = delivered inter-chiplet (source, destination) pairs over all inter-chiplet pairs. Masks: up to 1,000 random masks per (size, rate) with
exactly n faulty VLs and a functional VL in every chiplet (rates 1/16 to 4/16: the masks of `reach_v10.py`; 8/16: `random.Random(2611)`), and the 16 masks of
Part B.

Check: the 18 rows of the three old rates equal `results_v10/report/reachability.csv` (masks, mean and worst share): **18 of 18**.

## Inter-chiplet pairs delivered: mean (worst mask) over the masks

| size | rate | faulty VLs | method | random masks | mean (worst) | masks with every pair delivered | Part B masks: mean (worst) | masks with every pair delivered |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1/16 | 1 | MTR | 16 | 93.75 % (93.75 %) | 0 | 93.75 % (93.75 %) | 0 of 16 |
| 2x2 | 1/16 | 1 | RC | 16 | 93.75 % (93.75 %) | 0 | 93.75 % (93.75 %) | 0 of 16 |
| 2x2 | 2/16 | 2 | MTR | 120 | 87.50 % (87.50 %) | 0 | 87.50 % (87.50 %) | 0 of 16 |
| 2x2 | 2/16 | 2 | RC | 120 | 87.50 % (87.50 %) | 0 | 87.50 % (87.50 %) | 0 of 16 |
| 2x2 | 4/16 | 4 | MTR | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 2x2 | 4/16 | 4 | RC | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 2x2 | 8/16 | 8 | MTR | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
| 2x2 | 8/16 | 8 | RC | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
| 3x3 | 1/16 | 2 | MTR | 630 | 94.44 % (94.44 %) | 0 | 94.44 % (94.44 %) | 0 of 16 |
| 3x3 | 1/16 | 2 | RC | 630 | 94.44 % (94.44 %) | 0 | 94.44 % (94.44 %) | 0 of 16 |
| 3x3 | 2/16 | 4 | MTR | 1000 | 88.89 % (88.89 %) | 0 | 88.89 % (88.89 %) | 0 of 16 |
| 3x3 | 2/16 | 4 | RC | 1000 | 88.89 % (88.89 %) | 0 | 88.89 % (88.89 %) | 0 of 16 |
| 3x3 | 4/16 | 9 | MTR | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 3x3 | 4/16 | 9 | RC | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 3x3 | 8/16 | 18 | MTR | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
| 3x3 | 8/16 | 18 | RC | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
| 4x4 | 1/16 | 4 | MTR | 1000 | 93.75 % (93.75 %) | 0 | 93.75 % (93.75 %) | 0 of 16 |
| 4x4 | 1/16 | 4 | RC | 1000 | 93.75 % (93.75 %) | 0 | 93.75 % (93.75 %) | 0 of 16 |
| 4x4 | 2/16 | 8 | MTR | 1000 | 87.50 % (87.50 %) | 0 | 87.50 % (87.50 %) | 0 of 16 |
| 4x4 | 2/16 | 8 | RC | 1000 | 87.50 % (87.50 %) | 0 | 87.50 % (87.50 %) | 0 of 16 |
| 4x4 | 4/16 | 16 | MTR | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 4x4 | 4/16 | 16 | RC | 1000 | 75.00 % (75.00 %) | 0 | 75.00 % (75.00 %) | 0 of 16 |
| 4x4 | 8/16 | 32 | MTR | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
| 4x4 | 8/16 | 32 | RC | 1000 | 50.00 % (50.00 %) | 0 | 50.00 % (50.00 %) | 0 of 16 |
