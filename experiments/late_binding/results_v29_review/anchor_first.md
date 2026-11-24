# A2: `EB_first` with `lut_bias 1e9` against DeFT_P (experiments_v29.py a2_fanchor)

Is DeFT_P the member of the family of `EB_first` at `lut_bias` towards infinity? `EB_first_inf` = the main row with `-deft_lb entry_commit first` and
`lut_bias 1e9` (and `-deft_lb entry_stats 1`, which only counts). Against `DeFT_P`. The runs of the anchor gate of round 28: the six fault-free
scenarios at 1.0 x Lsat with seed 101, and uniform traffic on mask 1 of rate 4/16 of round 26 at 1.0 x Lsat of that mask with seed 151; pipe_all 2,
`-traffic_rng 1`. Compared: every field of the `summary` block except the three energy fields, and the delay statistics, the packets per VL and the
dead-end events of the `deft_lb` block. `_ts`: the same row with the diagnostic `-deft_lb tie_stream 1`, with which the two tie-breaks of the commit
(the output, then the candidate) draw from a stream of their own instead of `rand()`, from which the routers' crossbar arbitration draws. Off packets:
the measured Up moves on a VL that is not DeFT-P's entry VL (`entry_stats`); 0 means every packet took DeFT-P's entry VL.

## `EB_first_inf`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | heads bound | identical |
|---|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104422 | 82.624 / 84.222 | 375 / 450 | 0 | 5120 | **no** |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128643 | 67.032 / 65.694 | 250 / 241 | 0 | 5031 | **no** |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058385 | 108.749 / 120.529 | 873 / 1208 | 0 | 2828 | **no** |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092727 | 142.799 / 131.767 | 559 / 458 | 0 | 5930 | **no** |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092566 | 84.315 / 83.917 | 469 / 441 | 0 | 2963 | **no** |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067758 | 109.502 / 118.025 | 697 / 683 | 0 | 3305 | **no** |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066795 | 84.726 / 84.667 | 432 / 466 | 0 | 3259 | **no** |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080985 | 139.224 / 138.617 | 652 / 582 | 0 | 10457 | **no** |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.117109 | 89.140 / 85.600 | 383 / 361 | 0 | 9975 | **no** |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024271 | 98.403 / 97.307 | 690 / 702 | 0 | 3139 | **no** |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060744 | 125.982 / 124.868 | 510 / 488 | 0 | 7830 | **no** |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044683 | 80.075 / 82.760 | 381 / 438 | 0 | 4245 | **no** |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032897 | 119.597 / 120.424 | 743 / 801 | 0 | 4228 | **no** |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052252 | 133.863 / 133.804 | 1059 / 988 | 0 | 6742 | **no** |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064547 | 147.356 / 140.670 | 749 / 587 | 0 | 15505 | **no** |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100873 | 122.816 / 124.985 | 739 / 726 | 0 | 15552 | **no** |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012434 | 98.210 / 95.245 | 771 / 658 | 0 | 3004 | **no** |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048237 | 204.787 / 208.151 | 881 / 832 | 0 | 12349 | **no** |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033598 | 163.654 / 165.784 | 1099 / 1238 | 0 | 6421 | **no** |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021773 | 188.903 / 195.188 | 1146 / 1126 | 0 | 5253 | **no** |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.028277 | 277.263 / 270.623 | 3086 / 3132 | 0 | 5906 | **no** |

**0 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR +0.08 %, LAT +0.21 %, P99 -0.71 %.

## `EB_first_inf_ts`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | heads bound | identical |
|---|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104537 | 82.624 / 82.624 | 375 / 375 | 0 | 5121 | yes |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128441 | 67.032 / 67.032 | 250 / 250 | 0 | 5027 | yes |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058402 | 108.749 / 108.749 | 873 / 873 | 0 | 2829 | yes |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 142.799 / 142.799 | 559 / 559 | 0 | 5919 | yes |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 84.315 / 84.315 | 469 / 469 | 0 | 2965 | yes |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067893 | 109.502 / 109.502 | 697 / 697 | 0 | 3309 | yes |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066699 | 84.726 / 84.726 | 432 / 432 | 0 | 3260 | yes |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080813 | 139.224 / 139.224 | 652 / 652 | 0 | 10433 | yes |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.116919 | 89.140 / 89.140 | 383 / 383 | 0 | 9952 | yes |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024292 | 98.403 / 98.403 | 690 / 690 | 0 | 3140 | yes |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060681 | 125.982 / 125.982 | 510 / 510 | 0 | 7828 | yes |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044760 | 80.075 / 80.075 | 381 / 381 | 0 | 4255 | yes |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032838 | 119.597 / 119.597 | 743 / 743 | 0 | 4223 | yes |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052030 | 133.863 / 133.863 | 1059 / 1059 | 0 | 6705 | yes |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064263 | 147.356 / 147.356 | 749 / 749 | 0 | 15455 | yes |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100645 | 122.816 / 122.816 | 739 / 739 | 0 | 15526 | yes |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012449 | 98.210 / 98.210 | 771 / 771 | 0 | 3007 | yes |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048234 | 204.787 / 204.787 | 881 / 881 | 0 | 12352 | yes |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033656 | 163.654 / 163.654 | 1099 / 1099 | 0 | 6439 | yes |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021762 | 188.903 / 188.903 | 1146 / 1146 | 0 | 5251 | yes |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.028176 | 277.263 / 277.263 | 3086 / 3086 | 0 | 5886 | yes |

**21 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR +0.00 %, LAT +0.00 %, P99 +0.00 %.

* `EB_first_inf` is not byte-identical to DeFT_P, but every packet takes DeFT-P's entry VL, and with its tie-breaks on a stream of their own (`EB_first_inf_ts`) it is identical in every run. So the only difference is the random stream: the two draws of a commit shift every later draw of the crossbar arbitration (as for the anchors of round 28, `results_v28_anchor/anchor.md`). With `lut_bias` towards infinity the row is DeFT_P's routing with another arbitration sequence.

Hops of the anchor runs at which a head that has left its commit router is offered more than one output (must be 0): 0. Largest number of commits of one
head (must be at most 1): 1.
