# v19 decisions (Part K)

## Option
`-deft_vn_rr 1`, default off, a top-level option as requested. With it on:
* **Boundary reassignment:** in `selectOutputVirtualNetwork`, a VN0 packet at a boundary router arriving on a horizontal port and leaving through Hub takes the round-robin VN of that router. The caller commits the counter when `reserve` succeeds.
* **Busy VC:** the head waits on the VC it was given. There is no fallback. If another head reserves first at that router, the counter moves and the waiting head's next attempt asks for the other VC; this follows from "advance on each successful reservation at that router".
* **R3:** `isOutputDirectionAllowed` tests the input VN on Horizontal -> Down.
* **Per-router counters:** one source and one boundary counter per router, replacing the two global counters (deviation D3). With the option off, the global counters are used as before.
* **Local -> Down keeps its VN.** The source round-robin has already chosen it. The prompt names only arrivals from a horizontal port.
* **MTR and RC:** `vn_rules 0` returns before any of this, so the option has no effect on them. They are run without it.

## Where this differs from the paper's Algorithm 1
Algorithm 1 gives every source on a boundary router the round-robin VN, whichever VL it will use. We keep the F1 fix: a boundary source gets VN1 only if it is committed to its own VL, since the unrestricted rule is unsafe (Finding F1). So **`-deft_vn_rr 1` is not all of Algorithm 1**. It differs in this one rule, in the direction of fewer VN1 sources. The VN0 packets of the other boundary sources then get the reassignment at their Down port anyway.

## Consequences outside the VN logic
* **Selection under the option:** `localCost` and `bestContinuation` read the occupancy of the VC the counter currently points to, at this router or the neighbour, for a Hub output. The simulator reads the neighbour's counter directly; real hardware would need it reported. Not charged here.
* **VC statistics:** a head that already owns its VC can see `RT_OUTVC_BUSY` when the counter has moved on, which would have counted as a false wait. The statistics hook now checks for an existing reservation. This only changes `-deft_lb vc_stats` output, and only under the option: without round-robin the status cannot arise for a reserved head. The v17 data are not affected.

## One binary for K and L
`-deft_lb decision_delay` and `-deft_lb hop_stats` (Part L) were added in the same build as `-deft_vn_rr`, before the regression. K5 runs and L runs then use the same binary, so the L report can use K5 as N = 0 without a second check. The experiments still run in the requested order.

## Proof check (recorded as required)
The DeFT paper's safety argument is its Theorems III.1-III.4 and the "Deadlock-freedom" paragraph on its page 1049. The prompt refers to "Theorem 2" and "Lemma 1" of our own paper, whose text is not in this checkout, so the argument is written out here in full, for the relation with the reassignment.

**Channels:** source and intra-chiplet channels on chiplets in VN0 and VN1, Down channels (one VL, two VCs), interposer channels in VN0 and VN1, Up channels (VN1 only), destination-chiplet channels (VN1).

**Which transitions exist with the option:**
1. Chiplet VN0 -> chiplet VN0: within a chiplet, under the chiplet turn model (intra-chiplet and source phase).
2. Chiplet VN0 -> Down in VN0 or VN1: the reassignment.
3. Local -> Down in the source's VN: not a channel dependency, as no channel precedes the injection.
4. Down in VN x -> interposer VN x. A packet on Down holds that VC; the VN does not change on the interposer.
5. Interposer VN x -> interposer VN x under the interposer turn model; interposer VN x -> Up in VN1.
6. Up -> destination chiplet VN1 -> destination chiplet VN1 under the chiplet turn model -> ejection.
7. Chiplet VN1 -> Down: **does not exist**. This is R3 on the input VN. VN1 on a chiplet holds destination-phase packets and intra-chiplet packets, and neither goes to Down.

**No cycle:** order the classes as: chiplet VN0, then Down, then interposer VN0 and interposer VN1 (no dependency between these two), then Up, then chiplet VN1. Every transition above stays in a class or moves to a later one. Within a class:
* the Down and Up channels have no dependency among themselves;
* chiplet and interposer channels in one VN are acyclic by the turn model (XY or odd-even) on minimal paths.

So the channel dependency graph has no cycle.

**What changes against the implementation without the option:** only transition 2 gains the VN1 target, and interposer VN1 gains packets. **The source-chiplet part is unchanged**, because a packet switches to VN1 only on the Down link and nothing in the chiplet VN0 class receives anything from later classes. The Down channels are one class whatever their VC, as the prompt expected.

**Late binding:** the argument does not use the fixed pair. Exit and entry candidates only select among the moves of transitions 1 and 5, which stay minimal and turn-legal. Livelock: each phase is minimal, so the hop count is bounded.

**Model check:** `formal/impl_relation_check.py` already explored both VNs on Horizontal -> Down from v1 on, which is what the implementation did **not** do until now. Earlier model-check results therefore already covered this relation. They are repeated here on the full mask set, with a negative control (`formal_vnrr.md`).

## Method parameters
`experiments_v10.methods`, no re-tuning, as the prompt requires: **all parameters and DeFT's rho\* were tuned without the round-robin**. This holds for DeFT(rho\*)'s LUT as well as for the learners. Which way it biases the comparison is not known.

## K5 on resuming (3 November)
* **The runner had not stopped.** The resume prompt says K5 was stopped. It was in fact still running, 17.2 h in, under the `wsl.exe` of the previous session. It was left running: a second runner would have duplicated in-flight runs, and stopping it would have gained nothing but a log file. Its binary is the one that passed the regression (md5 f72577901551675dfc2767526fd36844).
* **It is not detached in the sense of the new rule,** since it depends on the previous session's PowerShell process. If it ends before the design is complete, K5 is restarted detached with the same command; the runner skips completed runs. All later stages run through `detach.sh`.
* **Integrity at 09:38:** 17,123 of 17,850 complete; missing 727 (RC and DeFT_noRR on 4x4); 0 truncated; 0 not in the job list; 0 byte-identical across seeds of a cell; 0 dead-end events (`experiments_v19.py check 1 eval`, which prints no results).
* **Time rule:** 207 runs in the last 30 minutes, so about 1.8 h remain, below the 16 h limit. The full design stays; there is no addendum and seeds 66-70 are kept.

## K6 and K7 postponed (3 November)
The K6 load sweep finished (1,260 of 1,260, 0 dead-end events; `fault_sweep_runs.csv`) and the load choice is committed (`fault_load_choice.json`, `.md`). **The K6 confirmatory runs and K7 are postponed by the v21 prompt and were not started.** Reason: they would measure a selection that is about to be replaced, since v20 showed that the simulated selection's latency gain does not survive the delay its timing implies. If they run later for the v21 selection, the load choice stands, because it depends only on DeFT(rho\*) with the round-robin. Seeds 71-75 and 41-43 of K6 and K7 stay unused.

## Figure
The prompt names `paper2/figures/latency_load` as the model of the latency-versus-load figure. No such file is in this checkout or in the parent repository, so the figure follows the v17 and v18 style: small multiples per size.
