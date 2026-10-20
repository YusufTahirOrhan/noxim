# v7 findings: bounded-deviation entry for interposer-only late binding

Design: `PREREGISTRATION.md` (committed before the drain tests and the evaluation of the bounded variants). Decisions:
`DECISIONS.md`. Selection: `selection.md`. Bottleneck statistics: `bottleneck.md`, `bottleneck_tables.md`. Tables:
`report/summary.md`, `report/primary.csv`; figure `report/effect_bound.png`. Per-run data: `eval_runs.csv` (1960 runs,
v6 columns), `eval_cand.csv` (entry candidates), `vlref_runs.csv`, `select_runs.csv`.

Run integrity:
* Evaluation: 1960 / 1960 new runs (seeds 31-40), 0 missing, 0 dead-end events, 0 LUT fallbacks. DeFT_tm(rho*),
  CI_heurLA and CI_qlLA come from `results_v6/eval_runs.csv`.
* Determinism, which makes the v6 runs reusable: 20 / 20 re-run v6 evaluation runs and 280 / 280 re-run parent runs
  are identical; the step-2 DeFT_tm runs reproduce v6's statistics exactly.
* Option off: 198 / 198 regression runs identical to the v6 binary.
* Drain: 16 / 16 PASS.
* Formal check, on 3x3 with every non-empty initial entry subset: 12 / 12 pass.

## 1. The option and the selection (steps 1 and 3)
* **What the bound does.** At injection, CI's entry candidates are cut to those whose shortest turn-legal path is
  at most k hops longer than the shortest one (mode min) or than the LUT entry's (mode lut).
* **Tight bounds hurt on 4x4** (seeds 101/102, saturation throughput against the unbounded parent):
  - mode min, k 0: -15 %, with 3-4 times the latency;
  - mode lut, k 0: -6 % to -7 %, with 12-22 % more latency.
  - k = 1 equals k = 0 (path-length parity).
* **Chosen** (only the loosest bounds of the grid met the 5 % latency constraint):

  | variant | mode, k | entry candidates left (of 4) | throughput vs parent (selection) | latency vs parent (selection) |
  |---|---|---|---|---|
  | CI_heurLA_B | lut, 4 | about 3.65 | +1.3 % | -0.2 % |
  | CI_qlLA_B | min, 4 | about 3.35 | +2.1 % | -4.5 % |

  Both lie at the top of the k grid, which was not extended (DECISIONS 13).

## 2. Primary results (pre-registered; Holm over 24 tests; 13 significant)
% change, mean over the 7 scenarios of the size, 95 % CI over seeds 31-40. Bold = significant after Holm.

**Against DeFT_tm(rho*) (12 tests, all significant).** In brackets: the unbounded parent (v6, same runs).

| size | variant | mean latency @1.0 Lsat | p99 latency @1.0 Lsat | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA_B | **-13.4** [-15.4, -11.4] (-13.6) | **-30.5** [-34.9, -25.8] (-30.4) | **-1.75** [-2.33, -1.17] (-2.61) |
| | CI_qlLA_B | **-15.1** [-18.2, -11.9] (-17.0) | **-32.9** [-39.1, -26.0] (-36.7) | **-1.98** [-2.63, -1.33] (-1.35) |
| 4x4 | CI_heurLA_B | **-20.3** [-25.6, -14.6] (-19.9) | **-38.1** [-44.3, -31.2] (-35.8) | **-7.88** [-8.85, -6.91] (-9.64) |
| | CI_qlLA_B | **-24.2** [-29.8, -18.2] (-23.8) | **-43.9** [-50.5, -36.3] (-43.6) | **-5.51** [-6.32, -4.70] (-5.72) |

**Against the unbounded parents (12 tests, 1 significant).**

| size | comparison | mean latency | p99 latency | saturation throughput |
|---|---|---|---|---|
| 3x3 | CI_heurLA_B vs CI_heurLA | +0.2 [-2.3, +2.7] (n.s.) | -0.1 (n.s.) | **+0.88** [+0.45, +1.31] (Holm p 0.015) |
| | CI_qlLA_B vs CI_qlLA | +2.2 [-0.5, +5.0] (n.s.) | +6.1 [-0.2, +12.8] (n.s.) | -0.64 [-1.28, -0.01] (Holm p 0.48, n.s.) |
| 4x4 | CI_heurLA_B vs CI_heurLA | -0.6 [-2.5, +1.5] (n.s.) | -3.6 [-8.5, +1.6] (n.s.) | +1.94 [+0.74, +3.16] (Holm p 0.058, n.s.) |
| | CI_qlLA_B vs CI_qlLA | -0.5 [-3.8, +2.8] (n.s.) | -0.4 [-8.9, +8.9] (n.s.) | +0.21 [-0.72, +1.16] (n.s.) |

**What the bound does:**
* **Latency:** no significant change on either size; the bounded variants keep the full latency benefit of late
  binding over DeFT_tm(rho*).
* **Throughput, heuristic:** a small gain, significant only on 3x3 (+0.9 %). On 4x4 it is +1.9 % (Holm p 0.058); the
  gap to DeFT_tm narrows from -9.6 % to -7.9 % but stays large.
* **Throughput, learner:** no gain on either size. On 3x3 the point estimate is slightly negative.
* **Against DeFT_tm(rho*):** every bounded variant is still significantly faster and has significantly lower
  saturation throughput on 9 and 16 chiplets.

## 3. Secondary (unadjusted)
* **Without chipperm:**
  - 3x3: the bounded variants gain throughput over DeFT_tm(rho*) (+2.8 %, +2.6 %; parents +1.9 %, +3.2 %).
  - 4x4: they are still below (-4.1 %, -1.9 %; parents -5.3 %, -2.0 %).
  - Chipperm is unchanged: still -25 % to -28 % for every variant.
* **4x4 per scenario, CI_heurLA_B vs its parent:**
  - The gains are on uniform (+2.7 %), localized (+4.3 %) and chipperm (+6.0 %).
  - Uniform is still -14.9 % against DeFT_tm(rho*) (parent -17.1 %).
  - For CI_qlLA_B no per-scenario change against the parent is significant.
* **Entry candidates:** the bound removes on average 0.35 (lut, 4) and 0.65 (min, 4) of 4 candidates (of 3 with
  faults), independent of load and almost independent of the pattern (`report/summary.md`).
* **VL imbalance (all VLs, corrected):**
  - The bound leaves it unchanged (4x4 uniform: CI_heurLA 1.28 -> 1.27, CI_qlLA 1.20 -> 1.21; DeFT_tm(rho*) 1.11).
  - **Correction to v4-v6:** their 3x3/4x4 VL imbalance tables covered only VL ids 0-15 (`vlref_check.md`).
    Corrected, DeFT_tm(rho*) is still the most balanced on every 4x4 scenario, but the v6 statement that CI_qlLA is
    close to it on 4x4 uniform (1.11-1.12) does not hold: corrected values are 1.20 (fault-free) and 1.33 (with
    faults), against 1.11 and 1.14.

## 4. Bottleneck comparison (step 2; 4x4, seeds 101-103; `bottleneck.md`)
4x4 uniform, 1.0 x Lsat:

| variant | interposer link load | centre / rest | entries differing from the LUT | mean extra hops |
|---|---|---|---|---|
| DeFT_tm(rho*) | 0.131 | 1.40 | 0 % | 0 |
| CI_heurLA, v5 parameters (v6 run) | 0.146 | 1.94 | 77 % | +0.46 |
| CI_heurLA, tuned | 0.144 | 1.94 | 75 % | +0.20 |
| CI_heurLA_B | 0.143 | 1.93 | 74 % | +0.08 |
| CI_qlLA, tuned | 0.143 | 1.80 | 74 % | +0.11 |
| CI_qlLA_B | 0.142 | 1.82 | 74 % | -0.11 |

Centre / rest = mean load of interposer links inside the central 8x8 routers over the others.
* **Beyond the knee** (1.2 x Lsat, uniform): the bound raises accepted throughput by 8 % (heuristic) and 3 % (learner)
  and shortens the queues at chiplet VL endpoints (42.7 -> 36.8 and 34.8 -> 31.4 cycles per hop). Both remain
  12 % and 8 % below DeFT_tm(rho*).

## 5. Is the v6 hypothesis supported? **No.**
Pre-registered criterion: (a) the bound moves CI's interposer load and centre concentration towards DeFT_tm(rho*),
and (b) it raises saturation throughput significantly against the unbounded parent.

* **Shown:**
  - (a) does not hold. With the chosen bounds, interposer link load falls by only 0.001 (0.144 -> 0.143 and
    0.143 -> 0.142, against 0.131 for DeFT_tm), and the centre / rest ratio does not change (1.93 and 1.82 against
    1.40). About 74 % of entries still differ from the LUT's. **The centre concentration does not disappear.**
  - (b) holds in 1 of 4 tests, the heuristic on 3x3 (+0.9 %). On 4x4, where the gap is, neither variant improves
    significantly.
  - The bound does what it is designed to do: it removes most of the remaining detours (mean extra hops +0.20 ->
    +0.08 and +0.11 -> -0.11) and helps a little beyond the knee. So long entry detours exist, but they are not what
    loads the interposer centre.
  - Forcing entries closer to the shortest or the LUT one (k 0-2) makes throughput clearly worse (-5 % to -15 %).
    Distance to a short or LUT entry is therefore not what limits CI.
* **Not shown / remaining hypotheses (not isolated):**
  - The centre concentration exists already for DeFT_tm(rho*) (1.40) and for every late-binding variant, FULL
    included (v6: 2.05), irrespective of how close the entry is. A remaining candidate is the router-local
    odd-even path choice on the interposer itself (which minimal path a packet takes to its entry), not the choice
    of entry VL.
  - A second candidate is the exit side: CI's exits are fixed by a LUT balanced for DeFT's XY paths, not for
    odd-even interposer routing.
  - Neither was tested in v7.

## 6. Limitations
* The bound was selected on 4x4 only (2 seeds, 5 loads) and transferred unchanged to 3x3. Both choices lie on the
  edge of the k grid (k 4, not extended), where the bound is loose (0.35-0.65 candidates removed).
* Step 2 used 3 seeds and two patterns.
* As before: one window, synthetic traffic, one chiplet size; the load points come from DeFT(rho*).

## Bottom line
* **Latency:** a bound on the entry candidates keeps CI's latency benefit (-13 % to -24 % mean, -30 % to -44 % p99
  against DeFT_tm(rho*)).
* **Throughput:** it adds at most about 1-2 % for the heuristic and nothing for the learner. The 4x4 gap to
  DeFT_tm(rho*) remains (-7.9 % and -5.5 %).
* **The v6 explanation:** it is not supported. CI's extra interposer load and its concentration in the centre are not
  caused by entries far from the short or LUT path.
