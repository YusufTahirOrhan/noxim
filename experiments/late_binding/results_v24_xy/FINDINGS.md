# Findings v24: late binding without path adaptivity (XY and a VN-split order on the interposer)

Status: in progress. Done: A0, A1, B1-B5, A2, A3, A4 (gates passed). Running: C2 (tuning). To do: Part D.

## Gates
* **Regression** (`regression.md`): 84 / 84 configurations byte-identical to the 8d84634 build, with the new options absent and
  with every option given explicitly off.
* **`busy_state` without lookahead** (`busy_state_check.md`): 10 / 10 runs identical in every statistic.
* **Q-learning with α = 0 against the heuristic under lookahead, fallback and busy state** (`equivalence.md`): 10 / 10 pairs
  identical (five parameter sets, 2x2 and 4x4, loads up to 2.4 × Lsat).
* **Model check** (`formal_xy.md`): `CI_XY_XY`, `FULL_XY_XY`, `CI_XY_O1`, `FULL_XY_O1`, `FIXED_XY_O1` on all 897 masks of
  2x2, 22 masks of 3x3 and 2 masks of 4x4, and two YX relations on 2x2: acyclic CDG, no dead end, no livelock (longest path
  24 / 32 / 40 hops). The negative control reports a cycle.
* **Drain tests** (`drain_summary.csv`): 1,254 / 1,254 pass, 0 dead-end events. The five Part C variants with their v10
  parameters and `DeFT_P_O1` at pipe_all 2 and 0 (684 runs), the five variants with `lut_bias 4` (285) and with the lookahead
  fallback and the busy state (285); each set has the v10 protocol on the three sizes plus 4x4 runs at 2.4 × Lsat on uniform,
  chipperm and chiptrans.

## The ten questions

### 1. Do the probe numbers reproduce (A0, B4, B5)?
Yes, all of them (`reproduction.md`).
* **A0** (existing options, the 8d84634 build): 10 / 10 rows identical in received packets and in latency to the ten printed
  decimals.
* **B4** (the options of this round): 6 / 6 values identical to the printed digits: `lut_bias 4` 0.0326 / 70.8, γ = 1
  0.0532 / 378.9, the lookahead fallback 0.0647 / 94.4 and 0.0831 / 467.5, the VN-split order 0.0793 / 253.2 and
  0.0479 / 735.3. One detail had to be settled for the fallback: read from the router's own buffer-full signal instead of the
  neighbour's buffer, its two rows are 0.0647 / 95.4 and 0.0831 / 446.9 (+1.1 % and −4.4 % latency). The two readings differ by
  less than 0.4 % in THR and LAT on the tuning seeds; the direct read is kept (`DECISIONS.md`, B2).
* **B5** (chiptrans, 4x4, rate 0.0060): DeFT-P 0.0421 / 514, MTR 0.0420 / 465, CI_qlLA_G 0.0485 / 66, with XY 0.0431 / 461,
  with the VN-split order 0.0486 / 49, DeFT_Dis with the VN-split order 0.0485 / 52: all six as probed.
* One statement of the review is measured differently in count only: DeFT-P and DeFT_Dis coincide on **810 of 810**
  fault-free run pairs of `results_v23_fidelity/eval_runs.csv` (both pipe depths; accepted, latency, p99, injected and
  received equal), not 405; with a faulty VL per chiplet none of the 270 pairs coincide. So DeFT_Dis is not a row of this
  round's tables; it appears only in A4 and in the hop-count sanity check.

### 2. What limits odd-even on chipperm (A4)?
The turn rules, not the VL choice (`centre_cut.md`; 4x4 chipperm at 0.8 × Lsat, pipe_all 0, seeds 101-102). With fixed VLs and
odd-even paths chosen by the v10 heuristic the network is already saturated: it accepts 0.0204 of the 0.0320 offered
(latency 865), where the same VLs with XY deliver everything at latency 68.
* Every packet of chipperm crosses both centre cuts; at this load that is 4.1 flits per cycle per direction over 16
  channels of 0.5. XY spreads it evenly: 0.22-0.28 per channel, max / mean ≤ 1.10.
* Odd-even forbids East → North and East → South in even columns, so the vertical part of the east-bound traffic runs on odd
  columns: in the east half the odd columns 9, 11, 13 carry 0.25-0.42 flits per cycle and the even ones 0.01-0.11 (max / mean
  2.4-2.7); the fullest channel is at 0.435 of 0.5.
* The blocking spreads: the westward crossing of the vertical cut carries 1.49 flits per cycle instead of 4.1, with 13
  waiting cycles per flit. The VLs carry 0.15-0.16 as with XY, so they are not the limit.
* This agrees with the review's item 1. Which packets block which is read from the turn rules and the waiting counts (the
  statistics do not separate east-bound from west-bound flits).
* The same table shows the low-load cost of the hop weight γ = 2 with XY: `CI_qlLA_X` with the v10 parameters puts the
  vertical crossings on the eight columns of the two nearest entry VLs (0.34-0.44 per channel, the fullest Up VL at 0.31
  against 0.16) and has latency 78 against 68.

### 3-10
Pending Part D.
