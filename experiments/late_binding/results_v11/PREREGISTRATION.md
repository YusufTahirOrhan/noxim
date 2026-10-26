# Pre-registration v11 (Part C): fault-rate sweep

Committed before any Part C evaluation run. The number of masks per (size, k) follows the two rules below. It is
recorded in `PREREGISTRATION_addendum.md` before the evaluation starts.

## Frozen design
* **Faults:** k = 1, 2, 3 faulty VLs in **every** chiplet (exactly k per chiplet).
  - 5 random masks per (size, k), drawn with `random.Random(3110)` and recorded in `masks.json` (committed in
    55b6a39). Faulty VLs are bidirectional.
  - If fewer masks are used, the first ones of each list are taken.
* **Sizes:** 2x2, 3x3, 4x4.
* **Traffic:** uniform and hotspot, at the 7 fault-free v5 load points of each pattern and size (0.2-1.6 x Lsat of
  DeFT(rho*) without faults; `results_v5/load_points.json`).
* **Seeds:** 51 and 52 (new). Window: 2000 + 8000 cycles.
* **Methods** (parameters as in v10, `experiments_v10.methods`):
  - DeFT(rho*), with DeFT's rho* uniform LUT generated for each mask (2x2 and 3x3 rho 0.01, 4x4 rho 0.001; the same
    file is the exit / pair LUT of CI_heurLA_G, CI_qlLA_G and DeFT_OE_G);
  - DeFT-Dis, DeFT-Ran, XY-SP (valid in v10), DeFT_OE_G, CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G.
  - MTR and RC are excluded, as in DeFT's Fig. 8.
* **Runs with 5 masks:** 3 sizes x 3 k x 5 masks x 2 patterns x 8 methods x 7 loads x 2 seeds = 10080.
* **Rules for the mask count** (fixed now; they depend on time estimates only, not on results):
  1. The 4x4 LUT generation time is estimated first (`lut_timing.md`). If the estimate exceeds 4 h: 3 masks per
     (size, k).
  2. The run-time estimate of a timing test (`runtime_estimate.md`). If it exceeds 16 h on the machines available:
     3 masks per (size, k).
* **Safety:** before the evaluation, every method is drain-tested on every mask used (all-pairs burst, seed 1). A FAIL
  stops the round.

## Metrics
1. **LAT:** mean packet latency at the 4th load (1.0 x the fault-free Lsat), as measured. Saturated cells are reported
   as measured and flagged.
2. **P99:** p99 packet latency at the same load.
3. **THR:** saturation throughput, the maximum accepted throughput over the 7 loads (cap rule as v5).

## Primary hypotheses (18; Holm over the 18)
At every (size, k), CI_qlLA_G and FULL_qlLA_G have lower LAT than DeFT(rho*). 2 variants x 3 sizes x 3 k = 18 tests.

**Test:**
* Each effect is pooled over masks, seeds and the two patterns.
* The unit is a (mask, seed) pair, with r(mask, seed) = mean over the two patterns of ln(LAT_variant / LAT_DeFT).
* Two-sided one-sample t-test of r over the units against 0 (5 masks x 2 seeds = 10 units, 9 df; with 3 masks, 6
  units).
* Effect = 100 x (exp(mean r) - 1) %, with a 95 % CI.
* A hypothesis is supported if the test is significant after Holm with a negative effect.

## Secondary (descriptive; unadjusted)
* THR and P99 for the same comparisons; LAT, P99, THR against DeFT-Dis and DeFT-Ran.
* All methods against DeFT(rho*) per (size, k).
* Saturation flags as in v10.
* Figure (as DeFT's Fig. 8): LAT at 1.0 x Lsat and THR against k, one panel per size, all methods. Values are the
  geometric means over masks, seeds and the two patterns.

## Exclusions
A missing run is listed. A unit with a missing run in any cell of a comparison is dropped from that comparison's test,
and this is reported.
