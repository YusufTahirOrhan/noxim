# Exploratory CI tuning beyond the v2 grid edges (secondary; seeds 101, 102; not used in v3 runs)

Criterion as in v2: geometric-mean latency over 16 tuning runs per configuration (lower is better).
Determinism check: 48 of 48 runs shared with the v2 tuning are identical.

## CI heuristic: w {2, 4, 8} x busy {0, 4}

| config | runs | geo-mean latency | vs v2 choice |
|---|---|---|---|
| CI-heur-w2.0-b0.0 (v2 choice) | 16 | 43.53 | +0.00 % |
| CI-heur-w4.0-b0.0 | 16 | 45.28 | +4.02 % |
| CI-heur-w2.0-b4.0 | 16 | 47.98 | +10.22 % |
| CI-heur-w4.0-b4.0 | 16 | 48.10 | +10.48 % |
| CI-heur-w8.0-b0.0 | 16 | 49.72 | +14.20 % |
| CI-heur-w8.0-b4.0 | 16 | 52.62 | +20.88 % |

Best: CI-heur-w2.0-b0.0 (43.53). v2 choice: CI-heur-w2.0-b0.0 (43.53); change of the criterion: +0.00 %. The optimum does not move.
(v2 grid for reference: best CI-heur-w2.0-b0.0 43.53.)

## CI_ql: alpha {0.001, 0.002, 0.005}, key = chiplet, w/busy = 2/0

| config | runs | geo-mean latency | vs v2 choice |
|---|---|---|---|
| CI-ql-a0.005-k1 (v2 choice) | 16 | 38.53 | +0.00 % |
| CI-ql-a0.002-k1 | 16 | 39.50 | +2.52 % |
| CI-ql-a0.001-k1 | 16 | 40.42 | +4.91 % |

Best: CI-ql-a0.005-k1 (38.53). v2 choice: CI-ql-a0.005-k1 (38.53); change of the criterion: +0.00 %. The optimum does not move.
(v2 grid for reference: best CI-ql-a0.005-k1 38.53.)

Tuning differences of a few per cent on 2 seeds are within the seed-to-seed noise seen in v2 (e.g. non-monotone alpha rankings), so a moved optimum is weak evidence on its own.
