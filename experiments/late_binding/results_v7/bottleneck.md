# v7 step 2: the 4x4 bottleneck with the tuned parameters and the entry bound (descriptive)

Runs: 4x4 uniform and localized, fault-free; DeFT_tm(rho*) (traffic-identical DEFT_LB proxy), CI_heurLA and CI_qlLA
with the v6 tuned parameters, CI_heurLA_B (lut, k 4) and CI_qlLA_B (min, k 4); loads 0.8, 1.0, 1.2 x Lsat (v5 load
points); seeds 101-103; 90 runs with the statistics flag, 0 missing. Raw files aggregated into `bottleneck_agg.json`
and `bottleneck_metrics.json`, then deleted. Full tables, side by side with v6: `bottleneck_tables.md`. Heatmaps of
the interposer at 1.0 x Lsat: `bottleneck_links_uniform.png`, `bottleneck_links_localized.png`.

The DeFT_tm proxy rows are identical to v6's in every number (same runs repeated with the new binary), another
confirmation of determinism.

## Uniform, 1.0 x Lsat (delivered traffic equal for all: accepted 0.0518-0.0521)

| variant | interposer link load | centre / rest | entry VL max/mean | entry differs from LUT | extra hops mean / share > 0 | latency |
|---|---|---|---|---|---|---|
| DeFT_tm(rho*) | 0.131 | 1.40 | 1.09 | 0 % | 0 / 0 % | 75.3 |
| CI_heurLA (v5 params, v6 run) | 0.146 | 1.94 | 1.53 | 76.6 % | +0.46 / 33 % | 64.9 |
| CI_heurLA (tuned) | 0.144 | 1.94 | 1.46 | 74.5 % | +0.20 / 29 % | 63.0 |
| CI_heurLA_B | 0.143 | 1.93 | 1.41 | 73.9 % | +0.08 / 28 % | 61.6 |
| CI_qlLA (tuned) | 0.143 | 1.80 | 1.35 | 74.2 % | +0.11 / 27 % | 59.4 |
| CI_qlLA_B | 0.142 | 1.82 | 1.38 | 73.5 % | -0.11 / 25 % | 59.8 |

"centre / rest" = mean load of the interposer links inside the central 8x8 routers over the mean of the others.

## Beyond the knee (1.2 x Lsat): accepted throughput and residence at chiplet VL endpoints

| variant | uniform: accepted | uniform: chip-VL residence | localized: accepted | localized: chip-VL residence |
|---|---|---|---|---|
| DeFT_tm(rho*) | 0.0611 | 21.0 | 0.0905 | 18.7 |
| CI_heurLA (tuned) | 0.0498 | 42.7 | 0.0804 | 25.4 |
| CI_heurLA_B | 0.0537 | 36.8 | 0.0799 | 27.6 |
| CI_qlLA (tuned) | 0.0550 | 34.8 | 0.0856 | 23.9 |
| CI_qlLA_B | 0.0564 | 31.4 | 0.0921 | 12.9 |

## What this shows
* **Tuning (v6) already reduced CI's detours, but not its interposer load.** With the tuned parameters the mean
  extra hops at 1.0 x Lsat fall from +0.46 to +0.20 (heuristic) and +0.11 (learner). The interposer link load stays
  about 9-10 % above DeFT_tm's (0.143-0.144 against 0.131), and the centre / rest ratio stays at 1.8-1.9 against
  1.40.
* **The bound removes most of the remaining detours, but not the centre concentration.** CI_heurLA_B and CI_qlLA_B
  cut the mean extra hops further (to +0.08 and -0.11). Interposer load changes by at most 0.001-0.002 and the
  centre / rest ratio not at all (1.93, 1.82). About 74 % of entries still differ from the LUT's. The bounds that
  step 3 could choose are loose (about 3.2-3.4 of 4 candidates left). The tight bounds that would force entries
  close to the shortest or the LUT one cost 6-15 % throughput (`selection.md`).
* **Beyond the knee the bound helps a little.** At 1.2 x Lsat on uniform, accepted throughput rises by 8 % (heuristic)
  and 3 % (learner), and the queues at chiplet VL endpoints are shorter. Both remain below DeFT_tm(rho*) (-12 % and
  -8 %). On localized, CI_qlLA_B reaches DeFT_tm's accepted throughput (0.0921 against 0.0905, 3 seeds); CI_heurLA_B
  does not change.
* **Consequence for the v6 hypothesis.** The extra interposer load and its concentration in the centre are not caused
  by entries far from the shortest or LUT path. Packets whose entry is within 4 hops of the shortest path still
  concentrate in the centre, and forcing them closer makes throughput worse. The centre concentration is present in
  DeFT_tm too (1.40), and every late-binding variant raises it, FULL included (v6: 2.05). The remaining candidate
  explanation is the router-local, odd-even adaptive choice on the interposer itself (which minimal path is taken),
  not the choice of entry VL; this was not isolated.
