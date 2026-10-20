# v8 step 3: selection of the interposer hop weight gamma (4x4, seeds 101/102)

Grid: CI_heurLA, CI_qlLA, FULL_qlLA (v6 tuned parameters) x gamma (`hop_weight_ipos`) {1.25, 1.5, 2, 3}, extended by gamma = 4 where the choice was 3; gamma = 1 = the parents. Cells as v7 step 3: the 7 v5 scenarios of 4x4 x loads 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat x seeds 101/102 = 70 runs per configuration. Per-run data: select_runs.csv (column source).

Parents: the CI_heurLA and CI_qlLA rows are reused from results_v7/select_runs.csv (same cells, same seeds; the binary with gamma = 1 is identical to v7, regression.md). Spot check of the reuse, 4 parent cells re-run with the v8 binary: CI_heurLA uniform 0x0 load 3 seed 101: identical; CI_heurLA chipperm 0x0 load 6 seed 102: identical; CI_qlLA hotspot 0x0 load 4 seed 101: identical; CI_qlLA uniform 0x1111111111111111 load 2 seed 102: identical. FULL_qlLA (not in v7) was run.

Criterion (fixed in the task): maximise THR = geometric mean over the 7 scenarios of the saturation throughput (max accepted over the 5 loads, mean over the 2 seeds), subject to LAT = geometric mean over the scenarios of the mean latency at 1.0 x Lsat (mean over the 2 seeds) at most 5 % above the parent's. Ties (THR within 0.5 % of the best feasible): lower LAT, then smaller gamma.

## CI_heurLA

| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | feasible | runs | dead ends |
|---|---|---|---|---|---|---|---|
| CI_heurLA (parent, gamma 1) | 0.03356 | +0.00 % | 59.20 | +0.00 % | - | 70 | 0 |
| CI_heurLA-g1.25 | 0.03300 | -1.66 % | 58.56 | -1.07 % | yes | 70 | 0 |
| CI_heurLA-g1.5 | 0.03421 | +1.94 % | 58.24 | -1.62 % | yes | 70 | 0 |
| CI_heurLA-g2.0 **(chosen)** | 0.03473 | +3.50 % | 59.28 | +0.14 % | yes | 70 | 0 |
| CI_heurLA-g3.0 | 0.03566 | +6.26 % | 63.29 | +6.90 % | no | 70 | 0 |

Chosen for CI_heurLA_G: gamma **2.0** (within 0.5 % of the best feasible THR: CI_heurLA-g2.0)

Per scenario (CI_heurLA, parent vs chosen): saturation throughput / latency at 1.0 x Lsat

| scenario | THR parent | THR chosen | LAT parent | LAT chosen |
|---|---|---|---|---|
| uniform  | 0.05212 | 0.05630 | 62.3 | 62.6 |
| localized  | 0.08312 | 0.08751 | 46.3 | 45.1 |
| hotspot  | 0.01838 | 0.01925 | 56.1 | 51.9 |
| chipperm  | 0.02854 | 0.02852 | 67.1 | 68.2 |
| movinghot  | 0.02363 | 0.02389 | 86.3 | 92.3 |
| uniform 0x1111111111111111 | 0.04751 | 0.05108 | 56.0 | 57.4 |
| hotspot 0x1111111111111111 | 0.01879 | 0.01848 | 48.6 | 48.6 |

## CI_qlLA

| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | feasible | runs | dead ends |
|---|---|---|---|---|---|---|---|
| CI_qlLA (parent, gamma 1) | 0.03433 | +0.00 % | 59.05 | +0.00 % | - | 70 | 0 |
| CI_qlLA-g1.25 | 0.03570 | +4.00 % | 56.23 | -4.78 % | yes | 70 | 0 |
| CI_qlLA-g1.5 | 0.03551 | +3.44 % | 56.84 | -3.75 % | yes | 70 | 0 |
| CI_qlLA-g2.0 **(chosen)** | 0.03690 | +7.47 % | 59.60 | +0.93 % | yes | 70 | 0 |
| CI_qlLA-g3.0 | 0.03703 | +7.85 % | 63.68 | +7.84 % | no | 70 | 0 |

Chosen for CI_qlLA_G: gamma **2.0** (within 0.5 % of the best feasible THR: CI_qlLA-g2.0)

Per scenario (CI_qlLA, parent vs chosen): saturation throughput / latency at 1.0 x Lsat

| scenario | THR parent | THR chosen | LAT parent | LAT chosen |
|---|---|---|---|---|
| uniform  | 0.05550 | 0.06378 | 59.6 | 60.0 |
| localized  | 0.08357 | 0.09653 | 44.3 | 43.8 |
| hotspot  | 0.01870 | 0.01880 | 59.5 | 58.3 |
| chipperm  | 0.02901 | 0.03141 | 60.1 | 68.2 |
| movinghot  | 0.02382 | 0.02460 | 88.8 | 85.5 |
| uniform 0x1111111111111111 | 0.05184 | 0.05566 | 53.9 | 54.7 |
| hotspot 0x1111111111111111 | 0.01809 | 0.01870 | 55.5 | 54.9 |

## FULL_qlLA

| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | feasible | runs | dead ends |
|---|---|---|---|---|---|---|---|
| FULL_qlLA (parent, gamma 1) | 0.03474 | +0.00 % | 51.69 | +0.00 % | - | 70 | 0 |
| FULL_qlLA-g1.25 | 0.03594 | +3.48 % | 47.32 | -8.45 % | yes | 70 | 0 |
| FULL_qlLA-g1.5 | 0.03565 | +2.64 % | 47.39 | -8.31 % | yes | 70 | 0 |
| FULL_qlLA-g2.0 **(chosen)** | 0.03710 | +6.80 % | 46.60 | -9.84 % | yes | 70 | 0 |
| FULL_qlLA-g3.0 | 0.03696 | +6.41 % | 54.55 | +5.53 % | no | 70 | 0 |

Chosen for FULL_qlLA_G: gamma **2.0** (within 0.5 % of the best feasible THR: FULL_qlLA-g2.0)

Per scenario (FULL_qlLA, parent vs chosen): saturation throughput / latency at 1.0 x Lsat

| scenario | THR parent | THR chosen | LAT parent | LAT chosen |
|---|---|---|---|---|
| uniform  | 0.06439 | 0.06341 | 47.0 | 47.9 |
| localized  | 0.08917 | 0.09599 | 36.6 | 37.0 |
| hotspot  | 0.01873 | 0.01896 | 76.7 | 46.1 |
| chipperm  | 0.02857 | 0.03373 | 51.3 | 54.1 |
| movinghot  | 0.02106 | 0.02387 | 68.1 | 51.6 |
| uniform 0x1111111111111111 | 0.05206 | 0.05584 | 46.1 | 47.3 |
| hotspot 0x1111111111111111 | 0.01811 | 0.01863 | 46.3 | 44.2 |

