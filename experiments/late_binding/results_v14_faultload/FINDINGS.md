# v14 findings: fault sweep below the faulty saturation point (Part F)

Design: `PREREGISTRATION.md`. Loads: `load_choice.json` / `load_choice.md` (F1). Report: `report/summary.md`,
`report/primary.csv`, `report/secondary.csv`, `report/fault_load.{png,pdf}`. Runs: `eval_runs.csv` (3600 of 3600,
seeds 53-57, no missing run, no dead-end event).

## F1: test loads
For each (size, k, pattern), the test load is the highest of the 7 v11 load points at which DeFT(rho*)'s pooled
latency stays within 3x its zero-load latency.
* **Range:** 0.2x to 1.0x the fault-free Lsat; 0.2-0.5x at k = 3.
* **Fallback:** never needed.
* **Exploratory effects:** the v11 data (seeds 51-52) at these loads showed the learners below DeFT(rho*) almost
  everywhere. These are listed in `load_choice.md`; they are not confirmatory.

## F2: confirmatory result (Holm over 18)
**15 of 18 primary hypotheses are supported. None is significant against our methods.**

| size | k | CI_qlLA_G | FULL_qlLA_G |
|---|---|---|---|
| 2x2 | 1 | -17.9 % | -16.3 % |
| 2x2 | 2 | -8.6 % | -2.1 % (n.s., CI -4.2 to +0.1) |
| 2x2 | 3 | -0.8 % (n.s.) | -0.2 % (n.s.) |
| 3x3 | 1 | -16.4 % | -19.9 % |
| 3x3 | 2 | -13.8 % | -17.1 % |
| 3x3 | 3 | -4.9 % | -5.4 % |
| 4x4 | 1 | -12.0 % | -20.0 % |
| 4x4 | 2 | -10.9 % | -15.8 % |
| 4x4 | 3 | -2.4 % | -2.6 % |

* **Comparison with v11:** v11 tested at fixed fractions of the fault-free Lsat and supported 11 of 18; there,
  k = 3 was saturated. Placing the test load below DeFT's own faulty saturation point removes that confound.
  - The advantage of the learners is largest at k = 1 and k = 2 (8-20 %).
  - It shrinks to 2-5 % at k = 3 on 3x3 and 4x4.
  - It is not significant on 2x2 at k = 3.
* **2x2, k = 3:** each chiplet has a single working VL, so there is no exit or entry choice left. All adaptive methods
  then route the same way as DeFT(rho*), and the latency is at the zero-load level (about 29 cycles) for every method.
  - A null effect is the expected outcome there.
  - On 3x3 and 4x4, k = 3 still leaves an intra-chiplet path choice and a choice of where to cross, which is where the
    remaining 2-5 % comes from.
* **FULL_qlLA_G on 2x2 at k = 2:** -2.1 %, n.s. CI_qlLA_G is significant there (-8.6 %).

## Secondary (unadjusted)
* **P99:** lower for both learners in every (size, k) except FULL_qlLA_G on 2x2 at k = 3 (n.s.).
  - Reductions of 25-39 % at k = 1 and 2 on 3x3 and 4x4.
* **Other methods vs DeFT(rho*):**
  - DeFT_OE_G and CI_heurLA_G are also lower everywhere it is significant.
  - DeFT-Dis, DeFT-Ran and XY-SP are much worse at k = 1 and 2 (up to +770 % for XY-SP on 2x2, k = 1).
  - At k = 3, DeFT-Dis and DeFT-Ran are identical to DeFT(rho*), since only one VL is left per chiplet.
* **Ranking:** FULL_qlLA_G has the lowest geometric-mean latency on 3x3 and 4x4 at k = 1 and 2. CI_qlLA_G has the lowest
  on 2x2 at k = 1 and 2.

## Caveats
* **Saturated flag at 2x2, k = 3:** the flag (accepted < 95 % of offered) is set on 5-12 of 50 runs per method there,
  although latency is at zero load. This is sampling noise of the accepted rate at a very low load (DECISIONS item 6),
  not saturation.
* **Hotspot test loads on 4x4:** these sit at 0.0017 (0.8x) for k = 1 and 2, below the uniform ones. The test points
  therefore differ in absolute load between patterns, by design.
