# Tuning of the DeFT LUT weight rho (seeds 101, 102)

Cells and criterion as for the other methods: uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; loads ~0.8 and ~1.1 x Lsat (2x2: v2 tuning loads; 3x3/4x4: from the v4 Lsat); 2 seeds = 16 runs per configuration; criterion = geometric mean of the mean latency. DeFT_tm uses the traffic-matched LUT on hotspot/chipperm and the uniform LUT (= DeFT) on the uniform cells. "Accepted @1.1" = geometric mean of the accepted throughput at the ~1.1 x Lsat load (the tuning loads do not reach saturation everywhere, so this stands in for saturation throughput). VL imbalance = analytic max/mean of the LUT fault-free (lut_scaling.py), under the LUT's own demand (uniform LUT: uniform; DeFT_tm: hotspot / chipperm).

## 2x2 DeFT

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 (chosen) | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |
| 0.003 | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |
| 0.001 | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |
| 0.0003 | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |
| 0.0001 | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |
| 0 | 16 | 61.41 | +0.00 % | 0.0659 | 1.000 |

## 2x2 DeFT_tm

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 (chosen) | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |
| 0.003 | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |
| 0.001 | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |
| 0.0003 | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |
| 0.0001 | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |
| 0 | 16 | 51.40 | +0.00 % | 0.0661 | 1.039 / 1.000 |

## 3x3 DeFT

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 (chosen) | 16 | 75.63 | +0.00 % | 0.0497 | 1.000 |
| 0.003 | 16 | 78.28 | +3.51 % | 0.0495 | 1.000 |
| 0.001 | 16 | 78.53 | +3.83 % | 0.0494 | 1.000 |
| 0.0003 | 16 | 78.53 | +3.83 % | 0.0494 | 1.000 |
| 0.0001 | 16 | 78.53 | +3.83 % | 0.0494 | 1.000 |
| 0 | 16 | 76.80 | +1.54 % | 0.0491 | 1.000 |

## 3x3 DeFT_tm

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 | 16 | 68.49 | +0.00 % | 0.0497 | 1.259 / 1.125 |
| 0.003 | 16 | 63.35 | -7.50 % | 0.0495 | 1.259 / 1.125 |
| 0.001 | 16 | 66.28 | -3.23 % | 0.0499 | 1.259 / 1.125 |
| 0.0003 | 16 | 63.82 | -6.82 % | 0.0498 | 1.259 / 1.125 |
| 0.0001 | 16 | 69.92 | +2.08 % | 0.0498 | 1.259 / 1.125 |
| 0 (chosen) | 16 | 60.47 | -11.72 % | 0.0499 | 1.259 / 1.125 |

## 4x4 DeFT

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 | 16 | 87.34 | +0.00 % | 0.0267 | 1.400 |
| 0.003 | 16 | 56.59 | -35.21 % | 0.0271 | 1.000 |
| 0.001 (chosen) | 16 | 55.22 | -36.78 % | 0.0269 | 1.000 |
| 0.0003 | 16 | 57.40 | -34.28 % | 0.0270 | 1.000 |
| 0.0001 | 16 | 57.40 | -34.28 % | 0.0270 | 1.000 |
| 0 | 16 | 58.09 | -33.50 % | 0.0270 | 1.000 |

## 4x4 DeFT_tm

| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | analytic VL imbalance |
|---|---|---|---|---|---|
| 0.01 | 16 | 66.98 | +0.00 % | 0.0269 | 2.489 / 1.000 |
| 0.003 (chosen) | 16 | 55.00 | -17.89 % | 0.0270 | 1.599 / 1.000 |
| 0.001 | 16 | 58.18 | -13.14 % | 0.0268 | 1.599 / 1.000 |
| 0.0003 | 16 | 59.65 | -10.95 % | 0.0269 | 1.599 / 1.000 |
| 0.0001 | 16 | 57.24 | -14.55 % | 0.0271 | 1.599 / 1.000 |
| 0 | 16 | 57.28 | -14.49 % | 0.0269 | 1.599 / 1.000 |

Budget: 6 configurations (rho values) per size and variant, 16 runs each; DeFT_tm reuses the DeFT runs on the uniform cells. The CI variants take their exit VL from the uniform LUT of DeFT's rho*.

## Reading
* **2x2: rho does not matter.** All six values give identical runs (the LUTs are already balanced at
  minimal distance), so rho* = 0.01 (the tie rule keeps the original).
* **3x3:** DeFT keeps rho* = 0.01. DeFT_tm picks rho* = 0 (-11.7 % on the tuning criterion), but its
  analytic imbalance is the same for every rho. The spread between rho values (-11.7 % to +2.1 %) is
  partly differences between equally balanced LUTs, i.e. noise on 2 seeds. The rule (best
  geometric-mean latency) was applied as fixed, which favours the baseline.
* **4x4: tuning matters a lot.** DeFT improves by 36.8 % at rho* = 0.001 and DeFT_tm by 17.9 % at
  rho* = 0.003. Both remove the LUT imbalance (analytic 1.40 -> 1.00 for the uniform LUT). This
  confirms the step-1 diagnosis that rho = 0.01 handicapped DeFT on 4x4.
* **DeFT and DeFT_tm chose different rho* on 3x3 and 4x4.** Each uses its own (DECISIONS item 7). The CI
  variants use the uniform LUT of DeFT's rho* (3x3: 0.01, 4x4: 0.001).
