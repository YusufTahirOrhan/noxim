# Findings v27: early against late binding

Status: **in progress.** Done: the gates, the pre-registration, the tuning (Part B) and the addendum with the frozen
values, the evaluation (Part C, 11,340 runs), Part D, the reuse check of Part E. Not done yet: the fault runs (Part E,
question 13). Every answer below says whether it is final.

**The question of the round.** Every reference of rounds 23 to 26 chooses the entry VL without looking at the network. So
those rounds cannot say how much of the main row's gain over DeFT comes from binding the entry VL late, on the interposer,
and how much from choosing it by congestion at all. This round adds rows that choose by congestion but bind early: at
injection (`EB_vl`, `EB_route`, `EB_vl64`) or at the Down move (`EB_down`); and the main row without the occupancy reports
across the VLs (`LB_noVLrep`). Nothing of the frozen configuration is retuned and no existing row is changed.

## The answer in short
**The gain comes from binding late. Choosing the entry VL by congestion and binding it early does not earn a part of the
gain: it loses against DeFT's table. The one exception is hotspot traffic, where choosing by congestion is what counts
and an early choice is nearly as good as a late one.**
* **All 18 tests of the primary family are supported, none against** (question 3). The main row has 7 to 43 % more
  throughput than `EB_vl`, `EB_route` and `EB_down` and 32 to 81 % less latency at 1.0 x Lsat, on every size.
* **The early rows are not between DeFT_P and the main row. They are behind DeFT_P** (question 4): `EB_vl` by 8 to 15 % in
  throughput, `EB_down` by 14 and 22 % on 3x3 and 4x4. The best of them, `EB_route`, is level with DeFT_P on 3x3 and 4x4 and
  behind it on 2x2. This holds although the injection-time rows read the state of the whole network at no cost and with
  no delay, which no real source could, and although their one parameter was tuned for them.
* **`EB_down` is the cleanest evidence** (question 10). It uses the main row's own cost and commits to the main row's own
  first choice; only the freedom to change the entry VL on the interposer is taken away. That costs 6.5 / 24.7 / 30.0 %
  of throughput.
* **Hotspot traffic is the exception** (questions 6 and 9): there every row that looks at the network is 17 to 23 % ahead
  of DeFT_P in throughput, and the early rows reach 77 to 100 % of the main row's gain. The hot spot does not move and the
  rest of the network is not loaded, so what a source reads at injection is still true when the packet arrives. Where the
  hot spot moves (movinghot), the early rows are behind DeFT_P again.
* **The occupancy reports across the VLs buy nothing measurable** (question 11): the main row without them is within
  0.2 % in throughput and 0.1 % in latency.
* **Below saturation an early row is never the better choice** (question 7): at 0.2 x Lsat all rows are within 3 %, from
  0.5 x Lsat on the early rows are slower than DeFT_P.
* What this does not show is in "Limits" at the end: the early rows are greedy choices of one kind, and a method that
  reserves or randomizes at injection was not tried.

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
*Final (`report/summary_C.md` C.1, `report/primary.csv`; 11,340 of 11,340 runs, seeds 161-170, no dead-end event, no hop of
an `EB` row offers more than one output).* **18 of 18 supported; none against; none not significant.** On every size the
main row has more throughput and less latency at 1.0 x Lsat than each of `EB_vl`, `EB_route` and `EB_down`.

Effect of the main row against the early row, in % with the 95 % interval over the ten seeds:

| size | early row | THR | LAT at 1.0 x Lsat |
|---|---|---|---|
| 2x2 | `EB_vl` | +20.0 [+19.4, +20.6] | -68.0 [-68.5, -67.3] |
| 2x2 | `EB_route` | +17.3 [+16.6, +17.9] | -59.9 [-61.0, -58.7] |
| 2x2 | `EB_down` | +6.9 [+6.4, +7.4] | -46.8 [-48.5, -45.1] |
| 3x3 | `EB_vl` | +23.6 [+22.9, +24.3] | -73.5 [-74.5, -72.4] |
| 3x3 | `EB_route` | +15.8 [+15.5, +16.1] | -32.4 [-33.8, -31.0] |
| 3x3 | `EB_down` | +32.8 [+32.2, +33.5] | -81.4 [-82.1, -80.7] |
| 4x4 | `EB_vl` | +31.8 [+31.1, +32.5] | -77.2 [-77.8, -76.6] |
| 4x4 | `EB_route` | +12.4 [+12.0, +12.8] | -41.0 [-41.6, -40.3] |
| 4x4 | `EB_down` | +42.9 [+42.2, +43.7] | -80.3 [-80.7, -79.9] |

* The largest Holm-adjusted p of the 18 is 1.4e-10 (2x2, `EB_down`, THR). The smallest effects are those of `EB_down` on 2x2
  in THR (+6.9 %) and of `EB_route` on 3x3 in LAT (-32.4 %).
* `check_v27_family.py` computes the 18 tests from `eval_runs.csv` without the report's code: all 18 agree, the largest
  difference of an effect or of an interval end is 0.005 percentage points (`report/families_check.md`). Fifteen numbers
  outside the family that this file quotes (shares, per-scenario effects, latencies at other loads) were also computed a
  second time by hand-written code and agree to the printed decimal.
* The test I had named as most at risk, the main row against `EB_route` on 2x2, is +17.3 % and -59.9 %.
* The latency numbers compare rows at 1.0 x Lsat of DeFT-P, where `EB_vl` and `EB_down` are past their own saturation
  (their packets wait 110 to 510 cycles at the source, those of the main row 3 to 6; question 9). "-68 %" says that one
  row is saturated there and the other is not; THR and the latencies of question 7 are the plainer comparison.

### 4. Which share of the main row's gain over DeFT_P does each early row reach, in THR and in LAT, per size?
*Final (`report/summary_C.md` C.2, `paper_data/early_late_effects.csv`).* **None worth the name: eight of the nine THR
shares and eight of the nine LAT shares of the three rows of the family are negative, which means that the row is behind
DeFT_P itself.** Share = (mean log ratio of the row against DeFT_P) / (that of the main row); in brackets the smallest
and the largest of the ten per-seed shares.

| size | row | THR against DeFT_P | share of the main row's THR gain | LAT against DeFT_P | share of the main row's LAT gain |
|---|---|---|---|---|---|
| 2x2 | main row | +7.5 % | 100 % | -35.5 % | 100 % |
| 2x2 | `EB_vl` | -10.4 % | -151 % [-173, -132] | +101.3 % | -160 % [-200, -136] |
| 2x2 | `EB_route` | -8.3 % | -119 % [-138, -96] | +60.7 % | -108 % [-135, -87] |
| 2x2 | `EB_down` | +0.6 % | 8 % [-5, 20] | +21.3 % | -44 % [-73, -20] |
| 3x3 | main row | +13.6 % | 100 % | -37.6 % | 100 % |
| 3x3 | `EB_vl` | -8.0 % | -66 % [-83, -53] | +135.2 % | -181 % [-309, -130] |
| 3x3 | `EB_route` | -1.9 % | -15 % [-26, -3] | -7.7 % | 17 % [-4, 29] |
| 3x3 | `EB_down` | -14.4 % | -122 % [-136, -101] | +235.9 % | -257 % [-400, -179] |
| 4x4 | main row | +11.7 % | 100 % | -37.4 % | 100 % |
| 4x4 | `EB_vl` | -15.2 % | -149 % [-165, -138] | +175.1 % | -216 % [-319, -155] |
| 4x4 | `EB_route` | -0.6 % | -5 % [-14, 3] | +6.1 % | -13 % [-50, 6] |
| 4x4 | `EB_down` | -21.8 % | -222 % [-257, -204] | +218.0 % | -247 % [-362, -184] |

* **The best early row is `EB_route` on 3x3 and 4x4, and it is level with DeFT_P, not between DeFT_P and the main row:**
  -1.9 % and -0.6 % in THR, -7.7 % and +6.1 % in LAT. Its 99th percentile is better than DeFT_P's there (-32 % and -21 %).
  On 2x2 it is behind DeFT_P.
* `EB_vl64` (not in the family): -182 / -87 / -162 % of the THR gain and -238 / -214 / -234 % of the LAT gain.
  `LB_noVLrep`: 99 / 100 / 101 % and 100 / 100 / 100 % (question 11).
* **The means over the six scenarios hide one scenario in which the shares are high.** Under hotspot traffic the
  injection-time rows reach 77 to 84 % of the main row's THR gain on 2x2 and 96 to 100 % on 3x3 and 4x4, and 87 to 98 %
  of its LAT gain; `EB_down` reaches 83 to 93 % and 95 to 98 %. In the other five scenarios the shares of `EB_vl`,
  `EB_vl64` and `EB_down` are negative on 3x3 and 4x4, and the largest share of `EB_route` on any size is 19 %; on 2x2
  `EB_down` reaches 22 to 35 % of the small THR gain under uniform, localized and movinghot traffic (question 6).

### 5. Which of `EB_vl` and `EB_route` is better, and where?
*Final (`report/summary_C.md` C.4).* **`EB_route`, on every size, and by more the larger the system.** Reading the queues on
the route beats reading the occupancy at the entry VL.

| size | `EB_route` against `EB_vl`: THR | LAT at 1.0 x Lsat | P99 | scenarios in which `EB_route` is the better one: THR | LAT |
|---|---|---|---|---|---|
| 2x2 | +2.3 [+1.7, +2.9] | -20.2 [-22.7, -17.5] | -16.5 [-19.8, -13.0] | 3 of 6 | 4 of 6 |
| 3x3 | +6.7 [+5.9, +7.5] | -60.8 [-62.4, -59.1] | -72.4 [-74.0, -70.6] | 6 of 6 | 5 of 6 |
| 4x4 | +17.2 [+16.6, +17.9] | -61.4 [-62.5, -60.3] | -66.2 [-67.1, -65.4] | 6 of 6 | 5 of 6 |

* **Where `EB_vl` is the better one:** under hotspot traffic in LAT on every size, by 1.5 to 4.6 points against the main
  row (the two are within 1.3 % in THR there), and on 2x2 also under movinghot traffic in LAT. On 2x2 it also has the
  higher mean THR under localized, chiptrans and movinghot traffic, by 0.3 points or less, which is inside the intervals:
  ties. Nowhere else.
* **Where the difference is largest:** chipperm and uniform traffic on 4x4. Under chipperm `EB_vl` has 45.7 % less
  throughput than DeFT_P and `EB_route` 10.4 % less; under uniform traffic -12.7 % against +1.8 %.
* Against the main row both are behind on every size: the main row against the better of the two, chosen per size,
  scenario and metric, is +17.1 / +15.8 / +12.4 % in THR and -58.9 / -32.2 / -40.8 % in LAT.

### 6. Per scenario: where is an early row level with or ahead of the main row?
*Final (`report/summary_C.md` C.6, `paper_data/early_late_per_scenario.csv`).* **Only under hotspot traffic, only on 3x3 and
4x4, only in throughput, and level, not ahead.** In no cell of size x scenario x early row x metric (216 cells) is an early
row ahead of the main row with an interval that excludes 0.

* **Hotspot, 3x3 and 4x4, THR: level.** The three injection-time rows are within 0.7 % of the main row and no interval
  excludes 0 (3x3: -0.7, -0.2, -0.7 %; 4x4: -0.3, 0.0, 0.0 % for `EB_vl`, `EB_route`, `EB_vl64`). In LAT they are behind by
  1.8 to 6.1 %, and those intervals exclude 0. `EB_down` is behind in both (THR -3.1 and -3.2 %, LAT +3.7 and +1.6 %).
* **Hotspot, 2x2: behind, by little.** THR -3.2 to -4.5 %, LAT +8 to +16 % for the injection-time rows; `EB_down` -1.5 %
  and +5.2 %.
* **The other five scenarios: behind on every size, in both metrics, every interval excluding 0.** The smallest gaps are
  those of `EB_route` under movinghot traffic on 3x3 and 4x4 (THR -6.7 and -5.5 %, LAT +36 and +25 %) and of `EB_down` on
  2x2 under localized, uniform and movinghot traffic (THR -1.2 to -3.3 %, LAT +20 to +33 %). The largest are under
  chipperm traffic: `EB_vl` has 34 to 50 % less throughput than the main row and 7 to 16 times its latency at 1.0 x Lsat.
* **Against DeFT_P the split is the same.** Under hotspot traffic every early row is far ahead of DeFT_P on every size
  (THR +16.8 to +23.0 %, LAT -56.5 to -70.5 %), as the main row is (+20.6 to +23.0 %, -57.9 to -71.3 %). In the other five
  scenarios the early rows are behind DeFT_P. The exceptions whose interval excludes 0: `EB_route` under uniform traffic
  on 4x4 (THR +1.8 %, LAT -6.2 %) and, in LAT only and with less throughput, on 3x3 (-6.2 %); `EB_down` on 2x2 under
  uniform traffic (THR +1.8 %). In five more cells the mean of an early row is on the good side of DeFT_P with an interval
  that includes 0. The main row is ahead of DeFT_P in all 36 cells of size x scenario x metric, every interval excluding 0.

So the answer to the question of the round has two parts. **Under hotspot traffic the gain comes from choosing the entry
VL by congestion at all:** every row that looks at the network gets it, and a row that binds early is 0 to 4.5 % behind
the main row in THR and 2 to 16 % in LAT. **Under the other five kinds of traffic the gain comes from binding late:** the
rows that choose by congestion and bind early do not get a part of it. They lose against the table of DeFT.

### 7. Latency below saturation (0.2, 0.5, 0.8 x Lsat): all rows
*Final (`report/summary_C.md` C.7 and C.10, `report/extra_C.md`).* **At 0.2 x Lsat every row is within 1.6 cycles (3 %) of
every other. From 0.5 x Lsat on only the main row (with or without the reports) is still faster than DeFT_P; the early
rows are slower than DeFT_P at half its saturation load and far slower at 0.8.** Mean latency against DeFT_P, in %, 2x2 /
3x3 / 4x4 (mean over the six scenarios and the ten seeds; the intervals are in the report, at 0.2 x Lsat at most 0.4
points wide):

| row | 0.2 x Lsat | 0.5 x Lsat | 0.8 x Lsat |
|---|---|---|---|
| main row | -1.8 / -2.7 / -2.2 | -2.0 / -2.2 / -1.7 | -7.4 / -7.4 / -6.0 |
| `LB_noVLrep` | -1.9 / -2.7 / -2.2 | -2.1 / -2.2 / -1.7 | -7.5 / -7.4 / -6.0 |
| `EB_vl` | -2.2 / -1.9 / -1.5 | +4.2 / +2.9 / +4.4 | +97.7 / +33.2 / +108.9 |
| `EB_route` | +0.1 / -0.2 / +0.3 | +8.1 / +5.8 / +6.6 | +19.9 / +9.7 / +15.4 |
| `EB_vl64` | -2.0 / -1.7 / -1.3 | +6.9 / +6.5 / +8.4 | +136.2 / +68.1 / +131.2 |
| `EB_down` | -2.0 / -2.6 / -1.9 | -1.2 / +7.1 / +22.4 | +3.3 / +166.6 / +232.2 |

In cycles at 0.2 / 0.5 / 0.8 x Lsat on 4x4: DeFT_P 63.1 / 68.5 / 86.5, the main row 61.8 / 67.5 / 81.7, `EB_vl` 62.2 / 71.9 /
324.2, `EB_route` 63.4 / 73.5 / 102.3, `EB_vl64` 62.3 / 74.9 / 353.6, `EB_down` 62.0 / 87.8 / 413.1.

* **0.2 x Lsat: nothing to choose between the rows.** The rows that may leave DeFT-P's entry VL for a nearer one are 1.3 to
  2.7 % faster than DeFT_P, about one cycle. `EB_route` is not, it is level with DeFT_P: even at this load its packets take
  2 % more hops than those of the main row and of `EB_vl` on 3x3 and 4x4 (`report/extra_C.md` X.1). With its `oracle_beta`
  of 4 one flit in a buffer on the route weighs like four hops, so a nearly empty network already moves its choice.
* **0.5 x Lsat: the early rows are already slower than DeFT_P**, by 3 to 8 % (`EB_down` by 7 % on 3x3 and 22 % on 4x4; on
  2x2 it is 1.2 % faster). The main row is 1.7 to 2.2 % faster.
* **0.8 x Lsat: the early rows are near their own limit.** Their largest throughput is 8 to 22 % below DeFT_P's (`EB_route`
  on 3x3 and 4x4 and `EB_down` on 2x2 excepted, question 4), so 0.8 x Lsat of DeFT-P is close to what they can carry. The
  latency of `EB_vl` and `EB_vl64` is 1.3 to 2.4 times DeFT_P's, that of `EB_down` 2.7 and 3.3 times on 3x3 and 4x4 (on 2x2
  it is 3 % slower). `EB_route` is 10 to 20 % slower than DeFT_P. The main row is 6 to 7 % faster.
* So an early row is never the better choice below saturation either: where the load is low it does not matter, and from
  half the saturation load on it costs.
* Above saturation (1.2 and 1.4 x Lsat, in the report): the main row is 57 to 67 % and 26 to 53 % faster than DeFT_P;
  `EB_route` is 7 to 11 % faster than DeFT_P at 1.2 x Lsat on 3x3 and 4x4 and level at 1.4; `EB_route` on 2x2 and every
  other early row are slower than DeFT_P at both loads, `EB_down` on 2x2 excepted (-10.9 % at 1.2 x Lsat, level at 1.4).

### 8. `EB_vl64` against `EB_vl`: what does the age of the information cost?
*Final (`report/summary_C.md` C.5).* **1.5 to 2.7 % of throughput and 8 to 41 % of latency at 1.0 x Lsat, most on 2x2.**

| size | `EB_vl64` against `EB_vl`: THR | LAT at 1.0 x Lsat | P99 | the main row against `EB_vl64`: THR | LAT at 1.0 x Lsat |
|---|---|---|---|---|---|
| 2x2 | -2.2 [-2.8, -1.6] | +40.9 [+34.4, +47.6] | +53.8 [+44.3, +64.0] | +22.7 [+22.1, +23.3] | -77.3 [-78.4, -76.1] |
| 3x3 | -2.7 [-3.2, -2.2] | +17.0 [+13.7, +20.3] | +11.3 [+8.8, +13.8] | +27.0 [+26.4, +27.6] | -77.3 [-77.8, -76.8] |
| 4x4 | -1.5 [-1.9, -1.1] | +8.4 [+6.1, +10.8] | +6.6 [+4.0, +9.3] | +33.8 [+33.2, +34.3] | -79.0 [-79.5, -78.5] |

* Every interval excludes 0: occupancies that are up to 64 cycles old are worse than fresh ones, on every size and in
  every metric. Below saturation too: at 0.5 x Lsat `EB_vl64` is 2.7 to 4.0 points slower than `EB_vl` against DeFT_P.
* **But this is the small part of the distance to the main row.** `EB_vl` with fresh occupancies is already 17 to 24 %
  behind the main row in THR; the 64 cycles cost another 1.5 to 2.7 %. What `oracle_period` ages is the information at the
  moment of the choice. The choice itself then ages on the way: it is 136 to 284 cycles old when the packet of `EB_vl`
  moves Up at 1.0 x Lsat (question 9), and no injection-time row can avoid that.
* The tuning had seen it coming: on 2x2 the best `oracle_beta` of `EB_vl64` is half that of `EB_vl` (0.25 against 0.5). Old
  occupancies deserve less weight.
* Under hotspot traffic on 3x3 and 4x4 the age costs nothing in THR (`EB_vl64` and `EB_vl` are both within 0.7 % of the
  main row) and 1.3 to 3.2 points in LAT; on 2x2 it costs 8 points in LAT.

### 9. Why do the injection-time rows lose or win: balance over the entry VLs, path length, age of the choice
*Final for what the counters show (`report/summary_C.md` C.8, `report/extra_C.md` X.1; counters of `entry_stats`, means over
the measured window).* **`EB_vl` loses the balance over the entry VLs that DeFT-P's table has. `EB_route` keeps the balance,
pays for it with longer routes, and ends level with DeFT_P. Path length is not what costs either of them. They win only
where the choice is still true when it takes effect, and that is hotspot traffic.**

At 1.0 x Lsat, 2x2 / 3x3 / 4x4 (mean over the six scenarios and the ten seeds):

| row | busiest VL over the mean VL | hops per packet | delivered share of the offered load | wait at the source (cycles) | from the injection to the Up move (cycles) |
|---|---|---|---|---|---|
| `DeFT_P` | 1.32 / 1.50 / 1.77 | 8.27 / 11.18 / 14.26 (anchor row, seed 101) | 1.004 / 0.996 / 0.992 | n/a | n/a |
| main row | 1.29 / 1.52 / 1.65 | 8.65 / 11.50 / 14.72 | 1.007 / 1.004 / 1.002 | 5.7 / 2.5 / 4.8 | 67 / 75 / 114 |
| `EB_vl` | 1.52 / 1.73 / 2.16 | 8.17 / 11.30 / 13.82 | 0.932 / 0.932 / 0.831 | 393 / 244 / 465 | 136 / 193 / 284 |
| `EB_route` | 1.33 / 1.41 / 1.55 | 8.85 / 11.86 / 14.97 | 0.975 / 1.003 / 0.988 | 171 / 12 / 53 | 125 / 113 / 181 |
| `EB_vl64` | 1.61 / 1.73 / 2.18 | 7.84 / 11.32 / 13.80 | 0.915 / 0.919 / 0.819 | 487 / 303 / 505 | 154 / 210 / 291 |

* **Balance: what `EB_vl` loses, and not what the main row wins by.** In the five scenarios without a fixed hot spot
  DeFT-P's table has the best balance of all rows. `EB_vl` gives it up: under chipperm traffic its busiest VL carries
  1.65 / 1.76 / 3.19 times the mean VL (DeFT_P 1.06 / 1.22 / 1.11), under chiptrans traffic 2.80 / 3.19 / 3.04 times
  (DeFT_P 2.10 / 1.64 / 1.50), and those are the scenarios in which its latency at 1.0 x Lsat is furthest from DeFT_P's
  on every size (3.8 to 10 times). The occupancy at the entry VL does not hold the packets apart, and the row drifts to
  the nearest VL. `EB_route` keeps the balance: 1.09 to 1.16 on 2x2, 1.11
  to 1.35 on 3x3 and 1.12 to 1.27 on 4x4 under uniform, localized and chipperm traffic, better than the main row on 3x3
  and 4x4. And it gains nothing over DeFT_P. The main row, for its part, is 13 and 19 % ahead of DeFT_P on 4x4 under
  localized and uniform traffic with a balance that is worse than DeFT_P's (1.19 and 1.21 against 1.09 and 1.10).
* **Path length: not the reason.** `EB_vl` and `EB_vl64` take shorter routes than the main row on every size (at 1.0 x
  Lsat 8.17 / 11.30 / 13.82 hops per packet against 8.65 / 11.50 / 14.72) and have less throughput. `EB_route` takes the
  longest routes of all rows, 2 to 3 % more hops than the main row and 5 to 7 % more than DeFT_P; the main row takes 3 to
  5 % more than DeFT_P. So `EB_route` buys its balance with detours that are a little longer than the main row's, and the
  detours alone do not explain a difference of 11 to 15 % in throughput between the two.
* **Age of the choice: 35 to 72 cycles below saturation, 110 to 290 at 1.0 x Lsat.** Below saturation an injection-time
  choice is as old as the trip is long: at 0.2 and 0.5 x Lsat 35 to 45 cycles pass between the injection and the Up move
  on 2x2, 47 to 57 on 3x3 and 58 to 72 on 4x4, at most 9 more than for the main row (38 to 42 / 46 to 50 / 58 to 63). At
  1.0 x Lsat it is 125 to 154, 113 to 210 and 181 to 291 cycles. A part of that is the row's own doing, since a saturated row has slow packets, so the age at
  1.0 x Lsat is a symptom as much as a cause. What the runs do say: the 64 cycles of `EB_vl64` on top cost 1.5 to 2.7 %
  of throughput (question 8), and the rows lose already at 0.5 x Lsat (question 7), where the choice is youngest.
* **Hotspot traffic: why they win there.** Three things come together. DeFT-P's table is the unbalanced one: it sends all
  packets of a destination through one entry VL, the hot nodes overload theirs, and its busiest VL carries 1.58 / 2.61 /
  4.00 times the mean. Any row that reads the occupancy moves packets to the other VLs of the hot chiplet (1.2 to 1.4 /
  1.5 to 1.9 / 2.0 to 2.6). The rest of the network is not loaded, so the choice is 47 to 57 cycles old when it takes
  effect at 1.0 x Lsat, hardly more than the 31 to 52 cycles at 0.2 x Lsat, and every row still delivers the offered
  load. And the hot spot does not move, so what the source read is still true when the packet arrives.
* **Movinghot traffic is the counter-example.** There the hot spot moves, and the same three rows are 4 to 15 % behind
  DeFT_P in throughput on every size (`EB_route` -4.0 to -11.8 %, `EB_vl` -9.5 to -13.0 %, `EB_vl64` -11.8 to -14.8 %).
* **What the counters do not show.** They are totals over the measured window. A row can be balanced over the whole run
  and still send its packets to one VL at a time. That `EB_route` does so, because every source reads the same queues
  at the same moment and nothing counts the packets that are already on their way to a VL, is my reading of why a
  balanced row with exact and free information gains nothing. The counters do not measure it, and I did not run a row
  that would test it.

### 10. `EB_down`: is it different from DeFT_P?
*Final (`report/summary_C.md` C.2, C.3, C.6, C.8; `report/extra_C.md`).* **Yes, and for the worse. On 3x3 and 4x4 it is the
weakest row of the round. On 2x2 it has DeFT_P's throughput and a higher latency.**

| size | THR against DeFT_P | LAT at 1.0 x Lsat against DeFT_P | THR against the main row | LAT at 1.0 x Lsat against the main row |
|---|---|---|---|---|
| 2x2 | +0.6 [+0.2, +1.0] | +21.3 [+16.2, +26.6] | -6.5 [-6.9, -6.0] | +88.0 [+82.0, +94.1] |
| 3x3 | -14.4 [-14.9, -14.0] | +235.9 [+215.2, +257.9] | -24.7 [-25.1, -24.3] | +438.6 [+418.2, +459.7] |
| 4x4 | -21.8 [-22.2, -21.4] | +218.0 [+200.5, +236.5] | -30.0 [-30.4, -29.7] | +407.8 [+398.2, +417.5] |

* **It is the cleanest test of "late" in the round.** What it commits to at the Down move is the main row's own first
  choice: in the unit checks the committed candidate was a cheapest output of the main row's selection at the same router
  and moment in 12,000 of 12,000 sampled heads on 3x3 and 4x4. Same cost, same information, same first step. The only
  difference is that the main row may still change the entry VL on the interposer. That freedom is worth 6.5 / 24.7 /
  30.0 % of throughput, and without it the row falls behind DeFT_P on 3x3 and 4x4.
* **What the commitment does:** the cheapest candidate at the Down move is mostly the nearest one. On 3x3 and 4x4 the row
  has the shortest routes of all rows (10.40 and 13.17 hops per packet at 1.0 x Lsat; DeFT_P 11.18 and 14.26) and the
  worst balance (its busiest VL carries 1.98 and 2.31 times the mean VL). The main row's cost is a good guide for the
  next hop and a bad forecast for the whole trip.
* **2x2 is different because the row rarely leaves DeFT-P's VL there.** With the hysteresis of the frozen configuration
  on 2x2 it moves Up on another VL than DeFT-P's for 15 to 20 % of its packets, against 49 to 52 % on 3x3 and 4x4. So it
  stays near DeFT_P: level under uniform, localized and movinghot traffic (THR +1.8, +0.5, +0.8 %), far ahead under
  hotspot traffic (+20.5 %, LAT -65.9 %) and far behind under chipperm and chiptrans traffic (THR -13.3 and -3.7 %, LAT
  3.6 and 2.6 times DeFT_P's).
* **Under hotspot traffic** it is, like every row that looks at the network, far ahead of DeFT_P on every size (THR +17
  to +21 %) and 1.5 to 3.2 % behind the main row.
* The prompt of the round expected it close to DeFT_P. I had expected it behind DeFT_P on 3x3 and 4x4, which it is, and
  between DeFT_P and the main row on 2x2, which it is not.

### 11. `LB_noVLrep`: what do the reports across the VLs buy?
*Final (`report/summary_C.md` C.3, C.6, C.7).* **Nothing that these runs can show.** The main row without the occupancy
reports across the VLs is within 0.2 % of the main row in THR, within 0.1 % in LAT at 1.0 x Lsat and within 0.8 % in P99
on every size, and all nine intervals include 0.

| size | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat |
|---|---|---|---|---|---|
| 2x2 | 0.0 [-0.2, +0.2] | -0.1 [-1.2, +1.0] | -0.8 [-2.8, +1.3] | -0.1 [-0.1, 0.0] | -0.1 [-0.1, 0.0] |
| 3x3 | 0.0 [-0.3, +0.2] | -0.1 [-0.6, +0.4] | -0.1 [-2.0, +1.9] | 0.0 [-0.1, 0.0] | 0.0 [0.0, 0.0] |
| 4x4 | +0.2 [-0.1, +0.4] | +0.1 [-0.2, +0.5] | 0.0 [-0.5, +0.5] | 0.0 [0.0, 0.0] | 0.0 [-0.1, +0.1] |

* **Per scenario** (36 cells of size x scenario x THR or LAT): outside movinghot traffic every difference is 0.4 % or
  less. Under movinghot traffic it is -0.6 % and -1.2 % on 3x3 and +1.3 % and +0.8 % on 4x4; the one interval of the 36
  that excludes 0 is THR on 4x4, in favour of the row without the reports. One in 36 is what chance gives.
* **Above saturation** the row without the reports is 1.0 to 1.9 % faster at 1.2 x Lsat (intervals include 0) and within
  0.3 % at 1.4 x Lsat on 2x2 and 4x4; on 3x3 it is 1.7 % faster there [-2.7, -0.6].
* **The counters are the same:** the share of packets off DeFT-P's VL (36.7 / 57.1 / 58.3 % against 36.7 / 56.7 /
  58.2 %), the balance, the hops and the time to the Up move differ in the last printed digit or not at all.
* **What it means.** With `up_report 0` the lookahead term of the Up output of an interposer router counts hops only; it
  no longer uses the occupancies of the outputs of the chiplet router above the VL, which that router would have to
  report down across the VL. The selection still sees the credits of the Up link itself, at the interposer router. What
  the reports add is the state one router further, and that is worth nothing measurable. So the hardware does not need
  occupancy wires across the VLs for this.
* **Limits.** Fault-free scenarios, pipe_all 2, the frozen configuration. The row was not run under faults (Part E has
  the three rows of the family only), and a chiplet that is left few functional VLs is where such reports would matter
  most, if anywhere. I had expected the row within 1 % in THR and 2 % in LAT; it is within 0.2 % and 0.1 %.

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

## Compared with what I stated in advance
The expectations are in `PREREGISTRATION.md` ("Stated in advance"), written before any tuning or evaluation run and not
changed after the tuning. **I overestimated the early rows.** I expected a congestion-aware early choice to earn a part of
the gain. Outside hotspot traffic it earns none.

| what I expected | what the runs show |
|---|---|
| `EB_down` behind DeFT_P on 3x3 and 4x4 | **Yes.** THR -14.4 and -21.8 %, LAT 3.4 and 3.2 times DeFT_P's. |
| `EB_down` between DeFT_P and the main row on 2x2 | **No.** THR level with DeFT_P (+0.6 %), LAT behind it (+21 %). |
| all six tests of the main row against `EB_down` supported | **Yes.** |
| `EB_vl` ahead of DeFT_P under hotspot and movinghot traffic | **Hotspot yes** (THR +17 to +23 %). **Movinghot no** (THR -9.5 to -13.0 %). |
| `EB_vl` about level with DeFT_P elsewhere | **No.** Far behind: THR -9 to -46 %, LAT 1.4 to 10 times DeFT_P's. |
| `EB_vl` behind the main row on every size | **Yes.** |
| `EB_route` the better of the two injection-time rows | **Yes**, on every size. |
| `EB_route` between DeFT_P and the main row on 3x3 and 4x4, with a third to two thirds of the gain | **No.** Level with DeFT_P: -15 and -5 % of the THR gain, +17 and -13 % of the LAT gain. |
| `EB_route` close to DeFT_P on 2x2 | **No.** Behind: THR -8.3 %, LAT +61 %. |
| `EB_vl64` behind `EB_vl` | **Yes**, by 1.5 to 2.7 % in THR. |
| `LB_noVLrep` within 1 % in THR and 2 % in LAT of the main row | **Yes.** Within 0.2 % and 0.1 %. |
| tests most at risk: the main row against `EB_route` on 2x2 | **Not at risk:** +17.3 % and -59.9 %. |
| Part E: the order of the rows stays under faults, the distances shrink | *Pending (question 13).* |

The tuning runs had already spoken against two of these (the addendum, A2). The expectations were left as they were.

## Limits
* **The early rows are one kind of early binder.** Each takes, at one moment, the candidate with the smallest sum of hops
  and weighted occupancy. They do not count the packets that are already on their way to a VL, they do not randomize
  among candidates that are nearly as good, and every source reads the same state. A method that reserves, or that
  spreads its choices, might do better. What the round shows is that congestion-aware early binding of this kind, with
  more information than a real source could have, does not reach DeFT_P outside hotspot traffic. It does not show that
  no early binder can.
* **`EB_down` does not have that limit in the same way**: it decides with the main row's own cost at a router on the
  packet's path, and loses for the reason the question is about, the commitment.
* **One `oracle_beta` per row and size**, chosen by the mean score over five scenarios on two seeds. The tuning by
  scenario shows that no value of the grid brings an early row to the main row's score in any tuning scenario; Part C
  itself has the chosen value only.
* **Latency at 1.0 x Lsat of DeFT-P compares rows of which some are saturated.** The large numbers (up to +440 % against
  the main row) say that a row is past its own limit at that load, not that it is that much slower in general. THR and the latencies at
  0.2 and 0.5 x Lsat are the plainer comparisons, and they point the same way.
* **THR is a lower bound in a quarter to two thirds of the cells** (the largest accepted throughput is at the last load,
  2.4 x Lsat, in 16 to 41 of 60 scenario-seed cells per size and row; `report/summary_C.md` C.9), for every row alike.
* **Part C is fault-free and at pipe_all 2.** Three of the early rows are run under faults in Part E; `EB_vl64` and
  `LB_noVLrep` are not.
* **The reading of why `EB_route` gains nothing** (sources that herd on the same momentarily empty route) is a reading.
  The counters are totals over the run and cannot show it.
