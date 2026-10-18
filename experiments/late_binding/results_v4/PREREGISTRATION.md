# Pre-registration v4: replication on larger systems

Committed before the saturation sweep and before any evaluation run of v4. The question: do the
v2/v3 results (late binding vs the traffic-matched DeFT) hold on 9 and 16 chiplets?

## Frozen design
* **Parameters:** exactly `variants_v2.py` as committed (FROZEN = True, per-scope values of
  results_v2/tuning_choice.json); no re-tuning. A_oracle and the learners other than CI_qlLA are
  not run.
* **LUTs:** every DeFT-based decision uses the LUT generated for the size
  (`luts/lut_{3x3,4x4}_rho001.yaml`; rho = 0.01, masks fault-free and north per chiplet). DeFT_tm
  uses the traffic-matched LUT of the size and pattern (`luts/lut_{size}_rho001_tm_{pattern}.yaml`).
  The CI exit uses the uniform LUT of the size, as in v2.
* **Variants run:** DeFT, DeFT_tm, CI_heur, CI_heurLA, CI_qlLA, FULL_heurLA. DeFT is run for the Lsat
  measurement and as context (DeFT_tm vs DeFT is secondary).
* **Sizes:** 3x3 and 4x4 chiplets of 4x4 routers (Noxim -deft_chiplets_x/-y; 144 or 256 chiplet
  routers on a 12x12 or 16x16 interposer; 36 or 64 VLs).
* **Scenarios per size (7):** uniform, localized, hotspot, chipperm and movinghot fault-free;
  uniform and hotspot with one faulty VL per chiplet (north slot; mask 0x111111111 on 3x3,
  0x1111111111111111 on 4x4). Patterns as defined in gen_traffic.py for C chiplets.
* **Loads:** 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x DeFT's Lsat measured per size and scenario (DeFT,
  seed 101, the v2 criterion: largest swept rate before the mean latency first exceeds 3x the
  latency at rate 0.001; 0.0005 grid), snapped to the 0.0005 grid.
* **Seeds:** 1-10 (paired). Window: 2000 warm-up + 8000 measured cycles (as v2).

## Primary metrics
1. **LAT:** mean packet latency at 1.0 x Lsat (the 4th load).
2. **P99:** 99th-percentile packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput: per seed and scenario, the maximum accepted throughput over the
   7 loads (capped when the maximum is at the top load and >= 95 % of it; capped cells are counted
   and reported, as in v2).

## Primary comparisons (per size; 4 x 3 metrics x 2 sizes = 24 hypotheses)
| # | variant | reference |
|---|---|---|
| 1 | CI_heur | DeFT_tm |
| 2 | CI_heurLA | DeFT_tm |
| 3 | CI_qlLA | DeFT_tm |
| 4 | FULL_heurLA | DeFT_tm |

## Test (as v2/v3)
For comparison c, metric m, size z, seed s and scenario k: r(s,k) = ln(X_variant / X_reference).
R(s) = mean of r(s,k) over the 7 scenarios of size z. Two-sided one-sample t-test of R(1..10)
against 0 (9 degrees of freedom); effect = 100 x (exp(mean R) - 1) % with a 95 % t-interval.
**Holm over all 24 p-values**, family-wise alpha = 0.05. A result is significant only if its
Holm-adjusted p < 0.05. For LAT and P99 lower is better; for THR higher is better.

Reading against v2/v3 (descriptive): for each comparison and metric, the 2x2 estimate from earlier
runs is shown next to 3x3 and 4x4. LAT and P99 at 1.0 x Lsat come from v3 (seeds 11-20) and v2
(seeds 1-10, secondary there); THR comes from v2. The earlier 2x2 scenarios were 11, not 7, so
those values are context, not a matched comparison.

## Secondary (descriptive; unadjusted intervals; never called significant)
* CI_qlLA vs CI_heurLA (all three metrics, both sizes).
* DeFT_tm vs DeFT.
* VL usage imbalance (max/mean over functional VLs) at ~0.5 and ~1.0 x Lsat. For DeFT_tm it comes
  from a traffic-identical DEFT_LB proxy with the same LUT pairs.
* LAT and P99 at the other loads, per-scenario paired differences, latency-vs-load curves.
* How each primary effect changes with system size: 4 chiplets (2x2, earlier runs), 9 and 16.

## Known limitations (fixed in advance)
* No re-tuning for the larger systems: parameters tuned on 2x2 may be sub-optimal at 9 and 16
  chiplets (for any variant, including the heuristics' weights). This favours none of the
  primary comparisons in a known direction.
* For an odd number of chiplets (3x3), chipperm maps the middle chiplet to itself.
* The 0.0005 load grid limits the resolution of Lsat in scenarios that saturate early.
* Saturation throughput is capped at 1.6 x DeFT's Lsat (as in v2).
* One window length; one chiplet size (4x4 routers).

## Run-time rule
A short timing test is run first and recorded. If the full estimate exceeds 12 hours, seeds 1-5
are run and analysed first, then seeds 6-10. The primary analysis is on seeds 1-10.

## Exclusions
None planned. A missing run is listed; a seed with a missing run in any scenario of a comparison is
dropped from that comparison's primary test, and this is reported.
