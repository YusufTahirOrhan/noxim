# Decisions v28

The standing rule of the round: never stop to ask; take the option that does not favour our methods and record it here. In this round
that means: when in doubt, favour the early rows.

## Part A

### A0: the reference
* The reference of the regression is a fresh build of b164e9e (the last commit of round 27, `build_ref.sh b164e9e`,
  `~/lbbin/noxim_b164e9e`). It has the md5 of `bin/noxim` (9c32b6ee...): the binary of round 27 is the build of its sources. The
  d641861 build (the reference of round 27) is compared as well.
* `regression_before.md` says that the sources differed from b164e9e when it was written: the A1 changes were being written in the
  working tree while A0 ran. The binary under test in A0 was the b164e9e build itself (md5 in the file), so A0 is the regression before
  the change.
* The first start of the A1 regression (03:26) gave every new option explicitly off except `tie_stream 0`, which I had left out of the
  list. It was stopped at 100 of 336 runs (03:33) and started again with `tie_stream 0` in the list; the partial outputs were deleted.

### A1: the options
* `oracle_bias D`, `oracle_pending 0|1` and the sampling of `oracle_scope route` and of the pending counters by `oracle_period P` are
  implemented as the prompt defines them (`DeftLateBinding.h`, "v28"). Details that the prompt leaves open:
  * The bias is added to the cost of an entry candidate that is not `defaultVl(false, src, dst)` (the LUT's `entries_by_destination`
    entry of the destination router, which is the entry VL DeFT_P uses with `-deft_lut_entry dst`). The early rows of round 27 do not
    pass `-deft_lut_entry dst`; it changes nothing for them, because the oracle chooses the entry VL itself and the exit VL is the
    LUT's `source_exit` in both cases (the anchor gate shows it).
  * The pending counter of a VL is a signed integer of flits. It grows in `prepareHeadPacket`, right after the injection-time choice,
    by `p.size`, and shrinks in `onHeadForward` when a head is forwarded Up at an interposer router, by the head's
    `sequence_length` (the same number). Every inter-chiplet packet of an oracle row is bound at injection, so every Up move is one of a
    counted packet. The counters do not depend on the measured window.
  * With `oracle_period P` the snapshot holds, for every router, the flits of every input port summed over the VCs
    (`portFlits`, which `occRoute` reads) and the pending counters, both taken in `oracleTick` at the cycle that is a multiple of P,
    where the occupancies of `oracle_scope vl` are taken (before any router changes state in that cycle). `occRoute` reads the
    snapshot. Before the first sample everything reads 0, as in round 27.
  * `oracle_period` with `oracle_scope route` was refused by round 27's validation; that check is removed. Nothing else of the
    validation changes. New checks: `oracle_bias > 0` and `oracle_pending 1` need `entry oracle`; `oracle_bias > 0` needs the LUT's
    `entries_by_destination` (as `lut_bias` and `entry_stats` do).
* **Two diagnostic options**, off by default, used in the gates only and in no row:
  * `pending_check K`: at the first three cycles that are multiples of K, the sum of the pending counters (and each counter) is
    compared with a scan of the network that does not use the counters (every head of an inter-chiplet packet that has not moved Up,
    in an input buffer of a router of its source chiplet or of the interposer, or on the link into such a router and not yet taken,
    counted with its packet length for the one candidate of its entry mask). The scan runs in the first process of the cycle
    (`Router::txProcess`, `Router::rxProcess` and the injection call it first), so it sees the state at the end of the previous cycle.
    It reads only (unit check 2). K = 3000, so the checks are at cycles 3000, 6000 and 9000 of the 10,000-cycle runs.
  * `tie_stream 1`: the tie-break of the injection-time choice (`chooseMasks`) and of the commit at the Down move (`commitEntry`)
    draw from a stream of their own (a `std::mt19937` seeded once from the run seed) instead of `rand()`. Without it (the default)
    the code is that of round 27. The reason for it is the next point.

### The anchors and the random stream (found while writing A1, confirmed by a smoke run before the gate)
* The crossbar arbitration of every router draws from `rand()` (`Router.cpp`: `rand() % reservations.size()` for every input port
  with a reservation, every cycle). The injection-time choice draws once from the same stream for every inter-chiplet packet
  (`ties[rand() % ties.size()]`, also when there is one tie), and the commit at the Down move once per commit (`pickMin`). So a row
  that takes DeFT-P's entry VL for every packet but draws once more per packet shifts every later draw of the arbitration, and its
  runs are not byte-identical to DeFT_P's although its routes are. DeFT_P draws only in the arbitration. This is why round 27's
  anchor (`exit lut`, `entry lut`: no cost loop, no draw) was identical and why the two anchors of this round are not expected to be.
* A smoke run on 2x2 (uniform, 1.0 x Lsat, seed 101; not a gate, `~/lbraw/v28/smoke`, deleted) showed exactly that: EBf(route, 1, 1,
  1e9) and `EB_down` with `lut_bias 1e9` take DeFT-P's entry VL for every packet and are not identical to DeFT_P; with `tie_stream 1`
  both are identical to DeFT_P.
* **What follows from it.** The gate is run as the prompt defines it (the rows as they draw), and again with `tie_stream 1`. If a
  row is not identical as defined but is identical with its own tie stream and takes DeFT-P's entry VL for every packet, then the
  family contains DeFT_P's routing and timing exactly and differs from DeFT_P by the sequence of the arbitration draws only. The
  prompt says what to do when an anchor is not identical: say why, and compare the tuned rows with that anchor row as well as with
  DeFT_P. So the anchor rows join the evaluation:
  * `EB_inf` = EBf(S, P, B, infinity) with the S, P and B of `EB_best` (`oracle_bias 1e9`), and `EB_down_inf` = `EB_down` with
    `lut_bias 1e9`. The gate also runs EBf(vl, 0, 0.5, infinity) with `oracle_period 64` against EBf(route, 1, 1, infinity): at
    T = infinity every choice is DeFT-P's entry VL and every injection draws once whatever the cost reads, so the results should be
    the same for every S, P, B and period, and one anchor row (`EB_inf`) stands for the T = infinity member of `EB_best` and of
    `EB_best64`.
  * They join Part C (1,620 runs each) and Part D (both rates, 768 runs per row and rate). Each tuned row is reported against its
    anchor next to DeFT_P (`EB_best` and `EB_best64` against `EB_inf`, `EB_down_t` against `EB_down_inf`).
  * The time rule of the prompt does not know them. They are put first in the drop order, in Part D only: **the anchor rows of
    Part D, then `EB_best64` in Part D**, then the prompt's order. They are a control of the comparison with DeFT_P, which the primary
    families do not use; in Part C they are never dropped.
  * Not done instead: drawing the tie-breaks of the new rows from their own stream (or only when there is more than one tie). That
    would make the anchors identical but would change the rows of round 27 (the P = 0, T = 0 members of the family, taken from round
    27's runs) and the reproduction gate would fail.

### A2: the gates
* **v27 reproduced** (`repro_v27.md`): the two rows the prompt names, `EB_vl_b1` and `EB_route_b4`, with the v28 arguments
  (`oracle_scope`, `oracle_pending 0` and `oracle_bias 0` given explicitly), on all 80 tuning runs each. **Added:** DeFT_P and the main
  row on the same 80 tuning runs each. Their runs of round 27 are the denominator of every tuning score of this round and the main
  row's score (the prompt says to take them from round 27's file), so they are checked as well (160 more runs).
* **Unit checks** (`unit_checks.md`): the pending check on all three sizes (the prompt names 4x4; 2x2 and 3x3 cost little) and for
  four rows: EBf(route, 1, 1, 4), EBf(vl, 1, 1, 4) and the same two with `oracle_period 64` (the prompt's drain rows). Also a
  description, not a gate: EBf(route, P, 1, T) for growing T on 4x4 (uniform and hotspot, 1.0 x Lsat), with the share of packets off
  DeFT-P's entry VL.
* **The reuse check of Parts D and E** (`reuse_check.md`) runs with the gates (chain a), before the pre-registration. It runs DeFT_P
  and the main row of round 26 again and compares them with round 26's file; it is not a run of the designs of this round. It covers
  masks 1 and 2 of all four rates (round 27: rate 4/16 only), since Part E uses the main row at every rate.
* **Drain tests** (`drain_v28.csv`): a test fails if a packet is not delivered, if there is a dead-end event, if a hop of the row
  offers more than one output, or if a pending counter is not 0 at the end (rows with `oracle_pending 1`).

### The pre-registration and the reuse check
* `PREREGISTRATION.md` was committed when the anchors, the reproduction, the unit checks and the drain tests had passed, while the reuse
  check (768 runs, about an hour) was still running; it gates Parts D and E only, and `chain_v28c.sh` refuses to start without it.
  The tuning (chain b) started at the same time and shared the machine with it until it ended. Nothing of the tuning depends on it.
* `unit_checks.md` check 4 (single runs, a description) was read after `stated_in_advance.md` had been committed and before the
  pre-registration; it suggests that the count of the bound packets buys more than I expected. The expectations were not changed; the
  pre-registration says that I saw the check.

## Part B
* **B3 shares the batches of B1.** B3 (`lut_bias` of `EB_down`) does not depend on B1, so its grid and its extension steps run in the
  same batches as B1's (the machine stays full). B2 starts when B1 and B3 are complete. The prompt's order "B1 -> B2, B3" is kept for
  B2.
* **Extensions** (the prompt: "per sub-family (S, P): if its best configuration has T = 16, add T = 32, 64, 128 one at a time (all four
  B) until the best T is no longer the largest. If its best B is 0.5 or 4, add B / 2 or 2 B (all T) once"), made precise:
  * per size and sub-family; the best configuration is the one with the largest score, of two equal scores the larger T;
  * a new T is run for every B of the sub-family at that moment (a B added by the B extension included); a new B for every T of the
    sub-family at that moment (a T added in the same step included), so a sub-family is always a full grid B x T;
  * the B extension is made at most once per sub-family, when the best B is 0.5 or 4 at a step; T is doubled up to 128;
  * B2: T doubled from 32 up to 128 while the best T is the largest; B3: D = 32 if the best D is 16, then D = 64 if the best D is 32;
  * of two equal scores the larger T (B2) or the larger D (B3) is taken, as for `EB_best` (the conservative choice: the row closer to
    DeFT_P).
* A configuration with P = 0 and T = 0 that an extension adds (B = 0.25 or 8) is taken from round 27's runs as well (round 27 ran every
  B in {0.125, ..., 8}).
* The scores read DeFT_P, the main row and the P = 0, T = 0 members from `results_v27_early/tune_runs.csv` and the runs of this round
  from the raw folder (later from `tune_runs.csv`, which has only the runs of this round).
* **How it ran.** 8,800 runs from 04:59 to 17:25 on 17 Nov (12.4 h), the first two hours next to the reuse check. Step 0: the B1 grid and the
  B3 grid (6,240 runs); step 1: T = 32 and B = 0.25 / 8 where the rule asked (1,840 runs); step 2: T = 64 for (route, 0) on 4x4 (200 runs);
  step 3: B2 (480 runs); B2's T = 64 on 2x2 (40 runs). The drain tests of the tuned rows then passed (54 / 54), and the addendum was committed
  before chain c started.

## Parts C, D and E
* **The machine at the timing runs** (17 Nov, from 17:41): nothing else of this round ran; on the Windows side only the Claude
  processes and the usual services were running, with no measurable CPU use in a 5 s sample taken just before the start.
* **Part D, rows and runs**: `EB_best` and `EB_down_t` at 1/16 and 4/16, `EB_best64` at 4/16, and the anchor rows if they join
  (above). The runs of the other rows (DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran, the main row) are those of round 26.
* **The time rule.** The estimate is taken as measured, with whatever else runs on the PC at the time of the timing runs (round 27,
  addendum A3). Timing runs: Part C the seed-171 runs at the 2nd, 5th and 9th load of every cell; Part D and Part E the seed-151 runs at
  the 1st and 4th load of masks 1 to 4 of every size and rate. They are runs of the designs and are kept. What is dropped is taken back
  if it fits later, in the reverse of the drop order (`restore_v28.py`), as in round 27.
* **Paused on the user's request** on 17 Nov 2026 at 19:28 (chain c stopped: tmux session ended, every simulator process ended, the
  disk flushed). At that moment 2,407 of the 11,340 runs of Part C were finished (the 378 timing runs included) and the timing runs of Parts
  D and E (432 and 192) were done; no output file was unreadable; the 12 runs in flight are run again when the chain resumes (the runner
  skips only finished runs). Nothing was dropped by the 30 h rule, so the pause changes no decision of the time rule; on resuming, the
  seconds of the pause are added to `~/lbraw/v28/c_start.txt` as the chain's header says, and the pause is recorded here with its length.
  **Resumed** on 18 Nov 2026 at 07:58 after 44,914 s (12.5 h); `c_start.txt` holds that number as its second entry.
* **v28 has its own `run_seg`**: round 27 called `experiments_v26_eval.run_seg`, which reads round 26's width file
  (`~/lbraw/v26/width.txt`, deleted), so a change of round 27's width file took effect only at the next stage. This round's stages
  read `~/lbraw/v28/width.txt` at every segment of 384 runs.
* **How Parts C and D ran.** Part C: 11,340 runs, 13.6 h of running time (17 Nov 17:41 to 18 Nov 20:27 with the pause of 12.5 h), the estimate was
  13.4 h. Part D: 6,912 runs from 18 Nov 20:27 to 19 Nov 03:48 (7.4 h). No run missing, no dead-end event, no hop of an early row with more than
  one output; `restore_v28.py` had nothing to take back because nothing was dropped.
* **The report was run part by part** (`report_v28.py c` after Part C, `d` after Part D), each with the code as committed before the runs of
  that part ended; `check_v28_family.py` after each. The Part D report was run once before on the finished 2x2 and 3x3 runs in a scratch
  folder (`~/lbraw/v28/dry_res`, deleted) to see that the code runs on real data; no number of that run is used, and nothing was changed
  after it.
* **Extra comparisons for Part D, added after its results were seen** (`extra_v28.py`, `report/extra_D.md`; descriptive, no test, outside
  the pre-registration, and marked so wherever they are used):
  * the fault-free runs of Part C restricted to the two traffic patterns of the fault design (uniform, hotspot), with THR over the nine
    loads and over the four loads of the fault design. Reason: Part C's shares are over six scenarios and Part D's over two, so "is the
    share larger under faults" cannot be read off the two reports;
  * round 27's early rows (`EB_vl`, `EB_route`, `EB_down`; `results_v27_early/fault_runs.csv`) against this round's rows on the same 48 masks
    of rate 4/16 (same traffic, loads and seeds). Reason: `EB_route` is a member of this round's family ((route, P = 0, T = 0) with round
    27's `oracle_beta`), and round 27 measured it within 0.5 % of the main row's throughput on 4x4. If a member of the family that the tuning
    did not choose is the stronger early binder under faults, that favours the early side and has to be said (the conservative rule);
  * `EB_best64` against `EB_best` without faults on the same two traffic patterns.
  The pre-registered tables, tests and verdicts are unchanged; `report_v28.py` was not edited.
