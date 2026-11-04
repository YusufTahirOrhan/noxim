# v21 findings: a fast selection, DEFT_FAST

**Sources:** design `PREREGISTRATION.md` (82d9e53) and `PREREGISTRATION_addendum.md` (b99dfa9), both before any evaluation run; decisions `DECISIONS.md`; tables `report/summary.md`, `report/primary.csv`, `secondary.csv`, `sensitivity.csv`, `area.csv`; timing `timing.md`, `n_fast.json`; figure `report/latency_load.{png,pdf}`; data `eval_runs.csv`.

## The answer
**Does the fast selection, at its measured N_fast, keep a latency gain over DeFT with the round-robin?**

| | CI (chosen: CI_fastQL, N = 3) 2x2 / 3x3 / 4x4 | FULL (chosen: FULL_fastQL, FULL_fastQL, FULL_fast; N = 3) 2x2 / 3x3 / 4x4 |
|---|---|---|
| **Mean latency at saturation (1.0 x Lsat)** | **-12.4 %** / 0.0 % n.s. / -2.7 % n.s. | -1.4 % n.s. / +4.2 % n.s. / +8.5 % n.s. |
| **Mean latency at low load (0.2 x Lsat)** | **+38.5 % / +50.9 % / +58.3 %, worse** | **+52.9 % / +62.8 % / +65.8 %, worse** |
| p99 at saturation | **-43.6 % / -32.2 % / -42.0 %** | **-37.7 % / -36.8 % / -30.3 %** |
| Saturation throughput | +8.2 % / -1.9 % / -0.2 % n.s. | -2.7 % / -6.5 % / -8.3 % |

Bold = holds up statistically (Holm for saturation latency and p99; unadjusted, with narrow CIs, for low load).

* **At saturation: only on 2x2, and only with CI.** On 3x3 and 4x4 no mean-latency gain over DeFT is left, and on 2x2 FULL none either.
* **At low load: no. It loses on every size and every variant,** by 23-67 %, with very narrow intervals. This includes `CI_fast`, the least delayed variant, at +22.6 / +31.5 / +37.1 %.
* **What survives is p99 at saturation:** all 6 tests are supported, -30 % to -44 %.

**At what area cost?** System-level router area relative to DeFT, in the form the simulator models (one unit per input port):

| | 2x2 / 3x3 / 4x4 |
|---|---|
| CI_fast | 1.52 / 1.52 / 1.51 |
| CI_fastQL (chosen for CI) | **2.00 / 2.16 / 2.44** |
| FULL_fast | 2.25 / 2.23 / 2.22 |
| FULL_fastQL | 3.18 / 3.51 / 4.03 |

So the configuration tested in the primary hypotheses costs 2.0 to 2.4 times DeFT's router area for CI and 2.2 to 3.5 times for FULL, for a p99 gain and no general mean-latency gain. The smaller form with one unit per router (1.16 for CI_fast, up to 2.32 for FULL_fastQL) is not what was simulated; see "Area" below.

**No variant decides within one cycle, so the goal of this round was not met.** The fastest needs two decision cycles.

## Run integrity
* 19,600 of 19,600 runs, 0 missing, 0 truncated, 0 byte-identical across seeds, 0 dead-end events. Binary md5 a82a1590224f4c2ed253c256c0285792.
* Regression: 84 / 84 byte-identical with the options absent or explicit, and for the K5 build (`regression.md`).
* 20 / 20 K5 baseline runs reproduce exactly on this binary (`k5_check.md`).
* Drain tests: 216 / 216 PASS before tuning (`drain_summary.csv`), 216 / 216 PASS with the tuned variants at N_fast (`drain_summary_tuned.csv`). An assertion in `selectFast` checks that the choice is offered; it never fired.
* fastQL at alpha 0 equals the fast heuristic: 6 / 6 (`alpha0_check.md`).

## F1: the function
* **H from a ROM is exact, but not with the index the prompt names.** (output, 4-bit mask) gives several H values for every entry, spread up to 53 hops, since H depends on the destination. (router, mask, destination) is exact: 0 mismatches against `hopsAfterMove` in 24 configurations of size, scope and fault mask (`rom_check.txt`).
* **The lookahead is different,** as the prompt intends: L is one packet-independent value per router. What changes is listed in `DECISIONS.md`.

## F2: timing (NanGate45, pre-layout, v18 flow)
RTL against the simulator: **1,450,802 vectors, 0 mismatches**, with the tuned weights (`functional_check.txt`). Router smoke test: 112 / 112 (`router_smoke.txt`). The router top level is not otherwise functionally checked.

Arrival + setup in ns, one unit per input port, ranges over sizes and router types, tuned weights:

| variant | stage A | decision, no cut | with the cut: first stage | second stage | **N_fast** (age) |
|---|---|---|---|---|---|
| CI_fast | 0.80-0.99 | 1.28-1.52 | 0.82-1.00 | 0.72-0.78 | **2** (2) |
| CI_fastQL | 0.81-1.17 | 1.52-1.81 | 0.97-1.14 | 0.82-1.06 | **3** (2) |
| FULL_fast | 0.83-1.96 | 1.22-1.66 | 0.82-1.05 | 0.67-0.89 | **3** (2) |
| FULL_fastQL | 0.78-1.87 | 1.48-1.79 | 0.93-1.20 | 0.85-1.06 | **3** (2) |

**How far it misses, and what dominates:**
* **Uncut, the decision misses 1 ns by 0.22-0.81 ns.** The parts are the minimum over the kept candidates, the add, and the parallel comparisons, each about a third of a nanosecond. No single part dominates.
* **The cut is the cost register.** With it, CI_fast fits on 5 of its 6 router designs. It misses on the 4x4 interposer router with a VL by **0.003 ns**.
* **Learning costs a cycle:** the residual adds a carry chain and wider comparators (first stage up to 1.20 ns).
* **LB-F's chiplet routers are the limit for FULL:** the path totals of the source phase take 1.5-1.96 ns in stage A, adding a cycle. FULL_fast's interposer routers alone would need N = 2.
* **Q update:** misses 1 ns by 0.53-1.00 ns. It is off the decision path, and the simulator applies it 3 cycles later.
* **Previous-cycle terms fit:** sums into `pre_p` 0.47 ns, value on the link at most 0.93 ns.

Compared with v18's plain design (5-7 cycles in total), this needs 3-4 (N + 1), a saving of 1-3 cycles. It does not reach one.

**N rests partly on very small misses.** CI_fast's N = 2 turns on 0.003 ns, and FULL_fast's move from 2 to 3 on 0.02-0.05 ns; the flow's noise is 0.06-0.18 ns. The rule was applied strictly and these Ns were used, which does not favour our methods. The rows at the lower N are below; they do not change the answer.

## F4: confirmatory results (Holm over 36)
**H1, against DeFT(rho\*) with the round-robin: 7 of 12 supported, 5 n.s., none against.** All 6 p99 tests and 1 of 6 latency tests (2x2 CI).

**H2, against MTR and RC, fault-free: 9 of 24 supported, 8 n.s., 7 significantly against ours.**

| LAT @1.0 Lsat, % | vs MTR | vs RC | P99 vs MTR | P99 vs RC |
|---|---|---|---|---|
| 2x2 CI_fastQL | +7.0 n.s. | **+18.4 against** | **-22.0** | -9.4 n.s. |
| 2x2 FULL_fastQL | **+20.4 against** | **+33.2 against** | **-13.6** | +0.4 n.s. |
| 3x3 CI_fastQL | -4.2 n.s. | -2.3 n.s. | **-28.0** | **-25.5** |
| 3x3 FULL_fastQL | -0.9 n.s. | +1.0 n.s. | **-34.0** | **-31.7** |
| 4x4 CI_fastQL | **+7.9 against** | **+4.5 against** | **-21.7** | **-24.9** |
| 4x4 FULL_fast | **+21.1 against** | **+17.2 against** | -5.8 n.s. | **-9.6** |

All 9 supported tests are p99. **No mean-latency test against MTR or RC is supported on any size.**

**At low load against MTR and RC (secondary):** every variant is slower, +29 % to +70 %.

**Saturation throughput against MTR and RC (secondary):** every variant is lower, -2.8 % to -17.5 %.

**DeFT-Dis and DeFT-Ran (secondary):** every variant has lower latency and p99 on every size (LAT -14 % to -57 %, P99 -44 % to -72 %). Throughput is higher for all CI variants but one tie (4x4 CI_fast vs DeFT-Dis, -0.2 %, n.s.); FULL is mixed, mostly lower than DeFT-Dis (-5.4 % to +1.8 %).

**The check against the DeFT paper repeats K5:** DeFT with the round-robin stays below MTR and RC in throughput on every size (-3.2 % to -9.4 %).

### All variants against DeFT (secondary, unadjusted)
| size | variant | N | LAT @1.0 | LAT @0.2 | P99 | THR |
|---|---|---|---|---|---|---|
| 2x2 | CI_fast | 2 | -12.9 | +22.6 | -35.2 | +6.9 |
| 2x2 | CI_fastQL | 3 | -12.4 | +38.5 | -43.6 | +8.2 |
| 2x2 | FULL_fast | 3 | +9.3 | +52.2 | -23.6 | -5.5 |
| 2x2 | FULL_fastQL | 3 | -1.4 | +52.9 | -37.7 | -2.7 |
| 3x3 | CI_fast | 2 | +2.1 | +31.5 | -15.4 | -4.6 |
| 3x3 | CI_fastQL | 3 | 0.0 | +50.9 | -32.2 | -1.9 |
| 3x3 | FULL_fast | 3 | +14.6 | +61.4 | -20.8 | -9.4 |
| 3x3 | FULL_fastQL | 3 | +4.2 | +62.8 | -36.8 | -6.5 |
| 4x4 | CI_fast | 2 | -4.5 | +37.1 | -33.5 | -3.3 |
| 4x4 | CI_fastQL | 3 | -2.7 | +58.3 | -42.0 | -0.2 |
| 4x4 | FULL_fast | 3 | +8.5 | +65.8 | -30.3 | -8.3 |
| 4x4 | FULL_fastQL | 3 | +4.1 | +67.0 | -39.5 | -6.5 |

### Sensitivity to N (secondary, seeds 81-85)
| size | variant | N | LAT @1.0 | LAT @0.2 |
|---|---|---|---|---|
| 2x2 / 3x3 / 4x4 | CI_fast, N = 1 (misses timing by 0.003 ns) | 1 | -13.2 / +0.9 / -5.7 | **+8.1 / +13.3 / +16.6** |
| 2x2 / 3x3 / 4x4 | CI_fast | 2 | -11.3 / +1.4 / -2.1 | +22.6 / +32.3 / +37.2 |
| 2x2 / 3x3 / 4x4 | CI_fast | 3 | -5.8 / +8.1 / +2.8 | +37.4 / +50.1 / +58.2 |
| 2x2 / 3x3 / 4x4 | FULL_fast, N = 2 (misses timing) | 2 | +3.6 / +5.1 / +1.7 | +32.1 / +38.6 / +41.3 |

* **Giving CI_fast the lower N does not change the answer.** Low-load latency is still worse by 8-17 %. At saturation it gains only on 2x2 and, slightly, on 4x4.
* **N = 0 was not simulated for `DEFT_FAST`.** Each cycle costs about 15-21 % at low load on CI_fast, so the low-load gain would at best be small even with no delay. That is an extrapolation, not a measurement. v20 measured -2 % to -8 % for the old selection at N = 0.
* **p99 and throughput barely move with N** (`sensitivity.csv`), as in v20.

## Area (hierarchical, as v18)
| | one unit per input port: 2x2 / 3x3 / 4x4 | one unit per router: 2x2 / 3x3 / 4x4 | v18, slow selection, one unit per router |
|---|---|---|---|
| CI_fast | 1.52 / 1.52 / 1.51 | 1.16 / 1.16 / 1.16 | 1.17 / 1.17 / 1.17 |
| CI_fastQL | 2.00 / 2.16 / 2.44 | 1.39 / 1.50 / 1.66 | 1.38 / 1.47 / 1.63 |
| FULL_fast | 2.25 / 2.23 / 2.22 | 1.35 / 1.35 / 1.35 | 1.39 / 1.39 / 1.39 |
| FULL_fastQL | 3.18 / 3.51 / 4.03 | 1.81 / 2.01 / 2.32 | 1.77 / 1.98 / 2.30 |

* **The fast design is not smaller.** In the same form it costs about what the slow selection cost: the lookahead logic saved is spent on stage registers.
* **The per-port form is what N_fast and the simulator assume:** every port decides each cycle, and a head on the link enters stage A directly.
* **The per-router form is smaller but slower, and not simulated as such.** Stage A takes up to 1.31 ns for CI_fast and 2.18 ns for FULL, with no direct entry from the link. A head would need at least one cycle more than the per-port timing suggests, so **N = 3 at least for CI_fast**, plus contention between ports that the simulator does not charge. The N_fast + 1 row above is its optimistic estimate: no gain on 3x3 and 4x4 at saturation, and +37 % to +58 % at low load.

## Limits
* **The delay is charged to our methods only.** No baseline gets a pipeline stage. Their route stage is about 1 ns in the same flow (0.8-1.1 ns), but v18's reference paths also miss 1 GHz slightly, for switch allocation.
* **A single-output hop skips the delay in the simulator.** The RTL has no bypass for this, so a real design pays for it in logic, or in delay on those hops. With one output are 34-39 % of interposer hops (v20), and all chiplet hops of CI. This favours our methods.
* **Not modelled, all favouring our methods:** a blocked head in the RTL retries every 2-3 cycles rather than every cycle; the round-robin counter is read in the first decision stage in the RTL and at the choice in the simulator.
* **Pre-layout, no wires.** The value on the links adds 8 bits per direction, counted as registers only.
* **FULL_fast was tuned at N = 2, age 1, and run at N = 3, age 2** (addendum). It is the chosen FULL variant on 4x4. Whether re-tuning helps is not known; the tuned criterion favoured it over the learner there by 2 %.
* **Tuning:** at the K5 loads on 2 seeds, as in v6. Two optima lie past the base grid (w = 4 after the one-step extension: 3x3 CI, 4x4 FULL), and 2x2 CI's alpha is on the edge of its grid (0.1).
* **The raw tuning runs were deleted before a per-run CSV was written.** `tuning.md` has every configuration's score, and the runs can be repeated.
* **ROM with faults:** the RTL's totals take the entry mask as an input, so they are logic, not a stored ROM of minimum size. Timing was measured for one position per router type and size.
* **Seeds and scenarios:** LAT at 1.0 x Lsat stays seed-sensitive; the low-load intervals are narrow.

## Conclusion for the paper
* **Do not claim a mean-latency gain over DeFT for a design with realistic decision timing,** except 2x2 with CI at saturation. At low load the methods are 23-67 % slower.
* **What can be claimed, with the delay charged:** p99 at saturation 30-44 % below DeFT on all sizes, significant after Holm. Against MTR and RC, p99 is significant in 9 of 12 tests, and mean latency in none, with 7 significantly worse.
* **The area price of that p99 gain** is 2.0-2.4 x DeFT for the CI learner in the form simulated.
* **The larger gains of v9-v19 stand only as zero-delay results:** they assume a decision that the RTL does not achieve.
* **The result rests on the delay model of v20:** N extra cycles on each multi-output hop, which is why low load suffers most. Fewer multi-output hops, or a route decided once and carried with the packet, would change this; neither is designed or tested here.
