# A1 / A2: unit checks of the new options (experiments_v27.py a2_units)

Seed 101, pipe_all 2, `-traffic_rng 1`, 1.0 x Lsat of DeFT_P.

## 1. `-deft_lb entry_stats 1` is observation only

The main row as round 25 defines it (`experiments_v25.row_args`) and the same row with `entry_stats 1`, on the six fault-free scenarios. Compared: the whole
`summary` block and every field of the `deft_lb` block that the row without the option has.

| size | scenario | accepted without / with | latency without / with | identical |
|---|---|---|---|---|
| 2x2 | uniform | 0.104393 / 0.104393 | 64.3062 / 64.3062 | yes |
| 2x2 | localized | 0.128693 / 0.128693 | 60.3170 / 60.3170 | yes |
| 2x2 | hotspot | 0.059729 / 0.059729 | 55.1541 / 55.1541 | yes |
| 2x2 | chipperm | 0.092873 / 0.092873 | 97.4513 / 97.4513 | yes |
| 2x2 | chiptrans | 0.092697 / 0.092697 | 59.5855 / 59.5855 | yes |
| 2x2 | movinghot | 0.067592 / 0.067592 | 90.1151 / 90.1151 | yes |
| 3x3 | uniform | 0.081384 / 0.081384 | 81.9379 / 81.9379 | yes |
| 3x3 | localized | 0.117186 / 0.117186 | 65.7639 / 65.7639 | yes |
| 3x3 | hotspot | 0.024790 / 0.024790 | 60.1337 / 60.1337 | yes |
| 3x3 | chipperm | 0.060833 / 0.060833 | 83.0558 / 83.0558 | yes |
| 3x3 | chiptrans | 0.044924 / 0.044924 | 65.1780 / 65.1780 | yes |
| 3x3 | movinghot | 0.032905 / 0.032905 | 110.0291 / 110.0291 | yes |
| 4x4 | uniform | 0.064196 / 0.064196 | 91.0346 / 91.0346 | yes |
| 4x4 | localized | 0.100572 / 0.100572 | 72.2347 / 72.2347 | yes |
| 4x4 | hotspot | 0.012500 / 0.012500 | 66.7994 / 66.7994 | yes |
| 4x4 | chipperm | 0.048208 / 0.048208 | 146.9687 / 146.9687 | yes |
| 4x4 | chiptrans | 0.034064 / 0.034064 | 83.5722 / 83.5722 | yes |
| 4x4 | movinghot | 0.021770 / 0.021770 | 205.1283 / 205.1283 | yes |

**18 / 18 identical.**

## 2. `entry_commit down` changes nothing when the entry mask has one candidate

`EB_down` against the main row on a mask of round 25 that leaves every chiplet one functional VL (uniform traffic at 1.0 x Lsat of that mask). Compared: the
whole `summary` block and every field of `deft_lb` except the two counters of the option.

| size | mask | rate | accepted main / EB_down | latency main / EB_down | Down moves counted | of them bound | identical |
|---|---|---|---|---|---|---|---|
| 2x2 | 0xBDBD | 0.0037 | 0.029516 / 0.029516 | 85.7961 / 85.7961 | 1425 | 0 | yes |
| 3x3 | 0x7EDE7EDEE | 0.0033 | 0.026345 / 0.026345 | 158.1849 / 158.1849 | 3346 | 0 | yes |
| 4x4 | 0x77E7BBD7EBEE7BDB | 0.0027 | 0.020939 / 0.020939 | 166.4223 / 166.4223 | 5047 | 0 | yes |

**3 / 3 identical.**

## 3. The output of the committed candidate against the main row's selection

`EB_down` with `-deft_lb commit_check 1000`: for the first 1,000 heads of the measured window that move Down with more than one entry candidate, the costs the
main row's selection gives the outputs of the interposer router below (full entry mask, the same state, the same moment) are computed next to the costs of the
candidates. *unique*: the output of the committed candidate is the one cheapest output of the main row's selection. *tie*: the main row's selection has more than
one cheapest output and the committed one is among them (the two break ties differently: the selection among outputs, the commit among candidates). *different*:
the output of the committed candidate is not a cheapest output of the main row's selection. On 3x3 and 4x4 (D = 0) *different* must be 0; on 2x2 (D = 2) the
penalty is charged differently (to an output that drops the default VL, or to a candidate that is not the default VL), so the two can differ.

| size | D | scenario | heads checked | unique | tie | different | largest difference of the least cost |
|---|---|---|---|---|---|---|---|
| 2x2 | 2 | uniform | 1000 | 950 | 46 | 4 | 2 |
| 2x2 | 2 | localized | 1000 | 952 | 39 | 9 | 2 |
| 2x2 | 2 | hotspot | 1000 | 930 | 64 | 6 | 2 |
| 2x2 | 2 | chipperm | 1000 | 1000 | 0 | 0 | 2 |
| 2x2 | 2 | chiptrans | 1000 | 1000 | 0 | 0 | 2 |
| 2x2 | 2 | movinghot | 1000 | 962 | 34 | 4 | 2 |
| 3x3 | 0 | uniform | 1000 | 939 | 61 | 0 | 0 |
| 3x3 | 0 | localized | 1000 | 960 | 40 | 0 | 0 |
| 3x3 | 0 | hotspot | 1000 | 911 | 89 | 0 | 0 |
| 3x3 | 0 | chipperm | 1000 | 982 | 18 | 0 | 0 |
| 3x3 | 0 | chiptrans | 1000 | 1000 | 0 | 0 | 0 |
| 3x3 | 0 | movinghot | 1000 | 917 | 83 | 0 | 0 |
| 4x4 | 0 | uniform | 1000 | 949 | 51 | 0 | 0 |
| 4x4 | 0 | localized | 1000 | 947 | 53 | 0 | 0 |
| 4x4 | 0 | hotspot | 1000 | 905 | 95 | 0 | 0 |
| 4x4 | 0 | chipperm | 1000 | 1000 | 0 | 0 | 0 |
| 4x4 | 0 | chiptrans | 1000 | 1000 | 0 | 0 | 0 |
| 4x4 | 0 | movinghot | 1000 | 936 | 64 | 0 | 0 |

| size | heads checked | unique | tie | different |
|---|---|---|---|---|
| 2x2 | 6000 | 5794 | 183 | 23 |
| 3x3 | 6000 | 5709 | 291 | 0 |
| 4x4 | 6000 | 5737 | 263 | 0 |

**Different on 3x3 and 4x4 (D = 0): 0.**

## 4. `EB_vl` with `oracle_beta 0`: the entry VL of least total hops (description, not a gate)

With `oracle_beta 0` the injection-time choice is the entry VL with the fewest hops from the source through the LUT's exit VL to the destination, ties at random.
Share of the packets that move Up on DeFT-P's entry VL (`entry_stats`, measured window), fault-free:

| size | uniform | localized | hotspot | chipperm | chiptrans | movinghot |
|---|---|---|---|---|---|---|
| 2x2 | 52.0 % | 53.1 % | 45.9 % | 52.0 % | 51.3 % | 52.9 % |
| 3x3 | 51.9 % | 51.9 % | 43.1 % | 52.3 % | 52.1 % | 52.9 % |
| 4x4 | 52.9 % | 51.4 % | 40.7 % | 53.2 % | 52.9 % | 53.1 % |

No hop of these `EB_vl` runs offers more than one output: yes.
No hop of the `EB_down` runs of check 3 offers more than one output: yes.

**All unit checks pass: yes.**
