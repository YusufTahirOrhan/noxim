# Horizontal-link fault coverage of the implemented relations (formal model)

Model: formal/impl_relation_check.py `hl` mode. Faulty horizontal links are bidirectional,
on a chiplet layer (C) or the interposer (I), and known only to the adjacent router: it never
takes a move onto a faulty link and adds no detour (candidate pruning stays fault-unaware).
Relations: A_fixed_XY (DeFT LUT and every injection-time policy: all functional VL pairs are
explored), CI_XY_OE (interposer-only late binding), FULL_OE_OE (full late binding).
Fault sets: all 208 single HL faults (96 chiplet, 112 interposer) and 500 random double faults (seed 7),
each without VL faults and with VL mask 0x1111.
"Pairs always delivered": share of the 4032 source-destination pairs for which no reachable
routing state (over every injection choice, VN and adaptive path) is a dead end. Because the
fixed-pair relation explores every VL pair, its figure is the worst case over all injection
policies, not the DeFT LUT pair alone. "Dead states": share of reachable routing states with no
legal move. Elapsed: 2122 s on 4 processes.

Without HL faults every relation delivers 100 % of the pairs with 0 dead states (both VL masks): A_fixed_XY/none: 1.000, 0.0000, A_fixed_XY/0x1111: 1.000, 0.0000, CI_XY_OE/none: 1.000, 0.0000, CI_XY_OE/0x1111: 1.000, 0.0000, FULL_OE_OE/none: 1.000, 0.0000, FULL_OE_OE/0x1111: 1.000, 0.0000.

| relation | VL mask | HL faults | sets | pairs always delivered: mean (min) | sets with 100 % pairs | dead states: mean (max) | CDG acyclic |
|---|---|---|---|---|---|---|---|
| A_fixed_XY | none | single, chiplet | 96 | 86.64 % (80.36 %) | 0 | 0.619 % (1.100 %) | 96/96 |
| A_fixed_XY | none | single, interposer | 112 | 74.60 % (68.25 %) | 0 | 0.233 % (0.356 %) | 112/112 |
| A_fixed_XY | none | single, all | 208 | 80.16 % (68.25 %) | 0 | 0.411 % (1.100 %) | 208/208 |
| A_fixed_XY | none | double (sample) | 500 | 65.35 % (36.51 %) | 0 | 0.811 % (2.213 %) | 500/500 |
| A_fixed_XY | 0x1111 | single, chiplet | 96 | 89.22 % (80.36 %) | 0 | 0.629 % (1.118 %) | 96/96 |
| A_fixed_XY | 0x1111 | single, interposer | 112 | 82.31 % (68.25 %) | 34 | 0.226 % (0.468 %) | 112/112 |
| A_fixed_XY | 0x1111 | single, all | 208 | 85.50 % (68.25 %) | 34 | 0.412 % (1.118 %) | 208/208 |
| A_fixed_XY | 0x1111 | double (sample) | 500 | 74.27 % (36.51 %) | 11 | 0.801 % (2.250 %) | 500/500 |
| CI_XY_OE | none | single, chiplet | 96 | 86.64 % (80.36 %) | 0 | 0.291 % (0.513 %) | 96/96 |
| CI_XY_OE | none | single, interposer | 112 | 83.16 % (55.56 %) | 26 | 0.282 % (0.940 %) | 112/112 |
| CI_XY_OE | none | single, all | 208 | 84.77 % (55.56 %) | 26 | 0.286 % (0.940 %) | 208/208 |
| CI_XY_OE | none | double (sample) | 500 | 71.98 % (36.51 %) | 6 | 0.584 % (1.730 %) | 500/500 |
| CI_XY_OE | 0x1111 | single, chiplet | 96 | 89.22 % (80.36 %) | 0 | 0.330 % (0.586 %) | 96/96 |
| CI_XY_OE | 0x1111 | single, interposer | 112 | 84.75 % (49.21 %) | 42 | 0.298 % (1.047 %) | 112/112 |
| CI_XY_OE | 0x1111 | single, all | 208 | 86.81 % (49.21 %) | 42 | 0.313 % (1.047 %) | 208/208 |
| CI_XY_OE | 0x1111 | double (sample) | 500 | 75.89 % (35.91 %) | 21 | 0.628 % (1.924 %) | 500/500 |
| FULL_OE_OE | none | single, chiplet | 96 | 89.53 % (70.49 %) | 0 | 0.103 % (0.187 %) | 96/96 |
| FULL_OE_OE | none | single, interposer | 112 | 83.16 % (55.56 %) | 26 | 0.311 % (1.037 %) | 112/112 |
| FULL_OE_OE | none | single, all | 208 | 86.10 % (55.56 %) | 26 | 0.215 % (1.037 %) | 208/208 |
| FULL_OE_OE | none | double (sample) | 500 | 74.08 % (36.51 %) | 6 | 0.450 % (1.911 %) | 500/500 |
| FULL_OE_OE | 0x1111 | single, chiplet | 96 | 90.43 % (70.49 %) | 0 | 0.149 % (0.261 %) | 96/96 |
| FULL_OE_OE | 0x1111 | single, interposer | 112 | 84.75 % (49.21 %) | 42 | 0.321 % (1.128 %) | 112/112 |
| FULL_OE_OE | 0x1111 | single, all | 208 | 87.37 % (49.21 %) | 42 | 0.242 % (1.128 %) | 208/208 |
| FULL_OE_OE | 0x1111 | double (sample) | 500 | 76.75 % (29.22 %) | 21 | 0.496 % (2.076 %) | 500/500 |

Removing links can only remove CDG edges, so the CDG stays acyclic by construction; the
column confirms it. The relations add no fault-aware detour, so every pair whose minimal
turn-legal paths all cross a faulty link is lost; the table measures how much path diversity
(late binding) recovers.

## Reading the numbers
* **No relation tolerates HL faults.** Without VL faults, not one single-HL-fault set keeps
  100 % of the pairs for the fixed-pair relation, and only 26 of 208 do for CI and FULL (all
  interposer links). Late binding raises the mean share of always-delivered pairs: single
  faults 80.2 % (fixed pair) -> 84.8 % (CI) -> 86.1 % (FULL); double faults 65.4 % -> 72.0 %
  -> 74.1 %. The worst case is no better (the minimum for single faults is 68.3 % or lower for
  every relation). Tolerating HL faults would need fault-aware detours, which none of the
  relations has.
* **Chiplet-link faults** are the weakest point of CI, which keeps XY routing and a
  fixed exit VL on the chiplets: CI equals the fixed-pair relation there (86.6 %). FULL's
  odd-even chiplet routing recovers part of it (89.5 %).
* **VL mask 0x1111 shows higher figures, but this is a property of the metric.** "Always
  delivered" is a worst case over every VL choice the relation allows. With fewer
  functional VLs there are fewer choices that can run into a faulty link. It does not mean
  VL faults help.
* **The fixed-pair figure is the worst case over all injection policies** (every VL pair is
  explored), so it is pessimistic for DeFT's single LUT pair. A DeFT-LUT-only figure would
  need the LUT in the model and was not computed.
* Raw per-fault-set results: hl_coverage.csv.
