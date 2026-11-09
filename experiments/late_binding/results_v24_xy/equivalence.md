# B4: Q-learning with alpha = 0 against the heuristic under lookahead (experiments_v24.py equiv)

CI with XY on the interposer (relation X), uniform fault-free, pipe_all 2, both with `lookahead_route 1 lookahead_fallback 1 busy_state 1 decision_delay 1`;
five runs per size (loads 0.5, 1.0, 1.4, 2.0 and 2.4 x Lsat of the v23 pipe_all 2 ladder, seeds 1-5), each with its own (w, beta, gamma, D).
Compared: the whole `summary` block and every field of `deft_lb` except the selection's name and parameters (`selection_strategy`, `heur_*`, `ql_*`).

| size | rate | seed | w, beta, gamma, D | accepted heuristic / alpha 0 | latency heuristic / alpha 0 | fallbacks taken heuristic / alpha 0 | identical |
|---|---|---|---|---|---|---|---|
| 2x2 | 0.0065 | 1 | 1, 4, 2, 4 | 0.049846 / 0.049846 | 43.4644 / 43.4644 | 179 / 179 | yes |
| 2x2 | 0.0130 | 2 | 2, 0, 1, 0 | 0.105260 / 0.105260 | 68.8992 / 68.8992 | 937 / 937 | yes |
| 2x2 | 0.0180 | 3 | 2, 4, 2, 2 | 0.127996 / 0.127996 | 638.7880 / 638.7880 | 2360 / 2360 | yes |
| 2x2 | 0.0260 | 4 | 1, 0, 1, 4 | 0.128576 / 0.128576 | 2140.8735 / 2140.8735 | 3272 / 3272 | yes |
| 2x2 | 0.0310 | 5 | 1, 4, 2, 0 | 0.124928 / 0.124928 | 2838.8022 / 2838.8022 | 2687 / 2687 | yes |
| 4x4 | 0.0040 | 1 | 1, 4, 2, 4 | 0.031462 / 0.031462 | 68.8773 / 68.8773 | 644 / 644 | yes |
| 4x4 | 0.0080 | 2 | 2, 0, 1, 0 | 0.063822 / 0.063822 | 93.7138 / 93.7138 | 3301 / 3301 | yes |
| 4x4 | 0.0110 | 3 | 2, 4, 2, 2 | 0.081794 / 0.081794 | 496.9849 / 496.9849 | 7345 / 7345 | yes |
| 4x4 | 0.0160 | 4 | 1, 0, 1, 4 | 0.081130 / 0.081130 | 1967.3134 / 1967.3134 | 10404 / 10404 | yes |
| 4x4 | 0.0190 | 5 | 1, 4, 2, 0 | 0.081799 / 0.081799 | 2523.9215 / 2523.9215 | 9059 / 9059 | yes |

**10 / 10 pairs identical.**
