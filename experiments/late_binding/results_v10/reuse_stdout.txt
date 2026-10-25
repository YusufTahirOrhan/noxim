# v9 reuse check (v10 A5)

20 runs drawn at random (Python random.Random(1010).sample) from the v9 evaluation runs of DeFT(rho*), CI_heurLA_G, CI_qlLA_G and FULL_qlLA_G, re-run with the v10 binary and compared field by field (repr of the JSON values) with results_v9/eval_runs.csv: accepted, latency, p99, injected, received, dead ends.

**20 / 20 identical.**

| variant | scenario | rate | seed | latency v9 / v10 | accepted v9 / v10 | result |
|---|---|---|---|---|---|---|
| FULL_qlLA_G | 2x2-hotspot 0x0000 | 0.0075 | 47 | 43.725325 / 43.725325 | 0.0613222 / 0.0613222 | identical |
| DeFT | 4x4-hotspot 0x1111111111111111 | 0.0024 | 48 | 423.04350 / 423.04350 | 0.0166987 / 0.0166987 | identical |
| FULL_qlLA_G | 4x4-localized 0x0 | 0.005 | 50 | 26.160222 / 26.160222 | 0.0393129 / 0.0393129 | identical |
| CI_qlLA_G | 2x2-hotspot 0x0000 | 0.012 | 44 | 1151.7452 / 1151.7452 | 0.0727441 / 0.0727441 | identical |
| DeFT | 3x3-hotspot 0x0 | 0.0035 | 48 | 50.281818 / 50.281818 | 0.0282612 / 0.0282612 | identical |
| CI_heurLA_G | 2x2-uniform 0x1111 | 0.0125 | 42 | 584.18285 / 584.18285 | 0.0874902 / 0.0874902 | identical |
| CI_qlLA_G | 4x4-uniform 0x0 | 0.0015 | 45 | 32.010599 / 32.010599 | 0.0117954 / 0.0117954 | identical |
| DeFT | 2x2-chipperm 0x0000 | 0.0065 | 48 | 380.39095 / 380.39095 | 0.0462675 / 0.0462675 | identical |
| CI_qlLA_G | 4x4-uniform 0x0 | 0.003 | 47 | 37.671414 / 37.671414 | 0.0244077 / 0.0244077 | identical |
| CI_heurLA_G | 4x4-hotspot 0x0 | 0.001 | 47 | 33.319369 / 33.319369 | 0.0079194 / 0.0079194 | identical |
| CI_heurLA_G | 3x3-uniform 0x0 | 0.01 | 48 | 114.03623 / 114.03623 | 0.0789791 / 0.0789791 | identical |
| DeFT | 2x2-chipperm 0x1111 | 0.001 | 48 | 30.500904 / 30.500904 | 0.0086425 / 0.0086425 | identical |
| FULL_qlLA_G | 2x2-uniform 0x9C63 | 0.0045 | 41 | 31.226928 / 31.226928 | 0.0350312 / 0.0350312 | identical |
| CI_heurLA_G | 4x4-uniform 0x0 | 0.0105 | 44 | 1655.4998 / 1655.4998 | 0.0550375 / 0.0550375 | identical |
| CI_heurLA_G | 3x3-hotspot 0x0 | 0.0035 | 46 | 47.443700 / 47.443700 | 0.0280329 / 0.0280329 | identical |
| FULL_qlLA_G | 4x4-movinghot 0x0 | 0.0026 | 42 | 119.08670 / 119.08670 | 0.0206005 / 0.0206005 | identical |
| FULL_qlLA_G | 2x2-uniform 0x9C63 | 0.0055 | 45 | 37.592736 / 37.592736 | 0.0443222 / 0.0443222 | identical |
| DeFT | 2x2-uniform 0x1111 | 0.011 | 48 | 297.74659 / 297.74659 | 0.0838203 / 0.0838203 | identical |
| FULL_qlLA_G | 2x2-chipperm 0x0000 | 0.0035 | 43 | 34.954994 / 34.954994 | 0.0284746 / 0.0284746 | identical |
| DeFT | 2x2-uniform 0x1111 | 0.0045 | 41 | 27.238812 / 27.238812 | 0.0352539 / 0.0352539 | identical |
