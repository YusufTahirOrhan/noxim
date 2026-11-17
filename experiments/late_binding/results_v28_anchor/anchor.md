# A2: the two anchors against DeFT_P (experiments_v28.py a2_anchor)

Is DeFT_P a member of the two early families? `EB_inf` = EBf(route, 1, 1, infinity): `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle`
`-deft_lb oracle_scope route -deft_lb oracle_pending 1 -deft_lb oracle_beta 1 -deft_lb oracle_bias 1e9` with XY in both layers; `EB_down_inf` =
`EB_down` of round 27 (the main row with `entry_commit down`) with `lut_bias 1e9`. Both with DeFT-P's VN options and `-deft_lb entry_stats 1`
(it only counts). Against `DeFT_P` (`-routing DEFT -deft_lut_entry dst` with the same VN options). Runs: the six fault-free scenarios at 1.0 x Lsat
with seed 101, and uniform traffic on mask 1 of rate 4/16 of round 26 at 1.0 x Lsat of that mask with seed 151; pipe_all 2, `-traffic_rng 1`.
Compared: every field of the `summary` block except the three energy fields, and the delay statistics, the packets per VL and the dead-end
events of the `deft_lb` block. `_ts`: the same row with the diagnostic `-deft_lb tie_stream 1`, with which the tie-breaks of the injection-time
choice and of the commit draw from a stream of their own instead of `rand()`, the stream the routers' crossbar arbitration draws from
(`Router.cpp`, `rand() % reservations.size()`). Off packets: the share of the measured Up moves on a VL that is not DeFT-P's entry VL
(`entry_stats`); 0 means every packet took DeFT-P's entry VL.

## `EB_inf`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | identical |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104506 | 82.624 / 82.848 | 375 / 386 | 0 | **no** |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128584 | 67.032 / 66.119 | 250 / 240 | 0 | **no** |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058736 | 108.749 / 103.192 | 873 / 797 | 0 | **no** |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092625 | 142.799 / 138.411 | 559 / 537 | 0 | **no** |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092467 | 84.315 / 86.597 | 469 / 515 | 0 | **no** |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067732 | 109.502 / 115.794 | 697 / 727 | 0 | **no** |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066385 | 84.726 / 87.157 | 432 / 464 | 0 | **no** |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080945 | 139.224 / 132.294 | 652 / 634 | 0 | **no** |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.116684 | 89.140 / 90.650 | 383 / 395 | 0 | **no** |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024143 | 98.403 / 100.961 | 690 / 740 | 0 | **no** |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060628 | 125.982 / 126.976 | 510 / 528 | 0 | **no** |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044694 | 80.075 / 81.228 | 381 / 441 | 0 | **no** |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032867 | 119.597 / 116.663 | 743 / 695 | 0 | **no** |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052284 | 133.863 / 120.111 | 1059 / 829 | 0 | **no** |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064495 | 147.356 / 146.473 | 749 / 676 | 0 | **no** |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100743 | 122.816 / 122.436 | 739 / 785 | 0 | **no** |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012418 | 98.210 / 93.889 | 771 / 631 | 0 | **no** |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048287 | 204.787 / 201.088 | 881 / 853 | 0 | **no** |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033691 | 163.654 / 159.417 | 1099 / 1149 | 0 | **no** |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021763 | 188.903 / 198.204 | 1146 / 1200 | 0 | **no** |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.027961 | 277.263 / 268.001 | 3086 / 2578 | 0 | **no** |

**0 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR -0.04 %, LAT -0.89 %, P99 -1.69 %.

## `EB_inf_ts`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | identical |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104537 | 82.624 / 82.624 | 375 / 375 | 0 | yes |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128441 | 67.032 / 67.032 | 250 / 250 | 0 | yes |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058402 | 108.749 / 108.749 | 873 / 873 | 0 | yes |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 142.799 / 142.799 | 559 / 559 | 0 | yes |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 84.315 / 84.315 | 469 / 469 | 0 | yes |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067893 | 109.502 / 109.502 | 697 / 697 | 0 | yes |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066699 | 84.726 / 84.726 | 432 / 432 | 0 | yes |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080813 | 139.224 / 139.224 | 652 / 652 | 0 | yes |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.116919 | 89.140 / 89.140 | 383 / 383 | 0 | yes |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024292 | 98.403 / 98.403 | 690 / 690 | 0 | yes |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060681 | 125.982 / 125.982 | 510 / 510 | 0 | yes |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044760 | 80.075 / 80.075 | 381 / 381 | 0 | yes |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032838 | 119.597 / 119.597 | 743 / 743 | 0 | yes |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052030 | 133.863 / 133.863 | 1059 / 1059 | 0 | yes |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064263 | 147.356 / 147.356 | 749 / 749 | 0 | yes |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100645 | 122.816 / 122.816 | 739 / 739 | 0 | yes |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012449 | 98.210 / 98.210 | 771 / 771 | 0 | yes |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048234 | 204.787 / 204.787 | 881 / 881 | 0 | yes |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033656 | 163.654 / 163.654 | 1099 / 1099 | 0 | yes |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021762 | 188.903 / 188.903 | 1146 / 1146 | 0 | yes |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.028176 | 277.263 / 277.263 | 3086 / 3086 | 0 | yes |

**21 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR +0.00 %, LAT +0.00 %, P99 +0.00 %.

## `EB_down_inf`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | identical |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104455 | 82.624 / 82.096 | 375 / 350 | 0 | **no** |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128564 | 67.032 / 65.919 | 250 / 240 | 0 | **no** |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058371 | 108.749 / 113.125 | 873 / 893 | 0 | **no** |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092473 | 142.799 / 144.663 | 559 / 525 | 0 | **no** |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092488 | 84.315 / 86.823 | 469 / 541 | 0 | **no** |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067768 | 109.502 / 112.857 | 697 / 701 | 0 | **no** |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066699 | 84.726 / 84.828 | 432 / 406 | 0 | **no** |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080476 | 139.224 / 135.683 | 652 / 615 | 0 | **no** |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.117122 | 89.140 / 87.293 | 383 / 382 | 0 | **no** |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024047 | 98.403 / 101.869 | 690 / 773 | 0 | **no** |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060586 | 125.982 / 128.922 | 510 / 532 | 0 | **no** |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044736 | 80.075 / 81.224 | 381 / 401 | 0 | **no** |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032873 | 119.597 / 118.430 | 743 / 740 | 0 | **no** |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052124 | 133.863 / 130.431 | 1059 / 934 | 0 | **no** |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064365 | 147.356 / 137.508 | 749 / 586 | 0 | **no** |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100583 | 122.816 / 127.197 | 739 / 830 | 0 | **no** |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012445 | 98.210 / 93.709 | 771 / 630 | 0 | **no** |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048254 | 204.787 / 214.405 | 881 / 940 | 0 | **no** |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033562 | 163.654 / 161.785 | 1099 / 1173 | 0 | **no** |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021773 | 188.903 / 195.695 | 1146 / 1136 | 0 | **no** |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.027904 | 277.263 / 250.541 | 3086 / 2672 | 0 | **no** |

**0 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR -0.13 %, LAT -0.16 %, P99 -1.89 %.

## `EB_down_inf_ts`

| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | identical |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0x0000 | 0.0130 | 101 | 0.104537 / 0.104537 | 82.624 / 82.624 | 375 / 375 | 0 | yes |
| 2x2 | localized | 0x0000 | 0.0160 | 101 | 0.128441 / 0.128441 | 67.032 / 67.032 | 250 / 250 | 0 | yes |
| 2x2 | hotspot | 0x0000 | 0.0075 | 101 | 0.058402 / 0.058402 | 108.749 / 108.749 | 873 / 873 | 0 | yes |
| 2x2 | chipperm | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 142.799 / 142.799 | 559 / 559 | 0 | yes |
| 2x2 | chiptrans | 0x0000 | 0.0115 | 101 | 0.092592 / 0.092592 | 84.315 / 84.315 | 469 / 469 | 0 | yes |
| 2x2 | movinghot | 0x0000 | 0.0085 | 101 | 0.067893 / 0.067893 | 109.502 / 109.502 | 697 / 697 | 0 | yes |
| 2x2 | uniform | 0x1023 | 0.0085 | 151 | 0.066699 / 0.066699 | 84.726 / 84.726 | 432 / 432 | 0 | yes |
| 3x3 | uniform | 0x0 | 0.0100 | 101 | 0.080813 / 0.080813 | 139.224 / 139.224 | 652 / 652 | 0 | yes |
| 3x3 | localized | 0x0 | 0.0145 | 101 | 0.116919 / 0.116919 | 89.140 / 89.140 | 383 / 383 | 0 | yes |
| 3x3 | hotspot | 0x0 | 0.0031 | 101 | 0.024292 / 0.024292 | 98.403 / 98.403 | 690 / 690 | 0 | yes |
| 3x3 | chipperm | 0x0 | 0.0075 | 101 | 0.060681 / 0.060681 | 125.982 / 125.982 | 510 / 510 | 0 | yes |
| 3x3 | chiptrans | 0x0 | 0.0055 | 101 | 0.044760 / 0.044760 | 80.075 / 80.075 | 381 / 381 | 0 | yes |
| 3x3 | movinghot | 0x0 | 0.0041 | 101 | 0.032838 / 0.032838 | 119.597 / 119.597 | 743 / 743 | 0 | yes |
| 3x3 | uniform | 0xC82846001 | 0.0065 | 151 | 0.052030 / 0.052030 | 133.863 / 133.863 | 1059 / 1059 | 0 | yes |
| 4x4 | uniform | 0x0 | 0.0080 | 101 | 0.064263 / 0.064263 | 147.356 / 147.356 | 749 / 749 | 0 | yes |
| 4x4 | localized | 0x0 | 0.0125 | 101 | 0.100645 / 0.100645 | 122.816 / 122.816 | 739 / 739 | 0 | yes |
| 4x4 | hotspot | 0x0 | 0.0016 | 101 | 0.012449 / 0.012449 | 98.210 / 98.210 | 771 / 771 | 0 | yes |
| 4x4 | chipperm | 0x0 | 0.0060 | 101 | 0.048234 / 0.048234 | 204.787 / 204.787 | 881 / 881 | 0 | yes |
| 4x4 | chiptrans | 0x0 | 0.0043 | 101 | 0.033656 / 0.033656 | 163.654 / 163.654 | 1099 / 1099 | 0 | yes |
| 4x4 | movinghot | 0x0 | 0.0028 | 101 | 0.021762 / 0.021762 | 188.903 / 188.903 | 1146 / 1146 | 0 | yes |
| 4x4 | uniform | 0x26E020A00402D804 | 0.0039 | 151 | 0.028176 / 0.028176 | 277.263 / 277.263 | 3086 / 3086 | 0 | yes |

**21 / 21 identical.** Runs with a packet off DeFT-P's entry VL: 0. Mean of the 21 runs against DeFT_P: THR +0.00 %, LAT +0.00 %, P99 +0.00 %.

* `EB_inf` is not identical to DeFT_P, but every packet takes DeFT-P's entry VL, and with its tie-breaks on a stream of their own (`EB_inf_ts`) it is identical in every run. So the only difference is the random stream: one more draw per injection (`EB_inf`) or per commit (`EB_down_inf`) shifts every later draw of the crossbar arbitration. The row is DeFT_P's routing with another arbitration sequence; it joins Parts C and D as an anchor (`DECISIONS.md`).
* `EB_down_inf` is not identical to DeFT_P, but every packet takes DeFT-P's entry VL, and with its tie-breaks on a stream of their own (`EB_down_inf_ts`) it is identical in every run. So the only difference is the random stream: one more draw per injection (`EB_inf`) or per commit (`EB_down_inf`) shifts every later draw of the crossbar arbitration. The row is DeFT_P's routing with another arbitration sequence; it joins Parts C and D as an anchor (`DECISIONS.md`).

* **T = infinity does not depend on S, P, B or the age of the information.** EBf(vl, 0, 0.5, infinity) with `oracle_period 64` (`EB_inf_other`)
  against `EB_inf` = EBf(route, 1, 1, infinity): **21 / 21 runs identical** (the whole `summary` block, the fields compared above and the counters of
  `entry_stats`). Every choice is the entry VL of DeFT-P and every injection draws once, whatever the cost reads; so one anchor row stands for the
  T = infinity member of every sub-family, of `EB_best` and of `EB_best64`.

Hops of the anchor runs that offer more than one output (must be 0): 0.
