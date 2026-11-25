# v29 Part C: tables added to the report (extra_v29.py c)

Descriptive; not in the pre-registration and no test. X.2 was defined on 25 November while C1 was running, before any of its results had been read; X.3 was
added after they had been read (`DECISIONS.md`, "Tables added after the results").

## X.2 The main row against the best reference, read at the area of the main row

A reference with 5-flit buffers has less area than the main row when the hierarchy is kept and more in the other two forms of the synthesis; one with 6-flit
buffers has more in every form (`report/summary_hw_E3.md`). The table reads the three measured comparisons (references with 4-flit buffers: round 25; with 5-flit and
6-flit buffers: C1; six scenarios, ten seeds, the best row of the set per scenario and metric at each depth) at the area of the main row: per seed the log ratio is
interpolated linearly in the system area between the two neighbouring depths, then the effect and its 95 % interval over the seeds are computed as everywhere.
No router with 4.6 or 5.4-flit buffers exists; the column says where the main row would stand against a reference that spent the same area on buffers, if the
effect moved evenly with the area. The areas are taken as exact (the flow spreads by about 1 % on unchanged logic). **Break-even**: the buffer depth of the
references (and its area relative to DeFT at depth 4, in the form of the block) at which the interpolated mean effect stops being in favour of the main row.

### hierarchy kept

| size | area: main row; d5; d6 | against | metric | 4-flit | 5-flit | 6-flit | at the area of the main row | break-even depth (area) |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1.251; 1.168; 1.321 | the best of the two DeFT variants | THR | +4.4 [+4.3, +4.6] | +1.6 [+1.4, +1.9] | -0.5 [-0.8, -0.2] | **+0.5 [+0.3, +0.7]** | 5.8 flits (1.286) |
| 2x2 | 1.251; 1.168; 1.321 | the best of the two DeFT variants | LAT | -23.9 [-26.8, -20.9] | -15.3 [-18.0, -12.6] | -10.1 [-12.4, -7.7] | **-12.5 [-14.9, -10.0]** | not up to 6-flit buffers |
| 2x2 | 1.251; 1.168; 1.321 | the best of MTR and RC | THR | +1.5 [+1.1, +1.9] | -0.4 [-0.7, -0.0] | -2.1 [-2.3, -1.9] | **-1.3 [-1.6, -1.0]** | 4.8 flits (1.135) |
| 2x2 | 1.251; 1.168; 1.321 | the best of MTR and RC | LAT | -11.8 [-14.4, -9.1] | -5.1 [-7.9, -2.3] | -1.2 [-3.4, +1.1] | **-3.0 [-5.4, -0.5]** | not up to 6-flit buffers |
| 2x2 | 1.251; 1.168; 1.321 | the best of the four | THR | +0.0 [-0.3, +0.3] | -1.8 [-2.1, -1.5] | -3.4 [-3.6, -3.2] | **-2.7 [-2.9, -2.5]** | 4.0 flits (1.000) |
| 2x2 | 1.251; 1.168; 1.321 | the best of the four | LAT | -11.1 [-13.2, -8.8] | -5.1 [-7.8, -2.4] | -1.2 [-3.4, +1.1] | **-3.0 [-5.4, -0.5]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of the two DeFT variants | THR | +9.2 [+8.7, +9.6] | +6.4 [+5.9, +6.9] | +3.9 [+3.5, +4.2] | **+5.6 [+5.2, +5.9]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of the two DeFT variants | LAT | -25.1 [-26.7, -23.6] | -15.1 [-16.1, -14.2] | -9.9 [-10.7, -9.1] | **-13.4 [-14.3, -12.6]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of MTR and RC | THR | +9.2 [+8.8, +9.6] | +7.4 [+6.9, +7.9] | +5.8 [+5.3, +6.4] | **+6.9 [+6.4, +7.4]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of MTR and RC | LAT | -15.2 [-17.7, -12.7] | -9.1 [-11.0, -7.1] | -5.9 [-7.8, -3.9] | **-8.0 [-9.9, -6.1]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of the four | THR | +6.7 [+6.3, +7.0] | +4.8 [+4.3, +5.2] | +2.9 [+2.5, +3.3] | **+4.1 [+3.7, +4.5]** | not up to 6-flit buffers |
| 3x3 | 1.217; 1.167; 1.319 | the best of the four | LAT | -9.7 [-10.9, -8.4] | -4.7 [-5.7, -3.7] | -2.2 [-3.1, -1.3] | **-3.9 [-4.8, -3.0]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of the two DeFT variants | THR | +8.4 [+8.1, +8.7] | +6.0 [+5.7, +6.4] | +3.8 [+3.6, +4.0] | **+5.3 [+5.0, +5.6]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of the two DeFT variants | LAT | -25.7 [-27.7, -23.7] | -16.0 [-17.4, -14.7] | -10.1 [-11.2, -8.9] | **-14.0 [-15.2, -12.8]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of MTR and RC | THR | +8.8 [+8.2, +9.3] | +6.4 [+5.8, +7.0] | +4.7 [+4.2, +5.2] | **+5.8 [+5.3, +6.3]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of MTR and RC | LAT | -19.8 [-23.6, -15.8] | -13.5 [-17.1, -9.7] | -9.8 [-13.3, -6.0] | **-12.2 [-15.8, -8.5]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of the four | THR | +6.0 [+5.7, +6.3] | +4.0 [+3.6, +4.3] | +2.3 [+2.1, +2.6] | **+3.4 [+3.1, +3.6]** | not up to 6-flit buffers |
| 4x4 | 1.218; 1.166; 1.317 | the best of the four | LAT | -13.2 [-14.6, -11.7] | -7.8 [-8.8, -6.7] | -4.3 [-5.8, -2.9] | **-6.6 [-7.7, -5.5]** | not up to 6-flit buffers |

### core kept

| size | area: main row; d5; d6 | against | metric | 4-flit | 5-flit | 6-flit | at the area of the main row | break-even depth (area) |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1.161; 1.175; 1.341 | the best of the two DeFT variants | THR | +4.4 [+4.3, +4.6] | +1.6 [+1.4, +1.9] | -0.5 [-0.8, -0.2] | **+1.9 [+1.6, +2.1]** | 5.8 flits (1.303) |
| 2x2 | 1.161; 1.175; 1.341 | the best of the two DeFT variants | LAT | -23.9 [-26.8, -20.9] | -15.3 [-18.0, -12.6] | -10.1 [-12.4, -7.7] | **-16.0 [-18.7, -13.3]** | not up to 6-flit buffers |
| 2x2 | 1.161; 1.175; 1.341 | the best of MTR and RC | THR | +1.5 [+1.1, +1.9] | -0.4 [-0.7, -0.0] | -2.1 [-2.3, -1.9] | **-0.2 [-0.6, +0.1]** | 4.8 flits (1.141) |
| 2x2 | 1.161; 1.175; 1.341 | the best of MTR and RC | LAT | -11.8 [-14.4, -9.1] | -5.1 [-7.9, -2.3] | -1.2 [-3.4, +1.1] | **-5.7 [-8.4, -2.9]** | not up to 6-flit buffers |
| 2x2 | 1.161; 1.175; 1.341 | the best of the four | THR | +0.0 [-0.3, +0.3] | -1.8 [-2.1, -1.5] | -3.4 [-3.6, -3.2] | **-1.6 [-1.9, -1.4]** | 4.0 flits (1.000) |
| 2x2 | 1.161; 1.175; 1.341 | the best of the four | LAT | -11.1 [-13.2, -8.8] | -5.1 [-7.8, -2.4] | -1.2 [-3.4, +1.1] | **-5.6 [-8.3, -2.9]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of the two DeFT variants | THR | +9.2 [+8.7, +9.6] | +6.4 [+5.9, +6.9] | +3.9 [+3.5, +4.2] | **+7.1 [+6.6, +7.5]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of the two DeFT variants | LAT | -25.1 [-26.7, -23.6] | -15.1 [-16.1, -14.2] | -9.9 [-10.7, -9.1] | **-17.7 [-18.8, -16.6]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of MTR and RC | THR | +9.2 [+8.8, +9.6] | +7.4 [+6.9, +7.9] | +5.8 [+5.3, +6.4] | **+7.8 [+7.4, +8.3]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of MTR and RC | LAT | -15.2 [-17.7, -12.7] | -9.1 [-11.0, -7.1] | -5.9 [-7.8, -3.9] | **-10.6 [-12.6, -8.6]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of the four | THR | +6.7 [+6.3, +7.0] | +4.8 [+4.3, +5.2] | +2.9 [+2.5, +3.3] | **+5.2 [+4.9, +5.6]** | not up to 6-flit buffers |
| 3x3 | 1.130; 1.172; 1.336 | the best of the four | LAT | -9.7 [-10.9, -8.4] | -4.7 [-5.7, -3.7] | -2.2 [-3.1, -1.3] | **-6.0 [-7.0, -4.9]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of the two DeFT variants | THR | +8.4 [+8.1, +8.7] | +6.0 [+5.7, +6.4] | +3.8 [+3.6, +4.0] | **+6.6 [+6.2, +6.9]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of the two DeFT variants | LAT | -25.7 [-27.7, -23.7] | -16.0 [-17.4, -14.7] | -10.1 [-11.2, -8.9] | **-18.3 [-19.8, -16.9]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of MTR and RC | THR | +8.8 [+8.2, +9.3] | +6.4 [+5.8, +7.0] | +4.7 [+4.2, +5.2] | **+6.9 [+6.4, +7.5]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of MTR and RC | LAT | -19.8 [-23.6, -15.8] | -13.5 [-17.1, -9.7] | -9.8 [-13.3, -6.0] | **-15.0 [-18.6, -11.2]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of the four | THR | +6.0 [+5.7, +6.3] | +4.0 [+3.6, +4.3] | +2.3 [+2.1, +2.6] | **+4.4 [+4.1, +4.7]** | not up to 6-flit buffers |
| 4x4 | 1.133; 1.171; 1.335 | the best of the four | LAT | -13.2 [-14.6, -11.7] | -7.8 [-8.8, -6.7] | -4.3 [-5.8, -2.9] | **-9.0 [-10.1, -7.9]** | not up to 6-flit buffers |

### flattened

| size | area: main row; d5; d6 | against | metric | 4-flit | 5-flit | 6-flit | at the area of the main row | break-even depth (area) |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1.103; 1.175; 1.340 | the best of the two DeFT variants | THR | +4.4 [+4.3, +4.6] | +1.6 [+1.4, +1.9] | -0.5 [-0.8, -0.2] | **+2.8 [+2.6, +3.0]** | 5.8 flits (1.302) |
| 2x2 | 1.103; 1.175; 1.340 | the best of the two DeFT variants | LAT | -23.9 [-26.8, -20.9] | -15.3 [-18.0, -12.6] | -10.1 [-12.4, -7.7] | **-19.0 [-21.7, -16.1]** | not up to 6-flit buffers |
| 2x2 | 1.103; 1.175; 1.340 | the best of MTR and RC | THR | +1.5 [+1.1, +1.9] | -0.4 [-0.7, -0.0] | -2.1 [-2.3, -1.9] | **+0.4 [+0.1, +0.8]** | 4.8 flits (1.141) |
| 2x2 | 1.103; 1.175; 1.340 | the best of MTR and RC | LAT | -11.8 [-14.4, -9.1] | -5.1 [-7.9, -2.3] | -1.2 [-3.4, +1.1] | **-8.0 [-10.5, -5.3]** | not up to 6-flit buffers |
| 2x2 | 1.103; 1.175; 1.340 | the best of the four | THR | +0.0 [-0.3, +0.3] | -1.8 [-2.1, -1.5] | -3.4 [-3.6, -3.2] | **-1.1 [-1.3, -0.8]** | 4.0 flits (1.000) |
| 2x2 | 1.103; 1.175; 1.340 | the best of the four | LAT | -11.1 [-13.2, -8.8] | -5.1 [-7.8, -2.4] | -1.2 [-3.4, +1.1] | **-7.6 [-10.0, -5.2]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of the two DeFT variants | THR | +9.2 [+8.7, +9.6] | +6.4 [+5.9, +6.9] | +3.9 [+3.5, +4.2] | **+7.9 [+7.5, +8.3]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of the two DeFT variants | LAT | -25.1 [-26.7, -23.6] | -15.1 [-16.1, -14.2] | -9.9 [-10.7, -9.1] | **-20.7 [-21.9, -19.5]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of MTR and RC | THR | +9.2 [+8.8, +9.6] | +7.4 [+6.9, +7.9] | +5.8 [+5.3, +6.4] | **+8.4 [+7.9, +8.8]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of MTR and RC | LAT | -15.2 [-17.7, -12.7] | -9.1 [-11.0, -7.1] | -5.9 [-7.8, -3.9] | **-12.4 [-14.6, -10.3]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of the four | THR | +6.7 [+6.3, +7.0] | +4.8 [+4.3, +5.2] | +2.9 [+2.5, +3.3] | **+5.8 [+5.5, +6.1]** | not up to 6-flit buffers |
| 3x3 | 1.077; 1.170; 1.333 | the best of the four | LAT | -9.7 [-10.9, -8.4] | -4.7 [-5.7, -3.7] | -2.2 [-3.1, -1.3] | **-7.4 [-8.5, -6.3]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of the two DeFT variants | THR | +8.4 [+8.1, +8.7] | +6.0 [+5.7, +6.4] | +3.8 [+3.6, +4.0] | **+7.3 [+7.0, +7.6]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of the two DeFT variants | LAT | -25.7 [-27.7, -23.7] | -16.0 [-17.4, -14.7] | -10.1 [-11.2, -8.9] | **-21.3 [-23.0, -19.7]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of MTR and RC | THR | +8.8 [+8.2, +9.3] | +6.4 [+5.8, +7.0] | +4.7 [+4.2, +5.2] | **+7.6 [+7.1, +8.2]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of MTR and RC | LAT | -19.8 [-23.6, -15.8] | -13.5 [-17.1, -9.7] | -9.8 [-13.3, -6.0] | **-16.9 [-20.6, -13.0]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of the four | THR | +6.0 [+5.7, +6.3] | +4.0 [+3.6, +4.3] | +2.3 [+2.1, +2.6] | **+5.0 [+4.7, +5.3]** | not up to 6-flit buffers |
| 4x4 | 1.079; 1.168; 1.332 | the best of the four | LAT | -13.2 [-14.6, -11.7] | -7.8 [-8.8, -6.7] | -4.3 [-5.8, -2.9] | **-10.7 [-11.9, -9.4]** | not up to 6-flit buffers |

## X.3 Absolute values per scenario (mean over the ten seeds), and which reference is the best of the four at each depth

Added on 25 November after the results of C1 had been read: C.3 and C.4 compare with "the best of the four" and do not say which row that is in a scenario.
THR in flits/node/cycle (the largest accepted throughput over the nine loads), LAT in cycles at 1.0 x Lsat of DeFT_P with 4-flit buffers. Each reference with
4-flit / 5-flit / 6-flit buffers; **bold**: the best of the four at that depth, which is the row that the main row is compared with.

### THR, 2x2

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 0.1293 | 0.1387 | 0.1220 / 0.1271 / 0.1317 | 0.1173 / 0.1232 / 0.1288 | 0.1302 / 0.1334 / 0.1366 | **0.1311** / **0.1347** / **0.1378** |
| localized | 0.1513 | 0.1629 | 0.1491 / 0.1564 / 0.1618 | 0.1357 / 0.1444 / 0.1503 | 0.1590 / 0.1642 / 0.1693 | **0.1638** / **0.1693** / **0.1735** |
| hotspot | 0.0769 | 0.0780 | 0.0634 / 0.0656 / 0.0672 | **0.0748** / **0.0759** / **0.0764** | 0.0668 / 0.0672 / 0.0684 | 0.0684 / 0.0696 / 0.0703 |
| chipperm | 0.1098 | 0.1126 | 0.0999 / 0.1019 / 0.1041 | 0.0625 / 0.0648 / 0.0658 | **0.1019** / **0.1037** / 0.1054 | 0.1019 / 0.1036 / **0.1055** |
| chiptrans | 0.1641 | 0.1653 | 0.1588 / 0.1599 / 0.1611 | 0.1415 / 0.1429 / 0.1433 | **0.1599** / **0.1609** / **0.1617** | 0.1597 / 0.1608 / 0.1617 |
| movinghot | 0.1042 | 0.1104 | 0.1010 / 0.1044 / 0.1064 | 0.0901 / 0.0936 / 0.0985 | **0.1080** / **0.1090** / **0.1118** | 0.1038 / 0.1063 / 0.1073 |

### THR, 3x3

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 0.1007 | 0.1085 | 0.0872 / 0.0903 / 0.0938 | 0.0892 / 0.0937 / **0.0976** | 0.0915 / 0.0936 / 0.0957 | **0.0915** / **0.0944** / 0.0969 |
| localized | 0.1364 | 0.1482 | 0.1257 / 0.1315 / 0.1370 | 0.1194 / 0.1268 / 0.1327 | 0.1340 / 0.1383 / 0.1424 | **0.1355** / **0.1395** / **0.1431** |
| hotspot | 0.0351 | 0.0355 | 0.0289 / 0.0301 / 0.0306 | **0.0342** / **0.0346** / **0.0347** | 0.0310 / 0.0314 / 0.0319 | 0.0314 / 0.0318 / 0.0321 |
| chipperm | 0.0924 | 0.0964 | 0.0685 / 0.0693 / 0.0697 | **0.0737** / **0.0749** / **0.0768** | 0.0699 / 0.0701 / 0.0704 | 0.0695 / 0.0698 / 0.0699 |
| chiptrans | 0.0833 | 0.0831 | 0.0786 / 0.0792 / 0.0800 | 0.0601 / 0.0607 / 0.0611 | **0.0790** / **0.0798** / 0.0803 | 0.0790 / 0.0797 / **0.0803** |
| movinghot | 0.0574 | 0.0610 | 0.0566 / 0.0580 / 0.0593 | 0.0530 / 0.0551 / 0.0569 | **0.0584** / 0.0590 / 0.0598 | 0.0579 / **0.0591** / **0.0601** |

### THR, 4x4

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 0.0833 | 0.0897 | 0.0704 / 0.0731 / 0.0757 | 0.0692 / 0.0718 / 0.0741 | **0.0736** / **0.0759** / **0.0781** | 0.0736 / 0.0759 / 0.0780 |
| localized | 0.1212 | 0.1336 | 0.1081 / 0.1133 / 0.1174 | 0.1023 / 0.1083 / 0.1127 | 0.1142 / 0.1183 / **0.1223** | **0.1149** / **0.1192** / 0.1221 |
| hotspot | 0.0198 | 0.0201 | 0.0159 / 0.0165 / 0.0168 | **0.0193** / **0.0194** / **0.0195** | 0.0167 / 0.0169 / 0.0171 | 0.0168 / 0.0171 / 0.0172 |
| chipperm | 0.0568 | 0.0583 | **0.0523** / **0.0534** / **0.0544** | 0.0270 / 0.0276 / 0.0279 | 0.0514 / 0.0526 / 0.0537 | 0.0515 / 0.0527 / 0.0537 |
| chiptrans | 0.0598 | 0.0595 | 0.0558 / 0.0562 / 0.0568 | 0.0384 / 0.0389 / 0.0389 | 0.0562 / 0.0566 / 0.0570 | **0.0562** / **0.0567** / **0.0571** |
| movinghot | 0.0389 | 0.0408 | 0.0379 / 0.0386 / 0.0394 | 0.0344 / 0.0360 / 0.0372 | **0.0388** / **0.0395** / 0.0399 | 0.0387 / 0.0394 / **0.0399** |

### LAT, 2x2

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 63.8 | 61.6 | 78.0 / 70.8 / 67.4 | 91.7 / 79.7 / 75.0 | 65.6 / 63.8 / 63.1 | **63.3** / **61.3** / **60.6** |
| localized | 58.5 | 56.1 | 67.7 / 62.6 / 59.6 | 94.9 / 74.3 / 69.6 | 59.0 / 57.0 / 56.2 | **54.0** / **52.9** / **52.1** |
| hotspot | 53.9 | 53.0 | 143.4 / 89.9 / 76.3 | **62.7** / **60.8** / 60.1 | 78.0 / 69.0 / 64.3 | 66.5 / 61.0 / **58.3** |
| chipperm | 94.4 | 91.2 | 149.5 / 132.0 / 119.2 | 1347.9 / 1282.7 / 1270.2 | 136.3 / 123.0 / 118.2 | **134.7** / **119.6** / **112.8** |
| chiptrans | 55.7 | 54.2 | 80.9 / 71.0 / 68.2 | 517.0 / 499.1 / 497.3 | **75.5** / 69.9 / 66.5 | 77.5 / **69.0** / **65.1** |
| movinghot | 94.5 | 72.9 | 132.2 / 109.2 / 97.3 | 152.4 / 117.0 / 100.9 | 101.0 / 90.2 / 83.1 | **94.8** / **85.2** / **79.7** |

### LAT, 3x3

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 81.5 | 78.9 | 136.4 / 109.9 / 98.2 | 129.7 / 106.6 / 99.0 | 98.8 / 91.0 / 88.0 | **98.0** / **89.8** / **86.8** |
| localized | 67.9 | 64.3 | 106.0 / 83.0 / 75.1 | 130.6 / 89.7 / 79.9 | 78.1 / 72.0 / 68.3 | **71.1** / **66.1** / **64.3** |
| hotspot | 58.5 | 58.0 | 135.6 / 105.3 / 89.5 | **61.7** / **61.5** / **61.4** | 99.6 / 90.0 / 83.8 | 93.0 / 82.5 / 78.1 |
| chipperm | 81.5 | 80.5 | 122.7 / 111.8 / 105.8 | 280.4 / 241.3 / 225.8 | 111.5 / 106.0 / 102.0 | **110.4** / **104.3** / **101.1** |
| chiptrans | 65.2 | 63.9 | 78.4 / 74.5 / 71.3 | 528.5 / 503.6 / 497.9 | **74.5** / **70.6** / **69.1** | 74.8 / 71.1 / 70.2 |
| movinghot | 116.0 | 97.1 | 142.5 / 118.6 / 109.8 | 162.3 / 132.2 / 117.6 | **104.6** / **99.4** / **95.2** | 112.4 / 105.6 / 98.9 |

### LAT, 4x4

| scenario | the main row | `LB_d6` | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|---|
| uniform | 91.8 | 89.6 | 133.8 / 113.2 / 105.6 | 199.8 / 155.8 / 131.9 | 107.9 / 101.9 / 98.9 | **103.3** / **98.3** / **96.4** |
| localized | 70.2 | 68.0 | 100.9 / 82.8 / 77.4 | 176.1 / 121.0 / 95.8 | 76.8 / 72.8 / 70.9 | **73.7** / **70.4** / **69.0** |
| hotspot | 66.9 | 66.8 | 146.8 / 118.8 / 111.2 | **70.3** / **70.2** / **70.1** | 118.3 / 108.7 / 103.9 | 118.1 / 107.3 / 102.4 |
| chipperm | 137.6 | 133.7 | 175.4 / 159.8 / 151.2 | 1452.0 / 1447.9 / 1433.5 | 166.6 / 153.9 / 147.9 | **160.8** / **150.8** / **144.6** |
| chiptrans | 91.1 | 87.3 | 190.9 / 165.8 / 147.0 | 740.6 / 696.6 / 682.9 | **168.4** / 156.1 / **144.4** | 176.7 / **152.7** / 145.4 |
| movinghot | 251.7 | 194.7 | 259.7 / 224.9 / 203.2 | 320.8 / 263.9 / 227.9 | 222.4 / 202.1 / 184.9 | **222.1** / **199.8** / **184.1** |

The best of the four references, counted over the 36 cells of size, scenario and metric (THR and LAT):

| buffers of the references | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|
| 4-flit (round 25) | 1 | 7 | 11 | 17 |
| 5-flit | 1 | 7 | 8 | 20 |
| 6-flit | 1 | 7 | 7 | 21 |

## X.5 Under faults (C3), counted over the masks: which DeFT variant is the better one, and on how many masks the main row is ahead

Added on 26 November after the results of C3 had been read: C.8 gives effects with intervals over the 16 masks of a size and rate and does not say which variant
"the best" is nor how the masks split. Per mask and traffic pattern the mean over the two seeds; THR over the four loads, LAT at 1.0 x Lsat of DeFT_P on the mask.
*Ahead*: the main row (4-flit buffers) has the higher THR, or the lower LAT, than the better of the two variants on that mask.

| size | rate | traffic | `DeFT_B_d6` is the better variant: THR | LAT | the main row ahead of the better variant with 6-flit buffers: THR | LAT | with 4-flit buffers (round 26): THR | LAT |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1/16 | uniform | 14 of 16 | 1 of 16 | 1 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 2x2 | 1/16 | hotspot | 16 of 16 | 16 of 16 | 7 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 2x2 | 4/16 | uniform | 9 of 16 | 4 of 16 | 1 of 16 | 13 of 16 | 13 of 16 | 16 of 16 |
| 2x2 | 4/16 | hotspot | 16 of 16 | 16 of 16 | 5 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 3x3 | 1/16 | uniform | 15 of 16 | 10 of 16 | 10 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 3x3 | 1/16 | hotspot | 16 of 16 | 16 of 16 | 15 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 3x3 | 4/16 | uniform | 9 of 16 | 5 of 16 | 5 of 16 | 10 of 16 | 16 of 16 | 15 of 16 |
| 3x3 | 4/16 | hotspot | 16 of 16 | 14 of 16 | 10 of 16 | 13 of 16 | 15 of 16 | 16 of 16 |
| 4x4 | 1/16 | uniform | 8 of 16 | 2 of 16 | 15 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 4x4 | 1/16 | hotspot | 16 of 16 | 16 of 16 | 15 of 16 | 16 of 16 | 16 of 16 | 16 of 16 |
| 4x4 | 4/16 | uniform | 7 of 16 | 7 of 16 | 10 of 16 | 9 of 16 | 15 of 16 | 16 of 16 |
| 4x4 | 4/16 | hotspot | 15 of 16 | 14 of 16 | 11 of 16 | 15 of 16 | 15 of 16 | 16 of 16 |
| all | both | uniform | 62 of 96 | 29 of 96 | 42 of 96 | 80 of 96 | 92 of 96 | 95 of 96 |
| all | both | hotspot | 95 of 96 | 92 of 96 | 63 of 96 | 92 of 96 | 94 of 96 | 96 of 96 |

