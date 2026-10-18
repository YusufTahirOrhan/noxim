# Pre-registration v3: confirmatory test of near-saturation latency

Committed before any v3 simulation run. The hypothesis comes from a *secondary* result of v2
(seeds 1-10): late binding reduces mean and p99 latency at ~1.0 x DeFT's Lsat. v3 tests it on
**new seeds 11-20** with all parameters frozen, as below. Nothing in v1/v2 is changed.

## Frozen design
* **Parameters:** exactly `variants_v2.py` as committed at e2b7f48 (`FROZEN = True`, per-scope
  values from `results_v2/tuning_choice.json`). There is no re-tuning; the exploratory tuning
  of v3 step 4 is not used.
* **Variants run:** DeFT_tm, CI_heur, CI_heurLA, CI_ql, CI_qlLA, FULL_heurLA, FULL_qlLA
  (definitions in variants_v2.py; DeFT_tm uses the traffic-matched LUT of the pattern).
* **Scenarios (11, as v2):** uniform, localized, hotspot, chipperm, movinghot fault-free;
  uniform, hotspot, chipperm on 0x1111 and 0x9C63.
* **Loads:** the 3rd, 4th and 5th v2 evaluation rates of each scenario
  (`results_v2/load_points.json`), i.e. 0.8, 1.0 and 1.2 x DeFT's Lsat snapped to the 0.0005
  grid. The 4th is exactly Lsat.
* **Seeds:** 11-20. Window: 2000 warm-up + 8000 measured cycles (as v2).

## Primary metrics (at 1.0 x Lsat, the 4th v2 rate)
1. **LAT:** mean packet latency (Noxim global average delay).
2. **P99:** 99th-percentile packet latency (deft_lb delay_p99; packets after warm-up).

## Primary comparisons (5 x 2 = 10 hypotheses)
| # | variant | reference | v2 estimate, seeds 1-10 (LAT; P99) |
|---|---|---|---|
| 1 | CI_heur | DeFT_tm | -16.0 % [-18.9, -13.0]; -29.1 % [-35.4, -22.1] |
| 2 | CI_heurLA | DeFT_tm | -19.6 % [-21.6, -17.6]; -32.3 % [-37.1, -27.2] |
| 3 | CI_qlLA | DeFT_tm | -22.1 % [-24.4, -19.7]; -36.8 % [-41.7, -31.6] |
| 4 | CI_qlLA | CI_heurLA | -3.1 % [-5.0, -1.1]; -6.7 % [-12.7, -0.2] |
| 5 | FULL_heurLA | DeFT_tm | -24.8 % [-27.1, -22.5]; -44.9 % [-48.9, -40.6] |

(v2 estimates use the same statistic as below on the v2 data. They were secondary in v2 and
are given here only to state what is being confirmed.)

## Test (identical to v2)
For comparison c, metric m, seed s and scenario k: r(s,k) = ln(X_variant / X_reference).
R(s) = mean of r(s,k) over the 11 scenarios. Two-sided one-sample t-test of R(11..20) against 0
(9 degrees of freedom). The effect is reported as 100 x (exp(mean R) - 1) % with a 95 % t-interval.
Holm step-down over the 10 primary p-values, family-wise alpha = 0.05.

**Confirmation criterion (per hypothesis):** Holm-adjusted p < 0.05 **and** the effect has the
same sign as in v2 (negative = lower latency). A significant effect of the opposite sign is
reported as a contradiction. A non-significant effect is reported as "not confirmed".

## Secondary (descriptive; unadjusted 95 % intervals; never called significant)
* LAT and P99 at 0.8 and 1.2 x Lsat for the 5 primary comparisons.
* **Accepted throughput (max over the three loads).** This is *not* the v2 saturation
  throughput: the sweep stops at 1.2 x Lsat, so it is heavily capped. A cell counts as
  capped when the maximum is at the 1.2 x load and is >= 95 % of it.
* CI_ql and FULL_qlLA: vs DeFT_tm, and vs their heuristics (CI_heur, FULL_heurLA), on all
  metrics.
* Per-scenario paired differences for every comparison.
* **Window sensitivity.** DeFT_tm, CI_heurLA and CI_qlLA on uniform, hotspot and movinghot
  (fault-free) at 1.0 x Lsat, seeds 11-15, with 40000 measured cycles (2000 warm-up +
  40000). Statistic: per scenario, the paired log ratio of CI_heurLA and CI_qlLA vs DeFT_tm
  for LAT and P99, mean and 95 % CI over the 5 seeds, at 40000 cycles and at 8000 cycles (the
  same seeds from the main runs).
  *Pre-stated reading:* a near-Lsat difference is called a possible short-window artefact if,
  at 40000 cycles, its sign flips, or its interval includes 0 while the 8000-cycle interval
  excludes it. Otherwise it is "consistent across windows".

## Known limitations (fixed in advance)
* At 1.0 x Lsat DeFT itself is at its knee by construction; any variant may be beyond its
  own knee in some scenarios. The fixed-window latency is then not a steady state. The window
  sensitivity check addresses this only partly (3 scenarios, 5 seeds).
* DeFT_tm equals DeFT on uniform, localized and movinghot (identical LUT).
* The same topology instance, window and traffic patterns as v2.

## Exclusions
None planned. A missing run is listed; a seed with a missing run in any scenario of a
comparison is dropped from that comparison's primary test, and this is reported.
