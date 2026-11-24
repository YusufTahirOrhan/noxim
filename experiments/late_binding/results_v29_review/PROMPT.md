# Prompt v29: what two reviews of the paper ask for. Scenarios never used, references of equal area, the reference set-up of the DeFT paper, the cost of the lookahead, and two more early binders

Repository: the Noxim fork, branch `feat/parametric-topology` (last commit e7569b1, round v28). Work
in `experiments/late_binding/results_v29_review/`.

Two untracked files were placed in the repository for this round; commit both with step A0:
`experiments/late_binding/results_v29_review/PROMPT.md` (this prompt) and
`experiments/late_binding/formal/lb_cdg_check.py` (the referee's independent check, see A2).

If this is a fresh session, read `experiments/late_binding/README.md` (rounds 23 to 28),
`results_v25_confirm/FINDINGS.md` and `results_v25_confirm/hw/FINDINGS_hw.md`,
`results_v28_anchor/FINDINGS.md` (the answer in short and "Limits"), the tuning rule in
`results_v24_xy/tuning.md`, `gen_traffic.py`, `experiments_v25.py` (`row_args`, `job`, the ladder
rule of A3), `experiments_v25_hw.py` and `experiments_v25_hw2.py`.

## Where we are

Round v28 was recomputed independently from the per-run files and agrees with its report to the
printed decimal. The paper draft (v7) was then reviewed twice: by Google's Deep Review and by an
independent referee who also re-implemented the routing function, the VN rules and the channel
dependency graph and found no counterexample to the proofs (4, 9 and 16 chiplets, XY and the
VN-split order; dropping R1, R2 or R3 gives a cycle). Draft v8 fixes what needs no run. Three
objections need runs, and each of them could reject the paper:

1. **The advantage over the best reference rests on the four scenarios used for tuning.** Round 25,
   the main row against the best of the five references (4 / 9 / 16 chiplets): four tuning scenarios
   THR +2.9 / +10.5 / +7.6 %, LAT -17.8 / -15.4 / -20.8 %; the two others (localized, moving
   hotspot) THR -5.6 / -0.5 / +2.9 %, LAT +4.2 / +3.1 / +4.2 %. Two scenarios cannot tell tuning
   from workload. The bias `lut_bias` is also set per size (2 on 2x2, 0 elsewhere).
2. **The cost is never weighed against the gain.** The main row has 22-25 % more router area. No
   reference was given that area. There is no power figure, and the lookahead term, which is what
   needs the report wires and registers, was never priced.
3. **MTR and RC are ahead of DeFT here, and behind it in the DeFT paper.** In round 25 DeFT_P has
   the lowest latency of the three only at 0.2 x Lsat (by 0.8-0.9 %); from 0.5 x Lsat on MTR and RC
   are faster, and they have 3-5 % more throughput. Round 23 (pipe_all 0, five seeds) suggests that
   the per-hop VC choice of MTR and RC explains most of this under uniform traffic: there DeFT_P
   is level with or faster than `MTR_static` at every load and within 5 % of `RC_static`; under
   hotspot traffic it stays behind both. This was never run at pipe_all 2.

Two smaller questions on early against late binding come along (Part F).

This round takes no side. Every part can come out against the main row, and that is then what the
paper will say. Nothing of the frozen configuration is retuned and no existing row is changed.

## Standing rules

- Commit and push after every step; commit only in the noxim repo.
- Never stop to ask; take the conservative option (the one that does not favour our methods) and
  record it in `DECISIONS.md`. Here that means: when in doubt, favour the references and the early
  rows.
- Stop only on a drain-test FAIL, a failed regression check or a dead-end event.
- New options default off; the 84 configurations stay byte-identical to the e7569b1 build with the
  options absent and with every option given explicitly off.
- Start the WSL keepalive before the first detached job. Long jobs detached in tmux, logged,
  resumable. Raw outputs deleted after aggregation.
- `PREREGISTRATION.md` before any run of Parts B to G, with your own expectations for B and C;
  `DECISIONS.md`, `FINDINGS.md`, per-run CSVs, `report/`.
- Unless stated: `-pipe_all 2`; every VN-based method with `-deft_up_keep 1 -deft_rr_fallback 1
  -deft_vn_rr 1`; `-traffic_rng 1`; the LUTs of v23; MTR and RC with `-vc_per_hop 1`.
- Seeds. Never used before: 181-190 (Part B), 191-195 (Part D2). Reused on purpose, so that new
  rows are paired with existing ones: 121-130 (round 25; Parts C, D1, E), 171-180 (round 28;
  Part F), 151 and 152 (round 26; Part C3). Tuning and calibration: 101, 102.
- Before a part reuses rows of an earlier round, rerun with the new build the main row and DeFT_P
  on two scenarios per size at 1.0 x Lsat (first two seeds of that round) and check that the
  statistics are identical. If not, say why and rerun the reused rows.

## Rows

| Row | Definition |
|---|---|
| `DeFT_P`, `DeFT_B`, `MTR`, `RC`, `XY_SP` | as round 25 |
| `CI_heurLA_X_LF` (**main**) | as round 25 (`lut_bias` 2 on 2x2, 0 on 3x3 and 4x4) |
| `LB_b0` | the main row with `lut_bias 0`; only on 2x2, where it differs |
| `X_d5`, `X_d6` | reference X with `-buffer 5` or `-buffer 6` everywhere (X in DeFT_P, DeFT_B, MTR, RC); RC keeps `rc_slots 4` |
| `X_i7` | reference X with 7-flit input buffers in the interposer routers and 4-flit buffers in the chiplet routers (new option, A1) |
| `LB_d6` | the main row with `-buffer 6` |
| `MTR_static`, `RC_static` | MTR and RC without `-vc_per_hop` (the rows of round 23), at pipe_all 2 |
| `LB_noLA` | the main row with `heur_lookahead 0` (the row `CI_heur_X` of round 24 in mechanism LF) |
| `EB_first` | new (A1): the entry VL is bound once, at the first hop that offers the head a choice |
| `EB_best16`, `EB_best256` | `EB_best` of round 28 with `oracle_period 16` or `256`, T tuned again |

---

## Part A: code and gates

- **A0.** Regression with the current build (84 / 84) before any change.
- **A1. New options** (all off by default):
  - `-buffer_ipos N` (default 0 = as `-buffer`): the depth of every input buffer of an interposer
    router, the one that receives from a Down VL included. The chiplet routers keep `-buffer`. The
    occupancies, the full status and everything the selection reads must follow the real depth.
  - `-deft_lb entry_commit first`: like `entry_commit down` of round 27, but the commit is made
    at the first interposer router at which the routing function offers the head more than one
    output, wherever that is: the router below the exit VL if the candidates lie on both sides of
    it, otherwise the first column of a candidate that the head reaches. The head selects by the
    cost of the main row at that router (lookahead included, `lut_bias` as given, computed when
    the main row computes its decision for that router) and keeps one candidate: the candidate of
    least cost through the selected output, with the tie rule of `entry_commit down`. From then on
    it has one candidate. Before that router nothing differs from the main row. With `lut_bias`
    towards infinity the row is DeFT_P.
  - Traffic patterns in `gen_traffic.py` (new, never run in this project):
    - `tornado`: router (x, y) of the chiplet layer sends to ((x + FW / 2 - 1) mod FW, y), FW = the
      width of the layer in routers;
    - `neighbour`: a source sends to a router of the chiplets adjacent to its own in the chiplet
      grid, uniformly over these routers;
    - `randperm`: one fixed permutation of the routers without fixed points, drawn once per size
      with `random.Random(2901)` (redraw until no router maps to itself); the table is written to
      the results folder.
  - Rebuild; regression 84 / 84 with the options absent and explicitly off.
- **A2. Gates** (three sizes):
  - `-buffer_ipos 4` with `-buffer 4` is byte-identical to the option absent, for DeFT_P, MTR, RC
    and the main row (uniform, 1.0 x Lsat, seed 121).
  - `-buffer 6`, `-buffer_ipos 7`: all-pairs drain tests of DeFT_P, DeFT_B, MTR, RC and the main
    row on the fault-free mask and on the north mask (the VN-based rows).
  - `EB_first`: all-pairs drain tests on the six masks per size of round 27; every head has at
    most one hop with more than one offered output; the committed VL is a candidate of least cost
    of the main row's selection at that router (check on 12,000 sampled heads per size, as round
    27 did for `entry_commit down`); with `lut_bias 1e9` the row gives DeFT_P's results (the
    anchor gate of round 28, same runs).
  - The three new traffic tables: every source sends, the rates sum to the nominal rate, `randperm`
    is a permutation without fixed points, `tornado` never leaves its row. Drain tests of all rows
    of Part B on the three patterns at 0.5 and 1.0 x Lsat.
  - `formal/lb_cdg_check.py` (the referee's independent re-implementation of the routing
    function, the VN rules and the CDG; it needs `networkx`): run its modes `main`, `turnmodels`,
    `rules` and `placements` with `python3 -I` and store the outputs in `formal_independent/`. It
    must report: no dead end, no path longer than d0, an acyclic CDG for XY and for the VN-split
    order on 4, 9 and 16 chiplets, and a cycle when R1, R2 or R3 is dropped. Do not edit the
    script. If the file is missing, say so and go on.
- **A3. Safety.** `EB_first` binds one functional candidate of the head's own set, so its paths
  are paths of the main row; the buffer options change no routing. Say whether you agree after
  reading the code.

---

## Part B: scenarios never used (pre-registered; seeds 181-190)

- **B0. Ladders.** `tornado`, `neighbour`, `randperm` on 2x2, 3x3, 4x4: DeFT_P's ladder by the rule
  of round 25 (A3 there: seed 101, pipe_all 2, 3 x L0, nine loads) into `load_points_v29.json`.
- **B1. Runs.** Rows `DeFT_P`, `DeFT_B`, `MTR`, `RC`, `XY_SP`, the main row, and `LB_b0` on 2x2:
  3 scenarios x 3 sizes x 9 loads x 10 seeds x 6 rows = 4,860, plus 270. `heldout_runs.csv` with
  the columns of `results_v25_confirm/eval_runs.csv`.
- **B2. `LB_b0` on the scenarios of round 25:** 2x2, the six fault-free scenarios, the ladders of
  `load_points_v25.json`, seeds 121-130: 540 runs, paired with the rows of round 25.
- Metrics, effects and tests as round 25 (paired over the ten seeds; the best reference per
  scenario, size and metric).
- **Primary family 1 (Holm over 12),** per size, over the three new scenarios: the main row has
  higher THR, and lower LAT at 1.0 x Lsat, than (a) DeFT_P and (b) the best of the five references.
- **Secondary (descriptive):** each scenario separately, with the reference that is the best; the
  main row against the best of DeFT_P and DeFT_B and against the best of MTR and RC; P99; LAT at
  0.2, 0.5 and 0.8 x Lsat; the five scenarios that the tuning never saw taken together (these
  three with localized and moving hotspot of round 25, each on its own seeds; report the mean of
  the five per-scenario effects and their range, without a test); `LB_b0` against the main row
  and against the best reference on 2x2, for the three new scenarios and for the six of round 25
  (all six, the four tuning scenarios, the other two).
- **Stated in advance** (write yours into the pre-registration). Mine: the main row is ahead of
  DeFT_P in all three scenarios on every size. Against the best reference I expect about zero on
  2x2 and a few percent on 3x3 and 4x4 for `tornado` and `randperm`, and nothing for `neighbour`,
  whose paths are short. `LB_b0` loses less than 1 % of throughput on 2x2.

---

## Part C: references with the area of the main row (pre-registered)

The main row's routers have 1.25 / 1.22 / 1.22 times DeFT's area (2x2 / 3x3 / 4x4) with the
hierarchy kept, which is the figure of the paper and an upper bound for this design; with the core
kept it is 1.16 / 1.13 on 2x2 / 4x4 and flattened 1.10 / 1.08 (`hw/FINDINGS_hw.md`, F3). Buffers are
about 60 % of DeFT's router, so a reference with 5-flit buffers (about 1.15) has roughly the main
row's area, one with 6-flit buffers (about 1.3) has more in every form of the synthesis, and one
with 7-flit buffers in the interposer routers only has the paper's figure in the same place. Part
E3 measures these ratios; the comparison is read with the measured ones.

- **C1. Depth 6 (primary) and depth 5.** `DeFT_P_d6`, `DeFT_B_d6`, `MTR_d6`, `RC_d6`, `LB_d6`, and
  `DeFT_P_d5`, `DeFT_B_d5`, `MTR_d5`, `RC_d5`: the six fault-free scenarios of round 25, the
  nine-load ladders of `load_points_v25.json` (DeFT_P at depth 4, so that every row is measured at
  the same loads), seeds 121-130: 9 x 1,620 = 14,580 runs. The main row and the references at
  depth 4 are the rows of round 25.
- **C2. Interposer depth 7 (secondary).** `X_i7` for the four references, seeds 121-130, on the
  ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat): 2,880 runs. For this comparison THR is
  the largest accepted throughput over the four loads, for every row, the main row of round 25
  included.
- **C3. Under faults (secondary).** `DeFT_P_d6` and `DeFT_B_d6` on the 48 masks of rate 4/16 and
  the 48 of rate 1/16 of round 26, uniform and hotspot traffic, the four loads of
  `load_points_v26.json`, seeds 151 and 152: 3,072 runs. The main row and the references at depth
  4 are the rows of round 26.
- **Primary family 2 (Holm over 12),** per size, over the six scenarios: the main row at depth 4
  has higher THR, and lower LAT at 1.0 x Lsat, than (a) the best of `DeFT_P_d6` and `DeFT_B_d6`
  and (b) the best of the four references at depth 6.
- **Secondary:** every reference at depth 5 and 6 against itself at depth 4 (what the area buys a
  reference); the two comparisons of the primary family at depth 5 (the references with about
  the main row's area), with intervals; the main row against each `X_d6`, `X_d5`, `X_i7` and
  against the best of each set;
  the four tuning scenarios and the other two separately; each scenario; `LB_d6` against the best
  reference at depth 6 (equal buffers again, at depth 6) and against the main row; LAT at 0.5 and
  0.8 x Lsat; C3 as round 26 (over the 16 masks, by rate and by traffic, against the best of the
  two variants at depth 6 and against each).
- **Stated in advance.** Mine: 6-flit buffers give a reference 3 to 8 % more throughput, 5-flit
  buffers about half of that. The main row stays ahead of the DeFT variants at depth 5 and 6 on
  3x3 and 4x4 and is about level on 2x2; against MTR and RC at depth 6 it is level or behind in
  throughput on every size, at depth 5 about level, and its latency at DeFT's Lsat is no longer
  lower. If so, the paper will say that the gain over MTR and RC does
  not survive equal area, and that the case for late binding rests on the references that tolerate
  VL faults.

---

## Part D: the references against the DeFT paper

- **D1. One VC per packet for MTR and RC.** `MTR_static`, `RC_static`: the six fault-free scenarios,
  three sizes, the ladders of round 25, seeds 121-130: 3,240 runs. Report: each against its
  per-hop row (THR, LAT at every load); DeFT_P against the better of the two static rows at every
  load, per size and per scenario; the main row against the best of DeFT_P, DeFT_B, `MTR_static`,
  `RC_static`, `XY_SP` (the main comparison of the paper with the other VC policy), all six
  scenarios, the tuning four and the other two.
- **D2. The set-up of the DeFT paper.** 2x2 (4 chiplets, 4 VLs per chiplet, packets of 8 flits,
  4-flit buffers, two VCs, rho = 0.01): uniform, localized (40 % intra-chiplet) and hotspot (three
  routers with 10 % each); rows DeFT_P, MTR, RC, `MTR_static`, `RC_static`; twelve rates, 0.1 to
  1.2 x Lsat of DeFT_P in steps of 0.1 (rounded to the 0.0001 grid; the ladders of rounds 25 and
  23 give Lsat at pipe_all 2 and 0); seeds 191-195; at pipe_all 2 and at pipe_all 0: 1,800 runs.
  Report the latency curves (one table and one figure per pattern) and, per pattern and pipe
  depth, the loads at which DeFT_P has the lowest latency of the three, with intervals. The DeFT
  paper states that DeFT has the lowest average latency against MTR and RC and gives no load, no
  throughput and no VC policy for MTR and RC; say plainly which of our five rows and which loads
  agree with that order and which do not.
- No test. One paragraph in `FINDINGS.md`: what explains the difference between this simulator and
  the DeFT paper, and what remains unexplained.

---

## Part E: the cost of the main row (hardware flow of round 25, Part F)

- **E1. `LB_noLA` in simulation:** the six fault-free scenarios, three sizes, the ladders of round
  25, seeds 121-130: 1,620 runs. Against the main row, DeFT_P and the best reference (THR, LAT,
  P99; LAT at 0.2 and 0.5 x Lsat), all six scenarios, the tuning four, the other two.
- **E2. RTL variants of the interposer router,** checked against recorded decisions of the
  matching simulator row as in round 25 (F2), then synthesised and timed as there:
  - the main row without the reports across the VLs (the design `LB_noVLrep` of round 27: no
    wires from the boundary router above, 24 x 3 report bits in every interposer router);
  - `LB_noLA`: no report wires or registers at all; the decision unit has the credit counts, the
    static hop terms and the bias only.
  For each: area of the four router types, the system ratio to DeFT on the three sizes (in the
  three forms of round 25: hierarchy kept, core kept, flattened), the stage times, the margin at
  T_ref and the delay left to an interposer link in the link cycle.
- **E3. The references with more buffers:** DeFT's routers with 5-flit and 6-flit buffers, and
  DeFT's interposer routers with 7-flit buffers: area and the system ratio to DeFT at depth 4, in
  the three forms of round 25 (hierarchy kept, core kept, flattened), next to the main row's
  ratios in the same forms.
- **E4. Power,** for DeFT's and the main row's interposer router (with and without a VL) and
  chiplet router on 4x4: OpenSTA `report_power` on the synthesised netlists. Activity from a VCD
  or SAIF of the RTL simulation that replays the recorded vectors of 4x4 uniform traffic at 0.5 and
  at 1.0 x Lsat, if the flow can read it; otherwise the default activity, stated as such. Report
  internal, switching and leakage power and the ratio of the main row to DeFT per router and for
  the system; the same for the two variants of E2 if E2 is done. State the limits (before layout,
  no wire capacitance, no clock tree).
- If a step of E2 to E4 cannot be done with the tools installed, say which and why, and go on.

---

## Part F: two more early binders (seeds 171-180, paired with round 28)

- **F1. `EB_first`.** Tuning of its `lut_bias` in {0, 1, 2, 4, 8} by the rule of round 24 (800
  runs; the choice as an addendum to the pre-registration). Then the six fault-free scenarios,
  three sizes, the ladders of round 25, seeds 171-180: 1,620 runs. Against DeFT_P, the main row,
  `EB_best` and `EB_down_t` of round 28: THR, LAT, the share of the main row's gain over DeFT_P;
  also the share of the heads whose commit is made at the router below the exit VL. The question:
  the main row decides at every column of a candidate, one candidate at a time. What is left of
  its gain if it decides once, at its first choice, from the same local occupancies? Against
  `EB_down_t` the row shows what the place of the single decision is worth.
- **F2. Age of the source's knowledge.** `EB_best16`, `EB_best256`: T tuned as B2 of round 28
  (2 x 480 runs), then the evaluation of F1 (2 x 1,620 runs). Report the share of the main row's
  gain (THR and LAT) against the age: 0 (`EB_best`), 16, 64 (`EB_best64`), 256 cycles, per size.
- Descriptive, no test.

---

## Part G (optional, at most 3 h): traces that load the network

The Netrace runs of round 25 (`experiments_v25_apps.py`) load the network with less than a tenth
of the saturation load. With `-netrace_compress S` on 2x2: for each of the nine traces find the
smallest S in {2, 4, 8, 16, 32} at which DeFT_P's mean latency is at least 1.5 times its latency
at S = 1, and run DeFT_P, MTR, RC and the main row there. Report the latency per trace and the geometric mean. If no S reaches the
factor, say so and stop.

---

## Part H: the artifact file

`experiments/late_binding/ARTIFACT.md`, from what the repository already knows: the six traffic
patterns of the paper with the routers they name (the three hot routers, the order of the hot
chiplets, where the 60 % of localized traffic go); the ladder rule and `load_points_v25.json`;
how the fault patterns of round 26 were drawn; the options of every row of the paper; the tuned
values of every rule (main row, `EB_best`, `EB_best64`, `EB_down_t`); how DeFT's tables are
generated (traffic, rho per size, exit and entry selection) and for which masks of the paper the
tables of DeFT_P differ between rho = 0.01 and 0.001 on 4x4 (without faults they are the same:
every router has its nearest VL); the VC policy of MTR and RC; the
fallback's order of the offered outputs; which script produces which table of `paper_data/`.

---

## Time rule

Estimate Parts B to G after the gates. Above 48 h in total drop, in this order: Part G; F2; the
rate 1/16 of C3; C2; D1 on 3x3 and 4x4; `LB_d6`; seeds 126-130 of the rows at depth 5. Parts B,
the rows at depth 6 of C1, D2, E1 and E3 are never dropped.

## Report

`report/summary.md` and `FINDINGS.md` answering:

1. Regression and gates: all pass? Are the reused rows of rounds 25, 26 and 28 reproduced by the
   new build?
2. Primary family 1: how many of 12 supported, which against? The main row on the three new
   scenarios against DeFT_P and against the best reference, per size and per scenario, and which
   reference is the best.
3. The five scenarios that the tuning never saw: is the main row ahead of the best reference, level
   or behind, per size? Ahead of the references that tolerate VL faults?
4. `LB_b0`: what does `lut_bias 2` buy on 2x2, and can the paper use one configuration for all
   sizes?
5. Primary family 2: how many of 12 supported, which against? What do 6-flit buffers buy each
   reference?
6. The main row against the references at depth 5, depth 6 and interposer depth 7, with the area
   ratios of E3 next to each, in each form of the synthesis: where does a reference with the main
   row's area reach it?
7. Under faults: the main row against the DeFT variants at depth 6.
8. `LB_d6`: does the gain of late binding hold with deeper buffers on both sides?
9. D1: what does the per-hop VC choice give MTR and RC at pipe_all 2, and how does the main
   comparison of the paper change with one VC per packet?
10. D2: at which loads and for which VC policy is DeFT_P the fastest of the three, as in the DeFT
    paper? What remains unexplained?
11. `LB_noLA`: what does the lookahead term buy in simulation, and what does it cost in area, wires
    and link budget (E2)? The same for the reports across the VLs.
12. Power: the ratio of the main row to DeFT, and how far the figure can be trusted.
13. `EB_first`: the share of the main row's gain it reaches. Is the gain of late binding that of
    one decision made late, or of deciding at several routers?
14. The share of the main row's gain against the age of the source's knowledge.
15. In one paragraph: which sentences of the paper's abstract no longer hold after this round, and
    which hold with a new number.

Also write `paper_data/`:
- `heldout_effects.csv` (per size, scenario and comparison: effect, 95 % interval, p; also the
  three pooled and the five untuned together), `lb_b0.csv`;
- `equal_area_effects.csv` (per size, set of references, scenario group and metric), with the
  measured area ratio of each set; `equal_area_faults.csv`;
- `vc_policy.csv` (D1), `deft_paper_setup.csv` (D2, the latency of every row at every load);
- `hw_variants.csv` (area, timing, link budget, power of DeFT, the main row and the two variants),
  `nola_effects.csv`;
- `early_more.csv` (F1, F2).

## Order

A0 -> A1 (code, regression) -> A2 -> PREREGISTRATION -> B0 -> timing estimate -> B1, B2
(detached) -> C1 (depth 6 first) -> D2 -> E1 -> E3 -> C3 -> D1 -> C2 -> E2, E4 -> F1 -> F2 -> G -> H -> report.
Update the README (round 29). Give a short summary at the end with the fifteen answers.
