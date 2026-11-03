# Addendum to the v21 pre-registration

Committed after the tuning and before any evaluation run of `DEFT_FAST`. No evaluation result existed when this was written. The tuning's latency scores were known.

## N_fast after re-synthesis with the tuned weights
As pre-registered, the larger N applies and the tuning is not repeated.

| variant | N fixed before tuning (age) | measured with tuned w, beta (age) | N used in F4 (age) |
|---|---|---|---|
| CI_fast | 2 (2) | 2 (2) | 2 (2) |
| CI_fastQL | 3 (2) | 3 (2) | 3 (2) |
| **FULL_fast** | 2 (1) | **3 (2)** | **3 (2)** |
| FULL_fastQL | 3 (2) | 3 (2) | 3 (2) |

**FULL_fast changes.** Its first decision stage on 3x3 chiplet boundary routers went from 0.97-0.99 to 1.02 ns, with the weights the tuning chose. It was tuned at N = 2, age 1, and runs at N = 3, age 2. This does not favour our method. The variant chosen for the primary hypotheses is unchanged: the choice stands as made on the tuning seeds.

## One added secondary row
**FULL_fast at N = 2, age 1, on seeds 81-85 (875 runs),** labelled as missing the timing by 0.02 ns, like CI_fast at N = 1. Reason: both Ns turn on misses smaller than the flow's noise (0.06-0.18 ns, `results_v20_delay/DECISIONS.md`), and F4 would otherwise have no row at the N this variant was tuned for. It enters no primary test, and it runs after CI_fast at N = 1 and before N_fast + 1.

**Runs in total:** 19,600.

## Tuning data
The raw tuning outputs were deleted before a per-run CSV was written, by mistake. `tuning.md` keeps the score, run count and accepted throughput of every configuration. The runs are reproducible from `experiments_v21.py tune`, with the seeds and configurations recorded there.
