# v23 LUTs against the LUTs of the earlier rounds (experiments_v23.py lutcheck)

Per size and mask: the `entries` (exit and entry VL per key) of luts/v23/lut_<size>_<mask>.yaml against the file the earlier rounds used for that mask (2x2: luts/lut_rho001.yaml for the drain masks, luts/v5 for the v5 masks, luts/v11 for the v11 masks; 3x3 and 4x4: luts/v5 and luts/v11). identical = every key has the same exit and the same entry VL.

| size | mask | reference file | keys | differing exits | differing entries |
|---|---|---|---|---|---|
| 2x2 | 0x0000 | luts/v5/lut_2x2_rho0.01.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x1111 | luts/v5/lut_2x2_rho0.01.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x9C63 | luts/v5/lut_2x2_rho0.01.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x0007 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x8421 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x7BDE | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x0E70 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x0008 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x1044 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x4080 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x8600 | luts/lut_rho001.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x2818 | luts/v11/lut_2x2_rho0.01_0x2818.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x2824 | luts/v11/lut_2x2_rho0.01_0x2824.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x8228 | luts/v11/lut_2x2_rho0.01_0x8228.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x4282 | luts/v11/lut_2x2_rho0.01_0x4282.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x1212 | luts/v11/lut_2x2_rho0.01_0x1212.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xAC5A | luts/v11/lut_2x2_rho0.01_0xAC5A.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xC653 | luts/v11/lut_2x2_rho0.01_0xC653.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x6A63 | luts/v11/lut_2x2_rho0.01_0x6A63.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xA6A6 | luts/v11/lut_2x2_rho0.01_0xA6A6.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0x5A6C | luts/v11/lut_2x2_rho0.01_0x5A6C.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xDE7D | luts/v11/lut_2x2_rho0.01_0xDE7D.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xDE7E | luts/v11/lut_2x2_rho0.01_0xDE7E.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xBDBD | luts/v11/lut_2x2_rho0.01_0xBDBD.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xEB77 | luts/v11/lut_2x2_rho0.01_0xEB77.yaml | 192 (192 in the reference) | 0 | 0 |
| 2x2 | 0xDEDE | luts/v11/lut_2x2_rho0.01_0xDEDE.yaml | 192 (192 in the reference) | 0 | 0 |
| 3x3 | 0x0 | luts/v5/lut_3x3_rho0.01.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x111111111 | luts/v5/lut_3x3_rho0.01.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x414418228 | luts/v11/lut_3x3_rho0.01_0x414418228.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x184484482 | luts/v11/lut_3x3_rho0.01_0x184484482.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x484124122 | luts/v11/lut_3x3_rho0.01_0x484124122.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x224828121 | luts/v11/lut_3x3_rho0.01_0x224828121.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x422281882 | luts/v11/lut_3x3_rho0.01_0x422281882.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x996553A66 | luts/v11/lut_3x3_rho0.01_0x996553A66.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x9C353C536 | luts/v11/lut_3x3_rho0.01_0x9C353C536.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xC55CAA6CA | luts/v11/lut_3x3_rho0.01_0xC55CAA6CA.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x5AC6AC569 | luts/v11/lut_3x3_rho0.01_0x5AC6AC569.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xC55C3636C | luts/v11/lut_3x3_rho0.01_0xC55C3636C.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xBB7D7D77B | luts/v11/lut_3x3_rho0.01_0xBB7D7D77B.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xBBD7EDEEE | luts/v11/lut_3x3_rho0.01_0xBBD7EDEEE.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0x7EDE7EDEE | luts/v11/lut_3x3_rho0.01_0x7EDE7EDEE.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xBEE77B7D7 | luts/v11/lut_3x3_rho0.01_0xBEE77B7D7.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 3x3 | 0xDB7EEBEED | luts/v11/lut_3x3_rho0.01_0xDB7EEBEED.yaml | 1152 (1152 in the reference) | 0 | 0 |
| 4x4 | 0x0 | luts/v5/lut_4x4_rho0.001.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x1111111111111111 | luts/v5/lut_4x4_rho0.001.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x8214882212828814 | luts/v11/lut_4x4_rho0.001_0x8214882212828814.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x8882482122418442 | luts/v11/lut_4x4_rho0.001_0x8882482122418442.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x8814142144214424 | luts/v11/lut_4x4_rho0.001_0x8814142144214424.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x2144224884144481 | luts/v11/lut_4x4_rho0.001_0x2144224884144481.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x4884441818411281 | luts/v11/lut_4x4_rho0.001_0x4884441818411281.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x9C665369659A555A | luts/v11/lut_4x4_rho0.001_0x9C665369659A555A.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x996A966563965959 | luts/v11/lut_4x4_rho0.001_0x996A966563965959.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x9CA593A6AC6A969C | luts/v11/lut_4x4_rho0.001_0x9CA593A6AC6A969C.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x955359CA63A56C56 | luts/v11/lut_4x4_rho0.001_0x955359CA63A56C56.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0xA53AA5665556566C | luts/v11/lut_4x4_rho0.001_0xA53AA5665556566C.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0xDEB77DEDDBBED7D7 | luts/v11/lut_4x4_rho0.001_0xDEB77DEDDBBED7D7.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x7DD7B77DDEBDDDDD | luts/v11/lut_4x4_rho0.001_0x7DD7B77DDEBDDDDD.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x77E7BBD7EBEE7BDB | luts/v11/lut_4x4_rho0.001_0x77E7BBD7EBEE7BDB.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x7DD7BDB7DD7ED7EB | luts/v11/lut_4x4_rho0.001_0x7DD7BDB7DD7ED7EB.yaml | 3840 (3840 in the reference) | 0 | 0 |
| 4x4 | 0x7E777ED7EBBEE77B | luts/v11/lut_4x4_rho0.001_0x7E777ED7EBBEE77B.yaml | 3840 (3840 in the reference) | 0 | 0 |

**All v23 `entries` identical to the earlier LUTs: True.** If so, DeFT-B can use the v23 files; otherwise DeFT-B keeps the old files.
