# Findings v24: late binding without path adaptivity (XY and a VN-split order on the interposer)

Status: complete. Gates passed; tuning 4,560 runs; Part D 14,850 runs, 0 missing, 0 dead-end events
(`report/summary.md`, `eval_runs.csv`).

**Primary result (pre-registered, Holm over 18): 17 supported, 1 against, 0 not significant.** With the implementable
timing (LF), late binding with XY on the interposer beats the best baseline of each scenario on every size in throughput,
mean latency and tail latency. With the VN-split order it does the same on 3x3 and 4x4 and loses 0.5 % of throughput on 2x2.

| size | row (mechanism LF) | THR | LAT at 1.0 × Lsat | P99 at 1.0 × Lsat |
|---|---|---|---|---|
| 2x2 | `CI_qlLA_X` | +3.7 % [+3.3, +4.1] | −18.9 % [−20.1, −17.6] | −40.1 % [−50.6, −27.3] |
| 2x2 | `CI_qlLA_O` | **−0.5 % [−0.8, −0.2] (against)** | −12.9 % [−14.3, −11.6] | −35.5 % [−47.0, −21.5] |
| 3x3 | `CI_qlLA_X` | +9.7 % [+9.3, +10.2] | −17.8 % [−21.3, −14.2] | −45.3 % [−52.9, −36.5] |
| 3x3 | `CI_qlLA_O` | +9.8 % [+9.4, +10.3] | −19.0 % [−22.9, −14.9] | −50.1 % [−57.1, −41.9] |
| 4x4 | `CI_qlLA_X` | +9.1 % [+8.7, +9.5] | −22.5 % [−24.5, −20.4] | −48.0 % [−52.6, −43.0] |
| 4x4 | `CI_qlLA_O` | +10.8 % [+10.4, +11.2] | −26.8 % [−29.0, −24.5] | −56.8 % [−61.3, −51.8] |

Effects are against the best of DeFT-P, DeFT-B, MTR and RC per scenario and metric, averaged over the five scenarios;
95 % intervals over seeds 111-115; every Holm-adjusted p ≤ 0.008. Everything below the primary table is descriptive
(unadjusted).

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
* **Sanity** (`report/sanity.md`): the largest flit rate of any vertical link in any tuning or evaluation run is 0.492 flits
  per cycle (limit 0.5); the two counting options (`count_vl`, `hop_stats`) leave every statistic unchanged.

## Tuning (C2; `tuning.md`, seeds 101-102, 4,560 runs)
* The rule chose, for the heuristic, W 2, B 0, G 1 on both sizes and both relations, with D 2 on 2x2 and D 0 on 4x4 (3x3
  inherits 4x4), and for Q-learning A 0.01 (the smallest value of its grid).
* The hop weight γ = 2 of rounds 8-23 is not kept: with XY or the VN-split order every configuration with G 1 and W 2 scores
  above its G 2 twin; the v10 values score 0.32 / 0.18 (2x2, X / O) and 0.53 / 0.68 (4x4) against 0.55 / 0.44 and 0.65 / 0.76
  for the chosen ones.

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
* Part D confirms it at pipe_all 2 on seeds 111-115: on 4x4 chipperm `CI_qlLA_G` reaches THR 0.0292 and latency 2,109 at
  1.0 × Lsat, against 0.0583 and 137 for `CI_qlLA_X`.

### 3. With an ideal decision, which interposer order wins in which scenario: X, O or odd-even?
XY wins three scenarios, the VN-split order wins chiptrans, and odd-even wins none (`CI_qlLA_X`, `CI_qlLA_O`, `CI_qlLA_G`
with an ideal decision; THR and LAT at 1.0 × Lsat on 2x2 / 3x3 / 4x4).

| scenario | THR: X | O | odd-even | LAT: X | O | odd-even | winner |
|---|---|---|---|---|---|---|---|
| uniform | 0.1316 / 0.1020 / 0.0844 | 0.1282 / 0.0991 / 0.0816 | 0.1260 / 0.0943 / 0.0693 | 63 / 82 / 92 | 66 / 84 / 93 | 69 / 90 / 102 | X |
| chipperm | 0.1126 / 0.0966 / 0.0583 | 0.0966 / 0.0941 / 0.0548 | 0.0932 / 0.0756 / 0.0292 | 94 / 81 / 137 | 136 / 85 / 135 | 217 / 107 / 2109 | X |
| chiptrans | 0.1668 / 0.0834 / 0.0597 | 0.1684 / 0.0978 / 0.0767 | 0.1669 / 0.0938 / 0.0721 | 56 / 66 / 93 | 51 / 54 / 66 | 58 / 57 / 70 | O |
| hotspot | 0.0765 / 0.0351 / 0.0198 | 0.0766 / 0.0352 / 0.0198 | 0.0760 / 0.0354 / 0.0199 | 55 / 58 / 67 | 55 / 58 / 67 | 56 / 59 / 68 | none (within 1 %) |
| faulty | 0.1012 / 0.0770 / 0.0631 | 0.0983 / 0.0746 / 0.0612 | 0.0999 / 0.0767 / 0.0600 | 70 / 78 / 95 | 73 / 80 / 96 | 71 / 77 / 91 | X in THR |

* **O against X over the five scenarios:** THR −3.8 % / +1.5 % / +2.5 %, LAT +7.4 % / −2.0 % / −6.5 %, P99 +8.5 % / −9.7 % /
  −18.4 % (2x2 / 3x3 / 4x4). The gain of O on the larger sizes is chiptrans alone (THR +17 % on 3x3 and +28 % on 4x4 over X);
  on the other four scenarios X has the same or a higher THR on every size (O gives up about 3 % on uniform and faulty and
  3-14 % on chipperm; on hotspot the two are equal).
* **Odd-even against X:** THR −4.9 % / −3.9 % / −13.9 %, LAT +22 % / +5 % / +66 %. It is second on chiptrans (3x3 and 4x4) and
  has the lowest P99 on the faulty scenario (185 against 200 on 3x3, 207 against 233 on 4x4); it loses chipperm on every size.
* The review expected XY to be weak on transpose-like traffic "as every baseline". Measured: on chiptrans XY late binding is
  weaker than O but still above the best baseline (THR +3.7 % / +5.1 % / +6.4 %, LAT −29 % / −19 % / −45 %, ideal decision).

### 4. Against the best baseline, what do CI_qlLA_X and CI_qlLA_O gain or lose with LF?
Per size: the table at the top. Per scenario (LF, against the best baseline of the scenario; 2x2 / 3x3 / 4x4):

| scenario (best baseline: THR; LAT) | `CI_qlLA_X` LF: THR | LAT | P99 | `CI_qlLA_O` LF: THR | LAT | P99 |
|---|---|---|---|---|---|---|
| uniform (RC, MTR, RC; RC, MTR, RC) | −2.2 / +9.7 / +12.7 % | +3.6 / −20.7 / −7.7 % | −7 / −55 / −26 % | −5.1 / +6.4 / +8.1 % | +8.0 / −18.1 / −6.5 % | −2 / −55 / −26 % |
| hotspot (DeFT-B on every size) | +1.9 / +1.4 / +3.1 % | −11.6 / −3.6 / −2.2 % | −24 / −5 / −2 % | +0.8 / +1.1 / +2.8 % | −11.4 / −3.2 / −1.8 % | −29 / −8 / −2 % |
| chipperm (MTR, DeFT-B, DeFT-P; MTR, MTR, RC) | +8.1 / +24.4 / +8.9 % | −26.6 / −29.4 / −17.0 % | −56 / −65 / −40 % | −6.3 / +14.6 / +1.0 % | +3.9 / −25.8 / −18.5 % | −29 / −64 / −49 % |
| chiptrans (RC, MTR, MTR; MTR on every size) | +2.7 / +5.1 / +6.4 % | −26.5 / −16.8 / −45.5 % | −54 / −47 / −77 % | +3.9 / +22.8 / +35.5 % | −32.4 / −31.2 / −60.1 % | −59 / −67 / −89 % |
| faulty (DeFT-B; DeFT-P, DeFT-B, DeFT-B) | +8.4 / +9.4 / +14.9 % | −28.9 / −16.4 / −31.4 % | −47 / −39 / −62 % | +4.5 / +5.5 / +9.9 % | −25.6 / −13.9 / −29.6 % | −45 / −38 / −62 % |

* **Where they lose.** On 2x2 uniform both are behind RC (X: THR −2.2 %, LAT +3.6 %; O: THR −5.1 %, LAT +8.0 %); with an
  ideal decision X is level with RC there (THR +0.7 %, LAT +0.1 %), so that loss is the cost of LF. O also loses 2x2 chipperm
  to MTR (THR −6.3 %).
* **Where the gain is small.** Hotspot: the best baseline is DeFT-B on every size and metric (DeFT-P loses 16-17 % of THR
  there, as in v23); the candidates are +1 to +3 % in THR and their P99 gain is inside the interval on 3x3 and 4x4.
* **Where it is large.** Chipperm and the faulty scenario for X (THR +8 to +24 %, P99 −39 to −65 %); chiptrans for O
  (THR +23 % and +36 % on 3x3 and 4x4).
* **Where THR sits.** On chiptrans the accepted throughput of every row still grows at the top load (the chiplets on the
  diagonal send inside their own chiplet), so THR there is the value at 2.4 × Lsat; on 4x4 O delivers 92 % of the offered load
  at that point, so its +36 % is close to what the ladder can show. On the other scenarios the maximum lies between 1.2 and
  2.4 × Lsat and the plateau is flat (question 9).
* The baselines among themselves, for scale (4x4, against the best baseline): DeFT-P THR −5.4 %, LAT +29 %, P99 +82 %; MTR
  −4.0 %, +13 %, +55 %; RC −4.0 %, +13 %, +50 %; DeFT-B −20 %, +138 %, +201 %.

### 5. What do LF and DLY cost against ideal? Is the lookahead needed? How rare are the decision hops?
**Cost against the ideal decision of the same candidate** (five scenarios; 2x2 / 3x3 / 4x4; the rows show relation X, and
O is within a point of it in latency and THR):

| mechanism | LAT at 0.2 × Lsat | LAT at 0.5 × Lsat | LAT at 1.0 × Lsat | P99 | THR |
|---|---|---|---|---|---|
| LF, heuristic (residual 0) | +0.2 / +0.1 / +0.1 % | +0.2 / +0.2 / +0.1 % | +0.5 / +0.2 / −0.6 % | +1.5 / +0.5 / −0.5 % | −1.5 / −2.3 / −1.1 % (O: −2.0 / −3.0 / −1.7 %) |
| LF, Q-learning (residual 1) | +3.9 / +3.1 / +2.7 % | +3.8 / +3.4 / +2.9 % | +3.1 / +2.8 / +1.9 % | +3.5 / +1.3 / +0.5 % | −1.7 / −1.7 / −1.0 % (O: −2.0 / −3.1 / −1.9 %) |
| DLY, heuristic (2 cycles) | +7.6 / +5.3 / +4.8 % | +6.8 / +5.3 / +4.7 % | +5.2 / +5.0 / +5.0 % | +2.1 / +2.9 / +4.7 % | 0.0 / 0.0 / −0.1 % |
| DLY, Q-learning (3 cycles) | +11.5 / +8.7 / +7.6 % | +10.6 / +8.8 / +7.8 % | +8.2 / +7.9 / +8.6 % | +5.5 / +5.2 / +10.8 % | −0.1 / −0.2 / −0.5 % |

* **LF costs throughput, DLY costs latency.** LF keeps the latency of the ideal decision (the heuristic within 0.6 % with X
  and within 1.5 % with O) and loses 1-3 % of THR. DLY keeps the THR and adds 5-12 % of latency at every load. DLY against LF: LAT at 0.2 × Lsat +7.4 /
  +5.3 / +4.7 %, LAT at 1.0 × Lsat +3 to +7 %, THR +0.6 to +3.7 %.
* **Is the lookahead needed?** For the gain over the baselines, no: with DLY the candidates still beat the best baseline
  (`CI_heurLA_X` DLY: THR +5.7 / +12.8 / +10.4 %, LAT −17.1 / −15.3 / −19.8 %, P99 −40 / −44 / −46 %). For the low-load latency,
  yes: DLY is slower than DeFT-P at 0.2 × Lsat (+2 to +10 %, question 8) and LF is not.
* **The fallback matters, the residual cycle costs what one cycle costs** (controls, `CI_qlLA_X`, uniform). Without the
  fallback (residual 1) the lookahead is +7.0 / +9.5 / +8.7 % in LAT at 1.0 × Lsat and +9 / +17 / +14 % in P99 against ideal;
  the fallback takes back 3.4 / 6.1 / 5.6 points of LAT and 5 / 12 / 11 points of P99. With the fallback at residual 0 the
  latency equals the ideal one (+0.2 to +1.2 %) and the THR loss stays (−2.9 / −2.4 / −1.8 %): the THR loss of LF comes from
  deciding one hop early, not from the residual cycle.
* **Decision hops are rare with X and O.** Hops that offer more than one output: 17 % / 13 % / 11-12 % of all hops (26 % /
  18-19 % / 14-15 % of the interposer hops, none in the chiplets), 1.6-1.8 per packet. With odd-even: 42 % / 48 % / 50 % of all hops,
  3.9 / 6.0 / 7.6 per packet; with the late exit (`FULL_qlLA_X`): 29 % / 24 % / 21 %.
* **Stale decisions and fallbacks.** 1.4-2.3 % of the stored decisions differ from a fresh one when the head arrives
  (7-17 % of those at decision hops: 9-17 % for the heuristic, 7-11 % for Q-learning). The head leaves through another output
  than the stored one at 6.6-9.4 % of the decision hops.

### 6. What does each piece of information add (random, occupancy, one-hop lookahead, Q-learning)?
Occupancy is nearly all of it (relation X, ideal decision, five scenarios; each row against the row above; 2x2 / 3x3 / 4x4).

| selection | THR against the best baseline | THR against the row above | LAT at 1.0 × Lsat against the row above | LAT at 1.4 × Lsat against the row above |
|---|---|---|---|---|
| random among the offered outputs (`CI_rand_X`) | −5.2 / +0.2 / +1.7 % | – | – | – |
| downstream occupancy (`CI_heur_X`) | +5.0 / +11.0 / +8.6 % | +10.8 / +10.8 / +6.7 % | −22.0 / −11.2 / −10.3 % | −40.5 / −50.5 / −25.7 % |
| plus one-hop lookahead (`CI_heurLA_X`) | +5.7 / +12.8 / +10.5 % | +0.7 / +1.6 / +1.8 % | −4.0 / −3.7 / −5.5 % | −4.8 / −10.4 / −10.1 % |
| plus Q-learning (`CI_qlLA_X`) | +5.5 / +11.6 / +10.3 % | −0.2 / −1.0 / −0.2 % | −0.2 / −0.8 / −0.4 % | −1.0 / +1.6 / +1.1 % |

* Late binding with a random choice is level with the best baseline in THR on 3x3 and 4x4 and already lowers LAT (−6 %,
  −10 %) and P99 (−30 %, −29 %) there; on 2x2 it is behind (THR −5.2 %). It takes 6-12 % more hops than the informed
  selections and is 6-9 % slower than DeFT-P at low load.
* The one-hop lookahead adds 1-2 % of THR and 4-10 % of latency.
* **Q-learning adds nothing** (the tuned rate is 0.01, the lower edge of its grid): no THR, less than 1 % of latency, and in
  mechanism LF it costs a residual cycle. The review's 4x4 uniform probe (0.0798 / 242 → 0.0803 / 185 at 1.4 × Lsat) is not
  seen with the tuned parameters at pipe_all 2: 0.0842 / 392 for the heuristic against 0.0838 / 411 with Q-learning.

### 7. What does the VN-split order do without late binding, and late binding without it?
* **The VN-split order alone** (`DeFT_P_O1` against DeFT-P, the same VL pairs): THR −3.8 % / +1.2 % / +1.2 % over the five
  scenarios. It helps on chiptrans (THR +2.7 / +16.5 / +23.0 %, LAT −29 / −36 / −68 %) and on hotspot latency (−54 % and −42 %
  on 3x3 and 4x4, with THR −2.5 % and −0.1 %), costs 2-3 % of THR on uniform and on the faulty scenario, and loses chipperm on
  2x2 and 4x4 (THR −15.5 % and −8.2 %, LAT +326 % and +43 %).
* **Late binding alone** (`CI_qlLA_X` against DeFT-P, XY as DeFT-P): THR +12.2 / +20.6 / +16.6 %, LAT −37 / −45 / −41 %,
  P99 −58 / −76 / −72 %, positive in every scenario on every size.
* **Late binding on top of the VN-split order** (`CI_qlLA_O` against `DeFT_P_O1`): THR +12.1 / +21.0 / +18.1 %, LAT −49 /
  −25 / −27 %, P99 −66 / −50 / −52 %.
* So late binding is worth +12 to +21 % of THR with either order. The order adds little on average (−3.8 % / +1.2 % / +1.2 %
  without late binding, −3.8 % / +1.5 % / +2.5 % with it): it moves throughput from uniform, chipperm and faulty traffic to
  transpose-like traffic. On chiptrans the order does the work (O1 alone +23 % on 4x4, late binding adds +12 % to it);
  elsewhere late binding does.

### 8. What is the low-load cost of every candidate against DeFT-P?
None for the ideal decision and for LF with the heuristic; one cycle on 2x2 for LF with Q-learning; 1-4 cycles for DLY
(LAT against DeFT-P over the five scenarios; 2x2 / 3x3 / 4x4; the rows show relation X, and O is within a point of it).

| mechanism | LAT at 0.2 × Lsat | in cycles | LAT at 0.5 × Lsat |
|---|---|---|---|
| ideal, heuristic | −2.0 / −3.3 / −2.7 % | −0.8 / −1.7 / −1.8 | −2.7 / −3.1 / −2.2 % |
| ideal, Q-learning | −1.0 / −3.5 / −2.9 % | −0.4 / −1.8 / −1.9 | −2.0 / −4.1 / −3.0 % |
| LF, heuristic | −1.8 / −3.1 / −2.6 % | −0.7 / −1.6 / −1.7 | −2.4 / −2.9 / −2.2 % |
| LF, Q-learning | +2.8 / −0.5 / −0.3 % | +1.2 / −0.3 / −0.1 | +1.7 / −0.8 / −0.2 % |
| DLY, heuristic | +5.5 / +1.9 / +1.9 % | +2.2 / +1.0 / +1.3 | +4.0 / +2.1 / +2.4 % |
| DLY, Q-learning | +10.4 / +5.0 / +4.5 % | +4.3 / +2.6 / +3.0 | +8.4 / +4.4 / +4.6 % |

* The candidates start below DeFT-P because their paths are shorter at low load: 8.51 / 11.61 / 14.90 hops per packet at
  0.2 × Lsat against 8.66 / 11.99 / 15.29 for DeFT-P's VL pairs (`DeFT_P_O1`). At 1.0 × Lsat they take 8.9 / 12.2 / 15.7:
  they pay hops to avoid queues.
* With γ = 2 this was the other way round (question 2 and the review's item 5); the tuning removed it.
* Other rows at 0.2 × Lsat: `FULL_qlLA_X` −2.6 / −5.7 / −4.9 %; `CI_qlLA_G` −1.4 / −2.1 / −1.7 %; `CI_rand_X` +9.2 / +6.7 /
  +5.6 %; MTR +2.8 / +2.3 / +1.9 %; RC +1.0 / +0.9 / +0.8 %.

### 9. Is the accepted throughput monotone beyond saturation for the candidates?
It reaches a flat plateau; it is not strictly monotone, and neither are the baselines.
* **Loss after the peak** (lowest accepted throughput at any load beyond the peak, relative to the peak; mean and worst of
  the five scenarios): the twelve candidate rows keep 98.6-100 % on average; the worst cells are 95.7 % (2x2, `CI_qlLA_O`,
  hotspot), 94.4 % (3x3, `CI_qlLA_O` LF, chipperm at 1.6 × Lsat, back to 99.5 % at 2.4 ×) and 96.4 % (4x4, `CI_heurLA_O` DLY,
  hotspot). The baselines: 98.5-100 % on average, worst cells 97.0 %, 99.1 % and 97.2 %.
* At 2.4 × Lsat every candidate row is at 98.8-100 % of its peak on average.
* The accepted throughput never falls by more than 1 % from one load to the next in 3-5 of the 5 scenarios for the candidate
  rows (2 of 5 for `CI_heurLA_X` LF on 2x2); for the baselines in 2-5.
* The collapse of v23 belongs to odd-even and to the late exit: `CI_qlLA_G` keeps 94.8 % on 4x4 (worst cell 88.1 %),
  `FULL_qlLA_G` 89-92 % (worst 74.5 %), `FULL_qlLA_X` 92.6 / 93.7 / 97.9 % (worst 86.5 %).

### 10. Which configuration should be the main one in the confirmatory round, and why?
**`CI_heurLA_X` in mechanism LF** (late entry, XY on both layers, the lookahead heuristic with W 2, B 0, G 1 and D 2 on 2x2 /
D 0 on 3x3 and 4x4, lookahead routing with the fallback and the busy state, no residual delay), with **`CI_heurLA_O` in
mechanism LF** as the second pre-registered configuration.
* **The heuristic, not Q-learning.** Q-learning adds nothing measurable (question 6) and costs a table (v18: 1.3-1.6 times
  DeFT's router area against 1.1-1.2 for the heuristic) and a residual cycle. In mechanism LF the heuristic rows are at least
  as good as the Q-learning rows on every size and metric: `CI_heurLA_X` LF has THR +4.1 / +10.2 / +9.3 %, LAT −20.7 / −19.2 /
  −24.0 %, P99 −40.5 / −45.6 / −48.5 % against the best baseline, and it is 2-3 % faster than DeFT-P at low load.
* **X as the main relation.** It gains on every size, it does not lose 2x2 as O does (O with the heuristic and LF: THR
  −0.6 %, with −5 % on uniform and −7 % on chipperm), it has the highest THR, or the same, in four of the five scenarios, it
  needs no second dimension order, and its decision hops are rare.
* **O as the second.** It is the only relation that removes XY's weakness on transpose-like traffic (+23 % and +37 % of THR on
  3x3 and 4x4 chiptrans against +5 % and +6 % for X) and it is ahead of X on 4x4 in all three metrics (THR +11.6 against
  +9.3 %, LAT −28.4 against −24.0 %, P99 −57.2 against −48.5 %). Which of the two a system wants depends on how much of its
  traffic is transpose-like; the confirmatory round should report both and not pick by result.
* **LF as the mechanism.** It keeps the latency of the ideal decision at every load for 1-3 % of THR; DLY keeps the THR and
  gives up the low-load latency.
* **What the confirmatory round should fix in advance:** the tuned values as they are (no retuning); fresh seeds; the best
  baseline per scenario as the reference; the 2x2 uniform cell as a stated risk (X with LF: THR −1.2 %, LAT +1.0 % against RC).
* Not for the main line: odd-even on the interposer (loses chipperm, question 2), the late exit (`FULL_qlLA_X`: THR 4-8 %
  below `CI_qlLA_X` and a falling plateau), and the Q-learning grid below 0.01 unless a round is spent on it.
