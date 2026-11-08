# Regression with the v23 options off (experiments_v23.py regress)

References: 780fa6b build md5 a82a1590224f4c2ed253c256c0285792; 3ac1bae build md5 3bc747aed4d383cb87346351fafd48e5. New binary: md5 b81b5d8b1fefc63276c1e80cffeaa01d (A1: -deft_up_keep, -deft_rr_fallback, -deft_lut_entry, -traffic_rng; B1-B4: -pipe_all, -deft_lb lookahead_route, -vc_per_hop, -deft_lb hysteresis).
Configurations: 84 = the 84-configuration set of v14-v21. Comparison: the whole stats JSON file, byte by byte, against the 780fa6b build.

* 3ac1bae build: **84 / 84 byte-identical**.
* New binary, options absent: **84 / 84 byte-identical**.
* New binary, `-deft_up_keep 0 -deft_rr_fallback 0 -deft_lut_entry src -traffic_rng 0 -pipe_all 0 -vc_per_hop 0 -deft_lb lookahead_route 0 -deft_lb hysteresis 0` given: **84 / 84 byte-identical**.

No differences.
