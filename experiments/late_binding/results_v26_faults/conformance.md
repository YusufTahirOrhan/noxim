# v26 A3: conformance of the model with the simulator (experiments_v26.py a3_build, a3_run, a3_report)

An instrumented copy of the simulator (`conf/patch_hopdump.py`, `conf/hopdump.inc`; the repository's sources and `bin/noxim` are unchanged) records every hop of a
head flit: router, input port, VN before, candidate masks before, destination, the outputs the routing function and the VN rule offer, the output taken, the VN and
the masks after. Every record is looked up in the state graph that `formal/impl_relation_check.explore()` builds for the destination (the function the model check
uses, unchanged, with the settings of `xy_check.py`): (1) the state before the hop is a node of the graph, (2) the offered outputs equal the moves on the edges
leaving the node, (3) the hop taken is one of those edges. The arrival at the destination router is compared too (the model must have delivered there).
Relations: DeFT_P -> `A_fixed_XY`, `CI_heurLA_X_LF` -> `CI_XY_XY`, `CI_heurLA_O_LF` -> `CI_XY_O1`. Runs: pipe_all 2, uniform and hotspot at 1.0 x Lsat of DeFT_P, six
masks per size (fault-free, the same VL faulty in every chiplet, mask 1 of each rate of Part B). Before the replay the geometry and the options the simulator
reports (VL positions, functional VLs, directions, turn models, VN options) are compared with the model's instance.

| row | relation | size | seeds | runs | statistics byte-identical to bin/noxim | hops compared | of them with more than one offered output | arrivals at the destination compared | distinct records | topology differences | mismatches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DeFT_P | A_fixed_XY | 2x2 | 1, 2 | 24 | 24 | 1019444 | 0 | 120746 | 581928 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 2x2 | 1, 2 | 24 | 24 | 1042044 | 159670 | 120991 | 697515 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 2x2 | 1, 2 | 24 | 24 | 1044590 | 160308 | 120961 | 700688 | 0 | **0** |
| DeFT_P | A_fixed_XY | 3x3 | 1, 2 | 16 | 16 | 1405704 | 0 | 119757 | 1205253 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 3x3 | 1, 2 | 16 | 16 | 1430288 | 174044 | 120637 | 1311072 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 3x3 | 1, 2 | 16 | 16 | 1433461 | 176233 | 120620 | 1315773 | 0 | **0** |
| DeFT_P | A_fixed_XY | 4x4 | 1 | 12 | 12 | 1531555 | 0 | 103991 | 1483238 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 4x4 | 1 | 12 | 12 | 1545058 | 152460 | 104603 | 1534708 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 4x4 | 1 | 12 | 12 | 1547281 | 153300 | 104596 | 1538168 | 0 | **0** |

**Total: 11999425 hops and 1036902 arrivals compared in 156 runs; mismatches: 0; topology differences: 0; runs with statistics byte-identical to `bin/noxim`: 156 of 156.**

Seeds: seed 1 on every mask; seeds 2, 3, ... are added for a row and size that has fewer than 1000000 compared hops. 2x2: seeds 1, 2 on all 6 masks (seed 1 alone: 503018 to 514811 hops per row). 3x3: seeds 1, 2 on the masks "fault-free", "same VL in every chiplet"; seed 1 on the masks "rate 1/16, mask 1", "rate 2/16, mask 1", "rate 4/16, mask 1", "rate 8/16, mask 1" (seed 1 alone: 1031945 to 1050718 hops per row). 4x4: seed 1 on all 6 masks (seed 1 alone: 1531555 to 1547281 hops per row).

Records (hops and arrivals) by phase of the model, all rows and sizes: intra-chiplet 518405, source chiplet 1842950, interposer 8388635, destination chiplet 2286337. Dead-end events in these runs: 0.
Per (row, size, mask, seed): `conformance.csv` (its four `records_` columns are these phases).

**0 mismatches, as required: yes.**
