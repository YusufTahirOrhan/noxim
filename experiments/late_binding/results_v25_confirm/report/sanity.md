# Sanity checks v25 Part B (experiments_v25.py sanity)

## Observation-only options

DeFT_P, DeFT_B and XY_SP run with `-deft_lb count_vl 1` (VL counts for plain routing) and every DEFT_LB row with `-deft_lb hop_stats 1`. The same run without the
option (seed 121, 1.0 x Lsat) must give the same accepted throughput, latency, p99 and received packets as the evaluation run.

| size | row | option removed | scenario | result |
|---|---|---|---|---|
| 2x2 | DeFT_P | count_vl | uniform | identical |
| 2x2 | XY_SP | count_vl | uniform | identical |
| 2x2 | CI_heurLA_X_LF | hop_stats | uniform | identical |
| 2x2 | CI_heurLA_O_LF | hop_stats | uniform | identical |
| 2x2 | DeFT_Dis | hop_stats | uniform+f | identical |
| 3x3 | DeFT_P | count_vl | uniform | identical |
| 3x3 | XY_SP | count_vl | uniform | identical |
| 3x3 | CI_heurLA_X_LF | hop_stats | uniform | identical |
| 3x3 | CI_heurLA_O_LF | hop_stats | uniform | identical |
| 3x3 | DeFT_Dis | hop_stats | uniform+f | identical |
| 4x4 | DeFT_P | count_vl | uniform | identical |
| 4x4 | XY_SP | count_vl | uniform | identical |
| 4x4 | CI_heurLA_X_LF | hop_stats | uniform | identical |
| 4x4 | CI_heurLA_O_LF | hop_stats | uniform | identical |
| 4x4 | DeFT_Dis | hop_stats | uniform+f | identical |

**All identical: yes.**

## Hops per packet (uniform fault-free, seed 121, 1.0 x Lsat, pipe_all 2)

Head-flit forwards counted by `hop_stats` in the measured window, divided by the packets delivered in the window; and the share of hops that offer more than one output.

| size | CI_heurLA_X_LF | CI_heurLA_O_LF | CI_heurLA_X_LF: decision hops (chiplet / interposer) | CI_heurLA_O_LF |
|---|---|---|---|---|
| 2x2 | 8.40 | 8.44 | 0.0 % / 29.8 % | 0.0 % / 29.9 % |
| 3x3 | 11.67 | 11.75 | 0.0 % / 21.4 % | 0.0 % / 21.3 % |
| 4x4 | 14.41 | 14.44 | 0.0 % / 16.8 % | 0.0 % / 16.7 % |

## Largest flit rate of a vertical link

Per run, the largest number of packets any Down VL and any Up VL carried (head flits forwarded over the whole 10,000 simulated cycles), times 8 flits, per cycle. A link
carries one flit per two cycles, so the value must not exceed 0.5.

| file | runs with VL counts | largest Down VL rate (run) | largest Up VL rate (run) | above 0.5 |
|---|---|---|---|---|
| eval_runs.csv | 18900 | 0.4920 (RC-p2, 2x2-chiptrans, rate 0.023, seed 121) | 0.4976 (XY_SP-p2, 3x3-chipperm, rate 0.009, seed 128) | 0 |

**Largest VL flit rate: 0.4976 flits/cycle (at most 0.5).**
