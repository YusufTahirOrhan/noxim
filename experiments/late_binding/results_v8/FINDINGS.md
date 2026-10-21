# v8 findings: plain DeFT(rho*) as a second reference, and the layer-weighted hop cost

Designs: `PREREGISTRATION_step1.md` (b2602ba, before the DeFT(rho*) runs) and `PREREGISTRATION_step5.md` (ef119a3,
before the step-4 results, the drain tests and the evaluation). Decisions: `DECISIONS.md`. Step 1: `FINDINGS_step1.md`.
Selection: `selection.md`. Bottleneck: `bottleneck.md`. Tables: `report/summary.md`, `report/primary.csv`; figure
`report/effect_gamma.png`. Per-run data: `eval_runs.csv` (2940 runs, v6 columns, VL imbalance over all VLs),
`deft_runs.csv`, `select_runs.csv`, `vlref_runs.csv`.

Run integrity:
* Evaluation: 2940 / 2940 runs (seeds 31-40), 0 missing, 0 dead-end events.
* Step 1: 980 / 980 DeFT(rho*) runs.
* Regression (gamma = 1 vs the v7 binary): 198 / 198 identical.
* alpha = 0 at gamma = 2: 12 / 12 identical.
* Selection: 4 / 4 reused parent cells identical.
* Drain: 24 / 24 PASS.

## 1. Plain DeFT(rho*) as reference (step 1; details in `FINDINGS_step1.md`)
Against the traffic-unaware DeFT(rho*), the v6-tuned variants (gamma 1):
* **Latency:** 19-39 % lower mean latency, 39-63 % lower p99.
* **Throughput:** lose at most 2.4 % on 3x3 (CI_qlLA gains 1.4 %, CI_heurLA level) and 1.7-5.9 % on 4x4.
* **Traffic matching (DeFT_tm vs DeFT)** helps only on chipperm (+19.5 % / +32.4 %). That is about half of the
  throughput gap reported against DeFT_tm(rho*) in v5-v7.

## 2. The hop weight and its selection (steps 2-3)
* **The weight:** `-deft_lb hop_weight_ipos gamma` counts each horizontal interposer hop as gamma in the selection's
  static remaining-path cost (heuristic, lookahead, learner estimate and target). The routing relation is unchanged.
* **Selection on 4x4 (seeds 101/102):** gamma = 2 for all three variants, an interior optimum (gamma = 3 broke the
  latency limit):

  | variant | THR vs parent | LAT vs parent |
  |---|---|---|
  | CI_heurLA_G | +3.5 % | +0.1 % |
  | CI_qlLA_G | +7.5 % | +0.9 % |
  | FULL_qlLA_G | +6.8 % | -9.8 % |

## 3. Primary results (pre-registered; Holm over 36 tests; 21 significant)
% change, mean over the 7 scenarios of the size, 95 % CI over seeds 31-40. Bold = significant after Holm.

**Against the gamma = 1 parent (18 tests, 7 significant):**

| size | comparison | mean latency | p99 latency | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA_G vs CI_heurLA | +2.5 [-0.5, +5.5] | +3.6 [-4.8, +12.8] | **+2.29** [+1.85, +2.74] (p 2e-5) |
| | CI_qlLA_G vs CI_qlLA | +1.4 [-0.7, +3.6] | -0.4 [-6.8, +6.4] | **+1.70** [+1.14, +2.26] (p 0.001) |
| | FULL_qlLA_G vs FULL_qlLA | **+7.3** [+4.7, +9.9] (worse) | +9.4 [+3.4, +15.7] (p 0.085) | **+2.14** [+1.22, +3.07] (p 0.008) |
| 4x4 | CI_heurLA_G vs CI_heurLA | -1.1 [-4.3, +2.3] | -4.9 [-11.7, +2.4] | **+6.07** [+4.60, +7.55] (p 1e-4) |
| | CI_qlLA_G vs CI_qlLA | +1.4 [-1.3, +4.2] | +0.5 [-7.3, +8.9] | **+4.73** [+3.67, +5.81] (p 7e-5) |
| | FULL_qlLA_G vs FULL_qlLA | +0.4 [-1.1, +2.0] | -0.0 [-4.7, +4.9] | **+6.81** [+5.76, +7.86] (p 3e-6) |

**Against DeFT_tm(rho*) (18 tests, 14 significant).** In brackets: the gamma = 1 parent (v6).

| size | variant | mean latency | p99 latency | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA_G | **-11.5** (-13.6) | **-27.9** (-30.4) | -0.38 [-1.02, +0.27] n.s. (-2.61) |
| | CI_qlLA_G | **-15.8** (-17.0) | **-37.0** (-36.7) | +0.33 [-0.40, +1.07] n.s. (-1.35) |
| | FULL_qlLA_G | **-24.2** (-29.3) | **-47.2** (-51.7) | **-3.07** [-4.06, -2.07] (-5.10) |
| 4x4 | CI_heurLA_G | **-20.7** (-19.9) | **-38.9** (-35.8) | **-4.16** [-5.02, -3.29] (-9.64) |
| | CI_qlLA_G | **-22.7** (-23.8) | **-43.4** (-43.6) | -1.25 [-2.16, -0.34] n.s. (-5.72) |
| | FULL_qlLA_G | **-36.2** (-36.4) | **-55.7** (-55.7) | +0.83 [+0.08, +1.58] n.s. (-5.60) |

* **Throughput against the parent:** gamma raises saturation throughput significantly for all three variants on
  both sizes: +1.7 % to +2.3 % on 3x3 and +4.7 % to +6.8 % on 4x4.
* **Latency against the parent:**
  - The CI variants and FULL_qlLA on 4x4 show no significant change.
  - FULL_qlLA_G on 3x3 is 7 % slower in mean latency, but still 24 % faster than DeFT_tm(rho*).
* **Against DeFT_tm(rho*):**
  - The 4x4 learners close the throughput gap: CI_qlLA_G -1.3 % and FULL_qlLA_G +0.8 %, both n.s., against -5.7 %
    and -5.6 % for the parents. On 3x3 both CI variants are level.
  - Still significantly below: CI_heurLA_G on 4x4 (-4.2 %, parent -9.6 %) and FULL_qlLA_G on 3x3 (-3.1 %, parent
    -5.1 %).
  - Every _G variant keeps a large, significant latency advantage over DeFT_tm(rho*) (mean -11 % to -36 %, p99 -28 %
    to -56 %).

## 4. Secondary (unadjusted)
* **Against plain DeFT(rho*):** on 4x4 the learners now **gain** saturation throughput (CI_qlLA_G +2.8 %
  [+2.0, +3.7], FULL_qlLA_G +5.0 % [+4.0, +6.0]), and CI_heurLA_G is level (-0.2 %). On 3x3 the CI variants gain
  (+2.4 %, +3.2 %) and FULL_qlLA_G is level (-0.4 %). Latency: -17 % to -39 % mean, -37 % to -63 % p99.
* **Without chipperm against DeFT_tm(rho*):** 4x4 CI_qlLA_G +3.1 %, FULL_qlLA_G +3.4 %, CI_heurLA_G -0.2 %; 3x3 +1.2 %
  to +4.3 %.
* **Per scenario (4x4, vs parent):** the gains are largest where the v6 diagnosis found the loss:
  - uniform: +8 % to +11 % for CI;
  - localized: +12 % for CI;
  - uniform with faults: +7 % to +15 %;
  - chipperm: CI_heurLA +10 %, FULL_qlLA +17 %;
  - movinghot: FULL_qlLA +7 %.
  - hotspot: unchanged.

  The remaining 4x4 losses against DeFT_tm(rho*) are chipperm (-14 % to -25 %, DeFT_tm capped) and movinghot (-3 %
  to -9 %).
* **VL imbalance (all VLs) rises with gamma** for every variant. On 4x4 uniform: CI_heurLA 1.28 -> 1.37, CI_qlLA
  1.20 -> 1.31, FULL_qlLA 1.50 -> 1.85, against DeFT_tm(rho*) 1.11. Weighting the interposer concentrates traffic
  on the VLs that give short interposer paths. The throughput gain is obtained despite less balanced VL use.

## 5. Bottleneck comparison (step 4; 4x4, seeds 101-103; `bottleneck.md`)
At 1.0 x Lsat on uniform, with the same delivered traffic:
* **Interposer load:** gamma lowers CI's interposer link load from 0.144 / 0.143 to 0.136 / 0.134 (DeFT_tm 0.131),
  removing about two thirds of the excess, and raises its chiplet-layer load (0.042 -> 0.046 / 0.045).
  FULL_qlLA_G overshoots to 0.117, below DeFT_tm.
* **Detours:** mean extra hops against the LUT path become negative (-0.24, -0.31).
* **Centre concentration:** the centre / rest ratio does **not** fall (CI 2.01 / 1.94 against 1.94 / 1.80).
* **Beyond the knee:** at 1.2 x Lsat CI_qlLA_G and FULL_qlLA_G accept more than DeFT_tm(rho*) (uniform 0.0638 against
  0.0611; localized 0.0964 / 0.0958 against 0.0905).

## 6. Verdict on the hypothesis: **supported**
Pre-registered criterion: on 4x4, at least one _G variant has significantly higher THR than its parent **and** its
interposer link load at 4x4 uniform, 1.0 x Lsat (step 4) is closer to DeFT_tm(rho*)'s than its parent's.
* CI_heurLA_G: THR +6.1 % (Holm p 1e-4); interposer load 0.136 against parent 0.144 and DeFT_tm 0.131: **closer. Met.**
* CI_qlLA_G: THR +4.7 % (Holm p 7e-5); 0.134 against 0.143 and 0.131: **closer. Met.**
* FULL_qlLA_G: THR +6.8 % (Holm p 3e-6), but its parent already matched DeFT_tm's interposer load (0.131) and gamma
  moves it below (0.117). **Not met** by the closeness condition.

**What is shown:**
* Counting interposer hops more than chiplet hops in the selection cost moves CI's traffic from the interposer back
  to the chiplet layer.
* It removes most of CI's excess interposer load.
* It raises saturation throughput significantly on 9 and 16 chiplets, without a significant latency cost for CI.

**What is not shown / limits of the explanation:**
* The centre concentration of the interposer load is not reduced. The gain comes from less total interposer load,
  not from a more even spread.
* FULL, which had no excess interposer load, gains as much (+6.8 %). So the mechanism is not only "CI moves
  chiplet hops onto the interposer". A cost that prefers chiplet hops helps every late-binding variant, consistent
  with the interposer being the bottleneck layer for all of them.
* gamma was selected on 4x4 only (2 seeds, 5 loads) and transferred to 3x3, where FULL_qlLA_G loses 7 % latency
  against its parent.

## 7. Limitations
* One gamma for all three variants and both sizes. The grid was coarse (1.25-3), and gamma = 3 was rejected only by
  the latency constraint.
* VL imbalance rises with gamma; the effect on fault tolerance under VL faults beyond one per chiplet was not tested.
* As before: one window, synthetic traffic, one chiplet size; the load points come from DeFT(rho*).

## Bottom line
* **The hypothesis holds for CI.** With interposer hops weighted twice in the selection cost, the interposer-only and
  full late-binding variants gain 1.7-2.3 % (3x3) and 4.7-6.8 % (4x4) saturation throughput over their tuned
  parents.
* **Against DeFT_tm(rho*):** the 4x4 learners are now level in saturation throughput (CI_qlLA_G -1.3 %, FULL_qlLA_G
  +0.8 %, both n.s.), and every variant keeps 11-36 % lower mean and 28-56 % lower p99 latency.
* **Against the traffic-unaware DeFT(rho*):** the 4x4 learners gain 2.8 % and 5.0 % saturation throughput as well.
