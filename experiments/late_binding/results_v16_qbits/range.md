# Residual range and fixed-point format (v16 H1)

CI_qlLA_G and FULL_qlLA_G (v10 parameters), every size, uniform and hotspot at 1.0 and 1.6 x Lsat, seed 1001, `-deft_lb ql_range 1` (float residuals; min / max of the stored residual R over all updates of the run).

| run | R min | R max | updates |
|---|---|---|---|
| range__CI_qlLA_G__2x2-uniform__0x0000__0.0110__s1001 | -3.827 | 4.256 | 60495 |
| range__CI_qlLA_G__2x2-uniform__0x0000__0.0175__s1001 | -2.144 | 10.73 | 78815 |
| range__CI_qlLA_G__2x2-hotspot__0x0000__0.0075__s1001 | -4.061 | 4.628 | 39894 |
| range__CI_qlLA_G__2x2-hotspot__0x0000__0.0120__s1001 | -1.759 | 10.16 | 49328 |
| range__FULL_qlLA_G__2x2-uniform__0x0000__0.0110__s1001 | -2.043 | 1.631 | 61362 |
| range__FULL_qlLA_G__2x2-uniform__0x0000__0.0175__s1001 | -0.5926 | 8.835 | 78911 |
| range__FULL_qlLA_G__2x2-hotspot__0x0000__0.0075__s1001 | -2.248 | 2.434 | 40079 |
| range__FULL_qlLA_G__2x2-hotspot__0x0000__0.0120__s1001 | -0.4655 | 6.452 | 47087 |
| range__CI_qlLA_G__3x3-uniform__0x0__0.0085__s1001 | -5.833 | 5.912 | 140336 |
| range__CI_qlLA_G__3x3-uniform__0x0__0.0135__s1001 | -1.99 | 23.84 | 176431 |
| range__CI_qlLA_G__3x3-hotspot__0x0__0.0035__s1001 | -6.699 | 8.094 | 55926 |
| range__CI_qlLA_G__3x3-hotspot__0x0__0.0056__s1001 | -4.486 | 33.58 | 70094 |
| range__FULL_qlLA_G__3x3-uniform__0x0__0.0085__s1001 | -2.698 | 3.155 | 143065 |
| range__FULL_qlLA_G__3x3-uniform__0x0__0.0135__s1001 | -0.5588 | 10.92 | 166076 |
| range__FULL_qlLA_G__3x3-hotspot__0x0__0.0035__s1001 | -2.44 | 3.456 | 56070 |
| range__FULL_qlLA_G__3x3-hotspot__0x0__0.0056__s1001 | -1.583 | 10.76 | 70601 |
| range__CI_qlLA_G__4x4-uniform__0x0__0.0065__s1001 | -5.497 | 7.97 | 240262 |
| range__CI_qlLA_G__4x4-uniform__0x0__0.0105__s1001 | -3.056 | 23.08 | 277063 |
| range__CI_qlLA_G__4x4-hotspot__0x0__0.0021__s1001 | -7.622 | 16.68 | 77263 |
| range__CI_qlLA_G__4x4-hotspot__0x0__0.0034__s1001 | -4.603 | 49.31 | 90938 |
| range__FULL_qlLA_G__4x4-uniform__0x0__0.0065__s1001 | -3.833 | 2.471 | 240053 |
| range__FULL_qlLA_G__4x4-uniform__0x0__0.0105__s1001 | -1.742 | 9.269 | 253066 |
| range__FULL_qlLA_G__4x4-hotspot__0x0__0.0021__s1001 | -4.944 | 6.501 | 75383 |
| range__FULL_qlLA_G__4x4-hotspot__0x0__0.0034__s1001 | -2.395 | 15.87 | 90413 |

Integer bits I = ceil(log2(2 x max |R|)) per size (factor-2 margin), sign bit separate; F = B - 1 - I.

| size | max abs R | I | F for B = 16 / 12 / 8 |
|---|---|---|---|
| 2x2 | 10.73 | 5 | 10 / 6 / 2 |
| 3x3 | 33.58 | 7 | 8 / 4 / 0 |
| 4x4 | 49.31 | 7 | 8 / 4 / 0 |
