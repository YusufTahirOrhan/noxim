# Formal check of the bounded initial entry masks on 3x3 (v7 step 1)

formal/impl_relation_check.py `size 3 3 ... bounded lean`: the initial entry mask of every
source-destination pair ranges over **every non-empty subset** of the functional entry VLs of the
destination chiplet (CI: every functional exit singleton; FULL: all functional exits), which contains every
mask that `entry_bound_mode` min or lut can produce for any k and any LUT. Monotone pruning, VN rules and
turn models as in the v4 size check. Fault masks: fault-free, one VL per chiplet (north), and the first 4
random masks of the v4 check (seed 7).

## 3x3 chiplets of 4x4 routers (144 chiplet routers, 36 VLs)

6 fault masks x 2 relations = 12 checks; 6 processes, 95 s wall; per-destination exploration (job_lean).

| mask | faulty VLs | relation | CDG acyclic | dead ends | livelock-free | longest path (hops) | CDG nodes / edges | time (s) |
|---|---|---|---|---|---|---|---|---|
| fault-free | 0 | CI_XY_OE_anysubset | True | 0 | True | 32 | 2002 / 4310 | 94 |
| fault-free | 0 | FULL_OE_OE_anysubset | True | 0 | True | 32 | 2002 / 4634 | 95 |
| north per chiplet | 9 | CI_XY_OE_anysubset | True | 0 | True | 32 | 1885 / 3793 | 33 |
| north per chiplet | 9 | FULL_OE_OE_anysubset | True | 0 | True | 32 | 1885 / 4117 | 34 |
| random 1 | 8 | CI_XY_OE_anysubset | True | 0 | True | 32 | 1978 / 4046 | 54 |
| random 1 | 8 | FULL_OE_OE_anysubset | True | 0 | True | 32 | 1978 / 4370 | 54 |
| random 2 | 14 | CI_XY_OE_anysubset | True | 0 | True | 32 | 1864 / 3628 | 22 |
| random 2 | 14 | FULL_OE_OE_anysubset | True | 0 | True | 32 | 1864 / 3952 | 23 |
| random 3 | 12 | CI_XY_OE_anysubset | True | 0 | True | 32 | 1948 / 3870 | 29 |
| random 3 | 12 | FULL_OE_OE_anysubset | True | 0 | True | 32 | 1948 / 4194 | 29 |
| random 4 | 23 | CI_XY_OE_anysubset | True | 0 | True | 29 | 1787 / 3127 | 4 |
| random 4 | 23 | FULL_OE_OE_anysubset | True | 0 | True | 29 | 1787 / 3451 | 4 |

**All checks pass: True** (acyclic CDG, no dead ends, no livelock).

Random masks: random 1: [1, 3, 16, 18, 20, 28, 30, 31]; random 2: [0, 2, 3, 4, 8, 10, 11, 14, 16, 17, 18, 20, 21, 26]; random 3: [7, 9, 10, 11, 12, 14, 17, 25, 27, 28, 30, 31]; random 4: [0, 1, 3, 4, 6, 7, 10, 11, 14, 15, 16, 17, 19, 20, 21, 23, 25, 26, 27, 28, 29, 33, 34]

