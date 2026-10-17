# DEFT_LB experiments: directions A, B and C

Code: `src/DeftLateBinding.{h,cpp}`, routing `DEFT_LB`, selections `DEFT_HEUR`, `DEFT_QL`.

## What is compared

| Variant | Direction | Routing relation | VL decision | Information used |
|---|---|---|---|---|
| `DeFT` | baseline | DeFT (XY, fixed pair) | offline LUT (rho = 0.01) | none at run time |
| `A_mindist` | A | DeFT (XY, fixed pair) | at injection: minimal total hops | static distance |
| `A_random` | A | DeFT (XY, fixed pair) | at injection: uniform random pair | none |
| `A_oracle` | A (upper bound) | DeFT (XY, fixed pair) | at injection: hops + beta * occupancy near both VLs | instantaneous global state (not implementable) |
| `CI_random` | control | interposer-only late binding (chiplets XY, exit from LUT, interposer OE) | random among legal outputs | none |
| `CI_heur` | C | same as CI | stateless heuristic | router-local |
| `CI_ql` | B | same as CI | Q-learning | router-local + learned residual |
| `FULL_random` | control | full late binding (OE on chiplets and interposer) | random | none |
| `FULL_heur` | C | full late binding | stateless heuristic | router-local |
| `FULL_heurLA` | C (wider budget) | full late binding | heuristic with one-hop lookahead | router-local + neighbour's downstream occupancy |
| `FULL_ql` | B | full late binding | Q-learning | router-local + learned residual |

### Boundaries of the heuristic (direction C)

A heuristic here is a fixed, stateless rule:
* it uses only what the router observes in the current cycle: for each legal output,
  the number of flits in the downstream input buffer of the output VC (what a credit
  counter reports) and whether the output VC is held by another packet;
* it adds static topology knowledge: the minimal remaining hop count after the move
  (towards the best remaining exit/entry candidate);
* cost(o) = heur_w * downstream_flits(o) + heur_busy * [output VC busy] + hops_after(o);
  the minimum wins, ties are broken at random;
* no memory, no learning, no global or remote information; the two weights are chosen
  once on tuning seeds (101, 102) from a 3x3 grid and frozen.
`FULL_heurLA` widens the budget by one hop (the neighbour's downstream occupancy on its
cheapest continuation) to show what more information buys without learning.

### Q-learning (direction B)

cost(o) = ql_w * downstream_flits(o) + ql_busy * [busy] + hop_cost * hops_after(o) + R(o).
R is a learned residual (time beyond the static hop estimate), kept per router, output
port and destination chiplet (`ql_key 1`) or destination router (`ql_key 0`). When a head
flit reaches the front of an input buffer, the router that sent it updates
R <- R + alpha * (1 + V_here - hop_cost * hops_after - R), where V_here is the receiving
router's minimum cost over its legal outputs (TD(0), observed local costs as step costs).
With alpha = 0 the learner is exactly the heuristic (checked: identical runs). The local
weights are set to the heuristic's tuned values, so B and C differ only by learning.
Safety does not depend on the selection: both choose only among legal outputs of the
routing relation.

### Safety evidence
* `formal/impl_relation_check.py`: model check of the implemented relations (fixed pair,
  CI, FULL) on 897 fault masks (CDG acyclic, no dead ends, no livelock).
* `drain_tests.py`: drain-mode runs for every variant (all-pairs burst on 11 masks x 2
  seeds, over-saturated random tables on 4 masks): every packet delivered, no dead ends.

## Reproduce
```
python3 gen_traffic.py traffic
python3 ../../other/deft_vl_lut_generator.py $(sed 's/^/--fault-mask /' drain_masks.txt) --output luts/lut_rho001.yaml
python3 formal/impl_relation_check.py all 2
python3 drain_tests.py 2
python3 experiments.py sat 2  && python3 analyze.py sat   # then choose load points (results/load_points.json)
python3 experiments.py tune 2 && python3 experiments.py tune_ql 2 && python3 analyze.py tune
python3 experiments.py eval 2 && python3 analyze.py eval
```
