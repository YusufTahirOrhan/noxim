# Regression of the v6 statistics flag (check_stats_regression.py)

Old binary: build of e4752bf (no statistics code). New binary: v6 statistics code.
Configurations: 66 (11 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at 1.0 x Lsat of v5; seed 7).

- flag off: 66 / 66 runs with identical summary and deft_lb blocks
- flag on: 66 / 66 runs with identical summary (and deft_lb) blocks; 66 statistics files written (every run writes one; for DEFT routing it holds no per-hop data because the hook only runs under DEFT_LB)

No differences.
