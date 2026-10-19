# Pre-registration v5: re-test against a tuned DeFT baseline

Committed before the drain tests (step 5) and before any evaluation run (seeds 21-30). Question: do the
v2-v4 conclusions about late binding hold when the DeFT baseline gets the same tuning effort as the
other methods (its LUT weight rho tuned per size, `tuning.md`)?

## Frozen design
* **Baselines (rho* from `tuning_choice.json`, chosen on seeds 101/102):**
  | size | DeFT rho* (uniform LUT) | DeFT_tm rho* (traffic-matched LUT) |
  |---|---|---|
  | 2x2 | 0.01 | 0.01 |
  | 3x3 | 0.01 | 0 |
  | 4x4 | 0.001 | 0.003 |
  LUTs: `luts/v5/lut_{size}_rho{rho}[_tm_{hotspot|chipperm}].yaml`. localized and movinghot use the
  uniform LUT (identical to their traffic-matched LUT).
* **Variants:** CI_heur, CI_heurLA, CI_qlLA, FULL_heurLA with the parameters frozen in `variants_v2.py`
  (no re-tuning). The CI variants take their exit VL from the uniform LUT of DeFT's rho* of the size.
  FULL_heurLA does not use the LUT.
* **Sizes and scenarios:** 2x2 (the 11 v2 scenarios: uniform, localized, hotspot, chipperm, movinghot
  fault-free; uniform, hotspot, chipperm with masks 0x1111 and 0x9C63); 3x3 and 4x4 (the 7 v4 scenarios:
  uniform, localized, hotspot, chipperm, movinghot fault-free; uniform and hotspot with one faulty VL
  per chiplet).
* **Loads:** 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat, where Lsat is re-measured per size and scenario
  with DeFT(rho*), seed 101, using the v4 rule including its amendment (L0 at rate 0.0002; 0.0001 grid
  where the coarse Lsat is <= 0.004) (`load_points.md`).
* **Seeds:** NEW seeds 21-30 (never used before). Window: 2000 warm-up + 8000 measured cycles.

## Primary metrics
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput: per seed and scenario, the maximum accepted throughput over the 7
   loads. A cell is capped when the maximum is at the top load and >= 95 % of it; capped cells are
   counted and reported.

## Primary comparisons (4 variants x 3 metrics x 3 sizes = 36 hypotheses)
Each of CI_heur, CI_heurLA, CI_qlLA, FULL_heurLA vs **DeFT_tm(rho*)** of the same size.

## Test (as v2-v4)
r(s,k) = ln(X_variant / X_reference) per seed s and scenario k. R(s) = mean over the scenarios of the size.
Two-sided one-sample t-test of R(21..30) against 0 (9 df). The effect is reported as 100 x (exp(mean R) - 1) %
with a 95 % CI. **Holm over all 36 p-values**, family-wise alpha = 0.05. LAT and P99: lower is better;
THR: higher is better.

## Secondary (descriptive; unadjusted; never called significant)
* **DeFT(rho*) (uniform LUT, no traffic knowledge) as an alternative reference.** It is run where its
  LUT differs from DeFT_tm's (3x3 and 4x4: every scenario, since the two rho* differ; 2x2: hotspot and
  chipperm scenarios). Elsewhere the two runs are identical by construction, and the DeFT_tm run is used.
* **The rho = 0.01 results of v2 (2x2) and v4 (3x3, 4x4)** for the same comparisons, side by side (seeds
  1-10; a different seed set and, on 2x2, different load points).
* Saturation throughput without the chipperm scenario.
* VL usage imbalance (DeFT_tm(rho*) from a traffic-identical DEFT_LB proxy at ~0.5 and ~1.0 x Lsat).
* Per-scenario paired differences.

## Known limitations fixed in advance
* rho was tuned on 2 seeds over 4 cells, like every other parameter. On 3x3 the choice for DeFT_tm is
  partly noise between equally balanced LUTs.
* The late-binding variants are not re-tuned for 3x3 and 4x4 (unchanged from v4). The baseline now is.
* As before: one window, synthetic traffic, one chiplet size; the 3x3 chipperm middle chiplet maps to
  itself.

## Run-time rule and exclusions
A timing test is run and recorded first. If the estimate exceeds 12 hours, seeds 21-25 are run and
analysed first, then 26-30; the primary analysis is on seeds 21-30. A missing run is listed. A seed
with a missing run in any scenario of a comparison is dropped from that comparison's test, and this is
reported.
