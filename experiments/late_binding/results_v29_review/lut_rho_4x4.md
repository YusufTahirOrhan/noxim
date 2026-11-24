# DeFT's tables on 4x4 with rho = 0.001 and with rho = 0.01 (lut_rho_v29.py; for ARTIFACT.md)

Every round uses rho = 0.001 on 4x4 and rho = 0.01 on 2x2 and 3x3 (`results_v5/tuning_choice.json`). For each mask of the paper on 4x4 the table was generated
with both values (`other/deft_vl_lut_generator.py --entry-model both`) and the selected VLs were compared entry by entry. Exit: per source router and
destination chiplet (3840 entries; every row with a table-driven exit VL). Entry by destination router (256 entries): DeFT_P. Entry by source router and
destination chiplet (3840 entries): DeFT_B.

The table generated here with rho = 0.001 has the selections of the table in `luts/v23` that the runs used: 66 of 66 masks.

**DeFT_P (exit and entry by destination): the two values give different tables for 0 of the 66 masks; DeFT_B (exit and entry by source): for 66.**

| mask | | exit entries that differ | entry (by destination) entries that differ | entry (by source) entries that differ |
|---|---|---|---|---|
| fault-free | 0x0 | 0 | 0 | 1465 |
| one faulty VL per chiplet (round 25) | 0x1111111111111111 | 0 | 0 | 1051 |
| round 26, rate 1/16, mask 1 | 0x0000040080080400 | 0 | 0 | 1346 |
| round 26, rate 1/16, mask 2 | 0x8000900000000800 | 0 | 0 | 1297 |
| round 26, rate 1/16, mask 3 | 0x0000050200200000 | 0 | 0 | 1401 |
| round 26, rate 1/16, mask 4 | 0x0020002001000002 | 0 | 0 | 1428 |
| round 26, rate 1/16, mask 5 | 0x0420000004000200 | 0 | 0 | 1368 |
| round 26, rate 1/16, mask 6 | 0x0188800000000000 | 0 | 0 | 1363 |
| round 26, rate 1/16, mask 7 | 0x1000008008800000 | 0 | 0 | 1487 |
| round 26, rate 1/16, mask 8 | 0x0808002000000004 | 0 | 0 | 1418 |
| round 26, rate 1/16, mask 9 | 0x0000060000100800 | 0 | 0 | 1354 |
| round 26, rate 1/16, mask 10 | 0x4100001010000000 | 0 | 0 | 1415 |
| round 26, rate 1/16, mask 11 | 0x4040004000008000 | 0 | 0 | 1450 |
| round 26, rate 1/16, mask 12 | 0x2104000000000800 | 0 | 0 | 1392 |
| round 26, rate 1/16, mask 13 | 0x0002000800000600 | 0 | 0 | 1349 |
| round 26, rate 1/16, mask 14 | 0x0000230000000001 | 0 | 0 | 1405 |
| round 26, rate 1/16, mask 15 | 0x4000080008000100 | 0 | 0 | 1452 |
| round 26, rate 1/16, mask 16 | 0x0000000B80000000 | 0 | 0 | 1392 |
| round 26, rate 2/16, mask 1 | 0x0170041002000020 | 0 | 0 | 1246 |
| round 26, rate 2/16, mask 2 | 0x802900002A000200 | 0 | 0 | 1269 |
| round 26, rate 2/16, mask 3 | 0x4400004082102040 | 0 | 0 | 1401 |
| round 26, rate 2/16, mask 4 | 0x0220002000406005 | 0 | 0 | 1244 |
| round 26, rate 2/16, mask 5 | 0x08010D0080010040 | 0 | 0 | 1295 |
| round 26, rate 2/16, mask 6 | 0x4628010000001001 | 0 | 0 | 1210 |
| round 26, rate 2/16, mask 7 | 0x22001000100088C0 | 0 | 0 | 1217 |
| round 26, rate 2/16, mask 8 | 0x0011110220800001 | 0 | 0 | 1311 |
| round 26, rate 2/16, mask 9 | 0x4284002840000002 | 0 | 0 | 1269 |
| round 26, rate 2/16, mask 10 | 0x4404000140040012 | 0 | 0 | 1270 |
| round 26, rate 2/16, mask 11 | 0x0208008010112010 | 0 | 0 | 1350 |
| round 26, rate 2/16, mask 12 | 0x0004C08050008080 | 0 | 0 | 1258 |
| round 26, rate 2/16, mask 13 | 0x0011C00240800010 | 0 | 0 | 1298 |
| round 26, rate 2/16, mask 14 | 0x2283000008000600 | 0 | 0 | 1198 |
| round 26, rate 2/16, mask 15 | 0x1008000800207001 | 0 | 0 | 1259 |
| round 26, rate 2/16, mask 16 | 0x0400002300082208 | 0 | 0 | 1224 |
| round 26, rate 4/16, mask 1 | 0x26E020A00402D804 | 0 | 0 | 986 |
| round 26, rate 4/16, mask 2 | 0x0C90902035808310 | 0 | 0 | 1001 |
| round 26, rate 4/16, mask 3 | 0x50888142420C0215 | 0 | 0 | 1023 |
| round 26, rate 4/16, mask 4 | 0x854310E410010260 | 0 | 0 | 952 |
| round 26, rate 4/16, mask 5 | 0x420830A482104941 | 0 | 0 | 1115 |
| round 26, rate 4/16, mask 6 | 0x1018211222234510 | 0 | 0 | 932 |
| round 26, rate 4/16, mask 7 | 0x01E8E4860080D000 | 0 | 0 | 1043 |
| round 26, rate 4/16, mask 8 | 0x0330100471A81014 | 0 | 0 | 1044 |
| round 26, rate 4/16, mask 9 | 0x181028A305942001 | 0 | 0 | 1039 |
| round 26, rate 4/16, mask 10 | 0x480410412286B110 | 0 | 0 | 1088 |
| round 26, rate 4/16, mask 11 | 0xA880208604252046 | 0 | 0 | 958 |
| round 26, rate 4/16, mask 12 | 0x084180C9E0485020 | 0 | 0 | 1079 |
| round 26, rate 4/16, mask 13 | 0x50202130C2000D85 | 0 | 0 | 1031 |
| round 26, rate 4/16, mask 14 | 0x20040162C6001B05 | 0 | 0 | 1016 |
| round 26, rate 4/16, mask 15 | 0x01488780A1072200 | 0 | 0 | 1088 |
| round 26, rate 4/16, mask 16 | 0x62844801442E0300 | 0 | 0 | 864 |
| round 26, rate 8/16, mask 1 | 0x4ECA9A866EBCD116 | 0 | 0 | 367 |
| round 26, rate 8/16, mask 2 | 0xD40E6A5CC5B8CAAE | 0 | 0 | 512 |
| round 26, rate 8/16, mask 3 | 0x770EA9AD0636C4CE | 0 | 0 | 313 |
| round 26, rate 8/16, mask 4 | 0xA49AAAC08B8B779D | 0 | 0 | 654 |
| round 26, rate 8/16, mask 5 | 0x8BA688E6CC49B59D | 0 | 0 | 398 |
| round 26, rate 8/16, mask 6 | 0xBA5525C453725DC9 | 0 | 0 | 608 |
| round 26, rate 8/16, mask 7 | 0x790D392DE78D09AA | 0 | 0 | 540 |
| round 26, rate 8/16, mask 8 | 0xA9545076EDE285BC | 0 | 0 | 621 |
| round 26, rate 8/16, mask 9 | 0x93713754A7D615A1 | 0 | 0 | 643 |
| round 26, rate 8/16, mask 10 | 0x29EA885D5E4E2DA6 | 0 | 0 | 579 |
| round 26, rate 8/16, mask 11 | 0xC3C5A95D6D90C137 | 0 | 0 | 437 |
| round 26, rate 8/16, mask 12 | 0x5AC1ED5E94282D9B | 0 | 0 | 528 |
| round 26, rate 8/16, mask 13 | 0xE3CAD6D097372624 | 0 | 0 | 510 |
| round 26, rate 8/16, mask 14 | 0x6EDC8AE4E8D0B14D | 0 | 0 | 431 |
| round 26, rate 8/16, mask 15 | 0x726A7CC0AA6CCE65 | 0 | 0 | 357 |
| round 26, rate 8/16, mask 16 | 0x17C7030ADC13EC7B | 0 | 0 | 361 |
