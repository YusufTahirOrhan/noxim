# Analytical hardware cost per router (selection logic only)

This is an estimate derived from what each selection function reads and stores in
`src/DeftLateBinding.cpp`. It is not a synthesis result. It counts state and wires
*beyond* a baseline router that already has credit-based flow control (a free-slot counter
per output VC) and the DEFT_LB routing relation.

Assumptions (from `config_examples/deft_2_5d_traffic_uniform.yaml` and the topology):
* P = 5 router ports (N, E, S, W, Local), plus a 6th (Hub) at the 16 VL endpoint routers. V = 2
  virtual channels. Buffer depth 4 flits, so an occupancy value fits in b_occ = 3 bits.
* Neighbour ports carrying lookahead information: the 4 horizontal neighbours (+ the Hub
  neighbour at VL endpoints). A neighbour exposes its occupancy for each of its output
  ports N, E, S, W, Hub (5) and each VC.
* The learner's residual R and the values exchanged use b_q = 16-bit fixed point. The
  simulator uses float; 16 bits is an assumption. The destination key is a chiplet (2 bits,
  4 chiplets) for ql_key = 1, or a router (6 bits, 64 routers) for ql_key = 0.
* Q-table entries per router: one per (key, output port): 4 x 6 = 24 entries (key = chiplet)
  or 64 x 6 = 384 (key = router). Ports a router does not have would let a real design
  drop entries; they are counted here as an upper bound.
* Common to all late-binding variants (not to DeFT): the head flit carries the exit and
  entry candidate masks (4 + 4 bits), against DeFT's fixed pair (2 + 2 bits).

| Selection | Extra storage per router | Extra wires per link direction (into a router) | Per router, incoming (4 links; 5 at VL endpoints) | Extra logic per head-flit decision |
|---|---|---|---|---|
| DEFT_HEUR (C) | 0 (uses the existing credit counters and VC-busy state) | 0 | 0 | per legal output (<= 3): hops_after from the candidate masks, w x occ + busy + hops, minimum |
| DEFT_HEUR + lookahead | 0 (sideband values can be used combinationally or latched: 5 x 2 x 3 = 30 bits per neighbour if latched) | neighbour's per-output, per-VC occupancy: 5 x 2 x 3 = **30** | **120** (150) | per legal output: the neighbour's legal outputs for this packet (a second routing evaluation) and a minimum over <= 3 continuations |
| DEFT_QL (B), key = chiplet | Q table 24 x 16 = **384 bits**; pending-update static estimate per output VC 6 x 2 x 16 = 192 bits; total **~576 bits** | feedback on the reverse channel: V_here (16) + key (2) + valid (1) = **19** | **76** (95) | Q read per legal output; at the receiver, V_here = min of the learner cost over its legal outputs; one multiply-add per update (alpha) |
| DEFT_QL, key = router | Q table 384 x 16 = 6144 bits; + 192; total **~6.3 kbit** | 16 + 6 + 1 = **23** | **92** (115) | as above |
| DEFT_QL + lookahead (QL-LA), key = chiplet | as DEFT_QL: **~576 bits** (+30 bits per neighbour if the sideband is latched) | lookahead sideband 30 + feedback 19 = **49** | **196** (245) | union of the two rows above; V_here includes the receiver's own lookahead term |
| DEFT_QL + lookahead, key = router | **~6.3 kbit** | 30 + 23 = **53** | **212** (265) | as above |

For reference, DeFT and DeFT_tm store a VL table: per source router, per destination
chiplet, one exit and one entry VL id (2 + 2 bits) for each fault scenario held, i.e. 3 x 4 =
12 bits per router per scenario. DeFT_tm differs only in the table contents. The CI
variants keep the exit half of this table (6 bits per router per scenario).

Reading the table
* The stateless heuristic costs essentially nothing beyond the routing relation. The lookahead
  heuristic's cost is wiring (120-150 sideband wires per router, comparable to adding one
  32-bit flit channel in each direction on every link) plus a second routing evaluation.
* The learner adds storage (0.6 kbit with the chiplet key, 6.3 kbit with the router key) and
  a reverse feedback channel. It also adds an update datapath with a multiplier, unless alpha
  is restricted to powers of two (0.005-0.1 is close to 2^-8 ... 2^-3).
* QL-LA pays both costs. It is the most expensive option and is only justified if it beats
  the lookahead heuristic. See FINDINGS.md for whether it does.
