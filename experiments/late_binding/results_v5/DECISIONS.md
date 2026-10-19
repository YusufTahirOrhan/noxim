# Decisions taken without the author (v5: tuned DeFT baseline)

The conservative option is the one that favours the baseline (DeFT / DeFT_tm).

## Step 1
1. **The analytic VL imbalance uses the traffic table of the pattern** (uniform for the uniform LUT).
   Each VL carries the down traffic of the sources whose exit it is plus the up traffic of the flows
   whose entry it is. It is computed fault-free from the generator's own optimisation results.
