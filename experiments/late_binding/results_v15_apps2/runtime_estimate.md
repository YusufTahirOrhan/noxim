# Run-time estimate v15 and choice of s

Timing test: 24 runs (seed 1001, DeFT(rho*) and FULL_qlLA_G, every pair, s = 1 and 2, fault-free), 12 processes: 768 s wall; 633 cpu-us per simulated cycle.

Estimate for the 324 runs per s: s = 1 3.3 h, s = 2 2.4 h, both 5.8 h. Rule: both if <= 8 h, else s = 1 only. **s: 1, 2.**
