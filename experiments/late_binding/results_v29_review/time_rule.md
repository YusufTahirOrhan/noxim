# v29: the time rule after the timing runs (restore_v29.py)

The rule of `PREREGISTRATION.md`: what the 48 h rule dropped is taken back, in the reverse of the drop order, if at the end of a part the time since the
start of the timing runs plus the estimate of what is still to run plus the item, at the speed measured until then, is at most 48 h. Each entry below is
one such moment; it reads the clock and counts finished runs, and opens no result.

## 2026-11-24 22:30:51: the end of B1 (decided afterwards from the log of the chain; nobody ran the script at that moment)

Time since the start of the timing runs: 6.07 h. Runs finished in it: B1 5130 of 5130; B2 0 of 540; C1 432 of 14580; D2 360 of 1800; E1 0 of 1620; C3 192 of 3072; D1 0 of 3240; C2 0 of 2880; F1 0 of 1620 rows runs, 0 tuning runs; by the seconds per run of the timing sets they are 6.08 h, so the speed is
0.998 times the estimate. Still to run of the kept parts: 38.76 h at this speed. Dropped at this moment: Part G, Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation).

* Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation): about 6.05 h; 6.07 + 38.76 + 6.05 = 50.89 h, above 48 h: **stays dropped**.

## 2026-11-24 22:41:46: the end of B2 (decided afterwards, as above)

Time since the start of the timing runs: 6.25 h. Runs finished in it: B1 5130 of 5130; B2 540 of 540; C1 432 of 14580; D2 360 of 1800; E1 0 of 1620; C3 192 of 3072; D1 0 of 3240; C2 0 of 2880; F1 0 of 1620 rows runs, 0 tuning runs; by the seconds per run of the timing sets they are 6.28 h, so the speed is
0.995 times the estimate. Still to run of the kept parts: 38.44 h at this speed. Dropped at this moment: Part G, Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation).

* Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation): about 6.03 h; 6.25 + 38.44 + 6.03 = 50.73 h, above 48 h: **stays dropped**.

