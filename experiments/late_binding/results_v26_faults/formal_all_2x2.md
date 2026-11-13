# v26 A1: the model check on all fault patterns of 2x2 (experiments_v26.py a1, a1csv)

All 15^4 = 50625 masks that leave every chiplet a functional VL (the fault-free mask included), relations `CI_XY_XY` (the main row) and `CI_XY_O1` (the second row):
101250 checks, one line each in `formal_all_2x2.csv`. Model: `formal/impl_relation_check.py` with the settings of `formal/xy_check.py` (the paper's Up rule,
both VNs explored on Horizontal -> Down, R3 on the input VN, the F1 source rule). Per mask and relation: (1) CDG acyclic, (2) no dead-end state, (3) state graph
acyclic and its longest path, (4) every CDG edge is an edge of the fault-free CDG of the same relation.

## Result

| relation | masks | cyclic CDG | masks with dead ends | masks with a cyclic state graph | masks with CDG edges outside the fault-free CDG | all four checks pass | longest path (hops) | largest CDG (nodes / edges) | fault-free CDG (nodes / edges) |
|---|---|---|---|---|---|---|---|---|---|
| CI_XY_XY | 50625 | 0 | 0 | 0 | 0 | 50625 | 24 | 800 / 1424 | 800 / 1424 |
| CI_XY_O1 | 50625 | 0 | 0 | 0 | 0 | 50625 | 24 | 800 / 1424 | 800 / 1424 |

**101250 lines, all four checks pass on every line: yes.**

## By the number of faulty VLs

| faulty VLs | masks | checks | pass | longest path (hops): min - max | CDG edges: min - max |
|---|---|---|---|---|---|
| 0 | 1 | 2 | 2 | 24 - 24 | 1424 - 1424 |
| 1 | 16 | 32 | 32 | 24 - 24 | 1356 - 1362 |
| 2 | 120 | 240 | 240 | 23 - 24 | 1278 - 1304 |
| 3 | 560 | 1120 | 1120 | 23 - 24 | 1210 - 1242 |
| 4 | 1816 | 3632 | 3632 | 21 - 24 | 1132 - 1182 |
| 5 | 4320 | 8640 | 8640 | 21 - 24 | 1062 - 1124 |
| 6 | 7744 | 15488 | 15488 | 20 - 24 | 984 - 1064 |
| 7 | 10560 | 21120 | 21120 | 20 - 24 | 918 - 1006 |
| 8 | 10896 | 21792 | 21792 | 18 - 24 | 856 - 952 |
| 9 | 8320 | 16640 | 16640 | 18 - 24 | 794 - 890 |
| 10 | 4480 | 8960 | 8960 | 17 - 24 | 748 - 832 |
| 11 | 1536 | 3072 | 3072 | 17 - 24 | 702 - 778 |
| 12 | 256 | 512 | 512 | 16 - 24 | 660 - 728 |

Time: 66533 CPU-seconds in 1 call(s) (0.66 s per check), 6713 s wall in all.
