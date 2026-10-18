# Decisions taken without the author (v3)

## Step 1: reproducibility
1. **eval_runs.csv is a new file in results_v2/** (requested explicitly); no existing v1/v2
   file was modified. Floats are written with repr() so the CSV round-trips the JSON exactly.
   For DeFT and DeFT_tm the VL imbalance comes from the traffic-identical proxy runs
   (column vl_source = proxy; identity re-checked on all 1540 rows).
2. **The re-analysis (primary_from_csv.py) is an independent implementation** that reads only
   the CSV. The load ladder and the 2nd rate per scenario come from the CSV itself. It does
   not import report_v2.py, so a bug shared between the two would have to be written twice.
