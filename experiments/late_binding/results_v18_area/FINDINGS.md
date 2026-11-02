# v18 findings: area and timing with open synthesis tools (Part J)

**Sources:**
* Design: `AREA_DESIGN.md` (before the RTL). Decisions: `DECISIONS.md`. Tools and versions: `tools.md`.
* RTL: `rtl/`. Flow: `../synth_v18.py`, `../report_v18.py`.
* Tables: `report/summary.md`. Data: `area_runs.csv`, `breakdown_runs.csv`, `timing_runs.csv`, `pipe_runs.csv`, `relax_runs.csv`.

**Scope:** pre-layout, NanGate45 typical corner, no wires, flip-flops for all buffers and tables, 156 designs. The figures are ratios from one flow, not a layout result.

## Functional check (J2): passed before synthesis
* **Vectors:** 1,011,642 vectors from the simulator's own code, **0 mismatches** (`functional_check.txt`).
  - **Routing unit, every reachable input:** 65,024 on the 8x8 interposer and 18,856 on one 4x4 chiplet, and the subsets for routers without a VL.
  - **Random:** selection (20,000 per configuration, on 2x2, 3x3 and 4x4), Q update, boundary feedback. XY units, VN rules and the nearest-VL logic are checked as well.
  - The first run also had 0 mismatches, so no RTL fix was needed.
* **Can the vectors fail?** 13 of 15 single-line mutations of the RTL produce mismatches (`mutation_check.txt`). The other two turned out to be redundant logic on reachable inputs: "no W after E", and "not here" in the pruning.
* **Router level:** 104 of 104 router configurations deliver every flit in a smoke test (`router_smoke.txt`). This does not check a whole network.
* **What is not checked:** the timing-only cuts of section 3, and the behaviour of the units across cycles.

## 1. System-level router area (the number for the paper)
Average over all routers of a size, weighted by router type (12 chiplet, 4 boundary, 12 interposer, 4 interposer with a VL per chiplet), relative to DeFT.

| method | 2x2 | 3x3 | 4x4 | flat flow: 2x2 / 3x3 / 4x4 |
|---|---|---|---|---|
| Reference (XY, no VNs) | 0.986 | 0.979 | 0.973 | 0.967 / 0.958 / 0.952 |
| DeFT | 1.000 | 1.000 | 1.000 | 1.000 |
| DeFT, 14 fault scenarios | 1.039 | 1.099 | 1.184 | 1.039 / 1.099 / 1.187 |
| MTR | 1.029 | 1.063 | 1.109 | 1.005 / 1.034 / 1.084 |
| RC | 1.060 | 1.055 | 1.048 | 1.038 / 1.028 / 1.021 |
| DeFT-Dis | 1.004 | 1.005 | 1.006 | 1.003 / 1.005 / 1.005 |
| **LB-I heuristic** | **1.169** | **1.166** | **1.167** | 1.094 / 1.105 / 1.106 |
| **LB-I Q-learning** | **1.377** | **1.467** | **1.626** | 1.278 / 1.377 / 1.514 |
| **LB-F heuristic** | **1.390** | **1.388** | **1.390** | 1.233 / 1.251 / 1.251 |
| **LB-F Q-learning** | **1.774** | **1.980** | **2.300** | 1.582 / 1.786 / 2.065 |

* **Form S**, one routing + selection unit per router (`DECISIONS.md`). With one unit per input port (form P), the upper bound, the system ratios are LB-I heuristic 1.72-1.75, LB-I Q-learning 2.08-2.49, LB-F heuristic 2.70-2.72, LB-F Q-learning 3.36-4.25.
* **Which flow:** the bold columns are hierarchical, which gives the shares and is the larger estimate. The flat flow removes module boundaries and is lower by 6-11 % of DeFT for LB-I and by 14-24 % for LB-F. Relaxing the clock to 6 ns changes the ratios by at most 0.03, so the gap comes from the boundaries, not from timing pressure.
* **DeFT with stored scenarios:** a DeFT that stores all 14 scenarios, as its paper describes, costs 1.04-1.18. Storing them would raise LB-I too, whose exit LUT has half of DeFT's bits; LB-F has no LUT and would not change.

**Per router type, relative to DeFT, 2x2 / 4x4 (hierarchical, form S):**

| method | chiplet | boundary | interposer | interposer + VL |
|---|---|---|---|---|
| LB-I heuristic | 1.004 / 1.016 | 1.003 / 1.015 | 1.351 / 1.339 | 1.301 / 1.293 |
| LB-I Q-learning | 1.004 / 1.016 | 1.049 / 1.057 | 1.781 / 2.321 | 1.653 / 2.087 |
| LB-F heuristic | 1.433 / 1.429 | 1.411 / 1.406 | 1.368 / 1.370 | 1.317 / 1.322 |
| LB-F Q-learning | 1.838 / 2.363 | 1.739 / 2.173 | 1.776 / 2.357 | 1.648 / 2.134 |

Absolute areas (um^2), cell counts and the ratios to the reference router, for 3x3 too: `report/summary.md`.

## 2. What dominates the overhead
Added area against DeFT on one router, 2x2 / 4x4:

| | total added (um^2) | Q table | selection | Q update + feedback | routing unit | allocators, crossbar, other |
|---|---|---|---|---|---|---|
| LB-I heuristic, interposer | 5970 / 5769 | - | 84 % / 84 % | - | 5 % / 5 % | 11 % / 12 % |
| LB-I Q-learning, interposer | 13268 / 22488 | 23 % / **58 %** | 43 % / 24 % | 21 % / 10 % | 2 % / 1 % | 11 % / 7 % |
| LB-F heuristic, chiplet | 7513 / 7649 | 1 % / 2 % | 83 % / 83 % | - | 3 % / 3 % | 14 % / 13 % |
| LB-F Q-learning, chiplet | 14531 / 24318 | 21 % / **54 %** | 48 % / 28 % | 17 % / 10 % | 2 % / 1 % | 12 % / 7 % |

* **The routing relation is cheap.** Moves, masks and pruning for 4 candidates add 200-280 um^2, 1-5 % of the overhead. Late binding as such is not what costs area.
* **The heuristic's cost is the lookahead selection**, 4,800-7,500 um^2 and independent of C. Each output needs a min over the neighbour's outputs, each of those over up to 4 candidates. The units are written plainly with no shared min trees, so this is an upper bound.
* **The Q-learning cost is the table, and it grows with C.** It is 5C x 16 bits at about 10 um^2 per bit: flip-flop, write mux and read muxes. That is 3,000 um^2 on 2x2 and 13,000 um^2 on 4x4. The table has the area of about 1.2 x the input buffers on 4x4.
  - Since the prompt asks for flip-flops, this is the largest pessimism for LB. A register-file or latch array is the obvious saving, but it needs one read port per output plus one for the update.
  - Keeping 5C on 5-port routers counts a bank that is never used: 20 % of the table.
  - The 12-bit format left open by v16 would remove 25 % of it, but v16 could not show it equivalent.

## 3. Does routing + selection fit in one cycle at 1 GHz? **No.**
Longest path from the input-buffer flip-flops through arbitration and routing + selection into the route registers, ns. **Slack = 1 ns - arrival - setup.** Ranges over sizes and router types of each layer; form S.

| method | chiplet routers | interposer routers |
|---|---|---|
| Reference, DeFT, MTR, RC, DeFT-Dis | 0.82-1.11 (slack -0.15 to +0.14) | 0.77-1.00 (slack -0.03 to +0.20) |
| LB-I heuristic | 0.87-1.08 (like DeFT: XY) | **4.06-4.62** (slack -3.66 to -3.10) |
| LB-I Q-learning | 0.87-1.02 (like DeFT: XY) | **4.63-5.29** (slack -4.33 to -3.67) |
| LB-F heuristic | **4.83-5.49** (slack -4.53 to -3.87) | **4.14-4.73** (slack -3.77 to -3.18) |
| LB-F Q-learning | **5.51-6.46** (slack -5.50 to -4.55) | **4.85-5.54** (slack -4.58 to -3.89) |

Form P is 0.1-0.6 ns shorter, since the head mux is smaller: LB-I 3.77-5.11, LB-F 3.75-5.95.

**One added pipeline stage is not enough.** Registers placed inside the unit (a timing-only experiment, `report/summary.md`, `pipe_runs.csv`):

| stages | cuts | longest stage: heuristic | longest stage: Q-learning | area, same router, flat |
|---|---|---|---|---|
| 2 | route + totals + continuation / cost + tree | 2.66-3.53 ns | 2.81-3.72 ns | +0.3-1.4 % |
| 3 | route + totals / continuation / cost + tree | 2.07-2.34 ns | 2.47-2.82 ns | +4.7-8.3 % |
| 5 | route / totals / continuation / cost / tree | 1.94-2.10 ns | 2.27-2.58 ns | +6.7-14.3 % |

Stage by stage (ns, 5 stages): route 1.32-1.50, totals 0.52-1.74, continuation 1.94-2.35, cost 0.46-0.55 (heuristic) or 2.10-2.35 (Q-learning, with the table read), tree 1.82-2.58.

* **As written, the unit reaches about 400-500 MHz with 5 stages.** At 1 GHz it would need cuts inside the min trees and the comparator tree: 6-7 stages at least, from the total delay alone.
* **The routing relation alone is close to one cycle:** 0.96-1.03 ns in form P (4x4, Q-learning designs), about the baseline's route stage. In form S it is 1.32-1.50 ns, as the arbitration over all input VCs comes first.
* **Q update:** 1.77-2.32 ns (slack -1.35 to -0.81). It is off the head path, so two cycles with a hazard check are enough.
* **Other carry logic does not help:** Kogge-Stone changes the stages by about 0.1 ns (`ks_check.txt`).
* **Reference router:** the worst path of every design also misses 1 GHz. For the baselines it is switch allocation into the credit counters, about 1.2-1.4 ns (slack -0.18 to -0.37). A real design would split this stage. It is common to all methods, and it does not come from routing or selection.

**Consequence for the results of v1-v16:** Noxim charges no cycles for routing or selection. **All latency results for the late-binding methods assume a decision in zero extra cycles**, and this round shows that a plain implementation needs several per hop. It is likely less on a hop with only one offered output, where no selection is needed. How much of the latency gain survives is not known from this round. Selection could also work from costs computed ahead of time, but this is not designed or evaluated here.

## 4. Comparison with the DeFT paper (normalized to MTR)

| ratio | paper | ours: 2x2 | 3x3 | 4x4 | ours without MTR's NI table: 2x2 / 3x3 / 4x4 |
|---|---|---|---|---|---|
| DeFT / MTR, boundary | 1.016 | 0.940 | 0.893 | 0.835 | 1.006 / 1.015 / 1.027 |
| DeFT / MTR, chiplet | 1.016 | 0.946 | 0.887 | 0.818 | 1.010 / 1.021 / 1.036 |
| RC boundary / MTR boundary | 1.133 | 1.350 | 1.270 | 1.175 | 1.445 / 1.444 / 1.444 |
| RC non-boundary / MTR non-boundary | 1.017 | 0.938 | 0.870 | 0.791 | 1.002 / 1.001 / 1.002 |

**Two large differences, both from storing tables and buffers in flip-flops:**
* **DeFT below MTR.** The 16C x 2-bit NI table of MTR, at about 9 um^2 per bit, costs 1,200-4,900 um^2. Without it, DeFT / MTR is 1.006-1.036, around the paper's 1.016. The paper's figure implies a much cheaper table. How the paper stores it is not known to us.
* **RC boundary above the paper's 1.133.** The RC buffer is 1,024 bits of flip-flops, 9,400 um^2 on a 22,800 um^2 boundary router. The paper's 13.3 % would be about 3,000 um^2, a factor 3 denser. That is the order of an SRAM or a register file against flip-flop + write mux + read mux, but we cannot verify it. Ratios to MTR also fall with C here, because MTR's table grows and RC's buffer does not.

The other differences (library, flow, ORION's model) cannot be separated from this one.

## 5. Cross-check of the reference router
**DSENT 0.91 (Bulk45LVT, DFF buffers, 32-bit flits, 2 VCs x 4 flits, 1 GHz; `dsent_check.txt`):**
| | DSENT | this flow (hierarchical) | ratio |
|---|---|---|---|
| 5 ports | 15,703 um^2 | 16,916 um^2 | 0.93 |
| 6 ports | 19,763 um^2 | 21,052 um^2 | 0.94 |

The totals agree within 7 %, with different models and libraries. By part (5 ports, DSENT vs this flow): buffers 12,317 vs 10,922; crossbar 2,448 vs 2,642; allocation 894 vs 3,075. DSENT has no VC allocator or credit counters in that figure, which accounts for most of the difference in allocation. So the absolute scale of the reference router is plausible.

## 6. What this does not include
* **Wires, clock tree, placement.** Long interposer links would hurt the sideband reports most.
* **Sideband wires between routers:** occupancy reports (24 bits per direction) and feedback (24 bits per direction on 4x4) are counted here only as their receive registers.
* **The switching power of the added logic.** v12 counted events in the simulator; there is no power figure from this flow.
* **Functional check of the pipelined forms,** and any simulation of the added stages.

## Conclusion for the paper
* **Report:** LB-I with the heuristic adds 17 % router area on average over DeFT on all sizes (9-11 % flat), and LB-F with the heuristic 39 % (23-25 % flat). With Q-learning, the area grows with the chiplet count: LB-I 38-63 % (28-51 % flat), LB-F 77-130 % (58-107 % flat).
* **Compare fairly:** the baselines cost 0-11 %, or 4-18 % for DeFT with its 14 scenarios stored.
* **State the limit:** the selection does not fit one 1 GHz cycle, and a plain implementation needs several stages, while the simulated latencies assume none. **LB-I with the heuristic is the cheapest option that keeps run-time adaptivity**, and on area alone it is the one to prefer in hardware. Its performance relative to LB-I with Q-learning is in v9-v10.
