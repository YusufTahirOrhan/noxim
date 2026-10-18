"""Re-run the v2 primary analysis (results_v2/PREREGISTRATION.md) from results_v2/eval_runs.csv alone.

Independent of report_v2.py and of the raw outputs: the load ladder of each scenario is read
from the CSV (its 7 distinct rates; LAT uses the 2nd, saturation throughput the maximum
accepted throughput over all 7, capped if the maximum is at the top rate and >= 95 % of it).
Writes results_v3/primary_from_csv.csv in the format of results_v2/report/primary.csv and
compares the two files byte for byte (and value by value).
Usage: python3 primary_from_csv.py
"""
import collections
import csv
import math
import os

from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'results_v2', 'eval_runs.csv')
REF = os.path.join(HERE, 'results_v2', 'report', 'primary.csv')
OUT = os.path.join(HERE, 'results_v3', 'primary_from_csv.csv')
# Pre-registered order of scenarios and comparisons (results_v2/PREREGISTRATION.md).
SCEN = [('uniform', '0x0000'), ('localized', '0x0000'), ('hotspot', '0x0000'), ('chipperm', '0x0000'),
        ('movinghot', '0x0000'), ('uniform', '0x1111'), ('uniform', '0x9C63'), ('hotspot', '0x1111'),
        ('hotspot', '0x9C63'), ('chipperm', '0x1111'), ('chipperm', '0x9C63')]
PRIMARY = [('CI_heur', 'DeFT_tm'), ('CI_heurLA', 'DeFT_tm'), ('FULL_heurLA', 'DeFT_tm'),
           ('CI_ql', 'CI_heur'), ('FULL_ql', 'FULL_heur'), ('CI_qlLA', 'CI_heurLA'),
           ('FULL_qlLA', 'FULL_heurLA'), ('DeFT_tm', 'DeFT')]
SEEDS = range(1, 11)


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)


def ttest(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    if sd == 0:
        return 0.0 if m != 0 else 1.0
    return 2 * st.t.sf(abs(m / (sd / math.sqrt(n))), n - 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def main():
    runs = {}
    rates = collections.defaultdict(set)
    for r in csv.DictReader(open(SRC)):
        k = (r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))
        runs[k] = (float(r['accepted']), float(r['latency']))
        rates[(r['pattern'], r['mask'])].add(float(r['rate']))
    ladder = {sc: sorted(v) for sc, v in rates.items()}
    assert all(len(v) == 7 for v in ladder.values()), 'expected 7 rates per scenario'

    def thr(v, p, m, s):
        acc = [(runs[(v, p, m, r, s)][0], r) for r in ladder[(p, m)]]
        best, at = max(acc)
        return best, at == ladder[(p, m)][-1] and best >= 0.95 * 8 * ladder[(p, m)][-1]

    def metric(v, p, m, s, name):
        if name == 'THR':
            return thr(v, p, m, s)[0]
        return runs[(v, p, m, ladder[(p, m)][1], s)][1]

    prim = []
    for a, b in PRIMARY:
        for name in ('THR', 'LAT'):
            per_seed = [sum(math.log(metric(a, p, m, s, name) / metric(b, p, m, s, name)) for p, m in SCEN) / len(SCEN)
                        for s in SEEDS]
            mu, h = ci(per_seed)
            nlb = sum(1 for p, m in SCEN for s in SEEDS if name == 'THR' and (thr(a, p, m, s)[1] or thr(b, p, m, s)[1]))
            prim.append(dict(variant=a, reference=b, metric=name, n_seeds=len(per_seed), dropped_seeds=0,
                             effect_pct=round(100 * (math.exp(mu) - 1), 2),
                             ci_low=round(100 * (math.exp(mu - h) - 1), 2), ci_high=round(100 * (math.exp(mu + h) - 1), 2),
                             p=ttest(per_seed), lower_bound_cells=nlb))
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        good = (x['effect_pct'] > 0) if x['metric'] == 'THR' else (x['effect_pct'] < 0)
        x['verdict'] = ('better' if good else 'worse') if q < 0.05 else 'n.s.'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(prim[0]), lineterminator='\n')
        w.writeheader()
        for x in prim:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})
    same_bytes = open(OUT, 'rb').read() == open(REF, 'rb').read()
    a, b = list(csv.DictReader(open(OUT))), list(csv.DictReader(open(REF)))
    diffs = [(i, k, x[k], y[k]) for i, (x, y) in enumerate(zip(a, b)) for k in x if x[k] != y[k]]
    print(f'rows {len(a)} vs {len(b)}; byte-identical: {same_bytes}; differing fields: {len(diffs)}')
    for d in diffs:
        print('  DIFF', d)
    return same_bytes and not diffs and len(a) == len(b)


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
