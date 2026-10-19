# v4 findings: late binding on larger systems (3x3 and 4x4 chiplets)

Question: do the 2x2 results (v2/v3) hold on 9 and 16 chiplets, with parameters frozen from v2 and
the LUTs generated for each size? Design: `PREREGISTRATION.md` (committed before any sweep or
evaluation run) and `PREREGISTRATION_AMENDMENT.md` (the load-point rule, amended after the coarse
saturation sweep and **before any evaluation run**). Decisions: `DECISIONS.md`. Tables:
`report/summary.md`, `report/primary.csv`; figures: `report/effect_vs_size.png`,
`report/latency_3x3.png`, `report/latency_4x4.png`; per-run data: `eval_runs.csv`.

## Validity checks before the evaluation
* **Parametrisation is behaviour-preserving on 2x2.** The parametric binary reproduces the old one
  exactly (identical summary and deft_lb blocks) on 132 fixed-window and 22 drain runs
  (`regression.md`).
* **The 2x2 inputs are unchanged.** The default LUT, all four traffic-matched LUTs and all 401
  default traffic tables are byte-identical through the parametric generators. The MILP used for the
  larger LUT problems reaches the exact DP optimum on all 264 2x2 optimisations (`generators.md`,
  `lut_milp_check.md`).
* **Formal model:** the three relations are deadlock-, dead-end- and livelock-free on 3x3 (22 masks,
  66 checks) and 4x4 (2 masks, 6 checks; per-destination exploration, exact) (`formal_sizes.md`).
* **Drain:** 56 / 56 PASS on 3x3 and 4x4 (`drain_summary.csv`).
* **Evaluation:** 5880 / 5880 runs plus 280 VL proxy runs; no missing output; 0 dead-end events. The
  proxy matches DeFT_tm exactly on all 280 runs.

## 1. Primary results (pre-registered; Holm over 24 tests; all 24 significant)
Effect: mean over the 7 scenarios of a size, % change vs DeFT_tm, 95 % CI over seeds 1-10.
2x2 values come from earlier runs and are context only, not part of the test: LAT and P99 from v3
(seeds 11-20), THR from v2 (seeds 1-10), 11 scenarios.

| comparison | metric | 2x2 (earlier) | **3x3** | **4x4** |
|---|---|---|---|---|
| CI_heur vs DeFT_tm | mean latency @1.0 Lsat | -17.6 | **-6.7** [-10.7, -2.5] | **-29.4** [-32.6, -26.1] |
| | p99 latency @1.0 Lsat | -32.5 | **-20.8** [-29.9, -10.4] | **-59.3** [-63.2, -54.9] |
| | saturation throughput | +2.2 | **-6.5** [-7.3, -5.8] (worse) | **+6.0** [+5.2, +6.9] |
| CI_heurLA vs DeFT_tm | mean latency | -21.4 | **-11.7** [-14.0, -9.4] | **-32.0** [-35.3, -28.5] |
| | p99 latency | -35.3 | **-25.1** [-29.8, -20.2] | **-60.5** [-64.4, -56.3] |
| | saturation throughput | +3.1 | **-5.1** [-5.7, -4.6] (worse) | **+6.4** [+5.8, +7.0] |
| CI_qlLA vs DeFT_tm | mean latency | -23.3 | **-17.1** [-19.4, -14.8] | **-33.0** [-37.1, -28.7] |
| | p99 latency | -38.7 | **-33.5** [-38.3, -28.3] | **-62.7** [-67.1, -57.6] |
| | saturation throughput | +4.7 | **-3.0** [-3.7, -2.4] (worse) | **+7.4** [+6.6, +8.2] |
| FULL_heurLA vs DeFT_tm | mean latency | -26.2 | **-28.0** [-30.9, -25.0] | **-38.2** [-41.2, -35.1] |
| | p99 latency | -46.0 | **-50.1** [-55.7, -43.8] | **-68.3** [-71.1, -65.3] |
| | saturation throughput | -1.7 | **-5.1** [-6.4, -3.9] (worse) | **+12.4** [+11.1, +13.8] |

Holm-adjusted p-values range from 9e-9 to 0.006 (`report/primary.csv`).

### Read this with the table
* **Near-saturation latency improves at every size**, for every late-binding configuration
  (significant in all 16 latency tests). The effect is **not monotone in size**: on 3x3 it is
  smaller than on 2x2 for the three CI variants (e.g. CI_heur -6.7 % vs -17.6 %), and on 4x4 it
  is the largest (-29 % to -38 %). FULL_heurLA is roughly stable from 2x2 to 3x3 and larger on 4x4.
* **Saturation throughput reverses sign with size.** On 3x3, all four late-binding variants have
  significantly **lower** saturation throughput than DeFT_tm (-3.0 % to -6.5 %); on 2x2 three of
  four were higher. On 4x4 all four are significantly higher (+6 % to +12 %). This is a negative
  result for 3x3 and is reported as such.
* **Capping.** 24-38 of the 70 seed-scenario cells of each 4x4 THR test are capped (a variant still
  accepts >= 95 % of the top load, 1.6 x DeFT's Lsat), so the 4x4 throughput gains are lower
  bounds. On 3x3 the capped cells (11 of 70) are DeFT_tm's (chipperm, movinghot), so the 3x3
  losses there are understated, not inflated.

## 2. Where the 3x3 throughput loss comes from (secondary)
* **Chipperm, mainly.** On 3x3 chipperm every late-binding variant is 24-26 % below DeFT_tm in
  saturation throughput (DeFT_tm still capped, so the gap is at least this large). On 4x4 chipperm
  they are 3.5-10.6 % below (FULL_heurLA's -3.5 % has an interval that includes 0). On 2x2 chipperm the difference was within +-2.5 %. Against a
  traffic-matched LUT, permutation traffic is the one pattern where late binding consistently loses
  on the larger systems. (On 3x3 the middle chiplet of chipperm maps to itself, as the pattern
  definition implies.)
* **Without chipperm** (sensitivity, not pre-registered; `report/sensitivity_thr_no_chipperm.txt`):
  - 3x3: CI_heur -2.8 %, CI_heurLA -1.6 %, CI_qlLA +1.4 %, FULL_heurLA -1.1 % (n.s.). The 3x3
    deficit shrinks but does not disappear for the two heuristics.
  - 4x4: +9.0 % to +15.3 %.
* **Per scenario on 4x4**, the largest gains are uniform with one faulty VL per chiplet (+33 % to
  +39 %, capped) and, for FULL_heurLA, uniform and localized fault-free (+19 % to +20 %).

## 3. Learning and other secondary results (descriptive, unadjusted; not significance claims)
* **CI_qlLA vs CI_heurLA** (learning over the lookahead heuristic):
  - 3x3: mean latency -6.2 % [-7.9, -4.4], p99 -11.2 %, throughput +2.2 %.
  - 4x4: mean latency -1.6 % [-4.6, +1.5], p99 -5.5 %, throughput +1.0 %.

  The direction is the same as in v2/v3. This comparison failed confirmation on 2x2 in v3, and it
  stays secondary here.
* **DeFT_tm vs DeFT:** throughput +2.4 % (3x3) and +5.2 % (4x4). As on 2x2, the gain comes entirely
  from chipperm (+19 % and +42 %); the LUTs for localized and movinghot are identical to the
  uniform one.
* **VL usage imbalance** (max/mean; `report/summary.md`):
  - On 3x3, DeFT_tm stays well balanced (1.06-1.33 at 1.0 x Lsat) and the late-binding variants
    are less balanced (CI 1.09-1.56, FULL 1.33-1.67), as on 2x2.
  - **On 4x4, DeFT_tm's own balance degrades** (1.41-1.43 on uniform and localized, about 2 on
    hotspot and movinghot), and the CI variants are better balanced than DeFT_tm in most scenarios
    (1.12-1.77).

  A plausible reason (not tested): the LUT objective keeps rho = 0.01. On a 16x16 interposer the
  distance term weighs more against the load term, so the size's LUT balances less. This may
  contribute to the 4x4 gains, and **rho was not re-tuned for size**; a DeFT with a size-adapted
  rho could narrow them.

## 4. Limitations
* **No re-tuning:** heuristic weights, learning rates and rho were fixed on 2x2 (pre-registered).
  This can disadvantage any method at 9 and 16 chiplets. The DeFT LUT's rho is one concrete
  candidate (section 3).
* **The load-point rule was amended before the evaluation** (L0 at rate 0.0002, 0.0001 grid for eight
  early-saturating scenarios), because the original rule would have placed the "1.0 x Lsat" point at
  up to 2 x Lsat on 4x4. The coarse result is kept in `load_points_coarse.md`.
* **Limited coverage:**
  - 7 scenarios per size, 10 seeds, one window, one chiplet size (4x4 routers), synthetic traffic.
  - 4x4 formal coverage is 2 fault masks.
  - The 2x2 comparison values come from earlier runs with 11 scenarios.
* **Fault-free 4x4 movinghot and chipperm saturate DeFT very early** (Lsat 0.0014 and 0.0024
  packets/cycle/source). Their load ladders sit close to the lowest rates the grid can resolve.

## Bottom line
* **Latency:** the near-saturation latency benefit of late binding against the traffic-matched DeFT
  replicates on 9 and 16 chiplets, for every configuration tested. It is largest on 16 chiplets
  (mean -29 % to -38 %, p99 -59 % to -68 %) but **smaller on 9 chiplets than on 4 for the CI
  variants**.
* **Throughput:** the effect is size-dependent. It is significantly **worse on 3x3** (-3 % to
  -6.5 %, driven mostly by chipperm, where the traffic-matched LUT wins by 24 % or more) and
  significantly better on 4x4 (+6 % to +12 %, lower bounds).
* **No simple scaling claim holds**, i.e. the data do not support "the benefit grows with system
  size". Permutation traffic favours the traffic-matched LUT on larger systems, and the 4x4 gains
  may partly reflect a LUT objective (rho) that was not adapted to the size.
