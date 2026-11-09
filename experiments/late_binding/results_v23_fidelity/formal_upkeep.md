# v23 A2: model check with the paper's Up-link rule (formal/upkeep_check.py, impl_relation_check.UP_KEEP)

Up channel = the VN the packet has on the interposer (both VCs of a VL form one class), destination chiplet VN1, the
boundary round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN, the F1 source rule.
Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).

## 2x2: 897 masks x 4 relations, 2716 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT-P, DeFT-B, DeFT-Dis, DeFT-Ran, XY-SP) | 897 | 0 | 0 | 0 | 24 | 800 / 1424 |
| CI | 897 | 0 | 0 | 0 | 24 | 876 / 1798 |
| FULL | 897 | 0 | 0 | 0 | 24 | 876 / 1942 |
| fixed pair, odd-even (DeFT_OE_G) | 897 | 0 | 0 | 0 | 24 | 876 / 1942 |

## 3x3: 22 masks x 4 relations, 398 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT-P, DeFT-B, DeFT-Dis, DeFT-Ran, XY-SP) | 22 | 0 | 0 | 0 | 32 | 1920 / 3632 |
| CI | 22 | 0 | 0 | 0 | 32 | 2038 / 4418 |
| FULL | 22 | 0 | 0 | 0 | 32 | 2038 / 4742 |
| fixed pair, odd-even (DeFT_OE_G) | 22 | 0 | 0 | 0 | 32 | 2038 / 4742 |

## 4x4: 2 masks x 4 relations, 735 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT-P, DeFT-B, DeFT-Dis, DeFT-Ran, XY-SP) | 2 | 0 | 0 | 0 | 40 | 3520 / 6848 |
| CI | 2 | 0 | 0 | 0 | 40 | 3680 / 8174 |
| FULL | 2 | 0 | 0 | 0 | 40 | 3680 / 8750 |
| fixed pair, odd-even (DeFT_OE_G) | 2 | 0 | 0 | 0 | 40 | 3680 / 8750 |

## Negative control

2x2, fault-free, fixed pair with XY, R3 and the F1 source rule removed (Up rule of the paper): CDG acyclic = False (expected False). The check can fail.

**All checks pass: True.**
