# A0: regression before any change of round 29 (experiments_v29.py regress 12 before)

Reference: the e7569b1 build (the last commit of round 28), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 dbeabbc7557f3db9be4105ddda8fe7a6.
Binary under test `bin/noxim`: md5 dbeabbc7557f3db9be4105ddda8fe7a6 (the same file as the reference build). The b164e9e build (round 27, the reference of the v28 regression): md5 9c32b6ee8f1038c43ea74ad683db3310.
Configurations: 84 = the 84-configuration set of v14-v28. Comparison: the whole stats JSON file, byte by byte, against the e7569b1 build.

* b164e9e build: **84 / 84 byte-identical**.
* `bin/noxim`, options absent: **84 / 84 byte-identical**.
* `bin/noxim`, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0 -deft_lb oracle_scope vl -deft_lb oracle_period 0 -deft_lb entry_commit off -deft_lb up_report 1 -deft_lb entry_stats 0 -deft_lb oracle_bias 0 -deft_lb oracle_pending 0 -deft_lb pending_check 0 -deft_lb tie_stream 0` given: **84 / 84 byte-identical**.

No differences.

Simulator sources against e7569b1 when this file was written (`git diff --name-only e7569b1 -- src bin/Makefile`): no difference.
