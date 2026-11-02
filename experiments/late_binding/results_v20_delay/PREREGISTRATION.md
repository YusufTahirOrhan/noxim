# Pre-registration v20 (Part L): decision-delay sensitivity (descriptive)

Committed before any L run and before any K5 result exists. No test is confirmatory in this round; the rules below only fix what is reported.

## Option
`-deft_lb decision_delay N`, default 0. A head at a router that offers it more than one output waits N extra cycles after reaching its buffer front before it may reserve an output. Hops with one offered output, including all baseline hops, get no delay.

## Design
* **Variants:** CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G, all with `-deft_vn_rr 1`, at N = 1, 2, 4. Parameters: `experiments_v10.methods`, no re-tuning.
* **Sizes and loads:** all sizes, the 7 K4 load points.
* **Scenarios:** uniform, hotspot and chipperm fault-free, and uniform with one faulty VL per chiplet.
* **Seeds:** 61-65, the first 5 K5 seeds. **Window:** 2000 + 8000 cycles.
* **Reference:** N = 0 and DeFT(rho\*) with the round-robin come from the K5 runs (same binary, seeds and loads).
* **Runs:** 3 x 3 x 3 x 4 x 7 x 5 = 3,780.

## Checks before the runs
* With N = 0, outputs are byte-identical (part of the K regression, with the option given explicitly).
* Drain tests pass at N = 4 for the three variants on all sizes, masks and protocols of K2.

## Report
* LAT and P99 at 1.0 x Lsat, and THR (maximum accepted over the 7 loads), against DeFT(rho\*) with the round-robin, for N = 0, 1, 2, 4, on every size. Effect = 100 x (exp(mean R) - 1) %, R(s) the mean over the 4 scenarios of the per-seed log ratio, with a 95 % CI over seeds 61-65 (n = 5).
* **"Beats DeFT" at a given N:** the 95 % CI of the effect lies entirely on the better side of 0 (below 0 for LAT, above 0 for THR).
* **The smallest N at which each variant stops beating DeFT**, in LAT and in THR, per size: the smallest N of {0, 1, 2, 4} at which it does not beat DeFT, or "> 4". The point estimates are shown next to it, since n = 5 is small: a variant can "stop" through a wide CI alone.
* The share of hops with more than one offered output, per variant and layer (chiplet, interposer), from the runs with N >= 1.

## Limits fixed in advance
* The delay applies only where more than one output is offered. It is a uniform N per such hop, not the v18 path delay, and it adds no router pipeline to any other method.
* The parameters were not re-tuned for a delayed decision.
