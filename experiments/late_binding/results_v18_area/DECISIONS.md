# v18 decisions (Part J: area and timing)

The design is in `AREA_DESIGN.md`, written before the RTL. This file records what was decided or changed afterwards, and the choices left open by the prompt.
The conservative option is the one that does not favour LB-I and LB-F.

## Tools
* Yosys, ABC, Icarus Verilog: OSS CAD Suite, without root. OpenSTA 3.1.0 built from source with user-local dependencies (it could be installed, so ABC's delay
  report is not used). Versions and the library's md5: `tools.md`.
* Sky130 fallback: not needed.
* DSENT cross-check: built within the hour (from gem5's `ext/dsent`), see `dsent_check.txt` and `FINDINGS.md`. ORION was not tried.

## Flow
* **Area:** hierarchy kept, so that the shares per block can be read. `abc -D 1000` runs on each module on its own. One module cannot see the delay budget of another; a module that
  cannot reach 1 ns on its own is mapped for speed anyway, which inflates the selection's area for the Q-learning and heuristic units.
* **Timing:** the same designs flattened, then OpenSTA, ideal clock, no wires, typical corner. ABC is run with its default script; no retiming.
* **Arithmetic:** Yosys's default carry logic. A trial with Kogge-Stone carry logic (`synth -extra-map +/choices/kogge-stone.v`) on the reference router and the largest LB router
  changed the route-stage slack by about 0.1 ns and did not change the conclusions, so it is not used.
* **Reference router's own timing:** its worst path, switch allocation to the credit counters, takes about 1.26 ns, with its route stage inside 1 ns. The allocators and crossbar are one stage here. A real design would
  split them; this cost is common to all methods and is not charged to any of them.

## Reference router
* Round-robin arbiters use two lowest-set-bit searches and a binary pointer. The first version (rotating index loop) was 15 % larger and slower.
* VC allocation has a single request per input VC, so the first arbitration stage is empty: one arbiter per output VC.
* The VC of a packet at the Local port comes from a toggle bit in all methods without VN rules (Noxim draws it uniformly). It is 1 flip-flop.
* PE-side flow control is not modelled in any method.

## Form S and form P (the open choice of how many units)
The prompt's "a read port per output" of the Q table describes one decision per router at a time, so **form S (one unit per router) is the form reported first**, and form P (one per input port,
so also one read port per output per input port) is reported as the conservative upper bound. The simulator decides at every input VC in every cycle, and neither form reproduces that. With form S, a head can wait
for the unit. Heads arrive at most once per 8 flits per port, so the unit's utilisation stays below 1, but this wait is not simulated.

## Choices that favour the baselines
* **MTR, RC, DeFT:** routing per input port, cheap units.
* **RC buffer:** one write bus from the crossbar's Hub output (the simulator lets slots fill in parallel). A bit per node and a round-robin arbiter instead of the simulator's FIFO of requests.
* **RC's nearest VL:** a fixed function of position, as RC has no fault tolerance.
* **LB units:** no position-specific optimisation (positions are straps). The arrival port is a run-time input of the unit in both forms.

## Choices that count against LB
* **5C-entry table on every router**, as specified, including the unused Hub bank on 5-port routers. Dropping it would save one fifth of the table.
* **An update datapath per bank** (5 per router), so that updates arrive and apply as in the simulator, with no arbitration or loss.
* **Occupancy reports registered on arrival:** 24 flip-flops per direction. In the simulator they are unregistered and current.
* **Fault table of 4C bits in each NI** for LB-I, LB-F and DeFT-Dis: the masks at injection need it. The prompt lists it for no method, but the simulator's `functionalMask` is this table. DeFT's LUT holds this information already.
* **VN logic on LB routers**, as they inherit DeFT's rules.
* **LB-I boundary routers:** a feedback generator in the Q-learning variant, with reports from 4 neighbours (96 flip-flops).

## Differences from the simulated methods (none of these is simulated)
* **Learning rate:** 2^-a + 2^-b as in `AREA_DESIGN.md`. The vectors use the same exact value in the C++, so the RTL is checked on the update itself.
* **Tie break:** rotating priority from a 3-bit LFSR, where the simulator draws uniformly from the ties. The vectors check that the choice is one of the ties.
* **LB-I chiplet routers have no table** (as specified), so the value they return to the interposer has a zero residual. In `CI_qlLA_G` the simulator also learns on chiplet routers.
* **Reports and feedback** are delayed by a register. The simulator uses same-cycle values and updates immediately.
* **Selection is taken as a stage, not as 0 cycles.** Noxim has no router pipeline; the latency of a multi-cycle selection is not in any v1-v16 result.
* **Q table reset:** an init counter writes zeros after reset, one address per cycle.
* **Head fields** stay in the 32-bit flit: 8 mask bits, 7 static bits and a valid bit reduce the payload on the head only.

## Functional check
* Vectors come from the simulator's code itself (`rtl/tb/export_vectors.cpp`, which includes `DeftLateBinding.cpp`). The "every reachable input" set is a breadth-first search from all injection states and all 15 non-empty masks.
* Destination positions on 3x3 and 4x4 are sampled for the selection vectors, since the number of reachable states grows (488 k on 4x4).
* `HAS_HUB = 0` units are checked on states at routers without a VL.
* The Q update is compared with `onHeadAtFront`. Its input goal is computed by the same formula as that function.
* **Mutation check:** single changes to the RTL must produce mismatches (`mutation_check.txt`), to show that the vectors can fail.
* **Router-level smoke test:** every method and router type, 2x2 and 4x4, random packets, all flits delivered, packets contiguous per output VC, no X on a valid output (`router_smoke.txt`). This does not check that a whole network works.
