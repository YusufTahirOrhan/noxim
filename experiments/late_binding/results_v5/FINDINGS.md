# v5 findings: late binding against a tuned DeFT baseline

Question: v4 compared the late-binding variants with a DeFT whose LUT weight rho = 0.01 had never been
tuned. Do the size results survive when DeFT gets the same tuning as the other methods?
Design: `PREREGISTRATION.md` (committed before the drain tests and any evaluation run); decisions:
`DECISIONS.md`. Tables: `report/summary.md`, `report/primary.csv`; figure: `report/effect_vs_size.png`;
per-run data: `eval_runs.csv`.

**Short answer: no for 4x4.** The v4 throughput gains on 4x4 were an artefact of the untuned baseline,
and against the tuned baseline they turn into significant losses. The latency gains survive on every
size but shrink markedly on 4x4. The 2x2 results are unchanged and replicate on new seeds.

## 1. Why the baseline was handicapped (step 1, `lut_scaling.md`)
* The LUT objective is rho * sum(distance) + sum_v |load_v - mean| / mean. The distance term grows
  with the number of demand points, while the balance term stays bounded.
* **On 4x4**, the 240-point entry problems trade balance for distance: the distance term is 23.4
  against a balance term of 0.60, giving an analytic VL imbalance of 1.40. That matches the 1.43
  measured in v4.
* **On 2x2 and 3x3** the rho = 0.01 LUT is perfectly balanced (analytic imbalance 1.00).

## 2. Tuning rho (step 2, `tuning.md`)
Seeds 101/102, the other methods' cells, loads and criterion; 6 values of rho per size and variant.

| size | DeFT rho* | DeFT_tm rho* | tuning criterion vs rho = 0.01 |
|---|---|---|---|
| 2x2 | 0.01 | 0.01 | 0 % (rho has no effect: all six LUTs give identical runs) |
| 3x3 | 0.01 | 0 | DeFT 0 %; DeFT_tm -11.7 % (same analytic imbalance for every rho: partly noise between equally balanced LUTs) |
| 4x4 | 0.001 | 0.003 | DeFT **-36.8 %**; DeFT_tm **-17.9 %** (LUT imbalance 1.40 -> 1.00) |

With rho*, the 4x4 DeFT saturates later (e.g. uniform Lsat 0.005 -> 0.0065 packets/cycle/source;
`load_points.md`). The measured VL imbalance of DeFT_tm on 4x4 uniform falls from 1.43 to 1.09.

## 3. Primary results (pre-registered; Holm over 36 tests; all 36 significant, largest Holm p = 0.020)
% change vs DeFT_tm(rho*) of the size, mean over its scenarios, 95 % CI over seeds 21-30. In brackets:
the same comparison against DeFT_tm(rho = 0.01) from v2 (2x2) / v4 (3x3, 4x4), seeds 1-10.

| size | variant | mean latency @1.0 Lsat | p99 latency @1.0 Lsat | saturation throughput |
|---|---|---|---|---|
| 2x2 | CI_heur | -15.9 (-16.0) | -29.1 (-29.1) | +2.5 (+2.2) |
| | CI_heurLA | -20.3 (-19.6) | -33.7 (-32.3) | +3.1 (+3.1) |
| | CI_qlLA | -21.9 (-22.1) | -36.6 (-36.8) | +4.5 (+4.7) |
| | FULL_heurLA | -24.4 (-24.8) | -44.6 (-44.9) | **-2.7** (-1.7) |
| 3x3 | CI_heur | -5.0 (-6.7) | -13.8 (-20.8) | **-6.9** (-6.5) |
| | CI_heurLA | -10.3 (-11.7) | -18.4 (-25.1) | **-5.5** (-5.1) |
| | CI_qlLA | -16.2 (-17.1) | -28.3 (-33.5) | **-3.6** (-3.0) |
| | FULL_heurLA | -26.8 (-28.0) | -46.8 (-50.1) | **-4.9** (-5.1) |
| 4x4 | CI_heur | -9.1 (-29.4) | -23.2 (-59.3) | **-10.3** (+6.0) |
| | CI_heurLA | -11.5 (-32.0) | -24.6 (-60.5) | **-10.6** (+6.4) |
| | CI_qlLA | -18.7 (-33.0) | -35.3 (-62.7) | **-9.0** (+7.4) |
| | FULL_heurLA | -31.3 (-38.2) | -50.3 (-68.3) | **-5.3** (+12.4) |

Bold = significantly worse than the baseline. Full intervals and p-values: `report/primary.csv`.

## 4. What changes in the earlier conclusions
* **v4's "+6 % to +12 % saturation throughput on 4x4" does not hold.** Against the tuned DeFT_tm, all
  four variants are significantly worse on 4x4 (-5 % to -11 %). The v4 gain came from the untuned LUT
  objective. The 4x4 loss is broad, not only chipperm:
  - The CI variants lose 12-17 % on uniform and localized, 6.6-9.1 % on movinghot and 25-32 % on chipperm,
    and gain only slightly on hotspot (secondary, `report/summary.md`).
  - Without chipperm the deficit is still about -6 % for the CI variants (-1.0 % for FULL_heurLA, n.s.).
* **v4's "the latency benefit is largest on 16 chiplets" does not hold.** On 4x4 the mean-latency
  reduction shrinks from -29 % to -33 % to **-9 % to -19 %** for the CI variants, and p99 from about
  -60 % to -23 % to -35 %. With a tuned baseline, the CI variants' latency benefit is largest on 2x2 and
  smaller on 3x3 and 4x4. FULL_heurLA keeps a large benefit at every size (-24 % to -31 % mean, -45 %
  to -50 % p99).
* **The near-saturation latency benefit itself survives** at every size against the tuned baseline:
  all 12 latency tests are significant.
* **2x2 is unchanged.** rho has no effect on the 2x2 LUT. The v5 2x2 results (seeds 21-30, re-measured
  Lsat) reproduce v2/v3 within about 1.5 percentage points. This is an independent replication of the
  2x2 conclusions.
* **3x3 is essentially unchanged**: the DeFT LUT was already balanced. The throughput losses (-3.6 % to
  -6.9 %) and the smaller latency gains are confirmed on new seeds.
* **Net picture for saturation throughput:** late binding gains only on 2x2 (CI variants +2.5 % to
  +4.5 %). On 9 and 16 chiplets it loses against a well-tuned DeFT LUT, and on 4x4 even against
  DeFT(rho*) with no traffic knowledge (-5 % to -7 % for the CI variants; FULL_heurLA -1.3 %, n.s.).

## 5. Secondary
* **DeFT(rho*), with a uniform LUT and no traffic knowledge, as the reference.** Late binding's
  latency benefit is larger at every size (e.g. 4x4 CI_heur -15.7 % mean, -38.2 % p99), because
  DeFT_tm itself is better than DeFT (4x4: -7.2 % mean latency, +4.3 % throughput, mostly chipperm).
* **VL imbalance** (4x4, ~1.0 x Lsat): DeFT_tm(rho*) is now the best-balanced design (1.09-1.48),
  ahead of the CI variants (1.13-1.79) and FULL_heurLA (1.30-1.91). In v4 the LUT's imbalance on 4x4
  had made the comparison favour late binding.
* **Learning** (CI_qlLA vs CI_heurLA, both vs DeFT_tm): CI_qlLA is ahead of CI_heurLA on every size
  and metric in the table above (e.g. 4x4 mean latency -18.7 % vs -11.5 %). This comparison is not
  tested directly here and remains secondary.

## 6. Limitations
* **The tuning asymmetry is now reversed.** DeFT's rho was tuned per size; the late-binding variants
  keep the 2x2-tuned weights and learning rates on 3x3 and 4x4 (pre-registered). This favours the
  baseline at the larger sizes (the conservative direction requested), and part of the 4x4 deficit
  may come from it.
* **rho was tuned on 2 seeds and 4 cells**, like every other parameter. The 3x3 DeFT_tm choice (rho =
  0) rests on differences between equally balanced LUTs.
* **The CI exit uses the uniform LUT of DeFT's rho*** (3x3: 0.01, 4x4: 0.001). On 4x4 that LUT is
  balanced, so CI's exit choice is not handicapped.
* As before: one window, synthetic traffic, one chiplet size, 10 seeds; capped THR cells are reported
  in `report/primary.csv`.

## Bottom line
With a fairly tuned DeFT baseline:
* **Latency:** late binding still lowers near-saturation mean and p99 latency at every size. The gain
  is large on 4 chiplets (-16 % to -24 % mean) and smaller for the interposer-only variants on 9 and 16
  chiplets (-5 % to -19 %); full late binding with lookahead stays at about -25 % to -31 %.
* **Throughput:** late binding raises saturation throughput only on 4 chiplets. On 9 and 16 chiplets it
  costs 3-11 %.
* **What no longer stands:** the v4 claims that the benefits grow with system size and that 4x4
  throughput improves.
