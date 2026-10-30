# v16 reuse check: ql_bits 0 reproduces v9 (random.Random(1016), 20 runs of CI_qlLA_G / FULL_qlLA_G)

**20 / 20 identical** (latency, accepted, p99).

| variant | scenario | rate | seed | result |
|---|---|---|---|---|
| CI_qlLA_G | 4x4-localized 0x0 | 0.008 | 45 | identical |
| FULL_qlLA_G | 3x3-uniform 0x111111111 | 0.007 | 49 | identical |
| CI_qlLA_G | 4x4-movinghot 0x0 | 0.0031 | 50 | identical |
| FULL_qlLA_G | 2x2-localized 0x0000 | 0.0215 | 46 | identical |
| CI_qlLA_G | 4x4-hotspot 0x1111111111111111 | 0.0016 | 49 | identical |
| FULL_qlLA_G | 3x3-uniform 0x111111111 | 0.0095 | 48 | identical |
| FULL_qlLA_G | 2x2-movinghot 0x0000 | 0.01 | 45 | identical |
| CI_qlLA_G | 2x2-uniform 0x9C63 | 0.001 | 41 | identical |
| FULL_qlLA_G | 3x3-hotspot 0x0 | 0.0042 | 45 | identical |
| FULL_qlLA_G | 3x3-hotspot 0x111111111 | 0.0042 | 42 | identical |
| FULL_qlLA_G | 3x3-hotspot 0x111111111 | 0.0018 | 48 | identical |
| CI_qlLA_G | 2x2-hotspot 0x0000 | 0.0105 | 42 | identical |
| CI_qlLA_G | 4x4-hotspot 0x1111111111111111 | 0.0016 | 48 | identical |
| FULL_qlLA_G | 2x2-hotspot 0x0000 | 0.0105 | 49 | identical |
| CI_qlLA_G | 2x2-chipperm 0x9C63 | 0.0007 | 44 | identical |
| FULL_qlLA_G | 2x2-chipperm 0x9C63 | 0.0027 | 50 | identical |
| FULL_qlLA_G | 2x2-hotspot 0x9C63 | 0.0075 | 45 | identical |
| FULL_qlLA_G | 4x4-hotspot 0x0 | 0.0025 | 41 | identical |
| FULL_qlLA_G | 2x2-chipperm 0x9C63 | 0.0054 | 46 | identical |
| FULL_qlLA_G | 2x2-uniform 0x1111 | 0.009 | 43 | identical |
