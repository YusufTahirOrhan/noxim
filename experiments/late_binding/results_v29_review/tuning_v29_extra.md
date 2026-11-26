# v29 Part F2: T of `EB_best256` on 2x2 beyond the cap of the rule (extra_v29_age.py tune)

A check added after the tuning (`DECISIONS.md`). The rule of `tuning_v29.md` doubles T up to 128 at most; on 2x2 it chose T = 128 for `EB_best256`, the largest
value it allows, with the score still rising. The table adds the values beyond the cap on the same 40 tuning cells (five scenarios, four loads, seeds 101 and
102; DeFT-P from `tune_first_runs.csv`). **The pre-registered row stays `EB_best256` with T = 128.** Scores in natural-log units against DeFT-P; T = infinity is
DeFT_P (score 0).

| T (`oracle_bias` = 0.5 x T) | score | THR | LAT1.0 | LAT0.5 | uniform | hotspot | chipperm | chiptrans | uniform+f | note |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | -2.3421 | -17.6 % | +488.9 % | +45.6 % | -3.330 | -0.052 | -3.298 | -2.690 | -2.340 |  |
| 2 | -2.2681 | -17.0 % | +479.6 % | +38.3 % | -3.268 | +0.000 | -3.078 | -2.695 | -2.298 |  |
| 4 | -2.1705 | -17.0 % | +442.8 % | +34.0 % | -3.177 | +0.221 | -3.094 | -2.518 | -2.285 |  |
| 8 | -2.0424 | -16.3 % | +419.1 % | +24.3 % | -3.060 | +0.362 | -2.891 | -2.475 | -2.148 |  |
| 16 | -1.8063 | -15.6 % | +372.4 % | +8.8 % | -2.828 | +0.561 | -2.659 | -2.206 | -1.900 |  |
| 32 | -1.4549 | -12.9 % | +272.5 % | +0.1 % | -2.352 | +0.742 | -2.221 | -1.867 | -1.577 |  |
| 64 | -0.1918 | -2.3 % | +18.4 % | -0.1 % | -0.132 | +0.762 | -0.680 | -0.771 | -0.138 |  |
| 128 | 0.1047 | +3.7 % | -6.5 % | -0.1 % | +0.013 | +0.479 | -0.001 | -0.017 | +0.049 | **`EB_best256`** (the choice of the rule); the largest score |
| 256 | 0.0102 | +0.1 % | -0.8 % | -0.1 % | +0.018 | +0.042 | +0.005 | -0.017 | +0.003 | beyond the cap |
| 512 | 0.0059 | -0.3 % | -0.8 % | -0.1 % | +0.018 | +0.020 | +0.005 | -0.017 | +0.003 | beyond the cap |

Runs of this check: 80 (`tune_age_extra_runs.csv`); dead-end events 0; hops that offer more than one output after the commit 0.

No T beyond the cap scores higher than T = 128: the cap did not bind the choice, and no extra row is run.

