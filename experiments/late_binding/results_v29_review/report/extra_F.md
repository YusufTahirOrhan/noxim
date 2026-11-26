# v29 Part F: tables added after the results were seen (extra_v29.py f)

Descriptive; not in the pre-registration and no test. X.9 was added on 26 November after the results of F1 had been read, X.10 on the same day after those of F2
(`DECISIONS.md`, "Tables added after the results").
Counters of the measured heads, summed over the scenarios named and the ten seeds (171-180); the main row, `EB_best`, `EB_best64` and `EB_down_t` are the runs of
round 28 (`results_v28_anchor/eval_runs.csv`), `EB_first` and the two other aged rows those of this round. 2x2 / 3x3 / 4x4.

## X.9 At how many routers a head of the main row has a choice, and how often each row leaves DeFT-P's entry VL

A head of the main row has a choice at every interposer router that offers it more than one output; a head of `EB_first` is bound at the first such router and has
one output from then on. *Choices per head*: the hops of the main row on the interposer at which more than one output was offered, divided by the heads that move
Up through an entry VL. *Share of the interposer hops*: the same hops as a share of all its hops on the interposer.

| load | choices per head of the main row, six scenarios | share of its interposer hops |
|---|---|---|
| 0.2 x Lsat | 2.08 / 1.69 / 1.73 | 27.9 % / 18.0 % / 14.2 % |
| 0.5 x Lsat | 2.10 / 1.78 / 1.83 | 28.0 % / 18.5 % / 14.6 % |
| 1.0 x Lsat | 2.15 / 1.94 / 2.00 | 28.1 % / 19.4 % / 15.4 % |
| 1.4 x Lsat | 2.15 / 2.03 / 2.07 | 27.6 % / 19.5 % / 15.7 % |

Per scenario at 1.0 x Lsat: the choices per head of the main row, and the heads that move Up on a VL that is not DeFT-P's entry VL.

| scenario | choices per head of the main row | off DeFT-P's entry VL: the main row | `EB_first` | `EB_down_t` |
|---|---|---|---|---|
| uniform | 2.09 / 1.93 / 1.92 | 34.7 % / 56.6 % / 56.7 % | 12.5 % / 14.5 % / 13.8 % | 6.7 % / 6.0 % / 4.4 % |
| localized | 2.09 / 1.95 / 1.94 | 34.8 % / 56.6 % / 57.2 % | 12.1 % / 14.2 % / 14.2 % | 6.5 % / 5.8 % / 4.8 % |
| hotspot | 2.07 / 1.70 / 1.66 | 30.4 % / 58.8 % / 59.7 % | 11.2 % / 7.1 % / 5.0 % | 7.5 % / 3.9 % / 2.6 % |
| chipperm | 2.26 / 1.93 / 2.19 | 39.4 % / 55.1 % / 57.9 % | 16.8 % / 11.8 % / 13.1 % | 3.1 % / 5.4 % / 1.3 % |
| chiptrans | 2.28 / 2.13 / 2.16 | 39.2 % / 55.5 % / 57.1 % | 16.6 % / 11.6 % / 14.0 % | 3.2 % / 1.5 % / 1.2 % |
| movinghot | 2.12 / 1.95 / 1.93 | 39.8 % / 57.6 % / 59.2 % | 15.0 % / 13.0 % / 16.7 % | 7.3 % / 4.6 % / 4.6 % |

The heads that move Up on a VL that is not DeFT-P's entry VL, six scenarios, by load:

| row | 0.2 x Lsat | 0.5 x Lsat | 1.0 x Lsat | 1.4 x Lsat |
|---|---|---|---|---|
| the main row | 15.8 % / 49.6 % / 50.3 % | 21.3 % / 51.5 % / 52.1 % | 36.5 % / 56.5 % / 57.5 % | 58.8 % / 64.9 % / 64.2 % |
| `EB_first` | 1.1 % / 1.4 % / 1.5 % | 3.5 % / 3.9 % / 4.4 % | 14.1 % / 12.8 % / 13.6 % | 25.4 % / 25.3 % / 22.8 % |
| `EB_down_t` | 0.4 % / 0.5 % / 0.3 % | 1.4 % / 1.4 % / 0.9 % | 5.6 % / 5.0 % / 3.4 % | 11.3 % / 10.0 % / 6.6 % |
| `EB_best` | 11.7 % / 35.1 % / 34.7 % | 19.3 % / 45.4 % / 45.6 % | 24.5 % / 49.9 % / 50.3 % | 27.3 % / 51.7 % / 51.6 % |
| `EB_best16` | 2.3 % / 12.2 % / 11.9 % | 8.2 % / 24.2 % / 23.7 % | 16.6 % / 35.3 % / 35.1 % | 21.2 % / 39.6 % / 38.2 % |
| `EB_best64` | 0.1 % / 2.2 % / 2.4 % | 1.1 % / 11.6 % / 11.1 % | 10.4 % / 34.4 % / 32.0 % | 19.1 % / 41.7 % / 38.2 % |
| `EB_best256` | 0.0 % / 0.0 % / 0.0 % | 0.0 % / 0.0 % / 0.0 % | 0.2 % / 4.4 % / 3.4 % | 2.1 % / 20.0 % / 15.9 % |

## X.10 The early binders of age 0 to 256 cycles by scenario

Each row against DeFT_P in one scenario, in per cent; (n.s.) = the unadjusted 95 % interval over the ten seeds includes 0. THR is the largest accepted throughput
over the nine loads, LAT the mean latency at 1.0 x Lsat. Last column: the heads that move Up on a VL that is not DeFT-P's entry VL at 1.0 x Lsat.

| scenario | knowledge of the source | THR against DeFT_P | LAT against DeFT_P | off DeFT-P's entry VL at 1.0 x Lsat |
|---|---|---|---|---|
| uniform | (the main row, late) | +4.9 / +14.6 / +18.7 | -19.2 / -38.6 / -27.9 | 34.7 % / 56.6 % / 56.7 % |
| uniform | 0 cycles (`EB_best`) | +8.3 / +9.8 / +10.9 | -21.8 / -34.9 / -23.2 | 24.7 % / 50.8 % / 51.2 % |
| uniform | 16 cycles (`EB_best16`) | +7.8 / +8.5 / +10.0 | -18.9 / -32.1 / -20.8 | 16.3 % / 38.0 % / 36.8 % |
| uniform | 64 cycles (`EB_best64`) | +4.7 / +4.7 / +7.1 | -11.3 / -9.7 / -8.2 | 8.4 % / 40.4 % / 34.9 % |
| uniform | 256 cycles (`EB_best256`) | -0.5 (n.s.) / -5.9 / -0.6 (n.s.) | +0.2 (n.s.) / +9.2 / -0.0 (n.s.) | 0.0 % / 4.5 % / 1.4 % |
| localized | (the main row, late) | +1.4 / +8.8 / +12.3 | -15.0 / -33.0 / -33.0 | 34.8 % / 56.6 % / 57.2 % |
| localized | 0 cycles (`EB_best`) | +6.2 / +6.6 / +8.3 | -18.3 / -30.4 / -28.8 | 24.9 % / 51.1 % / 51.5 % |
| localized | 16 cycles (`EB_best16`) | +6.1 / +6.2 / +8.2 | -16.0 / -28.1 / -27.6 | 16.1 % / 37.9 % / 37.1 % |
| localized | 64 cycles (`EB_best64`) | +3.6 / +2.6 / +5.1 | -9.0 / -6.1 / -14.8 | 8.1 % / 38.8 % / 35.8 % |
| localized | 256 cycles (`EB_best256`) | +0.1 (n.s.) / -5.4 / -0.8 | -0.5 (n.s.) / -0.1 (n.s.) / -1.2 (n.s.) | 0.0 % / 3.2 % / 2.4 % |
| hotspot | (the main row, late) | +21.5 / +19.5 / +24.8 | -67.4 / -61.7 / -59.4 | 30.4 % / 58.8 % / 59.7 % |
| hotspot | 0 cycles (`EB_best`) | +20.6 / +18.1 / +23.4 | -68.0 / -61.0 / -58.5 | 28.6 % / 48.8 % / 44.9 % |
| hotspot | 16 cycles (`EB_best16`) | +20.4 / +18.6 / +23.4 | -67.3 / -60.9 / -58.5 | 18.2 % / 28.8 % / 26.0 % |
| hotspot | 64 cycles (`EB_best64`) | +20.8 / +18.1 / +23.5 | -65.0 / -59.7 / -57.7 | 10.4 % / 17.8 % / 15.9 % |
| hotspot | 256 cycles (`EB_best256`) | +17.9 / +18.7 / +22.6 | -35.4 / -52.5 / -51.3 | 1.5 % / 4.7 % / 3.9 % |
| chipperm | (the main row, late) | +10.3 / +34.0 / +8.4 | -37.7 / -38.2 / -23.2 | 39.4 % / 55.1 % / 57.9 % |
| chipperm | 0 cycles (`EB_best`) | +8.6 / +15.4 / +7.6 | -36.1 / -31.1 / -23.2 | 23.7 % / 49.6 % / 50.4 % |
| chipperm | 16 cycles (`EB_best16`) | +7.9 / +13.4 / +7.3 | -33.1 / -27.7 / -21.5 | 17.5 % / 35.6 % / 35.7 % |
| chipperm | 64 cycles (`EB_best64`) | +3.8 / +10.5 / +6.0 | -18.4 / -13.5 / -10.1 | 13.0 % / 36.0 % / 33.7 % |
| chipperm | 256 cycles (`EB_best256`) | +0.1 (n.s.) / +0.7 (n.s.) / -1.1 | -0.6 (n.s.) / -6.5 / -0.7 (n.s.) | 0.0 % / 2.8 % / 2.0 % |
| chiptrans | (the main row, late) | +3.2 / +6.3 / +7.2 | -30.8 / -17.0 / -52.4 | 39.2 % / 55.5 % / 57.1 % |
| chiptrans | 0 cycles (`EB_best`) | +2.5 / +3.0 / +2.2 | -29.0 / -15.1 / -33.8 | 23.0 % / 48.4 % / 49.1 % |
| chiptrans | 16 cycles (`EB_best16`) | +2.3 / +3.0 / +2.2 | -25.5 / -12.4 / -29.5 | 17.1 % / 31.4 % / 31.2 % |
| chiptrans | 64 cycles (`EB_best64`) | +1.1 / +1.3 / +1.4 | -13.8 / -4.3 / -20.9 | 12.4 % / 23.8 % / 21.7 % |
| chiptrans | 256 cycles (`EB_best256`) | -0.1 (n.s.) / -4.8 / -0.7 | +0.3 (n.s.) / +0.5 (n.s.) / -3.2 (n.s.) | 0.0 % / 0.4 % / 1.1 % |
| movinghot | (the main row, late) | +3.1 / +1.6 (n.s.) / +2.0 | -25.6 / -12.9 / -4.1 (n.s.) | 39.8 % / 57.6 % / 59.2 % |
| movinghot | 0 cycles (`EB_best`) | +4.0 / +1.1 (n.s.) / +2.2 | -38.1 / -18.3 / -2.9 (n.s.) | 22.8 % / 47.5 % / 49.1 % |
| movinghot | 16 cycles (`EB_best16`) | +4.1 / +0.8 (n.s.) / +2.0 | -35.6 / -18.5 / -2.0 (n.s.) | 14.2 % / 30.2 % / 33.4 % |
| movinghot | 64 cycles (`EB_best64`) | +2.6 / +0.0 (n.s.) / -0.6 (n.s.) | -24.7 / -0.4 (n.s.) / +8.3 | 10.5 % / 29.1 % / 31.0 % |
| movinghot | 256 cycles (`EB_best256`) | +0.4 (n.s.) / -4.6 / -3.6 | -3.1 (n.s.) / +39.3 / +20.1 | 0.4 % / 14.3 % / 17.7 % |

For scale: the mean latency of a packet of DeFT_P, mean over the six scenarios and the ten seeds, is 39 / 51 / 63 cycles at 0.2 x Lsat, 44 / 55 / 68 at 0.5 x Lsat and 114 / 123 / 173 at
1.0 x Lsat.

