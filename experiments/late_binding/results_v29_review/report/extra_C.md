# v29 Part C: a table added to the report (extra_v29.py c)

Descriptive; not in the pre-registration and no test. Defined on 25 November while C1 was running, before any of its results had been read (`DECISIONS.md`,
"Tables added after the results").

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

