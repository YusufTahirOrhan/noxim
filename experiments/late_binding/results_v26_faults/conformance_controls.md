# v26 A3: controls of the comparison (experiments_v26.py a3_control)

The comparison must be able to fail. Hops of 2x2 runs (uniform and hotspot at 1.0 x Lsat, seed 1) are replayed through a model that is deliberately not the
one of the run; each control must report mismatches. "The right model" lines replay the same hops through the model of the run and must report none.

| control | hops of | replayed through | records compared | mismatches | kinds |
|---|---|---|---|---|---|
| the right model | CI_heurLA_O_LF, mask 0x0000 | CI_XY_O1, mask 0x0000 | 119541 | 0 | - |
| the other interposer order | CI_heurLA_O_LF, mask 0x0000 | CI_XY_XY, mask 0x0000 | 119541 | 33625 | offered outputs differ: 4854; state before the hop is not a state of the model: 28771 |
| the right model | CI_heurLA_X_LF, mask 0x0000 | CI_XY_XY, mask 0x0000 | 119328 | 0 | - |
| the Up rule of rounds 1-22 (the Up channel is VN1) | CI_heurLA_X_LF, mask 0x0000 | CI_XY_XY, mask 0x0000, UP_KEEP = False | 119328 | 9770 | state before the hop is not a state of the model: 4883; the hop taken is not a transition of the model: 4887 |
| the entry fixed at injection | CI_heurLA_X_LF, mask 0x0000 | A_fixed_XY, mask 0x0000 | 119328 | 53816 | state before the hop is not a state of the model: 53816 |
| the right model | DeFT_P, mask 0x1111 | A_fixed_XY, mask 0x1111 | 95596 | 0 | - |
| another fault mask (VL 1 faulty in every chiplet instead of VL 0) | DeFT_P, mask 0x1111 | A_fixed_XY, mask 0x2222 | 95596 | 54171 | state before the hop is not a state of the model: 54171 |

**Every control behaves as expected: yes.**
