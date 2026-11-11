# Sanity checks v24 (experiments_v24.py sanity)

## Hops per packet (uniform fault-free, seed 111, 1.0 x Lsat, pipe_all 2)

Head-flit forwards counted by `-deft_lb hop_stats 1` in the measured window (router-to-router and vertical hops; the ejection is not counted), divided by the packets
delivered in the window. DeFT_Dis takes the nearest VL at both ends; the CI variants take the LUT exit and bind the entry late, on minimal paths.

| size | rate | DeFT_Dis | CI_qlLA_X | CI_qlLA_O | CI_qlLA_X: hops offering more than one output (chiplet / interposer) | CI_qlLA_O |
|---|---|---|---|---|---|---|
| 2x2 | 0.0130 | 8.02 | 8.30 | 8.36 | 0.0 % / 30.3 % | 0.0 % / 30.2 % |
| 3x3 | 0.0100 | 11.24 | 11.62 | 11.63 | 0.0 % / 22.4 % | 0.0 % / 22.0 % |
| 4x4 | 0.0080 | 13.90 | 14.25 | 14.27 | 0.0 % / 17.6 % | 0.0 % / 17.4 % |

## Observation-only options

The reference rows DeFT_P and DeFT_B run with `-deft_lb count_vl 1` (VL counts for plain DEFT routing) and every DEFT_LB row with `-deft_lb hop_stats 1`. Same run
with and without the option (uniform fault-free, seed 111, 1.0 x Lsat): the `summary` block and the delay statistics must be identical.

| size | DeFT_P with / without count_vl | CI_qlLA_G with / without hop_stats |
|---|---|---|
| 2x2 | identical | identical |
| 3x3 | identical | identical |
| 4x4 | identical | identical |

## Largest flit rate of a vertical link

Per run, the largest number of packets any Down VL and any Up VL carried (head flits forwarded over the whole 10,000 simulated cycles), times 8 flits, per cycle. A link
carries one flit per two cycles, so the value must not exceed 0.5.

| file | runs with VL counts | largest Down VL rate (run) | largest Up VL rate (run) | above 0.5 |
|---|---|---|---|---|
| tune_runs.csv | 4480 | 0.4912 (hO_W1_B4_G1_D4-p2, 2x2-chiptrans, rate 0.016, seed 102) | 0.4848 (hO_W1_B0_G2_D4-p2, 2x2-chiptrans, rate 0.016, seed 101) | 0 |
| eval_runs.csv | 14850 | 0.4920 (CI_qlLA_G-p2, 2x2-chiptrans, rate 0.0185, seed 111) | 0.4800 (DeFT_B-p2, 2x2-chipperm, rate 0.006, seed 111) | 0 |

**Largest VL flit rate of the round: 0.4920 flits/cycle (at most 0.5).**
