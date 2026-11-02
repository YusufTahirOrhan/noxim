# v17 findings: VC usage per link (Part I, descriptive)

**Sources:**
* Definitions: `DECISIONS.md`.
* Tables and figure: `report/summary.md`, `report/imbalance_vs_latency.{png,pdf}`.
* Data: `vc_runs.csv` (per run and link class), `run_summary.csv`. 270 of 270 runs, 0 dead-end events, no deadlock flag.

**Checks:**
* Option off: 84 / 84 stats files byte-identical to the 3ac1bae build (`regression.md`).
* Option on: 5 / 5 stats files byte-identical to the same run with it off (`oncheck.md`).
* VC draw for MTR and RC: uniform over the 2 VCs per packet, in the code (`DECISIONS.md`) and in the data (49:51 to 51:49 on every class and size).

All numbers below are at 1.0 x Lsat, the mean of seeds 41-43, unless stated otherwise. This round is descriptive, with no statistical test.

## Does the data support the explanation in the Context?
**Its core holds, with two corrections: the imbalance comes from the VN rules, but it is not the towards / away split on chiplet links that is largest, and imbalance alone does not predict latency.**

**1. The imbalance on chiplet links is much larger for DeFT, LB-I and LB-F than for MTR and RC: yes.**

| | 2x2 uniform | 2x2 hotspot | 3x3 uniform | 3x3 hotspot | 4x4 uniform | 4x4 hotspot |
|---|---|---|---|---|---|---|
| DeFT(rho*) | 0.66 | 0.69 | 0.74 | 0.79 | 0.78 | 0.82 |
| LB-I (CI_qlLA_G) | 0.67 | 0.70 | 0.79 | 0.82 | 0.82 | 0.86 |
| LB-F (FULL_qlLA_G) | 0.47 | 0.58 | 0.53 | 0.70 | 0.57 | 0.73 |
| MTR | 0.10 | 0.11 | 0.10 | 0.16 | 0.11 | 0.20 |
| RC | 0.10 | 0.12 | 0.12 | 0.16 | 0.13 | 0.22 |
| MTR routes + DeFT's VN rules | 0.74 | 0.74 | 0.89 | 0.90 | 0.94 | 0.94 |

VC imbalance over all chiplet links. The small values of MTR and RC are per-link sampling noise of a 50:50 draw; they rise where fewer packets cross a link.

**2. "MTR routes + DeFT VN rules" shows the imbalance too: yes, and more than DeFT on chiplet links.**
* Same routes, VN rules on: chiplet imbalance rises from 0.10-0.20 to 0.74-0.94.
* On the interposer and both VLs this configuration matches DeFT (0.73-0.76 and 1.00).
* Without VN rules, DeFT's own LUT routes (0.8 x Lsat only) are balanced like MTR: 0.09-0.19 per chiplet class, and no deadlock flag in these 18 runs. The sanity check found the collapse at 1.0-1.2 x Lsat.
* So the VN rules cause the imbalance, and the routes only shift it.

## What differs from the Context
**The towards / away split is only clean for routes that go to the nearest VL.**

| share of flits (VC0:VC1), range over sizes and patterns | towards VL | away from VL |
|---|---|---|
| MTR routes + DeFT VNs | 89:11 to 98:2 | 18:82 to 4:96 |
| DeFT-Dis | 89:11 to 98:2 | 23:77 to 6:94 |
| DeFT(rho*) | 67:33 to 76:24 | 11:89 to 3:97 |
| LB-I (CI_qlLA_G) | 78:22 to 83:17 | 14:86 to 3:97 |
| LB-F (FULL_qlLA_G) | 81:19 to 86:14 | 45:55 to 38:62 |

* **DeFT, towards VL:** only 67-76 % is VC0. The class is defined by the nearest VL, while the LUT often picks another one. So 20-28 % of the flits on these links are destination-phase packets in VC1 (`report/summary.md`, phase table).
* **LB-F, away from VL:** close to balanced (0.41-0.70), not mostly VC1. Late binding sends source-phase packets in VC0 away from the nearest VL.

**The largest imbalance is off the chiplets, which the Context does not mention.**

| VC0:VC1 | interposer | Down VL | Up VL |
|---|---|---|---|
| DeFT(rho*), DeFT-Dis, MTR routes + VNs, LB-I | 87:13 to 88:12 | 87:13 to 88:12 | 0:100 |
| LB-F | 100:0 | 100:0 | 0:100 |
| MTR, RC | 50:50 | 50:50 | 50:50 |

* **Why:** a packet in VN0 keeps VN0 across the interposer up to the Up link.
* **The 12-13 % in VC1** are the packets of boundary-router sources committed to their own VL (F1 fix): 4 of 16 sources x 1/2 round-robin = 12.5 %. LB-F has none, because a fault-free exit mask holds 4 VLs at injection.
* **Buffers:** "half of the buffers idle" is literal on the Up VL, where the VC0 occupancy is 0.00. On the interposer, DeFT's VC1 buffers hold 0.01-0.05 flits against 0.12-0.47 in VC0, and LB-F's hold 0.00.

**Where the wait appears: the VLs, mostly as "VC held".** VC-wait cycles per flit, uniform traffic, 2x2 / 3x3 / 4x4:

| | chiplet towards | chiplet away | interposer | Down VL | Up VL |
|---|---|---|---|---|---|
| DeFT(rho*) | 0.11 / 0.15 / 0.12 | 0.07 / 0.04 / 0.03 | 0.18 / 0.24 / 0.21 | **1.17 / 1.58 / 1.17** | 0.51 / 0.54 / 0.39 |
| MTR routes + VNs | 0.16 / 0.30 / 0.12 | 0.04 / 0.02 / 0.01 | 0.21 / 0.28 / 0.18 | **1.23 / 2.03 / 0.90** | 0.68 / 0.61 / 0.45 |
| MTR | 0.06 / 0.07 / 0.04 | 0.06 / 0.02 / 0.01 | 0.14 / 0.19 / 0.14 | **0.64 / 0.79 / 0.49** | 0.36 / 0.34 / 0.24 |
| RC | 0.02 / 0.01 / 0.00 | 0.05 / 0.02 / 0.01 | 0.15 / 0.19 / 0.15 | **0.82 / 0.95 / 0.60** | 0.35 / 0.34 / 0.25 |

* On MTR's routes, the VN rules raise the Down VL wait by a factor of 1.8-2.6 and the Up VL wait by 1.8-1.9.
* On the Down VL, most of this wait is "VC held by another packet", not "no credit": 80-94 % for DeFT, 88-94 % for MTR routes + VNs, 95-99 % for LB-I and LB-F, all patterns (`report/summary.md`). This is what a link with one usable VC should show. MTR (84-94 %) and RC (68-92 %) show it too, at about half the level.

## Imbalance and latency (figure)
**Imbalance alone does not predict latency.**
* **Same routes, imbalance matters.** MTR routes with VN rules against MTR:
  - uniform, 1.0 x Lsat: 57 vs 44, 110 vs 64, 75 vs 65 cycles on 2x2 / 3x3 / 4x4;
  - hotspot, 2x2 and 3x3: 265 vs 144, 436 vs 239;
  - 4x4 hotspot is the exception (228 vs 258). Both saturate there: accepted throughput is 0.013-0.014 against DeFT's 0.017.
* **Different routes, the route choice can outweigh it.**
  - LB-I's imbalance is similar to DeFT's and LB-F's is lower on chiplet links, yet at 1.0 x Lsat one of the two has the lowest latency in every cell.
  - Under hotspot, MTR and RC are balanced and still slower than DeFT, LB-I and LB-F (81-274 vs 40-103 cycles at 1.0 x Lsat). Their Down VL wait of 1.5-15.6 cycles per flit shows the hot VLs, a route effect.

## Limits of this round
* The loads are 0.8 and 1.0 x Lsat. Accepted throughput is equal across methods on uniform traffic there. **This round does not measure saturation throughput directly**, so the 3-11 % gap of v10 is explained through the waits above, not reproduced.
* Three seeds, no intervals. Differences of a few percent between methods should not be read from these tables.
* The deadlock flag detects a collapse of accepted flits below 50 % of DeFT, not a cyclic wait. `DeFT_LUT_noVN` was run at 0.8 x Lsat only, as requested.

## RC buffer (`report/summary.md`)
* Occupancy per boundary router, capacity 32 flits: mean 0.5-7.4 flits, 0.25-1.14 slots. Every scenario reaches 4 slots at peak, and 11 of 12 reach 32 flits.
* Mean permission wait per outbound packet: 1.0-2.3 cycles on uniform; on hotspot 1.0-57.7 cycles, rising with load and size (57.7 on 4x4 at 1.0 x Lsat).

## Conclusion for the paper
The measured explanation for MTR and RC beating DeFT at equal VCs:
* DeFT's VN rules confine each segment of an inter-chiplet path to one VC. The strongest effect is on the interposer (87-100 % in one VC) and on the VLs (Up VL 100 % VC1), not on the chiplet links alone.
* The cost shows mainly as VC-held waits at the Down and Up VLs.
* With the same routes, adding the rules makes MTR about as slow as DeFT, or slower.
* The late-binding variants inherit the rules and pay the same imbalance, but their route adaptivity more than compensates in latency.
