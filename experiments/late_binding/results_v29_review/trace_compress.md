# v29 Part G: the compression at which a trace loads the network (experiments_v29.py g_find)

DeFT_P on 2x2, pipe_all 2, one application: the first 700000 cycles of region 2 of each trace, dependency mode, 2- and 18-flit packets, seed 41 (the protocol of the
trace runs of round 25), with `-netrace_compress S`: the time stamps of the trace are divided by S. Chosen per trace: the smallest S in {2, 4, 8, 16, 32} at which
the mean latency of DeFT_P is at least 1.5 times its latency at S = 1. *Offered*: received flits per node and cycle up to the completion of the window.
The runs at S = 1 are runs of round 25 made again with the build of this round; *as round 25*: mean latency, p99 and completion cycle equal the row of
`results_v25_confirm/app_runs.csv`.

| trace | S = 1: latency (cycles), offered | as round 25 | S = 2: latency / factor | S = 4: latency / factor | S = 8: latency / factor | S = 16: latency / factor | S = 32: latency / factor | chosen S | offered at the chosen S |
|---|---|---|---|---|---|---|---|---|---|
| blackscholes | 52.1, 0.0028 | yes | 52.2 / 1.00 | 52.4 / 1.01 | 53.0 / 1.02 | 56.6 / 1.08 | 61.1 / 1.17 | none reaches 1.5 | - |
| bodytrack | 20.9, 0.0001 | yes | 20.9 / 1.00 | 20.9 / 1.00 | 20.9 / 1.00 | 21.1 / 1.01 | 21.9 / 1.05 | none reaches 1.5 | - |
| canneal | 65.6, 0.0015 | yes | 59.9 / 0.91 | 58.2 / 0.89 | 60.2 / 0.92 | 64.9 / 0.99 | 70.6 / 1.08 | none reaches 1.5 | - |
| dedup | 41.3, 0.0004 | yes | 42.2 / 1.02 | 44.2 / 1.07 | 46.3 / 1.12 | 47.9 / 1.16 | 48.8 / 1.18 | none reaches 1.5 | - |
| fluidanimate | 44.7, 0.0005 | yes | 45.7 / 1.02 | 45.9 / 1.03 | 46.1 / 1.03 | 46.5 / 1.04 | 48.9 / 1.10 | none reaches 1.5 | - |
| swaptions | 41.6, 0.0019 | yes | 42.0 / 1.01 | 42.3 / 1.02 | 42.1 / 1.01 | 42.2 / 1.02 | 42.4 / 1.02 | none reaches 1.5 | - |
| ferret | 40.5, 0.0013 | yes | 40.8 / 1.01 | 40.9 / 1.01 | 45.2 / 1.12 | 50.5 / 1.25 | 52.7 / 1.30 | none reaches 1.5 | - |
| vips | 55.0, 0.0027 | yes | 50.6 / 0.92 | 50.1 / 0.91 | 51.4 / 0.93 | 52.6 / 0.96 | 55.8 / 1.02 | none reaches 1.5 | - |
| x264 | 45.9, 0.0035 | yes | 46.2 / 1.01 | 49.4 / 1.08 | 64.5 / 1.41 | 88.0 / 1.92 | 154.0 / 3.36 | 16 | 0.0041 |

**Traces with a chosen S: 1 of 9.** Runs at S = 1 equal to round 25: 9 of 9.
