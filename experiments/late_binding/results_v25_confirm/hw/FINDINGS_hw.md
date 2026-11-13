# v25 Part F: the hardware of the final design

**Sources.** RTL `rtl/` (`lb25_units.v`, `router25_top.v`, `core25.v`, `chip25_top.v`, `lb25_funcs.vh`; buffers, allocators and
crossbar are `results_v18_area/rtl/router_core.v`, unchanged). Test benches and checkers `tb/`. Drivers
`experiments_v25_hw.py`, `experiments_v25_hw2.py` (stages `f_*` of `experiments_v25.py`); tables `report_v25_hw.py` ->
`../report/summary_F.md`, `n_fast.json`, `../paper_data/hw_*.csv`. Per-design data `area_runs.csv`, `breakdown_runs.csv`,
`timing_runs.csv`; checks `functional_check.txt`, `mutation_check.txt`, `router_smoke.txt`, `latency_check.txt`.
Flow: Yosys + ABC (`abc -D 1000`), NanGate45 typical, OpenSTA, pre-layout: the flow, library and constraints of rounds 18
and 21 (`results_v18_area/tools.md`); DeFT and the round-18 late-binding router are synthesised again in the same run.
Decisions: `../DECISIONS.md`, Part F.

## Short answers
* **What is built.** The interposer router of the three heuristic rows: lookahead routing with the fallback (LF) for XY
  (`CI_heurLA_X_LF`, the main row) and for the VN-split order (`CI_heurLA_O_LF`), and the decision at the buffer front (DLY)
  for XY (`CI_heurLA_X_DLY`), with the reference core of round 18 around them.
* **Does the RTL compute what the simulator computes?** Yes: 6.12 M, 6.21 M and 4.97 M vectors per design from 36 simulator runs, the decisions applied with each of the eight register configurations, and 597 M checks of the tie break (0 mismatches required, 0 found). Of 25 single-line mutations of the RTL the same vectors catch 23; the two that pass change logic that no reachable input exercises.
* **Area.** Interposer router of the main row 1.41-1.50 x DeFT's (hierarchy kept), 1.23-1.31 x with the router core kept as one module and the rest flattened; chiplet router 1.01-1.02 x
  on 3x3 and 4x4 and 1.05-1.06 x on 2x2 (where the default-VL penalty needs a table); a whole system 1.22-1.25 x DeFT (hierarchy kept),
  1.13-1.16 x with the core kept. Round 18's heuristic: 1.16 x with one unit per router, 1.71-1.74 x with one per input port.
* **Timing.** The reference pipeline's period in this flow is 1.27-1.32 ns (T_ref, DeFT's switch allocation). The decision of
  the main row takes **two cycles at T_ref** (one register in the decision unit, margin +0.23 ns) and three at 1 ns (marginal).
  A hop with one offered output keeps the reference's four cycles in every design; the router's longest stage is not longer
  than DeFT's.
* **F5: can LF be built with residual delay 0?** **Yes at the period of the reference pipeline**: the decision is done in the
  cycle the head is on the link and its route cycle, the VC allocation finds the stored decision, and a head with a choice
  takes the four cycles of the reference pipeline (measured in RTL simulation). The evaluated main row is the mechanism that is
  built. Two conditions: the first stage of the decision reads the head on the link (0.28-0.42 ns of the link cycle are left
  for the wire, against 0.82-0.90 ns in DeFT's router), and the clock is the reference's, not 1 ns. If either fails the same
  RTL has one residual cycle; that row was run as an addendum (`../PREREGISTRATION_addendum.md`, `../report/summary_A.md`):
  all nine of its tests against the best baseline are supported, and the cycle costs no throughput and 2.2-3.7 % of mean
  latency (`../FINDINGS.md`, question 9).

---

## F1. The design

### What the frozen configuration asks of an interposer router
1. **Relation** (late entry binding without path adaptivity). A head carries a 4-bit mask of entry candidates: the functional
   VLs of the destination chiplet that are still allowed. Candidate s sits at a fixed place of that chiplet (slots N (1,0),
   E (3,1), S (2,3), W (0,2)), so its position follows from the destination coordinates. Under one dimension order a
   candidate has at most one minimal legal move at a router (XY: X first; no U-turn; no X move after a Y move). The offered
   outputs are the moves of the candidates in the mask, and the Up link if the VL of a candidate is at this router; the mask
   after an output keeps the candidates that move through it. With the VN-split order the order is XY in VN0 and YX in VN1
   (the VN is the VC, so no header bit selects it).
2. **Selection** (heuristic with W 2, B 0, G 1, one-hop lookahead, default-VL penalty D). Because every candidate has one
   move, the cost is computed per candidate and not per output:
   `C(s) = T(s) + 2 (f(o_s) + g(o_s, z_s)) + D [o_s drops the default VL from the mask]`,
   with T(s) the hops left through s (interposer hops, the Up link, chiplet hops from the VL to the destination), o_s the
   move towards s, f the flits in the downstream buffer of o_s on the packet's VC, z_s the move s takes at the router behind
   o_s and g the flits in the buffer behind that output (the neighbour's report). The chosen output is the move of a candidate
   of least cost; ties between outputs are broken by a rotating priority. This is the simulator's
   `w f + 1 + bestContinuation + lutBias` per output, rearranged (the vectors compare the costs themselves).
3. **Lookahead routing with the fallback.** The decision is taken before the head reaches the buffer front and is stored;
   at the front the head asks for the stored output if its VC there is free and has room, else for the first other offered
   output that is, else for the stored one.

### Structure (`router25_top.v`)
* **Decision unit** (`lb25_dec`), four stages: A relation and static terms (candidate positions, moves, T, the neighbour's
  move), M the occupancies each candidate meets, B the candidate costs, C comparison and tie break. A register can be placed
  after A, M and B (parameters), so a decision takes L_dec = 1 + (number of cuts) cycles. The occupancies are read in stage M.
* **LF.** One decision unit per input port that can bring a head with a choice. The unit reads the head **on the link**; its
  result goes into a store of two entries per input VC (packets have at least two flits, a buffer holds four). At the buffer
  front the route stage evaluates the relation only (the offered outputs of every head, into a 5-bit register); in the
  VC-allocation stage the head asks for its only output or, through the fallback, for the stored one, every cycle until the
  allocator grants it. A head whose decision is not stored yet waits there. The VC allocation and everything behind it are
  the reference core's; on the interposer the output VC is the input VC (the VN is kept).
* **With XY the N and S input ports have no decision unit.** A head that arrives from N or S has one candidate left (a
  chiplet has one VL per column). The units are on E, W and the Down link: two per router, three under a VL. With the
  VN-split order every link port has one (four, or five under a VL).
* **DLY.** The decision unit sits at the buffer front, one per input port (form P) or one per router behind a round-robin
  over the input VCs (form S). A hop with one offered output is routed in the route cycle; a head with a choice waits for the
  decision, L_dec - 1 cycles more.
* **LF has no form S.** Heads arrive on several links in the same cycle and each decision has to be ready when its head
  reaches the VC allocation; one shared unit would need a queue and loses the two cycles the mechanism lives on.
* **No sideband request.** Round 23 assumed that the upstream router sends a pre-route request and that the downstream router
  answers. This RTL needs neither: nothing travels in the head and no wire is added between routers for the decision. The
  price is in F4: the decision has two cycles, not the three of W = pipe_all + 1.

### State and wires DeFT's router does not have (interposer router of the main row)
| what | size |
|---|---|
| stored decisions | per decision port: 4 entries x 3 bits, 4 valid bits, 4 pointer bits |
| offered outputs of the head at the front | 5 bits per input VC |
| pipeline register of a decision unit (cut after M) | 71 bits per unit |
| neighbours' occupancy reports, registered on arrival | only the (output, neighbour output, VC) triples the relation can ask for: 24 x 3 bits, 28 x 3 under a VL (round 18 kept 32 and 42 triples) |
| report wires | 24 bits per X link, 12 per Y link, 12 from the boundary router above |
| tie break | a 3-bit LFSR per router |

Flip-flops: 1,795 -> 2,125-2,133 (interposer router), 2,184 -> 2,640-2,652 (with a VL); `breakdown_runs.csv`.

### Header bits
| field | DeFT | this design |
|---|---|---|
| destination (footprint x, y) | 6 (2x2), 8 (3x3, 4x4) | the same |
| exit VL | 2, from DeFT's table | 2, from the exit LUT |
| entry | 2: the entry VL, bound at the source | 4: the mask of entry candidates, pruned on the way |
| default entry VL (for the penalty D) | - | 2, on 2x2 only (D = 2); not present where D = 0 |
| stored decision | - | none: the decision is stored in the router, not in the head |
| VN | the VC | the VC |

**Two bits more than DeFT (four on 2x2).** All three designs (LF with XY, LF with the VN-split order, DLY) have the same
header. The simulator's lookahead carries the output in the head (`Flit::deft_lookahead_out`); in hardware that would be 3
bits and a valid bit, which this design does not need. As in round 18 the fields stay within the 32-bit flit (type 2,
destination 8, exit field 4, entry field 4, default VL 2) and the payload bits they take are not charged.

### Chiplet routers
The design does not route differently in the chiplets: XY to the exit VL of the LUT, DeFT's VN rules. The chiplet router is
the one of rounds 18 and 21 (DeFT's router with the exit LUT of (C - 1) x 2 bits and the fault table the NI fills the mask
from); the mask and the default VL pass through as header bits. On 2x2, where D = 2, the NI also needs the default entry VL
per destination: a table of 16 (C - 1) x 2 = 96 bits (`chip25_top.v`), in flip-flops like every table of round 18.

---

## F2. Does the RTL compute what the simulator computes?

**Vectors from simulator runs.** An instrumented copy of the simulator (`tb/patch_vecdump.py`: five anchored edits of a copy
of the sources, `src/` untouched) writes one line per evaluation: every decision computed ahead for the next router or at
the buffer front, every stored decision of a hop with one offered output, and every evaluation of
`Router::selectionFunction` (relation, the only output, the fallback with the free outputs it saw). 12 runs per design at
pipe_all 2 (uniform at 1.0 and 1.4 x Lsat, chipperm, uniform with one faulty VL per chiplet; three sizes; seed 1). **Every
instrumented run gives a statistics file byte-identical to `bin/noxim`'s.**

Checked per selection vector, with each of the eight cut configurations: the offered outputs, the pruned mask of every
offered output, the cost of every offered output, and the choice (the simulator's choice is given to the unit as the pointer
of its rotating priority, so the unit returns it exactly when it is an output of least cost; then the pointer is swept over
its five positions and the unit must return the first output of least cost at or after it). Checked per front vector: the
offered outputs, the pruned masks, the only output, and the output finally requested through the fallback.

| design | runs with statistics identical to `bin/noxim` | decisions | of them with a choice | evaluations at the buffer front | fallback evaluated / took another output | vectors | mismatches |
|---|---|---|---|---|---|---|---|
| LF, XY | 12 of 12 | 1,870,613 | 564,929 | 4,250,603 | 289,389 / 23,435 | **6,121,216** | **0** |
| LF, VN-split order | 12 of 12 | 1,861,048 | 563,170 | 4,346,446 | 291,963 / 23,352 | **6,207,494** | **0** |
| DLY, XY | 12 of 12 | 761,561 | 761,561 | 4,205,674 | - | **4,967,235** | **0** |

The decisions were applied with the eight register configurations (15.0 M, 14.9 M and 6.1 M applications) and the pointer
sweep made 251 M, 250 M and 97 M further checks. A sample of 2,000 lines of every vector file kept also runs through an
Icarus test bench of the same units (`tb/tb25.v`): 0 mismatches. In the XY designs no decision with a choice follows a move
north or south (0 of 564,929 and 0 of 761,561): those are the two ports without a decision unit. Details per run:
`functional_check.txt`.

**Can the check fail?** `mutation_check.txt`: 25 single-line mutations of the RTL (a wrong dimension order, missing pruning,
a missing hop in the path total, the wrong VC of an occupancy, the weight, the penalty, the comparison, the tie break and its
wrap-around, the fallback's free test, its order and its offered test). The checker is rebuilt from the mutated copy and run
on the vectors kept from one simulator run. **23 of 25 are caught.** The first version of the checker caught 21 of 24: it
never moved the tie-break pointer away from the simulator's choice, so a tie break that does not wrap around passed; the
pointer sweep was added for that and all vectors were checked again. The two mutations that still pass change logic that no
input of the network exercises:
* *An X move after a Y move is allowed* (the guard `!ly` of the XY moves). After a move north or south the mask holds only
  candidates of this column: the turn pruned the others, and a chiplet has one VL per column. No remaining candidate asks for
  an X move, so the guard never decides (none of the 253,834 kept decisions differs). It protects against an inconsistent
  header only.
* *The fallback tries N before the Up link.* The order between the two matters only if both are alternatives to a third,
  stored, output. With XY the Up link and N are never offered together (both candidates would be in one column). With the
  VN-split order they can be, but then they are the only two offered outputs: S would be a U-turn, and E or W would need a
  second candidate in this row, and a chiplet has one VL per row.

**Router level** (`router_smoke.txt`): each of the 140 router configurations (three designs, forms, eight cut
configurations, two sizes, with and without the Up link, and the relation alone) under random packets, random reports and
randomly delayed credits: every flit that enters leaves, packets stay contiguous per output VC, every head leaves through an
output the relation offers, on its VC, with the mask the relation gives. 140 of 140 pass. This test found the control error
of the first RTL (a head that arrived in the cycle in which the previous user of its store entry left lost its valid bit and
was never served); the second case of that kind, a decision that arrives after a head with one output has already left, is
exercised by the same test in the configurations with cuts.

**Cycles** (`latency_check.txt`): F4.

---

## F3. Area
`../report/summary_F.md` has the full tables. NanGate45 typical, 1 GHz target, three syntheses of every design:
**hierarchy kept** (every unit on its own: the primary figure, as in round 18, and an upper bound for this design, whose
relation units per input VC share nothing), **core kept** (the router core is one module, everything around it is flattened:
logic is shared within the routing and selection logic but not across the core's ports) and **flattened** (which also removes
the Local output port of the interposer router from the designs of this round, because their relation never requests it,
and not from DeFT's RTL: 122-150 flip-flops disappear from the main row's router, 10-12 from DeFT's; this figure favours the
design and is given for completeness).

Relative to DeFT, as hierarchy kept / core kept / flattened (the interposer routers of 4x4; those of 2x2 are in `../report/summary_F.md`):

| design | interposer router | interposer router under a VL | system, 2x2 | system, 4x4 |
|---|---|---|---|---|
| round 18, LB-I heuristic, one unit per router | 1.33 / 1.22 / 1.20 | 1.28 / 1.20 / 1.20 | 1.16 / 1.11 / 1.09 | 1.16 / 1.11 / 1.11 |
| round 18, LB-I heuristic, one unit per input port | 2.44 / 1.68 / 1.70 | 2.46 / 1.75 / 1.76 | 1.74 / 1.32 / 1.33 | 1.71 / 1.35 / 1.36 |
| round 21, fast selection, per router / per input port (its own table, hierarchy kept) | 1.30 / 2.02 | 1.25 / 1.98 | - | - |
| **LF, XY (main row), one cut: what T_ref needs** | **1.41 / 1.23 / 1.12** | **1.48 / 1.31 / 1.20** | **1.25 / 1.16 / 1.10** | **1.22 / 1.13 / 1.08** |
| LF, XY, two cuts (what 1 ns would need) | 1.44 / 1.26 / 1.15 | 1.51 / 1.35 / 1.25 | 1.26 / 1.18 / 1.12 | 1.23 / 1.15 / 1.10 |
| LF, VN-split order, one cut | 1.66 / 1.40 / 1.32 | 1.70 / 1.46 / 1.38 | 1.38 / 1.24 / 1.20 | 1.34 / 1.21 / 1.17 |
| DLY, XY, per input port, two cuts (the evaluated delay) | 1.33 / 1.22 / 1.17 | 1.40 / 1.29 / 1.26 | 1.21 / 1.16 / 1.13 | 1.18 / 1.13 / 1.10 |
| DLY, XY, per router, two cuts (does not fit T_ref) | 1.18 / 1.15 / 1.15 | 1.16 / 1.14 / 1.14 | 1.12 / 1.11 / 1.10 | 1.09 / 1.08 / 1.08 |
| the relation alone (LF structure, no decision unit) | 1.14 / 1.05 / 0.93 | 1.13 / 1.06 / 0.94 | - | - |

* Chiplet routers of this design relative to DeFT's: 1.010-1.016 on 3x3 and 4x4 (the exit LUT), 1.051-1.062 on 2x2 (the exit
  LUT and the 96-bit table of the default entry VL). System = 12 chiplet, 4 boundary, 12 interposer and 4 interposer routers
  under a VL per chiplet.
* All routers of a system, hierarchy kept: 2x2 (128 routers) 2.35 mm^2 for DeFT and 2.94 mm^2 for the main row; 4x4 (512
  routers) 9.54 and 11.63 mm^2.
* The main row's router is larger than round 18's heuristic with one unit per router (1.22 against 1.16 at system level,
  hierarchy kept; 1.13 against 1.11 with the core kept) and much smaller than its per-port form (1.71), which is the form
  that mechanism LF needs. Against round 18's per-port router it saves the units on the N and S ports and the per-output
  cost logic.
* Round 21's numbers are from its own table (not synthesised again; its parser had the gap described below).

Where the area of the main row's interposer router goes (4x4, under a VL, hierarchy kept, cut after M; DeFT 21,318 um^2,
this router 31,503): decision units and reports 6,015 (three units), relation 2,563 against DeFT's 251 (one relation per
input VC at the front, plus one in every decision unit), stored decisions and glue 1,481, input-VC control +279, header
update in the crossbar +222, fallback 179. Buffers (13,106) are unchanged.

**Correction of round 18's accounting.** Its area parser counted sub-modules without parameters as cells of no area: the
`xy_dir` unit inside the route units of DeFT, MTR, RC and the reference (about 190 um^2, 0.9 % of an interposer router). The
late-binding routers had no such sub-module, so round 18's ratios to DeFT were about 1 % too high (LB-I heuristic 1.167 ->
1.161 on 4x4). This round's totals are checked against the synthesis tool's own design area on all 344 netlists.

---

## F4. Timing
OpenSTA on the flattened netlists, ideal clock, no wires. Stage time = arrival + setup. **T_ref** = the longest stage of the
DeFT router of the same type and size in the same run: 1.27-1.32 ns, its switch allocation and crossbar (the route stage
takes 0.86-0.97 ns, the VC allocation 1.20-1.26 ns). No router of this flow meets the 1 ns target: the "1 ns" column asks
what the decision alone would need. The spread of the flow on unchanged logic is 0.13 ns (chiplet routers of DeFT against
the same routers with the tables of this round); a margin below it is called marginal. A stage that starts on a link gets
0.11 ns added for the clock-to-output delay of the upstream output register.

| design | cuts that fit T_ref (fewest) | L_dec, N_fast | margin | at 1 ns |
|---|---|---|---|---|
| LF, XY (main row) | one, after M | 2, 1 | +0.23 ns | 3 cycles (cuts after A and B), +0.07 ns: marginal |
| LF, VN-split order | one, after M | 2, 1 | +0.18 ns | 3 cycles, +0.05 ns: marginal |
| DLY, XY, per input port | one, after M | 2, 1 | +0.00 ns: marginal (two cuts: +0.06, also marginal) | does not fit: the first stage (buffer front, arbitration, relation) is 1.19-1.27 ns |
| DLY, XY, per router | none | - | 0.28 ns over with three cuts | does not fit |

* **The decision path of the main row.** Without a register the decision needs 1.80 ns from the link. With the register
  after M: first stage (head on the link, relation, static terms, occupancies) 1.04 ns including the 0.11, second stage
  (costs, comparison, tie break, store) 1.09 ns. With registers after A and B: 0.93 / 0.89 / 0.81 ns.
* **The route computation of a hop with one offered output.** LF: the relation into the offered-output register takes
  0.66-0.73 ns (DeFT's route stage: 0.86-0.97 ns); the VC allocation then asks for the only output. DLY, per port: the
  relation into the route registers 0.99-1.12 ns (relation only) and 1.11-1.31 ns with the decision unit beside it; per
  router 1.27-1.56 ns.
* **The pre-route path** of lookahead routing is the first stage above: it starts on the link. The link cycle of DeFT's
  router holds the buffer write only (0.41-0.45 ns with the 0.11), which leaves 0.82-0.90 ns for the wire. With the decision
  of the main row 0.28-0.42 ns are left (VN-split order: 0.18-0.37 ns). This is the cost of having no sideband request, and it
  is the first condition of F5.
* **The fallback** sits in the VC-allocation stage (stored decision, free outputs, the request, the allocator, the route
  registers written at the grant): 1.08-1.20 ns, against 1.20-1.26 ns for DeFT's VC allocation. The bookkeeping of the
  stored decisions ends behind the switch allocation (a head leaves): 1.08-1.15 ns.
* **The whole router.** The longest stage of the main row's router is 0.90-0.96 x T_ref: the design does not lengthen the
  clock period. (It is not faster either: the flattened netlist of this design has lost the Local output port, see F3, and
  the allocation stages vary by about 0.1 ns between netlists.) DLY per router lengthens it by 3-22 %.

**Cycles, measured in RTL simulation** (`latency_check.txt`; a two-flit packet into an idle router, link to link, 140
configurations): a head with one offered output takes 4 cycles in every design (link and buffer write, route, VC allocation,
switch allocation and crossbar: the reference pipeline). A head with a choice takes 4 cycles in LF with at most one cut and
one more per further cut (residual = max(0, L_dec - 2)), and 4 + cuts in DLY (decision_delay = L_dec - 1).

**N_fast of this design.** At T_ref: L_dec = 2, so N_fast = 1 for LF with either order and for DLY per port (marginal). Round
24 assumed N_fast = 2 for the heuristic (the value round 21 measured for its fast selection at 1 ns); at 1 ns this design
needs the same.

---

## F5. Conclusion
**With W = pipe_all + 1 = 3 cycles per hop, can LF be built with residual delay 0?**

* The simulator's window counts three cycles between the forwarding of the head by the upstream router and its reservation
  at this router. In hardware the third of them, the switch-traversal cycle of the upstream router, can only be used if that
  router announces the head on sideband wires. This RTL has none, so **the decision has two cycles: the link cycle and the
  route cycle**, and the residual is max(0, L_dec - 2).
* **At the clock period of the reference pipeline the decision takes two cycles: residual 0.** One register (after the
  occupancy stage), +0.23 ns of margin for the main row and +0.18 ns for the VN-split order, no stage of the router longer
  than DeFT's, four cycles per hop for every head in RTL simulation. **`CI_heurLA_X_LF` as evaluated in Part B is the
  mechanism that is built**, and `CI_heurLA_O_LF` likewise.
* **Two conditions.** (1) The first stage reads the head on the link and leaves 0.28-0.42 ns of that cycle to the wire
  (DeFT: 0.82-0.90 ns). An interposer link that needs more forces the decision to start from a register: one cycle later.
  (2) At a 1 ns clock the decision needs three cycles (and the reference router itself does not reach 1 ns). In both cases
  **the same RTL has one residual cycle** for heads with a choice: LF with residual 1, which was not one of the frozen rows.
  It was pre-registered and run on the Part B design (`CI_heurLA_X_LF1`, `../PREREGISTRATION_addendum.md`). Result
  (`../report/summary_A.md`): 9 of 9 tests against the best baseline supported (THR +1.5 / +6.7 / +6.5 %, LAT -11.1 / -8.5 /
  -13.2 %, P99 -27.4 / -27.3 / -33.3 % on 2x2 / 3x3 / 4x4); against the main row THR unchanged and LAT +2.2 to +3.7 %,
  one cycle per hop with a choice.
* **A request from the upstream router** would give the third cycle back: 15 bits (destination, mask, default VL, VN) and a
  valid bit per link, sent when the upstream VC allocation has granted the output, and registered at this router. The
  decision would then start from a register one cycle before the head is on the link, and residual 0 would not depend on the
  link wire. Not built; it costs about 16 wires and flip-flops per link and no further logic.
* **DLY** can be built per input port with a decision_delay of 1 at T_ref, without timing margin, and 2 with +0.06 ns; the
  evaluated row has 2. Its route stage is the longest of the design (the head has to pass an arbiter between the two VCs of
  the port before the relation). With one unit per router it does not fit the reference period at all (0.28 ns over with
  three cuts, 5-22 % longer clock). DLY is the mechanism to fall back on only where the link cycle cannot be used at all and
  one residual cycle of LF is not acceptable; LF with residual 1 is the cheaper answer to both conditions.

---

## What the RTL and the flow do not cover
* **Wires and layout.** Pre-layout, ideal clock, no wire delay: every stage time is optimistic, the reference's too. The one
  place where this decides a conclusion, the link cycle, is stated above.
* **The Q-learning row** (`CI_qlLA_X_LF`) is not built.
* **The network.** The check is per unit on vectors from simulator runs, per router under random traffic, and per router in
  cycles; no network of RTL routers is simulated.
* **Moment of the state read.** The simulator evaluates the decision at the moment the upstream router forwards the head; the
  RTL reads the occupancies one to two cycles later (stage M). The function is the same and is what the vectors check; the
  hardware's information is fresher, which the simulation does not credit.
* **Neighbour reports** are registered on arrival (one cycle old), as in round 18; the simulator reads them in the same
  cycle.
* **Tie break.** A 3-bit LFSR and a rotating priority instead of the simulator's random draw: the unit returns an output of
  least cost for every pointer value, but the sequence of choices among equal outputs is not the simulator's.
* **Two entries per VC** in the store rely on packets of at least two flits in a four-flit buffer (8 flits in the
  evaluation, 2 and 18 in the traces). Single-flit packets would need four.
* **Tables are flip-flops** (the exit LUT and the default-VL table), as in round 18: it pushes every ratio towards 1 less
  than SRAM would, and it is what makes the 2x2 chiplet router 5-6 % larger.
* **Chiplet routers** are taken from round 18 and synthesised, not checked again.
