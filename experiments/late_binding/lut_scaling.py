"""How the DeFT LUT objective scales with system size (results_v5/lut_scaling.md).

LUT objective per optimisation problem: rho * sum(distance) + sum_v |load_v - mean| / mean.
For each size and rho this builds the LUT's optimisations exactly as deft_vl_lut_generator.py
does (source exit per chiplet, destination entry per chiplet) and reports, fault-free:
  * demand points per exit / entry problem,
  * the distance term (rho * sum distance) and the balance term at the optimum,
  * the analytic VL load imbalance: per VL, the traffic of the sources whose exit it is (down)
    plus the traffic of the flows whose entry it is (up), from the pattern's traffic table;
    imbalance = max / mean over all VLs.
Usage: python3 lut_scaling.py               -> rho = 0.01 table for 2x2, 3x3, 4x4
       (analyze(size, rho, pattern) is reused by the v5 tuning report)
"""
import os
import sys
from fractions import Fraction
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'other'))
import deft_vl_lut_generator as G  # noqa: E402

SIZES = {'2x2': (2, 2), '3x3': (3, 3), '4x4': (4, 4)}


def table_path(size, pattern):
    d = 'traffic' if size == '2x2' else f'traffic_{size}'
    return Path(HERE) / d / f'{pattern}_0.0100.txt'


def analyze(size, rho, pattern='uniform', mask=0):
    """Optimise as the generator does; return per-problem terms and the analytic VL imbalance."""
    G.set_size(*SIZES[size], 4, 4)
    rho = Fraction(rho)
    demand = G.read_demand_table(table_path(size, pattern))
    use_w = pattern != 'uniform'
    func = G.functional_vl_ids(mask)
    src, dst = {}, {}
    for c in range(G.CHIPLET_COUNT):
        src[c] = G.optimize_assignments(G.source_demand_points(c), G.links_for_chiplet(c, func), rho,
                                        G.source_weights(c, demand) if use_w else None)
    for c in range(G.CHIPLET_COUNT):
        dst[c] = G.optimize_assignments(G.destination_demand_points(c, src), G.links_for_chiplet(c, func), rho,
                                        G.destination_weights(c, demand) if use_w else None)
    # physical VL loads (packets/cycle at the table's rate): down via exits, up via entries
    load = {v: Fraction(0) for v in func}
    for c in range(G.CHIPLET_COUNT):
        sw = G.source_weights(c, demand)
        for key, v in src[c].selected_by_key.items():
            load[v] += sw[key]
        dw = G.destination_weights(c, demand)
        for key, e in dst[c].selected_by_key.items():
            load[e] += dw[key]
    vals = [float(x) for x in load.values()]
    mean = sum(vals) / len(vals)

    def terms(res):
        return float(rho * res.total_distance_cost), float(res.load_imbalance_cost)
    sterms = [terms(src[c]) for c in src]
    dterms = [terms(dst[c]) for c in dst]
    n_src = len(G.source_demand_points(0))
    n_dst = len(G.destination_demand_points(0, src))
    return dict(size=size, rho=float(rho), pattern=pattern, n_src=n_src, n_dst=n_dst,
                src_dist=sum(t[0] for t in sterms) / len(sterms), src_bal=sum(t[1] for t in sterms) / len(sterms),
                dst_dist=sum(t[0] for t in dterms) / len(dterms), dst_bal=sum(t[1] for t in dterms) / len(dterms),
                src_hops=sum(src[c].total_distance_cost for c in src) / len(src) / n_src,
                dst_hops=sum(dst[c].total_distance_cost for c in dst) / len(dst) / n_dst,
                imbalance=max(vals) / mean, cv=(sum((x - mean) ** 2 for x in vals) / len(vals)) ** 0.5 / mean)


def main():
    rows = [analyze(s, '0.01') for s in SIZES]
    L = ['# DeFT LUT objective vs system size (uniform LUT, rho = 0.01, fault-free)', '',
         'Objective of every LUT optimisation: rho * sum(distance) + sum_v |load_v - mean| / mean (deft_vl_lut_generator.py).',
         'The balance term is normalised by the mean load and is at most about 2 regardless of the number of demand',
         'points n, while the distance term grows linearly with n. So the larger the problem, the less balance is',
         'worth against distance.', '',
         '| size | exit problem: points | exit: distance term | exit: balance term | exit: mean hops | entry problem: points | '
         'entry: distance term | entry: balance term | entry: mean hops | analytic VL imbalance (max/mean) | CV |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append(f'| {r["size"]} | {r["n_src"]} | {r["src_dist"]:.3f} | {r["src_bal"]:.3f} | {r["src_hops"]:.2f} | '
                 f'{r["n_dst"]} | {r["dst_dist"]:.3f} | {r["dst_bal"]:.3f} | {r["dst_hops"]:.2f} | '
                 f'{r["imbalance"]:.3f} | {r["cv"]:.3f} |')
    L += ['', 'Terms are means over the chiplets of a size (one exit and one entry problem per chiplet). The distance',
          'term is rho times the total Manhattan distance (in hops) of the problem\'s points to their VLs. The analytic',
          'imbalance uses the uniform traffic table: each VL carries the down traffic of the sources whose exit it',
          'is plus the up traffic of the flows whose entry it is.', '',
          'Measured in v4 (DEFT_LB proxy with the uniform-pattern LUT, uniform traffic, ~1.0 x Lsat, fault-free):',
          'VL imbalance 1.07 (2x2, v2), 1.06 (3x3), 1.43 (4x4). The entry problem grows from 48 points (2x2) to 240',
          '(4x4), while its balance term stays bounded.']
    out = os.path.join(HERE, 'results_v5', 'lut_scaling.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
