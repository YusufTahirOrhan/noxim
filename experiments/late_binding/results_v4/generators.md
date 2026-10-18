# Generators on the parametric instance (v4 step 3)

## Default output unchanged (byte-identical)
- LUT, uniform demand, 11 drain masks: identical to luts/lut_rho001.yaml.
- Traffic-matched LUTs (localized, hotspot, chipperm, movinghot; 11 masks): identical to luts/lut_rho001_tm_*.yaml (final generator code).
- Traffic tables: all 401 default files (0.001 and 0.0005 grids, all-pairs burst) identical through the parametric code path.

## MILP solver (larger destination-entry problems)
- Optimisations compared: 264 (11 masks x 4 chiplets x source/destination x 3 demand profiles).
- Largest |objective(DP) - objective(MILP)|: 0.000e+00.
- Identical assignments: 126 of 264 (the rest are equally good alternatives).

## Larger instances
| size | LUT (masks 0x0 and north per chiplet) | traffic-matched LUTs: selected-VL lines differing from the uniform LUT | traffic tables |
|---|---|---|---|
| 3x3 (144 + 144 routers, 36 VLs) | luts/lut_3x3_rho001.yaml, 1 s | localized 0, hotspot 710, chipperm 998, movinghot 0 (of 4608) | traffic_3x3/: 240 tables (rates up to 0.024) + all-pairs burst (20592 packets) |
| 4x4 (256 + 256 routers, 64 VLs) | luts/lut_4x4_rho001.yaml, 2 s | localized 0, hotspot 1732, chipperm 2634, movinghot 0 (of 15360) | traffic_4x4/: 240 tables + all-pairs burst (65280 packets) |

As on 2x2, localized and movinghot produce exactly the uniform LUT: the LUT objective is per chiplet,
and their time-averaged demand is the same for every router within each chiplet problem.

## Checksums
```
03ea938476b02897e228e38037fbcfdd93ba6d76a8a1a8924811a5446600dbfc  luts/lut_3x3_rho001.yaml
c5a821bbab9175bf0a0bc27581c586507e525277a2b3a2378f961a7e962dec46  luts/lut_3x3_rho001_tm_chipperm.yaml
174f3b8f6feba7b7b38fa9acfcb4d44229d15a4580ae7a0ef8205f0cd19914a2  luts/lut_3x3_rho001_tm_hotspot.yaml
0e47f3d54b68a02af9aa3c96b85bf5afaaf6a69b0bf0a55d0267f20870f83535  luts/lut_3x3_rho001_tm_localized.yaml
b7292e28a843e3e9e1e76a4bbf497f3853f2a204ccb2850430532d0c70754d04  luts/lut_3x3_rho001_tm_movinghot.yaml
ae003848865419611ffc0bef723688df225701b008816a30ceff2328ce0e547b  luts/lut_4x4_rho001.yaml
4dc72a983166329280f187caccdf111d03c15095c6df00c975ed6092c3769358  luts/lut_4x4_rho001_tm_chipperm.yaml
b87bdfcdbb92d3e9b726a02bbcc339f8ecf1a8bf90b9d58dd8ef9f1fb76d27db  luts/lut_4x4_rho001_tm_hotspot.yaml
fea38b8e8805ff417f8492d039ebe14a22dbe2a311b2141902e7cd3f0b894e21  luts/lut_4x4_rho001_tm_localized.yaml
5b75db448aed2ddee7e7fbe783ec57e45a9f5bb762da9ccc2d93a0e9f399b0dd  luts/lut_4x4_rho001_tm_movinghot.yaml
```
