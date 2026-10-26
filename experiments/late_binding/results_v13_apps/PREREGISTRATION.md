# Pre-registration v13 (Part E): PARSEC application traces

Descriptive part, no hypotheses. Written and committed before any application-trace run, to fix the design. Details of
the trace pipeline: `APPS_DESIGN.md`.

## Design
* **Traces:** Netrace (64-core CMP, M5 full system, PARSEC), the smallest input available per benchmark:
  - blackscholes simsmall, bodytrack simlarge, canneal simmedium, dedup simmedium, fluidanimate simsmall,
    swaptions simlarge (DeFT's set as available in Netrace);
  - ferret simmedium, vips simmedium, x264 simsmall.
* **Region and window:** region 2 (the PARSEC region of interest), the first N packets, the same N for every benchmark
  and method.
  - N is chosen by a timing test **before any evaluation run**: the largest multiple of 100,000 packets, at most
    3,000,000, for which the whole part is estimated to take at most 8 h on one machine (`experiments_v13.py
    timing`; result in `window.json` and `runtime_estimate.md`).
  - The rule depends on run time only.
* **System:** the 2x2 system; trace node n is chiplet router n (the identity on the 8x8 footprint).
  - Fault-free, plus VL mask 0x1111 (one faulty VL per chiplet) for the methods that tolerate faults.
* **Methods:** those of Part B.
  - Fault-free: DeFT(rho*), MTR, RC, DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G, CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G.
  - Mask 0x1111: all except MTR and RC.
  - 2x2 parameters as in v9/v10, gamma = 2.
* **Injection:** dependency mode (`-netrace_deps 1`).
  - A packet is injected at its trace cycle, or 8 cycles after the last packet it depends on is delivered.
  - At most one new packet per node and cycle.
  - Control packets are 2 flits and data packets 18 flits (32-bit flits).
* **Seeds:** 41, 42, 43 (random VC choice and tie-breaking). 9 benchmarks x 18 (method, mask) x 3 seeds = 486 runs.
* **Checks:**
  - The regression set is byte-identical with the mode off (`results_v11/regression.md`: 84 / 84, same binary).
  - Every run must end with the whole window delivered (`netrace_finished`, injected = delivered; drain check).
    A run that does not is reported and excluded.

## Metrics and report
* Per benchmark and mask:
  - mean and p99 packet latency, normalised to DeFT(rho*) of the same benchmark, mask and seed, then averaged over
    the seeds (geometric mean);
  - the cycles needed to complete the window, normalised the same way.
* Grouped bar chart (benchmark x method) as DeFT's Fig. 6, a table, and FINDINGS.md.
* Geometric means over the benchmarks are reported as a summary.
