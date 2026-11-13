# A0: regression before round 26 (experiments_v26.py regress)

Reference: the ee0e247 build (the last commit of round 25), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 2b58bee06d53c11c4dba50319a7a9530.
Current binary `bin/noxim`: md5 2b58bee06d53c11c4dba50319a7a9530 (the same file as the reference build). The ce6ab6a build (round 24, the reference of the v25 regression): md5 2b58bee06d53c11c4dba50319a7a9530.
Configurations: 84 = the 84-configuration set of v14-v25. Comparison: the whole stats JSON file, byte by byte, against the ee0e247 build.

* ce6ab6a build: **84 / 84 byte-identical**.
* `bin/noxim`, options absent: **84 / 84 byte-identical**.
* `bin/noxim`, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0` given: **84 / 84 byte-identical**.

No differences.

Simulator sources against ee0e247 when this file was written (`git diff --name-only ee0e247 -- src bin/Makefile`): no difference.
