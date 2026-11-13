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
| DeFT_P | A_fixed_XY | 2x2 | 1, 2 | 8 | 8 | 382842 | 0 | 46088 | 207039 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 2x2 | 1, 2 | 8 | 8 | 393744 | 64918 | 46178 | 257567 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 2x2 | 1, 2 | 8 | 8 | 394968 | 65513 | 46170 | 258542 | 0 | **0** |
| DeFT_P | A_fixed_XY | 3x3 | 1, 2 | 8 | 8 | 744323 | 0 | 64548 | 633771 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 3x3 | 1, 2 | 8 | 8 | 759959 | 98733 | 64950 | 697177 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 3x3 | 1, 2 | 8 | 8 | 762484 | 100244 | 64944 | 701840 | 0 | **0** |
| DeFT_P | A_fixed_XY | 4x4 | 1 | 4 | 4 | 618167 | 0 | 42845 | 593708 | 0 | **0** |
| CI_heurLA_X_LF | CI_XY_XY | 4x4 | 1 | 4 | 4 | 629846 | 68922 | 43039 | 624191 | 0 | **0** |
| CI_heurLA_O_LF | CI_XY_O1 | 4x4 | 1 | 4 | 4 | 630529 | 69695 | 43023 | 625492 | 0 | **0** |

**Total: 5316862 hops and 461785 arrivals compared in 60 runs; mismatches: 0; topology differences: 0; runs with statistics byte-identical to `bin/noxim`: 60 of 60.**

Hops by phase of the model (all rows and sizes): intra-chiplet 222887, source chiplet 782428, interposer 3758997, destination chiplet 1014335. Dead-end events in these runs: 0.
Per (row, size, mask, seed): `conformance.csv`.

Fewer than 1000000 compared hops so far: DeFT_P 2x2 (382842); CI_heurLA_X_LF 2x2 (393744); CI_heurLA_O_LF 2x2 (394968); DeFT_P 3x3 (744323); CI_heurLA_X_LF 3x3 (759959); CI_heurLA_O_LF 3x3 (762484); DeFT_P 4x4 (618167); CI_heurLA_X_LF 4x4 (629846); CI_heurLA_O_LF 4x4 (630529).

**0 mismatches, as required: yes.**
