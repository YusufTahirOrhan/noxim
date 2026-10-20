# v8 step 1 findings: late binding vs plain DeFT(rho*) (seeds 31-40)

Design: `PREREGISTRATION_step1.md` (committed before any run, b2602ba). Tables: `report_step1/summary.md`,
`report_step1/primary.csv`. Per-run data: `deft_runs.csv` (980 DeFT(rho*) runs, 0 missing). Variant runs and
DeFT_tm(rho*) from `results_v6/eval_runs.csv`.

## Primary results (pre-registered; Holm over 24 tests; 23 significant)
% change against DeFT(rho*), mean over the 7 scenarios, 95 % CI over seeds 31-40. In brackets: the v6 result against
DeFT_tm(rho*) (same variant runs). Bold = significant after Holm.

| size | variant | mean latency @1.0 Lsat | p99 latency @1.0 Lsat | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA | **-18.7** [-21.7, -15.5] (-13.6) | **-39.3** [-44.5, -33.7] (-30.4) | +0.12 [-0.22, +0.47] n.s. (-2.61) |
| | CI_qlLA | **-21.9** [-24.7, -19.0] (-17.0) | **-44.8** [-48.9, -40.4] (-36.7) | **+1.42** [+0.85, +2.00] (-1.35) |
| | FULL_heurLA | **-30.9** [-33.8, -27.9] (-26.6) | **-54.9** [-59.1, -50.4] (-48.3) | **-2.37** [-3.51, -1.22] (-5.04) |
| | FULL_qlLA | **-33.5** [-36.7, -30.1] (-29.3) | **-57.9** [-62.4, -52.9] (-51.7) | **-2.44** [-3.26, -1.61] (-5.10) |
| 4x4 | CI_heurLA | **-23.6** [-27.8, -19.2] (-19.9) | **-46.4** [-52.3, -39.7] (-35.8) | **-5.89** [-6.78, -5.00] (-9.64) |
| | CI_qlLA | **-27.3** [-30.4, -24.2] (-23.8) | **-52.9** [-57.8, -47.5] (-43.6) | **-1.81** [-2.44, -1.17] (-5.72) |
| | FULL_heurLA | **-35.0** [-37.8, -32.1] (-31.9) | **-58.1** [-62.5, -53.2] (-49.8) | **-3.42** [-4.92, -1.89] (-7.26) |
| | FULL_qlLA | **-39.4** [-42.2, -36.4] (-36.4) | **-63.0** [-66.7, -58.8] (-55.7) | **-1.69** [-2.89, -0.48] (-5.60) |

* **Latency:** every variant is significantly faster than plain DeFT(rho*), by more than against DeFT_tm(rho*):
  - mean latency -19 % to -39 %;
  - p99 latency -39 % to -63 %.
* **Saturation throughput:**
  - 3x3: CI_qlLA is significantly **higher** than plain DeFT (+1.4 %), CI_heurLA is level (+0.1 %, n.s.), and the
    FULL variants are 2.4 % lower.
  - 4x4: every variant is still significantly lower. The learners are within 2 % (CI_qlLA -1.8 %, FULL_qlLA -1.7 %);
    the heuristics lose 3.4 % (FULL) and 5.9 % (CI).
* **Compared with the v6 result against DeFT_tm(rho*):** all throughput losses shrink by 2.5-4 points. About half
  of the v6 gap was the traffic matching of the reference, not late binding.

## Secondary (unadjusted)
* **What traffic matching buys: only chipperm.**
  - DeFT_tm(rho*) vs DeFT(rho*): saturation throughput +2.8 % (3x3) and +4.1 % (4x4) overall.
  - All of it comes from chipperm (+19.5 % and +32.4 %, DeFT_tm still capped). Without chipperm the two references
    are level (+0.3 %, +0.1 %), and so is latency (+0.0 %, +2.5 %, n.s.).
* **Without chipperm:**
  - Against plain DeFT the numbers are almost the same as against DeFT_tm: 3x3 CI +2.2 % / +3.5 %, FULL -0.6 %
    (n.s.); 4x4 CI -5.2 % / -2.0 %, FULL -4.0 % / -1.7 %.
  - So the 4x4 throughput gap of the CI heuristic on uniform (-16 %) and localized (-13 %), and of FULL on movinghot
    (-15 % to -17 %), is a real loss against a traffic-unaware LUT, not a traffic-matching effect.
* **Chipperm against plain DeFT:**
  - 3x3: every variant still loses 10-13 %.
  - 4x4: CI_qlLA, FULL_heurLA and FULL_qlLA are level (-0.9 %, +0.4 %, -1.9 %); CI_heurLA loses 9.9 %.

## Bottom line
* Against the realistic, traffic-unaware DeFT(rho*), late binding cuts near-saturation latency by a fifth to two
  fifths, and its p99 by two fifths to three fifths, on 9 and 16 chiplets.
* It costs at most about 2 % saturation throughput with learning (gaining 1.4 % with CI_qlLA on 3x3), and up to 6 %
  with the CI heuristic on 4x4.
* The larger losses reported against DeFT_tm(rho*) in v5-v7 come about half from DeFT_tm's traffic-matched chipperm
  LUT.
