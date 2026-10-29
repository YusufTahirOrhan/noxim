# Two applications at once (v15, Part G): design

Written before any code for this part.

## Overlay of two traces
* Two Netrace readers run at the same time. Each replays its own trace window on all 64 nodes, with its own dependency
  tracking, and the packets of both share the network and the NI (PE) queues.
* This is our analogue of DeFT's two applications on 32 cores each.
* **Deviation:** Netrace traces cannot be split onto 32 nodes, because each trace's caches and directories are spread
  over all 64 nodes. Both applications therefore use all 64 nodes, and their packets interleave in every NI queue.
* **Per node and cycle:** each reader may release one new packet (the v13 rule, applied per reader), so a node can
  receive up to two new packets per cycle, one from each application.
* **Ids:** a packet carries the index of its reader. Its delivery clears the dependencies of that reader only.

## Pairs
The benchmarks are ranked by their packet count in the v13 window (`results_v13_apps/app_runs.csv`, field
`packets`: first 700,000 cycles of region 2, self-addressed packets included).

| rank | benchmark | packets |
|---|---|---|
| 1 | blackscholes (simsmall) | 14,147 |
| 2 | vips (simmedium) | 13,932 |
| 3 | x264 (simsmall) | 13,620 |
| 4 | swaptions (simlarge) | 8,882 |
| 5 | canneal (simmedium) | 8,198 |
| 6 | ferret (simmedium) | 6,651 |
| 7 | fluidanimate (simsmall) | 2,407 |
| 8 | dedup (simmedium) | 2,266 |
| 9 | bodytrack (simlarge) | 412 |

The 6 pairs among the four heaviest:
* blackscholes + vips
* blackscholes + x264
* blackscholes + swaptions
* vips + x264
* vips + swaptions
* x264 + swaptions

## Compression
* Option s >= 1 divides the trace timestamps by s: a packet at trace offset d (from the start of region 2) becomes
  available at simulation cycle ceil(d / s).
* Dependencies are still enforced.
* The 8-cycle delay after the last dependency is delivered (Netrace's `L2_LATENCY`) stays 8 **simulation** cycles, so it
  is not compressed.
* The 700,000-cycle trace window plays in 700,000 / s cycles; the work (all packets of both windows) is the same.

## Settings
* s = 1 and s = 2. If the timing test estimates more than 8 h for both, s = 1 only.
* Unchanged from v13:
  - window: the first 700,000 cycles of region 2;
  - system: 2x2;
  - methods: the 10 methods of Part B. The task says "all 9"; Part B has 10 (DeFT(rho*), MTR, RC, DeFT-Dis, DeFT-Ran,
    XY-SP, DeFT_OE_G and the three _G variants), and all 10 are run.
  - masks: fault-free for all; 0x1111 for the fault-tolerant ones;
  - seeds: 41-43.
* Runs: 6 pairs x 18 (method, mask) x 3 seeds = 324 per s.

## Implementation (options off by default)
* `-netrace2 FILE`: second trace.
* `-netrace_compress S`: compression factor (default 1).
* With one trace and S = 1 the driver behaves exactly as in v13.
* New JSON fields appear only when the options are used.
