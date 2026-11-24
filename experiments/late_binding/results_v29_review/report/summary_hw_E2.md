# v29 E2: two RTL variants of the interposer router (report_v29_hw.py e2)

The interposer router of the main row (round 25: lookahead routing with a fallback, XY) without the reports across the VLs (`LB_noVLrep`), and without any
report (`LB_noLA`: the decision unit has the credit counts of the router, the static hop terms and the bias). RTL: `hw/rtl/lb29_units.v`, the units of round 25
with two macros; the main row is built from the same file with both macros at 1 and synthesised in the same run. Router top, core, test benches and
checkers are those of round 25. Flow as round 25 (NanGate45 typical, Yosys + ABC at 1 GHz, OpenSTA on the flattened netlists, pre-layout, no wires).

## E2.1 Checks

Vectors from runs of the matching simulator row through the Verilator checkers of round 25 (`hw/functional_check_variants.txt`): every selection vector with
each of the eight cut configurations, and the front vectors. Control: the selection vectors of a variant through the units of the main row.

| design | simulator runs (statistics identical to bin/noxim) | selection vectors | of those with a choice | front vectors | applied in all | mismatches | control: vectors, mismatches |
|---|---|---|---|---|---|---|---|
| main | 12 (12) | 1870613 | 564929 | 4250603 | 19215507 | 0 | - |
| noVLrep | 12 (12) | 1868162 | 563659 | 4250347 | 19195643 | 0 | 1868162, 9181 |
| noLA | 12 (12) | 1851164 | 557462 | 4370897 | 19180209 | 0 | 1851164, 309078 |

**All vectors match, every instrumented run equals bin/noxim, the controls give mismatches: yes.**

Router-level test under random packets, reports and credit delays (`hw/router_smoke_variants.txt`): configurations 96, OK 96, FAIL 0.
Cycles of a head through an idle router (`hw/latency_check_variants.txt`): configurations 96, all as expected: **yes**.

## E2.2 Area of the interposer routers (um^2: hierarchy kept / core kept / flattened; in brackets relative to DeFT's router of the same type and size)

Cuts: the registers inside the decision unit (after stage A, M, B). "M" is the configuration of the main row in round 25; the last column of E2.4 gives the
configuration each design needs at T_ref.

### 2x2

| design | cuts | interposer (5 ports) | interposer + VL (6 ports) | flip-flops (ipos5, ipos6) | report inputs read (of 150) |
|---|---|---|---|---|---|
| main row | none | 23869 / 20016 / 18066 (1.392 / 1.201 / 1.090) | 30822 / 26127 / 23896 (1.448 / 1.261 / 1.159) | 1999, 2439 | 72, 84 |
| main row | M | 24470 / 20704 / 18695 (1.427 / 1.242 / 1.128) | 31836 / 27225 / 24899 (1.495 / 1.314 / 1.208) | 2133, 2652 | 72, 84 |
| `LB_noVLrep`: no reports across the VLs | none | 23869 / 20016 / 18066 (1.392 / 1.201 / 1.090) | 30529 / 26027 / 23594 (1.434 / 1.256 / 1.144) | 1999, 2427 | 72, 72 |
| `LB_noVLrep`: no reports across the VLs | M | 24470 / 20704 / 18728 (1.427 / 1.242 / 1.130) | 31494 / 26961 / 24722 (1.479 / 1.301 / 1.199) | 2133, 2640 | 72, 72 |
| `LB_noLA`: no reports at all | none | 22292 / 19212 / 17286 (1.300 / 1.153 / 1.043) | 28367 / 24669 / 22327 (1.332 / 1.190 / 1.083) | 1927, 2355 | 0, 0 |
| `LB_noLA`: no reports at all | M | 22935 / 19821 / 17928 (1.337 / 1.189 / 1.082) | 29372 / 25782 / 23523 (1.380 / 1.244 / 1.141) | 2053, 2556 | 0, 0 |
| `LB_noLA`: no reports at all | B | 22767 / 19645 / 17742 (1.327 / 1.179 / 1.071) | 29134 / 25498 / 23182 (1.368 / 1.230 / 1.124) | 2029, 2520 | 0, 0 |

### 4x4

| design | cuts | interposer (5 ports) | interposer + VL (6 ports) | flip-flops (ipos5, ipos6) | report inputs read (of 150) |
|---|---|---|---|---|---|
| main row | none | 23665 / 20005 / 18009 (1.378 / 1.195 / 1.080) | 30538 / 26044 / 23650 (1.433 / 1.252 / 1.138) | 1999, 2439 | 72, 84 |
| main row | M | 24215 / 20630 / 18712 (1.410 / 1.233 / 1.122) | 31501 / 27060 / 24773 (1.478 / 1.301 / 1.192) | 2125, 2640 | 72, 84 |
| `LB_noVLrep`: no reports across the VLs | none | 23665 / 20005 / 18009 (1.378 / 1.195 / 1.080) | 30225 / 25748 / 23361 (1.418 / 1.238 / 1.124) | 1999, 2427 | 72, 72 |
| `LB_noVLrep`: no reports across the VLs | M | 24215 / 20630 / 18712 (1.410 / 1.233 / 1.122) | 31140 / 26914 / 24534 (1.461 / 1.294 / 1.180) | 2125, 2628 | 72, 72 |
| `LB_noLA`: no reports at all | none | 22064 / 19270 / 17202 (1.285 / 1.151 / 1.031) | 28102 / 24745 / 22302 (1.318 / 1.190 / 1.073) | 1927, 2355 | 0, 0 |
| `LB_noLA`: no reports at all | M | 22749 / 19862 / 17924 (1.324 / 1.187 / 1.075) | 29088 / 25709 / 23462 (1.364 / 1.236 / 1.129) | 2045, 2544 | 0, 0 |
| `LB_noLA`: no reports at all | B | 22610 / 19610 / 17714 (1.316 / 1.172 / 1.062) | 28863 / 25368 / 23062 (1.354 / 1.220 / 1.109) | 2029, 2520 | 0, 0 |

The main row built from `lb29_units.v` against the main row built from the units of round 25 (`lb25_units.v`, the E3 run), cuts M, four routers: the areas
differ by at most 0.13 % / 0.29 % / 0.54 % (hierarchy kept / core kept / flattened). The two texts describe the same logic (the vectors above) but are not synthesised to the same
netlists, so every comparison of this part is between designs built from the one file. The 3x3 rows of the system table use the 4x4 interposer routers, and
the timing tables the routers of 2x2 and 4x4, as in round 25.

## E2.3 System: average router area relative to DeFT (hierarchy kept / core kept / flattened)

Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers. The chiplet routers are those of the main row for every variant
(they send no report in a variant that reads none: wires, no logic). The 3x3 interposer routers are the 4x4 ones.

| design | cuts | 2x2 | 3x3 | 4x4 |
|---|---|---|---|---|
| main row | M | 1.251 / 1.161 / 1.101 | 1.216 / 1.129 / 1.077 | 1.218 / 1.132 / 1.078 |
| `LB_noVLrep`: no reports across the VLs | M | 1.248 / 1.159 / 1.101 | 1.214 / 1.128 / 1.075 | 1.215 / 1.131 / 1.076 |
| `LB_noLA`: no reports at all | M | 1.203 / 1.133 / 1.075 | 1.170 / 1.104 / 1.051 | 1.172 / 1.107 / 1.052 |
| `LB_noLA`: no reports at all | B | 1.197 / 1.127 / 1.069 | 1.166 / 1.096 / 1.044 | 1.168 / 1.099 / 1.045 |

2x2, LB_noVLrep against the main row (cuts M): 0.998 / 0.998 / 1.000 of the main row's area; of the main row's area above DeFT it keeps 99 % / 99 % / 100 %.
2x2, LB_noLA against the main row (cuts M): 0.962 / 0.975 / 0.976 of the main row's area; of the main row's area above DeFT it keeps 81 % / 82 % / 74 %.
3x3, LB_noVLrep against the main row (cuts M): 0.998 / 0.999 / 0.998 of the main row's area; of the main row's area above DeFT it keeps 99 % / 99 % / 98 %.
3x3, LB_noLA against the main row (cuts M): 0.962 / 0.978 / 0.976 of the main row's area; of the main row's area above DeFT it keeps 79 % / 80 % / 66 %.
4x4, LB_noVLrep against the main row (cuts M): 0.998 / 0.999 / 0.998 of the main row's area; of the main row's area above DeFT it keeps 99 % / 99 % / 98 %.
4x4, LB_noLA against the main row (cuts M): 0.962 / 0.978 / 0.976 of the main row's area; of the main row's area above DeFT it keeps 79 % / 81 % / 67 %.

## E2.4 Timing (OpenSTA on the flattened netlists; ns)

T_ref of a router type and size = the longest stage of DeFT's router of that type and size in this run: ipos5 2x2 1.27; ipos6 2x2 1.32; ipos5 4x4 1.31; ipos6 4x4 1.27.
Spread of the flow on unchanged logic (the chiplet routers, as round 25): 0.13 ns; a margin below it is called marginal.

### Decision path: main row

Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4). First stage: from the link. Route at the front: the relation of the head at the
buffer front into its offered-output register.

| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |
|---|---|---|---|---|---|---|---|---|
| none | 1 | 1.93 | - | (the first) | 0.74 | no (-0.93) | no (-0.66) | 0 |
| A | 2 | 0.95 | - | 1.42 | 0.76 | no (-0.42) | no (-0.10) | 0 |
| M | 2 | 1.02 | - | 1.06 | 0.72 | no (-0.06) | yes (+0.22) | 0 |
| B | 2 | 1.21 | - | 0.85 | 0.71 | no (-0.21) | yes (+0.10) | 0 |
| A, M | 3 | 0.97 | 0.71 | 1.10 | 0.72 | no (-0.10) | yes (+0.22) | 1 |
| A, B | 3 | 1.03 | 0.91 | 0.88 | 0.77 | no (-0.03) | yes (+0.24) | 1 |
| M, B | 3 | 1.03 | 0.39 | 0.85 | 0.70 | no (-0.03) | yes (+0.25) | 1 |
| A, M, B | 4 | 0.92 | 0.71, 0.39 | 0.83 | 0.71 | yes (+0.08) | yes (+0.35) | 2 |

At 1 ns: **L_dec = 4** (cuts: A, M, B; worst margin +0.08 ns, on RA on ipos6 4x4; inside the spread of the flow); residual 2.

At T_ref: **L_dec = 2** (cuts: M; worst margin +0.22 ns, on DMEM on ipos6 4x4); residual 0.

### Decision path: `LB_noVLrep`: no reports across the VLs

Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4). First stage: from the link. Route at the front: the relation of the head at the
buffer front into its offered-output register.

| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |
|---|---|---|---|---|---|---|---|---|
| none | 1 | 1.88 | - | (the first) | 0.75 | no (-0.88) | no (-0.61) | 0 |
| A | 2 | 0.96 | - | 1.37 | 0.74 | no (-0.37) | no (-0.09) | 0 |
| M | 2 | 1.08 | - | 1.09 | 0.72 | no (-0.09) | yes (+0.19) | 0 |
| B | 2 | 1.17 | - | 0.84 | 0.73 | no (-0.17) | yes (+0.13) | 0 |
| A, M | 3 | 0.94 | 0.66 | 1.06 | 0.73 | no (-0.06) | yes (+0.26) | 1 |
| A, B | 3 | 0.92 | 0.93 | 0.84 | 0.74 | yes (+0.07) | yes (+0.34) | 1 |
| M, B | 3 | 1.00 | 0.39 | 0.84 | 0.72 | no (-0.00) | yes (+0.27) | 1 |
| A, M, B | 4 | 0.94 | 0.66, 0.39 | 0.84 | 0.71 | yes (+0.06) | yes (+0.33) | 2 |

At 1 ns: **L_dec = 3** (cuts: A, B; worst margin +0.07 ns, on RB on ipos5 2x2; inside the spread of the flow); residual 1.

At T_ref: **L_dec = 2** (cuts: M; worst margin +0.19 ns, on RM on ipos6 4x4); residual 0.

### Decision path: `LB_noLA`: no reports at all

Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4). First stage: from the link. Route at the front: the relation of the head at the
buffer front into its offered-output register.

| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |
|---|---|---|---|---|---|---|---|---|
| none | 1 | 1.51 | - | (the first) | 0.75 | no (-0.51) | no (-0.19) | 0 |
| A | 2 | 0.93 | - | 1.22 | 0.71 | no (-0.22) | yes (+0.06) | 0 |
| M | 2 | 0.92 | - | 1.07 | 0.72 | no (-0.07) | yes (+0.19) | 0 |
| B | 2 | 1.01 | - | 0.80 | 0.71 | no (-0.01) | yes (+0.27) | 0 |
| A, M | 3 | 0.88 | 0.39 | 1.03 | 0.71 | no (-0.03) | yes (+0.24) | 1 |
| A, B | 3 | 0.92 | 0.62 | 0.87 | 0.73 | yes (+0.08) | yes (+0.35) | 1 |
| M, B | 3 | 0.88 | 0.38 | 0.89 | 0.75 | yes (+0.11) | yes (+0.38) | 1 |
| A, M, B | 4 | 0.88 | 0.39, 0.38 | 0.84 | 0.72 | yes (+0.12) | yes (+0.41) | 2 |

At 1 ns: **L_dec = 3** (cuts: M, B; worst margin +0.11 ns, on DMEM on ipos6 4x4; inside the spread of the flow); residual 1.

At T_ref: **L_dec = 2** (cuts: B; worst margin +0.27 ns, on RB on ipos6 4x4); residual 0.

## E2.5 The link cycle and the whole router

Link stage = the longest path that starts on a link input (DeFT: the buffer write; the designs of this round: the first stage of the decision, which reads the
head on the link) plus T_CQ = 0.11 ns. Left for the wire = T_ref minus the link stage: what an interposer link may take of the link cycle. Each design at the
cut configuration it needs at T_ref (and the main row's, M).

| design | cuts | router | size | T_ref | link stage + T_CQ | left for the wire | route, one output | VC-allocation stage | whole router | whole router / T_ref |
|---|---|---|---|---|---|---|---|---|---|---|
| DeFT | none | ipos5 | 2x2 | 1.27 | 0.43 | 0.84 | 0.97 | 1.20 | 1.27 | 1.000 |
| DeFT | none | ipos6 | 2x2 | 1.32 | 0.43 | 0.89 | 0.88 | 1.23 | 1.32 | 1.000 |
| DeFT | none | ipos5 | 4x4 | 1.31 | 0.41 | 0.90 | 0.89 | 1.23 | 1.31 | 1.000 |
| DeFT | none | ipos6 | 4x4 | 1.27 | 0.45 | 0.82 | 0.86 | 1.26 | 1.27 | 1.000 |
| main row | M | ipos5 | 2x2 | 1.27 | 0.85 | 0.41 | 0.63 | 1.07 | 1.14 | 0.898 |
| main row | M | ipos6 | 2x2 | 1.32 | 0.92 | 0.40 | 0.71 | 1.15 | 1.22 | 0.927 |
| main row | M | ipos5 | 4x4 | 1.31 | 1.01 | 0.30 | 0.69 | 1.12 | 1.15 | 0.876 |
| main row | M | ipos6 | 4x4 | 1.27 | 1.02 | 0.25 | 0.72 | 1.17 | 1.22 | 0.960 |
| `LB_noVLrep`: no reports across the VLs | M | ipos5 | 2x2 | 1.27 | 0.85 | 0.42 | 0.62 | 1.09 | 1.16 | 0.917 |
| `LB_noVLrep`: no reports across the VLs | M | ipos6 | 2x2 | 1.32 | 0.88 | 0.44 | 0.70 | 1.12 | 1.18 | 0.891 |
| `LB_noVLrep`: no reports across the VLs | M | ipos5 | 4x4 | 1.31 | 1.01 | 0.30 | 0.69 | 1.12 | 1.15 | 0.876 |
| `LB_noVLrep`: no reports across the VLs | M | ipos6 | 4x4 | 1.27 | 1.08 | 0.19 | 0.72 | 1.18 | 1.24 | 0.977 |
| `LB_noLA`: no reports at all | M | ipos5 | 2x2 | 1.27 | 0.84 | 0.42 | 0.67 | 1.08 | 1.15 | 0.910 |
| `LB_noLA`: no reports at all | M | ipos6 | 2x2 | 1.32 | 0.79 | 0.53 | 0.72 | 1.12 | 1.20 | 0.906 |
| `LB_noLA`: no reports at all | M | ipos5 | 4x4 | 1.31 | 0.86 | 0.45 | 0.64 | 1.09 | 1.16 | 0.882 |
| `LB_noLA`: no reports at all | M | ipos6 | 4x4 | 1.27 | 0.92 | 0.35 | 0.72 | 1.14 | 1.20 | 0.943 |
| `LB_noLA`: no reports at all | B | ipos5 | 2x2 | 1.27 | 0.95 | 0.32 | 0.62 | 1.08 | 1.17 | 0.920 |
| `LB_noLA`: no reports at all | B | ipos6 | 2x2 | 1.32 | 1.01 | 0.31 | 0.71 | 1.15 | 1.20 | 0.910 |
| `LB_noLA`: no reports at all | B | ipos5 | 4x4 | 1.31 | 0.91 | 0.40 | 0.67 | 1.10 | 1.17 | 0.892 |
| `LB_noLA`: no reports at all | B | ipos6 | 4x4 | 1.27 | 1.00 | 0.27 | 0.71 | 1.17 | 1.23 | 0.970 |

Left for the wire, range over the four routers: DeFT 0.82 to 0.90 ns; main (cuts M) 0.25 to 0.41 ns; LB_noVLrep (cuts M) 0.19 to 0.44 ns; LB_noLA (cuts M) 0.35 to 0.53 ns; LB_noLA (cuts B) 0.27 to 0.40 ns.

