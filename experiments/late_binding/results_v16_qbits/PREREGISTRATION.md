# Pre-registration v16 (Part H): Q-table entry width (equivalence test)

Committed before any equivalence run. The fixed-point formats were fixed from the residual range (`range.md`,
`qformat.json`; float runs at seed 1001, not evaluation seeds).

## Implementation
* **Option:** `-deft_lb ql_bits B` (0 = the current float32 storage) and `-deft_lb ql_frac F`.
  - B > 0: each residual R is stored as a signed fixed-point value of B bits with F fractional bits.
  - On every update, R is computed in floating point, rounded to the nearest multiple of 2^-F, and saturated to
    [-2^(B-1), 2^(B-1) - 1] x 2^-F.
* **Format per size:** I = ceil(log2(2 x max |R|)) integer bits (the observed maximum with a factor-2 margin), and
  F = B - 1 - I.

  | size | max abs R | I | F for B = 16 / 12 / 8 |
  |---|---|---|---|
  | 2x2 | 10.7 | 5 | 10 / 6 / 2 |
  | 3x3 | 33.6 | 7 | 8 / 4 / 0 |
  | 4x4 | 49.3 | 7 | 8 / 4 / 0 |

## Design
* **Variants:** CI_qlLA_G and FULL_qlLA_G (v10 parameters).
* **Sizes:** 2x2, 3x3, 4x4.
* **Scenarios:** uniform, hotspot, chipperm, movinghot (fault-free), and uniform with one faulty VL per chiplet (2x2
  0x1111, 3x3/4x4 the v9 mask).
* **Loads:** the 7 v9 load points.
* **Seeds:** 41-45.
* **B:** 16, 12, 8.
* **Runs:** 2 x 3 x 5 x 7 x 5 x 3 = 3150.
* **Reference:** the v9 float runs (`results_v9/eval_runs.csv`, the same seeds), reused after the check that
  `ql_bits 0` reproduces 20 random v9 runs of these variants exactly.

## Metrics and equivalence (margins fixed now)
* **Metrics:** LAT and P99 at 1.0 x Lsat, and THR (saturation throughput) as in v9.
* **Effect of B against float:** the mean over the 5 scenarios of the per-seed log ratio, 100 x (exp(mean) - 1) %, with
  a 95 % CI over the 5 seeds.
* **Margins:** LAT +-3 %, P99 +-5 %, THR +-1 %.
* B is **equivalent** for a variant and size if the 95 % CIs of all three effects lie inside their margins.
* The smallest B that is equivalent for both variants on all sizes is reported, and the cost table is updated with it.
* If 8 bits fail, the report states whether learning stalls: the share of updates that leave the stored value
  unchanged (`ql_updates_changed`), and the residual range.

## Exclusions
A missing run is listed. A seed with a missing run in any scenario of a comparison is dropped from that comparison, and
this is reported.
