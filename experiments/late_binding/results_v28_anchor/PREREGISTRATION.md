# Pre-registration v28: the strongest early binder

Committed before any run of Parts B (tuning), C (evaluation), D (faults) and E (the reports across the VLs under faults), the timing
runs included. Done before it: the regression before and after the code change (`regression_before.md`, `regression.md`), and the
gates of the new rows (`anchor.md`, `repro_v27.md`, `unit_checks.md`, `drain_v28.csv`). Their results are summarised under "Gates" below.
The reuse check of the rows of round 26 (`reuse_check.md`) runs while this file is committed; it gates Parts D and E only. Nothing below
depends on a result of Part B, C, D or E.

**The question.** Round 27 found that without faults the main row's gain over DeFT needs late binding: rows that choose the entry VL
by congestion and bind it early were behind DeFT_P outside hotspot traffic. But those rows were a weak class of early binders, for
two reasons that round 27 names itself: their family does not contain DeFT (with any `oracle_beta` they leave DeFT-P's balanced
table), and they herd (every source reads the same state and nothing counts the packets already on their way to a VL). A reviewer
will say that a sensible early binder is never worse than DeFT. This round builds the strongest early binder we can and gives it the
same tuning as the main row: ideal information (global, instantaneous, free), a count of the packets already bound to each VL, and an
anchor at DeFT-P's entry VL with a threshold, so that the family contains DeFT_P itself. The question is the one of round 27: **how
much of the main row's gain can a congestion-aware choice reach if it is bound early?** Either answer is a result. If the best early
binder reaches the main row, the statement becomes "the main row gets from local information what an early choice only gets from
global knowledge", and the row with old information says what that knowledge costs.

Also in this round: the main row without the occupancy reports across the VLs (`LB_noVLrep`) under random VL faults. Without faults the
reports buy nothing (round 27, question 11). If that holds under faults, the hardware loses 12 wires per VL.

**Nothing of the frozen configuration is retuned and no existing row is changed.** DeFT_P and the main row are built by
`experiments_v25.row_args` with the values round 24 chose; `EB_down_t` and `LB_noVLrep` are rows of round 27 with their parameters as
round 27 defined them, except the `lut_bias` of `EB_down_t`, which is tuned here. The simulator is the b164e9e build plus the options of
`DeftLateBinding.h`, "v28", all off by default.

## Rows
| row | the entry VL is bound | from what | definition |
|---|---|---|---|
| `DeFT_P` | offline | nothing at run time | as round 25: `-routing DEFT -deft_lut_entry dst` |
| `CI_heurLA_X_LF` (**main**) | on the interposer, hop by hop | local occupancies, two hops ahead | as round 25 (frozen) |
| `EB_best` | at injection, once | the state of the whole network at that moment, and the packets already bound to each VL | the member of the early family with the best tuning score, per size (Part B) |
| `EB_best64` | at injection, once | the same, sampled every 64 cycles | `EB_best` with `oracle_period 64` (occupancies and pending counts up to 64 cycles old), T tuned again |
| `EB_down_t` | at the Down move, once | what the main row knows at its first decision on the interposer | `EB_down` of round 27 (the main row with `entry_commit down`) with its own tuned `lut_bias` |
| `LB_noVLrep` | as the main row | as the main row, without the reports across the VLs | as round 27 (`-deft_lb up_report 0`); Part E only |
| `EB_inf`, `EB_down_inf` (anchors) | at injection / at the Down move | nothing: DeFT-P's entry VL for every packet | the T = infinity members of the two families (`oracle_bias 1e9`, `lut_bias 1e9`); Parts C and D (see "The anchors") |

### The early family
An injection-time row `EBf(S, P, B, T)` chooses the entry VL e of least

    cost(e) = hops(e) + B x ( occ_S(e) + P x pending(e) ) + B x T x [ e is not DeFT-P's entry VL ]

* hops(e): the hop term of `chooseMasks`, unchanged (the exit VL from the LUT).
* occ_S(e): S = `vl`: `occEntry(e)` (all input buffers of the interposer router below e and the Up input buffer above it); S = `route`:
  `occRoute(v, e)` (the input buffers the packet will pass on its XY route on the interposer from below its exit VL v to below e, and the
  Up input buffer above e). As in round 27.
* pending(e): the flits of the packets that were bound to e at injection and whose head has not yet moved Up on e. P is 0 or 1.
* T: a threshold in flits. DeFT-P's entry VL (the LUT's `entries_by_destination` entry of the destination) is kept unless another VL is
  better by more than T flits and the difference in hops. T = 0 with P = 0 is a row of round 27; T = infinity is DeFT_P's choice of the
  entry VL for every packet (the anchor gate: DeFT_P is a member of the family, score 0).
* Ties at random, as in round 27 (one draw from `rand()` per injection).
* Command line: `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle -deft_lb oracle_scope S -deft_lb oracle_pending P
  -deft_lb oracle_beta B -deft_lb oracle_bias (B x T) -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_lb hop_stats 1 -deft_lb entry_stats 1`,
  with DeFT-P's VN options; `EB_best64` adds `-deft_lb oracle_period 64`.
* The information is global, without delay (`EB_best`) and costs no wires: source-side selection in its most favourable form.

### `EB_down_t`
`EB_down` of round 27: the main row until the head moves Down; then every entry candidate v gets the cost the frozen selection gives,
at the interposer router below and at that moment, to the output that leads towards v, plus D if v is not DeFT-P's entry VL; the
cheapest is kept (ties at random) and the packet has one entry candidate from there. D = `lut_bias`, which in the frozen main row is 2
on 2x2 and 0 on 3x3 and 4x4; here it is tuned for this row. Everything else is the frozen main row. D = infinity is DeFT_P's routing
(the anchor gate).

### The anchors
The T = infinity members (`oracle_bias 1e9`, and `lut_bias 1e9` for `EB_down`) take DeFT-P's entry VL for every packet. They are not
byte-identical to DeFT_P (`anchor.md`): every router's crossbar arbitration draws from `rand()`, and the injection-time choice draws from it
once per packet (the commit at the Down move once per commit), so every later arbitration draw is shifted. With their tie-breaks on a stream
of their own (the diagnostic `tie_stream 1`) both are identical to DeFT_P in every run of the gate. So DeFT_P's routing and timing are
members of both families, and the anchor rows differ from DeFT_P by the sequence of the arbitration draws only. As the prompt asks when an
anchor is not identical, the tuned rows are compared with the anchor rows as well as with DeFT_P:
* `EB_inf` = EBf(S, P, B, infinity) with the S, P and B of `EB_best` (at T = infinity the results do not depend on S, P, B or
  `oracle_period`: `anchor.md`, so it is the anchor of `EB_best` and of `EB_best64`); `EB_down_inf` = `EB_down` with `lut_bias 1e9`,
  the anchor of `EB_down_t`.
* Both run in Part C (1,620 runs each) and in Part D (both rates, 768 runs per row and rate). In the time rule they are dropped first,
  in Part D only (`DECISIONS.md`).
* DeFT_P stays the reference of every share; the anchors give each tuned row a second comparison, with the T = infinity member of its
  own family.

## Options of every run of Parts B, C, D and E
* pipe_all 2; window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers; LUTs `luts/v23`, one per mask; `-traffic_rng 1`; every
  row with `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`.
* Observation only: `-deft_lb count_vl 1` on DeFT_P; `-deft_lb hop_stats 1` on every DEFT_LB row; `-deft_lb entry_stats 1` on the main row
  and on every new row (round 27, `unit_checks.md`: the main row gives the same statistics with and without it).
* Dead-end events must be 0 in every run, and no hop of an early row (`EB_best`, `EB_best64`, `EB_down_t`, the anchors, every tuning
  configuration) may offer more than one output.

## Gates (done; results)
* **Regression** (`regression_before.md`, `regression.md`): the 84-configuration set is byte-identical to the b164e9e build before the change
  (A0) and after it (A1), with the options absent and with every option of rounds 23 to 28 given at its default (the diagnostics
  `pending_check 0` and `tie_stream 0` included).
* **The anchors** (`anchor.md`): both T = infinity members take DeFT-P's entry VL for every packet in all 21 runs (six fault-free scenarios at 1.0 x Lsat with
  seed 101 and mask 1 of rate 4/16 with seed 151, three sizes) and are byte-identical to DeFT_P in none; with their tie-breaks on a stream of
  their own (`tie_stream 1`) both are identical to DeFT_P in 21 / 21. Mean of the 21 runs against DeFT_P: `EB_inf` THR -0.04 %, LAT -0.9 %,
  P99 -1.7 %; `EB_down_inf` THR -0.13 %, LAT -0.2 %, P99 -1.9 % (single runs differ by up to 10 % in LAT at 1.0 x Lsat: the noise of the
  arbitration sequence near saturation). EBf(vl, 0, 0.5, infinity) with `oracle_period 64` is identical to EBf(route, 1, 1, infinity) in
  21 / 21. So DeFT_P's routing and timing are members of both families; the anchor rows differ from DeFT_P by the sequence of the
  arbitration draws only, and they join Parts C and D ("The anchors" above).
* **Round 27 reproduced** (`repro_v27.md`): **320 / 320 runs identical** in every column of `results_v27_early/tune_runs.csv`: `EB_vl_b1` = EBf(vl, 0, 1, 0) and
  `EB_route_b4` = EBf(route, 0, 4, 0) with the arguments of this round (`oracle_pending 0` and `oracle_bias 0` given explicitly), and DeFT_P
  and the main row, on all 40 tuning cells of 2x2 and of 4x4. So the 8 members with P = 0 and T = 0 and the denominators of every score are
  taken from round 27's file.
* **Unit checks** (`unit_checks.md`): all pass. (1) The pending counters equal a scan of the network that does not use them, in total and per VL, at cycles
  3000, 6000 and 9000, in 12 / 12 runs (EBf(route, 1, 1, 4), EBf(vl, 1, 1, 4) and the same two with `oracle_period 64`, on 2x2, 3x3 and 4x4,
  uniform traffic at 1.0 x Lsat); 224 to 2,216 flits are bound and on their way at a check. (2) `pending_check` reads only: 12 / 12 runs
  identical with and without it. (3) `oracle_period 64` takes 156 samples in a run, one every 64 cycles. (4) A description, read after
  `stated_in_advance.md` was committed (single runs on 4x4 at 1.0 x Lsat, seed 101, EBf(route, P, 1, T)): with growing T the share of
  packets off DeFT-P's entry VL falls from 63 to 66 % (T = 0) to 36 % (uniform, T = 8), 8 % (T = 32) and 0 % (T = infinity). The mean
  latency under uniform traffic is 94 to 103 cycles with the pending count for T from 0 to 32, 120 cycles without it (T = 0), and 146 to
  147 cycles at T = infinity and for DeFT_P; under hotspot traffic 68 to 70 cycles against 94 to 98. These single runs suggest that the
  count of the packets already bound buys more than I wrote in `stated_in_advance.md`; the expectations stay as they were written.
* **Drain tests** (`drain_v28.csv`): **90 / 90 pass**: EBf(route, 1, 1, 4), EBf(vl, 1, 1, 4), the same two with `oracle_period 64`, and `EB_down` with
  `lut_bias 4`, on six masks per size (fault-free, the same VL faulty in every chiplet, and mask 1 of each of the four rates of round 26):
  every packet delivered, the network empties, no dead-end event, no hop that offers more than one output, and every pending counter is 0
  at the end (the four rows with `oracle_pending 1`). The tuned rows are tested again after Part B (`drain_v28_tuned.csv`); a failure there
  stops the round before Part C.
* **Reuse check of Parts D and E** (`reuse_check.md`): running when this file was committed (768 runs: DeFT_P and the main row as round 26 defined
  them, on masks 1 and 2 of every rate and size, compared with `results_v26_faults/fault_rate_runs.csv` in every column). It gates Parts D
  and E only: no run of Part D or E starts before it has passed (`chain_v28c.sh` checks it). If a run is not identical, the five reused
  rows are run again in full on the masks of Parts D and E, and that is reported.
* **Safety (A3).** I agree, after reading the code, that every new row binds one functional entry VL, at injection (`EB_best`, `EB_best64`,
  the anchor `EB_inf`) or at the Down move (`EB_down_t`, `EB_down_inf`), and that the new options change only which one:
  * `oracle_bias` and `oracle_pending` enter the cost in `chooseMasks` and nothing else; the candidates are the pairs (v, e) with v the
    LUT's exit VL and e a functional VL of the destination chiplet (`functionalMask`), and the pick is one of them. `oracle_period`
    with scope route changes which buffer fills the cost reads (the sample instead of the live ones), not the candidates. So the relation
    of every injection-time row is the fixed-pair relation `A_fixed_XY` of round 27, which explores every functional (exit, entry) pair.
  * `EB_down_t` with any `lut_bias` (1e9 included): `lut_bias` enters the cost in `commitEntry` (and in `selectHeuristic`, where for this
    row every hop offers one output: the exit is the LUT's, and after the commit the entry mask has one candidate); the commit writes
    `bit(v)` for a member v of the entry mask. The argument of round 27 (`results_v27_early/FINDINGS.md`, A3) holds unchanged.
  * The diagnostics read only (`pending_check`, unit check 2) or move a tie-break to another random stream (`tie_stream`; gates only).
  * Checked by simulation in every run of the round: no hop of an early row offers more than one output, no dead-end event.

---

## Part B: tuning (seeds 101, 102; the rule of round 24)
The rule is written out in `tuning_v28.md` ("The rule") before any tuning run; in short:
* The rule of `results_v24_xy/tuning.md`, unchanged: sizes 2x2 and 4x4 (3x3 takes the 4x4 choice); the five tuning scenarios (uniform,
  hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet); ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x
  Lsat); seeds 101 and 102; DeFT-P on the same loads and seeds; score = mean of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 /
  LAT0.5_P)`. 80 runs per configuration. DeFT_P scores 0.
* **B1, the early family.** S in {vl, route} x P in {0, 1} x B in {0.5, 1, 2, 4} x T in {0, 2, 4, 8, 16}: 80 configurations. The 8 with
  P = 0 and T = 0 are rows of `results_v27_early/tune_runs.csv` and are taken from there; 72 x 80 = 5,760 new runs. Extension per size
  and sub-family (S, P): while its best configuration has the largest T run so far (16 at first), T is doubled (up to 128) for every B
  of the sub-family; if its best B is 0.5 or 4, B / 2 or 2 B is added for every T, once. Of two equal scores the larger T.
* **`EB_best`** per size = the configuration with a finite T and the largest score over the whole family; of two equal scores the one with
  the larger T. If its score is below 0, the best member of the family is DeFT_P itself (T = infinity): that is said in the first line of
  the answer to question 2, the finite configuration stays `EB_best` so that there is a row to run, and the main row is compared with the
  better of `EB_best` and DeFT_P wherever a share is reported.
* **B2, `EB_best64`:** S, P and B of `EB_best`, `oracle_period 64`, T in {0, 2, 4, 8, 16, 32}, extended as above (64, 128): 480 runs.
* **B3, `EB_down_t`:** `lut_bias` in {0, 1, 2, 4, 8, 16} on both sizes (32, then 64, if the best is the largest): 480 runs. A `lut_bias` of
  infinity is DeFT_P's routing; the rule for a best score below 0 is that of B1. B3 runs in the batches of B1 (`DECISIONS.md`).
* Reported: the full table; the best configuration of each of the four sub-families; the score of each by scenario; DeFT_P (score 0) and
  the main row on the same loads and seeds (the runs of round 27, `repro_v27.md`). What the anchor buys (the best member with T = 0
  against the best member over all T) and what the pending count buys (the best member with P = 0 against the best with P = 1).
* The chosen configurations are added to this file as an addendum before any run of Parts C and D, and the drain tests are run again with
  them (`drain_v28_tuned.csv`); a failure there stops the round before Part C.

---

## Part C: evaluation without faults

### Design
* **Scenarios:** the six fault-free scenarios of round 25: uniform, localized, hotspot, chipperm, chiptrans, movinghot. **Sizes** 2x2, 3x3,
  4x4. **Loads:** the nine points (0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat of DeFT-P) of
  `results_v25_confirm/load_points_v25.json`. **Seeds 171-180** (never used before).
* **Rows:** `DeFT_P`, the main row, `EB_best`, `EB_best64`, `EB_down_t`: 5 x 1,620 = 8,100 runs; and the anchor rows that are not
  identical to DeFT_P (see "Gates"), 1,620 runs each. `eval_runs.csv` has the columns of `results_v27_early/eval_runs.csv`, followed by
  the counters of this round.

### Metrics, effects and tests (as round 27)
* **THR:** the largest accepted throughput over the nine loads. **LAT** and **P99:** mean and 99th-percentile packet latency at 1.0 x Lsat of
  DeFT-P (the 4th load). **LAT at a load:** the mean latency at that point of the ladder.
* **Effect per size** of row A against row B = 100 x (exp(mean over the seeds of R_s) - 1) %, where R_s = mean over the six scenarios of
  ln(metric_A / metric_B) for seed s, the two rows paired by scenario and seed. Test: two-sided one-sample t test of the ten R_s against 0
  (9 df); the 95 % interval is the t interval of the mean of R_s, transformed the same way.
* **Share of the main row's gain** that a row reaches, per size and metric: (mean of R_s of the row against DeFT_P) / (mean of R_s of the
  main row against DeFT_P), with the range of the ten per-seed shares; for all six scenarios, for hotspot alone (R_s over the one scenario)
  and for the other five.

### Primary family 1 (12 tests, Holm over the 12, alpha = 0.05)
For each size and each of `EB_best` and `EB_down_t`: the main row has higher THR, and lower LAT at 1.0 x Lsat, than that row. Supported =
significant after Holm with the main row ahead. A significant effect with the early row ahead is reported as against; anything else as
not significant. **An early row that is level with the main row or ahead of it is a result and is reported as such.**

### Secondary (descriptive; unadjusted p values, never called significant)
* every row against DeFT_P (THR, LAT, P99) and the share of the main row's gain it reaches, per size; the same for hotspot traffic alone and
  for the other five scenarios together; if a chosen configuration scored below 0 in the tuning, also the share of the better of that row
  and DeFT_P (chosen per size, scenario and metric by the mean over the seeds);
* each tuned row against its anchor (`EB_best` and `EB_best64` against `EB_inf`, `EB_down_t` against `EB_down_inf`) where the anchors run;
* each scenario separately; the (size, scenario, metric) cells in which an early row is level with or ahead of the main row, with the
  unadjusted interval over the seeds;
* `EB_best64` against `EB_best`;
* LAT at 0.2, 0.5, 0.8, 1.2 and 1.4 x Lsat for every row against DeFT_P and against the main row;
* counters at 0.5 and 1.0 x Lsat: the share of packets off DeFT-P's entry VL (by scenario), `vl_imbalance`, hops per packet, wait at the
  source, time from injection to the Up move;
* for orientation only (other seeds, other design): the rows of round 27 against DeFT_P next to the rows of this round against DeFT_P;
* the number of runs in which the largest accepted throughput is at the last load (THR is then a lower bound).

---

## Part D: the early rows under random VL faults

### Design
* The design of round 26: the 48 masks of rate 1/16 and the 48 of rate 4/16 (`results_v26_faults/masks_v26.json`, 16 per size and rate),
  uniform and hotspot traffic, the four loads of `results_v26_faults/load_points_v26.json` (0.5, 1.0, 1.4, 2.0 x Lsat of DeFT-P on the mask),
  seeds 151 and 152; unit = mask.
* **New runs:** `EB_best` and `EB_down_t` at both rates (2 x 2 x 768 = 3,072), `EB_best64` at 4/16 (768), and the anchor rows that join
  (768 per row and rate). `fault_runs.csv` has the columns of `results_v26_faults/fault_rate_runs.csv`, followed by the counters of this
  round.
* **Reused:** DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran and the main row from `results_v26_faults/fault_rate_runs.csv`, after the reuse check
  (`reuse_check.md`, under "Gates").
* **Value of a mask** for row A against row B: V_m = the mean over the two traffic patterns and the two seeds of ln(metric_A / metric_B),
  paired by seed; THR = the largest accepted throughput over the four loads; LAT and P99 at 1.0 x Lsat of DeFT-P on the mask. **Effect** of
  a size and rate = 100 x (exp(mean of V_m over the 16 masks) - 1) %, with the 95 % t interval over the masks; test: two-sided one-sample t
  test of the 16 V_m against 0 (15 df). As round 26.

### Primary family 2 (24 tests, Holm over the 24, alpha = 0.05)
For each size, each of the two rates and each of `EB_best` and `EB_down_t`: the main row has higher THR, and lower LAT at 1.0 x Lsat, than
that row. Verdicts as in family 1. The two families are adjusted separately.

### Secondary (descriptive)
Each early row against DeFT_P and against the best DeFT variant (per mask, traffic and metric the best of DeFT_P, DeFT_B, DeFT_Dis and
DeFT_Ran by the mean of the two seeds); the share of the main row's gain over DeFT_P ((mean V_m of the row against DeFT_P) / (mean V_m of the
main row against DeFT_P)); uniform and hotspot traffic separately; the masks with and without a chiplet that is left one functional VL;
`EB_best64` against `EB_best` at 4/16; each tuned row against its anchor where the anchors run.

---

## Part E: the reports across the VLs under faults
* `LB_noVLrep` on the 192 masks of round 26 (rates 1/16, 2/16, 4/16, 8/16), uniform and hotspot traffic, the four loads, seeds 151 and 152:
  3,072 runs (`novlrep_runs.csv`). The main row is reused from round 26.
* Per size and rate: `LB_noVLrep` against the main row in THR, LAT at 1.0 x Lsat and P99, effect and 95 % interval over the 16 masks, as in
  Part D.
* **Stated before the runs:** the reports are called unnecessary if, for every size and rate, the interval lies within +-1 % in THR and
  +-3 % in LAT. Otherwise the report says where they matter.
* Also: the same for the masks with a chiplet that is left one functional VL, and the mask with the largest loss in each size and rate.

---

## Time rule
Parts C, D and E are timed first (`runtime_estimate.md`): for Part C the seed-171 runs at the 2nd, 5th and 9th load of every cell, for
Parts D and E the seed-151 runs at the 1st and 4th load of masks 1 to 4 of every size and rate (runs of the designs, kept; their results are
not looked at; one set after the other, no other job of the round next to a set). The estimate is taken as measured, with whatever else
runs on the PC. If the three estimates together exceed 30 h, the following are dropped in this order until they do not: (0) the anchor rows
in Part D (if they run; see `DECISIONS.md`); (1) `EB_best64` in Part D; (2) rates 1/16 and 2/16 of Part E; (3) seeds 176-180 of
`EB_best64` in Part C; (4) rate 1/16 of Part D. What is dropped is taken back if it fits later (`restore_v28.py`): in the reverse of the
drop order, when the time since the start of the timing runs plus the time of the item at the speed measured until then is at most 30 h,
decided from the clock and the number of finished runs only. If an item stays dropped, the analysis is the one above on what was run.

## Checks of the analysis
The 12 tests of family 1 and the 24 of family 2 are computed a second time by a script that shares no code with the report
(`check_v28_family.py`), as in rounds 25 to 27.

## Not done in this round
No retuning of the frozen configuration, no change to an existing row, no new proof and no new model check (the new rows restrict the
checked relation, as in round 27; `FINDINGS.md`, A3). `EB_best64` is not run at the rate 1/16 and `LB_noVLrep` not without faults (round
27 has it).

---

## Stated in advance
*This section is `stated_in_advance.md` unchanged, committed on its own (ffe51de) before the gates had run any row whose performance I looked at.*

Written on 17 Nov 2026 at about 03:35, before any run of a new row whose performance I looked at: the smoke runs of A1 (`DECISIONS.md`) were
read for identity with DeFT_P and for the pending check only, and the description run of the unit checks (check 4) had not run yet.

**The prompt's expectation**, quoted from the task of this round: `EB_best` will be DeFT-P's table with a correction for hot spots. It gets
most of the main row's gain under hotspot traffic and little in the other five scenarios, so a positive share without faults that is well
below 100 %, and a larger share under faults. If it reaches the main row, that is a result and is reported as such.

**Mine:**
* **Tuning (B1).** `EB_best` comes from the sub-family (route, P = 1) on both sizes, with a finite T between 4 and 32 and B between 1 and
  4. Its score is positive and far below the main row's: about +0.05 to +0.20 on 4x4 (main row +0.65) and 0 to +0.10 on 2x2 (main row
  +0.53). On 2x2 a best score below 0 would not surprise me. **The anchor buys most of the distance to round 27** (round 27's members with
  T = 0 scored -0.1 to -1.3, so the best T > 0 should be at least 0.1 above the best T = 0 on each size). **The pending count buys less**:
  with the anchor, P = 1 against P = 0 should differ by less than 0.05 in score at the chosen S, B and T, more for S = vl than for S =
  route, and more at small T than at large T.
* **B2.** `EB_best64` chooses a T at least as large as `EB_best`'s (old information should count less) and scores within 0.05 of it.
* **B3.** `EB_down_t` chooses a large `lut_bias` (8 or more on 4x4) and scores near 0 (between -0.05 and +0.10): the commit at the Down
  move knows less than the oracle.
* **Part C, family 1: 12 of 12 supported**; the main row is ahead of `EB_best` by 4 to 10 % in THR and 20 to 35 % in LAT at 1.0 x Lsat on
  every size. The tests most at risk: THR against `EB_best` on 3x3 and 4x4, where the hotspot share is largest.
* **Share of the main row's gain without faults:** `EB_best` 15 to 40 % in THR and 10 to 40 % in LAT over the six scenarios; 70 to 100 %
  under hotspot traffic alone; 0 to 20 % in the other five together (it should no longer be negative there: the anchor keeps it near
  DeFT-P's table). `EB_down_t` 0 to 25 %.
* **Per scenario:** an early row is level with the main row in THR only under hotspot traffic on 3x3 and 4x4, as in round 27; ahead of it
  nowhere with an interval that excludes 0.
* **Below saturation:** `EB_best` within 1 % of DeFT_P at 0.2 and 0.5 x Lsat (at low load the anchor keeps DeFT-P's entry VL); the main row
  1.5 to 2.5 % faster than DeFT_P there, as in rounds 25 and 27.
* **How often `EB_best` leaves DeFT-P's entry VL:** 5 to 25 % of the packets at 1.0 x Lsat over the six scenarios, most under hotspot
  traffic (30 to 60 %) and under 10 % in the other five. So it is DeFT with a correction for hot spots, not more.
* **`EB_best64` against `EB_best`:** THR within 1.5 %, LAT at 1.0 x Lsat 2 to 10 % higher; under hotspot traffic nearly no cost (the hot
  spot does not move).
* **Part D, family 2: 20 to 23 of 24 supported, none against.** At the rate 1/16 every test supported. At 4/16 the THR tests against
  `EB_best` on 3x3 and 4x4 are at risk of not being significant (round 27's `EB_route` was within 1.1 and 0.5 % of the main row there,
  and `EB_best` is at least as strong); the LAT tests should be supported. `EB_down_t` behind the main row in every test. Shares of the
  main row's THR gain under faults: `EB_best` 60 to 100 % at 4/16 and 30 to 70 % at 1/16; larger under hotspot than under uniform traffic.
* **Part E:** the reports across the VLs are unnecessary by the stated margin at every size and rate; if a cell misses the margin, it is
  8/16 on 2x2 (few masks with a free choice, wide intervals), and the loss sits in masks with a chiplet that is left one functional VL.
* **In one sentence:** without faults an early binder with ideal information and an anchor at DeFT gets the hotspot part of the gain and
  little else, so most of the gain still needs late binding; under faults it gets most of the throughput gain and part of the latency gain.
