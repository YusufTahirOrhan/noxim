# paper_data (round 27)

One CSV per table or figure. Written by `report_v27.py` from the per-run CSVs of `results_v27_early/` (Part D from `results_v25_confirm/eval_runs.csv`, the reused rows
of Part E from `results_v26_faults/fault_rate_runs.csv`); nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`.

**Effects** are percentages, 100 x (exp(mean log ratio) - 1). Part C and Part D: per seed the mean over the six scenarios of ln(row / reference); the interval is the
95 % t interval over the ten seeds. Part E: per mask the mean over the two traffic patterns and the two seeds; the interval is over the 16 masks. THR = the largest
accepted throughput over the loads of the ladder (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet latency at 1.0 x Lsat of
DeFT-P (cycles; negative effect = lower). Only the 18 tests of the primary family are adjusted (`../report/primary.csv`); everything else is descriptive.

| file | table or figure | rows |
|---|---|---|
| `early_late_effects.csv` | Part C, per size and row: the effect against DeFT_P and against the main row (THR, LAT, P99) with the 95 % interval over the ten seeds, and the share of the main row's gain over DeFT_P that the row reaches (THR, LAT) with the smallest and the largest per-seed share | size x row |
| `early_late_per_scenario.csv` | Part C, per size, scenario and row: THR, LAT and P99 (mean over the ten seeds) and the effects against DeFT_P and against the main row with their intervals | size x scenario x row |
| `early_late_faults.csv` | Part E, per size: each early row and the main row against the main row, DeFT_P and the best DeFT variant under random VL faults at the rate 4/16 (unit = mask; 95 % interval over the 16 masks; `masks_behind` = masks in which the row is on the wrong side) | size x row x reference x metric |
| `latency_by_load_v25.csv` | Part D, from the runs of round 25: the mean latency of the main row and of the five references at each of the nine loads, per scenario and over the six scenarios (`scenario` = all), the best reference of the cell, the effect of the main row against it, and the accepted share of the offered load | size x load x scenario |
| `tuning_v27.csv` | Part B: the score of every `oracle_beta` value of `EB_vl`, `EB_route` and `EB_vl64` and of the main row on the tuning seeds, with its three terms | size x row x value |
