# Decisions taken without the author (v7)

The conservative option is the one that favours the baseline (DeFT_tm(rho*)) and, for the bounded variants, their
unbounded parents.

## Environment
1. **Hardware, memory, disk.** 12 hardware threads, WSL memory limit 7.9 GB (unchanged, as v6), 12 runner processes.
   C: had 6.4 GB free at the start. v7 raw outputs are deleted after aggregation; only aggregated CSV/JSON/MD and
   figures are kept.

## Step 1: implementation
2. **Where the bound lives.** A new function `boundEntryMask` in `DeftLateBinding.cpp`, called from
   `prepareHeadPacket` right after `chooseMasks` (which already restricts the masks to the functional VLs), only
   when `entry_bound_mode` is not `off`. It consumes no random numbers, so with the option on the random stream
   is unchanged up to the routing decisions themselves. The source virtual network depends only on the exit mask
   and is unchanged.
3. **L(e).** Each phase of DEFT_LB routes minimally under its turn model and starts with no previous move (after
   injection and after a vertical hop), and both XY and odd-even admit a minimal path between any two routers. So
   the shortest turn-legal path src -> exit v -> entry e -> dst has length
   |src - v| + 1 + |v - e| + 1 + |e - dst| (Manhattan distances on the footprint, VL hops counted). The code still
   checks each leg with the turn-model reachability cache (`reach`) and treats an unreachable leg as infinite.
   L(e) uses the best exit of the packet's exit mask (CI: the LUT's single exit; FULL: every functional exit).
4. **Mode lut.** e_LUT is the entry of the LUT loaded with `-deft_vl_lut`. For CI (and FULL) runs this is DeFT's
   rho* uniform LUT of the size, the one CI uses for its exit (v6 decision 12). The LUT has one entry per fault mask
   and its selected entry is always functional, so the fallback to mode min (e_LUT faulty or missing) is
   implemented and counted (`entry_bound_lut_fallbacks`) but does not occur in the v7 scenarios (0 in every run).
   In mode lut the kept set also contains entries shorter than e_LUT (L(e) <= L(e_LUT) + k), as specified.
5. **Statistics.** The `deft_lb` block gets `entry_bound_mode`, `entry_bound_k`, `entry_bound_packets`,
   `entry_bound_lut_fallbacks`, `entry_candidates_before_mean` and `entry_candidates_after_mean`, **only when the
   option is on**, so that with the option off the block stays byte-identical. Candidate counts are averaged over the
   inter-chiplet packets injected after the warm-up; the fallback counter covers all packets.
6. **Formal check.** The model did not support per-packet initial masks. It was extended with an entry policy
   `subsets`: the initial entry mask of every source-destination pair ranges over every non-empty subset of the
   functional entries (CI: with every functional exit singleton; FULL: with all functional exits). This contains
   every mask any (mode, k, LUT) can produce, so one check covers all configurations, including the ones chosen in
   step 3. 3x3, 6 fault masks (fault-free, one VL per chiplet, the first 4 random masks of the v4 check): 12 / 12
   pass (`formal_bounded.md`).
7. **Regression baseline.** The v6 binary (build of 2d93fef, md5 7e7e268d..., confirmed up to date with `make`
   before any change) was copied aside and run with the same arguments as the new binary: the 66 configurations of
   the v6 statistics regression (11 v2 variants x 2x2/3x3/4x4 x fault-free / faulty), once with the option absent and
   once with an explicit `entry_bound_mode off` (and k = 2), 198 runs (`regression.md`).
8. **Determinism check cells.** 20 v6 evaluation runs chosen by a fixed rule (sizes alternate; DeFT_tm, CI_heurLA,
   CI_qlLA cycle; scenarios, loads and seeds spread over the v6 grid), compared field by field with
   `results_v6/eval_runs.csv` (`determinism.md`).
9. **VL imbalance bug found and fixed.** `make_eval_csv.py` computed the VL imbalance over VL ids 0-15 only (a
   leftover of the 2x2 instance), so on 3x3 and 4x4 the `vl_imbalance` column of v4-v6 covers only the VLs of the
   first four chiplets. Fixed for v7 (all VLs). The v4-v6 files are not changed. For the v7 secondary VL-imbalance
   comparison the references (DeFT_tm(rho*) through its proxy, CI_heurLA, CI_qlLA) are re-run at 1.0 x Lsat on
   seeds 31-40 (stage `vlref`, 420 runs); the parent runs double as an extended determinism check.
