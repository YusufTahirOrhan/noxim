# v20 decisions (Part L)

## Checks added to the pre-registered ones
* **N = 0 against K5 (`n0_check.md`):** the three variants on every size, with the options given explicitly, whole stats files against the K5 runs. Added because the pre-registered regression gives `decision_delay 0` without the round-robin. It runs before the K5 raw outputs are deleted.
* **Low-load check (`delay_sanity.md`):** at very low load, latency must rise by N x (multi-output hops per packet). This shows the delay acts as defined, which the drain tests do not. Seed 1001 is not an evaluation seed. It is not a gate: a large difference is reported, not a reason to stop.

## L3: terms computed in the previous cycle (timing only)
**Files:** `rtl_pre/` holds copies of `lb_units.v` and `router_top.v` of v18 with a parameter `PRE`; the other RTL files are v18's. Flow: `experiments_v20.py pre`, the v18 yosys and OpenSTA steps, flattened, form S, the 18 designs of the v18 pipeline experiment. Data: `pre_runs.csv`.

**Two forms were run, because the design in the prompt does not keep the simulated function:**
* `PRE = 1`, same function apart from occupancy one cycle old: w f + beta b per output and VC, and w occ per output, neighbour output and VC, are registered.
* `PRE = 2`, the design in the prompt: also the lookahead minimum per output and VC, and the path totals per candidate and destination chiplet.

**What makes `PRE = 2` a different selection function.** In the simulator and in v18's RTL, the lookahead term is the minimum over the neighbour's outputs z of (best total among the candidates still reachable through z + w occ(z)). The occupancy and the candidates are coupled through the packet's legal moves, so the minimum cannot be taken before the packet is known. `PRE = 2` splits it into (minimum total over the candidates reachable through any z) + (minimum of w occ over all z). It can pick a different output, so **no simulated latency in this project applies to it, and the L2 results describe the delay of the simulated function, not of this function.** The totals also stop at the destination chiplet: the distance from the entry VL to the destination node is dropped.

**Conservative choices:**
* Moves, masks, the minimum over candidates, the Q-table read and the final comparison stay in the decision cycle.
* In the destination and intra-chiplet phases, the distance to the destination stays in the decision cycle.
* The tables ignore the entry mask of the packet (static with the fault mask), and the arbitration over the input VCs stays on the path (form S), as in v18.

**Cycles:** ceil(arrival + setup), no register overhead, so a lower bound on what a pipelined version needs, as in v18.

**Flow noise:** the `PRE = 0` runs differ from v18's for the same logic by 0.06 ns (LB-I heuristic, 2x2) and 0.18 ns (LB-F Q-learning, 4x4 interposer), so differences of this size mean nothing.

**Time:** 12 minutes of synthesis at low priority beside K5; well inside the 2 h limit of the prompt.
