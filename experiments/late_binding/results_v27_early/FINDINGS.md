# Findings v27: early against late binding

Status: **in progress.** Done: the regression before and after the code change, the anchor row, the unit checks of the new
options, the drain tests of the new rows, the pre-registration, the tuning (Part B) and the addendum with the frozen
values, the reuse check of Part E, Part D. Not done yet: the evaluation (Part C) and the fault runs (Part E). Every
answer below says whether it is final.

**The question of the round.** Every reference of rounds 23 to 26 chooses the entry VL without looking at the network. So
those rounds cannot say how much of the main row's gain over DeFT comes from binding the entry VL late, on the interposer,
and how much from choosing it by congestion at all. This round adds rows that choose by congestion but bind early: at
injection (`EB_vl`, `EB_route`, `EB_vl64`) or at the Down move (`EB_down`); and the main row without the occupancy reports
across the VLs (`LB_noVLrep`). Nothing of the frozen configuration is retuned and no existing row is changed.

## Safety of the new rows (A3)
**No new proof and no new model check are needed, and after reading the code path I agree with that.** Each new row either
restricts the checked relation or leaves it unchanged.
* **`EB_vl`, `EB_route`, `EB_vl64`.** `chooseMasks` gives the head one exit VL (the LUT's, a functional VL of the source
  chiplet) and one entry VL chosen among the functional VLs of the destination chiplet. With one-candidate masks and XY in
  both layers the relation is the fixed-pair relation `A_fixed_XY` of the formal model, which explores every functional
  (exit, entry) pair: it is the relation of DeFT with any injection-time choice. The three options change which functional
  entry VL is chosen (`oracle_beta`, `oracle_scope`, `oracle_period` only enter the cost), never the set it is chosen from.
* **`EB_down`.** Until the Down move the head is a head of the main row. The entry mask is not read in the source chiplet:
  the moves there depend on the exit mask, and the virtual network is assigned from the exit mask alone
  (`assignSourceVirtualNetwork`, `sourceCanUseEitherVirtualNetwork`). At the Down move the mask is replaced by one of its
  own members (`commitEntry` only ever writes `bit(v)` for a candidate v of the mask), and the stored lookahead decision is
  computed for the reduced mask. From there the head is a fixed-pair head with that entry VL. So every path of `EB_down` is
  a path of `A_fixed_XY`. It is also a path of the main row's relation `CI_XY_XY`: with fewer candidates a head is offered
  a subset of the moves it is offered with more (the monotonicity that round 26 tested on every mask of 2x2), and the one
  remaining candidate is reachable by XY from every interposer router.
* **`LB_noVLrep`.** The relation is the main row's, unchanged. The option changes one term of the cost by which the
  selection orders the offered outputs; the offered outputs are the same.
* What was checked by simulation: no hop of an `EB` run offers more than one output (every run of the unit checks; this is
  checked again in every run of Parts B, C and E), and the drain tests below.

## The thirteen questions

### 1. Regression and gates: all pass? Is the anchor row identical to DeFT_P?
*Final.*
**All pass, and the anchor row is identical to DeFT_P.**
* **Regression** (`regression_before.md`, `regression.md`): 84 / 84 byte-identical to the d641861 build before the change,
  and after it with the options absent and with every option given at its default.
* **Anchor** (`anchor.md`): **identical.** DEFT_LB with both VLs from the LUT, XY in both layers and DeFT-P's options gives
  DeFT_P's results in 18 of 18 runs (six fault-free scenarios, three sizes, 1.0 x Lsat, seed 101): every performance field
  of the summary, the delay statistics and the packets per VL. Only the energy fields differ, because the power model
  charges the routing function by its name.
* **Unit checks** (`unit_checks.md`): all pass. `entry_stats` changes no statistic of the main row (18 / 18 runs
  identical). `entry_commit down` changes nothing when every chiplet has one functional VL (3 / 3 runs identical). Where
  D = 0 (3x3, 4x4) the output of the committed candidate is a cheapest output of the main row's selection at the same
  router and moment in 12,000 of 12,000 sampled heads (554 of them ties, where the two may break the tie differently); on
  2x2, where D = 2 is charged to a different thing, in 5,977 of 6,000.
* **Drain tests** (`drain_v27.csv`): the five new rows on six masks per size (fault-free, the same VL faulty in every
  chiplet, mask 1 of each of the four fault rates of round 26): **90 / 90 pass**, every packet delivered, the network
  empties, no dead-end event. The three tuned rows again with their chosen values (`drain_v27_tuned.csv`): **54 / 54
  pass**.
* **The binding is early:** no hop of an `EB` run offers more than one output, in every run so far (unit checks, drain
  tests and the 1,680 tuning runs of the three tuned rows).
* **`EB_vl` with `oracle_beta 0`** (description): the entry VL of fewest hops is DeFT-P's entry VL for 51 to 53 % of the
  packets in five of the six scenarios and for 41 to 46 % under hotspot traffic. So "nearest" and DeFT-P's LUT agree for
  about half of the packets.

### 2. The tuned `oracle_beta` of `EB_vl`, `EB_route` and `EB_vl64`, and their scores next to the main row's
*Final.* From `tuning_v27.md` and `tuning_choice_v27.json` (`tune_runs.csv`: 1,840 runs, seeds 101 and 102, no dead-end
event, no hop of an `EB` run offers more than one output). Scores are in natural-log units against DeFT-P, higher is
better; the three terms of the score are given as percentages against DeFT-P over the five tuning scenarios.

| size | row | `oracle_beta` | score | THR | LAT at 1.0 x Lsat | LAT at 0.5 x Lsat |
|---|---|---|---|---|---|---|
| 2x2 | main row (frozen, not tuned here) | | **+0.530** | +10.6 % | -33.4 % | -2.3 % |
| 2x2 | `EB_vl` | **0.5** | -0.893 | -8.7 % | +115.7 % | +3.4 % |
| 2x2 | `EB_route` | **2** | -0.597 | -6.1 % | +58.9 % | +7.4 % |
| 2x2 | `EB_vl64` | **0.25** | -1.094 | -10.5 % | +149.9 % | +6.9 % |
| 4x4, and 3x3 by the rule | main row (frozen, not tuned here) | | **+0.648** | +17.5 % | -37.3 % | -2.0 % |
| 4x4, and 3x3 by the rule | `EB_vl` | **1** | -1.276 | -13.4 % | +201.2 % | +3.0 % |
| 4x4, and 3x3 by the rule | `EB_route` | **4** | -0.116 | +2.1 % | +8.9 % | +5.3 % |
| 4x4, and 3x3 by the rule | `EB_vl64` | **1** | -1.406 | -14.4 % | +232.7 % | +5.0 % |

* **No chosen value lies at an end of the grid** {0.125, ..., 8}, so the grid was not extended. The values are frozen in
  the addendum of `PREREGISTRATION.md`.
* **With its best value every early row scores below DeFT-P; the main row scores +0.53 and +0.65.** On the tuning
  scenarios the tuned early rows are not between DeFT-P and the main row, they are behind DeFT-P. The one that comes near
  DeFT-P is `EB_route` on 4x4 (THR +2.1 %, LAT at 1.0 x Lsat +8.9 %). I had expected `EB_route` between DeFT-P and the main
  row on the larger sizes; on the tuning scenarios it is not.
* **The mean hides a split by traffic** (`tuning_by_scenario_v27.md`; two seeds per cell, so pointers and no more).
  Under **hotspot** traffic the three early rows are close to the main row: THR +16 to +20 % against the main row's
  +19.9 % on 2x2 and +28.7 to +29.0 % against +30.5 % on 4x4; LAT at 1.0 x Lsat -51 to -52 % against -56 % and -31 to
  -32 % against -33 %. Under **uniform** traffic `EB_route` is level with DeFT-P or ahead of it on 4x4 (LAT -12 % without
  faults, -22 % with one faulty VL per chiplet, against the main row's -36 % and -40 %) and behind it on 2x2; `EB_vl` and
  `EB_vl64` are behind DeFT-P on both sizes. Under **chipperm and chiptrans** traffic every early row has a negative
  score at every value of the grid: under chipperm `EB_vl` has 30 % (2x2) and 46 % (4x4) less throughput than DeFT-P and
  10 and 8.6 times its latency at 1.0 x Lsat.
* **The result does not hang on the chosen value.** In no tuning scenario does any value of the grid bring an early row
  to the main row's score. The closest is `EB_route` under hotspot traffic on 4x4: +0.722 against +0.729.
* The early rows have one free parameter each, tuned here. The main row's parameters were tuned in round 24 by the same
  score on the same scenarios and seeds, and are frozen since.

### 3. Primary family: how many of 18 supported, which against?
*Pending.*

### 4. Which share of the main row's gain over DeFT_P does each early row reach, in THR and in LAT, per size?
*Pending.*

### 5. Which of `EB_vl` and `EB_route` is better, and where?
*Pending.*

### 6. Per scenario: where is an early row level with or ahead of the main row?
*Pending.*

### 7. Latency below saturation (0.2, 0.5, 0.8 x Lsat): all rows
*Pending.*

### 8. `EB_vl64` against `EB_vl`: what does the age of the information cost?
*Pending.*

### 9. Why do the injection-time rows lose or win: balance over the entry VLs, path length, age of the choice
*Pending.*

### 10. `EB_down`: is it different from DeFT_P?
*Pending.*

### 11. `LB_noVLrep`: what do the reports across the VLs buy?
*Pending.*

### 12. Part D: the table, and whether it agrees with the numbers above
*Final (no new runs; `report/summary_D.md`, `paper_data/latency_by_load_v25.csv`).* **It agrees: all 15 numbers of the
independent computation are reproduced to the printed decimal.**

Mean latency of the main row against the best reference (the best of DeFT_P, DeFT_B, MTR, RC, XY_SP per scenario, size and
load), from the runs of round 25 (six fault-free scenarios, seeds 121-130), in % with the 95 % interval over the seeds;
negative = the main row is faster. In brackets after it: the share of the offered load that the main row delivers and the
largest share of a reference.

| load (x Lsat) | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| 0.2 | +2.0 [+1.7, +2.2] | +1.5 [+1.3, +1.6] | +0.9 [+0.7, +1.1] |
| 0.5 | -0.5 [-0.7, -0.3] | 0.0 [-0.2, +0.1] | +0.4 [+0.3, +0.6] |
| 0.8 | -0.1 [-0.6, +0.4] | -0.6 [-1.0, -0.2] | +0.7 [+0.3, +1.1] |
| 1.0 | -11.0 [-13.2, -8.8] | -9.7 [-10.9, -8.4] | -13.2 [-14.6, -11.7] |
| 1.2 | -29.2 [-31.7, -26.7] (0.987 / 0.953) | -49.7 [-51.8, -47.5] (0.995 / 0.941) | -39.4 [-40.5, -38.4] (0.987 / 0.933) |
| 1.4 | +1.1 [-1.5, +3.8] (0.889 / 0.871) | -40.3 [-42.6, -38.0] (0.934 / 0.843) | -21.8 [-22.9, -20.6] (0.917 / 0.834) |
| 1.6 | +5.9 [+4.2, +7.6] (0.792 / 0.780) | -11.9 [-13.7, -10.0] (0.845 / 0.769) | -9.5 [-12.1, -6.9] (0.834 / 0.750) |
| 2.0 | +5.0 [+3.7, +6.2] (0.657 / 0.645) | +6.0 [+3.1, +8.9] (0.717 / 0.658) | +8.5 [+6.6, +10.5] (0.697 / 0.633) |
| 2.4 | +7.7 [+7.2, +8.3] (0.565 / 0.554) | +4.7 [+2.4, +7.1] (0.624 / 0.575) | +16.6 [+12.4, +21.0] (0.604 / 0.555) |

* **Below saturation the main row buys nothing and costs little.** At 0.2 x Lsat it is 0.9 to 2.0 % slower than the best
  reference, which there is XY_SP (shortest paths) in 17 of the 18 cells; against DeFT_P it is faster at that load (2x2
  uniform: 37.1 against 37.9 cycles). At 0.5 and 0.8 x Lsat it is within 0.7 % of the best reference (RC in most cells).
* **The gain is around saturation:** 10 to 13 % at 1.0 x Lsat and 29 to 50 % at 1.2 x Lsat, where the main row still
  delivers 99 % of the offered load and no reference more than 95 %.
* **Far above saturation the sign turns, and the number no longer compares like with like.** From 1.4 x Lsat on no row
  delivers the offered load, and the mean latency is that of the packets that arrived. At 2.0 and 2.4 x Lsat the main row
  has 5 to 17 % more latency than the best reference (MTR in most cells) and delivers 2 to 10 % more. The largest cells are
  hotspot on 3x3 and 4x4 (4x4 at 2.0 x Lsat: 653 against 321 cycles, with 0.761 against 0.614 of the offered load
  delivered): the row that delivers more of the packets to the hot nodes has their waiting time in its mean.
* **Scenarios in which the main row is behind the best reference at 1.0 x Lsat** (known from round 25): localized on 2x2
  (+8.4 %, RC; at 1.4 x Lsat RC also delivers more: 0.900 against 0.826) and movinghot on 3x3 (+11.1 %, MTR) and 4x4
  (+14.1 %, RC), at the same delivered share.

### 13. Part E: do the early rows behave differently under faults?
*Pending.*
