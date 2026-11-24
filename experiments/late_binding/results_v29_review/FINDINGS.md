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
* **The best reference is RC** in 15 of the 18 cells of THR and LAT and MTR in the other three; no DeFT variant is the best anywhere.
* The 2x2 loss under `randperm` is a loss of throughput beyond saturation only: at 1.0 x Lsat the main row has the lowest latency of
  all rows there (66 cycles against 73 for MTR and 112 for DeFT_P), and its P99 is 24 % below the best reference's.
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
