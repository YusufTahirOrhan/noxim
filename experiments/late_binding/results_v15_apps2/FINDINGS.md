# v15 findings: two PARSEC applications at once (Part G)

Descriptive part, as v13. There are no significance tests.

**Sources:**
* Design: `APPS2_DESIGN.md`, `PREREGISTRATION.md`.
* Runs: `pair_runs.csv`: 648 runs = 2 values of s x 6 pairs x 18 (method, mask) x seeds 41-43.
  - Every run finished and delivered both windows completely (injected = delivered).
  - No run was excluded, and there was no dead-end event.
* Report: `report/summary.md` and `report/normalised.csv`, with bar charts `report/pairs_{latency,p99,completion_cycles}_s{1,2}_{fault-free,0x1111}.{png,pdf}`.

**Checks:**
* Regression with the options off: 84 / 84 byte-identical (`regression.md`).
* A single trace at s = 1 reproduces v13: 9 / 9 (`v13_check.md`).
* s rule: an estimated 5.8 h for both values of s, so s = 1 and s = 2 were both run (`runtime_estimate.md`).

## Geometric means over the 6 pairs (DeFT(rho*) = 1)

| method | s=1 free: mean / p99 / completion | s=1 0x1111: mean / p99 / completion | s=2 free: mean / p99 / completion | s=2 0x1111: mean / p99 / completion |
|---|---|---|---|---|
| MTR | 0.995 / 0.978 / 1.000 | - | 0.976 / 0.909 / 1.010 | - |
| RC | 1.020 / 0.892 / 1.001 | - | 1.002 / 0.921 / 1.027 | - |
| DeFT-Dis | 1.003 / 0.995 / 1.000 | 0.981 / 0.866 / 1.000 | 0.997 / 0.985 / 1.008 | 0.981 / 0.960 / 0.986 |
| DeFT-Ran | 1.112 / 0.954 / 1.001 | 1.049 / 0.808 / 1.001 | 1.109 / 1.044 / 1.057 | 1.058 / 0.872 / 1.040 |
| XY-SP | 0.968 / 1.186 / 0.999 | 0.954 / 0.900 / 0.999 | 0.969 / 1.055 / 0.965 | 0.991 / 1.068 / 0.962 |
| DeFT_OE_G | 0.999 / 0.959 / 1.000 | 1.005 / 1.025 / 1.000 | 0.998 / 1.018 / 1.002 | 1.002 / 0.952 / 1.001 |
| CI_heurLA_G | 0.965 / 0.936 / 1.000 | 0.951 / 0.952 / 1.000 | 0.956 / 0.924 / 0.984 | 0.947 / 0.895 / 0.973 |
| CI_qlLA_G | 0.961 / 0.883 / 1.000 | 0.953 / 0.970 / 1.000 | 0.951 / 0.889 / 0.983 | 0.942 / 0.862 / 0.972 |
| **FULL_qlLA_G** | **0.930 / 0.855 / 1.000** | **0.894 / 0.650 / 0.999** | **0.927 / 0.917 / 0.964** | **0.901 / 0.727 / 0.957** |

## Does completion now differ between methods?
* **s = 1: no.** With both applications at their original timing, every method completes both windows within
  0.2 % of DeFT(rho*) (0.9986-1.0022), as in v13.
  - The completion time is about 700,000 cycles, which is the length of the window itself. The trace timestamps set the
    pace, not the network.
* **s = 2: yes, by a few percent.** The timestamps alone would allow completion in 350,000 cycles. Instead, the runs
  take 418,000-610,000 cycles, so the dependency chains and the network latency now set the completion time.
  - FULL_qlLA_G completes 3.6 % (fault-free) and 4.3 % (0x1111) faster than DeFT(rho*) in the geometric mean. In every
    pair it is 3-5 % faster (0.946-0.969).
  - CI_qlLA_G and CI_heurLA_G are 2-3 % faster.
  - XY-SP is 3.5-4 % faster.
  - DeFT-Ran is 4-6 % slower, and RC is 2.7 % slower.
  - The spread across methods (0.946-1.061 of DeFT(rho*)) is far larger than at s = 1 (0.9986-1.0022).

## Latency
* **FULL_qlLA_G has the lowest mean latency** in all four settings: 7 % below DeFT(rho*) fault-free and 10-11 % below
  with 0x1111. It is lowest in 17 of the 24 (s, mask, pair) cells, down to 0.838 (vips + swaptions, 0x1111, s = 2).
  - XY-SP is lowest in 6 cells, all on pairs with swaptions or x264, by 0.15-0.46 percentage points of DeFT(rho*).
  - CI_qlLA_G is lowest in 1 cell (vips + x264, fault-free, s = 2).
* **p99 with 0x1111:** FULL_qlLA_G reduces it most, to 0.65 (s = 1) and 0.73 (s = 2). It reaches 0.55-0.60 on the
  pairs that contain vips.
* **The other learners:** CI_qlLA_G and CI_heurLA_G are 4-6 % below DeFT(rho*) in mean latency.
* **XY-SP:** a low mean (shortest paths at light load), but a higher p99 fault-free (1.19 at s = 1).
* **DeFT-Ran** is the slowest (+5-11 %).
* **MTR and RC** are close to DeFT(rho*) in mean latency. Their p99 is lower (0.89-0.98).

## Load and limits
* **Offered load:** DeFT(rho*) carries 0.005-0.007 flits per node and cycle at s = 1 and 0.006-0.009 at s = 2, averaged
  over the completion time.
  - This is about 5-10 % of the synthetic 2x2 uniform Lsat (0.011 packets x 8 flits = 0.088 flits per node and cycle).
  - The load is still light on average. The latency effects come from bursts, and s = 2 makes the dependency-bound part
    of the run visible in the completion time.
* **Overlay on 64 nodes:** both applications use all 64 nodes, unlike DeFT's 32 cores per application (DECISIONS item 1).
* **Short windows:** each window is 700,000 cycles long.
* **Seeds:** 3 per configuration.
