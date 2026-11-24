#!/usr/bin/env python3
"""v29: the two primary families computed a second time, without the report's code.

Family 1 (Part B): reads heldout_runs.csv and computes the 12 tests as results_v29_review/PREREGISTRATION.md defines them: for each size,
over the three new scenarios (tornado, neighbour, randperm), the main row CI_heurLA_X_LF against (a) DeFT_P and (b) the best of DeFT_P,
DeFT_B, MTR, RC and XY_SP, in THR and in LAT at 1.0 x Lsat; per seed the mean over the scenarios of the log ratio; one-sample t over the ten
seeds; Holm over the 12.
Family 2 (Part C): reads depth_runs.csv (the references with 6-flit buffers) and results_v25_confirm/eval_runs.csv (the main row with 4-flit
buffers, the six fault-free scenarios, seeds 121-130) and computes the 12 tests: for each size the main row against (a) the best of
DeFT_P_d6 and DeFT_B_d6 and (b) the best of DeFT_P_d6, DeFT_B_d6, MTR_d6 and RC_d6; Holm over the 12.
The best row of a set is taken per size, scenario and metric: the largest mean THR over the seeds, the smallest mean LAT.
Both are compared with report/primary_B.csv and report/primary_C.csv (written by report_v29.py): effect, interval, p, Holm-adjusted p and
verdict. Nothing of report_v29.py or report_v25.py is imported: THR is the largest accepted throughput over the nine loads of a cell, and the
load at 1.0 x Lsat is the fourth of the nine loads of a cell, in increasing order of the rate.

usage: python3 check_v29_family.py      (V29_RES overrides the results directory)
Writes report/families_check.md; exit status 1 if a test differs or is missing.
"""
import csv
import math
import os
import sys
from collections import defaultdict

from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V29_RES', os.path.join(HERE, 'results_v29_review'))
R25 = os.path.join(HERE, 'results_v25_confirm')
TOL = 0.006       # percentage points (the report rounds to 0.01)
RTOL = 2e-3       # relative, p values (the report writes four significant digits)
MAIN = 'CI_heurLA_X_LF'
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


def cells_of(paths_rows):
    """{(size, scenario, row, seed): {rate: run}} of the named rows of the named files (fault-free masks only)."""
    cell = defaultdict(dict)
    n = 0
    for path, keep in paths_rows:
        for r in csv.DictReader(open(path)):
            row = r['variant'].rsplit('-p', 1)[0]
            if row not in keep or int(r['mask'], 16) != 0:
                continue
            size, scen = r['pattern'].split('-', 1)
            cell[(size, scen, row, int(r['seed']))][float(r['rate'])] = r
            n += 1
    return cell, n


def family(cell, scens, seeds, groups):
    """groups: {name: [reference rows]}. For each size, group and metric: the main row against the best row of the group."""
    def metric(size, scen, row, seed, what):
        c = cell[(size, scen, row, seed)]
        assert len(c) == 9, 'a cell does not have nine loads: %s %s %s %d' % (size, scen, row, seed)
        if what == 'THR':
            return max(float(x['accepted']) for x in c.values())
        return float(c[sorted(c)[3]]['latency'])

    mine, best = {}, {}
    for size in sorted({k[0] for k in cell}):
        for g, refs in groups.items():
            for what in ('THR', 'LAT'):
                ref_of = {}
                for sc in scens:
                    mean = {b: sum(metric(size, sc, b, s, what) for s in seeds) / len(seeds) for b in refs}
                    ref_of[sc] = max(mean, key=mean.get) if what == 'THR' else min(mean, key=mean.get)
                per = []
                for s in seeds:
                    v = [math.log(metric(size, sc, MAIN, s, what) / metric(size, sc, ref_of[sc], s, what)) for sc in scens]
                    per.append(sum(v) / len(v))
                mine[(size, g, what)] = tstat(per)
                best[(size, g, what)] = ref_of
    holm(mine)
    return mine, best


def compare(mine, path, L, title):
    if not os.path.exists(path):
        L.append('* %s: `%s` not found.' % (title, os.path.basename(path)))
        return 1
    rep = {(r['size'], r['group'], r['metric']): r for r in csv.DictReader(open(path))}
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
                and v == b['verdict'] and n == int(b['n_seeds']))
        bad += not same
        if not same:
            L.append('* DIFFERENT %s: second computation %.2f [%.2f, %.2f] p %.4g Holm %.4g %s (n %d); report %s [%s, %s] p %s Holm %s %s (n %s)' % (
                ' '.join(k), e, lo, hi, p, ph, v, n, b['effect_pct'], b['ci_low'], b['ci_high'], b['p'], b['p_holm'], b['verdict'], b['n_seeds']))
    if len(rep) != len(mine):
        bad += 1
        L.append('* the report has %d tests, the second computation %d' % (len(rep), len(mine)))
    L.append('* **%s: %d tests, %d different.** Largest difference of an effect or of an interval end: %.4f percentage points (the report rounds to 0.01); verdicts: %s.' % (
        title, len(mine), bad, worst, ', '.join('%d %s' % (sum(1 for x in mine.values() if x[6] == v), v) for v in ('supported', 'against', 'n.s.'))))
    return bad


def main():
    L = ['# v29: the two primary families computed a second time (generated by check_v29_family.py)', '',
         'The tests of `PREREGISTRATION.md` computed from the per-run CSVs by a script that shares no code with `report_v29.py`, and compared with',
         '`report/primary_B.csv` and `report/primary_C.csv` (effect of the main row against the reference, 95 % interval, p, Holm-adjusted p, verdict).', '']
    bad = 0
    f = os.path.join(RES, 'heldout_runs.csv')
    if os.path.exists(f):
        refs = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP']
        cell, n = cells_of([(f, set(refs) | {MAIN})])
        scens = sorted({k[1] for k in cell})
        seeds = sorted({k[3] for k in cell})
        mine, best = family(cell, scens, seeds, {'a': ['DeFT_P'], 'b': refs})
        L.append('* Part B: %d runs; scenarios %s; seeds %d-%d. The best reference of (b) per scenario, THR: %s.' % (n, ', '.join(scens), seeds[0], seeds[-1], '; '.join(
            '%s: %s' % (z, ', '.join(best[(z, 'b', 'THR')][sc] for sc in scens)) for z in sorted({k[0] for k in cell}))))
        bad += compare(mine, os.path.join(RES, 'report', 'primary_B.csv'), L, 'Family 1 (Part B)')
    else:
        L.append('* Part B: no heldout_runs.csv yet.')
    f = os.path.join(RES, 'depth_runs.csv')
    if os.path.exists(f):
        d6 = ['DeFT_P_d6', 'DeFT_B_d6', 'MTR_d6', 'RC_d6']
        cell, n = cells_of([(f, set(d6)), (os.path.join(R25, 'eval_runs.csv'), {MAIN})])
        scens = sorted({k[1] for k in cell if k[2] == 'DeFT_P_d6'})
        seeds = sorted({k[3] for k in cell if k[2] == 'DeFT_P_d6'})
        cell = {k: v for k, v in cell.items() if k[1] in scens and k[3] in seeds}
        mine, best = family(cell, scens, seeds, {'a': d6[:2], 'b': d6})
        L.append('* Part C: %d runs read (the four references at depth 6 and the main row of round 25); scenarios %s; seeds %d-%d.' % (n, ', '.join(scens), seeds[0], seeds[-1]))
        bad += compare(mine, os.path.join(RES, 'report', 'primary_C.csv'), L, 'Family 2 (Part C)')
    else:
        L.append('* Part C: no depth_runs.csv yet.')
    L += ['', '**All compared tests agree: %s.**' % ('yes' if bad == 0 else 'NO'), '']
    os.makedirs(os.path.join(RES, 'report'), exist_ok=True)
    with open(os.path.join(RES, 'report', 'families_check.md'), 'w', newline=NL) as fh:
        fh.write(NL.join(L))
    print(NL.join(L))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
