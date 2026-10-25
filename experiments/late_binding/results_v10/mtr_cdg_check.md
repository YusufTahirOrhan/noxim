# MTR: full-system CDG check (formal/mtr_cdg_check.py), fault-free

Physical-channel CDG of the complete MTR routing function (all ordered pairs of chiplet routers), and a check that every route uses only allowed boundary turns.

| chiplets | CDG nodes / edges | acyclic | turn violations |
|---|---|---|---|
| 2x2 | 400 / 688 | True | 0 |
| 3x3 | 960 / 1762 | True | 0 |
| 4x4 | 1760 / 3328 | True | 0 |

**All checks pass: True.**
