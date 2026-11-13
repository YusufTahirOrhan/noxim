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

## Part B
* **Drain tests of all six rows.** The prompt asks for the two frozen rows. B5 reports the delivered share of DeFT as well, and
  round 25 drained every row of its sweep, so the four reference rows are drained on every mask too.
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
