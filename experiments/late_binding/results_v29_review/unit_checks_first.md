# A2: unit checks of `-deft_lb entry_commit first` (experiments_v29.py a2_funits)

Seed 101, pipe_all 2, `-traffic_rng 1`, 1.0 x Lsat of DeFT_P.

## 1. `entry_commit first` changes nothing when the entry mask has one candidate

`EB_first` (the main row with `entry_commit first`) against the main row on a mask of round 25 that leaves every chiplet one functional VL (uniform traffic at
1.0 x Lsat of that mask). Compared: the whole `summary` block and every field of `deft_lb` except the counters of the option.

| size | mask | rate | accepted main / EB_first | latency main / EB_first | heads bound | identical |
|---|---|---|---|---|---|---|
| 2x2 | 0xBDBD | 0.0037 | 0.029516 / 0.029516 | 85.7961 / 85.7961 | 0 | yes |
| 3x3 | 0x7EDE7EDEE | 0.0033 | 0.026345 / 0.026345 | 158.1849 / 158.1849 | 0 | yes |
| 4x4 | 0x77E7BBD7EBEE7BDB | 0.0027 | 0.020939 / 0.020939 | 166.4223 / 166.4223 | 0 | yes |

**3 / 3 identical.**

## 2. The committed VL against the main row's selection at the commit router

`EB_first` with `-deft_lb commit_check 1000`: for the first 1000 heads of the measured window that are bound, the costs that the main row's selection gives the
outputs of the commit router (the full entry mask, the state of that router at the moment the decision for it is computed, `lut_bias` as the selection charges
it) are computed a second time, next to the commit. *unique*: the output towards the committed VL is the one cheapest output of the main row's selection.
*tie*: the selection has more than one cheapest output and the output towards the committed VL is among them. *different*: it is not a cheapest output (must be
0 on every size, 2x2 with its penalty included: the commit follows the selection's own choice). *not least*: the committed VL is not a candidate of least cost
among those that the selected output keeps (must be 0). Two values of `lut_bias` per size: the frozen value of the main row, and 4.

| size | lut_bias | scenario | heads checked | unique | tie | different | not least | largest difference of the least cost |
|---|---|---|---|---|---|---|---|---|
| 2x2 | 2 | uniform | 1000 | 853 | 147 | 0 | 0 | 0 |
| 2x2 | 4 | uniform | 1000 | 941 | 59 | 0 | 0 | 0 |
| 2x2 | 2 | localized | 1000 | 875 | 125 | 0 | 0 | 0 |
| 2x2 | 4 | localized | 1000 | 957 | 43 | 0 | 0 | 0 |
| 2x2 | 2 | hotspot | 1000 | 825 | 175 | 0 | 0 | 0 |
| 2x2 | 4 | hotspot | 1000 | 959 | 41 | 0 | 0 | 0 |
| 2x2 | 2 | chipperm | 1000 | 904 | 96 | 0 | 0 | 0 |
| 2x2 | 4 | chipperm | 1000 | 938 | 62 | 0 | 0 | 0 |
| 2x2 | 2 | chiptrans | 1000 | 893 | 107 | 0 | 0 | 0 |
| 2x2 | 4 | chiptrans | 1000 | 924 | 76 | 0 | 0 | 0 |
| 2x2 | 2 | movinghot | 1000 | 886 | 114 | 0 | 0 | 0 |
| 2x2 | 4 | movinghot | 1000 | 955 | 45 | 0 | 0 | 0 |
| 3x3 | 0 | uniform | 1000 | 770 | 230 | 0 | 0 | 0 |
| 3x3 | 4 | uniform | 1000 | 939 | 61 | 0 | 0 | 0 |
| 3x3 | 0 | localized | 1000 | 760 | 240 | 0 | 0 | 0 |
| 3x3 | 4 | localized | 1000 | 958 | 42 | 0 | 0 | 0 |
| 3x3 | 0 | hotspot | 1000 | 564 | 436 | 0 | 0 | 0 |
| 3x3 | 4 | hotspot | 1000 | 966 | 34 | 0 | 0 | 0 |
| 3x3 | 0 | chipperm | 1000 | 792 | 208 | 0 | 0 | 0 |
| 3x3 | 4 | chipperm | 1000 | 939 | 61 | 0 | 0 | 0 |
| 3x3 | 0 | chiptrans | 1000 | 784 | 216 | 0 | 0 | 0 |
| 3x3 | 4 | chiptrans | 1000 | 936 | 64 | 0 | 0 | 0 |
| 3x3 | 0 | movinghot | 1000 | 778 | 222 | 0 | 0 | 0 |
| 3x3 | 4 | movinghot | 1000 | 963 | 37 | 0 | 0 | 0 |
| 4x4 | 0 | uniform | 1000 | 781 | 219 | 0 | 0 | 0 |
| 4x4 | 4 | uniform | 1000 | 932 | 68 | 0 | 0 | 0 |
| 4x4 | 0 | localized | 1000 | 790 | 210 | 0 | 0 | 0 |
| 4x4 | 4 | localized | 1000 | 929 | 71 | 0 | 0 | 0 |
| 4x4 | 0 | hotspot | 1000 | 542 | 458 | 0 | 0 | 0 |
| 4x4 | 4 | hotspot | 1000 | 983 | 17 | 0 | 0 | 0 |
| 4x4 | 0 | chipperm | 1000 | 854 | 146 | 0 | 0 | 0 |
| 4x4 | 4 | chipperm | 1000 | 960 | 40 | 0 | 0 | 0 |
| 4x4 | 0 | chiptrans | 1000 | 823 | 177 | 0 | 0 | 0 |
| 4x4 | 4 | chiptrans | 1000 | 934 | 66 | 0 | 0 | 0 |
| 4x4 | 0 | movinghot | 1000 | 758 | 242 | 0 | 0 | 0 |
| 4x4 | 4 | movinghot | 1000 | 968 | 32 | 0 | 0 | 0 |

| size | heads checked | unique | tie | different | not least |
|---|---|---|---|---|---|
| 2x2 | 12000 | 10910 | 1090 | 0 | 0 |
| 3x3 | 12000 | 10149 | 1851 | 0 | 0 |
| 4x4 | 12000 | 10254 | 1746 | 0 | 0 |

**Different or not least, over the three sizes: 0.** Sizes with fewer than 12000 checked heads: none.

## 3. `commit_check` reads only

`EB_first` on uniform traffic with and without `commit_check`. Compared: the whole `summary` block and every field of `deft_lb` except those of the check.

| size | lut_bias | accepted without / with | latency without / with | identical |
|---|---|---|---|---|
| 2x2 | 2 | 0.104385 / 0.104385 | 71.9671 / 71.9671 | yes |
| 3x3 | 0 | 0.081474 / 0.081474 | 102.0892 / 102.0892 | yes |
| 4x4 | 0 | 0.064323 / 0.064323 | 111.5279 / 111.5279 | yes |

**3 / 3 identical.**

## 4. At most one decision with more than one offered output per head

Per run of check 2: the measured heads that were bound (a commit is a decision at which the routing function offers the head more than one output), the
largest number of commits of one head (counted per packet; must be 1), the hops at which a head is offered more than one output after it left the router
before its commit router (`hops_chip_multi` + `hops_ipos_multi`; must be 0), and where the commit is made: at the router below the exit VL (the decision
computed at the Down move) or further on.

| size | lut_bias | scenario | Up moves | heads bound | share bound | bound below the exit VL | share | most commits of one head | multi-output hops after |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | 2 | uniform | 5127 | 5111 | 99.7 % | 1681 | 32.9 % | 1 | 0 |
| 2x2 | 4 | uniform | 5128 | 5109 | 99.6 % | 1681 | 32.9 % | 1 | 0 |
| 2x2 | 2 | localized | 5032 | 5034 | 100.0 % | 1657 | 32.9 % | 1 | 0 |
| 2x2 | 4 | localized | 5031 | 5030 | 100.0 % | 1657 | 32.9 % | 1 | 0 |
| 2x2 | 2 | hotspot | 2892 | 2889 | 99.9 % | 981 | 34.0 % | 1 | 0 |
| 2x2 | 4 | hotspot | 2894 | 2889 | 99.8 % | 981 | 34.0 % | 1 | 0 |
| 2x2 | 2 | chipperm | 5841 | 5846 | 100.1 % | 0 | 0.0 % | 1 | 0 |
| 2x2 | 4 | chipperm | 5918 | 5921 | 100.1 % | 0 | 0.0 % | 1 | 0 |
| 2x2 | 2 | chiptrans | 2937 | 2938 | 100.0 % | 0 | 0.0 % | 1 | 0 |
| 2x2 | 4 | chiptrans | 2967 | 2967 | 100.0 % | 0 | 0.0 % | 1 | 0 |
| 2x2 | 2 | movinghot | 3293 | 3286 | 99.8 % | 1085 | 33.0 % | 1 | 0 |
| 2x2 | 4 | movinghot | 3300 | 3290 | 99.7 % | 1086 | 33.0 % | 1 | 0 |
| 3x3 | 0 | uniform | 10529 | 10512 | 99.8 % | 2615 | 24.9 % | 1 | 0 |
| 3x3 | 4 | uniform | 10521 | 10497 | 99.8 % | 2611 | 24.9 % | 1 | 0 |
| 3x3 | 0 | localized | 9967 | 9977 | 100.1 % | 2434 | 24.4 % | 1 | 0 |
| 3x3 | 4 | localized | 9976 | 9972 | 100.0 % | 2434 | 24.4 % | 1 | 0 |
| 3x3 | 0 | hotspot | 3203 | 3206 | 100.1 % | 808 | 25.2 % | 1 | 0 |
| 3x3 | 4 | hotspot | 3211 | 3205 | 99.8 % | 808 | 25.2 % | 1 | 0 |
| 3x3 | 0 | chipperm | 7851 | 7836 | 99.8 % | 2011 | 25.7 % | 1 | 0 |
| 3x3 | 4 | chipperm | 7856 | 7842 | 99.8 % | 2013 | 25.7 % | 1 | 0 |
| 3x3 | 0 | chiptrans | 4115 | 4110 | 99.9 % | 0 | 0.0 % | 1 | 0 |
| 3x3 | 4 | chiptrans | 4267 | 4264 | 99.9 % | 0 | 0.0 % | 1 | 0 |
| 3x3 | 0 | movinghot | 4238 | 4234 | 99.9 % | 1099 | 26.0 % | 1 | 0 |
| 3x3 | 4 | movinghot | 4227 | 4227 | 100.0 % | 1098 | 26.0 % | 1 | 0 |
| 4x4 | 0 | uniform | 15470 | 15468 | 100.0 % | 3213 | 20.8 % | 1 | 0 |
| 4x4 | 4 | uniform | 15457 | 15458 | 100.0 % | 3213 | 20.8 % | 1 | 0 |
| 4x4 | 0 | localized | 15502 | 15501 | 100.0 % | 3063 | 19.8 % | 1 | 0 |
| 4x4 | 4 | localized | 15512 | 15491 | 99.9 % | 3059 | 19.7 % | 1 | 0 |
| 4x4 | 0 | hotspot | 3015 | 3015 | 100.0 % | 607 | 20.1 % | 1 | 0 |
| 4x4 | 4 | hotspot | 3006 | 3015 | 100.3 % | 607 | 20.1 % | 1 | 0 |
| 4x4 | 0 | chipperm | 11559 | 11552 | 99.9 % | 0 | 0.0 % | 1 | 0 |
| 4x4 | 4 | chipperm | 12341 | 12336 | 100.0 % | 0 | 0.0 % | 1 | 0 |
| 4x4 | 0 | chiptrans | 6091 | 6088 | 100.0 % | 0 | 0.0 % | 1 | 0 |
| 4x4 | 4 | chiptrans | 6459 | 6452 | 99.9 % | 0 | 0.0 % | 1 | 0 |
| 4x4 | 0 | movinghot | 5258 | 5256 | 100.0 % | 1074 | 20.4 % | 1 | 0 |
| 4x4 | 4 | movinghot | 5234 | 5243 | 100.2 % | 1072 | 20.4 % | 1 | 0 |

**Most commits of one head over all runs: 1. Multi-output hops after the commit: 0.**

**All unit checks pass: yes.**
