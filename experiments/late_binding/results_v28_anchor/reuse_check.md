# Parts D and E: the reused rows are reproduced by the new build (experiments_v28.py d_reuse)

DeFT_P and the main row `CI_heurLA_X_LF`, with the row definitions of round 26 (`experiments_v25.row_args`, no option of this round), on masks 1 and 2 of
every rate (1/16, 2/16, 4/16, 8/16) and size: uniform and hotspot traffic, the four loads, seeds 151 and 152, run with the `bin/noxim` of this round.
Compared with the rows of `results_v26_faults/fault_rate_runs.csv`: every column of that file, as text. DeFT_B, DeFT_Dis and DeFT_Ran are taken
from that file without a run of their own, as in round 27.

| size | rate | row | runs | identical |
|---|---|---|---|---|
| 2x2 | 1/16 | CI_heurLA_X_LF | 32 | 32 |
| 2x2 | 1/16 | DeFT_P | 32 | 32 |
| 2x2 | 2/16 | CI_heurLA_X_LF | 32 | 32 |
| 2x2 | 2/16 | DeFT_P | 32 | 32 |
| 2x2 | 4/16 | CI_heurLA_X_LF | 32 | 32 |
| 2x2 | 4/16 | DeFT_P | 32 | 32 |
| 2x2 | 8/16 | CI_heurLA_X_LF | 32 | 32 |
| 2x2 | 8/16 | DeFT_P | 32 | 32 |
| 3x3 | 1/16 | CI_heurLA_X_LF | 32 | 32 |
| 3x3 | 1/16 | DeFT_P | 32 | 32 |
| 3x3 | 2/16 | CI_heurLA_X_LF | 32 | 32 |
| 3x3 | 2/16 | DeFT_P | 32 | 32 |
| 3x3 | 4/16 | CI_heurLA_X_LF | 32 | 32 |
| 3x3 | 4/16 | DeFT_P | 32 | 32 |
| 3x3 | 8/16 | CI_heurLA_X_LF | 32 | 32 |
| 3x3 | 8/16 | DeFT_P | 32 | 32 |
| 4x4 | 1/16 | CI_heurLA_X_LF | 32 | 32 |
| 4x4 | 1/16 | DeFT_P | 32 | 32 |
| 4x4 | 2/16 | CI_heurLA_X_LF | 32 | 32 |
| 4x4 | 2/16 | DeFT_P | 32 | 32 |
| 4x4 | 4/16 | CI_heurLA_X_LF | 32 | 32 |
| 4x4 | 4/16 | DeFT_P | 32 | 32 |
| 4x4 | 8/16 | CI_heurLA_X_LF | 32 | 32 |
| 4x4 | 8/16 | DeFT_P | 32 | 32 |

**768 / 768 runs identical.**
