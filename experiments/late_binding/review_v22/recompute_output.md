
## v19 K5 primary (Holm over 60): mine vs repository report (60 tests)
| size | variant | reference | metric | effect mine / repo | CI mine / repo | p_holm mine / repo | verdict mine / repo |
|---|---|---|---|---|---|---|---|
| 2x2 | CI_qlLA_G | DeFT | LAT | -24.10 / -24.10 | [-27.7, -20.3] / [-27.7, -20.3] | 1.4e-05 / 1.4e-05 | ours better / ours better |
| 2x2 | CI_qlLA_G | DeFT | P99 | -39.55 / -39.55 | [-46.2, -32.1] / [-46.2, -32.1] | 8.55e-05 / 8.55e-05 | ours better / ours better |
| 2x2 | FULL_qlLA_G | DeFT | LAT | -15.62 / -15.62 | [-19.4, -11.7] / [-19.4, -11.7] | 0.000177 / 0.000177 | ours better / ours better |
| 2x2 | FULL_qlLA_G | DeFT | P99 | -32.76 / -32.76 | [-39.2, -25.6] / [-39.2, -25.6] | 0.000136 / 0.000136 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT | LAT | -11.68 / -11.68 | [-14.4, -8.9] / [-14.4, -8.8] | 0.000136 / 0.000136 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT | P99 | -30.44 / -30.44 | [-34.8, -25.8] / [-34.8, -25.8] | 1.43e-05 / 1.43e-05 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT | LAT | -9.75 / -9.75 | [-12.4, -7.0] / [-12.4, -7.0] | 0.000308 / 0.000308 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT | P99 | -27.31 / -27.31 | [-32.3, -21.9] / [-32.4, -21.9] | 7.65e-05 / 7.65e-05 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT | LAT | -15.94 / -15.94 | [-19.1, -12.7] / [-19.1, -12.7] | 6.5e-05 / 6.5e-05 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT | P99 | -39.91 / -39.91 | [-44.2, -35.3] / [-44.2, -35.3] | 2.94e-06 / 2.94e-06 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT | LAT | -19.29 / -19.29 | [-23.4, -15.0] / [-23.4, -14.9] | 0.000115 / 0.000115 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT | P99 | -42.07 / -42.07 | [-47.7, -35.8] / [-47.7, -35.8] | 2.17e-05 / 2.17e-05 | ours better / ours better |
| 2x2 | CI_qlLA_G | MTR | LAT | -6.50 / -6.50 | [-11.9, -0.8] / [-11.9, -0.8] | 0.186 / 0.186 | n.s. / n.s. |
| 2x2 | CI_qlLA_G | MTR | P99 | -13.56 / -13.56 | [-20.8, -5.7] / [-20.8, -5.7] | 0.0352 / 0.0352 | ours better / ours better |
| 2x2 | CI_qlLA_G | RC | LAT | -1.07 / -1.07 | [-8.0, +6.4] / [-8.0, +6.4] | 0.984 / 0.984 | n.s. / n.s. |
| 2x2 | CI_qlLA_G | RC | P99 | -5.58 / -5.58 | [-15.3, +5.2] / [-15.2, +5.2] | 0.945 / 0.945 | n.s. / n.s. |
| 2x2 | CI_qlLA_G | DeFT_Dis | LAT | -41.91 / -41.91 | [-45.3, -38.3] / [-45.3, -38.3] | 3.85e-07 / 3.85e-07 | ours better / ours better |
| 2x2 | CI_qlLA_G | DeFT_Dis | P99 | -56.42 / -56.42 | [-59.7, -52.8] / [-59.8, -52.8] | 1.04e-07 / 1.04e-07 | ours better / ours better |
| 2x2 | CI_qlLA_G | DeFT_Ran | LAT | -62.13 / -62.13 | [-65.4, -58.6] / [-65.4, -58.6] | 7.85e-08 / 7.85e-08 | ours better / ours better |
| 2x2 | CI_qlLA_G | DeFT_Ran | P99 | -68.26 / -68.26 | [-71.8, -64.3] / [-71.8, -64.3] | 1.82e-07 / 1.82e-07 | ours better / ours better |
| 2x2 | FULL_qlLA_G | MTR | LAT | +5.18 / +5.18 | [-2.3, +13.2] / [-2.3, +13.2] | 0.773 / 0.773 | n.s. / n.s. |
| 2x2 | FULL_qlLA_G | MTR | P99 | -3.66 / -3.66 | [-14.4, +8.4] / [-14.3, +8.4] | 0.984 / 0.984 | n.s. / n.s. |
| 2x2 | FULL_qlLA_G | RC | LAT | +11.29 / +11.29 | [+4.3, +18.8] / [+4.3, +18.8] | 0.0352 / 0.0352 | ours worse / ours worse |
| 2x2 | FULL_qlLA_G | RC | P99 | +5.24 / +5.24 | [-3.9, +15.3] / [-3.9, +15.3] | 0.945 / 0.945 | n.s. / n.s. |
| 2x2 | FULL_qlLA_G | DeFT_Dis | LAT | -35.43 / -35.43 | [-39.5, -31.1] / [-39.5, -31.1] | 3.46e-06 / 3.46e-06 | ours better / ours better |
| 2x2 | FULL_qlLA_G | DeFT_Dis | P99 | -51.53 / -51.53 | [-55.6, -47.1] / [-55.6, -47.1] | 7.36e-07 / 7.36e-07 | ours better / ours better |
| 2x2 | FULL_qlLA_G | DeFT_Ran | LAT | -57.90 / -57.90 | [-61.7, -53.7] / [-61.8, -53.7] | 3.61e-07 / 3.61e-07 | ours better / ours better |
| 2x2 | FULL_qlLA_G | DeFT_Ran | P99 | -64.70 / -64.70 | [-69.1, -59.7] / [-69.1, -59.7] | 1.11e-06 / 1.11e-06 | ours better / ours better |
| 3x3 | CI_qlLA_G | MTR | LAT | -16.40 / -16.40 | [-20.3, -12.4] / [-20.2, -12.4] | 0.000161 / 0.000161 | ours better / ours better |
| 3x3 | CI_qlLA_G | MTR | P99 | -31.43 / -31.43 | [-35.8, -26.8] / [-35.8, -26.8] | 1.24e-05 / 1.24e-05 | ours better / ours better |
| 3x3 | CI_qlLA_G | RC | LAT | -16.58 / -16.58 | [-18.9, -14.2] / [-18.9, -14.2] | 5.08e-06 / 5.08e-06 | ours better / ours better |
| 3x3 | CI_qlLA_G | RC | P99 | -30.88 / -30.88 | [-34.4, -27.1] / [-34.4, -27.1] | 2.78e-06 / 2.78e-06 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT_Dis | LAT | -53.79 / -53.79 | [-55.3, -52.2] / [-55.3, -52.2] | 1e-10 / 1e-10 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT_Dis | P99 | -69.89 / -69.89 | [-71.7, -67.9] / [-71.7, -67.9] | 5.85e-10 / 5.85e-10 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT_Ran | LAT | -56.14 / -56.14 | [-60.6, -51.1] / [-60.6, -51.1] | 1.39e-06 / 1.39e-06 | ours better / ours better |
| 3x3 | CI_qlLA_G | DeFT_Ran | P99 | -70.95 / -70.95 | [-74.4, -67.1] / [-74.4, -67.1] | 1.68e-07 / 1.68e-07 | ours better / ours better |
| 3x3 | FULL_qlLA_G | MTR | LAT | -14.21 / -14.21 | [-18.9, -9.2] / [-18.9, -9.2] | 0.00158 / 0.00158 | ours better / ours better |
| 3x3 | FULL_qlLA_G | MTR | P99 | -28.09 / -28.09 | [-33.7, -22.0] / [-33.7, -22.0] | 0.000115 / 0.000115 | ours better / ours better |
| 3x3 | FULL_qlLA_G | RC | LAT | -14.39 / -14.39 | [-17.2, -11.5] / [-17.2, -11.5] | 5.1e-05 / 5.1e-05 | ours better / ours better |
| 3x3 | FULL_qlLA_G | RC | P99 | -27.51 / -27.51 | [-31.9, -22.8] / [-31.9, -22.8] | 2.87e-05 / 2.87e-05 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT_Dis | LAT | -52.79 / -52.79 | [-54.9, -50.6] / [-54.9, -50.6] | 1.74e-09 / 1.74e-09 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT_Dis | P99 | -68.54 / -68.54 | [-70.9, -66.0] / [-70.9, -66.0] | 4.21e-09 / 4.21e-09 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT_Ran | LAT | -55.18 / -55.18 | [-60.2, -49.6] / [-60.2, -49.6] | 3.46e-06 / 3.46e-06 | ours better / ours better |
| 3x3 | FULL_qlLA_G | DeFT_Ran | P99 | -69.64 / -69.64 | [-73.7, -64.9] / [-73.7, -65.0] | 7.35e-07 / 7.35e-07 | ours better / ours better |
| 4x4 | CI_qlLA_G | MTR | LAT | -11.29 / -11.29 | [-13.8, -8.7] / [-13.8, -8.7] | 0.000106 / 0.000106 | ours better / ours better |
| 4x4 | CI_qlLA_G | MTR | P99 | -25.48 / -25.48 | [-29.5, -21.2] / [-29.5, -21.2] | 2.17e-05 / 2.17e-05 | ours better / ours better |
| 4x4 | CI_qlLA_G | RC | LAT | -11.25 / -11.25 | [-14.8, -7.5] / [-14.8, -7.5] | 0.00105 / 0.00105 | ours better / ours better |
| 4x4 | CI_qlLA_G | RC | P99 | -26.50 / -26.50 | [-31.7, -20.9] / [-31.7, -20.9] | 0.000101 / 0.000101 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT_Dis | LAT | -47.94 / -47.94 | [-49.8, -46.1] / [-49.8, -46.1] | 7.13e-10 / 7.13e-10 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT_Dis | P99 | -65.25 / -65.25 | [-68.5, -61.7] / [-68.5, -61.7] | 7.41e-08 / 7.41e-08 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT_Ran | LAT | -32.21 / -32.21 | [-35.7, -28.5] / [-35.7, -28.5] | 2.01e-06 / 2.01e-06 | ours better / ours better |
| 4x4 | CI_qlLA_G | DeFT_Ran | P99 | -45.60 / -45.60 | [-50.9, -39.7] / [-51.0, -39.7] | 1.08e-05 / 1.08e-05 | ours better / ours better |
| 4x4 | FULL_qlLA_G | MTR | LAT | -12.76 / -12.76 | [-15.5, -10.0] / [-15.4, -10.0] | 8.55e-05 / 8.55e-05 | ours better / ours better |
| 4x4 | FULL_qlLA_G | MTR | P99 | -23.78 / -23.78 | [-27.8, -19.5] / [-27.9, -19.5] | 3.62e-05 / 3.61e-05 | ours better / ours better |
| 4x4 | FULL_qlLA_G | RC | LAT | -12.72 / -12.72 | [-15.3, -10.1] / [-15.3, -10.1] | 6.8e-05 / 6.8e-05 | ours better / ours better |
| 4x4 | FULL_qlLA_G | RC | P99 | -24.82 / -24.82 | [-28.7, -20.8] / [-28.7, -20.8] | 1.89e-05 / 1.89e-05 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT_Dis | LAT | -50.02 / -50.02 | [-51.1, -48.9] / [-51.1, -49.0] | 4.6e-12 / 4.6e-12 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT_Dis | P99 | -66.50 / -66.50 | [-68.0, -64.9] / [-68.0, -64.9] | 8.72e-11 / 8.72e-11 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT_Ran | LAT | -34.91 / -34.91 | [-38.4, -31.3] / [-38.4, -31.3] | 1.08e-06 / 1.08e-06 | ours better / ours better |
| 4x4 | FULL_qlLA_G | DeFT_Ran | P99 | -47.55 / -47.55 | [-52.5, -42.2] / [-52.5, -42.1] | 4.33e-06 / 4.33e-06 | ours better / ours better |

Largest absolute difference in effect or CI bound: 0.005 percentage points

## v19 secondary: DeFT(rho*) with round-robin vs MTR and RC, fault-free (unadjusted), mine
| size | ref | LAT | P99 | THR | cells whose max accepted sits at the top load, variant / reference |
|---|---|---|---|---|---|
| 2x2 | MTR | +24.7 [+13.3, +37.3] (p 0.00055) | +54.1 [+25.1, +89.8] (p 0.0011) | -8.0 [-8.6, -7.5] (p 2.2e-10) | 33/50 / 42/50 |
| 2x2 | RC | +32.0 [+22.9, +41.8] (p 1e-05) | +68.3 [+44.4, +96.1] (p 3e-05) | -9.3 [-9.7, -8.9] (p 2.5e-12) | 33/50 / 43/50 |
| 3x3 | MTR | -7.4 [-11.5, -3.1] (p 0.004) | -3.7 [-9.8, +2.9] (p 0.23) | -3.2 [-3.8, -2.7] (p 2.5e-07) | 37/50 / 46/50 |
| 3x3 | RC | -7.6 [-12.0, -3.0] (p 0.0053) | -2.9 [-9.0, +3.6] (p 0.34) | -3.5 [-4.0, -3.0] (p 7.4e-08) | 37/50 / 48/50 |
| 4x4 | MTR | +3.6 [-4.3, +12.1] (p 0.34) | +26.2 [+9.4, +45.6] (p 0.0051) | -6.8 [-7.3, -6.4] (p 1.5e-10) | 31/50 / 47/50 |
| 4x4 | RC | +3.6 [-2.9, +10.7] (p 0.25) | +24.5 [+11.3, +39.2] (p 0.0017) | -7.5 [-8.3, -6.7] (p 5.2e-09) | 31/50 / 48/50 |

## v21 primary rows of 3x3 (Holm over all 36): mine vs repository report (12 tests)
| size | variant | reference | metric | effect mine / repo | CI mine / repo | p_holm mine / repo | verdict mine / repo |
|---|---|---|---|---|---|---|---|
| 3x3 | CI_fastQL | DeFT | LAT | +0.04 / +0.04 | [-3.9, +4.2] / [-3.9, +4.2] | 1 / 1 | n.s. / n.s. |
| 3x3 | CI_fastQL | DeFT | P99 | -32.18 / -32.18 | [-37.8, -26.1] / [-37.8, -26.1] | 7.64e-05 / 7.64e-05 | ours better / ours better |
| 3x3 | CI_fastQL | MTR | LAT | -4.16 / -4.16 | [-8.1, -0.1] / [-8.1, -0.1] | 0.477 / 0.477 | n.s. / n.s. |
| 3x3 | CI_fastQL | MTR | P99 | -28.00 / -28.00 | [-33.2, -22.4] / [-33.2, -22.4] | 8.71e-05 / 8.71e-05 | ours better / ours better |
| 3x3 | CI_fastQL | RC | LAT | -2.29 / -2.29 | [-6.0, +1.6] / [-6.0, +1.6] | 1 / 1 | n.s. / n.s. |
| 3x3 | CI_fastQL | RC | P99 | -25.50 / -25.50 | [-30.7, -19.9] / [-30.7, -19.9] | 0.000152 / 0.000152 | ours better / ours better |
| 3x3 | FULL_fastQL | DeFT | LAT | +4.22 / +4.22 | [+0.8, +7.7] / [+0.8, +7.7] | 0.217 / 0.217 | n.s. / n.s. |
| 3x3 | FULL_fastQL | DeFT | P99 | -36.82 / -36.82 | [-41.4, -31.9] / [-41.4, -31.9] | 7.24e-06 / 7.24e-06 | ours better / ours better |
| 3x3 | FULL_fastQL | MTR | LAT | -0.92 / -0.92 | [-4.3, +2.6] / [-4.3, +2.6] | 1 / 1 | n.s. / n.s. |
| 3x3 | FULL_fastQL | MTR | P99 | -34.02 / -34.02 | [-37.3, -30.6] / [-37.3, -30.6] | 6.36e-07 / 6.36e-07 | ours better / ours better |
| 3x3 | FULL_fastQL | RC | LAT | +1.01 / +1.01 | [-3.4, +5.6] / [-3.4, +5.6] | 1 / 1 | n.s. / n.s. |
| 3x3 | FULL_fastQL | RC | P99 | -31.73 / -31.73 | [-36.2, -26.9] / [-36.2, -26.9] | 1.38e-05 / 1.38e-05 | ours better / ours better |

Largest absolute difference in effect or CI bound: 0.005 percentage points

## v21 secondary on 3x3: LAT at 0.2 x Lsat vs DeFT, all four variants, mine vs report/secondary.csv
- CI_fast: mine +31.48 [+30.6, +32.3]  repo +31.48 [+30.6, +32.3]
- CI_fastQL: mine +50.86 [+50.1, +51.7]  repo +50.86 [+50.0, +51.7]
- FULL_fast: mine +61.44 [+60.5, +62.3]  repo +61.44 [+60.5, +62.3]
- FULL_fastQL: mine +62.75 [+61.9, +63.7]  repo +62.75 [+61.9, +63.6]

MAX_DIFF v19 0.0050 v21 0.0050
