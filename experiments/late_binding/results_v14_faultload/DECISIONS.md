# Decisions taken without the author (v14, Part F)

1. **Pooling for the load rule:** the DeFT(rho*) mean latency is averaged over the 5 masks and both v11 seeds (51-52) per
   load point; the zero-load latency is the pooled latency at the lowest load point. For every (size, k, pattern) the
   pooled latency rises monotonically, so the highest unsaturated point is also the end of an unsaturated prefix.
   Every (size, k, pattern) has at least one unsaturated point; the fallback (lowest point) was not needed.
2. **One load per (size, k, pattern):** the test load can differ between uniform and hotspot. Each unit's value is the
   mean of the two patterns' log ratios, each at its own test load.
3. **Exploratory v11 effects:** reported at the chosen loads (seeds 51-52, unadjusted) and labelled exploratory; they
   are not part of the confirmatory test.
4. **Binary:** unchanged since v11/v13 (md5 01c7e9d0); Part F needs no C++ change, so no new regression run is needed.
5. **LUTs:** the v11 per-mask LUTs (`luts/v11/`), regenerated if missing.
6. **"Saturated" flag at the lowest loads:** the report counts a run as saturated when accepted < 95 % of offered. At
   2x2 k = 3 (test load 0.2 x Lsat), 5-12 of 50 runs per method carry the flag although the mean latency stays at the
   zero-load level (about 29 cycles). The accepted/offered ratio there is 0.92-1.03 because so few packets are injected
   that sampling noise alone moves it below 0.95. The flag is reported as computed, the runs are not excluded (the
   pre-registration has no exclusion on it), and FINDINGS.md explains it.
7. **Raw outputs:** deleted after `eval_runs.csv` (3600 rows) was written.
