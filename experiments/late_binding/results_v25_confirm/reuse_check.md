# A5: the rows of this round reproduce the v24 runs (experiments_v25.py reuse)

Three evaluation runs of round 24 per row (the four frozen rows and DeFT_P, DeFT_B, MTR, RC; drawn with `random.Random(2511).sample` from
`results_v24_xy/eval_runs.csv`, seeds 111-115) were run again with `bin/noxim` and the row definitions of this round (`experiments_v25.row_args`) and compared
field by field (repr of the JSON values): accepted, latency, p99, injected, received, dead ends and the hop and lookahead counters.

**24 / 24 identical.**

| row | scenario | rate | seed | latency v24 / now | accepted v24 / now | result |
|---|---|---|---|---|---|---|
| CI_heurLA_X_LF-p2 | 3x3-uniform 0x111111111 | 0.0015 | 115 | 51.8527889 / 51.8527889 | 0.0120807 / 0.0120807 | identical |
| CI_heurLA_X_LF-p2 | 4x4-uniform 0x0 | 0.0015 | 115 | 60.7192866 / 60.7192866 | 0.0118291 / 0.0118291 | identical |
| CI_heurLA_X_LF-p2 | 2x2-uniform 0x1111 | 0.014 | 112 | 639.448732 / 639.448732 | 0.0991718 / 0.0991718 | identical |
| CI_heurLA_O_LF-p2 | 4x4-chiptrans 0x0 | 0.0103 | 113 | 430.326745 / 430.326745 | 0.0766772 / 0.0766772 | identical |
| CI_heurLA_O_LF-p2 | 2x2-uniform 0x0000 | 0.0025 | 111 | 36.8502340 / 36.8502340 | 0.0200488 / 0.0200488 | identical |
| CI_heurLA_O_LF-p2 | 2x2-hotspot 0x0000 | 0.009 | 112 | 175.328254 / 175.328254 | 0.0717011 / 0.0717011 | identical |
| CI_heurLA_X_DLY-p2 | 3x3-chipperm 0x0 | 0.0105 | 114 | 123.207084 / 123.207084 | 0.0843125 / 0.0843125 | identical |
| CI_heurLA_X_DLY-p2 | 4x4-chiptrans 0x0 | 0.0052 | 115 | 261.817342 / 261.817342 | 0.0401845 / 0.0401845 | identical |
| CI_heurLA_X_DLY-p2 | 2x2-hotspot 0x0000 | 0.006 | 114 | 48.6874391 / 48.6874391 | 0.0481855 / 0.0481855 | identical |
| CI_qlLA_X_LF-p2 | 4x4-chipperm 0x0 | 0.012 | 111 | 2335.85761 / 2335.85761 | 0.0567060 / 0.0567060 | identical |
| CI_qlLA_X_LF-p2 | 2x2-chiptrans 0x0000 | 0.0275 | 114 | 1003.38267 / 1003.38267 | 0.1639785 / 0.1639785 | identical |
| CI_qlLA_X_LF-p2 | 2x2-chipperm 0x0000 | 0.014 | 115 | 325.856452 / 325.856452 | 0.1099355 / 0.1099355 | identical |
| DeFT_P-p2 | 4x4-chipperm 0x0 | 0.0095 | 112 | 1780.30822 / 1780.30822 | 0.0520312 / 0.0520312 | identical |
| DeFT_P-p2 | 4x4-chiptrans 0x0 | 0.0103 | 114 | 1236.88216 / 1236.88216 | 0.0560473 / 0.0560473 | identical |
| DeFT_P-p2 | 2x2-chipperm 0x0000 | 0.0275 | 113 | 3187.01633 / 3187.01633 | 0.0994414 / 0.0994414 | identical |
| DeFT_B-p2 | 4x4-chiptrans 0x0 | 0.0052 | 113 | 1080.87401 / 1080.87401 | 0.0291015 / 0.0291015 | identical |
| DeFT_B-p2 | 2x2-hotspot 0x0000 | 0.009 | 112 | 297.836808 / 297.836808 | 0.0689414 / 0.0689414 | identical |
| DeFT_B-p2 | 4x4-chipperm 0x0 | 0.005 | 112 | 1124.31227 / 1124.31227 | 0.0266000 / 0.0266000 | identical |
| MTR-p2 | 3x3-chiptrans 0x0 | 0.009 | 111 | 560.479251 / 560.479251 | 0.0627369 / 0.0627369 | identical |
| MTR-p2 | 2x2-chipperm 0x0000 | 0.014 | 114 | 620.478519 / 620.478519 | 0.0996269 / 0.0996269 | identical |
| MTR-p2 | 4x4-chipperm 0x0 | 0.006 | 115 | 187.763050 / 187.763050 | 0.0480390 / 0.0480390 | identical |
| RC-p2 | 4x4-chiptrans 0x0 | 0.0103 | 115 | 1232.80043 / 1232.80043 | 0.0557875 / 0.0557875 | identical |
| RC-p2 | 3x3-uniform 0x0 | 0.012 | 113 | 435.820241 / 435.820241 | 0.0907039 / 0.0907039 | identical |
| RC-p2 | 3x3-uniform 0x0 | 0.024 | 115 | 2995.78061 / 2995.78061 | 0.0903246 / 0.0903246 | identical |
