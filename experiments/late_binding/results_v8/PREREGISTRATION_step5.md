# Pre-registration v8 step 5: layer-weighted hop cost (gamma)

Committed before the drain tests and any evaluation run of the _G variants. Question: does weighting interposer hops
more than chiplet hops in the selection's static remaining-path cost (hypothesis: CI's equal hop weights move
destination-chiplet hops onto the interposer, the bottleneck layer) raise saturation throughput on 9 and 16 chiplets
without giving up the latency benefit?

## Frozen design
* **Sizes:** 3x3 and 4x4 chiplets of 4x4 routers.
* **Scenarios:** the 7 v5 scenarios per size. **Loads:** the 7 v5 load points per scenario.
* **Seeds:** 31-40 (the v6 seeds). Window: 2000 warm-up + 8000 measured cycles.
* **Reference and parents, reused from `results_v6/eval_runs.csv`:** DeFT_tm(rho*), and CI_heurLA, CI_qlLA, FULL_qlLA
  with the v6 tuned parameters (gamma = 1). Valid because the simulator is deterministic (v7: 20 / 20 and 280 / 280
  re-run v6 runs identical) and with gamma = 1 the v8 binary is identical to v6/v7's (regression.md: 198 / 198 runs;
  step 3: 4 / 4 re-run parent cells identical).
* **New variants**, the step 3 choice (`selection_choice.json`, 4x4, seeds 101/102), applied unchanged on both sizes:
  * **CI_heurLA_G** = CI_heurLA + `-deft_lb hop_weight_ipos 2.0`
  * **CI_qlLA_G** = CI_qlLA + `-deft_lb hop_weight_ipos 2.0`
  * **FULL_qlLA_G** = FULL_qlLA + `-deft_lb hop_weight_ipos 2.0`
  CI's exit comes from the uniform LUT of DeFT's rho* of the size (3x3: 0.01, 4x4: 0.001); the same LUT file is passed
  to the FULL runs, which do not use it.

## Metrics (as v6)
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads per seed and scenario (capped when
   the maximum is at the top load and >= 95 % of it; capped cells reported).

## Primary hypotheses (36)
* Per size, each _G variant vs DeFT_tm(rho*) on LAT, P99, THR (18).
* Per size, each _G variant vs its gamma = 1 parent on LAT, P99, THR (18).

## Test (as v6)
r(s,k) = ln(X_variant / X_reference); R(s) = mean over the 7 scenarios of the size; two-sided one-sample t-test of
R(31..40) against 0 (9 df); effect = 100 x (exp(mean R) - 1) % with a 95 % CI. **Holm over all 36**, family-wise
alpha = 0.05. LAT/P99 lower is better, THR higher is better.

## Verdict on the hypothesis (fixed in the task)
The hypothesis counts as **supported** only if, on 4x4, at least one _G variant has a significantly higher THR than
its parent (primary test) **and** its interposer link load in step 4 is closer to DeFT_tm(rho*)'s than its parent's.
For the second condition the step-4 cell is 4x4 uniform at 1.0 x Lsat, the cell of the v6/v7 diagnosis
(`bottleneck_closeness.json` also lists the other five cells, reported descriptively).

## Secondary (descriptive; unadjusted)
* Against plain DeFT(rho*) (step 1 runs, `deft_runs.csv`) for the _G variants and the parents.
* THR without chipperm; per-scenario tables.
* VL imbalance at 1.0 x Lsat over all VLs: DeFT_tm(rho*) (proxy), CI_heurLA and CI_qlLA from
  `results_v7/vlref_runs.csv`; FULL_qlLA re-run for its VL counts (140 runs, `vlref_runs.csv`).

## Known limitations fixed in advance
* gamma was selected on 4x4 only (2 seeds, 5 loads) and is applied unchanged on 3x3.
* The load points come from DeFT(rho*).
* One window; synthetic traffic; one chiplet size.

## Run-time rule and exclusions
A timing test is run and recorded first. If the estimate exceeds 14 hours, 4x4 is run and analysed first, then 3x3.
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison's
test, and this is reported.
