# v8 step 4: the 4x4 bottleneck with the layer-weighted hop cost (descriptive)

Runs: 4x4 uniform and localized, fault-free; CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G (gamma 2) and the FULL_qlLA parent
(gamma 1, not in v7); loads 0.8, 1.0, 1.2 x Lsat; seeds 101-103; 72 runs with the statistics flag, 0 missing. Raw
files aggregated into `bottleneck_agg.json` and `bottleneck_metrics.json`, then deleted. DeFT_tm(rho*), CI_heurLA and
CI_qlLA from `results_v7/bottleneck_agg.json`. Full tables: `bottleneck_tables.md`; per-cell interposer-load closeness
to DeFT_tm: `bottleneck_closeness.json`. Heatmaps (interposer, 1.0 x Lsat): `bottleneck_links_{uniform,localized}.png`.

## Uniform, 1.0 x Lsat (delivered traffic equal: accepted 0.0516-0.0519)

| variant | interposer link load | chiplet link load | centre / rest | entry VL max/mean | entry differs from LUT | extra hops mean / share > 0 | latency |
|---|---|---|---|---|---|---|---|
| DeFT_tm(rho*) | 0.131 | 0.056 | 1.40 | 1.09 | 0 % | 0 / 0 % | 75.3 |
| CI_heurLA | 0.144 | 0.042 | 1.94 | 1.46 | 74.5 % | +0.20 / 29 % | 63.0 |
| **CI_heurLA_G** | **0.136** | 0.046 | 2.01 | 1.71 | 65.8 % | -0.24 / 19 % | 63.0 |
| CI_qlLA | 0.143 | 0.042 | 1.80 | 1.35 | 74.2 % | +0.11 / 27 % | 59.4 |
| **CI_qlLA_G** | **0.134** | 0.045 | 1.94 | 1.54 | 64.3 % | -0.31 / 17 % | 59.4 |
| FULL_qlLA | 0.131 | 0.064 | 1.92 | 1.24 | 75.4 % | +0.58 / 38 % | 47.1 |
| **FULL_qlLA_G** | **0.117** | 0.068 | 2.16 | 1.49 | 66.8 % | -0.21 / 26 % | 47.7 |

## Beyond the knee (1.2 x Lsat): accepted throughput

| variant | uniform | localized |
|---|---|---|
| DeFT_tm(rho*) | 0.0611 | 0.0905 |
| CI_heurLA -> CI_heurLA_G | 0.0498 -> 0.0558 | 0.0804 -> 0.0867 |
| CI_qlLA -> CI_qlLA_G | 0.0550 -> **0.0638** | 0.0856 -> **0.0964** |
| FULL_qlLA -> FULL_qlLA_G | 0.0576 -> **0.0638** | 0.0915 -> **0.0958** |

(Interposer link load at 1.2 x Lsat is not comparable across variants: the accepted traffic differs.)

## What this shows
* **gamma moves CI's load from the interposer back to the chiplet layer.** At 1.0 x Lsat, with the same delivered
  traffic, CI's interposer link load falls from 0.144 / 0.143 to 0.136 / 0.134. That removes about two thirds of its
  excess over DeFT_tm(rho*) (0.131). Its chiplet-layer load rises from 0.042 to 0.046 / 0.045, still below DeFT_tm's
  0.056. Localized shows the same (0.142 -> 0.132 / 0.134 against 0.128).
* **The detours disappear.** Mean extra hops against the LUT path become negative (-0.24, -0.31: shorter than the LUT
  path on average); the share of packets with extra hops falls from 27-29 % to 17-19 %. Fewer entries differ from the
  LUT's (66 % against 74 %).
* **FULL_qlLA_G overshoots.** Its interposer load drops to 0.117, 11 % *below* DeFT_tm's, and its chiplet load rises
  to 0.068.
* **The centre concentration does not decrease.** The centre / rest ratio rises slightly for every _G variant (CI 2.01 /
  1.94 against 1.94 / 1.80). Entry-VL imbalance also rises (1.71 / 1.54 against 1.46 / 1.35). The total interposer
  load falls mainly outside the centre.
* **Beyond the knee the _G learners exceed DeFT_tm(rho*).** At 1.2 x Lsat CI_qlLA_G and FULL_qlLA_G accept 0.0638 on
  uniform (DeFT_tm 0.0611) and 0.0964 / 0.0958 on localized (0.0905), 3 seeds. CI_heurLA_G improves (+12 % / +8 %) but
  stays below.

## Pre-registered closeness criterion (cell: 4x4 uniform, 1.0 x Lsat)

| variant | interposer load | parent's | DeFT_tm's | closer to DeFT_tm than the parent |
|---|---|---|---|---|
| CI_heurLA_G | 0.1363 | 0.1442 | 0.1308 | **yes** |
| CI_qlLA_G | 0.1342 | 0.1432 | 0.1308 | **yes** |
| FULL_qlLA_G | 0.1167 | 0.1308 | 0.1308 | **no** (the parent already equals DeFT_tm; gamma moves it below) |

Descriptively, over the six step-4 cells the CI variants are closer in 4 to 5 of 6. The exceptions are the 1.2 x Lsat
cells, where the accepted traffic differs.
