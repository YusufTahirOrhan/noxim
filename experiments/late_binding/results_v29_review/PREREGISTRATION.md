# Pre-registration v29: what two reviews of the paper ask for

Committed before any run of Parts B to G: before the ladders of the new traffic patterns (B0), the timing runs and every tuning run.
Done before it: the regression before and after the code change (`regression_before.md`, `regression.md`) and the gates of A2 that do not
need a ladder of a new pattern (`buffer_checks.md`, `drain_buffers.csv`, `anchor_first.md`, `unit_checks_first.md`, `drain_first.csv`,
`traffic_checks.md`, `formal_independent/`, `reuse_check.md`). Their results are summarised under "Gates" below. The drain tests on the
three new patterns need DeFT_P's saturation load on them and run after B0, before any evaluation run of a new pattern (`DECISIONS.md`).
Nothing below depends on a result of Parts B to G. What I expected was committed on its own before the gates (`stated_in_advance.md`,
commits 0c3988c and 8429055) and is copied unchanged at the end.

**The three objections.** The paper draft was reviewed twice. Three objections need runs, and each of them could reject the paper:
1. **The advantage over the best reference rests on the four scenarios used for tuning.** In round 25 the main row is ahead of the best
   of five references on the four tuning scenarios (THR +2.9 / +10.5 / +7.6 %, LAT -17.8 / -15.4 / -20.8 % on 2x2 / 3x3 / 4x4) and level
   with it or behind on the two others (THR -5.6 / -0.5 / +2.9 %, LAT +4.2 / +3.1 / +4.2 %). Two scenarios cannot tell tuning from
   workload, and `lut_bias` is set per size. Part B runs three scenarios that no round has used.
2. **The cost is never weighed against the gain.** The main row has 22 to 25 % more router area; no reference was given that area, there
   is no power figure, and the lookahead term was never priced. Parts C and E.
3. **MTR and RC are ahead of DeFT here, and behind it in the DeFT paper.** Part D runs them with one VC per packet at pipe_all 2 and
   runs the set-up of the DeFT paper.

Two smaller questions on early against late binding come along (Part F), and traces that load the network (Part G, optional).

**This round takes no side.** Every part can come out against the main row, and that is then what the paper will say. Nothing of the
frozen configuration is retuned and no existing row is changed. Where the prompt left a choice, the option that favours the references
and the early rows was taken (`DECISIONS.md`). The simulator is the e7569b1 build plus the options of `DeftLateBinding.h`, "v29", and
`-buffer_ipos`, all off by default.

## Gates (done; results)
* **Regression** (`regression_before.md`, `regression.md`): the 84-configuration set is byte-identical to the e7569b1 build before the
  change (A0; `bin/noxim` was the same file as a fresh build of e7569b1) and after it (A1), with the options absent and with every
  option of rounds 23 to 29 given at its default (`-buffer_ipos 0` and the diagnostic `buffer_stats 0` included).
* **The buffer options** (`buffer_checks.md`): `-buffer_ipos 4` with `-buffer 4` gives a statistics file byte-identical to the option
  absent in 12 / 12 runs (DeFT_P, MTR, RC and the main row, uniform traffic at 1.0 x Lsat, seed 121, three sizes). With the diagnostic
  `buffer_stats` the capacity of every input buffer that received a flit and the largest fill per layer are the ones asked for in
  24 / 24 runs (`-buffer 5`: 5 / 5, `-buffer 6`: 6 / 6, `-buffer_ipos 7`: 4 in the chiplet routers and 7 in the interposer routers, and
  `-buffer 6 -buffer_ipos 3` as a fourth case), and the diagnostic changes no statistic (6 / 6). `-buffer 5` and `-buffer 6` stopped
  the simulator before this round (the power table has no such depth; `DECISIONS.md`).
* **Drain tests with deeper buffers** (`drain_buffers.csv`): 72 / 72 pass. All-pairs workload (4,032 / 20,592 / 65,280 packets on 2x2 /
  3x3 / 4x4) with `-buffer 5`, `-buffer 6` and `-buffer_ipos 7`: DeFT_P, DeFT_B, MTR, RC and the main row fault-free, and DeFT_P, DeFT_B
  and the main row with the same VL faulty in every chiplet. Every packet is delivered and there is no dead-end event. The prompt asks
  for the tests at `-buffer 6` and `-buffer_ipos 7`; depth 5 is tested too because C1 runs it.
* **`EB_first` with `lut_bias 1e9` is DeFT_P's routing** (`anchor_first.md`): on the 21 runs of the anchor gate of round 28 every packet
  takes DeFT-P's entry VL; the row is byte-identical to DeFT_P in 0 / 21 runs as it is, because a commit draws twice from `rand()`, from
  which the routers' crossbar arbitration draws, and in 21 / 21 runs with its tie-breaks on a stream of their own (`tie_stream 1`). Mean
  of the 21 runs against DeFT_P: THR +0.08 %, LAT +0.21 %, P99 -0.71 %. So the family of `EB_first` contains DeFT_P's routing, with
  another arbitration sequence, as the anchors of round 28 did.
* **Unit checks of `entry_commit first`** (`unit_checks_first.md`): all pass. (1) On a mask that leaves every chiplet one functional VL
  the row is the main row (3 / 3 runs identical, no head bound). (2) For 12,000 bound heads per size (1,000 in each of the six
  fault-free scenarios at 1.0 x Lsat, with the main row's `lut_bias` and with 4) the selection of the main row at the commit router was
  evaluated a second time: the output towards the committed VL is a cheapest output of that selection in every case (2x2: 10,910
  unique and 1,090 ties; 3x3: 10,149 and 1,851; 4x4: 10,254 and 1,746; 0 different), and the committed VL is a candidate of least cost
  among those that take that output in every case. (3) The check reads only (3 / 3). (4) No head is bound more than once in any run, and
  no hop offers a head more than one output after its commit. Nearly every head that moves Up was bound (99.6 to 100.3 % of the Up
  moves of the measured window; the two are counted at different moments). The commit router is the one below the exit VL for 33 to
  34 % of the bound heads on 2x2, 24 to 26 % on 3x3 and about 20 % on 4x4, and for none under chiptrans traffic on any size and under
  chipperm traffic on 2x2 and 4x4.
  *Seen in these single runs, after `stated_in_advance.md` was committed:* with the main row's `lut_bias`, uniform traffic at 1.0 x Lsat,
  seed 101, `EB_first` has a mean latency of 72.0 / 102.1 / 111.5 cycles on 2x2 / 3x3 / 4x4. The expectations stay as they were written.
* **Drain tests of `EB_first`** (`drain_first.csv`): 36 / 36 pass. All-pairs workload (4,032 / 20,592 / 65,280 packets on 2x2 / 3x3 / 4x4)
  with the main row's `lut_bias` and with `lut_bias 4`, on the six masks per size of the drain tests of round 27 (fault-free, the same
  VL faulty in every chiplet, and mask 1 of each of the four fault rates of round 26): every packet is delivered, no dead-end event, no
  hop offers a head more than one output (the commit is made when the decision for the first such hop is computed), and no head is
  bound more than once. The tuned value of F1 is tested again before the evaluation of Part F (`drain_first_tuned.csv`).
* **The tables of the three new traffic patterns** (`traffic_checks.md`, `randperm_<size>.txt`): on every size every router of the
  chiplet layer sends, the rates of a source add up to the nominal rate (largest deviation 1.6e-08 packets/cycle, the rounding of the
  nine decimals of a line), `tornado` has one destination per source in the same row, `neighbour` has exactly the routers of the
  edge-adjacent chiplets, each with the same rate, and `randperm` is the permutation of `random.Random(2901)` without a fixed point.
  Share of the traffic that stays in the source's own chiplet: `tornado` 25 % on 2x2 and none on 3x3 and 4x4; `neighbour` none;
  `randperm` 23.4 / 9.7 / 5.9 %. The tables of the ladders are checked again after B0, and the drain tests of all rows of Part B on the
  three patterns at 0.5 and 1.0 x Lsat (`drain_traffic.csv`) run then, before any evaluation run of a new pattern; a failure stops the
  round.
* **The referee's independent check** (`formal_independent/`): `formal/lb_cdg_check.py` is not edited (its sha256 is in
  `formal_independent/README.md`) and every mode was run with `python3 -I`; the script needs `networkx`, which this machine has only in a
  user folder, so the isolated interpreter is started through a two-line wrapper that appends that one folder to the path and runs the
  script unchanged (`DECISIONS.md`). It reports what the prompt asks. `main`: no dead end, no path longer than d0 and an acyclic channel
  dependency graph for XY and for the VN-split order on 4, 9 and 16 chiplets (6 / 6 configurations). `rules`: a cycle when R2, R3 or R1 is
  dropped (3 / 3). `turnmodels` and `placements` are stored as printed: 17 configurations, every graph acyclic; the one configuration that
  switches rule (iii) off has dead ends, which is what it is there to show.
* **Reuse of the rows of rounds 25, 26 and 28** (`reuse_check.md`): with the build of this round and the row definitions of those rounds,
  24 / 24 runs of round 25 (the main row and DeFT_P, uniform and movinghot traffic at 1.0 x Lsat, seeds 121 and 122), 24 / 24 of round 26
  (the same rows on mask 1 of the rates 1/16 and 4/16, seeds 151 and 152) and 60 / 60 of round 28 (DeFT_P, the main row, `EB_best`,
  `EB_best64`, `EB_down_t`, uniform and chiptrans traffic, seeds 171 and 172) are identical to the rows of the earlier per-run files in
  every column. So the rows of rounds 25, 26 and 28 are taken from those files.
* **Safety (A3).** After reading the code I agree with the prompt on both points.
  * **`EB_first` binds one functional candidate of the head's own set.** `commitFirst` reduces the entry mask to `bit(v)` for a `v` that
    `nextMasks` keeps for the selected output, and `nextMasks` only removes candidates from the mask the head carries; that mask was set
    at injection to the functional VLs of the destination chiplet (`functionalMask`) and has only been pruned since. Until the commit the
    head was offered one output at every hop, and that output is the XY move towards every candidate still in its mask, the committed one
    included; after the commit it follows XY to that candidate. So the whole path of an `EB_first` packet is the path of DeFT's fixed-pair
    relation for (the LUT's exit VL, the committed entry VL), the relation `A_fixed_XY` that the model check of round 27 covers for every
    functional pair, and every channel dependency it uses is one of the main row's relation (`CI_XY_XY`: at each hop the move towards a
    candidate of the mask is among the offered outputs). The VN of a packet does not depend on the entry mask. The commit changes which
    candidate is kept, never the set it is chosen from; `lut_bias` (1e9 included) and the two draws only enter the choice. The referee's
    model takes the union over every non-empty initial candidate set, single VLs included, so it covers these paths as well.
  * **The buffer options change no routing.** `-buffer` and `-buffer_ipos` set the capacity of input buffers (`Router::configure`) and the
    buffer entries of the power model; the routing functions, the VN rules, the candidate masks and their pruning do not read a depth.
    The selection reads occupancies and full flags of the buffers themselves, which changes what it chooses among the offered outputs
    and not what is offered. The argument for deadlock freedom (an acyclic channel dependency graph) holds for any buffer depth of at
    least one flit.
  * Checked by simulation: the drain tests above, no dead-end event in any gate run, and in every run of the round the checks named
    under "Options of every run".

---

## Rows
Every row runs at pipe_all 2 unless a part says otherwise; LUTs `luts/v23`; `-traffic_rng 1`.

| row | definition |
|---|---|
| `DeFT_P`, `DeFT_B`, `MTR`, `RC`, `XY_SP` | as round 25 (`experiments_v25.row_args`): the VN-based rows with `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`, MTR and RC with `-vc_per_hop 1`, RC with `rc_slots 4` |
| `CI_heurLA_X_LF` (**main**) | as round 25, frozen: `lut_bias` 2 on 2x2 and 0 on 3x3 and 4x4 |
| `LB_b0` | the main row with `lut_bias 0`; run on 2x2 only, where it differs from the main row |
| `X_d5`, `X_d6` | reference X (DeFT_P, DeFT_B, MTR, RC) with `-buffer 5` or `-buffer 6`: every input buffer of every router; RC keeps `rc_slots 4` |
| `X_i7` | reference X with `-buffer_ipos 7`: 7-flit input buffers in the interposer routers, 4-flit buffers in the chiplet routers |
| `LB_d6` | the main row with `-buffer 6`, nothing retuned |
| `MTR_static`, `RC_static` | MTR and RC without `-vc_per_hop` (`experiments_v23.methods`, the rows of round 23): a packet keeps the VC drawn at injection |
| `LB_noLA` | the main row with `heur_lookahead 0`: the cost of an output is 2 x the fill of the buffer behind it + the hops left (+ `lut_bias`); lookahead routing, the fallback and the busy state stay |
| `EB_first` | the main row with `-deft_lb entry_commit first` and its own tuned `lut_bias` (Part F1) |
| `EB_best16`, `EB_best256` | `EB_best` of round 28 (S, P, B of `results_v28_anchor/tuning_choice_v28.json`) with `oracle_period 16` or `256`, T tuned again (Part F2) |

`experiments_v29_rows.row_args` builds every new row from the arguments of the existing row by replacing one value or appending one
option, so nothing else of a row can differ. No existing row is changed and nothing of the frozen configuration is retuned.

### `EB_first`
The main row until the head is forwarded to the first interposer router at which the routing function offers it more than one output
(the router below the exit VL if the entry candidates lie on both sides of it, otherwise the first column of a candidate that the head
reaches). At that moment, which is when the main row computes its decision for that router, the outputs get the main row's cost at that
router (occupancy, lookahead term, `lut_bias`), the output of least cost is selected with the selection's tie rule, and the entry mask is
reduced to the candidate of least cost among those that the selected output keeps (the cost the selection gives that output for a head
with this one candidate, plus `lut_bias` if it is not DeFT-P's entry VL while that VL is in the mask; ties at random). From then on the
packet has one entry candidate. The fallback of the main row cannot act at the commit router (`DECISIONS.md`). With `lut_bias` towards
infinity the row is DeFT_P's routing (`anchor_first.md`).

## Options of every run of Parts B to F
* Window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers unless the row says otherwise; one LUT per mask.
* Observation only: `-deft_lb count_vl 1` on DeFT_P and DeFT_B; `-deft_lb hop_stats 1` on every DEFT_LB row; `-deft_lb entry_stats 1` on
  the rows of Part F (round 27, `unit_checks.md`: the main row gives the same statistics with and without it).
* Dead-end events must be 0 in every run. No hop of an early row (`EB_first`, `EB_best16`, `EB_best256`, every tuning configuration) may
  offer more than one output after its commit, and no head of `EB_first` may be bound twice. A violation stops the round.

## Seeds
| seeds | used before | parts | paired with |
|---|---|---|---|
| 181-190 | never | B1 | - |
| 191-195 | never | D2 | - |
| 121-130 | round 25 | B2, C1, C2, D1, E1 | the rows of `results_v25_confirm/eval_runs.csv` |
| 151, 152 | round 26 | C3 | the rows of `results_v26_faults/fault_rate_runs.csv` |
| 171-180 | round 28 | F1, F2 | the rows of `results_v28_anchor/eval_runs.csv` |
| 101, 102 | tuning and calibration in every round | B0 (seed 101), the tuning of Part F | - |

A reused row is taken from the earlier round's per-run file only after the reuse check (`reuse_check.md`, under "Gates").

## Metrics, effects and tests (as round 25)
* **THR** of a row in a scenario for a seed: the largest accepted throughput over the loads of the ladder (nine loads; four in C2 and C3,
  for every row of the comparison alike). **LAT** and **P99**: mean and 99th-percentile packet latency at 1.0 x Lsat of DeFT_P with 4-flit
  buffers (the 4th load of the ladder). **LAT at a load**: the mean latency at that point of the ladder.
* **Effect per size** of row A against row B over a set of scenarios = 100 x (exp(mean over the seeds of R_s) - 1) %, R_s = the mean over
  the scenarios of ln(metric_A / metric_B) for seed s, the two rows paired by scenario and seed. The 95 % interval is the t interval of
  the mean of the R_s, transformed the same way; the test is the two-sided one-sample t test of the R_s against 0.
* **The best of a set of rows** is chosen per size, scenario and metric by the mean over the seeds (the largest THR, the smallest LAT or
  P99), and that row is then the reference of the scenario for every seed (round 25).
* **Verdicts of a primary test:** supported = significant after Holm (alpha = 0.05) with the main row ahead; against = significant with
  the main row behind; otherwise not significant. Everything outside the two primary families is descriptive: unadjusted intervals,
  never called significant.

---

## Part B: scenarios never used
* **B0.** DeFT_P's ladders of `tornado`, `neighbour` and `randperm` on 2x2, 3x3 and 4x4 by the rule of round 25 (seed 101, pipe_all 2,
  Lsat = the last rate before the latency exceeds 3 x L0, nine loads at 0.2 to 2.4 x Lsat) -> `load_points_v29.json`. A scenario that is
  not saturated at the end of the usual sweep (0.024) is swept further in steps of 0.004.
* **B1.** Rows `DeFT_P`, `DeFT_B`, `MTR`, `RC`, `XY_SP`, the main row, and `LB_b0` on 2x2; the three scenarios, three sizes, nine loads,
  seeds 181-190: 4,860 + 270 runs -> `heldout_runs.csv` (the columns of `results_v25_confirm/eval_runs.csv`).
* **B2.** `LB_b0` on 2x2 on the six fault-free scenarios of round 25, the ladders of `load_points_v25.json`, seeds 121-130: 540 runs ->
  `lb_b0_runs.csv`, paired with the rows of round 25.

### Primary family 1 (12 tests, Holm over the 12)
For each size, over the three new scenarios: the main row has higher THR, and lower LAT at 1.0 x Lsat, than (a) `DeFT_P` and (b) the
best of the five references (`DeFT_P`, `DeFT_B`, `MTR`, `RC`, `XY_SP`; the best per scenario and metric).

### Secondary (descriptive)
* each scenario separately, against DeFT_P and against the best reference, with the reference that is the best;
* the main row against the best of `DeFT_P` and `DeFT_B` (the references that tolerate VL faults) and against the best of `MTR` and `RC`;
* P99; LAT at 0.2, 0.5 and 0.8 x Lsat;
* **the five scenarios that the tuning never saw taken together:** the three new ones (seeds 181-190) with localized and movinghot of
  round 25 (seeds 121-130), each on its own seeds: the mean of the five per-scenario effects and their range, against the best of the
  five references, against the best of DeFT_P and DeFT_B and against the best of MTR and RC; no test;
* **`LB_b0`** against the main row and against the best reference on 2x2: for the three new scenarios, and for the six of round 25 (all
  six, the four tuning scenarios uniform, hotspot, chipperm, chiptrans, and the other two); also LAT at 0.5 x Lsat, which is a term of the
  tuning score;
* the number of cells in which THR is reached at the last load (THR is then a lower bound), the accepted throughput beyond the peak, and
  the hops with a choice per packet of the main row, as round 25 reports them.

---

## Part C: references with the area of the main row
The main row's routers have 1.25 / 1.22 / 1.22 times DeFT's area with the hierarchy kept, 1.16 / 1.13 on 2x2 / 4x4 with the core kept and
1.10 / 1.08 flattened (`results_v25_confirm/hw/FINDINGS_hw.md`). Part E3 measures the area of DeFT's routers with 5-flit and 6-flit
buffers and with 7-flit buffers in the interposer routers, in the same three forms; the comparisons below are read with the measured
ratios, whatever they are.

* **C1.** `DeFT_P_d6`, `DeFT_B_d6`, `MTR_d6`, `RC_d6`, `LB_d6`, and `DeFT_P_d5`, `DeFT_B_d5`, `MTR_d5`, `RC_d5`: the six fault-free
  scenarios of round 25, three sizes, the nine loads of `load_points_v25.json` (the ladders of DeFT_P at depth 4, so that every row is
  measured at the same loads), seeds 121-130: 9 x 1,620 = 14,580 runs -> `depth_runs.csv`. The main row and the references at depth 4
  are the rows of round 25.
* **C2.** `DeFT_P_i7`, `DeFT_B_i7`, `MTR_i7`, `RC_i7`: the same scenarios and seeds on the ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4,
  2.0 x Lsat): 2,880 runs -> `ipos7_runs.csv`. In every comparison with an `X_i7` row THR is the largest accepted throughput over these
  four loads, for every row, the rows of round 25 included.
* **C3.** `DeFT_P_d6` and `DeFT_B_d6` on the 48 masks of rate 4/16 and the 48 of rate 1/16 of round 26, uniform and hotspot traffic, the
  four loads of `load_points_v26.json`, seeds 151 and 152: 3,072 runs -> `depth_fault_runs.csv`. The main row and the references at depth
  4 are the rows of round 26.

### Primary family 2 (12 tests, Holm over the 12)
For each size, over the six scenarios: the main row at depth 4 has higher THR, and lower LAT at 1.0 x Lsat, than (a) the best of
`DeFT_P_d6` and `DeFT_B_d6` and (b) the best of the four references at depth 6. The two families are adjusted separately.

### Secondary (descriptive)
* every reference at depth 5, at depth 6 and with interposer depth 7 against itself at depth 4 (what the buffers buy it): THR, LAT, P99;
* the two comparisons of the primary family at depth 5, with intervals;
* the main row against each `X_d6`, `X_d5` and `X_i7` and against the best of each set, with the area ratio of the set that E3 measures
  next to it, in each of the three forms of the synthesis;
* the four tuning scenarios and the other two separately; each scenario;
* `LB_d6` against the best reference at depth 6 and against the best of the two DeFT variants at depth 6 (equal buffers again, at depth
  6), and against the main row;
* LAT at 0.5 and 0.8 x Lsat;
* **C3 as round 26:** the value of a mask is the mean over the two traffic patterns and the two seeds of ln(metric_A / metric_B), THR the
  largest accepted throughput over the four loads, LAT at 1.0 x Lsat of DeFT_P on the mask; effect = the mean over the 16 masks of a size
  and rate with its 95 % t interval. The main row against the best of the two variants at depth 6 (the best per mask, traffic and metric
  by the mean of the two seeds) and against each; by rate and by traffic; each variant at depth 6 against itself at depth 4.

---

## Part D: the references against the DeFT paper (descriptive, no test)
* **D1.** `MTR_static` and `RC_static`: the six fault-free scenarios, three sizes, the ladders of round 25, seeds 121-130: 3,240 runs ->
  `vc_static_runs.csv`. Reported: each static row against its per-hop row of round 25 (THR; LAT at every load); DeFT_P against the better
  of the two static rows at every load, per size and per scenario; the main row against the best of `DeFT_P`, `DeFT_B`, `MTR_static`,
  `RC_static` and `XY_SP` (the main comparison of the paper with the other VC policy): all six scenarios, the tuning four, the other two.
* **D2.** The set-up of the DeFT paper: 2x2 (4 chiplets of 4x4 routers, 4 VLs per chiplet), 8-flit packets, 4-flit buffers, two VCs,
  the LUT with rho = 0.01 (`luts/v23`, the 2x2 table of every round); uniform, localized (40 % of a source's traffic stays in its chiplet)
  and hotspot traffic (three routers receive 10 % each). Rows `DeFT_P`, `MTR`, `RC`, `MTR_static`, `RC_static`. Twelve rates per pattern
  and pipe depth: k / 10 x Lsat of DeFT_P for k = 1 ... 12, rounded to the 0.0001 grid (halves up), with Lsat of the ladder of round 25
  at pipe_all 2 and of round 23 at pipe_all 0 (both in `load_points_v25.json`). Seeds 191-195; pipe_all 2 and pipe_all 0: 1,800 runs ->
  `deft_setup_runs.csv`.
  Reported per pattern and pipe depth: the mean latency of every row at every rate with its 95 % interval over the five seeds (one table
  and one figure per pattern); and at every rate whether DeFT_P has the lowest mean latency of DeFT_P, MTR and RC, once with the per-hop
  rows and once with the static rows: the effect of DeFT_P against the better of the two others with its interval. "Lowest" is said with
  the interval: lowest with an interval that excludes 0, lowest within the interval, or not the lowest.
* One paragraph in `FINDINGS.md`: what explains the difference between this simulator and the DeFT paper, and what remains unexplained.

---

## Part E: the cost of the main row
* **E1 (simulation, descriptive).** `LB_noLA`: the six fault-free scenarios, three sizes, the ladders of round 25, seeds 121-130: 1,620
  runs -> `nola_runs.csv`. Against the main row, DeFT_P and the best of the five references of round 25: THR, LAT, P99, LAT at 0.2 and
  0.5 x Lsat; all six scenarios, the tuning four, the other two.
* **E2 (hardware).** Two RTL variants of the interposer router of the main row, each checked against recorded decisions of the matching
  simulator row as in round 25 (F2), then synthesised and timed with the flow of round 25: (1) without the reports across the VLs (the
  design of `LB_noVLrep`: no wires from the boundary router above, 24 x 3 report bits in every interposer router); (2) `LB_noLA`: no
  report wires or registers at all; the decision unit has the credit counts, the static hop terms and the bias only. For each: the area
  of the four router types, the system ratio to DeFT on the three sizes in the three forms of round 25 (hierarchy kept, core kept,
  flattened), the stage times, the margin at T_ref and the delay left to an interposer link in the link cycle.
* **E3 (hardware).** DeFT's routers with 5-flit and 6-flit buffers, and DeFT's interposer routers with 7-flit buffers: area and the system
  ratio to DeFT at depth 4 in the three forms, next to the main row's ratios in the same forms, synthesised in the same run.
* **E4 (hardware).** Power of DeFT's and the main row's interposer router (with and without a VL) and chiplet router on 4x4 with OpenSTA
  `report_power` on the flattened netlists, at the 1 ns clock of the synthesis. Internal, switching and leakage power, the ratio of the
  main row to DeFT per router and for the system (12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers per chiplet); the
  same for the two variants of E2. The limits are stated with the numbers (before layout, no wire capacitance, no clock tree).
  Two sets of numbers, decided now, before any of them exists:
  * **the default activity of the tool** (0.1 transitions per clock period and a duty of 0.5 at every input, propagated through the
    gates), stated as such, for every router;
  * **the activity of a simulation, read from a VCD.** The vectors that the flow records (round 25, F2) are evaluations of the decision
    unit; they hold no cycle and no port, so they cannot drive a router, and DeFT's routers have no such vectors at all. What is replayed
    is therefore the load: the instrumented copy of the simulator counts, on 4x4 under uniform traffic at 0.5 and at 1.0 x Lsat (the 2nd
    and 4th load of the ladder of round 25, seed 1, pipe_all 2), the flits per input port of every router, the share on VC 1 and the mean
    stay of a flit in an input buffer; the router-level test benches of rounds 18 and 25 then drive each synthesised netlist with random
    8-flit packets at these flit rates per port, with the measured share of heads that end at the router or take its vertical link, and
    with credits that come back after the measured stay (`hw/tb/tb_act18.v`, `tb_act25.v`; DeFT's routers with the counts of the DeFT_P
    run, the others with the counts of their own row). The simulation is of the netlist itself (Verilog models of the cells written by
    Yosys from the liberty file, zero delay, so no glitches), 2,000 + 10,000 cycles, and the VCD holds the 10,000.
  If the simulation or its reading fails with the installed tools, the default activity stands alone and the report says why.
* A step of E2 to E4 that the installed tools cannot do is named with the reason, and the round goes on.

---

## Part F: two more early binders (descriptive, no test; seeds 171-180, paired with round 28)
The tuning rule is written out in `tuning_v29.md` ("The rule") before any tuning run: the rule of round 24 as rounds 27 and 28 applied it
(2x2 and 4x4, 3x3 takes the 4x4 choice; five tuning scenarios; four loads; seeds 101 and 102; the score against DeFT-P).
* **F1. `EB_first`.** `lut_bias` in {0, 1, 2, 4, 8}, extended to 16, 32, 64 while the best value is the largest. The chosen value is
  added to this file as an addendum before any evaluation run of the row, and the drain tests are run again with it
  (`drain_first_tuned.csv`); a failure there stops the round before the evaluation of the row. Then the six fault-free scenarios, three
  sizes, the ladders of round 25, seeds 171-180: 1,620 runs -> `early_first_runs.csv`. Reported against `DeFT_P`, the main row, `EB_best`
  and `EB_down_t` of round 28: THR, LAT, and the share of the main row's gain over DeFT_P ((mean R_s of the row against DeFT_P) / (mean
  R_s of the main row against DeFT_P), as round 28); the share of the bound heads whose commit is made at the router below the exit VL.
* **F2. `EB_best16`, `EB_best256`.** T in {0, 2, 4, 8, 16, 32}, extended to 64 and 128 while the best value is the largest (B2 of round
  28); the chosen values as an addendum; then the evaluation of F1 for both rows: 3,240 runs -> `early_age_runs.csv`. Reported: the share
  of the main row's gain (THR and LAT) against the age of the source's knowledge: 0 (`EB_best`), 16, 64 (`EB_best64`), 256 cycles, per
  size, for all six scenarios, for hotspot traffic alone and for the other five.
* If a chosen configuration scores below 0 in the tuning, DeFT_P is the best member of its family: that is said first, and every share
  is also reported for the better of the row and DeFT_P.

## Part G (optional, at most 3 h): traces that load the network
2x2, the nine PARSEC traces of round 25 (`experiments_v25_apps.py`), `-netrace_compress S`: for each trace the smallest S in {2, 4, 8, 16,
32} at which DeFT_P's mean latency is at least 1.5 times its latency at S = 1; at that S the rows DeFT_P, MTR, RC and the main row.
Reported: the mean latency per trace and the geometric mean over the traces, relative to DeFT_P. A trace for which no S reaches the
factor is reported as such; if none does, the part stops there. Descriptive.

---

## Time rule
After the gates and B0 the parts are timed with runs of the designs (kept; their results are not looked at; one set after the other, no
other job of the round next to a set; `runtime_estimate.md`): per size the seed-181 runs of B1, the runs of the references at depth 6
with seeds 121 and 122 at the 2nd, 5th and 9th load, and the seed-151 runs of C3 at the 1st and 4th load of masks 1 to 4 of both rates;
and the seed-191 runs of D2. A part is estimated with the seconds per run of the set of its kind and size, taken as measured; the tuning
runs of Part F are counted at their grids, Part G at 3 h. If Parts B to G together exceed 48 h, the following are dropped in this order
until they do not: Part G; F2; the rate 1/16 of C3; C2; D1 on 3x3 and 4x4; `LB_d6`; seeds 126-130 of the rows at depth 5. Parts B, the
rows at depth 6 of C1, D2, E1 and E3 are never dropped. What was dropped is taken back in the reverse of the drop order if it fits
later: when, at the end of a part, the time since the start of the timing runs plus the estimate of what is still to run plus the item,
at the speed measured until then, is at most 48 h; decided from the clock and the number of finished runs only. If an item stays
dropped, the analysis is the one above on what was run, and the report says what is missing.

## Checks of the analysis
The 12 tests of family 1 and the 12 of family 2 are computed a second time by a script that shares no code with the report
(`check_v29_family.py`), as in rounds 25 to 28.

## Not done in this round
No retuning of the frozen configuration and no change to an existing row. No new proof and no new model check: `EB_first` binds one
functional candidate of the head's own set and the buffer options change no routing (A3, under "Gates"). `LB_d6` is not retuned for
6-flit buffers and its RTL is not built. MTR and RC are not run with faults (they cannot deliver every pair, round 26).

---

## Addendum F1 (26 Nov 2026, 10:50): the tuned `lut_bias` of `EB_first`, frozen before any evaluation run of the row
Written by `addendum_v29.py` from `tuning_choice_v29.json`: the choice of `experiments_v29.py f1_choose` by the rule of `tuning_v29.md` ("The rule", committed on
25 November before any tuning run). Tuning runs: 560 rows in `tune_first_runs.csv` (seeds 101 and 102: the values of `lut_bias`, DeFT-P and the main row), dead-end
events 0. No evaluation run of `EB_first` existed at this moment (no file in its raw folder, no `early_first_runs.csv`). Scores against DeFT-P in natural-log
units, higher is better; DeFT_P scores 0.

| row | 2x2 | 3x3 (the 4x4 choice) | 4x4 |
|---|---|---|---|
| `EB_first` | `lut_bias` 4; score +0.3322 | `lut_bias` 4; score +0.3445 | `lut_bias` 4; score +0.3445 |
| main row (frozen, not tuned) | score +0.5303 | score +0.6479 | score +0.6479 |

* Values of `lut_bias` that were run: 2x2 {0, 1, 2, 4, 8}, chosen 4; 4x4 {0, 1, 2, 4, 8}, chosen 4.
* No chosen value scores below 0, so the rule for a best member at `lut_bias` = infinity (DeFT_P) does not apply and no "better of the row and DeFT_P" share is reported.
* DeFT-P and the main row on the tuning cells, run again with the build of this round, against the rows of `results_v27_early/tune_runs.csv` (every column, as text): **160 / 160 identical.**
* Hops of the tuning runs of the early rows that offer more than one output after the commit (must be 0): 0. The same for the tuning runs of F2: 0.
* The drain tests of `EB_first` are run again with these values before its evaluation (`drain_first_tuned.csv`, `chain_v29c.sh d`); a failure stops the round
  before the evaluation of the row.
* What I had stated in advance: "its tuned `lut_bias` is 2 or 4".

---

## Addendum F2 (26 Nov 2026, 10:50): the tuned T of `EB_best16` and `EB_best256`, frozen before any evaluation run of the two rows
Written by `addendum_v29.py` from `tuning_choice_v29.json`: the choice of `experiments_v29.py f2_choose` by the rule of `tuning_v29.md` (B2 of round 28, unchanged:
S, P and B of `EB_best`, T tuned for each age). Tuning runs: 1120 rows in `tune_age_runs.csv` (seeds 101 and 102), dead-end events 0. No evaluation run of the two rows
existed at this moment (no file in their raw folder, no `early_age_runs.csv`). Part F2 is run because the user lifted the limit of 48 h on 25 November
(`DECISIONS.md`, `time_rule.md`); its definition above is unchanged. Scores as in Addendum F1.

| row | 2x2 | 3x3 (the 4x4 choice) | 4x4 |
|---|---|---|---|
| `EB_best16` | S vl, P 1, B 0.5, T 16 (`oracle_bias` 8), `oracle_period 16`; score +0.4901 | S vl, P 1, B 1, T 8 (`oracle_bias` 8), `oracle_period 16`; score +0.4584 | S vl, P 1, B 1, T 8 (`oracle_bias` 8), `oracle_period 16`; score +0.4584 |
| `EB_best256` | S vl, P 1, B 0.5, T 128 (`oracle_bias` 64), `oracle_period 256`; score +0.1047 | S vl, P 1, B 1, T 64 (`oracle_bias` 64), `oracle_period 256`; score +0.1521 | S vl, P 1, B 1, T 64 (`oracle_bias` 64), `oracle_period 256`; score +0.1521 |
| for comparison, round 28: `EB_best` (age 0) | T 8; score +0.5505 | T 2; score +0.4936 | T 2; score +0.4936 |
| `EB_best64` (age 64) | T 32; score +0.3473 | T 16; score +0.3446 | T 16; score +0.3446 |
| main row (frozen, not tuned) | score +0.5303 | score +0.6479 | score +0.6479 |

* Values of T for `EB_best16` that were run: 2x2 {0, 2, 4, 8, 16, 32}, chosen 16; 4x4 {0, 2, 4, 8, 16, 32}, chosen 8.
* Values of T for `EB_best256` that were run: 2x2 {0, 2, 4, 8, 16, 32, 64, 128} (extension: 64, 128), chosen 128: **the largest value run**; 4x4 {0, 2, 4, 8, 16, 32, 64, 128} (extension: 64, 128), chosen 64.
* No chosen value scores below 0, so the rule for a best member at T = infinity (DeFT_P) does not apply and no "better of the row and DeFT_P" share is reported.
* Hops of the tuning runs of the early rows that offer more than one output after the commit (must be 0): 0. The same for the tuning runs of F2: 0.
* What I had stated in advance: the share of the main row's gain falls with the age of the information on every size.

---

## Stated in advance
The file `stated_in_advance.md` as committed before the gates (commits 0c3988c and 8429055), unchanged from the next line to the end.

# Stated in advance (v29)

Written on 24 Nov 2026 at about 14:50, after the code change of A1 was built and while its regression ran: before any gate of A2, before
any ladder of the new traffic patterns and before any run of Parts B to G. It is copied unchanged into `PREREGISTRATION.md`.

**What I had seen of the new options when I wrote this** (six smoke runs of the new binary, made to see that the options are accepted; seed
121, pipe_all 2):
* DeFT_P on 2x2 under uniform traffic at 2.4 x Lsat: accepted throughput 0.1205 flits/node/cycle with 4-flit buffers, 0.1263 with
  `-buffer 5` (+4.8 %), 0.1283 with `-buffer_ipos 7` (+6.5 %). One run each, far above saturation.
* The main row with `entry_commit first` and the main row's own `lut_bias`, uniform traffic at 1.0 x Lsat: on 2x2 the same accepted
  throughput as the main row and a mean latency of 66.5 cycles against 61.0; on 4x4 a mean latency of 108.0 cycles (no run of the main row
  next to it). Of the heads that were bound, 34 % (2x2) and 21 % (4x4) were bound at the router below the exit VL.

Nothing else: no run of a new traffic pattern, of a row at depth 6, of `LB_b0`, `LB_noLA`, `MTR_static` or `RC_static` at pipe_all 2 in
this round, and no tuning run.

## Part B: scenarios never used

**The prompt's expectation**, quoted: "the main row is ahead of DeFT_P in all three scenarios on every size. Against the best reference I
expect about zero on 2x2 and a few percent on 3x3 and 4x4 for `tornado` and `randperm`, and nothing for `neighbour`, whose paths are
short. `LB_b0` loses less than 1 % of throughput on 2x2."

**Mine:**
* **Against DeFT_P, over the three new scenarios:** the main row is ahead on every size, THR +5 to +12 % and LAT at 1.0 x Lsat -25 to
  -40 %; ahead in each of the nine cells of scenario and size in both metrics. The smallest gain is under `neighbour` (THR +3 to +10 %).
  All six tests (a) of family 1 supported.
* **Against the best of the five references, over the three new scenarios:**

  | size | THR | LAT at 1.0 x Lsat |
  |---|---|---|
  | 2x2 | -2 to +2 %, more likely below 0 than above | -8 to +5 % |
  | 3x3 | +1 to +6 % | -12 to 0 % |
  | 4x4 | +2 to +7 % | -15 to -2 % |

  So of the six tests (b) I expect the four on 3x3 and 4x4 supported (the LAT test on 3x3 is the one of them I am least sure of) and the
  two on 2x2 not supported, the THR test there possibly against. **Family 1: 9 or 10 of 12 supported, at most one against.**
* **Per scenario against the best reference** (THR; 2x2 / 3x3 and 4x4): `tornado` 0 to +5 % / +3 to +10 %; `randperm` -3 to +2 % /
  +2 to +8 %; `neighbour` -5 to 0 % / -1 to +6 %. I do not expect "nothing" for `neighbour` on 4x4: every packet of it crosses two VLs and
  has four entry candidates, which is what the main row works on; I expect a loss on 2x2, as under localized traffic in round 25.
* **Which reference is the best:** MTR or RC for THR and LAT in most of the nine cells; a DeFT variant under `tornado` on 4x4 (as under
  chipperm traffic in round 25).
* **The five scenarios that the tuning never saw, taken together** (the mean of the five per-scenario effects against the best reference):
  THR -3 to 0 % on 2x2, 0 to +3 % on 3x3, +1 to +5 % on 4x4; LAT at 1.0 x Lsat 0 to +5 % on 2x2 and 3x3 (the main row slower) and -5 to
  +3 % on 4x4. That is: behind on 2x2, level on 3x3, a little ahead on 4x4. Against the two references that tolerate VL faults (the best
  of DeFT_P and DeFT_B) ahead on every size in both metrics.
* **`LB_b0` on 2x2:** within 1 % of the main row in THR in every group of scenarios (the three new ones, the four of the tuning, the other
  two of round 25). LAT at 1.0 x Lsat 1 to 4 % higher than the main row on the four tuning scenarios (that difference is why the tuning
  chose 2) and within 2 % elsewhere. Against the best reference it gives the same picture as the main row. So I expect the answer "the
  paper can use one configuration for all sizes, for a few per cent of latency on the tuning scenarios of 2x2".

## Part C: references with the area of the main row

**The prompt's expectation**, quoted: "6-flit buffers give a reference 3 to 8 % more throughput, 5-flit buffers about half of that. The
main row stays ahead of the DeFT variants at depth 5 and 6 on 3x3 and 4x4 and is about level on 2x2; against MTR and RC at depth 6 it is
level or behind in throughput on every size, at depth 5 about level, and its latency at DeFT's Lsat is no longer lower."

**Mine** (the smoke runs above moved me upwards from the prompt's 3 to 8 %):
* **What the buffers buy a reference** (against itself at depth 4, over the six scenarios): THR +5 to +10 % at depth 6 and +3 to +5 % at
  depth 5; LAT at 1.0 x Lsat of DeFT_P -20 to -40 % for DeFT_P and DeFT_B (they sit on their knee at that load) and -10 to -25 % for MTR
  and RC. `X_i7` buys about what `X_d6` buys (the interposer is where the buffers count).
* **Family 2, the main row at depth 4 against the best of `DeFT_P_d6` and `DeFT_B_d6` (a):** THR -3 to +2 % on 2x2 (not supported),
  +2 to +8 % on 3x3 and +1 to +6 % on 4x4 (both supported); LAT -10 to +10 % on 2x2 (not supported) and -15 to +5 % on 3x3 and 4x4
  (I expect one of the two supported).
* **Against the best of the four references at depth 6 (b):** THR -8 to -3 % on 2x2 (against), -3 to +2 % on 3x3 and 4x4 (not
  significant, or against); LAT +5 to +25 % on every size (against).
* **Family 2 in numbers: 2 to 4 of 12 supported, 4 to 6 against.** The paper's sentence would then be the one the prompt writes: the gain
  over MTR and RC does not survive equal area.
* **At depth 5** (about the main row's area with the core kept): against the best of the four references THR -4 to -1 % on 2x2, 0 to
  +4 % on 3x3 and 4x4; LAT within -5 to +10 %. Against the DeFT variants at depth 5 ahead on 3x3 and 4x4 in both metrics, level on 2x2.
* **`LB_d6`:** THR +4 to +8 % against the main row; against the best reference at depth 6 about what the main row has against the best
  reference at depth 4 or a little less (THR -1 / +5 / +5 % on 2x2 / 3x3 / 4x4): the gain of late binding holds with deeper buffers on both
  sides. The weights of the selection were tuned for 4-flit buffers, so a smaller gain would not surprise me.
* **C3, under faults:** against the best of `DeFT_P_d6` and `DeFT_B_d6` the main row at depth 4 is behind in THR at the rate 4/16 on every
  size (-6 to -1 %) and level to behind at 1/16 (-3 to +2 %); in LAT between -5 and +15 %. At depth 4 it was ahead by 3 to 9 % in THR and
  17 to 20 % in LAT (round 26).

## The other parts (not asked for; one line each, so that they can be held against the results)
* **D1:** the per-hop VC choice gives MTR and RC +2 to +5 % THR and -5 to -15 % LAT at 1.0 x Lsat against one VC per packet. Against the
  best of DeFT_P, DeFT_B, `MTR_static`, `RC_static` and XY_SP the main row is about two points further ahead in THR than against the
  per-hop rows.
* **D2:** DeFT_P has the lowest latency of DeFT_P, MTR and RC only at the lowest loads (up to 0.3 to 0.5 x Lsat) against the per-hop rows,
  and up to 0.6 to 0.8 x Lsat under uniform traffic against the static rows; under hotspot traffic at no load above 0.3 x Lsat; the same
  at pipe_all 0.
* **E1:** `LB_noLA` against the main row: THR -1 to -2 %, LAT at 1.0 x Lsat +4 to +10 %.
* **F1:** `EB_first` reaches 50 to 80 % of the main row's THR gain and of its LAT gain, more than `EB_down_t` on 3x3 and 4x4; its tuned
  `lut_bias` is 2 or 4.
* **F2:** the share of the main row's gain falls with the age of the information on every size: with 16 cycles between `EB_best` and
  `EB_best64`, with 256 cycles 10 to 25 points below `EB_best64`.
