# v25 decisions: confirmatory round for late binding with XY, and the hardware of the final design

The conservative option is the one that does not favour late binding. Nothing is tuned in this round; where the prompt left a
choice open, the choice is recorded here before the runs it affects.

## A5: regression before anything else
* **Reference binary.** `~/lbbin/noxim_ce6ab6a`: commit ce6ab6a (the last commit of round 24) exported with `git archive` into
  a separate tree and built there with the repository's Makefile (`build_ref.sh`, new in this round). Its md5 (2b58bee0...)
  equals that of `bin/noxim`, so the binary left by round 24 is the build of ce6ab6a and no rebuild was needed.
* **Regression** (`regression.md`): the 84-configuration set, whole stats files byte by byte against the ce6ab6a build: the
  8d84634 build (the reference of the v24 regression), `bin/noxim` with the options absent, and `bin/noxim` with every option of
  rounds 23-24 given explicitly off: 84 / 84 each.
* **Added: the rows of this round reproduce round 24** (`reuse_check.md`). Three v24 evaluation runs per row (the four frozen
  rows, DeFT_P, DeFT_B, MTR, RC; drawn with `random.Random(2511)`) were run again with `experiments_v25.row_args`: 24 / 24
  identical in every compared field. The row definitions of this round call the v24 code (`experiments_v24_eval.row_args`),
  which reads `results_v24_xy/tuning_choice.json`; the check shows that nothing drifted between the two drivers. These runs use
  the v24 seeds (111-115) and are a reproduction, not an evaluation.

## A1
* `results_v24_xy/DECISIONS.md`: the authors of O1TURN corrected to Daeho Seo, Akif Ali, Won-Taek Lim, Nauman Rafique and
  Mithuna Thottethodi (ISCA 2005). The README of round 24 cites the work by name only and needed no change.

## A2: scenarios and reference rows
* The eight scenarios are those of the prompt; in tables a scenario with one faulty VL per chiplet is written `uniform+f`,
  `hotspot+f`.
* **XY_SP** is `experiments_v23.methods(size)['XY_SP']`: `-routing INTERPOSER_AWARE_XY` (the v10 definition) with DeFT-P's VN
  options. It runs with `-deft_lb count_vl 1` like DeFT_P and DeFT_B (the option only counts; `report/sanity.md` compares a
  run with and without it).
* **DeFT_Dis and DeFT_Ran** are the v23 definitions (`exit near entry near` / `exit ran entry ran`, XY on both layers, DeFT-P's
  VN options), with `-deft_lb hop_stats 1`.

## A3: ladders
* The prompt asks for ladders of the three scenarios the tuning did not see "by the v23 D1 rule". Round 23 had already made
  ladders for exactly these scenarios by that rule (its D1 swept all seven v9 scenarios), and `load_points_v24.json` carries
  them. They are **made again in this round** with `bin/noxim` (`experiments_v25.py sat`, `points`) and compared with the v23
  values; `load_points_v25.md` says whether they are equal. If one were not, this round's ladder would be used.
* `load_points_v25.json` also keeps the pipe_all 0 ladders of round 23 unchanged; Part E reads them.

## A4: drain tests
* The four frozen rows with their tuned values at pipe_all 2 (the depth of Parts B-D): v10 protocol and masks with the v23 LUT
  of each mask on the three sizes, plus over-saturated 4x4 runs at 2.4 x Lsat on localized and movinghot (sources cut off
  after 3000 cycles).
* **Added:** the two late-binding rows of Part E at pipe_all 0 (`CI_heurLA_X` with an ideal decision and `CI_heurLA_X_DLY`),
  the same protocol, with the 2.4 x Lsat rates of the pipe_all 0 ladders. Round 24 drained the ideal variants at pipe_all 0
  only with the v10 parameters.

## Part B
* **Processes.** The timing runs and the evaluation use 10 processes; two cores are left to Part F, which the prompt asks to
  run in parallel on two threads. The 36 h rule is applied to the estimate for 10 processes.
* **Timing runs** are the seed-121 runs at the 2nd, 5th and 9th load of every cell, as in round 24: runs of the design, kept,
  not looked at before the design has run.
* **Best baseline.** Per (size, scenario, metric) the reference row available on the scenario with the best arithmetic mean
  over the ten seeds. A size effect averages, per seed, the log ratios of the eight scenarios, each against its own best
  baseline.

## Part C
* **Drain tests of every row.** The prompt asks for an all-pairs drain test of the two candidates on every mask. The four
  reference rows are drained on the same masks as well, so that "every packet must arrive" is checked for every row of the
  sweep.
* **2x2 masks.** The prompt takes the 2x2 masks as covered by the 897 masks of round 24. Those are all masks with at most three
  faulty VLs plus 200 random ones; the masks of the sweep have 4, 8 and 12 faulty VLs, so the model check is run on every 2x2
  mask of the sweep that is not among the 897.
* **Ladders.** The D1 sweep is run upwards in batches and stops after the first rate whose latency exceeds 3 x L0. Lsat is
  defined by the first exceedance, so the result is the one of the full sweep; only runs far beyond saturation are saved.

## Part D
* **Seeds 41-43**, as the v13 and v15 protocols. The prompt lists new seeds for Parts B, C and E only; Part D is descriptive
  and no frozen row has ever been run on a trace.
* **Window.** The 700,000-cycle window of rounds 13 and 15 (`results_v13_apps/window.json`), not re-chosen.

## Part E
* The frozen selection values are used at pipe_all 0 as they are (they were tuned at pipe_all 2).

## Part F
* **What is built.** The interposer router of the three heuristic rows the prompt lists: LF with XY (`CI_heurLA_X_LF`, the
  main row), LF with the VN-split order (`CI_heurLA_O_LF`) and DLY with XY (`CI_heurLA_X_DLY`; one decision unit per input
  port, and one per router). The Q-learning row is not built. The core (buffers, allocators, crossbar) is the reference core
  of round 18, unchanged; `core25.v` adds the input-VC control of LF, which asks for its output in the VC-allocation stage.
  Chiplet routers: the chiplet router of round 18 with the exit LUT; on 2x2, where the default-VL penalty is 2, with a table
  of the default entry VL (16 (C - 1) x 2 bits) whose entry is written into the head (`chip25_top.v`).
* **LF without a sideband request.** Round 23 assumed that the downstream router computes on a pre-route request sent by
  the upstream router over sideband wires. The RTL of this round does not use one: the decision unit of an input port
  reads the head from the link, and its result is stored per input VC (two entries per VC: packets have at least two
  flits and a buffer holds four). This needs no wire that the reference router does not have, and it is the conservative
  choice for the timing question: the decision has two cycles (link, route) instead of the three of W = pipe_all + 1.
  The variant with a request from the upstream router is described in `hw/FINDINGS_hw.md` and not built.
* **Per-candidate cost.** With one dimension order per packet every entry candidate has exactly one minimal move, so the
  RTL computes one cost per candidate (four) and takes the output of a candidate of least cost. This is the simulator's
  `w f + 1 + bestContinuation + lutBias` per output, rearranged; the vectors check that the two agree, cost by cost.
* **With XY the N and S input ports have no decision unit.** A head that arrives from N or S has one candidate left (a
  chiplet has one VL per column). The vectors confirm it: no selection with more than one offered output after a move
  north or south in any run of the XY designs.
* **Vectors from simulator runs without a simulator option.** The prompt expects no new option. The vectors are dumped by
  an instrumented copy of the simulator, built by a patch script from the sources of this commit (`hw/tb/patch_vecdump.py`,
  `vecdump.inc`); `src/` is untouched and `bin/noxim` is not rebuilt. Every instrumented run is compared with the same run
  of `bin/noxim`: the statistics files must be byte-identical. The vector runs use seed 1 (not an evaluation seed).
* **Tie break.** The simulator draws at random among the outputs of least cost; the RTL uses a rotating priority driven by
  a 3-bit LFSR. The check gives the unit the simulator's choice as the pointer (the unit must return it), and sweeps the
  pointer over its five positions (the unit must return the first output of least cost at or after it). The LFSR itself is
  not compared with the simulator's generator.
* **Timing conventions.** Stage time = arrival + setup on the flattened netlist (1 ns - slack), as in rounds 18 and 21;
  router positions are input straps. A stage that starts on a link gets T_CQ = 0.11 ns added (the clock-to-output delay of
  the upstream output register; a path launched at an input port does not contain it). **T_ref** of a router type and size
  is the longest stage of the DeFT router of that type and size, synthesised in the same run. A cut configuration fits a
  period when every stage of the decision path does, on the four interposer routers (two types, 2x2 and 4x4); L_dec is 1 +
  the number of cuts of the fitting configuration with the fewest cuts. The spread of the flow is measured on the chiplet
  routers (unchanged logic): a margin below it is called marginal.
* **Residual from the RTL, not from the formula.** LF: residual = max(0, L_dec - 2); DLY: decision_delay = L_dec - 1.
  Both are measured in RTL simulation (`hw/latency_check.txt`: cycles of a head through an idle router for every design
  and cut configuration).
* **Area: hierarchy kept is the primary figure**, as in round 18. The flattened figure favours the designs of this round
  (flattening removes the Local output port of the interposer router, which the relation never requests, from these
  designs and not from DeFT's RTL), so a third synthesis keeps the router core as one module and flattens the rest
  (`f_semi`); all three are reported.
* **Correction of the area accounting of round 18.** Its parser (and the first tables of this round) counted sub-modules
  without parameters as cells of no area: `xy_dir` inside the route units of DeFT, MTR, RC and the reference (about 190 um^2,
  0.9 % of an interposer router) and, in this round, `lb25_single` and `lb25_fallback`. The totals of this round are checked
  against the synthesis tool's own design area on all 344 netlists. Round 18's ratios of the late-binding routers to DeFT
  were therefore about 1 % too high; its files are not changed.
* **An addendum row.** At the reference period the evaluated main row is the mechanism that is built, so the pre-registration
  does not require an addendum. The result depends on the link cycle being available to the decision and on the clock
  period; under either condition the buildable LF has one residual cycle, a row that was not evaluated. The conservative
  choice: that row is pre-registered (`PREREGISTRATION_addendum.md`) and run on the Part B design, for the main row only.

## Report
* **The report was run on the finished sizes while 4x4 was still running.** When the 2x2 and 3x3 runs of Part B were complete
  (12,600 of 18,900 runs), the report script and the second computation of the families (`check_v25_families.py`) were run
  on them in a scratch folder, to test both on real output. Nothing of the design, the rows, the metrics or the tests was
  changed afterwards, and no run was added or removed. Two things were changed in the report script as a result, both
  descriptive: (1) the latency figures: a row now keeps its colour, dash and marker in every panel and the legend lists every
  row (the first version listed only the rows of the last panel, and the fault-only rows took the colours of MTR and RC);
  (2) two tables were added, in no family and with unadjusted intervals: per cell (one scenario on one size), in how many
  cells each primary row is better or worse than each reference row (B.6), and the decision hops per scenario (in B.11).
  They were added because the picture differs between the scenarios, which the size-level tables hide.
* **A second computation of the two families** (`check_v25_families.py`, `report/families_check.md`): the 18 tests of Part B
  and the 12 of Part C are computed from the per-run CSVs by a script that shares no code with the report, and compared with
  the report's values. Not asked for by the prompt; added as a check of the statistics. The nine tests of the addendum were
  added to it before the addendum's 4x4 runs were finished.
* **Extra descriptive tables** (`extra_v25.py` -> `report/extra_D.md`, `extra_E.md`, `extra_A.md`). Numbers that `FINDINGS.md`
  quotes and the tables of `report_v25.py` do not hold (counts of cells, differences in cycles, the ladder of Part E above
  1.0 x Lsat, the reference rows among themselves). Read only, no test, unadjusted intervals; written after the results of
  the part were seen, and labelled descriptive wherever they are quoted.
* **Part E against the four-cycle model.** The comparison uses the Part B runs of the same four scenarios (seeds 121-130)
  next to the Part E runs (seeds 141-145). The seeds and the row differ (Part E has the ideal decision, Part B the LF
  mechanism), so the differences between the two models are read as sizes, not tested.
* **The addendum report was run on the finished sizes while 4x4 was still running** (2x2, then 2x2 and 3x3, in a scratch
  folder), as for Part B. Nothing of the row, the design or the nine tests was changed afterwards. Three things were changed
  in the report script as a result, all descriptive: the per-scenario cost of the residual cycle at 0.2 and 0.5 x Lsat and
  the share of stored decisions that differ from a fresh one were added, so that every descriptive item of
  `PREREGISTRATION_addendum.md` has a table; the row's latency against the offered load is written to its own file
  (`paper_data/addendum_latency_load.csv`) instead of into the figures of Part B, which show the frozen rows only; and the
  row against each reference row is written to the CSVs.
* **The addendum family stays apart.** Its nine tests have their own Holm correction and are reported next to the primary
  family; the count of the primary family is 17 of 18 with or without them.
* **Q-learning against the heuristic at equal residual delay** (`report/extra_A.md`, Y.6). No pre-registration names this
  comparison; it was made after the addendum results were seen, because the addendum row is the heuristic with the cycle the
  Q-learning row has. It is unadjusted and descriptive. The answer of record to question 5 is the frozen comparison of
  Part B (Q-learning adds nothing); Y.6 only says where its latency difference comes from.
* **Area of the design with one residual cycle.** `FINDINGS.md` quotes the synthesised configuration with two registers in
  the decision unit (what a 1 ns clock would need). The other case, a decision that starts one cycle later because the link
  cycle is not available to it, was not synthesised as a configuration of its own.
