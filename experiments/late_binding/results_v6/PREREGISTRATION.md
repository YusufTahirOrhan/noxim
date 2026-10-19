# Pre-registration v6: re-test on 3x3/4x4 with the proposed methods tuned per size

Committed before the step-4 drain tests and before any evaluation run (seeds 31-40). Question: after giving
the late-binding variants the same per-size tuning that the DeFT baseline received in v5, how do they compare
with DeFT_tm(rho*) on 9 and 16 chiplets, and what does learning add?

## Frozen design
* **Sizes:** 3x3 and 4x4 chiplets of 4x4 routers.
* **Scenarios:** the 7 v5 scenarios per size (uniform, localized, hotspot, chipperm, movinghot fault-free;
  uniform and hotspot with one faulty VL per chiplet).
* **Loads:** the 7 v5 load points per scenario (0.2-1.6 x Lsat of DeFT(rho*); `results_v5/load_points.json`),
  not re-measured.
* **Seeds:** 31-40 (new; not used before). Window: 2000 warm-up + 8000 measured cycles.
* **Reference:** DeFT_tm(rho*) with the v5 rho* (3x3: 0, 4x4: 0.003) and its traffic-matched LUTs.
* **Variants, with the parameters tuned in step 2 (`tuning_choice.json`):**
  | size | CI_heurLA (w, busy) | CI_qlLA (alpha, key) | FULL_heurLA (w, busy) | FULL_qlLA (alpha, key) |
  |---|---|---|---|---|
  | 3x3 | (2, 0) | (0.1, chiplet) | (2, 0) | (0.02, chiplet) |
  | 4x4 | (2, 0) | (0.1, chiplet) | (1, 4) | (0.05, chiplet) |
  The QL-LA learners use the (w, busy) of the lookahead heuristic of their scope and size. CI takes its exit
  from the uniform LUT of DeFT's rho* of the size (3x3: 0.01, 4x4: 0.001), as in v5.

## Metrics
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads per seed and scenario
   (capped when the maximum is at the top load and >= 95 % of it; capped cells reported, as v5).

## Primary hypotheses (36)
* Per size, each of CI_heurLA, CI_qlLA, FULL_heurLA, FULL_qlLA vs DeFT_tm(rho*) on LAT, P99, THR (24).
* Per size, CI_qlLA vs CI_heurLA and FULL_qlLA vs FULL_heurLA on LAT, P99, THR (12).

## Test (as v5)
r(s,k) = ln(X_variant / X_reference); R(s) = mean over the 7 scenarios of the size; two-sided one-sample
t-test of R(31..40) against 0 (9 df); effect = 100 x (exp(mean R) - 1) % with a 95 % CI. **Holm over all 36**,
family-wise alpha = 0.05. LAT/P99 lower is better, THR higher is better.

## Secondary (descriptive; unadjusted; never called significant)
* The same comparisons with the v5 (2x2-tuned) parameters, from `results_v5/eval_runs.csv` (seeds 21-30),
  side by side (FULL_qlLA was not run in v5).
* THR without the chipperm scenario; per-scenario tables; VL imbalance (DeFT_tm(rho*) from its DEFT_LB proxy
  at ~0.5 and ~1.0 x Lsat).

## Known limitations fixed in advance
* The tuning used 2 seeds and 4 cells, like all earlier tuning. CI_qlLA's alpha is on the edge of its grid.
* The load points come from DeFT(rho*), not from the tuned variants.
* One window; synthetic traffic; one chiplet size.

## Run-time rule and exclusions
A timing test is run and recorded first. If the estimate exceeds 30 hours, seeds 31-35 are run, analysed
and committed first, then 36-40; the primary analysis is on 31-40. A missing run is listed. A seed with a
missing run in any scenario of a comparison is dropped from that comparison's test, and this is reported.
