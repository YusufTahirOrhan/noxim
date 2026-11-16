# A2: the anchor row against DeFT_P (experiments_v27.py a2_anchor)

`EB_lut` = `-routing DEFT_LB -deft_lb exit lut -deft_lb entry lut -deft_lb chip_tm XY -deft_lb ipos_tm XY` with DeFT-P's options (`-deft_up_keep 1
-deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst`) against `DeFT_P` (`-routing DEFT` with the same options): the six fault-free scenarios at 1.0 x Lsat,
seed 101, pipe_all 2, `-traffic_rng 1`. Compared: every field of the `summary` block of the stats file except the three energy fields (injected and received
packets and flits, mean and largest delay, throughput), and the delay statistics of the `deft_lb` block (mean, median, p95, p99, inter- and intra-chiplet).

| size | scenario | rate | accepted DeFT_P / EB_lut | latency DeFT_P / EB_lut | p99 DeFT_P / EB_lut | received DeFT_P / EB_lut | identical |
|---|---|---|---|---|---|---|---|
| 2x2 | uniform | 0.0130 | 0.104537 / 0.104537 | 82.6236 / 82.6236 | 375 / 375 | 6687 / 6687 | yes |
| 2x2 | localized | 0.0160 | 0.128441 / 0.128441 | 67.0322 / 67.0322 | 250 / 250 | 8221 / 8221 | yes |
| 2x2 | hotspot | 0.0075 | 0.058402 / 0.058402 | 108.7493 / 108.7493 | 873 / 873 | 3737 / 3737 | yes |
| 2x2 | chipperm | 0.0115 | 0.092592 / 0.092592 | 142.7993 / 142.7993 | 559 / 559 | 5928 / 5928 | yes |
| 2x2 | chiptrans | 0.0115 | 0.092592 / 0.092592 | 84.3150 / 84.3150 | 469 / 469 | 5927 / 5927 | yes |
| 2x2 | movinghot | 0.0085 | 0.067893 / 0.067893 | 109.5020 / 109.5020 | 697 / 697 | 4343 / 4343 | yes |
| 3x3 | uniform | 0.0100 | 0.080813 / 0.080813 | 139.2243 / 139.2243 | 652 / 652 | 11634 / 11634 | yes |
| 3x3 | localized | 0.0145 | 0.116919 / 0.116919 | 89.1396 / 89.1396 | 383 / 383 | 16839 / 16839 | yes |
| 3x3 | hotspot | 0.0031 | 0.024292 / 0.024292 | 98.4029 / 98.4029 | 690 / 690 | 3497 / 3497 | yes |
| 3x3 | chipperm | 0.0075 | 0.060681 / 0.060681 | 125.9819 / 125.9819 | 510 / 510 | 8736 / 8736 | yes |
| 3x3 | chiptrans | 0.0055 | 0.044760 / 0.044760 | 80.0754 / 80.0754 | 381 / 381 | 6448 / 6448 | yes |
| 3x3 | movinghot | 0.0041 | 0.032838 / 0.032838 | 119.5967 / 119.5967 | 743 / 743 | 4729 / 4729 | yes |
| 4x4 | uniform | 0.0080 | 0.064263 / 0.064263 | 147.3564 / 147.3564 | 749 / 749 | 16447 / 16447 | yes |
| 4x4 | localized | 0.0125 | 0.100645 / 0.100645 | 122.8161 / 122.8161 | 739 / 739 | 25767 / 25767 | yes |
| 4x4 | hotspot | 0.0016 | 0.012449 / 0.012449 | 98.2099 / 98.2099 | 771 / 771 | 3187 / 3187 | yes |
| 4x4 | chipperm | 0.0060 | 0.048234 / 0.048234 | 204.7869 / 204.7869 | 881 / 881 | 12353 / 12353 | yes |
| 4x4 | chiptrans | 0.0043 | 0.033656 / 0.033656 | 163.6536 / 163.6536 | 1099 / 1099 | 8612 / 8612 | yes |
| 4x4 | movinghot | 0.0028 | 0.021762 / 0.021762 | 188.9025 / 188.9025 | 1146 / 1146 | 5571 / 5571 | yes |

**18 / 18 identical.** The energy fields of the summary are equal as well in 0 of 18 runs (the power model charges the routing function by its name).

Also identical in every one of these runs: the packets per Down VL and per Up VL (`vl_down_packets`, `vl_up_packets`), which DeFT_P counts with `count_vl`.

Hops per packet of DeFT-P's paths (head-flit forwards of `EB_lut` in the measured window per delivered packet; the ejection is not counted):

| size | uniform | localized | hotspot | chipperm | chiptrans | movinghot |
|---|---|---|---|---|---|---|
| 2x2 | 8.03 | 6.93 | 8.04 | 11.45 | 7.08 | 8.07 |
| 3x3 | 11.14 | 8.21 | 11.36 | 14.71 | 10.29 | 11.38 |
| 4x4 | 13.83 | 9.90 | 14.60 | 19.46 | 13.13 | 14.62 |
