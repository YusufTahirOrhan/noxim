"""v29: descriptive tables that were added after the results of a part were seen (DECISIONS.md says why). Nothing here is a test and
nothing of report_v29.py is changed; FINDINGS.md marks every number it takes from here.

  python3 extra_v29.py [b]      ->  results_v29_review/report/extra_B.md
     X.1  the one test of family 1 that is against the main row (THR against the best reference on 2x2) comes from randperm: accepted
          throughput and latency of every row at each of the nine loads on 2x2 randperm (mean over the ten seeds), and the load at which
          each row's accepted throughput is the largest
"""
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V29_RES', os.path.join(HERE, 'results_v29_review'))
OUT = os.path.join(RES, 'report')
NL = chr(10)
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]


def write(name, L):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)
    print('wrote report/%s (%d lines)' % (name, len(L)))


def part_b():
    P = json.load(open(os.path.join(RES, 'load_points_v29.json')))
    R = defaultdict(list)
    for r in csv.DictReader(open(os.path.join(RES, 'heldout_runs.csv'))):
        R[(r['variant'][:-3], r['pattern'], float(r['rate']))].append((float(r['accepted']), float(r['latency'])))
    L = ['# v29 Part B: tables added after the results were seen (extra_v29.py b)', '',
         'Descriptive; not in the pre-registration. `DECISIONS.md` ("Tables added after the results") says why each is here.', '',
         '## X.1 Accepted throughput (flits/node/cycle) and mean latency (cycles) at each load, mean over the ten seeds', '',
         'The one test of primary family 1 that is against the main row is THR against the best reference on 2x2, and it comes from `randperm` (B.2). THR is the largest',
         'accepted throughput over the nine loads. The table shows at which loads the rows differ. **Bold**: the largest accepted throughput of the load.', '']
    for z, pat in (('2x2', 'randperm'), ('2x2', 'tornado'), ('2x2', 'neighbour'), ('3x3', 'randperm'), ('4x4', 'randperm')):
        key = [k for k in P if k.startswith('%s__%s__' % (z, pat))][0]
        rates = P[key]['eval']
        rows = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP', 'CI_heurLA_X_LF'] + (['LB_b0'] if z == '2x2' else [])
        L += ['### %s, %s (Lsat of DeFT_P %.4f packets/cycle/source)' % (z, pat, P[key]['lsat']), '',
              '| load | offered | ' + ' | '.join(rows) + ' |', '|---|---|' + '---|' * len(rows)]
        peak = {}
        for m, x in zip(MULTS, rates):
            acc = {r: sum(a for a, _ in R[(r, '%s-%s' % (z, pat), x)]) / len(R[(r, '%s-%s' % (z, pat), x)]) for r in rows}
            lat = {r: sum(l for _, l in R[(r, '%s-%s' % (z, pat), x)]) / len(R[(r, '%s-%s' % (z, pat), x)]) for r in rows}
            best = max(acc.values())
            for r in rows:
                if r not in peak or acc[r] > peak[r][1]:
                    peak[r] = (m, acc[r])
            L.append('| %.1f x Lsat | %.4f | ' % (m, 8 * x) + ' | '.join(('**%.4f** / %.0f' if abs(acc[r] - best) < 5e-5 else '%.4f / %.0f') % (acc[r], lat[r]) for r in rows) + ' |')
        L += ['| the load of the largest mean accepted throughput | | ' + ' | '.join('%.1f x Lsat' % peak[r][0] for r in rows) + ' |', '']
    write('extra_B.md', L)


if __name__ == '__main__':
    parts = sys.argv[1:] or ['b']
    for p in parts:
        globals()['part_' + p]()
