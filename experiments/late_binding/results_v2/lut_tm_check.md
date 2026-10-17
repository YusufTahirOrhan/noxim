# Traffic-matched LUT checks (check_lut_tm.py)

1. default generation identical to luts/lut_rho001.yaml: True
2. uniform demand table: 1 differing line(s), same length: True: `traffic_assumption: uniform_unit_interchiplet_demand` -> `traffic_assumption: demand_matrix_from_traffic_table_time_averaged`

3. Selected-VL lines (exit and entry, 11 masks) differing from the uniform LUT:
   - localized: 0 of 4224
   - hotspot: 53 of 4224
   - chipperm: 1050 of 4224
   - movinghot: 0 of 4224

4. Sanity runs (tuning seeds), mean latency / accepted throughput:

| run | DeFT latency | DeFT_tm latency | DeFT accepted | DeFT_tm accepted |
|---|---|---|---|---|
| chipperm__0x0000__0.0050__s101 | 117.3 | 37.6 | 0.0392 | 0.0388 |
| chipperm__0x0000__0.0050__s102 | 147.6 | 39.2 | 0.0403 | 0.0414 |
| chipperm__0x9C63__0.0040__s101 | 353.8 | 48.2 | 0.0303 | 0.0318 |
| chipperm__0x9C63__0.0040__s102 | 336.9 | 48.6 | 0.0296 | 0.0328 |
| hotspot__0x0000__0.0080__s101 | 67.5 | 67.5 | 0.0633 | 0.0633 |
| hotspot__0x0000__0.0080__s102 | 80.8 | 80.8 | 0.0640 | 0.0640 |
| hotspot__0x9C63__0.0060__s101 | 104.0 | 78.8 | 0.0487 | 0.0492 |
| hotspot__0x9C63__0.0060__s102 | 73.8 | 133.5 | 0.0483 | 0.0491 |
