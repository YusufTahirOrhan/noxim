# Pre-registration v23 Part D: reference measurements under the paper's rules

Committed before any Part D run (D1 included). The gates of Parts A and B (regression, model check, drain tests) are done
before the first run. Nothing in this design depends on a Part D result; the decisions below were taken by the prompt of
this round and are not open.

## Options of every run
* Every VN-based method: `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -traffic_rng 1`.
* **DeFT-P** = that with `-deft_lut_entry dst` (the paper's second selection); **DeFT-B** = that with the v1-v21 entry.
  DeFT-P is the primary reference. LUTs: `luts/v23/lut_<size>_<mask>.yaml` (their `entries` equal the earlier LUTs',
  `lut_check.md`).
* MTR and RC: `-vc_per_hop 1 -traffic_rng 1` (primary rows); without `-vc_per_hop` as secondary rows (pipe_all 0 only).
* The old DeFT of v19-v21 (`DeFT_old`: `-deft_vn_rr 1 -traffic_rng 1`, the DeFT-B LUT, up_keep and fallback off), for H1,
  at pipe_all 0 only.
* The ideal late-binding references CI_qlLA_G and FULL_qlLA_G: their v10 parameters (`experiments_v10.methods`), decision
  delay 0, no retuning.
* Window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers.

## D1: load points
DeFT-P, seed 101, every size and every v9 scenario (2x2: the 11 v2 scenarios; 3x3 and 4x4: the 7 v5 scenarios), at
pipe_all = 0 and pipe_all = 2. L0 = DeFT-P's latency at 0.0002. Lsat = the largest swept rate before the latency first
exceeds 3 × L0, on the 0.0001 grid where the coarse (0.0005-grid) Lsat is ≤ 0.004, otherwise on the 0.0005 grid. Ladder:
0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 × Lsat (9 loads, rounded to the grid, strictly increasing). Written to
`load_points_v23.json` before any D2 run. The pipe_all = 2 ladder is used by the pipe_all = 2 runs.

## D2: design
* Sizes 2x2, 3x3, 4x4. Scenarios: uniform, hotspot and chipperm fault-free, and uniform with one faulty VL per chiplet
  (0x1111 / 0x111111111 / 0x1111111111111111). MTR and RC: the three fault-free scenarios (their tables assume fault-free VLs).
* Loads: the 9 ladder points of the scenario and pipe depth. pipe_all ∈ {0, 2}. Seeds 91-95 (new).
* Methods: DeFT-P, DeFT-B, MTR, RC, DeFT-Dis, CI_qlLA_G, FULL_qlLA_G at both pipe depths; MTR_static and RC_static (no per-hop
  VC) at pipe_all 0; DeFT_old at pipe_all 0.
* Runs: (5 VN methods × 4 scenarios + 2 × 3) × 3 sizes × 9 loads × 2 pipes × 5 seeds = 7,020, plus 810 (static MTR/RC) plus
  540 (DeFT_old) = 8,370. A timing test estimates the wall time first; if it exceeds 20 h, pipe_all = 2 is dropped for
  DeFT-Dis and recorded in `DECISIONS.md`.

## Metrics
* **LAT**: mean packet latency at 1.0 × Lsat (the 4th load of the ladder). **P99**: p99 latency at the same load.
  **THR**: the maximum accepted throughput over the 9 loads; the report says per cell whether the maximum sits at the top load.
* Effect = 100 × (exp(mean_s R_s) − 1) %, R_s = mean over the scenarios of ln(metric_variant / metric_reference) for seed s
  (4 scenarios for the VN-based methods, the 3 fault-free ones for MTR and RC). Two-sided one-sample t-test over seeds 91-95
  (4 df). Holm over the whole primary family (18 tests).

## Primary hypotheses (18; Holm over the 18), pipe_all = 0
* **H1 (6 tests):** on each size, DeFT-P has higher THR and lower LAT than DeFT_old (the v19 reference), over the 4 scenarios.
* **H2 (12 tests):** on each size, CI_qlLA_G and FULL_qlLA_G have lower LAT and lower P99 than DeFT-P, over the 4 scenarios.

Supported = significant after Holm in the hypothesised direction. A significant effect in the other direction is reported as
such.

## Secondary (descriptive, unadjusted p values, never called significant)
* DeFT-P against MTR and RC per scenario and per size (LAT, P99, THR): does "DeFT loses to MTR and RC" survive, and on which
  patterns.
* DeFT-P against DeFT-B (LAT, P99, THR), all scenarios.
* MTR and RC with against without `-vc_per_hop` (pipe_all 0).
* Every comparison again at pipe_all = 2.
* Per cell: whether the THR maximum sits at the top load; the saturation flag of v10 (accepted at 1.0 × Lsat below 95 % of
  offered).
* Tables in the v10 format: per size, every method against DeFT-P; a latency-versus-load figure for uniform at both pipe
  depths; the VC-split table of A2.

## D4: herding A/B (exploratory; no test)
CI_qlLA_G and FULL_qlLA_G, 4x4 uniform and hotspot, the ladder loads from 1.0 to 2.4 × Lsat (6 loads), seeds 101-102,
`-deft_lb hysteresis D`, D ∈ {0, 1, 2, 4}, in two delay configurations: decision_delay 0 at pipe_all 0, and the lookahead
residual at pipe_all 2 (`lookahead_route 1`, decision_delay 1). Reported: accepted throughput against load per D (is it
monotone, which D keeps THR highest). It only decides the tuning grid of the next round.

## D5: lookahead check
CI_qlLA_G and FULL_qlLA_G on 2x2 and 4x4 uniform, pipe_all 2, seeds 91-95, the 9 loads, with `-deft_lb lookahead_route 1`
and the residual decision_delay max(0, N_fast + 1 − (pipe_all + 1)) = 1 (N_fast = 3 for the learners), against the same
variant at decision_delay 0 and pipe_all 2 (the D2 runs). Reported: LAT at 0.2, 1.0 and 2.0 × Lsat and THR, per-seed log
ratios with 95 % intervals; the share of the ideal gain over DeFT-P that the lookahead model keeps; the share of stored
decisions that differ from the fresh decision at the next router (`lookahead_mismatch / lookahead_used`).

## Exclusions and gates
Evaluation runs only after the regression, the model check and the drain tests have passed; a failure stops the round. A
missing run is listed; a seed with a missing run in a scenario of a comparison is dropped from that comparison and this is
reported. The full design is run; a reduction follows only the 20 h rule above.
