# paper_data (round 29)

One CSV per table or figure. Written by `report_v29.py` and `report_v29_hw.py` from the per-run CSVs of `results_v29_review/` and of the rounds whose rows are
reused (`results_v25_confirm/eval_runs.csv`, `results_v26_faults/fault_rate_runs.csv`, `results_v28_anchor/eval_runs.csv`; `../reuse_check.md`); nothing here is
edited by hand. Definitions: `../PREREGISTRATION.md`.

**Effects** are percentages, 100 x (exp(mean log ratio) - 1): per seed the mean over the scenarios of ln(row / reference), with the 95 % t interval over the seeds
(Part C3: per mask the mean over the two traffic patterns and the two seeds, the interval over the 16 masks). THR = the largest accepted throughput over the loads
of the ladder (flits/node/cycle; positive = higher); LAT, P99 = mean and 99th-percentile packet latency at 1.0 x Lsat of DeFT-P with 4-flit buffers (cycles;
negative = lower). Only the two primary families are adjusted (`../report/primary_B.csv`, `../report/primary_C.csv`); everything else is descriptive.

| file | table or figure | rows |
|---|---|---|
| `heldout_effects.csv` | Part B, the three scenarios that no round had run (seeds 181-190): the main row against DeFT_P, the best of the five references, the best of DeFT_P and DeFT_B, the best of MTR and RC and XY_SP; per scenario and over the three; the primary family with its Holm-adjusted p and verdict; and the five scenarios that the tuning never saw (with localized and movinghot of round 25) as the mean of the five per-scenario effects | size x scenario x comparison x metric |
| `lb_b0.csv` | Part B: `LB_b0` (the main row with `lut_bias 0`) on 2x2 against the main row and against the best reference, and the main row against the best reference, on the three new scenarios and on the scenarios of round 25 (all six, the four of the tuning, the other two, each one) | scenario set x row x reference x metric |
| `hw_variants.csv` | Parts E2 and E4 (`report_v29_hw.py`): DeFT, the main row and its two RTL variants: system area relative to DeFT in the three forms, the cut configuration needed at T_ref with its margin, the delay left for an interposer link in the link cycle, the report inputs read, and on 4x4 the power of the average router with each activity | design x size |
