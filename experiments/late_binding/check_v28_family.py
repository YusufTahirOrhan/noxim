#!/usr/bin/env python3
"""v28: the two primary families computed a second time, without the report's code.

Family 1 (Part C): reads eval_runs.csv and computes the 12 tests as results_v28_anchor/PREREGISTRATION.md defines them (for each size and
each of EB_best and EB_down_t: the main row CI_heurLA_X_LF against that row in THR and in LAT at 1.0 x Lsat; per seed the mean over the six
scenarios of the log ratio; one-sample t over the seeds; Holm over the 12).
Family 2 (Part D): reads fault_runs.csv (the early rows) and results_v26_faults/fault_rate_runs.csv (the main row) and computes the 24 tests
(for each size, each of the rates 1/16 and 4/16 and each of EB_best and EB_down_t: the main row against that row in THR and in LAT at 1.0 x
Lsat of DeFT-P on the mask; per mask the mean over the two traffic patterns and the two seeds of the log ratio, paired by seed; one-sample t
over the 16 masks; Holm over the 24). The rate of a mask is read from results_v26_faults/masks_v26.json.
Both are compared with report/primary_C.csv and report/primary_D.csv (written by report_v28.py): effect, interval, p, Holm-adjusted p and
verdict. Nothing of report_v28.py is imported: THR is the largest accepted throughput over the loads of a cell, and the load at 1.0 x Lsat
is the fourth of the nine loads of a cell (Part C) or the second of the four (Part D), in increasing order of the rate.

usage: python3 check_v28_family.py      (V28_RES overrides the results directory)
Writes report/families_check.md; exit status 1 if a test differs or is missing.
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V28_RES', os.path.join(HERE, 'results_v28_anchor'))
R26 = os.path.join(HERE, 'results_v26_faults')
TOL = 0.006       # percentage points (the report rounds to 0.01)
RTOL = 2e-3       # relative, p values (the report writes four significant digits)
MAIN = 'CI_heurLA_X_LF'
EARLY = ['EB_best', 'EB_down_t']
NL = chr(10)


def tstat(per):
    n = len(per)
    m = sum(per) / n
    se = math.sqrt(sum((x - m) ** 2 for x in per) / (n - 1)) / math.sqrt(n)
    h = stats.t.ppf(0.975, n - 1) * se
    p = 2 * stats.t.sf(abs(m / se), n - 1)
    return [100 * (math.exp(m) - 1), 100 * (math.exp(m - h) - 1), 100 * (math.exp(m + h) - 1), p, n]


def holm(mine):
    keys = sorted(mine)
    order = sorted(range(len(keys)), key=lambda i: mine[keys[i]][3])
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(keys) - rank) * mine[keys[i]][3]))
        k = keys[i]
        mine[k] += [run, 'n.s.' if run >= 0.05 else ('supported' if (mine[k][0] > 0) == (k[-1] == 'THR') else 'against')]
    return keys


def family_c():
    cell = defaultdict(dict)       # (size, scenario, row, seed) -> {rate: run}
    rows = list(csv.DictReader(open(os.path.join(RES, 'eval_runs.csv'))))
    for r in rows:
        size, scen = r['pattern'].split('-', 1)
        cell[(size, scen, r['variant'].rsplit('-p', 1)[0], int(r['seed']))][float(r['rate'])] = r
    assert {len(v) for v in cell.values()} == {9}, 'a cell does not have nine loads'
    sizes = sorted({k[0] for k in cell})
    scens = sorted({k[1] for k in cell})

    def metric(size, scen, row, seed, what):
        c = cell[(size, scen, row, seed)]
        if what == 'THR':
            return max(float(x['accepted']) for x in c.values())
        return float(c[sorted(c)[3]]['latency'])

    mine = {}
    for size in sizes:
        for row in EARLY:
            seeds = sorted({k[3] for k in cell if k[0] == size and k[2] == row} & {k[3] for k in cell if k[0] == size and k[2] == MAIN})
            for what in ('THR', 'LAT'):
                per = []
                for s in seeds:
                    acc = [math.log(metric(size, sc, MAIN, s, what) / metric(size, sc, row, s, what)) for sc in scens]
                    per.append(sum(acc) / len(acc))
                mine[(size, row, what)] = tstat(per)
    holm(mine)
    return mine, len(rows), sizes, scens


def family_d():
    rate_of = {(e['size'], e['mask']): e['rate'] for e in json.load(open(os.path.join(R26, 'masks_v26.json')))['part_b']}
    cell = defaultdict(dict)       # (size, mask, pattern, row, seed) -> {rate: run}
    n = 0
    for path, keep in ((os.path.join(RES, 'fault_runs.csv'), set(EARLY)), (os.path.join(R26, 'fault_rate_runs.csv'), {MAIN})):
        for r in csv.DictReader(open(path)):
            row = r['variant'].rsplit('-p', 1)[0]
            if row not in keep:
                continue
            size, pat = r['pattern'].split('-', 1)
            cell[(size, r['mask'], pat, row, int(r['seed']))][float(r['rate'])] = r
            n += 1
    assert {len(v) for v in cell.values()} == {4}, 'a cell does not have four loads'

    def metric(size, mask, pat, row, seed, what):
        c = cell[(size, mask, pat, row, seed)]
        if what == 'THR':
            return max(float(x['accepted']) for x in c.values())
        return float(c[sorted(c)[1]]['latency'])

    mine = {}
    sizes = sorted({k[0] for k in cell})
    for size in sizes:
        for rate in ('1/16', '4/16'):
            for row in EARLY:
                masks = sorted({k[1] for k in cell if k[0] == size and k[3] == row and rate_of[(size, k[1])] == rate})
                if not masks:
                    continue
                for what in ('THR', 'LAT'):
                    per = []
                    for m in masks:
                        v = [math.log(metric(size, m, p, MAIN, s, what) / metric(size, m, p, row, s, what)) for p in ('uniform', 'hotspot') for s in (151, 152)]
                        per.append(sum(v) / len(v))
                    mine[(size, rate, row, what)] = tstat(per)
    holm(mine)
    return mine, n, sizes


def compare(mine, path, keyf, nkey, L, title):
    if not os.path.exists(path):
        L.append('* %s: `%s` not found.' % (title, os.path.basename(path)))
        return 1, 0
    rep = {keyf(r): r for r in csv.DictReader(open(path))}
    bad, worst = 0, 0.0
    for k in sorted(mine):
        e, lo, hi, p, n, ph, v = mine[k]
        b = rep.get(k)
        if b is None:
            bad += 1
            L.append('* MISSING in the report: %s' % ' '.join(k))
            continue
        d = max(abs(e - float(b['effect_pct'])), abs(lo - float(b['ci_low'])), abs(hi - float(b['ci_high'])))
        worst = max(worst, d)
        same = (d < TOL and abs(p - float(b['p'])) <= RTOL * max(float(b['p']), 1e-300) and abs(ph - float(b['p_holm'])) <= RTOL * max(float(b['p_holm']), 1e-300)
                and v == b['verdict'] and n == int(b[nkey]))
        bad += not same
        if not same:
            L.append('* DIFFERENT %s: second computation %.2f [%.2f, %.2f] p %.4g Holm %.4g %s (n %d); report %s [%s, %s] p %s Holm %s %s (n %s)' % (
                ' '.join(k), e, lo, hi, p, ph, v, n, b['effect_pct'], b['ci_low'], b['ci_high'], b['p'], b['p_holm'], b['verdict'], b[nkey]))
    if len(rep) != len(mine):
        bad += 1
        L.append('* the report has %d tests, the second computation %d' % (len(rep), len(mine)))
    L.append('* **%s: %d tests, %d different.** Largest difference of an effect or of an interval end: %.4f percentage points (the report rounds to 0.01); verdicts: %s.' % (
        title, len(mine), bad, worst, ', '.join('%d %s' % (sum(1 for x in mine.values() if x[6] == v), v) for v in ('supported', 'against', 'n.s.'))))
    return bad, len(mine)


def main():
    L = ['# v28: the two primary families computed a second time (generated by check_v28_family.py)', '',
         'The tests of `PREREGISTRATION.md` computed from the per-run CSVs by a script that shares no code with `report_v28.py`, and compared with',
         '`report/primary_C.csv` and `report/primary_D.csv` (effect of the main row against the early row, 95 % interval, p, Holm-adjusted p, verdict).', '']
    bad = 0
    if os.path.exists(os.path.join(RES, 'eval_runs.csv')):
        m1, n1, sizes, scens = family_c()
        L.append('* Part C: %d runs; sizes %s; scenarios %s.' % (n1, ', '.join(sizes), ', '.join(scens)))
        b, _ = compare(m1, os.path.join(RES, 'report', 'primary_C.csv'), lambda r: (r['size'], r['early_row'], r['metric']), 'n_seeds', L, 'Family 1 (Part C)')
        bad += b
    else:
        L.append('* Part C: no eval_runs.csv yet.')
    if os.path.exists(os.path.join(RES, 'fault_runs.csv')):
        m2, n2, sizes = family_d()
        L.append('* Part D: %d runs of the early rows and of the main row; sizes %s.' % (n2, ', '.join(sizes)))
        b, _ = compare(m2, os.path.join(RES, 'report', 'primary_D.csv'), lambda r: (r['size'], r['rate'], r['early_row'], r['metric']), 'n_masks', L, 'Family 2 (Part D)')
        bad += b
    else:
        L.append('* Part D: no fault_runs.csv yet.')
    L += ['', '**All compared tests agree: %s.**' % ('yes' if bad == 0 else 'NO'), '']
    os.makedirs(os.path.join(RES, 'report'), exist_ok=True)
    with open(os.path.join(RES, 'report', 'families_check.md'), 'w', newline=NL) as fh:
        fh.write(NL.join(L))
    print(NL.join(L))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
