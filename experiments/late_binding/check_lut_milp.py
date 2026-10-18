"""Check the MILP solver of deft_vl_lut_generator.py against its exact DP (results_v4/lut_milp_check.md).

On the default 2x2 instance every optimisation (source exit per chiplet, destination entry per
chiplet; 11 drain masks; uniform demand and the chipperm and hotspot demand tables) is solved by
both the dynamic programme and the MILP. The optimal objective values must agree (the chosen
assignments may differ only where several assignments are equally good).
Usage: python3 check_lut_milp.py
"""
import os
import sys
import time
from fractions import Fraction
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'other'))
import deft_vl_lut_generator as G  # noqa: E402


def main():
    masks = [int(l.strip(), 16) for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    rho = Fraction(G.DEFAULT_RHO)
    demands = {'uniform': None}
    for p in ('chipperm', 'hotspot'):
        demands[p] = G.read_demand_table(Path(HERE) / 'traffic' / f'{p}_0.0100.txt')
    rows, worst, n, same_assign = [], 0.0, 0, 0
    t = time.time()
    for name, demand in demands.items():
        for mask in masks:
            func = G.functional_vl_ids(mask)
            src = {}
            for c in range(G.CHIPLET_COUNT):
                pts = G.source_demand_points(c)
                wts = None if demand is None else G.source_weights(c, demand)
                dp = G.optimize_assignments(pts, G.links_for_chiplet(c, func), rho, wts)
                mi = G.optimize_assignments_milp(pts, G.links_for_chiplet(c, func), rho, wts)
                src[c] = dp
                d = abs(float(dp.total_cost - mi.total_cost))
                worst, n = max(worst, d), n + 1
                same_assign += dp.selected_by_key == mi.selected_by_key
            for c in range(G.CHIPLET_COUNT):
                pts = G.destination_demand_points(c, src)
                wts = None if demand is None else G.destination_weights(c, demand)
                dp = G.optimize_assignments(pts, G.links_for_chiplet(c, func), rho, wts)
                mi = G.optimize_assignments_milp(pts, G.links_for_chiplet(c, func), rho, wts)
                d = abs(float(dp.total_cost - mi.total_cost))
                worst, n = max(worst, d), n + 1
                same_assign += dp.selected_by_key == mi.selected_by_key
        rows.append(f'- {name}: done')
    lines = ['# MILP vs exact DP in the LUT generator (default 2x2 instance)', '',
             f'Optimisations compared: {n} (11 masks x 4 chiplets x source/destination x 3 demand profiles).',
             f'Largest |objective(DP) - objective(MILP)|: {worst:.3e}.',
             f'Identical assignments: {same_assign} of {n} (the rest are equally good alternatives).',
             f'Elapsed: {time.time() - t:.0f} s.', '',
             'The MILP reaches the DP optimum in every case, so it is used for problems with more than '
             f'{G.DP_MAX_POINTS} demand points (destination entry on 3x3 and larger grids).' if worst < 1e-9 else
             '**MISMATCH: the MILP does not reach the DP optimum in every case.**']
    open(os.path.join(HERE, 'results_v4', 'lut_milp_check.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return worst < 1e-9


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
