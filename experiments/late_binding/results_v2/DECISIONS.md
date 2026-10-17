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

## Stage 2: information-matched learner (ql_lookahead)
8. **ql_lookahead is a file-local variable in src/DeftLateBinding.cpp** (set through
   the existing `-deft_lb key value` parser), not a new field of `Config`. A new field
   would require editing DeftLateBinding.h, and only the .cpp change was authorised.
   The deft_lb JSON block reports the value (`ql_lookahead`), which is part of adding
   the parameter in the same file.
9. **The lookahead term is shared code.** DEFT_HEUR's lookahead block was moved
   verbatim into `bestContinuation(rd, o, w)`. The heuristic calls it with heur_w and the
   learner with ql_w, so with ql_w = heur_w the term is the same computation. The
   refactor was checked to leave every existing variant unchanged (24/24 runs
   identical, results_v2/qlla_check.md).
10. **The QL-LA residual target.** At forward time ql_prev_static = 1 + best_continuation(o)
    with the current router state. The update is unchanged: target = 1 + V_here, where
    V_here is the receiving router's minimum learner cost (which now includes its own
    lookahead term).
11. **QL-LA uses the local weights (w, busy) tuned for the lookahead heuristic of the
    same scope.** QL uses those of the plain heuristic. This mirrors v1, so each learner
    differs from its heuristic only by the learned residual.

## Stage 4 (run before stage 3): load points
12. **Stage 4 ran before stage 3.** The tuning loads (~0.8 and ~1.1 Lsat of each tuning
    cell) need the per-scenario Lsat, including uniform 0x1111.
13. **0.0005 rate grid.** On the 0.001 grid, scenarios with Lsat <= 0.0045 cannot hold 7
    distinct points between 0.2 and 1.6 Lsat. gen_traffic.py gained a `half` mode that
    writes only the odd multiples of 0.0005; the existing tables are unchanged (checksums
    verified).
14. **Lsat criterion: the first crossing.** Lsat is the largest swept rate before latency
    *first* exceeds 3x L0, with L0 the latency at 0.001 as in v1. One DeFT seed (101) is
    used, as in v1.
15. **Load points come from DeFT's Lsat.** DeFT_tm saturates later on chipperm, and so may
    the late-binding variants. Wherever a variant still accepts >= 95 % of the highest
    offered load, its saturation throughput is reported as a lower bound and flagged.
    The load range was not widened beyond 1.6 x DeFT's Lsat (instructions).
