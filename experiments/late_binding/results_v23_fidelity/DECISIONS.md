# v23 decisions: DeFT fidelity, modelling fixes, cross-validation, reference measurements

The conservative option is the one that does not favour late binding. The findings this round acts on are those of the
independent review `review_v22/REVIEW.md` (R1, R2, R4, R6, R7, R9, R10, R13); the review's source patch
(`review_v22/patch_review.py`) supplied working versions of `up_keep`, `rr_fallback` and `pipe_all`, which were ported into
`src/` as the options below.

## A1: the options (all default off; with every option off the 84 regression configurations are byte-identical, `regression.md`)

* **`-deft_up_keep 1`** (R1). `DeftVirtualNetwork::selectOutputVirtualNetwork`: the Up VL output keeps the input VN; the
  chiplet boundary router that receives from its Hub port still assigns VN1 to every output (the existing
  `isFromInterposerInsideChiplet` branch), so a VN0 packet switches to VN1 before any Up → Horizontal move and Rule 2 never
  fires. Up → Local is consumption. The option sits in the shared VN module, so it applies to DEFT, INTERPOSER_AWARE_XY and
  DEFT_LB alike.
* **`-deft_rr_fallback 1`** (R2). Boundary round-robin (`Router::txProcess`): when the counter's VC is held, the other VC is
  taken if it is free; the counter advances on every successful reservation, whichever VC was taken. Source round-robin
  (`assignSourceVirtualNetwork`): the PE passes the router's full local VC buffers (`buffer_full_status_tx`); if the counter's VC
  is full and the other is not, the other is taken; the counter advances on every assignment. Only packets that may use either
  VN are affected (intra-chiplet, and boundary sources committed to their own VL).
* **`-deft_lut_entry dst`** (R4). A second table in the LUT file, `entries_by_destination`, keyed by (fault mask,
  destination router): the paper's second selection, the 16 routers of each chiplet assigned to its functional VLs by
  ρ·Σ in-chiplet distance + Σ|l_v − l̄|/l̄ with the same exact dynamic programme as the exit selection (16 points, so never the
  MILP). `DeftVerticalLinkLut::lookupPair` substitutes the destination table's selection for `destination_entry` when the option
  is on; every consumer of the pair (DEFT routing, DEFT_LB's `lut` policies, the bounded-entry mode, the statistics) goes through
  it. The exit selection is unchanged (it already matches the paper). LUTs: `luts/v23/lut_<size>_<mask>.yaml`, generated with
  `--entry-model both` for every mask a run of the rounds can use (v5/v9 masks, the 2x2 drain masks, the v11 masks), with
  ρ* = 0.01 / 0.01 / 0.001 (2x2 / 3x3 / 4x4). Their `entries` equal the earlier LUTs' (`lut_check.md`), so DeFT-B uses the same
  files.
* **DeFT-P / DeFT-B.** DeFT-P = `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst`; DeFT-B = the same VN
  options with the v1-v21 entry. DeFT-P is the primary reference of every later round, DeFT-B is reported next to it. Decided
  before any run.
* **`-traffic_rng 1`** (R10). `ProcessingElement` draws from a `std::mt19937` seeded once from `-seed`; routers keep the global
  `rand()`. The off path keeps the exact original expressions (`rand() / RAND_MAX`, `rand() % n`, the `randInt` formula), so
  the regression stays byte-identical. The traffic generator's draws do not depend on the network, so two variants with the same
  seed see the same packets at the same generation times.
* **Lsat L0** (R13). `experiments_v19.coarse_lsat` now takes L0 at 0.0002 like the fine pass; `load_points_rr.json` was made with
  the old rule and is not regenerated (it only decided which grid the fine pass used). The v23 points use 0.0002 throughout.

## A2: gates and the proof note

* **Model check** (`formal/impl_relation_check.py`, flag `UP_KEEP`; `formal/upkeep_check.py` → `formal_upkeep.md`): the Up
  channel of a VL is `('U', vl, vn)` with the VN the packet has on the interposer, the destination chiplet is VN1. Run on all
  897 masks of 2x2 and the sampled masks of 3x3 and 4x4 for the fixed pair (XY and odd-even), CI and FULL, with the negative
  control (R3 and the F1 rule removed must give a cycle).
* **Proof note.** Channel classes with the paper's Up rule: κ1 chiplet VN0 (source and intra-chiplet phases), κ2 Down (both
  VCs), κ3 interposer VN0 and VN1 (no dependency between the two: the VN does not change on the interposer), κ4 Up (both VCs:
  a VN0 packet uses the Up channel in VC0, a VN1 packet in VC1), κ5 chiplet VN1 (destination and intra-chiplet phases). Every
  dependency stays in its class or moves to a later one: κ1 → κ1 (chiplet turn model), κ1 → κ2 (the round-robin), κ2 → κ3,
  κ3 → κ3 (interposer turn model) and κ3 → κ4, κ4 → κ5 (the boundary router assigns VN1 to every output of a packet that came
  up, before any horizontal move, so Rule 2 is never violated and no κ4 → κ1 edge exists), κ5 → κ5 → ejection. κ5 never goes
  Down (Rule 3 on the input VN). The Up channels have no dependency among themselves whatever their VC. So the CDG is
  acyclic; the only change against the v19 argument is that κ4 now holds both VCs of a VL instead of VC1 alone, which adds no
  edge between classes. **Lemma 1 of the paper draft** (a packet in the source chiplet is in VN1 only if it is committed to the
  source router's own VL) is untouched: the Up rule concerns the interposer and destination side. **Theorem 2** (acyclicity of
  the late-binding relation) needs only the class definition of κ4 changed to "both VCs of the Up links"; its proof reads the same.
* **Drain tests:** the v10 protocol and masks for every VN-based method with DeFT-P's VN options (DeFT-P, DeFT-B, DeFT-Dis,
  DeFT-Ran, XY-SP, DeFT_OE_G with both LUT entries, CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G), for the lookahead variants (B2) and
  for MTR and RC with the per-hop VC (B3). All with the v23 LUT of the mask (`drain_summary.csv`).
* **VC split:** DeFT-P, DeFT-B and the old reference, 2x2 and 4x4 uniform at 1.0 × Lsat of the K4 ladders, seeds 41-43
  (`vc_split.md`).

## B: modelling fixes

* **B1 `-pipe_all N`.** `Router::txProcess`: a head waits N cycles from the cycle it reached the input-buffer front before it may
  reserve an output; every routing algorithm, every router, the RC input path included (the RC FIFO's drain onto the Up link,
  the paper's RCVA, is not delayed: it has no route stage). The decision delay of DEFT_LB counts from the end of the pipe wait
  (additive), as the review's second build did. `probe_pipe.md` measures the per-router increment.
* **B2 `-deft_lb lookahead_route 1`.** `DeftLB::onHeadForward` (the head leaves router A towards B) computes B's decision with
  `precomputeNextDecision`: B's offered outputs after A's move (candidate masks pruned by the move, arrival port, destination,
  VC), and the active selection (`DEFT_HEUR`, `DEFT_QL`, `DEFT_FAST`, or a random pick for the control selections) evaluated
  on B's state at that moment (occupancies, lookahead terms, residuals). The output travels in the head (`Flit::deft_lookahead_out`).
  At B, `Router::selectionFunction` uses it if it is among the offered outputs and aborts otherwise (it never did in the drain
  tests: the offered set is a deterministic function of the same inputs). The fresh decision is computed once per head, at its
  first routing evaluation at B, for the staleness statistic only (`lookahead_used`, `lookahead_mismatch`). The computation
  moment is A's forwarding of the head, i.e. after A's route stage and pipe wait; the charge is the pre-registered residual
  `-deft_lb decision_delay max(0, N_fast + 1 − W)`, W = pipe_all + 1, set by the driver (`experiments_v23.residual`), with
  N_fast = 2 for CI heuristics and 3 for the others. Hardware assumption recorded as required: B computes on a pre-route
  request from A over sideband wires (mask, arrival direction, destination chiplet in; chosen output back); nothing is
  duplicated; the request path's RTL and timing are for the next round.
* **B3 `-vc_per_hop 1`.** Implemented, not too invasive: in the reservation phase, when the VN rules are off, the head tries the
  output's VCs in round-robin order from a per-output pointer and takes the first free one (an existing reservation of the head
  is kept); `Router::rcDrain` lets a head in the RC buffer take any free Up-link VC (the paper's RCVA) and the body follows on
  the slot's VC. With the VN rules on the option does nothing (DeFT's rules decide the VC). MTR's deadlock argument is on
  physical channels and RC's is VC-agnostic, so any VC use is safe; the drain tests confirm.
* **B4 `-deft_lb hysteresis D`.** In `selectHeuristic`, `selectQLearning` and `selectFast`: the default output is the offered
  output with the smallest remaining hop count (`hopsAfterMove`, `fastHops`), the first in the offer order on ties; another
  output is taken only if cost(best) < cost(default) − D, then the random tie-break among the best applies as before. The
  branch runs only for D > 0, so D = 0 is the previous code path.
* **B5.** The ladders of this round have 9 loads (0.2 … 1.6, 2.0, 2.4 × Lsat); THR is the maximum accepted throughput over the
  9 and the report says per cell whether it sits at the top load.

## Choices left open by the prompt, taken conservatively

* The drain tests of A2 run DeFT_OE_G with both LUT entries (src and dst), since the ablation of later rounds may use either.
* The lookahead variants' drain tests run at their v21 N_fast with pipe_all 0 (the largest decision delay a run of this round
  can use for them) and with DeFT-P's VN options.
* In D5 the ideal learners' N_fast is 3 (CI_qlLA_G, FULL_qlLA_G), the value of their learning kind, as the prompt fixes.
