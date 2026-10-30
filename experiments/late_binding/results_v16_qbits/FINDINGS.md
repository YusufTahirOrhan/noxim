# v16 findings: Q-table entry width (Part H)

**Sources:**
* Design: `PREREGISTRATION.md`. Formats: `range.md`, `qformat.json`.
* Report: `report/summary.md`, `report/equivalence.csv`, `report/cost_table_qbits.md`.
* Runs: `eval_runs.csv`, 3150 of 3150 with no missing run. The reference is the reused v9 float runs, seeds 41-45.
* Learning statistics: `ql_stats.csv`.

**Checks:**
* `ql_bits 0` regression: 84 / 84 byte-identical (`regression.md`).
* Reuse: 20 / 20 v9 runs reproduced exactly (`reuse_check.md`).

## Pre-registered result
**No tested width is equivalent: none of B = 16, 12 or 8 meets all three margins for both variants on every size.
Not one (size, variant, B) cell is equivalent.**

Effects are fixed point vs float (%), with the 95 % CI over seeds 41-45 (n = 5). The margins are LAT +-3 %, P99 +-5 %
and THR +-1 %.

| size | variant | B = 16: LAT / P99 / THR | B = 12: LAT / P99 / THR | B = 8: LAT / P99 / THR |
|---|---|---|---|---|
| 2x2 | CI_qlLA_G | -2.2 / -5.6 / +0.2 | -1.6 / -6.7 / +0.7 | -1.1 / -3.8 / +0.2 |
| 2x2 | FULL_qlLA_G | -1.1 / -3.9 / +0.1 | -1.7 / -4.6 / +0.2 | +3.2 / +1.5 / +0.3 |
| 3x3 | CI_qlLA_G | -0.8 / -2.3 / +0.3 | -2.0 / -2.2 / +0.4 | +0.8 / +1.1 / **-2.1** |
| 3x3 | FULL_qlLA_G | -1.0 / -1.4 / -0.4 | -0.4 / -2.4 / +0.0 | +2.8 / +3.0 / +0.2 |
| 4x4 | CI_qlLA_G | **+2.5** / **+6.9** / +1.1 | +0.1 / +2.7 / +0.0 | +3.1 / +11.0 / **-2.0** |
| 4x4 | FULL_qlLA_G | +3.5 / +6.6 / +0.8 | +3.5 / +7.6 / +0.7 | **+7.2** / **+14.4** / -0.7 |

Bold marks an effect whose 95 % CI lies entirely on one side of zero, with the fixed-point version worse.

The cost table therefore keeps 16 bits (`report/cost_table_qbits.md`): 320 / 720 / 1280 bits per router for
2x2 / 3x3 / 4x4, or 21 / 47 / 83 % of a router's input-buffer bits.

## Why 16 and 12 bits fail
The CIs are too wide, not the effects too large.
* **Point estimates:** at B = 16 and 12, most lie inside the margins. LAT is between -2.2 % and +3.5 %, and THR between
  -0.4 % and +1.1 %.
* **CI width:** with n = 5 seeds the 95 % CIs are typically +-3-10 % for LAT and +-7-20 % for P99. They cannot fit
  inside +-3 % and +-5 %.
* **Source of the spread (exploratory, `report/exploratory_per_scenario_lat.txt`):** it comes from the hotspot and
  movinghot scenarios at 1.0x Lsat. There, the per-seed log ratio of latency has a standard deviation of 4-40 % even at
  B = 16, where rounding is at the 2^-8 to 2^-10 level.
  - Any change to a single stored value changes later routing choices. At saturation, such a change moves the run to a
    different trajectory, so a fixed-point run behaves like another sample of the same system rather than a small
    perturbation of the float run.
  - In uniform, chipperm and uniform with a faulty VL, B = 16 stays within +-3.2 %, and 14 of these 18 cells are within
    +-1.5 % (sd 0.2-6.9 %).
* **One exception that looks real:** CI_qlLA_G on 4x4 at 16 bits has LAT +2.5 % [+0.2, +4.7] and P99 +6.9 %
  [+3.0, +10.9], driven by hotspot (+15.5 %).
  - With 7 integer bits and 8 fractional bits the format should represent the values closely, so this may be a
    trajectory effect of the hotspot scenario rather than a precision effect. These data cannot separate the two.
* **Equivalence at this margin needs a less chaotic metric or more seeds.** The design can only show equivalence when the
  per-seed log ratio has an sd below about 2.4 % for LAT with a zero mean (half-width 2.78 x sd / sqrt 5).

## 8 bits: does learning stall?
**Yes for FULL_qlLA_G, almost entirely for CI_qlLA_G.** The table gives the share of updates that change the stored
value (mean over runs); its full form is in `report/summary.md` and `ql_stats.csv`.

| size | CI_qlLA_G 16 / 12 / 8 bits | FULL_qlLA_G 16 / 12 / 8 bits |
|---|---|---|
| 2x2 (F = 10 / 6 / 2) | 85 / 69 / 11 % | 68 / 38 / **0 %** |
| 3x3 (F = 8 / 4 / 0) | 83 / 64 / 5 % | 69 / 17 / **0 %** |
| 4x4 (F = 8 / 4 / 0) | 84 / 69 / 5 % | 79 / 53 / **0 %** |

* **FULL_qlLA_G:** at 8 bits no update ever changes a stored residual. The table stays at its initial value: the stored
  range is 0..1, 0..0 and 0..2 versus about -15..+26 in float.
  - The method then runs on its heuristic prior alone. Its update steps (learning rate x TD error) are smaller than half
    a quantisation step (2^-2, or 1 for F = 0).
* **CI_qlLA_G:** 5-11 % of the updates still change the table at 8 bits. These are the large residuals (up to 48).
  Small corrections are lost, and the negative side is almost empty (min -2 / -0.25).
* **Consequences at 8 bits:**
  - CI_qlLA_G loses 2 % of saturation throughput on 3x3 and 4x4: THR -2.1 % [-2.8, -1.3] and -2.0 % [-3.0, -0.9],
    both entirely outside the -1 % margin.
  - FULL_qlLA_G's latency rises by 7 % on 4x4 (LAT +7.2 % [+2.8, +11.9], P99 +14.4 %).
  - Uniform fault-free traffic shows a consistent +3.4 to +5.3 % latency increase on 3x3 and 4x4 for both variants
    (sd 1.2-2.7 %). This is a real degradation, not noise.
  - Uniform with a faulty VL shows the same increase (+3.3 to +5.8 %), except CI_qlLA_G on 3x3 (+0.2 %).
* **What 12 bits still does:**
  - 17-69 % of the updates still change the table at 12 bits. Learning is slower but active.
  - At 12 bits the point estimates are as close to float as at 16 bits (exploratory reading).

## Conclusion for the paper
* **8-bit entries are not enough:** learning stalls (FULL) or nearly stalls (CI) on every size, with a measurable
  throughput or latency penalty.
* **16 and 12 bits could not be shown equivalent** under the pre-registered margins and 5 seeds. The point estimates are
  mostly within the margins, but the latency of hotspot and movinghot at 1.0x Lsat is too seed-sensitive for the CIs to
  fit.
* **Hardware cost:** the cost table uses 16 bits. A claim that 12 bits suffice would need a new confirmatory test with
  more seeds or a load below saturation.
