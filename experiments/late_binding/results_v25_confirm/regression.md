# A5: regression before the confirmatory round (experiments_v25.py regress)

Reference: the ce6ab6a build (the last commit of round 24), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 2b58bee06d53c11c4dba50319a7a9530.
Current binary `bin/noxim`: md5 2b58bee06d53c11c4dba50319a7a9530 (the same file as the reference build). The 8d84634 build (round 23, the reference of the v24 regression): md5 b81b5d8b1fefc63276c1e80cffeaa01d.
Configurations: 84 = the 84-configuration set of v14-v24. Comparison: the whole stats JSON file, byte by byte, against the ce6ab6a build.

* 8d84634 build: **84 / 84 byte-identical**.
* `bin/noxim`, options absent: **84 / 84 byte-identical**.
* `bin/noxim`, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0` given: **84 / 84 byte-identical**.

No differences.

Simulator sources against ce6ab6a when this file was written (`git diff --name-only ce6ab6a -- src bin/Makefile`): no difference.
