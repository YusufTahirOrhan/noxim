# Pre-registration v21: DEFT_FAST

Committed before any tuning run and before any evaluation run of `DEFT_FAST`. N_fast comes from the timing (`n_fast.json`, `timing.md`) and is fixed here, before any performance number of this selection is known. The short smoke runs of the code were not looked at for performance.

## N_fast: fixed before tuning
| variant | N_fast | age of the registered terms (extra cycles) | what sets it |
|---|---|---|---|
| CI_fast | 2 | 2 | one router type misses the cut by 0.02 ns: 4x4 interposer with a VL, first stage 1.02 ns. Every other CI_fast router fits N = 1 |
| CI_fastQL | 3 | 2 | first decision stage 1.12-1.16 ns on 3x3, 4x4; Q read in stage A up to 1.15 ns |
| FULL_fast | 2 | 1 | stage A on chiplet routers, 1.5-1.9 ns; the decision fits one cut |
| FULL_fastQL | 3 | 2 | both |

The rule is in `DECISIONS.md`. **No variant decides within one cycle.** If the RTL is re-synthesised with the tuned (w, beta) and a value changes, the larger N applies and the tuning is not repeated.

## F4.1 Tuning (seeds 101, 102)
* v6 protocol: uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; ~0.8 and ~1.1 x Lsat of `load_points_rr.json`; 16 runs per configuration; criterion: the geometric mean of the mean latency.
* All runs with `-deft_vn_rr 1` and each variant's N_fast and age.
* **Heuristic:** w in {0.5, 1, 2} x beta in {0, 4, 8} per size and scope, plus the v6 one-step extension where the optimum lies on an extendable edge.
* **Learners:** alpha in {0.005, 0.01, 0.02, 0.05, 0.1}, with (w, beta) of the heuristic of the scope and size, key = destination chiplet, 16-bit residuals (F = 10, 8, 8).
* **Chosen variant per size and scope for the primary hypotheses:** the lower criterion of the tuned heuristic and the tuned learner, each at its own N_fast.

## F4.2 Confirmatory design
Sizes, scenarios and loads of K5 (`load_points_rr.json`). **Seeds 81-90 (new).** Window 2000 + 8000 cycles.

| methods | scenarios | seeds | runs | order |
|---|---|---|---|---|
| DeFT(rho\*) with `-deft_vn_rr 1`, MTR, RC | all; MTR and RC fault-free | 81-90 | 3,850 | first |
| CI_fast, CI_fastQL, FULL_fast, FULL_fastQL at N_fast | all | 81-90 | 7,000 | first |
| DeFT-Dis, DeFT-Ran with the option | all | 81-90 | 3,500 | second |
| CI_fast at N = 1, age 1 (secondary) | all | 81-85 | 875 | third |
| each variant at N_fast + 1, same age | all | 81-85 | 3,500 | fourth |

**Runs:** 18,725. Baselines are re-run on these seeds, after 20 K5 baseline runs reproduce exactly on the current binary. Tuned drain tests pass before the runs start.

## Metrics (as K5)
LAT: mean latency at 1.0 x Lsat. P99: p99 latency at 1.0 x Lsat. THR: maximum accepted over the 7 loads. LOW: mean latency at 0.2 x Lsat. Effect = 100 x (exp(mean R) - 1) %, R(s) the mean over the scenarios of the per-seed log ratio; two-sided one-sample t-test over seeds (9 df).

## Primary hypotheses (36; Holm over the 36)
On each size, for the chosen variant of each scope (CI and FULL):
* **H1 (12 tests):** lower LAT and lower P99 than DeFT(rho\*) with the round-robin, all scenarios.
* **H2 (24 tests):** lower LAT and lower P99 than each of MTR and RC, fault-free scenarios.

Supported = significant after Holm with a negative effect. A significant positive effect is reported as significant against our method.

## Secondary (unadjusted, never called significant)
* THR for all primary comparisons.
* **LOW against DeFT(rho\*), MTR and RC, now pre-registered:** this is where v20 found that one extra cycle reverses the gain.
* All four variants against DeFT(rho\*), MTR, RC, DeFT-Dis and DeFT-Ran, on LAT, P99, THR and LOW.
* DeFT(rho\*) with the round-robin against MTR and RC.
* N_fast against N_fast + 1, seeds 81-85. CI_fast at N = 1, seeds 81-85, labelled: it **misses the timing** by 0.02 ns on one router type, so it is not the design's measured N.
* Saturation flags as v10. The latency-versus-load figure.

## What FINDINGS.md must answer
Does a selection this fast keep a latency gain over DeFT, at saturation and at low load? At what area cost, in the form the simulator models (one unit per port) and in the smaller form with one unit per router?

## Time rule
Aim: committed by Wednesday night, 4 November. If the runs cannot finish, the analysis uses what is complete, in the order above, and the summary says what is still running. Nothing is dropped from the design without being stated.

## Exclusions
A missing run is listed. A seed with a missing run in a scenario of a comparison is dropped from that comparison's test, and this is reported.
