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
