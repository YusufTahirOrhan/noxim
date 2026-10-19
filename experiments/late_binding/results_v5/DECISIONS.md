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

## Steps 3-6
8. **Lsat is re-measured on every size, 2x2 included**, with the v4 amended rule (L0 at 0.0002;
   0.0001 grid where the coarse Lsat <= 0.004). On 2x2 the v2 load points used L0 at 0.001, so the
   2x2 load points of v5 differ slightly from v2 (only 2x2 chipperm 0x9C63 moves to the fine grid).
9. **DeFT(rho*) is run where its LUT differs from DeFT_tm(rho*):** on 2x2 only hotspot and chipperm
   (same rho* for both); on 3x3 and 4x4 every scenario (the two rho* differ, so even the uniform
   LUTs differ). Where the LUTs are identical, the analysis uses the DeFT_tm run for DeFT.
10. **Drain:** 72 runs. DeFT_tm runs the burst with its hotspot and chipperm LUTs. The CI variants
    use the uniform LUT of DeFT's rho*. FULL_heurLA does not use a LUT and was drain-tested in v4
    (unchanged).
11. **The pre-registration was committed after the load points** (step 3) and before the drain
    tests and the evaluation, as instructed ("commit before step 5").
