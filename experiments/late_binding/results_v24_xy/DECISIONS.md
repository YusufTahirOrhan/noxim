# v24 decisions: late binding without path adaptivity (XY and a VN-split order on the interposer)

The conservative option is the one that does not favour late binding. The explanations of the review that started this round
are treated as hypotheses; where a measurement of this round disagrees with one, the measurement is what `FINDINGS.md` reports.

## A0: reproduction of the probes
* **Reference binary.** `~/lbbin/noxim_8d84634`: commit 8d84634 exported with `git archive` into a separate tree
  (`~/lbref/8d84634`) and built there with the repository's Makefile. Its md5 (b81b5d8b…) equals that of `bin/noxim` as left by
  round 23, so the two are the same build.
* The ten rows of the prompt's A0 table were run with that binary before any source change (`reproduction.md`, 10 / 10
  identical to the printed digits).

## A1: `-deft_lb ipos_tm YX` and `O1` (default: unchanged; `chip_tm` accepts XY and OE only)
* **`YX`**: dimension order with Y first. `legalTurn` forbids X → Y turns, `movesMask` offers the Y move while one is
  productive. The `reach` cache has a third turn model.
* **`O1`**: on the interposer a packet in VN0 is routed XY and a packet in VN1 YX (`iposTm(vn)` in `DeftLateBinding.cpp`).
  The VN is the VC of the input buffer the head sits in; DeFT's rules do not change it on the interposer, so each VN's
  interposer channels carry one dimension order. The VN's order is used wherever the interposer turn model is used:
  - the offered moves (`legalMoves`, interposer phase) and through `movesMask` the `reach` test;
  - the pruning of the entry candidates (`nextMasks` has a new last argument, the VN at the current router; default 0, so
    the testbenches of rounds 18 and 21 compile unchanged);
  - the one-hop lookahead (`bestContinuation` evaluates the neighbour with the VC the head would have there). Across the Down
    link that VC is the boundary round-robin's current value, which is what the head gets unless the fallback of
    `-deft_rr_fallback` takes the other VC; the lookahead term is an estimate either way, the offered moves at the interposer
    router itself always use the VC the head arrived in.
  - the bounded-entry path length (`pathLength`) treats O1 as XY: from a fresh start either order reaches every node.
* `O1` needs the DeFT VN rules (`vn_rules 1`; rejected otherwise). `YX` and `O1` are rejected with `-sel DEFT_FAST` (its
  ROM is not built for them; the prompt does not ask for it).
* **Related work.** O1TURN (Seo, Jayasimha, Chien, ISCA 2005) lets a packet take XY or YX and gives each dimension order
  its own virtual channel class, which keeps the union deadlock-free and balances the load of the two orders. ReD (Taheri et
  al., IEEE TCAD 2024) uses a different turn model in each virtual network of a 2.5D system. `O1` is the same construction
  on DeFT's two interposer VNs: the VN that DeFT's boundary round-robin assigns for deadlock freedom also selects the
  dimension order, so no VC is added and no rule of DeFT changes.

## A2: model check (`formal/xy_check.py` → `formal_xy.md`)
* `formal/impl_relation_check.py` has the five relations of the prompt (`CI_XY_XY`, `FULL_XY_XY`, `CI_XY_O1`, `FULL_XY_O1`,
  `FIXED_XY_O1`) and the turn model `YX` (`formal/deft_cdg_model.py`). For `O1` the interposer phase takes its turn model
  from the VN of the state (XY in VN0, YX in VN1), as the simulator does.
* Run as `upkeep_check.py`: `UP_KEEP = True`, all 897 masks of 2x2, the 22 masks of 3x3 and the 2 masks of 4x4, the same
  negative control (R3 and the F1 source rule removed must give a cycle).
* Two relations more than asked, on 2x2 only: `CI_XY_YX` and `FIXED_XY_YX`, so that the plain option `ipos_tm YX` (not used
  by any run of this round) is not left unchecked.
* Result: every check passes (acyclic CDG, no dead end, no livelock; longest path 24 / 32 / 40 hops); the negative control
  reports a cycle.

## B1: `-deft_lb lut_bias D` (default 0 = off)
* The **default VL** of a packet is DeFT-P's choice: the LUT's `source_exit` for the source router (exit) and its
  `entries_by_destination` entry for the destination router (entry), whatever `-deft_lut_entry` says; under faults the LUT's
  choice for the current mask (`defaultVl`, cached per source router and destination chiplet / per destination router).
* An offered output gets `+D` in the selection cost when the default VL of the current phase (exit in the source chiplet,
  entry on the interposer) is in the candidate mask before the move and not in the mask `nextMasks` returns for the move.
  This includes taking the Down or Up link at another VL. Once the default VL is gone, nothing is penalised.
* The term is added in `selectHeuristic` and `selectQLearning` to the costs the choice is made on. It is not in the learner's
  TD target (`onHeadAtFront`) and not in the one-hop lookahead term (`bestContinuation`). With lookahead routing the stored
  decision is the next router's choice, so it contains that router's penalty.
* **Safety.** The candidate masks, the offered outputs and the pruning are not touched: the penalty only reorders the
  selection among outputs the relation offers. Lemma 1 and Theorem 2 of the paper draft (and the model check of A2) do not
  depend on the selection, so they are untouched.
* **Header cost.** A router cannot look the default VL up (it depends on the source router and the fault mask), so the
  head carries it as a slot index of the chiplet's four VLs: 2 bits for CI (the entry; its exit is fixed), 4 bits for FULL
  (exit and entry).
* Needs a LUT with `entries_by_destination` (the v23 LUTs); rejected with `-sel DEFT_FAST`.

## B2: `-deft_lb lookahead_fallback 1` (default off; needs `lookahead_route 1`)
* In `Router::selectionFunction`, at a hop that offers more than one output, for a head with a stored decision: a head that
  holds an output keeps it (`findReservation`); otherwise, every cycle, the stored output is requested if it is free, else
  the first other offered output (offer order: the vertical link, then N, E, S, W) that is free, else the stored one.
* **Free** = the output VC the head would get is not held by another packet and the downstream buffer of that VC is not
  full. The VC follows the reservation phase: DeFT's VN rules, with the round-robin's other VC when the counter's VC is held
  (`-deft_rr_fallback 1`).
* **Reading of "downstream buffer not full" (decided on tuning seeds, before any evaluation run).** Two readings fit the
  description: the router's own `buffer_full_status_tx` signal (one cycle old, what the forwarding phase uses) and the
  neighbour's input buffer read directly (how the selection's occupancy term has read it since round 1). The first
  implementation used the signal and gave 0.0647 / 95.4 and 0.0831 / 446.9 on the two fallback rows of B4 (probe: 0.0647 /
  94.4 and 0.0831 / 467.5); the direct read gives the probe's values to the last printed digit. An A/B on the tuning seeds
  (CI with XY, v10 parameters, the LF mechanism, pipe_all 2, uniform and chipperm, 2x2 and 4x4, loads 0.5, 1.0, 1.4 and
  2.0 × Lsat, seeds 101-102; geometric means over the 8 cells, signal against direct): THR −0.37 %, LAT at 1.0 × Lsat −0.34 %,
  P99 −1.27 %, LAT at 0.5 × Lsat −0.02 %. The two are the same within 0.4 % on THR and LAT, and neither is the less
  favourable on all three metrics (the direct read is worse for late binding on LAT and P99 and better on THR). **The direct
  read is kept**: it is the reading the rest of the selection uses, and it makes the B4 probe values reproduce exactly, so
  this round's numbers stay comparable with the review's. The A/B table:

  | size | pattern | THR signal / direct | LAT 0.5 × Lsat | LAT 1.0 × Lsat | P99 1.0 × Lsat |
  |---|---|---|---|---|---|
  | 2x2 | uniform | 0.1288 / 0.1302 | 43.8 / 43.8 | 66.6 / 67.0 | 193 / 192 |
  | 2x2 | chipperm | 0.1092 / 0.1098 | 64.7 / 64.7 | 103.2 / 103.9 | 295 / 316 |
  | 4x4 | uniform | 0.0829 / 0.0828 | 69.5 / 69.5 | 92.9 / 92.8 | 216 / 217 |
  | 4x4 | chipperm | 0.0577 / 0.0578 | 96.9 / 96.9 | 145.2 / 145.5 | 375 / 370 |

* **Counters** (JSON fields present only with the option; whole run, like the v23 lookahead counters):
  `lookahead_multi` (stored decisions used at a hop with more than one offered output), `lookahead_fb_checks` (head-cycles
  in which the rule was evaluated), `lookahead_fb_blocked` (of those, the stored output was not free),
  `lookahead_fb_requests` (of those, another output was requested), `lookahead_fb_taken` (heads that left through another
  output than the stored one). Fallback rate = `lookahead_fb_taken / lookahead_multi`.

## B3: `-deft_lb busy_state 1` (default off)
* `outputVcBusy` reads the reservation entries of the output (`ReservationTable::outputVcHolder`): busy when the output VC
  is held by a packet other than the asking one. A reservation under the asking head's own input port and VC is its own only
  when the head is in the router; when the decision is computed ahead (`precomputeNextDecision`), a reservation under that
  key belongs to the packet in front of it in the same input VC and counts as busy. This is the term the v23 lookahead model
  lost (`checkReservation` answered ALREADY_SAME / ALREADY_OTHER_OUT for every output in that case).
* Used in every lookahead run of this round (LF mechanism and the two controls). Check without lookahead:
  `busy_state_check.md`.
