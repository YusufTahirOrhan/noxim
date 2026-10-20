# v7 step 3: selection of the entry bound (4x4, seeds 101/102)

Grid: CI_heurLA and CI_qlLA (v6 tuned parameters) x entry_bound_mode {min, lut} x entry_bound_k {0, 1, 2, 4}, plus the unbounded parents. Cells: the 7 v5 scenarios of 4x4 x loads 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat (v5 load points) x seeds 101/102 = 70 runs per configuration, 1260 runs. Per-run data: select_runs.csv.

Criterion (fixed in the task before any run): maximise THR = geometric mean over the 7 scenarios of the saturation throughput (max accepted over the 5 loads, mean over the 2 seeds), subject to LAT = geometric mean over the scenarios of the mean latency at 1.0 x Lsat (mean over the 2 seeds) being at most 5 % above the unbounded parent's. Ties (THR within 0.5 % of the best feasible): smaller LAT, then larger k.

"candidates" = mean number of entry candidates after bounding at 1.0 x Lsat (4 = unbounded on fault-free scenarios; 3 on the two faulty ones).

## CI_heurLA

| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | feasible (LAT <= +5 %) | candidates | dead ends | LUT fallbacks |
|---|---|---|---|---|---|---|---|---|
| CI_heurLA (parent) | 0.03356 | +0.00 % | 59.20 | +0.00 % | - | 3.71 | 0 | 0 |
| CI_heurLA-min-k0 | 0.02843 | -15.27 % | 257.79 | +335.46 % | no | 1.65 | 0 | 0 |
| CI_heurLA-min-k1 | 0.02843 | -15.27 % | 257.79 | +335.46 % | no | 1.65 | 0 | 0 |
| CI_heurLA-min-k2 | 0.03198 | -4.72 % | 73.20 | +23.66 % | no | 2.48 | 0 | 0 |
| CI_heurLA-min-k4 | 0.03362 | +0.18 % | 60.30 | +1.86 % | yes | 3.18 | 0 | 0 |
| CI_heurLA-lut-k0 | 0.03152 | -6.08 % | 72.09 | +21.77 % | no | 2.20 | 0 | 0 |
| CI_heurLA-lut-k1 | 0.03152 | -6.08 % | 72.09 | +21.77 % | no | 2.20 | 0 | 0 |
| CI_heurLA-lut-k2 | 0.03371 | +0.44 % | 60.63 | +2.42 % | yes | 2.89 | 0 | 0 |
| CI_heurLA-lut-k4 **(chosen)** | 0.03399 | +1.29 % | 59.10 | -0.17 % | yes | 3.43 | 0 | 0 |

Chosen for CI_heurLA_B: mode **lut**, k **4** (configurations within 0.5 % of the best feasible THR: CI_heurLA-lut-k4)

Per scenario (CI_heurLA, parent vs chosen): saturation throughput / latency at 1.0 x Lsat

| scenario | THR parent | THR chosen | LAT parent | LAT chosen |
|---|---|---|---|---|
| uniform  | 0.05212 | 0.05474 | 62.3 | 62.0 |
| localized  | 0.08312 | 0.08279 | 46.3 | 46.7 |
| hotspot  | 0.01838 | 0.01873 | 56.1 | 55.2 |
| chipperm  | 0.02854 | 0.02804 | 67.1 | 66.8 |
| movinghot  | 0.02363 | 0.02431 | 86.3 | 82.3 |
| uniform 0x1111111111111111 | 0.04751 | 0.04909 | 56.0 | 55.5 |
| hotspot 0x1111111111111111 | 0.01879 | 0.01846 | 48.6 | 51.7 |

## CI_qlLA

| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | feasible (LAT <= +5 %) | candidates | dead ends | LUT fallbacks |
|---|---|---|---|---|---|---|---|---|
| CI_qlLA (parent) | 0.03433 | +0.00 % | 59.05 | +0.00 % | - | 3.71 | 0 | 0 |
| CI_qlLA-min-k0 | 0.02935 | -14.52 % | 214.09 | +262.52 % | no | 1.65 | 0 | 0 |
| CI_qlLA-min-k1 | 0.02935 | -14.52 % | 214.09 | +262.52 % | no | 1.65 | 0 | 0 |
| CI_qlLA-min-k2 | 0.03274 | -4.62 % | 64.36 | +8.99 % | no | 2.48 | 0 | 0 |
| CI_qlLA-min-k4 **(chosen)** | 0.03505 | +2.10 % | 56.37 | -4.54 % | yes | 3.18 | 0 | 0 |
| CI_qlLA-lut-k0 | 0.03197 | -6.89 % | 66.10 | +11.93 % | no | 2.20 | 0 | 0 |
| CI_qlLA-lut-k1 | 0.03197 | -6.89 % | 66.10 | +11.93 % | no | 2.20 | 0 | 0 |
| CI_qlLA-lut-k2 | 0.03401 | -0.95 % | 59.58 | +0.90 % | yes | 2.89 | 0 | 0 |
| CI_qlLA-lut-k4 | 0.03489 | +1.64 % | 56.41 | -4.47 % | yes | 3.43 | 0 | 0 |

Chosen for CI_qlLA_B: mode **min**, k **4** (configurations within 0.5 % of the best feasible THR: CI_qlLA-min-k4, CI_qlLA-lut-k4)

Per scenario (CI_qlLA, parent vs chosen): saturation throughput / latency at 1.0 x Lsat

| scenario | THR parent | THR chosen | LAT parent | LAT chosen |
|---|---|---|---|---|
| uniform  | 0.05550 | 0.05742 | 59.6 | 59.7 |
| localized  | 0.08357 | 0.08981 | 44.3 | 44.0 |
| hotspot  | 0.01870 | 0.01888 | 59.5 | 52.1 |
| chipperm  | 0.02901 | 0.02911 | 60.1 | 60.4 |
| movinghot  | 0.02382 | 0.02420 | 88.8 | 82.0 |
| uniform 0x1111111111111111 | 0.05184 | 0.05236 | 53.9 | 53.6 |
| hotspot 0x1111111111111111 | 0.01809 | 0.01810 | 55.5 | 49.9 |

