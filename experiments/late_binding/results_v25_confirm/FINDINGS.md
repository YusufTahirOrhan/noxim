# Findings v25: confirmatory round for late binding with XY, and the hardware of the final design

Status: **complete.** Part A (gates), the pre-registration, Part B (18,900 runs; `report/summary_B.md`,
`eval_runs.csv`), Part C (3,240 runs; `report/summary_C.md`, `fault_runs.csv`), Part D (630 trace runs, none excluded;
`report/summary_D.md`, `app_runs.csv`, `pair_runs.csv`), Part E (2,970 runs with the one-cycle router model;
`report/summary_E.md`, `pipe0_runs.csv`), Part F (hardware; `hw/FINDINGS_hw.md`) and the addendum row (2,160 runs;
`report/summary_A.md`, `addendum_runs.csv`). Of the 27,900 evaluation runs none is missing and none has a dead-end
event. The whole report is `report/summary.md`; the tables for the paper are in `paper_data/`.

Nothing is tuned in this round: the configuration is the one round 24 chose on seeds 101-102, the simulator is the ce6ab6a
build, and the analysis is fixed in `PREREGISTRATION.md` (Parts B and C) and `PREREGISTRATION_addendum.md`.

**Primary result (pre-registered, Holm over 18): 17 supported, 1 against, 0 not significant.** On seeds no earlier round
used and on eight scenarios, the frozen main row (XY on the interposer, lookahead with fallback) beats the best baseline on
every size in throughput, mean latency and tail latency. The second row (VN-split order) does the same on 3x3 and 4x4 and
loses 2.7 % of throughput on 2x2; the pre-registration had named that test as the one not expected to be supported.

| size | row | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |
|---|---|---|---|---|
| 2x2 | `CI_heurLA_X_LF` (main) | +1.5 % [+1.2, +1.8] | -13.1 % [-15.0, -11.1] | -27.8 % [-31.8, -23.5] |
| 2x2 | `CI_heurLA_O_LF` (second) | **-2.7 % [-3.0, -2.4] (against)** | -6.2 % [-8.4, -3.9] | -21.3 % [-26.1, -16.3] |
| 3x3 | `CI_heurLA_X_LF` (main) | +6.7 % [+6.4, +7.0] | -10.5 % [-11.7, -9.3] | -27.9 % [-30.8, -24.9] |
| 3x3 | `CI_heurLA_O_LF` (second) | +5.9 % [+5.4, +6.3] | -8.7 % [-10.2, -7.1] | -29.6 % [-32.9, -26.1] |
| 4x4 | `CI_heurLA_X_LF` (main) | +6.6 % [+6.3, +7.0] | -15.0 % [-16.6, -13.5] | -34.2 % [-36.6, -31.8] |
| 4x4 | `CI_heurLA_O_LF` (second) | +7.3 % [+7.0, +7.7] | -16.1 % [-17.7, -14.4] | -40.9 % [-43.3, -38.5] |

Effects are against the best reference row per scenario and metric (DeFT_P, DeFT_B, MTR, RC, XY_SP without faults; DeFT_P,
DeFT_B, DeFT_Dis, DeFT_Ran with faults), averaged over the eight scenarios; 95 % intervals over seeds 121-130; every
Holm-adjusted p <= 0.0003. Everything else in Part B is descriptive (unadjusted).

**Addendum (pre-registered before any of its runs; a family of its own, Holm over 9): 9 supported, 0 against, 0 not
significant.** `CI_heurLA_X_LF1` is the main row with one residual cycle at every hop with a choice. It is what the router
of Part F does if its decision cannot start while the head is on the link, or if the clock is 1 ns (question 9). The cycle
costs no throughput and 2.2-3.7 % of mean latency (1.4-2.4 cycles per packet). All nine tests against the best baseline
are supported, as for the main row. What the row loses is the main row's latency advantage over DeFT_P at low load (LAT at
0.2 x Lsat +1.5 / -0.5 / -0.1 % instead of -2.1 / -3.1 / -2.5 %).

| size | row | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |
|---|---|---|---|---|
| 2x2 | `CI_heurLA_X_LF1` (addendum) | +1.5 % [+1.2, +1.7] | -11.1 % [-13.2, -9.0] | -27.4 % [-31.0, -23.7] |
| 3x3 | `CI_heurLA_X_LF1` (addendum) | +6.7 % [+6.3, +7.0] | -8.5 % [-9.8, -7.2] | -27.3 % [-30.2, -24.2] |
| 4x4 | `CI_heurLA_X_LF1` (addendum) | +6.5 % [+6.0, +7.1] | -13.2 % [-14.7, -11.6] | -33.3 % [-35.6, -31.0] |

**The average hides a split** (question 2). On the five scenarios the tuning saw, the effects of round 24 come again on the
new seeds (main row: THR +4.1 / +10.5 / +9.1 %, LAT -20.1 / -16.4 / -23.6 %). On the three it did not see, the main row is
level with the best baseline on average (THR -2.7 / +0.7 / +2.5 %, LAT 0.0 / +0.3 / +1.4 %): it gains on hotspot with
faults, and it is behind RC on 2x2 localized and behind MTR and RC on the moving hotspot. Against DeFT_B it is ahead in
throughput and mean latency in all 24 cells (a cell is one scenario on one size), against DeFT_P in 23 and behind in none.

## Gates
* **Regression** (`regression.md`): the 84-configuration set is byte-identical to a fresh build of ce6ab6a in all three
  comparisons (the 8d84634 build, `bin/noxim` with the options absent, `bin/noxim` with every option of rounds 23-24 given
  explicitly off). No simulator source changed in this round.
* **The rows of this round are the rows of round 24** (`reuse_check.md`): 24 of 24 evaluation runs of round 24, drawn at
  random over the four frozen rows and DeFT_P, DeFT_B, MTR and RC, are reproduced field by field with this round's driver.
* **Ladders** (`load_points_v25.md`): the three scenarios the tuning did not see (localized, movinghot, hotspot with one
  faulty VL per chiplet) got their ladders again by the D1 rule; all nine equal the ladders round 23 had made for them.
* **Drain tests of the frozen rows** (`drain_summary.csv`): 336 of 336 pass, 0 dead-end events: the four frozen rows at
  pipe_all 2 and the two late-binding rows of Part E at pipe_all 0, each with the v10 protocol and masks on the three sizes
  and with over-saturated 4x4 runs on localized and movinghot.
* **Model check of the fault-sweep masks** (`formal_faults.md`): 27 masks (k = 1, 2, 3 faulty VLs in every chiplet; all nine
  masks of every size, the 4x4 ones included), relations `CI_XY_XY` and `CI_XY_O1` with the paper's Up rule: 54 of 54 pass
  (acyclic CDG, no dead-end state, no livelock; longest path at most 24 / 32 / 40 hops).
* **Drain tests on the fault-sweep masks** (`drain_faults.csv`): 162 / 162 pass (the six rows of the sweep on each of the 27 masks,
  all-pairs burst: every packet delivered, 4,032 / 20,592 / 65,280 on 2x2 / 3x3 / 4x4, no dead-end event).
* **Drain tests of the addendum row** (`drain_summary_addendum.csv`): 56 of 56 pass, 0 dead-end events (the protocol of the
  frozen rows at pipe_all 2), run before the first evaluation run of the row.
* **Run-time rule** (`runtime_estimate.md`): 26.5 h estimated for Part B with 10 processes; nothing was dropped.
* **Hardware checks** (`hw/FINDINGS_hw.md`, F2): 6.12 M, 6.21 M and 4.97 M vectors from simulator runs against the RTL of the
  three designs, 0 mismatches; every instrumented simulator run byte-identical to `bin/noxim`; 23 of 25 mutations caught (the
  two others change logic no reachable input exercises); 140 of 140 router configurations pass the router-level test.

## The ten questions

### 1. Primary family of Part B: how many supported, which against?
**17 of 18 supported, 1 against, none not significant** (`report/summary_B.md`, B.1; the table at the top). 18,900 runs,
none missing, no dead-end event.
* **Main row `CI_heurLA_X_LF`: 9 of 9 supported.** Against the best baseline over the eight scenarios (2x2 / 3x3 / 4x4):
  THR +1.5 / +6.7 / +6.6 %, LAT at 1.0 x Lsat -13.1 / -10.5 / -15.0 %, P99 -27.8 / -27.9 / -34.2 %.
* **Second row `CI_heurLA_O_LF`: 8 of 9 supported; THR on 2x2 is against** (-2.7 % [-3.0, -2.4], Holm p 4e-08). The
  pre-registration had said in advance that this test was not expected to be supported (round 24: -0.6 %). Its other
  effects: THR +5.9 / +7.3 % on 3x3 / 4x4, LAT -6.2 / -8.7 / -16.1 %, P99 -21.3 / -29.6 / -40.9 %.
* The effects are smaller than in round 24's family (heuristic with XY and LF there: THR +4.1 / +10.2 / +9.3 %, LAT
  -20.7 / -19.2 / -24.0 %) because the family now has eight scenarios instead of five and the three added ones show no
  gain on average (question 2).
* The family was computed a second time by a script that shares no code with the report (`check_v25_families.py`,
  `report/families_check.md`): all 18 tests agree in effect, interval, adjusted p and verdict.
* **Reported next to it and not merged with it: the family of the addendum (Holm over its own 9 tests), 9 of 9
  supported** (`report/summary_A.md`, A.1). The main row with one residual cycle, `CI_heurLA_X_LF1`, against the best
  baseline: THR +1.5 / +6.7 / +6.5 %, LAT -11.1 / -8.5 / -13.2 %, P99 -27.4 / -27.3 / -33.3 %; every Holm-adjusted p <=
  1.1e-06; 2,160 runs, none missing, no dead-end event. The second computation agrees on these nine tests as well. Why
  the row was run and what the cycle costs: question 9.

### 2. Per scenario: where are the gains and the losses? The three scenarios not seen in tuning against the five that were?
`report/summary_B.md`, B.3 (per scenario), B.4 (seen against not seen), B.6 (per cell). Main row against the best baseline,
2x2 / 3x3 / 4x4; "(=)" marks an effect whose 95 % interval includes zero.

| scenario | tuning saw it | best baseline for THR | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |
|---|---|---|---|---|---|
| uniform | yes | RC, RC, MTR | -1.4 / +10.0 / +13.2 % | +0.8 (=) / -16.7 / -11.2 % | -7.5 (=) / -42.5 / -30.4 % |
| hotspot | yes | DeFT_B | +2.9 / +2.5 / +2.4 % | -13.9 / -5.2 / -4.8 % | -20.0 / -3.7 / -2.1 (=) % |
| chipperm | yes | MTR, DeFT_B, DeFT_P | +7.8 / +25.4 / +8.7 % | -29.4 / -26.0 / -14.3 % | -52.8 / -59.8 / -29.4 % |
| chiptrans | yes | MTR, MTR, RC | +2.7 / +5.4 / +6.4 % | -25.6 / -12.4 / -45.6 % | -49.3 / -33.3 / -74.8 % |
| uniform+f | yes | DeFT_B | +9.0 / +10.4 / +15.5 % | -28.5 / -20.0 / -33.9 % | -51.7 / -45.3 / -68.8 % |
| localized | no | RC | -7.6 / +0.7 (=) / +5.5 % | +8.4 / -4.4 / -4.7 % | +2.7 (=) / -28.0 / -22.6 % |
| movinghot | no | MTR | -3.5 / -1.8 / +0.2 (=) % | +0.2 (=) / +11.1 / +14.1 % | +2.9 (=) / +38.2 / +29.7 % |
| hotspot+f | no | DeFT_B | +3.3 / +3.2 / +1.9 % | -8.0 / -5.2 / -4.1 % | -18.3 / -9.4 / -7.6 % |

* **Gains.** Of the 24 cells (one scenario on one size) the main row is better than the best baseline in 18 in throughput,
  19 in mean latency and 18 in tail latency. The largest gains are on chipperm, on uniform with faults, on chiptrans and on
  uniform on 3x3 and 4x4. On hotspot with and without faults the gains are small and on every size (THR +2 to +3 %, LAT -4
  to -14 %).
* **Losses.** It is worse in 4 cells in throughput, 3 in mean latency and 2 in tail latency, all of them on 2x2 or on the
  moving hotspot:
  * 2x2 uniform: THR -1.4 % against RC, latency level. The pre-registration had named this cell as a risk.
  * 2x2 localized: THR -7.6 % and LAT +8.4 % against RC.
  * moving hotspot: THR -3.5 / -1.8 % on 2x2 / 3x3 against MTR, and LAT +11.1 / +14.1 %, P99 +38.2 / +29.7 % on 3x3 / 4x4
    against MTR and RC.

  In each of these cells the best baseline is MTR or RC, which do not use VNs. Against DeFT_P the main row is ahead in the
  same cells or level with it (moving hotspot: THR on 3x3, LAT on 4x4), except in the tail latency of the moving hotspot on
  4x4 (+11.8 %; question 3).
* **Seen against not seen** (effect against the best baseline, 2x2 / 3x3 / 4x4):

  | row | metric | five scenarios the tuning saw | three it did not see |
  |---|---|---|---|
  | main | THR | +4.1 / +10.5 / +9.1 % | -2.7 / +0.7 / +2.5 % |
  | main | LAT | -20.1 / -16.4 / -23.6 % | -0.0 (=) / +0.3 (=) / +1.4 (=) % |
  | main | P99 | -38.8 / -39.5 / -48.1 % | -4.8 (=) / -3.4 (=) / -2.5 (=) % |
  | second | THR | -0.7 / +10.1 / +11.5 % | -5.9 / -0.9 / +0.7 % |
  | second | LAT | -14.2 / -17.6 / -27.9 % | +8.9 / +8.3 / +8.1 % |
  | second | P99 | -34.2 / -44.0 / -57.1 % | +6.0 (=) / +2.9 (=) / +0.6 (=) % |

  On the five scenarios of the tuning the effects of round 24 come again on seeds that round never used (round 24, main
  row: THR +4.1 / +10.2 / +9.3 %, LAT -20.7 / -19.2 / -24.0 %, P99 -40.5 / -45.6 / -48.5 %; second row on 4x4: THR +11.6 %,
  LAT -28.4 %). So those gains are not an effect of the seeds. On the three scenarios the tuning did not see, the main row
  is level with the best baseline in mean and tail latency and within 3 % of it in throughput (behind on 2x2, ahead on 3x3
  and 4x4); the second row is behind it in mean latency by 8-9 % on every size.
* **The three new scenarios differ among themselves.** Hotspot with faults behaves as hotspot does (gain on every size).
  Localized gains on 3x3 and 4x4 in latency and loses on 2x2. The moving hotspot loses. The second row is hit harder by the
  moving hotspot than the main row (LAT +22.7 / +36.1 / +35.5 % against the best baseline).
* **Tuning or scenario?** This design cannot separate the two; every late-binding row was tuned on the same five scenarios.
  Two things can be said. On localized a packet meets fewer hops with a choice (1.2 per packet against 1.6-1.8 on uniform;
  B.11), so there is less to gain. On the moving hotspot it meets as many as on uniform (1.6-1.8), yet the gain over DeFT_P
  is small (THR +3.1 % / level / +2.7 %, against +6.0 / +15.4 / +18.4 % on uniform) while MTR and RC keep their lead over
  DeFT_P; so the cause there is not a lack of decisions. What the selection does with them on that pattern was not analysed
  in this round.

### 3. Against each reference row separately
`report/summary_B.md`, B.5 and B.6. Main row; effect over the scenarios both rows ran on, 2x2 / 3x3 / 4x4; cells in which
the main row is better / worse (95 % interval excludes zero).

| reference | scenarios | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat | cells better / worse: THR, LAT |
|---|---|---|---|---|---|
| DeFT_P | all eight | +10.6 / +16.5 / +14.8 % | -32.0 / -37.3 / -39.9 % | -52.3 / -67.0 / -70.9 % | 23 / 0 of 24, 23 / 0 |
| DeFT_B | all eight | +16.3 / +13.9 / +26.1 % | -57.1 / -47.0 / -57.6 % | -69.9 / -68.2 / -74.1 % | 24 / 0 of 24, 24 / 0 |
| MTR | six fault-free | +2.5 / +9.6 / +9.0 % | -16.8 / -17.4 / -21.4 % | -36.5 / -44.8 / -49.6 % | 13 / 4 of 18, 14 / 2 |
| RC | six fault-free | +2.2 / +9.5 / +8.8 % | -12.2 / -16.3 / -20.4 % | -28.4 / -44.2 / -47.9 % | 12 / 2 of 18, 13 / 2 |
| XY_SP | six fault-free | +72.6 / +65.3 / +72.8 % | -93.2 / -87.7 / -85.3 % | -95.6 / -93.0 / -90.6 % | 18 / 0 of 18, 18 / 0 |
| DeFT_Dis | two with faults | +29.2 / +31.4 / +30.6 % | -60.1 / -65.6 / -71.3 % | -82.6 / -90.9 / -93.1 % | 6 / 0 of 6, 6 / 0 |
| DeFT_Ran | two with faults | +33.8 / +24.5 / +18.8 % | -69.3 / -42.9 / -36.1 % | -76.5 / -59.8 / -54.0 % | 6 / 0 of 6, 6 / 0 |

* **DeFT_P, DeFT_B, XY_SP, DeFT_Dis, DeFT_Ran: in throughput and mean latency the main row is behind in no cell.** Against
  DeFT_P the two cells that are not ahead are level (THR of the moving hotspot on 3x3, LAT of the moving hotspot on 4x4). In
  tail latency one cell is behind DeFT_P: the moving hotspot on 4x4 (+11.8 %).
* **MTR and RC are the references that set the best baseline where the main row loses.** Against MTR it is behind in
  throughput on 2x2 uniform (-0.7 %), 2x2 localized (-4.8 %) and the moving hotspot on 2x2 and 3x3 (-3.5, -1.8 %), and in
  mean latency on the moving hotspot on 3x3 and 4x4 (+11.1, +13.8 %). Against RC it is behind in throughput on 2x2 uniform
  (-1.4 %) and 2x2 localized (-7.6 %), and in mean latency on 2x2 localized (+8.4 %) and the moving hotspot on 4x4
  (+14.1 %). On 3x3 and 4x4 it is ahead of both by about 9 % in throughput over the six fault-free scenarios.
* **Second row** (B.5): against DeFT_P THR +6.0 / +15.6 / +15.6 %, LAT -26.6 / -36.0 / -40.7 %; against MTR THR -2.1 /
  +9.3 / +10.7 %; against RC THR -2.4 / +9.3 / +10.5 %. On 2x2 it is behind MTR and RC in throughput over the six scenarios;
  on 3x3 and 4x4 it is ahead of every reference row.

### 4. Fault sweep: the family of Part C, the trend over k, and the k = 3 check
`report/summary_C.md`. Uniform traffic, k faulty VLs in every chiplet, three masks per size and k, four loads per mask,
seeds 131-135: 3,240 runs, none missing, no dead-end event.
* **Family (Holm over 12): 12 of 12 supported.** Main row against the best reference row of each mask (DeFT_P, DeFT_B,
  DeFT_Dis, DeFT_Ran); every Holm-adjusted p <= 0.003.

  | size | k = 1: THR | LAT at 1.0 x Lsat | k = 2: THR | LAT at 1.0 x Lsat |
  |---|---|---|---|---|
  | 2x2 | +7.8 % [+6.8, +8.9] | -19.3 % [-25.2, -12.9] | +3.8 % [+2.9, +4.7] | -28.5 % [-32.7, -23.9] |
  | 3x3 | +13.5 % [+12.8, +14.1] | -37.2 % [-43.3, -30.5] | +8.8 % [+7.5, +10.1] | -22.4 % [-28.6, -15.7] |
  | 4x4 | +22.1 % [+20.3, +24.1] | -26.8 % [-31.2, -22.1] | +13.9 % [+12.0, +15.8] | -35.4 % [-41.8, -28.3] |

  The second computation of the family (`report/families_check.md`) agrees on all 12 tests.
* **Trend over k.** The throughput gain falls as VLs fail and grows with the size: +7.8 -> +3.8 -> 0 % on 2x2, +13.5 ->
  +8.8 -> 0 % on 3x3, +22.1 -> +13.9 -> 0 % on 4x4 for k = 1 -> 2 -> 3. So does the gain at low load (LAT at 0.5 x Lsat:
  -2.3 -> -1.7 -> 0 %, -3.0 -> -2.0 -> 0 %, -2.6 -> -1.9 -> 0 %). The latency gain at 1.0 x Lsat stays between -19 and
  -37 % for k = 1 and 2 without an order in k (P99: -35 to -70 %). With fewer functional VLs there is less to choose
  from, and with one there is nothing.
* **k = 3 check: passed.** With one functional VL per chiplet the main row is identical to DeFT_P in all 180 run pairs (nine
  masks, four loads, five seeds: accepted throughput, latency, p99 and received packets), and none of its 0.35-1.8 million
  hops per mask offers more than one output. The four reference rows coincide there as well. The second
  row is not identical, because its interposer order differs from DeFT's: THR +1.3 / +3.2 / +0.3 (=) %, LAT -8.9 (=) /
  -15.1 (=) / -23.2 %.
* **Against each reference row** (C.3; THR, 2x2 / 3x3 / 4x4): DeFT_P +11.2 / +17.5 / +23.7 % at k = 1 and +6.0 / +8.8 /
  +13.9 % at k = 2; DeFT_B +7.8 / +13.5 / +22.3 % and +3.8 / +18.9 / +29.3 %; DeFT_Dis +23.8 / +31.1 / +37.2 % and +13.3 /
  +20.0 / +27.4 %; DeFT_Ran +40.1 / +35.0 / +36.9 % and +28.2 / +27.1 / +25.1 %. The best reference row is DeFT_B on most
  masks with k = 1 and DeFT_P on most with k = 2.
* **Second row**: THR +5.3 / +14.3 / +21.4 % at k = 1 and +3.9 / +7.0 / +16.6 % at k = 2; LAT -18.0 / -37.9 / -27.4 % and
  -30.3 / -26.1 / -40.4 %: effects of the size of the main row's.
* **Nothing is lost.** Received over injected packets is at least 0.986 for every row at every load (C.5; packets in flight
  at the end of a run count as not delivered), and the drain tests on the 27 masks pass 162 of 162.
* The cell of Part B with one faulty VL per chiplet (uniform+f: one mask, ten seeds) and k = 1 here (three masks, five
  seeds) agree in sign and size: THR +9.0 / +10.4 / +15.5 % there, +7.8 / +13.5 / +22.1 % here.

### 5. Q-learning against the heuristic on all eight scenarios
**Q-learning adds nothing, as in round 24** (`report/summary_B.md`, B.8). `CI_qlLA_X_LF` against `CI_heurLA_X_LF`, same
relation and mechanism, over the eight scenarios (2x2 / 3x3 / 4x4):

| THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat | LAT at 0.2 x Lsat |
|---|---|---|---|
| -0.2 / -0.2 / -0.2 (=) % | +3.0 / +1.9 / +2.1 % | +2.3 / +1.3 / +2.4 % | +4.7 / +2.7 / +2.3 % |

* Per scenario the mean latency at 1.0 x Lsat is higher with Q-learning in 22 of the 24 cells and lower in none; the
  throughput is higher in two cells (moving hotspot on 3x3, +1.7 % [+0.1, +3.4]; chipperm on 4x4, +0.2 %) and lower in
  eight (by at most 1.0 %).
* The extra latency is the residual cycle that round 24 chose for this row (1.4-1.5 hops with a choice per packet), not
  the learning. Against the heuristic with the same cycle (`CI_heurLA_X_LF1`, the addendum; `report/extra_A.md`, Y.6; a
  descriptive comparison that no pre-registration names) the Q-learning row has THR -0.2 (=) / -0.2 (=) / -0.1 (=) %,
  LAT at 0.2 x Lsat +1.0 / 0.0 (=) / -0.1 %, LAT at 1.0 x Lsat +0.8 / -0.4 / -0.1 (=) % and P99 +1.8 (=) / +0.4 (=) /
  +1.1 (=) %. At equal delay the two selections are within 1 % of each other in every metric: Q-learning is that much
  slower on 2x2 and level or up to 0.5 % faster on 3x3 and 4x4.
* Against the best baseline it is still ahead on every size (THR +1.3 / +6.5 / +6.4 %, LAT -10.4 / -8.8 / -13.2 %), by less
  than the heuristic.

### 6. DLY against LF
**DLY buys 1-2 % of throughput with 3-7 % more latency, as in round 24** (`report/summary_B.md`, B.7). `CI_heurLA_X_DLY`
against `CI_heurLA_X_LF` over the eight scenarios:

| size | THR | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |
|---|---|---|---|---|---|
| 2x2 | +1.6 % | +7.2 % | +6.6 % | +3.3 % | -1.4 (=) % |
| 3x3 | +1.8 % | +5.2 % | +5.0 % | +4.1 % | +0.6 (=) % |
| 4x4 | +1.0 % | +4.6 % | +4.6 % | +4.3 % | +2.7 % |

* Round 24 on five scenarios: THR +0.6 to +3.7 %, LAT at 0.2 x Lsat +7.4 / +5.3 / +4.7 %, at 1.0 x Lsat +3 to +7 %.
* Against the best baseline DLY has THR +3.1 / +8.6 / +7.7 %, LAT -10.2 / -6.8 / -11.4 %, P99 -28.8 / -27.4 / -32.5 %.
* Against DeFT_P at low load DLY is slower by its two cycles at a hop with a choice (question 10), where LF is faster than
  DeFT_P. The hardware gives the same order: LF fits the reference period with margin, DLY only without (question 9).
* LF with one residual cycle (`CI_heurLA_X_LF1`, the addendum; `report/summary_A.md`, A.2) lies between the two in
  latency and has LF's throughput. Against DLY: THR -1.6 / -1.8 / -1.0 %, LAT at 0.2 x Lsat -3.3 / -2.4 / -2.1 %, at
  1.0 x Lsat -1.0 / -1.8 / -2.0 %, P99 +1.9 (=) / +0.2 (=) / -1.3 %. A cycle of waiting added to the lookahead buys no
  throughput (THR against the main row -0.0 (=) / -0.0 (=) / -0.1 (=) %). Which part of DLY gives its 1-2 %, the
  decision at the buffer front or the two cycles it waits there, was not separated in this round.

### 7. Application traces
**The main row's mean latency is 2-4 % below DeFT_P's on every trace and every pair (one exception: bodytrack with
faulty VLs, where the rows are identical), and it never completes later. The traces load the network to a few percent of
its saturation load, so they show the low-load gain of Part B and say nothing about its throughput gain**
(`report/summary_D.md`; the counts of cases and the per-trace details: `report/extra_D.md`; `app_runs.csv`,
`pair_runs.csv`). 2x2, pipe_all 2, seeds
41-43, without faults and with one faulty VL per chiplet (0x1111): nine PARSEC traces alone (protocol of round 13: the
first 700,000 cycles of region 2, dependency mode) and the six pairs of the four heaviest at compression 1 and 2
(protocol of round 15). 630 runs; every run delivered its whole window, none is excluded, no dead-end event.
Descriptive, no test.

Geometric mean over the traces or pairs, relative to DeFT_P of the same trace, mask and seed (MTR and RC run only
without faults):

| runs | mean latency: DeFT_B | MTR | RC | main | second | completion time: DeFT_B | MTR | RC | main | second |
|---|---|---|---|---|---|---|---|---|---|---|
| one application, fault-free | 0.993 | 1.004 | 1.008 | 0.973 | 0.974 | 0.9979 | 0.9975 | 1.0017 | 0.9970 | 0.9970 |
| one application, 0x1111 | 1.015 | | | 0.975 | 0.974 | 1.0038 | | | 0.9974 | 0.9974 |
| two, compression 1, fault-free | 0.995 | 0.981 | 0.995 | 0.973 | 0.974 | 0.9914 | 0.9915 | 1.0074 | 0.9890 | 0.9896 |
| two, compression 1, 0x1111 | 1.019 | | | 0.971 | 0.973 | 1.0087 | | | 0.9899 | 0.9906 |
| two, compression 2, fault-free | 0.999 | 0.977 | 0.992 | 0.974 | 0.976 | 0.9889 | 0.9938 | 1.0118 | 0.9796 | 0.9804 |
| two, compression 2, 0x1111 | 1.018 | | | 0.969 | 0.970 | 1.0149 | | | 0.9838 | 0.9852 |

Per trace, main row relative to DeFT_P:

| trace | offered load (flits/node/cycle) | DeFT_P latency (cycles) | fault-free: latency | completion time | 0x1111: latency | completion time |
|---|---|---|---|---|---|---|
| blackscholes | 0.0028 | 52.1 | 0.977 | 0.9832 | 0.972 | 0.9832 |
| bodytrack | 0.0001 | 20.9 | 0.967 | 1.0000 | 1.000 | 1.0000 |
| canneal | 0.0015 | 65.2 | 0.976 | 1.0000 | 0.972 | 1.0000 |
| dedup | 0.0004 | 41.3 | 0.969 | 1.0000 | 0.974 | 1.0000 |
| ferret | 0.0013 | 40.5 | 0.967 | 0.9963 | 0.977 | 0.9975 |
| fluidanimate | 0.0005 | 44.7 | 0.974 | 1.0000 | 0.966 | 1.0000 |
| swaptions | 0.0019 | 41.6 | 0.965 | 0.9990 | 0.971 | 0.9992 |
| vips | 0.0027 | 54.9 | 0.977 | 0.9966 | 0.967 | 0.9976 |
| x264 | 0.0035 | 45.9 | 0.980 | 0.9978 | 0.979 | 0.9988 |

* **Mean latency against DeFT_P.** The main row is lower in each of the 27 (trace, seed) cases without faults and in each
  of the 72 (pair, mask, compression, seed) cases: 0.965-0.980 per trace (0.7 to 1.6 cycles per packet) and 0.963-0.978
  per pair. With the faulty VLs it is lower in 24 of the 27 single cases (0.966-0.979; 0.9 to 2.1 cycles); the three
  others are bodytrack (412 packets in the window), on which the four rows have the same latency. The second row is
  within 1.1 % of the main row on every trace and pair.
* **Against the other reference rows.** On average DeFT_B is level with DeFT_P without faults (0.993-0.999) and
  1.5-1.9 % above it with them; RC is level with DeFT_P (0.992-1.008). MTR is the reference row that comes closest: over
  the pairs it is at 0.981 and 0.977, and it has the lowest mean latency of all rows on blackscholes alone (by 0.13
  cycles), on two of the six pairs at compression 1 and on three at compression 2, each time within 0.6 % of the main
  row; over the nine single traces it is level with DeFT_P (1.004; +7.8 % on bodytrack). A late-binding row has the
  lowest mean latency on 7 of the 9 traces (DeFT_B on swaptions, by 0.02 cycles), on 4 and 3 of the 6 pairs without
  faults, and on every trace and pair with the faulty VLs (bodytrack: a tie).
* **Completion time.** One application without faults: every row is within 0.4 % of DeFT_P on eight of the nine traces
  and equal to it to four digits on four of them; on blackscholes the main row needs 1.7 % fewer cycles (MTR 1.9 %,
  DeFT_B 1.4 % fewer, RC 0.9 % more). Two applications: the main row needs 1.0-1.1 % fewer cycles than DeFT_P at compression 1 and
  1.6-2.0 % fewer at compression 2, and fewer in every pair (0.980-0.999 and 0.976-0.987). It has the shortest completion
  time of the rows in each of the four groups of pairs, and a late-binding row has it in 23 of the 24 (pair, mask,
  compression) cells. DeFT_B needs 0.9-1.1 % fewer cycles than DeFT_P without faults and 0.9-1.5 % more with them, MTR
  0.6-0.9 % fewer, RC 0.7-1.2 % more.
* **Why the completion time moves at all.** In dependency mode a packet is injected when the packets it depends on have
  arrived, so a lower latency moves a chain forward. blackscholes needs 774,000 cycles for its 700,000-cycle window with
  DeFT_P and is the trace on which the rows differ; the other eight need 695,000-720,000. Compression 2 shortens only the
  pairs without blackscholes (582,000-640,000 cycles instead of 713,000-722,000; the three with blackscholes need
  788,000-801,000 at either compression) and raises the offered load only for them (to 0.0056-0.0069 flits/node/cycle).
* **Load.** The traces offer 0.0001-0.0035 flits/node/cycle alone and 0.0043-0.0069 in pairs. Uniform traffic with
  8-flit packets saturates DeFT_P on 2x2 at 0.104 flits/node/cycle (0.080 with the faulty VLs), so the traces reach at
  most 3.4 % of that alone and 6.6 % in pairs (4.4 % and 8.6 % with the faulty VLs): below the lowest load of Part B
  (0.2 x Lsat). There the main row has
  -2.1 % (-0.8 cycles) against DeFT_P on 2x2 (question 10); the traces give -2.7 % (-0.7 to -1.6 cycles). The gains in
  throughput and in latency near saturation (questions 1-4) cannot appear at this load: the traces neither confirm nor
  contradict them.
* **Earlier rounds.** Rounds 13 and 15 ran the same traces with the one-cycle router model and the late-binding rows of
  that time: 4-7 % lower mean latency than DeFT, completion times within 0.2 % (one application and pairs at compression
  1). With the four-cycle model and the frozen rows the result has the same form: a small latency gain on every trace
  and no trace on which late binding costs time.

### 8. One-cycle router model (Part E): what changes?
**No conclusion changes; two sizes do. The throughput gain is the same in both router models. The latency gain at
1.0 x Lsat is half to three quarters as large with the one-cycle router, because that load lies earlier on the curve
there: at 1.2 x Lsat the gain is 42-51 %, against 49-63 % in the four-cycle model. A decision delay of two cycles costs
the same three cycles per packet in both models, which is twice the share of a latency that is half as long**
(`report/summary_E.md`; the
comparison with the four-cycle model and the values in cycles: `report/extra_E.md`; `pipe0_runs.csv`). `-pipe_all 0`
(Noxim's one-cycle router: two cycles per hop instead of four), the pipe_all 0 ladders of round 23, seeds 141-145;
uniform, hotspot and chipperm without faults and uniform with one faulty VL per chiplet; DeFT_P, DeFT_B, MTR, RC,
`CI_heurLA_X` with an ideal decision (the main row's selection, no delay, no lookahead routing) and `CI_heurLA_X_DLY`.
2,970 runs, none missing, no dead-end event. Descriptive, no test. The four-cycle rows below are the Part B runs
restricted to the same four scenarios and the same four reference rows (E.4). The ideal decision has no row in the
four-cycle model (LF is its buildable form); DLY ran in both.

Against the best baseline of each scenario, over the four scenarios (2x2 / 3x3 / 4x4; every interval excludes zero):

| router model | row | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat | LAT at 0.2 x Lsat against DeFT_P |
|---|---|---|---|---|---|
| one cycle | `CI_heurLA_X`, ideal decision | +6.0 / +13.5 / +10.8 % | -9.4 / -12.8 / -9.9 % | -24.3 / -28.8 / -23.8 % | -2.7 / -3.5 / -2.8 % (-0.6 / -0.9 / -0.9 cycles) |
| one cycle | `CI_heurLA_X_DLY` | +6.4 / +14.6 / +11.2 % | -6.4 / -9.6 / -6.9 % | -25.3 / -30.1 / -24.2 % | +11.2 / +6.2 / +5.7 % (+2.5 / +1.8 / +2.1 cycles) |
| four cycles | `CI_heurLA_X_LF` (main) | +4.5 / +11.8 / +9.8 % | -18.6 / -17.3 / -16.8 % | -35.9 / -40.9 / -37.8 % | -2.1 / -3.4 / -2.9 % (-0.9 / -1.8 / -1.9 cycles) |
| four cycles | `CI_heurLA_X_DLY` | +6.2 / +15.2 / +11.0 % | -14.7 / -13.6 / -12.9 % | -35.3 / -39.3 / -36.4 % | +5.3 / +1.7 / +1.6 % (+2.3 / +1.0 / +1.2 cycles) |

* **Throughput: the same.** DLY, the mechanism that ran in both models, has +6.4 / +14.6 / +11.2 % with the one-cycle
  router and +6.2 / +15.2 / +11.0 % with the four-cycle one. The ideal decision has 1-2 points more than LF. Against
  DeFT_P: +13.9 / +23.0 / +18.1 % (ideal, one cycle) and +12.2 / +22.5 / +18.0 % (LF, four cycles).
* **Latency at 1.0 x Lsat: half to three quarters of the gain, two thirds of the tail gain.** In cycles the late-binding
  row is 5.5 / 8.3 / 7.6 below the best baseline instead of 19.1 / 17.2 / 21.8. The comparison point moves: Lsat is the
  last load before DeFT_P's latency exceeds three times its zero-load latency, that latency is half as long with the
  one-cycle router, and so Lsat is 0-17 % lower while DeFT_P's peak throughput is within 3 % of its four-cycle value in
  10 of the 12 cells. 1.0 x Lsat is 0.83 / 0.80 / 0.83 of DeFT_P's peak throughput in the one-cycle model and 0.91 /
  0.88 / 0.89 in the four-cycle model. Along the ladder the gain in mean latency against the best baseline of each load is

  | router model | row | 0.8 x Lsat | 1.0 x | 1.2 x | 1.4 x |
  |---|---|---|---|---|---|
  | one cycle | ideal | -1.9 / -4.5 / -3.5 % | -9.4 / -12.8 / -9.9 % | -45.8 / -50.5 / -42.0 % | -41.5 / -70.8 / -56.0 % |
  | four cycles | LF | -3.0 / -4.8 / -4.3 % | -18.6 / -17.3 / -16.8 % | -48.6 / -62.5 / -51.6 % | -18.0 / -55.2 / -34.9 % |

  so the gain is not lost with the shorter pipeline; it appears one step later on a ladder that starts lower
  (`report/extra_E.md`, X.9 and X.12).
* **Low load: the same in per cent, half in cycles.** The ideal decision is 2.7 / 3.5 / 2.8 % faster than DeFT_P (LF with
  four cycles: 2.1 / 3.4 / 2.9 %), which is 0.6 / 0.9 / 0.9 cycles instead of 0.9 / 1.8 / 1.9: the gain comes from
  shorter paths (round 24) and a hop takes half as long.
* **The decision delay costs twice as much in relative terms.** Against the row that decides at once, DLY adds 3.1 /
  2.7 / 3.0 cycles per packet at low load with the one-cycle router and 3.2 / 2.8 / 3.1 with the four-cycle one (1.6-1.8
  hops with a choice per packet at 1.0 x Lsat in both, two cycles each). That is +14.2 / +10.0 / +8.7 % of the latency against +7.6 /
  +5.3 / +4.6 %, and DLY ends 6-11 % slower than DeFT_P at low load instead of 2-5 %. At 1.0 x Lsat it adds 3.4 / 3.8 /
  3.3 % (four cycles: 4.9 / 4.6 / 4.7 %), and it buys less throughput: +0.4 / +1.0 / +0.4 (=) % against +1.6 / +3.0 /
  +1.1 %.
* **Per scenario** (ideal decision with one cycle; LF with four cycles from B.3):

  | scenario | one cycle: THR | LAT at 1.0 x Lsat | four cycles: THR | LAT at 1.0 x Lsat |
  |---|---|---|---|---|
  | uniform | +1.0 (=) / +10.9 / +13.9 % | +4.3 / -2.1 (=) / -6.9 % | -1.4 / +10.0 / +13.2 % | +0.8 (=) / -16.7 / -11.2 % |
  | hotspot | +4.5 / +1.4 (=) / +2.1 (=) % | -6.7 / -5.8 / -3.8 % | +2.9 / +2.5 / +2.4 % | -13.9 / -5.2 / -4.8 % |
  | chipperm | +9.4 / +33.2 / +10.6 % | -11.2 / -23.9 / -3.9 (=) % | +7.8 / +25.4 / +8.7 % | -29.4 / -26.0 / -14.3 % |
  | uniform with faults | +9.5 / +10.8 / +17.0 % | -22.1 / -17.7 / -23.3 % | +9.0 / +10.4 / +15.5 % | -28.5 / -20.0 / -33.9 % |

  Of the 12 cells the ideal decision is better than the best baseline in 9 / 9 / 8 (THR / LAT / P99) and worse in one:
  mean latency on 2x2 uniform, +4.3 % against RC. LF with four cycles: better in 11 / 11 / 10, worse in one, the
  throughput on 2x2 uniform (-1.4 % against RC). 2x2 uniform is the cell in which RC is level with late binding in
  both models. DLY with the one-cycle router is better in 11 / 6 / 8 and worse in mean latency in three (2x2 uniform
  +8.1 % against RC; hotspot on 3x3 and 4x4, +0.8 % and +2.5 % against DeFT_B).
* **The reference rows keep their order.** MTR and RC are 4-7 % ahead of DeFT_P in throughput and 11-24 % in mean
  latency with the one-cycle router (four cycles: 2-6 % and 15-29 %). The best baseline is DeFT_B for the throughput in
  7 of the 12 cells and RC for the mean latency in 6, in both models.
* **Beyond the peak: one cell differs.** On 4x4 chipperm with the one-cycle router every row except DeFT_B has its peak
  at 1.4 x Lsat and loses throughput above it: DeFT_P keeps 0.892 of its peak, MTR 0.872, RC 0.886, the two late-binding
  rows 0.833. Above 1.0 x Lsat the late-binding rows accept more than every reference row at every load of that cell
  (0.0444 flits/node/cycle at 2.4 x Lsat against 0.0418-0.0426), but their margin over RC falls from +10.6 % at the
  peak, which is what THR measures, to +4 % at the highest load. No row loses more than 5 % in any other cell of either
  model (`report/extra_E.md`, X.10). The cause was not examined in this round.

### 9. Hardware: area, timing, header bits; which mechanism can be built, and what the evaluated row of that mechanism achieves
Details and tables: `hw/FINDINGS_hw.md`, `report/summary_F.md`. Flow of rounds 18 and 21 (Yosys + ABC, NanGate45, OpenSTA,
pre-layout); DeFT's router and round 18's late-binding router are synthesised again in the same run.

* **What is built.** The interposer router of the three heuristic rows: lookahead routing with the fallback (LF) for XY
  (the main row) and for the VN-split order (the second row), and the decision at the buffer front (DLY) for XY. Buffers,
  allocators and crossbar are the reference core of round 18. The chiplet router is DeFT's with the exit LUT (round 18's),
  on 2x2 with a 96-bit table of the default entry VL.
* **The lookahead needs no bit in the head and no wire between routers.** The decision unit of an input port reads the head
  on the link and its result is stored in the router (two entries per input VC). The price: the decision has two cycles
  (link and route), not the three of W = pipe_all + 1 that a request from the upstream router would give.
* **Header bits.** Two more than DeFT (the 4-bit mask of entry candidates replaces the 2-bit entry VL), four more on 2x2
  (2 bits of default entry VL for the penalty D = 2). The same for all three designs.
* **Area, relative to DeFT** (hierarchy kept / router core kept as one module / flattened; the first is the primary figure
  and an upper bound, the last favours the design):

  | design | interposer router (4x4) | under a VL | all routers of a 2x2 system | of a 4x4 system |
  |---|---|---|---|---|
  | **main row: LF, XY, one register in the decision unit** | 1.41 / 1.23 / 1.12 | 1.48 / 1.31 / 1.20 | 1.25 / 1.16 / 1.10 | 1.22 / 1.13 / 1.08 |
  | second row: LF, VN-split order | 1.66 / 1.40 / 1.32 | 1.70 / 1.46 / 1.38 | 1.38 / 1.24 / 1.20 | 1.34 / 1.21 / 1.17 |
  | DLY, XY, one unit per input port, two registers | 1.33 / 1.22 / 1.17 | 1.40 / 1.29 / 1.26 | 1.21 / 1.16 / 1.13 | 1.18 / 1.13 / 1.10 |
  | round 18: LB-I heuristic, one unit per router | 1.33 / 1.22 / 1.20 | 1.28 / 1.20 / 1.20 | 1.16 / 1.11 / 1.09 | 1.16 / 1.11 / 1.11 |
  | round 18: LB-I heuristic, one unit per input port | 2.44 / 1.68 / 1.70 | 2.46 / 1.75 / 1.76 | 1.74 / 1.32 / 1.33 | 1.71 / 1.35 / 1.36 |

  Chiplet router 1.01-1.02 x DeFT's on 3x3 and 4x4, 1.05-1.06 x on 2x2. In absolute terms (hierarchy kept) all routers of a
  2x2 system take 2.35 mm^2 with DeFT and 2.94 mm^2 with the main row; of a 4x4 system 9.54 and 11.63 mm^2. The VN-split
  order costs a decision unit on every link port instead of on E, W and the Down link only.
* **Timing.** No router of this flow meets 1 ns; the reference pipeline's period is 1.27-1.32 ns (T_ref, DeFT's switch
  allocation). The main row's decision takes **two cycles at T_ref** (one register, margin +0.23 ns; VN-split order
  +0.18 ns) and three at 1 ns (margin +0.07 ns, inside the 0.13 ns spread of the flow). A hop with one offered output keeps
  the four cycles of the reference pipeline; its route stage is shorter than DeFT's (0.66-0.73 ns against 0.86-0.97 ns); the
  fallback sits in the VC-allocation stage (1.08-1.20 ns against DeFT's 1.20-1.26 ns). The longest stage of the main row's
  router is 0.90-0.96 x T_ref: the design does not lengthen the clock.
* **Which mechanism can be built.** **LF with residual delay 0, at the period of the reference pipeline**: every head takes
  four cycles per hop in RTL simulation, so `CI_heurLA_X_LF` as evaluated in Part B is the mechanism that is built, and
  `CI_heurLA_O_LF` likewise. Two conditions: the first decision stage reads the head on the link and leaves 0.28-0.42 ns of
  the link cycle to the wire (DeFT's router leaves 0.82-0.90 ns), and the clock is the reference's, not 1 ns. If either
  fails, the same RTL has one residual cycle for heads with a choice. That row (`CI_heurLA_X_LF1`) was not among the
  frozen ones and was run as a pre-registered addendum (the last item below).
* **DLY** fits the reference period only with one unit per input port and without margin (+0.00 ns with one register,
  +0.06 ns with the two of the evaluated row); with one unit per router it does not fit (0.28 ns over).
* **What the evaluated row of the mechanism achieves** (residual 0, the main row of Part B; 2x2 / 3x3 / 4x4): against the
  best baseline THR +1.5 / +6.7 / +6.6 %, LAT -13.1 / -10.5 / -15.0 %, P99 -27.8 / -27.9 / -34.2 %, all nine tests
  supported; against DeFT_P, whose router it extends, THR +10.6 / +16.5 / +14.8 %, LAT -32.0 / -37.3 / -39.9 %, P99
  -52.3 / -67.0 / -70.9 %, and 0.8-1.6 cycles less latency at low load. The price is 1.25 / 1.22 / 1.22 times the router
  area of a DeFT system (hierarchy kept; 1.10 / 1.08 / 1.08 flattened) and two header bits (four on 2x2).
* **What the row achieves if either condition fails** (one residual cycle, `CI_heurLA_X_LF1`; the addendum:
  `PREREGISTRATION_addendum.md`, `report/summary_A.md`, `report/extra_A.md`; the Part B design, 2,160 runs): **9 of 9
  tests supported** (Holm over the nine). Against the best baseline THR +1.5 / +6.7 / +6.5 %, LAT -11.1 / -8.5 / -13.2 %,
  P99 -27.4 / -27.3 / -33.3 %; against DeFT_P THR +10.6 / +16.5 / +14.7 %, LAT -30.5 / -35.9 / -38.6 %, P99 -52.1 /
  -66.7 / -70.6 %. The hardware is the main row's RTL with at most one more register in the decision unit: 1.26 / 1.23 /
  1.23 times the router area of a DeFT system with two registers (hierarchy kept; 1.12 / 1.10 / 1.10 flattened), the
  same header bits.
  * *The cycle costs latency and no throughput.* Against the main row: THR -0.0 (=) / -0.0 (=) / -0.1 (=) %; LAT +3.7 /
    +2.7 / +2.4 % at 0.2 x Lsat (+1.41 / +1.35 / +1.49 cycles) and +2.2 / +2.3 / +2.2 % at 1.0 x Lsat (+1.38 / +1.75 /
    +2.36 cycles); P99 +0.5 (=) / +0.8 (=) / +1.3 %. At low load it is one cycle per hop with a choice (1.00 / 1.02 /
    1.04 cycles; a packet has 1.3-1.4 such hops on average; `report/extra_A.md`, Y.7). The addendum had stated in
    advance: 2-4 % at low load, 2-3 % at 1.0 x Lsat, THR within 1 %.
  * *The latency advantage over DeFT_P at low load is gone.* LAT at 0.2 x Lsat against DeFT_P: +1.5 / -0.5 / -0.1 %
    (+0.60 / -0.25 / -0.08 cycles); the main row has -2.1 / -3.1 / -2.5 %, DLY +5.0 / +2.0 / +2.0 %.
  * *Per cell* it is better than the best baseline in 18 / 19 / 18 of the 24 cells in THR / LAT / P99, the counts of the
    main row. One loss is added, the mean latency on 2x2 uniform (+3.3 % [+0.8, +5.9] against RC), and one of the main
    row's is inside the interval here (THR on the 3x3 moving hotspot, -1.0 % [-2.4, +0.3]). On the three scenarios the
    tuning did not see, its mean latency is 1.7 (=) / 2.3 / 3.4 % above the best baseline's (main row: 0.0 (=) / +0.3 (=)
    / +1.4 (=) %); on the five it saw, THR +4.0 / +10.5 / +9.1 % and LAT -18.1 / -14.3 / -21.8 %.
  * *The stored decision is used one cycle later.* At 1.0 x Lsat 2.1 / 2.6 / 2.2 % of the stored decisions differ from a
    fresh one (main row 1.8 / 2.3 / 1.9 %) and the fallback is taken at 6.9 / 7.8 / 9.3 % of the hops with a choice
    (6.8 / 7.5 / 8.8 %). Beyond the peak the row keeps 0.992 / 0.995 / 0.998 of its peak throughput on average.
  * So the result of the round does not rest on the two conditions. With the residual cycle the design keeps its
    throughput and most of its latency gain against the best baseline (-11.1 / -8.5 / -13.2 % of -13.1 / -10.5 /
    -15.0 %). At low load it is within 0.5 % of DeFT_P on 3x3 and 4x4 and 0.6 cycles slower on 2x2, where the main row
    is one to two cycles faster.

### 10. Low-load latency and the accepted throughput beyond the peak: as in v24?
**Yes, both** (`report/summary_B.md`, B.9-B.11; eight scenarios here, five in round 24).
* **Low-load latency against DeFT_P** (2x2 / 3x3 / 4x4; round 24 in brackets):

  | row | LAT at 0.2 x Lsat | in cycles | LAT at 0.5 x Lsat |
  |---|---|---|---|
  | `CI_heurLA_X_LF` (main) | -2.1 / -3.1 / -2.5 % (-1.8 / -3.1 / -2.6) | -0.8 / -1.6 / -1.6 (-0.7 / -1.6 / -1.7) | -2.4 / -2.8 / -2.2 % (-2.4 / -2.9 / -2.2) |
  | `CI_heurLA_O_LF` (second) | -2.0 / -3.1 / -2.6 % | -0.8 / -1.6 / -1.6 | -1.7 / -2.8 / -2.5 % |
  | `CI_heurLA_X_DLY` | +5.0 / +2.0 / +2.0 % (+5.5 / +1.9 / +1.9) | +2.0 / +1.0 / +1.3 (+2.2 / +1.0 / +1.3) | +4.1 / +2.1 / +2.3 % |
  | `CI_qlLA_X_LF` | +2.5 / -0.5 / -0.2 % (+2.8 / -0.5 / -0.3) | +1.0 / -0.3 / -0.1 | +1.9 / -0.6 / -0.3 % |
  | `CI_heurLA_X_LF1` (addendum; not in round 24) | +1.5 / -0.5 / -0.1 % | +0.60 / -0.25 / -0.08 | +1.0 / -0.1 (=) / +0.1 (=) % |
  | MTR (six fault-free) | +2.8 / +2.4 / +2.1 % (+2.8 / +2.3 / +1.9) | +1.1 / +1.2 / +1.3 | +0.6 / +0.7 / +0.5 % |
  | RC (six fault-free) | +0.9 / +0.8 / +0.8 % (+1.0 / +0.9 / +0.8) | +0.4 / +0.4 / +0.5 | -1.5 / -1.0 / -0.7 % |

  The two frozen LF rows of the heuristic, which have no residual cycle, are the only rows faster than DeFT_P at
  0.2 x Lsat on every size; every interval excludes zero. The gain is one to two cycles per packet. One residual cycle
  takes it away: the addendum row and the Q-learning row, which both have one, are 1.5-2.5 % slower than DeFT_P on 2x2
  and within 0.5 % of it on 3x3 and 4x4.
* **Beyond the peak** (mean accepted throughput relative to the row's peak, at the lowest point after the peak; mean over
  the scenarios, worst scenario in brackets): main row 0.992 (0.979) / 0.995 (0.971) / 0.997 (0.987), the worst always on
  localized; the addendum row 0.992 (0.980) / 0.995 (0.975) / 0.998 (0.991), also on localized; DeFT_P 0.991 (0.962) /
  0.998 (0.989) / 0.996 (0.988); MTR 0.998 / 0.996 / 0.993; RC 0.995 / 0.999 / 0.993.
  The main row never falls by more than 1 % from one load to the next in 7 / 7 / 8 of the 8 scenarios. Round 24: the
  late-binding rows kept 98.6-100 % on average. DeFT_Ran loses the most of all rows (0.940 / 0.925 / 0.962 on average, 0.909
  in its worst scenario).
* **Decision hops** (main row at 1.0 x Lsat): 17.1 / 13.0 / 11.1 % of all hops and 27.0 / 18.8 / 14.9 % of the interposer
  hops offer more than one output (round 24: 17 / 13 / 11-12 % and 26 / 18-19 / 14-15 %), 1.5 / 1.5 / 1.6 per packet over
  the eight scenarios and 1.6 / 1.7 / 1.8 on uniform (round 24: 1.6-1.8). The fallback is taken at 6.8 / 7.5 / 8.8 % of
  those hops (round 24: 6.6-9.4 %); 1.8 / 2.3 / 1.9 % of the stored decisions differ from a fresh one (round 24: 1.4-2.3 %).
