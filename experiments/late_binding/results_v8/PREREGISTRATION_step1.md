# Pre-registration v8 step 1: plain DeFT(rho*) as a second reference (seeds 31-40)

Committed before any DeFT(rho*) run on seeds 31-40. Question: how do the four late-binding variants with the v6 tuned
parameters compare with the plain DeFT baseline (one uniform LUT for every traffic pattern), i.e. the baseline that
does not know the traffic, rather than the traffic-matched DeFT_tm(rho*)?

## Frozen design
* **Sizes:** 3x3 and 4x4 chiplets of 4x4 routers.
* **Scenarios:** the 7 v5 scenarios per size (uniform, localized, hotspot, chipperm, movinghot fault-free; uniform
  and hotspot with one faulty VL per chiplet).
* **Loads:** the 7 v5 load points per scenario (`results_v5/load_points.json`; they come from DeFT(rho*) itself).
* **Seeds:** 31-40. Window: 2000 warm-up + 8000 measured cycles.
* **Reference: DeFT(rho*)**: DEFT routing (XY, LUT-fixed VL pair) with the uniform LUT of DeFT's v5 rho* of the size
  (3x3: rho 0.01, 4x4: rho 0.001) for **every** scenario. These are the LUTs that CI already uses for its exit. 980
  new runs.
* **Variants (runs reused from `results_v6/eval_runs.csv`):** CI_heurLA, CI_qlLA, FULL_heurLA, FULL_qlLA with the v6
  tuned parameters (`results_v6/tuning_choice.json`). The reuse is valid: the simulator is deterministic (v7: 20 / 20
  and 280 / 280 re-run v6 runs identical).

## Metrics (as v6)
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads per seed and scenario (capped
   when the maximum is at the top load and >= 95 % of it; capped cells reported).

## Primary hypotheses (24)
Per size, each of CI_heurLA, CI_qlLA, FULL_heurLA, FULL_qlLA vs DeFT(rho*) on LAT, P99, THR.

## Test (as v6)
r(s,k) = ln(X_variant / X_DeFT); R(s) = mean over the 7 scenarios of the size; two-sided one-sample t-test of
R(31..40) against 0 (9 df); effect = 100 x (exp(mean R) - 1) % with a 95 % CI. **Holm over the 24**, family-wise
alpha = 0.05. LAT/P99 lower is better, THR higher is better.

## Secondary (descriptive; unadjusted)
* The v6 table against DeFT_tm(rho*) side by side, and DeFT_tm(rho*) vs DeFT(rho*) (what traffic matching buys).
* THR without chipperm; per-scenario tables.

## Exclusions
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison's
test, and this is reported.
