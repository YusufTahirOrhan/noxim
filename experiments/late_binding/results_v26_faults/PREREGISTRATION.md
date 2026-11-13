# Pre-registration v26: fault coverage

Committed together with `masks_v26.json` before any run of Parts A and B (model checks, drain tests, ladders, timing runs and
evaluation runs). Done before it: the regression A0 (`regression.md`: 84 / 84 byte-identical to the ee0e247 build in all
three comparisons). Nothing below depends on a result of this round.

**Nothing is tuned and no row is changed.** The configuration is the one of round 25 (`results_v24_xy/tuning_choice.json`);
the simulator is the ee0e247 build, whose sources are those of ce6ab6a. The analysis below was written before any run.

## Rows
| row | definition |
|---|---|
| `CI_heurLA_X_LF` (**main**) | as in round 25: exit from the LUT, late entry, XY on both layers; the lookahead heuristic with heur_w 2, heur_busy 0, hop_weight_ipos 1, lut_bias 2 on 2x2 and 0 on 3x3 and 4x4; `lookahead_route 1 lookahead_fallback 1 busy_state 1`, decision_delay 0 |
| `CI_heurLA_O_LF` (**second**) | the same with `ipos_tm O1` |

References under faults: DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran. MTR and RC do not run with faults. The arguments of every row are
built by `experiments_v25.row_args`, unchanged.

Options of every simulator run unless stated: pipe_all 2; window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers;
`-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`; `-traffic_rng 1`; one LUT per mask, made with the generator settings of
round 23 (`experiments_v23._gen`: rho of the size, `--entry-model both`).

## Masks (`masks_v26.json`, `masks_v26.md`)
A mask is a set of faulty VLs; a faulty VL is faulty in both directions. Every mask leaves every chiplet a functional VL.
* **Part B:** fault rates 1/16, 2/16, 4/16 and 8/16 of all VLs; n = floor(rate x number of VLs) faulty VLs: 2x2 1 / 2 / 4 / 8,
  3x3 2 / 4 / 9 / 18, 4x4 4 / 8 / 16 / 32. Per (size, rate) 16 distinct masks, drawn uniformly among the masks with exactly n
  faulty VLs and a functional VL in every chiplet: rejection sampling with one `random.Random(2611)`, sizes and rates in this
  order. 2x2 at 1/16: all 16 masks exist and all are taken, in VL order. 192 masks; the order in the file is the order of the
  draw (mask 1 to 16 of a cell).
* **A2** (3x3 and 4x4): set 1 the fault-free mask; set 2 every fault combination of one chiplet (its 14 patterns with one to
  three faulty VLs) with all other chiplets fault-free, 126 and 224 masks; set 3 random masks from the whole space, every
  chiplet drawing one of its 15 patterns uniformly, 200 masks on 3x3 and 60 on 4x4, from a second `random.Random(2611)` (3x3
  first); set 4 the 64 masks of Part B of the size.

---

## Part A: the model check on all fault patterns

Model: `formal/impl_relation_check.py` with the settings of `formal/xy_check.py`: `UP_KEEP = True` (the paper's Up rule: the Up
channel carries the VN the packet has on the interposer, the destination chiplet is VN1), both VNs explored on every
Horizontal -> Down hop of a VN0 packet, rule R3 on the input VN, the F1 source rule. Relations `CI_XY_XY` (the main row) and
`CI_XY_O1` (the second row). The model is not changed in this round.

**Checks per mask and relation**
1. the channel dependency graph (CDG) is acyclic;
2. no reachable state is a dead end;
3. the state graph is acyclic (no livelock); its longest path is reported;
4. **subset:** every edge of the CDG is an edge of the CDG of the fault-free mask of the same relation and size.

A check that fails on any mask is a model-check failure and stops the round. This holds for check 4 as well.

**Controls (the checks must be able to fail).** (a) The negative control of `xy_check.py`: 2x2, fault-free, the fixed pair with XY,
R3 and the F1 source rule removed: the CDG must be cyclic. The same removal is applied to `CI_XY_XY` and `CI_XY_O1` and reported.
(b) For check 4: the fault-free CDG of `CI_XY_O1` is tested against the fault-free CDG of `CI_XY_XY` on 2x2; it must not be a
subset (the VN-split order uses YX dependencies in VN1 that XY does not have).

**A1. 2x2, exhaustive.** All 15^4 = 50,625 masks that leave every chiplet a functional VL, the fault-free one included, both
relations: 101,250 lines in `formal_all_2x2.csv` (mask, relation, faulty VLs, the four checks, longest path, CDG nodes and edges,
CDG edges outside the fault-free CDG). Run in chunks; a chunk that is finished is not run again.

**A2. 3x3 and 4x4.** The four sets above, both relations, the per-destination exploration (`job_lean` semantics): 391 masks on
3x3 and 349 on 4x4. `formal_a2.csv`, one line per size, set, mask and relation.
* **Time rule.** The time of the 4x4 checks is estimated from 24 of them, spread evenly over the list of checks (every 29th
  check of sets 1 to 4 in this order), with the number of processes the checks use. If the estimate for all 4x4 checks exceeds
  4 h, set 3 on 4x4 is reduced to its first 30 masks; this is then stated in `FINDINGS.md`. Nothing else is reduced.

**The argument for set 2, and its two tests.** In the model a packet's states depend on the fault pattern only through (i) the
functional VLs of its destination chiplet, which are its entry candidates, and (ii) its exit VL, which is one functional VL of
its source chiplet; every functional exit VL is explored. If that is so, then
* *first half:* a mask can only remove behaviours, so the dependencies of every mask are dependencies of the fault-free mask.
  Tested by check 4 on every mask of A1 and A2.
* *second half:* the packets to chiplet c behave under a mask M as they do under the mask that keeps only the faults M has in
  chiplet c, except that fewer exits are explored. So set 2 (every pattern of one chiplet, the others fault-free) contains
  every packet behaviour of every mask. Tested directly on 2x2: for 1,000 masks of A1 with faults in at least two chiplets
  (drawn with a third `random.Random(2611)`), both relations and each of the four chiplets c, the reachable states of the
  packets with a destination in chiplet c under M must be a subset of those under M restricted to chiplet c
  (`formal_subset_2x2.csv`).
`FINDINGS.md` gives the argument and says whether the data agree. A failure of the second-half test is not one of the four
checks: it does not stop the round, it refutes the argument, and set 2 is then reported as a sample like set 3.

**A3. Conformance of the model with the simulator.**
* An instrumented copy of the simulator (the copy mechanism of round 25, `results_v25_confirm/hw/tb/patch_vecdump.py`,
  extended; the repository's sources and `bin/noxim` are not changed) records every hop of a head flit: router, layer,
  direction of arrival or injection, VN before, candidate masks before, destination, the set of offered outputs, the output
  taken, VN after, masks after. Every instrumented run must give a statistics file byte-identical to that of `bin/noxim`.
* Every recorded hop is replayed through the Python model (`impl_relation_check.py`, the settings above):
  1. the set of offered outputs equals the set the model offers in that state;
  2. the hop taken (next router, VN, masks) is a transition of the model.
  The relation of the model is `CI_XY_XY` for the main row, `CI_XY_O1` for the second row and the fixed pair with XY
  (`A_fixed_XY`) for DeFT_P.
* **Runs:** the two frozen rows and DeFT_P; 2x2, 3x3, 4x4; six masks per size: fault-free, the mask with the same VL faulty in
  every chiplet (0x1111, 0x111111111, 0x1111111111111111) and mask 1 of each of the four rates of Part B; uniform and hotspot;
  1.0 x Lsat of DeFT_P (the ladders of round 25 for the first two masks, those of Part B for the others); seed 1. If a row and
  size has fewer than 1,000,000 compared hops, seeds 2, 3, ... are added for that row and size until it has.
* **Required: 0 mismatches.** On a mismatch the round stops and reports the state and both answers. Neither the model nor the
  simulator is changed to make it pass. (An error in the new comparison code itself, that is in the dump or in the replay, is
  corrected and recorded in `DECISIONS.md`; the comparison is then run again in full.)

---

## Part B: performance under random VL faults

### Before the runs
* The model check of A2 set 4 (3x3, 4x4) and of A1 (2x2) covers the 192 masks.
* All-pairs drain test of every row of the design on every mask (the protocol of `c_drain` of round 25: one burst of every
  source-destination pair, seed 1, pipe_all 2): `drain_v26.csv`. Every packet must arrive and no dead-end event may occur. A
  FAIL stops the round.

### Design
* **Traffic:** uniform and hotspot, as defined in round 25 (`gen_traffic.py`).
* **Ladder per (mask, traffic):** Lsat of DeFT_P by the D1 rule as run in Part C of round 25: seed 101, pipe_all 2, the LUT of the
  mask; L0 = latency at 0.0002; the coarse sweep on the 0.0005 grid runs upwards and stops after the first rate whose latency
  exceeds 3 x L0; Lsat = the largest swept rate before that, on the 0.0001 grid where the coarse Lsat is at most 0.004 and on the
  0.0005 grid otherwise. Loads 0.5, 1.0, 1.4 and 2.0 x Lsat, rounded to the grid and kept strictly increasing.
  `load_points_v26.json`.
* **Rows:** DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran, `CI_heurLA_X_LF`, `CI_heurLA_O_LF`. **Seeds 151 and 152** (never used before).
* **Runs:** 192 masks x 2 traffic patterns x 6 rows x 4 loads x 2 seeds = 18,432, and the ladders.
* **Time rule.** The time is estimated first from timing runs that are runs of the design and are kept; their results are not
  looked at: seed 151, the 1st and 4th load, masks 1 to 4 of every (size, rate), every row and both traffic patterns (1,152
  runs), with the number of processes the evaluation uses. If the estimate for the whole design exceeds 40 h, this is dropped,
  in this order, until it does not: (1) rate 8/16 on 4x4; (2) masks 13 to 16 of every remaining (size, rate). Nothing else is
  reduced. With (1) the primary family has 22 tests; with (2) a cell has 12 masks.

### Metrics
* **THR:** the largest accepted throughput over the four loads. **LAT** and **P99:** mean and 99th-percentile packet latency at
  1.0 x Lsat of DeFT_P (the 2nd load). **LAT at 0.5 x Lsat:** the 1st load.
* **Dead-end events must be 0 in every run**; one event stops the round.
* **Best reference** per (mask, traffic, metric): the reference row (DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran) with the best
  arithmetic mean of the metric over the two seeds (highest THR, lowest LAT, lowest P99); its per-seed values are the
  reference.
* **Unit = mask.** Value of a mask: V_m = mean over the two traffic patterns and the two seeds of ln(metric_row /
  metric_reference), paired by seed. **Effect per (size, rate)** = 100 x (exp(mean over the masks of V_m) - 1) %. Test:
  two-sided one-sample t test of the V_m of the cell against 0 (15 df with 16 masks); the 95 % interval is the t interval of
  the mean of V_m, transformed the same way.
* A (mask, traffic, seed) for which a run of the row or of a reference row is missing is left out of the comparisons it
  enters; the value of the mask is the mean over what remains.

### Primary family (24 tests, Holm over the 24, alpha = 0.05)
For each size and each rate, `CI_heurLA_X_LF` has higher THR and lower LAT at 1.0 x Lsat than the best reference.
Supported = significant after Holm in the hypothesised direction; a significant effect in the other direction is reported as
against; anything else as not significant.

### Secondary (descriptive: unadjusted, never called significant)
* P99; `CI_heurLA_O_LF` against the best reference and against the main row; each traffic pattern separately.
* The main row against each reference row, DeFT_P in particular.
* The distribution of V_m over the masks of a cell: minimum, quartiles, maximum.
* The number of masks (V_m on the wrong side of 0) and of (mask, traffic) cells (mean over the two seeds on the wrong side) in
  which the main row is behind the best reference in THR or in LAT; the same against DeFT_P.
* The ten worst (mask, traffic) cells in THR and in LAT: the mask, its faults per chiplet, and the values of every row.
* The effect by the largest number of faults in one chiplet, and by the number of chiplets with one functional VL.
* LAT at 0.5 x Lsat against DeFT_P.
* Rates 4/16 and 8/16 next to k = 1 and k = 2 of round 25 (`results_v25_confirm/fault_runs.csv`: the same share of faulty VLs,
  spread evenly; uniform traffic, so the comparison uses the uniform half of this round), computed for both rounds with the
  definitions of this round.
* The number of (mask, traffic, row) cells whose largest accepted throughput is at the last load: THR is then a lower bound
  for that row.
* Ladders with Lsat below 0.001 are listed: L0 is measured at 0.0002, which is then more than a fifth of Lsat.

### B5. Reachability (static, descriptive)
* The analysis of `reach_v10.py` for MTR and RC (the definitions the simulator runs use today: `results_v10/mtr_config.json`
  for MTR, the nearest boundary router for RC), with the rate 8/16 added: share of the inter-chiplet source-destination pairs
  that can be delivered, mean and worst case over up to 1,000 masks per (size, rate), and over the 16 masks of Part B. The masks
  of the rates 1/16, 2/16 and 4/16 are those of `reach_v10.py` (`random.Random(2210)`, so its numbers must come again); the
  masks of 8/16 are drawn with a `random.Random(2611)` of their own.
* For DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran and the two frozen rows: the delivered share and the dead-end counts of the drain tests.

## Stated in advance
* Round 25 (even patterns, uniform traffic): THR +7.8 / +13.5 / +22.1 % at k = 1 (25 %) and +3.8 / +8.8 / +13.9 % at k = 2
  (50 %) on 2x2 / 3x3 / 4x4; with one functional VL in every chiplet the main row is DeFT_P. With one faulty VL per chiplet and
  hotspot traffic: THR +3.3 / +3.2 / +1.9 %, LAT -8.0 / -5.2 / -4.1 %.
* Expected here: the effect is largest at the low rates on 3x3 and 4x4 and shrinks as the rate grows, because a chiplet with
  one functional VL leaves nothing to choose (at 8/16 the masks have 0.9 of 4, 2.6 of 9 and 4.6 of 16 such chiplets on
  average). The hotspot half lowers every effect against the uniform-only numbers of round 25.
* The tests most at risk: 8/16 on every size, and 2x2 at every rate (round 25: THR +1.5 % on 2x2 over eight scenarios).
* The best reference is chosen among four rows from two seeds per cell. This selection favours the reference (the luckier of
  four rows is taken) and so works against the tested row; it is kept as defined.
* A1 and A2: all four checks are expected to pass on every mask. A3: 0 mismatches are expected; a mismatch would mean that the
  model check does not cover the simulated router.

## Not done in this round
No retuning, no new row, no simulator option. MTR and RC are not run under faults (their reachability is reported instead).
The second-half test of the argument is run on 2x2 only.

## Checks of the analysis
The 24 tests of the primary family are computed a second time by a script that shares no code with the report
(`check_v26_family.py`), as in round 25.
