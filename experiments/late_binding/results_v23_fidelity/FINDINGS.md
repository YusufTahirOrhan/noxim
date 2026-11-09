# Findings v23: DeFT fidelity, modelling fixes, cross-validation, reference measurements

Status: Parts A, B and D1 complete; D2 (8,370 runs) running; D3-D5, Part C report and the five answers follow.

## Gates (Parts A and B)
* **Regression** (`regression.md`): 84 / 84 configurations byte-identical against the 780fa6b build, three times: the 3ac1bae
  build, the new binary with every option absent, and the new binary with every option given explicitly off.
* **Model check with the paper's Up rule** (`formal_upkeep.md`): 2x2 897 masks, 3x3 22 masks, 4x4 2 masks, four relations
  each (fixed pair XY, CI, FULL, fixed pair odd-even): CDG acyclic, no dead-end state, no livelock everywhere. The negative
  control (R3 and the F1 source rule removed) fails as expected, so the check can fail.
* **Drain tests** (`drain_summary.csv`): 948 runs (all-pairs 522 plus uniform, hotspot and chipperm workloads at several
  rates), 19 variants including DeFT-P, DeFT-B and DeFT-Dis: 948 PASS, 0 dead-end events, injected = received in every run.
* **VC split** (`vc_split.md`): with the paper's rules the Up VL carries 50:50 on VC0:VC1 for DeFT-P and DeFT-B against 0:100
  for the old DeFT (v19-v21), and the VC-wait per flit on the Up VL drops from 1.21 to 0.38 (2x2) and 0.85 to 0.27 (4x4)
  cycles. Latency at 1.0 x Lsat (uniform, K4 ladders): 2x2 44.0 (DeFT-P) / 50.8 (DeFT-B) / 58.1 (old); 4x4 65.3 / 71.1 / 75.9.
* **Pipeline option** (`probe_pipe.md`): `-pipe_all N` adds exactly N cycles per router on 1-, 3- and 16-hop paths.
* **LUTs** (`lut_check.md`): the v23 LUT entries equal the earlier rounds' for every size and mask.

## D1: load points (`load_points_v23.md`)
DeFT-P saturates later than the old DeFT (v19 Lsat) on uniform (x1.00-1.08 at pipe_all 0), localized (x1.09-1.12) and
movinghot (x1.09-1.15), much later on chipperm (x1.17-2.22), and **earlier on hotspot** at 3x3 and 4x4 (x0.75-0.84; 2x2
x0.85-1.00). At pipe_all 2 every Lsat is equal or higher than at pipe_all 0 (the deeper pipeline raises L0 and so 3 x L0).
The hotspot result is a D1 fact (seed 101, one method); D2 measures it with 5 seeds.

## The five questions
(pending D2-D5)
