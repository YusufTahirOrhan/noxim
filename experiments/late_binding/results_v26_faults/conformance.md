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
| DeFT_P | A_fixed_XY | 2x2 | 1 | 4 | 4 | 188489 | 0 | 22726 | 102806 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 2x2 | 1 | 4 | 4 | 193680 | 31864 | 22770 | 127611 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 2x2 | 1 | 4 | 4 | 194227 | 32241 | 22769 | 127423 | 0 | **0** |
| DeFT_P | A_fixed_XY | 3x3 | 1 | 4 | 4 | 370564 | 0 | 32052 | 316023 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 3x3 | 1 | 4 | 4 | 378367 | 49193 | 32269 | 347232 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 3x3 | 1 | 4 | 4 | 379741 | 49939 | 32261 | 349723 | 0 | **0** |
| DeFT_P | A_fixed_XY | 4x4 | 1 | 4 | 4 | 618167 | 0 | 42845 | 593708 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 4x4 | 1 | 4 | 4 | 629846 | 68922 | 43039 | 624191 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 4x4 | 1 | 4 | 4 | 630529 | 69695 | 43023 | 625492 | 0 | **0** |

**Total: 3583610 hops and 293754 arrivals compared in 36 runs; mismatches: 0; topology differences: 0; runs with statistics byte-identical to `bin/noxim`: 36 of 36.**

Hops by phase of the model (all rows and sizes): intra-chiplet 124911, source chiplet 507039, interposer 2583432, destination chiplet 661982. Dead-end events in these runs: 0.
Per (row, size, mask, seed): `conformance.csv`.

Fewer than 1000000 compared hops so far: DeFT_P 2x2 (188489); CI_heurLA_X_LF 2x2 (193680); CI_heurLA_O_LF 2x2 (194227); DeFT_P 3x3 (370564); CI_heurLA_X_LF 3x3 (378367); CI_heurLA_O_LF 3x3 (379741); DeFT_P 4x4 (618167); CI_heurLA_X_LF 4x4 (629846); CI_heurLA_O_LF 4x4 (630529).

**0 mismatches, as required: yes.**
