# Pre-registration v7: bounded-deviation entry for interposer-only late binding

Committed before the drain tests of the chosen configurations and before any evaluation run of them (step 5).
Question: does restricting CI's entry candidates at injection to entries close in path length (v6 bottleneck
hypothesis: the router-local entry choice drifts away from the balanced LUT entry) recover saturation throughput
against DeFT_tm(rho*) on 9 and 16 chiplets, and what does it cost in latency against the unbounded parents?

## Frozen design
* **Sizes:** 3x3 and 4x4 chiplets of 4x4 routers.
* **Scenarios:** the 7 v5 scenarios per size (uniform, localized, hotspot, chipperm, movinghot fault-free; uniform
  and hotspot with one faulty VL per chiplet).
* **Loads:** the 7 v5 load points per scenario (0.2-1.6 x Lsat of DeFT(rho*); `results_v5/load_points.json`).
* **Seeds:** 31-40 (the v6 seeds). Window: 2000 warm-up + 8000 measured cycles.
* **Reference and parents, reused from `results_v6/eval_runs.csv`:** DeFT_tm(rho*) (v5 rho*, traffic-matched LUTs),
  CI_heurLA and CI_qlLA with the v6 tuned parameters (3x3 and 4x4: (w 2, busy 0); alpha 0.1, key chiplet). Reuse is
  valid because the simulator is deterministic: 20 / 20 re-run v6 runs were identical (`determinism.md`), and with
  `entry_bound_mode off` the new binary is identical to the v6 one on 198 / 198 regression runs (`regression.md`).
* **New variants**, the step 3 choice (`selection_choice.json`), applied unchanged on both sizes:
  * **CI_heurLA_B** = CI_heurLA + `-deft_lb entry_bound_mode lut -deft_lb entry_bound_k 4`
  * **CI_qlLA_B** = CI_qlLA + `-deft_lb entry_bound_mode min -deft_lb entry_bound_k 4`
  (step 3 on 4x4, seeds 101/102: THR +1.3 % / +2.1 % and LAT -0.2 % / -4.5 % against the parents; `selection.md`.)
  CI's exit and the bound's e_LUT come from the uniform LUT of DeFT's rho* of the size (3x3: 0.01, 4x4: 0.001).

## Metrics (as v6)
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads per seed and scenario (capped
   when the maximum is at the top load and >= 95 % of it; capped cells reported).

## Primary hypotheses (24)
* Per size, CI_heurLA_B and CI_qlLA_B vs DeFT_tm(rho*) on LAT, P99, THR (12).
* Per size, CI_heurLA_B vs CI_heurLA and CI_qlLA_B vs CI_qlLA on LAT, P99, THR (12).

## Test (as v6)
r(s,k) = ln(X_variant / X_reference); R(s) = mean over the 7 scenarios of the size; two-sided one-sample t-test of
R(31..40) against 0 (9 df); effect = 100 x (exp(mean R) - 1) % with a 95 % CI. **Holm over all 24**, family-wise
alpha = 0.05. LAT/P99 lower is better, THR higher is better.

## Secondary (descriptive; unadjusted; never called significant)
* THR without the chipperm scenario; per-scenario tables.
* Entry candidates after bounding per scenario and load.
* VL imbalance at 1.0 x Lsat over **all** VLs (the v4-v6 column covered VL ids 0-15 only, DECISIONS.md 9), with the
  references re-run for their VL counts (DeFT_tm(rho*) via its DEFT_LB proxy, CI_heurLA, CI_qlLA; seeds 31-40).
* The bottleneck comparison of step 2 (`bottleneck.md`).

## Hypothesis test of the v6 explanation (stated in advance)
The v6 hypothesis is counted as **supported** if, on 4x4, the bounded variants (a) reduce CI's interposer link load
and its centre concentration (step 2, uniform at 1.0 x Lsat, towards the DeFT_tm(rho*) values) **and** (b) raise
saturation throughput significantly against their unbounded parents (primary test). If (a) holds without (b), the
mechanism is shown to exist but not to explain the throughput gap; if neither holds, the hypothesis is not supported.

## Known limitations fixed in advance
* The bound was selected on 4x4 only (seeds 101/102, 5 loads) and is applied unchanged on 3x3.
* The load points come from DeFT(rho*), not from the bounded variants.
* One window; synthetic traffic; one chiplet size.

## Run-time rule and exclusions
A timing test is run and recorded first. If the estimate exceeds 14 hours, 4x4 is run and analysed first, then 3x3.
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison's
test, and this is reported.
