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

## X.7 The references with 7-flit buffers in the interposer routers (C2) next to those with 5-flit and 6-flit buffers

Added on 26 November after the results of C2 had been read: C.2 and C.3 take THR over the four loads of C2 in the lines with `X_i7` and over the nine loads in the
lines with `X_d5` and `X_d6`, so the lines cannot be read against each other in THR. Here THR is the largest accepted throughput over the four loads (0.5, 1.0, 1.4,
2.0 x Lsat) for every row; LAT and P99 at 1.0 x Lsat of DeFT_P with 4-flit buffers, as everywhere. Six scenarios, ten seeds, 2x2 / 3x3 / 4x4. Area of all routers
relative to DeFT with 4-flit buffers (E3):

| design | hierarchy kept | core kept | flattened |
|---|---|---|---|
| the main row | 1.251 / 1.217 / 1.218 | 1.161 / 1.130 / 1.133 | 1.103 / 1.077 / 1.079 |
| `X_d5` | 1.168 / 1.167 / 1.166 | 1.175 / 1.172 / 1.171 | 1.175 / 1.170 / 1.168 |
| `X_d6` | 1.321 / 1.319 / 1.317 | 1.341 / 1.336 / 1.335 | 1.340 / 1.333 / 1.332 |
| `X_i7` | 1.239 / 1.237 / 1.236 | 1.249 / 1.246 / 1.246 | 1.254 / 1.247 / 1.246 |

**Each `X_i7` against the same reference with deeper buffers in every router** (positive THR, negative LAT and P99: the 7-flit buffers in the interposer routers
alone give the reference more):

| reference | against | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|---|
| DeFT_P_i7 | itself with 5-flit buffers | +0.9 [+0.8, +1.1] / +1.2 [+0.8, +1.5] / +2.5 [+2.1, +2.9] | -2.1 [-3.7, -0.4] / -5.6 [-6.8, -4.5] / -7.9 [-9.1, -6.8] | -4.8 [-7.7, -1.8] / -12.1 [-15.2, -8.9] / -14.8 [-17.4, -12.2] |
| DeFT_P_i7 | itself with 6-flit buffers | -1.3 [-1.7, -0.9] / -0.9 [-1.0, -0.8] / +0.2 [-0.0, +0.5] | +6.5 [+3.8, +9.2] / +3.1 [+1.9, +4.4] / -0.5 [-1.5, +0.6] | +10.1 [+5.5, +14.9] / +5.1 [+1.9, +8.4] / -2.2 [-5.4, +1.1] |
| DeFT_B_i7 | itself with 5-flit buffers | -1.4 [-1.6, -1.1] / -0.6 [-0.9, -0.2] / +1.0 [+0.7, +1.3] | +4.1 [+3.1, +5.0] / +0.6 [-0.5, +1.7] / -6.9 [-8.7, -5.1] | +5.0 [+2.2, +7.8] / -0.7 [-3.9, +2.7] / -15.1 [-18.4, -11.8] |
| DeFT_B_i7 | itself with 6-flit buffers | -4.1 [-4.4, -3.8] / -3.1 [-3.3, -2.9] / -1.1 [-1.4, -0.7] | +9.3 [+8.1, +10.4] / +7.2 [+6.0, +8.5] / +2.2 [+1.1, +3.4] | +13.4 [+10.8, +16.1] / +9.2 [+7.0, +11.4] / -0.7 [-3.7, +2.4] |
| MTR_i7 | itself with 5-flit buffers | +1.9 [+1.6, +2.1] / +1.7 [+1.3, +2.0] / +2.6 [+2.2, +3.1] | -3.8 [-5.7, -1.8] / -5.0 [-6.3, -3.6] / -7.2 [-7.9, -6.4] | -9.4 [-14.7, -3.8] / -13.6 [-16.3, -10.8] / -16.1 [-19.1, -13.1] |
| MTR_i7 | itself with 6-flit buffers | -0.1 [-0.4, +0.3] / +0.4 [+0.1, +0.7] / +0.7 [+0.3, +1.0] | +0.5 [-1.7, +2.8] / -0.9 [-1.8, -0.1] / -2.4 [-3.1, -1.7] | -0.7 [-7.4, +6.6] / -2.2 [-3.5, -0.8] / -5.7 [-8.0, -3.4] |
| RC_i7 | itself with 5-flit buffers | +1.9 [+1.7, +2.2] / +1.5 [+1.2, +1.8] / +2.7 [+2.5, +3.0] | -4.7 [-5.8, -3.5] / -4.7 [-5.8, -3.5] / -6.9 [-8.2, -5.5] | -10.1 [-13.1, -7.0] / -13.4 [-16.9, -9.8] / -12.7 [-15.6, -9.6] |
| RC_i7 | itself with 6-flit buffers | +0.1 [-0.1, +0.4] / +0.1 [-0.2, +0.5] / +1.0 [+0.7, +1.2] | -0.7 [-1.0, -0.4] / -1.1 [-2.1, -0.2] / -2.9 [-4.1, -1.7] | -1.9 [-3.8, +0.1] / -4.2 [-6.7, -1.7] / -5.9 [-7.3, -4.3] |

**The main row (4-flit buffers) against the best of each set, THR over the four loads for every set:**

| buffers of the references | against | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|---|
| 4-flit (round 25) | the best of the two DeFT variants | +4.0 [+3.9, +4.2] / +8.7 [+8.3, +9.1] / +8.9 [+8.6, +9.2] | -23.9 [-26.8, -20.9] / -25.1 [-26.7, -23.6] / -25.7 [-27.7, -23.7] | -39.1 [-44.3, -33.5] / -47.2 [-50.1, -44.1] / -45.2 [-49.1, -41.0] |
| 4-flit (round 25) | the best of MTR and RC | +1.5 [+1.2, +1.8] / +9.3 [+8.6, +9.9] / +10.3 [+9.9, +10.7] | -11.8 [-14.4, -9.1] / -15.2 [-17.7, -12.7] / -19.8 [-23.6, -15.8] | -28.4 [-33.9, -22.4] / -42.3 [-46.9, -37.3] / -47.1 [-52.2, -41.4] |
| 4-flit (round 25) | the best of the four | +0.0 [-0.2, +0.2] / +6.5 [+6.0, +6.9] / +6.6 [+6.3, +7.0] | -11.1 [-13.2, -8.8] / -9.7 [-10.9, -8.4] / -13.2 [-14.6, -11.7] | -24.4 [-29.8, -18.5] / -27.3 [-29.9, -24.6] / -29.6 [-31.9, -27.2] |
| 5-flit | the best of the two DeFT variants | +1.4 [+1.1, +1.7] / +6.2 [+5.7, +6.7] / +6.5 [+6.0, +7.0] | -15.3 [-18.0, -12.6] / -15.1 [-16.1, -14.2] / -16.0 [-17.4, -14.7] | -26.8 [-31.2, -22.0] / -33.1 [-35.5, -30.5] / -31.7 [-34.4, -28.8] |
| 5-flit | the best of MTR and RC | -0.4 [-0.8, +0.0] / +7.4 [+6.7, +8.1] / +8.0 [+7.6, +8.5] | -5.1 [-7.9, -2.3] / -9.1 [-11.0, -7.1] / -13.5 [-17.1, -9.7] | -15.0 [-21.5, -8.0] / -31.5 [-35.8, -26.9] / -38.6 [-44.7, -31.9] |
| 5-flit | the best of the four | -1.8 [-2.1, -1.5] / +4.5 [+3.9, +5.2] / +4.4 [+4.0, +4.8] | -5.1 [-7.8, -2.4] / -4.7 [-5.7, -3.7] / -7.8 [-8.8, -6.7] | -12.3 [-18.3, -5.9] / -16.8 [-18.8, -14.8] / -21.6 [-23.7, -19.4] |
| 6-flit | the best of the two DeFT variants | -0.7 [-1.1, -0.3] / +4.0 [+3.6, +4.2] / +4.3 [+4.1, +4.6] | -10.1 [-12.4, -7.7] / -9.9 [-10.7, -9.1] / -10.1 [-11.2, -8.9] | -18.6 [-22.3, -14.6] / -24.1 [-26.8, -21.3] / -23.2 [-25.1, -21.1] |
| 6-flit | the best of MTR and RC | -2.0 [-2.3, -1.8] / +5.9 [+5.4, +6.4] / +6.1 [+5.6, +6.5] | -1.2 [-3.4, +1.1] / -5.9 [-7.8, -3.9] / -9.8 [-13.3, -6.0] | -7.3 [-13.6, -0.5] / -24.0 [-28.2, -19.6] / -32.7 [-39.2, -25.6] |
| 6-flit | the best of the four | -3.4 [-3.6, -3.1] / +2.8 [+2.6, +3.1] / +2.7 [+2.3, +3.1] | -1.2 [-3.4, +1.1] / -2.2 [-3.1, -1.3] / -4.3 [-5.8, -2.9] | -6.7 [-13.2, +0.3] / -10.3 [-12.5, -8.2] / -15.4 [-18.4, -12.4] |
| 7-flit in the interposer routers | the best of the two DeFT variants | +0.1 [-0.1, +0.4] / +5.5 [+5.0, +5.9] / +3.6 [+3.3, +4.0] | -11.2 [-13.5, -8.8] / -10.0 [-10.9, -9.1] / -9.0 [-10.1, -7.9] | -21.8 [-25.9, -17.4] / -23.6 [-26.5, -20.6] / -20.3 [-22.8, -17.7] |
| 7-flit in the interposer routers | the best of MTR and RC | -2.0 [-2.4, -1.6] / +5.7 [+5.1, +6.4] / +5.2 [+4.9, +5.5] | -0.5 [-2.7, +1.8] / -5.3 [-7.3, -3.2] / -7.1 [-10.1, -4.0] | -5.5 [-11.1, +0.4] / -21.8 [-26.2, -17.2] / -28.3 [-34.6, -21.3] |
| 7-flit in the interposer routers | the best of the four | -3.4 [-3.7, -3.1] / +3.4 [+3.0, +3.9] / +1.8 [+1.4, +2.1] | -0.5 [-2.7, +1.8] / -1.6 [-2.5, -0.7] / -2.4 [-3.9, -0.9] | -4.4 [-10.3, +1.8] / -8.6 [-10.6, -6.5] / -12.5 [-15.8, -9.0] |

**The best of the four `X_i7` against the best of the four of the other sets** (the best row of each set per scenario and metric):

| the best `X_i7` against the best of the four with | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|
| 4-flit (round 25) buffers | +3.5 [+3.3, +3.8] / +2.9 [+2.6, +3.2] / +4.8 [+4.4, +5.2] | -10.7 [-12.2, -9.1] / -8.2 [-9.1, -7.2] / -11.0 [-11.8, -10.3] | -20.8 [-25.4, -16.1] / -20.5 [-22.1, -18.8] / -19.6 [-21.0, -18.1] |
| 5-flit buffers | +1.6 [+1.4, +1.9] / +1.1 [+0.7, +1.5] / +2.6 [+2.3, +2.9] | -4.7 [-5.6, -3.8] / -3.2 [-3.7, -2.6] / -5.5 [-6.5, -4.5] | -8.2 [-10.6, -5.8] / -9.0 [-10.4, -7.7] / -10.4 [-12.7, -8.0] |
| 6-flit buffers | +0.0 [-0.2, +0.2] / -0.5 [-0.8, -0.2] / +0.9 [+0.5, +1.3] | -0.7 [-1.0, -0.4] / -0.6 [-1.0, -0.2] / -2.0 [-2.6, -1.3] | -2.3 [-4.4, -0.3] / -1.9 [-3.6, -0.2] / -3.4 [-5.0, -1.8] |

**Read at the area of the main row.** With the hierarchy kept an `X_i7` reference has the area of the main row within two points, and the line above is the
measured comparison at equal area. In the other two forms the main row is smaller. The table reads the comparison at the area of the main row on the way from the
references with 4-flit buffers to `X_i7`: per seed the log ratio is interpolated linearly in the system area between the two measured sets, as in X.2. It is a
reading aid defined after the results were seen; no reference with 5-flit or 6-flit buffers in the interposer routers alone was run or synthesized.

| form | size | area: main row; `X_i7` | against | THR | LAT at 1.0 x Lsat |
|---|---|---|---|---|---|
| hierarchy kept | 2x2 | 1.251; 1.239 | the best of the two DeFT variants | measured against `X_i7`, which has less area: +0.1 [-0.1, +0.4] | measured against `X_i7`, which has less area: -11.2 [-13.5, -8.8] |
| hierarchy kept | 2x2 | 1.251; 1.239 | the best of MTR and RC | measured against `X_i7`, which has less area: -2.0 [-2.4, -1.6] | measured against `X_i7`, which has less area: -0.5 [-2.7, +1.8] |
| hierarchy kept | 2x2 | 1.251; 1.239 | the best of the four | measured against `X_i7`, which has less area: -3.4 [-3.7, -3.1] | measured against `X_i7`, which has less area: -0.5 [-2.7, +1.8] |
| hierarchy kept | 3x3 | 1.217; 1.237 | the best of the two DeFT variants | +5.7 [+5.3, +6.2] | -11.4 [-12.3, -10.5] |
| hierarchy kept | 3x3 | 1.217; 1.237 | the best of MTR and RC | +6.0 [+5.4, +6.7] | -6.2 [-8.2, -4.1] |
| hierarchy kept | 3x3 | 1.217; 1.237 | the best of the four | +3.7 [+3.2, +4.1] | -2.3 [-3.2, -1.4] |
| hierarchy kept | 4x4 | 1.218; 1.236 | the best of the two DeFT variants | +4.0 [+3.7, +4.4] | -10.4 [-11.5, -9.2] |
| hierarchy kept | 4x4 | 1.218; 1.236 | the best of MTR and RC | +5.6 [+5.3, +5.9] | -8.1 [-11.1, -4.9] |
| hierarchy kept | 4x4 | 1.218; 1.236 | the best of the four | +2.1 [+1.8, +2.5] | -3.2 [-4.7, -1.7] |
| core kept | 2x2 | 1.161; 1.249 | the best of the two DeFT variants | +1.5 [+1.3, +1.7] | -15.9 [-18.4, -13.3] |
| core kept | 2x2 | 1.161; 1.249 | the best of MTR and RC | -0.8 [-1.1, -0.4] | -4.6 [-6.7, -2.5] |
| core kept | 2x2 | 1.161; 1.249 | the best of the four | -2.2 [-2.4, -1.9] | -4.3 [-6.4, -2.2] |
| core kept | 3x3 | 1.130; 1.246 | the best of the two DeFT variants | +7.0 [+6.6, +7.3] | -17.5 [-18.7, -16.3] |
| core kept | 3x3 | 1.130; 1.246 | the best of MTR and RC | +7.4 [+6.7, +8.1] | -10.1 [-12.3, -7.9] |
| core kept | 3x3 | 1.130; 1.246 | the best of the four | +4.8 [+4.4, +5.2] | -5.5 [-6.5, -4.5] |
| core kept | 4x4 | 1.133; 1.246 | the best of the two DeFT variants | +6.0 [+5.7, +6.3] | -17.2 [-18.7, -15.7] |
| core kept | 4x4 | 1.133; 1.246 | the best of MTR and RC | +7.5 [+7.2, +7.9] | -13.2 [-16.5, -9.7] |
| core kept | 4x4 | 1.133; 1.246 | the best of the four | +4.0 [+3.7, +4.3] | -7.5 [-9.0, -6.1] |
| flattened | 2x2 | 1.103; 1.254 | the best of the two DeFT variants | +2.4 [+2.2, +2.6] | -19.0 [-21.6, -16.2] |
| flattened | 2x2 | 1.103; 1.254 | the best of MTR and RC | +0.1 [-0.2, +0.4] | -7.4 [-9.6, -5.1] |
| flattened | 2x2 | 1.103; 1.254 | the best of the four | -1.4 [-1.6, -1.1] | -6.9 [-9.0, -4.8] |
| flattened | 3x3 | 1.077; 1.247 | the best of the two DeFT variants | +7.7 [+7.3, +8.0] | -20.7 [-22.0, -19.3] |
| flattened | 3x3 | 1.077; 1.247 | the best of MTR and RC | +8.2 [+7.5, +8.8] | -12.2 [-14.5, -9.9] |
| flattened | 3x3 | 1.077; 1.247 | the best of the four | +5.5 [+5.1, +5.9] | -7.2 [-8.3, -6.1] |
| flattened | 4x4 | 1.079; 1.246 | the best of the two DeFT variants | +7.2 [+6.9, +7.5] | -20.8 [-22.4, -19.0] |
| flattened | 4x4 | 1.079; 1.246 | the best of MTR and RC | +8.6 [+8.3, +9.0] | -15.9 [-19.4, -12.2] |
| flattened | 4x4 | 1.079; 1.246 | the best of the four | +5.0 [+4.7, +5.3] | -9.9 [-11.3, -8.4] |

**Absolute values per scenario** (mean over the ten seeds; THR in flits/node/cycle over the four loads, LAT in cycles at 1.0 x Lsat). Each reference with 4-flit
buffers / with 7-flit buffers in the interposer routers; **bold**: the best of the four `X_i7`, the row that the main row is compared with.

### THR, 2x2

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 0.1289 | 0.1216 / 0.1303 | 0.1163 / 0.1215 | 0.1296 / 0.1366 | 0.1304 / **0.1381** |
| localized | 0.1490 | 0.1483 / 0.1571 | 0.1347 / 0.1386 | 0.1579 / 0.1674 | 0.1631 / **0.1720** |
| hotspot | 0.0765 | 0.0630 / 0.0638 | 0.0744 / **0.0749** | 0.0664 / 0.0669 | 0.0682 / 0.0687 |
| chipperm | 0.1097 | 0.0995 / 0.1049 | 0.0622 / 0.0636 | 0.1013 / 0.1065 | 0.1015 / **0.1065** |
| chiptrans | 0.1458 | 0.1406 / 0.1430 | 0.1231 / 0.1236 | 0.1415 / 0.1438 | 0.1414 / **0.1439** |
| movinghot | 0.1004 | 0.0991 / 0.1018 | 0.0894 / 0.0913 | 0.1035 / **0.1064** | 0.1010 / 0.1057 |

### THR, 3x3

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 0.1001 | 0.0866 / 0.0937 | 0.0887 / 0.0940 | 0.0913 / **0.0971** | 0.0909 / 0.0971 |
| localized | 0.1343 | 0.1248 / 0.1354 | 0.1182 / 0.1238 | 0.1337 / 0.1422 | 0.1345 / **0.1438** |
| hotspot | 0.0346 | 0.0285 / 0.0289 | 0.0339 / **0.0343** | 0.0302 / 0.0307 | 0.0306 / 0.0312 |
| chipperm | 0.0898 | 0.0658 / 0.0663 | 0.0707 / **0.0703** | 0.0666 / 0.0672 | 0.0669 / 0.0676 |
| chiptrans | 0.0745 | 0.0709 / 0.0720 | 0.0547 / 0.0553 | 0.0712 / **0.0724** | 0.0712 / 0.0722 |
| movinghot | 0.0535 | 0.0538 / 0.0549 | 0.0502 / 0.0519 | 0.0547 / 0.0559 | 0.0544 / **0.0560** |

### THR, 4x4

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 0.0830 | 0.0699 / 0.0763 | 0.0689 / 0.0734 | 0.0730 / **0.0789** | 0.0727 / 0.0786 |
| localized | 0.1207 | 0.1067 / 0.1168 | 0.1013 / 0.1090 | 0.1135 / 0.1225 | 0.1138 / **0.1232** |
| hotspot | 0.0195 | 0.0151 / 0.0155 | 0.0187 / **0.0190** | 0.0157 / 0.0161 | 0.0157 / 0.0161 |
| chipperm | 0.0567 | 0.0521 / **0.0549** | 0.0266 / 0.0273 | 0.0505 / 0.0529 | 0.0506 / 0.0531 |
| chiptrans | 0.0546 | 0.0507 / 0.0519 | 0.0351 / 0.0352 | 0.0510 / **0.0522** | 0.0511 / 0.0522 |
| movinghot | 0.0357 | 0.0352 / 0.0361 | 0.0329 / 0.0348 | 0.0355 / 0.0365 | 0.0354 / **0.0367** |

### LAT, 2x2

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 63.8 | 78.0 / 68.6 | 91.7 / 80.8 | 65.6 / 63.1 | 63.3 / **60.5** |
| localized | 58.5 | 67.7 / 61.2 | 94.9 / 77.5 | 59.0 / 56.9 | 54.0 / **52.5** |
| hotspot | 53.9 | 143.4 / 109.0 | 62.7 / 61.7 | 78.0 / 71.5 | 66.5 / **60.3** |
| chipperm | 94.4 | 149.5 / 114.9 | 1347.9 / 1319.9 | 136.3 / 110.1 | 134.7 / **107.2** |
| chiptrans | 55.7 | 80.9 / 66.2 | 517.0 / 512.9 | 75.5 / 63.9 | 77.5 / **62.8** |
| movinghot | 94.5 | 132.2 / 104.9 | 152.4 / 130.7 | 101.0 / 85.2 | 94.8 / **79.9** |

### LAT, 3x3

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 81.5 | 136.4 / 96.6 | 129.7 / 101.7 | 98.8 / 86.8 | 98.0 / **85.9** |
| localized | 67.9 | 106.0 / 74.9 | 130.6 / 86.5 | 78.1 / 68.1 | 71.1 / **63.9** |
| hotspot | 58.5 | 135.6 / 109.7 | 61.7 / **61.6** | 99.6 / 81.2 | 93.0 / 78.4 |
| chipperm | 81.5 | 122.7 / 104.3 | 280.4 / 249.8 | 111.5 / 101.0 | 110.4 / **99.6** |
| chiptrans | 65.2 | 78.4 / 70.4 | 528.5 / 507.8 | 74.5 / 68.4 | 74.8 / **68.2** |
| movinghot | 116.0 | 142.5 / 114.8 | 162.3 / 142.3 | 104.6 / **95.5** | 112.4 / 97.7 |

### LAT, 4x4

| scenario | the main row | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|---|
| uniform | 91.8 | 133.8 / 103.9 | 199.8 / 125.8 | 107.9 / 97.8 | 103.3 / **95.5** |
| localized | 70.2 | 100.9 / 76.6 | 176.1 / 97.0 | 76.8 / 70.9 | 73.7 / **68.8** |
| hotspot | 66.9 | 146.8 / 115.9 | 70.3 / **70.2** | 118.3 / 101.6 | 118.1 / 95.7 |
| chipperm | 137.6 | 175.4 / 147.6 | 1452.0 / 1425.8 | 166.6 / 144.4 | 160.8 / **142.4** |
| chiptrans | 91.1 | 190.9 / 140.1 | 740.6 / 706.3 | 168.4 / **136.1** | 176.7 / 136.5 |
| movinghot | 251.7 | 259.7 / 209.1 | 320.8 / 259.4 | 222.4 / 180.0 | 222.1 / **177.9** |

The best of the four references of each set, counted over the 36 cells of size, scenario and metric (THR over the four loads, and LAT):

| buffers of the references | DeFT_P | DeFT_B | MTR | RC |
|---|---|---|---|---|
| 4-flit (round 25) | 1 | 7 | 11 | 17 |
| 5-flit | 1 | 7 | 6 | 22 |
| 6-flit | 1 | 7 | 10 | 18 |
| 7-flit in the interposer routers | 1 | 6 | 7 | 22 |

## X.8 The main row against the best of the four references of each set with one scenario left out

Added on 26 November after the results of C2 had been read: against references with deeper buffers the main row is ahead in some scenarios and behind in others
(C.4), and the mean over the six does not show how much one scenario carries. Each line leaves one scenario out; effect [95 % interval over the ten seeds],
2x2 / 3x3 / 4x4. THR over the nine loads, and over the four loads of C2 in the column of `X_i7`. Descriptive, no test.

| left out | metric | 4-flit (round 25) | 5-flit | 6-flit | 7-flit in the interposer routers |
|---|---|---|---|---|---|
| none (the six scenarios) | THR | +0.0 [-0.3, +0.3] / +6.7 [+6.3, +7.0] / +6.0 [+5.7, +6.3] | -1.8 [-2.1, -1.5] / +4.8 [+4.3, +5.2] / +4.0 [+3.6, +4.3] | -3.4 [-3.6, -3.2] / +2.9 [+2.5, +3.3] / +2.3 [+2.1, +2.6] | -3.4 [-3.7, -3.1] / +3.4 [+3.0, +3.9] / +1.8 [+1.4, +2.1] |
| none (the six scenarios) | LAT | -11.1 [-13.2, -8.8] / -9.7 [-10.9, -8.4] / -13.2 [-14.6, -11.7] | -5.1 [-7.8, -2.4] / -4.7 [-5.7, -3.7] / -7.8 [-8.8, -6.7] | -1.2 [-3.4, +1.1] / -2.2 [-3.1, -1.3] / -4.3 [-5.8, -2.9] | -0.5 [-2.7, +1.8] / -1.6 [-2.5, -0.7] / -2.4 [-3.9, -0.9] |
| uniform | THR | +0.3 [-0.0, +0.6] / +6.0 [+5.7, +6.3] / +4.6 [+4.3, +4.9] | -1.3 [-1.6, -1.0] / +4.4 [+3.9, +4.8] / +2.8 [+2.4, +3.3] | -2.9 [-3.1, -2.6] / +2.8 [+2.3, +3.3] / +1.5 [+1.2, +1.8] | -2.7 [-3.1, -2.3] / +3.5 [+2.9, +4.0] / +1.1 [+0.7, +1.4] |
| uniform | LAT | -13.2 [-15.8, -10.6] / -8.2 [-9.8, -6.5] / -13.6 [-15.3, -11.8] | -6.9 [-10.0, -3.7] / -3.8 [-5.0, -2.6] / -8.0 [-9.3, -6.7] | -2.4 [-4.8, +0.1] / -1.4 [-2.5, -0.3] / -4.2 [-6.0, -2.5] | -1.6 [-4.1, +1.0] / -0.9 [-2.0, +0.2] / -2.1 [-3.9, -0.3] |
| localized | THR | +1.6 [+1.2, +2.0] / +7.9 [+7.4, +8.4] / +6.1 [+5.8, +6.4] | +0.1 [-0.2, +0.4] / +6.2 [+5.5, +6.8] / +4.4 [+4.0, +4.8] | -1.4 [-1.6, -1.2] / +4.4 [+3.9, +5.0] / +3.0 [+2.6, +3.3] | -1.2 [-1.6, -0.9] / +5.5 [+5.0, +6.1] / +2.5 [+2.1, +3.0] |
| localized | LAT | -14.5 [-17.0, -12.0] / -10.7 [-12.2, -9.2] / -14.8 [-16.4, -13.1] | -8.0 [-11.0, -5.0] / -6.2 [-7.2, -5.1] / -9.2 [-10.4, -7.9] | -3.7 [-6.2, -1.1] / -3.7 [-4.7, -2.7] / -5.5 [-7.2, -3.8] | -2.7 [-5.2, -0.0] / -3.1 [-4.0, -2.1] / -3.3 [-5.0, -1.4] |
| hotspot | THR | -0.6 [-0.9, -0.2] / +7.5 [+7.2, +7.8] / +6.7 [+6.4, +7.0] | -2.4 [-2.7, -2.1] / +5.4 [+5.1, +5.8] / +4.3 [+4.1, +4.6] | -4.2 [-4.5, -4.0] / +3.3 [+2.9, +3.6] / +2.5 [+2.1, +2.8] | -4.4 [-4.8, -4.1] / +3.9 [+3.5, +4.2] / +1.6 [+1.3, +2.0] |
| hotspot | LAT | -10.5 [-12.9, -8.0] / -10.5 [-12.0, -9.1] / -14.8 [-16.5, -13.0] | -3.9 [-7.0, -0.6] / -4.7 [-5.8, -3.5] / -8.4 [-9.6, -7.1] | +0.1 [-2.6, +2.9] / -1.7 [-2.7, -0.6] / -4.3 [-6.0, -2.5] | +1.7 [-1.1, +4.6] / -0.9 [-1.9, +0.2] / -1.9 [-3.8, -0.1] |
| chipperm | THR | -1.5 [-1.8, -1.2] / +3.3 [+2.9, +3.7] / +5.5 [+5.1, +5.8] | -3.2 [-3.5, -3.0] / +1.4 [+0.9, +1.9] / +3.5 [+3.0, +3.9] | -4.9 [-5.1, -4.7] / -0.3 [-0.8, +0.2] / +1.9 [+1.6, +2.1] | -4.6 [-5.0, -4.2] / -0.9 [-1.3, -0.4] / +1.4 [+1.1, +1.9] |
| chipperm | LAT | -6.8 [-8.9, -4.7] / -6.0 [-7.0, -5.0] / -12.9 [-14.6, -11.3] | -1.7 [-4.3, +1.1] / -0.9 [-1.8, +0.1] / -7.6 [-8.9, -6.3] | +2.1 [-0.1, +4.4] / +1.6 [+0.7, +2.6] / -4.3 [-6.0, -2.5] | +2.0 [-0.3, +4.3] / +2.1 [+1.1, +3.1] / -2.2 [-4.1, -0.3] |
| chiptrans | THR | -0.5 [-0.9, -0.2] / +6.9 [+6.6, +7.3] / +5.9 [+5.5, +6.3] | -2.5 [-2.8, -2.2] / +4.8 [+4.3, +5.4] / +3.6 [+3.2, +4.1] | -4.4 [-4.7, -4.1] / +2.7 [+2.2, +3.2] / +1.8 [+1.5, +2.1] | -4.3 [-4.7, -4.0] / +3.5 [+3.0, +4.0] / +1.2 [+0.8, +1.7] |
| chiptrans | LAT | -7.8 [-10.6, -4.9] / -9.1 [-10.5, -7.7] / -4.7 [-6.1, -3.2] | -2.1 [-4.9, +0.8] / -4.2 [-5.2, -3.0] / +0.5 [-0.6, +1.7] | +1.6 [-0.6, +3.9] / -1.5 [-2.5, -0.5] / +3.8 [+2.9, +4.7] | +1.8 [-0.3, +4.1] / -1.1 [-1.9, -0.2] / +5.1 [+4.3, +5.9] |
| movinghot | THR | +0.7 [+0.4, +1.0] / +8.4 [+8.1, +8.8] / +7.2 [+6.6, +7.7] | -1.2 [-1.6, -0.9] / +6.4 [+6.0, +6.7] / +5.0 [+4.6, +5.5] | -2.7 [-3.1, -2.4] / +4.4 [+4.1, +4.7] / +3.3 [+3.0, +3.5] | -2.9 [-3.2, -2.6] / +5.1 [+4.5, +5.6] / +2.6 [+2.2, +3.1] |
| movinghot | LAT | -13.1 [-14.9, -11.3] / -13.3 [-14.6, -12.0] / -17.8 [-18.9, -16.6] | -8.1 [-10.1, -6.0] / -8.5 [-9.5, -7.5] / -13.4 [-14.5, -12.3] | -4.7 [-6.3, -3.0] / -6.4 [-7.1, -5.6] / -11.0 [-12.3, -9.6] | -3.8 [-5.3, -2.2] / -5.6 [-6.4, -4.8] / -9.4 [-10.8, -8.0] |

