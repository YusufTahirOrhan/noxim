"""v26 report, following results_v26_faults/PREREGISTRATION.md.

Usage: python3 report_v26.py      (V26_RES overrides the results directory)
  fault_rate_runs.csv, load_points_v26.json, masks_v26.json -> report/primary.csv, secondary.csv, per_mask.csv, summary_B.md,
      paper_data/fault_rate_effects.csv, fault_rate_per_mask.csv
  formal_all_2x2.csv, formal_a2.csv, formal_subset_2x2.csv, conformance.csv -> report/summary_A.md, paper_data/formal_summary.csv
  reachability_v26.csv -> paper_data/reachability_v26.csv
report/summary.md is the concatenation of what exists.

Part B. Unit = mask. THR = the largest accepted throughput over the four loads; LAT and P99 at 1.0 x Lsat of DeFT_P (the 2nd load); LAT05 at
0.5 x Lsat (the 1st load). Best reference per (mask, traffic, metric): the reference row with the best mean over the two seeds. Value of a mask
V_m = mean over the traffic patterns and seeds of ln(metric_row / metric_reference), paired by seed. Effect of a group of masks =
100 x (exp(mean of V_m) - 1) %; 95 % t interval and two-sided one-sample t test over the masks.
"""
import csv
import json
import math
import os
import shutil
import sys

import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V26_RES', os.path.join(HERE, 'results_v26_faults'))
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
R25 = os.path.join(HERE, 'results_v25_confirm')
SIZES = ['2x2', '3x3', '4x4']
RATES = ['1/16', '2/16', '4/16', '8/16']
PATTERNS = ['uniform', 'hotspot']
SEEDS = [151, 152]
MAIN, SECOND = 'CI_heurLA_X_LF', 'CI_heurLA_O_LF'
REFS = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran']
ROWS = REFS + [MAIN, SECOND]
METRICS = ['THR', 'LAT', 'P99']
HIGHER = {'THR': True, 'LAT': False, 'P99': False, 'LAT05': False}
NL = chr(10)
NAN = float('nan')


def isnan(x):
    return x != x


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else NAN


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def tci(xs):
    """(mean, low, high, p, n) of a sample of log ratios; the interval and the test are those of a one-sample t."""
    xs = [x for x in xs if x is not None and not isnan(x)]
    n = len(xs)
    if n == 0:
        return NAN, NAN, NAN, NAN, 0
    m = sum(xs) / n
    if n == 1:
        return m, NAN, NAN, NAN, 1
    se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) / math.sqrt(n)
    if se == 0:
        return m, m, m, (1.0 if m == 0 else 0.0), n
    h = st.t.ppf(0.975, n - 1) * se
    return m, m - h, m + h, 2 * st.t.sf(abs(m / se), n - 1), n


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = run
    return out


def quart(xs):
    """(min, q1, median, q3, max) with linear interpolation."""
    xs = sorted(xs)
    if not xs:
        return [NAN] * 5

    def q(f):
        k = f * (len(xs) - 1)
        lo, hi = int(math.floor(k)), int(math.ceil(k))
        return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)
    return [xs[0], q(0.25), q(0.5), q(0.75), xs[-1]]


def eff(t, sign=True):
    """'+1.2 [+0.3, +2.1]' of a tci() tuple, in per cent."""
    m, lo, hi, p, n = t
    if n == 0:
        return 'n/a'
    if isnan(lo):
        return '%+.1f (one mask)' % pct(m)
    return '%+.1f [%+.1f, %+.1f]' % (pct(m), pct(lo), pct(hi))


def pv(p):
    return 'n/a' if isnan(p) else ('%.2g' % p if p < 0.001 else '%.3f' % p)


def write(path, rows, cols=None):
    cols = cols or (list(rows[0]) if rows else [])
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator=NL, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def wmd(name, L):
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


class Data:
    """The runs of one fault design: masks (entries with size, rate, index, mask), ladders, per-run values."""

    def __init__(self, runs, ladder, entries, patterns, seeds, refs):
        self.R, self.lad, self.E, self.patterns, self.seeds, self.refs = runs, ladder, entries, patterns, seeds, refs
        self._best = {}

    def val(self, row, e, p, s, name):
        lad = self.lad(e, p)
        if name == 'THR':
            v = [self.R.get((row, e['size'], p, e['mask'], r, s)) for r in lad]
            if any(x is None for x in v):
                return None
            return max(x['accepted'] for x in v)
        r = self.R.get((row, e['size'], p, e['mask'], lad[0 if name == 'LAT05' else 1], s))
        if r is None:
            return None
        x = r['p99' if name == 'P99' else 'latency']
        return x if x > 0 else None

    def smean(self, row, e, p, name):
        v = [self.val(row, e, p, s, name) for s in self.seeds]
        return None if any(x is None for x in v) else sum(v) / len(v)

    def best(self, e, p, name):
        k = (e['size'], e['mask'], p, name)
        if k not in self._best:
            c = [(self.smean(r, e, p, name), r) for r in self.refs]
            c = [x for x in c if x[0] is not None]
            self._best[k] = (max(c, key=lambda x: x[0]) if HIGHER[name] else min(c, key=lambda x: x[0]))[1] if c else None
        return self._best[k]

    def lr(self, row, ref, e, p, s, name):
        b = self.best(e, p, name) if ref == 'best' else ref
        if b is None:
            return None
        x, y = self.val(row, e, p, s, name), self.val(b, e, p, s, name)
        return None if x is None or y is None else math.log(x / y)

    def cell(self, row, ref, e, p, name):
        """Mean over the seeds of the log ratio of one (mask, traffic) cell."""
        v = [self.lr(row, ref, e, p, s, name) for s in self.seeds]
        v = [x for x in v if x is not None]
        return sum(v) / len(v) if v else None

    def vm(self, row, ref, e, name, patterns=None):
        """V_m: mean over the traffic patterns and seeds of the log ratio."""
        v = [self.lr(row, ref, e, p, s, name) for p in (patterns or self.patterns) for s in self.seeds]
        v = [x for x in v if x is not None]
        return sum(v) / len(v) if v else None

    def group(self, row, ref, es, name, patterns=None):
        return tci([self.vm(row, ref, e, name, patterns) for e in es])

    def wrong(self, x, name):
        return x is not None and (x < 0 if HIGHER[name] else x > 0)


def load_runs(path):
    R = {}
    for r in csv.DictReader(open(path)):
        size, pat = r['pattern'].split('-', 1)
        R[(r['variant'].rsplit('-p', 1)[0], size, pat, r['mask'], float(r['rate']), int(r['seed']))] = dict(
            accepted=float(r['accepted']), latency=float(r['latency']), p99=float(r['p99']), dead=int(r['dead_ends']), injected=int(r['injected']), received=int(r['received']))
    return R


# =====================================================================================================================
# Part B
# =====================================================================================================================
def part_b():
    P = json.load(open(os.path.join(RES, 'load_points_v26.json')))
    E = json.load(open(os.path.join(RES, 'masks_v26.json')))['part_b']
    drops = json.load(open(os.path.join(RES, 'drops.json')))['dropped'] if os.path.exists(os.path.join(RES, 'drops.json')) else []
    E = [e for e in E if not ('rate8_4x4' in drops and e['size'] == '4x4' and e['rate'] == '8/16') and not ('masks13_16' in drops and e['index'] >= 13)]
    R = load_runs(os.path.join(RES, 'fault_rate_runs.csv'))
    D = Data(R, lambda e, p: P['%s__%s__%s' % (e['size'], p, e['mask'])]['eval'], E, PATTERNS, SEEDS, REFS)
    design = [(row, e['size'], p, e['mask'], r, s) for e in E for p in PATTERNS for row in ROWS for r in D.lad(e, p) for s in SEEDS]
    missing = [k for k in design if k not in R]
    dead = sum(x['dead'] for x in R.values())
    sizes = [z for z in SIZES if any(e['size'] == z for e in E)]

    def cellm(z, rate):
        return [e for e in E if e['size'] == z and e['rate'] == rate]
    cells = [(z, rate) for z in sizes for rate in RATES if cellm(z, rate)]
    L = ['# v26 Part B: performance under random VL faults at four rates (seeds 151, 152; generated by report_v26.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d.%s' % (len(design) - len(missing), len(design), len(missing), dead,
                                                                  (' Dropped by the 40 h rule: %s.' % ', '.join(drops)) if drops else ' Nothing was dropped by the 40 h rule.'),
         'pipe_all 2; every row with DeFT-P\'s VN options and `-traffic_rng 1`; one LUT per mask. Per (size, rate) %d masks drawn at random among the masks with that number of' % max(
             len(cellm(z, r)) for z, r in cells),
         'faulty VLs and a functional VL in every chiplet; traffic uniform and hotspot; loads 0.5, 1.0, 1.4 and 2.0 x Lsat of DeFT-P on the mask. **THR** = the largest accepted',
         'throughput over the four loads; **LAT** and **P99** at 1.0 x Lsat. **Best reference** per (mask, traffic, metric): the one of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran with the best',
         'mean over the two seeds. **Unit = mask**: the value of a mask is the mean over the two traffic patterns and the two seeds of ln(row / reference); the effect of a',
         '(size, rate) is the mean over its masks, as a percentage (THR positive = higher, LAT and P99 negative = lower), with the 95 % t interval and the t test over the masks.',
         'Only the primary table is adjusted (Holm); every other number is unadjusted and descriptive.', '']
    if missing:
        L += ['Missing runs (a (mask, traffic, seed) with a missing run of the row or of a reference is left out of the comparisons it enters): ' +
              '; '.join('%s %s %s %s %s s%d' % k for k in missing[:30]), '']

    # ---- primary family ----
    prim = []
    for z, rate in cells:
        for n in ('THR', 'LAT'):
            m, lo, hi, p, k = D.group(MAIN, 'best', cellm(z, rate), n)
            prim.append(dict(size=z, rate=rate, row=MAIN, reference='best reference', metric=n, n_masks=k, effect_pct=round(pct(m), 2), ci_low=round(pct(lo), 2), ci_high=round(pct(hi), 2),
                             p=float('%.4g' % p), _m=m))
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = float('%.4g' % q)
        x['verdict'] = 'n.s.' if q >= 0.05 else ('supported' if (x['_m'] > 0) == HIGHER[x['metric']] else 'against')
    write(os.path.join(OUT, 'primary.csv'), prim, ['size', 'rate', 'row', 'reference', 'metric', 'n_masks', 'effect_pct', 'ci_low', 'ci_high', 'p', 'p_holm', 'verdict'])
    cnt = lambda v: sum(1 for x in prim if x['verdict'] == v)  # noqa: E731
    L += ['## B.1 Primary family (Holm over %d): `CI_heurLA_X_LF` against the best reference, per size and rate' % len(prim), '',
          '| size | rate | faulty VLs | masks | THR: effect [95 % CI] | p (Holm) | verdict | LAT at 1.0 x Lsat: effect [95 % CI] | p (Holm) | verdict |', '|---|---|---|---|---|---|---|---|---|---|']
    for z, rate in cells:
        a = [x for x in prim if x['size'] == z and x['rate'] == rate and x['metric'] == 'THR'][0]
        b = [x for x in prim if x['size'] == z and x['rate'] == rate and x['metric'] == 'LAT'][0]
        L.append('| %s | %s | %d | %d | %+.1f [%+.1f, %+.1f] | %s | **%s** | %+.1f [%+.1f, %+.1f] | %s | **%s** |' % (
            z, rate, cellm(z, rate)[0]['n_faulty'], a['n_masks'], a['effect_pct'], a['ci_low'], a['ci_high'], pv(a['p_holm']), a['verdict'],
            b['effect_pct'], b['ci_low'], b['ci_high'], pv(b['p_holm']), b['verdict']))
    L += ['', '**Supported %d of %d; against %d; not significant %d.**' % (cnt('supported'), len(prim), cnt('against'), cnt('n.s.')), '']

    # ---- secondary: every row and reference, per (size, rate) ----
    sec = []
    for z, rate in cells:
        es = cellm(z, rate)
        for row in (MAIN, SECOND):
            for ref in ['best'] + REFS + ([MAIN] if row == SECOND else []):
                for n in METRICS + ['LAT05']:
                    for pats, pname in ((None, 'both'), (['uniform'], 'uniform'), (['hotspot'], 'hotspot')):
                        vs = [D.vm(row, ref, e, n, pats) for e in es]
                        ok = [v for v in vs if v is not None]
                        m, lo, hi, p, k = tci(vs)
                        q = quart([pct(v) for v in ok])
                        sec.append(dict(size=z, rate=rate, row=row, reference='best reference' if ref == 'best' else ref, metric=n, traffic=pname, n_masks=k,
                                        effect_pct=round(pct(m), 2) if k else '', ci_low=round(pct(lo), 2) if k > 1 else '', ci_high=round(pct(hi), 2) if k > 1 else '',
                                        p=float('%.4g' % p) if k > 1 else '', min_pct=round(q[0], 2) if k else '', q1_pct=round(q[1], 2) if k else '', median_pct=round(q[2], 2) if k else '',
                                        q3_pct=round(q[3], 2) if k else '', max_pct=round(q[4], 2) if k else '', masks_behind=sum(1 for v in ok if D.wrong(v, n)), _t=(m, lo, hi, p, k)))
    write(os.path.join(OUT, 'secondary.csv'), sec, [c for c in sec[0] if c != '_t'])

    def find(z, rate, row, ref, n, traffic='both'):
        ref = 'best reference' if ref == 'best' else ref
        return [x for x in sec if x['size'] == z and x['rate'] == rate and x['row'] == row and x['reference'] == ref and x['metric'] == n and x['traffic'] == traffic][0]

    # ---- trend over the rate ----
    L += ['## B.2 The trend over the fault rate (effect [95 % CI] over the masks; both traffic patterns)', '',
          '| size | row | against | metric | 1/16 | 2/16 | 4/16 | 8/16 |', '|---|---|---|---|---|---|---|---|']
    for z in sizes:
        for row, ref in ((MAIN, 'best'), (MAIN, 'DeFT_P'), (SECOND, 'best')):
            for n in METRICS:
                L.append('| %s | %s | %s | %s | %s |' % (z, row, 'best reference' if ref == 'best' else ref, n,
                                                       ' | '.join(eff(find(z, rate, row, ref, n)['_t']) if (z, rate) in cells else 'dropped' for rate in RATES)))
    L.append('')
    L += ['## B.3 Each traffic pattern separately: `CI_heurLA_X_LF` against the best reference (effect [95 % CI] over the masks)', '',
          '| size | traffic | metric | 1/16 | 2/16 | 4/16 | 8/16 |', '|---|---|---|---|---|---|---|']
    for z in sizes:
        for t in PATTERNS:
            for n in METRICS:
                L.append('| %s | %s | %s | %s |' % (z, t, n, ' | '.join(eff(find(z, rate, MAIN, 'best', n, t)['_t']) if (z, rate) in cells else 'dropped' for rate in RATES)))
    L.append('')
    L += ['## B.4 `CI_heurLA_X_LF` against each reference row (effect [95 % CI] over the masks; both traffic patterns)', '',
          '| size | rate | metric | DeFT_P | DeFT_B | DeFT_Dis | DeFT_Ran | best reference | the best reference is (cells of mask x traffic): DeFT_P / DeFT_B / DeFT_Dis / DeFT_Ran |',
          '|---|---|---|---|---|---|---|---|---|']
    for z, rate in cells:
        for n in METRICS:
            who = [D.best(e, p, n) for e in cellm(z, rate) for p in PATTERNS]
            L.append('| %s | %s | %s | %s | %s | %s |' % (z, rate, n, ' | '.join(eff(find(z, rate, MAIN, r, n)['_t']) for r in REFS), eff(find(z, rate, MAIN, 'best', n)['_t']),
                                                    ' / '.join(str(sum(1 for w in who if w == r)) for r in REFS)))
    L.append('')

    # ---- distribution over the masks, masks and cells behind ----
    L += ['## B.5 Distribution over the masks: `CI_heurLA_X_LF`, per-mask effect in per cent (minimum / first quartile / median / third quartile / maximum)', '',
          '| size | rate | THR against the best reference | LAT against the best reference | THR against DeFT_P | LAT against DeFT_P |', '|---|---|---|---|---|---|']
    for z, rate in cells:
        c = []
        for ref in ('best', 'DeFT_P'):
            for n in ('THR', 'LAT'):
                x = find(z, rate, MAIN, ref, n)
                c.append('%+.1f / %+.1f / %+.1f / %+.1f / %+.1f' % (x['min_pct'], x['q1_pct'], x['median_pct'], x['q3_pct'], x['max_pct']) if x['n_masks'] else 'n/a')
        L.append('| %s | %s | %s |' % (z, rate, ' | '.join(c)))
    L.append('')
    L += ['## B.6 Where `CI_heurLA_X_LF` is behind: masks (value of the mask on the wrong side of 0) and (mask, traffic) cells (mean over the two seeds on the wrong side)', '',
          '| size | rate | masks | THR behind the best reference: masks / cells | LAT behind the best reference: masks / cells | THR behind DeFT_P: masks / cells | LAT behind DeFT_P: masks / cells |',
          '|---|---|---|---|---|---|---|']
    tot = {}
    for z, rate in cells:
        es, c = cellm(z, rate), []
        for ref in ('best', 'DeFT_P'):
            for n in ('THR', 'LAT'):
                nm = sum(1 for e in es if D.wrong(D.vm(MAIN, ref, e, n), n))
                nc = sum(1 for e in es for p in PATTERNS if D.wrong(D.cell(MAIN, ref, e, p, n), n))
                tot[(ref, n)] = (tot.get((ref, n), (0, 0))[0] + nm, tot.get((ref, n), (0, 0))[1] + nc)
                c.append('%d / %d' % (nm, nc))
        L.append('| %s | %s | %d | %s |' % (z, rate, len(es), ' | '.join(c)))
    L.append('| all | all | %d | %s |' % (len(E), ' | '.join('%d / %d' % tot[(ref, n)] for ref in ('best', 'DeFT_P') for n in ('THR', 'LAT'))))
    L += ['', 'Cells per (size, rate): twice the number of masks (uniform and hotspot).', '']

    # ---- the ten worst cells ----
    def lsat(e, p):
        return P['%s__%s__%s' % (e['size'], p, e['mask'])]['lsat']
    for n, title in (('THR', 'throughput'), ('LAT', 'mean latency at 1.0 x Lsat')):
        allc = [(D.cell(MAIN, 'best', e, p, n), e, p) for e in E for p in PATTERNS]
        allc = [x for x in allc if x[0] is not None]
        allc.sort(key=lambda x: x[0], reverse=not HIGHER[n])
        L += ['## B.7 The ten worst (mask, traffic) cells of `CI_heurLA_X_LF` in %s (against the best reference)' % title, '',
              '| size | rate | # | mask | faults per chiplet | traffic | Lsat | effect | best reference | ' + ' | '.join(ROWS) + ' |', '|---|---|---|---|---|---|---|---|---|' + '---|' * len(ROWS)]
        for v, e, p in allc[:10]:
            vals = [D.smean(r, e, p, n) for r in ROWS]
            L.append('| %s | %s | %d | %s | %s | %s | %s | %+.1f %% | %s | %s |' % (
                e['size'], e['rate'], e['index'], e['mask'], ' '.join(str(x) for x in e['faults_per_chiplet']), p, lsat(e, p), pct(v), D.best(e, p, n),
                ' | '.join(('%.4f' % x if n == 'THR' else '%.1f' % x) if x is not None else 'n/a' for x in vals)))
        L += ['', 'Values: mean over the two seeds (%s).' % ('accepted flits/node/cycle' if n == 'THR' else 'cycles'), '']

    # ---- by the structure of the mask ----
    L += ['## B.8 The effect by the structure of the mask: `CI_heurLA_X_LF` against the best reference (effect [95 % CI] over the masks of the group, all rates of the size)', '',
          '| size | grouped by | value | masks | rates in the group | THR | LAT | THR against DeFT_P |', '|---|---|---|---|---|---|---|---|']
    for z in sizes:
        for key, label in (('max_faults_in_a_chiplet', 'largest number of faults in one chiplet'), ('chiplets_with_one_functional_vl', 'chiplets with one functional VL')):
            for v in sorted({e[key] for e in E if e['size'] == z}):
                es = [e for e in E if e['size'] == z and e[key] == v]
                L.append('| %s | %s | %d | %d | %s | %s | %s | %s |' % (z, label, v, len(es), ', '.join(r for r in RATES if any(e['rate'] == r for e in es)),
                                                                   eff(D.group(MAIN, 'best', es, 'THR')), eff(D.group(MAIN, 'best', es, 'LAT')), eff(D.group(MAIN, 'DeFT_P', es, 'THR'))))
    L.append('')

    # ---- low load ----
    L += ['## B.9 LAT at 0.5 x Lsat against DeFT_P (effect [95 % CI] over the masks; both traffic patterns)', '',
          '| size | row | 1/16 | 2/16 | 4/16 | 8/16 |', '|---|---|---|---|---|---|']
    for z in sizes:
        for row in (MAIN, SECOND):
            L.append('| %s | %s | %s |' % (z, row, ' | '.join(eff(find(z, rate, row, 'DeFT_P', 'LAT05')['_t']) if (z, rate) in cells else 'dropped' for rate in RATES)))
    L.append('')

    # ---- second row ----
    L += ['## B.10 `CI_heurLA_O_LF` against `CI_heurLA_X_LF` (effect [95 % CI] over the masks; both traffic patterns)', '',
          '| size | metric | 1/16 | 2/16 | 4/16 | 8/16 |', '|---|---|---|---|---|---|']
    for z in sizes:
        for n in METRICS + ['LAT05']:
            L.append('| %s | %s | %s |' % (z, 'LAT at 0.5 x Lsat' if n == 'LAT05' else n, ' | '.join(eff(find(z, rate, SECOND, MAIN, n)['_t']) if (z, rate) in cells else 'dropped' for rate in RATES)))
    L.append('')

    # ---- random against even patterns (round 25) ----
    L += random_vs_even(D, E, sizes, cells, cellm, P)

    # ---- THR at the last load ----
    L += ['## B.12 Cells whose largest accepted throughput is at the last load (2.0 x Lsat): THR is then a lower bound for that row', '',
          'Counted per (mask, traffic, seed); %d per (size, rate) and row with 16 masks.' % (16 * len(PATTERNS) * len(SEEDS)), '',
          '| size | rate | ' + ' | '.join(ROWS) + ' |', '|---|---|' + '---|' * len(ROWS)]
    for z, rate in cells:
        c = []
        for row in ROWS:
            k = 0
            for e in cellm(z, rate):
                for p in PATTERNS:
                    for s in SEEDS:
                        v = [R.get((row, z, p, e['mask'], r, s)) for r in D.lad(e, p)]
                        if all(x is not None for x in v) and max(range(4), key=lambda i: v[i]['accepted']) == 3:
                            k += 1
            c.append(str(k))
        L.append('| %s | %s | %s |' % (z, rate, ' | '.join(c)))
    L.append('')

    # ---- absolute values ----
    L += ['## B.13 Absolute values (mean over the masks, the two traffic patterns and the two seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '',
          '| size | rate | mean Lsat (uniform / hotspot) | row | THR | LAT | P99 | LAT at 0.5 x Lsat |', '|---|---|---|---|---|---|---|---|']
    for z, rate in cells:
        es = cellm(z, rate)
        ls = ' / '.join('%.4f' % mean(lsat(e, p) for e in es) for p in PATTERNS)
        for row in ROWS:
            v = {n: [D.smean(row, e, p, n) for e in es for p in PATTERNS] for n in METRICS + ['LAT05']}
            L.append('| %s | %s | %s | %s | %s |' % (z, rate, ls, row, ' | '.join(('%.4f' if n == 'THR' else '%.1f') % mean(x for x in v[n] if x is not None) for n in METRICS + ['LAT05'])))
    low = [(e, p) for e in E for p in PATTERNS if lsat(e, p) < 0.001]
    L += ['', 'Ladders with Lsat below 0.001 (L0 is measured at 0.0002, more than a fifth of Lsat): %d%s.' % (
        len(low), (': ' + '; '.join('%s %s #%d %s %s' % (e['size'], e['rate'], e['index'], p, lsat(e, p)) for e, p in low[:20])) if low else ''), '']
    wmd('summary_B.md', L)

    # ---- paper data ----
    os.makedirs(PD, exist_ok=True)
    pe = []
    for x in sec:
        if x['traffic'] != 'both' or x['metric'] == 'LAT05':
            continue
        y = dict(x)
        pr = [q for q in prim if q['size'] == x['size'] and q['rate'] == x['rate'] and q['row'] == x['row'] and q['reference'] == x['reference'] and q['metric'] == x['metric']]
        y['primary_p_holm'] = pr[0]['p_holm'] if pr else ''
        y['primary_verdict'] = pr[0]['verdict'] if pr else ''
        pe.append(y)
    write(os.path.join(PD, 'fault_rate_effects.csv'), pe, ['size', 'rate', 'row', 'reference', 'metric', 'n_masks', 'effect_pct', 'ci_low', 'ci_high', 'p', 'primary_p_holm', 'primary_verdict',
                                                           'min_pct', 'q1_pct', 'median_pct', 'q3_pct', 'max_pct', 'masks_behind'])
    pm = []
    for e in E:
        for p in PATTERNS:
            row = dict(size=e['size'], rate=e['rate'], faulty_vls=e['n_faulty'], mask_index=e['index'], mask=e['mask'], faults_per_chiplet=' '.join(str(x) for x in e['faults_per_chiplet']),
                       max_faults_in_a_chiplet=e['max_faults_in_a_chiplet'], chiplets_with_one_functional_vl=e['chiplets_with_one_functional_vl'], traffic=p, lsat=lsat(e, p),
                       best_reference_THR=D.best(e, p, 'THR'), best_reference_LAT=D.best(e, p, 'LAT'))
            for n in METRICS:
                for r in ROWS:
                    v = D.smean(r, e, p, n)
                    row['%s_%s' % (n, r)] = '' if v is None else (round(v, 6) if n == 'THR' else round(v, 3))
            pm.append(row)
    write(os.path.join(PD, 'fault_rate_per_mask.csv'), pm)
    write(os.path.join(OUT, 'per_mask.csv'), pm)
    return L


def random_vs_even(D, E, sizes, cells, cellm, P):
    """Rates 4/16 and 8/16 of this round (random masks, the uniform half) next to k = 1 and k = 2 of round 25 (even masks, uniform), both with
    the definitions of this round."""
    f25 = os.path.join(R25, 'fault_runs.csv')
    L = ['## B.11 Random against even patterns at the same share of faulty VLs: this round (uniform traffic only) next to k = 1 and k = 2 of round 25', '']
    if not os.path.exists(f25):
        return L + ['`results_v25_confirm/fault_runs.csv` not found.', '']
    R25r = load_runs(f25)
    P25 = json.load(open(os.path.join(R25, 'load_points_faults.json')))
    E25 = [dict(size=v['size'], mask=v['mask'], k=v['k']) for v in P25.values()]
    D25 = Data(R25r, lambda e, p: P25['%s__%s' % (e['size'], e['mask'])]['eval'], E25, ['uniform'], list(range(131, 136)), REFS)
    L += ['Round 25: k faulty VLs in every chiplet, three masks per (size, k), seeds 131-135. This round: the same number of faulty VLs placed at random, 16 masks, seeds 151-152.',
          'Both computed with the definitions of this round (best reference per mask and metric, unit = mask, uniform traffic). With three masks an interval has 2 degrees of freedom.', '',
          '| size | share | pattern | masks | mean Lsat | THR against the best reference | LAT | THR against DeFT_P | LAT against DeFT_P |', '|---|---|---|---|---|---|---|---|---|']
    for z in sizes:
        for rate, k in (('4/16', 1), ('8/16', 2)):
            if (z, rate) in cells:
                es = cellm(z, rate)
                L.append('| %s | %s | random (this round) | %d | %.4f | %s | %s | %s | %s |' % (
                    z, rate, len(es), mean(P['%s__uniform__%s' % (z, e['mask'])]['lsat'] for e in es), eff(D.group(MAIN, 'best', es, 'THR', ['uniform'])),
                    eff(D.group(MAIN, 'best', es, 'LAT', ['uniform'])), eff(D.group(MAIN, 'DeFT_P', es, 'THR', ['uniform'])), eff(D.group(MAIN, 'DeFT_P', es, 'LAT', ['uniform']))))
            es = [e for e in E25 if e['size'] == z and e['k'] == k]
            L.append('| %s | %s | even, k = %d (round 25) | %d | %.4f | %s | %s | %s | %s |' % (
                z, rate, k, len(es), mean(P25['%s__%s' % (z, e['mask'])]['lsat'] for e in es), eff(D25.group(MAIN, 'best', es, 'THR')), eff(D25.group(MAIN, 'best', es, 'LAT')),
                eff(D25.group(MAIN, 'DeFT_P', es, 'THR')), eff(D25.group(MAIN, 'DeFT_P', es, 'LAT'))))
    return L + ['']


# =====================================================================================================================
# Part A
# =====================================================================================================================
def part_a():
    rows = []
    for fn in ('formal_all_2x2.csv', 'formal_a2.csv'):
        f = os.path.join(RES, fn)
        if os.path.exists(f):
            rows += list(csv.DictReader(open(f)))
    if not rows:
        return None
    summ = []
    for z in SIZES:
        for s in sorted({r['set'] for r in rows if r['size'] == z}):
            r = [x for x in rows if x['size'] == z and x['set'] == s]
            summ.append(dict(size=z, set='all 50,625 masks' if s == 'all' else s, masks=len({x['mask'] for x in r}), relations=len({x['relation'] for x in r}), checks=len(r),
                             passes=sum(int(x['pass']) for x in r), cyclic_cdg=sum(1 for x in r if not int(x['cdg_acyclic'])), with_dead_ends=sum(1 for x in r if int(x['dead_ends']) > 0),
                             cyclic_state_graph=sum(1 for x in r if not int(x['state_graph_acyclic'])), outside_fault_free_cdg=sum(1 for x in r if int(x['edges_outside_fault_free']) > 0),
                             longest_path_hops=max(int(x['longest_path']) for x in r)))
    f = os.path.join(RES, 'formal_subset_2x2.csv')
    if os.path.exists(f):
        r = list(csv.DictReader(open(f)))
        summ.append(dict(size='2x2', set='second-half test (states of the packets to a chiplet)', masks=len({x['mask'] for x in r}), relations=len({x['relation'] for x in r}), checks=len(r),
                         passes=sum(int(x['subset']) for x in r), cyclic_cdg='', with_dead_ends='', cyclic_state_graph='', outside_fault_free_cdg='', longest_path_hops=''))
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'formal_summary.csv'), summ)
    L = ['# v26 Part A: the model check on all fault patterns, and the conformance of the model with the simulator (generated by report_v26.py)', '',
         'Model: `formal/impl_relation_check.py` with the settings of `formal/xy_check.py`; relations `CI_XY_XY` (main row) and `CI_XY_O1` (second row). Checks per mask and',
         'relation: CDG acyclic, no dead-end state, state graph acyclic (no livelock), CDG edges a subset of the fault-free CDG. Details: `formal_all_2x2.md`, `formal_a2.md`,',
         '`formal_subset_2x2.md`, `formal_controls.md`, `conformance.md`, `conformance_controls.md`.', '',
         '## A.1 Summary per size and set', '',
         '| size | set | masks | checks | pass | cyclic CDG | with dead ends | cyclic state graph | CDG edges outside the fault-free CDG | longest path (hops) |', '|---|---|---|---|---|---|---|---|---|---|']
    for x in summ:
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % tuple(x[k] for k in ('size', 'set', 'masks', 'checks', 'passes', 'cyclic_cdg', 'with_dead_ends', 'cyclic_state_graph',
                                                                                              'outside_fault_free_cdg', 'longest_path_hops')))
    tot = [x for x in summ if x['cyclic_cdg'] != '']
    L += ['', '**Model check: %d checks on %d (size, mask) pairs, %d pass.**' % (sum(x['checks'] for x in tot), len({(r['size'], r['mask']) for r in rows}), sum(x['passes'] for x in tot)), '']
    f = os.path.join(RES, 'conformance.csv')
    if os.path.exists(f):
        r = list(csv.DictReader(open(f)))
        L += ['## A.2 Conformance of the model with the simulator (A3)', '',
              '| row | relation | size | seeds | hops compared | arrivals compared | mismatches | runs | statistics byte-identical to bin/noxim |', '|---|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            for row in ('DeFT_P', MAIN, SECOND):
                g = [x for x in r if x['size'] == z and x['row'] == row]
                if g:
                    L.append('| %s | %s | %s | %s | %d | %d | %d | %d | %d |' % (row, g[0]['relation'], z, ', '.join(sorted({x['seed'] for x in g}, key=int)), sum(int(x['hops_compared']) for x in g),
                                                                              sum(int(x['ejections_compared']) for x in g), sum(int(x['mismatches']) + int(x['topology_differences']) for x in g),
                                                                              sum(int(x['runs']) for x in g), sum(int(x['runs_with_identical_statistics']) for x in g)))
        L += ['', '**Conformance: %d hops and %d arrivals compared, %d mismatches.**' % (sum(int(x['hops_compared']) for x in r), sum(int(x['ejections_compared']) for x in r),
                                                                                       sum(int(x['mismatches']) + int(x['topology_differences']) for x in r)), '']
    wmd('summary_A.md', L)
    return L


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)
    part_a()
    if os.path.exists(os.path.join(RES, 'fault_rate_runs.csv')):
        L = part_b()
        print(NL.join(L[:44]))
    f = os.path.join(RES, 'reachability_v26.csv')
    if os.path.exists(f):
        shutil.copy(f, os.path.join(PD, 'reachability_v26.csv'))
    H = ['# v26 report: all tables (generated by report_v26.py; the answers in words are in `../FINDINGS.md`)', '',
         'Where the ten questions of the round are answered:', '', '| question | tables |', '|---|---|',
         '| 1. A1: the exhaustive model check on 2x2 | A.1; `../formal_all_2x2.md` |',
         '| 2. A2: the four sets on 3x3 and 4x4, and the argument for set 2 | A.1; `../formal_a2.md`, `../formal_subset_2x2.md` |',
         '| 3. A3: conformance of the model with the simulator | A.2; `../conformance.md`, `../conformance_controls.md` |',
         '| 4. Primary family of Part B | B.1; computed a second time in `families_check.md` |',
         '| 5. The trend over the fault rate, per size and traffic pattern | B.2, B.3; `extra_B.md` X.2 |',
         '| 6. Where the main row is behind | B.5, B.6, B.7, B.8; `extra_B.md` X.1, X.3, X.4, X.5, X.8 |',
         '| 7. `CI_heurLA_O_LF` against the main row | B.10, B.2; `extra_B.md` X.7 |',
         '| 8. Against each reference row | B.4; `extra_B.md` X.6 |',
         '| 9. Random against even patterns | B.11; `extra_B.md` X.3 |',
         '| 10. Reachability of MTR and RC | `../reachability_v26.md` |', '',
         '`extra_B.md` (written by `extra_v26.py`) holds descriptive tables beyond the pre-registered ones.', '', '---', '']
    S = []
    for name in ('summary_A.md', 'summary_B.md'):
        f = os.path.join(OUT, name)
        if os.path.exists(f):
            S += [open(f, encoding='utf-8').read().rstrip(), '', '---', '']
    f = os.path.join(RES, 'reachability_v26.md')
    if os.path.exists(f):
        S += [open(f, encoding='utf-8').read().rstrip(), '', '---', '']
    if S:
        open(os.path.join(OUT, 'summary.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(H + S[:-2]) + NL)


if __name__ == '__main__':
    main()
