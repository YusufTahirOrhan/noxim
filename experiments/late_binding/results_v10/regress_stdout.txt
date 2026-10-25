# Regression of the v10 options with their defaults (experiments_v10.py regress)

Old binary: build of 4953092 (v9). New binary: v10 baseline code (A1-A4). Same arguments.
Configurations: 66 (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at 1.0 x Lsat of v5; seed 7; v5 rho* LUTs), the regression set of v6-v8.

- new binary, options absent: 66 / 66 runs with byte-identical summary and deft_lb blocks
- new binary, `-deft_lb vn_rules 1 rc 0 count_vl 0` explicit: 66 / 66 identical

No differences.
