# v20 findings: decision-delay sensitivity (Part L, descriptive)

**Sources:** design `PREREGISTRATION.md` (dea53a6, before any L run and any K5 result); decisions `DECISIONS.md`; tables `report/summary.md`; figure `report/delay_effects.{png,pdf}`; data `delay_runs.csv`, `pre_runs.csv`.

## Checks
* **N = 0:** 84 / 84 byte-identical with the option given (K regression); 9 / 9 byte-identical to the K5 runs with the round-robin (`n0_check.md`).
* **Drain tests at N = 4:** 162 / 162 PASS (`drain_summary.csv`).
* **The delay acts as defined** (`delay_sanity.md`): at very low load, latency rises by about N x (multi-output hops per packet). Within 8 % at N = 4; up to 37 % at N = 1, on about 100 packets per run.
* **Runs:** 3,780 of 3,780, 0 dead-end events, same binary as K5.

**How to read N.** N is added to the router's existing cycle. A design whose path takes c cycles corresponds to about N = c - 1, on multi-output hops only.

## Result in one paragraph
**The latency gain over DeFT does not survive the delay that a plain implementation would need.** At 1.0 x Lsat the gain shrinks with N and is gone by N = 4 on 3x3 and 4x4. At low load, a single extra cycle already puts every variant behind DeFT. Only p99 at 1.0 x Lsat and saturation throughput hold up, and both come with the caveat below. v18 puts the plain design at c = 5-7, so N = 4-6, at or beyond the largest N tested.

## LAT at 1.0 x Lsat against DeFT(rho\*) with the round-robin (% ; 95 % CI, 5 seeds)

| size | variant | N = 0 | N = 1 | N = 2 | N = 4 |
|---|---|---|---|---|---|
| 2x2 | CI_heurLA_G | -26.6 \* | -21.3 \* | -19.6 \* | -9.3 [-25.7, +10.8] |
| 2x2 | CI_qlLA_G | -29.4 \* | -26.2 \* | -24.7 \* | -13.8 [-27.9, +3.1] |
| 2x2 | FULL_qlLA_G | -18.5 \* | -17.0 \* | -12.5 | +2.5 [-15.5, +24.4] |
| 3x3 | CI_heurLA_G | -6.1 \* | -3.7 | -3.4 \* | **+10.4 [+6.8, +14.2]** |
| 3x3 | CI_qlLA_G | -10.7 \* | -10.1 \* | -7.2 \* | **+6.8 [+0.5, +13.6]** |
| 3x3 | FULL_qlLA_G | -7.2 \* | -4.1 | -2.0 | **+15.1 [+10.8, +19.7]** |
| 4x4 | CI_heurLA_G | -15.6 \* | -11.6 | -8.3 | +7.5 [-5.8, +22.6] |
| 4x4 | CI_qlLA_G | -17.4 \* | -16.7 \* | -10.7 | +7.8 [-4.0, +21.1] |
| 4x4 | FULL_qlLA_G | -19.7 \* | -18.2 \* | -12.1 \* | +9.2 [-2.3, +22.1] |

\* = CI entirely below 0. Bold = CI entirely above 0: significantly slower than DeFT. The N = 0 column covers these 4 scenarios and 5 seeds, so it differs from K5's H1 table.

## Smallest N at which each variant stops beating DeFT (pre-registered rule)

| size | variant | LAT | THR |
|---|---|---|---|
| 2x2 | CI_heurLA_G | 4 | > 4 |
| 2x2 | CI_qlLA_G | 4 | > 4 |
| 2x2 | FULL_qlLA_G | 2 | 0 |
| 3x3 | CI_heurLA_G | 1 | > 4 |
| 3x3 | CI_qlLA_G | 4 | > 4 |
| 3x3 | FULL_qlLA_G | 1 | 0 |
| 4x4 | CI_heurLA_G | 1 | 0 |
| 4x4 | CI_qlLA_G | 2 | > 4 |
| 4x4 | FULL_qlLA_G | 4 | 0 |

* **This rule is noisy, as the pre-registration warned.** With n = 5, 3x3 CI_heurLA_G "stops" at N = 1 and beats DeFT again at N = 2, and 4x4 CI_heurLA_G stops at N = 1 through a wide CI at -11.6 %. Read it with the point estimates: **they cross zero between N = 2 and N = 4 on 3x3 and 4x4, and stay below zero up to N = 4 on 2x2 except FULL_qlLA_G.**
* **THR = 0** means no significant throughput gain over DeFT even at N = 0 on these 4 scenarios, not a loss caused by the delay. On 3x3, FULL_qlLA_G is below DeFT at every N (-2.6 % to -4.5 %).

## Low load (exploratory, added after seeing the data)
LAT at 0.2 x Lsat against DeFT. Not pre-registered. It was added because a head at low load is held by nothing else and pays the whole delay, which the pre-registered point at 1.0 x Lsat hides.

| | N = 0 | N = 1 | N = 2 | N = 4 |
|---|---|---|---|---|
| 2x2, three variants | -7.3 to -8.0 | +7.5 to +12.8 | +23.1 to +33.0 | +55.6 to +75.9 |
| 3x3 | -2.4 to -4.7 | +13.9 to +17.7 | +32.7 to +40.2 | +71.4 to +87.8 |
| 4x4 | -2.8 to -6.2 | +16.7 to +18.2 | +37.6 to +41.8 | +80.7 to +92.2 |

All with narrow CIs (`report/low_load.csv`). **At low load the gain is small even at N = 0, and N = 1 reverses it on every size and variant.**

## P99 and THR do not fall with N: read with care
* **P99 at 1.0 x Lsat** stays 28-56 % below DeFT at every N, and for some variants it is lower at N = 2 than at N = 0.
* **THR rises with N** for CI_heurLA_G and CI_qlLA_G (for example 4x4 CI_qlLA_G +6.8 % at N = 0, +10.4 % at N = 2).
* **What the data show:** per load, CI_qlLA_G on uniform traffic, accepted flits and latency at N = 0 / 2 / 4:
  * below saturation, accepted is the same and latency rises (4x4 at 0.2 x Lsat: 33 / 46 / 61 cycles);
  * above saturation, accepted is higher and latency is lower (4x4 at 1.4 x Lsat: 0.0605 / 0.0672 / 0.0660 accepted; 767 / 396 / 581 cycles).
* **Not a claim that delay is good.** The delay reduces the collapse beyond saturation. It could act as a throttle or through a selection on fresher state, and this round does not separate the two. It may also point to a tuning or stability problem of the undelayed selection at overload, which was not examined.
* These two metrics cannot be cited alone as "robust to delay".

## Share of hops with more than one offered output

| | chiplet | interposer |
|---|---|---|
| CI_heurLA_G, CI_qlLA_G | 0 % | 60.7-65.6 % |
| FULL_qlLA_G | 40.4-41.5 % | 63.6-66.5 % |

Over all loads and N >= 1. The delay model charges only these hops. FULL_qlLA_G pays on the chiplets as well, which fits its larger low-load cost.

## L3: terms computed in the previous cycle (an estimate, timing only, not functionally checked)
Table: `report/summary.md`. Cycles at 1 GHz, ceil(arrival + setup), no register overhead; ranges over sizes and router types.

| | heuristic | Q-learning |
|---|---|---|
| as simulated (v18) | 4.5-5.5 ns, 5-6 cycles | 5.2-6.5 ns, 6-7 cycles |
| PRE 1: same function, occupancy one cycle old | 4.3-5.5 ns, 5-6 cycles | 5.4-6.3 ns, 6-7 cycles |
| PRE 2: the design in the prompt | **3.0-3.8 ns, 4 cycles** | **4.0-4.4 ns, 5 cycles** |

* **The occupancy terms do fit the previous cycle:** 0.37-0.38 ns.
* **Only the design that changes the function helps.** Registering occupancy while keeping the function gains nothing (PRE 1), since the long path is the coupled minimum over moves and candidates, which needs the packet.
* **PRE 2 saves 1-2 cycles and still needs about N = 3 (heuristic) or N = 4 (Q-learning).** It is a different selection function, so **the L2 numbers do not apply to it directly**; they describe the simulated function with a delay. If PRE 2 performed as the simulated function does, the L2 table above suggests little or no latency gain at N = 3-4. Its own performance was not simulated.

## Limits
* **The delay is charged to our methods only.** No baseline gets a pipeline stage. This is the setting that does not favour our methods, and it is also the fair one on the v18 numbers (baselines fit about 1 ns), with the caveat that v18's reference paths also miss 1 GHz slightly.
* **N = 3 was not run,** and the mapping from cycles to N assumes a pipeline with no other cost, such as the head holding its VC longer or the state being older.
* **Parameters** were not re-tuned for a delay.
* **n = 5 seeds on 4 scenarios.** LAT at 1.0 x Lsat is seed-sensitive, particularly under hotspot, so the CIs are wide.

## Conclusion for the paper
All simulated latency gains of the late-binding methods assume zero extra cycles. **State this next to every latency number:** at 1.0 x Lsat the point estimates stay below DeFT up to N = 2 (the CI is entirely below 0 in 5 of 9 cells at N = 2), and the gain is gone by N = 4 on 3x3 and 4x4. At low load, one cycle removes it. v18 and L3 provide no design that decides within 2 extra cycles. Without one, what remains in hardware terms is throughput and p99 near and above saturation, with the caveat above, and not mean latency.
