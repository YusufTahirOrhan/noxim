# Horizontal-link fault coverage v3: exists-path and fault-aware pruning (formal model)

Model: formal/impl_relation_check.py `hl3` mode. Fault sets as results_v2/hl_coverage.md: all
208 single HL faults and the same 500 sampled double faults (seed 7), each without VL
faults and with VL mask 0x1111; relations A_fixed_XY (every VL pair explored), CI_XY_OE, FULL_OE_OE.

Metrics (share of the 4032 source-destination pairs):
* **always (v2, unaware):** no reachable state of the pair is a dead end, with routers that only
  refuse a faulty link next to them (as v2).
* **exists-path:** at least one routing path of the relation (some injection choice, some
  adaptive choice) is delivered. Fault-aware pruning only removes moves that cannot lead to
  delivery, so this share is the same with and without pruning (checked: column `exists aware`).
* **always (aware):** with fault-aware pruning. Routers know every HL fault of their own layer
  (all chiplet links for chiplet routers, all interposer links for interposer routers, as ReD
  distributes VL faults) and never take a move after which no remaining candidate (VL, or the
  destination in the intra/destination phase) is reachable on a minimal, turn-legal, fault-free path
  of that layer. Candidate sets and injection choices are unchanged, and faults of the other layer
  stay unknown (the exit VL is chosen without knowing the interposer, the entry VL without knowing
  the destination chiplet).
Elapsed: 1323 s on 11 processes. v2 cross-check: 4248 of 4248 rows identical (relation, mask, kind, layers, always, dead).

| relation | VL mask | HL faults | sets | always (v2, unaware): mean (min) | exists-path: mean (min) | always (aware): mean (min) | sets 100 % aware | dead states aware: mean | CDG acyclic aware | exists aware = unaware |
|---|---|---|---|---|---|---|---|---|---|---|
| A_fixed_XY | none | single, chiplet | 96 | 86.64 % (80.36 %) | 99.34 % (99.21 %) | 86.64 % (80.36 %) | 0 | 0.921 % | 96/96 | 96/96 |
| A_fixed_XY | none | single, interposer | 112 | 74.60 % (68.25 %) | 100.00 % (100.00 %) | 74.60 % (68.25 %) | 0 | 0.235 % | 112/112 | 112/112 |
| A_fixed_XY | none | single, all | 208 | 80.16 % (68.25 %) | 99.69 % (99.21 %) | 80.16 % (68.25 %) | 0 | 0.552 % | 208/208 | 208/208 |
| A_fixed_XY | none | double (sample) | 500 | 65.35 % (36.51 %) | 99.39 % (96.65 %) | 65.35 % (36.51 %) | 0 | 1.104 % | 500/500 | 500/500 |
| A_fixed_XY | 0x1111 | single, chiplet | 96 | 89.22 % (80.36 %) | 99.14 % (98.21 %) | 89.22 % (80.36 %) | 0 | 0.935 % | 96/96 | 96/96 |
| A_fixed_XY | 0x1111 | single, interposer | 112 | 82.31 % (68.25 %) | 100.00 % (100.00 %) | 82.31 % (68.25 %) | 34 | 0.229 % | 112/112 | 112/112 |
| A_fixed_XY | 0x1111 | single, all | 208 | 85.50 % (68.25 %) | 99.60 % (98.21 %) | 85.50 % (68.25 %) | 34 | 0.555 % | 208/208 | 208/208 |
| A_fixed_XY | 0x1111 | double (sample) | 500 | 74.27 % (36.51 %) | 99.20 % (96.13 %) | 74.27 % (36.51 %) | 11 | 1.088 % | 500/500 | 500/500 |
| CI_XY_OE | none | single, chiplet | 96 | 86.64 % (80.36 %) | 99.34 % (99.21 %) | 86.64 % (80.36 %) | 0 | 0.429 % | 96/96 | 96/96 |
| CI_XY_OE | none | single, interposer | 112 | 83.16 % (55.56 %) | 100.00 % (100.00 %) | 99.55 % (87.30 %) | 108 | 0.003 % | 112/112 | 112/112 |
| CI_XY_OE | none | single, all | 208 | 84.77 % (55.56 %) | 99.69 % (99.21 %) | 93.59 % (80.36 %) | 108 | 0.199 % | 208/208 | 208/208 |
| CI_XY_OE | none | double (sample) | 500 | 71.98 % (36.51 %) | 99.39 % (96.65 %) | 87.95 % (63.10 %) | 139 | 0.399 % | 500/500 | 500/500 |
| CI_XY_OE | 0x1111 | single, chiplet | 96 | 89.22 % (80.36 %) | 99.14 % (98.21 %) | 89.22 % (80.36 %) | 0 | 0.487 % | 96/96 | 96/96 |
| CI_XY_OE | 0x1111 | single, interposer | 112 | 84.75 % (49.21 %) | 100.00 % (100.00 %) | 99.77 % (87.30 %) | 110 | 0.002 % | 112/112 | 112/112 |
| CI_XY_OE | 0x1111 | single, all | 208 | 86.81 % (49.21 %) | 99.60 % (98.21 %) | 94.90 % (80.36 %) | 110 | 0.226 % | 208/208 | 208/208 |
| CI_XY_OE | 0x1111 | double (sample) | 500 | 75.89 % (35.91 %) | 99.21 % (96.13 %) | 90.50 % (63.10 %) | 144 | 0.444 % | 500/500 | 500/500 |
| FULL_OE_OE | none | single, chiplet | 96 | 89.53 % (70.49 %) | 99.70 % (99.60 %) | 96.33 % (85.34 %) | 0 | 0.034 % | 96/96 | 96/96 |
| FULL_OE_OE | none | single, interposer | 112 | 83.16 % (55.56 %) | 100.00 % (100.00 %) | 99.55 % (87.30 %) | 108 | 0.003 % | 112/112 | 112/112 |
| FULL_OE_OE | none | single, all | 208 | 86.10 % (55.56 %) | 99.86 % (99.60 %) | 98.06 % (85.34 %) | 108 | 0.017 % | 208/208 | 208/208 |
| FULL_OE_OE | none | double (sample) | 500 | 74.08 % (36.51 %) | 99.72 % (96.88 %) | 96.31 % (80.18 %) | 139 | 0.035 % | 500/500 | 500/500 |
| FULL_OE_OE | 0x1111 | single, chiplet | 96 | 90.43 % (70.49 %) | 99.70 % (99.60 %) | 97.47 % (85.34 %) | 0 | 0.046 % | 96/96 | 96/96 |
| FULL_OE_OE | 0x1111 | single, interposer | 112 | 84.75 % (49.21 %) | 100.00 % (100.00 %) | 99.77 % (87.30 %) | 110 | 0.002 % | 112/112 | 112/112 |
| FULL_OE_OE | 0x1111 | single, all | 208 | 87.37 % (49.21 %) | 99.86 % (99.60 %) | 98.71 % (85.34 %) | 110 | 0.022 % | 208/208 | 208/208 |
| FULL_OE_OE | 0x1111 | double (sample) | 500 | 76.75 % (29.22 %) | 99.72 % (96.88 %) | 97.61 % (80.28 %) | 144 | 0.045 % | 500/500 | 500/500 |

## Reading the numbers (comparison with the v2 worst-case metric)
* **Almost every pair still has a delivering path.** exists-path is 99.2-100 % for every relation
  and fault set (interposer single faults: 100 %). The large v2 losses (always delivered 65-87 %)
  come from fault-unaware choices that run into a faulty link, not from a lack of paths.
  The residual 0.1-0.8 % are mostly intra- or same-row pairs whose only minimal turn-legal
  path crosses a faulty chiplet link; minimal routing cannot detour around it.
* **Fault-aware pruning recovers most of the gap, but only where the relation has choices:**
  - FULL (late exit and entry, odd-even everywhere): single faults 86.1 % -> 98.1 %, double
    faults 74.1 % -> 96.3 % (without VL faults); with 0x1111, 87.4 % -> 98.7 % and 76.8 % ->
    97.6 %.
  - CI: interposer faults are recovered (83.2 % -> 99.6 %). Chiplet faults are not
    (86.6 % -> 86.6 %): CI keeps XY routing and a fixed LUT exit on the chiplets, so a router
    has nothing to choose from. Overall single faults 84.8 % -> 93.6 %, double 72.0 % -> 88.0 %.
  - Fixed pair (DeFT LUT and every injection-time policy): **no change** (80.2 % -> 80.2 %). With
    a fixed VL pair and XY routing there is no alternative move to prune to. Pruning only
    turns later dead ends into earlier ones (dead-state share 0.41 % -> 0.55 %).
* **Why aware pruning still falls short of exists-path** (e.g. FULL 98.1 % vs 99.9 %): the
  exit VL is chosen on the chiplet without knowledge of interposer faults, and the entry VL
  on the interposer without knowledge of destination-chiplet faults. A packet can commit to a
  VL from which the next layer has no fault-free minimal route. Interposer single faults
  with FULL still leave a worst case of 87.3 % for this reason. Closing it would need
  cross-layer fault information (or non-minimal detours), which neither the model nor the
  simulator has.
* **The CDG stays acyclic in every case** (pruning removes moves, so it cannot add
  dependencies). The unaware metric reproduces the v2 table exactly (4248 / 4248 rows).
* These are properties of the formal model of the routing relations. The simulator has no
  HL-fault support, so nothing here was simulated.
