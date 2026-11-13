# v26 A2: the model check on 3x3 and 4x4 (experiments_v26.py a2)

Relations `CI_XY_XY` and `CI_XY_O1`, the model and the four checks of A1, with the per-destination exploration. Sets: 1 the fault-free mask; 2 every fault
combination of one chiplet with all other chiplets fault-free; 3 random masks from the whole space (every chiplet draws one of its 15 patterns);
4 the masks of Part B. One line per size, set, mask and relation in `formal_a2.csv`.

| size | set | masks | checks | cyclic CDG | dead ends | cyclic state graph | CDG edges outside the fault-free CDG | pass | longest path (hops) | faulty VLs: min - max | CPU-seconds: mean (max) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3x3 | 1 fault-free | 1 | 2 | 0 | 0 | 0 | 0 | 2 | 32 | 0 - 0 | 8 (8) |
| 3x3 | 2 one chiplet | 126 | 252 | 0 | 0 | 0 | 0 | 252 | 32 | 1 - 3 | 8 (10) |
| 3x3 | 3 random | 200 | 400 | 0 | 0 | 0 | 0 | 400 | 32 | 10 - 24 | 4 (6) |
| 3x3 | 4 Part B | 64 | 128 | 0 | 0 | 0 | 0 | 128 | 32 | 2 - 18 | 5 (7) |
| 4x4 | 1 fault-free | 1 | 2 | 0 | 0 | 0 | 0 | 2 | 40 | 0 - 0 | 37 (40) |
| 4x4 | 2 one chiplet | 224 | 448 | 0 | 0 | 0 | 0 | 448 | 40 | 1 - 3 | 38 (43) |
| 4x4 | 3 random | 60 | 120 | 0 | 0 | 0 | 0 | 120 | 40 | 21 - 38 | 15 (23) |
| 4x4 | 4 Part B | 64 | 128 | 0 | 0 | 0 | 0 | 128 | 40 | 4 - 32 | 26 (41) |

## 3x3, per relation over the four sets

| relation | masks | cyclic CDG | masks with dead ends | masks with a cyclic state graph | masks with CDG edges outside the fault-free CDG | all four checks pass | longest path (hops) | largest CDG (nodes / edges) | fault-free CDG (nodes / edges) |
|---|---|---|---|---|---|---|---|---|---|
| CI_XY_XY | 391 | 0 | 0 | 0 | 0 | 391 | 32 | 1920 / 3632 | 1920 / 3632 |
| CI_XY_O1 | 391 | 0 | 0 | 0 | 0 | 391 | 32 | 1920 / 3632 | 1920 / 3632 |

## 4x4, per relation over the four sets

| relation | masks | cyclic CDG | masks with dead ends | masks with a cyclic state graph | masks with CDG edges outside the fault-free CDG | all four checks pass | longest path (hops) | largest CDG (nodes / edges) | fault-free CDG (nodes / edges) |
|---|---|---|---|---|---|---|---|---|---|
| CI_XY_XY | 349 | 0 | 0 | 0 | 0 | 349 | 40 | 3520 / 6848 | 3520 / 6848 |
| CI_XY_O1 | 349 | 0 | 0 | 0 | 0 | 349 | 40 | 3520 / 6848 | 3520 / 6848 |

Time rule of 4x4 (pre-registered): 24 checks spread evenly over the list took 32 CPU-seconds on average; estimate for the 698 checks with 6 processes: 1.04 h.
Set 3 on 4x4 has 60 masks.

**1480 checks, all four checks pass on every line: yes.**
