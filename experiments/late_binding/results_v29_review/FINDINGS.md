# Findings v29: what two reviews of the paper ask for

Round 29 answers three objections of two reviews with runs: the advantage over the best reference rests on the tuning scenarios (Part B);
the cost is never weighed against the gain (Parts C and E); MTR and RC are ahead of DeFT here and behind it in the DeFT paper (Part D).
Two questions on early against late binding come along (Part F). Everything was pre-registered (`PREREGISTRATION.md`, committed before any
run of Parts B to G, with what I expected at its end); choices the prompt left open are in `DECISIONS.md`; the tables are in `report/`
(`summary_B.md` ... `summary_F.md`, `summary_hw_E2.md`, `summary_hw_E3.md`, `summary_hw_E4.md`) and the numbers for the paper in
`paper_data/`. Effects are per size, in per cent, with the 95 % interval over the seeds; "2x2 / 3x3 / 4x4" is the order of every triple.
THR is the largest accepted throughput over the loads of the ladder, LAT and P99 the mean and 99th-percentile latency at 1.0 x Lsat of
DeFT_P. Only the two primary families are tested (Holm over 12 each); everything else is descriptive.

**This file is written part by part as the runs finish. Answers 1 to 4 are final; the others follow.**

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
* **The best reference is RC** in 14 of the 18 cells of THR and LAT and MTR in the other four; no DeFT variant is the best anywhere.
* The 2x2 loss under `randperm` is a loss of throughput beyond saturation only: at 1.0 x Lsat the main row has the lowest latency of
  all rows there (66 cycles against 73 for MTR and 112 for DeFT_P), and its P99 is 24 % below the best reference's.
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
  3x3 and 4x4 holds without the tuning scenarios (the throughput gain over the best reference there is +3.8 and +5.6 % on the untuned
  five against +10.5 and +7.6 % on the tuning four of round 25: about half), and the picture for 2x2 is confirmed as a loss in
  throughput (-3.3 % against +2.9 % on the tuning four).

## 4. `LB_b0`: what does `lut_bias 2` buy on 2x2?

About 1 % of throughput and 4 % of latency (`report/summary_B.md`, B.6): `LB_b0`, the main row with the value of 3x3 and 4x4, against the
main row has THR -1.0 [-1.4, -0.5] % and LAT +4.1 [+3.6, +4.6] % on the three new scenarios, and THR -0.8 [-1.0, -0.7] % and LAT
+4.2 [+3.3, +5.1] % on the six scenarios of round 25 (the four of the tuning: -0.8 % and +3.6 %; the other two: -1.0 % and +5.5 %).
The difference is the same on the scenarios that the tuning saw and on those it did not, so it is not an artefact of the tuning set.

**The paper can use one configuration for all sizes.** With `lut_bias 0` on 2x2 the comparisons read: against the best reference THR
-2.6 % instead of -1.7 % on the new scenarios and -0.8 % instead of 0.0 % on the six of round 25; LAT -8.1 % instead of -11.7 % and
-7.3 % instead of -11.1 %. No verdict of a 2x2 test of round 25 or of this round depends on it except where the effect was already
within 1 % of zero; the price of a single configuration is one point of throughput and four points of latency on the smallest system.
