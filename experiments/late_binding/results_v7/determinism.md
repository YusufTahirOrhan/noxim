# Determinism check (v7 step 1)

Twenty v6 evaluation runs (seeds 31-40; DeFT_tm(rho*), CI_heurLA, CI_qlLA with the v6 tuned parameters; 3x3 and 4x4; scenarios, loads and seeds spread by a fixed rule) re-run with the v7 binary (entry_bound_mode off) and compared field by field (repr of the JSON values) with results_v6/eval_runs.csv: accepted throughput, mean latency, p99, injected, received, dead ends.

**20 / 20 identical.**

| size | variant | scenario | rate | seed | latency v6 / v7 | accepted v6 / v7 | result |
|---|---|---|---|---|---|---|---|
| 3x3 | DeFT_tm | uniform 0x0 | 0.0015 | 31 | 27.54946 / 27.54946 | 0.011781 / 0.011781 | identical |
| 4x4 | DeFT_tm | localized 0x0 | 0.01 | 32 | 58.35367 / 58.35367 | 0.080677 / 0.080677 | identical |
| 3x3 | CI_heurLA | hotspot 0x0 | 0.0056 | 33 | 1124.471 / 1124.471 | 0.033159 / 0.033159 | identical |
| 4x4 | CI_heurLA | chipperm 0x0 | 0.0024 | 34 | 56.82804 / 56.82804 | 0.019441 / 0.019441 | identical |
| 3x3 | CI_qlLA | movinghot 0x0 | 0.0049 | 35 | 539.7306 / 539.7306 | 0.038177 / 0.038177 | identical |
| 4x4 | CI_qlLA | uniform 0x1111111111111111 | 0.0025 | 36 | 37.57895 / 37.57895 | 0.020078 / 0.020078 | identical |
| 3x3 | DeFT_tm | hotspot 0x111111111 | 0.0042 | 37 | 417.7251 / 417.7251 | 0.030428 / 0.030428 | identical |
| 4x4 | DeFT_tm | uniform 0x0 | 0.0015 | 38 | 34.01817 / 34.01817 | 0.012032 / 0.012032 | identical |
| 3x3 | CI_heurLA | localized 0x0 | 0.0115 | 39 | 41.08485 / 41.08485 | 0.093383 / 0.093383 | identical |
| 4x4 | CI_heurLA | hotspot 0x0 | 0.0034 | 40 | 814.3821 / 814.3821 | 0.017463 / 0.017463 | identical |
| 3x3 | CI_qlLA | chipperm 0x0 | 0.005 | 31 | 51.84790 / 51.84790 | 0.039740 / 0.039740 | identical |
| 4x4 | CI_qlLA | movinghot 0x0 | 0.0031 | 32 | 795.7169 / 795.7169 | 0.022714 / 0.022714 | identical |
| 3x3 | DeFT_tm | uniform 0x111111111 | 0.003 | 33 | 33.35984 / 33.35984 | 0.023653 / 0.023653 | identical |
| 4x4 | DeFT_tm | hotspot 0x1111111111111111 | 0.0024 | 34 | 217.3786 / 217.3786 | 0.017176 / 0.017176 | identical |
| 3x3 | CI_heurLA | uniform 0x0 | 0.0015 | 35 | 25.88525 / 25.88525 | 0.012118 / 0.012118 | identical |
| 4x4 | CI_heurLA | localized 0x0 | 0.01 | 36 | 46.27133 / 46.27133 | 0.080112 / 0.080112 | identical |
| 3x3 | CI_qlLA | hotspot 0x0 | 0.0056 | 37 | 1166.076 / 1166.076 | 0.033039 / 0.033039 | identical |
| 4x4 | CI_qlLA | chipperm 0x0 | 0.0024 | 38 | 54.48845 / 54.48845 | 0.019125 / 0.019125 | identical |
| 3x3 | DeFT_tm | movinghot 0x0 | 0.0049 | 39 | 462.1512 / 462.1512 | 0.038026 / 0.038026 | identical |
| 4x4 | DeFT_tm | uniform 0x1111111111111111 | 0.0025 | 40 | 39.18691 / 39.18691 | 0.019587 / 0.019587 | identical |
