# Decisions taken without the author (v4: parametric topology and larger systems)

## Step 1: parametrisation (C++)
1. **The topology constants became run-time `int` variables with the same names**
   (DeftTopology::ChipletGridWidth, ..., VerticalLinkCount, LayoutHeight), set together by
   `DeftTopology::configure()`. Existing uses keep compiling and read the current values.
   `VerticalLinksPerChiplet` stays a compile-time 4 (as instructed), and `MaxVerticalLinkCount`
   is 64.
2. **Configuration order:** YAML (`deft_chiplets_x`, `deft_chiplets_y`, `deft_chiplet_w`,
   `deft_chiplet_h`; defaults 2, 2, 4, 4), then the command line (`-deft_chiplets_x`, ...),
   then `configure()`. It runs before `checkConfiguration()` and sets mesh_dim_x/y and
   n_delta_tiles from the footprint.
3. **Supported sizes:** at least 2 chiplets, chiplets of at least 3x3 routers, at most 64 VLs
   (16 chiplets). The slot positions are N=(1,0), E=(w-1,1), S=(w-2,h-1), W=(0,h-2), which is the
   fixed layout for 4x4 chiplets. They are distinct for every w, h >= 3.
4. **DeftLateBinding.cpp:** the namespace-scope copies (W, H, NVL, NROUTERS, NCHIP_ROUTERS)
   became `const int &` references to the topology variables. A copy would have been
   initialised with the default values at static-initialisation time. The router registry,
   the VL counters and the reach cache became vectors sized on first use (the reach cache
   is a pure memo). The Q table was already sized at run time.
5. **VL masks are uint64_t** (Packet, RouteData, Flit, DeftLateBinding through the `VlMask`
   alias, DeftVirtualNetwork, the LUT fault masks). `Flit::operator==` does not compare
   the masks, so signal-event behaviour is unaffected.
6. **Fault-mask ids** are "0x" plus ceil(VLs / 4) hex digits: 0x0000 for 16 VLs (as
   before), 9 digits for 36 VLs, 16 digits for 64 VLs. The LUT parser requires exactly this
   width.
7. **The JSON `config` block gains `deft_size`** for DEFT_2_5D runs. The `summary` and `deft_lb`
   blocks are unchanged, which is what the step-2 regression compares.
8. **No routing or selection logic was changed.** The only edits in DeftLateBinding.cpp are
   types, array sizing and the references of item 4.

## Step 2: default-instance regression
9. **132 fixed-window runs instead of "60".** The configuration list in the instructions
   (11 variants x uniform/hotspot/chipperm x 0x0000/0x1111 x 2 loads x seed 1) gives 132
   runs; the full list was run (a superset of 60). The loads are the 2nd and 5th v2
   evaluation rates (~0.5 and ~1.2 x Lsat), so one is below and one beyond saturation.
10. **22 drain runs instead of 20:** all 11 variants on the all-pairs burst with masks
    0x0000 (seed 1) and 0x9C63 (seed 2). DeFT_tm uses the chipperm LUT there.
11. **Reference binary:** the build of 4a3b345 (= the v2/v3 binary, byte-identical to the
    one used for the v2 and v3 runs).

## Step 3: generators and model
12. **Exact DP up to 64 demand points, exact MILP beyond.** The LUT generator's exact DP over load
    vectors is infeasible for the destination-entry problems of larger grids (128 points on 3x3,
    240 on 4x4). Those are solved as a MILP of the same objective (binary assignment variables,
    linearised absolute deviations; scipy.optimize.milp / HiGHS, mip_rel_gap = 0). Every 2x2
    problem and every source-exit problem keeps the DP, so the 2x2 LUTs are byte-identical. On
    all 264 2x2 optimisations (11 masks, 3 demand profiles), the MILP reaches the DP optimum
    exactly (results_v4/lut_milp_check.md). Ties may be broken differently.
13. **MILP weights are normalised to mean 1** (the objective is scale-invariant), so equal-weight
    demand gives exactly the unit-demand problem and its solution. Without this, the localized
    LUT differed from the uniform one only through tie-breaking on differently scaled inputs.
    With it, as on 2x2, localized and movinghot give exactly the uniform LUT on 3x3 and 4x4; only
    hotspot and chipperm get distinct traffic-matched LUTs.
14. **Traffic for C chiplets:**
    - hotspots at local (1, 1) of chiplets 0, 1 and CX (= routers 9, 13, 41 on 2x2);
    - movinghot cycles through the four corner chiplets 0, CX-1, C-CX, C-1 (= 0, 1, 2, 3 on 2x2);
    - chipperm c -> C-1-c; on 3x3 the middle chiplet 4 maps to itself and sends to its own other
      routers (self-traffic excluded). The instruction defines the permutation this way, so it
      was not changed.
    - Default tables are byte-identical through the parametric code path (401 files).
    - Larger instances get rates up to 0.024 only (`--upto`), to keep the tables small.
15. **Fault masks for the larger instances:** fault-free and one VL per chiplet (north, slot 0).
    The 20 random 3x3 masks of the formal check draw 0-3 faulty VLs per chiplet uniformly
    (seed 7; empty and duplicate masks rejected). This samples the "at most 3 per chiplet" space
    more evenly than drawing a total and rejecting.
16. **Formal 4x4 checks explore one destination at a time** (job_lean, exact; equal to job on 21 / 21
    checks). The whole-graph version was killed by the OOM killer at 4.7 GB and took the WSL VM
    down with it. WSL was restarted (`wsl --shutdown`); the killed jobs (a drain run in progress,
    two generator checks) were re-run from scratch, and no result of the killed run was used.

## Steps 4-6: drain, pre-registration, load points, evaluation
17. **Drain runs:** cutoff 1000 cycles (hard-coded traffic does not repeat; the bursts last 143 and
    255 cycles), timeout 1,000,000 cycles. DeFT_tm runs the burst with the hotspot and with the
    chipperm LUT (localized and movinghot equal the uniform LUT): 56 runs, all PASS.
18. **The pre-registration was committed while the last drain run was still finishing.** The rule
    "any drain FAIL stops the evaluation" was kept: the evaluation started only after 56 / 56 PASS.
19. **Load-point amendment** (PREREGISTRATION_AMENDMENT.md, committed before the fine sweep and before
    any evaluation run): L0 at rate 0.0002, and a 0.0001 grid where the coarse Lsat is <= 0.004.
    Under the original rule, 4x4 movinghot had Lsat = 0.001 (the reference rate itself), and its
    "1.0 x Lsat" load would have been at 2 x Lsat. Restoring the pre-registered load design was the
    conservative option, and the coarse result is kept. Under the amended rule the high-Lsat
    scenarios keep their coarse Lsat, except 3x3 uniform-north (0.0065 -> 0.006).
20. **DeFT is run in the evaluation** (not in a primary comparison) for the size trend of DeFT_tm vs
    DeFT. The VL-count proxy is run for DeFT_tm only, at ~0.5 and ~1.0 x Lsat (280 runs). DeFT's VL
    imbalance is not measured in v4.
21. **Disk:** C: had about 10 GB free. Only the tables that are needed (pattern x rate) are generated for
    the fine sweep and the evaluation loads (`gen_traffic.py --rates --patterns`).
