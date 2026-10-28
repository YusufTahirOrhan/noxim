# v13 findings: PARSEC application traces (Part E, descriptive)

**Documents:**
* Design: `APPS_DESIGN.md`.
* Pre-registration: `PREREGISTRATION.md` (b370814) and `PREREGISTRATION_addendum.md` (cbefa12: window), both before
  any run.
* Decisions: `DECISIONS.md`.
* Tables: `report/summary.md`, `report/normalised.csv`.
* Figures: `report/apps_{latency,p99}_{fault-free,0x1111}.{png,pdf}`.
* Per-run data: `app_runs.csv` (486 runs).

**Run integrity:**
* 486 / 486 runs: 9 benchmarks x 18 (method, mask) x seeds 41-43.
* Every run delivered its whole window (`netrace_finished`, injected = delivered).
* 0 dead-end events.
* The Netrace mode is off-by-default code that passed the 84-run regression.

**Setup:**
* Netrace traces of a 64-core CMP running PARSEC (M5 full system), on our 2x2 system (trace node n = chiplet router n).
* The first 700,000 cycles of the region of interest (412-14,147 packets per benchmark).
* Dependency-driven injection.
* Ratios to DeFT(rho*) with the same benchmark, mask and seed; geometric means over seeds and benchmarks.

## Fault-free
| method | mean latency / DeFT(rho*) | p99 / DeFT(rho*) | cycles to complete the window |
|---|---|---|---|
| MTR | 1.012 | 1.035 | 1.000 |
| RC | 1.032 | 1.038 | 1.000 |
| DeFT-Dis | 1.005 | 0.996 | 1.000 |
| DeFT-Ran | 1.138 | 1.128 | 1.000 |
| XY-SP | 0.954 | 1.028 | 1.000 |
| DeFT_OE_G | 0.998 | 1.000 | 1.000 |
| CI_heurLA_G | 0.959 | 1.000 | 1.000 |
| CI_qlLA_G | 0.959 | 0.997 | 1.000 |
| **FULL_qlLA_G** | **0.926** | **0.986** | 1.000 |

* **Mean latency:**
  - The three late-binding variants are below DeFT(rho*) on every benchmark: 2-11 % per benchmark, 4-7 % in the
    geometric mean. FULL_qlLA_G is the lowest (0.895-0.965).
  - MTR and RC are close to DeFT(rho*): +1 % and +3 % on average, and up to +12 % on bodytrack.
  - DeFT-Ran is 14 % slower.
  - XY-SP has low mean latency (shortest pairs), but a higher p99 on canneal and vips (+31 %, +36 %).
* **p99:** in the geometric mean within about 4 % of DeFT(rho*) for all methods except DeFT-Ran (+13 %).
* **Completion:** the window takes the same number of cycles for every method (within 0.2 %). The application's
  dependency chains, not the network, set the pace.
* **Absolute latencies are low:** DeFT(rho*) 10-48 cycles, depending on the benchmark.

## One faulty VL per chiplet (mask 0x1111; MTR and RC do not tolerate it)
| method | mean latency / DeFT(rho*) | p99 / DeFT(rho*) |
|---|---|---|
| DeFT-Dis | 0.969 | 0.958 |
| DeFT-Ran | 1.073 | 1.015 |
| XY-SP | 0.936 | 0.944 |
| DeFT_OE_G | 0.998 | 1.000 |
| CI_heurLA_G | 0.956 | 0.979 |
| CI_qlLA_G | 0.954 | 0.965 |
| **FULL_qlLA_G** | **0.900** | **0.878** |

* FULL_qlLA_G has the largest gain, especially where the traffic is heaviest: canneal 0.73 mean / 0.61 p99, and vips
  0.83 / 0.65.
* With this mask DeFT-Dis and XY-SP are also somewhat below DeFT(rho*) at this light load (0.97 and 0.94); DeFT-Ran
  stays above (1.07).

## Interpretation and limits
* **The traces load the network lightly.** The network does not limit the applications, so the completion time is the
  same for every method, and the latency differences are much smaller than with synthetic traffic near saturation.
* **Latency differences are small.** Late binding reduces latency by 4-10 % on average, up to 27 % (canneal, one faulty
  VL per chiplet).
* **Short windows.** The window is short (700,000 cycles, set by the 8 h budget), and the packet count varies by
  benchmark. Bodytrack has only 412 packets, so its p99 rests on very few packets.
* No significance tests: this part is descriptive, as specified.
