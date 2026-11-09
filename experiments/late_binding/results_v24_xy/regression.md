# Regression with the v24 options off (experiments_v24.py regress)

Reference: the 8d84634 build (round 23), md5 b81b5d8b1fefc63276c1e80cffeaa01d. New binary: md5 2b58bee06d53c11c4dba50319a7a9530 (A1: `-deft_lb ipos_tm YX | O1`; B1: `-deft_lb lut_bias`; B2: `-deft_lb lookahead_fallback`; B3: `-deft_lb busy_state`).
Configurations: 84 = the 84-configuration set of v14-v23. Comparison: the whole stats JSON file, byte by byte, against the reference build.

* New binary, options absent: **84 / 84 byte-identical**.
* New binary, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0 -deft_lb lut_bias 0 -deft_lb lookahead_fallback 0 -deft_lb busy_state 0` given: **84 / 84 byte-identical**.

No differences.
