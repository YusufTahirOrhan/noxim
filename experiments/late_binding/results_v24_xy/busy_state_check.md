# B3: `-deft_lb busy_state 1` without lookahead (experiments_v24.py busy)

CI_qlLA_G (the v23 odd-even variant, v10 parameters, DeFT-P VN options, `-traffic_rng 1`), uniform fault-free, pipe_all 0, no lookahead; five runs per size
(the loads 0.5, 1.0, 1.4, 2.0 and 2.4 x Lsat of the v23 ladder with seeds 1-5). Compared: the whole `summary` block and the whole `deft_lb` block of the
stats JSON except the field `busy_state` itself.

| size | rate | seed | accepted off / on | latency off / on | p99 off / on | all statistics identical |
|---|---|---|---|---|---|---|
| 2x2 | 0.0060 | 1 | 0.045936 / 0.045936 | 25.6423 / 25.6423 | 79 / 79 | yes |
| 2x2 | 0.0115 | 2 | 0.092539 / 0.092539 | 48.0291 / 48.0291 | 167 / 167 | yes |
| 2x2 | 0.0160 | 3 | 0.122080 / 0.122080 | 364.1010 / 364.1010 | 3019 / 3019 | yes |
| 2x2 | 0.0230 | 4 | 0.122271 / 0.122271 | 1636.1231 / 1636.1231 | 5681 / 5681 | yes |
| 2x2 | 0.0275 | 5 | 0.120527 / 0.120527 | 2185.2889 / 2185.2889 | 6283 / 6283 | yes |
| 4x4 | 0.0035 | 1 | 0.027637 / 0.027637 | 41.3639 / 41.3639 | 106 / 106 | yes |
| 4x4 | 0.0070 | 2 | 0.055812 / 0.055812 | 70.6704 / 70.6704 | 197 / 197 | yes |
| 4x4 | 0.0100 | 3 | 0.063593 / 0.063593 | 852.9127 / 852.9127 | 4514 / 4514 | yes |
| 4x4 | 0.0140 | 4 | 0.061637 / 0.061637 | 2188.7195 / 2188.7195 | 6908 / 6908 | yes |
| 4x4 | 0.0170 | 5 | 0.057504 / 0.057504 | 2973.3952 / 2973.3952 | 7296 / 7296 | yes |

**10 / 10 runs identical.**

Why they must be: with the head at the front of its input VC, the old test (`checkReservation` = RT_OUTVC_BUSY) and the new one (a reservation entry of the
output with that output VC that is not the head's own) differ only once the head itself holds an output; from then on the head keeps that output and the
result of the selection is not used. The two tests differ in effect only when the decision is computed for a head that is not in the router yet
(lookahead routing).
