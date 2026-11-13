# paper_data (round 25)

One CSV per table or figure. Written by `report_v25.py` (evaluation) and `report_v25_hw.py` (hardware) from the per-run CSVs of
`results_v25_confirm/`; nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`, `../PREREGISTRATION_addendum.md`.

**Effects** are percentages, 100 x (exp(mean over seeds of R_s) - 1), R_s = the mean over the scenarios (or masks) of
ln(metric of the row / metric of the reference) for seed s; `ci_low`, `ci_high` are the 95 % t interval over the seeds,
transformed the same way; `p` is the two-sided one-sample t test (unadjusted unless the column says Holm). THR = the largest
accepted throughput over the loads (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet
latency at 1.0 x Lsat of DeFT-P (cycles; negative effect = lower); LAT02, LAT05 = mean latency at 0.2 and 0.5 x Lsat.
`reference` is a reference row or `best baseline` (per size, scenario and metric: the reference row available on the scenario
with the best mean over the seeds).

| file | table or figure | rows |
|---|---|---|
| `effects_per_size.csv` | Part B, per size: each frozen row against the best baseline and against each reference row, over the scenarios both ran on. `primary_p_holm`, `primary_verdict` are filled on the 18 rows of the primary family | size x row x reference x metric |
| `effects_per_scenario.csv` | Part B, per scenario: each frozen row against the best baseline (`best_baseline` names it) and against each reference row; `seen_by_tuning` marks the five scenarios round 24 tuned on | size x row x scenario x reference x metric |
| `absolute_values.csv` | Part B: mean and 95 % interval over the ten seeds of THR, LAT, P99, LAT02, LAT05 for every row and scenario | size x row x scenario |
| `latency_load_<size>_<scenario>.csv` | latency against offered load for every row (2x2 and 4x4; uniform, hotspot, chipperm, chiptrans, uniform with one faulty VL per chiplet = `uniform_f`): mean and 95 % interval over the seeds of the mean latency, the p99 and the accepted throughput at each of the nine loads | row x load |
| `fault_sweep.csv` | Part C: THR, LAT, P99 and LAT at 0.5 x Lsat against k (faulty VLs per chiplet): absolute mean and interval over the five seeds (mean over the three masks), and the effect against the best reference row of each mask | size x k x row |
| `addendum_effects.csv` | the addendum row `CI_heurLA_X_LF1` (main row with one residual cycle): its family of nine tests (`p_holm`, `verdict`), and its effects against the main row, the DLY row, each reference row and per scenario | test |
| `addendum_latency_load.csv` | the addendum row's latency, p99 and accepted throughput against the offered load, in the columns of the `latency_load_<size>_<scenario>.csv` files (all three sizes and eight scenarios in one file) | size x scenario x load |
| `apps.csv` | Part D: mean latency and completion time relative to DeFT_P per trace (protocol `single`) and per pair and compression `s` (protocol `pair`), fault-free (`0x0000`) and with one faulty VL per chiplet (`0x1111`); geometric means; the offered load of each trace | workload x mask x row |
| `pipe0_effects.csv` | Part E (one-cycle router model): each row against the best baseline, per size and per scenario | size x row x scenarios x metric |
| `hw_area.csv` | Part F: area of every router design, type, size and cut configuration in the three syntheses (hierarchy kept, router core kept, flattened), absolute and relative to DeFT | design x type x size x cuts |
| `hw_system_area.csv` | Part F: average router area of a whole system relative to DeFT, and the total of all routers (mm^2, hierarchy kept) | design x size x cuts |
| `hw_timing.csv` | Part F: stages of the decision path per design, cut configuration, router type and size; whether every stage fits 1 ns and T_ref | design x cuts x type x size |
| `hw_paths.csv` | Part F: the other paths (route of a hop with one offered output, VC-allocation stage with the fallback, link stage, whole router against T_ref) | design x cuts x type x size |

No file has intervals for the hardware numbers (one synthesis per design) or for the traces (the three seeds of a trace run
only drive VC choices and tie breaks; the values are geometric means over them).
