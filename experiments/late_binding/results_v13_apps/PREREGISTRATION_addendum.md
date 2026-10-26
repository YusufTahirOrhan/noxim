# Pre-registration v13, addendum: trace window (committed before any evaluation run)

The pre-registered rule fixed the window as the first N packets of region 2, N the largest multiple of 100,000 for
which the whole part (486 runs) fits in at most 8 h. The timing test (`runtime_estimate.md`) showed this rule cannot
be met:
* Noxim needs about 0.5 ms per simulated cycle regardless of the load.
* The PARSEC traces are light but spread over millions of cycles. The first 100,000 packets of region 2 span 1.5-5.5 M
  trace cycles, and completing them in dependency mode takes 1.2-2.8 times the window's cycles.
* Even N = 100,000 is estimated at 34.9 h.

**Deviation (decided on run time only, before any evaluation run):** the window is defined in **cycles** instead of
packets, the other form named in the task ("the first 2 M cycles or 1 M packets").
* **Rule:** the largest multiple of 100,000 cycles of region 2, the same for every benchmark and method, whose
  estimated total time is <= 8 h.
* **Cost model:** the timing test's cost per simulated cycle (515 cpu-us), and per benchmark its measured ratio of
  completion cycles to window cycles.
* **Result: the first 700,000 cycles of region 2 of every benchmark** (estimated 7.3 h; `window.json`).
* All other parts of the design are unchanged: methods, masks, seeds, dependency mode, metrics.

Packets in the window (region 2, first 700,000 cycles):

| benchmark | packets |
|---|---|
| blackscholes | 14,147 |
| bodytrack | 412 (bodytrack's region of interest starts with a long quiet phase) |
| canneal | 8,198 |
| dedup | 2,266 |
| ferret | 6,651 |
| fluidanimate | 2,407 |
| swaptions | 8,882 |
| vips | 13,932 |
| x264 | 13,620 |

These counts include self-addressed packets, which are counted as delivered at once.
