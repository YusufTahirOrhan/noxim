# v17 decisions (Part I: VC usage per link)

## Option
`-deft_lb vc_stats FILE`, default off (empty file name). It writes one JSON file with the counters of every link direction;
the normal stats file is unchanged. It works for every routing on DEFT_2_5D, plain DEFT included.

## How Noxim draws the VC at injection (checked in the code, recorded as required)
* `ProcessingElement::randInt(0, n_vc - 1)`: `min + (int)((double)(max - min + 1) * rand() / (RAND_MAX + 1.0))`, so **uniform over
  the 2 VCs**, per packet, from the run's `rand()` stream. Set for the table-driven traffic used here in the table branch of
  `ProcessingElement::canShot` (`int vc = randInt(...); packet.make(...)`), and in the same way for all other traffic types.
* **MTR and RC (`vn_rules 0`):** `DeftLB::prepareHeadPacket` leaves the drawn VC alone, and
  `DeftVirtualNetwork::selectOutputVirtualNetwork` returns the input VC on every hop. The VC is fixed from injection to
  ejection, as the Context says. `Router::rcDrain` also uses the flit's own VC on the Up link.
* **Methods with DeFT's VN rules (`vn_rules 1`):** the drawn VC is overwritten by `assignSourceVirtualNetwork`:
  - intra-chiplet packets: global round-robin over VN0 / VN1;
  - inter-chiplet packets: VN0, except that a boundary-router source committed to its own VL also gets round-robin (F1 fix);
  - on the way: the VC is kept, except Up link and destination chiplet (arrival on the Hub port): VN1.
  - A packet that is in VN0 therefore keeps VN0 **across the interposer**, up to the Up link. The Context does not mention
    the interposer; it is measured here as its own class.

## Link direction and counters (measured window: as all other statistics, `now - reset_time >= warm-up`)
A link direction is (router, output port), with output N, E, S, W or Hub; Local (ejection) is not a link. Per VC:
* **Flits forwarded:** counted where a flit is written to the link (`Router::txProcess`, `Router::rcDrain`), with the VC it has
  on that link.
* **VC-wait cycles of a head flit** (one count per waiting head per cycle, attributed to the wanted (output, VC)):
  - *VC held:* the head at an input-buffer front has no reservation and the reservation table answers `RT_OUTVC_BUSY` for the
    (output, VC) its route asks for in this cycle. Adaptive routing re-decides each cycle, so a head can count towards
    different outputs in different cycles.
  - *No credit:* the head owns (output, VC) and the downstream VC buffer is full (`buffer_full_status_tx`).
  - *RC buffer:* a head at the front of an RC-buffer slot counts as VC held when another slot owns the Up link's VC, and as no
    credit when the downstream VC buffer is full.
  - A head that owns its VC and loses only switch arbitration, or the handshake, is **not** counted.
* **Mean buffer occupancy:** the mean over the measured cycles of the downstream input buffer [port][VC] that the link feeds,
  sampled once per cycle at the end of the router's process.
* **Packet phase of each flit** (added to explain the result, not in the prompt): source chiplet, interposer, destination
  chiplet, intra-chiplet.

## Link classes (exact definitions)
`dist(r)` = footprint Manhattan distance from chiplet router r to the nearest functional VL endpoint of its chiplet. The runs
are fault-free, so all 4 VLs of each chiplet count.
* **`chip_towards`:** chiplet link r -> n (same chiplet) with `dist(n) < dist(r)`.
* **`chip_away`:** every other chiplet link (`dist(n) >= dist(r)`). All links leaving a VL router are here.
* **`ipos`:** horizontal interposer links.
* **`vl_down`:** Hub output of a chiplet boundary router.
* **`vl_up`:** Hub output of an interposer router with a VL.

Consequence: the class says where the link leads, not what the packet is doing. A "towards" link also carries packets of the
destination-phase and intra-chiplet traffic that happen to go that way. This is why the phase counters were added.

## Metrics
* **VC imbalance of a class:** sum over its link directions of |f0 - f1|, divided by the sum of f0 + f1. This equals the
  traffic-weighted mean of |f0 - f1| / (f0 + f1) requested.
* **VC share:** sum f0 and sum f1 over the class.
* **VC-wait cycles per flit:** (VC held + no credit head cycles) / flits forwarded, per class.
* Values are computed per run and averaged over the 3 seeds. "Chiplet links" in the figure means both chiplet classes, summed within
  each run.

## Runs
* Load points: `results_v5/load_points.json`, positions 2 and 3 of the evaluation list (0.8 and 1.0 x DeFT's Lsat), as in v10.
* Methods: `experiments_v10.methods` exactly; LUT: DeFT's rho* uniform LUT, for every pattern, as in v10.
* Diagnostics as in `sanity_diag_v10.py`:
  - `MTR_VN`: MTR's arguments with `vn_rules 1`, at both loads;
  - `DeFT_LUT_noVN`: `exit lut, entry lut`, XY, `vn_rules 0`, at 0.8 x Lsat only.
* **Deadlock flag (diagnostic configurations and all others):** accepted flits below 50 % of DeFT(rho*) in the same cell (size,
  pattern, load, seed). The rule is taken over from the sanity check's reading of a collapsed throughput; it detects a collapse, not a
  cycle in the channel graph. A run in which only part of the network deadlocks late in the window can escape it.

## Checks
* Regression, option off: 84 / 84 byte-identical against a binary built from 3ac1bae in a separate worktree (`regression.md`).
* Option on vs off: 5 / 5 stats files byte-identical (`oncheck.md`).
