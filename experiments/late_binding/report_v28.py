"""v28 report, following results_v28_anchor/PREREGISTRATION.md (and its addendum).

Usage: python3 report_v28.py [c|d|e|all]      (V28_RES overrides the results directory)
  c    Part C: eval_runs.csv -> report/primary_C.csv, secondary_C.csv, summary_C.md, paper_data/early_best_effects.csv, early_best_per_scenario.csv
  d    Part D: fault_runs.csv and results_v26_faults/fault_rate_runs.csv -> report/primary_D.csv, summary_D.md, paper_data/early_best_faults.csv
  e    Part E: novlrep_runs.csv and results_v26_faults/fault_rate_runs.csv -> report/summary_E.md, paper_data/novlrep_faults.csv
  all  every part whose input exists, then report/summary.md (the concatenation) and paper_data/README.md

Part C: effect of row A against row B on a size = 100 x (exp(mean over the seeds of R_s) - 1) %, R_s = mean over the scenarios of
ln(metric_A / metric_B) for seed s (paired by scenario and seed); 95 % t interval and two-sided one-sample t test over the seeds.
THR = the largest accepted throughput over the loads of the ladder; LAT and P99 at 1.0 x Lsat of DeFT_P.
Parts D and E: unit = mask; V_m = mean over the two traffic patterns and the two seeds of ln(A / B), paired by seed; the effect of a size and
rate is the mean of V_m over its 16 masks, with the 95 % t interval and the t test over the masks.
"""
import csv
import json
import math
import os
import sys

import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V28_RES', os.path.join(HERE, 'results_v28_anchor'))
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
R25 = os.path.join(HERE, 'results_v25_confirm')
R26 = os.path.join(HERE, 'results_v26_faults')
R27 = os.path.join(HERE, 'results_v27_early')
SIZES = ['2x2', '3x3', '4x4']
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
SCEN = ['uniform', 'localized', 'hotspot', 'chipperm', 'chiptrans', 'movinghot']
OTHER5 = [p for p in SCEN if p != 'hotspot']
SETS = [('all', SCEN), ('hotspot', ['hotspot']), ('other five', OTHER5)]
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
MAIN = 'CI_heurLA_X_LF'
TUNED = ['EB_best', 'EB_best64', 'EB_down_t']
PRIMARY_ROWS = ['EB_best', 'EB_down_t']
ANCHORS = ['EB_inf', 'EB_down_inf']
ANCHOR_OF = {'EB_best': 'EB_inf', 'EB_best64': 'EB_inf', 'EB_down_t': 'EB_down_inf'}
ROWS = ['DeFT_P', MAIN] + TUNED + ANCHORS
HIGHER = {'THR': True, 'LAT': False, 'P99': False, 'LAT05': False}
C_SEEDS = list(range(171, 181))
D_RATES = ['1/16', '4/16']
E_RATES = ['1/16', '2/16', '4/16', '8/16']
REFS26 = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran']
NL = chr(10)
NAN = float('nan')


def isnan(x):
    return x != x


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else NAN


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def s1(x):
    """A signed percentage with one decimal; a value that rounds to zero is printed as 0.0 (not as +0.0 or -0.0)."""
    s = '%+.1f' % x
    return '0.0' if s in ('+0.0', '-0.0') else s


def tci(xs):
    """(mean, low, high, p, n) of a sample of log ratios: one-sample t interval and two-sided test against 0."""
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


def eff(t):
    """'+1.2 [+0.3, +2.1]' of a tci() tuple, in per cent."""
    m, lo, hi, p, n = t
    if n == 0:
        return 'n/a'
    if isnan(lo):
        return s1(pct(m))
    return '%s [%s, %s]' % (s1(pct(m)), s1(pct(lo)), s1(pct(hi)))


def pv(p):
    return 'n/a' if isnan(p) else ('%.2g' % p if p < 0.001 else '%.3f' % p)


def r2(x):
    return '' if x is None or isnan(x) else round(x, 2)


def write(path, rows, cols=None):
    cols = cols or (list(rows[0]) if rows else [])
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator=NL, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def wmd(name, L):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


def load_runs(path):
    """{(row, size, pattern, mask, rate, seed): dict of the numeric columns} of a per-run CSV."""
    R = {}
    for r in csv.DictReader(open(path)):
        size, pat = r['pattern'].split('-', 1)
        d = dict(accepted=float(r['accepted']), latency=float(r['latency']), p99=float(r['p99']), offered=float(r['offered']), dead=int(r['dead_ends']),
                 injected=int(r['injected']), received=int(r['received']))
        for k in r:
            if k not in d and k not in ('variant', 'pattern', 'mask', 'rate', 'seed', 'dead_ends', 'vl_source'):
                try:
                    d[k] = float(r[k])
                except ValueError:
                    d[k] = None
        R[(r['variant'].rsplit('-p', 1)[0], size, pat, r['mask'], float(r['rate']), int(r['seed']))] = d
    return R


def choice():
    f = os.path.join(RES, 'tuning_choice_v28.json')
    return json.load(open(f)) if os.path.exists(f) else {}


def below_zero():
    """{size: [rows whose chosen configuration scored below 0 in the tuning]} (3x3 takes the 4x4 choice)."""
    c = choice()
    return {z: [r for r in TUNED if c.get(z, {}).get(r, {}).get('below_zero')] for z in SIZES}


def drops_text():
    DJ = json.load(open(os.path.join(RES, 'drops.json'))) if os.path.exists(os.path.join(RES, 'drops.json')) else {}
    d, back = DJ.get('dropped', []), DJ.get('restored', [])
    return ((' Dropped by the 30 h rule: %s.' % ', '.join(d)) if d else ' Nothing is dropped by the 30 h rule.') + (
        (' Dropped at the timing runs and run after all (`time_rule.md`): %s.' % ', '.join(back)) if back else '')


# =====================================================================================================================
# Part C: evaluation without faults
# =====================================================================================================================
class Eval:
    """The runs of the evaluation: per-run values and log ratios, paired by scenario and seed."""

    def __init__(self, runs, ladders, seeds):
        self.R, self.P, self.seeds = runs, ladders, seeds
        self.rows = [r for r in ROWS if any(k[0] == r for k in runs)]

    def lad(self, z, p):
        return self.P['%s__%s__%s__p2' % (z, p, FREE[z])]['eval']

    def run(self, row, z, p, i, s):
        return self.R.get((row, z, p, FREE[z], self.lad(z, p)[i], s))

    def val(self, row, z, p, s, name):
        """name: THR, LAT, P99, or ('LAT', i) for the latency at load index i."""
        if name == 'THR':
            v = [self.run(row, z, p, i, s) for i in range(9)]
            return None if any(x is None for x in v) else max(x['accepted'] for x in v)
        i = 3 if not isinstance(name, tuple) else name[1]
        r = self.run(row, z, p, i, s)
        if r is None:
            return None
        x = r['p99' if name == 'P99' else 'latency']
        return x if x > 0 else None

    def has(self, row, s):
        return any(k[0] == row and k[5] == s for k in self.R)

    def lr(self, a, b, z, p, s, name):
        """ln(metric of a / metric of b); b may be a function (z, p, name) -> row."""
        rb = b(z, p, name) if callable(b) else b
        x, y = self.val(a, z, p, s, name), self.val(rb, z, p, s, name)
        return None if x is None or y is None else math.log(x / y)

    def Rs(self, a, b, z, name, scen=SCEN):
        """Per seed: the mean over the scenarios of the log ratio (None if a run of the seed is missing)."""
        out = []
        for s in self.seeds:
            v = [self.lr(a, b, z, p, s, name) for p in scen]
            out.append(None if any(x is None for x in v) else sum(v) / len(v))
        return out

    def group(self, a, b, z, name, scen=SCEN):
        return tci(self.Rs(a, b, z, name, scen))

    def smean(self, row, z, p, name):
        v = [self.val(row, z, p, s, name) for s in self.seeds]
        v = [x for x in v if x is not None]
        return mean(v) if v else None

    def better(self, rows):
        """A function (z, p, name) -> the row of `rows` with the better mean over the seeds."""
        def f(z, p, name):
            base = name[0] if isinstance(name, tuple) else name
            c = [(self.smean(r, z, p, name), r) for r in rows]
            c = [x for x in c if x[0] is not None]
            return (max(c) if HIGHER[base] else min(c))[1]
        return f

    def share(self, r, z, n, scen=SCEN, ref='DeFT_P'):
        """(share, smallest per-seed share, largest) of the main row's gain over DeFT_P that row r (or a function of a row) reaches."""
        a, b = self.Rs(r, ref, z, n, scen), self.Rs(MAIN, ref, z, n, scen)
        ok = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
        if not ok:
            return None
        tot = mean(x for x, _ in ok) / mean(y for _, y in ok)
        per = [x / y for x, y in ok if y != 0]
        return tot, min(per), max(per)


def side(t, name):
    """'ahead' / 'behind' of the first row, with '*' if the unadjusted 95 % interval excludes 0."""
    m, lo, hi, p, n = t
    if n == 0:
        return 'n/a'
    good = (m > 0) == HIGHER[name[0] if isinstance(name, tuple) else name]
    clear = not isnan(lo) and (lo > 0 or hi < 0)
    return ('ahead' if good else 'behind') + ('*' if clear else '')


def part_c():
    f = os.path.join(RES, 'eval_runs.csv')
    if not os.path.exists(f):
        return None
    R = load_runs(f)
    E = Eval(R, json.load(open(os.path.join(R25, 'load_points_v25.json'))), C_SEEDS)
    rows = E.rows
    early = [r for r in TUNED if r in rows]
    anchors = [r for r in ANCHORS if r in rows]
    new = early + anchors
    seeds_of = {r: [s for s in C_SEEDS if E.has(r, s)] for r in rows}
    design = [(r, z, p, FREE[z], E.lad(z, p)[i], s) for r in rows for z in SIZES for p in SCEN for i in range(9) for s in seeds_of[r]]
    missing = [k for k in design if k not in R]
    dead = sum(x['dead'] for x in R.values())
    multi = sum(int((x.get('hops_chip_multi') or 0) + (x.get('hops_ipos_multi') or 0)) for k, x in R.items() if k[0].startswith('EB'))
    ch = choice()
    bz = below_zero()
    METS = ['THR', 'LAT', 'P99']
    L = ['# v28 Part C: the strongest early binder without faults (seeds 171-180; generated by report_v28.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d; hops of the early rows that offer more than one output: %d.%s' % (
             len(design) - len(missing), len(design), len(missing), dead, multi, drops_text()),
         'Six fault-free scenarios (uniform, localized, hotspot, chipperm, chiptrans, movinghot), nine loads (0.2 to 2.4 x Lsat of DeFT-P), pipe_all 2, every row with',
         'DeFT-P\'s VN options and `-traffic_rng 1`. **THR** = the largest accepted throughput over the nine loads; **LAT** and **P99** at 1.0 x Lsat. **Effect** of row A',
         'against row B on a size = the mean over the six scenarios and the ten seeds of ln(A / B), as a percentage (THR positive = A higher, LAT and P99 negative = A',
         'lower), with the 95 % t interval and the t test over the ten seeds (per seed the mean over the scenarios). Only the primary table is adjusted (Holm); every',
         'other number is unadjusted and descriptive.', '']
    if ch:
        L += ['The tuned rows (`tuning_choice_v28.json`; 3x3 takes the 4x4 choice):', '', '| size | `EB_best` | `EB_best64` | `EB_down_t` |', '|---|---|---|---|']
        for z in SIZES:
            c = ch[z]
            L.append('| %s | %s (score %+.3f) | T %s (score %+.3f) | `lut_bias` %s (score %+.3f) |' % (
                z, 'S %s, P %d, B %g, T %g' % (c['EB_best']['S'], c['EB_best']['P'], c['EB_best']['B'], c['EB_best']['T']), c['EB_best']['score'],
                '%g' % c['EB_best64']['T'], c['EB_best64']['score'], '%g' % c['EB_down_t']['D'], c['EB_down_t']['score']))
        L.append('')

    # ---- C.1 primary family ----
    prim = []
    for z in SIZES:
        for row in [r for r in PRIMARY_ROWS if r in rows]:
            for n in ('THR', 'LAT'):
                t = E.group(MAIN, row, z, n)
                prim.append(dict(size=z, early_row=row, metric=n, n_seeds=t[4], effect_pct=round(pct(t[0]), 2), ci_low=round(pct(t[1]), 2), ci_high=round(pct(t[2]), 2),
                                 p=float('%.4g' % t[3]), _t=t))
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = float('%.4g' % q)
        x['verdict'] = 'n.s.' if q >= 0.05 else ('supported' if (x['_t'][0] > 0) == HIGHER[x['metric']] else 'against')
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'primary_C.csv'), prim, ['size', 'early_row', 'metric', 'n_seeds', 'effect_pct', 'ci_low', 'ci_high', 'p', 'p_holm', 'verdict'])
    cnt = lambda v: sum(1 for x in prim if x['verdict'] == v)  # noqa: E731
    L += ['## C.1 Primary family 1 (Holm over %d): the main row `CI_heurLA_X_LF` against `EB_best` and `EB_down_t`' % len(prim), '',
          'Effect of the main row against the early row: THR positive and LAT negative mean that the main row is ahead.', '',
          '| size | early row | THR: main against it [95 % CI] | p (Holm) | verdict | LAT at 1.0 x Lsat: main against it [95 % CI] | p (Holm) | verdict |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in [r for r in PRIMARY_ROWS if r in rows]:
            a = [x for x in prim if x['size'] == z and x['early_row'] == row and x['metric'] == 'THR'][0]
            b = [x for x in prim if x['size'] == z and x['early_row'] == row and x['metric'] == 'LAT'][0]
            L.append('| %s | `%s` | %s | %s | **%s** | %s | %s | **%s** |' % (z, row, eff(a['_t']), pv(a['p_holm']), a['verdict'], eff(b['_t']), pv(b['p_holm']), b['verdict']))
    L += ['', '**Supported %d of %d; against %d; not significant %d.**' % (cnt('supported'), len(prim), cnt('against'), cnt('n.s.')), '']

    # ---- secondary table (CSV) ----
    sec = []

    def add(z, a, b, bname, n, scen, sname):
        t = E.group(a, b, z, n, scen)
        nm = n if not isinstance(n, tuple) else 'LAT at %.1f x Lsat' % MULTS[n[1]]
        sec.append(dict(size=z, row=a, against=bname, metric=nm, scenario=sname, n_seeds=t[4], effect_pct=round(pct(t[0]), 2) if t[4] else '',
                        ci_low=round(pct(t[1]), 2) if t[4] > 1 else '', ci_high=round(pct(t[2]), 2) if t[4] > 1 else '', p=float('%.4g' % t[3]) if t[4] > 1 else '', _t=t, _n=n))
        return t
    for z in SIZES:
        for sname, scen in SETS + [(p, [p]) for p in SCEN if p != 'hotspot']:
            for n in METS + [('LAT', i) for i in (0, 1, 2, 4, 5)]:
                for r in rows:
                    if r != 'DeFT_P':
                        add(z, r, 'DeFT_P', 'DeFT_P', n, scen, sname)
                    if r != MAIN:
                        add(z, r, MAIN, MAIN, n, scen, sname)
                for r in early:
                    a = ANCHOR_OF[r]
                    if a in rows:
                        add(z, r, a, a, n, scen, sname)
                if 'EB_best64' in rows and 'EB_best' in rows:
                    add(z, 'EB_best64', 'EB_best', 'EB_best', n, scen, sname)
    write(os.path.join(OUT, 'secondary_C.csv'), sec, ['size', 'row', 'against', 'metric', 'scenario', 'n_seeds', 'effect_pct', 'ci_low', 'ci_high', 'p'])

    def find(z, a, bname, n, sname='all'):
        return [x for x in sec if x['size'] == z and x['row'] == a and x['against'] == bname and x['_n'] == n and x['scenario'] == sname][0]['_t']

    # ---- C.2 every row against DeFT_P, and the share of the main row's gain ----
    L += ['## C.2 Every row against DeFT_P, and the share of the main row\'s gain that it reaches', '',
          'Share = (mean log ratio of the row against DeFT_P) / (mean log ratio of the main row against DeFT_P), per size; in brackets the smallest and the largest of the',
          'ten per-seed shares. 100 % = the row gains what the main row gains; 0 % = it gains nothing over DeFT_P; a negative share = it is behind DeFT_P. *Scenarios*: all',
          'six, hotspot alone, and the other five together.', '',
          '| size | row | scenarios | THR against DeFT_P | share of the main row\'s THR gain | LAT against DeFT_P | share of the main row\'s LAT gain | P99 against DeFT_P |',
          '|---|---|---|---|---|---|---|---|']
    eff_rows = []

    def fsh(sh):
        return '%.0f %% [%.0f, %.0f]' % tuple(100 * x for x in sh) if sh else 'n/a'
    for z in SIZES:
        for r in rows:
            if r == 'DeFT_P':
                continue
            for sname, scen in SETS:
                sh = {n: E.share(r, z, n, scen) for n in ('THR', 'LAT')}
                L.append('| %s | `%s` | %s | %s | %s | %s | %s | %s |' % (z, r, sname, eff(find(z, r, 'DeFT_P', 'THR', sname)), fsh(sh['THR']),
                                                                    eff(find(z, r, 'DeFT_P', 'LAT', sname)), fsh(sh['LAT']), eff(find(z, r, 'DeFT_P', 'P99', sname))))
                e = dict(size=z, row=r, scenarios=sname)
                for n in METS:
                    for bname, tag in (('DeFT_P', 'vs_DeFT_P'), (MAIN, 'vs_main')):
                        if r == bname:
                            e.update({'%s_%s_pct' % (n, tag): '', '%s_%s_ci_low' % (n, tag): '', '%s_%s_ci_high' % (n, tag): ''})
                            continue
                        t = find(z, r, bname, n, sname)
                        e.update({'%s_%s_pct' % (n, tag): r2(pct(t[0])), '%s_%s_ci_low' % (n, tag): r2(pct(t[1])), '%s_%s_ci_high' % (n, tag): r2(pct(t[2]))})
                for n in ('THR', 'LAT'):
                    e['share_of_main_gain_%s_pct' % n] = round(100 * sh[n][0], 1) if sh[n] else ''
                    e['share_%s_seed_min_pct' % n] = round(100 * sh[n][1], 1) if sh[n] else ''
                    e['share_%s_seed_max_pct' % n] = round(100 * sh[n][2], 1) if sh[n] else ''
                eff_rows.append(e)
    L.append('')
    bzr = sorted({(z, r) for z in SIZES for r in bz[z] if r in rows})
    if bzr:
        L += ['### The share of the better of the row and DeFT_P (the chosen configuration scored below 0 in the tuning)', '',
              'Per size, scenario and metric the better of the row and DeFT_P by the mean over the ten seeds; its runs stand for the row.', '',
              '| size | row | scenarios | share of the main row\'s THR gain | share of the main row\'s LAT gain |', '|---|---|---|---|---|']
        for z, r in bzr:
            b = E.better([r, 'DeFT_P'])
            for sname, scen in SETS:
                sh = {}
                for n in ('THR', 'LAT'):
                    a = [mean(E.lr(b(z, p, n), 'DeFT_P', z, p, s, n) for p in scen) if all(E.val(b(z, p, n), z, p, s, n) is not None for p in scen) else None
                         for s in C_SEEDS]
                    m = E.Rs(MAIN, 'DeFT_P', z, n, scen)
                    ok = [(x, y) for x, y in zip(a, m) if x is not None and y is not None]
                    sh[n] = (mean(x for x, _ in ok) / mean(y for _, y in ok), min(x / y for x, y in ok if y), max(x / y for x, y in ok if y)) if ok else None
                L.append('| %s | `%s` | %s | %s | %s |' % (z, r, sname, fsh(sh['THR']), fsh(sh['LAT'])))
        L.append('')
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'early_best_effects.csv'), eff_rows)

    # ---- C.3 every new row against the main row ----
    L += ['## C.3 Every early row against the main row (effect of the row against `CI_heurLA_X_LF`; THR negative and LAT positive mean that the row is behind)', '',
          '| size | row | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for r in new:
            L.append('| %s | `%s` | %s | %s | %s | %s | %s |' % (z, r, eff(find(z, r, MAIN, 'THR')), eff(find(z, r, MAIN, 'LAT')), eff(find(z, r, MAIN, 'P99')),
                                                              eff(find(z, r, MAIN, ('LAT', 0))), eff(find(z, r, MAIN, ('LAT', 1)))))
    L.append('')
    if anchors:
        L += ['## C.4 Each tuned row against its anchor (the T = infinity member of its family: DeFT_P\'s routing with the row\'s draws of the random stream)', '',
              '| size | row | anchor | scenarios | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            for r in early:
                a = ANCHOR_OF[r]
                if a not in rows:
                    continue
                for sname, _ in SETS:
                    L.append('| %s | `%s` | `%s` | %s | %s | %s | %s |' % (z, r, a, sname, eff(find(z, r, a, 'THR', sname)), eff(find(z, r, a, 'LAT', sname)), eff(find(z, r, a, 'P99', sname))))
        L += ['', 'Each anchor against DeFT_P (the same routing, another sequence of the arbitration draws):', '', '| size | anchor | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|']
        for z in SIZES:
            for a in anchors:
                L.append('| %s | `%s` | %s | %s | %s |' % (z, a, eff(find(z, a, 'DeFT_P', 'THR')), eff(find(z, a, 'DeFT_P', 'LAT')), eff(find(z, a, 'DeFT_P', 'P99'))))
        L.append('')
    if 'EB_best64' in rows and 'EB_best' in rows:
        L += ['## C.5 Old information: `EB_best64` against `EB_best`, and the main row against `EB_best64`', '',
              '| size | `EB_best64` against `EB_best`: THR | LAT at 1.0 x Lsat | P99 | main against `EB_best64`: THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            L.append('| %s | %s | %s | %s | %s | %s | %s |' % (z, eff(find(z, 'EB_best64', 'EB_best', 'THR')), eff(find(z, 'EB_best64', 'EB_best', 'LAT')),
                                                            eff(find(z, 'EB_best64', 'EB_best', 'P99')), eff(E.group(MAIN, 'EB_best64', z, 'THR')),
                                                            eff(E.group(MAIN, 'EB_best64', z, 'LAT')), eff(E.group(MAIN, 'EB_best64', z, 'P99'))))
        L += ['', 'By scenario set (`EB_best64` against `EB_best`):', '', '| size | scenarios | THR | LAT at 1.0 x Lsat |', '|---|---|---|---|']
        for z in SIZES:
            for sname, _ in SETS[1:]:
                L.append('| %s | %s | %s | %s |' % (z, sname, eff(find(z, 'EB_best64', 'EB_best', 'THR', sname)), eff(find(z, 'EB_best64', 'EB_best', 'LAT', sname))))
        L.append('')

    # ---- C.6 per scenario ----
    L += ['## C.6 Each scenario separately: every early row against the main row (THR / LAT at 1.0 x Lsat; the mark says where the row stands, * = the unadjusted interval excludes 0)', '']
    psc = []
    for z in SIZES:
        L += ['### %s' % z, '', '| scenario | ' + ' | '.join('`%s`: THR | LAT' % r for r in new) + ' |', '|---|' + '---|---|' * len(new)]
        for p in SCEN:
            c = []
            for r in new:
                for n in ('THR', 'LAT'):
                    t = find(z, r, MAIN, n, p)
                    c.append('%s (%s)' % (s1(pct(t[0])), side(t, n)) if t[4] else 'n/a')
            L.append('| %s | %s |' % (p, ' | '.join(c)))
            for r in rows:
                e = dict(size=z, scenario=p, row=r, THR=E.smean(r, z, p, 'THR'), LAT=E.smean(r, z, p, 'LAT'), P99=E.smean(r, z, p, 'P99'))
                for n in METS:
                    e[n] = '' if e[n] is None else (round(e[n], 6) if n == 'THR' else round(e[n], 3))
                    for bname, tag in (('DeFT_P', 'vs_DeFT_P'), (MAIN, 'vs_main')):
                        if r == bname:
                            e.update({'%s_%s_pct' % (n, tag): '', '%s_%s_ci_low' % (n, tag): '', '%s_%s_ci_high' % (n, tag): ''})
                            continue
                        t = find(z, r, bname, n, p)
                        e.update({'%s_%s_pct' % (n, tag): r2(pct(t[0])) if t[4] else '', '%s_%s_ci_low' % (n, tag): r2(pct(t[1])) if t[4] > 1 else '',
                                  '%s_%s_ci_high' % (n, tag): r2(pct(t[2])) if t[4] > 1 else ''})
                psc.append(e)
        L.append('')
    write(os.path.join(PD, 'early_best_per_scenario.csv'), psc)
    lev = []
    for z in SIZES:
        for p in SCEN:
            for r in early:
                for n in METS:
                    t = find(z, r, MAIN, n, p)
                    if not t[4]:
                        continue
                    ahead = (t[0] > 0) == HIGHER[n] and t[0] != 0
                    level = not isnan(t[1]) and t[1] <= 0 <= t[2]
                    if ahead or level:
                        lev.append((z, p, r, n, t, ahead, level))
    L += ['### Cells in which an early row is level with the main row (the interval includes 0) or ahead of it (%d of %d cells of size x scenario x early row x metric)' % (
        len(lev), len(SIZES) * len(SCEN) * len(early) * len(METS)), '',
          '| size | scenario | early row | metric | the row against the main row [95 % CI] | ahead | interval includes 0 |', '|---|---|---|---|---|---|---|']
    for z, p, r, n, t, ahead, level in lev:
        L.append('| %s | %s | `%s` | %s | %s | %s | %s |' % (z, p, r, n, eff(t), 'yes' if ahead else 'no', 'yes' if level else 'no'))
    L.append('')
    L += ['### Each scenario separately: every row against DeFT_P (THR / LAT at 1.0 x Lsat; the mark says where the row stands against DeFT_P)', '']
    others = [r for r in rows if r != 'DeFT_P']
    for z in SIZES:
        L += ['#### %s' % z, '', '| scenario | ' + ' | '.join('`%s`: THR | LAT' % r for r in others) + ' |', '|---|' + '---|---|' * len(others)]
        for p in SCEN:
            c = []
            for r in others:
                for n in ('THR', 'LAT'):
                    t = find(z, r, 'DeFT_P', n, p)
                    c.append('%s (%s)' % (s1(pct(t[0])), side(t, n)) if t[4] else 'n/a')
            L.append('| %s | %s |' % (p, ' | '.join(c)))
        L.append('')

    # ---- C.7 latency by load ----
    L += ['## C.7 Mean latency at the loads below and above saturation: every row against DeFT_P and against the main row', '']
    for bname in ('DeFT_P', MAIN):
        L += ['Against `%s`:' % bname, '', '| size | row | 0.2 x Lsat | 0.5 x Lsat | 0.8 x Lsat | 1.0 x Lsat | 1.2 x Lsat | 1.4 x Lsat |', '|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            for r in rows:
                if r == bname or r == 'DeFT_P':
                    continue
                L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(eff(find(z, r, bname, n)) for n in (('LAT', 0), ('LAT', 1), ('LAT', 2), 'LAT', ('LAT', 4), ('LAT', 5)))))
        L.append('')

    # ---- C.8 entry VLs, hops, age ----
    anc = json.load(open(os.path.join(R27, 'anchor.json')))
    L += ['## C.8 Entry VLs, path length and the age of the choice (mean over the six scenarios and the ten seeds)', '',
          '*off DeFT-P\'s VL*: share of the packets that move Up on a VL that is not the LUT\'s entry VL for their destination. *imbalance*: the busiest VL (packets Down',
          'plus Up) over the mean VL. *hops*: head-flit forwards per delivered packet (DeFT_P: its anchor row of round 27, seed 101, 1.0 x Lsat). *wait*: in the',
          'source queue before the choice. *to Up*: mean time since generation at the Up move minus mean time since generation at the injection; for the',
          'injection-time rows this is the age of their choice when it takes effect (an estimate from two means over the measured window).', '']

    def vlstats(r, z, scen, i):
        v = [x for x in (E.run(r, z, p, i, s) for p in scen for s in C_SEEDS) if x is not None]

        def m(f):
            w = [y for y in (f(x) for x in v) if y is not None]
            return mean(w) if w else None
        hp = m(lambda x: (x['hops_chip'] + x['hops_ipos']) / x['packets_measured'] if x.get('hops_chip') is not None and x.get('packets_measured') else None)
        if r == 'DeFT_P':
            hp = mean(anc['hops']['%s__%s' % (z, p)] for p in scen) if i == 3 else None
        wait, age = m(lambda x: x.get('entry_inj_wait_mean')), m(lambda x: x.get('entry_up_age_mean'))
        return dict(share=m(lambda x: x['entry_up_not_default'] / x['entry_up_moves'] if x.get('entry_up_moves') else None), imb=m(lambda x: x.get('vl_imbalance')),
                    hops=hp, wait=wait, toup=(age - wait) if age is not None and wait is not None else None)

    def fm(x, form):
        return form % x if x is not None and not isnan(x) else 'n/a'
    for i, lname in ((1, '0.5 x Lsat'), (3, '1.0 x Lsat')):
        L += ['### At %s' % lname, '', '| size | row | off DeFT-P\'s VL | imbalance | hops per packet | wait at the source (cycles) | to Up (cycles) |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            for r in rows:
                q = vlstats(r, z, SCEN, i)
                L.append('| %s | `%s` | %s | %s | %s | %s | %s |' % (z, r, '0 % (by definition)' if r == 'DeFT_P' else fm(100 * q['share'] if q['share'] is not None else None, '%.1f %%'),
                                                                 fm(q['imb'], '%.2f'), fm(q['hops'], '%.2f'), fm(q['wait'], '%.1f'), fm(q['toup'], '%.1f')))
        L.append('')
    L += ['### Per scenario at 1.0 x Lsat: off DeFT-P' + chr(39) + 's VL / imbalance / hops per packet / to Up (cycles)', '']
    for z in SIZES:
        L += ['#### %s' % z, '', '| scenario | `DeFT_P`: imbalance / hops | ' + ' | '.join('`%s`' % r for r in rows if r != 'DeFT_P') + ' |', '|---|---|' + '---|' * (len(rows) - 1)]
        for p in SCEN:
            c = []
            for r in rows:
                q = vlstats(r, z, [p], 3)
                if r == 'DeFT_P':
                    c.append('%s / %s' % (fm(q['imb'], '%.2f'), fm(q['hops'], '%.2f')))
                else:
                    c.append('%s / %s / %s / %s' % (fm(100 * q['share'] if q['share'] is not None else None, '%.0f %%'), fm(q['imb'], '%.2f'), fm(q['hops'], '%.2f'), fm(q['toup'], '%.0f')))
            L.append('| %s | %s |' % (p, ' | '.join(c)))
        L.append('')
    L += ['### Share of the packets off DeFT-P' + chr(39) + 's entry VL by scenario, at 0.5 and 1.0 x Lsat', '',
          '| size | row | ' + ' | '.join('%s 0.5 / 1.0' % p for p in SCEN) + ' |', '|---|---|' + '---|' * len(SCEN)]
    for z in SIZES:
        for r in [x for x in rows if x != 'DeFT_P']:
            c = []
            for p in SCEN:
                a, b = vlstats(r, z, [p], 1)['share'], vlstats(r, z, [p], 3)['share']
                c.append('%s / %s' % (fm(100 * a if a is not None else None, '%.0f %%'), fm(100 * b if b is not None else None, '%.0f %%')))
            L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(c)))
    L.append('')

    # ---- C.9 THR at the last load, C.10 absolute values ----
    L += ['## C.9 Runs in which the largest accepted throughput is at the last load (2.4 x Lsat): THR is then a lower bound for that row', '',
          'Counted per (scenario, seed): 60 per size and row.', '', '| size | ' + ' | '.join('`%s`' % r for r in rows) + ' |', '|---|' + '---|' * len(rows)]
    for z in SIZES:
        c = []
        for r in rows:
            k = 0
            for p in SCEN:
                for s in C_SEEDS:
                    v = [E.run(r, z, p, i, s) for i in range(9)]
                    if all(x is not None for x in v) and max(range(9), key=lambda i: v[i]['accepted']) == 8:
                        k += 1
            c.append(str(k))
        L.append('| %s | %s |' % (z, ' | '.join(c)))
    L += ['', '## C.10 Absolute values (mean over the six scenarios and the ten seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '',
          '| size | row | THR | LAT | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 0.8 x Lsat |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for r in rows:
            v = {n: [E.val(r, z, p, s, n) for p in SCEN for s in C_SEEDS] for n in METS + [('LAT', 0), ('LAT', 1), ('LAT', 2)]}
            L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(('%.4f' if n == 'THR' else '%.1f') % mean(x for x in v[n] if x is not None) for n in METS + [('LAT', 0), ('LAT', 1), ('LAT', 2)])))
    L.append('')

    # ---- C.11 for orientation: the rows of round 27 ----
    f27 = os.path.join(R27, 'paper_data', 'early_late_effects.csv')
    if os.path.exists(f27):
        L += ['## C.11 For orientation only: the rows of round 27 against DeFT_P (seeds 161-170) next to the rows of this round (seeds 171-180)', '',
              'Not the same seeds; the same design. Effect against DeFT_P in % and the share of the main row\'s gain (all six scenarios).', '',
              '| size | row (round) | THR against DeFT_P | share THR | LAT against DeFT_P | share LAT |', '|---|---|---|---|---|---|']
        old = list(csv.DictReader(open(f27)))
        for z in SIZES:
            for x in [y for y in old if y['size'] == z and y['row'] != 'LB_noVLrep']:
                L.append('| %s | `%s` (27) | %s [%s, %s] | %s %% | %s [%s, %s] | %s %% |' % (z, x['row'], x['THR_vs_DeFT_P_pct'], x['THR_vs_DeFT_P_ci_low'], x['THR_vs_DeFT_P_ci_high'],
                                                                                    x['share_of_main_gain_THR_pct'], x['LAT_vs_DeFT_P_pct'], x['LAT_vs_DeFT_P_ci_low'],
                                                                                    x['LAT_vs_DeFT_P_ci_high'], x['share_of_main_gain_LAT_pct']))
            for e in [y for y in eff_rows if y['size'] == z and y['scenarios'] == 'all']:
                L.append('| %s | `%s` (28) | %s [%s, %s] | %s %% | %s [%s, %s] | %s %% |' % (z, e['row'], e['THR_vs_DeFT_P_pct'], e['THR_vs_DeFT_P_ci_low'], e['THR_vs_DeFT_P_ci_high'],
                                                                                    e['share_of_main_gain_THR_pct'], e['LAT_vs_DeFT_P_pct'], e['LAT_vs_DeFT_P_ci_low'],
                                                                                    e['LAT_vs_DeFT_P_ci_high'], e['share_of_main_gain_LAT_pct']))
        L.append('')
    wmd('summary_C.md', L)
    return L


# =====================================================================================================================
# Parts D and E: the designs of round 26
# =====================================================================================================================
def fault_data(new_file, rates, refs):
    """(Data of report_v26 over the runs of round 26 and of this round, the mask entries of the rates, the new runs, keys in both files)."""
    sys.path.insert(0, HERE)
    import report_v26 as RP26
    P = json.load(open(os.path.join(R26, 'load_points_v26.json')))
    ents = [e for e in json.load(open(os.path.join(R26, 'masks_v26.json')))['part_b'] if e['rate'] in rates]
    R = RP26.load_runs(os.path.join(R26, 'fault_rate_runs.csv'))
    new = RP26.load_runs(new_file)
    clash = [k for k in new if k in R]
    R.update(new)
    D = RP26.Data(R, lambda e, p: P['%s__%s__%s' % (e['size'], p, e['mask'])]['eval'], ents, RP26.PATTERNS, RP26.SEEDS, refs)
    return D, ents, new, clash, RP26


def fault_header(D, ents, new, rows, clash, f):
    import report_v26 as RP26
    design = [(r, e['size'], p, e['mask'], x, s) for e in ents for p in RP26.PATTERNS for r in rows(e) for x in D.lad(e, p) for s in RP26.SEEDS]
    missing = [k for k in design if k not in new]
    dead = sum(x['dead'] for x in new.values())
    multi = sum(int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0) for r in csv.DictReader(open(f)) if r['variant'].startswith('EB'))
    return 'New runs: %d of %d; missing: %d; dead-end events: %d; hops of the early rows that offer more than one output: %d; keys also present in the file of round 26: %d.' % (
        len(design) - len(missing), len(design), len(missing), dead, multi, len(clash))


def part_d():
    f = os.path.join(RES, 'fault_runs.csv')
    if not os.path.exists(f) or sum(1 for _ in open(f)) < 2:
        return None
    D, ents, new, clash, RP26 = fault_data(f, D_RATES, REFS26)
    present = sorted({k[0] for k in new})
    early = [r for r in TUNED if r in present]
    anchors = [r for r in ANCHORS if r in present]
    masks_of = {r: {k[3] for k in new if k[0] == r} for r in early + anchors}

    def rows_of(e):
        return [r for r in early + anchors if e['mask'] in masks_of[r]]

    def es(z, rate, sel=None):
        return [e for e in ents if e['size'] == z and e['rate'] == rate and (sel is None or sel(e))]

    def runs_at(r, z, rate):
        return any(e['mask'] in masks_of.get(r, set()) for e in es(z, rate))
    METS = ['THR', 'LAT', 'P99']
    L = ['# v28 Part D: the early rows under random VL faults (seeds 151, 152; generated by report_v28.py)', '',
         fault_header(D, ents, new, rows_of, clash, f) + drops_text(),
         'The design of round 26 at the rates 1/16 and 4/16: 16 random masks per size and rate, uniform and hotspot traffic, loads 0.5, 1.0, 1.4 and 2.0 x Lsat of DeFT-P',
         'on the mask. DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran and the main row are the runs of round 26 (`results_v26_faults/fault_rate_runs.csv`; `reuse_check.md`). **Unit =',
         'mask**: the value of a mask is the mean over the two traffic patterns and the two seeds of ln(row / reference); the effect of a size and rate is the mean over its',
         '16 masks, with the 95 % t interval and the t test over the masks. THR = the largest accepted throughput over the four loads; LAT and P99 at 1.0 x Lsat. Best DeFT',
         'variant per (mask, traffic, metric): the one of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran with the best mean over the two seeds. Only the primary table is adjusted.', '']
    # ---- D.1 primary family 2 ----
    prim = []
    for z in SIZES:
        for rate in D_RATES:
            for row in [r for r in PRIMARY_ROWS if r in early]:
                for n in ('THR', 'LAT'):
                    t = D.group(MAIN, row, es(z, rate), n)
                    prim.append(dict(size=z, rate=rate, early_row=row, metric=n, n_masks=t[4], effect_pct=round(pct(t[0]), 2), ci_low=round(pct(t[1]), 2),
                                     ci_high=round(pct(t[2]), 2), p=float('%.4g' % t[3]), _t=t))
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = float('%.4g' % q)
        x['verdict'] = 'n.s.' if q >= 0.05 else ('supported' if (x['_t'][0] > 0) == HIGHER[x['metric']] else 'against')
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'primary_D.csv'), prim, ['size', 'rate', 'early_row', 'metric', 'n_masks', 'effect_pct', 'ci_low', 'ci_high', 'p', 'p_holm', 'verdict'])
    cnt = lambda v: sum(1 for x in prim if x['verdict'] == v)  # noqa: E731
    L += ['## D.1 Primary family 2 (Holm over %d): the main row against `EB_best` and `EB_down_t` under random VL faults' % len(prim), '',
          'Effect of the main row against the early row over the 16 masks: THR positive and LAT negative mean that the main row is ahead.', '',
          '| size | rate | early row | THR: main against it [95 % CI] | p (Holm) | verdict | LAT at 1.0 x Lsat: main against it [95 % CI] | p (Holm) | verdict |',
          '|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in D_RATES:
            for row in [r for r in PRIMARY_ROWS if r in early]:
                a = [x for x in prim if x['size'] == z and x['rate'] == rate and x['early_row'] == row and x['metric'] == 'THR'][0]
                b = [x for x in prim if x['size'] == z and x['rate'] == rate and x['early_row'] == row and x['metric'] == 'LAT'][0]
                L.append('| %s | %s | `%s` | %s | %s | **%s** | %s | %s | **%s** |' % (z, rate, row, eff(a['_t']), pv(a['p_holm']), a['verdict'], eff(b['_t']), pv(b['p_holm']), b['verdict']))
    L += ['', '**Supported %d of %d; against %d; not significant %d.**' % (cnt('supported'), len(prim), cnt('against'), cnt('n.s.')), '']

    out = []

    def rec(z, rate, row, ref, traffic, sel_name, n, t, behind=None):
        out.append(dict(size=z, rate=rate, row=row, against='best DeFT variant' if ref == 'best' else ref, traffic=traffic, masks_subset=sel_name, metric=n, masks=t[4],
                        effect_pct=r2(pct(t[0])), ci_low=r2(pct(t[1])), ci_high=r2(pct(t[2])), masks_behind='' if behind is None else behind))

    def line(z, rate, a, b, sel=None, sel_name='all', pats=None, traffic='both'):
        c = []
        for n in METS:
            t = D.group(a, b, es(z, rate, sel), n, pats)
            vs = [D.vm(a, b, e, n, pats) for e in es(z, rate, sel)]
            rec(z, rate, a, b, traffic, sel_name, n, t, sum(1 for v in vs if D.wrong(v, n)))
            c.append(eff(t))
        return ' | '.join(c)
    L += ['## D.2 Each early row against the main row, against DeFT_P and against the best DeFT variant (effect [95 % CI] over the 16 masks)', '',
          '| size | rate | row | against the main row: THR | LAT | P99 | against DeFT_P: THR | LAT | P99 | against the best DeFT variant: THR | LAT | P99 |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in D_RATES:
            for r in early + anchors:
                if runs_at(r, z, rate):
                    L.append('| %s | %s | `%s` | %s | %s | %s |' % (z, rate, r, line(z, rate, r, MAIN), line(z, rate, r, 'DeFT_P'), line(z, rate, r, 'best')))
            L.append('| %s | %s | `%s` (round 26) | | | | %s | %s |' % (z, rate, MAIN, line(z, rate, MAIN, 'DeFT_P'), line(z, rate, MAIN, 'best')))
    # ---- D.3 shares ----
    L += ['', '## D.3 The share of the main row' + chr(39) + 's gain over DeFT_P that each early row reaches (ratio of the mean log ratios over the 16 masks)', '',
          '| size | rate | row | both traffic patterns: THR | LAT | uniform: THR | LAT | hotspot: THR | LAT |', '|---|---|---|---|---|---|---|---|---|']
    shares = []
    for z in SIZES:
        for rate in D_RATES:
            for r in early + anchors:
                if not runs_at(r, z, rate):
                    continue
                c = []
                for traffic, pats in (('both', None), ('uniform', ['uniform']), ('hotspot', ['hotspot'])):
                    for n in ('THR', 'LAT'):
                        a, b = D.group(r, 'DeFT_P', es(z, rate), n, pats)[0], D.group(MAIN, 'DeFT_P', es(z, rate), n, pats)[0]
                        ok = not isnan(a) and not isnan(b) and b != 0
                        c.append('%.0f %%' % (100 * a / b) if ok else 'n/a')
                        shares.append(dict(size=z, rate=rate, row=r, traffic=traffic, metric=n, share_of_main_gain_pct=round(100 * a / b, 1) if ok else ''))
                L.append('| %s | %s | `%s` | %s |' % (z, rate, r, ' | '.join(c)))
    # ---- D.4 masks with and without a chiplet left one functional VL ----
    L += ['', '## D.4 By the structure of the mask: masks without and with a chiplet that is left one functional VL (round 26, question 6)', '',
          '| size | rate | chiplets with one functional VL | masks | row | against the main row: THR | LAT | against DeFT_P: THR | LAT |', '|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in D_RATES:
            for name, sel in (('none', lambda e: e['chiplets_with_one_functional_vl'] == 0), ('one or more', lambda e: e['chiplets_with_one_functional_vl'] > 0)):
                if not es(z, rate, sel):
                    continue
                for r in early + [MAIN]:
                    if r != MAIN and not runs_at(r, z, rate):
                        continue
                    c = [eff(D.group(r, MAIN, es(z, rate, sel), n)) if r != MAIN else '' for n in ('THR', 'LAT')] + [eff(D.group(r, 'DeFT_P', es(z, rate, sel), n)) for n in ('THR', 'LAT')]
                    if r != MAIN:
                        for n in ('THR', 'LAT'):
                            rec(z, rate, r, MAIN, 'both', 'one-VL chiplet: ' + name, n, D.group(r, MAIN, es(z, rate, sel), n))
                    L.append('| %s | %s | %s | %d | `%s` | %s |' % (z, rate, name, len(es(z, rate, sel)), r, ' | '.join(c)))
    # ---- D.5 by traffic ----
    L += ['', '## D.5 Each traffic pattern separately: each early row against the main row and against DeFT_P', '',
          '| size | rate | row | uniform, against the main row: THR | LAT | hotspot, against the main row: THR | LAT | uniform, against DeFT_P: THR | LAT | hotspot, against DeFT_P: THR | LAT |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in D_RATES:
            for r in early:
                if not runs_at(r, z, rate):
                    continue
                c = []
                for ref in (MAIN, 'DeFT_P'):
                    for p in RP26.PATTERNS:
                        for n in ('THR', 'LAT'):
                            t = D.group(r, ref, es(z, rate), n, [p])
                            rec(z, rate, r, ref, p, 'all', n, t)
                            c.append(eff(t))
                L.append('| %s | %s | `%s` | %s |' % (z, rate, r, ' | '.join(c)))
    # ---- D.6 old information ----
    if 'EB_best64' in early and 'EB_best' in early:
        L += ['', '## D.6 Old information under faults: `EB_best64` against `EB_best` at the rate 4/16', '', '| size | THR | LAT | P99 | uniform: THR | LAT | hotspot: THR | LAT |',
              '|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            c = [eff(D.group('EB_best64', 'EB_best', es(z, '4/16'), n)) for n in METS] + [eff(D.group('EB_best64', 'EB_best', es(z, '4/16'), n, [p])) for p in RP26.PATTERNS for n in ('THR', 'LAT')]
            L.append('| %s | %s |' % (z, ' | '.join(c)))
    # ---- D.7 anchors ----
    if anchors:
        L += ['', '## D.7 Each tuned row against its anchor, and each anchor against DeFT_P', '', '| size | rate | row | against | THR | LAT | P99 |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            for rate in D_RATES:
                for r in early:
                    a = ANCHOR_OF[r]
                    if a in anchors and runs_at(r, z, rate) and runs_at(a, z, rate):
                        L.append('| %s | %s | `%s` | `%s` | %s |' % (z, rate, r, a, ' | '.join(eff(D.group(r, a, es(z, rate), n)) for n in METS)))
                for a in anchors:
                    if runs_at(a, z, rate):
                        L.append('| %s | %s | `%s` | DeFT_P | %s |' % (z, rate, a, ' | '.join(eff(D.group(a, 'DeFT_P', es(z, rate), n)) for n in METS)))
    # ---- D.8 absolute values ----
    L += ['', '## D.8 Absolute values (mean over the 16 masks, the two traffic patterns and the two seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '',
          '| size | rate | row | THR | LAT | P99 |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in D_RATES:
            for r in REFS26 + [MAIN] + early + anchors:
                v = {n: [D.smean(r, e, p, n) for e in es(z, rate) for p in RP26.PATTERNS] for n in METS}
                if all(x is None for x in v['THR']):
                    continue
                L.append('| %s | %s | `%s` | %s |' % (z, rate, r, ' | '.join(('%.4f' if n == 'THR' else '%.1f') % mean(x for x in v[n] if x is not None) for n in METS)))
    L.append('')
    wmd('summary_D.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'early_best_faults.csv'), out)
    write(os.path.join(PD, 'early_best_faults_shares.csv'), shares)
    return L


def part_e():
    f = os.path.join(RES, 'novlrep_runs.csv')
    if not os.path.exists(f) or sum(1 for _ in open(f)) < 2:
        return None
    D, ents, new, clash, RP26 = fault_data(f, E_RATES, REFS26)
    present = {k[3] for k in new}
    rates = [x for x in E_RATES if any(e['mask'] in present for e in ents if e['rate'] == x)]
    METS = ['THR', 'LAT', 'P99']
    MARGIN = {'THR': 1.0, 'LAT': 3.0}

    def es(z, rate, sel=None):
        return [e for e in ents if e['size'] == z and e['rate'] == rate and (sel is None or sel(e))]
    L = ['# v28 Part E: the reports across the VLs under faults (seeds 151, 152; generated by report_v28.py)', '',
         fault_header(D, [e for e in ents if e['rate'] in rates], new, lambda e: ['LB_noVLrep'], clash, f) + drops_text(),
         '`LB_noVLrep` (the main row without the occupancy reports across the VLs, `-deft_lb up_report 0`) against the main row of round 26 on the masks of round 26,',
         'uniform and hotspot traffic, four loads, two seeds; unit = mask, as in Part D. **The criterion stated before the runs:** the reports are called unnecessary if,',
         'for every size and rate, the 95 % interval lies within +-1 % in THR and within +-3 % in LAT.', '']
    out = []

    def within(t, n):
        return n in MARGIN and not isnan(t[1]) and pct(t[1]) >= -MARGIN[n] and pct(t[2]) <= MARGIN[n]
    L += ['## E.1 `LB_noVLrep` against the main row (effect [95 % CI] over the 16 masks; THR negative and LAT positive mean that the row without the reports is behind)', '',
          '| size | rate | THR | LAT at 1.0 x Lsat | P99 | THR within +-1 % | LAT within +-3 % |', '|---|---|---|---|---|---|---|']
    ok_all = True
    for z in SIZES:
        for rate in rates:
            c, w = [], []
            for n in METS:
                t = D.group('LB_noVLrep', MAIN, es(z, rate), n)
                c.append(eff(t))
                out.append(dict(size=z, rate=rate, masks_subset='all', traffic='both', metric=n, masks=t[4], effect_pct=r2(pct(t[0])), ci_low=r2(pct(t[1])), ci_high=r2(pct(t[2])),
                                within_margin=('yes' if within(t, n) else 'no') if n in MARGIN else ''))
                if n in MARGIN:
                    w.append(within(t, n))
            ok_all = ok_all and all(w)
            L.append('| %s | %s | %s | %s | %s |' % (z, rate, ' | '.join(c), 'yes' if w[0] else '**no**', 'yes' if w[1] else '**no**'))
    L += ['', '**By the stated margin the reports are %s** (every size and rate within the margin: %s).' % ('unnecessary' if ok_all else 'not shown to be unnecessary',
                                                                                                        'yes' if ok_all else 'no'), '']
    L += ['## E.2 The masks with a chiplet that is left one functional VL', '', '| size | rate | masks | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|']

    def one(e):
        return e['chiplets_with_one_functional_vl'] > 0
    for z in SIZES:
        for rate in rates:
            s = es(z, rate, one)
            if not s:
                L.append('| %s | %s | 0 | | | |' % (z, rate))
                continue
            c = []
            for n in METS:
                t = D.group('LB_noVLrep', MAIN, s, n)
                c.append(eff(t))
                out.append(dict(size=z, rate=rate, masks_subset='one-VL chiplet', traffic='both', metric=n, masks=t[4], effect_pct=r2(pct(t[0])), ci_low=r2(pct(t[1])),
                                ci_high=r2(pct(t[2])), within_margin=''))
            L.append('| %s | %s | %d | %s |' % (z, rate, len(s), ' | '.join(c)))
    L += ['', '## E.3 The mask with the largest loss of the row without the reports, per size and rate', '',
          'The mask with the lowest V_m in THR, and the mask with the highest V_m in LAT (V_m: mean over the two traffic patterns and the two seeds).', '',
          '| size | rate | mask (THR) | chiplets with one functional VL | THR | mask (LAT) | chiplets with one functional VL | LAT |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in rates:
            vt = [(D.vm('LB_noVLrep', MAIN, e, 'THR'), e) for e in es(z, rate)]
            vl = [(D.vm('LB_noVLrep', MAIN, e, 'LAT'), e) for e in es(z, rate)]
            vt = [x for x in vt if x[0] is not None]
            vl = [x for x in vl if x[0] is not None]
            if not vt or not vl:
                continue
            a, b = min(vt, key=lambda x: x[0]), max(vl, key=lambda x: x[0])
            L.append('| %s | %s | %d (`%s`) | %d | %s %% | %d (`%s`) | %d | %s %% |' % (z, rate, a[1]['index'], a[1]['mask'], a[1]['chiplets_with_one_functional_vl'], s1(pct(a[0])),
                                                                               b[1]['index'], b[1]['mask'], b[1]['chiplets_with_one_functional_vl'], s1(pct(b[0]))))
    L += ['', '## E.4 Each traffic pattern separately', '', '| size | rate | uniform: THR | LAT | hotspot: THR | LAT |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for rate in rates:
            c = []
            for p in RP26.PATTERNS:
                for n in ('THR', 'LAT'):
                    t = D.group('LB_noVLrep', MAIN, es(z, rate), n, [p])
                    c.append(eff(t))
                    out.append(dict(size=z, rate=rate, masks_subset='all', traffic=p, metric=n, masks=t[4], effect_pct=r2(pct(t[0])), ci_low=r2(pct(t[1])), ci_high=r2(pct(t[2])),
                                    within_margin=''))
            L.append('| %s | %s | %s |' % (z, rate, ' | '.join(c)))
    L.append('')
    wmd('summary_E.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'novlrep_faults.csv'), out)
    return L


def paper_readme():
    T = [('early_best_effects.csv', 'Part C, per size, row and scenario set (all six, hotspot alone, the other five): the effect against DeFT_P and against the main row '
          '(THR, LAT, P99) with the 95 % interval over the ten seeds, and the share of the main row' + chr(39) + 's gain over DeFT_P that the row reaches (THR, LAT) with the '
          'smallest and the largest per-seed share', 'size x row x scenario set'),
         ('early_best_per_scenario.csv', 'Part C, per size, scenario and row: THR, LAT and P99 (mean over the ten seeds) and the effects against DeFT_P and against the main row '
          'with their intervals', 'size x scenario x row'),
         ('early_best_faults.csv', 'Part D, per size, rate and row: the effect against the main row, DeFT_P, the best DeFT variant (THR, LAT, P99), for both traffic patterns, '
          'each alone, and the masks with and without a chiplet left one functional VL (unit = mask; 95 % interval over the masks; `masks_behind` = masks in which the '
          'row is on the wrong side)', 'size x rate x row x reference x traffic x subset x metric'),
         ('early_best_faults_shares.csv', 'Part D: the share of the main row' + chr(39) + 's gain over DeFT_P that each early row reaches, per size, rate and traffic',
          'size x rate x row x traffic x metric'),
         ('novlrep_faults.csv', 'Part E: `LB_noVLrep` against the main row per size and rate (THR, LAT, P99; whether the interval is within the stated margin), the masks with a '
          'chiplet left one functional VL, and each traffic pattern', 'size x rate x subset x traffic x metric'),
         ('tuning_v28.csv', 'Part B: the score of every configuration of the early family (B1), of `EB_best64` (B2) and of `EB_down_t` (B3), with its three terms and the '
          'source of its runs', 'size x configuration')]
    L = ['# paper_data (round 28)', '',
         'One CSV per table or figure. Written by `report_v28.py` and by `experiments_v28.py b_choose` (`tuning_v28.csv`) from the per-run CSVs of `results_v28_anchor/`',
         '(the reused rows of Parts D and E from `results_v26_faults/fault_rate_runs.csv`; DeFT_P, the main row and the P = 0, T = 0 members of the tuning from',
         '`results_v27_early/tune_runs.csv`); nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`.', '',
         '**Effects** are percentages, 100 x (exp(mean log ratio) - 1). Part C: per seed the mean over the scenarios of ln(row / reference); the interval is the 95 % t',
         'interval over the ten seeds. Parts D and E: per mask the mean over the two traffic patterns and the two seeds; the interval is over the 16 masks. THR = the',
         'largest accepted throughput over the loads of the ladder (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet latency at',
         '1.0 x Lsat of DeFT-P (cycles; negative effect = lower). Only the tests of the two primary families are adjusted (`../report/primary_C.csv`,',
         '`../report/primary_D.csv`); everything else is descriptive.', '', '| file | table or figure | rows |', '|---|---|---|']
    L += ['| `%s` | %s | %s |' % t for t in T if os.path.exists(os.path.join(PD, t[0]))]
    open(os.path.join(PD, 'README.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


def main(what):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)
    if what in ('c', 'all'):
        part_c()
    if what in ('d', 'all'):
        part_d()
    if what in ('e', 'all'):
        part_e()
    if what == 'all':
        paper_readme()
        H = ['# v28 report: all tables (generated by report_v28.py; the answers in words are in `../FINDINGS.md`)', '',
             'Where the twelve questions of the round are answered:', '', '| question | tables |', '|---|---|',
             '| 1. Regression and gates; the anchors; v27 reproduced | `../regression_before.md`, `../regression.md`, `../anchor.md`, `../repro_v27.md`, `../unit_checks.md`, '
             '`../drain_v28.csv`, `../drain_v28_tuned.csv`, `../reuse_check.md` |',
             '| 2. The tuning | `../tuning_v28.md` |',
             '| 3. Primary family 1 | C.1; computed a second time in `families_check.md` |',
             '| 4. The share of the main row' + chr(39) + 's gain without faults | C.2 |',
             '| 5. Per scenario | C.6 |',
             '| 6. Latency below saturation | C.7, C.3 |',
             '| 7. How often `EB_best` leaves DeFT-P' + chr(39) + 's entry VL | C.8 |',
             '| 8. `EB_best64` against `EB_best` | C.5, D.6 |',
             '| 9. `EB_down_t` | C.2, C.3, C.6 |',
             '| 10. Primary family 2 and the shares under faults | D.1, D.3; `families_check.md` |',
             '| 11. The reports across the VLs under faults | E |', '', '---', '']
        S = []
        for name in ('summary_C.md', 'summary_D.md', 'summary_E.md'):
            fn = os.path.join(OUT, name)
            if os.path.exists(fn):
                S += [open(fn, encoding='utf-8').read().rstrip(), '', '---', '']
        if S:
            open(os.path.join(OUT, 'summary.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(H + S[:-2]) + NL)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
