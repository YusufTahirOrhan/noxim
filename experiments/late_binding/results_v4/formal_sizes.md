# Formal model of the implemented relations on larger instances (v4 step 3)

formal/impl_relation_check.py `size` mode (parametric deft_cdg_model.set_size). Same relations
and checks as v1 (results/impl_relation_check_all.txt): CDG acyclicity, dead-end states,
state-graph acyclicity with the longest path.

## 3x3 chiplets of 4x4 routers (144 chiplet routers, 36 VLs)

22 fault masks x 3 relations = 66 checks; 4 processes, 145 s wall.

| mask | faulty VLs | relation | CDG acyclic | dead ends | livelock-free | longest path (hops) | CDG nodes / edges | time (s) |
|---|---|---|---|---|---|---|---|---|
| fault-free | 0 | A_fixed_XY | True | 0 | True | 32 | 1884 / 3524 | 18 |
| fault-free | 0 | CI_XY_OE | True | 0 | True | 32 | 2002 / 4310 | 17 |
| fault-free | 0 | FULL_OE_OE | True | 0 | True | 32 | 2002 / 4634 | 17 |
| north per chiplet | 9 | A_fixed_XY | True | 0 | True | 32 | 1611 / 2781 | 11 |
| north per chiplet | 9 | CI_XY_OE | True | 0 | True | 32 | 1885 / 3793 | 11 |
| north per chiplet | 9 | FULL_OE_OE | True | 0 | True | 32 | 1885 / 4117 | 12 |
| random 1 | 8 | A_fixed_XY | True | 0 | True | 32 | 1772 / 3092 | 11 |
| random 1 | 8 | CI_XY_OE | True | 0 | True | 32 | 1978 / 4046 | 11 |
| random 1 | 8 | FULL_OE_OE | True | 0 | True | 32 | 1978 / 4370 | 11 |
| random 2 | 14 | A_fixed_XY | True | 0 | True | 32 | 1592 / 2636 | 6 |
| random 2 | 14 | CI_XY_OE | True | 0 | True | 32 | 1864 / 3628 | 8 |
| random 2 | 14 | FULL_OE_OE | True | 0 | True | 32 | 1864 / 3952 | 9 |
| random 3 | 12 | A_fixed_XY | True | 0 | True | 32 | 1704 / 2878 | 9 |
| random 3 | 12 | CI_XY_OE | True | 0 | True | 32 | 1948 / 3870 | 10 |
| random 3 | 12 | FULL_OE_OE | True | 0 | True | 32 | 1948 / 4194 | 10 |
| random 4 | 23 | A_fixed_XY | True | 0 | True | 29 | 1369 / 2055 | 2 |
| random 4 | 23 | CI_XY_OE | True | 0 | True | 29 | 1787 / 3127 | 3 |
| random 4 | 23 | FULL_OE_OE | True | 0 | True | 29 | 1787 / 3451 | 4 |
| random 5 | 17 | A_fixed_XY | True | 0 | True | 32 | 1565 / 2511 | 5 |
| random 5 | 17 | CI_XY_OE | True | 0 | True | 32 | 1859 / 3559 | 6 |
| random 5 | 17 | FULL_OE_OE | True | 0 | True | 32 | 1859 / 3883 | 7 |
| random 6 | 13 | A_fixed_XY | True | 0 | True | 31 | 1639 / 2727 | 7 |
| random 6 | 13 | CI_XY_OE | True | 0 | True | 31 | 1899 / 3687 | 8 |
| random 6 | 13 | FULL_OE_OE | True | 0 | True | 31 | 1899 / 4011 | 8 |
| random 7 | 9 | A_fixed_XY | True | 0 | True | 32 | 1715 / 2945 | 11 |
| random 7 | 9 | CI_XY_OE | True | 0 | True | 32 | 1975 / 4007 | 12 |
| random 7 | 9 | FULL_OE_OE | True | 0 | True | 32 | 1975 / 4331 | 11 |
| random 8 | 11 | A_fixed_XY | True | 0 | True | 32 | 1703 / 2879 | 9 |
| random 8 | 11 | CI_XY_OE | True | 0 | True | 32 | 1969 / 3943 | 10 |
| random 8 | 11 | FULL_OE_OE | True | 0 | True | 32 | 1969 / 4267 | 11 |
| random 9 | 16 | A_fixed_XY | True | 0 | True | 32 | 1590 / 2556 | 5 |
| random 9 | 16 | CI_XY_OE | True | 0 | True | 32 | 1936 / 3752 | 7 |
| random 9 | 16 | FULL_OE_OE | True | 0 | True | 32 | 1936 / 4076 | 7 |
| random 10 | 13 | A_fixed_XY | True | 0 | True | 31 | 1647 / 2755 | 7 |
| random 10 | 13 | CI_XY_OE | True | 0 | True | 31 | 1913 / 3689 | 8 |
| random 10 | 13 | FULL_OE_OE | True | 0 | True | 31 | 1913 / 4013 | 8 |
| random 11 | 15 | A_fixed_XY | True | 0 | True | 29 | 1623 / 2655 | 6 |
| random 11 | 15 | CI_XY_OE | True | 0 | True | 29 | 1861 / 3489 | 7 |
| random 11 | 15 | FULL_OE_OE | True | 0 | True | 29 | 1861 / 3813 | 7 |
| random 12 | 8 | A_fixed_XY | True | 0 | True | 31 | 1756 / 3086 | 11 |
| random 12 | 8 | CI_XY_OE | True | 0 | True | 31 | 1978 / 4006 | 11 |
| random 12 | 8 | FULL_OE_OE | True | 0 | True | 31 | 1978 / 4330 | 12 |
| random 13 | 10 | A_fixed_XY | True | 0 | True | 32 | 1734 / 2988 | 9 |
| random 13 | 10 | CI_XY_OE | True | 0 | True | 32 | 1924 / 3814 | 9 |
| random 13 | 10 | FULL_OE_OE | True | 0 | True | 32 | 1924 / 4138 | 9 |
| random 14 | 16 | A_fixed_XY | True | 0 | True | 29 | 1548 / 2516 | 4 |
| random 14 | 16 | CI_XY_OE | True | 0 | True | 29 | 1828 / 3422 | 6 |
| random 14 | 16 | FULL_OE_OE | True | 0 | True | 29 | 1828 / 3746 | 6 |
| random 15 | 8 | A_fixed_XY | True | 0 | True | 31 | 1728 / 3030 | 10 |
| random 15 | 8 | CI_XY_OE | True | 0 | True | 31 | 1920 / 3830 | 10 |
| random 15 | 8 | FULL_OE_OE | True | 0 | True | 31 | 1920 / 4154 | 10 |
| random 16 | 19 | A_fixed_XY | True | 0 | True | 32 | 1507 / 2347 | 3 |
| random 16 | 19 | CI_XY_OE | True | 0 | True | 32 | 1867 / 3397 | 5 |
| random 16 | 19 | FULL_OE_OE | True | 0 | True | 32 | 1867 / 3721 | 6 |
| random 17 | 10 | A_fixed_XY | True | 0 | True | 31 | 1710 / 2942 | 8 |
| random 17 | 10 | CI_XY_OE | True | 0 | True | 31 | 1926 / 3808 | 9 |
| random 17 | 10 | FULL_OE_OE | True | 0 | True | 31 | 1926 / 4132 | 9 |
| random 18 | 8 | A_fixed_XY | True | 0 | True | 32 | 1772 / 3086 | 10 |
| random 18 | 8 | CI_XY_OE | True | 0 | True | 32 | 1978 / 4072 | 11 |
| random 18 | 8 | FULL_OE_OE | True | 0 | True | 32 | 1978 / 4396 | 11 |
| random 19 | 12 | A_fixed_XY | True | 0 | True | 29 | 1616 / 2750 | 7 |
| random 19 | 12 | CI_XY_OE | True | 0 | True | 29 | 1822 / 3496 | 8 |
| random 19 | 12 | FULL_OE_OE | True | 0 | True | 29 | 1822 / 3820 | 8 |
| random 20 | 11 | A_fixed_XY | True | 0 | True | 29 | 1683 / 2865 | 8 |
| random 20 | 11 | CI_XY_OE | True | 0 | True | 29 | 1939 / 3783 | 8 |
| random 20 | 11 | FULL_OE_OE | True | 0 | True | 29 | 1939 / 4107 | 8 |

**All checks pass: True** (acyclic CDG, no dead ends, no livelock).

Random masks: random 1: [1, 3, 16, 18, 20, 28, 30, 31]; random 2: [0, 2, 3, 4, 8, 10, 11, 14, 16, 17, 18, 20, 21, 26]; random 3: [7, 9, 10, 11, 12, 14, 17, 25, 27, 28, 30, 31]; random 4: [0, 1, 3, 4, 6, 7, 10, 11, 14, 15, 16, 17, 19, 20, 21, 23, 25, 26, 27, 28, 29, 33, 34]; random 5: [4, 5, 7, 9, 12, 13, 15, 19, 20, 21, 22, 25, 27, 28, 29, 30, 33]; random 6: [1, 9, 10, 11, 19, 20, 22, 29, 30, 31, 32, 33, 34]; random 7: [4, 11, 12, 16, 19, 24, 28, 31, 35]; random 8: [2, 5, 6, 17, 18, 19, 20, 23, 29, 30, 32]; random 9: [2, 4, 8, 10, 12, 14, 17, 18, 21, 22, 25, 28, 29, 31, 32, 35]; random 10: [1, 3, 6, 8, 9, 10, 12, 19, 22, 27, 32, 34, 35]; random 11: [4, 5, 7, 8, 9, 10, 12, 14, 15, 17, 20, 27, 31, 33, 34]; random 12: [0, 15, 17, 25, 27, 30, 32, 35]; random 13: [6, 7, 8, 9, 10, 16, 17, 18, 21, 27]; random 14: [0, 3, 9, 12, 15, 16, 17, 19, 21, 22, 26, 27, 29, 30, 31, 35]; random 15: [3, 8, 9, 11, 15, 22, 30, 34]; random 16: [3, 4, 8, 10, 11, 15, 16, 17, 18, 20, 22, 24, 25, 28, 30, 31, 33, 34, 35]; random 17: [8, 16, 18, 22, 27, 28, 31, 32, 33, 34]; random 18: [7, 12, 14, 20, 22, 24, 28, 29]; random 19: [1, 3, 4, 8, 14, 21, 26, 27, 30, 33, 34, 35]; random 20: [4, 7, 15, 19, 25, 26, 27, 28, 29, 33, 34]

## 4x4 chiplets of 4x4 routers (256 chiplet routers, 64 VLs)

2 fault masks x 3 relations = 6 checks; 3 processes, 84 s wall; per-destination exploration (job_lean).

| mask | faulty VLs | relation | CDG acyclic | dead ends | livelock-free | longest path (hops) | CDG nodes / edges | time (s) |
|---|---|---|---|---|---|---|---|---|
| fault-free | 0 | A_fixed_XY | True | 0 | True | 40 | 3456 / 6656 | 43 |
| fault-free | 0 | CI_XY_OE | True | 0 | True | 40 | 3616 / 7982 | 50 |
| fault-free | 0 | FULL_OE_OE | True | 0 | True | 40 | 3616 / 8558 | 51 |
| north per chiplet | 16 | A_fixed_XY | True | 0 | True | 40 | 2952 / 5216 | 23 |
| north per chiplet | 16 | CI_XY_OE | True | 0 | True | 40 | 3446 / 7118 | 32 |
| north per chiplet | 16 | FULL_OE_OE | True | 0 | True | 40 | 3446 / 7694 | 33 |

**All checks pass: True** (acyclic CDG, no dead ends, no livelock).

## Notes
* 2x2 (default instance): the v1 result (results/impl_relation_check_all.txt, 897 masks) is unchanged;
  set_size(2, 2, 4, 4) reproduces the fixed model exactly (same node list and VL positions).
* Run time and memory: one 3x3 check takes 13-16 s and about 1.5 GB with the whole state graph in
  memory (66 checks: 145 s on 4 processes). A 4x4 check with the whole state graph exceeded the
  7.9 GB available in WSL (killed by the OOM killer; the WSL VM had to be restarted). The 4x4 checks
  therefore use `job_lean`, which explores one destination at a time. This is exact: states carry
  their destination and no transition changes it, so dead ends add up, the state graph is acyclic
  iff every per-destination part is, the longest path is the maximum, and the CDG is the union of
  the per-destination dependencies. job_lean reproduces job on 21 / 21 checks (2x2 with 3 masks,
  3x3 with 4 masks, all three relations). With it, one 4x4 check takes 23-51 s and about 90 MB.
* 4x4 was checked on 2 masks only (fault-free and north per chiplet), as instructed.
