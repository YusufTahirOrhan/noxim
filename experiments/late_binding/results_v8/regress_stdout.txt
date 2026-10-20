# Regression of the v8 layer-weighted hop cost with hop_weight_ipos 1.0 (experiments_v8.py regress)

Old binary: build of 4477b04 (v7, no hop weight). New binary: v8 hop-weight code. Same arguments.
Configurations: 66 (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at 1.0 x Lsat of v5; seed 7; v5 rho* LUTs), as the v6 and v7 regressions.

- new binary, default parameters (option absent): 66 / 66 runs with byte-identical summary and deft_lb blocks (compared as parsed JSON values)
- new binary, explicit `-deft_lb hop_weight_ipos 1.0`: 66 / 66 identical

No differences.
