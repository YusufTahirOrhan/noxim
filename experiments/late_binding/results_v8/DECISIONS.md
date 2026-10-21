# Decisions taken without the author (v8)

The conservative option is the one that favours the baseline and, for the _G variants, their gamma = 1 parents.

## Environment
1. **Hardware, memory, disk.** 12 hardware threads, WSL memory limit 7.9 GB (unchanged), 12 runner processes.
   C: had 5.8 GB free at the start. Raw outputs are deleted after aggregation.

## Step 1: plain DeFT(rho*)
2. **DeFT(rho*) uses the same uniform LUT for every scenario**, including the faulty ones (the LUT files hold one
   entry set per fault mask). The two references differ in every scenario: by rho* (DeFT: 3x3 0.01, 4x4 0.001;
   DeFT_tm: 3x3 0, 4x4 0.003, each tuned in v5) and, on hotspot and chipperm, by DeFT_tm's traffic-matched LUTs.
3. **No VL imbalance for DeFT(rho*):** DEFT routing does not count VL use, and step 1 has no VL hypothesis, so no
   proxy runs were made.
4. **The C++ of step 2 was built only after the step-1 runs had finished**, so that the 980 DeFT(rho*) runs used the
   v7 binary (4477b04) without a rebuild underneath them.

## Step 2: layer-weighted hop cost
5. **Where gamma enters.** `remainingHops` and `hopsAfterMove` in `DeftLateBinding.cpp` are used only by the
   selection: DEFT_HEUR without lookahead (hopsAfterMove), its one-hop lookahead (`bestContinuation`: hopsAfterMove of
   the next move and remainingHops as the fallback), the learner's static estimate (`remoteStatic`, both
   `ql_lookahead` modes) and the learner's value at a router with no legal output (remainingHops). All of them now
   use the weighted length, so the learner's residual target (1 + v_here - static of the previous router) uses the
   same static estimate at both ends.
6. **Weighted length.** Each horizontal interposer hop counts gamma; each chiplet hop and each VL hop counts 1. The
   move being evaluated counts gamma if it is a horizontal interposer move. The minimum over candidates is taken
   under the weighted length (for the source phase over exit and entry pairs). The functions return double. With
   gamma = 1 every value is the same integer as before, so all costs and tie comparisons are unchanged.
7. **JSON.** `hop_weight_ipos` is written to the deft_lb block only when it is not 1.0, so the block is unchanged at
   the default.
8. **Valid range:** gamma > 0 (gamma <= 0 is rejected at start-up).
9. **Regression baseline:** the v7 binary (build of 4477b04, md5 d8649040..., `make -q` up to date) copied aside before
   the change; 66 configurations x (old, option absent, explicit 1.0) = 198 runs (`regression.md`).
10. **alpha = 0 check with gamma = 2:** CI_qlLA (alpha 0, v6 tuned weights, key chiplet) vs CI_heurLA, both with
    gamma 2, on 3x3/4x4 uniform fault-free and hotspot with one faulty VL per chiplet, 1.0 x Lsat, seeds 1-3 (12
    pairs; `alpha0_check.md`). gamma = 2 lies inside the selection grid.

## Step 3: selection
11. **Parent rows reused from v7.** The CI_heurLA and CI_qlLA rows (gamma 1) come from results_v7/select_runs.csv
    (same cells and seeds). The reuse was checked by re-running 4 parent cells with the v8 binary: 4 / 4 identical.
    FULL_qlLA was not in v7 and was run (70 runs). 910 new runs in total (12 gamma configurations + FULL_qlLA).
12. **Latency term** as v7: per scenario the mean over the 2 seeds, then the geometric mean over the scenarios.
13. **No extension:** gamma = 2 won for all three variants (interior; gamma = 3 broke the 5 % latency limit for all
    three), so the gamma = 4 step was not needed.

## Steps 4-5
14. **FULL_qlLA parent added to step 4.** The verdict compares a _G variant's interposer load with its parent's, and
    FULL_qlLA was not in the v7 bottleneck runs, so it was run with the three _G variants (72 runs). DeFT_tm(rho*),
    CI_heurLA and CI_qlLA come from results_v7/bottleneck_agg.json (same runs, identical binary at gamma 1).
15. **Verdict cell fixed before the step-4 data.** The pre-registration (committed while the step-4 runs were still
    running, before any result was seen) fixed the closeness test to 4x4 uniform at 1.0 x Lsat, the cell of the
    v6/v7 diagnosis, where the delivered traffic is equal for all variants. The other five cells are reported
    descriptively; at 1.2 x Lsat the accepted traffic differs, so the link load is not comparable there.
16. **FULL_qlLA_G and closeness.** Its parent already had DeFT_tm's interposer load, and gamma moves it 11 % below, so
    it counts as "not closer" (the literal criterion). The verdict rests on the two CI variants.
17. **VL imbalance of the references:** DeFT_tm, CI_heurLA, CI_qlLA from results_v7/vlref_runs.csv (all VLs); FULL_qlLA
    re-run at 1.0 x Lsat (140 runs, stage vlref), because the v6 column covers VL ids 0-15 only.
18. **Both sizes in one run:** the timing estimate was 4.8 h (rule threshold 14 h).
19. **Raw outputs deleted after aggregation:** DeFT(rho*), regression, alpha0, selection, bottleneck, drain, timing,
    evaluation and VL runs. Kept: deft_runs.csv, select_runs.csv, eval_runs.csv, vlref_runs.csv, bottleneck JSONs and
    the reports.
