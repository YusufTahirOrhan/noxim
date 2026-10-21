# v9 findings: confirmatory test of the layer-weighted cost (gamma = 2) against plain DeFT(rho*)

Design: `PREREGISTRATION.md` (7da0d28, before any drain or evaluation run) and `PREREGISTRATION_addendum.md` (95f6ed7,
seed choice, before the evaluation). Decisions: `DECISIONS.md`. Tables: `report/summary.md`, `report/primary.csv`,
`report/confirmation.csv`; figure `report/effect_vs_size.png`. Per-run data: `eval_runs.csv` (8750 runs, v8 columns,
VL imbalance over all VLs for the DEFT_LB variants).

**Run integrity:**
* Evaluation: 8750 / 8750 runs, seeds 41-50 (new), 0 missing, 0 dead-end events. Seed rule: estimate 8.4 h <= 9 h,
  so seeds 41-50.
* Drain, 2x2 with gamma = 2 (first time): 102 / 102 PASS.
* Nothing was tuned in v9 and there was no C++ change.

## 1. Primary results (pre-registered; Holm over 27 tests; 25 significant)
% change against plain DeFT(rho*), mean over the scenarios of the size (2x2: 11, 3x3/4x4: 7), 95 % CI over seeds
41-50. Bold = significant after Holm.

| size | variant | mean latency @1.0 Lsat | p99 latency @1.0 Lsat | saturation throughput |
|---|---|---|---|---|
| 2x2 | CI_heurLA_G | **-28.8** [-30.6, -27.0] | **-52.4** [-55.6, -49.1] | **+11.0** [+10.4, +11.6] |
| | CI_qlLA_G | **-32.8** [-35.1, -30.4] | **-56.0** [-59.6, -52.1] | **+11.1** [+10.2, +12.0] |
| | FULL_qlLA_G | **-28.7** [-31.3, -26.0] | **-55.6** [-59.7, -51.1] | **+3.9** [+2.8, +5.1] |
| 3x3 | CI_heurLA_G | **-18.5** [-22.6, -14.1] | **-41.1** [-47.1, -34.4] | **+2.3** [+1.8, +2.8] |
| | CI_qlLA_G | **-21.8** [-26.0, -17.3] | **-46.0** [-52.3, -39.0] | **+2.6** [+2.1, +3.1] |
| | FULL_qlLA_G | **-29.1** [-31.8, -26.4] | **-54.3** [-57.9, -50.4] | -0.8 [-1.7, +0.0] (Holm p 0.10, n.s.) |
| 4x4 | CI_heurLA_G | **-24.8** [-29.1, -20.2] | **-50.1** [-55.2, -44.4] | -0.9 [-2.0, +0.1] (Holm p 0.10, n.s.) |
| | CI_qlLA_G | **-28.0** [-31.7, -24.1] | **-55.7** [-59.2, -51.8] | **+1.9** [+1.3, +2.6] |
| | FULL_qlLA_G | **-40.5** [-43.9, -36.9] | **-65.3** [-68.6, -61.8] | **+4.5** [+3.8, +5.2] |

On 2x2, 30-32 of the 110 seed x scenario throughput cells are capped. These are mainly chipperm and faulty-mask
chipperm, where the variants still accept the top load. A capped cell under-states the variant, so the 2x2
throughput gains are lower bounds.

## 2. Confirmation of the v8 results: **16 of 16 confirmed**
Criterion (fixed in advance): the same v9 test significant after Holm with the same sign.

| size | variant | metric | v8 (seeds 31-40) | v9 (seeds 41-50) | Holm p | confirmed |
|---|---|---|---|---|---|---|
| 3x3 | CI_heurLA_G | LAT | -16.70 | -18.49 | 5e-5 | yes |
| 3x3 | CI_heurLA_G | P99 | -37.13 | -41.06 | 1e-5 | yes |
| 3x3 | CI_heurLA_G | THR | +2.42 | +2.28 | 1e-5 | yes |
| 3x3 | CI_qlLA_G | LAT | -20.82 | -21.75 | 2e-5 | yes |
| 3x3 | CI_qlLA_G | P99 | -45.04 | -46.02 | 1e-5 | yes |
| 3x3 | CI_qlLA_G | THR | +3.15 | +2.63 | 1e-5 | yes |
| 3x3 | FULL_qlLA_G | LAT | -28.66 | -29.11 | 1e-7 | yes |
| 3x3 | FULL_qlLA_G | P99 | -53.92 | -54.29 | 8e-8 | yes |
| 4x4 | CI_heurLA_G | LAT | -24.42 | -24.78 | 1e-5 | yes |
| 4x4 | CI_heurLA_G | P99 | -48.99 | -50.11 | 2e-6 | yes |
| 4x4 | CI_qlLA_G | LAT | -26.31 | -28.03 | 2e-6 | yes |
| 4x4 | CI_qlLA_G | P99 | -52.69 | -55.66 | 8e-8 | yes |
| 4x4 | CI_qlLA_G | THR | +2.84 | +1.94 | 2e-4 | yes |
| 4x4 | FULL_qlLA_G | LAT | -39.14 | -40.49 | 2e-7 | yes |
| 4x4 | FULL_qlLA_G | P99 | -63.00 | -65.32 | 3e-8 | yes |
| 4x4 | FULL_qlLA_G | THR | +5.00 | +4.46 | 2e-6 | yes |

**Without a prediction**, and still not significant in v9:
* 3x3 FULL_qlLA_G THR: v8 -0.35, v9 -0.84 [-1.69, +0.01].
* 4x4 CI_heurLA_G THR: v8 -0.18, v9 -0.93 [-1.96, +0.10].

Both v9 point estimates lie close to the v8 ones. The v9 throughput effects are 0.1-0.9 points smaller than v8's,
consistent with some selection optimism in v8, where gamma was chosen on 4x4.

## 3. 2x2 (new; no prediction)
All 9 tests are significant and favourable:
* **Latency:** mean -29 % to -33 %, p99 -52 % to -56 %.
* **Saturation throughput:** +11.0 % (CI_heurLA_G), +11.1 % (CI_qlLA_G), +3.9 % (FULL_qlLA_G).
* **Where the CI gains come from** (per scenario): every 2x2 scenario. Fault-free uniform and localized +8 % to
  +10 %; chipperm +17 % to +32 % (capped).
* **FULL_qlLA_G per scenario:** gains on chipperm (+17 % to +30 %, capped) and localized (+4 %), but loses on hotspot
  (-10 % fault-free, -6 % with mask 0x1111) and movinghot (-3.5 %).

## 4. Secondary (unadjusted)
**Against DeFT_tm(rho*):**

| size | variant | mean latency | p99 latency | saturation throughput |
|---|---|---|---|---|
| 2x2 | CI_heurLA_G | -15.0 [-16.5, -13.4] | -28.2 | +5.3 [+4.7, +5.8] |
| | CI_qlLA_G | -19.8 [-21.9, -17.5] | -33.5 | +5.4 [+4.7, +6.0] |
| | FULL_qlLA_G | -14.9 [-17.5, -12.2] | -32.9 | -1.4 [-2.3, -0.6] |
| 3x3 | CI_heurLA_G | -11.9 [-15.3, -8.3] | -27.8 | +0.1 [-0.3, +0.5] |
| | CI_qlLA_G | -15.4 [-18.0, -12.6] | -33.9 | +0.5 [-0.1, +1.0] |
| | FULL_qlLA_G | -23.3 [-25.1, -21.6] | -44.0 | -3.0 [-3.6, -2.3] |
| 4x4 | CI_heurLA_G | -19.6 [-23.5, -15.4] | -38.0 | -4.5 [-5.7, -3.4] |
| | CI_qlLA_G | -23.0 [-27.0, -18.8] | -44.9 | -1.8 [-2.6, -0.9] |
| | FULL_qlLA_G | -36.4 [-39.4, -33.1] | -56.9 | +0.7 [+0.1, +1.2] |

* Every variant is faster than DeFT_tm(rho*) on every size.
* In saturation throughput against DeFT_tm:
  - The CI variants gain on 2x2, are level on 3x3, and lose on 4x4 (-4.5 % heuristic, -1.8 % learner).
  - FULL_qlLA_G loses on 2x2 and 3x3 and gains slightly on 4x4.
  - Nearly all of the gap is chipperm, where DeFT_tm's traffic-matched LUT is +17 % to +34 % better than DeFT.
* **What traffic matching buys** (DeFT_tm vs DeFT): saturation throughput +5.4 % (2x2), +2.2 % (3x3), +3.8 % (4x4),
  coming only from chipperm. Without chipperm the two references are level (-0.3 %, -0.5 %, -0.5 %). On 2x2, DeFT_tm
  also has lower latency (-16 %), almost entirely from the three chipperm scenarios (-35 % to -55 % at 1.0 x Lsat).
* **Without chipperm, against DeFT(rho*):**
  - 2x2: CI +6.7 % / +7.2 %, FULL -2.2 %.
  - 3x3: CI +3.4 % / +3.9 %, FULL +1.1 %.
  - 4x4: CI_heurLA_G -1.2 % (n.s.), CI_qlLA_G +2.1 %, FULL_qlLA_G +2.8 %.

  Against DeFT_tm the values are almost the same (+7.0 / +7.5 / -1.9; +3.9 / +4.4 / +1.6; -0.6 / +2.6 / +3.3).
* **Per scenario, 4x4, against DeFT(rho*):**
  - Gains: localized (CI_qlLA_G +3.5 %, FULL_qlLA_G +5.3 %), hotspot (+1.4 % to +2.6 %), uniform with faults
    (+4.8 % to +14.2 %), and chipperm for FULL_qlLA_G (+15 %).
  - Losses: movinghot for every variant (-4.7 % to -9.3 %), and CI_heurLA_G on fault-free uniform (-7.7 %).
* **VL imbalance (all VLs) of the variants** at 1.0 x Lsat, fault-free uniform: CI_heurLA_G 1.22 / 1.26 / 1.37,
  CI_qlLA_G 1.14 / 1.21 / 1.32, FULL_qlLA_G 1.49 / 1.68 / 1.83 (2x2 / 3x3 / 4x4). There are no reference values
  (DEFT routing does not count VL use).

## Bottom line
* **Everything v8 predicted against plain DeFT(rho*) is confirmed on new seeds (16 / 16):**
  - the latency gains of all three variants on 3x3 and 4x4;
  - the saturation-throughput gains of both CI variants on 3x3;
  - the saturation-throughput gains of CI_qlLA_G and FULL_qlLA_G on 4x4.
* **On 2x2,** never used for gamma before, all three variants are significantly better in all three metrics, with
  saturation-throughput gains of 11 % for the CI variants.
* **Across sizes:**
  - CI_qlLA_G is the only variant that is significantly better than plain DeFT(rho*) in all three metrics on all
    three sizes (mean latency -22 % to -33 %, p99 -46 % to -56 %, saturation throughput +1.9 % to +11.1 %).
  - FULL_qlLA_G has the lowest latency on 3x3 and 4x4 and the largest 4x4 throughput gain (+4.5 %), but is level on
    3x3 throughput.
  - CI_heurLA_G is level on 4x4 throughput.

## Limitations
* gamma = 2 was chosen on 4x4 (v8, seeds 101/102) and applied unchanged here; the 2x2 parameters are the v2 ones.
* The 2x2 throughput gains are lower bounds (capped cells).
* One window, synthetic traffic, one chiplet size; the load points come from DeFT(rho*) (v5).
