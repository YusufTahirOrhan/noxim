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
