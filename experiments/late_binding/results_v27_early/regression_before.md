# A0: regression before any change of round 27 (experiments_v27.py regress 12 before)

Reference: the d641861 build (the last commit of round 26), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 2b58bee06d53c11c4dba50319a7a9530.
Binary under test `bin/noxim`: md5 2b58bee06d53c11c4dba50319a7a9530 (the same file as the reference build). The ee0e247 build (round 25, the reference of the v26 regression): md5 2b58bee06d53c11c4dba50319a7a9530.
Configurations: 84 = the 84-configuration set of v14-v26. Comparison: the whole stats JSON file, byte by byte, against the d641861 build.

* ee0e247 build: **84 / 84 byte-identical**.
* `bin/noxim`, options absent: **84 / 84 byte-identical**.
* `bin/noxim`, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0` given: **84 / 84 byte-identical**.

No differences.

Simulator sources against d641861 when this file was written (`git diff --name-only d641861 -- src bin/Makefile`): no difference.
