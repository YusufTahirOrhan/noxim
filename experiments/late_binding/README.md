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
