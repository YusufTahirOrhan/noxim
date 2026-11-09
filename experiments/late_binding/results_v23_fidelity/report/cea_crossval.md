# Part C: cross-validation against CEA's noxim3.5d-sop (cea_crossval.py report)

Configuration: `cea/deft_2x2_rr.yaml`, `cea/deft_2x2_bl.yaml`, `cea/config_notes.md`. Uniform traffic, fault-free 2x2 system. Both simulators record the head latency from the generation timestamp (identical `Stats::receivedFlit`). Accepted throughput per chiplet router = CEA network throughput / 64.

## Saturation load (D1 rule: L0 at 0.0002, Lsat = largest swept rate before the latency first exceeds 3 x L0; seed 101)

| simulator | L0 | Lsat | grid | Lsat / ours (DeFT-B) |
|---|---|---|---|---|
| CEA DeFT (rr) | 19.5 | 0.0115 | 0.0005 | 1.05 |
| CEA DeFT (bl) | 19.5 | 0.011 | 0.0005 | 1.00 |
| ours, DeFT-B (pipe_all 0) | 19.2 | 0.011 | 0.0005 | 1.00 |
| ours, DeFT-P (D1) | 17.8 | 0.0115 | 0.0005 | 1.05 |

## Latency and accepted throughput against load (9 loads of DeFT-P's ladder; geometric mean of seeds 91-93)

| load (x Lsat) | rate | CEA rr: lat | CEA bl: lat | ours DeFT-B: lat | ours DeFT-P: lat | CEA rr: acc | CEA bl: acc | ours DeFT-B: acc | ours DeFT-P: acc |
|---|---|---|---|---|---|---|---|---|---|
| 0.2 | 0.0025 | 21.9 | 22.1 | 21.9 | 20.0 | 0.0205 | 0.0205 | 0.0204 | 0.0205 |
| 0.5 | 0.0060 | 27.6 | 28.0 | 28.2 | 25.4 | 0.0488 | 0.0488 | 0.0490 | 0.0490 |
| 0.8 | 0.0090 | 37.1 | 38.3 | 39.4 | 34.1 | 0.0734 | 0.0734 | 0.0735 | 0.0735 |
| 1.0 | 0.0115 | 56.9 | 58.4 | 57.5 | 49.6 | 0.0943 | 0.0944 | 0.0935 | 0.0937 |
| 1.2 | 0.0140 | 215.7 | 185.1 | 205.1 | 164.2 | 0.1127 | 0.1135 | 0.1110 | 0.1123 |
| 1.4 | 0.0160 | 663.7 | 649.2 | 582.8 | 503.2 | 0.1154 | 0.1154 | 0.1135 | 0.1176 |
| 1.6 | 0.0185 | 1255.9 | 1273.6 | 1030.4 | 959.1 | 0.1159 | 0.1150 | 0.1141 | 0.1182 |
| 2.0 | 0.0230 | 2025.7 | 2120.3 | 1861.5 | 1779.5 | 0.1145 | 0.1131 | 0.1139 | 0.1166 |
| 2.4 | 0.0275 | 2555.9 | 2655.3 | 2466.3 | 2392.6 | 0.1160 | 0.1145 | 0.1146 | 0.1176 |

## Verdict

* Saturation load: CEA (rr) 0.0115 against ours (DeFT-B) 0.011, deviation 5 % (within the 15 % band). CEA (bl): 0.011.
* Curve shape: CEA (rr) / ours (DeFT-B) latency ratio over the 9 loads 1.00, 0.98, 0.94, 0.99, 1.05, 1.14, 1.22, 1.09, 1.04; both curves are monotone in load up to saturation.
* The comparison validates the DeFT mechanics shared by both simulators (VN rules, round-robin, exit and entry tables) under the same topology, buffers and traffic. It does not validate the paper's per-destination-router entry (not expressible in CEA's format) nor our late-binding modes.
