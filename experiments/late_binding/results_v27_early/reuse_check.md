# Part E: the reused rows are reproduced by the new build (experiments_v27.py e_reuse)

DeFT_P and the main row `CI_heurLA_X_LF`, with the row definitions of round 26 (`experiments_v25.row_args`, no option of this round), on masks 1 and 2 of rate
4/16 of every size: uniform and hotspot traffic, the four loads, seeds 151 and 152, run with the `bin/noxim` of this round. Compared with the rows of
`results_v26_faults/fault_rate_runs.csv`: every column of that file, as text (accepted, latency, p99, injected, received, dead ends, the VL counts and the hop and
lookahead counters).

| size | row | runs |
|---|---|---|
| 2x2 | CI_heurLA_X_LF-p2 | 32 |
| 2x2 | DeFT_P-p2 | 32 |
| 3x3 | CI_heurLA_X_LF-p2 | 32 |
| 3x3 | DeFT_P-p2 | 32 |
| 4x4 | CI_heurLA_X_LF-p2 | 32 |
| 4x4 | DeFT_P-p2 | 32 |

**192 / 192 runs identical.**
