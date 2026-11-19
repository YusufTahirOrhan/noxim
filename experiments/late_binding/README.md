# DEFT_LB experiments: directions A, B and C

Code: `src/DeftLateBinding.{h,cpp}`, routing `DEFT_LB`, selections `DEFT_HEUR`, `DEFT_QL`.

## What is compared

| Variant | Direction | Routing relation | VL decision | Information used |
|---|---|---|---|---|
| `DeFT` | baseline | DeFT (XY, fixed pair) | offline LUT (rho = 0.01) | none at run time |
| `A_mindist` | A | DeFT (XY, fixed pair) | at injection: minimal total hops | static distance |
| `A_random` | A | DeFT (XY, fixed pair) | at injection: uniform random pair | none |
| `A_oracle` | A (upper bound) | DeFT (XY, fixed pair) | at injection: hops + beta * occupancy near both VLs | instantaneous global state (not implementable) |
| `CI_random` | control | interposer-only late binding (chiplets XY, exit from LUT, interposer OE) | random among legal outputs | none |
| `CI_heur` | C | same as CI | stateless heuristic | router-local |
| `CI_ql` | B | same as CI | Q-learning | router-local + learned residual |
| `FULL_random` | control | full late binding (OE on chiplets and interposer) | random | none |
| `FULL_heur` | C | full late binding | stateless heuristic | router-local |
| `FULL_heurLA` | C (wider budget) | full late binding | heuristic with one-hop lookahead | router-local + neighbour's downstream occupancy |
| `FULL_ql` | B | full late binding | Q-learning | router-local + learned residual |

### Boundaries of the heuristic (direction C)

A heuristic here is a fixed, stateless rule:
* it uses only what the router observes in the current cycle: for each legal output,
  the number of flits in the downstream input buffer of the output VC (what a credit
  counter reports) and whether the output VC is held by another packet;
* it adds static topology knowledge: the minimal remaining hop count after the move
  (towards the best remaining exit/entry candidate);
* cost(o) = heur_w * downstream_flits(o) + heur_busy * [output VC busy] + hops_after(o);
  the minimum wins, ties are broken at random;
* no memory, no learning, no global or remote information; the two weights are chosen
  once on tuning seeds (101, 102) from a 3x3 grid and frozen.
`FULL_heurLA` widens the budget by one hop (the neighbour's downstream occupancy on its
cheapest continuation) to show what more information buys without learning.

### Q-learning (direction B)

cost(o) = ql_w * downstream_flits(o) + ql_busy * [busy] + hop_cost * hops_after(o) + R(o).
R is a learned residual (time beyond the static hop estimate), kept per router, output
port and destination chiplet (`ql_key 1`) or destination router (`ql_key 0`). When a head
flit reaches the front of an input buffer, the router that sent it updates
R <- R + alpha * (1 + V_here - hop_cost * hops_after - R), where V_here is the receiving
router's minimum cost over its legal outputs (TD(0), observed local costs as step costs).
With alpha = 0 the learner is exactly the heuristic (checked: identical runs). The local
weights are set to the heuristic's tuned values, so B and C differ only by learning.
Safety does not depend on the selection: both choose only among legal outputs of the
routing relation.

### Safety evidence
* `formal/impl_relation_check.py`: model check of the implemented relations (fixed pair,
  CI, FULL) on 897 fault masks (CDG acyclic, no dead ends, no livelock).
* `drain_tests.py`: drain-mode runs for every variant (all-pairs burst on 11 masks x 2
  seeds, over-saturated random tables on 4 masks): every packet delivered, no dead ends.

## Tuning budget (seeds 101, 102 only; never used for evaluation)

Each configuration is run on 4 cells (uniform, hotspot, chipperm on the fault-free
network, uniform on 0x1111) x 2 loads (~0.8 and ~1.1 x DeFT Lsat, `results/load_points.json`)
x 2 seeds = 16 runs. Selection criterion: geometric mean of the mean packet latency over
those 16 runs (`choose_tuning.py`; tables in `results/tuning_*.txt`).

| Method | Parameters searched | Configurations | Runs | Chosen |
|---|---|---|---|---|
| DeFT | none (LUT with the default rho = 0.01) | 0 | 0 | - |
| A_mindist, A_random | none | 0 | 0 | - |
| A_oracle | oracle_beta in {0.25, 0.5, 1, 2} | 4 | 64 | beta = 0.5 |
| CI/FULL_random | none | 0 | 0 | - |
| C: FULL_heur (CI_heur, FULL_heurLA reuse it) | heur_w in {0.5, 1, 2} x heur_busy in {0, 4, 8} | 9 | 144 | w = 1.0, busy = 0.0 |
| B: FULL_ql (CI_ql reuses it) | ql_alpha in {0.05, 0.2, 0.5} x ql_key in {0, 1} x ql_eps in {0, 0.05}, local weights fixed to C's choice | 12 (+9 inherited) | 192 (+144) | alpha = 0.05, key = 1 (destination chiplet), eps = 0 |

Notes:
* B received more tuning than C: its own 12 configurations on top of the 9 that fixed
  its local weights. Any B-over-C gain must be read with this asymmetry in mind.
* All tuning was done on FULL and applied unchanged to CI (and to FULL_heurLA).
* The chosen ql_alpha (0.05) is the smallest value of its grid, so a smaller rate may be
  better; the grid was not extended, to keep the budget fixed in advance.
* The heuristic ranking is flat at the top (the four best configurations lie within 3 %
  of each other in geometric-mean latency), so its choice is weakly determined.
* The drain tests were re-run with the frozen parameters
  (`results/drain_summary.csv`; the pre-tuning run is kept as `drain_summary_pretuning.csv`).

## Reproduce
```
python3 gen_traffic.py traffic
mkdir -p luts && python3 ../../other/deft_vl_lut_generator.py $(sed 's/^/--fault-mask /' drain_masks.txt) --output luts/lut_rho001.yaml
python3 formal/impl_relation_check.py all 2
python3 drain_tests.py 2
python3 experiments.py sat 2  && python3 analyze.py sat   # then choose load points (results/load_points.json)
python3 experiments.py tune 2 && python3 choose_tuning.py heur && python3 experiments.py tune_ql 2 && python3 choose_tuning.py ql && python3 analyze.py tune
python3 experiments.py eval 2 && python3 analyze.py eval
python3 experiments.py eval_vl 2 && python3 report_eval.py   # figures, paired differences, summary.md
```

## Results
`results/eval_report/FINDINGS.md` (read its caveats first; 5 seeds, preliminary),
`results/eval_report/summary.md`, the latency curves `latency_<pattern>_<mask>.png` and
`saturation.png`. Safety: `results/impl_relation_check_all.txt`, `results/drain_summary.csv`.
Plain DEFT routing does not count VL usage, so DeFT's VL counts come from `eval_vl`
(DEFT_LB with the LUT pairs, exit and entry). Its traffic statistics are identical to
DeFT's: all 385 runs give the same latency, p99 and packet counts; only the energy
model differs.

## Second evaluation (results_v2/)
Traffic-matched DeFT baseline (DeFT_tm), information-matched learners (ql_lookahead), per-scope
tuning, per-scenario load points, 10 seeds, pre-registered primary analysis (Holm), HL-fault
coverage and hardware-cost estimates. Start with `results_v2/FINDINGS.md`; the decisions taken
without the author are in `results_v2/DECISIONS.md`.
```
python3 gen_traffic.py traffic half                       # 0.0005-grid tables
python3 ../../other/deft_vl_lut_generator.py $(sed 's/^/--fault-mask /' drain_masks.txt) \
    --demand-table traffic/<pattern>_0.0100.txt --output luts/lut_rho001_tm_<pattern>.yaml
python3 check_lut_tm.py && python3 check_qlla.py BIN_BEFORE BIN_AFTER
python3 experiments_v2.py sat 11 && python3 experiments_v2.py points
python3 experiments_v2.py tune 11 && python3 experiments_v2.py choose_tune
python3 experiments_v2.py tune_ql 11 && python3 experiments_v2.py choose_tune_ql   # then freeze variants_v2.py
python3 experiments_v2.py drain 11 && python3 experiments_v2.py timing 11
python3 experiments_v2.py eval 11 all && python3 experiments_v2.py evalvl 11 all && python3 report_v2.py
(cd formal && python3 impl_relation_check.py hl 4 ../results_v2/hl_coverage.md)
```

## Third round (results_v3/)
Confirmatory near-saturation latency test on new seeds 11-20 (pre-registered), window
sensitivity, exploratory tuning beyond the v2 grid edges, per-run CSVs, and HL-fault exists-path /
fault-aware-pruning coverage. Start with `results_v3/FINDINGS.md`.
```
python3 make_eval_csv.py results_v2 eval && python3 primary_from_csv.py
python3 experiments_v3.py confirm 11 && python3 experiments_v3.py window 11 && python3 experiments_v3.py tunex 11
python3 make_eval_csv.py results_v3 confirm && python3 make_eval_csv.py results_v3 window
python3 report_v3.py && python3 report_tunex.py
(cd formal && python3 impl_relation_check.py hl3 11 ../results_v3/hl_coverage_v3.md ../results_v2/hl_coverage.csv)
```

## Fourth round (results_v4/, branch feat/parametric-topology)
Parametric DEFT_2_5D topology (Noxim -deft_chiplets_x/-y, -deft_chiplet_w/-h; default 2x2 of 4x4
unchanged, regression in results_v4/regression.md) and a pre-registered replication on 3x3 and 4x4
chiplets. Start with `results_v4/FINDINGS.md`.
```
python3 gen_traffic.py traffic_3x3 --chiplets 3 3 --upto 0.024   (and 'half'; same for 4x4)
python3 ../../other/deft_vl_lut_generator.py --chiplets-x 3 --chiplets-y 3 --fault-mask 0x0 \
    --fault-mask 0x111111111 [--demand-table traffic_3x3/<pattern>_0.0100.txt] --output luts/lut_3x3_rho001[_tm_<pattern>].yaml
python3 check_param_regression.py BIN_OLD BIN_NEW && python3 check_lut_milp.py
(cd formal && python3 impl_relation_check.py size 3 3 4 ../results_v4/formal_sizes.md 20 && \
              python3 impl_relation_check.py size 4 4 3 ../results_v4/formal_sizes.md 0 lean)
python3 experiments_v4.py drain 6 && python3 experiments_v4.py sat 10 && python3 experiments_v4.py points_coarse
python3 experiments_v4.py satfine 10 && python3 experiments_v4.py points && python3 experiments_v4.py tables
python3 experiments_v4.py timing 10 && python3 experiments_v4.py eval 10 all && python3 experiments_v4.py evalvl 10 all
python3 make_eval_csv.py results_v4 eval && python3 report_v4.py && python3 sensitivity_v4.py
```

## Fifth round (results_v5/): tuned DeFT baseline
The DeFT LUT weight rho is tuned per size (seeds 101/102, same protocol as the other methods), and
the size results are re-tested against DeFT_tm(rho*) on new seeds 21-30. Start with
`results_v5/FINDINGS.md`.
```
python3 lut_scaling.py
python3 experiments_v5.py luts 8 && python3 experiments_v5.py tune 10 && python3 experiments_v5.py choose
python3 experiments_v5.py sat 10 && python3 experiments_v5.py satfine 10 && python3 experiments_v5.py points
python3 experiments_v5.py drain 6 && python3 experiments_v5.py timing 10
python3 experiments_v5.py eval 10 all && python3 experiments_v5.py evalvl 10 all
python3 make_eval_csv.py results_v5 eval && python3 report_v5.py
```

## Sixth round (results_v6/): bottleneck diagnosis and per-size tuning of the proposed methods
Optional statistics (`-deft_lb stats_file PATH`, off by default; regression in results_v6/stats_regression.md),
the 4x4 bottleneck diagnosis, per-size tuning of CI_heurLA/FULL_heurLA/CI_qlLA/FULL_qlLA, and a pre-registered
re-test on 3x3/4x4 against DeFT_tm(rho*), seeds 31-40. Start with `results_v6/FINDINGS.md`.
```
python3 check_stats_regression.py BIN_OLD BIN_NEW
python3 bottleneck_v6.py run 12 && python3 bottleneck_v6.py analyze cleanup
python3 experiments_v6.py tune_heur 12 && python3 experiments_v6.py extend 12 && python3 experiments_v6.py choose_heur
python3 experiments_v6.py tune_ql 12 && python3 experiments_v6.py choose_ql && python3 experiments_v6.py alpha0 12
python3 experiments_v6.py drain 12 && python3 experiments_v6.py timing 12
python3 experiments_v6.py eval 12 all && python3 experiments_v6.py evalvl 12 all
python3 make_eval_csv.py results_v6 eval && python3 report_v6.py
```

## Seventh round (results_v7/): bounded-deviation entry for CI
Optional bound on CI's (and FULL's) entry candidates at injection (`-deft_lb entry_bound_mode off|min|lut`,
`-deft_lb entry_bound_k K`; off by default; regression in results_v7/regression.md), selection on 4x4, bottleneck
statistics with the tuned and bounded variants, and a pre-registered test on 3x3/4x4 against DeFT_tm(rho*) and the
unbounded parents, seeds 31-40 (reference and parent runs reused from v6). Start with `results_v7/FINDINGS.md`.
```
python3 formal/impl_relation_check.py size 3 3 6 results_v7/formal_bounded.md 4 lean bounded
python3 experiments_v7.py regress 12 BIN_V6 && python3 experiments_v7.py determinism 12
python3 experiments_v7.py select 12 && python3 experiments_v7.py choose
python3 bottleneck_v7.py run 12 && python3 bottleneck_v7.py analyze cleanup
python3 experiments_v7.py drain 12 && python3 experiments_v7.py timing 12
python3 experiments_v7.py eval 12 all && python3 experiments_v7.py vlref 12 && python3 experiments_v7.py evalcand
python3 make_eval_csv.py results_v7 eval && python3 make_eval_csv.py results_v7 vlref && python3 report_v7.py
```

## Eighth round (results_v8/): plain DeFT(rho*) reference and the layer-weighted hop cost
Step 1 compares the v6-tuned variants with plain DeFT(rho*) (uniform LUT for every pattern) on seeds 31-40. Steps 2-5
add `-deft_lb hop_weight_ipos GAMMA` (default 1.0; weight of a horizontal interposer hop in the selection's static
remaining-path cost; regression in results_v8/regression.md), select gamma on 4x4 and test CI_heurLA_G, CI_qlLA_G,
FULL_qlLA_G against DeFT_tm(rho*) and their gamma = 1 parents. Start with `results_v8/FINDINGS.md`.
```
python3 experiments_v8.py deft 12 && python3 make_eval_csv.py results_v8 deft && python3 report_v8_step1.py
python3 experiments_v8.py regress 12 BIN_V7 && python3 experiments_v8.py alpha0 12
python3 experiments_v8.py select 12 && python3 experiments_v8.py choose 12
python3 bottleneck_v8.py run 12 && python3 bottleneck_v8.py analyze cleanup
python3 experiments_v8.py drain 12 && python3 experiments_v8.py timing 12
python3 experiments_v8.py eval 12 all && python3 experiments_v8.py vlref 12
python3 make_eval_csv.py results_v8 eval && python3 make_eval_csv.py results_v8 vlref && python3 report_v8.py
```

## Ninth round (results_v9/): confirmatory test of gamma = 2 against plain DeFT(rho*)
Frozen design on 2x2/3x3/4x4, new seeds 41-50 (chosen by a pre-registered timing rule), no tuning, no C++ change.
Start with `results_v9/FINDINGS.md`.
```
python3 experiments_v9.py drain 12 && python3 experiments_v9.py timing 12
python3 experiments_v9.py eval 12 all
python3 make_eval_csv.py results_v9 eval && python3 report_v9.py
```

## Rounds 10-13 (results_v10/, results_v11/, results_v12_energy/, results_v13_apps/): baselines, faults, energy, applications
New simulator options, all off by default. With the defaults, the regression set is byte-identical
(`results_v10/regression.md`, `results_v11/regression.md`).
* **DEFT_LB injection policies:**
  - `near` (DeFT-Dis, RC);
  - `ran` (DeFT-Ran, separate RNG);
  - `mtr` with `-deft_lb mtr_table PATH` (MTR; tables from `formal/mtr_search.py`).
* **Baseline mechanisms:**
  - `-deft_lb vn_rules 0`: DeFT's VN rules off (MTR, RC);
  - `-deft_lb rc 1 rc_slots N`: RC buffer and injection permission.
* `-deft_lb count_vl 1`: VL counts for plain DEFT.
* `-netrace FILE -netrace_window CYCLES -netrace_deps 0|1`: Netrace-driven traffic, from packet lists cut by
  `netrace/netrace_cut`.
* `runner.py` accepts `--shard i/n` (deterministic partition); `merge_csv.py` merges per-shard CSVs.
```
python3 formal/mtr_search.py results_v10 && python3 formal/mtr_cdg_check.py results_v10/mtr_config.json results_v10/mtr_cdg_check.md
python3 experiments_v10.py regress 12 BIN_V9 && python3 experiments_v10.py reuse 12 && python3 experiments_v10.py drain 12
python3 experiments_v10.py sanity 12 && python3 sanity_diag_v10.py 12 && python3 reach_v10.py
python3 experiments_v10.py timing 12 && python3 experiments_v10.py eval 12
python3 make_eval_csv.py results_v10 eval && python3 report_v10.py
python3 experiments_v11.py regress 12 BIN_V10 && python3 experiments_v11.py luttime 3 && python3 experiments_v11.py luts 12
python3 experiments_v11.py drain 12 && python3 experiments_v11.py timing 12 && python3 experiments_v11.py eval 12
python3 make_eval_csv.py results_v11 eval && python3 report_v11.py
python3 experiments_v12.py energy 12 && python3 cost_v12.py
curl -sL https://www.cs.utexas.edu/~netrace/download/TRACE.tra.bz2 | netrace/netrace_cut - 2 1000000000 3000000 WINDOWS/TRACE_r2.txt
python3 experiments_v13.py timing 12 && python3 experiments_v13.py eval 12 && python3 experiments_v13.py csv && python3 report_v13.py
```
Start with `results_v10/FINDINGS.md` (Parts A-B), `results_v11/FINDINGS.md` (Part C), `results_v12_energy/FINDINGS.md`
(Part D) and `results_v13_apps/FINDINGS.md` (Part E).

## Rounds 14-16 (results_v14_faultload/, results_v15_apps2/, results_v16_qbits/): faults below saturation, two applications, Q-table width
New simulator options, all off by default. With the defaults, the 84-configuration regression set is byte-identical
(`results_v15_apps2/regression.md`: whole stats files compared).
* **Second trace:** `-netrace2 FILE` overlays a second Netrace window. It has its own dependency tracking on all 64
  nodes and shares the network and NI queues with the first.
* **Compression:** `-netrace_compress S` divides the trace timestamps by S. Dependencies are still enforced, and the
  post-dependency delay stays 8 cycles.
* **Fixed-point Q table:** `-deft_lb ql_bits B ql_frac F`: signed B-bit residuals with F fractional bits, rounded to
  nearest and saturating (0 = float32).
* **Residual range:** `-deft_lb ql_range 1` logs it as extra JSON fields.
```
python3 experiments_v14.py choose && python3 experiments_v14.py timing 12 && python3 experiments_v14.py eval 12
python3 make_eval_csv.py results_v14_faultload eval && python3 report_v14.py
python3 experiments_v15.py regress 12 BIN_V14 && python3 experiments_v15.py v13check
python3 experiments_v15.py timing 12 && python3 experiments_v15.py eval 12 && python3 experiments_v15.py csv && python3 report_v15.py
python3 experiments_v16.py range 12 && python3 experiments_v16.py reuse 12 && python3 experiments_v16.py eval 12
python3 experiments_v16.py qlstats && python3 make_eval_csv.py results_v16_qbits eval && python3 report_v16.py && python3 explore_v16.py
```

### v14 (Part F): fault sweep below the faulty saturation point
* **Test load:** for each (size, k, pattern), the highest v11 load at which DeFT(rho*) stays within 3x its zero-load
  latency. This is 0.2-1.0x the fault-free Lsat.
* **Primary (Holm over 18; seeds 53-57): 15 / 18 supported, none against.** CI_qlLA_G and FULL_qlLA_G lower mean latency
  by 9-20 % at k = 1-2 and by 2-5 % at k = 3 on 3x3 and 4x4.
* **Not supported:**
  - 2x2 at k = 3 (both variants), where one VL per chiplet leaves no choice;
  - FULL_qlLA_G on 2x2 at k = 2 (-2.1 %).
* **P99:** -25 to -39 % at k = 1-2 on 3x3 and 4x4.

### v15 (Part G): two PARSEC applications at once
* **Setup:** 6 pairs of the four heaviest benchmarks, s = 1 and 2, 648 runs; every run delivered both windows.
* **Latency:** FULL_qlLA_G has the lowest geometric-mean latency in every setting: -7 % fault-free and -10 to -11 % with
  0x1111. Its p99 with 0x1111 is 0.65-0.73 of DeFT(rho*).
* **Completion time:**
  - s = 1: identical across methods (within 0.2 %).
  - s = 2: differs. FULL_qlLA_G is 3.6-4.3 % faster, and DeFT-Ran 4-6 % slower.

### v16 (Part H): Q-table entry width
* **Pre-registered equivalence** (LAT +-3 %, P99 +-5 %, THR +-1 %, 5 seeds): **no tested width (16, 12, 8) is equivalent
  everywhere.**
  - At 16 and 12 bits the point estimates are mostly within the margins. The CIs are too wide: latency at 1.0x Lsat
    under hotspot and movinghot is very seed-sensitive.
* **8 bits:** learning stalls. FULL_qlLA_G changes 0 % of the stored values, and CI_qlLA_G 5-11 %.
  - CI_qlLA_G loses 2 % throughput on 3x3 and 4x4.
  - FULL_qlLA_G's latency is +7 % on 4x4.
* **Cost table:** keeps 16 bits.

Start with `results_v14_faultload/FINDINGS.md`, `results_v15_apps2/FINDINGS.md` and `results_v16_qbits/FINDINGS.md`.

## Rounds 17-18 (results_v17_vcdiag/, results_v18_area/): VC usage and area / timing
New simulator option, off by default. With the default, the 84-configuration regression set is byte-identical to the 3ac1bae build (`results_v17_vcdiag/regression.md`):
* `-deft_lb vc_stats FILE`: per link direction and VC, flits forwarded, head-flit cycles waiting for that VC (held or no credit), mean downstream occupancy, flits by packet phase; RC buffer occupancy and the measured permission wait. Own output file, the stats file stays the same (`oncheck.md`).

Tools for round 18 (no root; versions in `results_v18_area/tools.md`): Yosys + ABC and Icarus Verilog from OSS CAD Suite, OpenSTA built from source, NanGate45 typical from OpenROAD-flow-scripts, all under `~/eda`.
```
python3 experiments_v17.py regress 12 BIN_3AC1BAE && python3 experiments_v17.py oncheck 10
python3 experiments_v17.py run 12 && python3 experiments_v17.py csv && python3 report_v17.py
bash results_v18_area/rtl/tb/run_vectors.sh 20000 && bash results_v18_area/rtl/tb/mutation_check.sh && bash results_v18_area/rtl/tb/run_router_smoke.sh
python3 synth_v18.py tools && python3 synth_v18.py hier 10 && python3 synth_v18.py flat 10
python3 synth_v18.py pipe 10 && python3 synth_v18.py relax 10 && python3 synth_v18.py csv && python3 report_v18.py
```

### v17 (Part I): VC usage per link (descriptive, 270 runs)
* **The VN rules cause the imbalance.** VC imbalance over chiplet links at 1.0 x Lsat: DeFT(rho*) 0.66-0.82, LB-I 0.67-0.86, LB-F 0.47-0.73, MTR and RC 0.10-0.22; MTR's routes with DeFT's VN rules 0.74-0.94.
* **The explanation needed two corrections:**
  - The largest split is off the chiplets: interposer and Down VL 87:13 (LB-F 100:0), Up VL 0:100, against 50:50 for MTR and RC. A packet in VN0 keeps it across the interposer.
  - "Towards VL = VC0" holds only for routes to the nearest VL (89-98 %). It is 67-76 % for DeFT, and LB-F's links away from a VL are nearly balanced.
* **The wait shows at the VLs,** mostly as "VC held": on MTR's routes the rules raise the Down VL wait by 1.8-2.6 times and the Up VL wait by 1.8-1.9 times.
* **Imbalance alone does not predict latency:** LB-I and LB-F have DeFT-like or lower imbalance and the lowest latency. This round does not measure saturation throughput.

### v18 (Part J): area and timing, NanGate45 (pre-layout, flip-flop storage, 156 designs)
* **Functional check:** 1,011,642 vectors from the simulator's own code, 0 mismatches.
* **System-level router area relative to DeFT (2x2 / 3x3 / 4x4):**

  | method | hierarchical | flat |
  |---|---|---|
  | LB-I heuristic | 1.17 / 1.17 / 1.17 | 1.09 / 1.11 / 1.11 |
  | LB-I Q-learning | 1.38 / 1.47 / 1.63 | 1.28 / 1.38 / 1.51 |
  | LB-F heuristic | 1.39 / 1.39 / 1.39 | 1.23 / 1.25 / 1.25 |
  | LB-F Q-learning | 1.77 / 1.98 / 2.30 | 1.58 / 1.79 / 2.07 |
  | MTR | 1.03 / 1.06 / 1.11 | 1.01 / 1.03 / 1.08 |
  | RC | 1.06 / 1.06 / 1.05 | 1.04 / 1.03 / 1.02 |

* **What dominates:** the lookahead selection for the heuristic (about 84 % of the added area); the Q table for Q-learning on large sizes (54-58 % on 4x4). The routing relation itself is 1-5 %.
* **Timing:** routing + selection does **not** fit one 1 GHz cycle: 4.1-6.5 ns against the baselines' 0.8-1.1 ns. Five stages still leave 1.9-2.6 ns per stage (timing-only experiment). The simulated latencies assume zero extra cycles.
* **DeFT paper:** DeFT / MTR is 0.82-0.95 here against its 1.016 (1.01-1.04 without MTR's NI table in flip-flops); RC boundary / MTR is 1.18-1.35 against 1.133.
* **Cross-check:** DSENT gives 0.93-0.94 of this flow's reference router area.

Start with `results_v17_vcdiag/FINDINGS.md` and `results_v18_area/FINDINGS.md`.

## Rounds 19-21 (results_v19_vnrr/, results_v20_delay/, results_v21_fastsel/): the round-robin, decision delay, a fast selection
New simulator options, all off by default. With the defaults, the 84-configuration regression set is byte-identical (`results_v19_vnrr/regression.md`, `results_v21_fastsel/regression.md`).
* `-deft_vn_rr 1`: DeFT's boundary round-robin (Algorithm 1 except the F1 source rule), R3 on the input VN, per-router counters.
* `-deft_lb decision_delay N`: N extra cycles on hops with more than one offered output. `-deft_lb hop_stats 1`: counts those hops.
* `-sel DEFT_FAST`, `-deft_lb fast_ql 1`, `-deft_lb fast_stale K`: the fast selection, its learner, and K more cycles of age of the registered terms.

Long jobs run detached: `bash detach.sh NAME COMMAND...` (tmux, log in `~/lbraw/logs`), with `keepalive.sh` started on the Windows side to hold the distro open. Runners skip completed runs.
```
python3 experiments_v19.py regress 12 BIN_3AC1BAE,BIN_D6F65F8 && python3 experiments_v19.py drain 12 && python3 experiments_v19.py vcbal 12
python3 experiments_v19.py sat 12 && python3 experiments_v19.py points && python3 experiments_v19.py timing 12 && python3 experiments_v19.py eval 12
python3 experiments_v19.py check 1 eval && python3 experiments_v20.py n0check 12 && python3 experiments_v19.py csv 1 && python3 report_v19.py k5
python3 experiments_v19.py fsweep 12 && python3 experiments_v19.py fchoose 1
python3 experiments_v20.py drain 12 && python3 experiments_v20.py sanity 12 && python3 experiments_v20.py pre 2 && python3 experiments_v20.py precsv 1
python3 experiments_v20.py eval 12 && python3 experiments_v20.py csv 1 && python3 report_v20.py
python3 experiments_v21.py regress 12 BIN_3AC1BAE,BIN_K5 && python3 experiments_v21.py alpha0 12 && python3 experiments_v21.py drain 12
bash results_v21_fastsel/tb/run_rom_check.sh OBJDIR && bash results_v21_fastsel/tb/run_fast_vectors.sh OBJDIR 20000 && bash results_v21_fastsel/tb/run_router_smoke.sh
V21_CUT=1 python3 experiments_v21.py synth 12 && V21_CUT=0 python3 experiments_v21.py synth 12 flat && V21_CUT=1 python3 experiments_v21.py synthcsv && V21_CUT=0 python3 experiments_v21.py synthcsv && python3 experiments_v21.py nfast
python3 experiments_v21.py tune 12 heur && python3 experiments_v21.py tune 12 ext && python3 experiments_v21.py choose 1 heur && python3 experiments_v21.py tune 12 ql && python3 experiments_v21.py choose 1 ql
python3 experiments_v21.py k5check 12 && python3 experiments_v21.py drain 12 tuned && python3 experiments_v21.py eval 12 && python3 experiments_v21.py csv 1 && python3 report_v21.py
```

### v19 (Part K): DeFT's round-robin
* **H1 (K5, Holm over 60): 12 / 12.** Gains over DeFT are smaller than in v9: LAT -10 % to -24 %, P99 -27 % to -42 %.
* **H2: 41 / 48, 6 n.s., 1 against.** All 7 misses are on 2x2 against MTR and RC, so "beats MTR and RC on all sizes" no longer stands.
* **The fix does not close the gap to the DeFT paper:** DeFT stays below MTR and RC in throughput on every size. It worsens DeFT's latency on 2x2 (+9 %) and improves p99 on 3x3 and 4x4.
* **K6 and K7:** the load choice is committed; the confirmatory runs were postponed by v21 and not run.

### v20 (Part L): decision delay (descriptive)
* **At 1.0 x Lsat,** the gain over DeFT shrinks with N and is gone by N = 4 on 3x3 and 4x4. **At 0.2 x Lsat, N = 1 already reverses it** (+8 % to +18 %).
* p99 and throughput hold up, with a caveat: the delay reduces the collapse beyond saturation, for a reason not separated here.
* **L3:** computing terms in the previous cycle helps only with a different function: 4-5 cycles, against 5-7.

### v21: DEFT_FAST
* **Timing:** no variant decides in one cycle. N_fast = 2 (CI_fast), 3 (the others). RTL against the simulator: 1,450,802 vectors, 0 mismatches.
* **At its N_fast, against DeFT with the round-robin (Holm over 36):**
  - Mean latency at saturation: a gain only on 2x2 CI (-12.4 %). 5 of 6 tests n.s.
  - Mean latency at 0.2 x Lsat: **worse everywhere,** +23 % to +67 %.
  - p99 at saturation: 6 / 6, -30 % to -44 %.
* **Against MTR and RC:** 9 / 24 supported, all p99; 7 significantly against ours, all mean latency.
* **Area relative to DeFT, one unit per port (the form simulated):** CI_fast 1.5, CI_fastQL 2.0-2.4, FULL_fast 2.2, FULL_fastQL 3.2-4.0. With one unit per router it is 1.16-2.32, but slower and not simulated as such.

Start with `results_v19_vnrr/FINDINGS.md`, `results_v20_delay/FINDINGS.md` and `results_v21_fastsel/FINDINGS.md`.

## Round 23 (results_v23_fidelity/): DeFT as in the paper, modelling fixes, cross-validation, new reference measurements
Follows the independent review `review_v22/REVIEW.md` (findings R1-R15). New simulator options, all off by default; with the
defaults, and with every option given explicitly off, the 84-configuration regression set is byte-identical to the 780fa6b and
3ac1bae builds (`results_v23_fidelity/regression.md`).
* `-deft_up_keep 1` (R1): the Up link keeps the packet's VN; `-deft_rr_fallback 1` (R2): the boundary and source round-robin take
  the other VC when the counter's VC is held; `-deft_lut_entry dst` (R4): the paper's entry per destination router
  (`entries_by_destination` in the LUT, `deft_vl_lut_generator.py --entry-model`); `-traffic_rng 1` (R10): the traffic generator
  on its own `mt19937`.
* `-pipe_all N`: every head waits N cycles at the input-buffer front (one hop = 2 + N); `-deft_lb lookahead_route 1`: the
  next router's decision is computed when the head leaves and carried in the header; `-vc_per_hop 1`: MTR and RC take any free
  VC per hop (RC's buffer drains onto any free Up VC); `-deft_lb hysteresis D`: the default (fewest-hops) output unless another
  wins by more than D.
* **DeFT-P** = `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst` is the reference of every later round;
  **DeFT-B** = the same VN rules with the v1-v21 entry. LUTs: `luts/v23/` (`python3 experiments_v23.py luts 12`, not committed).
```
python3 experiments_v23.py regress 12 BIN780,BIN3AC && python3 experiments_v23.py luts 12 && python3 experiments_v23.py lutcheck
python3 experiments_v23.py probe 12 && python3 experiments_v23.py formal 6 && python3 experiments_v23.py drain 12 && python3 experiments_v23.py vcsplit 4
python3 experiments_v23.py sat 12 && python3 experiments_v23.py points && python3 experiments_v23.py timing 12 && python3 experiments_v23.py eval 12
python3 experiments_v23.py check 1 eval && python3 experiments_v23.py csv 1 && python3 experiments_v23.py look 12 && python3 experiments_v23.py lookcsv 1
python3 experiments_v23.py herd 12 && python3 experiments_v23.py herdcsv 1 && python3 report_v23.py all
python3 cea_crossval.py config && python3 cea_crossval.py sweep 4 && python3 cea_crossval.py eval 4 && python3 cea_crossval.py report
```

### Gates (A2, B)
* **Model check with the paper's Up rule** (`formal_upkeep.md`): all 897 masks of 2x2 and the sampled masks of 3x3 and 4x4, four
  relations (fixed pair XY and odd-even, CI, FULL): acyclic CDG, no dead end, no livelock; the negative control fails as it should.
* **Drain tests** (`drain_summary.csv`): 948 / 948 pass, 0 dead-end events (every VN-based method with the DeFT-P options, the
  lookahead variants, MTR and RC with the per-hop VC).
* **VC split** (`vc_split.md`): with the paper's rule the Up VL carries 50:50 (the old reference: 0:100) and the VC wait on the
  Up VL falls from 1.21 to 0.38 cycles per flit (2x2) and from 0.85 to 0.27 (4x4).
* `-pipe_all N` adds exactly N cycles per router (`probe_pipe.md`).

### Part D (pre-registered, `PREREGISTRATION.md`; seeds 91-95, 9 loads up to 2.4 x Lsat, pipe_all 0 and 2)
* D1 load points of DeFT-P per size, scenario and pipe depth (`load_points_v23.md`); D2 8,370 runs (`eval_runs.csv`); D5 180
  lookahead runs (`look_runs.csv`); D4 384 hysteresis runs (`herd_runs.csv`); 0 missing, 0 dead ends. Report: `report/summary.md`
  (v10-format tables per size and pipe depth, `latency_load.png`, the VC-split table), `report/primary.csv` (Holm over 18).
* **H1** (DeFT-P against the old DeFT, pipe_all 0): supported on 2x2 (THR +17 %, LAT -52 %) and 4x4 (THR +10 %, LAT -36 %),
  n.s. on 3x3. Per scenario DeFT-P wins on uniform (THR +5 to +10 %) and chipperm (THR +6 to +92 %) and **loses on hotspot**
  (THR -13 to -14 % on every size; the per-destination entry funnels the hot chiplet's traffic through one VL). The gap to MTR
  and RC is not closed: uniform LAT +13 to +21 %, THR -3.6 to -7.7 % (1.4-3.3 % against the static-VC MTR and RC of v19-v21).
* **H2** (ideal learners against DeFT-P): P99 gains supported on 2x2 and 3x3 (-33 to -55 %), LAT supported for CI on 2x2 only;
  on 4x4 LAT goes against (+32 to +37 %) because of chipperm (LAT +14x, THR -31 %), while uniform, hotspot and the faulty-VL
  scenario keep gains of LAT -8 to -60 %.
* **D5:** the lookahead model keeps none of the learners' gain at pipe_all 2 except 16 % for FULL on 4x4 (LAT +22 to +521 %
  against the ideal learner at 1.0 x Lsat; 5-6 % of stored decisions differ at the next router).
* **D4:** hysteresis matters only for FULL_qlLA_G beyond saturation (D = 4: +17 to +23 % accepted throughput on 4x4 uniform at
  pipe_all 0, peak unchanged); for CI no D changes anything by more than 5 %. Next grid for FULL: D in {2, 4, 6, 8}.

### Part C: CEA's simulator
Our 2x2 system expressed in `noxim3.5d-sop`'s format (`cea/`): the paper's per-destination-router entry cannot be expressed, so
the comparison is with DeFT-B. Saturation loads agree within 5 % (CEA 0.0115 / 0.011 against ours 0.011; L0 19.5 against 19.2
cycles), the latency ratio CEA / ours is 0.94-1.05 up to saturation and the accepted throughput agrees to 1 % at every load
(`report/cea_crossval.md`).

Start with `results_v23_fidelity/FINDINGS.md`.

## Round 24 (results_v24_xy/): late binding without path adaptivity (XY and a VN-split order on the interposer)
Follows a review of round 23: the chipperm loss of the late-binding variants comes from the odd-even turn model on the interposer,
not from the VL choice. New simulator options, all off by default; with the defaults, and with every option given explicitly off,
the 84-configuration regression set is byte-identical to the 8d84634 build (`results_v24_xy/regression.md`).
* `-deft_lb ipos_tm YX | O1`: `YX` = dimension order with Y first; `O1` = the order of the packet's VN on the interposer, XY in
  VN0 and YX in VN1 (the VN does not change on the interposer, so each VN's interposer channels carry one order; cf. O1TURN, ReD).
* `-deft_lb lut_bias D`: +D in the selection cost of an output whose move drops DeFT-P's VL (the LUT's exit, the per-destination
  entry) from the candidate mask. Candidate masks and pruning are untouched.
* `-deft_lb lookahead_fallback 1`: with lookahead routing, a head that holds no output asks for the stored output if it is free,
  else for the first other offered output that is free, else for the stored one.
* `-deft_lb busy_state 1`: the busy term read from the reservation entries of the output (the v23 lookahead lost it when the
  packet ahead in the same input VC still held an output).
* `gen_traffic.py --patterns chiptrans`: chiplet (cx, cy) sends to chiplet (cy, cx).
* **Names.** Relation **X** = `chip_tm XY ipos_tm XY`, **O** = `chip_tm XY ipos_tm O1`, **G** = the v23 odd-even variants.
  Mechanisms of a candidate: ideal (decision_delay 0), **LF** (lookahead + fallback + busy state at the residual delay), **DLY**
  (no lookahead, decision_delay N_fast).
```
python3 experiments_v24.py repro 10 && python3 experiments_v24.py regress 6 BIN_8D84634 && python3 experiments_v24.py busy 6 && python3 experiments_v24.py equiv 6
python3 experiments_v24.py repro2 6 && python3 experiments_v24.py formal 6 && python3 experiments_v24.py sat 12 && python3 experiments_v24.py points
python3 experiments_v24.py drain 12 v10 && python3 experiments_v24.py drain 12 bias && python3 experiments_v24.py drain 12 lf && python3 experiments_v24.py b5 6
python3 experiments_v24.py tunerule && python3 experiments_v24.py tune1 12 && python3 experiments_v24.py choose1 && python3 experiments_v24.py tune2 12 && python3 experiments_v24.py choose2
python3 experiments_v24.py cut 4 && python3 experiments_v24.py timing 12 && python3 experiments_v24.py eval 12 && python3 experiments_v24.py check
python3 experiments_v24.py csv && python3 experiments_v24.py sanity 9 && python3 report_v24.py
```

### Gates and tuning
* **Reproduction** (`reproduction.md`): the review's 22 probe rows reproduce (10 with existing options to the last digit, 12 with
  the options of this round to the printed digits).
* **Model check** (`formal_xy.md`): late binding with XY and with O1, fixed pair with O1: all 897 masks of 2x2 and the sampled
  masks of 3x3 and 4x4, acyclic CDG, no dead end, no livelock. **Drain tests** (`drain_summary.csv`): 1,254 / 1,254 pass.
* **Centre cut** (`centre_cut.md`): with fixed VLs odd-even is already saturated at 0.8 x Lsat on 4x4 chipperm (0.0204 of 0.0320
  accepted): the turn rules put the vertical crossings on the odd columns (0.25-0.42 against 0.01-0.11 flits/cycle).
* **Tuning** (`tuning.md`, seeds 101-102, 4,560 runs): heur_w 2, heur_busy 0, hop_weight_ipos 1 on every size and relation;
  lut_bias 2 on 2x2 and 0 on 3x3 and 4x4; ql_alpha 0.01. The hop weight 2 of rounds 8-23 is not kept.

### Part D (pre-registered, `PREREGISTRATION.md`; pipe_all 2, seeds 111-115, 14,850 runs, 0 missing, 0 dead ends)
* **Primary family (Holm over 18): 17 supported, 1 against.** `CI_qlLA_X` and `CI_qlLA_O` in mechanism LF against the best of
  DeFT-P, DeFT-B, MTR and RC per scenario, over five scenarios (uniform, hotspot, chipperm, chiptrans, one faulty VL per chiplet):

  | size | row | THR | LAT at 1.0 x Lsat | P99 |
  |---|---|---|---|---|
  | 2x2 | X | +3.7 % | -18.9 % | -40.1 % |
  | 2x2 | O | -0.5 % (against) | -12.9 % | -35.5 % |
  | 3x3 | X | +9.7 % | -17.8 % | -45.3 % |
  | 3x3 | O | +9.8 % | -19.0 % | -50.1 % |
  | 4x4 | X | +9.1 % | -22.5 % | -48.0 % |
  | 4x4 | O | +10.8 % | -26.8 % | -56.8 % |

* **Orders (ideal decision):** XY wins uniform, chipperm and the faulty scenario; the VN-split order wins chiptrans (THR +17 % and
  +28 % over XY on 3x3 and 4x4) and gives up about 3 % on uniform and faulty and 3-14 % on chipperm; odd-even wins none and loses
  chipperm (4x4: THR 0.0292 against 0.0583).
* **Mechanisms:** LF keeps the latency of the ideal decision (the heuristic within 1.5 %, Q-learning +2-4 %) for 1-3 % of THR; DLY
  keeps the THR and costs 5-12 % of latency at every load. With X and O only 11-17 % of the hops offer a choice (odd-even: 42-50 %).
* **Information:** occupancy is nearly all of the gain over a random choice (THR +7 to +11 %); the one-hop lookahead adds 1-2 % of
  THR and 4-10 % of latency; Q-learning adds nothing.
* **Low load:** no cost against DeFT-P for the ideal decision and for LF with the heuristic (2-3 % faster at 0.2 x Lsat).
* **Beyond saturation:** the candidates keep 98.6-100 % of their peak on average, like the baselines.
* **Recommended main configuration for the confirmatory round:** `CI_heurLA_X` in mechanism LF, with `CI_heurLA_O` in LF as the
  second configuration (it removes XY's weakness on transpose-like traffic and is ahead on 4x4).

Start with `results_v24_xy/FINDINGS.md`.

## Round 25 (results_v25_confirm/): the frozen configuration confirmed on fresh seeds, and its hardware
Nothing is tuned and no simulator option is added. The configuration is the one round 24 chose
(`results_v24_xy/tuning_choice.json`), the simulator is the ce6ab6a build (`results_v25_confirm/regression.md`: the
84-configuration set byte-identical), and the tests are fixed in `results_v25_confirm/PREREGISTRATION.md` before any evaluation
run.
* **Frozen rows.** `CI_heurLA_X_LF` (**main**: late entry, XY on both layers, the lookahead heuristic with W 2, B 0, G 1 and D 2
  on 2x2 / D 0 on 3x3 and 4x4; lookahead routing with the fallback and the busy state, no residual delay), `CI_heurLA_O_LF`
  (**second**: the same with the VN-split order), `CI_heurLA_X_DLY` (the main row's selection at the buffer front,
  decision_delay 2), `CI_qlLA_X_LF` (Q-learning with alpha 0.01, one residual cycle). References: DeFT_P, DeFT_B on every
  scenario, MTR, RC and XY_SP on the fault-free ones, DeFT_Dis and DeFT_Ran on those with faults.
* **Scenarios** (the same eight on every size): uniform, localized, hotspot, chipperm, chiptrans, movinghot fault-free, and
  uniform and hotspot with one faulty VL per chiplet. The tuning of round 24 did not see localized, movinghot and hotspot with
  faults.
* **Drivers.** `experiments_v25.py` (Part A) dispatches to `experiments_v25_eval.py` (B), `_faults.py` (C, stages `c_*`),
  `_apps.py` (D, `d_*`), `_pipe0.py` (E, `e_*`), `_hw.py` and `_hw2.py` (F, `f_*`); `experiments_v25_add.py` runs the addendum
  row. `chain_v25.sh` and `chain_v25_add.sh` run the steps after Part B's runs unattended and stop at the first failed check.
  `report_v25.py` and `report_v25_hw.py` write `report/` and `paper_data/`; `extra_v25.py` writes the descriptive tables
  `report/extra_D.md`, `extra_E.md` and `extra_A.md` that `FINDINGS.md` quotes; `check_v25_families.py` computes the three
  pre-registered families (Part B, Part C, the addendum) a second time without the report's code
  (`report/families_check.md`). `build_ref.sh COMMIT` makes the reference build.
```
bash build_ref.sh ce6ab6a && python3 experiments_v25.py regress 12 && python3 experiments_v25.py reuse 12
python3 experiments_v25.py sat 12 && python3 experiments_v25.py points && python3 experiments_v25.py drain 12
python3 experiments_v25.py timing 10 && python3 experiments_v25.py eval 10 && python3 experiments_v25.py check && python3 experiments_v25.py csv && python3 experiments_v25.py sanity 12
python3 experiments_v25.py c_formal 2 && python3 experiments_v25.py c_drain 2 && python3 experiments_v25.py c_sat 2 && python3 experiments_v25.py c_points
python3 experiments_v25.py c_eval 12 && python3 experiments_v25.py c_check && python3 experiments_v25.py c_csv
python3 experiments_v25.py d_eval 12 && python3 experiments_v25.py d_check && python3 experiments_v25.py d_csv
python3 experiments_v25.py e_eval 12 && python3 experiments_v25.py e_check && python3 experiments_v25.py e_csv
python3 experiments_v25.py f_build && python3 experiments_v25.py f_smoke && python3 experiments_v25.py f_vec && python3 experiments_v25.py f_mut && python3 experiments_v25.py f_lat
python3 experiments_v25.py f_synth && python3 experiments_v25.py f_semi && python3 experiments_v25.py f_csv && python3 report_v25_hw.py
python3 experiments_v25_add.py drain 12 && python3 experiments_v25_add.py eval 12 && python3 experiments_v25_add.py check && python3 experiments_v25_add.py csv
python3 report_v25.py && python3 extra_v25.py && python3 check_v25_families.py
```

### Gates
* **Regression** (`regression.md`): 84 / 84 byte-identical to a fresh build of ce6ab6a (the 8d84634 build, the options absent,
  every option of rounds 23-24 explicitly off). **Reuse** (`reuse_check.md`): 24 / 24 runs of round 24 reproduced with this
  round's row definitions.
* **Ladders** (`load_points_v25.md`): the ladders of the three scenarios the tuning did not see, made again by the D1 rule, equal
  round 23's. **Drain tests** (`drain_summary.csv`): 336 / 336 pass (the four frozen rows at pipe_all 2, the two late-binding
  rows of Part E at pipe_all 0).
* **Fault-sweep masks:** model check of `CI_XY_XY` and `CI_XY_O1` on all 27 masks, 54 / 54 pass (`formal_faults.md`); all-pairs
  drain tests of every row of the sweep on every mask, 162 / 162 pass (`drain_faults.csv`).

### Part B: the frozen rows on eight scenarios (`report/summary_B.md`; 18,900 runs, seeds 121-130, no dead-end event)
* **Primary family (Holm over 18): 17 supported, 1 against.** Against the best baseline over the eight scenarios (2x2 / 3x3 /
  4x4): the main row THR +1.5 / +6.7 / +6.6 %, LAT at 1.0 x Lsat -13.1 / -10.5 / -15.0 %, P99 -27.8 / -27.9 / -34.2 % (9 of 9
  supported); the second row THR -2.7 / +5.9 / +7.3 %, LAT -6.2 / -8.7 / -16.1 %, P99 -21.3 / -29.6 / -40.9 % (THR on 2x2 is
  against; the pre-registration had named that test as the one not expected to be supported).
* **Seen against not seen.** On the five scenarios of the tuning the effects of round 24 come again on the new seeds (main row:
  THR +4.1 / +10.5 / +9.1 %, LAT -20.1 / -16.4 / -23.6 %). On the three it did not see the main row is level with the best
  baseline (THR -2.7 / +0.7 / +2.5 %, LAT 0.0 / +0.3 / +1.4 %): it gains on hotspot with faults, and it is behind RC on 2x2
  localized and behind MTR and RC on the moving hotspot.
* **Per reference row.** Ahead of DeFT_B in THR and LAT in 24 of 24 cells (a cell is one scenario on one size), of DeFT_P in 23
  and behind in none, of XY_SP, DeFT_Dis and DeFT_Ran in all; against MTR better in 13 and worse in 4 of 18 cells in THR,
  against RC in 12 and 2.
* **Q-learning** adds nothing to the heuristic (THR -0.2 %, LAT +2 to +3 %). **DLY** buys 1-2 % of THR with 3-7 % more latency.
* **Low load and beyond the peak** as in round 24: LAT at 0.2 x Lsat against DeFT_P -2.1 / -3.1 / -2.5 % (one to two cycles);
  the accepted throughput beyond the peak stays at 0.992-0.997 of the peak on average.

### Part C: fault sweep (`report/summary_C.md`; 3,240 runs, seeds 131-135, no dead-end event)
* **Family (Holm over 12): 12 of 12 supported.** Main row against the best reference row of each mask, uniform traffic: THR
  +7.8 / +13.5 / +22.1 % with one faulty VL in every chiplet and +3.8 / +8.8 / +13.9 % with two; LAT at 1.0 x Lsat -19 to -37 %.
* **k = 3 check passed:** with one functional VL per chiplet the main row is identical to DeFT_P in all 180 run pairs.

### Part D: application traces (`report/summary_D.md`; 630 runs, none excluded, no dead-end event)
* The main row's mean latency is 2-4 % below DeFT_P's on every trace and pair (geometric mean 0.973 for one application,
  0.973-0.974 for two; 0.969-0.975 with one faulty VL per chiplet); its completion time is equal for one application (0.997)
  and 1-2 % shorter for two. The traces offer at most 3-9 % of the saturation load: they show the low-load gain of Part B and
  say nothing about its throughput gain.

### Part E: one-cycle router model (`report/summary_E.md`, `report/extra_E.md`; 2,970 runs, seeds 141-145, no dead-end event)
* Descriptive, no test: `-pipe_all 0`, uniform, hotspot, chipperm and uniform with one faulty VL per chiplet; `CI_heurLA_X`
  with an ideal decision and `CI_heurLA_X_DLY` against DeFT_P, DeFT_B, MTR and RC. Against the best baseline (2x2 / 3x3 / 4x4):
  the ideal decision THR +6.0 / +13.5 / +10.8 %, LAT at 1.0 x Lsat -9.4 / -12.8 / -9.9 %, P99 -24.3 / -28.8 / -23.8 %; DLY THR
  +6.4 / +14.6 / +11.2 %, LAT -6.4 / -9.6 / -6.9 %.
* **Against the four-cycle model on the same four scenarios** (Part B runs: LF THR +4.5 / +11.8 / +9.8 %, LAT -18.6 / -17.3 /
  -16.8 %; DLY THR +6.2 / +15.2 / +11.0 %): the throughput gain is the same; the latency gain at 1.0 x Lsat is half to three
  quarters as large, because Lsat lies earlier on the curve with the shorter pipeline (at 1.2 x Lsat the gain is 42-51 %
  against 49-63 %); the low-load gain against DeFT_P is the same in per cent (-2.7 / -3.5 / -2.8 %) and half in cycles; the
  decision delay of DLY costs the same three cycles per packet, which is 9-14 % of the low-load latency instead of 5-8 %.
* One cell differs beyond the peak: on 4x4 chipperm every row except DeFT_B loses 11-17 % of its peak throughput above
  1.4 x Lsat (the late-binding rows 17 %; they still accept more than every reference row at every load above 1.0 x Lsat).

### Part F: hardware of the final design (`hw/FINDINGS_hw.md`, `report/summary_F.md`)
RTL of the interposer router of the three heuristic rows (`hw/rtl/`: LF with XY, LF with the VN-split order, DLY with XY) around
the reference core of round 18; flow of rounds 18 and 21 (Yosys + ABC, NanGate45, OpenSTA, pre-layout).
* **Check against the simulator:** 6.12 M, 6.21 M and 4.97 M vectors from simulator runs (offered outputs, pruned masks, costs,
  the stored decision, the output requested through the fallback), 0 mismatches; every instrumented run byte-identical to
  `bin/noxim`; 23 of 25 mutations caught (the other two change logic no reachable input exercises); 140 / 140 router
  configurations pass the router-level test.
* **The lookahead needs no header bit and no sideband wire:** the decision unit of an input port reads the head on the link and
  the result is stored in the router. Header: 2 bits more than DeFT (the 4-bit entry mask), 4 on 2x2 (the default entry VL).
* **Area** relative to DeFT (hierarchy kept / router core kept / flattened): interposer router of the main row 1.41-1.50 /
  1.23-1.31 / 1.12-1.21; chiplet router 1.01-1.02 (2x2: 1.05-1.06); all routers of a system 1.22-1.25 / 1.13-1.16 /
  1.08-1.10. The VN-split order: 1.34-1.38 / 1.21-1.24 / 1.17-1.20 per system. Round 18's area parser counted sub-modules
  without parameters as zero area (its ratios to DeFT were about 1 % too high); this round's totals are checked against the
  tool's design area.
* **Timing:** the reference pipeline reaches 1.27-1.32 ns in this flow (T_ref). The main row's decision takes two cycles at
  T_ref (margin +0.23 ns) and three at 1 ns; a hop with one offered output keeps the reference's four cycles; the router's
  longest stage is 0.90-0.96 x T_ref.
* **F5:** LF with residual delay 0 can be built at the reference period, so the evaluated main row is the mechanism that is
  built. Two conditions: the first decision stage reads the head on the link (0.28-0.42 ns of the link cycle left for the wire,
  DeFT 0.82-0.90 ns) and the clock is the reference's. If either fails the same RTL has one residual cycle; that row
  (`CI_heurLA_X_LF1`) is the pre-registered addendum (`PREREGISTRATION_addendum.md`). DLY fits only with one unit per input port
  and without margin.

### Addendum: the main row with one residual cycle (`report/summary_A.md`, `report/extra_A.md`; 2,160 runs, seeds 121-130, no dead-end event)
* `CI_heurLA_X_LF1` is the main row with `decision_delay 1`: what the RTL of Part F does if either condition of F5 fails.
  Defined in `PREREGISTRATION_addendum.md` before any of its runs; the Part B design; drain tests 56 / 56
  (`drain_summary_addendum.csv`).
* **A family of its own (Holm over 9), reported next to the primary family: 9 of 9 supported.** Against the best baseline
  THR +1.5 / +6.7 / +6.5 %, LAT at 1.0 x Lsat -11.1 / -8.5 / -13.2 %, P99 -27.4 / -27.3 / -33.3 %.
* **The cycle costs latency and no throughput.** Against the main row: THR -0.0 / -0.0 / -0.1 %, LAT +3.7 / +2.7 / +2.4 % at
  0.2 x Lsat and +2.2 / +2.3 / +2.2 % at 1.0 x Lsat: one cycle per hop with a choice, 1.4-2.4 cycles per packet. The main
  row's latency advantage over DeFT_P at low load is gone (+1.5 / -0.5 / -0.1 % instead of -2.1 / -3.1 / -2.5 %).
* With the same residual cycle, Q-learning and the heuristic are within 1 % of each other in every metric
  (`report/extra_A.md`, Y.6; descriptive).

Start with `results_v25_confirm/FINDINGS.md`. The tables for the paper are in `results_v25_confirm/paper_data/` (one CSV per
table or figure; `paper_data/README.md` lists them).

## Round 26 (results_v26_faults/): fault coverage. The model check on all fault patterns, and random VL faults at four rates
Nothing is tuned, no row is changed and no simulator option is added. The configuration is the frozen one of round 25, the
simulator is the ee0e247 build (`results_v26_faults/regression.md`: the 84-configuration set byte-identical; no simulator source
changed in this round), and the masks and the tests are fixed in `results_v26_faults/PREREGISTRATION.md` and `masks_v26.json`
before any run of Parts A and B.
* **Frozen rows.** `CI_heurLA_X_LF` (**main**) and `CI_heurLA_O_LF` (**second**), as defined in round 25. References under
  faults: DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran. MTR and RC are not run with faults: they cannot deliver every pair (B5).
* **Masks.** A mask is a set of faulty VLs that leaves every chiplet a functional VL. Part A: every mask of 2x2 (15^4 = 50,625)
  and four sets on 3x3 and 4x4. Part B: 16 random masks per size and fault rate (1/16, 2/16, 4/16, 8/16 of the VLs), 192 in all
  (`masks_v26.md`), each with a LUT of its own.
* **Drivers.** `experiments_v26.py` (A0, the masks, the LUTs) dispatches to `experiments_v26_formal.py` (the model check: `aneg`,
  `a1`, `a1csv`, `a2`, `a2sub`), `experiments_v26_conf.py` (conformance of the model with the simulator: `a3_*`) and
  `experiments_v26_eval.py` (Part B: `b_*`). `chain_v26_formal.sh` and `chain_v26_b.sh` run Part A and Part B unattended, share
  the machine through a width file and stop at the first failed check. `reach_v26.py` is B5. `report_v26.py` writes `report/`
  and `paper_data/`; `extra_v26.py` writes the descriptive tables `report/extra_B.md` that `FINDINGS.md` quotes;
  `check_v26_family.py` computes the primary family a second time without the report's code (`report/families_check.md`).
```
bash build_ref.sh ee0e247 && python3 experiments_v26.py regress 12 && python3 experiments_v26.py masks && python3 experiments_v26.py luts 12
python3 experiments_v26.py aneg && python3 experiments_v26.py a1 10 && python3 experiments_v26.py a1csv
python3 experiments_v26.py a2 6 3x3 && python3 experiments_v26.py a2 6 4x4 && python3 experiments_v26.py a2sub 6
python3 experiments_v26.py a3_build && python3 experiments_v26.py a3_control && python3 experiments_v26.py a3_run 2 1
python3 experiments_v26.py a3_run 2 2:2x2 && python3 experiments_v26.py a3_run 2 2:3x3:base && python3 experiments_v26.py a3_report
python3 experiments_v26.py b_drain 12 && python3 experiments_v26.py b_sat 12 && python3 experiments_v26.py b_points
python3 experiments_v26.py b_timing 12 && python3 experiments_v26.py b_eval 12 && python3 experiments_v26.py b_check && python3 experiments_v26.py b_csv
python3 reach_v26.py && python3 report_v26.py && python3 extra_v26.py && python3 check_v26_family.py
```
(`a3_run NPROC SEEDS[:SIZES[:base]]`: seed 1 on the six masks of every size, then further seeds for a row and size with fewer
than 1,000,000 compared hops; `a3_report` lists those. The raw outputs stay under `~/lbraw/v26` until the stage that writes
the CSV.)

### Gates
* **Regression** (`regression.md`): 84 / 84 byte-identical to a fresh build of ee0e247 (the ce6ab6a build, the options absent,
  every option explicitly off).
* **Controls** (`formal_controls.md`, `conformance_controls.md`): the model check finds the cycle when R3 and the F1 source rule
  are removed, the subset check fails between two different relations, and the conformance replay reports 9,770 to 54,171
  mismatches when it is given a model that is not the one of the run. The checks can fail.
* **Drain tests** (`drain_v26.csv`): the six rows of Part B on the 192 masks, 1,152 / 1,152 pass, no dead-end event.

### Part A: the model check on all fault patterns (`formal_all_2x2.md`, `formal_a2.md`, `formal_subset_2x2.md`, `conformance.md`)
Four checks per mask and relation (`CI_XY_XY` for the main row, `CI_XY_O1` for the second): the CDG is acyclic, no reachable
state is a dead end, the state graph is acyclic (its longest path is the hop bound), and the CDG is a subset of the fault-free
CDG of the relation. The model (`formal/impl_relation_check.py` with the settings of `formal/xy_check.py`) is not changed.
* **A1, 2x2, exhaustive: 50,625 masks, 101,250 checks, all pass.** The subset check holds on every mask; the longest path is
  24 hops (16-24 over the masks). The 2x2 result no longer rests on a sample (round 24: 897 masks).
* **A2, 3x3 and 4x4: 1,480 checks on 739 masks, all pass**: the fault-free mask, every fault pattern of a single chiplet
  (126 and 224 masks), 200 and 60 random masks from the whole space, and the 64 masks of Part B per size. Longest path 32 and
  40 hops.
* **The argument for the patterns not enumerated** (15^9 and 15^16): the fault mask enters the model only where the initial
  states are built, so (1) a fault only removes channel dependencies (check 4, on every mask checked) and (2) the packets to
  one chiplet see only that chiplet's faults (tested directly on 2x2: 8,000 comparisons, the subset holds in all). With the
  fault-free mask and all single-chiplet patterns passing, every combination passes. For 3x3 and 4x4 this is an argument
  confirmed on every mask tried, not an enumeration.
* **A3, the model against the simulator:** every head-flit hop of simulator runs is looked up in the model's state graph (the
  state must be a node, the offered outputs must equal the moves of the node, the hop taken must be an edge).
  **11,999,425 hops in 156 runs, 0 mismatches**: DeFT_P and the two frozen rows, more than 1,000,000 hops for every row on
  every size, six masks per size (fault-free, the same VL in every chiplet, mask 1 of each rate of Part B), uniform and
  hotspot at 1.0 x Lsat. Every instrumented run has a statistics file byte-identical to `bin/noxim`. This is a test on
  runs, not a proof that the two agree in states the runs did not visit.

### Part B: random VL faults at four rates (`report/summary_B.md`, `report/extra_B.md`; 18,432 runs, seeds 151, 152, no dead-end event)
Uniform and hotspot traffic; one ladder per mask and traffic pattern (DeFT_P, the D1 rule, `load_points_v26.md`); loads 0.5,
1.0, 1.4 and 2.0 x Lsat; six rows. The unit of every test is the mask (16 per size and rate).
The 40 h rule dropped nothing (`runtime_estimate.md`).
* **Primary family (Holm over 24: three sizes, four rates, THR and LAT at 1.0 x Lsat; the main row against the best of the
  four DeFT variants): 22 of 24 supported, none against.** Not significant: 2x2 at 8/16, both metrics. Computed a second
  time by `check_v26_family.py`: all 24 tests agree.

  | size | THR at 1/16, 2/16, 4/16, 8/16 | LAT at 1/16, 2/16, 4/16, 8/16 |
  |---|---|---|
  | 2x2 | +3.3, +3.0, +2.6, +0.6 % | -18.9, -17.3, -16.9, -6.0 % |
  | 3x3 | +5.5, +4.6, +3.2, +1.4 % | -18.4, -16.6, -16.0, -7.1 % |
  | 4x4 | +8.9, +6.8, +4.9, +2.0 % | -19.6, -19.6, -18.0, -13.2 % |
* **The gain shrinks as the rate grows**, most under uniform traffic (4x4: THR +14.4 % at 1/16, +2.7 % at 8/16). Under
  hotspot traffic it is +2 to +4 % up to 4/16 and nearly flat.
* **What costs the gain is a chiplet that is left one functional VL**, not the number of faults as such. Within one rate
  the masks without such a chiplet keep the gain and those with one lose most of the throughput gain: 4x4 at 4/16 +7.9 %
  against +3.1 %, 3x3 at 4/16 +4.3 % against +1.5 %, 2x2 at 8/16 +3.7 % against -0.5 %. The main row is behind the best
  reference in 15 of the 192 masks in THR (by at most 2.0 %) and in 6 in LAT; 15 of the 17 masks concerned have such a
  chiplet. It is behind DeFT_P in 2 masks in THR and in 1 in LAT.
* **Against each reference row** the main row is ahead in THR, LAT and P99 in all 12 cells. Against DeFT_P: THR +12 to
  +21 % and LAT -44 to -52 % up to 4/16, +3.6 to +7.0 % and -20 to -33 % at 8/16. DeFT_B is the strongest reference.
* **The second row** has 1.6 to 2.7 % less throughput than the main row in 11 of the 12 cells and an equal or higher latency
  at 1.0 x Lsat. Against the best reference it is ahead in LAT in every cell, in THR only on 3x3 and 4x4 at the lower rates.
* **Random against even patterns** (round 25, uniform traffic). At the same share of faulty VLs a random pattern gives about
  three tenths of the even pattern's THR gain at 4/16 (+2.1 / +4.0 / +6.8 % against +7.8 / +13.5 / +22.2 %) and less than a
  fifth at 8/16 (+0.7 / +0.6 / +2.7 % against +3.8 / +8.8 / +13.9 %). The random masks of 2x2 that happen to be even give
  round 25's numbers: the fault numbers of round 25 are those of the most favourable placement of the faults.
* THR is the largest accepted throughput over loads up to 2.0 x Lsat; in about half of the cells it is reached at the last
  load and is then a lower bound, for every row alike. Everything outside the primary family is descriptive.

### B5: reachability (`reachability_v26.md`)
* **MTR and RC lose exactly the faulty share of the VLs**: 93.75 / 87.5 / 75 / 50 % of the inter-chiplet pairs can be delivered
  at the rates 1/16, 2/16, 4/16, 8/16 (94.44 / 88.89 % at the first two on 3x3), on every mask, the same for both methods: a
  faulty VL cuts a quarter of the sources (RC) or of the destinations (MTR) of its chiplet off from every other chiplet. The
  rows of the three old rates equal round 10's.
* **DeFT and the two late-binding rows deliver every pair on all 192 masks** (the drain tests).

Start with `results_v26_faults/FINDINGS.md`. The tables for the paper are in `results_v26_faults/paper_data/` (one CSV per
table or figure; `paper_data/README.md` lists them).

## Round 27 (results_v27_early/): early against late binding. Does the gain come from binding late, or from choosing the entry VL by congestion at all?
Every reference of rounds 23 to 26 chooses the entry VL without looking at the network, so those rounds cannot say how much of
the main row's gain over DeFT comes from binding the entry VL late and how much from choosing it by congestion at all. This
round adds rows that choose by congestion but bind early, and the main row without its occupancy reports across the VLs. The
frozen configuration of round 25 is not retuned and no existing row is changed. The simulator gets four options, all off by
default (`results_v27_early/regression.md`: the 84-configuration set is byte-identical to the d641861 build with the options
absent and with every option given at its default). The rows, the tuning rule, the tests and what I expected are fixed in
`results_v27_early/PREREGISTRATION.md` before any run of Parts B, C and E; its addendum freezes the tuned values before Part C.

**The answer.** Without faults the gain comes from binding late: all 18 tests are supported, and the rows that choose by
congestion and bind early are not between DeFT_P and the main row but behind DeFT_P. The exception is hotspot traffic, where
choosing by congestion at all is what counts. With a quarter of the VLs faulty the early rows are ahead of DeFT_P, and the
best of them comes within about 1 % of the main row's throughput on 3x3 and 4x4 (descriptive, Part E).
* **New options of `-deft_lb`:** `oracle_scope vl|route` (what the injection-time choice reads: the occupancy at the entry VL,
  or the queues on the interposer route to it), `oracle_period P` (the occupancies are sampled every P cycles; 0 = read at
  the moment of the choice), `entry_commit off|down` (the head commits to one entry VL at the Down move), `up_report 0|1`
  (the occupancy reports across the VLs). `entry_stats 1` only counts; `commit_check N` is a diagnostic of the unit checks.
* **Rows** (pipe_all 2; every row with DeFT-P's VN options and `-traffic_rng 1`; LUTs `luts/v23`).

  | row | what binds the entry VL, and when |
  |---|---|
  | `DeFT_P` | the LUT, at injection (round 25) |
  | `CI_heurLA_X_LF` (**main**) | the selection on the interposer, hop by hop (round 25, frozen) |
  | `EB_vl` | at injection: fewest hops + `oracle_beta` x the occupancy at the entry VL, read at that moment |
  | `EB_route` | at injection: fewest hops + `oracle_beta` x the queues on the interposer route to the entry VL |
  | `EB_vl64` | `EB_vl` with occupancies sampled every 64 cycles |
  | `EB_down` | the main row until the Down move, where it commits to its cheapest entry VL |
  | `LB_noVLrep` | the main row without the occupancy reports across the VLs |

  The three injection-time rows read the state of the whole network at no cost and with no delay, which no real source
  could. They are the favourable case for early binding in what they know, and greedy in what they do with it.
* **Drivers.** `experiments_v27.py` (the regression; dispatches to `experiments_v27_eval.py`: the gates `a2_*`, the tuning
  `b_*`, Part C `c_*`, Part E `e_*`). `chain_v27.sh a|b` and `chain_v27c.sh` run the round unattended and stop at the first
  failed check; `restore_v27.py` is the time rule after the timing runs. `tune_scen_v27.py` writes the tuning by scenario.
  `report_v27.py` writes `report/` and `paper_data/`; `extra_v27.py` writes the descriptive tables `report/extra_C.md` and
  `report/extra_E.md` that `FINDINGS.md` quotes; `check_v27_family.py` computes the primary family a second time without the
  report's code (`report/families_check.md`).
```
bash build_ref.sh d641861 && python3 experiments_v27.py regress 12 before && make && python3 experiments_v27.py regress 12 after
python3 experiments_v27.py a2_anchor 12 && python3 experiments_v27.py a2_units 12 && python3 experiments_v27.py a2_drain 12
python3 experiments_v27.py e_reuse 12 && python3 experiments_v27.py b_rule && python3 experiments_v27.py b_tune 12 && python3 experiments_v27.py b_choose
python3 experiments_v27.py a2_drain 12 tuned && python3 tune_scen_v27.py
python3 experiments_v27.py c_timing 12 && python3 experiments_v27.py c_eval 12 && python3 experiments_v27.py c_check && python3 experiments_v27.py c_csv
python3 experiments_v27.py e_eval 12 && python3 experiments_v27.py e_check && python3 experiments_v27.py e_csv
python3 report_v27.py all && python3 check_v27_family.py && python3 extra_v27.py
```
(The raw outputs stay under `~/lbraw/v27` until the stage that writes the CSV.)

### Gates
* **Regression** (`regression_before.md`, `regression.md`): 84 / 84 byte-identical to the d641861 build before the change, and
  after it with the options absent and with every option at its default.
* **Anchor** (`anchor.md`): DEFT_LB with both VLs from the LUT and XY in both layers gives DeFT_P's results in 18 / 18 runs,
  so the early rows are compared with DeFT_P itself.
* **Unit checks** (`unit_checks.md`): `entry_stats` changes no statistic (18 / 18); `entry_commit down` changes nothing when
  every chiplet has one functional VL (3 / 3); the committed candidate is a cheapest output of the main row's selection in
  12,000 of 12,000 sampled heads on 3x3 and 4x4.
* **Drain tests** (`drain_v27.csv`, `drain_v27_tuned.csv`): the five new rows on six masks per size, 90 / 90 pass; the three
  tuned rows again with their chosen values, 54 / 54 pass. No dead-end event, and no hop of an `EB` run offers more than one
  output, in any run of the round.
* **Safety** (`FINDINGS.md`, A3): each new row restricts the checked relation or leaves it unchanged, so no new proof and no
  new model check are needed.

### Part B: tuning of `oracle_beta` (`tuning_v27.md`, `tuning_by_scenario_v27.md`; 1,840 runs, seeds 101, 102)
The rule of round 24 on 2x2 and 4x4 (3x3 takes the 4x4 value), grid {0.125, ..., 8}, separately for the three rows.

| | `EB_vl` | `EB_route` | `EB_vl64` | main row (frozen) |
|---|---|---|---|---|
| 2x2: value (score) | 0.5 (-0.893) | 2 (-0.597) | 0.25 (-1.094) | (+0.530) |
| 4x4 and 3x3: value (score) | 1 (-1.276) | 4 (-0.116) | 1 (-1.406) | (+0.648) |
* No chosen value is at an end of the grid. **With its best value every early row scores below DeFT-P** (score 0); the main
  row scores +0.53 and +0.65.
* By scenario the mean hides a split: under hotspot traffic the early rows are close to the main row, under chipperm and
  chiptrans traffic they are behind DeFT-P at every value of the grid. No value brings an early row to the main row's score
  in any tuning scenario.

### Part C: the evaluation (`report/summary_C.md`, `report/extra_C.md`; 11,340 runs, seeds 161-170, no dead-end event)
Six fault-free scenarios, nine loads (0.2 to 2.4 x Lsat of DeFT-P), seven rows, ten seeds. The 30 h rule dropped nothing
(`runtime_estimate.md`). Effects are means over the six scenarios with the 95 % interval over the ten seeds.
* **Primary family (Holm over 18: three sizes; the main row against `EB_vl`, `EB_route` and `EB_down`; THR and LAT at
  1.0 x Lsat): 18 of 18 supported, none against.** Computed a second time by `check_v27_family.py`: all 18 tests agree.

  | size | THR: the main row against `EB_vl`, `EB_route`, `EB_down` | LAT at 1.0 x Lsat: against `EB_vl`, `EB_route`, `EB_down` |
  |---|---|---|
  | 2x2 | +20.0, +17.3, +6.9 % | -68.0, -59.9, -46.8 % |
  | 3x3 | +23.6, +15.8, +32.8 % | -73.5, -32.4, -81.4 % |
  | 4x4 | +31.8, +12.4, +42.9 % | -77.2, -41.0, -80.3 % |
* **The early rows are behind DeFT_P, not between DeFT_P and the main row.** THR against DeFT_P on 2x2 / 3x3 / 4x4: `EB_vl`
  -10.4 / -8.0 / -15.2 %, `EB_route` -8.3 / -1.9 / -0.6 %, `EB_down` +0.6 / -14.4 / -21.8 %, `EB_vl64` -12.4 / -10.5 /
  -16.5 %; the main row +7.5 / +13.6 / +11.7 %. Of the 18 shares of the main row's gain that the three rows of the family
  reach (three sizes, THR and LAT), 16 are negative; the largest is 17 %.
* **Hotspot traffic is the exception.** There every row that looks at the network is 17 to 23 % ahead of DeFT_P in THR, the
  early rows reach 77 to 100 % of the main row's THR gain, and on 3x3 and 4x4 the injection-time rows are level with the
  main row in THR (within 0.7 %). In the other five scenarios every early row is behind the main row on every size in
  both metrics, and behind DeFT_P in all but 9 of 120 cells. In no cell is an early row ahead of the main row with an
  interval that excludes 0.
* **`EB_route` is the better injection-time row** (THR +2.3 / +6.7 / +17.2 % against `EB_vl`): the queues on the route say
  more than the occupancy at the entry VL. It is level with DeFT_P on 3x3 and 4x4 and behind it on 2x2.
* **`EB_down` is the cleanest test of "late".** It commits at the Down move to what is the main row's own first choice
  (unit checks) and has 6.5 / 24.7 / 30.0 % less throughput than the main row; on 3x3 and 4x4 it is the weakest row.
* **Age of the information:** `EB_vl64` has 1.5 to 2.7 % less THR and 8 to 41 % more LAT at 1.0 x Lsat than `EB_vl`.
* **Why the early rows lose.** `EB_vl` and `EB_down` give up the balance of DeFT-P's table and drift to the nearest VL (the
  busiest VL of `EB_vl` carries 3.2 times the mean VL under chipperm traffic on 4x4, DeFT_P's 1.1). `EB_route` keeps the
  balance, with 5 to 7 % more hops than DeFT_P, and still gains nothing. An injection-time choice is 35 to 72 cycles old
  when it takes effect below saturation and 110 to 290 cycles at 1.0 x Lsat. Under hotspot traffic the hot spot does not
  move and the rest of the network is not loaded, so the early choice is still true on arrival; under movinghot traffic
  the injection-time rows are 4 to 15 % behind DeFT_P.
* **`LB_noVLrep`: the occupancy reports across the VLs buy nothing measurable** (THR within 0.2 %, LAT within 0.1 %, P99
  within 0.8 % of the main row on every size, every interval including 0).
* **Below saturation:** at 0.2 x Lsat all rows are within 3 % of each other; from 0.5 x Lsat on the early rows are slower
  than DeFT_P (+3 to +8 % for the injection-time rows at 0.5 x Lsat) and the main row is faster (-2 %).
* **The main row's gain over DeFT_P is the same on a third set of seeds:** THR +7.5 / +13.6 / +11.7 % and LAT -35.5 / -37.6 /
  -37.4 % here, +7.3 / +14.1 / +12.0 % and -33.0 / -34.3 / -33.9 % in round 25 on the same six scenarios.
* THR is the largest accepted throughput over loads up to 2.4 x Lsat; in a quarter to two thirds of the cells it is
  reached at the last load and is then a lower bound, for every row alike. LAT at 1.0 x Lsat of DeFT-P compares rows of
  which some are past their own saturation. Everything outside the primary family is descriptive. The early rows are
  greedy choices of one kind with exact and free information; a method that reserves or randomizes at injection was not
  tried (`FINDINGS.md`, "Limits").

### Part D: latency at every load (`report/summary_D.md`; no new runs, from `results_v25_confirm/eval_runs.csv`)
Mean latency of the main row against the best of DeFT_P, DeFT_B, MTR, RC and XY_SP at each of the nine loads (the best
reference per scenario, size and load), six fault-free scenarios, seeds 121-130; negative = the main row is faster.

| load (x Lsat) | 0.2 | 0.5 | 0.8 | 1.0 | 1.2 | 1.4 | 1.6 | 2.0 | 2.4 |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | +2.0 % | -0.5 % | -0.1 % | -11.0 % | -29.2 % | +1.1 % | +5.9 % | +5.0 % | +7.7 % |
| 3x3 | +1.5 % | 0.0 % | -0.6 % | -9.7 % | -49.7 % | -40.3 % | -11.9 % | +6.0 % | +4.7 % |
| 4x4 | +0.9 % | +0.4 % | +0.7 % | -13.2 % | -39.4 % | -21.8 % | -9.5 % | +8.5 % | +16.6 % |
* Below saturation the main row buys nothing and costs little: 0.9 to 2.0 % slower than the best reference at 0.2 x Lsat
  (which there is XY_SP, shortest paths), within 0.7 % at 0.5 and 0.8 x Lsat.
* The gain is around saturation: 10 to 13 % at 1.0 x Lsat and 29 to 50 % at 1.2 x Lsat, where the main row still delivers
  99 % of the offered load and no reference more than 95 %.
* Far above saturation the sign turns, and the number no longer compares like with like: no row delivers the offered load,
  the mean is that of the packets that arrived, and the main row delivers 2 to 10 % more of them.

### Part E: the early rows under random VL faults (`report/summary_E.md`, `report/extra_E.md`; 2,304 new runs, seeds 151, 152, no dead-end event)
The 48 masks of rate 4/16 of round 26 (16 per size), uniform and hotspot traffic, four loads; `EB_vl`, `EB_route` and `EB_down`
are new runs, the DeFT variants and the main row are the runs of round 26 (`reuse_check.md`: 192 / 192 runs reproduced by
the build of this round). Unit = mask. Descriptive, no test.
* **Under faults the early rows are ahead of DeFT_P and much closer to the main row.** The order of the rows is that of
  the fault-free runs.

  | size | THR against the main row: `EB_vl`, `EB_route`, `EB_down` | LAT against the main row | THR against DeFT_P | share of the main row's THR gain |
  |---|---|---|---|---|
  | 2x2 | -4.9, -4.1, -2.0 % | +22.5, +22.4, +18.4 % | +7.5, +8.3, +10.7 % | 59, 65, 83 % |
  | 3x3 | -5.4, -1.1, -6.6 % | +33.3, +10.5, +70.4 % | +6.2, +11.0, +4.9 % | 52, 90, 41 % |
  | 4x4 | -5.2, -0.5, -6.6 % | +27.9, +6.2, +53.6 % | +7.3, +12.6, +5.8 % | 57, 96, 45 % |
* **The main row is still ahead of every early row** on every size in both metrics; one interval includes 0 (THR against
  `EB_route` on 4x4). `EB_route` has the higher throughput in 6 of the 16 masks of 4x4.
* **The change against the fault-free runs is under uniform traffic.** Under hotspot traffic the early rows reach 73 to
  101 % of the main row's THR gain with faults and 77 to 100 % without. Under uniform traffic `EB_route` reaches 73 and 84 %
  of it on 3x3 and 4x4 with faults and -13 and 11 % without; `EB_vl` and `EB_down` stay level with DeFT_P or behind it
  on those two sizes.
* **There is less to bind late.** Under uniform traffic the main row's own gain over DeFT_P is +4.1 / +6.4 / +7.9 % with
  these faults and +5.2 / +15.2 / +18.6 % without. In the masks with a chiplet that is left one functional VL the early
  rows are within 3.2 % of the main row's throughput on 3x3 and 4x4.
* Against the best of the four DeFT variants only `EB_route` on 3x3 and 4x4 is ahead (THR +2.1 and +4.4 %, LAT -7.2 and
  -13.0 %; the main row +3.2 and +4.9 %, -16.0 and -18.0 %).
* So "the gain needs late binding" is the result without faults. With a quarter of the VLs faulty an injection-time
  choice that reads the queues on the route, with exact and instant knowledge of the whole network, gets most of the
  throughput gain. One fault rate, two traffic patterns, two seeds; `EB_vl64`, which would show what that knowledge is
  worth at a realistic age, was not run under faults.

Start with `results_v27_early/FINDINGS.md` (the thirteen questions, the comparison with what was stated in advance, the
limits). The tables for the paper are in `results_v27_early/paper_data/` (`paper_data/README.md` lists them).

## Round 28 (results_v28_anchor/): the strongest early binder. An early family that contains DeFT, a tuned commit at the Down move, and the reports across the VLs under faults
Round 27's early rows were a weak class of early binders: their family did not contain DeFT (any `oracle_beta` leaves DeFT-P's balanced
table) and they herded (every source read the same state; nothing counted the packets already on their way to a VL). This round builds the
strongest early binder we can and gives it the tuning of the main row: ideal information (global, instantaneous, free), a count of the
packets already bound to each VL, and an anchor at DeFT-P's entry VL with a threshold T, so that the family contains DeFT_P (T = infinity).
Also: the main row without the occupancy reports across the VLs (`LB_noVLrep`) under random VL faults. The frozen configuration of round 25
is not retuned and no existing row is changed. The simulator gets two options and two diagnostics, all off by default
(`results_v28_anchor/regression.md`: the 84-configuration set is byte-identical to the b164e9e build with the options absent and with every
option given at its default). The rows, the tuning rule, the tests and what I expected are fixed in `results_v28_anchor/PREREGISTRATION.md`
(the expectations committed separately before any performance result, `stated_in_advance.md`); its addendum freezes the tuned rows before
Part C.

**The answer.** The strongest early binder reaches the main row on 2x2, where it is slightly ahead, and most of the main row's gain on
3x3 and 4x4: without faults 66 and 75 % of the throughput gain over DeFT_P and 93 and 82 % of the latency gain, and under random VL faults
what it reaches without faults under the same traffic. So round 27's answer ("without faults the gain comes from binding late") was an
answer about early binders that herd; it does not hold for an early binder that counts the packets already bound to each VL. That binder
has to know the whole network at the moment of injection. With the same state 64 cycles old, or with the main row's own information
bound at the Down move, an early row reaches about half of the gain on 3x3 and 4x4. Primary family 1: 10 of 12 supported, 2 against;
primary family 2: 20 of 24 supported, 3 against, 1 not significant; the six tests that are not supported are the ones against `EB_best`
on 2x2. The occupancy reports across the VLs are unnecessary under faults by the margin stated before the runs.

* **New options of `-deft_lb`:** `oracle_bias D` (the cost of an entry candidate that is not DeFT-P's entry VL is raised by D = B x T),
  `oracle_pending 0|1` (one counter per VL of the flits bound to it at injection whose head has not moved Up, added to the occupancy term),
  and `oracle_period P` for `oracle_scope route` and for the counters (a snapshot every P cycles). Diagnostics: `pending_check K` (the
  counters against a scan of the network at three cycles) and `tie_stream 1` (the tie-breaks of the early rows draw from a stream of their
  own instead of `rand()`, from which the routers' crossbar arbitration draws).
* **Rows** (pipe_all 2; every row with DeFT-P's VN options and `-traffic_rng 1`; LUTs `luts/v23`).

  | row | what binds the entry VL, and when |
  |---|---|
  | `DeFT_P` | the LUT, at injection (round 25) |
  | `CI_heurLA_X_LF` (**main**) | the selection on the interposer, hop by hop (round 25, frozen) |
  | `EB_best` | at injection: the entry VL of least hops + B (occupancy + P x pending) + B T [not DeFT-P's VL], the best member of the family by the tuning score |
  | `EB_best64` | `EB_best` with occupancies and pending counts sampled every 64 cycles, T tuned again |
  | `EB_down_t` | `EB_down` of round 27 (the main row until the Down move, where it commits) with its own tuned `lut_bias` |
  | `EB_inf`, `EB_down_inf` | the T = infinity members (anchors): DeFT_P's routing with the row's draws of the random stream |
  | `LB_noVLrep` | the main row without the occupancy reports across the VLs (Part E only) |

* **Drivers.** `experiments_v28.py` (the regression; dispatches to `experiments_v28_eval.py`: the gates `a2_*`, the reuse check `d_reuse`, the
  tuning `b_*`, Parts C, D and E `c_*`, `d_*`, `e_*`). `chain_v28.sh a|b` and `chain_v28c.sh` run the round unattended and stop at the first
  failed check; `restore_v28.py` is the time rule after the timing runs. `report_v28.py` writes `report/` and `paper_data/`;
  `check_v28_family.py` computes both primary families a second time without the report's code (`report/families_check.md`);
  `extra_v28.py` writes the descriptive tables `report/extra_D.md` and `report/extra_E.md` that `FINDINGS.md` quotes (added after the
  results of those parts were seen).
```
bash build_ref.sh b164e9e && python3 experiments_v28.py regress 12 before && make && python3 experiments_v28.py regress 12 after
python3 experiments_v28.py a2_anchor 12 && python3 experiments_v28.py a2_repro 12 && python3 experiments_v28.py a2_units 12
python3 experiments_v28.py a2_drain 12 && python3 experiments_v28.py d_reuse 12
python3 experiments_v28.py b_rule && python3 experiments_v28.py b_tune 12 && python3 experiments_v28.py b_choose && python3 experiments_v28.py a2_drain 12 tuned
python3 experiments_v28.py c_timing 12 && python3 experiments_v28.py c_eval 12 && python3 experiments_v28.py c_check && python3 experiments_v28.py c_csv
python3 experiments_v28.py d_eval 12 && python3 experiments_v28.py d_check && python3 experiments_v28.py d_csv
python3 experiments_v28.py e_eval 12 && python3 experiments_v28.py e_check && python3 experiments_v28.py e_csv
python3 report_v28.py all && python3 check_v28_family.py && python3 extra_v28.py
```
(The raw outputs stay under `~/lbraw/v28` until the stage that writes the CSV; the tuning keeps its state in `~/lbraw/v28/tune_state.json`.)

### Gates
* **Regression** (`regression_before.md`, `regression.md`): 84 / 84 byte-identical to the b164e9e build before the change, and after it with
  the options absent and with every option given at its default.
* **The anchors** (`anchor.md`): the T = infinity members (`oracle_bias 1e9`; `EB_down` with `lut_bias 1e9`) take DeFT-P's entry VL for
  every packet but are byte-identical to DeFT_P in 0 / 21 runs: the routers' crossbar arbitration draws from `rand()`, and the early rows
  draw once more per packet. With their tie-breaks on a stream of their own (`tie_stream 1`) both are identical in 21 / 21. So the families
  contain DeFT_P's routing exactly; the anchor rows `EB_inf` and `EB_down_inf` (DeFT_P with another arbitration sequence) join Parts C and D.
* **Round 27 reproduced** (`repro_v27.md`): 320 / 320 tuning runs identical (two early rows of round 27, DeFT_P, the main row).
* **Unit checks** (`unit_checks.md`): the pending counters equal a scan of the network at three cycles in 12 / 12 runs; the check reads only.
* **Drain tests:** 90 / 90 (`drain_v28.csv`) and 54 / 54 for the tuned rows (`drain_v28_tuned.csv`), every pending counter 0 at the end, no
  dead-end event, no hop of an early row that offers more than one output. **Reuse check** (`reuse_check.md`): 768 / 768 runs of round 26
  reproduced. **Safety** (`FINDINGS.md`, A3): each new row binds one functional entry VL; no new proof or model check is needed.

### Part B: tuning (`tuning_v28.md`; 8,800 runs, seeds 101, 102)
The rule of round 24 on 2x2 and 4x4 (3x3 takes the 4x4 choice). B1: S in {vl, route} x P in {0, 1} x B in {0.5, 1, 2, 4} x T in {0, 2, 4, 8,
16} with the extensions the rule asks for (T to 32 and 64, B to 0.25 and 8); B2: T of `EB_best64`; B3: `lut_bias` of `EB_down_t`.

| | `EB_best` | `EB_best64` | `EB_down_t` | main row (frozen) |
|---|---|---|---|---|
| 2x2: configuration (score) | vl, P 1, B 0.5, T 8 (+0.551) | T 32 (+0.347) | `lut_bias` 4 (+0.260) | (+0.530) |
| 4x4 and 3x3: configuration (score) | vl, P 1, B 1, T 2 (+0.494) | T 16 (+0.345) | `lut_bias` 4 (+0.225) | (+0.648) |
* **The count of the bound packets buys most of it:** at T = 0 the best member scores +0.530 / +0.484 with it and -0.597 / -0.116 without
  it (round 27's rows). **The anchor buys much without the count** (+0.204 / +0.219 at T = 16 / 32) **and little with it** (+0.02 / +0.01).
  Round 27's early rows lost because they herded.
* On the tuning seeds `EB_best` is about level with the main row on 2x2 and has three quarters of its score on 4x4.

### Part C: the evaluation without faults (`report/summary_C.md`; 11,340 runs, seeds 171-180, no dead-end event)
Six fault-free scenarios, nine loads (0.2 to 2.4 x Lsat of DeFT-P), seven rows, ten seeds. The 30 h rule dropped nothing
(`runtime_estimate.md`). Effects are means over the six scenarios with the 95 % interval over the ten seeds.
* **Primary family 1 (Holm over 12: three sizes; the main row against `EB_best` and `EB_down_t`; THR and LAT at 1.0 x Lsat):
  10 of 12 supported, 2 against.** The two against are the tests against `EB_best` on 2x2, where the early row is ahead in
  both metrics. Computed a second time by `check_v28_family.py`: all 12 tests agree.

  | size | THR: the main row against `EB_best`, `EB_down_t` | LAT at 1.0 x Lsat: against `EB_best`, `EB_down_t` |
  |---|---|---|
  | 2x2 | -0.9, +1.8 % | +3.9, -17.7 % |
  | 3x3 | +4.4, +7.1 % | -3.0, -17.1 % |
  | 4x4 | +2.9, +6.4 % | -7.8, -22.5 % |
* **The strongest early binder reaches the main row on 2x2 and most of its gain over DeFT_P on 3x3 and 4x4.** Share of the
  main row's gain that a row reaches (THR / LAT at 1.0 x Lsat; above 100 % = ahead of the main row), 2x2 / 3x3 / 4x4:

  | row | all six scenarios: THR | LAT | hotspot alone: THR | LAT | the other five: THR | LAT |
  |---|---|---|---|---|---|---|
  | `EB_best` | 113 / 66 / 75 % | 109 / 93 / 82 % | 96 / 93 / 95 % | 102 / 98 / 97 % | 129 / 58 / 66 % | 114 / 90 / 74 % |
  | `EB_best64` | 82 / 46 / 58 % | 72 / 48 / 51 % | 97 / 93 / 95 % | 94 / 95 / 95 % | 70 / 31 / 40 % | 56 / 21 / 29 % |
  | `EB_down_t` | 74 / 46 / 46 % | 56 / 58 / 43 % | 83 / 65 / 55 % | 80 / 72 / 72 % | 66 / 41 / 41 % | 37 / 50 / 29 % |

  Against DeFT_P: the main row THR +7.2 / +13.7 / +12.0 %, LAT -35.5 / -35.7 / -36.0 %; `EB_best` +8.2 / +8.8 / +8.9 % and -37.9 /
  -33.8 / -30.6 %; `EB_best64` +5.9 / +6.0 / +6.8 % and -27.1 / -19.0 / -20.4 %; `EB_down_t` +5.3 / +6.1 / +5.3 % and -21.6 / -22.5 /
  -17.5 %. No tuned row is behind DeFT_P on any size (in round 27 every early row was behind it in THR, `EB_down` on 2x2 excepted).
* **`EB_best` is not DeFT with a correction for hot spots.** At 1.0 x Lsat it leaves DeFT-P's entry VL for 24.6 / 49.4 / 49.4 %
  of the packets, in every scenario alike (19.2 / 44.2 / 43.6 % at 0.5 x Lsat; the main row 36.4 / 56.7 / 57.9 %), and it is
  ahead of DeFT_P in THR and LAT in 34 of the 36 cells of size and scenario and level in two. Its VLs are balanced like
  the main row's or better (busiest VL / mean VL 1.28 / 1.32 / 1.40; the main row 1.30 / 1.52 / 1.67, DeFT_P 1.33 / 1.50 /
  1.77), with 1 to 5 % more hops per packet than DeFT_P.
* **Per scenario** (unadjusted intervals): in 42 of the 162 cells (size x scenario x tuned early row x THR, LAT, P99) an early
  row is ahead of the main row (24) or level with it (18). `EB_best` is ahead in THR and LAT under uniform (+3.2 / -3.2 %) and
  localized traffic (+4.8 / -3.9 %) on 2x2, and in LAT under hotspot and movinghot traffic there. On 3x3 and 4x4 it is behind
  in every scenario except movinghot; its largest deficits are chipperm on 3x3 (THR -13.8 %), uniform on 4x4 (THR -6.6 %) and
  chiptrans on 4x4 (LAT +38.9 %). `EB_down_t` is ahead in THR under movinghot traffic on every size (+1.1 / +1.8 / +2.6 %).
* **Old information costs a quarter to a half of the gain.** `EB_best64` against `EB_best`: THR -2.1 / -2.6 / -1.9 %, LAT +17.4 /
  +22.3 / +14.7 %. Under hotspot traffic nothing is lost in THR (+0.2 / 0.0 / +0.1 %); in the other five scenarios THR -2.6 /
  -3.1 / -2.3 % and LAT +19.0 / +26.5 / +17.4 %.
* **`EB_down_t`** (the main row until the Down move, the commit there with its own tuned `lut_bias`) is the weakest tuned
  row: the main row is ahead of it in all six tests, by 1.8 to 7.1 % in THR and 17 to 22 % in LAT. Tuned, it is no longer
  behind DeFT_P as `EB_down` was in round 27; it leaves DeFT-P's entry VL for 5.7 / 4.5 / 3.1 % of the packets.
* **Below saturation** no tuned early row costs anything worth naming: at 0.2 and 0.5 x Lsat each is within 0.9 % of DeFT_P
  or faster, and at 0.8 x Lsat `EB_best` is as fast as the main row (6 to 10 % faster than DeFT_P). At 0.2 and 0.5 x Lsat the
  main row keeps a lead of 1.2 to 2.4 % over `EB_best` on 3x3 and 4x4, where `EB_best` takes 2 to 3 % more hops than DeFT_P.
  **Above DeFT-P's saturation load the main row carries on and `EB_best` does not on 3x3 and 4x4:** at 1.2 x Lsat `EB_best` has
  39 and 35 % more latency than the main row there, at 1.4 x Lsat 47 and 18 % more (2x2: +5.2 and -3.5 %). That is where
  the THR shares of 66 and 75 % come from.
* **The anchors** `EB_inf` and `EB_down_inf` are level with DeFT_P (THR within 0.1 %, LAT within 1.6 %, every interval over
  the six scenarios including 0), so the tuned rows' effects are not an effect of the other draws of the random stream.
* **The main row's gain over DeFT_P is the same on a fourth set of seeds:** THR +7.2 / +13.7 / +12.0 % and LAT -35.5 / -35.7 /
  -36.0 % here; +7.5 / +13.6 / +11.7 % and -35.5 / -37.6 / -37.4 % in round 27.
* THR is the largest accepted throughput over loads up to 2.4 x Lsat; in 24 to 43 of 60 (scenario, seed) cells per size and
  row it is reached at the last load and is then a lower bound, for every row alike. LAT at 1.0 x Lsat of DeFT-P compares
  rows of which some are past their own saturation. Everything outside the primary family is descriptive.

### Part D: the early rows under random VL faults (`report/summary_D.md`, `report/extra_D.md`; 6,912 new runs, seeds 151, 152, no dead-end event)
The 96 masks of the rates 1/16 and 4/16 of round 26 (16 per size and rate), uniform and hotspot traffic, four loads. `EB_best`,
`EB_down_t` and the two anchors at both rates, `EB_best64` at 4/16; the DeFT variants and the main row are the runs of round 26
(`reuse_check.md`: 768 / 768 runs reproduced by the build of this round). Unit = mask. Nothing was dropped by the 30 h rule.
* **Primary family 2 (Holm over 24: three sizes, two rates; the main row against `EB_best` and `EB_down_t`; THR and LAT at
  1.0 x Lsat): 20 of 24 supported, 3 against, 1 not significant.** The four that are not supported are the tests against
  `EB_best` on 2x2. Computed a second time by `check_v28_family.py`: all 24 tests agree.

  | size | rate | THR: the main row against `EB_best`, `EB_down_t` | LAT at 1.0 x Lsat: against `EB_best`, `EB_down_t` |
  |---|---|---|---|
  | 2x2 | 1/16 | -1.7 (against), +1.2 % | +3.1 (against), -14.4 % |
  | 2x2 | 4/16 | -0.3 (n.s.), +2.8 % | +2.2 (against), -14.8 % |
  | 3x3 | 1/16 | +1.3, +6.7 % | -5.2, -26.1 % |
  | 3x3 | 4/16 | +1.5, +4.8 % | -4.4, -24.0 % |
  | 4x4 | 1/16 | +3.9, +9.5 % | -5.6, -22.5 % |
  | 4x4 | 4/16 | +2.5, +6.7 % | -7.6, -27.2 % |
* **Under faults `EB_best` reaches what it reaches without faults.** Share of the main row's gain over DeFT_P, THR and LAT,
  2x2 / 3x3 / 4x4: 113 / 92 / 80 % and 105 / 93 / 91 % at 1/16, 102 / 87 / 80 % and 104 / 92 / 87 % at 4/16; without faults under
  the same two traffic patterns 110 / 85 / 82 % and 104 / 95 / 93 % (`extra_D.md`, descriptive). The shares are larger than
  Part C's because the fault design has uniform and hotspot traffic only. Under hotspot traffic 92 to 101 % and 97 to 103 %
  at every size and rate. Under uniform traffic at 4/16 the share is below the fault-free one on every size (THR 117 / 64 /
  50 % against 158 / 70 / 62 %, LAT 105 / 78 / 61 % against 115 / 88 / 81 %).
* **Against the best of DeFT's four variants on each mask** `EB_best` is ahead at every size and rate (THR +5.1 / +4.2 / +4.8 %
  at 1/16, +2.9 / +1.8 / +2.4 % at 4/16; LAT -21.3 / -13.9 / -14.8 % and -18.7 / -12.2 / -11.3 %); the main row +3.3 / +5.5 / +8.9 %
  and +2.6 / +3.2 / +4.9 %, -18.9 / -18.4 / -19.6 % and -16.9 / -16.0 / -18.0 %. `EB_down_t` is level with the best DeFT variant
  or behind it on 3x3 and 4x4.
* **`EB_down_t`** reaches 91 / 58 / 52 % and 77 / 60 / 48 % of the THR gain and 74 / 59 / 61 % and 73 / 53 / 46 % of the LAT gain;
  the main row is ahead of it in all twelve tests (THR 1.2 to 9.5 %, LAT 14 to 27 %).
* **Old information costs less under faults:** `EB_best64` against `EB_best` at 4/16 THR -0.6 / -0.3 / 0.0 % and LAT +9.8 / +7.7 /
  +4.4 % (without faults under the same traffic -1.6 / -2.5 / -1.6 % and +11.5 / +19.8 / +10.4 %); it reaches 97 / 85 / 80 % of the
  main row's THR gain and 88 / 80 / 79 % of its LAT gain.
* **On 4x4 at 4/16 the tuned row is not the strongest early row** (`extra_D.md` X.2, descriptive, added after the results
  were seen). Round 27's `EB_route`, the member (route, P = 0, T = 0) of this round's family, ran on the same masks: `EB_best`
  against it THR +4.6 / -0.3 / -1.9 %, LAT -20.1 / -5.3 / +1.9 %. On 4x4 `EB_route` is level with the main row in THR (-0.5 %
  [-1.2, +0.1]) and 6.2 % slower, so there the main row's lead over the best early row that was run is a lead in latency
  only. The best member with S = route and the count, (route, P 1, B 0.5, T 4), scored above `EB_best` in the tuning's faulty
  scenario (+0.630 against +0.540) and was not run in Part D.
* **The anchors** are level with DeFT_P (THR within 0.23 %, LAT within 1.7 %; one of 24 intervals excludes 0, barely).
* Two traffic patterns, two seeds, four loads; THR is the largest accepted throughput over loads up to 2.0 x Lsat of DeFT-P
  on the mask. Everything outside the primary family is descriptive.

### Part E: the reports across the VLs under faults (`report/summary_E.md`, `report/extra_E.md`; 3,072 new runs, seeds 151, 152, no dead-end event)
`LB_noVLrep` (the main row with `-deft_lb up_report 0`) on the 192 masks of round 26 (rates 1/16, 2/16, 4/16, 8/16; 16 per size and rate),
uniform and hotspot traffic, four loads; the main row is the runs of round 26. Stated before the runs: the reports are called
unnecessary if at every size and rate the 95 % interval over the masks lies within +-1 % in THR and +-3 % in LAT.
* **They are unnecessary by that margin: all 24 intervals are inside.** The row without the reports is within 0.3 % of the main row
  in THR and in LAT in every cell (THR -0.1 to +0.3 %, LAT -0.2 to +0.3 %). The widest intervals are [-0.1, +0.6] in THR (2x2 at 1/16)
  and [-1.2, +1.9] in LAT (3x3 at 8/16).
* **The same where a chiplet is left one functional VL** (66 of the 192 masks; in the cells with 6 or more such masks THR -0.1 to
  +0.2 % and LAT -0.4 to +0.3 %, every interval including 0) and under each traffic pattern alone (THR -0.2 to +0.4 %, LAT -0.5 to
  +0.8 %).
* **Single masks** lose up to 1.0 % in THR and 5.9 % in LAT and gain up to 1.9 % and 5.0 %, each value from four pairs of runs. The row
  without the reports is behind the main row in 78 of the 192 masks in THR and in 95 in LAT (`extra_E.md`, a table added after the
  results were seen).
* With round 27 (no faults: within 0.2 % in THR and 0.1 % in LAT) this says that the main row does not need the occupancy wires across
  the VLs (12 per VL). The frozen configuration keeps them; no row was changed.

### How much of the gain needs late binding (`FINDINGS.md`, question 12)
* **Against an early binder with ideal information:** none on 2x2. On 3x3 and 4x4 a third and a quarter of the THR gain and 7 and 18 %
  of the LAT gain without faults, 8 to 20 % and 7 to 13 % under faults.
* **With the main row's own information, bound at the Down move instead of hop by hop:** about half (a quarter of the THR gain on
  2x2).
* **How sure.** The direction on each size rests on tests fixed before the runs (both families adjusted by Holm and computed twice) and
  has the same sign on the tuning seeds, on ten fresh seeds and under faults. The sizes of the shares are descriptive. `EB_best` is the
  best member of one family of early binders, so the parts that need late binding are upper bounds; on 4x4 at the rate 4/16 a member
  that the tuning did not choose is level with the main row in THR. And `EB_best` uses what no source has: the fill of every entry
  buffer and the count of every bound packet, at the instant of injection.

Start with `results_v28_anchor/FINDINGS.md` (the twelve questions, the comparison with what was stated in advance, the limits). Every
table of the report is in `results_v28_anchor/report/summary.md`; the tables for the paper are in `results_v28_anchor/paper_data/`
(`paper_data/README.md` lists them).
