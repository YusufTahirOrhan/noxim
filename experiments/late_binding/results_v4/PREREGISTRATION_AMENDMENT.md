# Amendment to the v4 pre-registration (load points), before any evaluation run

Committed after the coarse DeFT saturation sweep (seed 101; `load_points_coarse.md`) and **before the
fine sweep and before any evaluation run (seeds 1-10)**. Only the Lsat procedure changes. Metrics,
comparisons, test, Holm family, seeds and window are unchanged.

## Problem found in the coarse sweep
The pre-registered v2 rule (L0 = latency at rate 0.001, 0.0005 grid) breaks down where the larger
systems saturate early:
* **4x4 movinghot:** Lsat = 0.001, i.e. the reference rate itself (lat/L0 = 1.00 at Lsat). On the 0.0005
  grid the 7 loads become 0.0005-0.0035 = 0.5-3.5 x Lsat, so the pre-registered "1.0 x Lsat" point (4th
  load) would be at 2 x Lsat.
* **4x4 hotspot, chipperm and hotspot-north (Lsat 0.0015-0.002):** the loads span about 0.25-2.3 x Lsat,
  and the 4th load is at 1.0-1.3 x Lsat only by rounding.
* **Rate 0.001 is no longer near zero load on 4x4:** L0 = 44.7 cycles on movinghot against 21 on 2x2, so
  "3 x L0" is a looser threshold there than in v2.

## Amended rule
* **L0** = DeFT latency at rate **0.0002** (seed 101), for every v4 scenario. That is at most 0.2 x the
  smallest coarse Lsat, i.e. near zero load in every scenario. On 2x2 the v2 reference 0.001 was
  0.07-0.25 x Lsat.
* **Grid:** scenarios whose coarse Lsat is <= 0.004 (3x3 hotspot, movinghot, hotspot-north; 4x4 hotspot,
  chipperm, movinghot, uniform-north, hotspot-north) get a sweep in **0.0001 steps** from 0.0001 up
  to the rate where the coarse sweep first crossed. Their loads are snapped to the 0.0001 grid. The
  other scenarios keep the 0.0005 grid and the coarse sweep rates.
* **Lsat** = the largest swept rate before the latency first exceeds 3 x L0 (as before). The
  evaluation loads are 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat (as before), bumped by one grid step
  if two coincide.

## Why this is the conservative choice
It restores the pre-registered design (7 loads spanning about 0.2-1.6 x Lsat, the 4th at 1.0 x
Lsat) in every scenario, instead of testing some scenarios at about 2 x Lsat. It was fixed before
any evaluation data existed, and it applies the same rule to every variant. Both the coarse and
the amended load points are kept (`load_points_coarse.*`, `load_points.*`).
