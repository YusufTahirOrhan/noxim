# v6 tuning of the proposed methods per size (seeds 101, 102)

Protocol of the v5 rho tuning: uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; ~0.8 and ~1.1 x Lsat (v5 load points); 2 seeds = 16 runs per configuration; criterion = geometric mean of the mean latency. "accepted @1.1" = geometric mean of the accepted throughput at the ~1.1 x Lsat load. CI takes its exit from the uniform LUT of DeFT's rho* of the size. QL-LA inherits the tuned (w, busy) of the lookahead heuristic of its scope and size.

## 3x3 CI_heurLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-heurLA-w2.0-b0.0 **(chosen)** | 16 | 54.08 | +0.00 % | 0.0501 |
| CI-heurLA-w4.0-b0.0 | 16 | 55.52 | +2.66 % | 0.0500 |
| CI-heurLA-w4.0-b8.0 | 16 | 55.62 | +2.85 % | 0.0499 |
| CI-heurLA-w1.0-b0.0 | 16 | 57.32 | +5.99 % | 0.0502 |
| CI-heurLA-w4.0-b4.0 | 16 | 57.91 | +7.07 % | 0.0500 |
| CI-heurLA-w1.0-b4.0 (2x2 parameters) | 16 | 59.19 | +9.44 % | 0.0500 |
| CI-heurLA-w0.5-b4.0 | 16 | 60.15 | +11.22 % | 0.0497 |
| CI-heurLA-w2.0-b4.0 | 16 | 62.82 | +16.15 % | 0.0500 |
| CI-heurLA-w0.5-b0.0 | 16 | 64.56 | +19.37 % | 0.0499 |
| CI-heurLA-w1.0-b8.0 | 16 | 66.15 | +22.32 % | 0.0499 |
| CI-heurLA-w2.0-b8.0 | 16 | 67.81 | +25.39 % | 0.0493 |
| CI-heurLA-w0.5-b8.0 | 16 | 72.17 | +33.46 % | 0.0485 |

## 3x3 CI_qlLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-qlLA-a0.1-k1 **(chosen)** | 16 | 50.07 | +0.00 % | 0.0502 |
| CI-qlLA-a0.05-k1 | 16 | 50.08 | +0.02 % | 0.0501 |
| CI-qlLA-a0.02-k1 | 16 | 50.80 | +1.45 % | 0.0502 |
| CI-qlLA-a0.005-k1 | 16 | 51.12 | +2.08 % | 0.0501 |
| CI-qlLA-a0.01-k1 | 16 | 51.64 | +3.12 % | 0.0501 |
| CI-qlLA-a0.1-k0 | 16 | 52.90 | +5.64 % | 0.0498 |
| CI-qlLA-a0.05-k0 | 16 | 54.20 | +8.24 % | 0.0503 |
| CI-qlLA-a0.02-k0 | 16 | 55.06 | +9.96 % | 0.0502 |
| CI-qlLA-a0.005-k0 | 16 | 55.53 | +10.90 % | 0.0500 |
| CI-qlLA-a0.01-k0 | 16 | 58.15 | +16.13 % | 0.0501 |

## 3x3 FULL_heurLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-heurLA-w2.0-b0.0 **(chosen)** (2x2 parameters) | 16 | 44.64 | +0.00 % | 0.0502 |
| FULL-heurLA-w1.0-b4.0 | 16 | 45.53 | +1.98 % | 0.0500 |
| FULL-heurLA-w1.0-b0.0 | 16 | 45.98 | +3.00 % | 0.0502 |
| FULL-heurLA-w4.0-b8.0 | 16 | 46.45 | +4.04 % | 0.0499 |
| FULL-heurLA-w4.0-b4.0 | 16 | 46.49 | +4.14 % | 0.0500 |
| FULL-heurLA-w1.0-b8.0 | 16 | 46.51 | +4.19 % | 0.0501 |
| FULL-heurLA-w2.0-b4.0 | 16 | 46.63 | +4.44 % | 0.0503 |
| FULL-heurLA-w0.5-b4.0 | 16 | 47.77 | +7.00 % | 0.0501 |
| FULL-heurLA-w4.0-b0.0 | 16 | 48.93 | +9.60 % | 0.0504 |
| FULL-heurLA-w0.5-b8.0 | 16 | 49.67 | +11.26 % | 0.0503 |
| FULL-heurLA-w0.5-b0.0 | 16 | 52.25 | +17.05 % | 0.0504 |
| FULL-heurLA-w2.0-b8.0 | 16 | 56.00 | +25.43 % | 0.0476 |

## 3x3 FULL_qlLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-qlLA-a0.02-k1 **(chosen)** | 16 | 43.75 | +0.00 % | 0.0501 |
| FULL-qlLA-a0.01-k1 | 16 | 43.97 | +0.50 % | 0.0501 |
| FULL-qlLA-a0.02-k0 | 16 | 44.50 | +1.72 % | 0.0499 |
| FULL-qlLA-a0.05-k1 | 16 | 44.54 | +1.80 % | 0.0501 |
| FULL-qlLA-a0.005-k0 | 16 | 44.70 | +2.17 % | 0.0498 |
| FULL-qlLA-a0.1-k0 | 16 | 44.73 | +2.24 % | 0.0503 |
| FULL-qlLA-a0.005-k1 | 16 | 44.95 | +2.75 % | 0.0504 |
| FULL-qlLA-a0.01-k0 | 16 | 44.97 | +2.80 % | 0.0500 |
| FULL-qlLA-a0.1-k1 | 16 | 45.06 | +3.01 % | 0.0504 |
| FULL-qlLA-a0.05-k0 | 16 | 45.17 | +3.26 % | 0.0502 |

## 4x4 CI_heurLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-heurLA-w2.0-b0.0 **(chosen)** | 16 | 57.83 | +0.00 % | 0.0328 |
| CI-heurLA-w1.0-b0.0 | 16 | 58.79 | +1.66 % | 0.0329 |
| CI-heurLA-w0.5-b0.0 | 16 | 62.08 | +7.36 % | 0.0328 |
| CI-heurLA-w1.0-b4.0 (2x2 parameters) | 16 | 62.66 | +8.36 % | 0.0326 |
| CI-heurLA-w0.5-b4.0 | 16 | 62.87 | +8.72 % | 0.0328 |
| CI-heurLA-w4.0-b0.0 | 16 | 64.39 | +11.35 % | 0.0329 |
| CI-heurLA-w4.0-b4.0 | 16 | 65.92 | +13.99 % | 0.0323 |
| CI-heurLA-w2.0-b8.0 | 16 | 66.76 | +15.45 % | 0.0325 |
| CI-heurLA-w2.0-b4.0 | 16 | 68.55 | +18.55 % | 0.0328 |
| CI-heurLA-w4.0-b8.0 | 16 | 70.99 | +22.76 % | 0.0320 |
| CI-heurLA-w0.5-b8.0 | 16 | 78.73 | +36.15 % | 0.0317 |
| CI-heurLA-w1.0-b8.0 | 16 | 79.68 | +37.79 % | 0.0317 |

## 4x4 CI_qlLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-qlLA-a0.1-k1 **(chosen)** | 16 | 56.06 | +0.00 % | 0.0329 |
| CI-qlLA-a0.02-k1 | 16 | 56.48 | +0.76 % | 0.0330 |
| CI-qlLA-a0.05-k0 | 16 | 56.70 | +1.14 % | 0.0329 |
| CI-qlLA-a0.05-k1 | 16 | 56.73 | +1.20 % | 0.0329 |
| CI-qlLA-a0.005-k1 | 16 | 57.14 | +1.94 % | 0.0326 |
| CI-qlLA-a0.01-k1 | 16 | 57.31 | +2.24 % | 0.0328 |
| CI-qlLA-a0.02-k0 | 16 | 57.80 | +3.10 % | 0.0330 |
| CI-qlLA-a0.1-k0 | 16 | 59.22 | +5.64 % | 0.0328 |
| CI-qlLA-a0.01-k0 | 16 | 61.18 | +9.14 % | 0.0328 |
| CI-qlLA-a0.005-k0 | 16 | 64.15 | +14.44 % | 0.0322 |

## 4x4 FULL_heurLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-heurLA-w1.0-b4.0 **(chosen)** | 16 | 49.53 | +0.00 % | 0.0330 |
| FULL-heurLA-w1.0-b0.0 | 16 | 50.36 | +1.68 % | 0.0328 |
| FULL-heurLA-w2.0-b4.0 | 16 | 50.59 | +2.14 % | 0.0330 |
| FULL-heurLA-w0.5-b8.0 | 16 | 50.77 | +2.50 % | 0.0328 |
| FULL-heurLA-w2.0-b0.0 (2x2 parameters) | 16 | 50.81 | +2.58 % | 0.0328 |
| FULL-heurLA-w2.0-b8.0 | 16 | 51.80 | +4.59 % | 0.0330 |
| FULL-heurLA-w0.5-b4.0 | 16 | 51.82 | +4.62 % | 0.0328 |
| FULL-heurLA-w0.5-b0.0 | 16 | 53.39 | +7.80 % | 0.0328 |
| FULL-heurLA-w1.0-b8.0 | 16 | 58.99 | +19.09 % | 0.0310 |

## 4x4 FULL_qlLA

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-qlLA-a0.05-k1 **(chosen)** | 16 | 47.77 | +0.00 % | 0.0329 |
| FULL-qlLA-a0.1-k1 | 16 | 48.20 | +0.89 % | 0.0328 |
| FULL-qlLA-a0.02-k1 | 16 | 48.60 | +1.72 % | 0.0327 |
| FULL-qlLA-a0.01-k1 | 16 | 48.60 | +1.73 % | 0.0328 |
| FULL-qlLA-a0.1-k0 | 16 | 48.62 | +1.78 % | 0.0328 |
| FULL-qlLA-a0.005-k0 | 16 | 49.49 | +3.60 % | 0.0328 |
| FULL-qlLA-a0.05-k0 | 16 | 49.87 | +4.39 % | 0.0328 |
| FULL-qlLA-a0.02-k0 | 16 | 50.35 | +5.39 % | 0.0329 |
| FULL-qlLA-a0.005-k1 | 16 | 50.37 | +5.45 % | 0.0330 |
| FULL-qlLA-a0.01-k0 | 16 | 50.93 | +6.61 % | 0.0328 |

## Distance of the tuned optimum from the 2x2 parameters

| size | scope | heurLA (w, busy): 2x2 -> tuned | criterion of the 2x2 heurLA setting vs tuned | qlLA (alpha, key): 2x2 -> tuned |
|---|---|---|---|---|
| 3x3 | CI | (1.0, 4.0) -> (2.0, 0.0) | +9.44 % | (0.05, 1) -> (0.1, 1) |
| 3x3 | FULL | (2.0, 0.0) -> (2.0, 0.0) | +0.00 % | (0.01, 1) -> (0.02, 1) |
| 4x4 | CI | (1.0, 4.0) -> (2.0, 0.0) | +8.36 % | (0.05, 1) -> (0.1, 1) |
| 4x4 | FULL | (2.0, 0.0) -> (1.0, 4.0) | +2.58 % | (0.01, 1) -> (0.05, 1) |

Budget: 1360 tuning runs in total (44 configuration names over both sizes); per size and scope 9 heuristic configurations (+ the extension, if any) and 10 learner configurations.
