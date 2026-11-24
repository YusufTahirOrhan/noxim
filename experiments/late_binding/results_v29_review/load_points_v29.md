# Load points of v29 (experiments_v29.py b_sat, b_points)

The three scenarios that no earlier round ran (tornado, neighbour, randperm, fault-free) get their ladders by the D1 rule of round 23 as round 25 ran it
(`results_v25_confirm/load_points_v25.md`): DeFT-P (`-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1`), seed 101,
pipe_all 2; L0 = latency at 0.0002; Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse
(0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid otherwise; 9 loads at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat. The coarse sweep ends at
0.016, 0.018, 0.020, 0.024 as in every round; a scenario that is not saturated at 0.024 is swept further in steps of 0.004 (0.028, 0.032, ...) until it is.
The six scenarios of round 25 keep their ladders (`results_v25_confirm/load_points_v25.json`).

| size | scenario | grid | L0 | Lsat | lat / L0 at Lsat | first rate above 3 x L0 | ladder (pipe_all 2) |
|---|---|---|---|---|---|---|---|
| 2x2 | tornado | 0.0005 | 32.1 | 0.013 | 2.98 | 0.0135 | [0.0025, 0.0065, 0.0105, 0.013, 0.0155, 0.018, 0.021, 0.026, 0.031] |
| 2x2 | neighbour | 0.0005 | 39.3 | 0.0105 | 2.65 | 0.011 | [0.002, 0.005, 0.0085, 0.0105, 0.0125, 0.0145, 0.017, 0.021, 0.025] |
| 2x2 | randperm | 0.0005 | 38.5 | 0.0125 | 2.37 | 0.013 | [0.0025, 0.006, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.025, 0.03] |
| 3x3 | tornado | 0.0005 | 44.5 | 0.0085 | 2.59 | 0.009 | [0.0015, 0.004, 0.007, 0.0085, 0.01, 0.012, 0.0135, 0.017, 0.0205] |
| 3x3 | neighbour | 0.0005 | 37.9 | 0.0085 | 2.34 | 0.009 | [0.0015, 0.004, 0.007, 0.0085, 0.01, 0.012, 0.0135, 0.017, 0.0205] |
| 3x3 | randperm | 0.0005 | 49.6 | 0.009 | 2.58 | 0.0095 | [0.002, 0.0045, 0.007, 0.009, 0.011, 0.0125, 0.0145, 0.018, 0.0215] |
| 4x4 | tornado | 0.0005 | 52.4 | 0.007 | 2.42 | 0.0075 | [0.0015, 0.0035, 0.0055, 0.007, 0.0085, 0.01, 0.011, 0.014, 0.017] |
| 4x4 | neighbour | 0.0005 | 39.9 | 0.0095 | 2.75 | 0.01 | [0.002, 0.005, 0.0075, 0.0095, 0.0115, 0.0135, 0.015, 0.019, 0.023] |
| 4x4 | randperm | 0.0005 | 57.8 | 0.0075 | 2.70 | 0.008 | [0.0015, 0.004, 0.006, 0.0075, 0.009, 0.0105, 0.012, 0.015, 0.018] |
