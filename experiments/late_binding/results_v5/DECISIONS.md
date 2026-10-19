# Decisions taken without the author (v5: tuned DeFT baseline)

The conservative option is the one that favours the baseline (DeFT / DeFT_tm).

## Step 1
1. **The analytic VL imbalance uses the traffic table of the pattern** (uniform for the uniform LUT).
   Each VL carries the down traffic of the sources whose exit it is plus the up traffic of the flows
   whose entry it is. It is computed fault-free from the generator's own optimisation results.

## Step 2: tuning rho
2. **rho = 0 is lexicographic** (balance first, then distance) in both solvers. The DP's ranking key
   already breaks ties by distance. The MILP got a second stage that minimises distance subject to
   the optimal balance (matches the DP on all four 2x2 entry problems). Without this, rho = 0 on
   3x3/4x4 would return an arbitrary balanced assignment with possibly very long paths, which is
   unfair to the baseline. The rho = 0.01 outputs are unchanged (2x2 and 4x4 byte-identical).
3. **Tuning cells, loads, seeds and criterion are those of the other methods:** uniform, hotspot,
   chipperm fault-free and uniform with one faulty VL per chiplet; ~0.8 and ~1.1 x Lsat (2x2: the v2
   tuning loads; 3x3/4x4: from the v4 Lsat); seeds 101, 102; geometric-mean latency.
4. **DeFT_tm reuses the DeFT runs on the uniform cells.** Its LUT there is the uniform LUT of the same
   rho, so those runs are identical, and repeating them adds no information.
5. **Only hotspot and chipperm get traffic-matched LUTs.** localized and movinghot give exactly the
   uniform LUT: within every LUT optimisation their demand weights are equal (shown for rho = 0.01
   in v2/v4; it follows from the scale invariance of both solvers for any rho).
6. **Ties between rho values** (identical LUTs, hence identical runs) are resolved towards the larger
   rho, i.e. closer to the original 0.01.
7. **If DeFT and DeFT_tm choose different rho*,** each uses its own, and the CI variants take their
   exit VL from the uniform LUT of DeFT's rho* (the uniform LUT tuned as a uniform LUT).
