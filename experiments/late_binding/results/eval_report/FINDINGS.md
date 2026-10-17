# DEFT_LB evaluation: findings (preliminary, 5 seeds)

Numbers come from `summary.md`, `paired.csv`, `saturation.csv` and `tail_vl.csv` in this
directory (`report_eval.py`). Each figure is the mean paired change vs the reference over
seeds 1-5, with a 95 % t-interval. "Significant" means the interval excludes 0.

## Read this first
* **Preliminary.** Five seeds give wide intervals. The tables hold 13 comparisons x 11
  scenarios x 4 metrics = 572 intervals with no multiplicity correction, so about 29 of
  them would exclude 0 by chance even with no real effect. Trust consistent patterns
  across scenarios more than single cells.
* **A_oracle is not implementable.** It picks the VL pair at injection using the
  instantaneous occupancy of the whole network. It is meant as an upper bound for
  direction A, but (see below) it is not an upper bound for DeFT's saturation throughput.
* **Fixed-window latency beyond saturation is not a steady state.** It grows with the
  window. Near-Lsat latency ratios are not steady-state values in the scenarios where
  DeFT itself is already saturated at that rate (uniform 0x9C63: DeFT accepts 73 % of
  the offered load; hotspot and chipperm 0x9C63: 94-95 %). The large reductions in those
  cells (for example -82 % on chipperm 0x9C63) contrast a saturated DeFT with an
  unsaturated variant. They are not latency gains in the usual sense.
* **Lower bounds.** On chipperm, most late-binding variants and A_random/A_oracle still
  accept >= 95 % of the highest offered load (1.75x DeFT Lsat), so their saturation
  throughput and their gains are lower bounds (hatched in `saturation.png`, `≥` in
  `summary.md`).
* **Tuning budget was unequal.** B (Q-learning) got 12 configurations of its own on top of
  the 9 that fixed its local weights; C got 9. The chosen ql_alpha = 0.05 is at the edge of
  its grid. Everything was tuned on FULL and reused unchanged for CI.
* **Single LUT.** DeFT uses one LUT (rho = 0.01, built for uniform inter-chiplet demand)
  for every traffic pattern. Its large losses on chipperm reflect that assumption.

## 1. Direction A (injection-time VL choice) does not beat DeFT
* A_mindist is the worst informed policy. It loses saturation throughput in all 11
  scenarios (-5 % to -38 %) because it piles traffic onto the nearest VLs (VL imbalance
  1.6-2.2 vs DeFT 1.06-1.13 on non-chipperm traffic).
* A_random beats DeFT only on chipperm (+19 % to +21 %, lower bounds) and loses 15-28 %
  elsewhere.
* A_oracle (unimplementable) has the lowest low-load latency in direction A (9/11 scenarios
  significantly better than DeFT, -4 % to -13 %). However, it **loses saturation throughput
  in 6/11 scenarios** (uniform -7.9 %, uniform 0x1111 -7.9 %). A one-shot choice based on
  occupancy at injection time does not match DeFT's offline load balancing at high load.
  Its gains are on chipperm only (+16 % to +28 %).
* Conclusion for A: within this design space, choosing the VLs once at injection, even
  with global knowledge, is not enough to improve on the LUT in general.

## 2. Adaptivity without information hurts (random controls)
CI_random and FULL_random are significantly worse than DeFT in saturation throughput in
9/11 and 10/11 scenarios (down to -25 % and -41 %), and in low-load latency in 11/11.
Whatever late binding gains below therefore comes from the information used for the
choice, not from path diversity alone.

## 3. Direction C (stateless local heuristic)
* **CI_heur is the most robust variant.** It has no significant saturation-throughput
  loss in any scenario and significant gains in 8/11: uniform +2.7 %, localized +9.3 %,
  hotspot +2.9 %, uniform 0x9C63 +11.5 %, hotspot 0x9C63 +7.2 %, and chipperm +17 % to
  +48 % (some lower bounds). Low-load latency is 5-9 % lower in 6/11 scenarios, with no
  significant loss.
* **FULL_heur cuts latency but costs throughput.** Low-load latency is 4-12 % lower in
  8/11 scenarios, but saturation throughput drops in 6/11 (uniform -7.7 %, hotspot
  -8.6 %). Late exit selection on the chiplets (odd-even on chiplets) works against the
  LUT's load spreading at high load. On fault-free non-chipperm traffic, VL imbalance is 1.5-1.8 for
  FULL vs 1.2-1.4 for CI.
* **FULL_heurLA (one hop of lookahead, still no learning)** has the lowest latencies of
  all implementable variants: low load better in 11/11 (-4 % to -14 %), near Lsat 10/11,
  p99 11/11. It recovers saturation throughput on uniform (+6.9 %) and uniform 0x9C63
  (+7.5 %), but is still worse on uniform 0x1111 (-4.9 %) and hotspot 0x1111 (-5.7 %).

## 4. Direction B (Q-learning) and B vs C
* FULL_ql vs DeFT: low-load latency is lower in 11/11 scenarios (-5 % to -16 %), but
  saturation throughput is lower in 5/11 (uniform -8.3 %, movinghot -10.2 %). Near-Lsat
  latency on uniform 0x9C63 is **27.7 % worse** than DeFT (an unsaturated-vs-saturated
  cell; see the caveat above).
* CI_ql vs DeFT: no significant saturation-throughput loss, gains in 6/11; low-load
  latency lower in 10/11 (-3 % to -11 %).
* **B vs C, isolating learning** (DEFT_QL with alpha = 0 reproduces DEFT_HEUR exactly,
  `results/alpha0_equivalence.txt`):
  - FULL_ql vs FULL_heur: no significant saturation-throughput difference in any
    scenario. Latency is lower: low load in 8/11 (-3 % to -9 %), near Lsat in 7/11,
    p99 near Lsat in 7/11. No significant loss on any latency metric.
  - CI_ql vs CI_heur: saturation throughput is **lower in 3/11** (uniform -2.6 %,
    localized -3.4 %, uniform 0x1111 -2.8 %). Latency improvements are smaller and
    rarer (low load 3/11).
  - So learning gives a small, consistent latency benefit on FULL and a small throughput
    cost on CI. Part of the FULL gain may come from B's larger tuning budget.
* **Learning vs one more hop of information** (FULL_ql vs FULL_heurLA, paired): QL has
  **lower saturation throughput in 3/11 scenarios** (uniform -14.2 %, localized
  -12.4 %, movinghot -10.8 %) and no gain anywhere. Latency is mostly equal. QL is 3-6 % lower in the two
  chipperm cells (0x0000 and 0x1111) at low and near-Lsat load, but 18.8 % higher on
  uniform 0x1111 near Lsat. Its p99 near Lsat is higher on localized (+5.6 %) and
  uniform 0x1111 (+35 %). The lookahead heuristic
  matches or beats the learner without any learned state.

## 5. Tail latency and VL usage
* p99 near Lsat follows the mean-latency pattern: FULL_heurLA 11/11 better than DeFT,
  FULL_ql and CI_ql 7/11 and 9/11, A_oracle 7/11.
* DeFT's VLs are evenly used (max/mean 1.06-1.13) except on chipperm (2.01 fault-free,
  about 1.55 with faults). The late-binding variants are mostly less balanced
  (CI 1.05-1.6, FULL 1.06-2.3; the lowest values are on 0x9C63, where few VLs remain) yet have lower latency. VL balance alone is not what limits
  performance here. Path length and local congestion matter more, and DeFT's balance
  shows up as saturation throughput, not as latency.

## 6. Safety (all variants, frozen parameters)
* Model check (897 masks, 3 relations): no cyclic CDG, no dead ends, no livelock.
* Drain tests: 374/374 PASS. Evaluation: 0 dead-end events in 4235 runs.

## Bottom line (preliminary)
* **Best overall trade-off:** interposer-only late binding with the stateless local
  heuristic (CI_heur). It never loses saturation throughput to DeFT and gains up to
  +11 % (+48 % on chipperm with faults), at slightly lower latency.
* **Lowest latency:** FULL_heurLA (and FULL_ql), at the cost of some throughput in
  several scenarios.
* **Q-learning** gives a small latency benefit over the same heuristic on FULL. That
  benefit does not carry over to CI, and the learner is beaten in throughput by a
  heuristic with one more hop of information. On this evidence the case for learning
  over a well-chosen stateless rule is weak.
* **Direction A, including the unimplementable oracle,** does not improve on DeFT except
  under chiplet-permutation traffic, where the LUT's uniform-traffic assumption fails.
