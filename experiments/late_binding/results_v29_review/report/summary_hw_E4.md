# v29 E4: power (report_v29_hw.py e4)

OpenSTA `report_power` on the flattened netlists of the 4x4 routers (NanGate45 typical, 1 ns clock, the netlists of E2 and E3): DeFT's four routers, the main
row's (its chiplet routers are the routers of round 18 with the exit LUT; its interposer routers have one register in the decision unit, after M) and the
interposer routers of the two variants of E2.

**Limits.** Before layout: no wire capacitance, no clock tree, no clock gating, ideal clock. The simulation of a netlist has zero delays, so no glitch is
counted. The library is the typical corner of a 45 nm teaching library. The figures compare designs within this flow; they are not the power of a chip.

## E4.1 The load a router carries (`hw/port_loads.csv`)

Counted by the instrumented copy of the simulator in the measured window (4x4, uniform traffic, pipe_all 2, seed 1; statistics byte-identical to bin/noxim):
flits per cycle on a mesh input (mean of the four ports and of the routers of the type), from the processing element and from the vertical link; the share
of the flits on VC 1; the mean stay of a flit in an input buffer (cycles).

| row | load | router | routers | mesh input | from the PE | from the vertical link | VC 1 share (mesh, vertical) | stay (mesh, vertical) |
|---|---|---|---|---|---|---|---|---|
| DeFT | 0.5 x Lsat (0.004) | chip5 | 192 | 0.0086 | 0.0315 | 0.0000 | 0.93, 0.00 | 2.93, 0.00 |
| DeFT | 0.5 x Lsat (0.004) | chip6 | 64 | 0.0235 | 0.0315 | 0.1187 | 0.02, 0.50 | 4.75, 3.06 |
| DeFT | 0.5 x Lsat (0.004) | ipos5 | 192 | 0.0828 | 0.0000 | 0.0000 | 0.50, 0.00 | 3.45, 0.00 |
| DeFT | 0.5 x Lsat (0.004) | ipos6 | 64 | 0.0836 | 0.0000 | 0.1188 | 0.50, 0.50 | 3.77, 3.93 |
| DeFT | 1.0 x Lsat (0.008) | chip5 | 192 | 0.0175 | 0.0633 | 0.0000 | 0.93, 0.00 | 2.78, 0.00 |
| DeFT | 1.0 x Lsat (0.008) | chip6 | 64 | 0.0471 | 0.0641 | 0.2380 | 0.03, 0.49 | 11.19, 3.16 |
| DeFT | 1.0 x Lsat (0.008) | ipos5 | 192 | 0.1655 | 0.0000 | 0.0000 | 0.49, 0.00 | 6.36, 0.00 |
| DeFT | 1.0 x Lsat (0.008) | ipos6 | 64 | 0.1674 | 0.0000 | 0.2385 | 0.49, 0.49 | 6.97, 8.53 |
| main | 0.5 x Lsat (0.004) | chip5 | 192 | 0.0169 | 0.0315 | 0.0000 | 0.96, 0.00 | 3.11, 0.00 |
| main | 0.5 x Lsat (0.004) | chip6 | 64 | 0.0272 | 0.0315 | 0.1187 | 0.16, 0.50 | 4.42, 3.22 |
| main | 0.5 x Lsat (0.004) | ipos5 | 192 | 0.0747 | 0.0000 | 0.0000 | 0.50, 0.00 | 3.34, 0.00 |
| main | 0.5 x Lsat (0.004) | ipos6 | 64 | 0.0761 | 0.0000 | 0.1188 | 0.50, 0.50 | 3.73, 3.64 |
| main | 1.0 x Lsat (0.008) | chip5 | 192 | 0.0365 | 0.0633 | 0.0000 | 0.97, 0.00 | 3.37, 0.00 |
| main | 1.0 x Lsat (0.008) | chip6 | 64 | 0.0567 | 0.0640 | 0.2381 | 0.19, 0.50 | 7.21, 3.63 |
| main | 1.0 x Lsat (0.008) | ipos5 | 192 | 0.1559 | 0.0000 | 0.0000 | 0.50, 0.00 | 4.38, 0.00 |
| main | 1.0 x Lsat (0.008) | ipos6 | 64 | 0.1577 | 0.0000 | 0.2386 | 0.50, 0.50 | 5.49, 5.33 |
| noVLrep | 0.5 x Lsat (0.004) | chip5 | 192 | 0.0172 | 0.0315 | 0.0000 | 0.96, 0.00 | 3.13, 0.00 |
| noVLrep | 0.5 x Lsat (0.004) | chip6 | 64 | 0.0273 | 0.0315 | 0.1187 | 0.16, 0.50 | 4.41, 3.25 |
| noVLrep | 0.5 x Lsat (0.004) | ipos5 | 192 | 0.0745 | 0.0000 | 0.0000 | 0.50, 0.00 | 3.35, 0.00 |
| noVLrep | 0.5 x Lsat (0.004) | ipos6 | 64 | 0.0759 | 0.0000 | 0.1188 | 0.50, 0.50 | 3.76, 3.65 |
| noVLrep | 1.0 x Lsat (0.008) | chip5 | 192 | 0.0368 | 0.0633 | 0.0000 | 0.97, 0.00 | 3.37, 0.00 |
| noVLrep | 1.0 x Lsat (0.008) | chip6 | 64 | 0.0569 | 0.0640 | 0.2381 | 0.19, 0.50 | 7.16, 3.64 |
| noVLrep | 1.0 x Lsat (0.008) | ipos5 | 192 | 0.1556 | 0.0000 | 0.0000 | 0.50, 0.00 | 4.37, 0.00 |
| noVLrep | 1.0 x Lsat (0.008) | ipos6 | 64 | 0.1573 | 0.0000 | 0.2386 | 0.50, 0.50 | 5.52, 5.28 |
| noLA | 0.5 x Lsat (0.004) | chip5 | 192 | 0.0170 | 0.0315 | 0.0000 | 0.96, 0.00 | 3.10, 0.00 |
| noLA | 0.5 x Lsat (0.004) | chip6 | 64 | 0.0271 | 0.0315 | 0.1188 | 0.15, 0.50 | 4.41, 3.21 |
| noLA | 0.5 x Lsat (0.004) | ipos5 | 192 | 0.0743 | 0.0000 | 0.0000 | 0.50, 0.00 | 3.38, 0.00 |
| noLA | 0.5 x Lsat (0.004) | ipos6 | 64 | 0.0757 | 0.0000 | 0.1188 | 0.50, 0.50 | 3.80, 3.66 |
| noLA | 1.0 x Lsat (0.008) | chip5 | 192 | 0.0359 | 0.0633 | 0.0000 | 0.97, 0.00 | 3.32, 0.00 |
| noLA | 1.0 x Lsat (0.008) | chip6 | 64 | 0.0561 | 0.0640 | 0.2381 | 0.18, 0.50 | 7.25, 3.65 |
| noLA | 1.0 x Lsat (0.008) | ipos5 | 192 | 0.1550 | 0.0000 | 0.0000 | 0.50, 0.00 | 4.64, 0.00 |
| noLA | 1.0 x Lsat (0.008) | ipos6 | 64 | 0.1571 | 0.0000 | 0.2386 | 0.50, 0.50 | 5.73, 5.38 |

## E4.2 The bench carries that load (`hw/tb/tb_act18.v`, `tb_act25.v`)

Random 8-flit packets at these rates per port, with the measured share of heads that end at the router or take its vertical link, credits after the measured
stay; calibrated on the RTL until every rate is within 3 % of the simulator's (or the closest of ten tries). The netlist is then simulated with the same
stimulus (2,000 + 10,000 cycles; the VCD holds the 10,000) and must print the same result line as the RTL.

| design | router | load | flits per cycle: mesh input, PE, vertical in, vertical out, to the PE (simulator -> bench) | tries | netlist = RTL | nets annotated |
|---|---|---|---|---|---|---|
| DeFT | chip5 | 0.5 x Lsat | 0.0086 -> 0.0085, 0.0315 -> 0.0293, -, -, 0.0315 -> 0.0313 | 10 | yes | vcd 33941 unannotated 0 |
| DeFT | chip5 | 1.0 x Lsat | 0.0175 -> 0.0173, 0.0633 -> 0.0611, -, -, 0.0633 -> 0.0613 | 10 | yes | vcd 33941 unannotated 0 |
| main | chip5 | 0.5 x Lsat | 0.0169 -> 0.0168, 0.0315 -> 0.0313, -, -, 0.0315 -> 0.0313 | 3 | yes | vcd 34267 unannotated 0 |
| main | chip5 | 1.0 x Lsat | 0.0365 -> 0.0382, 0.0633 -> 0.0627, -, -, 0.0633 -> 0.0653 | 10 | yes | vcd 34267 unannotated 0 |
| DeFT | chip6 | 0.5 x Lsat | 0.0235 -> 0.0228, 0.0315 -> 0.0327, 0.1187 -> 0.1120, 0.1188 -> 0.1113, 0.0315 -> 0.0313 | 10 | yes | vcd 41911 unannotated 0 |
| DeFT | chip6 | 1.0 x Lsat | 0.0471 -> 0.0473, 0.0641 -> 0.0671, 0.2380 -> 0.2340, 0.2385 -> 0.2234, 0.0641 -> 0.0627 | 10 | yes | vcd 41911 unannotated 0 |
| main | chip6 | 0.5 x Lsat | 0.0272 -> 0.0272, 0.0315 -> 0.0307, 0.1187 -> 0.1140, 0.1188 -> 0.1150, 0.0315 -> 0.0313 | 10 | yes | vcd 42576 unannotated 0 |
| main | chip6 | 1.0 x Lsat | 0.0567 -> 0.0527, 0.0640 -> 0.0607, 0.2381 -> 0.2327, 0.2386 -> 0.2231, 0.0640 -> 0.0593 | 10 | yes | vcd 42576 unannotated 0 |
| DeFT | ipos5 | 0.5 x Lsat | 0.0828 -> 0.0820, -, -, -, - | 2 | yes | vcd 33328 unannotated 0 |
| DeFT | ipos5 | 1.0 x Lsat | 0.1655 -> 0.1653, -, -, -, - | 3 | yes | vcd 33328 unannotated 0 |
| main | ipos5 | 0.5 x Lsat | 0.0747 -> 0.0755, -, -, -, - | 1 | yes | vcd 36564 unannotated 0 |
| main | ipos5 | 1.0 x Lsat | 0.1559 -> 0.1568, -, -, -, - | 2 | yes | vcd 36564 unannotated 0 |
| noVLrep | ipos5 | 0.5 x Lsat | 0.0745 -> 0.0743, -, -, -, - | 2 | yes | vcd 36564 unannotated 0 |
| noVLrep | ipos5 | 1.0 x Lsat | 0.1556 -> 0.1552, -, -, -, - | 2 | yes | vcd 36564 unannotated 0 |
| noLA | ipos5 | 0.5 x Lsat | 0.0743 -> 0.0747, -, -, -, - | 1 | yes | vcd 34847 unannotated 0 |
| noLA | ipos5 | 1.0 x Lsat | 0.1550 -> 0.1517, -, -, -, - | 1 | yes | vcd 34847 unannotated 0 |
| DeFT | ipos6 | 0.5 x Lsat | 0.0836 -> 0.0823, -, 0.1188 -> 0.1207, 0.1187 -> 0.1187, - | 1 | yes | vcd 42389 unannotated 0 |
| DeFT | ipos6 | 1.0 x Lsat | 0.1674 -> 0.1637, -, 0.2385 -> 0.2387, 0.2380 -> 0.2333, - | 4 | yes | vcd 42389 unannotated 0 |
| main | ipos6 | 0.5 x Lsat | 0.0761 -> 0.0763, -, 0.1188 -> 0.1193, 0.1187 -> 0.1213, - | 5 | yes | vcd 50691 unannotated 0 |
| main | ipos6 | 1.0 x Lsat | 0.1577 -> 0.1587, -, 0.2386 -> 0.2401, 0.2381 -> 0.2372, - | 9 | yes | vcd 50691 unannotated 0 |
| noVLrep | ipos6 | 0.5 x Lsat | 0.0760 -> 0.0749, -, 0.1188 -> 0.1200, 0.1187 -> 0.1180, - | 3 | yes | vcd 50047 unannotated 0 |
| noVLrep | ipos6 | 1.0 x Lsat | 0.1573 -> 0.1545, -, 0.2386 -> 0.2360, 0.2381 -> 0.2422, - | 1 | yes | vcd 50047 unannotated 0 |
| noLA | ipos6 | 0.5 x Lsat | 0.0757 -> 0.0752, -, 0.1188 -> 0.1186, 0.1187 -> 0.1160, - | 9 | yes | vcd 47224 unannotated 0 |
| noLA | ipos6 | 1.0 x Lsat | 0.1570 -> 0.1570, -, 0.2386 -> 0.2380, 0.2381 -> 0.2363, - | 5 | yes | vcd 47224 unannotated 0 |

## E4.3 Power per router (mW: internal / switching / leakage = total)

### default activity of the tool (0.1 transitions per clock period at every input)

| design | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) | system: average router | relative to DeFT |
|---|---|---|---|---|---|---|
| DeFT | 14.471 / 1.770 / 0.334 = 16.575 | 17.398 / 2.196 / 0.419 = 20.014 | 13.749 / 1.524 / 0.322 = 15.594 | 16.716 / 1.958 / 0.404 = 19.078 | 16.950 | 1.000 |
| main | 14.756 / 1.816 / 0.339 = 16.911 (1.020) | 17.586 / 2.177 / 0.413 = 20.175 (1.008) | 16.060 / 2.460 / 0.368 = 18.888 (1.211) | 20.485 / 3.750 / 0.489 = 24.724 (1.296) | 19.037 | 1.123 |
| noVLrep | (the main row's) | (the main row's) | 16.060 / 2.460 / 0.368 = 18.888 (1.211) | 20.362 / 3.653 / 0.482 = 24.497 (1.284) | 19.009 | 1.121 |
| noLA | (the main row's) | (the main row's) | 15.537 / 2.275 / 0.352 = 18.164 (1.165) | 19.764 / 3.408 / 0.466 = 23.638 (1.239) | 18.630 | 1.099 |

### default activity; reset, position and table inputs constant

| design | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) | system: average router | relative to DeFT |
|---|---|---|---|---|---|---|
| DeFT | 18.296 / 4.625 / 0.343 = 23.264 | 21.966 / 5.632 / 0.429 = 28.027 | 17.375 / 4.391 / 0.332 = 22.099 | 21.122 / 5.490 / 0.418 = 27.030 | 23.893 | 1.000 |
| main | 18.315 / 4.537 / 0.348 = 23.199 (0.997) | 22.089 / 5.612 / 0.425 = 28.127 (1.004) | 19.439 / 4.900 / 0.376 = 24.715 (1.118) | 24.663 / 6.963 / 0.500 = 32.126 (1.189) | 25.499 | 1.067 |
| noVLrep | (the main row's) | (the main row's) | 19.439 / 4.900 / 0.376 = 24.715 (1.118) | 24.674 / 6.971 / 0.493 = 32.138 (1.189) | 25.501 | 1.067 |
| noLA | (the main row's) | (the main row's) | 18.928 / 4.804 / 0.361 = 24.094 (1.090) | 24.181 / 6.829 / 0.477 = 31.488 (1.165) | 25.187 | 1.054 |

### simulation of the netlist at the load of 0.5 x Lsat

| design | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) | system: average router | relative to DeFT |
|---|---|---|---|---|---|---|
| DeFT | 10.885 / 0.040 / 0.334 = 11.259 | 12.499 / 0.145 / 0.419 = 13.063 | 9.660 / 0.206 / 0.321 = 10.186 | 11.511 / 0.305 / 0.406 = 12.223 | 11.203 | 1.000 |
| main | 10.730 / 0.060 / 0.339 = 11.128 (0.988) | 12.266 / 0.160 / 0.418 = 12.844 (0.983) | 10.944 / 0.257 / 0.368 = 11.569 (1.136) | 13.378 / 0.430 / 0.488 = 14.296 (1.170) | 11.904 | 1.063 |
| noVLrep | (the main row's) | (the main row's) | 10.943 / 0.254 / 0.368 = 11.565 (1.135) | 13.296 / 0.421 / 0.482 = 14.199 (1.162) | 11.890 | 1.061 |
| noLA | (the main row's) | (the main row's) | 10.388 / 0.230 / 0.354 = 10.972 (1.077) | 12.665 / 0.371 / 0.469 = 13.505 (1.105) | 11.581 | 1.034 |

### simulation of the netlist at the load of 1.0 x Lsat

| design | chiplet (5 ports) | boundary (6 ports) | interposer (5 ports) | interposer + VL (6 ports) | system: average router | relative to DeFT |
|---|---|---|---|---|---|---|
| DeFT | 10.280 / 0.079 / 0.335 = 10.694 | 12.255 / 0.324 / 0.421 = 13.000 | 9.774 / 0.435 / 0.322 = 10.531 | 11.697 / 0.639 / 0.407 = 12.743 | 11.177 | 1.000 |
| main | 10.351 / 0.135 / 0.341 = 10.827 (1.012) | 12.113 / 0.340 / 0.418 = 12.870 (0.990) | 11.092 / 0.505 / 0.369 = 11.966 (1.136) | 13.671 / 0.878 / 0.489 = 15.039 (1.180) | 12.036 | 1.077 |
| noVLrep | (the main row's) | (the main row's) | 11.090 / 0.502 / 0.369 = 11.960 (1.136) | 13.596 / 0.850 / 0.483 = 14.929 (1.172) | 12.020 | 1.075 |
| noLA | (the main row's) | (the main row's) | 10.503 / 0.442 / 0.355 = 11.299 (1.073) | 12.934 / 0.750 / 0.469 = 14.153 (1.111) | 11.675 | 1.045 |

In brackets: relative to DeFT's router of the same type. System: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers per chiplet; the chiplet
routers of a variant are the main row's.

