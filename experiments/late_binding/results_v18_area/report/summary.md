# v18 report: area and timing (NanGate45, Yosys + ABC, OpenSTA)

## System-level average router area

Weighted by the router counts of a chiplet: 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL. Relative to DeFT.

| method | 2x2: um^2 / rel. | 3x3: um^2 / rel. | 4x4: um^2 / rel. |
|---|---|---|---|
| Reference (XY, no VNs) | 17940 / 0.986 | 17960 / 0.979 | 17960 / 0.973 |
| DeFT | 18201 / 1.000 | 18341 / 1.000 | 18465 / 1.000 |
| DeFT, 14 scenarios | 18903 / 1.039 | 20164 / 1.099 | 21867 / 1.184 |
| MTR | 18726 / 1.029 | 19491 / 1.063 | 20482 / 1.109 |
| RC | 19302 / 1.060 | 19349 / 1.055 | 19349 / 1.048 |
| DeFT-Dis | 18270 / 1.004 | 18430 / 1.005 | 18571 / 1.006 |
| LB-I heuristic | 21271 / 1.169 | 21379 / 1.166 | 21550 / 1.167 |
| LB-I Q-learning | 25057 / 1.377 | 26910 / 1.467 | 30033 / 1.626 |
| LB-F heuristic | 25306 / 1.390 | 25448 / 1.388 | 25663 / 1.390 |
| LB-F Q-learning | 32289 / 1.774 | 36321 / 1.980 | 42462 / 2.300 |

## Sensitivity of the system-level ratio to the flow

Relative to DeFT in the same flow. Hierarchy at 1 GHz is the primary table. Flat: the same designs without module boundaries, so constants and shared logic are optimised across units. Relaxed: hierarchy at a 6 ns target.

| method | 2x2 hier / flat / relaxed | 3x3 hier / flat / relaxed | 4x4 hier / flat / relaxed |
|---|---|---|---|
| Reference (XY, no VNs) | 0.986 / 0.967 / 0.986 | 0.979 / 0.958 / 0.979 | 0.973 / 0.952 / 0.973 |
| DeFT | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| DeFT, 14 scenarios | 1.039 / 1.039 / 1.039 | 1.099 / 1.099 / 1.099 | 1.184 / 1.187 / 1.184 |
| MTR | 1.029 / 1.005 / 1.029 | 1.063 / 1.034 / 1.063 | 1.109 / 1.084 / 1.109 |
| RC | 1.060 / 1.038 / 1.060 | 1.055 / 1.028 / 1.055 | 1.048 / 1.021 / 1.048 |
| DeFT-Dis | 1.004 / 1.003 / 1.004 | 1.005 / 1.005 / 1.005 | 1.006 / 1.005 / 1.006 |
| LB-I heuristic | 1.169 / 1.094 / 1.166 | 1.166 / 1.105 / 1.163 | 1.167 / 1.106 / 1.164 |
| LB-I Q-learning | 1.377 / 1.278 / 1.354 | 1.467 / 1.377 / 1.458 | 1.626 / 1.514 / 1.616 |
| LB-F heuristic | 1.390 / 1.233 / 1.377 | 1.388 / 1.251 / 1.377 | 1.390 / 1.251 / 1.380 |
| LB-F Q-learning | 1.774 / 1.582 / 1.745 | 1.980 / 1.786 / 1.958 | 2.300 / 2.065 / 2.269 |

Flat, per router type, relative to DeFT, 4x4 / 2x2:

| method | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|---|
| Reference (XY, no VNs) | 0.937 / 0.962 | 0.942 / 0.977 | 0.968 / 0.969 | 0.961 / 0.967 |
| DeFT | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| DeFT, 14 scenarios | 1.390 / 1.083 | 1.317 / 1.068 | 1.000 / 1.000 | 1.000 / 1.000 |
| MTR | 1.206 / 1.036 | 1.196 / 1.065 | 0.962 / 0.967 | 0.959 / 0.961 |
| RC | 0.940 / 0.968 | 1.417 / 1.459 | 0.962 / 0.967 | 0.959 / 0.961 |
| DeFT-Dis | 1.010 / 1.007 | 1.007 / 1.005 | 1.000 / 1.000 | 1.000 / 1.000 |
| LB-I heuristic | 1.017 / 1.003 | 1.009 / 1.002 | 1.197 / 1.183 | 1.204 / 1.192 |
| LB-I Q-learning | 1.017 / 1.003 | 1.047 / 1.046 | 2.012 / 1.535 | 2.025 / 1.554 |
| LB-F heuristic | 1.277 / 1.265 | 1.294 / 1.275 | 1.218 / 1.193 | 1.221 / 1.209 |
| LB-F Q-learning | 2.082 / 1.609 | 2.105 / 1.629 | 2.038 / 1.540 | 2.047 / 1.567 |

## Area per router type (um^2 / relative to DeFT / relative to the reference router)

Hierarchical synthesis, 1 GHz target, form S (one routing + selection unit per router). Cell counts: `area_runs.csv`.

### 2x2 (C = 4)

| method | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|---|
| Reference (XY, no VNs) | 16916 / 0.975 / 1.000 | 21052 / 0.979 / 1.000 | 16904 / 0.995 / 1.000 | 21008 / 0.996 / 1.000 |
| DeFT | 17345 / 1.000 / 1.025 | 21496 / 1.000 / 1.021 | 16993 / 1.000 / 1.005 | 21098 / 1.000 / 1.004 |
| DeFT, 14 scenarios | 18748 / 1.081 / 1.108 | 22899 / 1.065 / 1.088 | 16993 / 1.000 / 1.005 | 21098 / 1.000 / 1.004 |
| MTR | 18335 / 1.057 / 1.084 | 22864 / 1.064 / 1.086 | 16957 / 0.998 / 1.003 | 21072 / 0.999 / 1.003 |
| RC | 17198 / 0.992 / 1.017 | 30876 / 1.436 / 1.467 | 16957 / 0.998 / 1.003 | 21072 / 0.999 / 1.003 |
| DeFT-Dis | 17483 / 1.008 / 1.034 | 21634 / 1.006 / 1.028 | 16993 / 1.000 / 1.005 | 21098 / 1.000 / 1.004 |
| LB-I heuristic | 17418 / 1.004 / 1.030 | 21569 / 1.003 / 1.025 | 22963 / 1.351 / 1.358 | 27453 / 1.301 / 1.307 |
| LB-I Q-learning | 17418 / 1.004 / 1.030 | 22540 / 1.049 / 1.071 | 30261 / 1.781 / 1.790 | 34878 / 1.653 / 1.660 |
| LB-F heuristic | 24858 / 1.433 / 1.469 | 30336 / 1.411 / 1.441 | 23249 / 1.368 / 1.375 | 27786 / 1.317 / 1.323 |
| LB-F Q-learning | 31876 / 1.838 / 1.884 | 37377 / 1.739 / 1.776 | 30178 / 1.776 / 1.785 | 34768 / 1.648 / 1.655 |

### 3x3 (C = 9)

| method | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|---|
| Reference (XY, no VNs) | 16932 / 0.962 / 1.000 | 21095 / 0.969 / 1.000 | 16920 / 0.994 / 1.000 | 21027 / 0.995 / 1.000 |
| DeFT | 17597 / 1.000 / 1.039 | 21758 / 1.000 / 1.031 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| DeFT, 14 scenarios | 21244 / 1.207 / 1.255 | 25405 / 1.168 / 1.204 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| MTR | 19832 / 1.127 / 1.171 | 24369 / 1.120 / 1.155 | 16985 / 0.998 / 1.004 | 21105 / 0.999 / 1.004 |
| RC | 17261 / 0.981 / 1.019 | 30951 / 1.422 / 1.467 | 16985 / 0.998 / 1.004 | 21105 / 0.999 / 1.004 |
| DeFT-Dis | 17772 / 1.010 / 1.050 | 21949 / 1.009 / 1.040 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| LB-I heuristic | 17770 / 1.010 / 1.049 | 21969 / 1.010 / 1.041 | 22804 / 1.340 / 1.348 | 27338 / 1.294 / 1.300 |
| LB-I Q-learning | 17770 / 1.010 / 1.049 | 22909 / 1.053 / 1.086 | 33586 / 1.974 / 1.985 | 38305 / 1.813 / 1.822 |
| LB-F heuristic | 25282 / 1.437 / 1.493 | 30563 / 1.405 / 1.449 | 23129 / 1.359 / 1.367 | 27788 / 1.315 / 1.322 |
| LB-F Q-learning | 35960 / 2.044 / 2.124 | 41535 / 1.909 / 1.969 | 34074 / 2.002 / 2.014 | 38928 / 1.843 / 1.851 |

### 4x4 (C = 16)

| method | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|---|
| Reference (XY, no VNs) | 16932 / 0.949 / 1.000 | 21095 / 0.959 / 1.000 | 16920 / 0.994 / 1.000 | 21027 / 0.995 / 1.000 |
| DeFT | 17846 / 1.000 / 1.054 | 22008 / 1.000 / 1.043 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| DeFT, 14 scenarios | 24649 / 1.381 / 1.456 | 28810 / 1.309 / 1.366 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| MTR | 21814 / 1.222 / 1.288 | 26352 / 1.197 / 1.249 | 16985 / 0.998 / 1.004 | 21105 / 0.999 / 1.004 |
| RC | 17261 / 0.967 / 1.019 | 30951 / 1.406 / 1.467 | 16985 / 0.998 / 1.004 | 21105 / 0.999 / 1.004 |
| DeFT-Dis | 18053 / 1.012 / 1.066 | 22230 / 1.010 / 1.054 | 17017 / 1.000 / 1.006 | 21127 / 1.000 / 1.005 |
| LB-I heuristic | 18130 / 1.016 / 1.071 | 22330 / 1.015 / 1.059 | 22786 / 1.339 / 1.347 | 27325 / 1.293 / 1.299 |
| LB-I Q-learning | 18130 / 1.016 / 1.071 | 23260 / 1.057 / 1.103 | 39504 / 2.321 / 2.335 | 44097 / 2.087 / 2.097 |
| LB-F heuristic | 25495 / 1.429 / 1.506 | 30944 / 1.406 / 1.467 | 23316 / 1.370 / 1.378 | 27924 / 1.322 / 1.328 |
| LB-F Q-learning | 42164 / 2.363 / 2.490 | 47818 / 2.173 / 2.267 | 40103 / 2.357 / 2.370 | 45074 / 2.134 / 2.144 |

## Form P: one routing + selection unit per input port (upper bound)

Relative to DeFT, per router type.

| size | method | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) | system average |
|---|---|---|---|---|---|---|
| 2x2 | LB-I heuristic | 1.004 | 1.003 | 2.506 | 2.501 | 1.747 |
| 2x2 | LB-I Q-learning | 1.004 | 1.049 | 3.190 | 3.123 | 2.083 |
| 2x2 | LB-F heuristic | 2.848 | 3.084 | 2.514 | 2.500 | 2.716 |
| 2x2 | LB-F Q-learning | 3.527 | 3.660 | 3.181 | 3.082 | 3.361 |
| 3x3 | LB-I heuristic | 1.010 | 1.010 | 2.448 | 2.451 | 1.718 |
| 3x3 | LB-I Q-learning | 1.010 | 1.053 | 3.490 | 3.440 | 2.229 |
| 3x3 | LB-F heuristic | 2.870 | 3.046 | 2.468 | 2.492 | 2.702 |
| 3x3 | LB-F Q-learning | 3.837 | 3.964 | 3.520 | 3.442 | 3.689 |
| 4x4 | LB-I heuristic | 1.016 | 1.015 | 2.462 | 2.483 | 1.725 |
| 4x4 | LB-I Q-learning | 1.016 | 1.057 | 4.057 | 3.899 | 2.485 |
| 4x4 | LB-F heuristic | 2.827 | 3.051 | 2.526 | 2.527 | 2.714 |
| 4x4 | LB-F Q-learning | 4.366 | 4.430 | 4.138 | 4.042 | 4.250 |

## Comparison with the DeFT paper (normalized to MTR)

Paper: logic synthesis (Cadence Genus) plus ORION 3.0.

| ratio | paper | 2x2 | 3x3 | 4x4 |
|---|---|---|---|---|
| DeFT / MTR, boundary router | 1.016 | 0.940 | 0.893 | 0.835 |
| DeFT / MTR, chiplet router | 1.016 | 0.946 | 0.887 | 0.818 |
| DeFT / MTR, interposer router | - | 1.002 | 1.002 | 1.002 |
| RC boundary / MTR boundary | 1.133 | 1.350 | 1.270 | 1.175 |
| RC non-boundary / MTR non-boundary | 1.017 | 0.938 | 0.870 | 0.791 |

Without the NI table of MTR (16C x 2 bits, stored in flip-flops here), the same ratios:

| ratio | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| DeFT / MTR, boundary router | 1.006 | 1.015 | 1.027 |
| DeFT / MTR, chiplet router | 1.010 | 1.021 | 1.036 |
| RC boundary / MTR boundary | 1.445 | 1.444 | 1.444 |
| RC non-boundary / MTR non-boundary | 1.002 | 1.001 | 1.002 |

Reference router, buffers as share of its area (flip-flop buffers): 2x2: 64.6 %, 3x3: 64.5 %, 4x4: 64.5 %

## Critical path of the routing + selection stage against the 1 GHz cycle

OpenSTA on the flattened design, pre-layout, ideal clock, no wires. Stage: from the input-buffer flip-flops through arbitration and routing + selection to the route registers of the input VCs. Arrival and slack in ns; stages = ceil(arrival + setup / 1 ns) with no register overhead added, so a lower bound on the stages needed.

| size | method | form | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) |
|---|---|---|---|---|---|---|
| 2x2 | Reference (XY, no VNs) | S | 0.86 / +0.11 / 1 | 0.82 / +0.14 / 1 | 0.77 / +0.20 / 1 | 0.81 / +0.15 / 1 |
| 2x2 | DeFT | S | 0.90 / +0.07 / 1 | 0.91 / +0.05 / 1 | 0.94 / +0.03 / 1 | 0.85 / +0.12 / 1 |
| 2x2 | DeFT, 14 scenarios | S | 0.92 / +0.04 / 1 | 0.90 / +0.06 / 1 | 0.94 / +0.03 / 1 | 0.85 / +0.12 / 1 |
| 2x2 | MTR | S | 0.93 / +0.04 / 1 | 1.05 / -0.09 / 2 | 1.00 / -0.03 / 2 | 0.90 / +0.07 / 1 |
| 2x2 | RC | S | 1.06 / -0.09 / 2 | 0.94 / +0.02 / 1 | 1.00 / -0.03 / 2 | 0.90 / +0.07 / 1 |
| 2x2 | DeFT-Dis | S | 0.88 / +0.09 / 1 | 0.91 / +0.05 / 1 | 0.94 / +0.03 / 1 | 0.85 / +0.12 / 1 |
| 2x2 | LB-I heuristic | S | 0.87 / +0.10 / 1 | 0.89 / +0.07 / 1 | 4.06 / -3.10 / 5 | 4.62 / -3.66 / 5 |
| 2x2 | LB-I heuristic | P | - | - | 3.77 / -2.81 / 4 | 4.09 / -3.13 / 5 |
| 2x2 | LB-I Q-learning | S | 0.87 / +0.10 / 1 | 0.91 / +0.05 / 1 | 4.63 / -3.67 / 5 | 5.28 / -4.32 / 6 |
| 2x2 | LB-I Q-learning | P | - | - | 4.39 / -3.43 / 5 | 4.87 / -3.91 / 5 |
| 2x2 | LB-F heuristic | S | 4.83 / -3.87 / 5 | 5.27 / -4.31 / 6 | 4.14 / -3.18 / 5 | 4.61 / -3.65 / 5 |
| 2x2 | LB-F heuristic | P | 4.40 / -3.44 / 5 | 4.81 / -3.85 / 5 | 3.75 / -2.79 / 4 | 3.98 / -3.02 / 5 |
| 2x2 | LB-F Q-learning | S | 5.51 / -4.55 / 6 | 5.96 / -5.00 / 7 | 4.85 / -3.89 / 5 | 5.19 / -4.23 / 6 |
| 2x2 | LB-F Q-learning | P | 5.05 / -4.09 / 6 | 5.49 / -4.53 / 6 | 4.21 / -3.25 / 5 | 4.79 / -3.83 / 5 |
| 3x3 | Reference (XY, no VNs) | S | 0.85 / +0.11 / 1 | 0.86 / +0.10 / 1 | 0.91 / +0.05 / 1 | 0.87 / +0.09 / 1 |
| 3x3 | DeFT | S | 0.95 / +0.01 / 1 | 1.07 / -0.11 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 3x3 | DeFT, 14 scenarios | S | 0.95 / +0.01 / 1 | 1.07 / -0.11 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 3x3 | MTR | S | 1.06 / -0.09 / 2 | 1.07 / -0.12 / 2 | 0.88 / +0.09 / 1 | 0.89 / +0.07 / 1 |
| 3x3 | RC | S | 1.11 / -0.15 / 2 | 1.09 / -0.12 / 2 | 0.88 / +0.09 / 1 | 0.89 / +0.07 / 1 |
| 3x3 | DeFT-Dis | S | 0.95 / +0.01 / 1 | 1.03 / -0.07 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 3x3 | LB-I heuristic | S | 0.97 / -0.02 / 2 | 1.08 / -0.13 / 2 | 4.40 / -3.44 / 5 | 4.58 / -3.62 / 5 |
| 3x3 | LB-I heuristic | P | - | - | 3.93 / -2.97 / 4 | 4.35 / -3.39 / 5 |
| 3x3 | LB-I Q-learning | S | 0.97 / -0.02 / 2 | 1.00 / -0.04 / 2 | 4.96 / -3.99 / 5 | 5.29 / -4.33 / 6 |
| 3x3 | LB-I Q-learning | P | - | - | 4.51 / -3.54 / 5 | 5.11 / -4.15 / 6 |
| 3x3 | LB-F heuristic | S | 5.05 / -4.09 / 6 | 5.32 / -4.36 / 6 | 4.31 / -3.35 / 5 | 4.53 / -3.57 / 5 |
| 3x3 | LB-F heuristic | P | 4.61 / -3.65 / 5 | 5.18 / -4.22 / 6 | 4.04 / -3.08 / 5 | 4.25 / -3.29 / 5 |
| 3x3 | LB-F Q-learning | S | 5.70 / -4.74 / 6 | 6.46 / -5.50 / 7 | 4.97 / -4.01 / 6 | 5.38 / -4.42 / 6 |
| 3x3 | LB-F Q-learning | P | 5.33 / -4.37 / 6 | 5.95 / -4.99 / 6 | 4.43 / -3.47 / 5 | 4.95 / -3.99 / 5 |
| 4x4 | Reference (XY, no VNs) | S | 0.85 / +0.11 / 1 | 0.86 / +0.10 / 1 | 0.91 / +0.05 / 1 | 0.87 / +0.09 / 1 |
| 4x4 | DeFT | S | 0.99 / -0.02 / 2 | 1.11 / -0.15 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 4x4 | DeFT, 14 scenarios | S | 0.99 / -0.02 / 2 | 1.04 / -0.08 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 4x4 | MTR | S | 1.05 / -0.08 / 2 | 1.07 / -0.11 / 2 | 0.88 / +0.09 / 1 | 0.89 / +0.07 / 1 |
| 4x4 | RC | S | 1.11 / -0.15 / 2 | 1.09 / -0.12 / 2 | 0.88 / +0.09 / 1 | 0.89 / +0.07 / 1 |
| 4x4 | DeFT-Dis | S | 1.07 / -0.11 / 2 | 1.09 / -0.13 / 2 | 0.85 / +0.11 / 1 | 0.82 / +0.14 / 1 |
| 4x4 | LB-I heuristic | S | 0.99 / -0.02 / 2 | 1.08 / -0.12 / 2 | 4.40 / -3.44 / 5 | 4.59 / -3.63 / 5 |
| 4x4 | LB-I heuristic | P | - | - | 3.96 / -3.00 / 5 | 4.51 / -3.55 / 5 |
| 4x4 | LB-I Q-learning | S | 0.99 / -0.02 / 2 | 1.02 / -0.06 / 2 | 4.91 / -3.94 / 5 | 5.28 / -4.32 / 6 |
| 4x4 | LB-I Q-learning | P | - | - | 4.55 / -3.59 / 5 | 4.95 / -3.99 / 5 |
| 4x4 | LB-F heuristic | S | 5.22 / -4.26 / 6 | 5.49 / -4.53 / 6 | 4.39 / -3.43 / 5 | 4.73 / -3.77 / 5 |
| 4x4 | LB-F heuristic | P | 4.59 / -3.63 / 5 | 5.10 / -4.14 / 6 | 3.96 / -3.01 / 5 | 4.48 / -3.52 / 5 |
| 4x4 | LB-F Q-learning | S | 5.72 / -4.76 / 6 | 6.22 / -5.26 / 7 | 5.03 / -4.07 / 6 | 5.54 / -4.58 / 6 |
| 4x4 | LB-F Q-learning | P | 5.47 / -4.51 / 6 | 5.66 / -4.70 / 6 | 4.59 / -3.63 / 5 | 5.36 / -4.40 / 6 |

## Other paths, form S (slack in ns against 1 ns)

| size | method | router type | whole design | Q table write (update path) |
|---|---|---|---|---|
| 2x2 | Reference (XY, no VNs) | chiplet (5 ports) | -0.30 | - |
| 2x2 | Reference (XY, no VNs) | boundary (6 ports) | -0.25 | - |
| 2x2 | Reference (XY, no VNs) | interposer (5 ports) | -0.31 | - |
| 2x2 | Reference (XY, no VNs) | interposer + VL (6 ports) | -0.28 | - |
| 2x2 | DeFT | chiplet (5 ports) | -0.25 | - |
| 2x2 | DeFT | boundary (6 ports) | -0.28 | - |
| 2x2 | DeFT | interposer (5 ports) | -0.27 | - |
| 2x2 | DeFT | interposer + VL (6 ports) | -0.32 | - |
| 2x2 | DeFT, 14 scenarios | chiplet (5 ports) | -0.26 | - |
| 2x2 | DeFT, 14 scenarios | boundary (6 ports) | -0.32 | - |
| 2x2 | DeFT, 14 scenarios | interposer (5 ports) | -0.27 | - |
| 2x2 | DeFT, 14 scenarios | interposer + VL (6 ports) | -0.32 | - |
| 2x2 | MTR | chiplet (5 ports) | -0.26 | - |
| 2x2 | MTR | boundary (6 ports) | -0.26 | - |
| 2x2 | MTR | interposer (5 ports) | -0.29 | - |
| 2x2 | MTR | interposer + VL (6 ports) | -0.37 | - |
| 2x2 | RC | chiplet (5 ports) | -0.27 | - |
| 2x2 | RC | boundary (6 ports) | -0.36 | - |
| 2x2 | RC | interposer (5 ports) | -0.29 | - |
| 2x2 | RC | interposer + VL (6 ports) | -0.37 | - |
| 2x2 | DeFT-Dis | chiplet (5 ports) | -0.28 | - |
| 2x2 | DeFT-Dis | boundary (6 ports) | -0.35 | - |
| 2x2 | DeFT-Dis | interposer (5 ports) | -0.27 | - |
| 2x2 | DeFT-Dis | interposer + VL (6 ports) | -0.32 | - |
| 2x2 | LB-I heuristic | chiplet (5 ports) | -0.22 | - |
| 2x2 | LB-I heuristic | boundary (6 ports) | -0.34 | - |
| 2x2 | LB-I heuristic | interposer (5 ports) | -3.16 | - |
| 2x2 | LB-I heuristic | interposer + VL (6 ports) | -3.72 | - |
| 2x2 | LB-I Q-learning | chiplet (5 ports) | -0.22 | - |
| 2x2 | LB-I Q-learning | boundary (6 ports) | -0.96 | - |
| 2x2 | LB-I Q-learning | interposer (5 ports) | -3.73 | -0.83 |
| 2x2 | LB-I Q-learning | interposer + VL (6 ports) | -4.40 | -0.87 |
| 2x2 | LB-F heuristic | chiplet (5 ports) | -4.00 | - |
| 2x2 | LB-F heuristic | boundary (6 ports) | -4.35 | - |
| 2x2 | LB-F heuristic | interposer (5 ports) | -3.22 | - |
| 2x2 | LB-F heuristic | interposer + VL (6 ports) | -3.71 | - |
| 2x2 | LB-F Q-learning | chiplet (5 ports) | -4.67 | -0.81 |
| 2x2 | LB-F Q-learning | boundary (6 ports) | -5.06 | -0.83 |
| 2x2 | LB-F Q-learning | interposer (5 ports) | -3.94 | -0.85 |
| 2x2 | LB-F Q-learning | interposer + VL (6 ports) | -4.33 | -0.81 |
| 3x3 | Reference (XY, no VNs) | chiplet (5 ports) | -0.22 | - |
| 3x3 | Reference (XY, no VNs) | boundary (6 ports) | -0.33 | - |
| 3x3 | Reference (XY, no VNs) | interposer (5 ports) | -0.30 | - |
| 3x3 | Reference (XY, no VNs) | interposer + VL (6 ports) | -0.36 | - |
| 3x3 | DeFT | chiplet (5 ports) | -0.26 | - |
| 3x3 | DeFT | boundary (6 ports) | -0.31 | - |
| 3x3 | DeFT | interposer (5 ports) | -0.31 | - |
| 3x3 | DeFT | interposer + VL (6 ports) | -0.27 | - |
| 3x3 | DeFT, 14 scenarios | chiplet (5 ports) | -0.28 | - |
| 3x3 | DeFT, 14 scenarios | boundary (6 ports) | -0.27 | - |
| 3x3 | DeFT, 14 scenarios | interposer (5 ports) | -0.31 | - |
| 3x3 | DeFT, 14 scenarios | interposer + VL (6 ports) | -0.27 | - |
| 3x3 | MTR | chiplet (5 ports) | -0.30 | - |
| 3x3 | MTR | boundary (6 ports) | -0.26 | - |
| 3x3 | MTR | interposer (5 ports) | -0.33 | - |
| 3x3 | MTR | interposer + VL (6 ports) | -0.30 | - |
| 3x3 | RC | chiplet (5 ports) | -0.30 | - |
| 3x3 | RC | boundary (6 ports) | -0.37 | - |
| 3x3 | RC | interposer (5 ports) | -0.33 | - |
| 3x3 | RC | interposer + VL (6 ports) | -0.30 | - |
| 3x3 | DeFT-Dis | chiplet (5 ports) | -0.25 | - |
| 3x3 | DeFT-Dis | boundary (6 ports) | -0.36 | - |
| 3x3 | DeFT-Dis | interposer (5 ports) | -0.31 | - |
| 3x3 | DeFT-Dis | interposer + VL (6 ports) | -0.27 | - |
| 3x3 | LB-I heuristic | chiplet (5 ports) | -0.25 | - |
| 3x3 | LB-I heuristic | boundary (6 ports) | -0.25 | - |
| 3x3 | LB-I heuristic | interposer (5 ports) | -3.52 | - |
| 3x3 | LB-I heuristic | interposer + VL (6 ports) | -3.68 | - |
| 3x3 | LB-I Q-learning | chiplet (5 ports) | -0.25 | - |
| 3x3 | LB-I Q-learning | boundary (6 ports) | -0.84 | - |
| 3x3 | LB-I Q-learning | interposer (5 ports) | -4.06 | -1.01 |
| 3x3 | LB-I Q-learning | interposer + VL (6 ports) | -4.43 | -0.97 |
| 3x3 | LB-F heuristic | chiplet (5 ports) | -4.19 | - |
| 3x3 | LB-F heuristic | boundary (6 ports) | -4.38 | - |
| 3x3 | LB-F heuristic | interposer (5 ports) | -3.42 | - |
| 3x3 | LB-F heuristic | interposer + VL (6 ports) | -3.66 | - |
| 3x3 | LB-F Q-learning | chiplet (5 ports) | -4.81 | -0.99 |
| 3x3 | LB-F Q-learning | boundary (6 ports) | -5.51 | -1.01 |
| 3x3 | LB-F Q-learning | interposer (5 ports) | -4.10 | -1.02 |
| 3x3 | LB-F Q-learning | interposer + VL (6 ports) | -4.51 | -1.02 |
| 4x4 | Reference (XY, no VNs) | chiplet (5 ports) | -0.22 | - |
| 4x4 | Reference (XY, no VNs) | boundary (6 ports) | -0.33 | - |
| 4x4 | Reference (XY, no VNs) | interposer (5 ports) | -0.30 | - |
| 4x4 | Reference (XY, no VNs) | interposer + VL (6 ports) | -0.36 | - |
| 4x4 | DeFT | chiplet (5 ports) | -0.24 | - |
| 4x4 | DeFT | boundary (6 ports) | -0.27 | - |
| 4x4 | DeFT | interposer (5 ports) | -0.31 | - |
| 4x4 | DeFT | interposer + VL (6 ports) | -0.27 | - |
| 4x4 | DeFT, 14 scenarios | chiplet (5 ports) | -0.27 | - |
| 4x4 | DeFT, 14 scenarios | boundary (6 ports) | -0.30 | - |
| 4x4 | DeFT, 14 scenarios | interposer (5 ports) | -0.31 | - |
| 4x4 | DeFT, 14 scenarios | interposer + VL (6 ports) | -0.27 | - |
| 4x4 | MTR | chiplet (5 ports) | -0.18 | - |
| 4x4 | MTR | boundary (6 ports) | -0.32 | - |
| 4x4 | MTR | interposer (5 ports) | -0.33 | - |
| 4x4 | MTR | interposer + VL (6 ports) | -0.30 | - |
| 4x4 | RC | chiplet (5 ports) | -0.30 | - |
| 4x4 | RC | boundary (6 ports) | -0.37 | - |
| 4x4 | RC | interposer (5 ports) | -0.33 | - |
| 4x4 | RC | interposer + VL (6 ports) | -0.30 | - |
| 4x4 | DeFT-Dis | chiplet (5 ports) | -0.27 | - |
| 4x4 | DeFT-Dis | boundary (6 ports) | -0.36 | - |
| 4x4 | DeFT-Dis | interposer (5 ports) | -0.31 | - |
| 4x4 | DeFT-Dis | interposer + VL (6 ports) | -0.27 | - |
| 4x4 | LB-I heuristic | chiplet (5 ports) | -0.25 | - |
| 4x4 | LB-I heuristic | boundary (6 ports) | -0.30 | - |
| 4x4 | LB-I heuristic | interposer (5 ports) | -3.55 | - |
| 4x4 | LB-I heuristic | interposer + VL (6 ports) | -3.73 | - |
| 4x4 | LB-I Q-learning | chiplet (5 ports) | -0.25 | - |
| 4x4 | LB-I Q-learning | boundary (6 ports) | -0.70 | - |
| 4x4 | LB-I Q-learning | interposer (5 ports) | -4.01 | -1.06 |
| 4x4 | LB-I Q-learning | interposer + VL (6 ports) | -4.37 | -1.11 |
| 4x4 | LB-F heuristic | chiplet (5 ports) | -4.42 | - |
| 4x4 | LB-F heuristic | boundary (6 ports) | -4.60 | - |
| 4x4 | LB-F heuristic | interposer (5 ports) | -3.53 | - |
| 4x4 | LB-F heuristic | interposer + VL (6 ports) | -3.88 | - |
| 4x4 | LB-F Q-learning | chiplet (5 ports) | -4.85 | -1.02 |
| 4x4 | LB-F Q-learning | boundary (6 ports) | -5.31 | -1.02 |
| 4x4 | LB-F Q-learning | interposer (5 ports) | -4.13 | -1.03 |
| 4x4 | LB-F Q-learning | interposer + VL (6 ports) | -4.68 | -1.01 |

## Timing experiment: the routing + selection unit cut into stages

Registers inserted in the unit, flattened, OpenSTA. Timing only: the control that would hold a head across these stages is not implemented, and the design is not functionally checked with cuts. Each cell: longest stage (ns) over the listed cuts and the last stage into the route registers / area relative to the same design without cuts.

| size | method | router type | form | no cut | route / rest | route+T / rest | route+T+BC / cost+tree | route+T / BC / cost+tree | route+T / BC+cost / tree | route+T / BC / cost / tree | route / T / BC / cost / tree |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2x2 | LB-F heuristic | boundary (6 ports) | S | 5.19 / 1.000 | 4.62 / 1.062 | 4.08 / 1.075 | 3.32 / 1.004 | 2.24 / 1.083 | 2.30 / 1.084 | 2.13 / 1.099 | 2.10 / 1.135 |
| 2x2 | LB-F heuristic | interposer + VL (6 ports) | S | 4.47 / 1.000 | 3.70 / 1.040 | 3.75 / 1.060 | 2.66 / 1.012 | 2.14 / 1.070 | 2.20 / 1.075 | 2.00 / 1.083 | 2.00 / 1.098 |
| 2x2 | LB-F Q-learning | boundary (6 ports) | S | 5.99 / 1.000 | 5.47 / 1.061 | 4.57 / 1.060 | 3.38 / 1.007 | 2.58 / 1.072 | 2.65 / 1.086 | 2.54 / 1.096 | 2.58 / 1.127 |
| 2x2 | LB-F Q-learning | interposer + VL (6 ports) | S | 5.33 / 1.000 | 4.69 / 1.044 | 4.45 / 1.044 | 2.83 / 1.011 | 2.68 / 1.057 | 2.52 / 1.067 | 2.51 / 1.079 | 2.37 / 1.086 |
| 2x2 | LB-I heuristic | interposer + VL (6 ports) | S | 4.42 / 1.000 | 4.17 / 1.055 | 3.63 / 1.061 | 2.78 / 1.010 | 2.19 / 1.070 | 2.31 / 1.074 | 1.96 / 1.085 | 1.99 / 1.097 |
| 2x2 | LB-I Q-learning | interposer + VL (6 ports) | S | 5.32 / 1.000 | 4.81 / 1.043 | 4.57 / 1.044 | 2.81 / 1.006 | 2.64 / 1.053 | 2.62 / 1.066 | 2.49 / 1.075 | 2.57 / 1.086 |
| 3x3 | LB-F heuristic | boundary (6 ports) | S | 5.63 / 1.000 | 5.05 / 1.084 | 4.01 / 1.065 | 3.53 / 1.007 | 2.34 / 1.075 | 2.38 / 1.078 | 2.33 / 1.089 | 2.05 / 1.138 |
| 3x3 | LB-F heuristic | interposer + VL (6 ports) | S | 4.72 / 1.000 | 4.06 / 1.043 | 3.77 / 1.063 | 2.94 / 1.014 | 2.12 / 1.074 | 2.20 / 1.075 | 1.98 / 1.089 | 1.99 / 1.101 |
| 3x3 | LB-F Q-learning | boundary (6 ports) | S | 6.29 / 1.000 | 5.69 / 1.063 | 4.49 / 1.051 | 3.72 / 1.007 | 2.56 / 1.060 | 2.57 / 1.069 | 2.29 / 1.076 | 2.58 / 1.111 |
| 3x3 | LB-F Q-learning | interposer + VL (6 ports) | S | 5.39 / 1.000 | 4.61 / 1.037 | 4.48 / 1.045 | 2.89 / 1.012 | 2.47 / 1.058 | 2.60 / 1.066 | 2.34 / 1.075 | 2.44 / 1.085 |
| 3x3 | LB-I heuristic | interposer + VL (6 ports) | S | 4.72 / 1.000 | 4.03 / 1.048 | 3.79 / 1.060 | 3.01 / 1.006 | 2.25 / 1.071 | 2.29 / 1.070 | 1.96 / 1.085 | 2.00 / 1.096 |
| 3x3 | LB-I Q-learning | interposer + VL (6 ports) | S | 5.26 / 1.000 | 4.64 / 1.033 | 4.37 / 1.045 | 2.94 / 1.011 | 2.67 / 1.055 | 2.45 / 1.066 | 2.17 / 1.072 | 2.27 / 1.083 |
| 4x4 | LB-F heuristic | boundary (6 ports) | S | 5.85 / 1.000 | 5.11 / 1.086 | 3.91 / 1.069 | 3.50 / 1.014 | 2.27 / 1.082 | 2.50 / 1.079 | 2.32 / 1.091 | 2.04 / 1.143 |
| 4x4 | LB-F heuristic | interposer + VL (6 ports) | S | 4.77 / 1.000 | 4.15 / 1.044 | 3.76 / 1.061 | 2.96 / 1.011 | 2.07 / 1.072 | 2.38 / 1.072 | 2.00 / 1.083 | 2.00 / 1.098 |
| 4x4 | LB-F Q-learning | boundary (6 ports) | P | 5.66 / 1.000 | 6.19 / 1.210 | 4.66 / 1.184 | 3.30 / 1.046 | 2.77 / 1.214 | 2.65 / 1.243 | 2.46 / 1.267 | 2.41 / 1.367 |
| 4x4 | LB-F Q-learning | boundary (6 ports) | S | 6.32 / 1.000 | 5.60 / 1.057 | 4.48 / 1.047 | 3.50 / 1.003 | 2.60 / 1.049 | 2.63 / 1.053 | 2.33 / 1.060 | 2.41 / 1.091 |
| 4x4 | LB-F Q-learning | interposer + VL (6 ports) | S | 5.46 / 1.000 | 4.79 / 1.029 | 4.49 / 1.040 | 2.94 / 1.009 | 2.82 / 1.050 | 2.59 / 1.054 | 2.38 / 1.059 | 2.35 / 1.067 |
| 4x4 | LB-I heuristic | interposer + VL (6 ports) | S | 4.81 / 1.000 | 3.94 / 1.049 | 3.74 / 1.063 | 3.05 / 1.007 | 2.13 / 1.070 | 2.30 / 1.071 | 1.95 / 1.082 | 1.94 / 1.099 |
| 4x4 | LB-I Q-learning | interposer + VL (6 ports) | P | 4.95 / 1.000 | 4.73 / 1.156 | 4.50 / 1.195 | 2.74 / 1.063 | 2.70 / 1.232 | 2.54 / 1.263 | 2.36 / 1.288 | 2.43 / 1.318 |
| 4x4 | LB-I Q-learning | interposer + VL (6 ports) | S | 5.47 / 1.000 | 4.72 / 1.025 | 4.39 / 1.036 | 2.95 / 1.012 | 2.60 / 1.047 | 2.48 / 1.052 | 2.44 / 1.060 | 2.27 / 1.068 |

Stage by stage with all cuts (route / T / BC / cost / tree), ns:

| size | method | router type | form | route | T | BC | cost | tree |
|---|---|---|---|---|---|---|---|---|
| 2x2 | LB-F heuristic | boundary (6 ports) | S | 1.49 | 1.53 | 2.10 | 0.48 | 2.04 |
| 2x2 | LB-F heuristic | interposer + VL (6 ports) | S | 1.32 | 0.52 | 2.00 | 0.46 | 1.93 |
| 2x2 | LB-F Q-learning | boundary (6 ports) | S | 1.50 | 1.68 | 2.25 | 2.24 | 2.58 |
| 2x2 | LB-F Q-learning | interposer + VL (6 ports) | S | 1.34 | 0.54 | 2.10 | 2.10 | 2.37 |
| 2x2 | LB-I heuristic | interposer + VL (6 ports) | S | 1.39 | 0.53 | 1.99 | 0.55 | 1.87 |
| 2x2 | LB-I Q-learning | interposer + VL (6 ports) | S | 1.32 | 0.55 | 2.21 | 2.20 | 2.57 |
| 3x3 | LB-F heuristic | boundary (6 ports) | S | 1.48 | 1.70 | 2.04 | 0.48 | 2.05 |
| 3x3 | LB-F heuristic | interposer + VL (6 ports) | S | 1.40 | 0.68 | 1.99 | 0.46 | 1.82 |
| 3x3 | LB-F Q-learning | boundary (6 ports) | S | 1.48 | 1.74 | 2.35 | 2.35 | 2.58 |
| 3x3 | LB-F Q-learning | interposer + VL (6 ports) | S | 1.41 | 0.67 | 2.16 | 2.15 | 2.44 |
| 3x3 | LB-I heuristic | interposer + VL (6 ports) | S | 1.46 | 0.73 | 2.00 | 0.46 | 1.86 |
| 3x3 | LB-I Q-learning | interposer + VL (6 ports) | S | 1.40 | 0.72 | 2.16 | 2.16 | 2.27 |
| 4x4 | LB-F heuristic | boundary (6 ports) | S | 1.49 | 1.72 | 2.04 | 0.53 | 1.91 |
| 4x4 | LB-F heuristic | interposer + VL (6 ports) | S | 1.38 | 0.70 | 2.00 | 0.55 | 1.92 |
| 4x4 | LB-F Q-learning | boundary (6 ports) | P | 1.03 | 1.96 | 2.32 | 2.33 | 2.41 |
| 4x4 | LB-F Q-learning | boundary (6 ports) | S | 1.46 | 1.72 | 2.28 | 2.27 | 2.41 |
| 4x4 | LB-F Q-learning | interposer + VL (6 ports) | S | 1.38 | 0.70 | 2.20 | 2.20 | 2.35 |
| 4x4 | LB-I heuristic | interposer + VL (6 ports) | S | 1.34 | 0.68 | 1.94 | 0.46 | 1.88 |
| 4x4 | LB-I Q-learning | interposer + VL (6 ports) | P | 0.96 | 1.05 | 2.24 | 2.20 | 2.43 |
| 4x4 | LB-I Q-learning | interposer + VL (6 ports) | S | 1.35 | 0.72 | 2.27 | 2.25 | 2.24 |

## Share of the router area (%)

Form S. FF = flip-flops in the router.

### 2x2, chiplet (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16916 | 1796 | 64.6 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.5 |
| DeFT | 17345 | 1808 | 63.0 | - | 15.2 | 17.7 | 0.7 | - | 0.6 | - | 0.2 | 2.6 |
| DeFT, 14 scenarios | 18748 | 1968 | 58.3 | - | 14.1 | 16.4 | 0.6 | - | 7.8 | - | 0.3 | 2.6 |
| MTR | 18335 | 1926 | 59.6 | - | 14.4 | 16.8 | 0.5 | - | 6.3 | - | 0.0 | 2.4 |
| RC | 17198 | 1796 | 63.5 | - | 15.4 | 17.9 | 0.6 | - | - | - | 0.1 | 2.6 |
| DeFT-Dis | 17483 | 1812 | 62.5 | - | 15.1 | 17.6 | 0.7 | - | 0.9 | - | 0.7 | 2.6 |
| LB-I heuristic | 17418 | 1818 | 62.7 | - | 15.2 | 17.7 | 0.7 | - | 1.0 | - | 0.1 | 2.6 |
| LB-I Q-learning | 17418 | 1818 | 62.7 | - | 15.2 | 17.7 | 0.7 | - | 1.0 | - | 0.1 | 2.6 |
| LB-F heuristic | 24858 | 1996 | 43.9 | - | 11.5 | 14.5 | 1.4 | 25.1 | 0.6 | - | 0.1 | 2.9 |
| LB-F Q-learning | 31876 | 2529 | 34.3 | - | 9.2 | 12.9 | 1.1 | 21.8 | 9.9 | 7.7 | 0.1 | 3.0 |

### 2x2, boundary (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21052 | 2185 | 62.3 | - | 16.4 | 19.7 | 0.3 | - | - | - | - | 1.3 |
| DeFT | 21496 | 2197 | 61.0 | - | 16.1 | 19.3 | 0.7 | - | 0.4 | - | 0.1 | 2.4 |
| DeFT, 14 scenarios | 22899 | 2357 | 57.2 | - | 15.1 | 18.1 | 0.6 | - | 6.4 | - | 0.2 | 2.4 |
| MTR | 22864 | 2355 | 57.3 | - | 15.1 | 18.2 | 0.5 | - | 6.6 | - | 0.0 | 2.3 |
| RC | 30876 | 3315 | 42.4 | 30.4 | 11.2 | 13.4 | 0.4 | - | - | - | 0.1 | 2.1 |
| DeFT-Dis | 21634 | 2201 | 60.6 | - | 16.0 | 19.1 | 0.7 | - | 0.7 | - | 0.5 | 2.4 |
| LB-I heuristic | 21569 | 2207 | 60.8 | - | 16.0 | 19.2 | 0.7 | - | 0.8 | - | 0.1 | 2.4 |
| LB-I Q-learning | 22540 | 2305 | 58.1 | - | 15.3 | 18.4 | 0.7 | 4.2 | 0.8 | - | 0.1 | 2.4 |
| LB-F heuristic | 30336 | 2432 | 43.2 | - | 12.2 | 15.7 | 1.2 | 24.4 | 0.5 | - | 0.1 | 2.7 |
| LB-F Q-learning | 37377 | 2983 | 35.1 | - | 10.3 | 14.4 | 0.9 | 21.4 | 8.5 | 6.5 | 0.1 | 2.9 |

### 2x2, interposer (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16904 | 1795 | 64.6 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.4 |
| DeFT | 16993 | 1795 | 64.3 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.8 |
| DeFT, 14 scenarios | 16993 | 1795 | 64.3 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.8 |
| MTR | 16957 | 1795 | 64.4 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.7 |
| RC | 16957 | 1795 | 64.4 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.7 |
| DeFT-Dis | 16993 | 1795 | 64.3 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.8 |
| LB-I heuristic | 22963 | 1939 | 47.6 | - | 12.3 | 14.5 | 1.4 | 21.9 | - | - | - | 2.3 |
| LB-I Q-learning | 30261 | 2472 | 36.1 | - | 9.6 | 12.7 | 1.1 | 18.6 | 10.0 | 9.4 | - | 2.5 |
| LB-F heuristic | 23249 | 1979 | 47.0 | - | 12.3 | 15.5 | 1.4 | 21.4 | - | - | - | 2.4 |
| LB-F Q-learning | 30178 | 2512 | 36.2 | - | 9.8 | 13.6 | 1.1 | 18.6 | 10.0 | 8.1 | - | 2.6 |

### 2x2, interposer + VL (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21008 | 2184 | 62.4 | - | 16.4 | 19.8 | 0.1 | - | - | - | - | 1.3 |
| DeFT | 21098 | 2184 | 62.1 | - | 16.4 | 19.6 | 0.3 | - | - | - | - | 1.6 |
| DeFT, 14 scenarios | 21098 | 2184 | 62.1 | - | 16.4 | 19.6 | 0.3 | - | - | - | - | 1.6 |
| MTR | 21072 | 2184 | 62.2 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.5 |
| RC | 21072 | 2184 | 62.2 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.5 |
| DeFT-Dis | 21098 | 2184 | 62.1 | - | 16.4 | 19.6 | 0.3 | - | - | - | - | 1.6 |
| LB-I heuristic | 27453 | 2367 | 47.7 | - | 13.4 | 16.3 | 1.2 | 19.2 | - | - | - | 2.2 |
| LB-I Q-learning | 34878 | 2918 | 37.6 | - | 10.8 | 14.6 | 0.9 | 16.9 | 8.6 | 8.1 | - | 2.4 |
| LB-F heuristic | 27786 | 2415 | 47.2 | - | 13.4 | 17.2 | 1.2 | 18.8 | - | - | - | 2.3 |
| LB-F Q-learning | 34768 | 2966 | 37.7 | - | 11.0 | 15.5 | 1.0 | 16.6 | 8.7 | 7.0 | - | 2.5 |

### 3x3, chiplet (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16932 | 1796 | 64.5 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.6 |
| DeFT | 17597 | 1828 | 62.1 | - | 15.0 | 17.5 | 0.8 | - | 1.5 | - | 0.3 | 2.8 |
| DeFT, 14 scenarios | 21244 | 2248 | 51.4 | - | 12.4 | 14.5 | 0.7 | - | 18.3 | - | 0.3 | 2.4 |
| MTR | 19832 | 2086 | 55.1 | - | 13.3 | 15.5 | 0.6 | - | 13.1 | - | 0.1 | 2.3 |
| RC | 17261 | 1796 | 63.3 | - | 15.3 | 17.8 | 0.7 | - | - | - | 0.1 | 2.8 |
| DeFT-Dis | 17772 | 1832 | 61.5 | - | 14.9 | 17.3 | 0.8 | - | 2.0 | - | 0.8 | 2.7 |
| LB-I heuristic | 17770 | 1848 | 61.5 | - | 14.9 | 17.3 | 0.8 | - | 2.5 | - | 0.3 | 2.7 |
| LB-I Q-learning | 17770 | 1848 | 61.5 | - | 14.9 | 17.3 | 0.8 | - | 2.5 | - | 0.3 | 2.7 |
| LB-F heuristic | 25282 | 2016 | 43.2 | - | 11.3 | 14.2 | 1.4 | 25.3 | 1.4 | - | 0.2 | 3.0 |
| LB-F Q-learning | 35960 | 2951 | 30.4 | - | 8.2 | 11.4 | 1.0 | 18.8 | 20.8 | 6.4 | 0.1 | 2.9 |

### 3x3, boundary (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21095 | 2185 | 62.1 | - | 16.4 | 19.7 | 0.4 | - | - | - | - | 1.4 |
| DeFT | 21758 | 2217 | 60.2 | - | 15.9 | 19.0 | 0.8 | - | 1.2 | - | 0.2 | 2.5 |
| DeFT, 14 scenarios | 25405 | 2637 | 51.6 | - | 13.6 | 16.3 | 0.7 | - | 15.3 | - | 0.3 | 2.3 |
| MTR | 24369 | 2515 | 53.8 | - | 14.2 | 17.1 | 0.6 | - | 12.0 | - | 0.1 | 2.3 |
| RC | 30951 | 3315 | 42.3 | 30.3 | 11.2 | 13.4 | 0.5 | - | - | - | 0.1 | 2.2 |
| DeFT-Dis | 21949 | 2221 | 59.7 | - | 15.7 | 18.9 | 0.8 | - | 1.6 | - | 0.6 | 2.5 |
| LB-I heuristic | 21969 | 2237 | 59.7 | - | 15.7 | 19.0 | 0.8 | - | 2.0 | - | 0.2 | 2.5 |
| LB-I Q-learning | 22909 | 2335 | 57.2 | - | 15.1 | 18.1 | 0.8 | 4.1 | 1.9 | - | 0.2 | 2.6 |
| LB-F heuristic | 30563 | 2452 | 42.9 | - | 12.2 | 15.6 | 1.2 | 24.0 | 1.2 | - | 0.2 | 2.8 |
| LB-F Q-learning | 41535 | 3405 | 31.6 | - | 9.2 | 13.0 | 0.9 | 19.0 | 18.0 | 5.5 | 0.1 | 2.8 |

### 3x3, interposer (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16920 | 1795 | 64.6 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.6 |
| DeFT | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| DeFT, 14 scenarios | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| MTR | 16985 | 1795 | 64.3 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.9 |
| RC | 16985 | 1795 | 64.3 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.9 |
| DeFT-Dis | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| LB-I heuristic | 22804 | 1939 | 47.9 | - | 12.4 | 14.6 | 1.4 | 21.2 | - | - | - | 2.5 |
| LB-I Q-learning | 33586 | 2874 | 32.5 | - | 8.6 | 11.5 | 1.0 | 16.0 | 21.2 | 6.7 | - | 2.5 |
| LB-F heuristic | 23129 | 1979 | 47.2 | - | 12.4 | 15.5 | 1.4 | 20.9 | - | - | - | 2.5 |
| LB-F Q-learning | 34074 | 2914 | 32.1 | - | 8.7 | 12.1 | 1.0 | 15.8 | 20.9 | 7.0 | - | 2.6 |

### 3x3, interposer + VL (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21027 | 2184 | 62.3 | - | 16.4 | 19.8 | 0.1 | - | - | - | - | 1.4 |
| DeFT | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| DeFT, 14 scenarios | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| MTR | 21105 | 2184 | 62.1 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.7 |
| RC | 21105 | 2184 | 62.1 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.7 |
| DeFT-Dis | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| LB-I heuristic | 27338 | 2367 | 47.9 | - | 13.4 | 16.4 | 1.2 | 18.8 | - | - | - | 2.3 |
| LB-I Q-learning | 38305 | 3320 | 34.2 | - | 9.8 | 13.3 | 0.9 | 15.0 | 18.6 | 5.8 | - | 2.4 |
| LB-F heuristic | 27788 | 2415 | 47.2 | - | 13.4 | 17.2 | 1.2 | 18.7 | - | - | - | 2.4 |
| LB-F Q-learning | 38928 | 3368 | 33.7 | - | 9.9 | 13.8 | 0.9 | 14.9 | 18.3 | 6.1 | - | 2.5 |

### 4x4, chiplet (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16932 | 1796 | 64.5 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.6 |
| DeFT | 17846 | 1856 | 61.2 | - | 14.8 | 17.2 | 0.8 | - | 2.9 | - | 0.3 | 2.7 |
| DeFT, 14 scenarios | 24649 | 2640 | 44.3 | - | 10.7 | 12.5 | 0.6 | - | 29.4 | - | 0.4 | 2.1 |
| MTR | 21814 | 2310 | 50.1 | - | 12.1 | 14.1 | 0.6 | - | 21.0 | - | 0.0 | 2.1 |
| RC | 17261 | 1796 | 63.3 | - | 15.3 | 17.8 | 0.7 | - | - | - | 0.1 | 2.8 |
| DeFT-Dis | 18053 | 1860 | 60.5 | - | 14.6 | 17.0 | 0.8 | - | 3.7 | - | 0.7 | 2.7 |
| LB-I heuristic | 18130 | 1890 | 60.2 | - | 14.6 | 17.0 | 0.8 | - | 4.6 | - | 0.2 | 2.7 |
| LB-I Q-learning | 18130 | 1890 | 60.2 | - | 14.6 | 17.0 | 0.8 | - | 4.6 | - | 0.2 | 2.7 |
| LB-F heuristic | 25495 | 2044 | 42.8 | - | 11.2 | 14.1 | 1.4 | 24.8 | 2.6 | - | 0.1 | 2.9 |
| LB-F Q-learning | 42164 | 3539 | 25.9 | - | 7.0 | 9.8 | 0.8 | 16.1 | 32.3 | 5.7 | 0.1 | 2.4 |

### 4x4, boundary (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21095 | 2185 | 62.1 | - | 16.4 | 19.7 | 0.4 | - | - | - | - | 1.4 |
| DeFT | 22008 | 2245 | 59.6 | - | 15.7 | 18.8 | 0.8 | - | 2.4 | - | 0.2 | 2.5 |
| DeFT, 14 scenarios | 28810 | 3029 | 45.5 | - | 12.0 | 14.4 | 0.6 | - | 25.2 | - | 0.3 | 2.0 |
| MTR | 26352 | 2739 | 49.7 | - | 13.1 | 15.8 | 0.6 | - | 18.7 | - | 0.0 | 2.1 |
| RC | 30951 | 3315 | 42.3 | 30.3 | 11.2 | 13.4 | 0.5 | - | - | - | 0.1 | 2.2 |
| DeFT-Dis | 22230 | 2249 | 59.0 | - | 15.5 | 18.7 | 0.8 | - | 3.0 | - | 0.5 | 2.5 |
| LB-I heuristic | 22330 | 2279 | 58.7 | - | 15.5 | 18.7 | 0.8 | - | 3.7 | - | 0.2 | 2.5 |
| LB-I Q-learning | 23260 | 2377 | 56.3 | - | 14.8 | 17.8 | 0.8 | 4.0 | 3.5 | - | 0.1 | 2.5 |
| LB-F heuristic | 30944 | 2480 | 42.4 | - | 12.0 | 15.4 | 1.2 | 24.1 | 2.1 | - | 0.1 | 2.8 |
| LB-F Q-learning | 47818 | 3993 | 27.4 | - | 8.0 | 11.3 | 0.7 | 16.7 | 28.4 | 5.0 | 0.1 | 2.4 |

### 4x4, interposer (5 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 16920 | 1795 | 64.6 | - | 15.6 | 18.2 | 0.1 | - | - | - | - | 1.6 |
| DeFT | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| DeFT, 14 scenarios | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| MTR | 16985 | 1795 | 64.3 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.9 |
| RC | 16985 | 1795 | 64.3 | - | 15.6 | 18.1 | 0.2 | - | - | - | - | 1.9 |
| DeFT-Dis | 17017 | 1795 | 64.2 | - | 15.5 | 18.1 | 0.3 | - | - | - | - | 1.9 |
| LB-I heuristic | 22786 | 1939 | 47.9 | - | 12.4 | 14.7 | 1.4 | 21.2 | - | - | - | 2.4 |
| LB-I Q-learning | 39504 | 3434 | 27.6 | - | 7.4 | 9.8 | 0.8 | 13.9 | 32.8 | 5.7 | - | 2.1 |
| LB-F heuristic | 23316 | 1979 | 46.8 | - | 12.3 | 15.4 | 1.4 | 21.6 | - | - | - | 2.5 |
| LB-F Q-learning | 40103 | 3474 | 27.2 | - | 7.4 | 10.3 | 0.8 | 14.0 | 32.3 | 6.0 | - | 2.1 |

### 4x4, interposer + VL (6 ports)

| method | area | FF | buffers | RC buffer | crossbar | allocators | routing unit | selection | tables | Q update + feedback regs | NI logic | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference (XY, no VNs) | 21027 | 2184 | 62.3 | - | 16.4 | 19.8 | 0.1 | - | - | - | - | 1.4 |
| DeFT | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| DeFT, 14 scenarios | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| MTR | 21105 | 2184 | 62.1 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.7 |
| RC | 21105 | 2184 | 62.1 | - | 16.4 | 19.7 | 0.2 | - | - | - | - | 1.7 |
| DeFT-Dis | 21127 | 2184 | 62.0 | - | 16.3 | 19.6 | 0.3 | - | - | - | - | 1.7 |
| LB-I heuristic | 27325 | 2367 | 48.0 | - | 13.4 | 16.4 | 1.2 | 18.8 | - | - | - | 2.3 |
| LB-I Q-learning | 44097 | 3880 | 29.7 | - | 8.6 | 11.5 | 0.8 | 13.0 | 29.3 | 5.1 | - | 2.1 |
| LB-F heuristic | 27924 | 2415 | 46.9 | - | 13.3 | 17.1 | 1.2 | 19.1 | - | - | - | 2.4 |
| LB-F Q-learning | 45074 | 3928 | 29.1 | - | 8.5 | 12.0 | 0.7 | 13.6 | 28.7 | 5.3 | - | 2.1 |

