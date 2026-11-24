# A2: the buffer options (experiments_v29.py a2_bufid)

## 1. `-buffer_ipos 4` with `-buffer 4` is the option absent

DeFT_P, MTR, RC and the main row `CI_heurLA_X_LF` on uniform traffic at 1.0 x Lsat of DeFT_P, seed 121, pipe_all 2, `-traffic_rng 1`: the run of the row as round 25
defines it, and the same run with `-buffer_ipos 4 -buffer 4`. Compared: the whole statistics file, byte by byte.

| size | row | rate | accepted | latency | byte-identical |
|---|---|---|---|---|---|
| 2x2 | DeFT_P | 0.0130 | 0.101652 | 76.6746 | yes |
| 2x2 | MTR | 0.0130 | 0.101418 | 63.8672 | yes |
| 2x2 | RC | 0.0130 | 0.101584 | 63.1872 | yes |
| 2x2 | CI_heurLA_X_LF | 0.0130 | 0.101541 | 60.9818 | yes |
| 3x3 | DeFT_P | 0.0100 | 0.079580 | 156.1276 | yes |
| 3x3 | MTR | 0.0100 | 0.079793 | 97.0852 | yes |
| 3x3 | RC | 0.0100 | 0.079799 | 98.0898 | yes |
| 3x3 | CI_heurLA_X_LF | 0.0100 | 0.080115 | 81.5815 | yes |
| 4x4 | DeFT_P | 0.0080 | 0.063853 | 138.6602 | yes |
| 4x4 | MTR | 0.0080 | 0.064209 | 102.4771 | yes |
| 4x4 | RC | 0.0080 | 0.064080 | 104.9418 | yes |
| 4x4 | CI_heurLA_X_LF | 0.0080 | 0.064372 | 92.1088 | yes |

**12 / 12 byte-identical.**

## 2. The depths are the real ones

DeFT_P and the main row on uniform traffic at 2.4 x Lsat of DeFT_P (seed 121) with the diagnostic `-deft_lb buffer_stats 1`, which records at every flit
written into an input buffer the capacity of that buffer and its fill after the write, per layer (chiplet routers, interposer routers; the smallest and
the largest capacity seen, and the largest fill). The capacity must be the one asked for on every buffer that received a flit, and at this load the
largest fill must reach it and cannot pass it. `-buffer 6 -buffer_ipos 3` is a fourth case, to show that the interposer depth can also be the smaller one.

| size | row | options | asked: chiplet / interposer | capacity seen: chiplet | interposer | largest fill: chiplet | interposer | as asked |
|---|---|---|---|---|---|---|---|---|
| 2x2 | DeFT_P | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 2x2 | DeFT_P | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 2x2 | DeFT_P | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 2x2 | DeFT_P | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |
| 2x2 | CI_heurLA_X_LF | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 2x2 | CI_heurLA_X_LF | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 2x2 | CI_heurLA_X_LF | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 2x2 | CI_heurLA_X_LF | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |
| 3x3 | DeFT_P | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 3x3 | DeFT_P | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 3x3 | DeFT_P | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 3x3 | DeFT_P | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |
| 3x3 | CI_heurLA_X_LF | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 3x3 | CI_heurLA_X_LF | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 3x3 | CI_heurLA_X_LF | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 3x3 | CI_heurLA_X_LF | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |
| 4x4 | DeFT_P | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 4x4 | DeFT_P | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 4x4 | DeFT_P | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 4x4 | DeFT_P | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |
| 4x4 | CI_heurLA_X_LF | `-buffer 5` | 5 / 5 | [5, 5] | [5, 5] | 5 | 5 | yes |
| 4x4 | CI_heurLA_X_LF | `-buffer 6` | 6 / 6 | [6, 6] | [6, 6] | 6 | 6 | yes |
| 4x4 | CI_heurLA_X_LF | `-buffer_ipos 7` | 4 / 7 | [4, 4] | [7, 7] | 4 | 7 | yes |
| 4x4 | CI_heurLA_X_LF | `-buffer 6 -buffer_ipos 3` | 6 / 3 | [6, 6] | [3, 3] | 6 | 3 | yes |

**24 / 24 as asked.**

## 3. `buffer_stats` reads only

The runs of check 2 with `-buffer 6`, with and without the diagnostic. Compared: the whole `summary` block and every field of `deft_lb` except those of the diagnostic.

| size | row | accepted without / with | latency without / with | identical |
|---|---|---|---|---|
| 2x2 | DeFT_P | 0.127311 / 0.127311 | 2775.4478 / 2775.4478 | yes |
| 2x2 | CI_heurLA_X_LF | 0.138016 / 0.138016 | 2520.3270 / 2520.3270 | yes |
| 3x3 | DeFT_P | 0.093320 / 0.093320 | 2904.3283 / 2904.3283 | yes |
| 3x3 | CI_heurLA_X_LF | 0.108238 / 0.108238 | 2431.8052 / 2431.8052 | yes |
| 4x4 | DeFT_P | 0.074295 / 0.074295 | 2778.3029 / 2778.3029 | yes |
| 4x4 | CI_heurLA_X_LF | 0.089420 / 0.089420 | 2230.0275 / 2230.0275 | yes |

**6 / 6 identical.**

**All checks of the buffer options pass: yes.**
