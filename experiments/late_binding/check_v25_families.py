#!/usr/bin/env python3
"""v25: the two pre-registered families computed a second time, without the report's code.

Reads the per-run CSVs (eval_runs.csv, fault_runs.csv), computes the 18 tests of the primary family of Part B and the 12 tests
of the family of Part C as PREREGISTRATION.md defines them, and compares effect, interval, p and Holm-adjusted p with
report/primary.csv and report/fault_family.csv (written by report_v25.py). Nothing of report_v25.py is imported: the load at
1.0 x Lsat is taken as the fourth of the nine loads of a cell (Part B) and the second of the four (Part C), the number of faulty
VLs per chiplet is read from the mask.

usage: python3 check_v25_families.py      (V25_RES overrides the results directory)
Writes report/families_check.md; exit status 1 if a test differs.
"""
import csv
import math
import os
import sys
from collections import defaultdict

from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V25_RES', os.path.join(HERE, 'results_v25_confirm'))
TOL = 0.006       # percentage points (the report rounds to 0.01)
RTOL = 2e-3       # relative, p values (the report writes four significant digits)


def rd(fn):
    with open(os.path.join(RES, fn)) as fh:
        return list(csv.DictReader(fh))


def tci(xs):
    n = len(xs)
    m = sum(xs) / n
    se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) / math.sqrt(n)
    if se == 0:
        return m, m, m, (1.0 if m == 0 else 0.0)
    h = stats.t.ppf(0.975, n - 1) * se
    return m, m - h, m + h, 2 * stats.t.sf(abs(m / se), n - 1)


def pct(x):
    return 100 * (math.exp(x) - 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = run
    return out


def verdict(effect, p_holm, higher_is_better):
    if p_holm >= 0.05:
        return 'n.s.'
    return 'supported' if (effect > 0) == higher_is_better else 'against'


def best_ref(refs, value, seeds, higher_is_better):
    """the reference row with the best mean over the seeds; rows that did not run are skipped"""
    best = None
    for ref in refs:
        vals = [value(ref, s) for s in seeds]
        if any(v is None for v in vals):
            continue
        mean = sum(vals) / len(vals)
        if best is None or (mean > best[0] if higher_is_better else mean < best[0]):
            best = (mean, ref)
    return best[1]


def compare(tag, mine, rep, L):
    bad = 0
    worst = 0.0
    for k in sorted(mine):
        eff, lo, hi, p, ph, v = mine[k]
        b = rep[k]
        d = max(abs(eff - float(b['effect_pct'])), abs(lo - float(b['ci_low'])), abs(hi - float(b['ci_high'])))
        worst = max(worst, d)
        same = (d < TOL and abs(p - float(b['p'])) <= RTOL * float(b['p']) and abs(ph - float(b['p_holm'])) <= RTOL * float(b['p_holm'])
                and v == b['verdict'])
        bad += not same
        if not same:
            L.append('* DIFFERENT %s %s: second computation %.2f [%.2f, %.2f] p %.4g Holm %.4g %s; report %s [%s, %s] p %s Holm %s %s' % (
                tag, ' '.join(k), eff, lo, hi, p, ph, v, b['effect_pct'], b['ci_low'], b['ci_high'], b['p'], b['p_holm'], b['verdict']))
    L.append('* **%s: %d tests, %d different.** Largest difference of an effect or of an interval end: %.4f percentage points '
             '(the report rounds to 0.01); verdicts: %s.' % (tag, len(mine), bad, worst, ', '.join(
                 '%d %s' % (sum(1 for x in mine.values() if x[5] == v), v) for v in ('supported', 'against', 'n.s.'))))
    return bad


def part_b(L):
    rows = rd('eval_runs.csv')
    refs = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP', 'DeFT_Dis', 'DeFT_Ran']
    cell = defaultdict(dict)   # (size, scenario, row, seed) -> {rate: run}
    for r in rows:
        size, pat = r['pattern'].split('-', 1)
        sc = pat + ('' if int(r['mask'], 16) == 0 else '+f')
        cell[(size, sc, r['variant'].rsplit('-p', 1)[0], int(r['seed']))][float(r['rate'])] = r
    sizes = sorted({k[0] for k in cell})
    scen = sorted({k[1] for k in cell})
    seeds = sorted({k[3] for k in cell})
    assert {len(v) for v in cell.values()} == {9}, 'a cell of Part B does not have nine loads'

    def metric(size, sc, m, seed, what):
        c = cell.get((size, sc, m, seed))
        if not c:
            return None
        if what == 'THR':
            return max(float(x['accepted']) for x in c.values())
        return float(c[sorted(c)[3]][{'LAT': 'latency', 'P99': 'p99'}[what]])

    mine = {}
    for size in sizes:
        for row in ('CI_heurLA_X_LF', 'CI_heurLA_O_LF'):
            for what in ('THR', 'LAT', 'P99'):
                per_seed = []
                for seed in seeds:
                    acc = []
                    for sc in scen:
                        ref = best_ref(refs, lambda m, s: metric(size, sc, m, s, what), seeds, what == 'THR')
                        acc.append(math.log(metric(size, sc, row, seed, what) / metric(size, sc, ref, seed, what)))
                    per_seed.append(sum(acc) / len(acc))
                m, lo, hi, p = tci(per_seed)
                mine[(size, row, what)] = [pct(m), pct(lo), pct(hi), p]
    keys = sorted(mine)
    for k, h in zip(keys, holm([mine[k][3] for k in keys])):
        mine[k] += [h, verdict(mine[k][0], h, k[2] == 'THR')]
    L.append('* Part B: %d runs, %d sizes, %d scenarios, seeds %d-%d.' % (len(rows), len(sizes), len(scen), seeds[0], seeds[-1]))
    return compare('Primary family of Part B', mine, {(r['size'], r['row'], r['metric']): r for r in rd('report/primary.csv')}, L)


def part_c(L):
    rows = rd('fault_runs.csv')
    refs = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran']
    chiplets = {'2x2': 4, '3x3': 9, '4x4': 16}
    cell = defaultdict(dict)   # (size, mask, row, seed) -> {rate: run}
    for r in rows:
        cell[(r['pattern'].split('-', 1)[0], r['mask'], r['variant'].rsplit('-p', 1)[0], int(r['seed']))][float(r['rate'])] = r
    sizes = sorted({k[0] for k in cell})
    seeds = sorted({k[3] for k in cell})
    assert {len(v) for v in cell.values()} == {4}, 'a cell of Part C does not have four loads'

    def kof(size, mask):
        per = {bin((int(mask, 16) >> (4 * c)) & 15).count('1') for c in range(chiplets[size])}
        assert len(per) == 1, (size, mask, per)
        return per.pop()

    masks = defaultdict(list)
    for (size, mask, _, _) in cell:
        if mask not in masks[(size, kof(size, mask))]:
            masks[(size, kof(size, mask))].append(mask)

    def metric(size, mask, m, seed, what):
        c = cell.get((size, mask, m, seed))
        if not c:
            return None
        if what == 'THR':
            return max(float(x['accepted']) for x in c.values())
        return float(c[sorted(c)[1]]['latency'])

    mine = {}
    for size in sizes:
        for k in (1, 2):
            for what in ('THR', 'LAT'):
                per_seed = []
                for seed in seeds:
                    acc = []
                    for mask in masks[(size, k)]:
                        ref = best_ref(refs, lambda m, s: metric(size, mask, m, s, what), seeds, what == 'THR')
                        acc.append(math.log(metric(size, mask, 'CI_heurLA_X_LF', seed, what) / metric(size, mask, ref, seed, what)))
                    per_seed.append(sum(acc) / len(acc))
                m, lo, hi, p = tci(per_seed)
                mine[(size, str(k), what)] = [pct(m), pct(lo), pct(hi), p]
    keys = sorted(mine)
    for key, h in zip(keys, holm([mine[key][3] for key in keys])):
        mine[key] += [h, verdict(mine[key][0], h, key[2] == 'THR')]
    L.append('* Part C: %d runs, masks per (size, k): %s, seeds %d-%d.' % (
        len(rows), ', '.join('%s k=%d: %d' % (s, k, len(v)) for (s, k), v in sorted(masks.items())), seeds[0], seeds[-1]))
    return compare('Family of Part C', mine, {(r['size'], r['k'], r['metric']): r for r in rd('report/fault_family.csv')}, L)


def main():
    L = ['# v25: the two families computed a second time (generated by check_v25_families.py)', '',
         'The tests of `PREREGISTRATION.md` computed from the per-run CSVs by a script that shares no code with `report_v25.py`, '
         'and compared with `report/primary.csv` and `report/fault_family.csv` (effect, 95 % interval, p, Holm-adjusted p, verdict).', '']
    bad = 0
    done = 0
    for fn, rep, part in (('eval_runs.csv', 'report/primary.csv', part_b), ('fault_runs.csv', 'report/fault_family.csv', part_c)):
        if os.path.exists(os.path.join(RES, fn)) and os.path.exists(os.path.join(RES, rep)):
            bad += part(L)
            done += 1
        else:
            L.append('* %s or %s not there yet: not checked.' % (fn, rep))
    L += ['', '**All compared tests agree: %s.**' % ('yes' if bad == 0 and done else 'NO' if bad else 'nothing compared'), '']
    os.makedirs(os.path.join(RES, 'report'), exist_ok=True)
    with open(os.path.join(RES, 'report', 'families_check.md'), 'w', newline='\n') as fh:
        fh.write('\n'.join(L))
    print('\n'.join(L))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
