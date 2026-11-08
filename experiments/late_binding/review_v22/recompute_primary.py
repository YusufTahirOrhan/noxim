"""Independent recomputation of headline numbers from the per-run CSVs (review v22).

Written from the pre-registrations alone (results_v19_vnrr/PREREGISTRATION.md, results_v21_fastsel/PREREGISTRATION.md),
without importing report_v19.py / report_v21.py / report_v4.py / primary_from_csv.py. Pure Python 3 (no scipy).

  python3 recompute_primary.py [SIZE]   -> v19 K5 primary table (60 tests, Holm) next to results_v19_vnrr/report/primary.csv,
                                           the v19 secondary DeFT-vs-MTR/RC rows with a THR-cap check,
                                           and the v21 primary rows of SIZE (default 3x3) next to results_v21_fastsel/report/primary.csv
Metric definitions (pre-registration):
  LAT  = mean packet latency at the 4th load of the scenario's ladder (1.0 x Lsat)
  P99  = p99 latency at the same load
  THR  = max accepted throughput over the 7 loads
  effect = 100 (exp(mean_s R_s) - 1), R_s = mean over scenarios of ln(metric_variant / metric_reference) for seed s;
  two-sided one-sample t test over seeds; Holm step-down over the family.
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LB = os.path.dirname(HERE)
V19 = os.path.join(LB, 'results_v19_vnrr')
V21 = os.path.join(LB, 'results_v21_fastsel')

SCEN_2X2 = [('uniform', '0x0000'), ('localized', '0x0000'), ('hotspot', '0x0000'), ('chipperm', '0x0000'),
            ('movinghot', '0x0000'), ('uniform', '0x1111'), ('uniform', '0x9C63'), ('hotspot', '0x1111'),
            ('hotspot', '0x9C63'), ('chipperm', '0x1111'), ('chipperm', '0x9C63')]
NORTH = {'3x3': '0x111111111', '4x4': '0x1111111111111111'}


def scen(size):
    if size == '2x2':
        return [('2x2-' + p, m) for p, m in SCEN_2X2]
    return [(size + '-' + p, '0x0') for p in ('uniform', 'localized', 'hotspot', 'chipperm', 'movinghot')] + \
           [(size + '-' + p, NORTH[size]) for p in ('uniform', 'hotspot')]


def ff(size):
    return [(p, m) for p, m in scen(size) if int(m, 16) == 0]


def load(path):
    R = {}
    for r in csv.DictReader(open(path)):
        R[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = \
            dict(lat=float(r['latency']), p99=float(r['p99']), acc=float(r['accepted']))
    return R


# --- Student t without scipy: regularized incomplete beta by continued fraction (Numerical Recipes) ---
def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 1e-15, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """two-sided p = P(|T_df| >= t)"""
    return betai(df / 2.0, 0.5, df / (df + t * t))


def t_ppf975(df):
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_sf2(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def stats(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = t_ppf975(n - 1) * sd / math.sqrt(n)
    if sd == 0:
        p = 1.0 if m == 0 else 0.0
    else:
        p = t_sf2(abs(m / (sd / math.sqrt(n))), n - 1)
    return m, h, p


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


class Eval:
    def __init__(self, R, ladder, seeds):
        self.R, self.ladder, self.seeds = R, ladder, list(seeds)

    def metric(self, v, p, m, s, name, idx=3):
        lad = self.ladder(p, m)
        if name == 'THR':
            return max(self.R[(v, p, m, r, s)]['acc'] for r in lad)
        x = self.R[(v, p, m, lad[idx], s)]
        return x['p99'] if name == 'P99' else x['lat']

    def thr_at_top(self, v, p, m, s):
        lad = self.ladder(p, m)
        accs = [self.R[(v, p, m, r, s)]['acc'] for r in lad]
        return accs.index(max(accs)) == len(lad) - 1

    def effect(self, a, b, name, scenarios, idx=3):
        per_seed = []
        for s in self.seeds:
            try:
                rs = [math.log(self.metric(a, p, m, s, name, idx) / self.metric(b, p, m, s, name, idx)) for p, m in scenarios]
            except KeyError:
                continue
            per_seed.append(sum(rs) / len(rs))
        mu, h, p = stats(per_seed)
        return dict(effect=100 * (math.exp(mu) - 1), lo=100 * (math.exp(mu - h) - 1), hi=100 * (math.exp(mu + h) - 1), p=p, n=len(per_seed))


def compare(mine, ref_rows, keys, label):
    print('\n## ' + label + ': mine vs repository report (' + str(len(mine)) + ' tests)')
    print('| size | variant | reference | metric | effect mine / repo | CI mine / repo | p_holm mine / repo | verdict mine / repo |')
    print('|---|---|---|---|---|---|---|---|')
    worst = 0.0
    for x in mine:
        r = next(rr for rr in ref_rows if all(rr[k] == str(x[k]) for k in keys))
        d = max(abs(x['effect'] - float(r['effect_pct'])), abs(x['lo'] - float(r['ci_low'])), abs(x['hi'] - float(r['ci_high'])))
        worst = max(worst, d)
        print('| %s | %s | %s | %s | %+.2f / %+.2f | [%+.1f, %+.1f] / [%+.1f, %+.1f] | %.3g / %.3g | %s / %s |' % (
            x['size'], x['variant'], x['reference'], x['metric'], x['effect'], float(r['effect_pct']), x['lo'], x['hi'],
            float(r['ci_low']), float(r['ci_high']), x['p_holm'], float(r['p_holm']), x['verdict'], r['verdict']))
    print('\nLargest absolute difference in effect or CI bound: %.3f percentage points' % worst)
    return worst


def ladder_fn(P):
    def ladder(p, m):
        size, pat = p.split('-')
        return P[size + '__' + pat + '__' + m]['eval']
    return ladder


def v19():
    P = json.load(open(os.path.join(V19, 'load_points_rr.json')))
    R = load(os.path.join(V19, 'eval_runs.csv'))
    seeds = range(61, 71)
    E = Eval(R, ladder_fn(P), seeds)
    tests = []
    for z in ('2x2', '3x3', '4x4'):
        for a in ('CI_qlLA_G', 'FULL_qlLA_G'):
            for n in ('LAT', 'P99'):
                tests.append(dict(size=z, variant=a, reference='DeFT', metric=n, scen=scen(z)))
    for z in ('2x2', '3x3', '4x4'):
        for a in ('CI_qlLA_G', 'FULL_qlLA_G'):
            for b in ('MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran'):
                for n in ('LAT', 'P99'):
                    tests.append(dict(size=z, variant=a, reference=b, metric=n, scen=ff(z) if b in ('MTR', 'RC') else scen(z)))
    for t in tests:
        t.update(E.effect(t['variant'], t['reference'], t['metric'], t['scen']))
    for t, q in zip(tests, holm([t['p'] for t in tests])):
        t['p_holm'] = q
        t['verdict'] = ('ours better' if t['effect'] < 0 else 'ours worse') if q < 0.05 else 'n.s.'
    ref = list(csv.DictReader(open(os.path.join(V19, 'report', 'primary.csv'))))
    w1 = compare(tests, ref, ('size', 'variant', 'reference', 'metric'), 'v19 K5 primary (Holm over 60)')
    print('\n## v19 secondary: DeFT(rho*) with round-robin vs MTR and RC, fault-free (unadjusted), mine')
    print('| size | ref | LAT | P99 | THR | cells whose max accepted sits at the top load, variant / reference |')
    print('|---|---|---|---|---|---|')
    for z in ('2x2', '3x3', '4x4'):
        for b in ('MTR', 'RC'):
            cells = []
            for n in ('LAT', 'P99', 'THR'):
                e = E.effect('DeFT', b, n, ff(z))
                cells.append('%+.1f [%+.1f, %+.1f] (p %.2g)' % (e['effect'], e['lo'], e['hi'], e['p']))
            capv = sum(E.thr_at_top('DeFT', p, m, s) for p, m in ff(z) for s in seeds)
            capr = sum(E.thr_at_top(b, p, m, s) for p, m in ff(z) for s in seeds)
            tot = len(ff(z)) * len(seeds)
            print('| %s | %s | %s | %d/%d / %d/%d |' % (z, b, ' | '.join(cells), capv, tot, capr, tot))
    return w1


def v21(size='3x3'):
    P = json.load(open(os.path.join(V19, 'load_points_rr.json')))
    R = load(os.path.join(V21, 'eval_runs.csv'))
    ch = json.load(open(os.path.join(V21, 'tuning_choice.json')))
    seeds = range(81, 91)
    E = Eval(R, ladder_fn(P), seeds)
    tests = []
    for z in ('2x2', '3x3', '4x4'):
        for sc in ('CI', 'FULL'):
            a = ch[z][sc]['best']
            for n in ('LAT', 'P99'):
                tests.append(dict(size=z, variant=a, reference='DeFT', metric=n, scen=scen(z)))
            for b in ('MTR', 'RC'):
                for n in ('LAT', 'P99'):
                    tests.append(dict(size=z, variant=a, reference=b, metric=n, scen=ff(z)))
    for t in tests:
        t.update(E.effect(t['variant'], t['reference'], t['metric'], t['scen']))
    for t, q in zip(tests, holm([t['p'] for t in tests])):
        t['p_holm'] = q
        t['verdict'] = ('ours better' if t['effect'] < 0 else 'ours worse') if q < 0.05 else 'n.s.'
    ref = list(csv.DictReader(open(os.path.join(V21, 'report', 'primary.csv'))))
    rows = [t for t in tests if t['size'] == size]
    w = compare(rows, ref, ('size', 'variant', 'reference', 'metric'), 'v21 primary rows of ' + size + ' (Holm over all 36)')
    print('\n## v21 secondary on ' + size + ': LAT at 0.2 x Lsat vs DeFT, all four variants, mine vs report/secondary.csv')
    sec = list(csv.DictReader(open(os.path.join(V21, 'report', 'secondary.csv'))))
    for v in ('CI_fast', 'CI_fastQL', 'FULL_fast', 'FULL_fastQL'):
        e = E.effect(v, 'DeFT', 'LAT', scen(size), idx=0)
        r = next(rr for rr in sec if (rr['size'], rr['variant'], rr['reference'], rr['metric']) == (size, v, 'DeFT', 'LAT@0.2'))
        print('- %s: mine %+.2f [%+.1f, %+.1f]  repo %+.2f [%+.1f, %+.1f]' % (
            v, e['effect'], e['lo'], e['hi'], float(r['effect_pct']), float(r['ci_low']), float(r['ci_high'])))
    return w


if __name__ == '__main__':
    w1 = v19()
    w2 = v21(sys.argv[1] if len(sys.argv) > 1 else '3x3')
    print('\nMAX_DIFF v19 %.4f v21 %.4f' % (w1, w2))
