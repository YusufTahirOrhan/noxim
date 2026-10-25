# Baseline design (v10, step A0)

Written before any code for the baselines. Sources:
* **MTR:** J. Yin et al., "Modular Routing Design for Chiplet-based Systems", ISCA 2018 (Sec. IV, Alg. 1, Sec. IV-C, IV-E).
* **RC:** P. Majumder et al., "Remote Control: A Simple Deadlock Avoidance Scheme for Modular SoC", arXiv 1910.04882
  (Sec. 3-4), published in IEEE TC 2021.
* **DeFT:** Taheri et al., DATE 2022 (DeFT-Dis and DeFT-Ran baselines, Fig. 8).

## Common rules (fixed by the task; the same for every method)
* **Topology:** our DEFT_2_5D instance (2x2, 3x3, 4x4 grids of 4x4-router chiplets on an interposer mesh of the same
  footprint). Each chiplet has 4 VLs at local positions N (1,0), E (3,1), S (2,3), W (0,2). These 4 routers are the
  boundary routers of every method. MTR's boundary-placement search (Alg. 1, outer loop) is skipped.
* **Buffering:** 2 VCs per port with the same depth as all our runs (`config_examples/deft_2_5d_traffic_uniform.yaml`).
* **Traffic, window, load points:** as v9 (8-flit packets, the same traffic tables, 2000 + 8000 cycles).

## Implementation vehicle
All VL-pair baselines run on the DEFT_LB relation with **singleton candidate masks and XY on both layers**. With
singleton masks and XY this relation is the DeFT relation: XY to the exit VL's chiplet endpoint, Down, XY on the
interposer to the entry VL's interposer endpoint, Up, XY to the destination. It has been traffic-identical to plain
DEFT routing with the same LUT in v2, v4 and v5. The baselines differ only in:
1. how the exit and entry VL are chosen at injection (a new injection policy);
2. whether DeFT's VN rules (R1-R3 and the F1 source rule) apply;
3. for RC, the RC buffer and the injection permission.

The chosen exit and entry VL travel in the head flit as singleton masks (the existing `deft_exit_mask` /
`deft_entry_mask` fields). This corresponds to MTR's "boundary router ID embedded in the header flit" and to DeFT's
LUT pair. All new options are `-deft_lb` parameters, off by default.

| method | exit / entry choice | VN rules | other |
|---|---|---|---|
| DeFT(rho*) | LUT (existing) | DeFT | reused v9 runs (plain DEFT routing) |
| DeFT-Dis | `near`: functional VL nearest to the source / destination router | DeFT | - |
| DeFT-Ran | `ran`: uniform among functional VLs, once per packet | DeFT | separate RNG stream |
| XY-SP | existing `INTERPOSER_AWARE_XY` (min total path length, fault-aware) | DeFT (F1: source VN0) | - |
| DeFT_OE_G | `lut` / `lut`, **OE on both layers**, FULL_qlLA_G selection and parameters, gamma 2 | DeFT | ablation |
| MTR | `mtr`: offline outbound / inbound tables | **off** | fault-free only |
| RC | `near` / `near` | **off** | RC buffer + permission; fault-free only |

### DeFT-Dis and DeFT-Ran (A1)
* **Why not a LUT file for Dis:** plain DEFT's LUT is keyed by (source chiplet, source router, destination chiplet).
  It cannot express an entry VL that depends on the destination router, which "nearest to the destination router"
  needs. Dis therefore uses the DEFT_LB relation with a new policy.
* **Distance:** Manhattan distance on the chiplet footprint. Ties go to the lowest VL id.
* **Ran:** a uniform draw among the functional VLs of the source chiplet (exit) and of the destination chiplet
  (entry), made once per packet when its head flit leaves the PE. The draw uses its own `std::mt19937` seeded from
  the run seed, so the traffic generator's `rand()` stream (injection times, destinations, VC choice) is the same as
  in every other method's run with that seed. The existing `random` policy (global `rand()`) is left unchanged.
* **VN rules and F1:** both keep DeFT's VN assignment and the F1 rule unchanged; the F1 rule sees the exit mask.

### XY-SP
* The existing `INTERPOSER_AWARE_XY` routing: XY on every layer, the VL pair minimising the total path length over
  functional VLs (ties to the lower exit, then entry VL id), DeFT's VNs.
* Under the F1 fix, inter-chiplet packets always start in VN0, because the exit is not known when the VN is
  assigned.
* No code change. The A5 drain tests decide whether it is valid; if not, it is dropped (not a stop condition).

### DeFT_OE_G (ablation)
* DEFT_LB with `exit lut`, `entry lut`, `chip_tm OE`, `ipos_tm OE`, and the selection and parameters of FULL_qlLA_G
  of the size, including gamma = 2. The only difference from FULL_qlLA_G is that the VL pair is fixed at injection.
* The formal relation checker did not cover fixed masks with odd-even routing. A configuration `FIXED_OE_OE` is added
  and checked on 2x2 (all masks of the v1 set) and 3x3 (the v4 masks).

## MTR (A2)
### Model (paper Sec. IV-A/B)
* The rest of the system is the virtual node x. Up channels (boundary router -> interposer) go into x; Down channels
  come out of x. Within the chiplet, XY routing.
* A cycle through x exists iff the chiplet CDG has a dependency path from some Down(a) to some Up(c).
  - With XY, every XY-legal turn is used by some intra-chiplet route, so every dependency path inside the chiplet is
    an X-then-Y monotone path.
  - So a cycle exists iff, for boundary routers a != c, there is a monotone XY path from a, leaving a in direction d1,
    to c, entering c from direction d2, with the inbound turn Down->d1 at a and the outbound turn d2->Up at c both
    allowed.
  - A path starting and ending at the same router does not exist (no U-turns).

### Candidate turns (task A2.2)
* **Inbound turns** Down->{N,E,S,W} at each boundary router, for the directions that exist inside the chiplet.
* **Outbound turns** {N,E,S,W}->Up, by the direction the packet arrives from.
* Local->Up (a boundary router's own PE) and Down->Local are not turns between channels and are always allowed.
* **Horizontal turns at boundary routers** are candidates in the task, but prohibiting one would break an
  intra-chiplet XY route: XY uses every XY-legal turn at every router, and the chiplet must stay connected (paper
  IV-D: "boundary router turn restrictions do not affect the internal chiplet network"). The connectivity constraint
  therefore always excludes them. They are enumerated and reported as excluded.

### Search (Alg. 1, replaced by an exhaustive search; `formal/mtr_search.py`)
* **Constraints:**
  - no cycle through x;
  - every chiplet router reaches at least one boundary router (outbound) and is reachable from at least one
    (inbound).
* **Objective** (paper Sec. IV-B): minimise Average_distance / Average_reachability, where
  - Average_distance is the mean over the 16 chiplet routers of (InD(r) + OutD(r)) / 2;
  - InD(r) / OutD(r) is the XY hop distance from the nearest boundary router that can reach r / to the nearest one
    r can reach;
  - Average_reachability is the mean over the 4 boundary routers of (InR(b) + OutR(b)) / 2, with InR and OutR the
    fractions of the 16 routers reachable from / reaching x through b.
* **Exhaustive method:**
  - The cycle condition is a conflict between an inbound turn variable and an outbound turn variable.
  - So all 2^(number of inbound candidates) inbound subsets are enumerated. For each, the outbound turns are set to
    the maximal set that conflicts with no allowed inbound turn; more allowed outbound turns never worsens the
    objective.
  - This finds the global optimum, which is at least as good for MTR as the paper's heuristic recursion.
  - Ties: fewer prohibited turns, then lexicographic order.

### Boundary assignment (paper Sec. IV-C, steps 1-3)
* The A_i / C_i / E_ij procedure is applied separately to:
  - inbound reachability (destination -> entry boundary router; the interposer table);
  - outbound reachability (source -> exit boundary router; the NI table).

  Distances are XY hop counts within the chiplet.
* "Equidistant to at least two boundary routers" uses the paper's two-router simplification: such a node goes to the
  E list of its two lowest-id nearest routers.
* All chiplets are identical (same VL positions), so one restriction set and one pair of tables serve every chiplet
  and size. The tables are written to `results_v10/mtr_config.json` and read by Noxim (`-deft_lb mtr_table PATH`).

### Routing, VCs, deadlock check
* **Routing:** XY to the exit boundary router (allowed by construction), Down, XY on the interposer, Up at the entry
  boundary router, XY to the destination.
* **VCs:** the DeFT VN rules are off (`-deft_lb vn_rules 0`), and the VC is chosen as Noxim does by default. The PE
  draws the VC uniformly at injection and the packet keeps it on every hop.
* **Deadlock check:**
  - The physical-channel CDG of the complete routing function is built from all source-destination routes, and its
    acyclicity is checked on 2x2, 3x3 and 4x4, fault-free (`formal/mtr_cdg_check.py`).
  - Acyclicity of the physical-channel CDG implies deadlock freedom for any VC assignment.
* **Deviations:**
  - no boundary placement search;
  - the interposer is our footprint-sized mesh, not a 4x4 mesh;
  - the global optimum instead of the heuristic recursion;
  - fault-free only, as in DeFT's comparison.

## RC (A3)
### Paper (Sec. 3-4)
* Outbound packets are segregated into an rc_buffer at the boundary router, a set of FIFOs each holding a whole
  packet (4 packets in the paper's setup).
* A non-boundary PE may inject an outbound packet only after its OPIC block has obtained permission from the
  boundary router's OPIC root, i.e. a free rc_buffer slot.
* Outbound packets at the boundary router skip VC allocation, go through the crossbar into the RCB, and compete for
  the downstream interposer VC from there (RCVA).
* Intra-chiplet packets and inbound packets are not controlled.
* Routing inside chiplets and on the interposer is unchanged (oblivious).

### Our implementation
* **Exit / entry:** the boundary router nearest to the source / destination (Manhattan), ties to the lowest VL id
  (the `near` policy, shared with DeFT-Dis). Routing XY / XY; DeFT VN rules off (`vn_rules 0`), VC as in Noxim.
* **RC buffer:** one per chiplet boundary router, enabled by `-deft_lb rc 1` with `rc_slots 4`. Each slot is a FIFO of
  max packet length (8 flits).
* **Permission:**
  - Before the head flit of an outbound packet leaves its PE, the PE requests a slot of its exit boundary router's
    RC buffer.
  - Requests are granted FIFO per boundary router while fewer than `rc_slots` slots are reserved.
  - A grant reserves a slot. The packet may be injected `max(1, d)` cycles after the grant, where d is the hop
    distance from the source to the boundary router.
  - A blocked outbound packet blocks its PE's injection queue (head of line, as in the paper's NI, Fig. 3d).
  - Intra-chiplet packets need no permission.
* **At the boundary router:**
  - An outbound head flit routed to the Up link (Hub) reserves one free RC FIFO instead of the Up output VC. One is
    always free because of the permission.
  - Its flits move from the input VC into the FIFO through the normal forwarding step (one flit per input port per
    cycle).
  - The RC FIFOs compete round-robin for the Up link. A packet keeps its VC, and the downstream VC is held from head
    to tail (wormhole).
  - The slot is released when the tail flit leaves the FIFO onto the Up link.
* **Deviations:**
  - No separate OPIC tree or RCVA pipeline timing: Noxim's router has no pipeline stages. The OPIC tree is
    represented by its latency (hop distance, at least 1 cycle) and FIFO service.
  - Grant latency is counted once (request and response together), which favours RC.
  - Deadlock freedom rests on RC's argument (outbound packets never hold chiplet VCs while waiting for the
    interposer), not on a CDG; the A5 drain tests decide.

## Reachability under faults (A6, DeFT Fig. 7)
Fraction of ordered (source, destination) chiplet-router pairs (source != destination) with a legal path. All pairs
are counted, intra-chiplet ones included (always reachable); the inter-chiplet-only fraction is also reported.
* **DeFT:** reachable iff both chiplets have a functional VL. The LUT generator assigns a functional VL to every
  (source, destination chiplet), and the v1/v4 formal checks found no dead end for any fixed functional pair.
* **CI, FULL:** reachable iff both chiplets have a functional VL. The formal checks found no dead end for any VL
  mask.
* **MTR (best case):** the turn restrictions are fixed at design time.
  - The source may use any functional boundary router it can reach under them (allowed outbound turn).
  - The destination may be entered through any functional boundary router that can reach it (allowed inbound
    turn).
* **RC:** the permission tree is fixed. A source can use only its own nearest boundary router's RC buffer (if that VL
  is faulty, all its outbound traffic is unreachable). The entry may be any functional boundary router of the
  destination chiplet.
