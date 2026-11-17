# Run-time estimate v28, Parts C, D and E (experiments_v28.py c_timing)

Timing runs (runs of the designs, kept; nothing of their results was looked at), 12 processes, one set after the other, no other job of this round next
to a set; what else ran on the PC at that time is in `DECISIONS.md`. The estimate is taken as measured (`PREREGISTRATION.md`).

| part | timing runs | wall | per run | runs of the design | estimate |
|---|---|---|---|---|---|
| C | 378 (0 missing) | 1612 s | 4.26 s | 11340 | 13.4 h |
| D | 432 (0 missing) | 1753 s | 4.06 s | 6912 | 7.8 h |
| E | 192 (0 missing) | 786 s | 4.09 s | 3072 | 3.5 h |

Together **24.7 h**. Rule (pre-registered): above 30 h in total drop, in this order: the anchor rows in Part D; `EB_best64` in Part D; rates 1/16 and 2/16 of Part E; seeds 176-180 of `EB_best64` in Part C; rate 1/16 of Part D.

**Dropped: nothing.** Runs to do: 11340 (C), 6912 (D), 3072 (E), estimated 24.7 h.
