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

## 2026-11-25 10:18:29: the limit of 48 h is lifted by the user

Not a decision of the rule. At 09:44 on 25 November the rule was looked at without writing anything (speed 0.989 times the estimate; 16.83 h spent, 27.58 h of the kept
parts still to run; Part F2 about 6.00 h, so 16.83 + 27.58 + 6.00 = 50.41 h, above 48 h: it would have stayed dropped, and Part G behind it). The user was told so and
answered: "Its ok to be above of 48h limit." With that the reason for the two drops is gone: **Part F2 and Part G are taken back** and are run in the order of the
prompt (F1, F2, G). Part G keeps its own limit of 3 h, which belongs to its definition and not to this rule. Nothing else had been dropped. With both parts the
estimate is 16.83 + 27.58 + 6.00 + 3.00 = 53.4 h since the start of the timing runs. No run of F2 or G existed at this moment, and no result of Parts C, D, E1 or F had
been read (`DECISIONS.md`, "The limit of 48 h lifted by the user"). The entries that follow are written by the script at the end of every part as before; with nothing
dropped they have nothing to decide.

## 2026-11-25 18:31:18: the end of C1

Time since the start of the timing runs: 25.61 h (0.47 h are not counted, `DECISIONS.md`). Runs finished in it: B1 5130 of 5130; B2 540 of 540; C1 14580 of 14580; D2 373 of 1800; E1 0 of 1620; C3 192 of 3072; D1 0 of 3240; C2 0 of 2880; F1 0 of 1620 rows runs, 0 tuning runs; by the seconds per run of the timing sets they are 26.45 h, so the speed is
0.968 times the estimate. Still to run of the kept parts: 17.88 h at this speed. Dropped at this moment: nothing.

Nothing to decide: nothing is dropped.

## 2026-11-25 18:54:07: the end of D2

Time since the start of the timing runs: 25.99 h (0.47 h are not counted, `DECISIONS.md`). Runs finished in it: B1 5130 of 5130; B2 540 of 540; C1 14580 of 14580; D2 1800 of 1800; E1 0 of 1620; C3 192 of 3072; D1 0 of 3240; C2 0 of 2880; F1 0 of 1620 rows runs, 0 tuning runs; by the seconds per run of the timing sets they are 26.80 h, so the speed is
0.970 times the estimate. Still to run of the kept parts: 17.58 h at this speed. Dropped at this moment: nothing.

Nothing to decide: nothing is dropped.

