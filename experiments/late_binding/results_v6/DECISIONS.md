# Decisions taken without the author (v6)

The conservative option is the one that favours the baseline (DeFT_tm(rho*)).

## Environment
1. **Hardware and memory.** 12 hardware threads. WSL's memory limit is 7.9 GB (the default of half
   the 16 GB RAM; there is no .wslconfig), and it was not changed. Runners use 12 processes; the
   memory of the 4x4 runs was watched, and the OOM incident of v4 came from the formal checker, not
   from the simulator.
2. **Disk:** C: had about 7 GB free at the start. The raw outputs of v1-v5 (about 200 MB, gitignored,
   already aggregated into the committed CSVs) were kept. v6 raw outputs are deleted after
   aggregation.

## Step 1: statistics
3. **Statistics through the existing DEFT_LB hooks.** Waiting per hop, per-link and per-VL forwarding
   counts, the entry/exit VL against the LUT's choice, extra hops, and the point where the entry or
   exit is fixed are all collected in `DeftLateBinding.cpp` from `onHeadForward` (which already
   receives `arrival_cycle` and the buffer-front cycle) and `onHeadConsumed`. They are enabled by
   `-deft_lb stats_file PATH` (off by default) and written to a separate file, so the `deft_lb` block
   is unchanged even with the flag on. Router.cpp is not touched.
4. **Hops are counted per packet in the statistics.** Noxim never increments `Flit::hop_no` (it stays
   0), so the extra-hop measure counts forwards in a map keyed by (source, generation time). This is
   unique because a PE generates at most one packet per cycle.
5. **DeFT_tm is measured through its DEFT_LB proxy** (exit and entry from its LUT, XY), because the
   hook is only active under DEFT_LB routing. The proxy is traffic-identical to DeFT_tm (checked
   in v2, v4 and v5).
6. **Link utilisation is counted from head flits x 8** (fixed packet size of 8 flits), over the
   8000 measured cycles.
7. **Reference LUT for "entry differs":** the uniform DeFT(rho*) LUT of 4x4 for CI_heurLA (its exit
   LUT) and FULL_heurLA. For the DeFT_tm proxy, its own LUT is the reference (sanity check: 0
   differences).

## Step 2: tuning
8. **Tuning loads come from the v5 Lsat** (~0.8 and ~1.1 x Lsat on each scenario's v5 grid), as
   instructed. The v5 rho tuning used the v4 Lsat for 3x3/4x4, but the protocol is otherwise the same:
   cells, seeds 101/102, geometric-mean latency.
9. **Grid extension (heuristics only).** The optimum lay on the w edge (w = 2 with busy = 0) for 3x3
   CI, 3x3 FULL and 4x4 CI, so w was extended by one step to 4, with busy {0, 4, 8}: 9 extra
   configurations. busy = 0 is a hard lower bound and was not extended. No w = 4 configuration won.
   4x4 FULL's optimum (w 1, busy 4) is interior.
10. **The learner grid was not extended**, although CI_qlLA chose alpha = 0.1, the top of its grid, on
    both sizes. The extension clause was given for the heuristic grid, and a larger learner budget
    would work against the baseline.
11. **FULL_qlLA existed since v2** (ql_lookahead on the FULL scope, alpha = 0 checked there on 6 runs).
    The 12-run check was repeated on 3x3/4x4 with the tuned weights: 12 / 12 identical
    (alpha0_check.md).
12. **CI keeps the uniform LUT of DeFT's rho* as its exit LUT** (3x3: 0.01, 4x4: 0.001), as in v5. The same
    LUT file is passed to the FULL runs, which do not use it.

## Steps 3-4
13. **Lsat and load points are v5's** (not re-measured), as instructed. The pre-registration was
    committed before the drain tests and before any evaluation run.
14. **Drain tests:** 32 runs (4 late-binding variants x 3x3/4x4 x 2 masks x 2 seeds), all PASS. The
    reference DeFT_tm(rho*) was drain-tested in v5 with the same LUTs.
15. **The evaluation ran all ten seeds at once** (estimate 8.1 h, rule threshold 30 h).
16. **Raw outputs deleted after aggregation:** statistics regression, bottleneck runs, tuning runs
    (aggregated into tune_runs.csv), drain, alpha0 and timing runs; the evaluation runs once
    eval_runs.csv is written.
