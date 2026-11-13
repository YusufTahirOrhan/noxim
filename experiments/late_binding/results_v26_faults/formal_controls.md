# v26 Part A: controls (experiments_v26.py aneg)

The checks must be able to fail. 2x2, the fault-free mask.

## (a) R3 and the F1 source rule removed (`impl_relation_check.NO_R3 = True`)

| relation | CDG acyclic | expected |
|---|---|---|
| A_fixed_XY | **no: cyclic** | no (the control of `xy_check.py`) |
| CI_XY_XY | **no: cyclic** | reported |
| CI_XY_O1 | **no: cyclic** | reported |

## (b) The subset check between two relations

Fault-free CDG: `CI_XY_XY` 800 nodes / 1424 edges, `CI_XY_O1` 800 nodes / 1424 edges, the fixed pair `A_fixed_XY` 800 / 1424 (all three acyclic: yes).
Edges of `CI_XY_O1` that are not edges of `CI_XY_XY`: **184** (expected: more than 0, so the subset check reports a failure here). Edges of `CI_XY_XY` that are
not edges of `CI_XY_O1`: 184. Edges of the fixed pair that are not edges of `CI_XY_XY`: 0 (the fixed pair is the late entry with one candidate).

**Both controls behave as expected: yes.**
