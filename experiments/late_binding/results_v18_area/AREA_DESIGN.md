# v18 design note: area and timing with open synthesis tools (Part J)

Written before any RTL. Later corrections go into `DECISIONS.md`; this note stays as written, apart from the tool versions, which are
filled in by the flow (`tools.md`).

## 1. Tools (one library, one flow, for everything)
* **Synthesis:** Yosys with its bundled ABC (OSS CAD Suite build, no root needed, under `~/eda/oss-cad-suite`).
* **Library:** NanGate45 Open Cell Library, typical corner, `NangateOpenCellLibrary_typical.lib` from OpenROAD-flow-scripts
  `flow/platforms/nangate45/lib/`. The fallback sky130_fd_sc_hd (tt) is used only if NanGate45 does not work in the flow.
* **Timing:** OpenSTA if it can be built without root; otherwise ABC's `stime`. All numbers are pre-layout: no placement and no wire
  parasitics. Interposer links are long in a real layout, so link-crossing signals are the optimistic part of these figures.
* **Simulation of the RTL:** Icarus Verilog (and Verilator if Icarus is too slow).
* **Optional cross-check:** DSENT, if it builds within about 1 h; otherwise skipped and recorded.

## 2. What is compared
A minimal reference wormhole router in synthesizable Verilog, plus each method's routing and selection logic. All areas are
ratios within this flow, so that one set of assumptions applies to all methods.

**Reference router (all methods share it):**
* 2 VCs per input port, 4-flit buffers of 32-bit flits, **flip-flops** (`ibuf`). Flip-flop buffers overstate buffer area against
  SRAM; this is applied equally to all methods and pushes every ratio towards 1, and it is recorded in the report.
* Credit counters per output VC (`credit_ctrs`).
* Separable round-robin allocators: VC allocator with one arbiter per output VC (`vc_alloc`) and an input-first switch allocator
  (`sw_alloc`), with per-input-VC state (`ivc_ctrl`).
* Crossbar with output registers (`xbar`).
* XY routing unit per input port.
* Clock target 1 GHz.

**Pipeline assumed:** buffer write, route (routing + selection, registered per input VC), VC and switch allocation, crossbar and output
register. Routing + selection is one stage of its own, so its timing is read against the whole cycle. Noxim has no router pipeline, so
this pipeline is not what was simulated; recorded as a limit.

**Router types:**
| type | ports | used for |
|---|---|---|
| `chip5` | N, E, S, W, Local | chiplet router without a VL |
| `chip6` | + Hub | boundary router |
| `ipos5` | N, E, S, W, Local | interposer router without a VL |
| `ipos6` | + Hub | interposer router with a VL |

Router positions are input straps, not constants, so no position-specific logic is optimised away (the conservative choice for all
methods; it affects the LB units most).

Sizes: C = 4, 9, 16 chiplets of 4x4 routers. Footprint coordinates need 3, 4 and 4 bits. Router counts per size: 12C `chip5`, 4C `chip6`,
12C `ipos5`, 4C `ipos6`.

## 3. Method-specific units (all parameterized by C; tables are flip-flops with a configuration write port)
* **DeFT:**
  - Table in the NI of each chiplet router: (C-1) x (2 + 2) bits, one fault scenario. Variant `DeFT14`: all 14 scenarios plus a scenario
    register, as the DeFT paper describes.
  - VN assignment as `DeftVirtualNetwork`: source VN (round-robin bit in the NI), Up link and destination chiplet to VN1.
  - R1-R3 checks per input port.
  - XY to the exit / entry VL.
* **MTR:** NI table of 16C entries x 2 bits, exit entry (2 bits), 8 turn-enable bits at boundary routers, XY, no VNs (VC toggled at
  injection).
* **RC:**
  - RC buffer at boundary routers: 4 packets x 8 flits x 32 bits, flip-flops, on one write bus from the crossbar's Hub output (the cheapest
    form; the simulator lets slots fill in parallel).
  - OPIC: per node, request and permit counters of 3 bits each and the request/response logic. Per boundary router, the used-slot counter,
    a pending bit per chiplet node, and a round-robin grant.
  - Nearest VL as a fixed function of the local position (RC has no fault tolerance, so no table and no comparators).
* **DeFT-Dis:** DeFT's VN logic and XY, with the nearest-VL comparator logic in the NI instead of the table, and a fault table of 4C bits
  that the comparators need.
* **LB-I (CI\_\*):**
  - Chiplet routers: exit LUT of (C-1) x 2 bits, the fault table of 4C bits (the NI fills the entry mask from it), XY, VN logic.
  - Interposer routers, routing: 4-bit entry mask, `moves_T` for up to 4 candidates under odd-even with the reachability check, mask pruning
    after a move, VL-at-router check.
  - Interposer routers, selection: Eq. (1) with gamma = 2, w f + beta b + H_gamma, per offered output, with the lookahead term from the
    neighbour's reported occupancies, and a comparator tree.
  - Q-learning variant: table of 5C entries x 16 bits (one bank per output), one read port per output, the Eq. (2) update datapath per
    bank, and the feedback path. Boundary routers get a small feedback generator, since the interposer's update needs the value at the next
    router; they get no table.
* **LB-F (FULL\_\*):** the same routing, selection and Q-learning logic on every router, chiplet and interposer, with two masks and no LUT.
  The NI needs only the fault table.

Frozen parameters are those of `experiments_v10.methods`:
| size | LB-I w, beta, alpha | LB-F w, beta, alpha | Q format (bits, fractional) |
|---|---|---|---|
| 2x2 | 1, 4, 0.05 | 2, 0, 0.01 | 16, 10 |
| 3x3 | 2, 0, 0.1 | 2, 0, 0.02 | 16, 8 |
| 4x4 | 2, 0, 0.1 | 1, 4, 0.05 | 16, 8 |

The learning rate is shift-add, 2^-a + 2^-b, hard-wired per size: 0.1 -> 1/16 + 1/32, 0.05 -> 1/32 + 1/64, 0.02 -> 1/64 + 1/256,
0.01 -> 1/128 + 1/512. The approximation is not simulated.

## 4. One routing + selection unit per router, or one per input port
The simulator decides every head at every input VC in every cycle. In hardware this logic is much larger than XY, and the specification's
"a read port per output" of the Q table describes one decision at a time per router. Both forms are synthesized and reported:
* **S (shared):** one routing + selection unit per router, with a round-robin arbiter over the input VCs that have a head to route. This is
  the form that matches the specification. A head may wait for the unit; that wait is not simulated.
* **P (per port):** one unit per input port, with its own Q-table read ports. No such wait across ports, but much more area. This is the
  conservative upper bound.

The baselines keep their cheap routing unit per input port.

## 5. Selection logic: what is shared
* The candidates' remaining-path totals T are computed once per candidate. A minimal move lowers the distance to every candidate that
  survives pruning by exactly 1, so H_gamma after a move and at the neighbour both follow from T, with no extra adders per output.
* The neighbour's offered moves are derived from per-candidate flags (sign and small magnitude of the coordinate differences), not from new
  subtractors.
* No other manual optimisation: the units are a straightforward upper bound, and the min trees are not shared.

## 6. Other hardware the simulator does not have to model
* **Occupancy reports:** a neighbour's occupancies are 4 outputs x 2 VCs x 3 bits per link direction, registered on arrival (24 flip-flops per
  input link). The simulator reads the same-cycle values; the one-cycle staleness is not simulated. Registering is the conservative choice.
* **Learning feedback:** the head carries a 7-bit static estimate and a valid bit. The next router returns the goal and the key on a reverse
  sideband, registered on arrival (per link direction).
* **Head fields:** masks and static estimate stay within the 32-bit flit and reduce the payload bits. That loss is not charged here.

## 7. Functional check before synthesis (J2)
Vectors come from the C++ itself: a small harness (`rtl/tb/export_vectors.cpp`) includes `DeftLateBinding.cpp` and calls `legalMoves`,
`nextMasks`, `learnerCost`, `bestContinuation`, `remoteStatic` and the update in `onHeadAtFront` directly, on real `Router` objects.
* **Routing:** every reachable input (breadth-first search from all injection states and all non-empty fault masks), one 4x4 chiplet and
  the 8x8 interposer.
* **Selection and Q update:** random vectors, in the fixed-point format, with alpha set to the exact shift-add value in the C++ run.
Any mismatch is fixed before synthesis.

## 8. Reports
Per router type, method and C: area in um^2, cell count, shares (buffers, crossbar, allocators, routing unit, selection, tables), critical
path of routing + selection against 1 ns, the system-level average weighted by router counts, and the comparison with the DeFT paper's
ratios (DeFT/MTR 1.016, RC boundary/MTR 1.133). See `FINDINGS.md`.
