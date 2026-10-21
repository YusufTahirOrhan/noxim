# Pre-registration v9, addendum: seed choice (committed before the evaluation starts)

Seed rule (PREREGISTRATION.md): if the estimated wall time of the full evaluation with seeds 41-50 is at most 9 h,
use seeds 41-50; otherwise 41-45.

Timing test (`runtime_estimate.md`, `seed_choice.json`): 375 runs (seed 1001; all five run types x 3 sizes x every
scenario at the 2nd, 4th and 7th load), 12 processes, 1299 s wall, 0 missing. Estimate for seeds 41-50 (8750 runs):
**8.4 h <= 9 h**.

**Seeds: 41-50.** No evaluation run had been made when this was committed. The 2x2 drain tests passed (102 / 102,
`drain_summary.csv`).
