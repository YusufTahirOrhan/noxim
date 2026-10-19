# v6 step 1: where the 4x4 bottleneck is (E3, descriptive)

Runs: 4x4 uniform and localized, fault-free; DeFT_tm(rho*) (through its traffic-identical DEFT_LB proxy),
CI_heurLA and FULL_heurLA with the v5 (2x2-tuned) parameters; loads 0.8, 1.0 and 1.2 x Lsat (v5 load points);
seeds 101-103; 54 runs with the statistics flag (`-deft_lb stats_file`). Raw files were aggregated into
`bottleneck_agg.json` and deleted. Full tables: `bottleneck_tables.md`. Figures: `bottleneck_links_uniform.png`,
`bottleneck_links_localized.png` (link and VL utilisation per layer, 1.0 x Lsat), `bottleneck_wait.png`.
The statistics flag was regression-tested: `stats_regression.md`, 66 / 66 identical runs with the flag off and
with it on.

## What is shown (measured)

**1. CI loads the interposer more than the baseline; FULL loads it less and uses the chiplet layer instead.**
Mean link utilisation at 1.0 x Lsat, uniform (flits/cycle per link direction; localized is the same pattern):

| variant | chiplet links | interposer links | VL down: mean / max | VL up: mean / max |
|---|---|---|---|---|
| DeFT_tm(rho*) | 0.056 | 0.131 | 0.196 / 0.222 (max/mean 1.13) | 0.196 / 0.214 (1.09) |
| CI_heurLA | 0.044 | **0.146 (+11 %)** | 0.194 / 0.208 (1.07) | 0.194 / **0.298 (1.54)** |
| FULL_heurLA | 0.062 | 0.128 (-2 %) | 0.196 / **0.364 (1.86)** | 0.196 / 0.285 (1.45) |

The delivered traffic is the same, since the accepted throughput at 1.0 x Lsat is equal (0.0517-0.0521). So
CI moves the same packets over more interposer link-hops. The interposer is the shared layer and already
the busiest one (0.13 against 0.06 on the chiplets). The heatmap shows CI's extra load concentrated in the
centre of the interposer and on the entry VLs there (entry max/mean 1.54 against 1.09).

**2. CI's late entry choice departs from the LUT for most packets and lengthens a third of them.**

| uniform | entry VL differs from the LUT's | packets with more hops than the LUT path | mean extra hops |
|---|---|---|---|
| CI_heurLA, 0.8 / 1.0 / 1.2 x Lsat | 73 / 77 / 78 % | 25 / 33 / 43 % | +0.06 / +0.46 / +1.05 |
| FULL_heurLA, 0.8 / 1.0 / 1.2 x Lsat | 71 / 73 / 76 % (exit: 57 / 61 / 74 %) | 24 / 33 / 56 % | -0.36 / +0.22 / +1.91 |

Both late-binding variants take longer paths as load grows, and both also take some shorter ones (up to
6-8 hops shorter than the LUT path, which trades distance for balance). For CI all of the change is on the
interposer, because its exit is the LUT's. For FULL it is split between the chiplet layer (exit) and the
interposer (entry).

**3. Where CI fixes its entry.** About 40 % of CI packets keep more than one entry candidate until they
take a VL (remaining hops 0 at fixing). The rest are pinned to one entry somewhere between 1 and about 20
interposer hops after coming down, typically 2-11 hops before the VL. FULL looks similar (about 48 % fixed
only when taking the VL).

**4. Waiting per hop.** At and below Lsat every late-binding variant waits less per hop than DeFT_tm in
every router class. At 1.0 x Lsat, uniform, the head-flit buffer residence (cycles) at chiplet VL endpoint
routers is 5.0 (DeFT_tm), 3.3 (CI) and 3.0 (FULL); at interposer VL endpoints 4.7, 4.0 and 2.6; at the
interposer interior 3.2, 2.8 and 1.9. This is why latency at 1.0 x Lsat is lower for both: 75, 65 and 50
cycles. **Beyond the knee (1.2 x Lsat) CI collapses first.**

| uniform, 1.2 x Lsat | residence per hop: chiplet interior / chiplet VL / interposer VL / interposer interior | accepted throughput |
|---|---|---|
| DeFT_tm | 4.8 / 21.0 / 9.0 / 5.7 | 0.0611 |
| CI_heurLA | 9.1 / **51.2** / 17.5 / 13.3 | **0.0468** |
| FULL_heurLA | 21.3 / 19.1 / 11.0 / 8.6 | 0.0523 |

On localized (1.2 x Lsat), FULL keeps up with DeFT_tm (accepted 0.0897 against 0.0905) while CI falls to 0.0729.

## Explanation (what follows from the evidence, and what is a hypothesis)

* **Supported by the measurements.** CI's throughput loss on 4x4 uniform comes from the interposer. With
  the exit fixed by the LUT, all of CI's adaptivity, and all the extra hops it takes, land on the
  interposer: about 11 % more interposer link load for the same delivered traffic, concentrated in the
  centre and on a subset of entry VLs. The interposer is the bottleneck layer even for DeFT, so this
  extra load moves CI's knee earlier. Beyond it, CI's queues grow fastest (1.9-2.4 times DeFT_tm's per hop),
  and its accepted throughput at 1.2 x Lsat is 23 % below DeFT_tm's.
* **Supported by the measurements.** FULL's late exit spreads the adaptivity over both layers: interposer
  link load is slightly below DeFT_tm's, and the chiplet layer, which has spare capacity, carries more.
  This is consistent with FULL matching DeFT_tm on uniform and localized saturation throughput in v5
  while CI lost 12-17 %.
* **Hypothesis (not isolated here).** The centre concentration comes from the CI entry heuristic itself.
  With router-local occupancy and odd-even adaptivity towards *any* remaining entry candidate, packets
  coming down at the LUT's (balanced) exits drift to entry VLs reached through momentarily less occupied
  links, which on a 16x16 interposer lie towards the centre. Testing this needs a run with the entry
  restricted (e.g. CI with fewer entry candidates), which was not done.
* **Hypothesis.** The very high residence at chiplet VL endpoints for CI at 1.2 x Lsat (51 cycles) is
  back-pressure. Source boundary routers cannot drain into a congested interposer, and destination
  boundary routers behind the hot entry VLs receive more than their share. The statistics do not separate
  the two directions at those routers.
* **Not supported:** VL imbalance alone does not explain the difference. FULL's VL loads are *less*
  balanced than CI's (down 1.86, up 1.45) and it still does better. The layer on which the extra
  hops are spent matters more.
* **Caveat:** these runs use the 2x2-tuned parameters (v5). Step 2 re-tunes them per size; the
  explanation above may change if the tuned CI weights reduce the extra interposer hops.
