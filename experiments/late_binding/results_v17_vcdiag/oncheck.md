# v17: statistics option on vs off (experiments_v17.py oncheck)

**5 / 5 stats files byte-identical** (latency statistics included; the VC counters go to their own file). Load 1.0 x Lsat, seed 41.

| method | size | pattern | mean latency | p99 | flits counted on links | stats file on vs off |
|---|---|---|---|---|---|---|
| DeFT | 2x2 | uniform | 52.646 | 226.0 | 394404 | identical |
| MTR | 3x3 | uniform | 65.854 | 238.0 | 925883 | identical |
| RC | 4x4 | hotspot | 279.661 | 3940.0 | 375637 | identical |
| CI_qlLA_G | 2x2 | hotspot | 37.736 | 193.0 | 253804 | identical |
| FULL_qlLA_G | 3x3 | uniform | 51.456 | 144.0 | 940113 | identical |
