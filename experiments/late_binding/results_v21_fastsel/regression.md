# Regression with the v21 options off (experiments_v21.py regress)

References: 3ac1bae build md5 3bc747aed4d383cb87346351fafd48e5; K5 build md5 f72577901551675dfc2767526fd36844. New binary: md5 a82a1590224f4c2ed253c256c0285792.
Configurations: 84 = the 84-configuration set of v14-v20. Comparison: the whole stats JSON file, byte by byte, against the 3ac1bae build.

* K5 build: **84 / 84 byte-identical**.
* New binary, options absent: **84 / 84 byte-identical**.
* New binary, `-deft_lb fast_ql 0` given: **84 / 84 byte-identical**.

No differences.
