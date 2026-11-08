# Model check of the paper's Up-link VN rule (review v22, vn_up_check.py)

Same exploration as formal/impl_relation_check.py, with the Up channel in the VN the packet has on the interposer and the first hop inside the destination chiplet in VN1 (the paper's Algorithm 1 / Theorem III.4), against the repository's rule (Up channel always VN1).

| instance | mask | relation | Up rule | CDG acyclic | dead ends | livelock-free | longest path | CDG nodes / edges |
|---|---|---|---|---|---|---|---|---|
| 2x2 | fault-free | A_fixed_XY | repository (VN1) | True | 0 | True | 24 | 784 / 1376 |
| 2x2 | fault-free | A_fixed_XY | paper (keep) | True | 0 | True | 24 | 800 / 1424 |
| 2x2 | fault-free | CI_XY_OE | repository (VN1) | True | 0 | True | 24 | 860 / 1750 |
| 2x2 | fault-free | CI_XY_OE | paper (keep) | True | 0 | True | 24 | 876 / 1798 |
| 2x2 | fault-free | FULL_OE_OE | repository (VN1) | True | 0 | True | 24 | 860 / 1894 |
| 2x2 | fault-free | FULL_OE_OE | paper (keep) | True | 0 | True | 24 | 876 / 1942 |
| 2x2 | 0x1111 | A_fixed_XY | repository (VN1) | True | 0 | True | 24 | 672 / 1104 |
| 2x2 | 0x1111 | A_fixed_XY | paper (keep) | True | 0 | True | 24 | 684 / 1140 |
| 2x2 | 0x1111 | CI_XY_OE | repository (VN1) | True | 0 | True | 24 | 790 / 1498 |
| 2x2 | 0x1111 | CI_XY_OE | paper (keep) | True | 0 | True | 24 | 802 / 1534 |
| 2x2 | 0x1111 | FULL_OE_OE | repository (VN1) | True | 0 | True | 24 | 790 / 1642 |
| 2x2 | 0x1111 | FULL_OE_OE | paper (keep) | True | 0 | True | 24 | 802 / 1678 |
| 2x2 | 0x9C63 | A_fixed_XY | repository (VN1) | True | 0 | True | 23 | 608 / 908 |
| 2x2 | 0x9C63 | A_fixed_XY | paper (keep) | True | 0 | True | 23 | 616 / 932 |
| 2x2 | 0x9C63 | CI_XY_OE | repository (VN1) | True | 0 | True | 23 | 798 / 1316 |
| 2x2 | 0x9C63 | CI_XY_OE | paper (keep) | True | 0 | True | 23 | 806 / 1340 |
| 2x2 | 0x9C63 | FULL_OE_OE | repository (VN1) | True | 0 | True | 23 | 798 / 1460 |
| 2x2 | 0x9C63 | FULL_OE_OE | paper (keep) | True | 0 | True | 23 | 806 / 1484 |
| 2x2 | 0x7BDE | A_fixed_XY | repository (VN1) | True | 0 | True | 23 | 500 / 708 |
| 2x2 | 0x7BDE | A_fixed_XY | paper (keep) | True | 0 | True | 23 | 504 / 720 |
| 2x2 | 0x7BDE | CI_XY_OE | repository (VN1) | True | 0 | True | 23 | 718 / 1106 |
| 2x2 | 0x7BDE | CI_XY_OE | paper (keep) | True | 0 | True | 23 | 722 / 1118 |
| 2x2 | 0x7BDE | FULL_OE_OE | repository (VN1) | True | 0 | True | 23 | 718 / 1250 |
| 2x2 | 0x7BDE | FULL_OE_OE | paper (keep) | True | 0 | True | 23 | 722 / 1262 |
| 3x3 | fault-free | A_fixed_XY | repository (VN1) | True | 0 | True | 32 | 1884 / 3524 |
| 3x3 | fault-free | A_fixed_XY | paper (keep) | True | 0 | True | 32 | 1920 / 3632 |

**All checks pass: True** (106 s).
