# Decisions taken without the author (v3)

## Step 1: reproducibility
1. **eval_runs.csv is a new file in results_v2/** (requested explicitly); no existing v1/v2
   file was modified. Floats are written with repr() so the CSV round-trips the JSON exactly.
   For DeFT and DeFT_tm the VL imbalance comes from the traffic-identical proxy runs
   (column vl_source = proxy; identity re-checked on all 1540 rows).
2. **The re-analysis (primary_from_csv.py) is an independent implementation** that reads only
   the CSV. The load ladder and the 2nd rate per scenario come from the CSV itself. It does
   not import report_v2.py, so a bug shared between the two would have to be written twice.

## Steps 2-3: confirmatory design
3. **The loads are the v2 rates themselves** (3rd-5th entries of results_v2/load_points.json:
   0.8, 1.0, 1.2 x Lsat snapped to the 0.0005 grid), not new values, so v2 and v3 measure
   the same operating points.
4. **The v2 estimates in the pre-registration** were computed with the same statistic on
   seeds 1-10 before any v3 run; they are context, not part of the test.
5. **"Saturation throughput" (secondary) is the max accepted throughput over the three v3
   loads**, labelled as such and reported with its capped-cell count. With loads only up to
   1.2 x Lsat, the v2 metric (up to 1.6 x) is not available.
6. **Window runs** use -sim 42000 -warmup 2000 (40000 measured cycles). The 8000-cycle
   comparison uses the same seeds (11-15) from the confirmatory runs.
7. **v3 per-run CSVs** (confirm_runs.csv, window_runs.csv) have no VL counts for DeFT_tm,
   because no proxy runs were made: VL imbalance is not a v3 metric.
