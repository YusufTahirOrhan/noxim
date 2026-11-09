# A2: VC split per link class with the paper's rules (experiments_v23.py vcsplit)

Uniform, 1.0 x Lsat of the K4 ladders (load_points_rr.json), seeds 41-43, v17 statistics. Each cell: share of flits VC0:VC1 (%), then VC-wait cycles per flit. DeFT_old = the v19-v21 reference (-deft_vn_rr 1 only).

| size | method | chiplet, towards VL | chiplet, away from VL | interposer | Down VL | Up VL | latency |
|---|---|---|---|---|---|---|---|
| 2x2 | DeFT_P | 88:12 / 0.08 | 22:78 / 0.15 | 50:50 / 0.16 | 50:50 / 0.38 | 50:50 / 0.38 | 44.0 |
| 2x2 | DeFT_B | 67:33 / 0.11 | 11:89 / 0.26 | 50:50 / 0.17 | 50:50 / 0.47 | 50:50 / 0.24 | 50.8 |
| 2x2 | DeFT_old | 67:33 / 0.14 | 11:89 / 0.08 | 50:50 / 0.22 | 50:50 / 0.66 | 0:100 / 1.21 | 58.1 |
| 4x4 | DeFT_P | 97:3 / 0.06 | 7:93 / 0.14 | 50:50 / 0.16 | 50:50 / 0.24 | 50:50 / 0.27 | 65.3 |
| 4x4 | DeFT_B | 70:30 / 0.08 | 3:97 / 0.17 | 50:50 / 0.19 | 50:50 / 0.31 | 50:50 / 0.21 | 71.1 |
| 4x4 | DeFT_old | 70:30 / 0.07 | 3:97 / 0.04 | 50:50 / 0.20 | 50:50 / 0.43 | 0:100 / 0.85 | 75.9 |
