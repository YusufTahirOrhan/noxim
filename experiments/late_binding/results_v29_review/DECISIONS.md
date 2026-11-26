# Decisions v29

Where the prompt (`PROMPT.md`) left a choice, the option that does not favour our methods was taken: in doubt the references and the
early rows are favoured. Each entry says what was open, what was chosen and why. Entries are in the order in which they came up.

## A0: regression before any change
* **Reference build.** `build_ref.sh e7569b1` exports the last commit of round 28 with `git archive` and builds it in a separate tree:
  `~/lbbin/noxim_e7569b1`, md5 dbeabbc7557f3db9be4105ddda8fe7a6, the same file as the `bin/noxim` that round 28 left. The regression
  compares against that build and, as every round, against the reference of the round before (b164e9e).
* **The two files that were placed in the repository** (`results_v29_review/PROMPT.md`, `formal/lb_cdg_check.py`) are committed with A0,
  unchanged.

## A1: the new options
* **`-buffer 5`, `-buffer 6` stopped the simulator before this round.** Noxim's power table (`bin/power.yaml`) has buffer depths 2, 4, 8,
  16, 32 and 64, and `Power::configureRouter` asserted that the depth is in it (`-buffer 5` with the e7569b1 build: assertion at
  `Power.cpp:88`). The table is not changed. For a depth that the table does not have, the four buffer entries (leakage, push, front, pop)
  are now interpolated linearly between the nearest tabulated depths below and above it with the same flit size (5, 6 and 7 between 4
  and 8). A depth in the table is read as before, so the 84 configurations are untouched. Only the three energy fields of the statistics
  depend on these entries; no comparison of this round uses them.
* **`-buffer_ipos N`: which buffers.** "Every input buffer of an interposer router, the one that receives from a Down VL included" is read
  as all six input ports of the router object (N, E, S, W, the Down-VL port, and the local port, which no packet uses on the interposer).
  The chiplet routers keep `-buffer` on every port, the port that receives from an Up VL included. The option is a global parameter
  (`buffer_depth_ipos` in the YAML, default 0 = as `-buffer`), valid for the DEFT_2_5D topology only.
* **Nothing in the statistics file says that `-buffer_ipos` was given.** A2 asks that `-buffer_ipos 4` with `-buffer 4` is byte-identical
  to the option absent, so the option writes no field. To check that the depths are the real ones there is a diagnostic,
  `-deft_lb buffer_stats 1` (off by default, observation only): the capacity and the largest fill of the input buffers per layer, taken at
  every flit that is written into a buffer. It is used in the gate `buffer_checks.md` and in no row.
* **Everything the selection reads follows the real depth without a change of the selection:** the occupancy term reads the neighbour's
  buffer (`Size()`), the full status and the fallback read `IsFull()` of that buffer, and both are per buffer. Nothing in the routing,
  the VN rules or the selection reads the global `-buffer` value (the one place that does, `Router::inCongestion`, belongs to the DyAD
  routing of the original Noxim and is not used here). The weights of the selection are not rescaled for deeper buffers: `LB_d6` is the
  frozen main row with `-buffer 6`, nothing retuned.
* **`entry_commit first`: when the commit is made.** The main row computes its decision for a router when the head leaves the router
  before it (lookahead routing). `first` is made at that moment, as `entry_commit down` is: when a head is forwarded to an interposer
  router at which the routing function offers it more than one output (with the entry mask it has after the move), the costs of the main
  row's selection for those outputs are computed from that router's state (lookahead term and `lut_bias` included, the busy term read as
  for a decision computed ahead), the output of least cost is selected with the selection's own tie rule (a draw from `rand()`), and the
  entry mask is reduced to one candidate among those that the selected output keeps: the one of least cost through that output (the cost
  the selection gives the output for a head with that one candidate, plus `lut_bias` if the candidate is not DeFT-P's entry VL while that
  VL is in the mask, as `entry_commit down` charges it), ties drawn as `entry_commit down` draws them. The head therefore reaches its
  commit router with one candidate and is offered one output there.
  * *What this reading leaves out:* the fallback of the main row cannot act at the commit router (a head with one candidate has no other
    output to ask for). The other reading, to keep the full mask until the head has left the commit router through whatever output the
    fallback gave it, would give the row one more late decision. The prompt says that the cost is "computed when the main row computes its
    decision for that router" and that the candidate is taken "through the selected output", and it calls the option "like `entry_commit
    down`", which has the same property; and the gate of A2 ("the committed VL is a candidate of least cost of the main row's selection
    at that router") can hold for every head only if the commit follows the selection and not the fallback. So the text decides for the
    first reading, although the second would be the more favourable one for the early row. The missing fallback at the commit router is
    named as a limit where `EB_first` is reported.
  * *"At most one hop with more than one offered output per head"* is checked with a counter per packet (the number of commits of one
    head, kept in a table of the packets in flight; its maximum must be 1) and with the hop counters of round 20 (no hop of an `EB_first`
    run may offer more than one output with the mask the head carries when it leaves a router).
  * *The anchor.* With `lut_bias 1e9` every commit takes DeFT-P's entry VL, but a commit draws twice from `rand()`, from which the routers'
    crossbar arbitration draws. As for the anchors of round 28 the gate compares the row with DeFT_P as it is and with the diagnostic
    `tie_stream 1`, for which both draws of a commit go to the stream of the tie-breaks.
* **The three traffic patterns.** `tornado` is defined on the chiplet layer as a whole (router (x, y) of the FW x FH grid, wrapping
  around in x), so a quarter of the sources of 2x2 send inside their own chiplet (x = 0 and x = 4) and none on 3x3 and 4x4. `neighbour`
  takes "adjacent in the chiplet grid" as sharing an edge (two to four chiplets); the rate of a source is spread evenly over all routers of
  those chiplets. `randperm` draws with a fresh `random.Random(2901)` per size: `shuffle` on `list(range(N))`, shuffled again with the same
  generator until no router maps to itself; the permutation is written to `randperm_<size>.txt` by the gate that checks the tables.
  The three patterns are written only when asked for with `--patterns`, as `chiptrans` is.

## A2: gates
* **Depth 5 is tested too.** The prompt names the drain tests for `-buffer 6` and `-buffer_ipos 7`; the rows `X_d5` run with `-buffer 5`, so
  the same tests are made for it (24 more drain tests).
* **Order of the drain tests on the new patterns.** They are asked for at 0.5 and 1.0 x Lsat, and Lsat of a new pattern is the result of
  B0. So the order is: the other gates, the pre-registration, B0 (DeFT_P with seed 101 only), the drain tests on the three patterns, the
  timing runs, B1. No evaluation run of a new pattern is made before its drain tests have passed.
* **The referee's script and `python3 -I`.** `lb_cdg_check.py` needs `networkx`, which this machine has only under `~/lbpkgs` (WSL has no
  pip). `-I` ignores `PYTHONPATH`. The script is therefore started as `python3 -I -c WRAP ~/lbpkgs formal/lb_cdg_check.py MODE`: the
  interpreter is isolated as asked (no environment variables, no user site, the script's folder not on the path), WRAP appends the one
  folder with `networkx` to the end of `sys.path` and runs the unchanged script with `runpy`. The script was read before it was run: it
  builds graphs and prints; it opens no file and no connection.
* **Reuse checks: which runs.** "Two scenarios per size at 1.0 x Lsat, the first two seeds of that round": round 25 uniform and
  movinghot (one scenario of the tuning, one that it did not see), seeds 121 and 122; round 26 mask 1 of the rate 4/16 with uniform
  traffic and mask 1 of the rate 1/16 with hotspot traffic, seeds 151 and 152; round 28 uniform and chiptrans, seeds 171 and 172, and
  there also the three tuned early rows that Part F is compared with (`EB_best`, `EB_best64`, `EB_down_t`), because they are reused as
  well. Every column of the earlier round's per-run file is compared as text.

## Part F: tuning runs
* **400 runs, not 800, for `EB_first`.** The prompt gives 800 runs for the grid {0, 1, 2, 4, 8}. By the rule of round 24 as rounds 27 and
  28 applied it (2x2 and 4x4, five scenarios, four loads, two seeds: 80 runs per configuration) five values are 400 runs. The rule is
  kept; DeFT-P and the main row are run again on the same cells (160 runs) and must equal the rows of round 27; the extension rule of
  `EB_down_t` in round 28 (16, 32, 64 if the best value is the largest) is taken over, which can add 40 runs per value and size.

## Before the gates: six smoke runs
* **Six runs of the new binary were made before anything was written down**, to see that the new options are accepted (DeFT_P on 2x2 with
  4-flit buffers, `-buffer 5` and `-buffer_ipos 7` at 2.4 x Lsat; `entry_commit first` on 2x2 and 4x4 and the main row on 2x2 at 1.0 x
  Lsat; seed 121). Their numbers are at the top of `stated_in_advance.md`, which was committed before the gates of A2 (commits 0c3988c,
  8429055; the second only corrects the time of day in its first line). The unit check of `entry_commit first` then showed the latency of
  that row on three more single runs; they are named in the pre-registration under "Gates", and the expectations were left as written.

## Time rule: the timing runs
* **What is timed.** Runs of the designs themselves, kept and not looked at: per size the seed-181 runs of B1 (every row, scenario and
  load of one seed), the references at depth 6 with seeds 121 and 122 at the 2nd, 5th and 9th load (deeper buffers carry more traffic
  beyond saturation, where a run is slowest, so B1 is no measure for them), and the seed-151 runs of C3 at the 1st and 4th load of masks
  1 to 4 of both rates; the seed-191 runs of D2. The three sets of a size run one after the other with nothing else of the round on the
  machine. Each part is then estimated with the seconds per run of the set of its kind and size, as measured, with no factor: B1 with
  its own set; every part on the scenarios and ladders of round 25 (B2, C1, C2, D1, E1 and the evaluation and tuning runs of Part F) with
  the depth-6 set; C3 with its own; D2 with its own. The rows of B2, E1 and F are late-binding rows at depth 4, which the depth-6 set of
  the references does not time exactly; no factor is put on it (round 25's estimate was 13 % above the time taken).
* **Not in the estimate: the hardware flow of Part E.** The prompt's drop list has no hardware item, and E2 to E4 have their own rule (a
  step that the tools cannot do is named). The synthesis starts after the timing runs and runs next to the simulation chain with three
  threads on the twelve logical processors, which slows the simulations while it lasts. If the time rule drops something, the hardware is
  paused before a part is given up for lack of time: the restore rule reads the clock.

## Part E: hardware
* **E3, the buffers of the references.** The reference core of round 18 has 4-flit buffers written into it, so `hw/rtl/router_core29.v` is
  that core with three macros: the depth of the input buffers, the depth behind the outputs that the credit counters count against, and
  the depth behind the vertical-link output. `DeFT_d4` is synthesised from the core of round 18 unchanged (the reference of every ratio,
  as in round 25) and `DeFT_d4c` from the new core at depth 4, to show that the new text alone changes nothing. `tb_core29.v` checks
  every depth and fails when the bench and the RTL disagree on a depth (`hw/buffer_core_check.txt`).
* **`DeFT_i7`: which buffers have 7 flits.** As `-buffer_ipos 7` in the simulator: every input buffer of an interposer router, the one
  behind the Down link included. So the boundary router of the chiplet layer counts 7 credits for its Down output and keeps 4-flit
  buffers, and the interposer router counts 4 credits for its Up output. The chiplet router without a VL is the one of depth 4.
* **E2, the two variants.** `hw/rtl/lb29_units.v` is `lb25_units.v` of round 25 with two macros that remove the reads of the reports and
  their registers (`LB_UP_REP 0`: the reports across the VLs; `LB_LOOKAHEAD 0`: every report). With both macros at 1 the text is the one
  of round 25, and the main row is synthesised again from this file next to the variants, so that the three are compared within one run.
  The router top, the core, the test benches and the Verilator checkers of round 25 are used unchanged. The vectors of a variant come
  from the simulator row it builds (`LB_noVLrep`: `-deft_lb up_report 0`; `LB_noLA`: `heur_lookahead 0`); as a control the same vectors
  are applied to the units of the main row and must give mismatches.
* **E4, what "replays the recorded vectors" can mean.** The vectors of round 25 are one line per evaluation of the decision unit. They
  carry no cycle and no port activity and exist for the main row only, so no router can be driven with them and DeFT's router not at all.
  The prompt allows the default activity when the flow cannot read an activity file; OpenSTA can read one, so both are done: the default
  activity for every router, and the activity of a simulation of each synthesised netlist under random packets at the flit rates per
  port that the instrumented simulator counts on 4x4 at 0.5 and 1.0 x Lsat (pre-registration, Part E). This is a replay of the measured
  load, not of recorded flits; the report says so next to the numbers. A replay of recorded flits through a router would need the
  credits of the simulator's neighbours, which arrive at other cycles than the RTL sends its flits (the simulator's router and the RTL
  differ in arbitration order and pipeline timing), and DeFT's RTL of round 18 has the VN rules of that round.

## B0 and the drain tests on the new patterns
* **No scenario needed the extended sweep.** DeFT_P saturates between 0.007 and 0.013 packets/cycle/source on the nine new cells
  (`load_points_v29.md`), inside the usual sweep.
* **The largest deviation of a table's sum is 3.2e-08 packets/cycle** once the tables of the ladders exist (`traffic_checks.md`; the
  pre-registration quotes 1.6e-08 from the one table that existed then). It is the rounding of the nine decimals of a line over the 48 or
  more destinations of a source under `neighbour` traffic.
* **Drain tests: 114 / 114 pass** (`drain_traffic.csv`): every row of Part B (on 2x2 also `LB_b0`) on the three patterns at 0.5 and 1.0 x
  Lsat on the three sizes delivers every packet with no dead-end event. They ran after B0 and before any evaluation run of a new pattern.

## What ran next to the timing runs
* The synthesis of E3 had started 11 minutes before the timing runs; its chain stops itself while they run (`chain_v29h.sh`, SIGSTOP to
  its process group from the second the timing stage starts, 16:26:41) and goes on after them.
* One compile of a Verilator checker (a try of the E2 vector check that I had started by hand) ran for about 30 seconds next to the
  first timing set (2x2, the Part B runs) before I stopped it. One process next to twelve for half a minute of a set of several minutes:
  the estimate of that set is high by well under 1 %, which errs towards dropping.

## The time rule: what was dropped, and how it can come back
* **Estimate 54.0 h, above 48 h: Part G and Part F2 are dropped** (`runtime_estimate.md`), the first two items of the pre-registered
  order; what is kept is estimated at 44.9 h. The runs were slower than in round 28 (9.5 s per run of a reference at depth 6 on 4x4
  against 7.8 s for the rows of round 28).
* **Taking an item back** (`restore_v29.py`, `time_rule.md`). The pre-registered sentence is applied literally at the end of every part:
  time since the start of the timing runs + what is still to run of the kept parts + the item, each at the speed measured until then
  (the time used so far over the estimate of the runs finished in it), at most 48 h. Reverse of the drop order: F2 first, G only after
  F2. Part G counts with its limit of 3 h, unscaled. The script reads the clock and counts files; it opens no result.
* **The ends of B1 and B2 passed with nobody at the keyboard** (the session that ran the round was interrupted between 17:30 and 23:45 on
  24 Nov). Their decisions were made afterwards with the times of the chain's log and only the files that existed at those moments:
  50.9 h and 50.7 h, so F2 stays dropped. From C1 on the script is run when a part ends.
* **Processors given to the hardware flow are not charged to the rule.** The synthesis and the checks of Part E run with three threads
  next to the twelve simulator processes. Their share of the machine (3 of 15 runnable processes for as long as they run) is written as
  a second number into `~/lbraw/v29/b_start.txt` and is not counted as time of Parts B to G; `time_rule.md` shows it at each decision.

## The limit of 48 h lifted by the user (25 November, 10:18)
* **What happened.** On 25 November the user asked when the runs would finish. A look at the rule at 09:44 that wrote nothing (speed
  0.989 times the estimate, 16.83 h spent, 27.58 h of the kept parts still to run) gave 50.41 h with Part F2, so F2 and Part G would
  have stayed dropped; the user was told so and answered: "Its ok to be above of 48h limit." The limit is the prompt's own rule, and the
  prompt is the user's, so their word replaces it: **Part F2 and Part G are taken back and run**, in the order of the prompt (F1, F2,
  G). `drops.json` (`dropped` empty, `restored` F2 and G, `limit_lifted` with the words and the time) and `time_rule.md` (an entry that
  says it is not a decision of the rule) were changed by hand at 10:18:29; `restore_v29.py` is unchanged and from now on finds nothing
  to decide. With both parts the estimate is 53.4 h since the start of the timing runs.
* **What was known at that moment.** The results of Part B and of the hardware parts (E2, E3, E4) had been read and are in
  `FINDINGS.md`. C1 was at 8,735 of 14,580 runs (10:17) and none of its results had been read; of D2 and C3 only the timing runs
  existed, which were not looked at; no run of D1, E1, C2, F1, F2 or G existed. F2 and G are descriptive parts without a test, and the reason they
  come back is the clock, not a result.
* **Part G keeps its own limit of 3 h.** "Optional, at most 3 h" is part of its definition in the prompt, not of the time rule. G is
  run because the only reason not to run it was the 48 h.
* **The report of Part G was written on 25 November, before any run of the part** (`report_v29.py`, `part_g`; tried on stand-in data
  made from the trace runs of round 25). The pre-registration asks for the mean latency per trace and the geometric mean over the
  traces, relative to DeFT_P: that is G.2. Added to it, also before any run: the p99 and the completion time in the same table (as
  round 25 reports its trace runs), G.3 (the same ratios as effects with the interval over the three seeds, and the main row against
  MTR and against RC, which follow from the ratios to DeFT_P) and G.4 (the same traces without compression, from the rows of round
  25). `paper_data/apps_loaded.csv` is not in the prompt's list of files; it holds G.2 and G.3.
* **Three smoke runs of the parts taken back** (25 November, 10:25 to 10:29, into a scratch folder that was deleted; next to the twelve
  processes of C1): the first tuning cell of `EB_best16` and of `EB_best256` on 2x2, and the search run of Part G for blackscholes at
  S = 32, to see that the stages start with the build of this round. Read from them: that each run ended, its dead-end count (0), the
  period it reports (16 and 256), and for the trace that every packet of the window was delivered (14,067 of 14,067) and the cycle at
  which the window was complete (767,156). No latency and no throughput of the three runs was read. The stages run the three cells
  again.
* **What is not reopened.** Nothing else had been dropped, so no other part changes. The order of the parts, the seeds, the grids and
  the tuning rule of F2 are those of `PREREGISTRATION.md` and of `tuning_v29.md`; the tuned values of F2 are added to the
  pre-registration as "Addendum F2" before any evaluation run of its rows, as for F1.

## The hand-over from the tuning of Part F to its evaluation (25 November, 13:25)
* **`addendum_v29.py` writes the addenda.** An addendum with tuned values is a record of what `f1_choose` and `f2_choose` chose by the
  rule of `tuning_v29.md`: the values, their scores, the values that were run, whether a score is below 0. It is generated from
  `tuning_choice_v29.json`, so the text is the same whoever runs the script, and it is refused if an evaluation run of the rows exists
  (a file in the raw folder of the part, or its per-run CSV). The addenda are put in front of the section "Stated in advance", which
  the pre-registration says runs to the end of the file. Tried on a copy of the file with a stand-in choice.
* **`after_c_v29.sh` does the hand-over if nobody is there.** The session that runs this round was cut off twice (a usage limit on
  24 November from 17:30 to 23:45, a connection error on 25 November from 11:16 to 13:20), and the evaluation of Part F cannot start
  before the addendum. The watcher waits 30 minutes after the end of chain c for chain d to be started by hand. If it was not, it runs
  `addendum_v29.py`, commits the results folder inside WSL (author as in the last commit; no push from there) and starts chain d.
  It chooses nothing; a chain c that failed or an addendum that is refused starts nothing. Its three paths were tried with stand-in
  logs.

## E2 and E4 as run
* **The main row is synthesised twice.** Once from the units of round 25 (in the E3 run, for the area ratios that Part C is read with;
  those netlists equal round 25's) and once from `lb29_units.v` with both macros on (in the E2 run, next to the two variants). The two
  texts pass the same vectors but are not synthesised to the same netlists (areas within 0.13 / 0.29 / 0.54 % in the three forms), so
  the variants are compared with the main row of their own file.
* **The cut configuration of a variant.** Round 25's rule is kept: the fewest registers in the decision unit that fit T_ref, and among
  those the largest worst margin. For `LB_noLA` that is the register after stage B, for the main row and `LB_noVLrep` the one after M;
  every table also gives `LB_noLA` with the main row's cut, because the delay left for the link is larger there.
* **E4, the bench.** One router of each type at a fixed place in chiplet (1, 1): a chiplet router at local (1, 1), the boundary router
  and the interposer router of the North VL, and the interposer router next to it. The NI tables of a chiplet router hold the North VL
  as exit VL for every destination chiplet (its nearest VL in both places) and all VLs functional. The reports of the five neighbours of
  a main-row router are its own report, delayed by a cycle: under uniform traffic the neighbours carry the same load, and random
  reports would toggle 150 wires in every cycle. Body and tail flits carry random bits (the simulator has no payload).
* **E4, calibration.** The bench is run on the RTL up to ten times, each time scaling a rate by target / achieved, until every rate is
  within 3 % of the simulator's; otherwise the closest try is taken. 9 of the 24 cases end outside 3 % in one rate (the worst 7 %, at
  the boundary routers, where the heads from the Up link, the heads that go down and the heads that end at the router share the same
  ports); `report/summary_hw_E4.md`, E4.2, lists target and achieved for each. Power moves by about 1 % between 0.5 and 1.0 x Lsat,
  so a rate that is 7 % off is of no consequence for the ratio.
* **E4, a third activity that was not pre-registered: the tool's default with the reset, position and table inputs held constant.**
  With the pure default every input toggles in 10 % of the cycles, the reset included, which holds the propagated activity of every
  register with a synchronous reset down. Both are reported; the pre-registered pair (pure default, simulation) is unchanged.
* **E4, the tie-low cell.** The synthesis script of rounds 18 and 25 names the output pin of `LOGIC0_X1` `ZN`; the cell's pin is `Z`.
  Area and the timing reports of those rounds do not depend on it (the cell is counted, constants are on no timed path), and E2 and E3
  keep the script as it is. For the simulation of a netlist and its power the pin is renamed in a copy of the netlist, where also
  every internal net is split into bits and given a plain name so that simulator and timing tool use the same names; every pin is
  annotated from the VCD in all 24 cases.
* **The hardware's share of the machine.** All hardware stages since the start of the timing runs lasted 6,901 s with three threads
  (`~/lbraw/logs/v29h.log`, `v29e4.log`): 6,901 x 3 / 15 = 1,380 s of the twelve simulator processes; 300 s more for the jobs run by
  hand in that time (the table comparison of ARTIFACT.md with two processes for 3.5 minutes, single tries of the E2 and E4 stages).
  1,680 s are written as the second number of `b_start.txt` and are not counted by the time rule from the end of C1 on.

## The report: what answer 15 is written against (25 November, 14:59; before a result of C1, D, E1, F or G was read)
* **The paper is not in this repository.** Question 15 asks which sentences of the paper's abstract no longer hold and which hold with
  a new number. Neither draft (v7, v8) is among the files of the repository, so the wording of its abstract cannot be quoted or
  checked. Answer 15 is therefore written against the statements that the prompt attributes to the paper ("Where we are", points 1
  to 3) and the headline results of rounds 25 to 28 that the paper's tables are built from (`paper_data/` of those rounds): the main
  row against the best reference in THR, LAT and P99; against DeFT without and with VL faults; its cost in area and its timing; the
  share of the gain that needs late binding. Each is given as a claim with the number of the earlier round and marked "does not
  hold", "holds with a new number" or "not touched by this round". Whoever holds the draft maps the list to its sentences; a sentence
  of the abstract that makes none of these claims is not judged here.

## The hand-over as it happened (26 November, 10:50)
* Chain c ended at 10:49:37 with both choices made. The hand-over was done by hand inside the watcher's 30 minutes: the watcher
  `lb_v29w` was stopped, `addendum_v29.py` wrote Addendum F1 and Addendum F2 into `PREREGISTRATION.md` (10:50), the tuned values went
  into `ARTIFACT.md`, the commit was pushed (3722f90) and chain d was started at 10:51:05. No evaluation run of a row of Part F existed
  before the addenda were committed.

## F2: the T of `EB_best256` on 2x2 is the cap of the rule (26 November, 10:53; before any evaluation run of Part F was read)
* **What the tuning gave.** The rule of `tuning_v29.md` (B2 of round 28, unchanged) doubles T while the best T is the largest, "64,
  128 at most". For `EB_best256` on 2x2 it chose T = 128, the cap, and the score still rises there (T 64: -0.19; T 128: +0.10). On
  4x4 the same row peaks at T = 64 and falls at 128, so there the cap did not bind. On 2x2 a T that the rule does not allow may
  serve the early row better, and then the share of the main row's gain that the pre-registered `EB_best256` reaches on 2x2 would
  understate what an early binder with knowledge 256 cycles old can reach.
* **What is done about it.** The pre-registered row is not touched: `EB_best256` on 2x2 is T = 128, as Addendum F2 says, and the
  tables of Part F are those of the pre-registration. Next to it, `extra_v29_age.py tune` runs the 40 tuning cells of 2x2 with T =
  256 and 512 (doubled further while the best T is the largest, 4096 at most) and writes `tuning_v29_extra.md`. If a T beyond the
  cap scores higher than T = 128, `extra_v29_age.py eval` runs the 540 cells of the evaluation of Part F on 2x2 with it as an extra
  row, `EB_best256x`, and `FINDINGS.md` gives its share next to the pre-registered one. If none does, the cap did not bind and
  nothing more is run. This favours the early row, which is the side the standing rules say to favour in doubt; it is defined
  here, after the tuning scores were seen and before any evaluation run of Part F was read.
* The runs go next to chain d with two processes (2x2 runs of about 15 s each); they are not part of the time rule's account.
* **Result (10:57, `tuning_v29_extra.md`, `tune_age_extra_runs.csv`; 80 runs, no dead-end event).** T = 256 scores +0.010 and T = 512
  +0.006, against +0.105 at T = 128: with a larger threshold the row falls back to DeFT_P, whose score is 0. **The cap did not bind
  the choice; T = 128 is the best T on 2x2 too, and no extra row is run.** `extra_v29_age.py eval` was not started.

## Part G: a clock for its 3 h (26 November, 12:32; before Part G started)
* The prompt gives Part G "at most 3 h", and the 48 h rule that the user lifted is another rule: the 3 h stay. `chain_v29c.sh d` runs
  `g_find`, `g_eval` and `g_csv` without a clock, and the session that drives the round was interrupted twice before. So a watcher,
  `g_clock_v29.sh` (session `lb_v29g`, log `~/lbraw/logs/v29g.log`), started at 12:32:37 while chain d was in the evaluation of F1,
  reads the start time of `g_find` from the chain's log and stops the chain when 3 h have passed since then and it has not ended
  (dry runs on stand-in logs before the start: a start 100 s ago with a limit of 60 s, a chain that has ended, a start 10 s ago
  with a limit of 25 s). The 3 h are wall time from the start of `g_find` to the end of `g_csv`, with nothing else on the machine.
* If the clock stops the part: the search and the traces whose runs are complete by then are reported as they are, the others as
  "not finished inside the 3 h", and nothing of Part G is started again.

## Tables added after the results (`extra_v29.py`; none is a test, none changes a pre-registered table)
* **`report/extra_B.md`, X.1** (after Part B): the accepted throughput and the latency of every row at each of the nine loads on five
  cells of Part B. Reason: the one test of family 1 that is against the main row (THR against the best reference on 2x2) comes from
  `randperm` alone, where the main row's THR is even below DeFT_P's, while its latency at 1.0 x Lsat is the lowest of all rows. The
  table shows where on the ladder the rows part: THR is a number from the last load.
* **`report/extra_C.md`, X.2** (defined on 25 November at 06:35, while C1 was at 6,067 of 14,580 runs and none of its results had
  been read; the code was run on stand-in data only): the three measured comparisons of the main row against the best reference
  (references with 4-flit buffers of round 25, with 5-flit and 6-flit buffers of C1) read at the area of the main row, by linear
  interpolation of the per-seed log ratio in the system area of E3, in each form of the synthesis, and the buffer depth at which the
  interpolated effect stops being in favour of the main row. Reason: question 6 asks where a reference with the main row's area
  reaches it, and no measured depth has that area (5.3 to 5.5 flits with the hierarchy kept, 4.5 to 4.9 in the other two forms). It
  is a reading aid for the measured columns, which stand next to it; no reference with such buffers was run, and the areas are taken
  as exact. Not in the pre-registration, so no claim of the round rests on an interpolated figure alone.
* **`report/extra_C.md`, X.3** (added on 25 November at 18:37, after the results of C1 had been read): THR and LAT of the main row,
  of `LB_d6` and of each reference with 4-flit, 5-flit and 6-flit buffers per size and scenario (mean over the ten seeds), with the
  best of the four marked, and the count of which reference is the best. Reason: C.3 and C.4 compare with "the best of the four"
  and do not say which row that is, and the report of Part C has no table of absolute values.
* **`report/extra_E.md`, X.4** (added on 25 November at 20:55, after the results of C1 and of E1 had been read): `LB_noLA` against
  the best reference with 4-flit, 5-flit and 6-flit buffers (the best of the four, of the two DeFT variants, of MTR and RC), with
  the main row next to it and the areas of E2 and E3. Reason: the pre-registered tables of E1 compare the row with the main row,
  with DeFT_P and with the references with 4-flit buffers only, and E2 had shown that with the hierarchy kept the row has the area
  of a reference with 5-flit buffers on 3x3 and 4x4 within 0.6 points (1.170 and 1.172 against 1.167 and 1.166). That makes the
  one comparison at equal area of this round that is measured on both sides and not interpolated; the runs are those of E1 and C1
  on the same seeds and ladders. Seen before it was defined: the tables of C1 and of E1, so it is a description and no test.
* **`report/extra_C.md`, X.5** (added on 26 November at 00:52, after the results of C3 had been read): under faults, per size, rate
  and traffic pattern, on how many of the 16 masks `DeFT_B_d6` is the better of the two variants with 6-flit buffers, and on how
  many masks the main row is ahead of the better variant (with 6-flit buffers, and with 4-flit buffers from the runs of round
  26). Reason: C.8 gives effects with intervals over the masks; it does not say which variant "the best" is, and an interval
  that includes 0 does not say whether the masks are split or each of them is a tie. Counts of signs of the per-mask means, no
  test.
* **`report/extra_D.md`, X.6** (added on 26 November at 04:34, after the results of D1 had been read): the per-hop rows against
  their static rows (D.1.1 gives the static row against the per-hop row; question 9 asks what the per-hop choice gives, and the
  two directions differ where the effects are large), which of the five references is the best per size, scenario and metric
  with each VC policy and the count over the 36 cells, the main row against the best of the five per scenario with each policy,
  the main row and DeFT_P against each static row alone, and the absolute values. Reason: D.1.3 compares the main row with "the
  best of DeFT_P, DeFT_B, `MTR_static`, `RC_static`, XY_SP" and does not say which row that is; it turned out to be a DeFT
  variant in 25 of 36 cells, which changes what the comparison is a comparison with. Same runs and statistic as D.1, no test.
* **`report/extra_C.md`, X.7** (added on 26 November at 08:57, after the results of C2 had been read): the `X_i7` rows next to
  the rows with 5-flit and 6-flit buffers with THR over the same four loads for every row: each `X_i7` against the same reference
  with 5-flit and with 6-flit buffers, the main row against the best of each set, the best `X_i7` against the best of each other
  set, the absolute values with the best `X_i7` marked and the count of which reference is the best, and the comparison of the
  main row with the 4-flit references and with `X_i7` read at the area of the main row in each form of the synthesis (the per-seed
  log ratio interpolated linearly in the area between the two measured sets, as X.2 does between the depths). Reason: as
  pre-registered, C.2 and C.3 take THR over the four loads of C2 in the lines with `X_i7` and over the nine loads in the lines
  with `X_d5` and `X_d6`, so the report cannot say whether 7-flit buffers in the interposer routers give a reference more or less
  than 6-flit buffers in every router; and with the hierarchy kept `X_i7` has the main row's area within two points, while in the
  other two forms the main row is smaller, so question 6 needs a reading there as well. The interpolation on the way to `X_i7` was
  defined after the results of C2 were seen (X.2 was defined before those of C1); `extra_C_ipos7.csv` holds its figures. No
  reference with 5-flit or 6-flit buffers in the interposer routers alone was run or synthesized. No test.
* **`report/extra_C.md`, X.8** (added on 26 November at 08:59, after the results of C2 had been read): the main row against the
  best of the four references of each set (4-flit, 5-flit, 6-flit buffers; 7-flit buffers in the interposer routers) with one of
  the six scenarios left out. Reason: C.4 shows that against references with deeper buffers the main row is far ahead in one or
  two scenarios and behind in others (on 3x3 +27.7 % of throughput under `chipperm` against the best `X_i7`, and -6.6 % to
  +3.1 % in the other five), so the mean over the six scenarios, on which the tests of primary family 2 are made, does not show
  what it rests on. The verdicts of family 2 are not touched: they are what was pre-registered. The table is a description of
  the same runs with the same statistic, and what it shows is against the main row on 3x3.
* **`report/extra_F.md`, X.9** (added on 26 November at 12:54, after the results of F1 had been read): from the counters of the
  measured heads, at how many interposer routers a head of the main row is offered more than one output (per head that moves Up,
  by load and by scenario), and the share of the heads that move Up on a VL that is not DeFT-P's entry VL for the main row,
  `EB_first`, `EB_down_t`, `EB_best` and the aged rows. Reason: question 13 asks whether the gain of late binding is that of one
  decision made late or of deciding at several routers, and the report of Part F gives the share that one decision reaches but
  not how many decisions a head of the main row has, nor how boldly each row uses its decision. Counters of the same runs
  (round 28 and F1; F2 when its runs are finished); no statistic, no test.
