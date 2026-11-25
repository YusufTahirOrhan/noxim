# Findings v29: what two reviews of the paper ask for

Round 29 answers three objections of two reviews with runs: the advantage over the best reference rests on the tuning scenarios (Part B);
the cost is never weighed against the gain (Parts C and E); MTR and RC are ahead of DeFT here and behind it in the DeFT paper (Part D).
Two questions on early against late binding come along (Part F). Everything was pre-registered (`PREREGISTRATION.md`, committed before any
run of Parts B to G, with what I expected at its end); choices the prompt left open are in `DECISIONS.md`; the tables are in `report/`
(`summary_B.md` ... `summary_F.md`, `summary_hw_E2.md`, `summary_hw_E3.md`, `summary_hw_E4.md`) and the numbers for the paper in
`paper_data/`. Effects are per size, in per cent, with the 95 % interval over the seeds; "2x2 / 3x3 / 4x4" is the order of every triple.
THR is the largest accepted throughput over the loads of the ladder, LAT and P99 the mean and 99th-percentile latency at 1.0 x Lsat of
DeFT_P. Only the two primary families are tested (Holm over 12 each); everything else is descriptive.

**This file is written part by part as the runs finish. Answers 1 to 5, 8 and 12 are final; answer 6 lacks the rows of C2 and answer
11 its simulation half; the others follow.**

## 1. Regression and gates: all pass? Are the reused rows reproduced?

Yes to both.
* **Regression** (`regression_before.md`, `regression.md`): the 84 configurations are byte-identical to the e7569b1 build before the code
  change and after it, with the new options absent and with every option of rounds 23 to 29 given at its default.
* **Buffer options** (`buffer_checks.md`, `drain_buffers.csv`): `-buffer_ipos 4` with `-buffer 4` is byte-identical to the option absent
  (12 / 12); the buffers have the capacity asked for (24 / 24); the drain tests with `-buffer 5`, `-buffer 6` and `-buffer_ipos 7` pass
  (72 / 72). `-buffer 5` and `-buffer 6` stopped the simulator before this round, because its power table has no such depth; the entry is
  now interpolated (`DECISIONS.md`).
* **`entry_commit first`** (`anchor_first.md`, `unit_checks_first.md`, `drain_first.csv`, `drain_first_tuned.csv`): with `lut_bias 1e9`
  every packet takes DeFT_P's entry VL (21 / 21 runs; byte-identical to DeFT_P with the tie-breaks on their own random stream); the
  committed VL is a least-cost candidate of the selected output for 12,000 heads per size; no head is bound twice and no hop offers a
  head more than one output; the drain tests pass (36 / 36).
* **Traffic tables** (`traffic_checks.md`, `drain_traffic.csv`): every table of `tornado`, `neighbour` and `randperm` is what its
  definition says; all rows of Part B drain on them at 0.5 and 1.0 x Lsat (114 / 114).
* **The referee's check** (`formal_independent/`): `formal/lb_cdg_check.py`, unedited, run with `python3 -I`: no dead end, no path longer
  than d0 and an acyclic channel dependency graph for XY and for the VN-split order on 4, 9 and 16 chiplets; a cycle when R1, R2 or R3
  is dropped.
* **Reuse** (`reuse_check.md`): the build of this round reproduces the rows of rounds 25, 26 and 28 column for column (24 / 24, 24 / 24,
  60 / 60 runs), so those rows are taken from the earlier per-run files.
* No dead-end event in any run of the round; `check_v29_family.py`, which shares no code with the report, reproduces every test of
  the primary families (`report/families_check.md`).

## 2. Primary family 1: the three scenarios that no round had run

**11 of 12 supported, 1 against** (`report/summary_B.md`, B.1; 5,130 runs, seeds 181-190).

| over tornado, neighbour, randperm | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| THR against DeFT_P | +6.6 [+6.2, +7.0] | +11.9 [+11.5, +12.2] | +11.1 [+10.5, +11.7] |
| LAT against DeFT_P | -33.8 [-36.5, -31.1] | -37.6 [-40.1, -35.0] | -31.6 [-34.6, -28.5] |
| THR against the best of the five references | **-1.7 [-2.0, -1.4] (against)** | +6.8 [+6.5, +7.0] | +7.5 [+7.1, +7.9] |
| LAT against the best of the five references | -11.7 [-13.3, -10.1] | -29.9 [-32.5, -27.1] | -20.0 [-22.6, -17.3] |

* **Against DeFT_P** the main row is ahead in both metrics on every size. Per scenario it has higher THR in eight of the nine cells
  (+3.2 to +17.6 %) and lower LAT in all nine (-12 to -44 %). The exception is `randperm` on 2x2, where its THR is 4.3 % below DeFT_P's.
* **Against the best reference** it is ahead in THR on 3x3 and 4x4 in every scenario (+1.9 to +12.2 %) and has lower LAT in all nine
  cells (-8 to -41 %). On 2x2 its THR is +1.3 % (`tornado`), +5.1 % (`neighbour`) and **-10.8 % (`randperm`)**, which makes the one test
  against.
* **The best reference is RC** in 15 of the 18 cells of THR and LAT and MTR in the other three; no DeFT variant is the best anywhere.
* The 2x2 loss under `randperm` is a loss far beyond saturation. Up to 1.2 x Lsat the main row carries the most traffic of all rows
  there with the lowest latency (at 1.0 x Lsat 66 cycles against 73 for MTR and 112 for DeFT_P, P99 24 % below the best reference's;
  at 1.2 x Lsat 0.1185 flits/node/cycle against 0.1165 for MTR). From 1.4 x Lsat on MTR and RC accept more, and at 2.4 x Lsat, where
  every row has its largest accepted throughput and a mean latency of 1,650 to 2,040 cycles in a window of 8,000, DeFT_P does too
  (0.1430 against 0.1368). (`report/extra_B.md`, a table added after the results were seen.)
* Below saturation (B.4): at 0.2 x Lsat the main row's latency is 2 to 5 % below DeFT_P's and 1.5 to 3.2 % **above** the best
  reference's; at 0.5 x Lsat it is 1 to 3 % below the best reference's and at 0.8 x Lsat 2 to 7 % below. The advantage over the best
  reference is an advantage at load, as in round 25.
* Held against what I wrote in advance: I expected 9 or 10 of 12 with at most one against, the 2x2 tests against the best reference
  unsupported and the THR one possibly against. The THR test is against, as expected; the LAT test on 2x2 is supported, which I did not
  expect. I expected the main row ahead of DeFT_P in every cell (wrong for `randperm` on 2x2), a loss under `neighbour` on 2x2 (wrong:
  +5.1 %), and a DeFT variant as the best reference under `tornado` on 4x4 (wrong: RC). The gains over the best reference on 3x3 and 4x4
  are at or above the top of my ranges, in latency far above them.

## 3. The five scenarios that the tuning never saw

The three new scenarios and `localized` and `movinghot` of round 25, each on its own seeds; the mean of the five per-scenario effects and
their range (`report/summary_B.md`, B.5; no test).

| the main row against | metric | 2x2 | 3x3 | 4x4 |
|---|---|---|---|---|
| the best of the five references | THR | -3.3 (-10.8 to +5.1) | +3.8 (-1.8 to +11.4) | +5.6 (+0.2 to +12.2) |
| the best of the five references | LAT | -5.7 (-17.9 to +8.4) | -18.2 (-40.9 to +11.1) | -11.1 (-35.3 to +14.1) |
| the best of DeFT_P and DeFT_B | THR | +4.9 (-4.3 to +13.8) | +9.0 (+1.3 to +17.6) | +9.6 (+2.7 to +15.6) |
| the best of DeFT_P and DeFT_B | LAT | -29.0 (-40.6 to -13.4) | -33.6 (-43.5 to -17.8) | -26.3 (-44.2 to -2.9) |

* **Against the best reference: behind in throughput on 2x2, ahead on 3x3 and 4x4**; in latency ahead on average on every size, but not
  in every scenario: under `movinghot` the main row is slower than the best reference on 3x3 and 4x4 (+11 %, +14 %) and under `localized`
  on 2x2 (+8 %), as round 25 reported.
* **Against the references that tolerate VL faults it is ahead on every size** in both metrics on average, and in every scenario in
  latency. In throughput the one exception is again `randperm` on 2x2.
* The objection of the reviews was that two untuned scenarios cannot tell tuning from workload. With five, the picture of round 25 for
  3x3 and 4x4 holds without the tuning scenarios, with smaller numbers: the throughput gain over the best reference is +3.8 and +5.6 %
  on the untuned five against +10.5 and +7.6 % on the tuning four of round 25 (about a third of it on 3x3, three quarters on 4x4). On
  2x2 the untuned scenarios show a loss in throughput (-3.3 %) where the tuning four showed a gain (+2.9 %).

## 4. `LB_b0`: what does `lut_bias 2` buy on 2x2?

About 1 % of throughput and 4 % of latency (`report/summary_B.md`, B.6): `LB_b0`, the main row with the value of 3x3 and 4x4, against the
main row has THR -1.0 [-1.4, -0.5] % and LAT +4.1 [+3.6, +4.6] % on the three new scenarios, and THR -0.8 [-1.0, -0.7] % and LAT
+4.2 [+3.3, +5.1] % on the six scenarios of round 25 (the four of the tuning: -0.8 % and +3.6 %; the other two: -1.0 % and +5.5 %).
The difference is the same on the scenarios that the tuning saw and on those it did not, so it is not an artefact of the tuning set.

**The paper can use one configuration for all sizes.** With `lut_bias 0` on 2x2 the comparisons read: against the best reference THR
-2.6 % instead of -1.7 % on the new scenarios and -0.8 % instead of 0.0 % on the six of round 25; LAT -8.1 % instead of -11.7 % and
-7.3 % instead of -11.1 %. On the six scenarios of round 25 the throughput against the best reference moves from level
(0.0 [-0.3, +0.3] %) to slightly behind (-0.8 [-1.1, -0.6] %). The price of a single configuration is one point of throughput and four
points of latency on the smallest system; the sentences of the paper about 2x2 would have to be written with those numbers.

## 5. Primary family 2: the main row against references with 6-flit buffers. What do the buffers buy a reference?

**9 of 12 supported, 2 against, 1 not significant** (`report/summary_C.md`, C.1; 14,580 new runs, seeds 121-130, the six fault-free
scenarios of round 25, every row at the loads of DeFT_P's ladder with 4-flit buffers; the main row and the references with 4-flit
buffers are the runs of round 25). A reference with 6-flit buffers has 1.32 to 1.34 times DeFT's router area, the main row 1.08 to 1.25
times (answer 6).

| the main row, 4-flit buffers, over the six scenarios | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| THR against the best of `DeFT_P_d6` and `DeFT_B_d6` | **-0.5 [-0.8, -0.2] (against)** | +3.9 [+3.5, +4.2] | +3.8 [+3.6, +4.0] |
| LAT against the best of `DeFT_P_d6` and `DeFT_B_d6` | -10.1 [-12.4, -7.7] | -9.9 [-10.7, -9.1] | -10.1 [-11.2, -8.9] |
| THR against the best of the four references at depth 6 | **-3.4 [-3.6, -3.2] (against)** | +2.9 [+2.5, +3.3] | +2.3 [+2.1, +2.6] |
| LAT against the best of the four references at depth 6 | -1.2 [-3.4, +1.1] (not significant) | -2.2 [-3.1, -1.3] | -4.3 [-5.8, -2.9] |

* **On 3x3 and 4x4 the main row with 4-flit buffers is ahead of every reference with 6-flit buffers in both metrics** (eight of eight
  tests): against the best of the four by 2 to 3 % in THR, 2 to 4 % in LAT and 10 to 15 % in P99; against each row alone by
  +8.5 / +6.4 % (`DeFT_P_d6`), +6.4 / +4.8 % (`MTR_d6`) and +6.0 / +4.7 % (`RC_d6`) in THR.
* **On 2x2 it is behind in throughput**: 3.4 % behind the best of the four (1.1 % behind `MTR_d6`, 1.4 % behind `RC_d6`, 1.7 % ahead of
  `DeFT_P_d6`) and 0.5 % behind the best DeFT variant. Its latency is 10 % below the best DeFT variant's and level with `RC_d6`'s, which
  is the fastest reference there in every scenario.
* **What the buffers buy a reference** (each against itself with 4-flit buffers, C.2; 2x2 / 3x3 / 4x4):

  | reference | THR, 6-flit buffers | THR, 5-flit | LAT at 1.0 x Lsat, 6-flit | LAT, 5-flit |
  |---|---|---|---|---|
  | DeFT_P | +5.5 / +5.1 / +5.3 | +3.1 / +2.8 / +2.8 | -22.6 / -22.6 / -20.9 | -15.9 / -15.4 / -14.6 |
  | DeFT_B | +6.4 / +5.8 / +5.1 | +3.6 / +3.1 / +3.0 | -16.0 / -20.0 / -21.5 | -11.8 / -14.8 / -13.8 |
  | MTR | +3.6 / +3.0 / +4.1 | +1.6 / +1.5 / +2.1 | -11.3 / -10.2 / -11.5 | -7.4 / -6.5 / -6.9 |
  | RC | +3.7 / +3.3 / +3.9 | +2.1 / +1.8 / +2.2 | -11.1 / -10.3 / -11.7 | -7.4 / -6.9 / -8.0 |

  Two more flits in every buffer, a third more router area, buy a DeFT variant 5 to 6 % of throughput and a fifth of its latency at
  DeFT's saturation load, and MTR and RC 3 to 4 % and a ninth; P99 falls by 21 to 38 %. The first of the two flits buys a little more
  than half. The gain depends on the traffic: 7 to 11 % of throughput for the DeFT variants under uniform and localized traffic, 1 to
  2 % for every reference under `chiptrans`.
* **By group of scenarios** (C.4) the split of round 25 comes again, one step lower. On the four tuning scenarios the main row is level
  with the best of the four at depth 6 in THR on 2x2 (-0.1 %) and ahead on 3x3 and 4x4 (+6.8, +4.3 %), with 8 to 14 % less latency on
  every size. **On `localized` and `movinghot` it is behind the best reference at depth 6 in both metrics on every size**: THR
  -9.9 / -4.5 / -1.6 %, LAT +15.2 / +13.4 / +18.1 % (with 4-flit buffers on both sides: -5.6 / -0.5 / +2.9 % and +4.2 / +3.1 / +4.2 %).
  The tests over the six scenarios are supported on 3x3 and 4x4 because the lead on `chipperm`, `chiptrans` and uniform traffic is
  larger than the deficit on these two.
* **Which reference is the best** (`report/extra_C.md`, X.3, a table added after the results were seen): of the 36 cells of size,
  scenario and metric RC is the best reference with 6-flit buffers in 21, MTR in 7, DeFT_B in 7 (five of the six cells of hotspot
  traffic, and in THR `chipperm` and uniform traffic on 3x3) and DeFT_P in 1 (`chipperm` on 4x4, THR). With 4-flit buffers the counts
  were 17, 11, 7 and 1: the buffers hardly change which reference is the best.
* **Below saturation the buffers decide nothing** (C.6): at 0.5 x Lsat the main row's latency is 0.4 to 1.2 % below the best
  reference's at every depth; at 0.8 x Lsat it is within 1.3 % of the best reference at depth 6 (+1.1 / -0.4 / +1.3 %).
* Held against what I wrote in advance. I expected 2 to 4 of 12 supported and 4 to 6 against, and with it the sentence "the gain over
  MTR and RC does not survive equal area". That was wrong for 3x3 and 4x4. The buffers buy the references less than I expected: the
  DeFT variants are at the bottom of my ranges (THR +5 to +10 %, LAT -20 to -40 %), MTR and RC below the THR range and at the bottom
  of the LAT range (-10 to -25 %). So against the best of the four at depth 6 the main row is not 5 to 25 % slower, as I had written,
  but level on 2x2 and 2 to 4 % faster elsewhere, and it keeps 2 to 3 % of throughput on 3x3 and 4x4 where I had expected -3 to +2 %.
  The two 2x2 tests of throughput are against, as I expected; of the two 2x2 tests of latency, which I expected unsupported, the one
  against the DeFT variants is supported. The prompt's expectation ("against MTR and RC at depth 6 it is level or behind in throughput
  on every size ... and its latency at DeFT's Lsat is no longer lower") holds on 2x2 and not on 3x3 and 4x4 (THR +5.8 / +4.7 %, LAT
  -5.9 / -9.8 % against the best of `MTR_d6` and `RC_d6`).

## 6. The main row against references of depth 5 and 6 and with 7-flit buffers on the interposer: where does a reference with the main row's area reach it?

*(The `X_i7` rows of C2 are not run yet; this answer is completed when they are.)*

Area of all routers of a system relative to DeFT with 4-flit buffers (E3, `report/summary_hw_E3.md`; 2x2 / 3x3 / 4x4):

| design | hierarchy kept | core kept | flattened |
|---|---|---|---|
| the main row | 1.251 / 1.217 / 1.218 | 1.161 / 1.130 / 1.133 | 1.103 / 1.077 / 1.079 |
| a reference with 5-flit buffers | 1.168 / 1.167 / 1.166 | 1.175 / 1.172 / 1.171 | 1.175 / 1.170 / 1.168 |
| a reference with 6-flit buffers | 1.321 / 1.319 / 1.317 | 1.341 / 1.336 / 1.335 | 1.340 / 1.333 / 1.332 |
| a reference with 7-flit buffers in the interposer routers | 1.239 / 1.237 / 1.236 | 1.249 / 1.246 / 1.246 | 1.254 / 1.247 / 1.246 |

What "the main row's area" is depends on the form of the synthesis: a reference with 5.3 to 5.5-flit buffers when the hierarchy is
kept, with 4.8 to 4.9-flit buffers when the core is kept, with 4.5 to 4.6-flit buffers flattened. A reference with 5-flit buffers has
5 to 8 points less area than the main row in the first form and 1 to 4 and 7 to 9 points more in the other two; one with 6-flit
buffers has 7 to 26 points more in every form.

The main row with 4-flit buffers against the best of the four references of each depth (six scenarios; `report/summary_C.md`, C.3), and
the same read at the area of the main row (`report/extra_C.md`: per seed the log ratio interpolated linearly in the area between the
two neighbouring depths; a reading aid defined before the results were read, not a measurement, no router with such buffers was run):

| references | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|
| 4-flit buffers (round 25) | 0.0 / +6.7 / +6.0 | -11.1 / -9.7 / -13.2 | -24.4 / -27.3 / -29.6 |
| 5-flit buffers | -1.8 / +4.8 / +4.0 | -5.1 / -4.7 / -7.8 | -12.3 / -16.8 / -21.6 |
| 6-flit buffers | -3.4 / +2.9 / +2.3 | -1.2 (n.s.) / -2.2 / -4.3 | -6.7 (n.s.) / -10.3 / -15.4 |
| *at the main row's area, hierarchy kept* | *-2.7 / +4.1 / +3.4* | *-3.0 / -3.9 / -6.6* | |
| *at the main row's area, core kept* | *-1.6 / +5.2 / +4.4* | *-5.6 / -6.0 / -9.0* | |
| *at the main row's area, flattened* | *-1.1 / +5.8 / +5.0* | *-7.6 / -7.4 / -10.7* | |

* **On 3x3 and 4x4 no reference reaches the main row up to 6-flit buffers**, which is 8 to 24 % more area than the main row has.
  Every flit of depth takes about two points of the throughput lead and 2.5 to 5.5 points of the latency lead. Against a reference
  that spends the main row's area on buffers the main row keeps 3 to 6 % of throughput and 4 to 11 % of latency at DeFT's
  saturation load: 57 to 87 % of the throughput lead of round 25 and 40 to 81 % of its latency lead are left, the lower figures with
  the hierarchy kept. The steps in throughput do not shrink with the depth (3x3: -1.9, -1.9 points; 4x4: -2.0, -1.7), so deeper
  buffers would reach the main row: at this pace at about 7.5 flits, 1.5 to 1.6 times DeFT's area. That is an extrapolation; no
  such row was run.
* **On 2x2 a reference reaches it in throughput at once.** With 4-flit buffers on both sides the main row is level with the best
  reference (0.0 [-0.3, +0.3] %); with the main row's area the best reference is 1.1 to 2.7 % ahead. MTR and RC alone are level
  with it at 4.8 flits (1.14 times DeFT's area: more than the main row's area flattened, less than its area in the other two forms),
  the DeFT variants at 5.8 flits (1.29 to 1.30, more than the main row's area in every form).
* **On 2x2 in latency a reference reaches it at 6 flits**: -11.1 % with 4-flit buffers, -5.1 % with 5, -1.2 [-3.4, +1.1] % with 6. At the
  main row's area it keeps 3 to 8 %.
* **Against the two references that tolerate VL faults** the main row is ahead at every depth on 3x3 and 4x4 (6-flit buffers: THR
  +3.9 / +3.8 %, LAT -10 %; at the main row's area THR +5.3 to +7.9 %, LAT -13 to -21 %). On 2x2 it is ahead with 5-flit buffers (THR
  +1.6 %, LAT -15.3 %) and level in throughput with 6 (-0.5 %), with 10 % less latency.
* **It differs by scenario** (C.4, references with 6-flit buffers; THR and LAT against the best of the four). The main row keeps
  its lead under `chipperm` and `chiptrans` on every size (THR +1.5 to +20.3 %, LAT -4.8 to -36.4 %) and under uniform traffic on 3x3
  and 4x4 (THR +3.2 / +6.6 %, LAT -6.1 / -4.8 %). Under hotspot traffic it is level in throughput (+0.7 to +1.6 %) with 5 to 8 % less
  latency. It is behind under uniform traffic on 2x2 (THR -6.2 %, LAT +5.2 %), under `localized` (THR -12.8 / -4.6 / -0.9 %, LAT
  +12.3 / +5.7 / +1.7 %) and under `movinghot` (THR -6.8 / -4.4 / -2.4 %, LAT +18.2 / +21.6 / +37.0 %); under `movinghot` it was behind
  with 4-flit buffers on both sides already.
* Held against what I wrote in advance (references with 5-flit buffers, the best of the four): THR -4 to -1 % on 2x2 (-1.8 %: inside)
  and 0 to +4 % on 3x3 and 4x4 (+4.8 / +4.0 %: at the top or above); LAT within -5 to +10 % (-5.1 / -4.7 / -7.8 %: at the favourable
  end or beyond). Against the DeFT variants with 5-flit buffers I expected the main row ahead on 3x3 and 4x4 and level on 2x2; it is
  ahead on every size.

## 8. `LB_d6`: does the gain hold when the main row and the references both have 6-flit buffers?

In throughput yes, unchanged; in latency about three quarters of it (`report/summary_C.md`, C.5; nothing retuned, the selection keeps
the weights tuned for 4-flit buffers).

| `LB_d6` against | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|
| the main row (4-flit buffers) | +4.2 [+4.1, +4.3] / +4.6 [+4.4, +4.8] / +4.3 [+4.1, +4.5] | -6.6 / -4.9 / -6.2 | -10.6 / -9.2 / -5.5 |
| the best of the four references with 6-flit buffers | +0.6 [+0.4, +0.9] / +7.6 [+7.2, +8.1] / +6.7 [+6.4, +7.1] | -7.7 / -7.0 / -10.3 | -16.6 / -18.6 / -20.1 |
| the best of `DeFT_P_d6` and `DeFT_B_d6` | +3.7 / +8.7 / +8.3 | -16.0 / -14.4 / -15.7 | -27.2 / -31.1 / -27.4 |
| for comparison, 4-flit buffers on both sides (round 25): the main row against the best of the four | 0.0 / +6.7 / +6.0 | -11.1 / -9.7 / -13.2 | -24.4 / -27.3 / -29.6 |

* **The throughput gain over the best reference is the same with 6-flit buffers on both sides as with 4-flit buffers on both sides**,
  or a little larger (+0.6 / +7.6 / +6.7 % against 0.0 / +6.7 / +6.0 %). The buffers buy the main row 4.2 to 4.6 % of throughput:
  what they buy MTR and RC (3.0 to 4.1 %) and less than they buy the DeFT variants (5.1 to 6.4 %).
* **The latency gain at 1.0 x Lsat is smaller** (-7.7 / -7.0 / -10.3 % against -11.1 / -9.7 / -13.2 %), and so is the P99 gain. That
  load is DeFT_P's saturation load with 4-flit buffers; with 6-flit buffers every row is further from its own saturation there, and
  the buffers take 5 to 7 % off the main row's latency where they take 10 to 12 % off MTR's and RC's and 16 to 23 % off a DeFT
  variant's.
* **By group of scenarios** as with 4-flit buffers, a little better on the two scenarios outside the tuning: on the four tuning
  scenarios THR +2.9 / +10.2 / +7.2 % and LAT -11.1 / -10.8 / -16.0 %; on `localized` and `movinghot` THR -3.7 / +2.6 / +5.8 % and LAT
  -0.5 / +1.1 / +2.2 % (4-flit buffers on both sides: -5.6 / -0.5 / +2.9 % and +4.2 / +3.1 / +4.2 %). The moving hotspot is where the
  buffers help the main row most: its latency at 1.0 x Lsat falls from 94 to 73 cycles on 2x2, from 116 to 97 on 3x3 and from 252 to
  195 on 4x4 (`report/extra_C.md`, X.3), in the other scenarios by 0 to 5 %.
* So the gain of the late binding is not something that buffers replace: both add up in throughput. What deeper buffers on the side
  of the references take away (answers 5 and 6) is what the same buffers would give the main row.
* Held against what I wrote in advance: THR +4 to +8 % against the main row (+4.2 to +4.6 %: the bottom of the range); against the
  best reference at depth 6 "about what the main row has against the best reference at depth 4 or a little less", -1 / +5 / +5 %
  (+0.6 / +7.6 / +6.7 %: not less, and above my figures).

## 11. `LB_noLA` and the reports across the VLs: what they cost in hardware (E2)

*(The simulation half of this answer, what the lookahead term buys, follows with E1.)*

Two RTL variants of the main row's interposer router, each checked against 1.85 million recorded selections of its own simulator row
in all eight cut configurations (0 mismatches; the same vectors through the main row's units give 9,181 and 309,078 mismatches) and
synthesised next to the main row (`report/summary_hw_E2.md`).

| | main row | `LB_noVLrep` | `LB_noLA` |
|---|---|---|---|
| report inputs an interposer router reads (without / with a VL) | 72 / 84 | 72 / 72 | 0 / 0 |
| flip-flops of an interposer router on 4x4 (without / with a VL; DeFT 1,795 / 2,184) | 2,125 / 2,640 | 2,125 / 2,628 | 2,045 / 2,544 |
| system area relative to DeFT, hierarchy kept (2x2 / 3x3 / 4x4) | 1.251 / 1.216 / 1.218 | 1.248 / 1.214 / 1.215 | 1.203 / 1.170 / 1.172 |
| system area, core kept | 1.161 / 1.129 / 1.132 | 1.159 / 1.128 / 1.131 | 1.133 / 1.104 / 1.107 |
| system area, flattened | 1.101 / 1.077 / 1.078 | 1.101 / 1.075 / 1.076 | 1.075 / 1.051 / 1.052 |
| registers needed in the decision unit at T_ref | 1 (after M) | 1 (after M) | 1 (after B, or after M) |
| delay left for an interposer link in the link cycle (DeFT 0.82 to 0.90 ns) | 0.25 to 0.41 ns | 0.19 to 0.44 ns | 0.35 to 0.53 ns (cut M), 0.27 to 0.40 ns (cut B) |

* **The lookahead term is about a fifth of the main row's area above DeFT**: without it the system has 1.17 instead of 1.22 times
  DeFT's area on 3x3 and 4x4 with the hierarchy kept (79 to 81 % of the overhead remains; 80 to 82 % with the core kept, 66 to 74 %
  flattened). It removes all 150 report wires into an interposer router and the 72 or 84 bits of them that the router registers.
* **The reports across the VLs are about one per cent of the overhead**: 12 report bits and 12 flip-flops in each of the 4 interposer
  routers per chiplet that have a VL, and the 30 wires down each VL.
* **Timing.** Every design needs one register inside the decision unit to fit DeFT's clock period, so the decision takes two cycles
  and the residual delay is 0 for all three; no variant gets back to one cycle (without a cut `LB_noLA` misses T_ref by 0.19 ns, the
  main row by 0.66 ns). At 1 ns the main row needs three registers and each variant two.
* **Link budget.** The decision reads the head on the link, so the first stage of the decision takes most of the link cycle: an
  interposer link may take 0.25 to 0.41 ns of it with the main row against 0.82 to 0.90 ns with DeFT. Without the lookahead term 0.35
  to 0.53 ns are left (with the same cut): about 0.1 ns more, which is the size of the spread of this flow on unchanged logic (0.13 ns).
  The reports across the VLs make no measurable difference.

## 12. Power: the ratio of the main row to DeFT, and how far the figure can be trusted

OpenSTA `report_power` on the flattened netlists of the 4x4 routers at a 1 ns clock (`report/summary_hw_E4.md`). Average router of a
system (12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL routers per chiplet), relative to DeFT:

| activity | main row | `LB_noVLrep` | `LB_noLA` | DeFT, mW per router |
|---|---|---|---|---|
| simulation of the netlists at the load of 0.5 x Lsat | **1.063** | 1.061 | 1.034 | 11.2 |
| simulation of the netlists at the load of 1.0 x Lsat | **1.077** | 1.075 | 1.045 | 11.2 |
| the tool's default (0.1 transitions per cycle at every input) | 1.123 | 1.121 | 1.099 | 17.0 |
| the default with reset, position and table inputs constant (not pre-registered) | 1.067 | 1.067 | 1.054 | 23.9 |

Per router with the simulated activity: interposer router 1.14, interposer router with a VL 1.17 to 1.18, chiplet and boundary router
0.98 to 1.01 (they differ from DeFT's by a table).

* **The main row's routers take 6 to 8 % more power than DeFT's at system level** with the activity of a simulation, 14 to 18 % more in
  an interposer router. The lookahead term is about 3 of the 6 to 8 points; the reports across the VLs 0.2 points.
* **What the activity is.** The vectors that the flow records are evaluations of the decision unit and cannot drive a router, so the
  load was replayed, not recorded flits: the simulator counted the flits per input port of every router on 4x4 under uniform traffic,
  and each synthesised netlist was simulated under random 8-flit packets at those rates (`DECISIONS.md`, "E4"). In all 24 cases the
  netlist prints the result line of the RTL, and every pin of it is annotated from the VCD.
* **How far to trust it.**
  * *The ratio is a ratio of flip-flops.* With the simulated activity 88 to 98 % of a router's power is in its flip-flops (their clock
    pins toggle in every cycle whether or not a flit moves), 3 % is leakage and 0.4 to 6 % switching. An interposer router of the main
    row has 1.12 times DeFT's flip-flops (1.15 with a VL) and 1.14 times its power (1.17 to 1.18). The figure therefore says little
    about the logic of the decision and much about the registers it adds.
  * *No clock gating, no clock tree, no wires.* A real router gates the clock of its buffers, which are 60 % of DeFT's area; that
    shrinks the part the two designs have in common, and the ratio then depends on whether the registers that the main row adds are
    gated as well. The 150 report wires into an interposer router and their drivers have no capacitance here; they toggle rarely
    (occupancies change when flits move), but they are not counted at all.
  * *Zero-delay simulation:* glitches are not counted. *One library corner* of a 45 nm teaching library.
  * *The default activity overstates the difference* (1.12): it lets the reset toggle, which damps every register behind a synchronous
    reset, and gives the 150 report inputs of the main row the activity of data.
  * The power is nearly flat in the load: DeFT's average router takes 11.20 mW at 0.5 x Lsat and 11.18 mW at 1.0 x Lsat.
  So: the direction and the size class (several per cent at system level, about a sixth in an interposer router) can be quoted; the
  second digit cannot, and a figure after layout with clock gating could differ in either direction.
