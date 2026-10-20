# Regression of the v7 entry bound with entry_bound_mode off (experiments_v7.py regress)

Old binary: build of 2d93fef (v6, no entry-bound code). New binary: v7 entry-bound code. Same arguments.
Configurations: 66 (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at 1.0 x Lsat of v5; seed 7; v5 rho* LUTs), as the v6 statistics regression.

- new binary, default parameters (option absent): 66 / 66 runs with byte-identical summary and deft_lb blocks (compared as parsed JSON values; the deft_lb block has no new field when the option is off)
- new binary, explicit `-deft_lb entry_bound_mode off -deft_lb entry_bound_k 2`: 66 / 66 identical

No differences.
