# v20: the decision delay at very low load

Uniform, fault-free, rate 0.0002, seed 1001 (not an evaluation seed). A head waits exactly N extra cycles on a multi-output hop when nothing else holds it, so latency(N) - latency(0) should be N x h, with h = multi-output hops per received packet.

| size | variant | h (N = 1) | latency N = 0 | N = 1: rise / N x h | N = 2: rise / N x h | N = 4: rise / N x h |
|---|---|---|---|---|---|---|
| 2x2 | CI_heurLA_G | 3.21 | 16.95 | 4.05 / 3.21 | 8.18 / 6.85 | 10.52 / 11.19 |
| 2x2 | CI_qlLA_G | 3.04 | 17.17 | 3.30 / 3.04 | 5.54 / 5.83 | 11.11 / 12.00 |
| 2x2 | FULL_qlLA_G | 4.31 | 17.47 | 4.34 / 4.31 | 7.21 / 8.27 | 16.79 / 17.43 |
| 3x3 | CI_heurLA_G | 5.31 | 23.35 | 6.06 / 5.31 | 9.98 / 10.05 | 21.40 / 21.13 |
| 3x3 | CI_qlLA_G | 4.74 | 24.66 | 3.00 / 4.74 | 10.96 / 10.95 | 20.64 / 21.37 |
| 3x3 | FULL_qlLA_G | 6.02 | 23.54 | 5.50 / 6.02 | 11.43 / 12.28 | 26.31 / 26.05 |
| 4x4 | CI_heurLA_G | 7.08 | 30.00 | 7.12 / 7.08 | 13.95 / 14.09 | 27.54 / 28.15 |
| 4x4 | CI_qlLA_G | 7.48 | 29.45 | 8.86 / 7.48 | 14.84 / 14.24 | 27.93 / 28.28 |
| 4x4 | FULL_qlLA_G | 8.13 | 28.50 | 8.58 / 8.13 | 15.95 / 15.85 | 32.79 / 32.02 |

Largest relative difference between the rise and N x h: 36.8 %. Each run has only about 100 packets, and the chosen paths change with N (h is measured per N), so single cells are noisy; the agreement is closest at N = 4, where the rise is largest.
