# paper_data (round 28)

One CSV per table or figure. Written by `report_v28.py` and by `experiments_v28.py b_choose` (`tuning_v28.csv`) from the per-run CSVs of `results_v28_anchor/`
(the reused rows of Parts D and E from `results_v26_faults/fault_rate_runs.csv`; DeFT_P, the main row and the P = 0, T = 0 members of the tuning from
`results_v27_early/tune_runs.csv`); nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`.

**Effects** are percentages, 100 x (exp(mean log ratio) - 1). Part C: per seed the mean over the scenarios of ln(row / reference); the interval is the 95 % t
interval over the ten seeds. Parts D and E: per mask the mean over the two traffic patterns and the two seeds; the interval is over the 16 masks. THR = the
largest accepted throughput over the loads of the ladder (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet latency at
1.0 x Lsat of DeFT-P (cycles; negative effect = lower). Only the tests of the two primary families are adjusted (`../report/primary_C.csv`,
`../report/primary_D.csv`); everything else is descriptive.

| file | table or figure | rows |
|---|---|---|
| `early_best_effects.csv` | Part C, per size, row and scenario set (all six, hotspot alone, the other five): the effect against DeFT_P and against the main row (THR, LAT, P99) with the 95 % interval over the ten seeds, and the share of the main row's gain over DeFT_P that the row reaches (THR, LAT) with the smallest and the largest per-seed share | size x row x scenario set |
| `early_best_per_scenario.csv` | Part C, per size, scenario and row: THR, LAT and P99 (mean over the ten seeds) and the effects against DeFT_P and against the main row with their intervals | size x scenario x row |
| `early_best_faults.csv` | Part D, per size, rate and row: the effect against the main row, DeFT_P, the best DeFT variant (THR, LAT, P99), for both traffic patterns, each alone, and the masks with and without a chiplet left one functional VL (unit = mask; 95 % interval over the masks; `masks_behind` = masks in which the row is on the wrong side) | size x rate x row x reference x traffic x subset x metric |
| `early_best_faults_shares.csv` | Part D: the share of the main row's gain over DeFT_P that each early row reaches, per size, rate and traffic | size x rate x row x traffic x metric |
| `novlrep_faults.csv` | Part E: `LB_noVLrep` against the main row per size and rate (THR, LAT, P99; whether the interval is within the stated margin), the masks with a chiplet left one functional VL, and each traffic pattern | size x rate x subset x traffic x metric |
| `tuning_v28.csv` | Part B: the score of every configuration of the early family (B1), of `EB_best64` (B2) and of `EB_down_t` (B3), with its three terms and the source of its runs | size x configuration |
