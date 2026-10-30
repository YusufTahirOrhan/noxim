# Regression with the v15/v16 options off (experiments_v15.py regress)

Old binary: md5 01c7e9d0609bef144b6b762b50aff46c (the v11-v14 binary). New binary: md5 3bc747aed4d383cb87346351fafd48e5 (code with -netrace2, -netrace_compress, -deft_lb ql_bits / ql_frac / ql_range; all off).
Configurations: 84 = the 66-configuration regression set + the six v10 baselines x 2x2/3x3/4x4 (uniform, fault-free, 1.0 x Lsat, seed 7). Comparison: the whole stats JSON file, byte by byte.

**84 / 84 byte-identical.**

No differences.
