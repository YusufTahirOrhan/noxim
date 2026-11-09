# v24 reproduction of the review's probe numbers (experiments_v24.py repro, repro2, b5, reprodoc)

The probes were single runs on a scratch build of 8d84634: 4x4 unless stated, seed 91, DeFT-P VN options, `-traffic_rng 1`, the v10 selection
parameters, v23 LUTs and traffic tables, `-sim 10000 -warmup 2000`. Where a value differs, both are listed; the measurement of this round is the one used.

## A0: existing options only (binary noxim_8d84634, md5 b81b5d8b1fefc63276c1e80cffeaa01d)

Method = key of `experiments_v23.methods(size)`, plus the extra arguments, plus the pipe depth and `-traffic_rng 1`.

| # | size | method + extra arguments | pipe_all | scenario (mask) | rate | received: probe / this round | latency: probe / this round | result |
|---|---|---|---|---|---|---|---|---|
| 1 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | chipperm (0x0) | 0.0050 | 10469 / 10469 | 98.7693189416 / 98.7693189416 | identical |
| 2 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | chipperm (0x0) | 0.0070 | 13434 / 13434 | 456.9803483698 / 456.9803483698 | identical |
| 3 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | uniform (0x0) | 0.0100 | 20549 / 20549 | 185.3428877318 / 185.3428877318 | identical |
| 4 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | uniform (0x1111111111111111) | 0.0075 | 15317 / 15317 | 215.4711105308 / 215.4711105308 | identical |
| 5 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | hotspot (0x0) | 0.0022 | 4567 / 4567 | 74.2583753011 / 74.2583753011 | identical |
| 6 | 4x4 | DeFT_Dis `-deft_lb ipos_tm OE` | 0 | chipperm (0x0) | 0.0050 | 4397 / 4397 | 1833.8910620878 / 1833.8910620878 | identical |
| 7 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY -deft_lb decision_delay 1` | 2 | uniform (0x0) | 0.0080 | 16575 / 16575 | 95.7701357466 / 95.7701357466 | identical |
| 8 | 4x4 | CI_qlLA_G `-deft_lb ipos_tm XY -deft_lb lookahead_route 1 -deft_lb decision_delay 1` | 2 | uniform (0x0) | 0.0080 | 16569 / 16569 | 101.4833122095 / 101.4833122095 | identical |
| 9 | 3x3 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | chipperm (0x0) | 0.0100 | 11657 / 11657 | 108.3540362014 / 108.3540362014 | identical |
| 10 | 2x2 | CI_qlLA_G `-deft_lb ipos_tm XY` | 0 | uniform (0x0000) | 0.0160 | 8162 / 8162 | 247.8145062485 / 247.8145062485 | identical |

**10 / 10 rows identical** (received packets equal and latency equal to the 10 printed decimals).

## B4: probe values that need the options of this round (binary md5 2b58bee06d53c11c4dba50319a7a9530)

The probe code was throw-away and may differ from this round's implementation in tie-breaking; the target is agreement within 3 %.

| variant | pipe_all | scenario, rate | accepted / latency: probe | this round | deviation (accepted, latency) | within 3 % |
|---|---|---|---|---|---|---|
| CI_qlLA_G `ipos_tm XY lut_bias 4` | 0 | chipperm 0.0040 | 0.0326 / 70.8 | 0.0326 / 70.8 | +0.1 %, +0.0 % | yes |
| CI_qlLA_G `ipos_tm XY hop_weight_ipos 1.0` | 0 | chipperm 0.0070 | 0.0532 / 378.9 | 0.0532 / 378.9 | -0.1 %, +0.0 % | yes |
| CI_qlLA_G `ipos_tm XY lookahead_route 1 lookahead_fallback 1 decision_delay 1` | 2 | uniform 0.0080 | 0.0647 / 94.4 | 0.0647 / 94.4 | -0.0 %, -0.0 % | yes |
| CI_qlLA_G `ipos_tm XY lookahead_route 1 lookahead_fallback 1 decision_delay 1` | 2 | uniform 0.0110 | 0.0831 / 467.5 | 0.0831 / 467.5 | +0.0 %, -0.0 % | yes |
| CI_qlLA_G `ipos_tm O1` | 0 | uniform 0.0100 | 0.0793 / 253.2 | 0.0793 / 253.2 | +0.0 %, -0.0 % | yes |
| CI_qlLA_G `ipos_tm O1` | 0 | chipperm 0.0070 | 0.0479 / 735.3 | 0.0479 / 735.3 | -0.1 %, -0.0 % | yes |

**6 / 6 rows within 3 % on both values.**

## B5: the new pattern `chiptrans` (4x4, seed 91, pipe_all 0, rate 0.0060; binary md5 2b58bee06d53c11c4dba50319a7a9530)

| method | accepted / latency: probe | this round | deviation (accepted, latency) |
|---|---|---|---|
| DeFT_P | 0.0421 / 514 | 0.0421 / 514.2 | +0.1 %, +0.0 % |
| MTR | 0.0420 / 465 | 0.0420 / 464.7 | -0.0 %, -0.1 % |
| CI_qlLA_G | 0.0485 / 66 | 0.0485 / 66.1 | -0.0 %, +0.2 % |
| CI_qlLA_G `ipos_tm XY` | 0.0431 / 461 | 0.0431 / 461.3 | -0.1 %, +0.1 % |
| CI_qlLA_G `ipos_tm O1` | 0.0486 / 49 | 0.0486 / 49.4 | -0.1 %, +0.8 % |
| DeFT_Dis `ipos_tm O1` | 0.0485 / 52 | 0.0485 / 51.6 | -0.0 %, -0.8 % |
