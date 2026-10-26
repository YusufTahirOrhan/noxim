# Pre-registration v11, addendum: mask count (committed before the evaluation starts)

* Rule 1 (LUT generation): all 45 per-mask LUTs (DeFT's rho* uniform model) took 5 s wall in total; the 4x4 estimate
  is far below 4 h (`lut_timing.md`).
* Rule 2 (run time): timing test of 432 runs, estimate **11.9 h** for the 10080 runs of 5 masks on one machine, below 16 h
  (`runtime_estimate.md`).
* **5 masks per (size, k)** (`mask_count.json`). The drain tests of all 8 methods on all 45 masks passed (360 / 360,
  `drain_summary.csv`). No evaluation run had been made when this was committed.
