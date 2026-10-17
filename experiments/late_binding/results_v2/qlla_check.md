# ql_lookahead checks (check_qlla.py)

Local weights for (a)/(c): w = 2.0, busy = 4.0; ql_key = 1, eps = 0.

## (a) QL-LA with alpha = 0 vs DEFT_HEUR with lookahead (summary block + deft_lb delays, VL counts, decisions)

- IDENTICAL CI__hotspot__0x1111__s1: latency 73.235 vs 73.235; ql_updates 47350, ql_lookahead 1
- IDENTICAL CI__hotspot__0x1111__s2: latency 105.759 vs 105.759; ql_updates 48585, ql_lookahead 1
- IDENTICAL CI__hotspot__0x1111__s3: latency 142.690 vs 142.690; ql_updates 48338, ql_lookahead 1
- IDENTICAL CI__uniform__0x0000__s1: latency 39.149 vs 39.149; ql_updates 56832, ql_lookahead 1
- IDENTICAL CI__uniform__0x0000__s2: latency 36.191 vs 36.191; ql_updates 55196, ql_lookahead 1
- IDENTICAL CI__uniform__0x0000__s3: latency 39.051 vs 39.051; ql_updates 57487, ql_lookahead 1
- IDENTICAL FULL__hotspot__0x1111__s1: latency 108.185 vs 108.185; ql_updates 50460, ql_lookahead 1
- IDENTICAL FULL__hotspot__0x1111__s2: latency 64.294 vs 64.294; ql_updates 50602, ql_lookahead 1
- IDENTICAL FULL__hotspot__0x1111__s3: latency 126.481 vs 126.481; ql_updates 52100, ql_lookahead 1
- IDENTICAL FULL__uniform__0x0000__s1: latency 35.744 vs 35.744; ql_updates 58717, ql_lookahead 1
- IDENTICAL FULL__uniform__0x0000__s2: latency 34.925 vs 34.925; ql_updates 58118, ql_lookahead 1
- IDENTICAL FULL__uniform__0x0000__s3: latency 36.103 vs 36.103; ql_updates 60154, ql_lookahead 1

FULL: 6/6 identical (required check); CI: 6/6 identical.

## (b) existing variants, binary before vs after the change

- IDENTICAL A_oracle__hotspot__0x1111__s1
- IDENTICAL A_oracle__hotspot__0x1111__s2
- IDENTICAL A_oracle__uniform__0x0000__s1
- IDENTICAL A_oracle__uniform__0x0000__s2
- IDENTICAL CI_ql__hotspot__0x1111__s1
- IDENTICAL CI_ql__hotspot__0x1111__s2
- IDENTICAL CI_ql__uniform__0x0000__s1
- IDENTICAL CI_ql__uniform__0x0000__s2
- IDENTICAL DeFT__hotspot__0x1111__s1
- IDENTICAL DeFT__hotspot__0x1111__s2
- IDENTICAL DeFT__uniform__0x0000__s1
- IDENTICAL DeFT__uniform__0x0000__s2
- IDENTICAL FULL_heurLA__hotspot__0x1111__s1
- IDENTICAL FULL_heurLA__hotspot__0x1111__s2
- IDENTICAL FULL_heurLA__uniform__0x0000__s1
- IDENTICAL FULL_heurLA__uniform__0x0000__s2
- IDENTICAL FULL_heur__hotspot__0x1111__s1
- IDENTICAL FULL_heur__hotspot__0x1111__s2
- IDENTICAL FULL_heur__uniform__0x0000__s1
- IDENTICAL FULL_heur__uniform__0x0000__s2
- IDENTICAL FULL_ql__hotspot__0x1111__s1
- IDENTICAL FULL_ql__hotspot__0x1111__s2
- IDENTICAL FULL_ql__uniform__0x0000__s1
- IDENTICAL FULL_ql__uniform__0x0000__s2

24/24 identical.

## (c) QL-LA with alpha = 0.2 learns

- CI__hotspot__0x1111__s1: ql_updates 48224, latency 64.446 (alpha 0: 73.235)
- CI__hotspot__0x1111__s2: ql_updates 48625, latency 98.623 (alpha 0: 105.759)
- CI__hotspot__0x1111__s3: ql_updates 48056, latency 85.991 (alpha 0: 142.690)
- CI__uniform__0x0000__s1: ql_updates 54269, latency 35.174 (alpha 0: 39.149)
- CI__uniform__0x0000__s2: ql_updates 55364, latency 36.970 (alpha 0: 36.191)
- CI__uniform__0x0000__s3: ql_updates 55778, latency 38.281 (alpha 0: 39.051)
- FULL__hotspot__0x1111__s1: ql_updates 52609, latency 93.882 (alpha 0: 108.185)
- FULL__hotspot__0x1111__s2: ql_updates 54357, latency 160.609 (alpha 0: 64.294)
- FULL__hotspot__0x1111__s3: ql_updates 54560, latency 205.420 (alpha 0: 126.481)
- FULL__uniform__0x0000__s1: ql_updates 62148, latency 35.735 (alpha 0: 35.744)
- FULL__uniform__0x0000__s2: ql_updates 61320, latency 34.420 (alpha 0: 34.925)
- FULL__uniform__0x0000__s3: ql_updates 61619, latency 34.941 (alpha 0: 36.103)
