# Tuning budget (v2; seeds 101, 102 only)

Per configuration: 4 cells (uniform, hotspot, chipperm fault-free; uniform 0x1111) x 2 loads
(~0.8 and ~1.1 x that scenario's DeFT Lsat) x 2 seeds = 16 runs. Criterion: geometric mean of
the mean packet latency over those 16 runs. CI and FULL were tuned separately.

| Method (per scope) | Grid | Configurations | Runs | CI choice | FULL choice |
|---|---|---|---|---|---|
| heuristic (heur) | w {0.5, 1, 2} x busy {0, 4, 8} | 9 | 144 | w = 2, busy = 0 | w = 2, busy = 0 |
| lookahead heuristic (heurLA) | same grid | 9 | 144 | w = 1, busy = 4 | w = 2, busy = 0 |
| QL | alpha {0.005, 0.01, 0.02, 0.05, 0.1} x key {0, 1}, eps 0; (w, busy) from heur | 10 | 160 | alpha = 0.005, key = chiplet | alpha = 0.02, key = chiplet |
| QL-LA | same grid; (w, busy) from heurLA | 10 | 160 | alpha = 0.05, key = chiplet | alpha = 0.01, key = chiplet |
| DeFT, DeFT_tm | none (LUT, rho = 0.01) | 0 | 0 | - | - |
| A_oracle | not re-tuned (v1: beta in {0.25, 0.5, 1, 2} on FULL-era cells) | 0 (v1: 4) | 0 (v1: 64) | beta = 0.5 | |

Totals: 76 configurations, 1216 runs (608 per scope).

Budget equality: each heuristic got 9 configurations and each learner 10. The learners also
inherit the local weights chosen for their heuristic (9 configurations), so a learner's
effective budget is 9 + 10 against the heuristic's 9. This was not equalised further. Every
learner-vs-heuristic comparison is therefore biased in favour of the learner by at most this
budget difference.

Edge-of-grid choices (a better value may lie outside the grid; the grid was not extended):
w = 2 for the plain heuristic (both scopes) and for FULL heurLA; alpha = 0.005 for CI QL.
Close calls: CI heurLA (w1/b4: 38.69 vs w2/b0: 38.72) and FULL heurLA top four within 4 %.
