# Decisions taken without the author (v16, Part H)

1. **Float reference is float32:** the existing Q table stores its values as `float` (32-bit), not `double`.
   `ql_bits 0` keeps that storage unchanged, so the reference is the float32 behaviour of v9.
2. **Residual-range logging behind an option:** min / max of R are written only with `-deft_lb ql_range 1` or
   `ql_bits > 0`. An always-on field would have changed the JSON output of every existing run, and so the
   byte-identical regression.
3. **Range runs on a development build:** the range runs (seed 1001, not an evaluation seed) used the development build
   of the same code (float storage, `ql_range 1`). The fixed-point formats were fixed from them before the
   pre-registration. The evaluation uses the final `bin/noxim` (md5 3bc747ae), whose regression is 84 / 84
   byte-identical (`regression.md`).
4. **Integer bits per size:** I = ceil(log2(2 x max |R|)), one format per size for both variants. On 3x3 and 4x4 this
   gives F = 0 at B = 8, so the stored residuals are integers.
   - This was not adjusted after the fact (for example by narrowing the margin to save a fractional bit). That is the
     conservative choice, since it risks a failure at 8 bits.
5. **Rounding:** round half up, floor(x x 2^F + 0.5); the stored value is saturated to the B-bit range on every update.
6. **Reference reuse:** the v9 float runs (`results_v9/eval_runs.csv`) cover all 3150 evaluation configurations; this
   was checked before the evaluation (0 missing).
   - `ql_bits 0` reproduced 20 / 20 randomly drawn v9 runs exactly (`reuse_check.md`).
7. **Faulty scenario on 2x2:** the VL mask is 0x1111 (one faulty VL per chiplet), which is among the v9 masks. 3x3 and
   4x4 use the v9 one-per-chiplet masks.
