"""v16 exploratory: per-scenario LAT log ratio (fixed point / float) at 1.0 x Lsat, mean and sd over seeds 41-45.
Output: results_v16_qbits/report/exploratory_per_scenario_lat.txt. Not part of the pre-registered test."""
import csv, math, statistics as st, sys, os
sys.path.insert(0, '.')
from report_v16 import scen
def load(f):
    return {(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed'])): r for r in csv.DictReader(open(f))}
v9 = load('results_v9/eval_runs.csv'); new = load('results_v16_qbits/eval_runs.csv')
for z in ('2x2', '3x3', '4x4'):
    for v in ('CI_qlLA_G', 'FULL_qlLA_G'):
        for b in (16, 12, 8):
            out = []
            for p, m in scen(z):
                rates = sorted({k[3] for k in new if k[0] == f'{v}-b{b}' and k[1] == p and k[2] == m})
                r = rates[3]
                xs = [math.log(float(new[(f'{v}-b{b}', p, m, r, s)]['latency']) / float(v9[(v, p, m, r, s)]['latency'])) for s in range(41, 46)]
                tag = p.split('-')[1][:5] + ('F' if int(m, 16) else '')
                out.append(f'{tag} {100*(math.exp(st.mean(xs))-1):+.1f}(sd {100*st.stdev(xs):.1f})')
            print(z, v, b, ' | '.join(out))
