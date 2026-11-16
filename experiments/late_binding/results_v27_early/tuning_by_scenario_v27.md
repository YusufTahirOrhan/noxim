# v27 Part B: the tuning runs by scenario (tune_scen_v27.py; descriptive)

From `tune_runs.csv` (seeds 101 and 102; two seeds per cell, so every number here is a pointer and no more). The rule of the tuning (`tuning_v27.md`) scores a
value by its mean over the five tuning scenarios; nothing here changes a choice. THR, LAT1.0 and LAT0.5 are percentages against DeFT-P on the same seeds
(100 x (exp(mean ln ratio) - 1)); score = ln THR ratio - ln LAT1.0 ratio - ln LAT0.5 ratio, in natural-log units.

## The chosen values next to the main row

The last four columns are means of the two runs at 1.0 x Lsat: the largest share of a chiplet's Up moves on one entry VL over the mean share (`vl_imbalance`;
DeFT-P's value in brackets), head-flit forwards per delivered packet, the share of the Up moves on a VL that is not DeFT-P's entry VL, and the age of the
choice at the Up move (mean time since generation at the Up move less the mean wait at the source; for the main row the time the packet has travelled).

### 2x2

| scenario | row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | vl_imbalance | hops per packet | not DeFT-P's VL | age at Up (cycles) |
|---|---|---|---|---|---|---|---|---|---|---|
| uniform | `CI_heurLA_X_LF` | frozen | +0.291 | +6.5 % | -18.9 % | -1.9 % | 1.09 (1.06) | 8.35 | 34 % | 57 |
| uniform | `EB_vl` | 0.5 | -0.466 | -12.7 % | +37.7 % | +1.1 % | 1.13 (1.06) | 8.22 | 49 % | 95 |
| uniform | `EB_route` | 2 | -0.437 | -13.3 % | +26.8 % | +5.9 % | 1.10 (1.06) | 8.65 | 67 % | 83 |
| uniform | `EB_vl64` | 0.25 | -0.877 | -13.5 % | +102.7 % | +2.6 % | 1.21 (1.06) | 7.85 | 40 % | 118 |
| uniform, one faulty VL per chiplet | `CI_heurLA_X_LF` | frozen | +0.426 | +13.9 % | -23.0 % | -3.3 % | 1.15 (1.14) | 8.87 | 34 % | 62 |
| uniform, one faulty VL per chiplet | `EB_vl` | 0.5 | -0.137 | -2.3 % | +13.7 % | -1.5 % | 1.09 (1.14) | 8.66 | 44 % | 88 |
| uniform, one faulty VL per chiplet | `EB_route` | 2 | -0.196 | -3.7 % | +13.8 % | +2.9 % | 1.14 (1.14) | 9.04 | 61 % | 85 |
| uniform, one faulty VL per chiplet | `EB_vl64` | 0.25 | -0.314 | -0.2 % | +36.4 % | +0.1 % | 1.15 (1.14) | 8.38 | 38 % | 100 |
| hotspot | `CI_heurLA_X_LF` | frozen | +1.045 | +19.9 % | -56.4 % | -3.4 % | 1.27 (1.56) | 8.18 | 31 % | 45 |
| hotspot | `EB_vl` | 0.5 | +0.947 | +18.0 % | -52.4 % | -3.7 % | 1.25 (1.56) | 7.90 | 50 % | 49 |
| hotspot | `EB_route` | 2 | +0.918 | +19.9 % | -51.2 % | -1.8 % | 1.23 (1.56) | 8.32 | 63 % | 48 |
| hotspot | `EB_vl64` | 0.25 | +0.895 | +16.4 % | -51.1 % | -2.8 % | 1.31 (1.56) | 7.69 | 48 % | 51 |
| chipperm | `CI_heurLA_X_LF` | frozen | +0.530 | +10.1 % | -34.0 % | -1.8 % | 1.09 (1.05) | 12.18 | 40 % | 74 |
| chipperm | `EB_vl` | 0.5 | -2.775 | -29.6 % | +907.5 % | +12.2 % | 1.62 (1.05) | 11.42 | 45 % | 234 |
| chipperm | `EB_route` | 2 | -1.789 | -18.4 % | +315.0 % | +17.7 % | 1.16 (1.05) | 12.82 | 70 % | 191 |
| chipperm | `EB_vl64` | 0.25 | -2.972 | -34.9 % | +946.6 % | +21.5 % | 1.71 (1.05) | 10.85 | 38 % | 229 |
| chiptrans | `CI_heurLA_X_LF` | frozen | +0.359 | +3.5 % | -26.9 % | -1.1 % | 2.11 (2.08) | 7.43 | 39 % | 73 |
| chiptrans | `EB_vl` | 0.5 | -2.033 | -10.3 % | +523.1 % | +9.9 % | 2.79 (2.08) | 6.32 | 41 % | 218 |
| chiptrans | `EB_route` | 2 | -1.481 | -10.5 % | +246.4 % | +13.7 % | 2.20 (2.08) | 7.41 | 71 % | 188 |
| chiptrans | `EB_vl64` | 0.25 | -2.201 | -12.2 % | +588.6 % | +15.1 % | 2.92 (2.08) | 5.98 | 38 % | 209 |

### 4x4

| scenario | row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | vl_imbalance | hops per packet | not DeFT-P's VL | age at Up (cycles) |
|---|---|---|---|---|---|---|---|---|---|---|
| uniform | `CI_heurLA_X_LF` | frozen | +0.642 | +19.4 % | -35.9 % | -2.0 % | 1.20 (1.08) | 14.35 | 57 % | 79 |
| uniform | `EB_vl` | 1 | -1.446 | -11.3 % | +267.8 % | +2.4 % | 1.27 (1.08) | 14.39 | 60 % | 257 |
| uniform | `EB_route` | 4 | +0.070 | -0.7 % | -12.3 % | +5.5 % | 1.16 (1.08) | 14.83 | 72 % | 109 |
| uniform | `EB_vl64` | 1 | -1.808 | -14.1 % | +397.0 % | +5.4 % | 1.34 (1.08) | 14.32 | 61 % | 277 |
| uniform, one faulty VL per chiplet | `CI_heurLA_X_LF` | frozen | +0.730 | +22.0 % | -39.5 % | -2.9 % | 1.27 (1.19) | 14.99 | 52 % | 84 |
| uniform, one faulty VL per chiplet | `EB_vl` | 1 | -1.105 | -7.2 % | +179.1 % | +0.3 % | 1.29 (1.19) | 14.99 | 55 % | 233 |
| uniform, one faulty VL per chiplet | `EB_route` | 4 | +0.269 | +6.3 % | -21.7 % | +3.7 % | 1.19 (1.19) | 15.36 | 64 % | 109 |
| uniform, one faulty VL per chiplet | `EB_vl64` | 1 | -1.312 | -11.8 % | +220.1 % | +2.3 % | 1.24 (1.19) | 15.06 | 56 % | 250 |
| hotspot | `CI_heurLA_X_LF` | frozen | +0.729 | +30.5 % | -33.4 % | -5.5 % | 2.31 (3.90) | 14.05 | 59 % | 55 |
| hotspot | `EB_vl` | 1 | +0.698 | +29.0 % | -32.4 % | -4.9 % | 2.22 (3.90) | 14.06 | 57 % | 56 |
| hotspot | `EB_route` | 4 | +0.670 | +28.8 % | -31.3 % | -4.1 % | 2.05 (3.90) | 14.34 | 62 % | 57 |
| hotspot | `EB_vl64` | 1 | +0.685 | +28.7 % | -31.7 % | -5.0 % | 2.23 (3.90) | 14.07 | 58 % | 57 |
| chipperm | `CI_heurLA_X_LF` | frozen | +0.361 | +9.5 % | -24.3 % | +0.7 % | 1.36 (1.11) | 20.46 | 58 % | 125 |
| chipperm | `EB_vl` | 1 | -2.832 | -45.5 % | +757.7 % | +7.9 % | 3.14 (1.11) | 17.43 | 65 % | 404 |
| chipperm | `EB_route` | 4 | -0.906 | -9.9 % | +96.5 % | +13.4 % | 1.24 (1.11) | 20.97 | 73 % | 261 |
| chipperm | `EB_vl64` | 1 | -2.864 | -44.1 % | +773.9 % | +12.1 % | 3.19 (1.11) | 17.28 | 65 % | 398 |
| chiptrans | `CI_heurLA_X_LF` | frozen | +0.777 | +7.7 % | -50.3 % | -0.3 % | 1.94 (1.50) | 13.82 | 56 % | 100 |
| chiptrans | `EB_vl` | 1 | -1.695 | -15.9 % | +317.1 % | +9.9 % | 3.19 (1.50) | 11.40 | 56 % | 400 |
| chiptrans | `EB_route` | 4 | -0.684 | -9.3 % | +65.2 % | +8.8 % | 1.78 (1.50) | 13.77 | 69 % | 244 |
| chiptrans | `EB_vl64` | 1 | -1.733 | -15.5 % | +329.3 % | +11.2 % | 3.14 (1.50) | 11.38 | 57 % | 413 |

## The score of every value in every scenario

One line per row and scenario; the largest score of the line is in bold. The last column is the value the rule chose for the row on that size (the largest mean
over the five scenarios).

### 2x2

| row | scenario | main row | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 | 8 | chosen |
|---|---|---|---|---|---|---|---|---|---|---|
| `EB_vl` | uniform | +0.291 | -1.401 | -0.630 | **-0.466** | -1.259 | -1.828 | -2.136 | -2.174 | 0.5 |
| `EB_vl` | uniform, one faulty VL per chiplet | +0.426 | -0.829 | **-0.118** | -0.137 | -0.480 | -0.823 | -1.081 | -1.151 | 0.5 |
| `EB_vl` | hotspot | +1.045 | +0.845 | +0.939 | **+0.947** | +0.882 | +0.797 | +0.711 | +0.676 | 0.5 |
| `EB_vl` | chipperm | +0.530 | -3.006 | -2.951 | -2.775 | -2.644 | **-2.603** | -2.818 | -2.769 | 0.5 |
| `EB_vl` | chiptrans | +0.359 | -2.274 | -2.120 | -2.033 | **-1.867** | -1.942 | -1.871 | -1.934 | 0.5 |
| `EB_route` | uniform | +0.291 | -1.137 | -0.536 | **-0.351** | -0.392 | -0.437 | -0.477 | -0.546 | 2 |
| `EB_route` | uniform, one faulty VL per chiplet | +0.426 | -1.037 | -0.433 | **-0.089** | -0.146 | -0.196 | -0.246 | -0.261 | 2 |
| `EB_route` | hotspot | +1.045 | +0.880 | +0.959 | **+0.972** | +0.961 | +0.918 | +0.864 | +0.836 | 2 |
| `EB_route` | chipperm | +0.530 | -2.636 | -2.461 | -2.102 | -2.046 | -1.789 | -1.856 | **-1.718** | 2 |
| `EB_route` | chiptrans | +0.359 | -2.064 | -1.810 | -1.782 | -1.632 | -1.481 | -1.557 | **-1.415** | 2 |
| `EB_vl64` | uniform | +0.291 | -1.675 | **-0.877** | -1.098 | -2.274 | -2.620 | -2.861 | -2.898 | 0.25 |
| `EB_vl64` | uniform, one faulty VL per chiplet | +0.426 | -1.001 | **-0.314** | -0.608 | -1.337 | -1.557 | -1.765 | -2.028 | 0.25 |
| `EB_vl64` | hotspot | +1.045 | +0.807 | **+0.895** | +0.851 | +0.718 | +0.559 | +0.387 | +0.404 | 0.25 |
| `EB_vl64` | chipperm | +0.530 | -3.047 | -2.972 | **-2.958** | -3.006 | -2.981 | -3.206 | -3.178 | 0.25 |
| `EB_vl64` | chiptrans | +0.359 | -2.301 | -2.201 | **-2.146** | -2.186 | -2.209 | -2.249 | -2.280 | 0.25 |

### 4x4

| row | scenario | main row | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 | 8 | chosen |
|---|---|---|---|---|---|---|---|---|---|---|
| `EB_vl` | uniform | +0.642 | -2.105 | -1.956 | -1.639 | **-1.446** | -1.968 | -1.890 | -2.086 | 1 |
| `EB_vl` | uniform, one faulty VL per chiplet | +0.730 | -1.597 | -1.555 | **-1.067** | -1.105 | -1.141 | -1.423 | -1.592 | 1 |
| `EB_vl` | hotspot | +0.729 | +0.688 | +0.695 | **+0.706** | +0.698 | +0.686 | +0.658 | +0.647 | 1 |
| `EB_vl` | chipperm | +0.361 | -3.002 | -2.959 | -2.911 | -2.832 | **-2.787** | -2.813 | -2.794 | 1 |
| `EB_vl` | chiptrans | +0.777 | -1.822 | -1.823 | -1.837 | -1.695 | -1.406 | -1.178 | **-0.826** | 1 |
| `EB_route` | uniform | +0.642 | -0.136 | +0.116 | **+0.183** | +0.160 | +0.118 | +0.070 | +0.074 | 4 |
| `EB_route` | uniform, one faulty VL per chiplet | +0.730 | +0.007 | +0.316 | **+0.368** | +0.332 | +0.290 | +0.269 | +0.236 | 4 |
| `EB_route` | hotspot | +0.729 | **+0.722** | +0.715 | +0.698 | +0.690 | +0.672 | +0.670 | +0.677 | 4 |
| `EB_route` | chipperm | +0.361 | -2.125 | -1.724 | -1.344 | -1.139 | -0.995 | **-0.906** | -0.989 | 4 |
| `EB_route` | chiptrans | +0.777 | -1.237 | -1.109 | -0.853 | -0.852 | -0.677 | -0.684 | **-0.639** | 4 |
| `EB_vl64` | uniform | +0.642 | -2.069 | -2.025 | -1.830 | **-1.808** | -1.998 | -2.057 | -2.250 | 1 |
| `EB_vl64` | uniform, one faulty VL per chiplet | +0.730 | -1.648 | -1.439 | **-1.148** | -1.312 | -1.456 | -1.689 | -1.845 | 1 |
| `EB_vl64` | hotspot | +0.729 | +0.687 | **+0.696** | +0.690 | +0.685 | +0.663 | +0.649 | +0.627 | 1 |
| `EB_vl64` | chipperm | +0.361 | -3.043 | -3.050 | -3.004 | **-2.864** | -2.888 | -2.930 | -2.957 | 1 |
| `EB_vl64` | chiptrans | +0.777 | -1.766 | -1.843 | -1.890 | -1.733 | -1.513 | -1.358 | **-1.231** | 1 |

