# Run-time estimate v27, Parts C and E (experiments_v27.py c_timing)

Part C timing runs: the 378 runs of seed 161 at the 2nd, 5th and 9th load (0.5, 1.2 and 2.4 x Lsat) of every (row, size, scenario) cell: 1629 s wall with 12 processes;
0 missing. Part E timing runs: the 144 runs of seed 151 at the 1st and 4th load (0.5 and 2.0 x Lsat) of masks 1 to 4 of every size, the three rows and both traffic
patterns: 589 s wall; 0 missing. Both sets are runs of the designs and are kept; nothing of their results was looked at. No other job of this round ran next to
a set; what else ran on the PC at that time is in `DECISIONS.md`. The estimate is taken as measured (`PREREGISTRATION.md`, addendum A3).

Part C: 11340 runs, estimated **13.6 h**. Part E: 2304 runs, estimated **2.6 h**. Together **16.2 h**.

Rule (pre-registered): above 30 h in total drop, in this order: Part E; `EB_vl64`; `LB_noVLrep`; seeds 166-170.

**Dropped: nothing.** Runs to do: 11340 (Part C) and 2304 (Part E), estimated 16.2 h.

What is dropped here is run after all if it later fits into the 30 h (addendum A3; `restore_v27.py` logs every such decision in `time_rule.md`).
