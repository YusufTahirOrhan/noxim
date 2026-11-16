# Decisions v27

Choices the prompt left open. Where there was a choice, the option that does not favour our methods was taken.

## A0 / A1: regression and the new options
* **Reference.** The d641861 build (the last commit of round 26), exported with `git archive` and built in a separate tree
  (`build_ref.sh d641861`). No simulator source changed between ce6ab6a and d641861, so it has the md5 of the two earlier
  reference builds. The regression is run twice: before any change (`regression_before.md`) and with the new options in the
  binary (`regression.md`). The three comparisons are those of round 26: the previous reference build (ee0e247), `bin/noxim`
  with the options absent, and `bin/noxim` with every option given explicitly at its default. The explicit list of the second
  run is the list of round 24 plus `oracle_scope vl`, `oracle_period 0`, `entry_commit off`, `up_report 1`, `entry_stats 0`.
* **`oracle_scope route`, which buffers.** As the prompt lists them: for every hop of the XY route on the interposer, the
  input buffer of the router the hop leads to at the port it arrives through, and the Up input buffer of the chiplet router
  above the candidate. The buffer in which the head arrives at the interposer router below the exit VL is not counted: the
  exit VL is fixed by the LUT, so that buffer is the same for every candidate and cannot change the choice. The option is
  rejected unless the exit is `lut`, the entry `oracle` and `ipos_tm` XY.
* **`oracle_period P`, when the sample is taken.** At the first process of a cycle that is a multiple of P: the routers call
  the sampling function at the top of their two processes (where `fastTick` is called), and the injection-time choice calls
  it too, for a source that runs before every router of the cycle. A source does not change a router buffer in the same
  cycle (it writes a signal), so the sample is the state of the buffers at the start of the cycle whichever process comes
  first. Before the first sample the occupancies are 0 (the network is empty during reset). One sample per VL holds both
  the entry and the exit occupancy; the rows of this round use the entry only. `oracle_period 1` is not `oracle_period 0`:
  0 reads the buffers at the moment of the choice inside the cycle, 1 at the start of the cycle.
* **`entry_commit down`, details the prompt left open.**
  * It is defined for `-sel DEFT_HEUR` and rejected with another selection: the cost is the heuristic's.
  * The head is not in the interposer router below when it is forwarded Down, so the busy term of the cost is read as for a
    decision computed ahead, exactly as the main row's lookahead reads it for the same router at the same moment.
  * The penalty D is charged to a candidate that is not the default entry VL only while the default VL is a candidate
    (as `lut_bias` stops charging once the default VL is gone).
  * A candidate whose one-candidate mask offers no output in the head's virtual network is skipped; with a turn model
    that offers more than one output for one candidate the cheapest is taken. Neither happens with XY on the interposer.
  * The entry mask is only ever reduced to a subset of itself, and only at this one move.
* **`up_report 0`.** Exactly as specified: in the lookahead term of the Up output of an interposer router the occupancy part
  of every continuation is 0. Rejected with `-sel DEFT_FAST`, which has its own lookahead values.
* **`entry_stats 1` (not in the prompt).** An option that only counts, added for two of the secondary items: the share of
  packets whose entry VL is not DeFT-P's, and the age of the injection-time choice. It counts the Up moves of heads in the
  measured window, those on a VL that is not the LUT's entry VL for the destination router, and two sums of
  (cycle - generation cycle of the packet): at the Up move and at the injection. The new rows carry it. So does the main
  row in Parts B and C; it is otherwise built by `experiments_v25.row_args`, and unit check 1 (`unit_checks.md`) compares the
  main row with and without the option on 18 runs. The reuse check of Part E runs the main row without it.
* **The age of the choice, with counters only.** The prompt allows a counter and nothing more. So the age is not measured
  per packet. It is the difference of two means over the measured window: the mean time since generation at the Up move,
  minus the mean time since generation at the injection of the head (which is when the choice is made). The two means are
  not over exactly the same packets at the two ends of the window; it is an estimate.
* **`commit_check N` (not in the prompt).** A diagnostic option for the unit check of `entry_commit`: for the first N bound
  heads of the measured window it computes the costs the main row's selection gives the outputs of the same router from the
  same state. It compares sets of cheapest outputs and draws no random number, so "what the main row would choose" is
  reported as: the committed output is the one cheapest output, is one of several cheapest outputs (a tie), or is not a
  cheapest output (a difference).
* **Selection of the injection-time rows.** The definition of `EB_vl` names none, so Noxim's default applies. It is never
  asked: no hop of these rows offers more than one output (checked in every run).
* **`-deft_lut_entry dst` is not given to the `EB` rows.** Their entry VL is not from the LUT. Their exit VL is the LUT's
  `source_exit` with or without the option, as for the main row.

## A2: gates
* **Anchor.** Compared are all fields of the `summary` block except the three energy fields, and the delay statistics of the
  `deft_lb` block. The power model charges the routing function by its name, so the energy of `-routing DEFT` and of
  `-routing DEFT_LB` may differ while every packet takes the same path at the same time; the file says in how many runs
  the energy is equal too.
* **Drain tests twice for the tuned rows.** A2 comes before the tuning, so `EB_vl`, `EB_route` and `EB_vl64` are drained
  first with `oracle_beta 1` (`drain_v27.csv`) and again with their chosen values before Part C (`drain_v27_tuned.csv`).
  The choice of `oracle_beta` cannot change the relation (one candidate either way), but the rows are tested as they run.
* **The mask with the same VL faulty in every chiplet** is the mask of rounds 9 to 26 (0x1111, 0x111111111,
  0x1111111111111111).
* **"One candidate" in unit check 2:** the first mask (in hex order) of round 25 that leaves every chiplet one functional VL.

## Before the pre-registration
* **A smoke run of every new row was looked at.** To see that the options run, one run of each new row was made on 2x2 and
  on 4x4 (uniform, 1.0 x Lsat, seed 101, `oracle_beta` 0 and 1) and its numbers were read. Seed 101 is a tuning seed, not an
  evaluation seed, and these runs are not part of any design; but the expectations in the pre-registration were written
  after them, and it says so.

## After the pre-registration, before any run of Parts C and E
* **Three descriptive tables were added to the report script** (`report_v27.py`, committed before the tuning ended and
  before any run of Parts C and E; on synthetic data only): every row against DeFT_P per scenario (C.6), the entry-VL
  counters per scenario (C.8), and in Part E the same early rows without faults, from the uniform and hotspot runs of
  Part C (E.6), so that question 13 can be answered from one page. None of them is a test.
* **A value that rounds to zero is printed as `0.0`** in the report tables, not as `+0.0` or `-0.0`. The CSV files hold the
  values with two decimals and their sign.

## Part D
* **The best reference** of a cell (scenario, size, load) is the reference with the lowest mean latency over the ten seeds;
  the main row is then compared with that reference seed by seed. The per-size number is the mean over the six scenarios of
  these log ratios, so the best reference may be a different row in each scenario. This is the reading of the prompt
  ("the best reference chosen per scenario, size and load") and it reproduces the 15 numbers of the independent
  computation to the printed decimal.
* **Latency above saturation is reported as measured,** with the accepted share of the offered load next to it. From
  1.4 x Lsat on no row delivers the offered load; the mean latency is then that of the packets that arrived, and a row that
  delivers more packets to congested destinations carries their waiting time in its mean. The table does not correct for
  this; `FINDINGS.md` says so where it reads the table.

## While the tuning ran (16 Nov, about 07:00)
* **The PC is shared, and the runs take about 1.7 to 2 times as long as in round 26.** Since 03:03 another application
  of the user runs on the PC and uses about 5 of its 12 hardware threads (measured twice: 4.9 on average since it started,
  5.1 over six seconds). A 4x4 run of the tuning takes about 200 s of one of the twelve process slots; in round 26 it took
  about 100 s. The simulator is not the cause: the d641861 build and the build of this round, started together on the same
  3,000-cycle 4x4 DeFT_P run, needed 66 and 67 s of processor time and wrote the same file. No result depends on the speed
  of the machine. Two things do: the durations, and the time rule of Part C.
* **The reuse check of Part E passed** (`reuse_check.md`): DeFT_P and the main row on masks 1 and 2 of every size, run with
  the build of this round, are identical to the rows of `results_v26_faults/fault_rate_runs.csv` in 192 of 192 runs, in
  every column. So the five reference rows of Part E are taken from that file and not run again.
* **The time rule on a shared machine** (fixed here, before the timing runs; it goes into the addendum of the
  pre-registration with the chosen values).
  1. The estimate is the one the timing runs give as they are measured, with whatever else runs on the PC at that time. We
     do not wait for a free machine and we do not correct the estimate. What is dropped follows the pre-registered order.
     The pre-registration says that each timing set has the machine to itself: that holds for the jobs of this round (no
     other job of the round runs next to a timing set), not for the PC, and `runtime_estimate.md` will say so.
  2. One addition. If something was dropped and the runs then go faster than estimated (the other application ends), the
     dropped items are run after all, in the reverse of the drop order (seeds 166-170, `LB_noVLrep`, `EB_vl64`, Part E):
     the items of Part C when the kept runs of Part C are done, Part E when Part C is complete. An item is run only if the
     time since the start of the timing runs plus the time of that item at the speed measured until then is at most 30 h.
     The decision reads the clock and the number of finished runs, nothing else: no result of Parts C and E is looked at
     before it and the report scripts are not run before it. So the budget of 30 h is kept either way, and the data are the
     most the budget allows. Without this addition a slow hour at the time of the timing runs would cost Part E for good.
* **The other application was closed at about 07:40** (by the user, who was told what it cost). From then on the 4x4 runs of
  the tuning finish at 7 to 8 per minute, against 3 to 4 per minute before: the speed of round 26. The 4x4 half of the
  tuning therefore ran partly on the shared and partly on the free machine, which changes its duration and nothing else.
  The time rule stays as fixed above, whatever the machine does at the time of the timing runs.

## After the tuning (16 Nov, about 09:20)
* **The values are the rule's, with no judgement added.** All six choices are interior points of the grid, so no
  extension step ran. For `EB_route` the score is flat towards large values (4x4: -0.119, -0.116, -0.128 at 2, 4, 8); the
  rule takes the largest and so do we.
* **A table of the tuning by scenario was added** (`tune_scen_v27.py`, `tuning_by_scenario_v27.md`). It is not in the
  pre-registration. It reads the tuning runs only and changes no choice. Reason: every tuned early row scores below
  DeFT-P, and the mean over the five scenarios hides that the three rows are close to the main row under hotspot traffic
  and far behind DeFT-P under chipperm and chiptrans traffic. Whoever reads the addendum should know what was known
  before Part C. The table also shows the score of every value in every scenario, so that one can see that the outcome
  does not hang on the chosen value: no value brings an early row to the main row's score in any tuning scenario.
* **The expectations of the pre-registration are not rewritten after the tuning.** They were written before any tuning
  run and the tuning runs already speak against two of them (`EB_vl` and `EB_route` at least level with DeFT-P). They stay
  and are compared with Part C as they are; the addendum (A2) records what the tuning showed.
* **The tuning does not favour the main row by its scenarios.** The score is the mean over uniform, hotspot, chipperm,
  chiptrans and uniform with one faulty VL per chiplet, the scenarios of round 24, where the main row's parameters were
  tuned by the same score on the same seeds. A score over hotspot alone, the traffic under which the early rows do best,
  would choose smaller values for `EB_route` (0.5 on 2x2, 0.125 on 4x4), but it would not change the picture: the hotspot
  score of every chosen value is within 0.06 of the best hotspot score of the grid (the largest gaps are those of
  `EB_route`, 0.054 on 2x2 and 0.052 on 4x4).
* **`chain_v27.sh c` is replaced by `chain_v27c.sh`**, which applies the time rule of the addendum (A3). The sentence of
  `runtime_estimate.md` about the machine was changed in `experiments_v27_eval.timing` before the timing runs, and the
  timing step was run once on stubbed runs in a scratch folder to check its text and its three outcomes (nothing dropped,
  Part E dropped, four items dropped). No run of Parts C and E existed at that time.

## The timing runs (16 Nov, 09:19 to 09:56)
* **The PC was free during the timing runs.** Sampled on the Windows side over six seconds: its processes together used
  0.03 hardware threads at the start (09:19) and 0.10 at the end (09:57); the application of the morning was not running
  and no process with more than 20 s of processor time had started in between. So the estimate of `runtime_estimate.md`
  is that of a free machine: 13.6 h for Part C and 2.6 h for Part E, 16.2 h together.
* **Nothing is dropped** (`drops.json`), so the addition to the time rule (addendum A3, point 2) has nothing to decide;
  `restore_v27.py` runs in the chain and reports that. If the machine is shared again later, the runs take longer than
  estimated; the rule decided at the timing runs and is not applied a second time, so nothing is dropped then either.

## After Part C (16 Nov, 23:45)
* **Part C ran as designed:** 11,340 of 11,340 runs, none missing, no dead-end event, no hop of an `EB` row with more than
  one output; 13.8 h of machine time after the timing runs (estimate 13.6 h with them). The PC stayed free.
* **Two descriptive tables were added that are not in the pre-registration** (`extra_v27.py`, `report/extra_C.md`): the
  counters of C.8 at 0.2, 0.5 and 0.8 x Lsat next to 1.0 x Lsat, with the delivered share of the offered load, and the
  share of the main row's gain per scenario. Reason for the first: C.8 gives the counters at 1.0 x Lsat of DeFT-P, as
  pre-registered, and there three of the early rows are past their own saturation (`EB_vl` and `EB_vl64` deliver 82 to
  93 % of the offered load, `EB_down` 82 and 87 % on 4x4 and 3x3), so the age of their choice at that load is partly a result of losing and not only a reason for it. The table at
  the lower loads shows the age where no row is saturated. Reason for the second: the mean over the six scenarios hides
  that the shares are 77 to 100 % under hotspot traffic and negative elsewhere. Neither table has a test, and neither
  changes a pre-registered number.
* **The latency at 1.0 x Lsat stays the pre-registered metric**, although for a saturated row it measures the saturation
  and not the routing. `FINDINGS.md` says so where it quotes those numbers and gives THR and the latencies below
  saturation next to them. The primary family is not changed: THR alone already gives nine supported tests of nine.
* **Fifteen secondary numbers were computed a second time** by code that shares nothing with the report (shares, effects
  per scenario, latencies at other loads, the row against row effects that `FINDINGS.md` leans on): all agree to the
  printed decimal. The primary family is checked by `check_v27_family.py` as pre-registered.
* **The report was run while Part E was still running.** Nothing had been dropped by the time rule, so no decision of the
  addendum (A3) was open, and Part E has no test.

## After Part E (17 Nov, 02:15)
* **Part E ran as designed:** 2,304 of 2,304 runs, none missing, no dead-end event, no hop of an `EB` row with more than
  one output; 2.5 h of machine time after the timing runs. Parts C and E together took 16.9 h from the start of the timing
  runs (estimate 16.2 h); the time rule dropped nothing.
* **The headline is stated with its limit.** Part C says that the gain needs late binding (18 of 18 tests). Part E says
  that with a quarter of the VLs faulty the early rows are ahead of DeFT_P and `EB_route` comes within about 1 % of the
  main row's throughput on 3x3 and 4x4. The second weakens the first as a general claim, and it is the result that does
  not favour our method, so it is in the first paragraph of `FINDINGS.md`, in the answer to question 13 and in the
  README, next to the first. `FINDINGS.md` also says that the two rest on evidence of different weight (a pre-registered
  family on ten seeds; a descriptive result on two seeds).
* **A table of Part E by traffic pattern was added** (`extra_v27.py`, `report/extra_E.md`; not pre-registered, no test).
  `summary_E.md` gives the effects against DeFT_P and against the best DeFT variant for the two patterns together, as
  pre-registered, and the pre-registered split by pattern only against the main row. Half of the design is hotspot
  traffic, under which the early rows are near the main row with and without faults; without the split against DeFT_P
  one cannot see that the change under faults is under uniform traffic and concerns `EB_route`. The table puts the same
  two patterns without faults (Part C) next to it, with the caveat that the two designs differ in seeds and loads.
* **The explanation of Part E is given as a reading.** That the imbalance under faults is fixed by the mask and visible
  on the routes, and that fewer candidates leave less to bind late, fits the numbers (the split by traffic, the split by
  masks with and without a chiplet of one functional VL, the smaller gain of the main row itself). No run tests it.
* **Sixteen numbers of Part E were computed a second time** by code that shares nothing with the reports (effects with
  their intervals, shares, the uniform-only effects, the two groups of masks, a count of masks): all agree.
* **Not done, and why:** `EB_vl64` under faults would say what `EB_route`'s result is worth with information of a
  realistic age. It is not in the pre-registered design of Part E, and adding a row after seeing the results would be a
  new experiment, so it is named as a limit and as the obvious next run.
