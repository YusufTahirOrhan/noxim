# Run-time estimate v11 (Part C)

Timing test: 432 runs (seed 1001; every method x size x k (first mask) x pattern at the 2nd, 4th and 7th load), 12 processes: 1842 s wall, 4.26 s per run; 0 missing.

Full design with 5 masks per (size, k): 10080 runs, estimated **11.9 h** on one machine. Rule: over 16 h -> 3 masks per (size, k). **Masks per (size, k): 5.**
