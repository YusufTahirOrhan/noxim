# Pre-registration v24 Part D: late binding with XY and with the VN-split order on the interposer

Committed before any Part D run (the timing runs included). Done before it: the reproduction of the review's probes
(`reproduction.md`), the regression (84 / 84 byte-identical, `regression.md`), the two equivalence checks
(`busy_state_check.md`, `equivalence.md`), the model check (`formal_xy.md`), the drain tests (`drain_summary.csv`), the
chiptrans ladders (`load_points_v24.md`), the centre-cut statistics (`centre_cut.md`) and the tuning on seeds 101-102
(`tuning.md`). Nothing below depends on a Part D result.

## Options of every run
* pipe_all 2; window 2000 + 8000 cycles; 8-flit packets; 2 VCs; 4-flit buffers; LUTs `luts/v23`; `-traffic_rng 1`.
* Every VN-based method: `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1`. MTR and RC: `-vc_per_hop 1`.
* Loads: the 9 points (0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 × Lsat of DeFT-P) of the pipe_all 2 ladders in
  `load_points_v24.json` (v23 ladders; chiptrans new, same rule).
* Sizes 2x2, 3x3, 4x4. Scenarios: uniform, hotspot, chipperm, chiptrans (fault-free) and uniform with one faulty VL per
  chiplet (0x1111 / 0x111111111 / 0x1111111111111111). Seeds 111-115 (new; 91 and 92 were used by the probes, 101-102 by
  the tuning).

## Rows (108 cells = row × scenario)
* **References (18 cells):** DeFT_P, DeFT_B (five scenarios each; with `-deft_lb count_vl 1`, which only counts); MTR, RC
  (the four fault-free scenarios).
* **Candidates (60 cells):** `CI_heurLA_X`, `CI_qlLA_X`, `CI_heurLA_O`, `CI_qlLA_O` with the tuned values below, each in three
  mechanisms, with `-deft_lb hop_stats 1`:
  - **ideal:** decision_delay 0, no lookahead;
  - **LF:** `lookahead_route 1 lookahead_fallback 1 busy_state 1` and the residual decision_delay max(0, N_fast + 1 − W),
    W = pipe_all + 1 = 3: 0 for the heuristic variants (N_fast = 2), 1 for the Q-learning variants (N_fast = 3);
  - **DLY:** no lookahead, decision_delay N_fast (2 heuristic, 3 Q-learning).
* **Secondary rows, ideal mechanism only (30 cells; `hop_stats 1`):** `FULL_qlLA_X` (the values of `CI_qlLA_X`);
  `CI_qlLA_G` and `FULL_qlLA_G` (the v23 odd-even variants, v10 parameters, unchanged); `DeFT_P_O1` (`-routing DEFT_LB`,
  exit and entry from the LUT, `chip_tm XY ipos_tm O1`, `-deft_lut_entry dst`); `CI_rand_X` (relation X, CI, `-sel RANDOM`);
  `CI_heur_X` (`CI_heurLA_X` with `heur_lookahead 0`).
* **Controls** (`CI_qlLA_X`, uniform fault-free, all sizes): lookahead without the fallback at residual 1
  (`lookahead_route 1 busy_state 1 decision_delay 1`); lookahead with the fallback at residual 0.
* Relation X = `chip_tm XY ipos_tm XY`; relation O = `chip_tm XY ipos_tm O1` (XY in VN0, YX in VN1 on the interposer).
  CI = exit from the LUT, entry late.

## Tuned values (`tuning.md`, seeds 101-102; frozen)
| size | relation | heuristic (`CI_heurLA`, `CI_heur_X`): heur_w, heur_busy, hop_weight_ipos, lut_bias | Q-learning (`CI_qlLA`, `FULL_qlLA_X`): ql_w, ql_busy, hop_weight_ipos, lut_bias, ql_alpha |
|---|---|---|---|
| 2x2 | X | 2, 0, 1, 2 | 2, 0, 1, 2, 0.01 |
| 2x2 | O | 2, 0, 1, 2 | 2, 0, 1, 2, 0.01 |
| 3x3 (the 4x4 values) | X | 2, 0, 1, 0 | 2, 0, 1, 0, 0.01 |
| 3x3 (the 4x4 values) | O | 2, 0, 1, 0 | 2, 0, 1, 0, 0.01 |
| 4x4 | X | 2, 0, 1, 0 | 2, 0, 1, 0, 0.01 |
| 4x4 | O | 2, 0, 1, 0 | 2, 0, 1, 0, 0.01 |

Q-learning: `ql_key 1` (destination chiplet), `ql_eps 0`, `ql_lookahead 1`; heuristic: `heur_lookahead 1` (0 for `CI_heur_X`).
`CI_qlLA_G` and `FULL_qlLA_G` keep their v10 parameters (`experiments_v10.methods`).

## Runs and the time rule
108 cells × 3 sizes × 9 loads × 5 seeds = 14,580 runs, plus 270 for the controls. The time is estimated first from the 990
runs of seed 111 at the 2nd, 5th and 9th load of every cell (runs of the design, kept; `runtime_estimate.md`). If the
estimate for the whole design exceeds 30 h, rows are dropped in this order until it does not: (1) DLY for the two heuristic
variants; (2) `CI_rand_X` and `CI_heur_X` on hotspot, chipperm and chiptrans. Nothing else is reduced.

## Metrics
* **THR:** the largest accepted throughput over the 9 loads (the report says where it sits). **LAT** and **P99:** mean and
  99th-percentile packet latency at 1.0 × Lsat of DeFT-P (the 4th load). **LAT at 0.2 and 0.5 × Lsat:** the low-load cost.
* **Best baseline** per (size, scenario, metric): the one of DeFT_P, DeFT_B, MTR, RC (with faults: DeFT_P, DeFT_B) with the
  best mean over the five seeds (highest THR, lowest LAT, lowest P99); its per-seed values are the reference.
* **Effect per size** = 100 × (exp(mean over seeds of R_s) − 1) %, R_s = mean over the five scenarios of
  ln(metric_row / metric_best baseline) for seed s. Two-sided one-sample t test over the five seeds (4 df).

## Primary family (18 tests, Holm over the 18, α = 0.05)
On each size, `CI_qlLA_X` and `CI_qlLA_O` in mechanism **LF** have higher THR, lower LAT and lower P99 than the best baseline.
Supported = significant after Holm in the hypothesised direction. A significant effect in the other direction is reported
as against.

## Secondary (descriptive; unadjusted p values, never called significant)
* every row per scenario against each baseline and against the best baseline;
* ideal and DLY against LF; the two controls;
* X against O against G (odd-even) per scenario;
* the ladder `CI_rand_X` → `CI_heur_X` → `CI_heurLA_X` → `CI_qlLA_X`;
* `DeFT_P_O1` against DeFT_P (the VN-split order without late binding);
* LAT at 0.2 and 0.5 × Lsat against DeFT_P for every candidate;
* accepted throughput at 2.0 and 2.4 × Lsat relative to the row's peak;
* the share of hops with more than one offered output (per layer), the fallback rate, the share of stored decisions that
  differ from a fresh one.

## Sanity (`report/sanity.md`; uniform fault-free, seed 111, 1.0 × Lsat, each size)
* hops per packet of `CI_qlLA_X` and `CI_qlLA_O` against DeFT_Dis (hop_stats);
* the largest flit rate of any VL in any run of the round: it must not exceed 0.5 flits per cycle;
* the two counting options (`count_vl`, `hop_stats`) leave the statistics unchanged.

## Exclusions
A missing run is listed; a seed with a missing run in a scenario of a comparison is dropped from that comparison and this
is reported. A dead-end event in any run stops the round. The design is run in full; the only reduction is the time rule.

## Report
`report/summary.md` (per size against the best baseline with all rows; per scenario; the mechanism table; the low-load
table; the selection ladder), latency-versus-load figures (4x4: uniform, chipperm, chiptrans, faulty) with DeFT_P, DeFT_B,
MTR, RC, `CI_qlLA_G`, `CI_qlLA_X` and `CI_qlLA_O` (ideal and LF), and `FINDINGS.md` with the ten answers.
