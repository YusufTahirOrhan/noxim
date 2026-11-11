# Part F: hardware of the final design (interposer router; NanGate45, Yosys + ABC, OpenSTA)

## F2: the RTL against the simulator

Vectors dumped from simulator runs (an instrumented copy of the simulator whose statistics are byte-identical to `bin/noxim` on every run); a selection vector is applied to the decision unit with each of the 8 cut configurations. Details: `hw/functional_check.txt`.

| design | simulator runs (identical to bin/noxim) | selection vectors | applied (x 8 cut configurations) | of them with more than one offered output | front vectors (relation, only output, fallback) | fallback evaluated / took another output | total distinct vectors | mismatches |
|---|---|---|---|---|---|---|---|---|
| LF_X | 12 (12) | 1870613 | 14964904 | 564929 | 4250603 | 289389 / 23435 | **6121216** | **0** |
| LF_O | 12 (12) | 1861048 | 14888384 | 563170 | 4346446 | 291963 / 23352 | **6207494** | **0** |
| DLY_X | 12 (12) | 761561 | 6092488 | 761561 | 4205674 | 0 / 0 | **4967235** | **0** |

All three designs pass: **yes**.

**21 of 24 mutations caught.**
Not caught: xy_turn: an X move after a Y move; rot_wrap: the tie break does not wrap around; fb_order: the fallback tries N before the Up link. See `hw/FINDINGS_hw.md` for whether each is redundant logic on reachable inputs.

## F3: area (NanGate45 typical, Yosys + ABC at 1 GHz; um^2: hierarchy kept / flattened; in brackets relative to DeFT of the same type and size)

* **Hierarchy kept** (the primary figure, as in round 18): every unit is synthesised on its own. Nothing is shared between the relation units of the input VCs and the decision units, so it is an upper bound for the designs of this round.
* **Core kept**: the router core (buffers, allocators, crossbar, input-VC state) stays one module and everything around it is flattened into the top. Logic is shared and constants are propagated within the routing and selection logic, not across the ports of the core.
* **Flattened**: no module boundary. For the designs of this round this also removes logic of the core that the relation can never ask for (the Local output port of an interposer router, turns the dimension order forbids; flip-flops removed by flattening: DeFT 10-12, LF with XY 122-150, DLY per router 24-28). The DeFT RTL of round 18 does not express that its interposer router never uses the Local output either, so this figure favours the designs of this round and is reported for completeness only.

### 2x2

| design | cuts | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|
| DeFT | none | 17152 / 16574 (1.000 / 1.000) | 21289 / 20618 (1.000 / 1.000) |
| LB-I heuristic of round 18, one unit per router | none | 22963 / 19607 (1.339 / 1.183) | 27453 / 24569 (1.290 / 1.192) |
| LB-I heuristic of round 18, one unit per input port | none | 42583 / 27325 (2.483 / 1.649) | 52759 / 35227 (2.478 / 1.709) |
| fast selection of round 21, per router (its table: hierarchy kept) | its cut | 22405 (1.306) | 26655 (1.252) |
| fast selection of round 21, per input port (its table: hierarchy kept) | its cut | 34908 (2.035) | 42506 (1.997) |
| relation only, LF structure | none | 19509 / 15408 (1.137 / 0.930) | 24164 / 19547 (1.135 / 0.948) |
| relation only, DLY, per port | none | 18365 / 16193 (1.071 / 0.977) | 22781 / 20541 (1.070 / 0.996) |
| relation only, DLY, per router | none | 17632 / 16896 (1.028 / 1.019) | 21849 / 21024 (1.026 / 1.020) |
| LF, XY (main row) | none | 23875 / 18089 (1.392 / 1.091) | 30839 / 23758 (1.449 / 1.152) |
| LF, XY (main row) | M | 24470 / 18796 (1.427 / 1.134) | 31876 / 24839 (1.497 / 1.205) |
| LF, XY (main row) | A, B | 24884 / 19310 (1.451 / 1.165) | 32631 / 25999 (1.533 / 1.261) |
| LF, VN-split order (second row) | none | 27871 / 20700 (1.625 / 1.249) | 35035 / 26829 (1.646 / 1.301) |
| LF, VN-split order (second row) | M | 29057 / 22224 (1.694 / 1.341) | 36770 / 28779 (1.727 / 1.396) |
| LF, VN-split order (second row) | A, B | 29886 / 23503 (1.742 / 1.418) | 38029 / 30733 (1.786 / 1.491) |
| DLY, XY, one unit per input port | none | 21916 / 18276 (1.278 / 1.103) | 28263 / 24197 (1.328 / 1.174) |
| DLY, XY, one unit per input port | M | 22529 / 19021 (1.313 / 1.148) | 29295 / 25078 (1.376 / 1.216) |
| DLY, XY, one unit per input port | A, M | 23128 / 19647 (1.348 / 1.185) | 30337 / 26321 (1.425 / 1.277) |
| DLY, XY, one unit per router | none | 19635 / 18350 (1.145 / 1.107) | 24005 / 22641 (1.128 / 1.098) |
| DLY, XY, one unit per router | A, M | 20330 / 19300 (1.185 / 1.164) | 24810 / 23524 (1.165 / 1.141) |

### 4x4

| design | cuts | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|
| DeFT | none | 17176 / 16680 (1.000 / 1.000) | 21318 / 20789 (1.000 / 1.000) |
| LB-I heuristic of round 18, one unit per router | none | 22786 / 19968 (1.327 / 1.197) | 27325 / 25038 (1.282 / 1.204) |
| LB-I heuristic of round 18, one unit per input port | none | 41900 / 28397 (2.439 / 1.702) | 52448 / 36587 (2.460 / 1.760) |
| fast selection of round 21, per router (its table: hierarchy kept) | its cut | 22375 (1.303) | 26629 (1.249) |
| fast selection of round 21, per input port (its table: hierarchy kept) | its cut | 34738 (2.022) | 42299 (1.984) |
| relation only, LF structure | none | 19509 / 15457 (1.136 / 0.927) | 24164 / 19576 (1.134 / 0.942) |
| relation only, DLY, per port | none | 18365 / 16284 (1.069 / 0.976) | 22781 / 20586 (1.069 / 0.990) |
| relation only, DLY, per router | none | 17632 / 16958 (1.027 / 1.017) | 21849 / 21069 (1.025 / 1.013) |
| LF, XY (main row) | none | 23656 / 18031 (1.377 / 1.081) | 30517 / 23736 (1.432 / 1.142) |
| LF, XY (main row) | M | 24236 / 18731 (1.411 / 1.123) | 31503 / 24846 (1.478 / 1.195) |
| LF, XY (main row) | A, B | 24679 / 19240 (1.437 / 1.153) | 32280 / 25912 (1.514 / 1.246) |
| LF, VN-split order (second row) | none | 27426 / 20662 (1.597 / 1.239) | 34483 / 26653 (1.618 / 1.282) |
| LF, VN-split order (second row) | M | 28589 / 22001 (1.664 / 1.319) | 36138 / 28652 (1.695 / 1.378) |
| LF, VN-split order (second row) | A, B | 29475 / 23308 (1.716 / 1.397) | 37436 / 30536 (1.756 / 1.469) |
| DLY, XY, one unit per input port | none | 21719 / 18210 (1.264 / 1.092) | 27881 / 24000 (1.308 / 1.154) |
| DLY, XY, one unit per input port | M | 22296 / 19230 (1.298 / 1.153) | 28914 / 24864 (1.356 / 1.196) |
| DLY, XY, one unit per input port | A, M | 22882 / 19549 (1.332 / 1.172) | 29899 / 26098 (1.403 / 1.255) |
| DLY, XY, one unit per router | none | 19535 / 18249 (1.137 / 1.094) | 23877 / 22501 (1.120 / 1.082) |
| DLY, XY, one unit per router | A, M | 20206 / 19177 (1.176 / 1.150) | 24665 / 23597 (1.157 / 1.135) |

### System level: average router area relative to DeFT (hierarchy kept / flattened)

Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL routers. Chiplet routers of the late-binding designs: the chiplet router of round 18 with the exit LUT; on 2x2, where the default-VL penalty is used (D = 2), with the table of the default entry VL (16 (C - 1) x 2 bits) in addition. The 3x3 interposer routers are the 4x4 ones (the RTL depends on the size through the coordinate width and D only).

| design | cuts | 2x2 | 3x3 | 4x4 |
|---|---|---|---|---|
| DeFT | none | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| LB-I heuristic of round 18, one unit per router | none | 1.163 / 1.094 | 1.160 / 1.105 | 1.161 / 1.106 |
| LB-I heuristic of round 18, one unit per input port | none | 1.735 / 1.334 | 1.707 / 1.369 | 1.714 / 1.362 |
| LF, XY (main row) | none | 1.232 / 1.080 | 1.198 / 1.055 | 1.200 / 1.056 |
| LF, XY (main row) | M | 1.251 / 1.103 | 1.217 / 1.077 | 1.218 / 1.079 |
| LF, XY (main row) | A, B | 1.264 / 1.122 | 1.231 / 1.096 | 1.232 / 1.097 |
| LF, VN-split order (second row) | none | 1.342 / 1.157 | 1.301 / 1.131 | 1.302 / 1.131 |
| LF, VN-split order (second row) | M | 1.378 / 1.204 | 1.336 / 1.173 | 1.337 / 1.173 |
| LF, VN-split order (second row) | A, B | 1.403 / 1.245 | 1.363 / 1.213 | 1.363 / 1.214 |
| DLY, XY, one unit per input port | none | 1.174 / 1.087 | 1.141 / 1.061 | 1.143 / 1.062 |
| DLY, XY, one unit per input port | M | 1.194 / 1.109 | 1.160 / 1.088 | 1.162 / 1.089 |
| DLY, XY, one unit per input port | A, M | 1.213 / 1.131 | 1.178 / 1.103 | 1.180 / 1.104 |
| DLY, XY, one unit per router | none | 1.099 / 1.078 | 1.070 / 1.051 | 1.072 / 1.052 |
| DLY, XY, one unit per router | A, M | 1.118 / 1.104 | 1.089 / 1.078 | 1.091 / 1.079 |

### Where the area is (hierarchy kept, um^2 and flip-flops)

2x2, interposer (5 ports):

| design | cuts | total | FF | buffers | crossbar | allocators | relation | decision units + reports | fallback | tables | NI logic | stored decisions + glue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | 17152 | 1795 | 10922 (1370) | 2642 (170) | 3128 (255) | 213 (0) | - | - | - | - | 248 (0) |
| LB-I heuristic of round 18, one unit per router | none | 22963 | 1939 | 10922 (1370) | 2819 (170) | 3473 (300) | 329 (0) | 5024 (96) | - | - | 2 (0) | 394 (3) |
| relation only, LF structure | none | 19509 | 1880 | 10922 (1370) | 2827 (170) | 3359 (290) | 1712 (0) | - | - | - | - | 689 (50) |
| LF, XY (main row) | M | 24470 | 2133 | 10922 (1370) | 2827 (170) | 3359 (290) | 2032 (0) | 4075 (206) | 119 (0) | - | - | 1136 (97) |
| LF, VN-split order (second row) | M | 29057 | 2311 | 10922 (1370) | 2827 (170) | 3359 (290) | 2410 (0) | 7761 (340) | 238 (0) | - | - | 1539 (141) |
| DLY, XY, one unit per input port | M | 22529 | 2046 | 10922 (1370) | 2827 (170) | 3415 (295) | 856 (0) | 4063 (204) | - | - | - | 446 (7) |
| DLY, XY, one unit per router | A, M | 20330 | 2062 | 10922 (1370) | 2827 (170) | 3497 (300) | 169 (0) | 2525 (209) | - | - | - | 390 (13) |

2x2, interposer + VL (6 ports):

| design | cuts | total | FF | buffers | crossbar | allocators | relation | decision units + reports | fallback | tables | NI logic | stored decisions + glue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | 21289 | 2184 | 13106 (1644) | 3453 (204) | 4205 (336) | 254 (0) | - | - | - | - | 271 (0) |
| LB-I heuristic of round 18, one unit per router | none | 27453 | 2367 | 13106 (1644) | 3665 (204) | 4636 (390) | 331 (0) | 5275 (126) | - | - | 2 (0) | 437 (3) |
| relation only, LF structure | none | 24164 | 2286 | 13106 (1644) | 3675 (204) | 4484 (378) | 2077 (0) | - | - | - | - | 822 (60) |
| LF, XY (main row) | M | 31876 | 2652 | 13106 (1644) | 3675 (204) | 4484 (378) | 2563 (0) | 6393 (297) | 179 (0) | - | - | 1477 (129) |
| LF, VN-split order (second row) | M | 36770 | 2838 | 13106 (1644) | 3675 (204) | 4484 (378) | 2960 (0) | 10365 (439) | 298 (0) | - | - | 1881 (173) |
| DLY, XY, one unit per input port | M | 29295 | 2535 | 13106 (1644) | 3675 (204) | 4551 (384) | 1034 (0) | 6379 (294) | - | - | - | 550 (9) |
| DLY, XY, one unit per router | A, M | 24810 | 2486 | 13106 (1644) | 3675 (204) | 4648 (390) | 171 (0) | 2761 (233) | - | - | - | 449 (15) |

4x4, interposer (5 ports):

| design | cuts | total | FF | buffers | crossbar | allocators | relation | decision units + reports | fallback | tables | NI logic | stored decisions + glue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | 17176 | 1795 | 10922 (1370) | 2642 (170) | 3128 (255) | 210 (0) | - | - | - | - | 275 (0) |
| LB-I heuristic of round 18, one unit per router | none | 22786 | 1939 | 10922 (1370) | 2819 (170) | 3473 (300) | 329 (0) | 4827 (96) | - | - | 3 (0) | 414 (3) |
| relation only, LF structure | none | 19509 | 1880 | 10922 (1370) | 2827 (170) | 3359 (290) | 1712 (0) | - | - | - | - | 689 (50) |
| LF, XY (main row) | M | 24236 | 2125 | 10922 (1370) | 2827 (170) | 3359 (290) | 2032 (0) | 3841 (198) | 119 (0) | - | - | 1136 (97) |
| LF, VN-split order (second row) | M | 28589 | 2295 | 10922 (1370) | 2827 (170) | 3359 (290) | 2410 (0) | 7294 (324) | 238 (0) | - | - | 1539 (141) |
| DLY, XY, one unit per input port | M | 22296 | 2038 | 10922 (1370) | 2827 (170) | 3415 (295) | 856 (0) | 3830 (196) | - | - | - | 446 (7) |
| DLY, XY, one unit per router | A, M | 20206 | 2054 | 10922 (1370) | 2827 (170) | 3497 (300) | 169 (0) | 2401 (201) | - | - | - | 390 (13) |

4x4, interposer + VL (6 ports):

| design | cuts | total | FF | buffers | crossbar | allocators | relation | decision units + reports | fallback | tables | NI logic | stored decisions + glue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | 21318 | 2184 | 13106 (1644) | 3453 (204) | 4205 (336) | 251 (0) | - | - | - | - | 303 (0) |
| LB-I heuristic of round 18, one unit per router | none | 27325 | 2367 | 13106 (1644) | 3665 (204) | 4636 (390) | 331 (0) | 5124 (126) | - | - | 3 (0) | 459 (3) |
| relation only, LF structure | none | 24164 | 2286 | 13106 (1644) | 3675 (204) | 4484 (378) | 2077 (0) | - | - | - | - | 822 (60) |
| LF, XY (main row) | M | 31503 | 2640 | 13106 (1644) | 3675 (204) | 4484 (378) | 2563 (0) | 6015 (285) | 179 (0) | - | - | 1481 (129) |
| LF, VN-split order (second row) | M | 36138 | 2818 | 13106 (1644) | 3675 (204) | 4484 (378) | 2960 (0) | 9733 (419) | 298 (0) | - | - | 1881 (173) |
| DLY, XY, one unit per input port | M | 28914 | 2523 | 13106 (1644) | 3675 (204) | 4551 (384) | 1034 (0) | 5998 (282) | - | - | - | 550 (9) |
| DLY, XY, one unit per router | A, M | 24665 | 2478 | 13106 (1644) | 3675 (204) | 4648 (390) | 171 (0) | 2615 (225) | - | - | - | 449 (15) |

## F4: timing (OpenSTA on the flattened netlists, pre-layout, ideal clock, no wires; ns)

Stage time = arrival + setup of the longest path into a group of registers. **T_ref** = the longest stage of the DeFT router of the same type and size in the same run: its clock period in this flow. Margins below 0.13 ns (the spread of this flow on unchanged logic, see the chiplet routers below) are called marginal.

| router | size | T_ref | its longest stage | route stage (XY to the VL) | VC allocation | switch allocation + crossbar | link stage (buffer write) + T_CQ |
|---|---|---|---|---|---|---|---|
| interposer (5 ports) | 2x2 | 1.27 | switch allocation | 0.97 | 1.20 | 1.27 | 0.43 |
| interposer + VL (6 ports) | 2x2 | 1.32 | switch allocation | 0.88 | 1.23 | 1.32 | 0.43 |
| interposer (5 ports) | 3x3 | 1.31 | switch allocation | 0.89 | 1.23 | 1.31 | 0.41 |
| interposer + VL (6 ports) | 3x3 | 1.27 | switch allocation | 0.86 | 1.26 | 1.27 | 0.45 |
| interposer (5 ports) | 4x4 | 1.31 | switch allocation | 0.89 | 1.23 | 1.31 | 0.41 |
| interposer + VL (6 ports) | 4x4 | 1.27 | switch allocation | 0.86 | 1.26 | 1.27 | 0.45 |

T_CQ = 0.11 ns is added to every stage that starts on a link: the clock-to-output delay of the upstream output register, which a path launched at an input port does not contain. Link wires have no delay in this flow.

### Decision path: LF, XY (main row)

Stages: the head is read on the link (first stage), registers after stage A / M / B where cut, the stored decision at the end. Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4) as first stage / middle stages / last stage. Route at the front = the relation of the head at the buffer front into its offered-output register (every head). Residual = max(0, L_dec - 2).

| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |
|---|---|---|---|---|---|---|---|---|
| none | 1 | 1.80 | - | (the first) | 0.72 | no (-0.80) | no (-0.49) | 0 |
| A | 2 | 0.93 | - | 1.41 | 0.73 | no (-0.41) | no (-0.14) | 0 |
| M | 2 | 1.04 | - | 1.09 | 0.73 | no (-0.09) | yes (+0.23) | 0 |
| B | 2 | 1.28 | - | 0.85 | 0.74 | no (-0.28) | no (-0.01) | 0 |
| A, M | 3 | 0.93 | 0.68 | 1.05 | 0.73 | no (-0.05) | yes (+0.26) | 1 |
| A, B | 3 | 0.93 | 0.89 | 0.81 | 0.71 | yes (+0.07) | yes (+0.34) | 1 |
| M, B | 3 | 1.04 | 0.39 | 0.81 | 0.74 | no (-0.04) | yes (+0.23) | 1 |
| A, M, B | 4 | 1.00 | 0.71, 0.39 | 0.86 | 0.73 | yes (+0.00) | yes (+0.27) | 2 |

At 1 ns: **L_dec = 3, N_fast = 2** (cuts: A, B; worst margin +0.07 ns, on RA on ipos6 4x4; inside the spread of the flow, 0.13 ns); residual 1.

At T_ref: **L_dec = 2, N_fast = 1** (cuts: M; worst margin +0.23 ns, on DMEM on ipos6 2x2); residual 0.

### Decision path: LF, VN-split order (second row)

Stages: the head is read on the link (first stage), registers after stage A / M / B where cut, the stored decision at the end. Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4) as first stage / middle stages / last stage. Route at the front = the relation of the head at the buffer front into its offered-output register (every head). Residual = max(0, L_dec - 2).

| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |
|---|---|---|---|---|---|---|---|---|
| none | 1 | 1.91 | - | (the first) | 0.72 | no (-0.91) | no (-0.59) | 0 |
| A | 2 | 0.97 | - | 1.51 | 0.74 | no (-0.51) | no (-0.19) | 0 |
| M | 2 | 1.09 | - | 1.10 | 0.70 | no (-0.10) | yes (+0.18) | 0 |
| B | 2 | 1.25 | - | 0.88 | 0.75 | no (-0.25) | yes (+0.03) | 0 |
| A, M | 3 | 0.97 | 0.70 | 1.12 | 0.73 | no (-0.12) | yes (+0.20) | 1 |
| A, B | 3 | 0.95 | 0.91 | 0.83 | 0.72 | yes (+0.05) | yes (+0.32) | 1 |
| M, B | 3 | 1.12 | 0.39 | 0.88 | 0.73 | no (-0.12) | yes (+0.15) | 1 |
| A, M, B | 4 | 1.02 | 0.71, 0.39 | 0.82 | 0.71 | no (-0.02) | yes (+0.30) | 2 |

At 1 ns: **L_dec = 3, N_fast = 2** (cuts: A, B; worst margin +0.05 ns, on RA on ipos6 4x4; inside the spread of the flow, 0.13 ns); residual 1.

At T_ref: **L_dec = 2, N_fast = 1** (cuts: M; worst margin +0.18 ns, on RM on ipos6 4x4); residual 0.

### Decision path: DLY, XY, one unit per input port

Stages: the head is read at the buffer front (first stage), registers after stage A / M / B where cut, the route registers at the end (also the end of the one-cycle route of a hop with one offered output). decision_delay = L_dec - 1.

| cuts | L_dec | first stage | middle stages | last stage | fits 1 ns (margin) | fits T_ref (margin) | decision_delay |
|---|---|---|---|---|---|---|---|
| none | 1 | 2.25 | - | (the first) | no (-1.25) | no (-0.98) | 0 |
| A | 2 | 1.27 | - | 1.66 | no (-0.66) | no (-0.39) | 1 |
| M | 2 | 1.27 | - | 1.31 | no (-0.31) | yes (+0.00) | 1 |
| B | 2 | 1.48 | - | 1.32 | no (-0.48) | no (-0.21) | 1 |
| A, M | 3 | 1.19 | 0.69 | 1.25 | no (-0.25) | yes (+0.06) | 2 |
| A, B | 3 | 1.22 | 0.91 | 1.32 | no (-0.32) | no (-0.05) | 2 |
| M, B | 3 | 1.24 | 0.39 | 1.26 | no (-0.26) | yes (+0.02) | 2 |
| A, M, B | 4 | 1.22 | 0.73, 0.39 | 1.25 | no (-0.25) | yes (+0.04) | 3 |

At 1 ns: **no configuration of the three cuts fits** (all three cuts: ROUTE on ipos6 2x2 is 0.25 ns over); a further cut is needed, L_dec >= 5.

At T_ref: **L_dec = 2, N_fast = 1** (cuts: M; worst margin +0.00 ns, on RM on ipos6 4x4; inside the spread of the flow, 0.13 ns); decision_delay 1.

### Decision path: DLY, XY, one unit per router

Stages: the head is read at the buffer front (first stage), registers after stage A / M / B where cut, the route registers at the end (also the end of the one-cycle route of a hop with one offered output). decision_delay = L_dec - 1.

| cuts | L_dec | first stage | middle stages | last stage | fits 1 ns (margin) | fits T_ref (margin) | decision_delay |
|---|---|---|---|---|---|---|---|
| none | 1 | 2.84 | - | (the first) | no (-1.84) | no (-1.57) | 0 |
| A | 2 | 1.59 | - | 1.71 | no (-0.71) | no (-0.44) | 1 |
| M | 2 | 1.62 | - | 1.64 | no (-0.64) | no (-0.31) | 1 |
| B | 2 | 1.94 | - | 1.76 | no (-0.94) | no (-0.67) | 1 |
| A, M | 3 | 1.48 | 0.70 | 1.54 | no (-0.54) | no (-0.23) | 2 |
| A, B | 3 | 1.50 | 0.95 | 1.63 | no (-0.63) | no (-0.36) | 2 |
| M, B | 3 | 1.65 | 0.39 | 1.64 | no (-0.65) | no (-0.38) | 2 |
| A, M, B | 4 | 1.50 | 0.70, 0.39 | 1.56 | no (-0.56) | no (-0.28) | 3 |

At 1 ns: **no configuration of the three cuts fits** (all three cuts: ROUTE on ipos6 2x2 is 0.56 ns over); a further cut is needed, L_dec >= 5.

At T_ref: **no configuration of the three cuts fits** (all three cuts: ROUTE on ipos6 4x4 is 0.28 ns over); a further cut is needed, L_dec >= 5.

### Route of a hop with one offered output, the fallback, and the period of the whole router

Per router: stage / T_ref of the same type and size. Route, one output: LF = the relation into the offered-output register (then the VC allocation asks for the only output); DLY and relation-only designs = the relation into the route registers. VC-allocation stage: for LF it contains the fallback (stored decision, free outputs, the request, the allocator, the route registers written at the grant). Valid bits: the bookkeeping of the stored decisions (set by the decision, cleared when the head leaves, i.e. behind the switch allocation). Whole router: its longest stage.

| design | cuts | router | size | T_ref | link stage + T_CQ | left in the link cycle for the wire | route, one output | VC-allocation stage | valid bits of the stored decisions | switch allocation | whole router | whole router / T_ref |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | ipos5 | 2x2 | 1.27 | 0.43 | 0.84 | 0.97 | 1.20 | - | 1.27 | 1.27 | 1.000 |
| DeFT | none | ipos6 | 2x2 | 1.32 | 0.43 | 0.89 | 0.88 | 1.23 | - | 1.32 | 1.32 | 1.000 |
| DeFT | none | ipos5 | 4x4 | 1.31 | 0.41 | 0.90 | 0.89 | 1.23 | - | 1.31 | 1.31 | 1.000 |
| DeFT | none | ipos6 | 4x4 | 1.27 | 0.45 | 0.82 | 0.86 | 1.26 | - | 1.27 | 1.27 | 1.000 |
| relation only, LF structure | none | ipos5 | 2x2 | 1.27 | 0.41 | 0.86 | 0.62 | 1.04 | - | 1.13 | 1.13 | 0.895 |
| relation only, LF structure | none | ipos6 | 2x2 | 1.32 | 0.42 | 0.90 | 0.69 | 1.12 | - | 1.20 | 1.20 | 0.911 |
| relation only, LF structure | none | ipos5 | 4x4 | 1.31 | 0.44 | 0.87 | 0.71 | 1.08 | - | 1.15 | 1.15 | 0.881 |
| relation only, LF structure | none | ipos6 | 4x4 | 1.27 | 0.41 | 0.86 | 0.73 | 1.15 | - | 1.20 | 1.20 | 0.947 |
| relation only, DLY, per port | none | ipos5 | 2x2 | 1.27 | 0.44 | 0.83 | 0.99 | 1.12 | - | 1.21 | 1.21 | 0.956 |
| relation only, DLY, per port | none | ipos6 | 2x2 | 1.32 | 0.42 | 0.90 | 1.12 | 1.19 | - | 1.28 | 1.28 | 0.967 |
| relation only, DLY, per port | none | ipos5 | 4x4 | 1.31 | 0.44 | 0.87 | 1.07 | 1.11 | - | 1.17 | 1.17 | 0.895 |
| relation only, DLY, per port | none | ipos6 | 4x4 | 1.27 | 0.43 | 0.84 | 1.01 | 1.18 | - | 1.25 | 1.25 | 0.980 |
| relation only, DLY, per router | none | ipos5 | 2x2 | 1.27 | 0.44 | 0.83 | 1.28 | 1.22 | - | 1.33 | 1.33 | 1.053 |
| relation only, DLY, per router | none | ipos6 | 2x2 | 1.32 | 0.44 | 0.88 | 1.38 | 1.32 | - | 1.39 | 1.39 | 1.055 |
| relation only, DLY, per router | none | ipos5 | 4x4 | 1.31 | 0.44 | 0.87 | 1.27 | 1.26 | - | 1.31 | 1.31 | 1.000 |
| relation only, DLY, per router | none | ipos6 | 4x4 | 1.27 | 0.44 | 0.83 | 1.45 | 1.38 | - | 1.44 | 1.45 | 1.142 |
| LF, XY (main row) | M | ipos5 | 2x2 | 1.27 | 0.84 | 0.42 | 0.66 | 1.08 | 1.08 | 1.15 | 1.15 | 0.907 |
| LF, XY (main row) | M | ipos6 | 2x2 | 1.32 | 0.92 | 0.40 | 0.73 | 1.20 | 1.15 | 1.23 | 1.23 | 0.934 |
| LF, XY (main row) | M | ipos5 | 4x4 | 1.31 | 1.04 | 0.28 | 0.66 | 1.10 | 1.09 | 1.18 | 1.18 | 0.897 |
| LF, XY (main row) | M | ipos6 | 4x4 | 1.27 | 0.98 | 0.29 | 0.70 | 1.13 | 1.11 | 1.22 | 1.22 | 0.958 |
| LF, VN-split order (second row) | M | ipos5 | 2x2 | 1.27 | 0.90 | 0.37 | 0.64 | 1.14 | 1.12 | 1.20 | 1.20 | 0.949 |
| LF, VN-split order (second row) | M | ipos6 | 2x2 | 1.32 | 1.00 | 0.32 | 0.69 | 1.20 | 1.19 | 1.25 | 1.25 | 0.949 |
| LF, VN-split order (second row) | M | ipos5 | 4x4 | 1.31 | 0.98 | 0.33 | 0.65 | 1.16 | 1.14 | 1.23 | 1.23 | 0.938 |
| LF, VN-split order (second row) | M | ipos6 | 4x4 | 1.27 | 1.09 | 0.18 | 0.70 | 1.19 | 1.17 | 1.23 | 1.23 | 0.971 |
| DLY, XY, one unit per input port | M | ipos5 | 2x2 | 1.27 | 0.42 | 0.85 | 1.15 | 1.12 | - | 1.16 | 1.16 | 0.911 |
| DLY, XY, one unit per input port | M | ipos6 | 2x2 | 1.32 | 0.44 | 0.88 | 1.31 | 1.25 | - | 1.28 | 1.31 | 0.989 |
| DLY, XY, one unit per input port | M | ipos5 | 4x4 | 1.31 | 0.44 | 0.87 | 1.15 | 1.14 | - | 1.22 | 1.22 | 0.931 |
| DLY, XY, one unit per input port | M | ipos6 | 4x4 | 1.27 | 0.44 | 0.83 | 1.26 | 1.22 | - | 1.28 | 1.28 | 1.006 |
| DLY, XY, one unit per input port | A, M | ipos5 | 2x2 | 1.27 | 0.44 | 0.83 | 1.11 | 1.10 | - | 1.15 | 1.15 | 0.910 |
| DLY, XY, one unit per input port | A, M | ipos6 | 2x2 | 1.32 | 0.44 | 0.88 | 1.25 | 1.22 | - | 1.26 | 1.26 | 0.955 |
| DLY, XY, one unit per input port | A, M | ipos5 | 4x4 | 1.31 | 0.45 | 0.86 | 1.11 | 1.11 | - | 1.19 | 1.19 | 0.909 |
| DLY, XY, one unit per input port | A, M | ipos6 | 4x4 | 1.27 | 0.44 | 0.83 | 1.21 | 1.19 | - | 1.24 | 1.24 | 0.977 |
| DLY, XY, one unit per router | A, M, B | ipos5 | 2x2 | 1.27 | 0.43 | 0.84 | 1.34 | 1.32 | - | 1.33 | 1.34 | 1.055 |
| DLY, XY, one unit per router | A, M, B | ipos6 | 2x2 | 1.32 | 0.44 | 0.88 | 1.56 | 1.50 | - | 1.44 | 1.56 | 1.181 |
| DLY, XY, one unit per router | A, M, B | ipos5 | 4x4 | 1.31 | 0.43 | 0.89 | 1.35 | 1.31 | - | 1.38 | 1.38 | 1.053 |
| DLY, XY, one unit per router | A, M, B | ipos6 | 4x4 | 1.27 | 0.44 | 0.83 | 1.56 | 1.50 | - | 1.45 | 1.56 | 1.224 |
| DLY, XY, one unit per router | A, M | ipos5 | 2x2 | 1.27 | 0.42 | 0.85 | 1.36 | 1.33 | - | 1.40 | 1.40 | 1.103 |
| DLY, XY, one unit per router | A, M | ipos6 | 2x2 | 1.32 | 0.43 | 0.89 | 1.54 | 1.51 | - | 1.50 | 1.54 | 1.163 |
| DLY, XY, one unit per router | A, M | ipos5 | 4x4 | 1.31 | 0.42 | 0.89 | 1.35 | 1.34 | - | 1.35 | 1.35 | 1.032 |
| DLY, XY, one unit per router | A, M | ipos6 | 4x4 | 1.27 | 0.44 | 0.83 | 1.50 | 1.46 | - | 1.46 | 1.50 | 1.180 |

Whole router / T_ref, range over the four routers: relation only, LF structure 0.881 - 0.947; relation only, DLY, per port 0.895 - 0.980; relation only, DLY, per router 1.000 - 1.142; LF, XY (main row) (cuts M) 0.897 - 0.958; LF, VN-split order (second row) (cuts M) 0.938 - 0.971; DLY, XY, one unit per input port (cuts M) 0.911 - 1.006; DLY, XY, one unit per input port (cuts A, M) 0.909 - 0.977; DLY, XY, one unit per router (cuts A, M, B) 1.053 - 1.224; DLY, XY, one unit per router (cuts A, M) 1.032 - 1.180.

Link stage = the longest path that starts on a link (DeFT, DLY: the buffer write; LF: the first stage of the decision) plus T_CQ. Left in the link cycle for the wire, range over the four routers: DeFT 0.82 - 0.90 ns; LF, XY (main row) (cuts M) 0.28 - 0.42 ns; LF, VN-split order (second row) (cuts M) 0.18 - 0.37 ns; DLY, XY, one unit per input port (cuts M) 0.83 - 0.88 ns; DLY, XY, one unit per input port (cuts A, M) 0.83 - 0.88 ns; DLY, XY, one unit per router (cuts A, M, B) 0.83 - 0.89 ns; DLY, XY, one unit per router (cuts A, M) 0.83 - 0.89 ns.

### Chiplet routers (unchanged logic; longest stage, ns)

The chiplet routers of the late-binding designs are those of round 18 (exit LUT); on 2x2 the table of the default entry VL is added at the NI. Their allocation stages are those of DeFT; the differences below are the spread of the flow on unchanged logic.

| size | router | DeFT | chiplet router of round 18 (exit LUT) | with the default-entry table (2x2) |
|---|---|---|---|---|
| 2x2 | chiplet (5 ports) | 1.25 | 1.22 | 1.37 |
| 2x2 | boundary (6 ports) | 1.28 | 1.34 | 1.37 |
| 3x3 | chiplet (5 ports) | 1.26 | 1.25 | - |
| 3x3 | boundary (6 ports) | 1.31 | 1.25 | - |
| 4x4 | chiplet (5 ports) | 1.24 | 1.25 | - |
| 4x4 | boundary (6 ports) | 1.27 | 1.30 | - |

Difference to DeFT over these netlists: -0.05 to +0.13 ns. The largest, 0.13 ns, is taken as the spread of the flow: a margin below it is called marginal.

### Measured decision latency (`hw/n_fast.json`)

| design | at 1 ns: cuts, L_dec, N_fast | at T_ref: cuts, L_dec, N_fast | consequence at T_ref |
|---|---|---|---|
| LF, XY (main row) | A, B, 3, 2 (marginal) | M, 2, 1 | residual 0 |
| LF, VN-split order (second row) | A, B, 3, 2 (marginal) | M, 2, 1 | residual 0 |
| DLY, XY, one unit per input port | does not fit with three cuts | M, 2, 1 (marginal) | decision_delay 1 |
| DLY, XY, one unit per router | does not fit with three cuts | does not fit with three cuts | - |

