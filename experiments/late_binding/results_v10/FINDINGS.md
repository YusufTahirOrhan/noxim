# v10 findings: comparison with the baselines of the DeFT paper (Parts A-B)

## Documents and data
* Design: `BASELINES_DESIGN.md` (before any code).
* Pre-registration: `PREREGISTRATION.md` (6af0e38, before any Part B run).
* Decisions: `DECISIONS.md`.
* Tables: `report/summary.md`, `report/primary.csv`, `report/ablation.csv`, `report/secondary.csv`,
  `report/saturation.csv`.
* Figures: `report/effects_vs_deft.{png,pdf}`, `report/reachability.{png,pdf}`.
* Per-run data: `eval_runs.csv` (9100 new runs).

## Run integrity
* Evaluation: 9100 / 9100 new runs (seeds 41-50), 0 missing, 0 dead-end events. DeFT(rho*), CI_heurLA_G, CI_qlLA_G and
  FULL_qlLA_G are the v9 runs; the reuse check re-ran 20 of them, 20 / 20 identical.
* Defaults: the new options left all 66 regression runs byte-identical (options absent and explicit).
* Drain tests: 246 / 246 PASS.
* Formal checks: MTR full-system CDG acyclic on 2x2/3x3/4x4; DeFT_OE_G relation checked on 28 masks.
* Binary: md5 1684544f (code of ac366c0).

## 1. The baselines (Part A)
* **MTR** (`mtr_search.md`):
  - The optimal restriction set allows only vertical inbound turns, so each boundary router delivers to its own
    column.
  - All outbound turns stay allowed, and the assignment balances 4 / 4 / 4 / 4 nodes.
* **RC:** an RC buffer of 4 packet slots per boundary router, and injection permission with FIFO grants.
* **DeFT-Dis / DeFT-Ran:** DeFT's routing and VNs with the nearest / a random VL pair.
* **XY-SP:** XY with the shortest VL pair and DeFT's VNs. It is valid: all its drain tests pass.
* **DeFT_OE_G:** FULL_qlLA_G with the VL pair fixed by DeFT's LUT.

## 2. Sanity check against the DeFT paper (A5): not met, explained
* **What we see:** on 2x2 uniform, MTR and RC are faster than DeFT(rho*). The DeFT paper reports the opposite.
* **Investigation** (`sanity_check.md`):
  - With DeFT's VN rules on MTR's routes, MTR is as slow as DeFT.
  - Without the VN rules, DeFT's own routes deadlock.
* **Conclusion:** the gap is the buffering cost of DeFT's VN-based deadlock avoidance: each segment of an inter-chiplet
  path uses one of the two VCs. MTR (turn restrictions) and RC (injection control) avoid this, with the same 2 VCs.
  The baselines were kept as specified, the setting that does not favour our methods. The evaluation confirms it on
  all sizes (section 5).

## 3. Primary results (pre-registered; Holm over 48): **48 of 48 supported**
On every size, CI_qlLA_G and FULL_qlLA_G have significantly lower mean and p99 latency at 1.0 x Lsat than MTR and RC
(fault-free scenarios) and DeFT-Dis and DeFT-Ran (all scenarios). None of the 48 is against our methods.

| size | ours | vs MTR: LAT / P99 | vs RC: LAT / P99 | vs DeFT-Dis: LAT / P99 | vs DeFT-Ran: LAT / P99 |
|---|---|---|---|---|---|
| 2x2 | CI_qlLA_G | -21.6 / -32.3 | -11.6 / -22.5 | -51.7 / -67.2 | -74.0 / -78.1 |
| | FULL_qlLA_G | -17.1 / -33.9 | -6.5 / -24.4 | -48.7 / -66.8 | -72.4 / -77.9 |
| 3x3 | CI_qlLA_G | -30.7 / -47.9 | -29.8 / -48.3 | -55.5 / -76.3 | -67.5 / -77.8 |
| | FULL_qlLA_G | -37.6 / -56.5 | -36.7 / -56.8 | -59.6 / -80.0 | -70.5 / -81.2 |
| 4x4 | CI_qlLA_G | -21.9 / -35.1 | -21.3 / -32.9 | -48.0 / -70.6 | -45.0 / -60.7 |
| | FULL_qlLA_G | -37.7 / -51.9 | -37.2 / -50.2 | -57.0 / -77.0 | -54.5 / -69.3 |

% change, mean over the scenarios of the per-seed log ratio. 95 % intervals and Holm p are in `report/summary.md`:
* largest Holm p 0.015 (2x2 FULL_qlLA_G vs RC, LAT);
* all others below 0.002.

## 4. Ablation (Holm over 6): **6 of 6 supported**
FULL_qlLA_G vs DeFT_OE_G: the same odd-even routing, selection, parameters and gamma, with the VL pair fixed by the
LUT instead of late binding.

| size | mean latency | p99 latency | saturation throughput (secondary) |
|---|---|---|---|
| 2x2 | -32.8 [-35.6, -29.8] | -55.5 [-59.1, -51.5] | +8.7 [+7.4, +10.0] |
| 3x3 | -32.4 [-34.6, -30.1] | -52.5 [-56.0, -48.6] | +5.9 [+5.1, +6.7] |
| 4x4 | -57.4 [-59.9, -54.6] | -72.3 [-75.3, -69.0] | +21.4 [+20.0, +22.9] |

Late binding, not the adaptive selection, carries the gain:
* Adaptive odd-even routing with the learned selection but a fixed VL pair (DeFT_OE_G) is no better than DeFT(rho*)
  on 2x2/3x3 (LAT +6.1 % / +4.8 %).
* It is clearly worse on 4x4 (LAT +39.5 %, THR -14.0 %).

## 5. Secondary (unadjusted)
* **Saturation throughput against the baselines:**
  - Our variants are **below MTR and RC**: -1.4 % to -2.4 % (CI_qlLA_G) and -6 % to -9 % (FULL_qlLA_G) on 2x2/3x3,
    and -6 % to -9 % on 4x4.
  - MTR and RC themselves are +3.4 % to +10.6 % above DeFT(rho*), the VN effect of section 2.
  - Our variants are above DeFT-Dis (+5.5 % to +12.8 %), DeFT-Ran (+8.4 % to +26.7 %) and XY-SP (+42 % to +53 %).
* **XY-SP:** it is valid but saturates at 0.5-0.8 x Lsat in most scenarios; mean latency at 1.0 x Lsat is 5-8 times
  DeFT(rho*)'s.
* **DeFT(rho*) against the baselines** (the DeFT paper's claims):

  | DeFT(rho*) vs | result | matches the DeFT paper? |
  |---|---|---|
  | DeFT-Dis, DeFT-Ran, XY-SP | lower latency and higher throughput on every size | yes |
  | MTR, RC: latency | DeFT is slower on 2x2 (MTR -13 %, RC -23 %) and 4x4 (-9 %, -10 %) but faster on 3x3 (+13.6 %, +12.1 %) | partly |
  | MTR, RC: p99 latency | MTR and RC lower on 2x2 and 4x4 (-34 % to -42 %), level on 3x3 | no |
  | MTR, RC: saturation throughput | MTR and RC higher on every size | no |

  For MTR and RC the paper's claims are therefore not reproduced in our setting (equal VCs, MTR and RC free of VN
  rules); section 2 explains why.
* **Saturation flags** (`report/saturation.csv`):
  - MTR and RC saturate below 1.0 x Lsat on 3x3/4x4 hotspot (fault-free), RC already at 0.5 x Lsat on 4x4.
  - DeFT-Dis saturates below 1.0 x Lsat on hotspot.
  - DeFT-Ran on 2x2/3x3 uniform and localized.
  - DeFT_OE_G on chipperm.
  - Our variants never do.

## 6. Reachability under VL faults (A6; `report/reachability.*`)
* **DeFT, CI, FULL:** 100 % at 1/16, 2/16 and 4/16 faulty VLs on every size and every mask (up to 1000 masks per
  point).
* **MTR (best case) and RC:** they lose exactly the faulty share of the VLs on every mask: 93.75 % / 87.5 % / 75 % of
  the inter-chiplet pairs. MTR's boundary router is the only entry of its column, and RC's is the only exit of its 4
  nearest sources.

## Bottom line
* **Against MTR and RC on fault-free traffic:** the late-binding learners have 6-38 % lower mean and 22-57 % lower p99
  latency on all sizes (all significant). MTR and RC sustain 1-9 % more saturation throughput, because they need no
  virtual-network separation.
* **Against DeFT's fault-tolerant baselines (DeFT-Dis, DeFT-Ran):** our variants are better in all three metrics on all
  sizes.
* **The ablation:** it isolates late binding as the source of the gain. The same adaptive routing and selection with a
  fixed VL pair loses 32-57 % mean latency.
* **Fault tolerance:** our methods keep DeFT's full reachability under VL faults, while MTR and RC lose a share of
  pairs equal to the fault rate.
