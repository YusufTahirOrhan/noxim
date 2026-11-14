# Decisions v26

Choices the prompt left open. Where there was a choice, the option that does not favour our methods was taken.

## A0: regression
* **Reference.** The ee0e247 build, exported with `git archive` and built in a separate tree (`build_ref.sh ee0e247`). The three
  comparisons of round 25 are kept: the build of the previous reference (ce6ab6a), `bin/noxim` with the options absent, and
  `bin/noxim` with every option given explicitly off. No simulator source changed between ce6ab6a and ee0e247, and the three
  binaries have the same md5.

## Masks
* **Three random streams.** The prompt gives `random.Random(2611)` for the masks of Part B and for set 3 of A2. Each of them, and
  the masks of the second-half test, has an instance of its own with that seed, so that each list can be drawn again without the
  others.
* **Order of the draw.** Part B: sizes 2x2, 3x3, 4x4, and within a size the rates 1/16, 2/16, 4/16, 8/16; a candidate is
  `rnd.sample(range(#VLs), n)`, rejected if a chiplet has no functional VL or if the mask was drawn before. The order in
  `masks_v26.json` is the order of the draw; "mask 1" of a cell (A3) and "masks 13 to 16" (the time rule) refer to it.
* **2x2 at 1/16.** There are exactly 16 masks with one faulty VL; all are taken, in VL order, without a draw.
* **Spelling of a mask.** One hex digit per chiplet with leading zeros (as the masks of round 11), so a mask names its LUT file and
  its runs without ambiguity. The fault-free mask keeps the spelling of the earlier rounds (0x0000, 0x0, 0x0).
* **Set 3 of A2** is drawn as the prompt says (every chiplet one of its 15 patterns, uniformly), 3x3 first; a mask drawn twice
  would have been drawn again (it did not happen). No mask of set 3 is in set 2.

## Part A
* **Check 4 stops the round like the other three.** The prompt lists it among the checks per mask and relation, and "a
  model-check failure" stops the round. A CDG edge outside the fault-free CDG would not be a deadlock, but it would refute the
  argument the coverage of 3x3 and 4x4 rests on.
* **A control for check 4.** The negative control of `xy_check.py` shows that check 1 can fail. Check 4 is new, so a control
  was added for it: the fault-free CDG of `CI_XY_O1` against that of `CI_XY_XY` must not be a subset.
* **The second-half test** uses 1,000 masks with faults in at least two chiplets (with faults in one chiplet only, the mask and
  its restriction to that chiplet are the same mask), both relations, all four chiplets. It is a test of the argument, not one
  of the four checks: if it fails, the round goes on and set 2 is reported as a sample.
* **Time rule of A2.** The estimate uses 24 checks spread evenly over the list instead of the first 24. The first 24 would all
  be masks with at most one faulty chiplet, which have the most states and take the longest; the estimate would be too high and
  could reduce set 3 without need.
* **A3, errors of the comparison code.** A mismatch stops the round and neither the model nor the simulator is changed. An
  error in the code written for the comparison itself (the dump in the instrumented copy, or the replay) is not a mismatch of
  the two: it is corrected, recorded here, and the comparison is run again in full. Said to the user before the round started.
* **A3, what counts as a hop.** Only hops for which the model has a transition count towards the 1,000,000 per row and size.
  The arrival at the destination router (the model has no transition there) is compared as well and counted separately.
* **A3, the seeds that ran.** Seed 1 on the six masks of every size. With seed 1, 2x2 had 503,018 to 514,811 hops per row,
  so seed 2 was added on its six masks (1.02 to 1.04 million); 4x4 had 1.53 to 1.55 million and got no further seed. On 3x3
  seed 2 ran on the fault-free and the same-VL mask at a time when only these two masks could run (the masks of Part B need
  their ladders) and the size was below 1,000,000 hops. Once the four masks of Part B had run, seed 1 alone had 1.03 to 1.05
  million on 3x3, so those four runs per row were not needed by the rule. They are kept and reported: they are more
  comparisons, with no mismatch, and leaving them out would change no conclusion.
* **A3, wording of the report.** The four phase counts of `conformance.md` and `conformance.csv` include the arrivals (they
  add up to hops plus arrivals). The first version called them "hops by phase"; the line and the four column names now say
  records. No number changed.

## Order of the runs
* **Two unattended chains share the machine** (6 cores, 12 threads): `chain_v26_formal.sh` (Part A) and `chain_v26_b.sh`
  (Part B). The prompt's order is A1, A2, B2, ladders, timing, B3. The drain tests and the ladders are started while A1 and A2
  still run, so that the machine is never idle; they do not depend on the model check. What the order protects is kept: **no
  evaluation run of a frozen row on a mask before that mask has passed the model check and its drain tests.** For this, set 4
  of A2 (the masks of Part B) is checked first on 3x3 and 4x4, before sets 1 to 3; the timing runs and the evaluation wait
  for A1 (all 2x2 masks), for set 4 and for the drain tests. The ladders run DeFT_P only.
* **A failed model check stops both chains**: the formal chain ends with a non-zero code and the chain of Part B checks that
  code before every stage.
* **The time rule of A2 with set 4 already done.** The 24 checks of the sample are spread over the whole list as
  pre-registered; those of set 4 are then read from the finished checks, with the time they took.
* **A3 and the timing runs.** The conformance runs on the masks of Part B need the ladders (their load is 1.0 x Lsat of the
  mask). They are started after the timing runs have finished, not during them: the timing runs must have the machine to
  themselves, or the estimate would come out too high and the 40 h rule could drop cells without need. While A3 runs, the
  evaluation leaves it two of the twelve threads. The fault-free and the same-VL mask use the ladders of round 25 and were run
  earlier, next to the model checks.
* **The machine went down during the timing runs.** At 09:42 on 14 November, 18 minutes into the timing runs, the machine
  stopped without a shutdown (Windows events 41 and 6008: power lost or a hard stop; no crash dump, no hardware-error
  event) and stayed off until 14:46. Everything finished before that was on disk and committed (the ladders at 09:25). What
  was done before the restart:
  * *The timing runs were run again in full.* 606 of the 1,152 had finished. The timing stage measures the wall time of
    one call and skips finished runs, so a restart would have timed only the other 546 and estimated about half of the true
    time; the 40 h rule would then have been applied to a wrong number. The 606 outputs were deleted (the runs are
    deterministic, so the second time gives the same files).
  * *The inputs were checked.* The stage that writes traffic tables writes only those that are missing, so a table damaged
    by the power loss would have been used silently: the 234 tables of the design were generated again and are
    byte-identical. `bin/noxim` has the md5 of the reference builds; the 192 LUTs, the scripts and the files of the round
    have no empty file and no NUL byte; the repository is intact.
  * The chain was started again with the same command (finished stages are skipped).
* **Number of processes.** The model checks of 3x3 and 4x4 use 6 processes (7 GB of memory). The stages of Part B run in
  segments and take the rest of the machine from a small file the chains write (`experiments_v26.width`). The number of
  processes changes nothing in a run: every run is fully determined by its arguments.

## Part B
* **Drain tests of all six rows.** The prompt asks for the two frozen rows. B5 reports the delivered share of DeFT as well, and
  round 25 drained every row of its sweep, so the four reference rows are drained on every mask too. This cost far more than I
  had told the user before the start (half an hour) and more than the estimate first written here (20 CPU-hours). Measured:
  about 68 process-hours and 8.1 hours of the machine (13:29 to 21:35; the first 3.6 h next to the model checks with 2 and
  then 6 processes, the last 4.4 h with 12). A 4x4 test sends 65,280 packets and takes 8 to 13 minutes of one of twelve
  processes, longer the more VLs are faulty. It was kept because it is pre-registered.
* **Timing runs.** Seed 151, the 1st and 4th load, masks 1 to 4 of every (size, rate), every row and both traffic patterns:
  1,152 runs of the design with the mix of the whole design. The lowest and the highest load are taken so that their mean
  (1.25 x Lsat) is close to the mean of the four loads (1.225 x Lsat).
* **Ladders.** The D1 rule exactly as Part C of round 25 ran it, including the full sweep of the 0.0001 grid from 0.0001 where
  the coarse Lsat is at most 0.004. Ladders with Lsat below 0.001 are listed, because L0 is measured at 0.0002.
* **Best reference.** Chosen per (mask, traffic, metric) from the mean of two seeds among four rows, as the prompt defines it.
  This favours the reference; it is kept.
* **B5.** The masks of the rates 1/16, 2/16 and 4/16 are drawn exactly as `reach_v10.py` draws them, so that its numbers must
  come again (a check of the script); the masks of 8/16 come from a stream of their own, so that adding the rate does not change
  the others.

## Report
* **Descriptors for question 6, fixed before the evaluation.** "What do these patterns have in common" needs properties of a
  mask to look at. They were chosen and the script (`extra_v26.py`) was committed while the drain tests were still running,
  before any ladder or evaluation run existed, so they cannot have been picked to fit the result: the share of faulty VLs;
  the number of chiplets with one functional VL; the largest number of faults in one chiplet; of the three chiplets that hold
  a hotspot router (0, 1 and CX), those with one functional VL; Lsat of DeFT_P on the mask relative to the fault-free Lsat of
  round 25. The script was tested on synthetic data only. Its tables are descriptive.
* **A smoke test of the report scripts on real outputs, without reading a result.** While the evaluation ran, the outputs
  finished so far were converted into a scratch folder, and `report_v26.py`, `check_v26_family.py` and `extra_v26.py` were
  run on it, to find a crash before the end of a 21-hour run and not after it. Shown were only exit codes, error output,
  the names and lengths of the files written, and on how many tests the two computations of the primary family differ. No
  effect, no p value and no verdict was printed or read, and the scratch folder was deleted. Result: the three scripts run
  on the real format; on the six tests whose masks were complete, the two computations give the same effect, interval, p
  and number of masks. No script was changed. Before it, every line of the converted CSV was checked to be a run of the
  design (the keys the report looks up), again without reading a value.
