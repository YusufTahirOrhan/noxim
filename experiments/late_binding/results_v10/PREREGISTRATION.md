# Pre-registration v10 Part B: comparison with the baselines of the DeFT paper

Committed before any Part B evaluation run. The baselines are implemented as in `BASELINES_DESIGN.md` and passed the
A5 checks (regression, v9 reuse, drain tests 246 / 246). The A5 sanity check found MTR and RC faster than DeFT(rho*) on
2x2 uniform (`sanity_check.md`); this is known before the evaluation and does not change the design.

## Frozen design
* **Sizes and scenarios:** as v9. 2x2: the 11 v2 scenarios; 3x3 and 4x4: the 7 v5 scenarios.
* **Loads:** the 7 v5 load points (`results_v5/load_points.json`).
* **Seeds:** 41-50. Window: 2000 warm-up + 8000 measured cycles.
* **Methods:**

  | method | scenarios | runs |
  |---|---|---|
  | MTR, RC | fault-free scenarios only (2x2: 5, 3x3: 5, 4x4: 5) | new |
  | DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G | all v9 scenarios | new |
  | DeFT(rho*), CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G | all v9 scenarios | reused from `results_v9/eval_runs.csv` (A5: 20 / 20 identical) |

  Parameters: `experiments_v10.methods(size)`. DeFT_OE_G is FULL_qlLA_G with the exit and entry fixed by DeFT's
  rho* uniform LUT of the size.
* **New runs:** 2 x 15 x 7 x 10 + 4 x 25 x 7 x 10 = 9100.

## Metrics (as v9)
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads (cap rule as v5).

Effect = 100 x (exp(mean R) - 1) %, with R(s) the mean over the scenarios of the per-seed log ratio; two-sided
one-sample t-test over seeds 41-50.

## Primary hypotheses (48; Holm over the 48)
On each size, CI_qlLA_G and FULL_qlLA_G have lower LAT and lower P99 than each of:
* MTR and RC, over the fault-free scenarios of the size;
* DeFT-Dis and DeFT-Ran, over all scenarios of the size.

2 variants x 4 baselines x 2 metrics x 3 sizes = 48 tests. A hypothesis is supported if its test is significant
after Holm with a negative effect. A significant positive effect is reported as a significant result against our
method.

## Ablation hypothesis (6; Holm over the 6, separately)
On each size, FULL_qlLA_G has lower LAT and lower P99 than DeFT_OE_G over all scenarios. Same pair, only late binding
differs.

## Secondary (descriptive; unadjusted p values shown, never called significant)
* THR for all primary and ablation comparisons.
* XY-SP against CI_qlLA_G and FULL_qlLA_G (LAT, P99, THR).
* DeFT(rho*) against each baseline (LAT, P99, THR), as a check of the DeFT paper's claims.
* **Saturation flag:** a method "saturates below 1.0 x Lsat" in a scenario if its accepted throughput at 1.0 x Lsat is
  below 95 % of the offered load (mean over seeds). Its LAT is reported as measured and flagged. Its own saturation
  load is the largest load of the sweep at which accepted >= 95 % of offered (as a multiple of Lsat).
* Per-size tables: all methods (rows) by LAT, P99, THR, with the effect against DeFT(rho*) and its unadjusted p.
* The reachability figure of A6.

## Runtime
A timing test is run and recorded first. The full design is run; it is not reduced. Sharding over two machines is
allowed (`--shard i/n`; results per run are machine-independent).

## Exclusions
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison's
test, and this is reported.
