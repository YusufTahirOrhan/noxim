# v19 findings: DeFT's boundary round-robin (Part K)

**Sources:** design `PREREGISTRATION.md` (dea53a6, before any evaluation run); decisions `DECISIONS.md`; tables `report/summary.md`; figure `report/latency_load.{png,pdf}`; data `eval_runs.csv`.

## Gates
* Regression: 84 / 84 byte-identical with the option off, absent or explicit (`regression.md`).
* Drain tests with the option: 432 / 432 PASS (`drain_summary.csv`).
* Model check: clean on all relations and sizes; its negative control reports a cycle (`formal_vnrr.md`).

## K3: VC balance (exploratory; `vc_balance.md`)
The option does what it should on the VC split: interposer and Down VL go from 87-88 : 12-13 (LB-F 100 : 0) to 50 : 50 (LB-F 56 : 44). The Up VL stays 0 : 100. Down VL waits fall, and **Up VL waits rise about 2 to 4 times**, for DeFT and for the learners: the rebalancing moves part of the wait rather than removing it. At the old 1.0 x Lsat, three seeds, DeFT's latency rises on 2x2 (54.3 to 58.1) and falls on 4x4 (83.4 to 75.9). The learners' latency rises on both sizes.

## K5: confirmatory re-evaluation (Holm over 60)
17,850 of 17,850 runs, 0 missing, 0 dead-end events. Binary md5 f72577901551675dfc2767526fd36844, the one that passed the gates. Seeds 61-70 were not reduced (`DECISIONS.md`).

### H1, against DeFT(rho*) with the round-robin: **12 of 12 supported**

| size | ours | LAT | P99 | v9 LAT / P99 (no round-robin) |
|---|---|---|---|---|
| 2x2 | CI_qlLA_G | -24.1 [-27.7, -20.3] | -39.5 [-46.2, -32.1] | -32.8 / -56.0 |
| 2x2 | FULL_qlLA_G | -15.6 [-19.4, -11.7] | -32.8 [-39.2, -25.6] | -28.7 / -55.6 |
| 3x3 | CI_qlLA_G | -11.7 [-14.4, -8.8] | -30.4 [-34.8, -25.8] | -21.8 / -46.0 |
| 3x3 | FULL_qlLA_G | -9.8 [-12.4, -7.0] | -27.3 [-32.4, -21.9] | -29.1 / -54.3 |
| 4x4 | CI_qlLA_G | -15.9 [-19.1, -12.7] | -39.9 [-44.2, -35.3] | -28.0 / -55.7 |
| 4x4 | FULL_qlLA_G | -19.3 [-23.4, -14.9] | -42.1 [-47.7, -35.8] | -40.5 / -65.3 |

**The gain over DeFT holds, but it is much smaller than published in v9:** roughly half or less for FULL_qlLA_G on latency, and about a quarter to a half smaller for CI_qlLA_G. The v9 column has other seeds and other loads, so this comparison is descriptive.

### H2, against the baselines: **41 of 48 supported, 6 n.s., 1 significant against ours**
* **DeFT-Dis and DeFT-Ran:** 24 of 24 supported on every size (-32 % to -71 %).
* **MTR and RC on 3x3 and 4x4:** 16 of 16 supported (LAT -11 % to -17 %, P99 -24 % to -31 %).
* **MTR and RC on 2x2: 1 of 8 supported.** This is the change from v10, which had 48 of 48:

| 2x2, fault-free | LAT | P99 |
|---|---|---|
| CI_qlLA_G vs MTR | -6.5 [-11.9, -0.8], n.s. | -13.6 [-20.8, -5.7], **supported** |
| CI_qlLA_G vs RC | -1.1 [-8.0, +6.4], n.s. | -5.6 [-15.2, +5.2], n.s. |
| FULL_qlLA_G vs MTR | +5.2 [-2.3, +13.2], n.s. | -3.7 [-14.3, +8.4], n.s. |
| FULL_qlLA_G vs RC | **+11.3 [+4.3, +18.8], significantly worse** | +5.2 [-3.9, +15.3], n.s. |

**So the claim "our methods beat MTR and RC on all sizes" no longer stands.** On 2x2, the learners are level with MTR and RC in latency, and FULL_qlLA_G is significantly slower than RC.

### Does DeFT with the round-robin still lose to MTR and RC? (fault-free, secondary, unadjusted)

| DeFT(rho*) with round-robin vs | LAT | P99 | THR |
|---|---|---|---|
| MTR, 2x2 | +24.7 [+13.3, +37.3] | +54.1 [+25.1, +89.8] | -8.0 [-8.6, -7.5] |
| RC, 2x2 | +32.0 [+22.9, +41.8] | +68.3 [+44.5, +96.1] | -9.3 [-9.7, -8.9] |
| MTR, 3x3 | -7.4 [-11.5, -3.1] | -3.6 [-9.8, +2.9] | -3.2 [-3.8, -2.7] |
| RC, 3x3 | -7.6 [-12.0, -3.0] | -2.9 [-9.0, +3.6] | -3.5 [-4.0, -3.0] |
| MTR, 4x4 | +3.6 [-4.3, +12.1] | +26.2 [+9.4, +45.6] | -6.8 [-7.3, -6.4] |
| RC, 4x4 | +3.6 [-3.0, +10.7] | +24.5 [+11.3, +39.2] | -7.5 [-8.3, -6.7] |

**Yes, mostly.** DeFT is below MTR and RC in throughput on every size, and slower in latency and p99 on 2x2 and in p99 on 4x4. It is faster in mean latency only on 3x3. **The fix does not close the gap to the DeFT paper's claims.** The VC split was therefore not the whole explanation that v17 suggested, at least not as far as this one fix can remove it.

### What the fix does to DeFT itself (with against without; secondary)

| size | LAT | P99 | THR |
|---|---|---|---|
| 2x2 | **+9.2 [+4.1, +14.6]** | +1.4 [-9.9, +14.1] | -0.3 [-0.7, +0.0] |
| 3x3 | -1.0 [-6.0, +4.2] | -13.0 [-21.7, -3.3] | +0.6 [-0.0, +1.3] |
| 4x4 | -3.9 [-7.9, +0.4] | -16.8 [-23.1, -10.1] | **+2.5 [+1.9, +3.1]** |

* **The fix helps with size.** It improves p99 on 3x3 and 4x4 and throughput on 4x4, and it **makes mean latency worse on 2x2**. The expectation in the pre-registration that DeFT would improve therefore holds only in part.
* DeFT was not the only method to change. All learners run with the option too, and K3 shows the option raises their latency; **their parameters were tuned without it**. The smaller gains above mix the gain DeFT made and the loss the learners took, and this design cannot separate them, since no learner was run without the option at these loads.

### Other secondary results (unadjusted)
* **Saturation throughput against DeFT(rho*):** CI_qlLA_G +4.5 % to +8.3 %. FULL_qlLA_G +2.7 % (2x2), **-2.9 % (3x3)**, +1.6 % (4x4).
* **Saturation throughput against MTR and RC:** CI_qlLA_G -2.6 % to -3.9 % on 2x2, +0.8 % to +1.1 % on 3x3, -2.3 % to -3.0 % on 4x4. FULL_qlLA_G -5.6 % to -8.6 % everywhere.
* **Against DeFT-Dis and DeFT-Ran:** both learners are higher on every size (+3.8 % to +23.7 %).
* **Ablation, FULL_qlLA_G vs DeFT_OE_G:** LAT -25.0 % / -12.3 % / -38.4 %, P99 -43.2 % / -25.6 % / -52.2 %, THR +6.6 % / +0.7 % (n.s.) / +14.3 %. Late binding still carries the gain, by less than in v10 (-32.8 % / -32.4 % / -57.4 %).
* **CI_qlLA_G vs CI_heurLA_G:** LAT -5.3 % / -5.4 % / -0.7 % (n.s.), THR +0.4 % / +2.2 % / +3.5 %. On 4x4 the heuristic matches the learner in mean latency.
* **Saturation flags** (`report/saturation.csv`): our variants are never flagged below 1.0 x Lsat. MTR and RC are flagged on 3x3 and 4x4 hotspot, RC already at 0.5 x Lsat on 4x4. DeFT-Dis on hotspot; DeFT-Ran on 2x2 uniform, localized and hotspot and on 3x3 hotspot; DeFT_OE_G on 4x4 chipperm; XY-SP in most scenarios.

### Limits of K5
* **Parameters:** all, including DeFT's rho\* LUT, were tuned without the round-robin and not re-tuned, as required. Which way this biases each comparison is not known, and the learners may lose more from it than DeFT does.
* **Loads:** chosen from DeFT with the round-robin, so 1.0 x Lsat is DeFT's own knee. This holds for every comparison, as in v9-v10.
* **Hardware:** the option's selection reads the round-robin counter of the neighbour for a Hub output (`DECISIONS.md`). The simulator reads it directly and this is not charged. All these latencies also assume a decision in zero extra cycles; Part L tests that.
* **Option vs paper:** `-deft_vn_rr 1` is not all of the paper's Algorithm 1. The F1 fix is kept, since the unrestricted source rule is unsafe.
