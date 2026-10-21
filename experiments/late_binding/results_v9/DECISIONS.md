# Decisions taken without the author (v9)

The conservative option is the one that favours the baseline (plain DeFT(rho*)).

## Environment
1. **Hardware, memory, disk.** 12 hardware threads, WSL memory limit 7.9 GB (unchanged), 12 runner processes. C: had
   5.3 GB free at the start. Raw outputs are deleted after aggregation.
2. **Binary.** The v8 build (85eae67; `make -q` up to date). WSL's git lists src/ files as modified, but with
   `core.autocrlf=true core.filemode=false` there is no difference: only line endings and file modes (Windows
   checkout). No C++ change in v9.

## Step 1: design
3. **2x2 parameters:** the v2 frozen parameters of `variants_v2.py`, which v5 used for 2x2:
   - CI_heurLA (w 1, busy 4);
   - CI_qlLA with the CI lookahead weights (w 1, busy 4), alpha 0.05, key chiplet;
   - FULL_qlLA with the FULL lookahead weights (w 2, busy 0), alpha 0.01, key chiplet.
   gamma = 2 is appended to each, unchanged.
4. **No VL-imbalance reference:** DEFT routing does not count VL use. v9 has no VL hypothesis, so no proxy runs were
   made; the variants' own VL imbalance is reported (all VLs).
5. **v8 values to confirm** are the secondary comparisons against DeFT(rho*) in `results_v8/report/summary.md`, listed
   in the pre-registration (16 predicted results). The two v8 throughput results whose CI included 0 (3x3 FULL_qlLA_G,
   4x4 CI_heurLA_G) and all 2x2 tests are reported without a prediction, as the task lists them.

## Step 2: drain and timing
6. **2x2 drain LUT.** The v2 protocol needs entries for all 11 v2 VL masks, which only the v2 uniform LUT
   (`luts/lut_rho001.yaml`, rho 0.01) has. The v5 evaluation LUT (`luts/v5/lut_2x2_rho0.01.yaml`) holds 3 masks, and
   its 576 entries are identical to the v2 LUT's for those masks. So the v2 LUT drain covers the evaluated
   configuration exactly, plus 8 more masks.
7. **Timing test covers all five run types** (both references too), because the seed rule concerns the full
   evaluation. Every variant x size x scenario at the 2nd, 4th and 7th load, seed 1001.
8. **Drain:** 102 runs (3 variants x (11 masks x 2 seeds allpairs + 12 high-load runs)), all PASS.
9. **Seed rule applied:** estimate 8.4 h for seeds 41-50 (rule threshold 9 h) -> seeds 41-50; addendum committed
   before the evaluation.
