# Application traces (v13, Part E): feasibility and design

## E0. Feasibility: Netrace works (gem5 not needed)
* **Library:** Netrace 1.0 (https://www.cs.utexas.edu/~netrace/; J. Hestness, S. W. Keckler, TR-10-11, UT Austin
  2011), a C reader library for bzip2 traces of a 64-core CMP running PARSEC under the M5 full-system simulator.
  The traces carry packet dependencies. Downloaded on 2026-10-25 (`netrace-1.0.tar.bz2`, 0.87 MB). The reader
  source compiles as C++ after two type adaptations (`experiments/late_binding/netrace/`, license in
  `NETRACE_LICENSE`).
* **Traces:** for every benchmark, the smallest input available on the site:
  - blackscholes simsmall, fluidanimate simsmall, x264 simsmall;
  - canneal, dedup, ferret, vips simmedium;
  - bodytrack, swaptions simlarge (only simlarge exists for these two).

  All of DeFT's set that Netrace provides (blackscholes, bodytrack, canneal, dedup, fluidanimate, swaptions) plus
  ferret, vips and x264. Streaming and cutting all nine took about 1.5 h.
* **Download strategy:** the server delivers about 0.5 MB/s, and the traces are 0.06-4.3 GB compressed. Each trace
  is therefore streamed into the cut tool (`netrace_cut -`):
  - The tool decodes the header, reads through regions 0-1 and writes the first 3,000,000 packets of region 2.
  - It then exits, which ends the download, so no full trace is ever stored.
  - For blackscholes the streamed cut was checked to be identical to a cut from the downloaded file
    (`nt_seek_region`).

  Windows are kept on D: (`D:/netrace_v13/windows/`, about 1.1 GB, not in git). Each file starts with a header
  line: benchmark, nodes, region, region start cycle, region cycles, region packets.

## E1. Trace injection in Noxim (`-netrace FILE`, off by default; `src/NetraceDriver.*`)
* **Node mapping:**
  - Netrace node n (8x8 CMP, node n at (n mod 8, n div 8)) is chiplet router n of the 2x2 system: footprint
    (x, y), chiplet (x div 4, y div 4).
  - This is the identity on router ids, because chiplet router ids are y * 8 + x on the 8x8 footprint.
* **Packet sizes:** Netrace's sizes in bytes (control 8 B: requests, write and upgrade responses, invalidations;
  data 72 B: read responses, writebacks, write requests) divided by the flit width of our configuration (32 bits = 4 B),
  rounded up, at least 2 flits.
  - Control packets are 2 flits, data packets 18 flits.
  - Noxim's minimum packet is head + tail; the RC slot depth follows the 18-flit maximum (`-size 2 18`).
* **Injection, dependency mode (the library's dependency semantics; `-netrace_deps 1`):**
  - A packet becomes available at its trace cycle. The simulation cycle maps to trace cycle = region start +
    simulation cycle.
  - It is injected at once if every packet it depends on (within the window) has been delivered. Otherwise it is
    injected 8 cycles (Netrace's `L2_LATENCY`) after the last of them is delivered.
  - At most one new packet per node and cycle, as in Netrace's example simulator.
  - A dependency is cleared when the tail flit of the packet is ejected at its destination.
  - Implementation: the cut file keeps each packet's dependency list (the ids of the packets that depend on it), and
    the driver keeps the reference counts. This is the same rule as `nt_dependencies_cleared` /
    `nt_clear_dependencies_free_packet`, without reading the bzip2 file during the simulation.
  - Packets with source = destination are not network packets and are counted as delivered at once.
* **Window:** the first N packets of region 2 (the PARSEC region of interest), the same for every method. N is sized
  by a timing test so that the whole part fits in about 8 h (`PREREGISTRATION.md`).
  - Every packet of the window is injected and delivered; the run ends when the window is complete (drain check).
  - The number of cycles needed to complete the window is reported.
* **Checks:** the regression set must be byte-identical with the mode off. Every trace run must end with
  `netrace_finished`, and with injected = delivered.
