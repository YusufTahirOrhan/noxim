# Regression with the v19 and v20 options off (experiments_v19.py regress)

References: 3ac1bae build md5 3bc747aed4d383cb87346351fafd48e5; d6f65f8 build md5 96100f7bd0fb8cefd50c8092860874e7. New binary: md5 f72577901551675dfc2767526fd36844 (code with -deft_vn_rr, -deft_lb decision_delay, -deft_lb hop_stats).
Configurations: 84 = the 84-configuration set of v14-v18. Comparison: the whole stats JSON file, byte by byte, against the 3ac1bae build.

* d6f65f8 build: **84 / 84 byte-identical**.
* New binary, options absent: **84 / 84 byte-identical**.
* New binary, `-deft_vn_rr 0 -deft_lb decision_delay 0 -deft_lb hop_stats 0` given: **84 / 84 byte-identical**.

No differences.
