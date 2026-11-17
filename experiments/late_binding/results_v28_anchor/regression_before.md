# A0: regression before any change of round 28 (experiments_v28.py regress 12 before)

Reference: the b164e9e build (the last commit of round 27), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 9c32b6ee8f1038c43ea74ad683db3310.
Binary under test `bin/noxim`: md5 9c32b6ee8f1038c43ea74ad683db3310 (the same file as the reference build). The d641861 build (round 26, the reference of the v27 regression): md5 2b58bee06d53c11c4dba50319a7a9530.
Configurations: 84 = the 84-configuration set of v14-v27. Comparison: the whole stats JSON file, byte by byte, against the b164e9e build.

* d641861 build: **84 / 84 byte-identical**.
* `bin/noxim`, options absent: **84 / 84 byte-identical**.
* `bin/noxim`, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0 -deft_lb oracle_scope vl -deft_lb oracle_period 0 -deft_lb entry_commit off -deft_lb up_report 1 -deft_lb entry_stats 0` given: **84 / 84 byte-identical**.

No differences.

Simulator sources against b164e9e when this file was written (`git diff --name-only b164e9e -- src bin/Makefile`): changed: src/DeftLateBinding.cpp, src/DeftLateBinding.h, src/Router.cpp.
