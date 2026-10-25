# Decisions taken without the author (v10, Parts A-B)

The conservative option is the one that does not favour our methods. Design of the baselines:
`BASELINES_DESIGN.md` (committed before any code, 2fe2c79).

## Environment
1. **Hardware, memory, disk.** 12 hardware threads, WSL memory limit 7.9 GB (unchanged), 12 runner processes.
   C: had about 4.6 GB free (D: 395 GB available, not needed so far). Raw outputs are deleted after aggregation.

## A1-A3: implementation
2. **Vehicle.** All VL-pair baselines run on the DEFT_LB relation with singleton masks and XY on both layers, which is
   the DeFT relation (traffic-identical to plain DEFT with the same LUT: v2/v4/v5, and again in the v10 smoke test:
   DEFT and the LUT proxy give identical results and VL counts). Reason: DeFT's LUT format cannot express an entry
   that depends on the destination router (needed for DeFT-Dis and RC), and the per-packet choice of DeFT-Ran must
   travel with the packet.
3. **DeFT-Ran RNG:** `std::mt19937` seeded with the run seed (`-seed`), separate from `rand()`. The traffic generator's
   stream is therefore that of every other method; network-dependent effects (back-pressure) still differ.
4. **MTR search:** exhaustive instead of the paper's recursion; global optimum of the paper's objective. Ties: fewer
   prohibited turns, then lexicographic. Result (`mtr_search.md`):
   - Inbound turns are restricted to the Y directions at all four boundary routers, so each boundary router serves
     exactly its own column; the four VL routers sit in four different columns.
   - All outbound turns stay allowed.
   - The assignment balances 4 / 4 / 4 / 4 nodes in both directions.
   - Horizontal turns at boundary routers are excluded by the connectivity constraint (all 8 are used by
     intra-chiplet XY routes).
5. **MTR deadlock check:** the full-system physical-channel CDG of the MTR routing function is acyclic on 2x2, 3x3,
   4x4 (fault-free), and every route uses only allowed boundary turns (`mtr_cdg_check.md`).
6. **MTR and RC VCs:** DeFT's VN rules off (`vn_rules 0`). The PE draws the VC uniformly at injection (Noxim's
   default) and the packet keeps it on every hop, also through the RC buffer.
7. **RC permission timing:**
   - The request enters the boundary router's FIFO when the head flit is at the front of the PE queue.
   - A grant happens as soon as a slot is free (checked every cycle).
   - The packet may leave `max(1, hops)` cycles after the grant.
   - The slot is released when the tail leaves the RC buffer onto the Up link, and the next request is granted in
     the same cycle.
   - The OPIC tree's request and response latencies are counted once (favours RC).
8. **RC buffer in the router:**
   - An outbound head routed to the Hub at a chiplet boundary router reserves a free RC slot (instead of the Up
     output VC).
   - Its flits move into the slot through the input port's normal forwarding step: one flit per input port per
     cycle, competing with the port's other reservations.
   - Slots drain round-robin onto the Up link, one flit per cycle; a packet holds its downstream VC from head to tail.
   - There is no separate VA/RCVA stage, because Noxim's router has no pipeline stages.
9. **RC exit policy:** RC uses the same `near` choice as DeFT-Dis (nearest boundary router to the source / destination,
   ties to the lowest VL id), as the task prescribes.

## A4
10. **Sharding:** jobs are sorted by name and job k belongs to shard k mod n. The flag is removed from `sys.argv` when
    `runner` is imported, so every experiment script accepts it. Per-shard CSVs are merged with `merge_csv.py`; a key
    seen twice with different values aborts the merge.
11. **.gitattributes:**
    - LF for sources, scripts and data (`*.cpp *.h *.py *.sh *.md *.yaml *.json *.csv *.txt Makefile*`); PDF and PNG
      binary.
    - The eight round-1 result CSVs, which were committed with CRLF, are marked `-text` so their bytes stay unchanged.
    - The working tree was rewritten to LF; only line endings changed. The rebuilt binary is byte-identical (md5
      1684544f...).
12. **Plain-DEFT VL counter:** added (`-deft_lb count_vl 1`, off by default). It counts head flits leaving on a Hub port
    for routings other than DEFT_LB (DEFT, INTERPOSER_AWARE_XY). With the flag on, plain DEFT's results are unchanged and
    its VL counts equal the LUT proxy's.

## A5
13. **Regression baseline:** a build of 4953092 (v9) made from a clean stash of the tree (md5 bf4f9da9...). The binary
    used in v8/v9 had been overwritten by a rebuild before it was copied; the v9 reuse check below compares the new
    binary directly with the v9 data.
14. **Drain tests:**
    - 2x2: the v2 protocol (all-pairs burst on the 11 v2 VL masks x 2 seeds; uniform, chipperm and hotspot at
      0.03 on 4 masks), with the v2 uniform LUT, which holds all 11 masks.
    - 3x3/4x4: the all-pairs burst on the fault-free and one-faulty-VL-per-chiplet masks x 2 seeds, plus (added in
      v10, more testing than before) uniform, chipperm and hotspot at the top v5 load (1.6 x Lsat) of each mask.
    - MTR and RC are tested fault-free only.
15. **DeFT_OE_G formal check:** a new configuration `FIXED_OE_OE` of the relation checker (exit and entry any functional
    singletons, odd-even on both layers, DeFT VNs) on 2x2 (22 masks) and 3x3 (6 masks).
16. **Sanity check:** seeds 1001-1003 (not evaluation seeds), 2x2 uniform at 0.8-1.6 x Lsat.

## A6: reachability definitions
17. **Masks:**
    - k = floor(rate x #VLs) faulty VLs: 2x2 1 / 2 / 4, 3x3 2 / 4 / 9, 4x4 4 / 8 / 16. Flooring gives fewer faults
      on 3x3, which favours MTR and RC.
    - Up to 1000 distinct masks per (size, rate) with at least one functional VL per chiplet, drawn with
      `random.Random(2210)`.
    - Where at most 4000 masks exist, they are enumerated and sampled (2x2: all 16 and 120 masks for k = 1, 2).
18. **Reachability:** fraction of all ordered pairs of distinct chiplet routers (intra-chiplet pairs included, always
    reachable); the inter-chiplet-only fraction is reported too.
19. **Method definitions:**
    - **DeFT:** its LUT for the mask selects functional VLs for every pair (the LUT loader rejects a faulty
      selection), and every fixed functional pair is deliverable (formal checks), so 100 % whenever every chiplet
      has a functional VL.
    - **CI, FULL:** no dead end for any VL mask (formal checks v1/v4/v7), so 100 %.
    - **MTR, best case:** a source may use any functional boundary router it can reach under the fixed restrictions,
      and a destination may be entered through any functional boundary router allowed to reach it.
    - **RC:** a source may use only its own fault-free nearest boundary router's RC buffer, and the entry may be any
      functional boundary router of the destination chiplet.
20. **Sanity check not met:** DeFT(rho*) is slower than MTR and RC on 2x2 uniform. The investigation
    (`sanity_check.md`) attributes the gap to DeFT's VN rules, which MTR and RC do not need: with DeFT's VN rules,
    MTR's routes perform like DeFT. The baselines stay as specified (the conservative choice), and the result is
    reported.
21. **XY-SP is valid:** all its drain tests pass (54 / 54, 2x2 v2 masks and 3x3/4x4), so it stays in the evaluation.
