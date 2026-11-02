# Pre-registration v19 (Part K): DeFT's boundary round-robin

Committed before K3 and before any evaluation run. The rules below are fixed now. The load points they refer to (`load_points_rr.json`, K4) and the
test loads of K6 (`fault_load_choice.json`) come out of these rules and are committed when they exist, before the run that uses them.

## What is tested
`-deft_vn_rr 1`: DeFT's Algorithm 1 at the boundary router, as its paper states it. A VN0 packet going Horizontal -> Down is reassigned by round-robin, R3 applies to the input VN, and
both round-robin counters are per router. The question is what this changes for DeFT itself and whether our methods still beat a DeFT with the fix. **DeFT is expected to improve, so the primary results of v9 and v10 may not hold.**

## K4: load points
For every size and v9 scenario, DeFT(rho*) with the option, seed 101, by the v5 rule:
* L0 = latency at 0.0002. Lsat = largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse Lsat is <= 0.004, otherwise on the 0.0005 grid.
* Seven loads at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat.

## K5: confirmatory re-evaluation
* **Sizes and scenarios:** as v9. 2x2: the 11 v2 scenarios; 3x3 and 4x4: the 7 v5 scenarios.
* **Loads:** the 7 new load points. **Seeds:** 61-70 (new). **Window:** 2000 + 8000 cycles.
* **Methods** (parameters: `experiments_v10.methods(size)`; they were tuned without the round-robin and are not re-tuned):

  | method | option | scenarios | runs |
  |---|---|---|---|
  | DeFT(rho*), DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G, CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G | on | all | 8 x 1750 |
  | MTR, RC | does not apply | fault-free only | 2 x 1050 |
  | DeFT(rho*) without the option (`DeFT_noRR`) | off | all | 1750 |

  **Runs:** 17,850.
* **Metrics (as v9, v10):**
  1. LAT: mean packet latency at 1.0 x Lsat (4th load).
  2. P99: p99 packet latency at 1.0 x Lsat.
  3. THR: maximum accepted throughput over the 7 loads.

  Effect = 100 x (exp(mean R) - 1) %, with R(s) the mean over the scenarios of the per-seed log ratio; two-sided one-sample t-test over seeds 61-70 (9 df).

### Primary hypotheses (60; Holm over the 60)
* **H1 (12 tests):** on each size, CI_qlLA_G and FULL_qlLA_G have lower LAT and lower P99 than DeFT(rho*) with the round-robin, over all scenarios.
* **H2 (48 tests):** on each size, CI_qlLA_G and FULL_qlLA_G have lower LAT and lower P99 than each of MTR and RC (fault-free scenarios), and DeFT-Dis and DeFT-Ran (all scenarios). The last two with the option.

Supported = significant after Holm with a negative effect. A significant positive effect is reported as a significant result against our method.

### Secondary (unadjusted p values shown, never called significant)
* THR for all primary comparisons.
* DeFT(rho*) with the round-robin against MTR and RC (LAT, P99, THR, fault-free scenarios), as a check against the DeFT paper.
* DeFT(rho*) with against without the round-robin (LAT, P99, THR).
* Ablation: FULL_qlLA_G against DeFT_OE_G (LAT, P99, THR).
* CI_qlLA_G against CI_heurLA_G (LAT, P99, THR).
* Saturation flag per scenario, as v10: accepted at 1.0 x Lsat below 95 % of offered (mean over seeds).
* Tables in the format of `results_v10/report/summary.md`, and a latency-versus-load figure for uniform traffic.

## K6: faults with the round-robin
* **Test loads:** DeFT(rho*) with the option on the v11 masks (5 per (size, k), k = 1, 2, 3), at the 7 new fault-free load points of the pattern, uniform and hotspot, seeds 51-52 (1,260 runs).
  For each (size, k, pattern): the highest load point at which the latency, pooled over the 5 masks and 2 seeds, is at most 3 x the pooled latency at the lowest load point (v14 rule).
* **Confirmatory runs:** the 8 VN-based methods with the option, at the chosen load, seeds 71-75 (new), window 2000 + 8000: 3,600 runs. DeFT's LUT: its rho* LUT of the mask.
* **Hypotheses (18; Holm over the 18):** at every (size, k), CI_qlLA_G and FULL_qlLA_G have a lower mean latency than DeFT(rho*). Unit = (mask, seed), 25 units; value = mean over the two patterns of ln(LAT_variant / LAT_DeFT); two-sided one-sample t-test (24 df).
* **Secondary:** P99, all methods against DeFT(rho*), and the v14 effects next to these.

## K7: PARSEC (descriptive)
Single-application traces as v13: 9 benchmarks, the 700,000-cycle window, masks fault-free and 0x1111, seeds 41-43; DeFT(rho*), CI_qlLA_G and FULL_qlLA_G with the option (162 runs). MTR and RC are reused from `results_v13_apps/app_runs.csv`, since the option does not apply to them. Report: ratios to DeFT(rho*) with the round-robin, per benchmark and as a geometric mean (latency, p99, completion time). No test.

## K3: VC balance (exploratory)
v17 statistics; 2x2 and 4x4, uniform, 1.0 x the old Lsat, seeds 41-43; DeFT, CI_qlLA_G, FULL_qlLA_G, each with and without the option. No test. Expected: interposer and Down VL towards 50:50, Up VL unchanged at 0:100.

## Gating and exclusions
* Evaluation runs only after the model check, the drain tests and the regression have passed. A failure of one of these stops the round.
* A missing run is listed. A seed (K5) or unit (K6) with a missing run in any scenario of a comparison is dropped from that comparison's test, and this is reported.
* The full design is run; it is not reduced.
