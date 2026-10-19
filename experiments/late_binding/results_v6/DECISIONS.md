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
