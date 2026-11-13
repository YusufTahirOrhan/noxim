# Findings v26: fault coverage

Status: **in progress.** Done: the regression (A0), the masks and the pre-registration, the exhaustive model check on 2x2
(A1), the reachability of MTR and RC (B5), and the first third of the conformance runs (A3: the fault-free and the same-VL
mask). Running, unattended: the model check on 3x3 and 4x4 (A2), the drain tests on the 192 masks (B2), then the ladders, the
timing runs and the 18,432 evaluation runs (B3). Every answer below says whether it is final.

Nothing is tuned and no row is changed: the configuration is the frozen one of round 25, the simulator is the ee0e247 build
(the sources of ce6ab6a), and the analysis is fixed in `PREREGISTRATION.md`, committed with `masks_v26.json` before any run of
Parts A and B.

## Gates
* **Regression** (`regression.md`): the 84-configuration set is byte-identical to a fresh build of ee0e247 in all three
  comparisons (the ce6ab6a build, `bin/noxim` with the options absent, `bin/noxim` with every option given explicitly off).
  The three binaries have the same md5. No simulator source changed in this round.
* **Controls of the model check** (`formal_controls.md`): with R3 and the F1 source rule removed the CDG is cyclic (the fixed
  pair and both relations of this round), and the subset check fails when the CDG of `CI_XY_O1` is tested against that of
  `CI_XY_XY` (184 edges outside). The checks can fail.
* **Controls of the conformance comparison** (`conformance_controls.md`): the hops of 2x2 runs replayed through four models
  that are deliberately not the one of the run (the other interposer order, the Up rule of rounds 1-22, the entry fixed at
  injection, another fault mask) give 9,770 to 54,171 mismatches out of 95,596 to 119,541 records; replayed through the right
  model they give none.

## The ten questions

### 1. A1: how many masks and checks, do all pass, does the subset check hold for every mask? The largest hop count
**Final. All 50,625 masks, 101,250 checks, every check passes on every mask; the subset check holds for every mask; the
longest path is 24 hops** (`formal_all_2x2.md`, `formal_all_2x2.csv`).
* The masks are all 15^4 fault patterns of 2x2 that leave every chiplet a functional VL, the fault-free one included, with
  0 to 12 faulty VLs. Both relations of the round were checked on each: `CI_XY_XY` (the main row) and `CI_XY_O1` (the second
  row), with the model and the settings of `formal/xy_check.py`.
* On all 101,250 lines: the CDG is acyclic, no reachable state is a dead end, the state graph is acyclic, and no CDG edge
  lies outside the fault-free CDG of the same relation.
* The fault-free CDG has 800 nodes and 1,424 edges for both relations (the number of the independent sampled run named in the
  prompt). The CDG shrinks as VLs fail: 1,356-1,362 edges with one faulty VL, 660-728 with twelve.
* The longest path is 24 hops for the fault-free mask and never longer: 16 to 24 hops over all masks.
* Round 24 had checked 897 of these masks. The 2x2 result no longer rests on a sample.
* Cost: 66,533 CPU-seconds, 0.66 s per check on the loaded machine (the prompt expected 0.3-0.5 s on a free one).

### 2. A2: the four sets on 3x3 and 4x4; does the argument for set 2 hold in the data?
*Pending (A2 is running).*

### 3. A3: how many hops compared per row and size, how many mismatches?
*Interim: 3,583,610 hops and 293,754 arrivals compared in 36 runs (the fault-free and the same-VL mask, three rows, three
sizes), 0 mismatches, every statistics file byte-identical to `bin/noxim` (`conformance.md`). The four masks of Part B per
size and the further seeds follow.*

### 4. Primary family of Part B: how many of 24 supported, which against?
*Pending.*

### 5. The trend over the fault rate, per size and per traffic pattern
*Pending.*

### 6. In which patterns is the main row behind the best reference, or behind DeFT_P? What do these patterns have in common?
*Pending.*

### 7. `CI_heurLA_O_LF` against the main row under faults
*Pending.*

### 8. Against each reference row
*Pending.*

### 9. Random against even patterns at the same rate (rounds 25 and 26)
*Pending.*

### 10. Reachability of MTR and RC at the four rates
**Final for MTR and RC; the drain-test table of DeFT and the late-binding rows is pending.**
MTR and RC lose exactly the share of the VLs that is faulty, on every mask (`reachability_v26.md`, static analysis of
`reach_v10.py`, unchanged, with the rate 8/16 added).

| rate | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| 1/16 | 93.75 % | 94.44 % | 93.75 % |
| 2/16 | 87.50 % | 88.89 % | 87.50 % |
| 4/16 | 75.00 % | 75.00 % | 75.00 % |
| 8/16 | 50.00 % | 50.00 % | 50.00 % |

* The table is the share of the inter-chiplet source-destination pairs that can be delivered. It is the same for MTR and for
  RC, the same for the mean and for the worst mask, and the same for the up to 1,000 random masks per (size, rate) and for the
  16 masks of Part B. No mask keeps every pair.
* The reason is in the two definitions. An RC source may leave only through the boundary router nearest to it, and each of
  the four VLs of a chiplet is the nearest for four of its sixteen routers. Under MTR's turn restrictions
  (`results_v10/mtr_config.json`) every source can reach all four exits, but every destination router can be entered
  through one VL only, again four routers per VL. So a faulty VL cuts off a quarter of the sources (RC) or of the
  destinations (MTR) of its chiplet from every other chiplet, whatever the other faults are, and the delivered share is the
  functional share of the VLs. (3x3 has 36 VLs, so its first two rates are 2 and 4 of 36.)
* The 18 rows of the three old rates equal those of round 10 (`results_v10/report/reachability.csv`).
