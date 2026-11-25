# Artifact description: what the experiments of the paper are made of

Collected in round 29 (`results_v29_review/PROMPT.md`, Part H) from the scripts of this folder and the simulator sources: the traffic,
the loads, the fault patterns, the options of every row, the tuned values, DeFT's tables, the VC policy of MTR and RC, the order of the
fallback, and which script writes which table of `paper_data/`. Paths are relative to the repository root; `LB` = `experiments/late_binding`.
Where a number was computed for this file, the script is named. The traffic tables (`LB/traffic*/`) and DeFT's tables (`LB/luts/`) are not
in the repository; the drivers write them again on demand (sections 2 and 7).

## 1. The system and one run

* **Topology `DEFT_2_5D`.** CX x CY chiplets of 4 x 4 routers on one interposer mesh under them. "2x2", "3x3" and "4x4" are the chiplet
  grids: 64 / 144 / 256 chiplet routers and as many interposer routers; the chiplet layer is FW = 8 / 12 / 16 routers wide
  (`LB/experiments_v5.py`, `SIZES`; `src/DeftTopology.cpp`).
* **Router ids.** Chiplet layer, row by row over the whole layer: router (x, y) has id y x FW + x and belongs to chiplet
  (y // 4) x CX + x // 4. The interposer router below it has id N + y x FW + x, N the number of chiplet routers.
* **Vertical links (VLs).** Four per chiplet, VL id = 4 x chiplet + slot, slots North, East, South, West = 0, 1, 2, 3 at the local
  positions (1, 0), (3, 1), (2, 3), (0, 2) (`src/DeftTopology.h`).
* **Base configuration** `config_examples/deft_2_5d_traffic_uniform.yaml`: 2 VCs, 4-flit input buffers, 8-flit packets, 1000 cycles of
  reset. Everything else is given on the command line.
* **The command line of a run** (`LB/experiments_v24.py`, `job`; `LB/runner.py`, `common_args`):
  `-config <base> -seed S -deft_vl_lut LB/luts/v23/lut_<size>_<mask>.yaml -stats_format json [-deft_faulty_vls <VL ids>]`
  `-traffic table ../experiments/late_binding/<traffic folder>/<pattern>_<rate>.txt [-deft_chiplets_x C -deft_chiplets_y C]`
  `<options of the row> -pipe_all 2 -traffic_rng 1 -sim 10000 -warmup 2000`, run from `bin/`.
  * Window: 2000 cycles of warm-up and 8000 measured cycles after the reset.
  * `-pipe_all 2`: every head waits two cycles at the front of an input buffer before it may reserve an output (a router of three
    cycles). A few parts run `-pipe_all 0` (round 25 Part E, round 29 D2) and say so.
  * `-traffic_rng 1`: the traffic generator has its own generator (`std::mt19937`, seeded with the run seed), so every row sees the same
    packets for a seed. The crossbar arbitration and the tie-breaks of the selection still draw from `rand()` (`src/Router.cpp`,
    `src/DeftLateBinding.cpp`), so two rows with the same routes are not byte-identical unless `-deft_lb tie_stream 1` is given (round 28).
* **Rates and loads.** A rate is in packets per cycle and source; the offered load in flits per node and cycle is 8 x rate.
* **Metrics** (`LB/make_eval_csv.py`, `LB/report_v25.py`): accepted throughput = `average_ip_throughput_flits_per_cycle_per_ip`, latency =
  `global_average_delay_cycles`, P99 = `deft_lb.delay_p99` of the statistics file. THR of a row = its largest accepted throughput over
  the loads of the ladder; LAT and P99 = at 1.0 x Lsat of DeFT_P (the fourth load).
* **Seeds.** 101 and 102: ladders and tuning only, never evaluation. Round 25: 121-130 (131-135 fault sweep, 141-145 one-cycle router,
  41-43 traces). Round 26: 151, 152. Round 27: 161-170. Round 28: 171-180. Round 29: 181-190 (held-out scenarios), 191-195 (D2); its
  other parts pair with the seeds of the round whose rows they reuse.

## 2. The six traffic patterns (`LB/gen_traffic.py`)

A table has one line per source and destination, `src dst rate x share`; the shares of a source add up to 1, and only the chiplet routers
send and receive. Tables: `LB/traffic/` (2x2), `LB/traffic_3x3/`, `LB/traffic_4x4/`, files `<pattern>_<rate with four decimals>.txt`,
written by `python3 gen_traffic.py <folder> --chiplets C C --rates r1,r2 --patterns p` (the drivers call it through
`experiments_v5.gen_tables` for every rate they need).

| pattern | where a source's packets go |
|---|---|
| `uniform` | every other router of the chiplet layer with the same share |
| `localized` | 40 % to the 15 other routers of its own chiplet (equal shares); **the other 60 % to all routers of all other chiplets, each with the same share** (48 / 128 / 240 routers on 2x2 / 3x3 / 4x4), with no weighting by distance |
| `hotspot` | 10 % to each of **three hot routers**, the rest equally to all other routers. The hot routers are the routers at local position (1, 1) of chiplets 0, 1 and CX, that is at (x, y) = (1, 1), (5, 1), (1, 5) of the chiplet layer on every size: **routers 9, 13, 41 on 2x2; 13, 17, 61 on 3x3; 17, 21, 81 on 4x4**. A hot router sends 10 % to each of the other two |
| `chipperm` | chiplet c sends only to chiplet C - 1 - c (the chiplet grid reflected through its centre), equally to its 16 routers; on 3x3 the middle chiplet sends to its own other routers |
| `chiptrans` | chiplet (cx, cy) sends only to chiplet (cy, cx), equally to its 16 routers; a chiplet on the diagonal sends to its own other routers |
| `movinghot` | 40 % to the routers of the **hot chiplet** of the phase, 60 % equally to all other routers (those of the hot chiplet included). Four phases of 2000 cycles repeat; **the hot chiplets are the four corner chiplets in the order 0, CX - 1, C - CX, C - 1: chiplets 0, 1, 2, 3 on 2x2; 0, 2, 6, 8 on 3x3; 0, 3, 12, 15 on 4x4**. The table is read with the absolute cycle, reset included, so the measured window (cycles 3000 to 11000) is one whole period: 1000 cycles of the second chiplet, 2000 of the third, 2000 of the fourth, 2000 of the first, and 1000 of the second again |

Round 29 adds three patterns that no earlier round ran (`tornado`, `neighbour`, `randperm` with `random.Random(2901)`;
`results_v29_review/traffic_checks.md`, `randperm_<size>.txt`).

## 3. The ladders

Every scenario (size, traffic pattern, fault mask) has its own nine loads, derived from DeFT_P (`LB/experiments_v25.py`: `sat`,
`coarse_lsat`, `fine_rates`, `points`; the rule of round 23, D1):

1. DeFT_P is run with seed 101 at `pipe_all 2` at the rate 0.0002 (its latency there is L0) and on the coarse grid 0.0005, 0.0010, ...,
   0.0160, then 0.018, 0.020, 0.024.
2. **Lsat = the largest swept rate before the latency first exceeds 3 x L0.** If the coarse Lsat is at most 0.004, the rates are swept
   again on the 0.0001 grid up to the first coarse rate above 3 x L0, and Lsat is read on that grid.
3. **The nine loads are 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0 and 2.4 x Lsat**, each rounded to the grid of the scenario (at least one grid
   step, and strictly increasing: a load that would not exceed the one before it becomes that one plus a grid step).

`results_v25_confirm/load_points_v25.json` holds the ladders of every scenario of rounds 23 to 25. Key
`<size>__<pattern>__<mask>__p<pipe_all>`, for example `2x2__uniform__0x0000__p2`; entry: `lsat`, `eval` (the nine rates; `eval[3]` is
1.0 x Lsat), `grid` (0.0005 or 0.0001), `l0` (cycles), `pipe_all`. It has 53 entries: the ladders at `pipe_all 2` that the paper uses, and
those at `pipe_all 0` of round 23 (the one-cycle router; `chiptrans` exists at `pipe_all 2` only). The fault-free mask is spelled `0x0000`
on 2x2 and `0x0` on 3x3 and 4x4. `results_v25_confirm/load_points_v25.md` shows the 24 scenarios of round 25 with L0, Lsat and the ladder.
The ladders under random faults are in `results_v26_faults/load_points_v26.json` (four loads, 0.5, 1.0, 1.4 and 2.0 x Lsat, per mask and
traffic pattern; key without the pipe depth), those of round 29's three patterns in `results_v29_review/load_points_v29.json`.

## 4. Fault patterns

* **Encoding.** A mask is a hexadecimal number with one digit per chiplet, chiplet 0 last; bit v is VL v, faulty in both directions.
  Within the digit of a chiplet 1 = North, 2 = East, 4 = South, 8 = West. The simulator gets the list of VL ids (`-deft_faulty_vls`,
  `LB/runner.py`, `mask_to_vls`). Every mask of the paper leaves every chiplet at least one functional VL.
* **Round 25** uses the fault-free mask and one mask with the North VL of every chiplet faulty (`0x1111`, `0x111111111`,
  `0x1111111111111111`; `LB/experiments_v5.py`, `NORTH`), and for its fault sweep the first three masks per size and k = 1, 2, 3 faulty VLs
  in every chiplet of `results_v11/masks.json`.
* **Round 26** (`LB/experiments_v26.py`, `draw_part_b`; `results_v26_faults/masks_v26.json`, `masks_v26.md`, `PREREGISTRATION.md`):
  four fault rates, 1/16, 2/16, 4/16 and 8/16 of all VLs, n = floor(rate x number of VLs) faulty VLs (2x2: 1, 2, 4, 8; 3x3: 2, 4, 9, 18;
  4x4: 4, 8, 16, 32). **Per size and rate 16 distinct masks, drawn uniformly among the masks with exactly n faulty VLs and a functional
  VL in every chiplet: rejection sampling with one `random.Random(2611)`**, sizes in the order 2x2, 3x3, 4x4 and within a size the rates
  in ascending order; a candidate is `rnd.sample(range(number of VLs), n)` and is rejected if it was drawn before or takes all four VLs
  of a chiplet. On 2x2 at 1/16 there are exactly 16 masks, and all are taken in VL order without a draw. 192 masks; the file and the
  pre-registration were committed before any run. Each mask gets its own table of DeFT (section 7) and its own ladder (section 3).

## 5. The options of every row

Printed from the drivers themselves (`experiments_v25.row_args`, `experiments_v27_eval.row_args`, `experiments_v28_eval.row_args`,
`experiments_v29_rows.row_args`); the command line of section 1 is put around them. `-deft_lb count_vl 1`, `hop_stats 1` and
`entry_stats 1` only count.

| row | options |
|---|---|
| `DeFT_P` | `-routing DEFT -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -deft_lb count_vl 1` |
| `DeFT_B` | `-routing DEFT -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb count_vl 1` |
| `MTR` | `-routing DEFT_LB -deft_lb exit mtr -deft_lb entry mtr -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_lb vn_rules 0 -deft_lb mtr_table LB/results_v10/mtr_config.json -vc_per_hop 1` |
| `RC` | `-routing DEFT_LB -deft_lb exit near -deft_lb entry near -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_lb vn_rules 0 -deft_lb rc 1 -deft_lb rc_slots 4 -vc_per_hop 1` |
| `XY_SP` | `-routing INTERPOSER_AWARE_XY -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb count_vl 1` |
| `CI_heurLA_X_LF` (**main row**) | `-routing DEFT_LB -deft_lb exit lut -deft_lb entry late -deft_lb chip_tm XY -deft_lb ipos_tm XY -sel DEFT_HEUR -deft_lb heur_w 2 -deft_lb heur_busy 0 -deft_lb heur_lookahead 1 -deft_lb hop_weight_ipos 1 -deft_lb lut_bias D -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb hop_stats 1 -deft_lb lookahead_route 1 -deft_lb lookahead_fallback 1 -deft_lb busy_state 1 -deft_lb decision_delay 0` with **D = 2 on 2x2 and 0 on 3x3 and 4x4** |
| `DeFT_Dis`, `DeFT_Ran` (faults, rounds 25 and 26) | `-routing DEFT_LB -deft_lb exit near -deft_lb entry near` (`Dis`) or `exit ran -deft_lb entry ran` (`Ran`) ` -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb hop_stats 1` |
| `LB_noVLrep` (rounds 27 to 29) | the main row and `-deft_lb up_report 0 -deft_lb entry_stats 1` |
| `EB_vl`, `EB_route`, `EB_vl64` (round 27) | `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle -deft_lb oracle_beta B -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_lb hop_stats 1 [-deft_lb oracle_scope route] [-deft_lb oracle_period 64] -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb entry_stats 1`; B in section 6 |
| `EB_down` (round 27) | the main row and `-deft_lb entry_commit down -deft_lb entry_stats 1` |
| `EB_best` (round 28) | `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle -deft_lb oracle_scope vl -deft_lb oracle_pending 1 -deft_lb oracle_beta B -deft_lb oracle_bias B x T -deft_lb chip_tm XY -deft_lb ipos_tm XY -deft_lb hop_stats 1 -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lb entry_stats 1`; B and T in section 6 |
| `EB_best64` (round 28) | `EB_best` with its own T and `-deft_lb oracle_period 64` |
| `EB_down_t` (round 28) | the main row with `lut_bias 4` on every size and `-deft_lb entry_commit down -deft_lb entry_stats 1` |
| `LB_b0` (round 29) | the main row with `lut_bias 0` (run on 2x2, where it differs) |
| `LB_noLA` (round 29) | the main row with `heur_lookahead 0` |
| `X_d5`, `X_d6`, `X_i7` (round 29; X = `DeFT_P`, `DeFT_B`, `MTR`, `RC`) | row X and `-buffer 5`, `-buffer 6` or `-buffer_ipos 7` |
| `LB_d6` (round 29) | the main row and `-buffer 6` |
| `MTR_static`, `RC_static` (rounds 23 and 29) | `MTR` and `RC` without `-vc_per_hop 1` |
| `EB_first` (round 29) | the main row with its own `lut_bias` (section 6) and `-deft_lb entry_commit first -deft_lb entry_stats 1` |
| `EB_best16`, `EB_best256` (round 29) | `EB_best` with its own T (section 6) and `-deft_lb oracle_period 16` or `256` |

What the options of the VN-based rows mean (`src/ConfigurationManager.cpp`): `-deft_vn_rr 1` DeFT's round-robin VN reassignment at the
Down port, with a counter per router; `-deft_up_keep 1` the Up VL keeps the packet's VN, and VN1 is assigned at the destination boundary
router (Algorithm 1 of the DeFT paper); `-deft_rr_fallback 1` the round-robin takes the other VC when the counter's VC is held or full;
`-deft_lut_entry dst` the entry VL of the table is keyed by the destination router (section 7).

## 6. The tuned values

Every tuning uses the rule of round 24 (`LB/experiments_v24_eval.py`): sizes 2x2 and 4x4 (3x3 takes the values of 4x4), five scenarios, the
loads 0.5, 1.0, 1.4 and 2.0 x Lsat, seeds 101 and 102; score of a configuration = the mean over scenarios and seeds of
ln(THR / THR of DeFT_P) - ln(LAT at 1.0 x Lsat / DeFT_P's) - ln(LAT at 0.5 x Lsat / DeFT_P's).

| row | parameter | 2x2 | 3x3 | 4x4 | file |
|---|---|---|---|---|---|
| main row | `heur_w` W, `heur_busy` B, `hop_weight_ipos` G, `lut_bias` D | 2, 0, 1, **2** | 2, 0, 1, **0** | 2, 0, 1, **0** | `results_v24_xy/tuning_choice.json`, `[size]["X"]["heur"]` |
| `EB_vl` | `oracle_beta` | 0.5 | 1 | 1 | `results_v27_early/tuning_choice_v27.json` |
| `EB_route` | `oracle_beta` | 2 | 4 | 4 | the same |
| `EB_vl64` | `oracle_beta` | 0.25 | 1 | 1 | the same |
| `EB_best` | scope S, pending P, `oracle_beta` B, threshold T (`oracle_bias` = B x T) | vl, 1, 0.5, 8 (bias 4) | vl, 1, 1, 2 (bias 2) | vl, 1, 1, 2 (bias 2) | `results_v28_anchor/tuning_choice_v28.json` |
| `EB_best64` | S, P, B of `EB_best`; T | 32 (bias 16) | 16 (bias 16) | 16 (bias 16) | the same |
| `EB_down_t` | `lut_bias` D | 4 | 4 | 4 | the same |
| `EB_first` | `lut_bias` D | see `results_v29_review/tuning_v29.md` | | | `results_v29_review/tuning_choice_v29.json` |
| `EB_best16`, `EB_best256` | S, P, B of `EB_best`; T | see `results_v29_review/tuning_v29.md` | | | the same |

* The main row's grid was W in {1, 2} x B in {0, 4} x G in {1, 2} x D in {0, 2, 4}; among the configurations within 0.02 of the best
  score the rule prefers D = 0, then G = 1, then B = 0, then W = 1. `heur_lookahead 1` is part of the row's definition, not tuned. The
  tuning ran the candidates with an ideal decision (`decision_delay 0`, no lookahead routing); the frozen row runs with lookahead routing
  and the fallback.
* The early family of round 28: the source binds the entry VL e of least hops(e) + B x (occupancy near e + P x flits of packets already
  bound to e) + B x T if e is not DeFT_P's entry VL. S = `vl`: the occupancy of the input buffers around the VL; S = `route`: of the buffers
  on the packet's path. With a period, the occupancies are those sampled at the last multiple of the period.
* What the parameters of the main row are in the simulator (`src/DeftLateBinding.cpp`, `selectHeuristic`, `bestContinuation`): the cost of
  an offered output o is `heur_w` x the fill of the buffer behind o (+ `heur_busy` if its VC is held by another packet) + 1 + the least,
  over the outputs z that the next router would offer, of (`heur_w` x the fill of the buffer behind z + the hops left after z)
  (`heur_lookahead 1`; with `heur_lookahead 0` the cost is `heur_w` x the fill behind o + the hops left after o) + `lut_bias` if the move
  drops DeFT_P's entry VL from the candidates while it is still among them. A hop on the interposer counts `hop_weight_ipos`. The least
  cost wins, ties at random. With `up_report 0` the fill behind z is not read when o is the Up link.

## 7. DeFT's tables

* **Generator** `other/deft_vl_lut_generator.py`, called once per size and mask by `LB/experiments_v23.py` (`_gen`; stage `luts`, and
  `LB/experiments_v26.py luts` for the masks of round 26):
  `--chiplets-x C --chiplets-y C --rho <rho> --fault-mask <mask> --entry-model both --output LB/luts/v23/lut_<size>_<mask>.yaml`.
* **Traffic assumed:** one unit of demand between every pair of routers of different chiplets (`traffic_assumption:
  uniform_unit_interchiplet_demand` in the table), whatever traffic pattern the run then uses. No `--demand-table` is given.
* **rho per size: 0.01 on 2x2, 0.01 on 3x3, 0.001 on 4x4** (`results_v5/tuning_choice.json`, the entry `DeFT`; chosen in round 5 by the
  geometric-mean latency among 0.01, 0.003, 0.001, 0.0003, 0.0001 and 0).
* **Objective**, per chiplet: assign every demand point to one functional VL of the chiplet so that
  rho x (sum of the Manhattan distances) + (sum over the VLs of |load - mean load| / mean load) is least. A larger rho favours the nearest
  VL; rho = 0 only balances.
  * **Exit selection** (`entries[...].source_exit`): the demand points are the 16 routers of the source chiplet, the distance is from the
    router to the VL inside the chiplet. Exact dynamic programme.
  * **Entry selection by the destination router** (`entries_by_destination`, the second selection of the DeFT paper): the same problem
    for the destination chiplet with its own 16 routers. Exact dynamic programme. **`DeFT_P` uses it (`-deft_lut_entry dst`).**
  * **Entry selection by the source router** (`entries[...].destination_entry`, the entry of rounds 1 to 21): the demand points are all
    routers of the other chiplets, each placed at the exit VL chosen for it, and the distance is the interposer distance from there to
    the entry VL. 48 points on 2x2 (dynamic programme), 128 and 240 on 3x3 and 4x4 (the same objective as a mixed-integer programme,
    solved exactly). **`DeFT_B` uses it.**
  * Ties: the least total, then the least imbalance, then the least distance, then the smallest tuple of VL ids.
* Both rows read the same file; the exit VL is the same for both. The late-binding rows take the exit VL from the table and, through
  `lut_bias`, DeFT_P's entry VL as the default one.
* **rho = 0.01 against rho = 0.001 on 4x4** (`LB/lut_rho_v29.py`, `results_v29_review/lut_rho_4x4.md`, `.csv`; computed for this file).
  For the fault-free mask, the mask with one faulty VL per chiplet and the 64 masks of round 26, the tables were generated with both
  values and compared entry by entry.
  * Without faults every router has its nearest VL as exit VL and, for DeFT_P, as entry VL, on every size (no router has two nearest
    VLs, and the four VLs of a chiplet get four routers each), so rho plays no part.
  * **DeFT_P's tables (exit, and entry by the destination router) are the same for both values of rho on all 66 masks**, the masks with
    faults included: 0 of 3,840 exit entries and 0 of 256 entry entries differ on any mask.
  * DeFT_B's entry by the source router differs on all 66 masks (491 to 1,487 of its 3,840 entries).
  * The tables generated again with rho = 0.001 have the selections of the tables that the runs used (66 of 66).

## 8. The VC policy of MTR and RC

Both run without DeFT's VN rules (`-deft_lb vn_rules 0`), on fault-free scenarios only (with faults they cannot deliver every pair,
`results_v26_faults/reachability_v26.md`).

* **Without `-vc_per_hop`** (`MTR_static`, `RC_static`): the processing element draws the VC of a packet uniformly at injection and the
  packet keeps it on every hop (`src/ProcessingElement.cpp`, `src/DeftVirtualNetwork.cpp`).
* **With `-vc_per_hop 1`** (`MTR`, `RC`: the rows of the paper since round 23): at every hop the head tries the VCs of the chosen output in
  round-robin order from a pointer of that output and takes the first free one; the pointer moves past the VC taken (`src/Router.cpp`,
  reservation phase). In RC's buffer on the Up link the head takes any free Up-link VC in round-robin order. With the VN rules on, the
  option does nothing.
* **`rc_slots 4`**: the RC buffer of a boundary router has four FIFOs of one packet (8 flits) each, and a boundary router hands out at
  most four injection permissions at a time; a permission is released when the tail leaves the buffer. Round 29 keeps 4 when the input
  buffers are deeper.

## 9. The fallback of the main row: the order of the offered outputs

With lookahead routing the router that forwards a head computes the decision for the next router and stores it in the head. At a hop
that offers more than one output, a head that holds no output yet asks every cycle (`src/Router.cpp`, `Router::selectionFunction`):

1. for the stored output, if it is free;
2. otherwise for **the first other offered output that is free, in the order vertical link, North, East, South, West**;
3. otherwise for the stored output again.

A head that already holds an output keeps it. "Free": the output VC the head would get is not held by another packet and the downstream
buffer of that VC is not full. The order is the order in which the routing function lists the outputs (`DeftLB::legalMoves`: the
vertical link first, then the horizontal moves by direction index). The RTL has the same order (`results_v25_confirm/hw/rtl/lb25_units.v`,
module `lb25_fallback`; there the vertical link is output 4, in the simulator 5).

## 10. Which script writes which table of `paper_data/`

Every report script reads the per-run CSVs of its results folder and writes `paper_data/`; nothing there is edited by hand. Each script
takes its results folder from an environment variable if set (`V25_RES` ... `V29_RES`).

| folder | file | script (part) | content |
|---|---|---|---|
| `results_v25_confirm/paper_data` | `effects_per_size.csv`, `effects_per_scenario.csv`, `absolute_values.csv` | `report_v25.py` (b) | the frozen rows against the best reference and each reference: per size, per scenario; means and intervals of THR, LAT, P99 |
| | `latency_load_<size>_<scenario>.csv` (2x2 and 4x4; uniform, hotspot, chipperm, chiptrans, uniform with faults) | `report_v25.py` (b, `curves`) | latency, P99 and accepted throughput of every row at the nine loads |
| | `fault_sweep.csv` | `report_v25.py` (c) | k = 1, 2, 3 faulty VLs per chiplet |
| | `apps.csv` | `report_v25.py` (d) | application traces relative to DeFT_P |
| | `pipe0_effects.csv` | `report_v25.py` (e) | the one-cycle router (`pipe_all 0`) |
| | `addendum_effects.csv`, `addendum_latency_load.csv` | `report_v25.py` (a) | the addendum row with one residual cycle |
| | `hw_area.csv`, `hw_system_area.csv`, `hw_timing.csv`, `hw_paths.csv` | `report_v25_hw.py` | area per router and per system, the stages of the decision path, the other paths |
| `results_v26_faults/paper_data` | `fault_rate_effects.csv`, `fault_rate_per_mask.csv` | `report_v26.py` (b) | random VL faults at four rates: effects per size and rate, and per mask |
| | `formal_summary.csv` | `report_v26.py` (a) | the model check per size and set of masks |
| | `reachability_v26.csv` | `reach_v26.py` (copied by `report_v26.py`) | the pairs MTR and RC can deliver under faults |
| `results_v27_early/paper_data` | `latency_by_load_v25.csv` | `report_v27.py` (d) | latency of the main row and the references at each load |
| | `early_late_effects.csv`, `early_late_per_scenario.csv` | `report_v27.py` (c) | the early rows against DeFT_P and the main row |
| | `early_late_faults.csv` | `report_v27.py` (e) | the same under faults at the rate 4/16 |
| | `tuning_v27.csv` | `report_v27.py` (b) | the score of every `oracle_beta` |
| `results_v28_anchor/paper_data` | `tuning_v28.csv` | `experiments_v28.py b_choose` | the score of every configuration of the early family |
| | `early_best_effects.csv`, `early_best_per_scenario.csv` | `report_v28.py` (c) | `EB_best`, `EB_best64`, `EB_down_t` against DeFT_P and the main row; the share of the main row's gain |
| | `early_best_faults.csv`, `early_best_faults_shares.csv` | `report_v28.py` (d) | the same under faults |
| | `novlrep_faults.csv` | `report_v28.py` (e) | `LB_noVLrep` against the main row under faults |
| `results_v29_review/paper_data` | `heldout_effects.csv`, `lb_b0.csv` | `report_v29.py` (b) | the three held-out scenarios; `lut_bias 0` on 2x2 |
| | `equal_area_effects.csv`, `equal_area_faults.csv` | `report_v29.py` (c) | the main row against references with deeper buffers, with the measured area ratio of each set |
| | `vc_policy.csv`, `deft_paper_setup.csv` | `report_v29.py` (d) | one VC per packet for MTR and RC; the set-up of the DeFT paper |
| | `nola_effects.csv` | `report_v29.py` (e) | the main row without the lookahead term |
| | `early_more.csv` | `report_v29.py` (f) | `EB_first` and the age of the source's knowledge |
| | `apps_loaded.csv` | `report_v29.py` (g) | the application traces of round 25 with `-netrace_compress S` (S per trace: the smallest of 2, 4, 8, 16, 32 at which DeFT_P's mean latency is 1.5 times its latency at S = 1), relative to DeFT_P |
| | `hw_variants.csv` | `report_v29_hw.py` | area, timing, link budget and power of DeFT, the main row and its two variants |

The independent second computation of the tested families is `check_v25_families.py`, `check_v26_family.py`, `check_v27_family.py`,
`check_v28_family.py` and `check_v29_family.py`; each writes `report/families_check.md` (or the file its header names) in its folder.
