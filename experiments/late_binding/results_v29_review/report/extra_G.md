# v29 Part G: a table added after the results were seen (extra_v29.py g)

Descriptive; not in the pre-registration and no test. Added on 26 November after the results of Part G had been read (`DECISIONS.md`, "Tables added after the
results"). The search runs of Part G (`trace_runs.csv`: DeFT_P, seed 41, 2x2, the first 700,000 cycles of region 2 of each trace, dependency mode).

## X.11 What the compression does to a trace

In dependency mode a packet is released when its time stamp has come and every packet it depends on has been delivered. `-netrace_compress S` divides the time
stamps by S; it does not shorten the wait for a dependency. *Completes at*: the cycle at which the last packet of the window is delivered, in thousands of
cycles (700 = the length of the window at S = 1). *Waited*: the packets that were not yet cleared by their dependencies when their time stamp came, as a share
of the packets that enter the network. *Offered*: received flits per node and cycle up to the completion, as a share of the load at which DeFT_P saturates
under uniform traffic (8 x Lsat = 0.104 flits/node/cycle).

| trace | packets | completes at, S = 1, 2, 4, 8, 16, 32 (thousand cycles) | waited, S = 1 | waited, S = 32 | offered, S = 1 | offered, S = 32 | latency at S = 32 / at S = 1 |
|---|---|---|---|---|---|---|---|
| blackscholes | 14067 | 774 / 767 / 766 / 765 / 767 / 767 | 94 % | 95 % | 2.7 % | 2.7 % | 1.17 |
| bodytrack | 412 | 695 / 348 / 174 / 87 / 44 / 22 | 26 % | 80 % | 0.1 % | 2.5 % | 1.05 |
| canneal | 8119 | 695 / 348 / 215 / 170 / 151 / 144 | 87 % | 98 % | 1.5 % | 7.2 % | 1.08 |
| dedup | 2266 | 700 / 351 / 177 / 107 / 107 / 106 | 65 % | 88 % | 0.4 % | 2.7 % | 1.18 |
| ferret | 6486 | 720 / 434 / 367 / 367 / 368 / 367 | 88 % | 97 % | 1.3 % | 2.5 % | 1.30 |
| fluidanimate | 2386 | 698 / 349 / 175 / 130 / 131 / 131 | 71 % | 94 % | 0.5 % | 2.4 % | 1.10 |
| swaptions | 8870 | 712 / 506 / 496 / 492 / 492 / 492 | 96 % | 99 % | 1.8 % | 2.6 % | 1.02 |
| vips | 13873 | 717 / 558 / 550 / 546 / 545 / 545 | 93 % | 98 % | 2.6 % | 3.4 % | 1.02 |
| x264 | 13362 | 711 / 619 / 611 / 609 / 608 / 610 | 80 % | 85 % | 3.4 % | 3.9 % | 3.36 |

