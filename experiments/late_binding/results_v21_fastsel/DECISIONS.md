# v21 decisions: DEFT_FAST

## The ROM index: the prompt's index is not exact, so it was widened
The prompt asks for H from a ROM indexed by (output, 4-bit candidate mask), exact, with the same value as the current H. **That index cannot be exact.** H depends on the destination, not only on the mask (`tb/rom_check.cpp`, `rom_check.txt`):

| index | entries with more than one H value (4x4, FULL, fault-free) | largest spread of H |
|---|---|---|
| (router, output, mask), the prompt's | 13,931 of 13,931 | 53 hops |
| (router, output, mask, destination chiplet) | 121,984 of 121,984 | 5 hops |
| (router, mask, destination) | 0 of 1,367,424 | 0 |
| (router, output, destination), destination phase | 0 of 5,184 | 0 |

**Choice:** H stays exact, as the prompt requires, so the index is (router, mask, destination). The output is not part of it: every candidate kept by a move lies on a minimal path through that move, so the total through it does not depend on the move. Dropping the destination would have been smaller and faster, but it changes the function and would flatter the timing, so it was not done.

**Check:** `fastHops` against `hopsAfterMove`, on every subset of the functional candidates and every arrival port, for all sizes, both scopes and 4 fault masks per size: 24 configurations, **0 mismatches**. This covers more than the reachable inputs.

**In hardware:** not a literal table with 5 read ports, which would be 16 x (destinations) entries per read. The RTL has one per-router function of the destination giving the total of each of the 4 candidates, then a selection per output from comparisons shared by all outputs. With the router position fixed this is a ROM in logic (`FIX_X`, `FIX_Y`).

## What changes against the simulated selection of v9-v20
| | v9-v20 (`DEFT_HEUR` / `DEFT_QL` with lookahead) | `DEFT_FAST` |
|---|---|---|
| Lookahead | per output, the minimum over the neighbour's **legal** moves of (remaining hops + w occupancy) | H(o) + L(o): L is one value per router, the minimum of w f + beta b over **all** its outputs and VCs |
| Coupling | occupancy and path are compared together, per neighbour output | decoupled: L can come from an output this packet cannot take, or from the other VC |
| Busy bit at the neighbour | not used | used (beta b is in L) |
| Neighbour is the destination | lookahead term 0 | L is still added: the value does not know the packet |
| Age of f, b | current | 1 cycle + cuts (below) |
| Age of L | current | 2 cycles + cuts |
| Q update | immediate | applied 3 cycles later, using `FAST_Q_WRITE_DELAY` |
| Bootstrap | minimum of the old cost at the next router | minimum of `cost` at the next router, so L-based |
| Q entry width | float32 in v10-v19 | 16-bit fixed point, F as v18, since that is what the RTL has and what the area counts. This does not favour our methods |
| LB-I chiplet routers | learned in the simulator although v18's RTL has no table there | no table and no learning there, matching the RTL |
| Tie break | random | random in the simulator; two priority orders from an LFSR bit in the RTL. Not modelled |

## Design that fits: where the time goes
Every change below was made to the RTL after measuring the path (`experiments_v21.py synth`), on 4x4 with one unit per port:
1. `w f + beta b + L` is packet-independent, so its sum is registered in the previous cycle. One carry chain left in the decision.
2. All comparisons in parallel, not a chain of minima.
3. The candidates' 6 comparisons are shared by all 5 outputs.
4. Two priority orders for ties instead of five.
5. Value ranges (6 and 7 bits), and a carry-save step with Q-learning.

**The stages:**
* **Stage A,** while the head is on the link or moves to the buffer front: relation, candidate totals, Q read. A head on the link enters directly when its port has nothing else to route, as the prompt's "the key is known when the head is buffered" needs.
* **Decision, first cycle:** H per output, then the cost.
* **Decision, second cycle:** comparisons and choice. The cut is the cost register.

## How N_fast is computed
`N = (cycles of stage A - 1) + (cycles of the decision - 1)`, the worst over sizes and router types (`nfast_table`), with a cycle count of ceil(arrival + setup) as in v18, so no register overhead.
* **Decision cycles:** 1 if the path without a cut fits; 2 only if **both** stages with the real cut fit (the prompt's rule); otherwise 3. The v18 formula on the uncut path alone would give less for some variants; it was not used, because a measured cut misses there.
* **One N per variant, the worst router.** `-deft_lb decision_delay` is uniform. LB-F's chiplet routers set its N, although its interposer routers are faster. This does not favour LB-F.
* **Form:** one unit per input port, since this is what the simulator models: every port decides each cycle, with no contention between ports. One unit per router is reported for area, but a head on the link could not enter stage A when another port holds the unit, which the simulator does not charge.

## The delay and age in the simulator
* `decision_delay N`: as v20, on multi-output hops only.
* `fast_stale K`: f, b and L are K cycles older, K = cycles from the cost registers to the choice. A decision with a cut uses values registered one cycle before it chooses. Without this, the simulator would use fresher values than the hardware has.
* **Not modelled:**
  * The guard in the RTL: a head granted in stage A cannot be granted again until its decision is over, so a blocked head retries every 2-3 cycles, not every cycle.
  * The round-robin counter read in the first decision stage.
  * The early exit: a single-output hop skips the delay in the simulator, as in v20. The RTL computes the same stages for it and would need a bypass, which is **not implemented** in the RTL. Its timing is not measured.

## Corrections made during the round
* **Drain tests, first run: 38 FAIL, all `NO_OUTPUT` on 2x2 CI.** The runs stopped at `LUT lookup failed: missing VL LUT entry`: the jobs passed DeFT's rho\* LUT, which lacks the exotic drain masks, instead of the default LUT of the v10 and v19 protocols. No packet ran, so this was not a deadlock. The LUT was fixed and the 2x2 tests re-run; the other 178 had drained completely. All 216 pass.
* **Router smoke test, first run: FAIL with one unit per port.** The direct entry from the link took a head whose VC buffer still held flits. It now requires that VC to be empty. All 112 pass. The vectors could not see this: they check the decision units, not the router around them.
* **The vector job was stopped and restarted** whenever the RTL it read changed. The result on file is from the frozen RTL, with the tuned weights.
* **Raw tuning outputs** were deleted before a per-run CSV was written (addendum).

## Tuning
Variants are tuned at the N_fast of their scope and kind, as the prompt asks. The learners inherit (w, beta) of the heuristic of their scope and size, and the grid for alpha has 5 points, since the prompt fixes the key to the destination chiplet (the v6 grid's key dimension does not apply).
