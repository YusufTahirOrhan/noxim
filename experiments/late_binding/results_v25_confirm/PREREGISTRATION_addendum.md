# Pre-registration addendum v25: the main row with one residual cycle

Committed before any run of the row defined here. At the time of this commit Part B is running (about 8,100 of its 18,900 runs
are done) and **none of its results has been read**: only the number of finished runs has been looked at. Parts C, D and E have
not produced an evaluation run. The hardware results this addendum rests on are in `hw/timing_runs.csv` and `hw/n_fast.json`.

## Why this row
`PREREGISTRATION.md` says: Part F decides which timing mechanism can be built, and if that mechanism is not one of the
evaluated rows (LF with residual 0, DLY with 2 cycles), the row is defined here before it is run.

Part F built the interposer router of the main row (`hw/rtl/`) and timed it (NanGate45, Yosys + ABC, OpenSTA, pre-layout):

* **At the clock period of the reference pipeline** (T_ref = the longest stage of DeFT's interposer router in the same run,
  1.27-1.32 ns: its switch allocation), the decision of mechanism LF takes **L_dec = 2 cycles** (one register in the decision
  unit, after the stage that reads the occupancies; worst margin +0.23 ns, the spread of the flow being 0.13 ns). The two
  cycles are the cycle the head is on the link and its route cycle; the VC allocation finds the stored decision. A head with a
  choice takes the 4 cycles of the reference pipeline, measured in RTL simulation. **The evaluated main row, `CI_heurLA_X_LF`
  (residual 0), is the mechanism that is built.**
* **Two conditions under which the same RTL has one residual cycle:**
  1. *The link cycle.* The first stage of the decision reads the head on the link. In this pre-layout flow a link has no
     delay. With the decision, 0.28-0.42 ns of the link cycle are left for the wire (0.82-0.90 ns in DeFT's router, whose only
     work in that cycle is the buffer write). Where the wire needs more, the decision has to start from a register, one cycle
     later.
  2. *A 1 ns clock.* No router of this flow meets 1 ns (the allocation stages need 1.2-1.3 ns). At that target the decision
     needs L_dec = 3 cycles (and only marginally: +0.07 ns).
  The window W = pipe_all + 1 = 3 of the pre-registration counts the cycle in which the upstream router forwards the head.
  The RTL has no sideband request from the upstream router, so that cycle cannot be used: the decision has two cycles, the
  link cycle and the route cycle. In both cases above a head with a choice waits one cycle (5 cycles through the router in RTL
  simulation with L_dec = 3).
* That mechanism, LF with the heuristic and **residual 1**, is not one of the evaluated rows. It is run so that the result of
  the round does not rest on the two conditions.

## Row
`CI_heurLA_X_LF1`: `CI_heurLA_X_LF` argument for argument, with `-deft_lb decision_delay 1` in place of `decision_delay 0`
(`experiments_v25_add.py args` prints both lists; they differ in that value only). In the simulator a head with more than one
offered output waits one more cycle after the pipeline wait before it uses its stored decision or the fallback; a head with
one offered output does not wait. This is what the RTL does with L_dec = 3.

## Gate
Drain tests of the row by the A4 protocol (v10 protocol and masks with the v23 LUT of each mask on the three sizes, and the
over-saturated 4x4 runs at 2.4 x Lsat on localized and movinghot), at pipe_all 2: `drain_summary_addendum.csv`. A FAIL stops
the round.

## Design
The Part B design, unchanged: the eight scenarios, three sizes, nine loads, seeds 121-130: 2,160 runs, run in full. The same
binary (the ce6ab6a build), ladders, traffic tables and options as Part B. It runs after Parts C, D and E (the machine is full
until then). Output: `addendum_runs.csv`.

## Tests (a family of its own)
On each size the row has higher THR, lower LAT and lower P99 than the best baseline: the three tests per size of the primary
family, with the metrics, the best baseline (from the reference rows of Part B), the effect and the t test over the ten seeds
exactly as `PREREGISTRATION.md` defines them for the main row. **Nine tests, Holm over the nine, alpha = 0.05.** They are
reported next to the primary family and are not merged with it.

## Descriptive (unadjusted, never called significant)
* The row against `CI_heurLA_X_LF`, per size and per scenario: what the residual cycle costs in THR, LAT, P99 and in LAT at
  0.2 and 0.5 x Lsat. The row against `CI_heurLA_X_DLY`.
* LAT at 0.2 and 0.5 x Lsat against DeFT_P.
* Its lookahead counters (stored decisions used, fallback rate).

## Stated in advance
Round 24 measured one residual cycle on the Q-learning rows (LF with residual 1 against the ideal decision: LAT at 0.2 x Lsat
+3.9 / +3.1 / +2.7 %, at 1.0 x Lsat +3.1 / +2.8 / +1.9 % on 2x2 / 3x3 / 4x4, THR unchanged by the cycle itself) and found
that "the residual cycle costs what one cycle costs". Expected here: the row is 2-4 % slower than the main row at low load
and 2-3 % at 1.0 x Lsat, with THR within 1 %. If the main row's latency gain over the best baseline is as in round 24
(-21 / -19 / -24 %), the row keeps most of it; the 2x2 tests are the ones at risk.

## Not run
The second row with a residual cycle (`CI_heurLA_O_LF` with decision_delay 1). Its hardware has the same timing result
(L_dec = 2 at T_ref with +0.18 ns, 3 at 1 ns), the conclusion of the round is drawn for the main row, and the cost of the
cycle is read from the main row.
