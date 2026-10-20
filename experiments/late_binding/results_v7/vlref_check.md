# VL-reference re-runs (v7 stage vlref): determinism and the v4-v6 VL imbalance bug

420 runs at 1.0 x Lsat, seeds 31-40, 3x3 and 4x4, 7 scenarios: DeFT_tm(rho*) through its traffic-identical DEFT_LB
proxy (140), CI_heurLA and CI_qlLA with the v6 tuned parameters (280). Per-run data: `vlref_runs.csv`.

* **Determinism:** the 280 CI_heurLA / CI_qlLA runs are identical to their `results_v6/eval_runs.csv` rows (mean latency,
  accepted throughput, p99; repr of the JSON values): **280 / 280**.
* **Bug confirmed:** for all **420 / 420** runs, the `vl_imbalance` value in `results_v6/eval_runs.csv` equals max/mean of
  the per-VL counts over VL ids 0-15 only (the first four chiplets), not over all 36 (3x3) or 64 (4x4) VLs. The
  v4-v6 VL imbalance tables of 3x3 and 4x4 are therefore wrong; the 2x2 values (16 VLs) are correct. v7 uses all VLs
  (`make_eval_csv.py` fixed in 71b66b3). Corrected 4x4 values at 1.0 x Lsat: DeFT_tm(rho*) 1.11-1.83 (v6 reported
  1.08-1.47), CI_qlLA 1.19-2.18 (v6 reported 1.11-1.12 on uniform; corrected uniform 1.20 and 1.33 with faults).
  `results_v7/report/summary.md` has the full corrected tables.
