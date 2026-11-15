# paper_data (round 26)

One CSV per table or figure. Written by `report_v26.py` from the per-run CSVs of `results_v26_faults/` (`reachability_v26.csv` is a copy of the file `reach_v26.py`
writes); nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`.

**Effects** are percentages, 100 x (exp(mean over the masks of V_m) - 1), V_m = the mean over the two traffic patterns and the two seeds of
ln(metric of the row / metric of the reference), paired by seed; `ci_low`, `ci_high` are the 95 % t interval over the masks of a (size, rate), transformed the same way;
`p` is the two-sided one-sample t test over the masks (unadjusted; `primary_p_holm` is adjusted by Holm over the tests of the primary family, `../report/primary.csv`).
THR = the largest accepted throughput over the four loads (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet latency at 1.0 x Lsat of
DeFT-P on the mask (cycles; negative effect = lower). `reference` is a reference row, the main row (for the second row), or `best reference` (per mask, traffic pattern and
metric: the reference row with the best mean over the two seeds).

| file | table or figure | rows |
|---|---|---|
| `fault_rate_effects.csv` | Part B, per size and fault rate: each frozen row against the best reference and against each reference row (the second row also against the main row). Next to the effect: the distribution of the per-mask effects (minimum, quartiles, maximum) and the number of masks on the wrong side of 0. `primary_p_holm`, `primary_verdict` are filled on the rows of the primary family | size x rate x row x reference x metric |
| `fault_rate_per_mask.csv` | Part B, per mask and traffic pattern: the mask, its faults per chiplet (chiplet 0 first), Lsat of DeFT-P on the mask, the best reference in THR and in LAT, and THR, LAT and P99 of every row (mean over the two seeds) | size x rate x mask x traffic |
| `formal_summary.csv` | Part A: the model check per size and set of masks: masks, relations, checks, passes, the failures of each of the four checks, the longest path in hops; the last row is the second-half test of the argument for set 2 (`checks` = comparisons, `passes` = comparisons in which the subset relation holds) | size x set |
| `reachability_v26.csv` | B5: the share of the inter-chiplet pairs (`*_inter`) and of all source-destination pairs (`*_all`) that MTR and RC can deliver, per size and fault rate: mean, worst and best mask of the random masks and of the 16 masks of Part B; the number of masks on which every pair is delivered | size x rate x mask set x method |

The unit of Part B is the mask: the two seeds and the two traffic patterns are averaged within a mask, and every interval is over the masks of a (size, rate).
The model check and the reachability analysis are exact (no interval).
