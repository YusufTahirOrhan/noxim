# v6 findings: per-size tuning of the proposed methods, and the 4x4 bottleneck

Design: `PREREGISTRATION.md` (committed before the drain tests and any evaluation run). Decisions:
`DECISIONS.md`. Bottleneck diagnosis: `bottleneck.md`. Tuning: `tuning.md`, `tuning_choice.json`. Tables:
`report/summary.md`, `report/primary.csv`; figure: `report/effect_vs_size.png`; per-run data:
`eval_runs.csv` (4900 runs plus 280 DeFT_tm VL-proxy rows), `tune_runs.csv` (1360 tuning runs).

Run integrity: 4900 / 4900 evaluation runs (seeds 31-40), 0 missing, 0 dead-end events; drain 32 / 32 PASS;
FULL_qlLA with alpha = 0 reproduces FULL_heurLA on 12 / 12 runs. The statistics code added for step 1 is off by
default and was regression-tested (66 / 66 identical runs with the flag off and with it on).

## 1. Tuned parameters (step 2)

| size | CI_heurLA (w, busy) | CI_qlLA alpha | FULL_heurLA (w, busy) | FULL_qlLA alpha |
|---|---|---|---|---|
| 2x2 (v2, used until v5) | (1, 4) | 0.05 | (2, 0) | 0.01 |
| 3x3 | **(2, 0)**: the 2x2 setting is 9.4 % worse on the tuning criterion | **0.1** (grid edge) | (2, 0): unchanged | 0.02 |
| 4x4 | **(2, 0)**: the 2x2 setting is 8.4 % worse | **0.1** (grid edge) | **(1, 4)**: the 2x2 setting is 2.6 % worse | 0.05 |

Key = destination chiplet everywhere. On the larger sizes the CI heuristic wants a higher occupancy weight and
no busy penalty, and its learner a faster learning rate.

## 2. Primary results (pre-registered; Holm over 36 tests)
% change, mean over the 7 scenarios of the size, 95 % CI over seeds 31-40. **33 of 36 significant.** In
brackets: the same comparison with the 2x2-tuned parameters (v5, seeds 21-30; FULL_qlLA not run in v5).

**Against DeFT_tm(rho*) (24 tests, all significant):**

| size | variant | mean latency @1.0 Lsat | p99 latency @1.0 Lsat | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA | -13.6 [-16.5, -10.5] (-10.3) | -30.4 (-18.4) | **-2.6** [-3.2, -2.0] (-5.5) |
| | CI_qlLA | -17.0 [-18.7, -15.3] (-16.2) | -36.7 (-28.3) | **-1.4** [-1.9, -0.8] (-3.6) |
| | FULL_heurLA | -26.6 [-28.3, -24.8] (-26.8) | -48.3 (-46.8) | **-5.0** [-6.5, -3.6] (-4.9) |
| | FULL_qlLA | -29.3 [-31.5, -27.0] | -51.7 | **-5.1** [-6.0, -4.2] |
| 4x4 | CI_heurLA | -19.9 [-26.0, -13.2] (-11.5) | -35.8 (-24.6) | **-9.6** [-10.6, -8.7] (-10.6) |
| | CI_qlLA | -23.8 [-28.1, -19.3] (-18.7) | -43.6 (-35.3) | **-5.7** [-6.4, -5.1] (-9.0) |
| | FULL_heurLA | -31.9 [-35.7, -27.8] (-31.3) | -49.8 (-50.3) | **-7.3** [-8.5, -6.0] (-5.3) |
| | FULL_qlLA | -36.4 [-40.7, -31.9] | -55.7 | **-5.6** [-6.4, -4.8] |

Bold = significantly worse than the baseline. Every variant is significantly faster near saturation, and every
variant has significantly lower saturation throughput, on both sizes.

**Learning vs the lookahead heuristic (12 tests, 9 significant):**

| size | comparison | mean latency | p99 latency | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_qlLA vs CI_heurLA | -4.0 (Holm p 0.053, n.s.) | -9.1 (0.053, n.s.) | **+1.3** [+0.7, +1.9] |
| | FULL_qlLA vs FULL_heurLA | **-3.7** [-5.0, -2.4] | **-6.6** [-10.2, -2.8] | -0.1 (n.s.) |
| 4x4 | CI_qlLA vs CI_heurLA | **-4.9** [-7.9, -1.7] | **-12.2** [-19.1, -4.8] | **+4.3** [+3.3, +5.4] |
| | FULL_qlLA vs FULL_heurLA | **-6.7** [-8.7, -4.7] | **-11.7** [-16.0, -7.1] | **+1.8** [+0.5, +3.1] |

## 3. What changes compared with v5
* **Tuning narrows the CI variants' throughput gap but does not close it.** CI_heurLA goes from -5.5 % to -2.6 %
  on 3x3 and from -10.6 % to -9.6 % on 4x4. CI_qlLA goes from -3.6 % to -1.4 % on 3x3 and from -9.0 % to -5.7 %
  on 4x4. All are still significantly below DeFT_tm(rho*). (v5 and v6 used different seeds, 21-30 and 31-40,
  so the before/after numbers are not paired.)
* **Tuning increases the CI variants' latency benefit:** on 4x4, mean latency goes from -11.5 % to -19.9 %
  (CI_heurLA) and from -18.7 % to -23.8 % (CI_qlLA), and p99 from -24.6 % to -35.8 % and from -35.3 % to -43.6 %.
* **FULL_heurLA does not gain throughput from tuning.** On 3x3 its parameters did not change. On 4x4 the tuned
  setting (1, 4) improves the latency-based tuning criterion but has lower saturation throughput (-7.3 %
  against -5.3 % with the 2x2 setting). The tuning criterion is latency, so it can trade throughput away.
* **The learner is now the best variant of each scope.** FULL_qlLA has the lowest latency of all (4x4: -36.4 %
  mean, -55.7 % p99), and CI_qlLA and FULL_qlLA have the smallest throughput losses. Learning is significantly
  better than its heuristic in 9 of 12 tests, against none confirmed on 2x2 in v3. On 4x4 it improves all
  three metrics for both scopes.
* **Unchanged from v5:** late binding lowers near-saturation latency at every size, and against a tuned DeFT
  LUT it does not raise saturation throughput on 9 or 16 chiplets.

## 4. Where the throughput gap is (secondary)
* **Chipperm is the dominant loss.** Every variant is 24-32 % below DeFT_tm(rho*) there (DeFT_tm still capped,
  so the gap is at least this large). The traffic-matched LUT is very strong on permutation traffic.
* **Without chipperm:**
  - 3x3: the CI variants gain (CI_heurLA +1.9 % [+1.2, +2.6], CI_qlLA +3.2 % [+2.6, +3.9]) and the FULL
    variants are level (-0.8 %, -0.9 %, intervals include 0).
  - 4x4: everything is still below, but the learners are close (CI_qlLA -2.0 %, FULL_qlLA -1.7 %; heuristics
    -5.3 % and -4.1 %).
* **4x4 per scenario:**
  - The remaining non-chipperm losses are uniform (CI_heurLA -17 %, FULL_heurLA -11 %, CI_qlLA -10.5 %,
    FULL_qlLA -2.0 % n.s.), localized (CI only) and movinghot (FULL -15 % to -17 %).
  - Hotspot gives small gains for every variant (+1.7 % to +4.0 %, not all significant), as is uniform with faults for
    CI_qlLA (+7.0 %).
* **VL imbalance** (4x4, 1.0 x Lsat): DeFT_tm(rho*) is the most balanced (1.08-1.47). The learners are close to
  it on uniform (CI_qlLA 1.11-1.12); the FULL variants are the least balanced (1.25-1.84).

## 5. The 4x4 bottleneck (step 1; details and evidence in `bottleneck.md`)
* **Shown:**
  - For the same delivered traffic (4x4 uniform, 1.0 x Lsat, 2x2-tuned parameters), CI_heurLA puts about
    11 % more load on the interposer, the busiest layer (mean link load 0.146 against 0.131 for DeFT_tm), and
    concentrates its entry traffic on central interposer VLs (up-VL max/mean 1.54 against 1.09).
    FULL_heurLA keeps the interposer at the baseline level (0.128) and carries more on the chiplet layer
    (0.062 against 0.056).
  - 77 % of CI's entries differ from the LUT's, and a third of its packets take extra hops (+0.46 on
    average; +1.05 at 1.2 x Lsat).
  - Beyond the knee CI's queues grow 1.9-2.4 times DeFT_tm's per hop, and its accepted throughput at
    1.2 x Lsat is 23 % lower.
* **Hypothesis (not isolated):** the centre concentration comes from the router-local entry choice. Packets
  that come down at the LUT's balanced exits drift towards entries reached through momentarily idle links,
  which on a 16x16 interposer lie towards the centre. The very high residence at chiplet VL endpoints at
  1.2 x Lsat is back-pressure from the congested interposer.
* **Consistent with v6:** the tuned CI weights (a higher occupancy weight, no busy penalty) and the learner's
  residual both make the entry choice more load-aware, and both reduce CI's throughput gap on 4x4 (uniform:
  CI_heurLA -17 %, CI_qlLA -10.5 %; v5 CI_heurLA -16.6 %). The bottleneck runs themselves used the v5
  parameters and were not repeated with the tuned ones.

## 6. Limitations
* Tuning: 2 seeds, 4 cells, latency criterion. CI_qlLA's alpha is on the edge of its grid (not extended,
  in favour of the baseline). The latency criterion selected a FULL_heurLA setting with lower throughput on 4x4.
* The v5/v6 comparison is across seed sets (21-30 against 31-40).
* As before: one window, synthetic traffic, one chiplet size; the load points come from DeFT(rho*).

## Bottom line
With both sides tuned per size:
* **Latency:** late binding lowers near-saturation latency strongly and robustly (mean -14 % to -36 %, p99
  -30 % to -56 %). Learning adds a further, now significant, 4-7 % (mean) and 7-12 % (p99) on 4x4.
* **Throughput:** it still costs saturation throughput on 9 and 16 chiplets (-1.4 % to -9.6 %), mostly on
  chipperm, where the traffic-matched LUT wins by 24 % or more. Without chipperm, the CI variants gain on 3x3
  and the learners are within about 2 % on 4x4.
* **CI vs FULL on 4x4:** the measurements support the explanation that CI's interposer-only adaptivity adds
  load to the bottleneck layer.
