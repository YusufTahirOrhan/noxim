# Pre-registration: second A/B/C evaluation (results_v2)

Written and committed before any evaluation run (seeds 1-10) was started. Tuning used only
seeds 101 and 102; the load points come from DeFT runs with seed 101 (`load_points.md`). The
analysis below is fixed now. Anything not listed under "Primary" is secondary and is reported
descriptively, never as significant.

## Design
* Variants (11): DeFT, DeFT_tm, A_oracle, CI_heur, CI_heurLA, CI_ql, CI_qlLA, FULL_heur,
  FULL_heurLA, FULL_ql, FULL_qlLA. Frozen parameters: `variants_v2.py`
  (`tuning_choice.json`). A_oracle is an unimplementable upper bound for injection-time
  choice and is not in the primary set.
* Scenarios (11): uniform, localized, hotspot, chipperm, movinghot on the fault-free network;
  uniform, hotspot and chipperm on fault masks 0x1111 and 0x9C63.
* Loads: 7 per scenario at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x DeFT's Lsat for that scenario
  (`load_points.json`).
* Seeds: 1-10 (paired: the same seed for every variant). 2000 warm-up + 8000 measured cycles.

## Primary metrics
1. **Saturation throughput (THR):** per seed and scenario, the maximum accepted throughput
   (flits/node/cycle) over the 7 loads. Higher is better.
2. **Latency at ~0.5 Lsat (LAT):** per seed and scenario, the mean packet latency at the 2nd
   evaluation load (0.5 x Lsat snapped to the 0.0005 grid). Lower is better.

## Primary comparisons (8 x 2 metrics = 16 hypotheses)
| # | variant | reference | question |
|---|---|---|---|
| 1 | CI_heur | DeFT_tm | stateless heuristic (CI) vs the traffic-matched DeFT |
| 2 | CI_heurLA | DeFT_tm | lookahead heuristic (CI) vs DeFT_tm |
| 3 | FULL_heurLA | DeFT_tm | lookahead heuristic (FULL) vs DeFT_tm |
| 4 | CI_ql | CI_heur | learning alone, router-local information (CI) |
| 5 | FULL_ql | FULL_heur | learning alone, router-local information (FULL) |
| 6 | CI_qlLA | CI_heurLA | learning alone, lookahead information (CI) |
| 7 | FULL_qlLA | FULL_heurLA | learning alone, lookahead information (FULL) |
| 8 | DeFT_tm | DeFT | value of matching the LUT to the traffic |

## Test
For comparison c, metric m, seed s and scenario k, let r(s,k) = ln(X_variant / X_reference).
Per seed, R(s) = mean of r(s,k) over the 11 scenarios. The hypothesis H0: E[R] = 0 is tested
with a two-sided one-sample t-test on R(1..10) (9 degrees of freedom). The effect is reported
as 100 x (exp(mean R) - 1) % with a 95 % t-interval back-transformed the same way.

Multiplicity: Holm step-down over the 16 primary p-values, family-wise alpha = 0.05. A primary
result is called significant only if its Holm-adjusted p < 0.05. For THR a positive effect is
an improvement; for LAT a negative effect is.

## Known limitations fixed in advance
* THR is capped by the highest offered load (1.6 x DeFT's Lsat). Where a variant still accepts
  >= 95 % of that load, its THR is a lower bound. Such cells are flagged. A capped reference
  understates a variant's loss, and a capped variant understates its gain.
* DeFT_tm equals DeFT on uniform, localized and movinghot, whose traffic-matched LUT is the
  uniform LUT. There r = 0 for comparison 8, and comparisons 1-3 are against DeFT itself.
* CI variants take their exit VL from the uniform LUT (`DECISIONS.md` item 6).
* One simulation length (8000 measured cycles) and one topology instance.

## Secondary (descriptive only; unadjusted 95 % intervals; never called significant)
* Per-scenario paired differences for the primary comparisons and metrics. Holm-adjusted p over
  the 176 per-scenario cells is shown for information.
* Every variant vs DeFT and vs DeFT_tm, including A_oracle.
* Latency at every other load, p99 latency, VL usage imbalance (max/mean over functional VLs),
  latency-vs-load curves.
* Hardware-cost estimates (analytical, not measured).

## Exclusions
None planned. A run with no output is listed and excluded from its cell. A seed with a missing
run in any scenario of a comparison is dropped from that comparison's primary test, and this is
reported.
