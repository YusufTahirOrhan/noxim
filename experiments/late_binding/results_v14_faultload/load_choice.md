# F1: test load per (size, k, pattern) (experiments_v14.py choose; no new runs)

DeFT(rho*) in results_v11/eval_runs.csv (seeds 51-52), mean latency pooled over the 5 masks and both seeds per load point. Unsaturated: pooled latency <= 3 x the pooled latency at the lowest load point. Test load = the highest unsaturated load point.

| size | k | pattern | zero-load latency | pooled latency per load point (cycles; * = unsaturated) | test load (rate, x fault-free Lsat) |
|---|---|---|---|---|---|
| 2x2 | 1 | uniform | 22.5 | 22* / 30* / 65* / 325 / 910 / 1492 / 1820 | 0.009 (0.8 x) |
| 2x2 | 1 | hotspot | 21.7 | 22* / 27* / 39* / 115 / 497 / 1066 / 1440 | 0.006 (0.8 x) |
| 2x2 | 2 | uniform | 24.3 | 24* / 43* / 720 / 1203 / 1548 / 1984 / 2229 | 0.0055 (0.5 x) |
| 2x2 | 2 | hotspot | 23.3 | 23* / 33* / 74 / 497 / 929 / 1318 / 1587 | 0.004 (0.5 x) |
| 2x2 | 3 | uniform | 31.5 | 31* / 816 / 1424 / 1702 / 2012 / 2247 / 2492 | 0.002 (0.2 x) |
| 2x2 | 3 | hotspot | 27.9 | 28* / 285 / 932 / 1237 / 1437 / 1705 / 1953 | 0.0015 (0.2 x) |
| 3x3 | 1 | uniform | 29.2 | 29* / 38* / 143 / 492 / 968 / 1500 / 1857 | 0.004 (0.5 x) |
| 3x3 | 1 | hotspot | 27.7 | 28* / 32* / 38* / 67* / 420 / 623 / 922 | 0.0035 (1.0 x) |
| 3x3 | 2 | uniform | 31.8 | 32* / 54* / 853 / 1281 / 1624 / 1964 / 2169 | 0.004 (0.5 x) |
| 3x3 | 2 | hotspot | 29.6 | 30* / 35* / 50* / 176 / 492 / 807 / 1055 | 0.0028 (0.8 x) |
| 3x3 | 3 | uniform | 39.8 | 40* / 689 / 1400 / 1562 / 1830 / 2023 / 2194 | 0.0015 (0.2 x) |
| 3x3 | 3 | hotspot | 34.4 | 34* / 55* / 484 / 808 / 1042 / 1274 / 1386 | 0.0018 (0.5 x) |
| 4x4 | 1 | uniform | 36.0 | 36* / 42* / 67* / 365 / 925 / 1274 / 1698 | 0.005 (0.8 x) |
| 4x4 | 1 | hotspot | 33.9 | 34* / 37* / 46* / 155 / 346 / 409 / 658 | 0.0017 (0.8 x) |
| 4x4 | 2 | uniform | 39.7 | 40* / 53* / 578 / 1069 / 1450 / 1701 / 2054 | 0.003 (0.5 x) |
| 4x4 | 2 | hotspot | 35.6 | 36* / 39* / 55* / 160 / 404 / 562 / 856 | 0.0017 (0.8 x) |
| 4x4 | 3 | uniform | 48.6 | 49* / 401 / 1170 / 1409 / 1736 / 1892 / 2121 | 0.0015 (0.2 x) |
| 4x4 | 3 | hotspot | 39.2 | 39* / 47* / 288 / 588 / 787 / 895 / 1050 | 0.001 (0.5 x) |

## Exploratory: v11 effects at these loads (seeds 51-52; not pre-registered)

Unit = (mask, seed), mean over uniform and hotspot of ln(LAT_variant / LAT_DeFT) at the chosen load of each pattern; 10 units; unadjusted t-test.

| size | k | CI_qlLA_G | FULL_qlLA_G |
|---|---|---|---|
| 2x2 | 1 | -20.0 [-26.7, -12.7] (p 0.00028) | -18.2 [-24.6, -11.2] (p 0.00036) |
| 2x2 | 2 | -9.3 [-11.8, -6.7] (p 2.9e-05) | -2.4 [-4.8, +0.0] (p 0.052) |
| 2x2 | 3 | -0.6 [-3.1, +2.0] (p 0.63) | -0.7 [-3.0, +1.5] (p 0.47) |
| 3x3 | 1 | -14.5 [-21.0, -7.5] (p 0.0015) | -18.9 [-24.4, -13.0] (p 8.7e-05) |
| 3x3 | 2 | -16.5 [-19.9, -13.0] (p 3.8e-06) | -19.7 [-22.9, -16.2] (p 8.7e-07) |
| 3x3 | 3 | -7.9 [-13.6, -1.9] (p 0.016) | -6.7 [-12.8, -0.2] (p 0.045) |
| 4x4 | 1 | -13.1 [-15.3, -10.8] (p 6.2e-07) | -21.3 [-23.1, -19.4] (p 2.9e-09) |
| 4x4 | 2 | -12.1 [-18.2, -5.4] (p 0.0032) | -17.2 [-22.9, -11.1] (p 0.0002) |
| 4x4 | 3 | -2.5 [-4.3, -0.6] (p 0.015) | -2.3 [-4.4, -0.2] (p 0.035) |
