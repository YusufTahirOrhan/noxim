# v24 C2: tuning of the selection parameters (experiments_v24.py tunerule, tune1, choose1, tune2, choose2)

## The rule (written before any tuning run)

* **Runs.** pipe_all 2, decision_delay 0 (ideal decision), DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3 inherits the 4x4
  values); the five scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet, the v9 masks); the ladder indices
  1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat of the pipe_all 2 ladders, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds.
* **Stage 1, heuristic** (`CI_heurLA_X` and `CI_heurLA_O`): W (heur_w) in {1, 2} x B (heur_busy) in {0, 4} x G (hop_weight_ipos) in {1, 2} x D (lut_bias) in
  {0, 2, 4}: 24 configurations per relation.
* **Stage 2, Q-learning** (`CI_qlLA_X` and `CI_qlLA_O`): W, B, G, D of the stage-1 choice of the relation and size; A (ql_alpha) in {0.01, 0.05, 0.1}.
  `FULL_qlLA_X` takes the parameters of `CI_qlLA_X`; `CI_heur_X` those of `CI_heurLA_X`.
* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of
  `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four
  loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.
* **Choice, stage 1:** the largest score; among the configurations within 0.02 of it, prefer D = 0, then G = 1, then B = 0, then W = 1 (the simplest
  hardware; applied in this order as successive filters, a filter that would leave nothing is skipped), then the larger score.
* **Choice, stage 2:** the A with the largest score.
* Also reported, not used for the choice: the score of the v10 values (2x2: W 1, B 4, G 2, D 0, A 0.05; 4x4: W 2, B 0, G 2, D 0, A 0.1) on both relations.
  For the heuristic they are grid points; for Q-learning they are run in addition where the stage-1 choice differs from them.
* Runs: (48 + 6) configurations x 2 sizes x 5 scenarios x 4 loads x 2 seeds = 4,320, plus 80 for DeFT-P, plus at most 160 for the v10 Q-learning values.

## Results

Not run yet.
