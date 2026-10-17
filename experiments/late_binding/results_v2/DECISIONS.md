# Decisions taken without the author (v2 evaluation)

Each entry: the decision, why, and the alternative not taken. Where several options
were open, the most conservative one was chosen (the one least likely to favour the
new methods).

## Stage 1: traffic-matched DeFT LUT
1. **Demand weights only the load terms.** Each demand point (a source router for the exit
   choice; a (source chiplet, source router) pair for the destination-entry choice)
   carries its time-averaged demand as a weight in the per-VL loads and in the mean
   load. The distance term stays unweighted, as instructed ("use it in the load terms").
   The LUT structure is unchanged: one exit VL per source router (independent of the
   destination chiplet) and one entry VL per (destination chiplet, source router).
2. **Time averaging follows Noxim's activation rule exactly**: a line is active
   (t_off - t_on - 1) / t_period of the time. For movinghot this leaves one-cycle
   gaps (1999 vs 2000 active cycles per phase). The resulting LUT still equals the
   uniform LUT in every selected VL.
3. **Demand from the rate-0.010 tables.** The LUT is invariant to scaling all
   demands; one fixed reference rate avoids rounding differences between tables.
4. **The traffic-matched LUTs cover all 11 masks of drain_masks.txt** (a superset of
   the three evaluation masks), so the drain tests can also exercise DeFT_tm.
5. **localized and movinghot produce exactly the uniform LUT** (only header lines
   differ). Their time-averaged inter-chiplet demand is the same for every source
   router and destination chiplet, so DeFT_tm = DeFT on uniform, localized and
   movinghot (5 of 11 scenarios). DeFT_tm is still run there (it doubles as an
   identity check).
6. **CI variants keep the uniform LUT for their exit VL** (as in v1). Giving CI the
   traffic-matched exit would be a different variant. Keeping the uniform exit can
   only disadvantage CI against DeFT_tm, which is the conservative direction for the
   primary comparisons CI_* vs DeFT_tm.
7. **A_oracle keeps oracle_beta = 0.5 from the v1 tuning** (seeds 101, 102). It is not
   in the v2 tuning list, and it is not part of any primary comparison.
