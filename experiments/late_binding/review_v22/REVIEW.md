# Review v22: independent review of the simulator, the baselines and the analysis

Reviewed: branch `feat/parametric-topology` at 780fa6b (`bin/noxim` md5 a82a1590224f4c2ed253c256c0285792, the v21 binary).
Sources checked against: Taheri et al., DATE 2022 (arXiv 2112.09234v1, Section III, Algorithm 1, Theorems III.1-III.4,
Section IV); Yin et al., ISCA 2018 (MTR); Majumder et al., IEEE TC 2021 / arXiv 1910.04882 (RC); CEA LIST's Noxim 3.5D
(`D3vKrish/noxim3.5d-sop`, `Routing_DEFT.cpp`, `RoutingMultiNoC.cpp`, read only). Everything written by this review is in this
folder; nothing under `src/`, the scripts or any `results_*` folder was changed. The confirming runs used a patched copy of the
sources built in a separate directory (`~/lbrev/noxim`, patch in `patch_review.py`); with its options off that binary reproduces
`bin/noxim` byte for byte (`regression.md`).

## 1. Summary

1. **The Up vertical link is modelled in VN1 only, which is not DeFT's rule.** Algorithm 1 and Theorem III.4 of the paper switch a
   VN0 packet to VN1 at the destination chiplet's boundary router, after the Up link; the CEA implementation does the same. This code
   (`src/DeftVirtualNetwork.cpp:305-311`) forces VN1 on the Up link itself, so every Up VL runs with one usable VC (measured
   0:100). The paper's rule is deadlock-free in the repository's own model (`vn_up_check.md`). Re-running DeFT with the paper's
   Up rule and a free-VC round-robin raises its saturation throughput by 6.7 / 7.2 / 3.7 % (2x2 / 3x3 / 4x4, uniform) and lowers
   its latency at 1.0 × Lsat by 4-8 %, most of the 5-10 % throughput gap to MTR and RC; with the paper-style entry selection as
   well, DeFT is within about 2 points of MTR in throughput and latency on every size (§5.1).
2. **The DeFT LUT's second (entry) selection is not the paper's.** The paper selects the entry VL per destination router, by the
   distance inside the destination chiplet (Eq. 4, "packets headed for the destination-chiplet routers"); the generator keys it by
   source router and interposer distance (`other/deft_vl_lut_generator.py:433-451`). The repository's own v19 data show the two
   choices differ by factors per traffic pattern (chipperm: LAT 85.6 vs 35.3 cycles; hotspot: 57.8 vs 315), so the DeFT baseline
   of every round is a repository-specific variant, not the paper's DeFT.
3. **The simulator charges late binding N extra cycles against a baseline router that is idealised in two ways.** Every router
   routes in one cycle, and Noxim's alternating-bit handshake makes a hop cost 2 cycles for the head while a link carries one flit
   per two cycles (measured here). N = 2-3 therefore adds 100-150 % to the per-hop head latency of a baseline that a real router
   (2-4 stages) would not have. Charging every router a uniform 2-cycle head delay (and the fast selection its N_fast on top)
   halves the fast selection's low-load penalty on 2x2 uniform (+33 % → +14 %), so v21's "+23 to +67 % at low load" is tied to
   the one-cycle baseline and should be read as an upper bound.

**Can the main comparisons be trusted as they stand?** The analysis scripts are correct: the v19 primary table (60 tests) and the
v21 rows recompute to within 0.005 percentage points with identical verdicts, Holm is implemented correctly, and the
pre-registrations were followed. The late-binding relation matches its stated definitions. What cannot be trusted as stated is
the DeFT baseline: items 1 and 2 above make "DeFT" in rounds v1-v21 a stricter and differently tuned algorithm than the paper's,
and the baselines MTR and RC are themselves modelled with a static per-packet VC (a handicap for them). The LB-vs-DeFT gains and
the "DeFT loses to MTR and RC" result should be re-run with the paper's Up-link rule before they are published; the LB-vs-MTR/RC
and the hardware conclusions stand with the modelling caveats of item 3.

## 2. Findings

| ID | Area | Severity | Finding and evidence | Expected effect on the results | Suggested fix or test | Confidence |
|---|---|---|---|---|---|---|
| R1 | 1 | **critical** | Up VL forced to VN1. `src/DeftVirtualNetwork.cpp:305-311` (`isInterposerToChiplet` → VN1) and the formal model (`formal/impl_relation_check.py:181`, `('U', here, 1)`). Paper: Algorithm 1 "Current router ∈ boundary routers … coming from the interposer: go to (remain in) VN.1" (boundary routers are chiplet routers, p. 2), Theorem III.4 "if a packet is in VN.0 … it can be switched to VN.1 to go from Up to Horizontal ports", Rule 2 presupposes VN0 packets at an Up port. CEA: `Routing_DEFT.cpp:158-185` assigns VN1 only when `dir_in == DIRECTION_DOWN` at the chiplet router; the interposer router's Up output keeps the VC (`RoutingMultiNoC.cpp:88-90`). Measured Up-VL split 0:100 with the repository rule, 50:50 with the paper's (§5.2); Up-VL VC-wait 1.09 → 0.26 cycles/flit. | Changes DeFT's own latency and throughput on every size, hence every LB-vs-DeFT effect (v1-v21) and the "DeFT below MTR/RC" check. Measured in §5.1 (uniform, fault-free, 2x2 / 3x3 / 4x4): the paper's Up rule alone gives THR +4.0 / +4.0 / +2.3 % and LAT @1.0 Lsat +2.4 / −2.0 / −6.9 %; with the free-VC round-robin (R2) as well THR +6.7 / +7.2 / +3.7 %, LAT −3.8 / −4.2 / −7.8 %, P99 −9 / −10 / −16 %, against MTR's THR +9.5 / +5.2 / +5.0 % over the repository's DeFT. | Make the Up output VN equal to the input VN and keep the VN1 assignment at the destination boundary router (one line, see `patch_review.py`); re-run the DeFT and LB baselines of v19/v21 with it (both rules are acyclic, `vn_up_check.md`). | high (deviation and direction, consistent on every seed and size), medium (exact size, 2-3 seeds) |
| R2 | 1 | major | Round-robin busy-VC semantics. The boundary counter is peeked in `selectOutputVirtualNetwork` and advanced only when the reservation succeeds (`Router.cpp:242-274`); a head whose counter VC is held waits for it even if the other VC is free, and so does every later head at that port. The paper only says "round-robin"; CEA toggles its per-(router, output) flag on every routing evaluation, so a blocked head tries the other VC the next cycle. | Idle Down-VL VCs under load. Measured in §5.1: the fallback alone gives THR +1.9 / +2.0 / +1.6 % (2x2 / 3x3 / 4x4) with latency changes within the 3-seed noise (+3.9 / +0.7 / +2.6 %); on top of the Up rule it adds 1-3 points of THR and turns the latency effect negative on every size. | Take the other VC when the counter's VC is held (`-deft_lb rr_fallback 1` in the patched copy), or state the chosen semantics as a modelling decision. | medium |
| R3 | 1 | minor | F1 source rule. Algorithm 1 gives every boundary-router source the round-robin VN; the code gives VN1 only when the packet is committed to the router's own VL (`DeftVirtualNetwork.cpp:72-104`). The paper's literal rule is unsafe: a VN1 packet whose exit is another VL must go Horizontal→Down, forbidden by Rule 3 (CEA asserts `vc_in != VN_1` there). In the repository's LUTs a boundary source never exits through another functional VL (0 of 48 / 288 / 960 boundary-source keys, `lut_path_analysis.py`), so F1 changes nothing for DeFT with its LUT; it forces VN0 for DeFT-Ran, XY-SP and the LB variants' boundary sources (12.5 % of the sources). | None for DeFT(rho*); a small VN0 bias for the others. | Document it as the paper's gap, not the code's. | high |
| R4 | 1 | major | LUT entry selection. Generator: `destination_demand_points` keys the entry by (source chiplet, source router), demand point = the source's exit VL on the interposer, distance = interposer distance (`other/deft_vl_lut_generator.py:433-451`; LUT metadata "interposer_context_assignment_without_destination_router_id"). Paper: the second selection "based on the packets headed for the destination-chiplet routers", distance D_r^v between a router and a VL "on the same chiplet" (Eq. 4), i.e. per destination router inside the destination chiplet. Fault-free mean path: LUT pair 10.58 / 12.79 / 15.28 hops (2x2 / 3x3 / 4x4) against 9.67 / 12.13 / 14.67 with the same exit and a destination-nearest entry, 8.79 / 11.22 / 13.74 minimal. The exit selection matches the paper (per source router, balanced, minimal distance; identical to the nearest-VL table). | The paper-style entry is exactly DeFT-Dis's entry in the fault-free case; v19 data (`results_v19_vnrr/eval_runs.csv`, seeds 61-70, 2x2): uniform THR 0.1074 vs 0.1056 and LAT 53.8 vs 57.0 in its favour, chipperm LAT 35.3 vs 85.6 and THR 0.0554 vs 0.0463 in its favour, hotspot LAT 315 vs 57.8 against it. The DeFT baseline's per-scenario results, and therefore the 11-scenario means of every round, depend on this choice. | Add a destination-router-keyed entry table (16 entries per chiplet and fault mask, as MTR's inbound table) and evaluate DeFT with the paper's two selections, or state in the paper that the entry rule is the repository's own. | high (deviation), medium (net effect on the means) |
| R5 | 1 | minor | Topology and setup. Interposer = footprint-sized mesh (8x8 for 2x2 chiplets, one interposer router under every chiplet router); the MTR and RC papers and the CEA DeFT configuration use a 4x4 interposer mesh (one router per boundary router); the DeFT paper does not state its size. VL slots N (1,0), E (3,1), S (2,3), W (0,2) are not verifiable against the paper (it only says "on the borders"). Packet 8 flits, buffer 4 flits, 2 VCs, flit 32 bits, uniform / localized 40 % / hotspot 3 × 10 % match Section IV-A; the paper's interposer sources (DRAM) are absent; the LUT holds one fault scenario per run (the paper stores 14 per chiplet, equivalent per mask). | Interposer paths are 1-7 hops instead of 1-3 for adjacent chiplets, for all methods alike; the balance between layers differs from the papers'. | State the interposer size as a design choice; a 4x4-interposer sensitivity run would settle whether the DeFT-vs-MTR/RC ordering depends on it. | medium |
| R6 | 2 | minor | MTR. Turn restrictions from an exhaustive search of the paper's objective (`formal/mtr_search.py`; optimum restricts inbound turns to the vertical ones, InR = 4/16 per boundary router, all outbound turns allowed), assignment by Sec. IV-C steps 1-3, routes checked acyclic and turn-legal (`mtr_cdg_check.md`). Deviations are documented (no placement search, interposer size). VCs: the packet keeps the VC drawn at injection on every hop (Noxim default); the MTR paper's Garnet allocates a free VC per hop. | MTR is handicapped, not favoured, relative to its paper; the restriction set is the paper's objective's optimum, not its heuristic's output. | None needed for fairness; mention the static-VC model. | high |
| R7 | 2 | minor | RC. rc_buffer 4 packets × 8 flits per boundary router, injection permission, intra-chiplet and inbound packets uncontrolled, release at the tail: as the paper. Permission latency max(1, hops) with request and response counted once (paper: 1 cycle per OPIC level each way, 2 cycles in a 4x4 chiplet) slightly favours RC; the RCVA's choice of any free downstream VC is not modelled (`Router::rcDrain` keeps the injection VC), which slightly handicaps RC; the nearest-boundary partition is balanced 4/4/4/4 (`nearbal_table.json`). | Second-order either way. | None needed. | high |
| R8 | 3 | **critical** | The 3-10 % saturation-throughput gap. Causes found: (a) R1 (Up VL single-VC) and (b) R2 (round-robin semantics), both repository-specific, on top of (c) the VN segregation inherent in DeFT (non-boundary sources in VN0, destination chiplet in VN1, 67:33 and 11:89 on chiplet links towards / away from the VLs) and (d) the THR metric itself: the maximum accepted throughput over the 7 ladder loads sits at the top load (1.6 × Lsat) in 42-48 of 50 MTR/RC cells and 31-37 of 50 DeFT cells, so "THR" is mostly the accepted throughput at 1.6 × Lsat and the MTR/RC advantage is a lower bound (2x2 uniform: MTR accepted 0.1169 → 0.1180 from 1.4 to 1.6 × Lsat; the review's run at 2.0 × Lsat gives 0.1178, so the cap is small on 2x2). VC split per class in §3.2. | Measured (§5.1, uniform, 2x2 / 3x3 / 4x4): the paper's Up rule with a free-VC round-robin recovers 6.7 / 7.2 / 3.7 points of MTR's 9.5 / 5.2 / 5.0 % throughput advantage, and with the paper-style entry 8.7 / 4.3 / 5.1 points; the latency gap at 1.0 × Lsat (MTR 20 / 6 / 13 % below the repository's DeFT) shrinks to 2 / −3 / 2 points, i.e. seed noise. The paper's hotspot claim is reproduced as it stands (v19, 2x2 hotspot: DeFT THR 0.0711 vs MTR 0.0646, LAT 58 vs 110 cycles): MTR's column-only inbound reachability funnels each hotspot's traffic through one VL. So the gap on uniform traffic is mostly the repository's two deviations, and the published statement "DeFT stays below MTR and RC in throughput on every size" does not survive them. | Re-run DeFT with the paper's Up-link rule (and a free-VC fallback) before concluding that DeFT loses to MTR and RC; extend the ladder or measure saturation from a sweep. | high (cause reproduced on three sizes), medium (split between R1, R2 and R4) |
| R9 | 4 | major | Hop timing. Noxim's alternating-bit handshake lets a link carry one flit per **two** cycles (measured: a saturated single link delivers 0.50 flits/cycle with 8-flit and with 2-flit packets); a hop costs 2 cycles for the head (measured 2 + 2 × hops for 1, 3 and 16 hops); the router routes, allocates and switches in the same cycle. Latency is the head flit's latency from packet generation (`Stats.cpp:41-42`), so it includes NI queueing and excludes serialisation. All methods share this. The decision delay of v20/v21 (`Router.cpp:199-203`) and the baselines' zero-cycle routing are charged in these cycles: N = 3 on a 2-cycle hop is +150 % per multi-output hop, where a 2-4-stage router would see +75-100 %, and the baselines pay nothing for their own route, VC and switch stages. | The low-load penalty of v21 (+23 to +67 %) is overstated relative to a pipelined baseline; §5.3 measures what a uniform head delay for every method does (2x2 uniform, 3 seeds): with every router charged 2 cycles and CI_fastQL its N_fast = 3 on top on multi-output hops, the low-load penalty against DeFT falls from +33 % to +14 % (3-cycle pipeline: +16 %), while the absolute extra stays 6-8 cycles; at 1.0 × Lsat the effect moves from −2.6 % to +4.9 % (within 3-seed noise) and the p99 gain stays (−27 % to −28 %). | Report the delay results next to a run in which every router pays its pipeline (`-deft_lb pipe_all N` in the patched copy), or map N to the baseline pipeline depth explicitly. | high (mechanism), medium (magnitude) |
| R10 | 4 | minor | One `rand()` stream. Routers' random tie-breaks and forwarding arbitration draw from the same C `rand()` as the traffic generator (`Router.cpp:335`, `DeftLateBinding.cpp:473`, `ProcessingElement.cpp:258-264`), so two variants with the same seed see different traffic realisations; only DeFT-Ran has its own RNG. | Seed pairing in the t-tests is weaker than it looks; no bias. | Give the traffic generator its own RNG, or say that seeds are not paired. | high |
| R11 | 4 | minor | Decision delay and staleness. A delayed head blocks only its own input VC (`continue` skips its reservation); the wait is serial with the VC wait and the decision is recomputed every cycle on fresh state, which a pipelined router would not do (it would overlap routing with waiting and decide once). Conservative against LB, as the rounds state. | None against the baselines. | Document. | high |
| R12 | 5 | minor | The relation matches its definitions: minimal turn-legal moves from the actual arrival port (`lastMoveFromDirIn`, `movesMask`, `legalTurn`), monotone pruning (`nextMasks` keeps only candidates on a minimal path through the move), no transit through other chiplets (`phaseOf` → `PH_INVALID` → no move; unreachable because moves only target the own chiplet's exits or the destination chiplet's entries), unconditional consumption (`Router::route` returns LOCAL first), exactly two VCs (`ConfigurationManager.cpp:550-554`). The model check (`formal/impl_relation_check.py`) models the implemented Up rule, not the paper's; with the paper's rule all 2x2 masks tried and 3x3 fault-free remain acyclic, dead-end-free and livelock-free (`vn_up_check.md`). | None. | Add the paper's Up rule to the formal model when R1 is fixed. | high |
| R13 | 6 | minor | Analysis. Effect, CI and p recomputed independently (`recompute_primary.py`, pure Python t distribution): all 60 v19 tests and the 12 v21 3x3 tests agree to ≤ 0.005 pp with identical verdicts; Holm step-down is implemented correctly; the pre-registered families, seeds, loads and metrics were used. Small inconsistency: the coarse Lsat pass takes L0 at rate 0.001 (`experiments_v19.py:241`) while the rule and the fine pass use 0.0002 (`:282`); it only decides the grid. The latency metric sits at DeFT's own knee (3 × L0), where DeFT's curve is steep, so LAT comparisons amplify knee differences; this is pre-registered. | None on the reported numbers. | None. | high |
| R14 | 7 | minor | Hardware. One flow (Yosys + ABC, NanGate45, OpenSTA, pre-layout, flip-flop storage for every table and buffer) for all methods; v18 reports form S (one unit per router) first and form P (per port) as the bound, v21 reports form P first because that is what the simulator models, both are given. N_fast follows the stated rule (checked on `timing.md`: CI_fast 4x4 ipos6 P misses the cut by 0.003 ns → N = 2; CI_fastQL 3x3 ipos5 P stage A 1.11 ns → N = 3). The baselines' own routers also miss 1 GHz (switch allocation slack −0.18 to −0.37 ns; MTR boundary / RC chiplet route stage 1.05-1.06 ns) and are charged nothing. The DeFT/MTR and RC/MTR area ratios differ from the paper's because tables are flip-flops; stated. | The "4-6.5 ns" and "N = 2-3" conclusions hold as pre-layout estimates against an idealised baseline (see R9). | Report N relative to a baseline pipeline depth of at least 2 stages, which the flow itself indicates. | medium |
| R15 | 1 | minor | Paper inconsistency, for the record: the proof of Theorem III.2 says "Packets entering the interposer are in VN.0", while Algorithm 1 reassigns VN0/VN1 by round-robin at the Down port. The code follows Algorithm 1 since v19 (`-deft_vn_rr 1`); before v19 it followed the theorem's sentence (Down link VN0 only, interposer 87:13), the known history. | None now. | None. | high |

## 3. VN per channel class

### 3.1 Which VN each hop uses

| Hop | DeFT paper (Alg. 1, Rules 1-3, Thm III.1-4) | CEA `Routing_DEFT` | This code (`-deft_vn_rr 1`) | Same? |
|---|---|---|---|---|
| Injection, non-boundary source, inter-chiplet | VN0 | VN0 (`allocateVC`) | VN0 | yes |
| Injection, boundary source, inter-chiplet | round-robin VN0/VN1, whatever the exit | round-robin per tile, whatever the exit (asserts if a VN1 packet later needs Horizontal→Down) | round-robin only if committed to the own VL, else VN0 (F1) | no (R3); no effect with the LUT |
| Injection, intra-chiplet | round-robin | round-robin per tile | round-robin, counter per router (global counter without the option) | yes |
| Injection at an interposer source | round-robin | round-robin | round-robin (no such source in the experiments) | yes |
| Source-chiplet horizontal hops | keep | keep | keep | yes |
| Local→Down (boundary source) | source VN (the reassignment branch is for non-source boundary routers) | source VN (`always_reassign_src_vc = false`) | source VN | yes |
| Horizontal→Down, VN0 packet | round-robin reassignment VN0/VN1 | VN0 or VN1, flag per (router, port) toggled each evaluation | counter per router, peeked, advanced on a successful reservation; a busy VC is waited for | semantics differ (R2) |
| Horizontal→Down, VN1 packet | forbidden (Rule 3) | asserted impossible | forbidden (R3 on the input VN) | yes |
| Down link | VN0 or VN1 as reassigned | same | same (VN0 only before v19) | yes |
| Interposer hops | keep (Thm III.2: both VNs) | keep | keep | yes |
| Horizontal→Up: the Up link | keep the interposer VN (switch happens at the chiplet boundary router) | keep (no `assignVCOut` branch for the Up output) | **VN1 forced** | **no (R1)** |
| Up→Horizontal and Up→Local at the destination boundary router | VN1 | VN1 (`dir_in == DIRECTION_DOWN`) | VN1 | yes |
| Destination-chiplet hops | VN1 | VN1 | VN1 | yes |
| Rule 1 (no VN1→VN0) | yes | by construction | `canTransition` | yes |
| Rule 2 (VN0: no Up→Horizontal) | yes | by construction | `isUpToHorizontal && VN0` → forbidden | yes |

Round-robin state: the paper does not say where it lives or what happens when the chosen VC is busy. This code: `router_source_vn`
and `router_boundary_vn`, one counter each per router (`DeftVirtualNetwork.cpp:21-29`); the source counter advances at every
eligible injection; the boundary counter advances when `Router::txProcess` reserves the Down output (`Router.cpp:259-260`); a busy
VC makes the head wait on that VC. CEA: one flag per tile for allocation, one per (tile, output) for switching, toggled on every
`selectVCOut` call.

### 3.2 VC0:VC1 split per link class, 2x2 uniform at 1.0 × Lsat

Repository data (`results_v19_vnrr/vc_balance.md`, seeds 41-43, old Lsat) and this review's runs (seed 1001, `SUMMARY.md`, which
also give VC-wait cycles per flit):

| rule | chiplet towards VL | chiplet away from VL | interposer | Down VL | Up VL |
|---|---|---|---|---|---|
| this code, `-deft_vn_rr 0` (v1-v18) | 67:33 | 10:90 | 88:12 | 88:12 | 0:100 |
| this code, `-deft_vn_rr 1` (v19-v21) | 67:33 | 11:89 | 50:50 | 50:50 | **0:100** |
| the paper's rules (Alg. 1, Thm III.4; patched copy `up_keep 1`) | 68:32 | 11:89 | 50:50 | 50:50 | **50:50** |
| MTR, RC (no VN rules) | 50:50 | 50:50 | 50:50 | 50:50 | 50:50 |

The chiplet-link skew is inherent in DeFT (source-phase traffic in VN0 flows towards the VLs, destination-phase traffic in VN1
flows away from them; the paper's Fig. 5 aggregates both directions per chiplet and reports 47.5:52.5). The Up-VL skew is not.

## 4. Recomputed headline numbers

`recompute_primary.py` re-derives the v19 K5 primary table and the v21 primary rows from the per-run CSVs and the load-point
file alone, with its own t distribution (`recompute_output.md`).

* v19 K5, 60 tests, Holm over 60: every effect, interval bound and Holm p agrees with `results_v19_vnrr/report/primary.csv` to
  within 0.005 percentage points (rounding of the stored values); 60 of 60 verdicts identical (H1 12/12 supported; H2 41
  supported, 6 n.s., 1 against). Secondary DeFT-vs-MTR/RC rows agree too (2x2 THR −8.0 % / −9.3 %, 3x3 −3.2 % / −3.5 %, 4x4
  −6.8 % / −7.5 %).
* v21, size 3x3, 12 primary rows (Holm over the 36): identical to `results_v21_fastsel/report/primary.csv` (CI_fastQL vs DeFT LAT
  +0.04 % n.s., P99 −32.2 % supported; FULL_fastQL vs DeFT LAT +4.2 % n.s., P99 −36.8 % supported; the four MTR/RC rows per
  variant as reported). The LAT at 0.2 × Lsat rows match (+31.5 / +50.9 / +61.4 / +62.8 %).

## 5. Confirming experiments

All runs: patched copy of the simulator (`patch_review.py`), default configuration of the rounds (2 VCs, 4-flit buffers, 8-flit
packets, 2000 + 8000 cycles), DeFT's rho* LUT of the size, `-deft_vn_rr 1` for every DeFT variant, uniform traffic, fault-free,
the K4 load ladders of `results_v19_vnrr/load_points_rr.json`, seeds 1001-1003 (4x4: 1001-1002; none of them an evaluation
seed). Driver `run_experiments.py`, raw outputs under `~/lbrev/raw`, per-run CSVs `gap_runs.csv`, `pipe_runs.csv`, tables in
`SUMMARY.md`. 472 + 168 + 42 + 4 + 8 runs, about 2.5 CPU-hours in total.

### 5.1 The DeFT baseline with the paper's Up-link rule and a free-VC round-robin

Variants: `DeFT` (as v19/v21), `DeFT_up` (Up link keeps its VN, R1), `DeFT_fb` (round-robin takes the other VC when the
counter's VC is held, R2), `DeFT_up_fb` (both), `DeFT_pe` (DeFT's LUT exit with a paper-style destination-keyed, balanced
nearest entry, R4), `DeFT_pe_up_fb`, `MTR`, `RC`.

Effects relative to the repository's DeFT (per-seed log ratios, geometric mean over seeds; THR = maximum accepted throughput over
the 7 ladder loads; latency = head latency, cycles). Absolute DeFT values: 2x2 THR 0.1076, LAT 55.3 / 21.4 at 1.0 / 0.2 × Lsat,
P99 224; 3x3 0.0811, 62.5 / 27.5, 227; 4x4 0.0648, 76.0 / 34.5, 289. Full tables with the accepted throughput at every load:
`SUMMARY.md`; per run: `gap_runs.csv`. No dead-end event in 472 runs.

| size | variant | THR | LAT @1.0 Lsat | LAT @0.2 Lsat | P99 @1.0 Lsat |
|---|---|---|---|---|---|
| 2x2 | DeFT_up (paper's Up rule) | +4.0 % | +2.4 % | −0.5 % | +22.7 % |
| 2x2 | DeFT_fb (free-VC round-robin) | +1.9 % | +3.9 % | +0.6 % | +6.5 % |
| 2x2 | DeFT_up_fb | +6.7 % | −3.8 % | −3.0 % | −9.1 % |
| 2x2 | DeFT_pe (paper-style entry) | +0.0 % | +4.6 % | −9.4 % | +24.2 % |
| 2x2 | DeFT_pe_up_fb | +8.7 % | −17.3 % | −7.9 % | −17.4 % |
| 2x2 | MTR | +9.5 % | −19.6 % | −5.2 % | −21.7 % |
| 2x2 | RC | +11.1 % | −23.6 % | −5.9 % | −27.8 % |
| 3x3 | DeFT_up | +4.0 % | −2.0 % | +0.3 % | +5.6 % |
| 3x3 | DeFT_fb | +2.0 % | +0.7 % | +2.3 % | +2.1 % |
| 3x3 | DeFT_up_fb | +7.2 % | −4.2 % | −0.8 % | −9.5 % |
| 3x3 | DeFT_pe | −3.2 % | +13.1 % | −3.2 % | +63.1 % |
| 3x3 | DeFT_pe_up_fb | +4.3 % | −8.5 % | −5.7 % | −10.4 % |
| 3x3 | MTR | +5.2 % | −5.5 % | −1.9 % | +0.3 % |
| 3x3 | RC | +4.4 % | −9.8 % | −1.2 % | −10.5 % |
| 4x4 | DeFT_up | +2.3 % | −6.9 % | −1.2 % | −15.7 % |
| 4x4 | DeFT_fb | +1.6 % | +2.6 % | +0.0 % | +4.2 % |
| 4x4 | DeFT_up_fb | +3.7 % | −7.8 % | −0.7 % | −15.6 % |
| 4x4 | DeFT_pe | +1.4 % | −6.1 % | −3.9 % | −16.5 % |
| 4x4 | DeFT_pe_up_fb | +5.1 % | −11.2 % | −4.4 % | −23.1 % |
| 4x4 | MTR | +5.0 % | −13.0 % | −1.7 % | −25.6 % |
| 4x4 | RC | +5.4 % | −17.4 % | −3.0 % | −31.5 % |

Reading: the two repository-specific rules (Up link in VN1, no free-VC fallback) account for most of MTR's throughput advantage on
every size and for the latency ordering on 2x2 and 3x3; the entry-selection choice (R4) adds the rest on 2x2 and 4x4 and is
pattern-dependent (it is DeFT-Dis's entry, which v19 shows to be much worse under hotspot traffic). The Up rule alone can raise
p99 on the small instance (2x2 +22.7 %): two Up VCs interleave flits on the link and hold the single-VC destination-chiplet
channels longer, which the free-VC round-robin repairs.

### 5.2 VC split

See §3.2 and `SUMMARY.md` (`vcsplit`): with the paper's Up rule the Up-VL wait falls from 1.09 to 0.26 cycles per flit; part of
the wait moves to the destination chiplet's single-VC links (chiplet-away wait 0.07 → 0.26).

### 5.3 A uniform per-hop delay for every method

`-deft_lb pipe_all N` makes every head of every algorithm wait N cycles at an input-buffer front before it may reserve an output,
a crude N-stage pipeline charged to all routers. 2x2 uniform, seeds 1001-1003, ladder loads. CI_fastQL is the v21 variant of
2x2 (N_fast = 3, age 2, w = 2, beta = 4, alpha = 0.1).

A head of a late-binding router at a multi-output hop waits pipe_all + N_fast cycles (its decision needs N_fast cycles more than
the baseline's route stage), every other head pipe_all. Geometric means over seeds 1001-1003 (`SUMMARY.md`, `pipe_runs.csv`):

| variant | pipe_all | THR | LAT @1.0 Lsat (cycles) | LAT @0.2 Lsat | P99 @1.0 Lsat |
|---|---|---|---|---|---|
| DeFT | 0 | 0.1076 | 55.3 | 21.4 | 224 |
| CI_fastQL (N_fast = 3) | 0 | 0.1081 | 53.8 | 28.5 | 165 |
| MTR | 0 | 0.1176 | 44.4 | 20.3 | 176 |
| DeFT | 2 | 0.1075 | 70.9 | 40.5 | 270 |
| CI_fastQL (N_fast = 3) | 2 | 0.1075 | 74.4 | 46.2 | 195 |
| MTR | 2 | 0.1206 | 60.1 | 38.8 | 182 |
| DeFT | 3 | 0.1040 | 79.8 | 49.4 | 243 |
| CI_fastQL (N_fast = 3) | 3 | 0.1032 | 88.3 | 57.1 | 225 |

CI_fastQL against DeFT at the same pipe_all (per-seed log ratios): LAT @0.2 Lsat +33.1 % (pipe 0), +14.1 % (pipe 2), +15.6 %
(pipe 3); LAT @1.0 Lsat −2.6 %, +4.9 %, +10.7 %; P99 −26.7 %, −27.8 %, −7.5 %. The extra head latency of the fast selection is
6-8 cycles at low load in every case; what changes is the baseline it is compared with. (v21 reports +38.5 % at 0.2 × Lsat on
10 seeds for this variant; the 3-seed pipe-0 value here is +33 %.) MTR against DeFT at pipe_all 2: LAT @1.0 Lsat −15 %,
LAT @0.2 Lsat −4 %, THR +12 %, so the DeFT-vs-MTR ordering does not depend on the pipeline charge.

## 6. Open questions

1. The DeFT paper's interposer size and VL positions. The text says only "four VLs on the borders" and "according to [7]"; MTR
   and RC use a 4x4 interposer. Whether the repository's footprint-sized interposer changes the DeFT-vs-MTR/RC ordering is not
   known; a 4x4-interposer run would settle it, but the topology code has no such option.
2. What "round-robin reassignment" does when the chosen VC is busy, in the paper's simulator. Neither the paper nor CEA's code
   documents the intended semantics; CEA's effective behaviour is "try the other VC next cycle".
3. The paper's exact second (entry) selection: per destination router with in-chiplet distance (this review's reading of Eq. 4
   and the text) or something else. The paper's Fig. 3 numbering could not be mapped to the repository's slot positions.
4. How the DeFT paper's own Noxim modelled MTR's and RC's VC usage (static per packet, as here, or per-hop allocation) and whether
   its links also carried one flit per two cycles. These decide how far the paper's "DeFT above MTR and RC" is comparable with the
   repository's runs at all.
5. Whether the v19/v21 learners, tuned with the repository's Up-link rule, keep their gains when DeFT and they run under the
   paper's rule (the LB variants inherit the VN rules, so both sides change).

## Files in this folder

* `REVIEW.md` (this file), `SUMMARY.md` (tables of the confirming runs), `regression.md`, `recompute_output.md`, `vn_up_check.md`.
* `recompute_primary.py`, `lut_path_analysis.py`, `vn_up_check.py`, `run_experiments.py`, `patch_review.py` (the source patch,
  applied to a copy of `src/` only; its last hunk, the additive decision delay, is in the second build `noxim_review2` used for
  the fast-selection pipeline runs), `nearbal_table.json`, `gap_runs.csv`, `pipe_runs.csv`.
* Reproduce: copy `src/` and `bin/Makefile` to a scratch directory, link `bin/libs`, `python3 patch_review.py SRC`,
  `make -C bin MODULE=noxim_review`; then `run_experiments.py prep|regress|gap|vcsplit|pipe|summarize` (WSL, cwd of the runs is
  the repository's `bin/`).
