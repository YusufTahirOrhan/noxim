# Findings v26: fault coverage

Status: **in progress.** Done: the regression (A0), the masks and the pre-registration, the model check on every mask of 2x2
(A1) and on the four sets of 3x3 and 4x4 (A2), the drain tests on the 192 masks (B2), the reachability analysis (B5), the
ladders of the 192 masks, the timing runs, and the conformance of the model with the simulator (A3). Part A is complete.
Not finished: the evaluation runs (B3; all 18,432, the time rule drops nothing). They were paused at the user's request on
14 November at 21:46 with 10,541 runs finished and no dead-end event; the chain resumes from the finished runs
(`DECISIONS.md`). Every answer below says whether it is final.

**Part A: 102,730 model checks, all pass, and 12.0 million simulator hops replayed through the model without a mismatch.**
Every fault pattern of 2x2 (50,625 masks), and on 3x3 and 4x4 every pattern of a single chiplet plus 388 masks from the
whole space, for both relations of the round: no cycle in the channel dependencies, no dead end, no livelock, and no
dependency that the fault-free pattern does not have. In 156 simulator runs under 18 masks, every hop of a head flit is a
transition of the model and every set of outputs the router offers is the set the model offers.

Nothing is tuned and no row is changed: the configuration is the frozen one of round 25, the simulator is the ee0e247 build
(the sources of ce6ab6a), and the analysis is fixed in `PREREGISTRATION.md`, committed with `masks_v26.json` before any run of
Parts A and B.

## Gates
* **Regression** (`regression.md`): the 84-configuration set is byte-identical to a fresh build of ee0e247 in all three
  comparisons (the ce6ab6a build, `bin/noxim` with the options absent, `bin/noxim` with every option given explicitly off).
  The three binaries have the same md5. No simulator source changed in this round.
* **Controls of the model check** (`formal_controls.md`): with R3 and the F1 source rule removed the CDG is cyclic (the fixed
  pair and both relations of this round), and the subset check fails when the CDG of `CI_XY_O1` is tested against that of
  `CI_XY_XY` (184 edges outside). The checks can fail.
* **Controls of the conformance comparison** (`conformance_controls.md`): the hops of 2x2 runs replayed through four models
  that are deliberately not the one of the run (the other interposer order, the Up rule of rounds 1-22, the entry fixed at
  injection, another fault mask) give 9,770 to 54,171 mismatches out of 95,596 to 119,541 records; replayed through the right
  model they give none.
* **Drain tests** (`drain_v26.csv`): 1,152 of 1,152 pass. Every one of the six rows of Part B on every one of the 192 masks:
  one burst with every source-destination pair is delivered in full (4,032, 20,592 and 65,280 packets on 2x2, 3x3 and 4x4),
  the network empties, no dead-end event.
* **Ladders** (`load_points_v26.md`): one per mask and traffic pattern, 384 ladders from 10,503 sweep runs of DeFT_P (seed
  101, the D1 rule as Part C of round 25 ran it), no dead-end event. No ladder has Lsat below 0.001 (the lowest is 0.0012),
  so the rate at which L0 is measured (0.0002) is at most a sixth of Lsat everywhere.
* **Time rule** (`runtime_estimate.md`, `drops.json`): the 1,152 timing runs took 4,789 s with 12 processes, which puts the
  full design of 18,432 runs at 21.3 h, below the limit of 40 h. Nothing is dropped: the design keeps all four rates on all
  three sizes and all 16 masks per cell.

## The ten questions

### 1. A1: how many masks and checks, do all pass, does the subset check hold for every mask? The largest hop count
**Final. All 50,625 masks, 101,250 checks, every check passes on every mask; the subset check holds for every mask; the
longest path is 24 hops** (`formal_all_2x2.md`, `formal_all_2x2.csv`).
* The masks are all 15^4 fault patterns of 2x2 that leave every chiplet a functional VL, the fault-free one included, with
  0 to 12 faulty VLs. Both relations of the round were checked on each: `CI_XY_XY` (the main row) and `CI_XY_O1` (the second
  row), with the model and the settings of `formal/xy_check.py`.
* On all 101,250 lines: the CDG is acyclic, no reachable state is a dead end, the state graph is acyclic, and no CDG edge
  lies outside the fault-free CDG of the same relation.
* The fault-free CDG has 800 nodes and 1,424 edges for both relations (the number of the independent sampled run named in the
  prompt). The CDG shrinks as VLs fail: 1,356-1,362 edges with one faulty VL, 660-728 with twelve.
* The longest path is 24 hops for the fault-free mask and never longer: 16 to 24 hops over all masks.
* Round 24 had checked 897 of these masks. The 2x2 result no longer rests on a sample.
* Cost: 66,533 CPU-seconds, 0.66 s per check on the loaded machine (the prompt expected 0.3-0.5 s on a free one).

### 2. A2: the four sets on 3x3 and 4x4; does the argument for set 2 hold in the data?
**Final. 1,480 checks on 3x3 and 4x4, every check passes on every mask; both halves of the argument hold in every case
the data can test** (`formal_a2.md`, `formal_a2.csv`, `formal_subset_2x2.md`).

| size | set | masks | checks | pass | longest path (hops) | faulty VLs |
|---|---|---|---|---|---|---|
| 3x3 | 1: fault-free | 1 | 2 | 2 | 32 | 0 |
| 3x3 | 2: every pattern of one chiplet, the others fault-free | 126 | 252 | 252 | 32 | 1-3 |
| 3x3 | 3: random, from the whole space | 200 | 400 | 400 | 27-32 | 10-24 |
| 3x3 | 4: the masks of Part B | 64 | 128 | 128 | 29-32 | 2-18 |
| 4x4 | 1: fault-free | 1 | 2 | 2 | 40 | 0 |
| 4x4 | 2: every pattern of one chiplet, the others fault-free | 224 | 448 | 448 | 40 | 1-3 |
| 4x4 | 3: random, from the whole space | 60 | 120 | 120 | 35-40 | 21-38 |
| 4x4 | 4: the masks of Part B | 64 | 128 | 128 | 34-40 | 4-32 |

* Both relations on every mask: CDG acyclic, no dead-end state, state graph acyclic, no CDG edge outside the fault-free
  CDG (1,920 nodes / 3,632 edges on 3x3, 3,520 / 6,848 on 4x4). One mask of Part B on 3x3 has both of its faults in one
  chiplet and is therefore also in set 2: 390 different masks on 3x3, 349 on 4x4.
* The 4 h rule was not reached: the 24 sampled 4x4 checks took 32 CPU-seconds on average, 1.04 h for all of them with six
  processes, so set 3 on 4x4 keeps its 60 masks. Before this round 31 masks had been checked on 3x3 and 11 on 4x4.

**The argument for set 2.** 3x3 has 15^9 and 4x4 15^16 fault patterns; they cannot be enumerated. The claim is that the
fault-free mask and set 2 decide all of them. It rests on one property of the model: the fault pattern enters
`impl_relation_check.explore()` in two lines only, where the initial states are built. A packet starts with one functional
VL of its source chiplet as its exit (every functional one is explored) and with the functional VLs of its destination
chiplet as its entry candidates. After that the successor of a state depends on the state alone. A fault in a third
chiplet never appears, and an intra-chiplet packet uses no VL.
* *First half: a fault only removes behaviour.* With fewer candidates a packet is offered a subset of the moves it is
  offered with more, and its pruned candidate set stays a subset. So every channel dependency of a mask is a dependency of
  the fault-free mask, and since the fault-free CDG is acyclic (check 1 on set 1), the CDG of every mask is acyclic. This
  is check 4. **It holds on all 50,625 masks of 2x2 and on all 739 masks checked on 3x3 and 4x4**, the 260 random masks of
  set 3 with 10 to 38 faulty VLs included.
* *Second half: the packets to one chiplet see only that chiplet's faults.* Under a mask M, the packets with a destination
  in chiplet c have the entry candidates they have under M restricted to c (the faults M has in c, all other chiplets
  fault-free), and fewer exits. So their reachable states are a subset of those under the restricted mask, with the same
  successors. The restricted mask is a mask of set 2, or the fault-free mask if c has no fault. If it has no dead end and
  no cycle for the packets to c, M has none for them either, and their longest path under M is not longer. Every packet
  has a destination chiplet, so checks 2 and 3 on sets 1 and 2 give checks 2 and 3 for every mask. **Tested directly on
  2x2: for 1,000 masks with faults in at least two chiplets, both relations and each of the four chiplets, the states
  under the mask are a subset of the states under the restricted mask in all 8,000 comparisons** (6,700 states against
  11,630 on average; never the same set, because the restricted mask explores more exits).
* *Do the data agree?* Yes, wherever they can speak. Check 4 fails on no mask. The second-half test fails in no
  comparison. On 2x2 the conclusion itself is checked without the argument, on every mask. On 3x3 and 4x4 the 388 masks of
  sets 3 and 4, which the argument says must pass, pass, and none has a longer path than set 2 (32 and 40 hops; they have
  27-32 and 34-40).
* *What this is and is not.* For 2x2 the result is exhaustive. For 3x3 and 4x4 it is exhaustive over the patterns of a
  single chiplet (all 14 patterns of each of the 9 and 16 chiplets) and extends to every combination by the argument,
  which is a property of the model's code and is confirmed on every mask tried; it is not an enumeration. The hop bounds
  are 24, 32 and 40 hops on 2x2, 3x3 and 4x4, for every fault pattern.
* All of this is about the model. Question 3 is what ties the model to the simulator.

### 3. A3: how many hops compared per row and size, how many mismatches?
**Final. 11,999,425 hops compared in 156 simulator runs, more than 1,000,000 for every row and size; 0 mismatches**
(`conformance.md`, `conformance.csv`).

| row | relation of the model | 2x2 | 3x3 | 4x4 |
|---|---|---|---|---|
| DeFT_P | `A_fixed_XY` | 1,019,444 | 1,405,704 | 1,531,555 |
| `CI_heurLA_X_LF` (main) | `CI_XY_XY` | 1,042,044 | 1,430,288 | 1,545,058 |
| `CI_heurLA_O_LF` (second) | `CI_XY_O1` | 1,044,590 | 1,433,461 | 1,547,281 |

* **What is compared.** An instrumented copy of the simulator writes one record per hop of a head flit: the router, the
  input port, the VN and the candidate masks before the hop, the destination, the outputs the routing function and the VN
  rule offer, the output taken, the VN and the masks after. The record is looked up in the state graph that the model check
  builds for that destination (`impl_relation_check.explore()`, the function Part A uses, unchanged): the state before the
  hop must be a node of the graph, the offered outputs must be exactly the moves that leave the node, and the hop taken
  must be one of its edges. The arrival at the destination router is compared too: 1,036,902 arrivals, at each of which
  the model must have delivered.
* **Result.** No mismatch in any of the three comparisons on any record, no difference between the topology the simulator
  reports and the model's instance, no dead-end event. All 156 instrumented runs give a statistics file byte-identical to
  that of `bin/noxim`, so the records are those of the simulator that the evaluation runs.
* **Runs.** Six masks per size: fault-free, the same VL faulty in every chiplet, and mask 1 of each of the four rates of
  Part B, so up to half of the VLs faulty; uniform and hotspot traffic at 1.0 x Lsat of DeFT_P on the mask; seed 1. With
  seed 1 2x2 had 503,018 to 514,811 hops per row, so seed 2 was added on its six masks. 4x4 needed seed 1 only. On 3x3
  seed 2 ran on the first two masks before the ladders of Part B existed; with all six masks seed 1 alone has 1.03 to 1.05
  million hops there, so those runs were not needed by the rule. They are kept (`DECISIONS.md`).
* **Where the comparison has most to say.** The late-binding rows offer more than one output on 15 %, 12 % and 10 % of
  their hops on 2x2, 3x3 and 4x4 (152,460 to 176,233 hops per row and size); there the whole offered set is compared, not
  only the hop taken. DeFT_P never offers more than one: its two VLs are fixed at injection. Of the 13.0 million records
  (hops and arrivals), 0.52 million are in the intra-chiplet phase of the model, 1.84 million in the source chiplet, 8.39
  million on the interposer and 2.29 million in the destination chiplet.
* **The comparison can fail** (`conformance_controls.md`): replayed through four models that are not the one of the run,
  2x2 runs give 9,770 to 54,171 mismatches out of 95,596 to 119,541 records.
* **What this is and is not.** It is a test on runs. On every hop the simulator made in them, the router offered exactly
  what the model offers and moved along a transition of the model. It does not prove that the two agree in states the runs
  did not visit. Together with questions 1 and 2: the model has no deadlock, no dead end and no livelock on the fault
  patterns checked, and on 12 million hops under 18 masks the simulated router did nothing that the model does not do.

### 4. Primary family of Part B: how many of 24 supported, which against?
*Pending.*

### 5. The trend over the fault rate, per size and per traffic pattern
*Pending.*

### 6. In which patterns is the main row behind the best reference, or behind DeFT_P? What do these patterns have in common?
*Pending.*

### 7. `CI_heurLA_O_LF` against the main row under faults
*Pending.*

### 8. Against each reference row
*Pending.*

### 9. Random against even patterns at the same rate (rounds 25 and 26)
*Pending.*

### 10. Reachability of MTR and RC at the four rates
**Final. MTR and RC lose exactly the share of the VLs that is faulty, on every mask; DeFT and the two late-binding rows
deliver every pair on every mask** (`reachability_v26.md`; MTR and RC by the static analysis of `reach_v10.py`, unchanged,
with the rate 8/16 added; the other rows by the drain tests).

| rate | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| 1/16 | 93.75 % | 94.44 % | 93.75 % |
| 2/16 | 87.50 % | 88.89 % | 87.50 % |
| 4/16 | 75.00 % | 75.00 % | 75.00 % |
| 8/16 | 50.00 % | 50.00 % | 50.00 % |

* The table is the share of the inter-chiplet source-destination pairs that can be delivered. It is the same for MTR and for
  RC, the same for the mean and for the worst mask, and the same for the up to 1,000 random masks per (size, rate) and for the
  16 masks of Part B. No mask keeps every pair.
* The reason is in the two definitions. An RC source may leave only through the boundary router nearest to it, and each of
  the four VLs of a chiplet is the nearest for four of its sixteen routers. Under MTR's turn restrictions
  (`results_v10/mtr_config.json`) every source can reach all four exits, but every destination router can be entered
  through one VL only, again four routers per VL. So a faulty VL cuts off a quarter of the sources (RC) or of the
  destinations (MTR) of its chiplet from every other chiplet, whatever the other faults are, and the delivered share is the
  functional share of the VLs. (3x3 has 36 VLs, so its first two rates are 2 and 4 of 36.)
* The 18 rows of the three old rates equal those of round 10 (`results_v10/report/reachability.csv`).
* **The rows of Part B deliver 100 % at every rate.** DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran, `CI_heurLA_X_LF` and
  `CI_heurLA_O_LF` were each given one burst with every source-destination pair on each of the 192 masks of Part B (48 masks
  per rate, 1,152 drain tests): 1,438,464 packets injected and 1,438,464 delivered per row and rate, no dead-end event
  (`drain_v26.csv`). This is a measurement on 192 masks, not an analysis of all masks; the model check of Part A is what
  covers the patterns that were not simulated, for the two late-binding rows.
* So with half of the VLs faulty MTR and RC serve half of the inter-chiplet pairs, and the rows compared in Part B serve all
  of them. MTR and RC are not run with faults for this reason; Part B has no performance number for them.
