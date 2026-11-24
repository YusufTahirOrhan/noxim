# Run-time estimate v29, Parts B to G (experiments_v29.py t_timing)

Timing runs (runs of the designs, kept; nothing of their results was looked at), 12 processes, one set after the other, no other job of this round next to a
set; what else ran on the PC at that time is in `DECISIONS.md`. The estimate is taken as measured (`PREREGISTRATION.md`, "Time rule"). A part is estimated with
the seconds per run of the set of its kind and size: Parts B2, C1, C2, D1, E1 and F (evaluation and tuning runs) with the ladder runs, C3 with the fault runs.
The tuning runs of Part F are counted at their grids (280 and 480 runs per tuning size, no extension); Part G at its limit of 3 h.

| set | size | timing runs | wall | per run |
|---|---|---|---|---|
| held-out scenarios (Part B1), seed 181, the nine loads | 2x2 | 189 (0 missing) | 209 s | 1.11 s |
| ladder runs on the scenarios of round 25 (the references at depth 6), seeds 121 and 122, the 2nd, 5th and 9th load | 2x2 | 144 (0 missing) | 194 s | 1.34 s |
| fault runs (C3), seed 151, the 1st and 4th load, masks 1-4 of both rates | 2x2 | 64 (0 missing) | 79 s | 1.23 s |
| held-out scenarios (Part B1), seed 181, the nine loads | 3x3 | 162 (0 missing) | 512 s | 3.16 s |
| ladder runs on the scenarios of round 25 (the references at depth 6), seeds 121 and 122, the 2nd, 5th and 9th load | 3x3 | 144 (0 missing) | 654 s | 4.54 s |
| fault runs (C3), seed 151, the 1st and 4th load, masks 1-4 of both rates | 3x3 | 64 (0 missing) | 290 s | 4.53 s |
| held-out scenarios (Part B1), seed 181, the nine loads | 4x4 | 162 (0 missing) | 1121 s | 6.92 s |
| ladder runs on the scenarios of round 25 (the references at depth 6), seeds 121 and 122, the 2nd, 5th and 9th load | 4x4 | 144 (0 missing) | 1369 s | 9.51 s |
| fault runs (C3), seed 151, the 1st and 4th load, masks 1-4 of both rates | 4x4 | 64 (0 missing) | 577 s | 9.02 s |
| the set-up of the DeFT paper (D2), seed 191, both pipe depths | 2x2 | 360 (0 missing) | 312 s | 0.87 s |

| part | runs | estimate | after the drops: runs | estimate |
|---|---|---|---|---|
| B1 | 5130 | 5.1 h | 5130 | 5.1 h |
| B2 | 540 | 0.2 h | 540 | 0.2 h |
| C1 | 14580 | 20.8 h | 14580 | 20.8 h |
| C2 | 2880 | 4.1 h | 2880 | 4.1 h |
| C3 | 3072 | 4.2 h | 3072 | 4.2 h |
| D1 | 3240 | 4.6 h | 3240 | 4.6 h |
| D2 | 1800 | 0.4 h | 1800 | 0.4 h |
| E1 | 1620 | 2.3 h | 1620 | 2.3 h |
| F1 | 2180 | 3.2 h | 2180 | 3.2 h |
| F2 | 4200 | 6.1 h | - | 0.0 h |
| G | - | 3.0 h | - | 0.0 h |

Together **54.0 h**. Rule (pre-registered): above 48 h in total drop, in this order: Part G; Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation); the rate 1/16 of C3; Part C2; D1 on 3x3 and 4x4; `LB_d6`; seeds 126-130 of the rows at depth 5.

**Dropped: Part G, Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation).** Estimate of what is run: 44.9 h.
