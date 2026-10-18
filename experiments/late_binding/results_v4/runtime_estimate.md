# Run-time estimate v4 (experiments_v4.py timing)

Timing test: 252 runs (seed 1001, not used elsewhere; every variant x size x scenario at the 2nd,
4th and 7th load), 10 processes: 1381 s wall, 5.48 s per run (weighted towards saturation).

Full evaluation: 5880 runs (6 variants x 2 sizes x 7 scenarios x 7 loads x 10 seeds) plus 280 VL-proxy runs: estimated 9.4 h wall.
Rule (instructions): over 12 h -> seeds 1-5 first. Estimate is within 12 h.
