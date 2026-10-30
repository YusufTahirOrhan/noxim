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
