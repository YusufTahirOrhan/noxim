# v24 A2: model check of the XY and VN-split relations (formal/xy_check.py; impl_relation_check.UP_KEEP = True)

Relations are (chip_tm, ipos_tm, exit, entry). O1: on the interposer a VN0 packet is routed XY and a VN1 packet YX; the model takes the
interposer turn model from the VN of the state. Up channel = the VN the packet has on the interposer, destination chiplet VN1, the boundary
round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN, the F1 source rule.
Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).

## 2x2: 897 masks x 7 relations, 1646 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| CI_XY_XY (XY, XY, fixed, late) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| FULL_XY_XY (XY, XY, late, late) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| CI_XY_O1 (XY, O1, fixed, late) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| FULL_XY_O1 (XY, O1, late, late) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| FIXED_XY_O1 (XY, O1, fixed, fixed) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| CI_XY_YX (XY, YX, fixed, late), extra | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| FIXED_XY_YX (XY, YX, fixed, fixed), extra | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |

## 3x3: 22 masks x 5 relations, 79 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| CI_XY_XY (XY, XY, fixed, late) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |
| FULL_XY_XY (XY, XY, late, late) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |
| CI_XY_O1 (XY, O1, fixed, late) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |
| FULL_XY_O1 (XY, O1, late, late) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |
| FIXED_XY_O1 (XY, O1, fixed, fixed) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |

## 4x4: 2 masks x 5 relations, 114 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| CI_XY_XY (XY, XY, fixed, late) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |
| FULL_XY_XY (XY, XY, late, late) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |
| CI_XY_O1 (XY, O1, fixed, late) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |
| FULL_XY_O1 (XY, O1, late, late) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |
| FIXED_XY_O1 (XY, O1, fixed, fixed) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |

## Negative control

2x2, fault-free, fixed pair with XY, R3 and the F1 source rule removed (Up rule of the paper): CDG acyclic = False (expected False). The check can fail.

**All checks pass: True.**
