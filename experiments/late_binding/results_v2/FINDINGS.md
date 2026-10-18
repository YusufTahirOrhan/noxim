# DEFT_LB evaluation v2: findings

Second evaluation, built to close the validity gaps of v1 (`results/eval_report/FINDINGS.md`):
a traffic-matched DeFT baseline (DeFT_tm), information-matched learners (QL-LA), per-scope
tuning with recorded budgets, per-scenario load points, 10 seeds, a pre-registered primary
analysis with Holm correction, HL-fault coverage in the formal model, and a hardware-cost
estimate. The decisions taken without the author are listed in `DECISIONS.md`.

Sources: `report/summary.md` (all tables), `report/primary.csv`, `report/paired.csv`, figures in
`report/`, `PREREGISTRATION.md` (committed before the first evaluation run), `tuning_budget.md`,
`hl_coverage.md`, `hw_cost.md`.

## Read this first
* **Only the 16 pre-registered tests below are significance claims** (Holm, family-wise
  alpha = 0.05). Everything else is secondary. Secondary intervals are unadjusted and marked
  `°` in summary.md when they exclude 0; they are not called significant here.
* **A_oracle can't be implemented in hardware.** It uses instantaneous global occupancy at
  injection, so it is an upper bound for injection-time VL choice only.
* **Capped throughput.** Saturation throughput (THR) is the maximum accepted throughput
  over loads up to 1.6 x DeFT's Lsat. On the three chipperm scenarios DeFT_tm and every
  late-binding variant still accept >= 95 % of the highest load, so their THR is a lower
  bound there (30 of the 110 seed-scenario cells of every primary THR test). A sensitivity
  analysis without those scenarios is reported (secondary).
* **Scope of validity.** One topology instance (4 chiplets of 4x4, 16 VLs), one window
  (2000 + 8000 cycles), synthetic traffic, and 10 seeds.
* **The learners got more tuning than the heuristics.** Each learner got 10 configurations
  of its own on top of the 9 that fixed its local weights; each heuristic got 9. Several
  optima lie on a grid edge (w = 2; CI QL alpha = 0.005). See `tuning_budget.md`.

Run integrity: 8470 / 8470 evaluation runs and 1540 VL-count proxy runs, no missing outputs, 0
dead-end events. The proxies (DEFT_LB with the LUT pairs) match DeFT / DeFT_tm in latency,
p99 and packet count on all 1540 runs. DeFT_tm equals DeFT on all 350 runs where their LUTs
are identical. Drain tests: 396 / 396 PASS for the 11 v2 variants. QL-LA with alpha = 0
reproduces the lookahead heuristic exactly (12 / 12 runs, `qlla_check.md`).

## 1. Primary results (pre-registered, Holm over 16 tests, 10 seeds)
Effect = mean over the 11 scenarios of the per-seed log ratio, as % change with a 95 % CI.
THR: higher is better. LAT = mean latency at ~0.5 Lsat: lower is better.

| comparison | THR % [95 % CI] | Holm p | LAT % [95 % CI] | Holm p |
|---|---|---|---|---|
| CI_heur vs DeFT_tm | **+2.24** [+1.68, +2.80] | 6e-5 | **-5.73** [-6.15, -5.30] | 4e-9 |
| CI_heurLA vs DeFT_tm | **+3.07** [+2.61, +3.53] | 1e-6 | **-7.47** [-7.82, -7.12] | 9e-11 |
| FULL_heurLA vs DeFT_tm | **-1.66** [-2.62, -0.69] (worse) | 0.020 | **-9.65** [-10.13, -9.17] | 1e-10 |
| CI_ql vs CI_heur | +0.74 [+0.07, +1.41] | 0.067 (n.s.) | **-1.56** [-1.92, -1.20] | 4e-5 |
| FULL_ql vs FULL_heur | **+2.96** [+1.18, +4.77] | 0.020 | **-2.97** [-3.49, -2.45] | 5e-6 |
| CI_qlLA vs CI_heurLA | **+1.57** [+1.19, +1.95] | 5e-5 | **-1.10** [-1.63, -0.57] | 0.007 |
| FULL_qlLA vs FULL_heurLA | +0.24 [-1.00, +1.50] | 0.67 (n.s.) | **-2.11** [-2.64, -1.57] | 7e-5 |
| DeFT_tm vs DeFT | **+5.16** [+4.71, +5.62] | 1e-8 | -0.56 [-1.01, -0.10] | 0.064 (n.s.) |

Significant: 13 of 16. Not significant: CI_ql THR, FULL_qlLA THR, DeFT_tm LAT.
**One significant negative result: FULL_heurLA has lower saturation throughput than
DeFT_tm.**

Sensitivity (secondary, not pre-registered): with the 3 capped chipperm scenarios removed, the
THR effects keep their sign and size (CI_heur +3.3 %, CI_heurLA +4.3 %, FULL_heurLA -2.2 %,
CI_ql +0.8 %, FULL_ql +3.0 %, CI_qlLA +2.1 %, FULL_qlLA +0.4 %). The one exception is
**DeFT_tm vs DeFT, which drops to -0.1 % [-0.4, +0.1]**: its whole THR gain comes from
chipperm.

## 2. Traffic-matched DeFT: where the v1 gains disappear
* Matching the LUT to the traffic only changes DeFT where the demand is asymmetric. For
  uniform, localized and movinghot the time-averaged demand gives exactly the uniform LUT.
  For hotspot it changes 53 of 4224 selections, with no THR effect (-0.9 to 0.0 %, secondary).
  For chipperm it changes 1050, giving +17 % to +23 % THR (lower bounds), latency near Lsat
  -33 % to -49 %, and VL imbalance falling from 1.55-2.08 to 1.06-1.17.
* **The large v1 chipperm gains of every late-binding variant (+16 % to +48 % THR vs DeFT)
  disappear against DeFT_tm.** CI_heur vs DeFT_tm on chipperm is +0.2 %, -2.5 % and +1.0 %
  (secondary; capped). The same holds for all other variants (-2.5 % to +1.4 %, except FULL_heur at -9.9 % on chipperm 0x1111). They came
  from DeFT's uniform-traffic LUT assumption, not from late binding. A_oracle's v1 chipperm
  gains vanish in the same way.
* Against DeFT_tm, the remaining late-binding gains are on the other scenarios and are
  modest: CI_heur THR -1.3 % to +8.5 % (largest on uniform 0x9C63), CI_heurLA +2.1 % to +8.8 %.

## 3. Direction C: stateless heuristics
* **CI (late binding on the interposer only) beats DeFT_tm on both primary metrics**, with
  and without lookahead: THR +2.2 % / +3.1 %, LAT -5.7 % / -7.5 %. The lookahead heuristic
  has lower latency than the plain one in all 11 scenarios at ~0.5 and ~1.0 Lsat (point
  estimates; secondary, the interval excludes 0 in 6 of 11 at each load).
* **FULL (late binding on chiplets too) trades throughput for latency.** FULL_heurLA has the
  lowest latency of the three primary heuristic comparisons (-9.7 %) but loses THR
  (-1.7 %, significant). Per scenario (secondary), it loses -10.2 % on hotspot, -8.2 % on hotspot
  0x1111 and -5.6 % on movinghot, and gains +4.3 % on uniform 0x9C63. Without lookahead,
  FULL_heur loses THR against DeFT_tm in 9 of 11 scenarios (-4.5 % to -15.5 %). Odd-even
  adaptivity on the chiplets concentrates traffic on fewer VLs (VL imbalance 1.4-2.4 for
  FULL vs 1.1-1.7 for CI at ~0.5 Lsat) and lowers the knee under non-uniform traffic.

## 4. Direction B: what learning adds over the same information
* **Learning gives a small, significant latency gain in all four pairs** (LAT -1.1 % to -3.0 %).
  THR improves significantly in two of four: FULL_ql +3.0 % and CI_qlLA +1.6 %. CI_ql
  (+0.7 %) and FULL_qlLA (+0.2 %) are not significant.
* The effects are 1-3 %, while the learners had a larger tuning budget (section "Read this
  first"). Some of this margin may come from tuning rather than learning. The evidence is
  that learning helps a little and never hurts on the primary metrics. It does not show a
  large benefit.
* **Information matters more than learning.** Adding the lookahead to the heuristic helps more
  than adding learning to it (secondary): FULL_heurLA vs FULL_heur THR +0.2 % to +19.4 %;
  learning alone on FULL: FULL_ql vs FULL_heur +3.0 % (primary). On CI both steps are small.
* **Comparison with v1.** v1 found that CI_ql lost 2.6-3.4 % THR against CI_heur and that the
  learner was beaten by the lookahead heuristic on throughput. With per-scope tuning and the
  information-matched pairing, CI_ql vs CI_heur is +0.7 % (n.s.). The v1 learner-vs-
  heuristic gap was therefore partly a tuning artefact (v1 tuned only on FULL and reused
  the weights on CI).

## 5. Direction A: the oracle (secondary; unimplementable)
A_oracle has lower latency than DeFT_tm at ~0.5 Lsat in 10 of 11 scenarios (-2.6 % to -12.4 %),
but **lower saturation throughput in 9 of 11** (-1.2 % to -10.3 %). Its THR is at most equal to
DeFT_tm's elsewhere. Even with global instantaneous knowledge, a one-shot VL choice at
injection does not match an offline LUT at high load. Late binding inside the network
(CI) does.

## 6. Tail latency and VL usage (secondary)
* p99 latency near Lsat follows the mean (summary.md, last per-scenario table). On chipperm
  the CI heuristics are within +-8 % of DeFT_tm, and CI_heur is +7.5 % higher on chipperm
  0x1111.
* DeFT and DeFT_tm keep the VLs balanced (max/mean 1.04-1.17, except DeFT on chipperm). All
  late-binding variants are less balanced (CI 1.05-1.68, FULL 1.16-2.43), yet they have
  lower latency and, for CI, higher THR. VL balance is not what limits performance in this
  instance. The learner-based variants are the most balanced of the late-binding ones.

## 7. Safety and HL faults
* Model check (v1, 897 VL masks): all three relations deadlock-free, dead-end-free and
  livelock-free. Drain tests v2: 396 / 396 PASS.
* **HL faults are not tolerated by any relation** (`hl_coverage.md`). The relations have no
  fault-aware detours, so a faulty horizontal link known only to its neighbour leaves some
  pairs undeliverable:
  - **Single faults:** mean share of pairs always delivered is 80.2 % (fixed pair), 84.8 % (CI)
    and 86.1 % (FULL).
  - **Double faults (sample):** 65.4 %, 72.0 % and 74.1 %.
  - **Minimum:** 68 % or lower for every relation.

  Late binding recovers part of the loss through path diversity. The CDG stays acyclic in
  every case. The fixed-pair figure is a worst case over all injection policies, not the
  DeFT LUT pair alone.

## 8. Hardware cost (analytical, `hw_cost.md`)
| selection | storage per router | sideband / feedback wires into a router |
|---|---|---|
| DEFT_HEUR | 0 | 0 |
| DEFT_HEUR + lookahead | 0 (30 bits per neighbour if latched) | ~120 (150 at VL endpoints) |
| DEFT_QL (key = chiplet, as tuned) | ~0.6 kbit | ~76 (95) |
| QL-LA (key = chiplet, as tuned) | ~0.6 kbit | ~196 (245) |

The stateless heuristic is almost free. CI_heur delivers +2.2 % THR and -5.7 % LAT against
DeFT_tm at essentially no hardware cost beyond the late-binding relation. Each further step
(lookahead, learning) buys about 1-2 % at a real wiring or storage cost.

## Bottom line
* Matching DeFT's LUT to the traffic removes the largest v1 gains (all on chipperm). Against
  this fairer baseline, **interposer-only late binding with a stateless local heuristic still
  wins on both primary metrics** (THR +2.2 %, LAT -5.7 %; +3.1 % / -7.5 % with lookahead), at
  almost no hardware cost.
* **Full late binding is a latency-throughput trade-off**, not a win: lowest latency, but
  significantly lower saturation throughput than DeFT_tm (FULL_heurLA -1.7 %).
* **Learning adds 1-3 %** over the same information (latency significant in all four pairs,
  throughput in two). Its larger tuning budget and its hardware cost make this a weak case
  for learning over a well-chosen stateless rule.
* **Injection-time choice (direction A) does not beat the LUT at saturation**, even with an
  unimplementable oracle.
* **None of the relations tolerates horizontal-link faults.** Fault-aware detours would be
  needed.
