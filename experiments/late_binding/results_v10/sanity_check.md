# Sanity check against the DeFT paper (v10 A5): 2x2 uniform, fault-free

Mean over seeds 1001-1003 (not evaluation seeds). Load = multiple of DeFT(rho*)'s Lsat (v5 load points).

| load | rate | DeFT(rho*) latency | MTR latency | RC latency | DeFT accepted | MTR accepted | RC accepted |
|---|---|---|---|---|---|---|---|
| 0.8 | 0.009 | 38.0 | 33.6 | 33.7 | 0.0722 | 0.0721 | 0.0724 |
| 1.0 | 0.011 | 59.0 | 44.5 | 42.2 | 0.0881 | 0.0882 | 0.0884 |
| 1.2 | 0.013 | 179.4 | 80.4 | 69.2 | 0.1019 | 0.1044 | 0.1055 |
| 1.4 | 0.0155 | 746.8 | 401.7 | 358.4 | 0.1050 | 0.1165 | 0.1183 |
| 1.6 | 0.0175 | 1332.0 | 950.8 | 885.6 | 0.1034 | 0.1176 | 0.1196 |

## Result: the expectation is not met, and why

DeFT(rho*) has **higher** latency than MTR and RC at every load, and lower accepted throughput beyond the knee. The
DeFT paper reports the opposite. The implementations were investigated before Part B (`sanity_diag_v10.py`, same
cells and seeds; `sanity_diag.json`):

| configuration (2x2 uniform) | 0.8 x Lsat | 1.0 | 1.2 | 1.4 | accepted at 1.2 | VL max/mean at 1.0 |
|---|---|---|---|---|---|---|
| DeFT(rho*) (DeFT VNs) | 38.0 | 59.0 | 179.4 | 746.8 | 0.1019 | 1.08 |
| MTR (no VN rules, both VCs) | 33.6 | 44.5 | 80.4 | 401.7 | 0.1044 | 1.06 |
| RC (no VN rules, RC buffer) | 33.7 | 42.2 | 69.2 | 358.4 | 0.1055 | 1.08 |
| *MTR routes with DeFT's VN rules* | 36.6 | 57.0 | 211.6 | 779.2 | 0.1024 | 1.07 |
| *DeFT's LUT routes without VN rules* | 36.3 | 46.3 | 49.4 | 229.1 | **0.0047 (deadlock)** | 1.10 |
| DeFT-Dis (DeFT VNs) | 35.1 | 57.3 | 195.1 | 859.3 | 0.1027 | 1.07 |
| *DeFT-Dis routes without VN rules, no RC buffer* | 32.6 | 41.7 | 77.8 | 139.5 (acc. 0.0129, deadlock) | 0.1043 | 1.08 |

Rows in italics are diagnostics only; without the VNs the DeFT relation is not deadlock-free in general.

**Findings:**
1. **The routes are not the cause.** With DeFT's VN rules applied to MTR's routes, MTR performs like DeFT (57.0 vs 59.0
   at 1.0 x Lsat, worse at 1.2). Load balance does not explain it either: VL use is equally balanced for all
   methods (max/mean 1.06-1.10).
2. **The cost is DeFT's VN-based deadlock avoidance.**
   - DeFT keeps an inter-chiplet packet in VN0 in the source chiplet. Under the F1 fix, VN1 is allowed at the source
     only when the packet exits through the source's own VL.
   - The packet then moves to VN1 for the Up link and the destination chiplet.
   - So each segment of an inter-chiplet path uses one of the two VCs. MTR (turn restrictions) and RC (injection
     control) keep both VCs available to every packet, as the task prescribes ("the VC is chosen as Noxim normally
     does").
3. **The VNs are needed.** Without them, DeFT's own LUT routes deadlock at 1.0-1.2 x Lsat (accepted throughput
   collapses), and RC's routes deadlock at 1.4 x Lsat without the RC buffer. The baselines are therefore not
   "missing" a safety mechanism: MTR's CDG is acyclic, and RC's buffer prevents the deadlock its routes otherwise
   show. All drain tests pass (`drain_summary.csv`).
4. **Possible reasons for the difference from the DeFT paper** (not testable here):
   - the paper's VC configuration for MTR and RC (the RC paper itself uses 2 VCs with 4-flit buffers);
   - DeFT's original source-VN rule, which allowed VN1 more often but was found unsafe (Finding F1);
   - simulator differences (Noxim has no router pipeline; the paper used a cycle-accurate pipeline model).

**Decision (conservative):** the baselines are kept as specified (equal buffering, no VN rules for MTR and RC). This
is the setting that does not favour our methods: our variants inherit DeFT's VN rules. Part B proceeds; the finding
is reported in FINDINGS.md.
