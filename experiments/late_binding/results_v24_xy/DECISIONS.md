# v24 decisions: late binding without path adaptivity (XY and a VN-split order on the interposer)

The conservative option is the one that does not favour late binding. The explanations of the review that started this round
are treated as hypotheses; where a measurement of this round disagrees with one, the measurement is what `FINDINGS.md` reports.

## A0: reproduction of the probes
* **Reference binary.** `~/lbbin/noxim_8d84634`: commit 8d84634 exported with `git archive` into a separate tree
  (`~/lbref/8d84634`) and built there with the repository's Makefile. Its md5 (b81b5d8b…) equals that of `bin/noxim` as left by
  round 23, so the two are the same build.
* The ten rows of the prompt's A0 table were run with that binary before any source change (`reproduction.md`, 10 / 10
  identical to the printed digits).
