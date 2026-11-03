# K6: test load per (size, k, pattern) (v14 rule, DeFT(rho*) with the round-robin)

Mean latency pooled over the 5 v11 masks and seeds 51-52 per load point. Unsaturated: pooled latency <= 3 x the pooled latency at the lowest load point. Test load = the highest unsaturated load point.

| size | k | pattern | zero-load latency | pooled latency per load point (cycles; * = unsaturated) | test load (rate, x fault-free Lsat) |
|---|---|---|---|---|---|
| 2x2 | 1 | uniform | 22.9 | 23* / 32* / 67* / 323 / 895 / 1512 / 1972 | 0.009 (0.8 x) |
| 2x2 | 1 | hotspot | 22.3 | 22* / 29* / 42* / 111 / 412 / 1009 / 1454 | 0.006 (0.8 x) |
| 2x2 | 2 | uniform | 25.1 | 25* / 49* / 743 / 1360 / 1851 / 2322 / 2666 | 0.0055 (0.5 x) |
| 2x2 | 2 | hotspot | 23.7 | 24* / 36* / 88 / 525 / 1018 / 1514 / 1890 | 0.004 (0.5 x) |
| 2x2 | 3 | uniform | 34.8 | 35* / 948 / 1637 / 2048 / 2362 / 2692 / 3028 | 0.002 (0.2 x) |
| 2x2 | 3 | hotspot | 30.4 | 30* / 376 / 1068 / 1463 / 1706 / 2056 / 2271 | 0.0015 (0.2 x) |
| 3x3 | 1 | uniform | 29.4 | 29* / 40* / 84* / 342 / 783 / 1229 / 1763 | 0.0065 (0.8 x) |
| 3x3 | 1 | hotspot | 27.9 | 28* / 32* / 44* / 131 / 488 / 785 / 1101 | 0.003 (0.8 x) |
| 3x3 | 2 | uniform | 32.7 | 33* / 60* / 724 / 1288 / 1690 / 1978 / 2459 | 0.004 (0.5 x) |
| 3x3 | 2 | hotspot | 30.0 | 30* / 37* / 59* / 284 / 656 / 979 / 1297 | 0.003 (0.8 x) |
| 3x3 | 3 | uniform | 43.7 | 44* / 748 / 1436 / 1775 / 2029 / 2295 / 2635 | 0.0015 (0.2 x) |
| 3x3 | 3 | hotspot | 35.1 | 35* / 61* / 739 / 1077 / 1305 / 1561 / 1754 | 0.0018 (0.5 x) |
| 4x4 | 1 | uniform | 36.7 | 37* / 44* / 71* / 299 / 871 / 1205 / 1686 | 0.005 (0.8 x) |
| 4x4 | 1 | hotspot | 33.8 | 34* / 38* / 48* / 130 / 397 / 480 / 798 | 0.0017 (0.8 x) |
| 4x4 | 2 | uniform | 40.9 | 41* / 58* / 577 / 1170 / 1690 / 2039 / 2422 | 0.003 (0.5 x) |
| 4x4 | 2 | hotspot | 36.1 | 36* / 41* / 58* / 164 / 423 / 693 / 1065 | 0.0017 (0.8 x) |
| 4x4 | 3 | uniform | 54.0 | 54* / 423 / 1341 / 1729 / 2057 / 2203 / 2504 | 0.0015 (0.2 x) |
| 4x4 | 3 | hotspot | 40.1 | 40* / 53* / 368 / 758 / 932 / 1050 / 1241 | 0.001 (0.5 x) |
