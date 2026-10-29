# Pre-registration v15 (Part G): two applications at once

Descriptive part (no hypotheses), as v13. Committed before any evaluation run of this part. Design and implementation:
`APPS2_DESIGN.md`.

## Design
* **Pairs** (the four heaviest benchmarks of the v13 window): blackscholes + vips, blackscholes + x264,
  blackscholes + swaptions, vips + x264, vips + swaptions, x264 + swaptions.
* **Overlay:** two independent Netrace readers, one per application, on all 64 nodes of the 2x2 system.
  - Each reader applies its own dependency tracking and releases at most one new packet per node and cycle.
  - Both readers' packets share the network and the NI queues.
* **Window:** the first 700,000 cycles of region 2 of each trace (as v13).
* **Compression s:** s = 1 and s = 2. The timestamps are divided by s, dependencies are kept, and the post-dependency
  delay stays 8 cycles.
  - Rule, fixed now: if the timing test estimates more than 8 h for both settings together, only s = 1 is run.
  - The rule depends on run time only.
* **Methods:** the 10 methods of Part B.
* **Masks:** fault-free for all methods; VL mask 0x1111 for the fault-tolerant ones (all except MTR and RC).
* **Seeds:** 41-43.
* **Runs per s:** 6 pairs x 18 (method, mask) x 3 seeds = 324.

## Checks (before the evaluation)
* Regression with the new options off: byte-identical on the 84-configuration set.
* A single trace with s = 1 reproduces v13 exactly: DeFT(rho*), seed 41, one run per benchmark.
* Every evaluation run must deliver both windows completely (injected = delivered, `netrace_finished`). A run that
  does not is reported and excluded.

## Metrics (per pair, s, mask)
* Mean and p99 packet latency (Noxim's global statistics, as v13), normalised to DeFT(rho*) with the same pair, s, mask
  and seed; geometric mean over the seeds and over the pairs.
* Cycles to complete both windows, normalised the same way.
* Offered load: flits delivered per node and cycle over the completion time (an average over the run, to place the
  load relative to the synthetic Lsat).
* Per-application completion cycles and mean latencies (measured at the tail of each packet) are reported as well.

## Report
* A grouped bar chart (pair x method) per s and mask, a table, and FINDINGS.md.
* FINDINGS.md states whether the completion time now differs between methods.
