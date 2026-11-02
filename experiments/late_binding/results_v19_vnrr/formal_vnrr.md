# v19 K2: model check with the boundary round-robin (formal/vnrr_check.py)

Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).

## 2x2: 897 masks x 4 relations, 770 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP) | 897 | 0 | 0 | 0 | 24 | 784 / 1376 |
| CI | 897 | 0 | 0 | 0 | 24 | 860 / 1750 |
| FULL | 897 | 0 | 0 | 0 | 24 | 860 / 1894 |
| fixed pair, odd-even (DeFT_OE_G) | 897 | 0 | 0 | 0 | 24 | 860 / 1894 |

## 3x3: 22 masks x 4 relations, 100 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP) | 22 | 0 | 0 | 0 | 32 | 1884 / 3524 |
| CI | 22 | 0 | 0 | 0 | 32 | 2002 / 4310 |
| FULL | 22 | 0 | 0 | 0 | 32 | 2002 / 4634 |
| fixed pair, odd-even (DeFT_OE_G) | 22 | 0 | 0 | 0 | 32 | 2002 / 4634 |

## 4x4: 2 masks x 4 relations, 190 s wall

| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |
|---|---|---|---|---|---|---|
| fixed pair, XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP) | 2 | 0 | 0 | 0 | 40 | 3456 / 6656 |
| CI | 2 | 0 | 0 | 0 | 40 | 3616 / 7982 |
| FULL | 2 | 0 | 0 | 0 | 40 | 3616 / 8558 |
| fixed pair, odd-even (DeFT_OE_G) | 2 | 0 | 0 | 0 | 40 | 3616 / 8558 |

## Negative control

2x2, fault-free, fixed pair with XY, R3 and the F1 source rule removed: CDG acyclic = False (expected False). The check can fail.

**All checks pass: True.**
