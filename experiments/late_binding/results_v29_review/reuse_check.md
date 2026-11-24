# The reused rows of rounds 25, 26 and 28 are reproduced by the build of this round (experiments_v29.py a2_reuse)

Before a part pairs new rows with rows of an earlier round, runs of that round are made again with the `bin/noxim` of this round and the row definitions of
that round, and compared with the rows of its per-run file: every column of that file, as text.

## Round 25

Runs: the main row and DeFT_P (`experiments_v25.row_args`), uniform and movinghot traffic at 1.0 x Lsat, seeds 121 and 122. Compared with `results_v25_confirm/eval_runs.csv`.

| size | row | runs | identical |
|---|---|---|---|
| 2x2 | CI_heurLA_X_LF | 4 | 4 |
| 2x2 | DeFT_P | 4 | 4 |
| 3x3 | CI_heurLA_X_LF | 4 | 4 |
| 3x3 | DeFT_P | 4 | 4 |
| 4x4 | CI_heurLA_X_LF | 4 | 4 |
| 4x4 | DeFT_P | 4 | 4 |

**24 / 24 runs identical.**

## Round 26

Runs: the main row and DeFT_P on mask 1 of the rate 1/16 (hotspot traffic) and of the rate 4/16 (uniform traffic), at 1.0 x Lsat of the mask, seeds 151 and 152. Compared with `results_v26_faults/fault_rate_runs.csv`.

| size | row | runs | identical |
|---|---|---|---|
| 2x2 | CI_heurLA_X_LF | 4 | 4 |
| 2x2 | DeFT_P | 4 | 4 |
| 3x3 | CI_heurLA_X_LF | 4 | 4 |
| 3x3 | DeFT_P | 4 | 4 |
| 4x4 | CI_heurLA_X_LF | 4 | 4 |
| 4x4 | DeFT_P | 4 | 4 |

**24 / 24 runs identical.**

## Round 28

Runs: DeFT_P, the main row and the tuned early rows `EB_best`, `EB_best64` and `EB_down_t` (`experiments_v28_eval.row_args`), uniform and chiptrans traffic at 1.0 x Lsat, seeds 171 and 172. Compared with `results_v28_anchor/eval_runs.csv`.

| size | row | runs | identical |
|---|---|---|---|
| 2x2 | CI_heurLA_X_LF | 4 | 4 |
| 2x2 | DeFT_P | 4 | 4 |
| 2x2 | EB_best | 4 | 4 |
| 2x2 | EB_best64 | 4 | 4 |
| 2x2 | EB_down_t | 4 | 4 |
| 3x3 | CI_heurLA_X_LF | 4 | 4 |
| 3x3 | DeFT_P | 4 | 4 |
| 3x3 | EB_best | 4 | 4 |
| 3x3 | EB_best64 | 4 | 4 |
| 3x3 | EB_down_t | 4 | 4 |
| 4x4 | CI_heurLA_X_LF | 4 | 4 |
| 4x4 | DeFT_P | 4 | 4 |
| 4x4 | EB_best | 4 | 4 |
| 4x4 | EB_best64 | 4 | 4 |
| 4x4 | EB_down_t | 4 | 4 |

**60 / 60 runs identical.**

**Every reused row is reproduced: yes.**
