# Findings v23: DeFT fidelity, modelling fixes, cross-validation, reference measurements

Status: Parts A, B, C, D1, D2 and D5 complete (8,370 + 180 runs, 0 missing, 0 dead ends); D4 running; the answer to question 5 follows.

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

Effects are 100 x (exp(mean over seeds 91-95 of the log ratio) - 1); LAT and P99 at 1.0 x Lsat of DeFT-P (the comparison
load is DeFT-P's own saturation load, so a method that saturates earlier or later than DeFT-P is measured at a different
fraction of its own capacity); THR = maximum accepted throughput over the 9 loads. Primary tests: `report/primary.csv`
(Holm over 18); everything else is descriptive (`report/secondary.csv`, unadjusted p values, never called significant).

### 1. Is DeFT-P faster than the old DeFT, by how much, and is the gap to MTR and RC closed?
**Against the old DeFT (H1, pipe_all 0, 4 scenarios):** supported on 2x2 (THR +17.1 %, LAT -52 %) and 4x4 (THR +10.4 %,
LAT -36 %), both after Holm; not supported on 3x3 (THR -1.2 %, LAT -7 %, n.s.). The aggregate hides opposite signs per
scenario (per-scenario effects, pipe_all 0, unadjusted):
* uniform: LAT -24 / -15 / -26 % and THR +10.4 / +4.9 / +6.3 % on 2x2 / 3x3 / 4x4 (every p < 0.001);
* chipperm: LAT -94 / -54 / -91 %, THR +92 / +5.8 / +60 % (the per-destination entry removes the entry-VL conflict of the
  permutation pairs; the old DeFT and DeFT-B are flagged saturated at 1.0 x Lsat on 2x2 and 4x4 chipperm);
* uniform with one faulty VL per chiplet: LAT -18 % (2x2, p 0.016), otherwise within noise; THR +2.9 / -1.4 / +1.0 %;
* **hotspot: DeFT-P is slower**: LAT +50 / +100 / +146 %, P99 +131 / +398 / +703 %, THR -14.0 / -13.0 / -13.9 % (THR p
  < 0.001 on every size). This matches D1 (DeFT-P's hotspot Lsat is 0.75-0.85 x the old one on 3x3 and 4x4) and the DeFT-B
  rows (DeFT-B keeps the source-keyed entry and shows the same hotspot THR advantage of 13.5-13.9 % over DeFT-P). Interpretation,
  not measured: the destination-keyed entry sends every source's traffic for the hot chiplet through the same entry VL, the
  source-keyed entry spreads it over the four.

**The two paper rules alone (DeFT-B against the old DeFT, i.e. up_keep + rr_fallback, same entry):** THR +6.0 / +6.0 / +4.2 %
and LAT -12 / -7 / -12 % on 2x2 / 3x3 / 4x4 at pipe_all 0 (every p < 0.003; computed from eval_runs.csv with the primary
method, 4 scenarios). The entry change (DeFT-P
against DeFT-B) adds THR +10.4 % (2x2), -6.8 % (3x3), +5.9 % (4x4): the 3x3 loss comes from hotspot (-13.5 %), chipperm
(-4.4 %) and the faulty-VL scenario (-7.7 %).

**Gap to MTR and RC (fault-free scenarios, pipe_all 0):** not closed. DeFT-P against MTR: LAT +24 / +18 / +14 %, THR -5.3 /
-4.2 / -3.6 %; against RC: LAT +30 / +24 / +12 %, THR -6.4 / -4.5 / -3.8 % (2x2 / 3x3 / 4x4).
* **Uniform:** LAT +13 to +21 % and THR -3.6 to -7.7 % behind MTR and RC on every size (every p < 0.002). Against the MTR and
  RC of v19-v21 (no per-hop VC, `MTR_static`, `RC_static`) the THR gap is 1.4-3.3 % and the LAT gap 3-13 %: the per-hop VC
  selection of B3 gives MTR and RC THR +1.6 to +3.8 % and LAT -5 to -12 % of their own.
* **Hotspot:** the gap is wider: LAT +18 to +70 % (p 0.003-0.17), P99 +30 to +175 %, THR -4.6 to -9.8 % (every p < 0.002).
* Chipperm: LAT +0.3 to +9.8 %, THR -0.9 to -3.0 %; on 4x4 at pipe_all 2 DeFT-P has THR +2.2 % (MTR) and +1.3 % (RC).
* At pipe_all 2 the picture is the same (uniform LAT +16 to +41 %, THR -4.3 to -6.0 %; hotspot THR -5.3 to -8.6 %).

### 2. Do the ideal learners keep a gain over DeFT-P?
Partly. **H2 (pipe_all 0, 4 scenarios, Holm over 18):** supported for P99 on 2x2 (CI -36 %, FULL -33 %) and 3x3 (CI -55 %,
FULL -54 %) and for LAT on 2x2 for CI (-14 %); LAT on 3x3 is -23 % for both but n.s. after Holm (unadjusted p 0.014 and
0.016); on 4x4 LAT goes **against** the hypothesis for both learners (CI +37 %, FULL +32 %, Holm p 0.03 and 0.04) and P99 is
n.s. (-9 %, -13 %). The 4x4 reversal is one scenario: on chipperm the learners have LAT +1379 % (CI) and +1424 % (FULL),
THR -31 %, and are flagged saturated at 1.0 x Lsat (their own saturation load is 0.8 x DeFT-P's chipperm Lsat, which is
itself 1.67 x the v19 one). On the three other 4x4 scenarios the learners keep their gain: uniform LAT -7.5 / -16 %, P99 -29 /
-35 %; hotspot LAT -59 / -60 %, P99 -86 %, THR +16 / +15 %; faulty-VL uniform LAT -37 / -41 %, THR +16 / +8 %.

Per scenario the pattern holds on every size: the learners gain on uniform (LAT -3 to -16 %, except FULL on 2x2 +7 %), on
hotspot (LAT -39 to -60 %, THR +8.5 to +18 %) and on the faulty-VL scenario (LAT -16 to -41 %, THR +3 to +16 %); they lose
on chipperm (THR -7 to -31 %, LAT +2 to +1424 %), where DeFT-P's fixed per-destination entry is conflict-free and the
queue-length learners herd. THR on fault-free uniform is a draw to a small loss (CI +3.7 / +5.8 / -2.1 %, FULL -5.0 / -5.8 /
-2.4 %).

At pipe_all 2 (secondary): the learners' aggregate LAT gain grows on 2x2 (CI -25 %) and 3x3 (CI -42 %, FULL -43 %, THR +14.5 /
+5.1 %) and the 4x4 aggregate stays against (+18 / +22 %, again chipperm: +985 / +1295 %); on 4x4 uniform at pipe_all 2 the
learners have LAT -23 / -30 % and P99 -51 / -56 %.

### 3. Does the lookahead model keep most of that gain at pipe_all = 2?
No. With `lookahead_route 1` and the residual decision_delay 1 (`report/lookahead.csv`; uniform, fault-free, seeds 91-95,
against the same learner at decision_delay 0 and pipe_all 2):
* at 0.2 x Lsat the lookahead variants are +10 to +15 % slower (4-7 cycles, about the residual cycle per router on the path);
* at 1.0 x Lsat they are +22 % (2x2 CI), +39 % (2x2 FULL), +521 % (4x4 CI) and +34 % (4x4 FULL) slower than the ideal learner,
  and THR drops 4.0 %, 9.7 %, 17.4 % and 1.9 % (the last n.s.);
* share of the ideal LAT gain over DeFT-P kept at 1.0 x Lsat: negative for 2x2 CI, 2x2 FULL and 4x4 CI (the lookahead variant is
  slower than DeFT-P: 85 against 78 cycles on 2x2 CI, 638 against 133 on 4x4 CI, where the lookahead variant saturates between
  0.8 and 1.0 x Lsat), and 16 % for 4x4 FULL (126 against 133 cycles; THR 0.0605 against DeFT-P's 0.0697 and the ideal
  learner's 0.0636);
* 4.6-5.9 % of the stored decisions differ from the fresh decision at the next router (1.4-3.3 % at 0.2 x Lsat, 4.8-6.5 % at
  2.0 x Lsat).

The low-load cost equals the residual delay; the cost at load grows faster than a fixed cycle per hop, so the stale decisions
(taken one router early on queue state that has changed) carry most of it. The design has no decision_delay-1-without-lookahead
control, so the split between the two is not measured in this round.

### 4. Did the cross-validation with CEA agree?
Yes (`report/cea_crossval.md`). Same 2x2 system, uniform traffic, fault-free, DeFT-B semantics (CEA's format cannot express
the per-destination-router entry): saturation load CEA 0.0115 (rr) / 0.011 (bl) against ours 0.011, deviation 5 % (inside the
15 % band); L0 19.5 against 19.2 cycles; the latency ratio CEA / ours over the 9 ladder loads is 1.00, 0.98, 0.94, 0.99, 1.05
below and at saturation and 1.04-1.22 beyond it; accepted throughput agrees to 1 % at every load; both curves are monotone.
The agreement covers the shared DeFT mechanics (VN rules, round-robin, exit and entry tables); it says nothing about the
per-destination entry or our late-binding modes.

### 5. Which hysteresis D is worth tuning?
(pending D4)
