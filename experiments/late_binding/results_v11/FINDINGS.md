# v11 findings: fault-rate sweep (Part C)

Design: `PREREGISTRATION.md` (077dae6) and `PREREGISTRATION_addendum.md` (e0a049f, 5 masks), both committed before the
evaluation. Decisions: `DECISIONS.md`. Tables: `report/summary.md`, `report/primary.csv`, `report/secondary.csv`.
Figure: `report/fault_sweep.{png,pdf}` (as DeFT's Fig. 8). Per-run data: `eval_runs.csv` (10080 runs).

**Run integrity:**
* Evaluation: 10080 / 10080 runs, seeds 51-52, 0 missing, 0 dead-end events.
* Drain tests: every method on every mask, 360 / 360 PASS.
* Regression with the Netrace mode off: 84 / 84 identical.

## Primary (Holm over 18): LAT at the fault-free 1.0 x Lsat, our learners vs DeFT(rho*): **11 of 18 supported**
% change; unit = (mask, seed), mean over uniform and hotspot; 10 units.

| size | k | CI_qlLA_G | FULL_qlLA_G |
|---|---|---|---|
| 2x2 | 1 | **-55.9** [-65.9, -43.1] | **-60.1** [-67.9, -50.4] |
| | 2 | **-25.3** [-34.5, -14.8] | **+32.9** [+11.6, +58.1] (against ours) |
| | 3 | -5.8 [-10.0, -1.5] (Holm p 0.076, n.s.) | **+16.0** [+9.5, +22.9] (against ours) |
| 3x3 | 1 | **-55.6** [-61.2, -49.3] | **-67.5** [-70.4, -64.3] |
| | 2 | **-39.5** [-49.8, -27.1] | **-32.3** [-42.3, -20.5] |
| | 3 | -6.8 (n.s.) | +0.4 (n.s.) |
| 4x4 | 1 | **-65.8** [-70.2, -60.8] | **-72.8** [-77.0, -67.7] |
| | 2 | **-38.6** [-46.7, -29.3] | **-26.9** [-37.5, -14.5] |
| | 3 | +5.4 (n.s.) | +10.0 (n.s.) |

* **Supported:** every k = 1 test, and every k = 2 test except FULL_qlLA_G on 2x2. That one, and FULL_qlLA_G on 2x2
  at k = 3, are significant **against** ours.
* **k = 3: the load is beyond saturation for every method.**
  - With 3 of 4 VLs faulty in every chiplet, all methods are saturated at the fault-free 1.0 x Lsat in every cell
    (20 / 20 flagged for every method and size).
  - So the k = 3 latency compares queues growing over the window, not latencies of a stable network.
  - With one VL per chiplet left there is no VL choice: DeFT(rho*), DeFT-Dis and DeFT-Ran give identical results, and
    FULL_qlLA_G gives the same results as DeFT_OE_G.
* **2x2 at k = 2:** FULL_qlLA_G is saturated in 20 / 20 cells, CI_qlLA_G in 16 / 20 and DeFT in 20 / 20.
  FULL_qlLA_G's saturation throughput is also 5.4 % lower there. A possible reason (hypothesis, not isolated): FULL's
  late exit balances the two remaining VLs of the source chiplet less well than DeFT's LUT on the small 2x2 system.

## Secondary (unadjusted)
* **Saturation throughput vs DeFT(rho*):**
  - CI_qlLA_G is higher at every (size, k): +6.4 % to +12.0 %.
  - FULL_qlLA_G is higher in 7 of 9: +2.6 % to +8.0 %; it is lower on 2x2 at k = 1 (-2.0 %, n.s.) and k = 2 (-5.4 %).
  - At k = 3 both are +7 % to +8 % on every size: adaptive (odd-even) routing helps on the remaining single VL path,
    where DeFT, DeFT-Dis and DeFT-Ran are identical.
* **P99 vs DeFT(rho*):**
  - k = 1: -64 % to -87 %.
  - k = 2: -4.5 % (n.s., 2x2 FULL) to -53 %.
  - k = 3: -6 % to +2 %, mostly n.s.
* **The fault-tolerant baselines:** DeFT-Dis, DeFT-Ran and XY-SP are worse than DeFT(rho*) at k = 1 and 2; at k = 3 DeFT-Dis and DeFT-Ran equal
  it and XY-SP is close to it. In the geometric means our learners are better than all three at k = 1 and 2, in latency and throughput
  (`report/summary.md`, unadjusted tests per comparison in `report/secondary.csv`).
* **Absolute values:** see the geometric-mean table in `report/summary.md`. For example on 4x4, mean latency at k = 1 is
  62-78 cycles for our learners against 229 for DeFT(rho*) and 355-506 for the baselines.

## Bottom line
* **One or two faulty VLs per chiplet (k = 1, 2):** late binding lowers latency strongly against DeFT(rho*) on 9 and 16
  chiplets (-27 % to -73 %, all significant) and raises saturation throughput (+4 % to +12 %).
* **On 2x2 with two faulty VLs per chiplet:** CI_qlLA_G still gains (-25 % latency, +6.6 % throughput), but FULL_qlLA_G
  loses (+33 % latency, -5.4 % throughput).
* **With a single VL left per chiplet (k = 3):** the networks are saturated at this load and the VL choice is gone. The
  latency effects are not significant, except FULL_qlLA_G on 2x2 (+16 %). The adaptive routing still gives 7-8 % more
  saturation throughput on every size.
