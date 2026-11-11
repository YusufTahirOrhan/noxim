# v25 Part C: model check on the masks of the fault sweep (experiments_v25.py c_formal)

Relations `CI_XY_XY` (late entry, XY on the interposer: the main row) and `CI_XY_O1` (the VN-split order: the second row), with the paper's Up rule
(`impl_relation_check.UP_KEEP = True`), the boundary round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN and the F1 source rule,
as in `results_v24_xy/formal_xy.md`. Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).

| size | k | mask | relation | CDG acyclic | dead-end states | livelock free | longest path (hops) | CDG nodes / edges | seconds |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | 1 | 0x2818 | CI_XY_XY | yes | 0 | yes | 24 | 696 / 1154 | 1 |
| 2x2 | 1 | 0x2818 | CI_XY_O1 | yes | 0 | yes | 24 | 696 / 1154 | 1 |
| 2x2 | 1 | 0x2824 | CI_XY_XY | yes | 0 | yes | 24 | 696 / 1152 | 1 |
| 2x2 | 1 | 0x2824 | CI_XY_O1 | yes | 0 | yes | 24 | 696 / 1152 | 1 |
| 2x2 | 1 | 0x8228 | CI_XY_XY | yes | 0 | yes | 24 | 720 / 1180 | 1 |
| 2x2 | 1 | 0x8228 | CI_XY_O1 | yes | 0 | yes | 24 | 720 / 1180 | 1 |
| 2x2 | 2 | 0xAC5A | CI_XY_XY | yes | 0 | yes | 24 | 606 / 926 | 0 |
| 2x2 | 2 | 0xAC5A | CI_XY_O1 | yes | 0 | yes | 24 | 606 / 926 | 1 |
| 2x2 | 2 | 0xC653 | CI_XY_XY | yes | 0 | yes | 24 | 588 / 906 | 0 |
| 2x2 | 2 | 0xC653 | CI_XY_O1 | yes | 0 | yes | 24 | 588 / 906 | 1 |
| 2x2 | 2 | 0x6A63 | CI_XY_XY | yes | 0 | yes | 22 | 582 / 900 | 0 |
| 2x2 | 2 | 0x6A63 | CI_XY_O1 | yes | 0 | yes | 22 | 582 / 900 | 0 |
| 2x2 | 3 | 0xDE7D | CI_XY_XY | yes | 0 | yes | 20 | 480 / 696 | 0 |
| 2x2 | 3 | 0xDE7D | CI_XY_O1 | yes | 0 | yes | 20 | 480 / 696 | 0 |
| 2x2 | 3 | 0xDE7E | CI_XY_XY | yes | 0 | yes | 23 | 486 / 702 | 0 |
| 2x2 | 3 | 0xDE7E | CI_XY_O1 | yes | 0 | yes | 23 | 486 / 702 | 0 |
| 2x2 | 3 | 0xBDBD | CI_XY_XY | yes | 0 | yes | 21 | 464 / 680 | 0 |
| 2x2 | 3 | 0xBDBD | CI_XY_O1 | yes | 0 | yes | 21 | 464 / 680 | 0 |
| 3x3 | 1 | 0x414418228 | CI_XY_XY | yes | 0 | yes | 31 | 1756 / 3082 | 7 |
| 3x3 | 1 | 0x414418228 | CI_XY_O1 | yes | 0 | yes | 31 | 1756 / 3082 | 7 |
| 3x3 | 1 | 0x184484482 | CI_XY_XY | yes | 0 | yes | 32 | 1750 / 3050 | 7 |
| 3x3 | 1 | 0x184484482 | CI_XY_O1 | yes | 0 | yes | 32 | 1750 / 3050 | 8 |
| 3x3 | 1 | 0x484124122 | CI_XY_XY | yes | 0 | yes | 32 | 1754 / 3068 | 7 |
| 3x3 | 1 | 0x484124122 | CI_XY_O1 | yes | 0 | yes | 32 | 1754 / 3068 | 7 |
| 3x3 | 2 | 0x996553A66 | CI_XY_XY | yes | 0 | yes | 32 | 1534 / 2442 | 4 |
| 3x3 | 2 | 0x996553A66 | CI_XY_O1 | yes | 0 | yes | 32 | 1534 / 2442 | 4 |
| 3x3 | 2 | 0x9C353C536 | CI_XY_XY | yes | 0 | yes | 32 | 1570 / 2506 | 4 |
| 3x3 | 2 | 0x9C353C536 | CI_XY_O1 | yes | 0 | yes | 32 | 1570 / 2506 | 4 |
| 3x3 | 2 | 0xC55CAA6CA | CI_XY_XY | yes | 0 | yes | 31 | 1504 / 2406 | 4 |
| 3x3 | 2 | 0xC55CAA6CA | CI_XY_O1 | yes | 0 | yes | 31 | 1504 / 2406 | 4 |
| 3x3 | 3 | 0xBB7D7D77B | CI_XY_XY | yes | 0 | yes | 28 | 1216 / 1774 | 2 |
| 3x3 | 3 | 0xBB7D7D77B | CI_XY_O1 | yes | 0 | yes | 28 | 1216 / 1774 | 2 |
| 3x3 | 3 | 0xBBD7EDEEE | CI_XY_XY | yes | 0 | yes | 32 | 1202 / 1750 | 2 |
| 3x3 | 3 | 0xBBD7EDEEE | CI_XY_O1 | yes | 0 | yes | 32 | 1202 / 1750 | 2 |
| 3x3 | 3 | 0x7EDE7EDEE | CI_XY_XY | yes | 0 | yes | 29 | 1228 / 1792 | 2 |
| 3x3 | 3 | 0x7EDE7EDEE | CI_XY_O1 | yes | 0 | yes | 29 | 1228 / 1792 | 2 |
| 4x4 | 1 | 0x8214882212828814 | CI_XY_XY | yes | 0 | yes | 40 | 3296 / 5978 | 29 |
| 4x4 | 1 | 0x8214882212828814 | CI_XY_O1 | yes | 0 | yes | 40 | 3296 / 5978 | 30 |
| 4x4 | 1 | 0x8882482122418442 | CI_XY_XY | yes | 0 | yes | 40 | 3288 / 5952 | 29 |
| 4x4 | 1 | 0x8882482122418442 | CI_XY_O1 | yes | 0 | yes | 40 | 3288 / 5952 | 30 |
| 4x4 | 1 | 0x8814142144214424 | CI_XY_XY | yes | 0 | yes | 40 | 3264 / 5892 | 29 |
| 4x4 | 1 | 0x8814142144214424 | CI_XY_O1 | yes | 0 | yes | 40 | 3264 / 5892 | 30 |
| 4x4 | 2 | 0x9C665369659A555A | CI_XY_XY | yes | 0 | yes | 40 | 2952 / 4900 | 17 |
| 4x4 | 2 | 0x9C665369659A555A | CI_XY_O1 | yes | 0 | yes | 40 | 2952 / 4900 | 18 |
| 4x4 | 2 | 0x996A966563965959 | CI_XY_XY | yes | 0 | yes | 39 | 2962 / 4960 | 18 |
| 4x4 | 2 | 0x996A966563965959 | CI_XY_O1 | yes | 0 | yes | 39 | 2962 / 4960 | 20 |
| 4x4 | 2 | 0x9CA593A6AC6A969C | CI_XY_XY | yes | 0 | yes | 40 | 2978 / 4938 | 18 |
| 4x4 | 2 | 0x9CA593A6AC6A969C | CI_XY_O1 | yes | 0 | yes | 40 | 2978 / 4938 | 18 |
| 4x4 | 3 | 0xDEB77DEDDBBED7D7 | CI_XY_XY | yes | 0 | yes | 40 | 2416 / 3584 | 8 |
| 4x4 | 3 | 0xDEB77DEDDBBED7D7 | CI_XY_O1 | yes | 0 | yes | 40 | 2416 / 3584 | 8 |
| 4x4 | 3 | 0x7DD7B77DDEBDDDDD | CI_XY_XY | yes | 0 | yes | 40 | 2316 / 3440 | 8 |
| 4x4 | 3 | 0x7DD7B77DDEBDDDDD | CI_XY_O1 | yes | 0 | yes | 40 | 2316 / 3440 | 8 |
| 4x4 | 3 | 0x77E7BBD7EBEE7BDB | CI_XY_XY | yes | 0 | yes | 36 | 2292 / 3406 | 7 |
| 4x4 | 3 | 0x77E7BBD7EBEE7BDB | CI_XY_O1 | yes | 0 | yes | 36 | 2292 / 3406 | 8 |

Wall time with 2 processes: 2x2 6 s, 3x3 41 s, 4x4 171 s.
2x2 masks of the sweep that are among the 897 masks checked in round 24 (not repeated): none; all nine were checked here.
All 4x4 masks were checked (the 3 h limit of the pre-registration was not reached).

**54 checks, all pass: yes.**
