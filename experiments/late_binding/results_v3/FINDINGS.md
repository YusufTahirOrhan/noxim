# v3 findings: confirmatory test of near-saturation latency

Question: v2 found, as a *secondary* result, that late binding cuts mean and p99 latency at
~1.0 x DeFT's Lsat. Does that hold on new seeds with nothing re-tuned?
Design: `PREREGISTRATION.md` (committed before any v3 run). Parameters are frozen from v2.
New seeds 11-20, the 11 v2 scenarios, loads 0.8, 1.0 and 1.2 x Lsat, the v2 statistic, Holm
over 10 tests. Tables: `confirm_summary.md`, `primary_v3.csv`; figure: `confirm_primary.png`;
per-run data: `confirm_runs.csv`, `window_runs.csv`.

Run integrity: 2310 / 2310 confirmatory runs and 45 / 45 window runs, no missing outputs, 0
dead-end events. The v2 per-run CSV re-analysis reproduces the v2 primary table byte for byte
(step 1, `primary_from_csv_check.txt`).

## 1. Primary result: 8 of 10 hypotheses confirmed, 2 not confirmed, none contradicted
| comparison | metric | v3 (seeds 11-20) % [95 % CI] | Holm p | verdict | v2 (seeds 1-10) |
|---|---|---|---|---|---|
| CI_heur vs DeFT_tm | mean | -17.6 [-19.9, -15.3] | 7e-7 | confirmed | -16.0 |
| CI_heur vs DeFT_tm | p99 | -32.5 [-36.3, -28.5] | 7e-7 | confirmed | -29.1 |
| CI_heurLA vs DeFT_tm | mean | -21.4 [-24.5, -18.3] | 1e-6 | confirmed | -19.6 |
| CI_heurLA vs DeFT_tm | p99 | -35.3 [-40.7, -29.3] | 4e-6 | confirmed | -32.3 |
| CI_qlLA vs DeFT_tm | mean | -23.3 [-25.8, -20.7] | 3e-7 | confirmed | -22.1 |
| CI_qlLA vs DeFT_tm | p99 | -38.7 [-43.9, -33.1] | 2e-6 | confirmed | -36.8 |
| **CI_qlLA vs CI_heurLA** | mean | -2.4 [-4.4, -0.3] (p = 0.029 unadjusted) | 0.057 | **not confirmed** | -3.1 |
| **CI_qlLA vs CI_heurLA** | p99 | -5.3 [-10.8, +0.5] (p = 0.066) | 0.066 | **not confirmed** | -6.7 |
| FULL_heurLA vs DeFT_tm | mean | -26.2 [-29.0, -23.2] | 3e-7 | confirmed | -24.8 |
| FULL_heurLA vs DeFT_tm | p99 | -46.0 [-51.0, -40.6] | 9e-7 | confirmed | -44.9 |

* **Late binding vs the traffic-matched DeFT is confirmed.** Near DeFT's saturation point, every
  late-binding configuration tested has lower mean latency (-18 % to -26 %) and lower p99 latency
  (-32 % to -46 %) than DeFT_tm, on seeds that played no part in forming the hypothesis. The v3
  estimates are within the v2 intervals or slightly larger.
* **Learning over the lookahead heuristic is not confirmed.** The point estimates have the v2
  sign and similar size (-2.4 % mean, -5.3 % p99), but after Holm correction neither
  reaches 0.05. The mean-latency interval only just excludes 0 before correction. A benefit
  of 2-5 % may be real, but this experiment cannot establish it. It remains a negative
  confirmatory result for the learner.

## 2. Window sensitivity: the near-Lsat differences are not a short-window artefact (secondary)
DeFT_tm vs CI_heurLA and CI_qlLA at 1.0 x Lsat on uniform, hotspot and movinghot, seeds
11-15, 40000 instead of 8000 measured cycles: **all 12 readings are "consistent across windows"**
by the pre-stated rule.
* Uniform and movinghot: effects at 40000 cycles match those at 8000 within about 3
  percentage points, with intervals 2-4 times narrower.
* Hotspot: the 8000-cycle intervals include 0, but at 40000 cycles the effect is larger and
  clearly negative (CI_heurLA: mean -14.0 % -> -24.6 %; p99 -22.2 % -> -41.6 %). DeFT_tm's mean
  latency on hotspot still grows with the window (46.5 -> 55.3 cycles), while the late-binding
  variants stay near 40 cycles. DeFT is at its knee there by construction, so the short window
  *understates* the difference rather than inflating it.
* This covers 3 of 11 scenarios and 5 seeds. The faulty and chipperm scenarios were not
  re-run with the long window.

## 3. Secondary results (descriptive, unadjusted; not significance claims)
* **The gap depends on load.** At 0.8 x Lsat the reductions are smaller (mean -6 % to -12 %,
  p99 -9 % to -23 %). At 1.2 x Lsat they are larger (mean -30 % to -49 %), but there DeFT_tm is
  past its knee and the fixed-window latency is not a steady state.
* **Per scenario, the gains are concentrated outside chipperm.** On the three chipperm scenarios
  (where DeFT_tm's matched LUT already balances the VLs) the mean-latency changes are -0.3 %
  to -8.7 %. CI_heur is +3.6 % *worse* than DeFT_tm on chipperm 0x1111, the only adverse
  cell. On the other 8 scenarios the reductions are -17 % to -46 %.
* **Learning vs heuristic (not primary):** CI_ql vs CI_heur gives mean -4.0 % [-6.0, -1.9] and
  FULL_qlLA vs FULL_heurLA gives -4.9 % [-6.7, -3.1] at 1.0 x Lsat. These are small and in
  the same direction as the unconfirmed primary comparison. FULL_qlLA has the lowest
  near-Lsat latency of all (mean -29.8 %, p99 -49.9 % vs DeFT_tm).
* **Accepted throughput (max over 0.8-1.2 x Lsat) is uninformative here.** 89-110 of the 110
  seed-scenario cells are capped by the highest offered load, so it does not test v2's
  saturation-throughput results. In particular, FULL_heurLA's significant v2 throughput loss
  (-1.7 %) is neither confirmed nor refuted by v3 (-0.3 % [-1.5, +1.0], capped).

## 4. What this changes in the v2 conclusions
* v2's secondary near-saturation latency result can now be stated as a confirmed result
  for the four late-binding configurations against DeFT_tm, with these limits: this topology
  instance, these synthetic patterns, a load defined relative to DeFT's own Lsat.
* The claim "learning helps over the same information" stays unconfirmed at the
  pre-registered level. v2's primary LAT result at 0.5 x Lsat for CI_qlLA vs CI_heurLA
  (-1.1 %) was significant there but is small. Taken together, the learner's
  benefit is at most a few per cent.

## 5. Exploratory tuning beyond the v2 grid edges (step 4; secondary, seeds 101/102, CI only)
`tuning_explore.md`. **Neither edge optimum moves.**
* CI heuristic, w in {2, 4, 8} x busy in {0, 4}: w = 2, busy = 0 (the v2 choice) stays best.
  The next best is w = 4 / busy 0 at +4.0 %, and larger weights get steadily worse (w = 8:
  +14 % / +21 %).
* CI_ql, alpha in {0.001, 0.002, 0.005}: alpha = 0.005 (the v2 choice) stays best. Smaller
  rates are worse (+2.5 % at 0.002, +4.9 % at 0.001).
* The tuning criterion therefore changes by 0 %: the v2 edge choices were at the optimum
  of the extended range for both parameters. All 48 runs shared with the v2 tuning
  reproduce exactly (determinism check). These values were not used in step 3.

The new HL-fault measurements (step 5) are in `hl_coverage_v3.md` and summarised below once
available.
