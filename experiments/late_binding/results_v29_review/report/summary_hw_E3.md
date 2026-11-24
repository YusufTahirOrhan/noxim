# v29 E3: the references with more buffers (report_v29_hw.py e3)

DeFT's four routers with 5-flit and 6-flit input buffers, and with 7-flit buffers in the interposer routers only, synthesised with the flow of round 25
(NanGate45 typical, Yosys + ABC at 1 GHz) in its three forms, in one run with DeFT at depth 4 and with the main row. RTL: `hw/rtl/router_core29.v`, the
reference core of round 18 with the depths as macros; `DeFT_d4` is the core of round 18 unchanged, `DeFT_d4c` the new core at depth 4.

Functional check of the depths (`hw/buffer_core_check.txt`): All cases pass and both controls fail: yes.

## E3.1 Area of a router (um^2 at depth 4; the others relative to depth 4 of the same router, form and size)

### hierarchy kept

| size | router | depth 4 (um^2) | new core at depth 4 | depth 5 | depth 6 | interposer depth 7 | buffers at depth 4 (share of the router) |
|---|---|---|---|---|---|---|---|
| 2x2 | chiplet (5 ports) | 17518 | 0.999 | 1.168 | 1.321 | 1.000 (the router of depth 4) | 62.3 % |
| 2x2 | boundary (6 ports) | 21701 | 0.999 | 1.163 | 1.311 | 0.999 | 60.4 % |
| 2x2 | interposer (5 ports) | 17152 | 0.999 | 1.172 | 1.328 | 1.489 | 63.7 % |
| 2x2 | interposer + VL (6 ports) | 21289 | 0.999 | 1.166 | 1.317 | 1.473 | 61.6 % |
| 3x3 | chiplet (5 ports) | 17770 | 0.999 | 1.166 | 1.316 | 1.000 (the router of depth 4) | 61.5 % |
| 3x3 | boundary (6 ports) | 21964 | 0.999 | 1.161 | 1.307 | 0.999 | 59.7 % |
| 3x3 | interposer (5 ports) | 17176 | 0.999 | 1.171 | 1.327 | 1.488 | 63.6 % |
| 3x3 | interposer + VL (6 ports) | 21318 | 0.999 | 1.166 | 1.316 | 1.472 | 61.5 % |
| 4x4 | chiplet (5 ports) | 18019 | 0.999 | 1.163 | 1.312 | 1.000 (the router of depth 4) | 60.6 % |
| 4x4 | boundary (6 ports) | 22213 | 0.999 | 1.159 | 1.304 | 0.999 | 59.0 % |
| 4x4 | interposer (5 ports) | 17176 | 0.999 | 1.171 | 1.327 | 1.488 | 63.6 % |
| 4x4 | interposer + VL (6 ports) | 21318 | 0.999 | 1.166 | 1.316 | 1.472 | 61.5 % |

### core kept

| size | router | depth 4 (um^2) | new core at depth 4 | depth 5 | depth 6 | interposer depth 7 | buffers at depth 4 (share of the router) |
|---|---|---|---|---|---|---|---|
| 2x2 | chiplet (5 ports) | 16942 | 1.000 | 1.176 | 1.343 | 1.000 (the router of depth 4) |  |
| 2x2 | boundary (6 ports) | 21134 | 1.003 | 1.171 | 1.327 | 1.001 |  |
| 2x2 | interposer (5 ports) | 16666 | 1.000 | 1.178 | 1.346 | 1.508 |  |
| 2x2 | interposer + VL (6 ports) | 20722 | 1.000 | 1.173 | 1.335 | 1.491 |  |
| 3x3 | chiplet (5 ports) | 17222 | 1.000 | 1.172 | 1.334 | 1.000 (the router of depth 4) |  |
| 3x3 | boundary (6 ports) | 21413 | 1.002 | 1.166 | 1.325 | 0.998 |  |
| 3x3 | interposer (5 ports) | 16735 | 0.999 | 1.176 | 1.344 | 1.506 |  |
| 3x3 | interposer + VL (6 ports) | 20799 | 0.998 | 1.172 | 1.334 | 1.489 |  |
| 4x4 | chiplet (5 ports) | 17432 | 1.002 | 1.169 | 1.332 | 1.000 (the router of depth 4) |  |
| 4x4 | boundary (6 ports) | 21603 | 1.000 | 1.165 | 1.321 | 1.001 |  |
| 4x4 | interposer (5 ports) | 16735 | 0.999 | 1.176 | 1.344 | 1.506 |  |
| 4x4 | interposer + VL (6 ports) | 20799 | 0.998 | 1.172 | 1.334 | 1.489 |  |

### flattened

| size | router | depth 4 (um^2) | new core at depth 4 | depth 5 | depth 6 | interposer depth 7 | buffers at depth 4 (share of the router) |
|---|---|---|---|---|---|---|---|
| 2x2 | chiplet (5 ports) | 16720 | 0.996 | 1.175 | 1.339 | 1.000 (the router of depth 4) |  |
| 2x2 | boundary (6 ports) | 20532 | 0.996 | 1.172 | 1.337 | 0.996 |  |
| 2x2 | interposer (5 ports) | 16574 | 1.006 | 1.179 | 1.345 | 1.518 |  |
| 2x2 | interposer + VL (6 ports) | 20618 | 1.003 | 1.171 | 1.332 | 1.500 |  |
| 3x3 | chiplet (5 ports) | 17035 | 0.993 | 1.167 | 1.331 | 1.000 (the router of depth 4) |  |
| 3x3 | boundary (6 ports) | 20785 | 1.005 | 1.167 | 1.328 | 1.000 |  |
| 3x3 | interposer (5 ports) | 16680 | 0.998 | 1.174 | 1.341 | 1.507 |  |
| 3x3 | interposer + VL (6 ports) | 20789 | 0.998 | 1.168 | 1.326 | 1.490 |  |
| 4x4 | chiplet (5 ports) | 17228 | 0.997 | 1.165 | 1.331 | 1.000 (the router of depth 4) |  |
| 4x4 | boundary (6 ports) | 21168 | 0.991 | 1.158 | 1.318 | 0.995 |  |
| 4x4 | interposer (5 ports) | 16680 | 0.998 | 1.174 | 1.341 | 1.507 |  |
| 4x4 | interposer + VL (6 ports) | 20789 | 0.998 | 1.168 | 1.326 | 1.490 |  |

## E3.2 System: average router area relative to DeFT at depth 4 (hierarchy kept / core kept / flattened)

Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers (round 25). The main row: its interposer routers (one register in
the decision unit, after stage M; the 3x3 routers are the 4x4 ones) and the chiplet routers of round 25.

| design | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| DeFT, new core at depth 4 | 0.999 / 1.000 / 1.001 | 0.999 / 1.000 / 0.997 | 0.999 / 1.000 / 0.997 |
| DeFT, 5-flit buffers (`X_d5`) | 1.168 / 1.175 / 1.175 | 1.167 / 1.172 / 1.170 | 1.166 / 1.171 / 1.168 |
| DeFT, 6-flit buffers (`X_d6`) | 1.321 / 1.341 / 1.340 | 1.319 / 1.336 / 1.333 | 1.317 / 1.335 / 1.332 |
| DeFT, 7-flit buffers in the interposer routers (`X_i7`) | 1.239 / 1.249 / 1.254 | 1.237 / 1.246 / 1.247 | 1.236 / 1.246 / 1.246 |
| main row, this run | 1.251 / 1.161 / 1.103 | 1.217 / 1.130 / 1.077 | 1.218 / 1.133 / 1.079 |
| main row, round 25 (`results_v25_confirm/report/hw_system_area.csv`) | 1.251 / 1.161 / 1.103 | 1.217 / 1.130 / 1.077 | 1.218 / 1.133 / 1.079 |

## E3.3 Which buffer depth gives a reference the main row's area

The depth at which DeFT's system area equals the main row's, read from the measured depths 4, 5 and 6 by linear interpolation (beyond 6: with the step
from 5 to 6). MTR and RC have DeFT's routers plus their own small units (round 18), so the same depths are taken for them.

| form | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| hierarchy kept | 5.5 flits | 5.3 flits | 5.3 flits |
| core kept | 4.9 flits | 4.8 flits | 4.8 flits |
| flattened | 4.6 flits | 4.5 flits | 4.5 flits |

Read: a reference with 5-flit buffers has 1.168 / 1.167 / 1.166 of DeFT's area and one with 6-flit buffers 1.321 / 1.319 / 1.317 (hierarchy kept, 2x2 / 3x3 / 4x4); 7-flit buffers in the
interposer routers alone give 1.239 / 1.237 / 1.236. The main row has 1.251 / 1.217 / 1.218.

