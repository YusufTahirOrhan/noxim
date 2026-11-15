# Findings v26: fault coverage

Status: **complete.** Part A (A0 to A3), Part B (B1 to B5) and the report are done, and every answer below is final. The
evaluation of Part B ran all 18,432 runs (the time rule dropped nothing), with a pause at the user's request from 21:46 on
14 November to 00:10 on 15 November (`DECISIONS.md`).

**Part A: 102,730 model checks, all pass, and 12.0 million simulator hops replayed through the model without a mismatch.**
Every fault pattern of 2x2 (50,625 masks), and on 3x3 and 4x4 every pattern of a single chiplet plus 388 masks from the
whole space, for both relations of the round: no cycle in the channel dependencies, no dead end, no livelock, and no
dependency that the fault-free pattern does not have. In 156 simulator runs under 18 masks, every hop of a head flit is a
transition of the model and every set of outputs the router offers is the set the model offers.

**Part B: under random VL faults the main row is ahead of the best DeFT variant in 22 of the 24 pre-registered tests and
behind in none.** On 192 random masks with 1/16 to 8/16 of the VLs faulty, `CI_heurLA_X_LF` has a higher throughput and a
lower latency at 1.0 x Lsat than the best of DeFT_P, DeFT_B, DeFT_Dis and DeFT_Ran at every rate on 3x3 and 4x4 and at
1/16 to 4/16 on 2x2. The gain shrinks as the rate grows: THR from +3.3 / +5.5 / +8.9 % at 1/16 to +0.6 / +1.4 / +2.0 % at
8/16 on 2x2 / 3x3 / 4x4, LAT from -18.9 / -18.4 / -19.6 % to -6.0 / -7.1 / -13.2 %. The two tests that are not
significant are 2x2 at 8/16. What takes the gain away is not the number of faulty VLs as such but a chiplet that is left
a single functional VL: within one rate, the masks without such a chiplet keep most of the gain, and the masks with one
lose most of the throughput gain (questions 6 and 9).

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
* **Evaluation runs** (`fault_rate_runs.csv`): 18,432 of 18,432, no dead-end event, no run without a received packet. The
  raw folder passed its check before it was aggregated (no output missing, truncated or outside the job list, none
  byte-identical across seeds). The 17,280 runs that were left after the timing runs took 20.3 h of machine time, in two
  parts because of the pause.
* **The analysis computed twice** (`report/families_check.md`): `check_v26_family.py`, which shares no code with the
  report, gives the same effect, interval, p value, Holm-adjusted p value and verdict for all 24 tests of the primary
  family (largest difference 0.005 percentage points).

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
**Final. 22 of 24 supported, none against, 2 not significant (2x2 at 8/16, both metrics)** (`report/summary_B.md` B.1,
`report/primary.csv`; computed a second time in `report/families_check.md`).

| size | rate | faulty VLs | THR: effect [95 % CI] | Holm p | verdict | LAT at 1.0 x Lsat: effect [95 % CI] | Holm p | verdict |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 1/16 | 1 | +3.3 [+2.5, +4.1] | 5e-06 | supported | -18.9 [-21.7, -15.9] | 4.4e-08 | supported |
| 2x2 | 2/16 | 2 | +3.0 [+2.1, +4.0] | 5.3e-05 | supported | -17.3 [-19.9, -14.7] | 3.2e-08 | supported |
| 2x2 | 4/16 | 4 | +2.6 [+1.8, +3.5] | 7.3e-05 | supported | -16.9 [-20.1, -13.5] | 9.2e-07 | supported |
| 2x2 | 8/16 | 8 | +0.6 [-0.5, +1.7] | 0.251 | **n.s.** | -6.0 [-10.9, -0.8] | 0.056 | **n.s.** |
| 3x3 | 1/16 | 2 | +5.5 [+5.1, +6.0] | 2.5e-13 | supported | -18.4 [-20.5, -16.3] | 8.3e-10 | supported |
| 3x3 | 2/16 | 4 | +4.6 [+3.2, +5.9] | 2.7e-05 | supported | -16.6 [-20.4, -12.7] | 7.5e-06 | supported |
| 3x3 | 4/16 | 9 | +3.2 [+2.1, +4.4] | 0.00015 | supported | -16.0 [-20.0, -11.9] | 1.8e-05 | supported |
| 3x3 | 8/16 | 18 | +1.4 [+0.6, +2.1] | 0.005 | supported | -7.1 [-10.4, -3.6] | 0.003 | supported |
| 4x4 | 1/16 | 4 | +8.9 [+7.5, +10.3] | 1.2e-08 | supported | -19.6 [-22.9, -16.1] | 3.1e-07 | supported |
| 4x4 | 2/16 | 8 | +6.8 [+4.8, +8.9] | 2.7e-05 | supported | -19.6 [-23.8, -15.3] | 4.3e-06 | supported |
| 4x4 | 4/16 | 16 | +4.9 [+3.5, +6.4] | 2.1e-05 | supported | -18.0 [-22.2, -13.6] | 1.1e-05 | supported |
| 4x4 | 8/16 | 32 | +2.0 [+1.0, +2.9] | 0.002 | supported | -13.2 [-16.9, -9.4] | 4.1e-05 | supported |

* **The test.** `CI_heurLA_X_LF` against the best reference: per mask, traffic pattern and metric the best of DeFT_P,
  DeFT_B, DeFT_Dis and DeFT_Ran. The unit is the mask, 16 per cell; uniform and hotspot traffic and the two seeds are
  averaged within a mask. Two-sided t test over the masks, Holm over the 24 tests at 0.05. THR is the largest accepted
  throughput over the four loads; LAT is the mean latency at 1.0 x Lsat of DeFT_P on the mask.
* **Supported:** THR and LAT at every rate on 3x3 and 4x4, and at 1/16, 2/16 and 4/16 on 2x2.
* **Not significant:** 2x2 at 8/16. THR +0.6 % with an interval that includes 0. LAT -6.0 %: its unadjusted interval
  excludes 0 (p 0.028), but the Holm-adjusted p is 0.056, so by the rule fixed in advance it is not significant.
* **Against:** none. None of the 24 effects is on the wrong side.
* **Computed twice.** The second script gives the same 24 effects, intervals, p values and verdicts.
* **Stated in advance:** the tests most at risk were 8/16 on every size and 2x2 at every rate. The two that are not
  significant are in that set. The others of the set are supported: 2x2 at the three lower rates with THR +2.6 to +3.3 %,
  3x3 and 4x4 at 8/16 with THR +1.4 and +2.0 %.
* **What THR measures.** The loads go up to 2.0 x Lsat. In about half of the (mask, traffic, seed) cells the largest
  accepted throughput of a row is at that last load (B.12: the main row in 22 to 45 of the 64 cells of a (size, rate),
  DeFT_P in 22 to 47). There THR is a lower bound of the saturation throughput, for the row and for the references alike:
  the comparison is of the accepted throughput within the loads of the design.

### 5. The trend over the fault rate, per size and per traffic pattern
**Final. The gain shrinks as the rate grows, on every size. The throughput gain falls steadily; the latency gain is nearly
flat up to 4/16 and drops at 8/16. Uniform traffic carries the trend; under hotspot traffic the gain is small and nearly
flat** (`report/summary_B.md` B.2, B.3; `report/extra_B.md` X.2).

`CI_heurLA_X_LF` against the best reference, effect in per cent, both traffic patterns (B.2):

| size | metric | 1/16 | 2/16 | 4/16 | 8/16 |
|---|---|---|---|---|---|
| 2x2 | THR | +3.3 | +3.0 | +2.6 | +0.6 |
| 2x2 | LAT | -18.9 | -17.3 | -16.9 | -6.0 |
| 2x2 | P99 | -31.0 | -29.4 | -30.0 | -8.8 |
| 3x3 | THR | +5.5 | +4.6 | +3.2 | +1.4 |
| 3x3 | LAT | -18.4 | -16.6 | -16.0 | -7.1 |
| 3x3 | P99 | -35.9 | -32.7 | -32.6 | -10.9 |
| 4x4 | THR | +8.9 | +6.8 | +4.9 | +2.0 |
| 4x4 | LAT | -19.6 | -19.6 | -18.0 | -13.2 |
| 4x4 | P99 | -41.1 | -42.7 | -33.5 | -17.9 |

Each traffic pattern separately (B.3):

| size | traffic | THR: 1/16 | 2/16 | 4/16 | 8/16 | LAT: 1/16 | 2/16 | 4/16 | 8/16 |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | +3.5 | +3.4 | +2.1 | +0.7 | -25.7 | -24.2 | -23.5 | -6.5 |
| 2x2 | hotspot | +3.0 | +2.7 | +3.1 | +0.5 | -11.4 | -9.8 | -9.7 | -5.5 |
| 3x3 | uniform | +8.6 | +6.5 | +4.0 | +0.6 | -27.9 | -25.6 | -23.1 | -8.2 |
| 3x3 | hotspot | +2.6 | +2.6 | +2.5 | +2.2 | -7.7 | -6.5 | -8.3 | -5.9 |
| 4x4 | uniform | +14.4 | +11.8 | +6.8 | +2.7 | -32.1 | -30.8 | -25.6 | -18.8 |
| 4x4 | hotspot | +3.6 | +2.1 | +3.1 | +1.2 | -4.8 | -6.8 | -9.7 | -7.2 |

* **THR** falls with every step of the rate on every size, and the larger size gains more at every rate: from +3.3, +5.5
  and +8.9 % at 1/16 to +0.6, +1.4 and +2.0 % at 8/16 on 2x2, 3x3 and 4x4.
* **LAT at 1.0 x Lsat** is -16 to -20 % on every size at 1/16, 2/16 and 4/16, almost unchanged over these three rates,
  and drops to -6.0, -7.1 and -13.2 % at 8/16. **P99** behaves the same way: -29 to -43 % up to 4/16, then -8.8 % (the
  interval includes 0), -10.9 % and -17.9 %.
* **Uniform traffic carries the trend.** There the THR gain falls from +14.4 to +2.7 % on 4x4 and from +8.6 to +0.6 % on
  3x3. Rank correlation of the per-mask THR effect with the share of faulty VLs: -0.46, -0.66 and -0.64 on 2x2, 3x3 and
  4x4 (X.2).
* **Under hotspot traffic the gain is small and depends little on the rate.** THR is +2 to +4 % on every size up to 4/16
  (3x3: +2.6, +2.6, +2.5, +2.2 % over the four rates), and the latency gain does not fall with the rate on 3x3 and 4x4
  (4x4: -4.8, -6.8, -9.7, -7.2 %). Rank correlations with the share: -0.38, -0.11, -0.43 for THR. This fits the ladders:
  under hotspot traffic the saturation load of DeFT_P hardly moves with the fault rate on 3x3 and 4x4 (mean Lsat 0.0032
  to 0.0028 and 0.0016 to 0.0016 from 1/16 to 8/16), while under uniform traffic it falls to half or less (0.0087 to
  0.0036, 0.0067 to 0.0034). With hotspot traffic the VLs are not what limits the network.
* **Against DeFT_P alone** the trend is the same at a higher level: THR +14.9 / +16.9 / +21.0 % at 1/16 and +3.6 / +7.0 /
  +5.9 % at 8/16; LAT -44 to -52 % up to 4/16 and -20.4 / -31.3 / -32.9 % at 8/16 (question 8).
* **At half load** (0.5 x Lsat) the main row is 2.6 to 4.1 % faster than DeFT_P up to 4/16 and 1.7 to 2.6 % at 8/16, in
  every cell with an interval that excludes 0 (B.9).
* **Stated in advance:** the effect would be largest at the low rates on 3x3 and 4x4 and shrink as the rate grows, and
  the hotspot half would lower the effects. The first is what the data show. The second holds for LAT in every cell and
  for THR in 10 of the 12 cells; on 2x2 at 4/16 and on 3x3 at 8/16 the hotspot THR gain is the larger one (+3.1 against
  +2.1 %, +2.2 against +0.6 %).
* The reason for the trend is in question 6: it is the chiplets that are left a single VL, and there are more of them
  the higher the rate.

### 6. In which patterns is the main row behind the best reference, or behind DeFT_P? What do these patterns have in common?
**Final. Behind the best reference in 15 of the 192 masks in THR (by at most 2.0 %) and in 6 in LAT; behind DeFT_P in 2
masks in THR and in 1 in LAT. Of the 17 masks concerned, 14 are at 8/16 and 15 leave at least one chiplet a single
functional VL. That chiplet is what they have in common** (`report/summary_B.md` B.5 to B.8; `report/extra_B.md` X.1,
X.3 to X.5, X.8, X.9).

Masks and (mask, traffic) cells in which `CI_heurLA_X_LF` is on the wrong side (B.6; 16 masks and 32 cells per line):

| size | rate | THR behind the best reference: masks / cells | LAT behind the best reference | THR behind DeFT_P | LAT behind DeFT_P |
|---|---|---|---|---|---|
| 2x2 | 1/16 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 2x2 | 2/16 | 1 / 4 | 0 / 0 | 0 / 0 | 0 / 0 |
| 2x2 | 4/16 | 1 / 3 | 0 / 0 | 0 / 3 | 0 / 0 |
| 2x2 | 8/16 | 7 / 15 | 4 / 10 | 2 / 4 | 1 / 5 |
| 3x3 | 1/16 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3x3 | 2/16 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3x3 | 4/16 | 1 / 2 | 0 / 2 | 0 / 1 | 0 / 0 |
| 3x3 | 8/16 | 3 / 6 | 2 / 3 | 0 / 1 | 0 / 2 |
| 4x4 | 1/16 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 4x4 | 2/16 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 0 |
| 4x4 | 4/16 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 0 |
| 4x4 | 8/16 | 2 / 5 | 0 / 1 | 0 / 2 | 0 / 0 |
| all | all | 15 / 41 | 6 / 16 | 2 / 11 | 1 / 7 |

* **Which masks** (X.9 lists all 17 with their faults per chiplet). Eight are 2x2 at 8/16 (7 behind in THR, 4 in LAT),
  four are 3x3 at 8/16 (3 and 2), two are 4x4 at 8/16 (THR only). The other three are 2x2 at 2/16 and 4/16 and 3x3 at
  4/16: each is behind in THR only, by 0.2 to 0.5 %, while 3 to 20 % ahead in LAT. No mask at 1/16 is behind in anything.
* **How far behind.** Per mask, THR -0.0 to -2.0 % (the largest: 2x2 at 8/16, faults per chiplet 2 3 2 1) and LAT +1.4
  to +7.6 % (3x3 at 8/16, faults 3 2 3 3 0 1 2 1 3). The worst single (mask, traffic) cell is -2.4 % in THR and +9.4 %
  in LAT (B.7). For scale, the cells in which the row is ahead average +3.1, +4.1 and +6.1 % in THR and -16.2, -15.3
  and -17.8 % in LAT on 2x2, 3x3 and 4x4 (X.5).
* **What they have in common: a chiplet with one functional VL.** A packet to such a chiplet has no entry to choose, so
  for it late binding has nothing to bind; and under uniform traffic that single VL carries everything the chiplet
  sends and receives, so it sets the capacity for every row alike. The clearest case is 2x2 at 8/16 (X.3):

  | chiplets with one functional VL | masks | THR against the best reference | LAT | THR against DeFT_P | LAT against DeFT_P |
  |---|---|---|---|---|---|
  | none (two faults in every chiplet) | 4 | +3.7 [+1.9, +5.4] | -19.7 [-28.1, -10.2] | +12.7 [+9.5, +16.0] | -50.4 [-68.0, -23.2] |
  | one | 10 | -0.5 [-1.0, +0.1] | -1.7 [-3.1, -0.3] | +0.8 [+0.4, +1.2] | -8.4 [-12.1, -4.6] |
  | two | 2 | -0.2 [-9.7, +10.3] | +3.2 [-13.2, +22.7] | +0.1 [-10.6, +12.1] | +1.4 [-24.0, +35.3] |

  The two tests of the primary family that are not significant are this cell: 12 of its 16 masks have such a chiplet.
* **One such chiplet is enough, also on the larger sizes and at low rates** (X.3). Within one rate, THR against the best
  reference without and with one such chiplet: 3x3 at 2/16 +5.1 % (14 masks) and +0.8 % (2); 3x3 at 4/16 +4.3 % (10)
  and +1.5 % (6); 4x4 at 2/16 +8.0 % (13) and +2.1 % (3); 4x4 at 4/16 +7.9 % (6) and +3.1 % (7). On 4x4 that is one
  chiplet of sixteen. The latency gain is roughly halved (-17.6 to -22.7 % without, -8.6 to -13.6 % with one).
* **With more such chiplets the gain shrinks further but stays on the right side on 3x3 and 4x4** (B.8, all rates): 3x3
  +5.1 % with none, then +1.6, +1.7, +1.3 and +0.1 % with one to four; 4x4 +8.5 % with none, then +2.8, +4.0, +2.7,
  +2.0, +2.0, +1.1 and +0.4 % with one to seven. Rank correlation of the per-mask THR effect with the number of such
  chiplets: -0.65, -0.74 and -0.81 on 2x2, 3x3 and 4x4; with the largest number of faults in one chiplet -0.58, -0.79
  and -0.89; with the share of faulty VLs -0.44, -0.64 and -0.68 (X.1). The concentration of the faults describes the
  loss better than their number.
* **The capacity that is left** (X.5). The cells behind have 36 to 50 % of the VLs faulty on average (the cells ahead 20
  to 23 %). On 2x2 and 3x3 they have 41 to 55 % of the fault-free saturation load left (ahead: 78 to 83 %). On 4x4 the
  cells behind are mostly hotspot cells (6 of 9 in THR), whose saturation load hardly depends on the faults (question 5).
* **Hotspot traffic** (X.4): what counts is whether a chiplet that holds a hot router is the one with a single VL. With
  none, THR +2.7 / +2.9 / +2.9 % and LAT -10.1 / -7.7 / -7.3 % on 2x2 / 3x3 / 4x4; with one, -0.2 / +0.8 / +1.1 % and
  -2.7 / -6.0 / -7.1 %; with two (3 masks on 3x3, 2 on 4x4), -0.6 and -0.4 % in THR.
* **Part of "behind the best reference" is the selection of the reference.** The best reference is the best of four
  rows from two seeds per cell, which favours the reference (stated in advance). In the cells in which the main row is
  behind in THR, the best reference is a row other than DeFT_B in 11 of 22 cells on 2x2, 5 of 10 on 3x3 and 2 of 9 on
  4x4; in the cells in which it is ahead, DeFT_B is the best reference in 90 of 106, 99 of 118 and 82 of 119. Where the
  six rows are within a few per cent of each other (2x2 at 8/16: mean THR 0.0408 to 0.0448), the best of four is ahead
  of each single one partly by chance.
* **Behind DeFT_P:** 2 masks in THR (2x2 at 8/16, by 0.0 and 0.8 %) and 1 mask in LAT (2x2 at 8/16, +3.7 %); 11 cells
  in THR (-0.7 to -0.8 % on average) and 7 in LAT (+4.1 to +4.8 %) of 384. All three masks have one or two chiplets
  with one functional VL.
* **Not DeFT_P's runs** (X.8). With one functional VL in every chiplet the main row is DeFT_P (round 25). Here no run
  of the main row has the accepted throughput and mean latency of DeFT_P's run (0 of 3,072), also at 8/16: every mask
  of this round leaves some chiplet a choice.
* The list X.9 was added after the results were seen; it lists what B.6 counts and tests nothing. The descriptors
  (chiplets with one functional VL, largest number of faults in a chiplet, share, hot chiplets, Lsat relative to
  fault-free) were fixed before the evaluation (`DECISIONS.md`).

### 7. `CI_heurLA_O_LF` against the main row under faults
**Final. The main row is the better of the two under faults. The second row has 1.6 to 2.7 % less throughput in 11 of the
12 cells and a latency at 1.0 x Lsat that is equal or higher; at half load and in P99 the two are level. Against the best
reference the second row is ahead in latency in every cell, in throughput only on 3x3 and 4x4 at the lower rates**
(`report/summary_B.md` B.10, B.2; `report/extra_B.md` X.6, X.7).

`CI_heurLA_O_LF` against `CI_heurLA_X_LF`, effect [95 % CI] in per cent (B.10; negative THR and positive LAT mean the
second row is worse):

| size | metric | 1/16 | 2/16 | 4/16 | 8/16 |
|---|---|---|---|---|---|
| 2x2 | THR | -2.6 [-3.1, -2.1] | -2.4 [-3.2, -1.5] | -2.7 [-3.5, -1.9] | -0.3 [-0.8, +0.3] |
| 2x2 | LAT | +2.7 [+1.8, +3.5] | +3.3 [+0.1, +6.7] | +7.0 [+2.7, +11.4] | +0.4 [-3.9, +4.9] |
| 2x2 | P99 | +1.2 [-1.8, +4.4] | +3.9 [-1.1, +9.2] | +11.7 [+4.4, +19.4] | -4.2 [-11.3, +3.4] |
| 3x3 | THR | -2.3 [-2.9, -1.7] | -2.1 [-2.9, -1.3] | -2.6 [-3.2, -1.9] | -1.6 [-2.4, -0.7] |
| 3x3 | LAT | -0.0 [-0.8, +0.8] | +0.8 [+0.1, +1.6] | +2.8 [+0.6, +5.1] | +3.9 [-5.1, +13.6] |
| 3x3 | P99 | -5.8 [-11.0, -0.3] | -1.4 [-3.9, +1.0] | +2.2 [-1.5, +6.1] | +1.9 [-16.3, +24.1] |
| 4x4 | THR | -2.6 [-3.4, -1.8] | -1.9 [-2.6, -1.2] | -1.8 [-2.6, -1.0] | -1.7 [-3.2, -0.3] |
| 4x4 | LAT | +0.3 [-0.8, +1.5] | +0.7 [-0.4, +1.7] | +3.6 [+0.3, +6.9] | +4.3 [-1.6, +10.6] |
| 4x4 | P99 | -1.8 [-5.5, +2.1] | +0.1 [-2.6, +2.8] | +1.0 [-6.7, +9.3] | +1.0 [-11.3, +15.1] |

* **THR:** lower in every cell, with an interval that excludes 0 in 11 of 12 (not 2x2 at 8/16). The second row has the
  higher THR in 0 to 2 of the 16 masks of a cell, except on 2x2 at 8/16 (7 of 16) (X.7).
* **LAT at 1.0 x Lsat:** higher on 2x2 up to 4/16 (+2.7, +3.3, +7.0 %); within 1 % on 3x3 and 4x4 at 1/16 and 2/16
  (-0.0 to +0.8 %) and higher at 4/16 (+2.8, +3.6 %). At 8/16 the intervals are wide and none excludes 0.
* **P99:** no consistent difference. Lower on 3x3 at 1/16 (-5.8 %), higher on 2x2 at 4/16 (+11.7 %), otherwise the
  interval includes 0. At 1/16 the second row has the lower P99 in 8, 9 and 12 of the 16 masks on 2x2, 3x3 and 4x4.
* **At 0.5 x Lsat** the two are within 0.5 % of each other in every cell.
* **Against the best reference** (B.2, X.6). LAT: ahead in all 12 cells, in 10 with an interval that excludes 0 (-9.5
  to -19.3 %; not 2x2 and 3x3 at 8/16: -5.6 and -3.5 %). THR: ahead with an interval that excludes 0 in 5 cells (3x3 at
  1/16 and 2/16: +3.1, +2.4 %; 4x4 at 1/16 to 4/16: +6.1, +4.8, +3.1 %) and level in the other 7 (-0.2 to +0.6 %), which
  include every rate of 2x2. It is never behind with an interval that excludes 0. The main row is ahead in THR with such
  an interval in 11 cells.
* **Single cells in which the second row stands out** (B.7). In four of the ten cells in which the main row has its
  largest latency loss, the second row has by far the lowest latency of the six rows: 191.7 cycles against 236.1 to
  246.7 (2x2 at 8/16, faults 1 3 1 3, uniform), 129.5 against 176.9 to 230.0 and 159.2 against 219.8 to 250.0 (3x3 at
  8/16, faults 3 2 3 3 0 1 2 1 3, uniform and hotspot), 151.1 against 184.2 to 201.2 (2x2 at 8/16, faults 0 3 2 3,
  uniform). These are four cells of three masks with two to four chiplets at one functional VL. Over all masks of 8/16
  the second row is not ahead of the main row in LAT (+0.4, +3.9, +4.3 %), so this is an observation, not a result.
* Nothing in these data argues for exchanging the two rows.

### 8. Against each reference row
**Final. The main row is ahead of each of the four reference rows in THR, LAT and P99 in all 12 cells, every time with an
unadjusted interval that excludes 0. DeFT_B is the strongest reference. Against DeFT_P the gain is +12 to +21 % in THR
and -44 to -52 % in LAT up to 4/16, and +3.6 to +7.0 % and -20 to -33 % at 8/16** (`report/summary_B.md` B.4, B.9, B.13;
`report/extra_B.md` X.6).

`CI_heurLA_X_LF` against each reference row, effect in per cent, both traffic patterns (B.4, which has the intervals):

| size | rate | THR: DeFT_P | DeFT_B | DeFT_Dis | DeFT_Ran | LAT: DeFT_P | DeFT_B | DeFT_Dis | DeFT_Ran |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | 1/16 | +14.9 | +3.5 | +21.1 | +35.5 | -45.4 | -21.7 | -68.5 | -77.8 |
| 2x2 | 2/16 | +15.7 | +3.1 | +23.4 | +33.0 | -47.3 | -19.8 | -70.4 | -74.2 |
| 2x2 | 4/16 | +13.0 | +3.2 | +18.4 | +24.3 | -44.9 | -19.6 | -62.4 | -63.6 |
| 2x2 | 8/16 | +3.6 | +1.0 | +5.6 | +7.7 | -20.4 | -7.7 | -33.3 | -28.3 |
| 3x3 | 1/16 | +16.9 | +5.6 | +22.6 | +24.9 | -52.1 | -20.2 | -68.1 | -61.1 |
| 3x3 | 2/16 | +15.2 | +5.2 | +19.9 | +18.8 | -49.7 | -22.0 | -63.0 | -54.8 |
| 3x3 | 4/16 | +12.3 | +4.0 | +16.8 | +15.0 | -44.3 | -22.3 | -59.0 | -47.2 |
| 3x3 | 8/16 | +7.0 | +1.6 | +7.6 | +5.1 | -31.3 | -9.1 | -33.4 | -18.9 |
| 4x4 | 1/16 | +21.0 | +9.5 | +24.8 | +18.0 | -48.2 | -25.9 | -57.8 | -48.9 |
| 4x4 | 2/16 | +18.1 | +7.6 | +21.8 | +15.6 | -49.8 | -25.7 | -60.9 | -43.9 |
| 4x4 | 4/16 | +13.2 | +6.1 | +14.3 | +10.1 | -44.5 | -26.7 | -48.5 | -36.5 |
| 4x4 | 8/16 | +5.9 | +2.4 | +6.5 | +4.2 | -32.9 | -17.3 | -35.5 | -23.3 |

* **All 144 comparisons** (12 cells, four reference rows, THR, LAT and P99) are on the hypothesised side with an
  unadjusted 95 % interval that excludes 0 (X.6). The closest is THR against DeFT_B on 2x2 at 8/16: +1.0 %, with an
  interval that starts just above 0. These numbers are descriptive and unadjusted.
* **DeFT_B is the reference to beat.** It is the best reference for THR in 17 to 31 of the 32 (mask, traffic) cells of
  every (size, rate), and for LAT in 16 to 28; DeFT_P is second (1 to 8 and 4 to 13). At 8/16 the four are close to each
  other and each is the best somewhere (2x2, THR: 5 / 17 / 3 / 7 cells for DeFT_P / DeFT_B / DeFT_Dis / DeFT_Ran).
* **Against DeFT_B:** THR +3.1 to +3.5 % on 2x2, +4.0 to +5.6 % on 3x3 and +6.1 to +9.5 % on 4x4 up to 4/16; +1.0, +1.6
  and +2.4 % at 8/16. LAT -19.6 to -26.7 % up to 4/16; -7.7, -9.1 and -17.3 % at 8/16. P99 -35 to -52 % up to 4/16;
  -13.9, -15.5 and -27.2 % at 8/16.
* **Against DeFT_P:** THR +12.3 to +21.0 % up to 4/16 and +3.6, +7.0, +5.9 % at 8/16. LAT -44.3 to -52.1 %, then -20.4,
  -31.3, -32.9 %. P99 -68.9 to -82.3 %, then -33.2, -51.7, -54.3 %. At 0.5 x Lsat the main row is 1.7 to 4.1 % faster
  (question 5).
* **Against DeFT_Dis and DeFT_Ran** the distance is larger still at the low rates (THR +10 to +36 %, LAT -37 to -78 % up
  to 4/16). DeFT_Ran is the weakest reference on 2x2, DeFT_Dis on 4x4.
* **Every distance shrinks with the rate**, as against the best reference (question 5).
* **In absolute terms** (B.13, means over the masks, both traffic patterns), 4x4 at 1/16: THR 0.0434 flits/node/cycle
  against 0.0383 for DeFT_B and 0.0366 for DeFT_P; LAT 80.9 cycles against 118.6 and 159.3. 4x4 at 8/16: 0.0221 against
  0.0216 and 0.0209; 148.2 cycles against 185.2 and 214.2.

### 9. Random against even patterns at the same rate (rounds 25 and 26)
**Final. At the same share of faulty VLs a random pattern gives a much smaller throughput gain than an even one: +2.1 /
+4.0 / +6.8 % against +7.8 / +13.5 / +22.2 % at 4/16 and +0.7 / +0.6 / +2.7 % against +3.8 / +8.8 / +13.9 % at 8/16 (2x2 /
3x3 / 4x4, uniform traffic). The difference is the uneven spread of the faults, not the round: the random masks that
happen to be even give round 25's numbers** (`report/summary_B.md` B.11; `report/extra_B.md` X.3, X.10).

`CI_heurLA_X_LF` against the best reference, uniform traffic, effect [95 % CI] in per cent (B.11):

| size | share | pattern | masks | mean Lsat | THR | LAT |
|---|---|---|---|---|---|---|
| 2x2 | 4/16 | random (this round) | 16 | 0.0087 | +2.1 [+0.7, +3.5] | -23.5 [-29.4, -17.1] |
| 2x2 | 4/16 | even, one per chiplet (round 25) | 3 | 0.0100 | +7.8 [+6.8, +8.9] | -19.3 [-22.3, -16.1] |
| 2x2 | 8/16 | random (this round) | 16 | 0.0051 | +0.7 [-0.5, +2.0] | -6.5 [-13.8, +1.4] |
| 2x2 | 8/16 | even, two per chiplet (round 25) | 3 | 0.0073 | +3.8 [+1.1, +6.6] | -28.5 [-53.4, +9.9] |
| 3x3 | 4/16 | random (this round) | 16 | 0.0057 | +4.0 [+2.0, +5.9] | -23.1 [-30.4, -15.1] |
| 3x3 | 4/16 | even, one per chiplet (round 25) | 3 | 0.0075 | +13.5 [+9.4, +17.6] | -37.2 [-53.5, -15.3] |
| 3x3 | 8/16 | random (this round) | 16 | 0.0036 | +0.6 [+0.2, +1.0] | -8.2 [-11.4, -5.0] |
| 3x3 | 8/16 | even, two per chiplet (round 25) | 3 | 0.0053 | +8.8 [+6.6, +11.0] | -22.4 [-45.3, +10.1] |
| 4x4 | 4/16 | random (this round) | 16 | 0.0045 | +6.8 [+4.0, +9.7] | -25.6 [-31.9, -18.6] |
| 4x4 | 4/16 | even, one per chiplet (round 25) | 3 | 0.0060 | +22.2 [+14.2, +30.7] | -26.8 [-28.1, -25.5] |
| 4x4 | 8/16 | random (this round) | 16 | 0.0034 | +2.7 [+1.5, +3.9] | -18.8 [-24.1, -13.1] |
| 4x4 | 8/16 | even, two per chiplet (round 25) | 3 | 0.0048 | +13.9 [+3.0, +25.9] | -35.4 [-52.8, -11.5] |

* **How the two rounds are put side by side.** Both with the definitions of this round (best reference per mask and
  metric, unit = mask) and uniform traffic only, because the fault runs of round 25 are uniform. Round 25 has 3 masks
  per line and 5 seeds, this round 16 masks and 2 seeds; with 3 masks an interval has 2 degrees of freedom. Computed this
  way, round 25 gives the numbers of its own report (+7.8 / +13.5 / +22.1 % and +3.8 / +8.8 / +13.9 %) but for one last
  digit.
* **THR:** a random pattern keeps about three tenths of the even pattern's gain at 4/16 (27 to 31 %) and less than a
  fifth at 8/16 (7 to 19 %).
* **LAT:** at 4/16 about the same on 2x2 and 4x4 (-23.5 against -19.3 %, -25.6 against -26.8 %) and smaller on 3x3
  (-23.1 against -37.2 %). At 8/16 smaller on every size (-6.5 / -8.2 / -18.8 against -28.5 / -22.4 / -35.4 %; the
  intervals of round 25 are wide).
* **A random pattern leaves less capacity.** Its mean Lsat is 13 to 32 % below that of the even patterns with the same
  number of faults. An even pattern spreads the loss over the chiplets; a random one puts three faults into some
  chiplets, and the chiplet with the fewest VLs sets the capacity.
* **The even masks among the random ones give round 25's result** (X.10, added after the results were seen). On 2x2,
  two of the 16 random masks of 4/16 have one fault in every chiplet and four of the 16 of 8/16 have two:

  | 2x2 | masks | THR, uniform | LAT, uniform | round 25, the same pattern: THR | LAT |
  |---|---|---|---|---|---|
  | 4/16, even | 2 | +7.6 [-2.6, +18.9] | -25.5 [-32.3, -18.0] | +7.8 | -19.3 |
  | 4/16, not even | 14 | +1.4 [+0.4, +2.3] | -23.2 [-30.0, -15.8] | | |
  | 8/16, even | 4 | +4.5 [+1.9, +7.1] | -25.0 [-41.3, -4.2] | +3.8 | -28.5 |
  | 8/16, not even | 12 | -0.5 [-1.0, +0.0] | +0.7 [-2.0, +3.4] | | |

  Two and four masks are few, and the table was not planned; but it shows that the two rounds agree where they measure
  the same thing. On 3x3 and 4x4 no random mask is even.
* **What this says about round 25.** Its numbers for "25 % and 50 % of the VLs faulty" are the gain for the most
  favourable placement of that many faults: every chiplet keeps three or two VLs to choose from. With random placement
  what matters is how many chiplets are left a single VL (question 6). At 8/16 a random mask has 0.9 of 4, 2.6 of 9 and
  4.6 of 16 such chiplets on average; an even one has none.
* **Hotspot traffic.** Round 25 also ran one faulty VL per chiplet with hotspot traffic: THR +3.3 / +3.2 / +1.9 %, LAT
  -8.0 / -5.2 / -4.1 % (from its report, not computed again here). The hotspot half of this round at the same share
  (4/16, random): THR +3.1 / +2.5 / +3.1 %, LAT -9.7 / -8.3 / -9.7 % (B.3). Under hotspot traffic the placement of the
  faults makes little difference, which fits question 5.

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

## Stated in advance, and what came out
* *Expected: the effect is largest at the low rates on 3x3 and 4x4 and shrinks as the rate grows, because a chiplet with
  one functional VL leaves nothing to choose.* Yes, and the mechanism named is the one the data point to: within one
  rate the masks with such a chiplet lose most of the throughput gain (question 6).
* *Expected: the hotspot half lowers every effect.* For LAT in all 12 cells, for THR in 10 of 12 (question 5).
* *The tests most at risk: 8/16 on every size and 2x2 at every rate.* The two tests that are not significant are 2x2 at
  8/16; the others of the set are supported (question 4).
* *The selection of the best reference favours the reference; it is kept.* It was kept. Its trace is visible where the
  rows are close to each other (question 6).
* *A1 and A2: every check passes. A3: no mismatch.* Both as expected (questions 1 to 3).
* Not expected in this form: how much a single chiplet with one functional VL costs. On 4x4 one such chiplet of sixteen
  takes the throughput gain from about +8 % to +2 to +3 % at the same fault rate. The round-25 numbers for even patterns
  therefore do not carry over to random faults at the same rate (question 9).

## What these results do not show
* 16 masks per size and rate are a sample of a very large space; every interval is over these masks. The model check of
  Part A covers the fault patterns for deadlock, dead ends and livelock, not for performance.
* Two seeds per mask, traffic pattern, load and row, and two traffic patterns. Only the 24 tests of the primary family
  are adjusted; every other number of Part B is descriptive.
* THR is bounded by the last load of the design in about half of the cells (question 4).
* Tables X.9 and X.10 of `report/extra_B.md` were added after the results were seen (`DECISIONS.md`).
* MTR and RC have no performance number under faults, because they cannot deliver every pair (question 10).
