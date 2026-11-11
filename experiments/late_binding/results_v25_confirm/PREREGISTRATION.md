# Pre-registration v25: confirmatory round for late binding with XY on the interposer

Committed before any evaluation run of Parts B and C (the timing runs included). Done before it: the regression
(`regression.md`, 84 / 84 byte-identical to the ce6ab6a build), the reproduction of 24 runs of round 24 with this round's row
definitions (`reuse_check.md`), the ladders of the three scenarios the tuning did not see (`load_points_v25.md`) and the drain
tests of the frozen rows (`drain_summary.csv`). Nothing below depends on a result of Part B or C.

**Nothing is tuned in this round.** The configuration is the one round 24 chose (`results_v24_xy/tuning_choice.json`, seeds
101-102) and recommended (`results_v24_xy/FINDINGS.md`, question 10). The simulator is the ce6ab6a build, unchanged.

## Frozen rows
| row | definition |
|---|---|
| `CI_heurLA_X_LF` (**main**) | exit from the LUT, late entry, XY on both layers (`chip_tm XY ipos_tm XY`); `-sel DEFT_HEUR` with heur_w 2, heur_busy 0, hop_weight_ipos 1, heur_lookahead 1, lut_bias 2 on 2x2 and 0 on 3x3 and 4x4; `lookahead_route 1 lookahead_fallback 1 busy_state 1`, decision_delay 0 |
| `CI_heurLA_O_LF` (**second**) | the same with `ipos_tm O1` (XY in VN0, YX in VN1 on the interposer) |
| `CI_heurLA_X_DLY` | the main row without lookahead routing, decision_delay 2 |
| `CI_qlLA_X_LF` | `-sel DEFT_QL` with ql_w 2, ql_busy 0, hop_weight_ipos 1, the same lut_bias, ql_alpha 0.01, ql_key 1, ql_eps 0, ql_lookahead 1; `lookahead_route 1 lookahead_fallback 1 busy_state 1`, decision_delay 1 |

References: DeFT_P, DeFT_B (every scenario); MTR, RC, XY_SP (fault-free scenarios; XY_SP = `-routing INTERPOSER_AWARE_XY`, the v10
definition); DeFT_Dis, DeFT_Ran (scenarios with faults; fault-free DeFT_Dis takes DeFT-P's routes). The arguments of every row are
built by `experiments_v25.row_args` (for the frozen rows and DeFT_P, DeFT_B, MTR, RC by the v24 code itself).

## Options of every run of Parts B, C and D
* pipe_all 2; window 2000 + 8000 cycles (Parts B, C); 8-flit packets; 2 VCs; 4-flit buffers; LUTs `luts/v23` (generator settings of
  v23); `-traffic_rng 1`.
* Every VN-based method: `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`. MTR and RC: `-vc_per_hop 1`.
* Observation only: `-deft_lb count_vl 1` on DeFT_P, DeFT_B, XY_SP; `-deft_lb hop_stats 1` on every DEFT_LB row with VN rules.

---

## Part B: main evaluation

### Design
* **Scenarios (the same eight on every size):** uniform, localized, hotspot, chipperm, chiptrans, movinghot fault-free; uniform
  and hotspot with one faulty VL per chiplet (masks 0x1111 / 0x111111111 / 0x1111111111111111). Seen by the v24 tuning:
  uniform, hotspot, chipperm, chiptrans, uniform with faults. **Not seen by the tuning:** localized, movinghot, hotspot with faults.
* **Sizes** 2x2, 3x3, 4x4. **Loads:** the nine points (0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat of DeFT-P) of the
  pipe_all 2 ladders in `load_points_v25.json`. **Seeds 121-130** (never used before).
* **Rows:** the four frozen rows, DeFT_P and DeFT_B on all eight scenarios; MTR, RC and XY_SP on the six fault-free ones;
  DeFT_Dis and DeFT_Ran on the two with faults.
* **Runs:** 6 x 2,160 + 3 x 1,620 + 2 x 540 = 18,900.
* **Time rule.** The time is estimated first from the 630 runs of seed 121 at the 2nd, 5th and 9th load of every cell (runs of
  the design, kept; their results are not looked at), with the number of processes the evaluation uses (10; two cores are left to
  Part F). If the estimate for the whole design exceeds 36 h, rows are dropped in this order until it does not: (1) XY_SP;
  (2) seeds 126-130 of `CI_qlLA_X_LF`. Nothing else is reduced. A dropped XY_SP is not a reference row anywhere.

### Metrics
* **THR:** the largest accepted throughput over the nine loads. **LAT** and **P99:** mean and 99th-percentile packet latency at
  1.0 x Lsat of DeFT-P (the 4th load). **LAT at 0.2 and 0.5 x Lsat:** the 1st and 2nd load.
* **Best baseline** per (size, scenario, metric): the reference row available on that scenario (fault-free: DeFT_P, DeFT_B, MTR,
  RC, XY_SP; with faults: DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran) with the best arithmetic mean of the metric over the ten seeds
  (highest THR, lowest LAT, lowest P99); its per-seed values are the reference.
* **Effect per size** = 100 x (exp(mean over seeds of R_s) - 1) %, where R_s = mean over the eight scenarios of
  ln(metric_row / metric_best baseline) for seed s. Test: two-sided one-sample t test of the ten R_s against 0 (9 df); the 95 %
  interval is the t interval of the mean of R_s, transformed the same way.

### Primary family (18 tests, Holm over the 18, alpha = 0.05)
On each size, `CI_heurLA_X_LF` and `CI_heurLA_O_LF` have higher THR, lower LAT and lower P99 than the best baseline.
Supported = significant after Holm in the hypothesised direction. A significant effect in the other direction is reported as
against; anything else as not significant.

Stated in advance, from round 24: `CI_heurLA_O_LF` lost THR on 2x2 there (-0.6 %), so that test is expected not to be supported;
the 2x2 uniform cell is a risk for the main row (THR -1.2 %, LAT +1.0 % against RC in round 24).

### Secondary (descriptive; unadjusted p values, never called significant)
* every row per scenario against the best baseline and against each reference row; the three scenarios not seen by the tuning
  separately from the five that were (the effect over the three and over the five, per size);
* `CI_heurLA_X_DLY` against `CI_heurLA_X_LF`;
* `CI_qlLA_X_LF` against `CI_heurLA_X_LF`, per scenario (does learning help on the moving hotspot?);
* LAT at 0.2 and 0.5 x Lsat against DeFT_P for every frozen row;
* accepted throughput beyond the peak: at 2.0 and 2.4 x Lsat relative to the row's peak, and the lowest point after the peak
  (the column added in round 24);
* the share of hops with more than one offered output (per layer), the fallback rate (`lookahead_fb_taken / lookahead_multi`),
  the share of stored decisions that differ from a fresh one.

### Sanity (`report/sanity.md`)
The observation-only options leave the statistics unchanged; the largest flit rate of any VL in any run does not exceed 0.5
flits per cycle.

---

## Part C: fault sweep (its own family)

### Design
* Uniform traffic; k = 1, 2, 3 faulty VLs in every chiplet; the **first three masks** per (size, k) of `results_v11/masks.json`
  (27 masks, drawn in round 11 with `random.Random(3110)`); the v23 LUT of each mask.
* **Gates before the runs:** the model check (`CI_XY_XY`, `CI_XY_O1`, the paper's Up rule) on every mask of 3x3 and 4x4, and
  on every 2x2 mask of the sweep that is not among the 897 masks checked in round 24 (if the 4x4 checks would take more than
  3 h, one 4x4 mask per k is checked and this is said); an all-pairs drain test of every row on every mask (a failure of a
  candidate stops the round).
* **Ladder per mask:** Lsat of DeFT_P by the D1 rule (seed 101, pipe_all 2, L0 at 0.0002, 3 x L0, the 0.0001 grid where the
  coarse Lsat is <= 0.004); loads 0.5, 1.0, 1.4, 2.0 x Lsat, rounded to the grid as in D1. The sweep is run upwards in batches
  and stops after the first rate above 3 x L0; this gives the Lsat of the full sweep.
* **Rows:** DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran, `CI_heurLA_X_LF`, `CI_heurLA_O_LF`. **Seeds 131-135** (never used before).
* **Runs:** 27 masks x 6 rows x 4 loads x 5 seeds = 3,240. The design is run in full.

### Metrics and tests
* THR = the largest accepted throughput over the four loads; LAT and P99 at 1.0 x Lsat; LAT at 0.5 x Lsat.
* **Best reference row** per (mask, metric): the one of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran with the best mean over the five seeds.
* **Effect per (size, k)** = 100 x (exp(mean over seeds of R_s) - 1) %, R_s = mean over the three masks of
  ln(metric_row / metric_best reference row of the mask) for seed s; two-sided one-sample t test over the five seeds (4 df).
* **Family (12 tests, Holm over the 12, alpha = 0.05):** for each size and k = 1, 2, `CI_heurLA_X_LF` has higher THR and lower
  LAT at 1.0 x Lsat than the best reference row.
* **Secondary (descriptive):** `CI_heurLA_O_LF`; P99; LAT at 0.5 x Lsat; each row against each reference row; the trend over k.
* **k = 3 is a check, not a test.** With one functional VL per chiplet there is nothing to bind, and with XY the main row takes
  DeFT-P's route. Reported per mask: the main row's THR, LAT, P99 and LAT at 0.5 x Lsat relative to DeFT_P's, the number of
  run pairs with identical statistics, and what LF changes (the counters of the lookahead and of the fallback). k = 3 is in no
  test.
* **Delivered share:** received / injected packets per row at every load (packets in flight at the end of a run count as not
  delivered), the dead-end events (must be 0), and the drain tests (every packet must arrive).

---

## Parts D and E (descriptive; fixed here so that they cannot follow the results)
* **Part D, application traces.** The v13 protocol (nine PARSEC traces through Netrace on 2x2, the first 700,000 cycles of
  region 2, dependency mode, 2- and 18-flit packets) and the v15 protocol (the six pairs of the four heaviest traces,
  compression 1 and 2), fault-free and with mask 0x1111; seeds 41-43 as in those protocols (they only drive the VC choice and
  the tie-breaks; no frozen row was ever run on a trace). Rows: DeFT_P, DeFT_B, MTR, RC (fault-free only), `CI_heurLA_X_LF`,
  `CI_heurLA_O_LF`, all at pipe_all 2. Reported: mean latency relative to DeFT_P and the completion time, per trace and as a
  geometric mean; the offered load of each trace. A run that does not deliver its whole window is listed and excluded.
* **Part E, one-cycle router model.** `-pipe_all 0`, the v23 pipe_all 0 ladders; uniform, hotspot, chipperm fault-free and
  uniform with one faulty VL per chiplet; three sizes; nine loads; seeds 141-145 (never used before). Rows: DeFT_P, DeFT_B,
  MTR, RC (fault-free), `CI_heurLA_X` with an ideal decision (decision_delay 0, no lookahead routing) and `CI_heurLA_X_DLY`
  (decision_delay 2), with the frozen selection values. Reported: the per-size table of Part B (THR, LAT, P99 against the best
  baseline of each scenario, over the four scenarios), with intervals over the five seeds; no test.

## Part F and a possible addendum
Part F (RTL, check against the simulator, synthesis, timing) decides which timing mechanism can be built with W = pipe_all + 1 =
3 cycles per hop. If that mechanism is not one of the evaluated rows (LF with residual 0, DLY with 2 cycles), the row is
defined in `PREREGISTRATION_addendum.md` before it is run, run on the Part B design (seeds 121-130) and tested against the
best baseline exactly as the main row (three tests per size, reported next to the primary family, with their own Holm
correction over those tests).

## Exclusions
A missing run is listed; a seed with a missing run in a scenario (or mask) of a comparison is dropped from that comparison and
this is reported. A dead-end event in any run, a drain-test FAIL, a failed model check or a failed regression check stops the
round. The designs are run in full; the only reduction is the time rule of Part B.

## Report
`report/summary.md` and `FINDINGS.md` with the ten answers of the prompt; `paper_data/` (one CSV per table or figure, with
means and 95 % intervals): per-size effects against the best baseline and against each reference row; per-scenario effects;
latency against offered load for every row (4x4 and 2x2: uniform, hotspot, chipperm, chiptrans, uniform with faults); the fault
sweep (THR and LAT against k); area and timing.
