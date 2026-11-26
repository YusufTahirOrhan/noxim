# v29 Part F: a table added after the results were seen (extra_v29.py f)

Descriptive; not in the pre-registration and no test. Added on 26 November after the results of F1 had been read (`DECISIONS.md`, "Tables added after the results").
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

