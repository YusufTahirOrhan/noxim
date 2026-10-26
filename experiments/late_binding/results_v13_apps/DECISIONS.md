# Decisions taken without the author (v13, Part E)

1. **Netrace instead of gem5.** Netrace's library and traces were available; no gem5 setup or estimate was needed
   (`APPS_DESIGN.md`).
2. **Benchmarks and inputs:** the smallest input Netrace offers per benchmark (simsmall for blackscholes,
   fluidanimate, x264; simmedium for canneal, dedup, ferret, vips; simlarge only for bodytrack and swaptions).
   ferret, vips and x264 were included: the time allowed it.
3. **Streaming cut:** the server delivers about 0.5 MB/s. Each trace was streamed into `netrace_cut` (no seek;
   regions 0-1 decoded and skipped), and the download stopped after the first 3,000,000 packets of region 2. For
   blackscholes this was checked to give a file identical to a cut from the full download. Windows live on D: (about
   1.1 GB, not in git); no full trace was stored.
4. **Dependency tracking in the simulator.** The cut keeps each packet's list of dependent packets, and the driver
   applies the library's rule: a packet is injectable when every in-window packet it depends on has been delivered. The
   library itself is not linked into Noxim; this avoids reading bzip2 during the runs.
   - Dependencies on packets outside the window (earlier regions) count as satisfied, as in the library after a
     region seek.
5. **Injection timing:** Netrace's example simulator:
   - injection at the trace cycle when the dependencies are already met, otherwise 8 cycles (`L2_LATENCY`) after
     the last one is delivered;
   - at most one new packet per node and cycle;
   - the latency is measured from the injection into the PE queue.
6. **Packet sizes:** control 8 B -> 2 flits, data 72 B -> 18 flits (32-bit flits), with `-size 2 18` so that the RC slot
   depth is the 18-flit maximum.
7. **Self-addressed packets** (source = destination, e.g. between caches of the same node) are not network traffic; they are
   counted as delivered at once (and clear their dependencies).
8. **Window: cycles, not packets.**
   - The pre-registered packet rule could not be met: N = 100,000 packets was estimated at 34.9 h for the 486
     runs.
   - The window is therefore the first 700,000 cycles of region 2 for every benchmark, chosen by the same 8 h rule
     (`PREREGISTRATION_addendum.md`, committed before any run).
   - The resulting sample sizes differ by benchmark, from 412 packets (bodytrack) to 14,147 (blackscholes).
9. **No warm-up** (`-warmup 0`): every packet of the window counts. The simulation ends when the window is delivered
   (limit 400 M cycles).
10. **Normalisation:** per benchmark, mask and seed, the ratio to DeFT(rho*) with the same mask and seed; geometric mean
    over the seeds, then over the benchmarks.
