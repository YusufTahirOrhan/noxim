# Pre-registration v27: early against late binding

Committed before any run of Parts B (tuning), C (evaluation) and E (faults), the timing runs included. Done before it: the
regression before and after the code change (`regression_before.md`, `regression.md`: 84 / 84 byte-identical to the d641861
build in all comparisons), the anchor row (`anchor.md`), the unit checks of the new options (`unit_checks.md`) and the drain
tests of the five new rows (`drain_v27.csv`). Their results are summarised under "Gates" below. Nothing below depends on a
result of Part B, C or E.

**The question.** Every reference of rounds 23 to 26 chooses the entry VL without looking at the network (offline LUT,
nearest, random). So those rounds cannot say how much of the main row's gain over DeFT comes from binding the entry VL
**late**, on the interposer, and how much from choosing it by congestion **at all**. This round adds rows that choose the
entry VL by congestion but bind it early: at injection, or at the Down move.

**Nothing of the frozen configuration is retuned and no existing row is changed.** `DeFT_P` and the main row are built by
`experiments_v25.row_args`, with the values round 24 chose. The simulator is the d641861 build plus four options that are off
by default.

## Rows
| row | the entry VL is chosen | from what | definition |
|---|---|---|---|
| `DeFT_P` | offline | nothing at run time | as round 25: `-routing DEFT -deft_lut_entry dst` |
| `CI_heurLA_X_LF` (**main**) | on the interposer, hop by hop | local occupancies, two hops ahead | as round 25: exit from the LUT, late entry, XY on both layers; `-sel DEFT_HEUR` with heur_w 2, heur_busy 0, hop_weight_ipos 1, heur_lookahead 1, lut_bias 2 on 2x2 and 0 on 3x3 and 4x4; `lookahead_route 1 lookahead_fallback 1 busy_state 1`, decision_delay 0 |
| `EB_vl` | at injection, once | the occupancy at every entry VL of the destination chiplet at that moment | `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle -deft_lb oracle_beta B -deft_lb chip_tm XY -deft_lb ipos_tm XY`; B tuned in Part B |
| `EB_route` | at injection, once | the queues on the whole route to every entry VL at that moment | `EB_vl` with `-deft_lb oracle_scope route`; its own tuned B |
| `EB_vl64` | at injection, once | the occupancies of `EB_vl`, sampled every 64 cycles | `EB_vl` with `-deft_lb oracle_period 64`; its own tuned B |
| `EB_down` | when the head moves Down, once | what the main row knows at its first decision | the main row with `-deft_lb entry_commit down` |
| `LB_noVLrep` | as the main row | as the main row, without the reports across the VLs | the main row with `-deft_lb up_report 0` |

* **The injection-time choice** (`chooseMasks`): cost(e) = hops from the source through the LUT's exit VL and e to the
  destination + B x occupancy(e); the cheapest entry VL, ties at random. occupancy(e) for `EB_vl`: the flits in all input
  buffers of the interposer router below e plus those in the Up input buffer of the chiplet router above e. For `EB_route`:
  the flits in the input buffers the packet will pass on the interposer (XY from the router below the exit VL to the router
  below e: at every hop the buffer of the port it arrives through) plus the Up input buffer above e. For `EB_vl64`: the
  occupancy of `EB_vl` as it was at the start of the last cycle that is a multiple of 64. The choice is made when the head
  flit leaves the source queue. The information is global, without delay (`EB_vl`, `EB_route`) and costs no wires: these
  rows are source-side selection in its most favourable form.
* **`EB_down`:** when the head is forwarded onto its Down VL with more than one entry candidate, every candidate v is
  given the cost the frozen selection gives, at the interposer router below and at that moment, to the output that leads
  towards v (`localCost + 1 + bestContinuation`, heur_w 2), plus D (lut_bias) if v is not DeFT-P's entry VL; the cheapest
  candidate is kept, ties at random. From there the packet has one entry candidate.
* **`LB_noVLrep`:** in the lookahead term of the Up output of an interposer router, the occupancies of the chiplet router
  above the VL are not used (they would have to be reported across the VL: 12 wires per VL). The local cost of the Up
  output and everything on the interposer are unchanged.
* The exit VL is the LUT's in every row. With one entry candidate and XY, the paths of the four `EB` rows are DeFT's paths
  for the chosen entry VL.
* `EB_down` and `LB_noVLrep` take the frozen parameters of the main row. Nothing is tuned for them.

## Options of every run of Parts B, C and E
* pipe_all 2; window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers; LUTs `luts/v23`, one per mask;
  `-traffic_rng 1`; every row with `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`.
* Observation only: `-deft_lb count_vl 1` on DeFT_P; `-deft_lb hop_stats 1` on every DEFT_LB row; `-deft_lb entry_stats 1`
  on the main row and on every new row (it counts the Up moves, those on a VL that is not DeFT-P's entry VL, and the time
  since the generation of the packet at the Up move and at the injection). `unit_checks.md` shows on 18 runs that the main
  row gives the same statistics with and without it.

## Gates (done; results)
* **Regression** (`regression_before.md`, `regression.md`): the 84-configuration set is byte-identical to the d641861 build
  before the change and after it, with the options absent and with every option given at its default.
* **Anchor** (`anchor.md`): `-routing DEFT_LB -deft_lb exit lut -deft_lb entry lut` with XY in both layers and DeFT-P's
  options gives DeFT_P's results on the six fault-free scenarios at 1.0 x Lsat, seed 101, on all three sizes: 18 / 18 runs
  identical in every performance field of the summary, in the delay statistics and in the packets per VL. So the `EB`
  rows are compared with DeFT_P itself; no `EB_lut` row is added to Part C.
* **Unit checks** (`unit_checks.md`): `entry_stats` changes no statistic of the main row (18 / 18 runs identical).
  `entry_commit down` changes nothing when every chiplet has one functional VL (3 / 3 identical). The output of the
  committed candidate is a cheapest output of the main row's selection at the same router and moment in 12,000 of 12,000
  sampled heads on 3x3 and 4x4 (554 of them ties); on 2x2, where D = 2 is charged differently, in 5,977 of 6,000. No hop of
  an `EB` run offers more than one output.
* **`EB_vl` with `oracle_beta 0`** (description): the entry VL of fewest hops is DeFT-P's entry VL for 41 to 53 % of the
  packets (fault-free, six scenarios).
* **Drain tests** (`drain_v27.csv`): all-pairs drain tests of the five new rows on six masks per size (fault-free, the
  same VL faulty in every chiplet, and mask 1 of each of the four fault rates of round 26); `oracle_beta 1` for the three
  rows that are tuned later. **90 / 90 pass**: every packet delivered, no dead-end event, no hop of an `EB` run offers more
  than one output. The three tuned rows are tested again with their chosen values after Part B (`drain_v27_tuned.csv`); a
  failure there stops the round before Part C.

---

## Part B: tuning of `oracle_beta` (seeds 101, 102)
The early rows must be at their best, or the comparison says nothing. The rule is that of round 24
(`results_v24_xy/tuning.md`), written out in `tuning_v27.md` before any tuning run:
* sizes 2x2 and 4x4 (3x3 takes the 4x4 value); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and
  uniform with one faulty VL per chiplet); ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat); seeds 101 and 102; DeFT-P on
  the same loads and seeds;
* score = mean over the scenarios and seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`;
* grid: `oracle_beta` in {0.125, 0.25, 0.5, 1, 2, 4, 8}, separately for `EB_vl`, `EB_route` and `EB_vl64`; the value with the
  largest score is chosen; if it lies at an end of the grid, the grid is extended at that end by factors of 2, one value at a
  time, at most three times;
* the main row runs on the same loads and seeds with its frozen parameters and its score is reported next to them.

The chosen values are added to this file as an addendum before any run of Part C.

---

## Part C: evaluation

### Design
* **Scenarios:** the six fault-free scenarios of round 25: uniform, localized, hotspot, chipperm, chiptrans, movinghot.
  **Sizes** 2x2, 3x3, 4x4. **Loads:** the nine points (0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat of DeFT-P) of
  `results_v25_confirm/load_points_v25.json`. **Seeds 161-170** (never used before).
* **Rows:** the seven rows of the table. If the anchor row is not identical to DeFT_P, it joins them as `EB_lut`.
* **Runs:** 6 scenarios x 3 sizes x 9 loads x 10 seeds x 7 rows = 11,340. `eval_runs.csv` has the columns of
  `results_v25_confirm/eval_runs.csv`, followed by the counters of `entry_stats` and `entry_commit`.
* **Time rule.** Parts C and E are timed first: for Part C the 378 runs of seed 161 at the 2nd, 5th and 9th load of every
  cell, for Part E the 144 runs of seed 151 at the 1st and 4th load of masks 1 to 4 of every size (runs of the designs, kept;
  their results are not looked at; each set has the machine to itself). If the two estimates together exceed 30 h, the
  following are dropped in this order until they do not: (1) Part E; (2) `EB_vl64`; (3) `LB_noVLrep`; (4) seeds 166-170.

### Metrics
* **THR:** the largest accepted throughput over the nine loads. **LAT** and **P99:** mean and 99th-percentile packet
  latency at 1.0 x Lsat of DeFT-P (the 4th load). **LAT at a load:** the mean latency at that point of the ladder.
* **Effect per size** of row A against row B = 100 x (exp(mean over the seeds of R_s) - 1) %, where R_s = mean over the six
  scenarios of ln(metric_A / metric_B) for seed s, the two rows paired by scenario and seed. Test: two-sided one-sample t
  test of the ten R_s against 0 (9 df); the 95 % interval is the t interval of the mean of R_s, transformed the same way.
* Dead-end events must be 0, and no hop of an `EB` row may offer more than one output, in every run.

### Primary family (18 tests, Holm over the 18, alpha = 0.05)
For each size and each of `EB_vl`, `EB_route`, `EB_down`: the main row has higher THR, and lower LAT at 1.0 x Lsat, than
that row. Supported = significant after Holm with the main row ahead. A significant effect with the early row ahead is
reported as against; anything else as not significant. **An early row that is level with the main row or ahead of it is a
result and is reported as such.**

### Secondary (descriptive; unadjusted p values, never called significant)
* every row against DeFT_P (THR, LAT, P99), and the **share of the main row's gain** that each early row reaches: per size,
  (mean of R_s of the row against DeFT_P) / (mean of R_s of the main row against DeFT_P), for THR and for LAT, with the
  range of the ten per-seed shares;
* the main row against the better of `EB_vl` and `EB_route`, chosen per (size, scenario, metric) as the one with the better
  mean over the ten seeds;
* the main row against `EB_vl64`; `EB_vl64` against `EB_vl`;
* `LB_noVLrep` against the main row: THR, LAT, P99, LAT at 0.2 and 0.5 x Lsat;
* each scenario separately; the (size, scenario, metric) cells in which an early row is ahead of the main row, with the
  unadjusted interval over the seeds;
* LAT at 0.2, 0.5, 0.8, 1.2 and 1.4 x Lsat for every row against DeFT_P and against the main row;
* entry VLs: `vl_imbalance` and `vl_max_up`; the share of packets that move Up on a VL that is not DeFT-P's entry VL; hops
  per packet (head-flit forwards per delivered packet; for DeFT_P from the anchor row if it is identical);
* for the three injection-time rows at 1.0 x Lsat: the age of the choice when the packet moves Up, as the mean time since
  generation at the Up move minus the mean time since generation at the injection (two means over the measured window,
  from counters; an estimate, see `DECISIONS.md`);
* the number of runs in which the largest accepted throughput is at the last load (THR is then a lower bound).

### Stated in advance
Written after the smoke runs named in `DECISIONS.md` (one run per new row on 2x2 and 4x4, uniform, 1.0 x Lsat, seed 101,
`oracle_beta` 0 and 1), which I looked at; and before any tuning or evaluation run.
In those runs the anchor row was identical to DeFT_P; `EB_vl` with `oracle_beta` 0 and 1 and `EB_vl64` with 1 were behind
DeFT_P in latency on both sizes; `EB_route` with 1 was between DeFT_P and the main row on 4x4 and slightly behind DeFT_P on
2x2; `EB_down` was between DeFT_P and the main row on 2x2 and far behind DeFT_P on 4x4; `LB_noVLrep` was within 1 % of the
main row. These are single runs of one scenario with untuned values, and they shaped what follows.
* **`EB_down`.** The prompt of the round expects it close to DeFT_P, because what the Down router knows says little about
  the entry VLs. I expect it to be **behind DeFT_P on 3x3 and 4x4**, for a related reason: the cost of a candidate is its
  remaining hop count plus the queues of its first two interposer hops. Unless those queues differ, the cheapest candidate
  is the one of fewest hops, so the commit is close to "the nearest entry VL", and that gives up the balance over the entry
  VLs that DeFT-P's LUT has by construction. On 2x2 the first hops are close to every entry VL, so it should lie between
  DeFT_P and the main row. All six tests of the main row against `EB_down` are expected to be supported.
* **`EB_vl`.** With a small `oracle_beta` it is the nearest entry VL again and behind DeFT_P; the tuning should move it to
  a larger value. I expect the tuned row to be ahead of DeFT_P where the entry VLs are unevenly loaded (hotspot,
  movinghot) and about level with it elsewhere, and behind the main row in THR and LAT on every size. Whether it is ahead
  of DeFT_P over the six scenarios is open.
* **`EB_route`** should be the better of the two injection-time rows: it looks at the queues the packet will meet, which is
  what the main row looks at hop by hop. I expect it between DeFT_P and the main row on 3x3 and 4x4, with a third to two
  thirds of the main row's gain, and close to DeFT_P on 2x2.
* **`EB_vl64`** should be behind `EB_vl`: every source of the network reads the same sample for 64 cycles and they send to
  the same "empty" VL together.
* **`LB_noVLrep`** should be within 1 % of the main row in THR and within about 2 % in LAT: the reports across the VLs buy
  little, because the local cost of the Up output already holds the credit count of the Up link.
* **Tests most at risk:** the main row against `EB_route` on 2x2 (both metrics), where the main row's own gain is smallest.
* **Part E:** under faults the order of the rows stays; with fewer entry VLs to choose from, the distances shrink.
* **If an early row is level with the main row or ahead of it, that is a result and is reported as such.** In that case
  the gain of rounds 23 to 26 would be a gain of congestion-aware choice, not of late binding.

---

## Part D: latency at every load (no new runs)
From `results_v25_confirm/eval_runs.csv` (six fault-free scenarios, seeds 121-130): the mean latency of the main row
against the best of DeFT_P, DeFT_B, MTR, RC and XY_SP at each of the nine loads. The best reference is chosen per
scenario, size and load: the reference with the lowest mean latency over the ten seeds at that load; its per-seed values
are the reference. Effect per size and load as in Part C (R_s over the six scenarios; interval over the ten seeds). One
table per size, with the reference that is best at each load and the accepted share of the offered load of every row at
every load. No test.

---

## Part E: the early rows under random VL faults (descriptive)
* The 48 masks of rate 4/16 of round 26 (`results_v26_faults/masks_v26.json`, 16 per size), uniform and hotspot traffic,
  the four loads of `results_v26_faults/load_points_v26.json`, seeds 151 and 152: the design of round 26.
* **New runs:** `EB_vl`, `EB_route`, `EB_down` with the values of Part B: 3 x 768 = 2,304. `fault_runs.csv` has the columns of
  `results_v26_faults/fault_rate_runs.csv`, followed by the counters of this round.
* **Reused:** DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran and the main row from `results_v26_faults/fault_rate_runs.csv`. First DeFT_P
  and the main row are run again on masks 1 and 2 of every size with the new build and the row definitions of round 26, and
  must be identical to the file in every column (`reuse_check.md`). If they are not, the five reused rows are run again in
  full and that is reported.
* **Effects** as in round 26, unit = mask: the value of a mask is the mean over the two traffic patterns and the two seeds
  of ln(metric_row / metric_reference), paired by seed; the effect of a size is the mean over its 16 masks, as a
  percentage, with the 95 % t interval over the masks. THR = the largest accepted throughput over the four loads; LAT and
  P99 at 1.0 x Lsat of DeFT-P on the mask. Each early row against the main row, against DeFT_P and against the best DeFT
  variant (per mask, traffic and metric the best of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran by the mean of the two seeds).
  No test.
* Also: the share of the main row's gain over DeFT_P that each early row reaches; the same effects for the masks without
  and with a chiplet that is left one functional VL (the property round 26 found to decide the main row's gain); each
  traffic pattern separately.

## Not done in this round
No retuning of the frozen configuration, no change to an existing row, no new proof and no new model check (the new rows
restrict the checked relation; see `FINDINGS.md`). `EB_vl64` and `LB_noVLrep` are not run under faults.

## Checks of the analysis
The 18 tests of the primary family are computed a second time by a script that shares no code with the report
(`check_v27_family.py`), as in rounds 25 and 26.
