# A2: unit checks of the new options (experiments_v28.py a2_units)

Seed 101, pipe_all 2, `-traffic_rng 1`, uniform traffic at 1.0 x Lsat of DeFT_P, fault-free.

## 1. The pending counters against a scan of the network

With `-deft_lb pending_check 3000`, at the first three cycles that are multiples of 3000, the sum of the pending counters is compared with a scan of the
network that does not use them: every head of an inter-chiplet packet that has not moved Up (in an input buffer of a router of its source chiplet or
of the interposer, or on the link into such a router and not yet taken), counted with the length of its packet, per entry VL. *VL mismatches*: the
(cycle, VL) pairs in which the counter of a VL is not the scan of that VL (must be 0).

| size | row | cycles | counters (sum over the VLs) | scan | VL mismatches | equal |
|---|---|---|---|---|---|---|
| 2x2 | `EBf_route_P1_B1_T4` | [3000, 6000, 9000] | [368, 224, 296] | [368, 224, 296] | 0 | yes |
| 2x2 | `EBf_vl_P1_B1_T4` | [3000, 6000, 9000] | [392, 248, 304] | [392, 248, 304] | 0 | yes |
| 2x2 | `EBf64_route_P1_B1_T4` | [3000, 6000, 9000] | [648, 408, 504] | [648, 408, 504] | 0 | yes |
| 2x2 | `EBf64_vl_P1_B1_T4` | [3000, 6000, 9000] | [656, 528, 528] | [656, 528, 528] | 0 | yes |
| 3x3 | `EBf_route_P1_B1_T4` | [3000, 6000, 9000] | [952, 800, 920] | [952, 800, 920] | 0 | yes |
| 3x3 | `EBf_vl_P1_B1_T4` | [3000, 6000, 9000] | [992, 744, 904] | [992, 744, 904] | 0 | yes |
| 3x3 | `EBf64_route_P1_B1_T4` | [3000, 6000, 9000] | [1552, 1296, 1400] | [1552, 1296, 1400] | 0 | yes |
| 3x3 | `EBf64_vl_P1_B1_T4` | [3000, 6000, 9000] | [1512, 1248, 1616] | [1512, 1248, 1616] | 0 | yes |
| 4x4 | `EBf_route_P1_B1_T4` | [3000, 6000, 9000] | [1376, 1328, 1504] | [1376, 1328, 1504] | 0 | yes |
| 4x4 | `EBf_vl_P1_B1_T4` | [3000, 6000, 9000] | [1232, 1328, 1496] | [1232, 1328, 1496] | 0 | yes |
| 4x4 | `EBf64_route_P1_B1_T4` | [3000, 6000, 9000] | [1760, 1856, 1944] | [1760, 1856, 1944] | 0 | yes |
| 4x4 | `EBf64_vl_P1_B1_T4` | [3000, 6000, 9000] | [1888, 2144, 2216] | [1888, 2144, 2216] | 0 | yes |

**12 / 12 runs equal** (and the counters are positive at every check: the network holds bound packets).

## 2. `pending_check` reads only

The same runs without the option. Compared: the whole `summary` block and every field of `deft_lb` except those of the check.

| size | row | THR without / with | LAT without / with | identical |
|---|---|---|---|---|
| 2x2 | `EBf_route_P1_B1_T4` | 0.104354 / 0.104354 | 65.0779 / 65.0779 | yes |
| 2x2 | `EBf_vl_P1_B1_T4` | 0.104398 / 0.104398 | 64.4990 / 64.4990 | yes |
| 2x2 | `EBf64_route_P1_B1_T4` | 0.103965 / 0.103965 | 133.8810 / 133.8810 | yes |
| 2x2 | `EBf64_vl_P1_B1_T4` | 0.103963 / 0.103963 | 147.7445 / 147.7445 | yes |
| 3x3 | `EBf_route_P1_B1_T4` | 0.081450 / 0.081450 | 85.6237 / 85.6237 | yes |
| 3x3 | `EBf_vl_P1_B1_T4` | 0.081398 / 0.081398 | 88.0947 / 88.0947 | yes |
| 3x3 | `EBf64_route_P1_B1_T4` | 0.081347 / 0.081347 | 145.7890 / 145.7890 | yes |
| 3x3 | `EBf64_vl_P1_B1_T4` | 0.080827 / 0.080827 | 168.7160 / 168.7160 | yes |
| 4x4 | `EBf_route_P1_B1_T4` | 0.064320 / 0.064320 | 95.4039 / 95.4039 | yes |
| 4x4 | `EBf_vl_P1_B1_T4` | 0.064246 / 0.064246 | 96.7670 / 96.7670 | yes |
| 4x4 | `EBf64_route_P1_B1_T4` | 0.064362 / 0.064362 | 132.6120 / 132.6120 | yes |
| 4x4 | `EBf64_vl_P1_B1_T4` | 0.064318 / 0.064318 | 147.3241 / 147.3241 | yes |

**12 / 12 identical.**

## 3. The snapshots of `oracle_period 64`

Samples taken (`oracle_samples`) in the runs with `oracle_period 64`: one at every cycle that is a multiple of 64 after the reset. The pending counters
left at the end of a run (`oracle_pending_left_abs`, the sum of their absolute values) are the packets still on their way; they must be 0 only after a
drain test.

| size | row | samples | pending flits left at the end |
|---|---|---|---|
| 2x2 | `EBf_route_P1_B1_T4` | - | 232 |
| 2x2 | `EBf_vl_P1_B1_T4` | - | 200 |
| 2x2 | `EBf64_route_P1_B1_T4` | 156 | 552 |
| 2x2 | `EBf64_vl_P1_B1_T4` | 156 | 520 |
| 3x3 | `EBf_route_P1_B1_T4` | - | 696 |
| 3x3 | `EBf_vl_P1_B1_T4` | - | 752 |
| 3x3 | `EBf64_route_P1_B1_T4` | 156 | 1128 |
| 3x3 | `EBf64_vl_P1_B1_T4` | 156 | 1464 |
| 4x4 | `EBf_route_P1_B1_T4` | - | 1264 |
| 4x4 | `EBf_vl_P1_B1_T4` | - | 1312 |
| 4x4 | `EBf64_route_P1_B1_T4` | 156 | 1592 |
| 4x4 | `EBf64_vl_P1_B1_T4` | 156 | 1800 |

## 4. The anchor at work (description, not a gate)

4x4, 1.0 x Lsat, seed 101: EBf(route, P, 1, T) for growing T. *Off*: the share of the measured Up moves on a VL that is not DeFT-P's entry VL.

| traffic | P | T | off | THR | LAT | P99 |
|---|---|---|---|---|---|---|
| uniform | 0 | 0 | 63.4 % | 0.064305 | 119.529 | 358 |
| uniform | 1 | 0 | 65.5 % | 0.064260 | 96.811 | 235 |
| uniform | 1 | 2 | 57.5 % | 0.064230 | 96.528 | 241 |
| uniform | 1 | 8 | 35.9 % | 0.064284 | 94.393 | 232 |
| uniform | 1 | 32 | 7.8 % | 0.064277 | 103.069 | 282 |
| uniform | 1 | inf | 0.0 % | 0.064495 | 146.473 | 676 |
| uniform | DeFT_P |  | n/a | 0.064263 | 147.356 | 749 |
| hotspot | 0 | 0 | 59.0 % | 0.012500 | 67.816 | 160 |
| hotspot | 1 | 0 | 62.8 % | 0.012502 | 68.799 | 151 |
| hotspot | 1 | 2 | 47.1 % | 0.012501 | 68.285 | 149 |
| hotspot | 1 | 8 | 28.2 % | 0.012501 | 67.922 | 148 |
| hotspot | 1 | 32 | 9.1 % | 0.012489 | 69.784 | 162 |
| hotspot | 1 | inf | 0.0 % | 0.012418 | 93.889 | 631 |
| hotspot | DeFT_P |  | n/a | 0.012449 | 98.210 | 771 |

Hops of these EB runs that offer more than one output (must be 0): 0.

**All unit checks pass: yes.**
