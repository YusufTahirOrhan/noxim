# Pre-registration v9: confirmatory test of the layer-weighted cost (gamma = 2) against plain DeFT(rho*)

Committed before any drain test or evaluation run of this round. Everything below is frozen; there is no tuning and no
C++ change in v9.

Question: do the v8 results of the gamma-weighted variants against plain DeFT(rho*) hold on new seeds, and what
happens on 2x2, where gamma = 2 has never been run?

## Frozen design
* **Sizes and scenarios:**
  - 2x2 (4 chiplets): the 11 v2 scenarios (uniform, localized, hotspot, chipperm, movinghot fault-free; uniform,
    hotspot and chipperm with VL masks 0x1111 and 0x9C63).
  - 3x3 and 4x4 (9 and 16 chiplets of 4x4 routers): the 7 v5 scenarios (uniform, localized, hotspot, chipperm,
    movinghot fault-free; uniform and hotspot with one faulty VL per chiplet).
* **Loads:** the 7 v5 load points per size and scenario (`results_v5/load_points.json`; 0.2-1.6 x Lsat of
  DeFT(rho*)), not re-measured. Window: 2000 warm-up + 8000 measured cycles.
* **References:**
  - **DeFT(rho*)**: DEFT routing with the uniform LUT of DeFT's v5 rho* (2x2 0.01, 3x3 0.01, 4x4 0.001) for every
    scenario.
  - **DeFT_tm(rho*)**: DEFT routing with DeFT_tm's v5 rho* (2x2 0.01, 3x3 0, 4x4 0.003) and its traffic-matched LUTs
    on hotspot and chipperm (the uniform LUT of its rho* elsewhere).
* **Variants, all with `-deft_lb hop_weight_ipos 2.0`, no re-tuning:**

  | size | CI_heurLA_G (w, busy) | CI_qlLA_G (alpha, key) | FULL_qlLA_G (w, busy; alpha, key) |
  |---|---|---|---|
  | 2x2 (v2 parameters, as used for 2x2 in v5) | (1, 4) | (1, 4; 0.05, chiplet) | (2, 0; 0.01, chiplet) |
  | 3x3 (`results_v6/tuning_choice.json`) | (2, 0) | (2, 0; 0.1, chiplet) | (2, 0; 0.02, chiplet) |
  | 4x4 (`results_v6/tuning_choice.json`) | (2, 0) | (2, 0; 0.1, chiplet) | (1, 4; 0.05, chiplet) |

  All three use the one-hop lookahead. CI takes its exit from DeFT's rho* uniform LUT of the size; the same file is
  passed to the FULL runs, which do not use it.
* **Seeds:** chosen by the step-2 timing test **before any evaluation run**, by a fixed rule that does not depend on
  any result:
  - if the estimated wall time of the full evaluation with seeds 41-50 is at most 9 h, seeds 41-50;
  - otherwise seeds 41-45.

  The choice is recorded in `PREREGISTRATION_addendum.md`, committed before the evaluation starts. Seeds 41-50 have
  never been used.

## Metrics (as v5)
1. **LAT:** mean packet latency at 1.0 x Lsat (4th load).
2. **P99:** p99 packet latency at 1.0 x Lsat.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads per seed and scenario (capped
   when the maximum is at the top load and >= 95 % of it; capped cells reported).

## Primary hypotheses (27)
Per size (2x2, 3x3, 4x4), each of CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G vs DeFT(rho*) on LAT, P99, THR.

## Test (as v5)
r(s,k) = ln(X_variant / X_DeFT); R(s) = mean over the scenarios of the size; two-sided one-sample t-test of R(s)
over the seeds against 0; effect = 100 x (exp(mean R) - 1) % with a 95 % CI. **Holm over the 27**, family-wise
alpha = 0.05. LAT/P99 lower is better, THR higher is better.

## Confirmation criterion (fixed now)
A v8 result counts as **confirmed** if the same v9 test is significant after Holm with the same sign. The v8 values
are the secondary comparisons against DeFT(rho*) in `results_v8/report/summary.md` (seeds 31-40, unadjusted).

| # | size | variant | metric | v8 effect (seeds 31-40) | predicted sign |
|---|---|---|---|---|---|
| 1 | 3x3 | CI_heurLA_G | LAT | -16.70 % | lower |
| 2 | 3x3 | CI_heurLA_G | P99 | -37.13 % | lower |
| 3 | 3x3 | CI_heurLA_G | THR | +2.42 % | higher |
| 4 | 3x3 | CI_qlLA_G | LAT | -20.82 % | lower |
| 5 | 3x3 | CI_qlLA_G | P99 | -45.04 % | lower |
| 6 | 3x3 | CI_qlLA_G | THR | +3.15 % | higher |
| 7 | 3x3 | FULL_qlLA_G | LAT | -28.66 % | lower |
| 8 | 3x3 | FULL_qlLA_G | P99 | -53.92 % | lower |
| 9 | 4x4 | CI_heurLA_G | LAT | -24.42 % | lower |
| 10 | 4x4 | CI_heurLA_G | P99 | -48.99 % | lower |
| 11 | 4x4 | CI_qlLA_G | LAT | -26.31 % | lower |
| 12 | 4x4 | CI_qlLA_G | P99 | -52.69 % | lower |
| 13 | 4x4 | CI_qlLA_G | THR | +2.84 % | higher |
| 14 | 4x4 | FULL_qlLA_G | LAT | -39.14 % | lower |
| 15 | 4x4 | FULL_qlLA_G | P99 | -63.00 % | lower |
| 16 | 4x4 | FULL_qlLA_G | THR | +5.00 % | higher |

**No prediction** (reported with sign and significance, not counted as confirmations or failures):
* 3x3 FULL_qlLA_G THR (v8 -0.35 %, CI incl. 0);
* 4x4 CI_heurLA_G THR (v8 -0.18 %, CI incl. 0);
* all 9 tests on 2x2.

## Secondary (descriptive; unadjusted; never called significant)
* The same comparisons against DeFT_tm(rho*).
* THR without chipperm (against both references).
* Per-scenario tables.
* DeFT_tm(rho*) vs DeFT(rho*).
* VL imbalance of the variants at 1.0 x Lsat (all VLs).

## Drain tests (step 2; any FAIL stops the round)
* **2x2, gamma = 2 (never run before):** the three variants with the v2 drain protocol:
  - allpairs burst on the 11 v2 VL masks (`drain_masks.txt`) x seeds 1, 2;
  - uniform, chipperm and hotspot at rate 0.03 on masks 0x0000, 0x1111, 0x9C63, 0x7BDE.

  These use the v2 uniform LUT (`luts/lut_rho001.yaml`). It covers all 11 masks and is entry-for-entry identical to
  the evaluation LUT (`luts/v5/lut_2x2_rho0.01.yaml`) on its three masks (576 / 576 entries).
* 3x3 and 4x4 were drain-tested with gamma = 2 in v8 (24 / 24 PASS) with the same LUTs, and the references in v5.

## Exclusions
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison's
test, and this is reported.
