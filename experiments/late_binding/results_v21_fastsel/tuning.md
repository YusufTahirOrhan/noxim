# v21 tuning of the fast variants per size (seeds 101, 102)

v6 protocol at the K5 load points (`load_points_rr.json`): uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; ~0.8 and ~1.1 x Lsat; 2 seeds = 16 runs per configuration; criterion = geometric mean of the mean latency. All runs with -deft_vn_rr 1 and the decision delay N_fast of the variant. The learners inherit (w, beta) of the heuristic of their scope and size, are keyed by the destination chiplet and use 16-bit residuals.

## 2x2 CI heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-heur-w2.0-b4.0 **(chosen)** | 16 | 53.35 | +0.00 % | 0.0654 |
| CI-heur-w0.5-b8.0 | 16 | 55.20 | +3.47 % | 0.0654 |
| CI-heur-w4.0-b4.0 | 16 | 57.38 | +7.56 % | 0.0652 |
| CI-heur-w2.0-b8.0 | 16 | 57.49 | +7.77 % | 0.0657 |
| CI-heur-w1.0-b8.0 | 16 | 59.30 | +11.16 % | 0.0655 |
| CI-heur-w1.0-b4.0 | 16 | 61.92 | +16.07 % | 0.0649 |
| CI-heur-w2.0-b0.0 | 16 | 68.51 | +28.42 % | 0.0651 |
| CI-heur-w0.5-b4.0 | 16 | 95.50 | +79.01 % | 0.0627 |
| CI-heur-w1.0-b0.0 | 16 | 189.59 | +255.38 % | 0.0579 |
| CI-heur-w0.5-b0.0 | 16 | 381.07 | +614.31 % | 0.0515 |

## 2x2 CI ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-ql-a0.1 **(chosen)** | 16 | 51.17 | +0.00 % | 0.0654 |
| CI-ql-a0.05 | 16 | 51.62 | +0.88 % | 0.0656 |
| CI-ql-a0.02 | 16 | 51.73 | +1.08 % | 0.0660 |
| CI-ql-a0.01 | 16 | 51.88 | +1.38 % | 0.0661 |
| CI-ql-a0.005 | 16 | 53.97 | +5.46 % | 0.0661 |

Variant for the primary hypotheses, 2x2 CI: **CI_fastQL**.

## 2x2 FULL heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-heur-w2.0-b4.0 **(chosen)** | 16 | 68.73 | +0.00 % | 0.0654 |
| FULL-heur-w4.0-b4.0 | 16 | 70.13 | +2.04 % | 0.0639 |
| FULL-heur-w1.0-b8.0 | 16 | 78.04 | +13.55 % | 0.0637 |
| FULL-heur-w1.0-b4.0 | 16 | 80.84 | +17.62 % | 0.0654 |
| FULL-heur-w2.0-b8.0 | 16 | 87.30 | +27.02 % | 0.0626 |
| FULL-heur-w2.0-b0.0 | 16 | 90.49 | +31.66 % | 0.0648 |
| FULL-heur-w0.5-b8.0 | 16 | 106.10 | +54.38 % | 0.0606 |
| FULL-heur-w0.5-b4.0 | 16 | 153.72 | +123.66 % | 0.0596 |
| FULL-heur-w1.0-b0.0 | 16 | 261.89 | +281.05 % | 0.0547 |
| FULL-heur-w0.5-b0.0 | 16 | 473.55 | +589.03 % | 0.0473 |

## 2x2 FULL ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-ql-a0.05 **(chosen)** | 16 | 58.83 | +0.00 % | 0.0662 |
| FULL-ql-a0.02 | 16 | 59.55 | +1.22 % | 0.0663 |
| FULL-ql-a0.1 | 16 | 59.71 | +1.49 % | 0.0660 |
| FULL-ql-a0.005 | 16 | 62.47 | +6.18 % | 0.0659 |
| FULL-ql-a0.01 | 16 | 65.15 | +10.73 % | 0.0662 |

Variant for the primary hypotheses, 2x2 FULL: **FULL_fastQL**.

## 3x3 CI heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-heur-w4.0-b4.0 **(chosen)** | 16 | 71.98 | +0.00 % | 0.0507 |
| CI-heur-w2.0-b4.0 | 16 | 73.39 | +1.96 % | 0.0508 |
| CI-heur-w1.0-b8.0 | 16 | 81.54 | +13.28 % | 0.0509 |
| CI-heur-w2.0-b0.0 | 16 | 82.94 | +15.23 % | 0.0505 |
| CI-heur-w1.0-b4.0 | 16 | 83.84 | +16.48 % | 0.0506 |
| CI-heur-w0.5-b8.0 | 16 | 87.08 | +20.98 % | 0.0507 |
| CI-heur-w2.0-b8.0 | 16 | 88.92 | +23.53 % | 0.0505 |
| CI-heur-w0.5-b4.0 | 16 | 103.14 | +43.29 % | 0.0499 |
| CI-heur-w1.0-b0.0 | 16 | 273.76 | +280.34 % | 0.0433 |
| CI-heur-w0.5-b0.0 | 16 | 563.51 | +682.88 % | 0.0353 |

## 3x3 CI ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-ql-a0.02 **(chosen)** | 16 | 70.42 | +0.00 % | 0.0510 |
| CI-ql-a0.1 | 16 | 71.71 | +1.84 % | 0.0508 |
| CI-ql-a0.01 | 16 | 72.90 | +3.52 % | 0.0511 |
| CI-ql-a0.05 | 16 | 73.57 | +4.47 % | 0.0507 |
| CI-ql-a0.005 | 16 | 74.99 | +6.49 % | 0.0508 |

Variant for the primary hypotheses, 3x3 CI: **CI_fastQL**.

## 3x3 FULL heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-heur-w2.0-b4.0 **(chosen)** | 16 | 78.62 | +0.00 % | 0.0509 |
| FULL-heur-w4.0-b4.0 | 16 | 79.53 | +1.16 % | 0.0507 |
| FULL-heur-w2.0-b0.0 | 16 | 86.73 | +10.32 % | 0.0507 |
| FULL-heur-w1.0-b4.0 | 16 | 87.61 | +11.44 % | 0.0508 |
| FULL-heur-w1.0-b8.0 | 16 | 88.55 | +12.63 % | 0.0506 |
| FULL-heur-w2.0-b8.0 | 16 | 96.80 | +23.12 % | 0.0490 |
| FULL-heur-w0.5-b8.0 | 16 | 96.92 | +23.27 % | 0.0500 |
| FULL-heur-w0.5-b4.0 | 16 | 141.70 | +80.23 % | 0.0484 |
| FULL-heur-w1.0-b0.0 | 16 | 287.85 | +266.13 % | 0.0424 |
| FULL-heur-w0.5-b0.0 | 16 | 561.91 | +614.72 % | 0.0348 |

## 3x3 FULL ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-ql-a0.05 **(chosen)** | 16 | 77.56 | +0.00 % | 0.0509 |
| FULL-ql-a0.1 | 16 | 78.28 | +0.93 % | 0.0507 |
| FULL-ql-a0.01 | 16 | 78.86 | +1.68 % | 0.0509 |
| FULL-ql-a0.005 | 16 | 80.40 | +3.66 % | 0.0509 |
| FULL-ql-a0.02 | 16 | 81.63 | +5.26 % | 0.0506 |

Variant for the primary hypotheses, 3x3 FULL: **FULL_fastQL**.

## 4x4 CI heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-heur-w2.0-b4.0 **(chosen)** | 16 | 81.49 | +0.00 % | 0.0336 |
| CI-heur-w1.0-b4.0 | 16 | 85.45 | +4.87 % | 0.0335 |
| CI-heur-w2.0-b0.0 | 16 | 86.67 | +6.36 % | 0.0339 |
| CI-heur-w4.0-b4.0 | 16 | 88.61 | +8.75 % | 0.0333 |
| CI-heur-w0.5-b8.0 | 16 | 91.12 | +11.81 % | 0.0334 |
| CI-heur-w1.0-b8.0 | 16 | 92.72 | +13.79 % | 0.0333 |
| CI-heur-w2.0-b8.0 | 16 | 98.12 | +20.41 % | 0.0330 |
| CI-heur-w0.5-b4.0 | 16 | 103.49 | +27.00 % | 0.0331 |
| CI-heur-w1.0-b0.0 | 16 | 208.72 | +156.13 % | 0.0284 |
| CI-heur-w0.5-b0.0 | 16 | 350.56 | +330.19 % | 0.0242 |

## 4x4 CI ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| CI-ql-a0.01 **(chosen)** | 16 | 81.10 | +0.00 % | 0.0338 |
| CI-ql-a0.1 | 16 | 81.10 | +0.00 % | 0.0337 |
| CI-ql-a0.05 | 16 | 81.15 | +0.07 % | 0.0336 |
| CI-ql-a0.02 | 16 | 82.59 | +1.85 % | 0.0336 |
| CI-ql-a0.005 | 16 | 84.94 | +4.74 % | 0.0335 |

Variant for the primary hypotheses, 4x4 CI: **CI_fastQL**.

## 4x4 FULL heur

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-heur-w4.0-b4.0 **(chosen)** | 16 | 83.65 | +0.00 % | 0.0334 |
| FULL-heur-w2.0-b4.0 | 16 | 83.75 | +0.11 % | 0.0336 |
| FULL-heur-w1.0-b8.0 | 16 | 84.11 | +0.55 % | 0.0335 |
| FULL-heur-w0.5-b8.0 | 16 | 85.27 | +1.93 % | 0.0336 |
| FULL-heur-w1.0-b4.0 | 16 | 87.74 | +4.88 % | 0.0334 |
| FULL-heur-w2.0-b8.0 | 16 | 88.81 | +6.16 % | 0.0335 |
| FULL-heur-w2.0-b0.0 | 16 | 90.02 | +7.61 % | 0.0336 |
| FULL-heur-w0.5-b4.0 | 16 | 116.28 | +39.00 % | 0.0321 |
| FULL-heur-w1.0-b0.0 | 16 | 204.06 | +143.93 % | 0.0298 |
| FULL-heur-w0.5-b0.0 | 16 | 340.80 | +307.39 % | 0.0248 |

## 4x4 FULL ql

| configuration | runs | geo-mean latency | vs best | accepted @1.1 |
|---|---|---|---|---|
| FULL-ql-a0.02 **(chosen)** | 16 | 85.45 | +0.00 % | 0.0337 |
| FULL-ql-a0.1 | 16 | 86.26 | +0.94 % | 0.0336 |
| FULL-ql-a0.05 | 16 | 86.81 | +1.60 % | 0.0337 |
| FULL-ql-a0.01 | 16 | 86.89 | +1.69 % | 0.0337 |
| FULL-ql-a0.005 | 16 | 95.23 | +11.45 % | 0.0330 |

Variant for the primary hypotheses, 4x4 FULL: **FULL_fast**.

