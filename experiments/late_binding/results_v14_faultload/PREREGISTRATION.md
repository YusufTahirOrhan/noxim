# Pre-registration v14 (Part F2): fault-sweep latency below the faulty saturation point

Committed before any F2 run. The test loads were fixed in F1 from v11 data only (`load_choice.json`, 585729e).

## Design
* **Masks:** the v11 masks, 5 per (size, k), k = 1, 2, 3 faulty VLs in every chiplet (`results_v11/masks.json`).
* **Sizes:** 2x2, 3x3, 4x4.
* **Traffic:** uniform and hotspot, each at its F1 test load: the highest v11 load point at which DeFT(rho*)'s pooled
  mean latency is at most 3 x its zero-load latency.
* **Methods:** the 8 v11 methods with the v10/v11 parameters (`experiments_v10.methods`):
  - DeFT(rho*) with its LUT for the mask;
  - DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G;
  - CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G.
* **Seeds:** 53-57 (new). Window: 2000 + 8000 cycles.
* **Runs:** 3 x 3 x 5 x 2 x 8 x 5 = 3600.

## Primary hypotheses (18; Holm over the 18)
At every (size, k), CI_qlLA_G and FULL_qlLA_G have a lower mean latency than DeFT(rho*).

**Test:**
* The unit is a (mask, seed) pair: 5 x 5 = 25 units.
* Each unit's value is the mean over the two patterns of ln(LAT_variant / LAT_DeFT), each pattern at its own test load.
* Two-sided one-sample t-test against 0 (24 df). Effect = 100 x (exp(mean) - 1) %, with a 95 % CI.
* Supported if significant after Holm with a negative effect.
* A significant positive effect is reported as a result against our methods.

## Secondary (descriptive; unadjusted)
* P99 for the same comparisons.
* All methods against DeFT(rho*) on LAT and P99.
* The share of cells in which each method is saturated at the test load (accepted < 95 % of offered).

## Report
* A figure as DeFT's Fig. 8: mean latency at the test load against k, one panel per size, all methods. Values are
  geometric means over masks, seeds and the two patterns.
* A table with the effects, their CIs and the loads used.
* FINDINGS.md and a per-run CSV.

## Exclusions
A missing run is listed. A unit with a missing run in either pattern is dropped from that comparison, and this is
reported.
