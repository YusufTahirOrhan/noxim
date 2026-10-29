# v15 check: single trace, s = 1, reproduces v13 (DeFT(rho*), seed 41, fault-free)

**9 / 9 identical** (mean latency, p99, completion cycle, delivered packets).

| benchmark | latency v13 / v15 | completion v13 / v15 | result |
|---|---|---|---|
| blackscholes | 30.377337 / 30.377337 | 700009 / 700009 | identical |
| bodytrack | 10.106796 / 10.106796 | 695331 / 695331 | identical |
| canneal | 48.918586 / 48.918586 | 694792 / 694792 | identical |
| dedup | 22.609002 / 22.609002 | 699771 / 699771 | identical |
| fluidanimate | 22.705783 / 22.705783 | 697836 / 697836 | identical |
| swaptions | 20.651183 / 20.651183 | 702110 / 702110 | identical |
| ferret | 20.571692 / 20.571692 | 700080 / 700080 | identical |
| vips | 37.838535 / 37.838535 | 698555 / 698555 | identical |
| x264 | 28.359901 / 28.359901 | 699969 / 699969 | identical |
