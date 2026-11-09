# Load points of v24 (experiments_v24.py sat, points)

New in this round: the pattern `chiptrans` (chiplet (cx, cy) sends to chiplet (cy, cx); a chiplet on the diagonal to its own other routers). Its ladders follow the
v23 D1 rule: DeFT-P (-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), seed 101, pipe_all 2; L0 = latency at 0.0002;
Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse (0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid
otherwise; 9 loads at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat. The other scenarios keep their v23 ladders (`results_v23_fidelity/load_points_v23.json`,
copied unchanged into `load_points_v24.json`). All runs of this round use the pipe_all = 2 ladders.

| size | scenario | source | grid | L0 | Lsat | lat / L0 at Lsat | ladder (pipe_all 2) |
|---|---|---|---|---|---|---|---|
| 2x2 | uniform 0x0000 | v23 | 0.0005 | 35.3 | 0.013 | (v23) | [0.0025, 0.0065, 0.0105, 0.013, 0.0155, 0.018, 0.021, 0.026, 0.031] |
| 2x2 | hotspot 0x0000 | v23 | 0.0005 | 36.5 | 0.0075 | (v23) | [0.0015, 0.004, 0.006, 0.0075, 0.009, 0.0105, 0.012, 0.015, 0.018] |
| 2x2 | chipperm 0x0000 | v23 | 0.0005 | 49.4 | 0.0115 | (v23) | [0.0025, 0.006, 0.009, 0.0115, 0.014, 0.016, 0.0185, 0.023, 0.0275] |
| 2x2 | chiptrans 0x0000 | v24 | 0.0005 | 32.0 | 0.0115 | 2.63 | [0.0025, 0.006, 0.009, 0.0115, 0.014, 0.016, 0.0185, 0.023, 0.0275] |
| 2x2 | uniform 0x1111 | v23 | 0.0005 | 37.9 | 0.01 | (v23) | [0.002, 0.005, 0.008, 0.01, 0.012, 0.014, 0.016, 0.02, 0.024] |
| 3x3 | uniform 0x0 | v23 | 0.0005 | 48.5 | 0.01 | (v23) | [0.002, 0.005, 0.008, 0.01, 0.012, 0.014, 0.016, 0.02, 0.024] |
| 3x3 | hotspot 0x0 | v23 | 0.0001 | 49.3 | 0.0031 | (v23) | [0.0006, 0.0015, 0.0025, 0.0031, 0.0037, 0.0043, 0.005, 0.0062, 0.0074] |
| 3x3 | chipperm 0x0 | v23 | 0.0005 | 60.7 | 0.0075 | (v23) | [0.0015, 0.004, 0.006, 0.0075, 0.009, 0.0105, 0.012, 0.015, 0.018] |
| 3x3 | chiptrans 0x0 | v24 | 0.0005 | 44.3 | 0.0055 | 1.81 | [0.001, 0.003, 0.0045, 0.0055, 0.0065, 0.0075, 0.009, 0.011, 0.013] |
| 3x3 | uniform 0x111111111 | v23 | 0.0005 | 52.9 | 0.007 | (v23) | [0.0015, 0.0035, 0.0055, 0.007, 0.0085, 0.01, 0.011, 0.014, 0.017] |
| 4x4 | uniform 0x0 | v23 | 0.0005 | 61.5 | 0.008 | (v23) | [0.0015, 0.004, 0.0065, 0.008, 0.0095, 0.011, 0.013, 0.016, 0.019] |
| 4x4 | hotspot 0x0 | v23 | 0.0001 | 62.3 | 0.0016 | (v23) | [0.0003, 0.0008, 0.0013, 0.0016, 0.0019, 0.0022, 0.0026, 0.0032, 0.0038] |
| 4x4 | chipperm 0x0 | v23 | 0.0005 | 82.8 | 0.006 | (v23) | [0.001, 0.003, 0.005, 0.006, 0.007, 0.0085, 0.0095, 0.012, 0.0145] |
| 4x4 | chiptrans 0x0 | v24 | 0.0001 | 57.0 | 0.0043 | 2.87 | [0.0009, 0.0022, 0.0034, 0.0043, 0.0052, 0.006, 0.0069, 0.0086, 0.0103] |
| 4x4 | uniform 0x1111111111111111 | v23 | 0.0005 | 65.6 | 0.006 | (v23) | [0.001, 0.003, 0.005, 0.006, 0.007, 0.0085, 0.0095, 0.012, 0.0145] |
