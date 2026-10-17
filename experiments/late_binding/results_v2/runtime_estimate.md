# Run-time estimate (experiments_v2.py timing)

Timing test: 363 runs (seed 1001, not used elsewhere; every variant x scenario at the
2nd, 4th and 7th load), 11 parallel processes: 358 s wall, 0.99 s per run.
The loads are weighted towards saturation (the slow end), so the estimate leans high.

Full evaluation: 8470 runs (11 variants x 11 scenarios x 7 loads x 10 seeds) plus
1540 VL-count proxy runs: estimated 2.7 h wall.
Decision rule (instructions): over 10 h -> seeds 1-5 first. Estimate is within 10 h.
