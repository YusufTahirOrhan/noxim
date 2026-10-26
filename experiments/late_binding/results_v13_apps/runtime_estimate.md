# Run-time estimate and trace window (v13)

Timing test: first 200000 packets of region 2 of each benchmark, DeFT(rho*) and FULL_qlLA_G, seed 1001, 12 processes: 7897 s wall; 515.10 cpu-us per simulated cycle.

Rule: the largest window N (packets, multiple of 100000, at most 3000000) whose estimated total time (486 runs) is <= 8 h.

**Window: the first 100000 packets of region 2** (estimated 34.9 h).

| benchmark | window cycles | completion cycles in the test (mean of 2 methods) |
|---|---|---|
| blackscholes_64c_simsmall | 3089021 | 6055013 |
| bodytrack_64c_simlarge | 11156397 | 14556541 |
| canneal_64c_simmedium | 6869427 | 8022724 |
| dedup_64c_simmedium | 6917575 | 10290506 |
| fluidanimate_64c_simsmall | 6879106 | 9683172 |
| swaptions_64c_simlarge | 4648042 | 6675272 |
| ferret_64c_simmedium | 4327753 | 8479059 |
| vips_64c_simmedium | 6627787 | 18208693 |
| x264_64c_simsmall | 3604752 | 10012410 |
