"""v27 report, following results_v27_early/PREREGISTRATION.md.

Usage: python3 report_v27.py [d|c|e|all]      (V27_RES overrides the results directory)
  d    Part D: results_v25_confirm/eval_runs.csv -> report/summary_D.md, paper_data/latency_by_load_v25.csv
  c    Part C: eval_runs.csv -> report/primary.csv, secondary.csv, summary_C.md, paper_data/early_late_effects.csv, early_late_per_scenario.csv
  e    Part E: fault_runs.csv and results_v26_faults/fault_rate_runs.csv -> report/summary_E.md, paper_data/early_late_faults.csv
  all  every part whose input exists, then report/summary.md (the concatenation) and paper_data/README.md, tuning_v27.csv

Effect of row A against row B on a size = 100 x (exp(mean over the seeds of R_s) - 1) %, R_s = mean over the scenarios of
ln(metric_A / metric_B) for seed s (paired by scenario and seed); 95 % t interval and two-sided one-sample t test over the seeds.
THR = the largest accepted throughput over the loads of the ladder; LAT and P99 at 1.0 x Lsat of DeFT_P.
"""
import csv
import json
import math
import os
import sys

import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V27_RES', os.path.join(HERE, 'results_v27_early'))
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
R25 = os.path.join(HERE, 'results_v25_confirm')
R26 = os.path.join(HERE, 'results_v26_faults')
SIZES = ['2x2', '3x3', '4x4']
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
SCEN = ['uniform', 'localized', 'hotspot', 'chipperm', 'chiptrans', 'movinghot']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
MAIN = 'CI_heurLA_X_LF'
EARLY = ['EB_vl', 'EB_route', 'EB_vl64', 'EB_down']
PRIMARY_ROWS = ['EB_vl', 'EB_route', 'EB_down']
NEW = EARLY + ['LB_noVLrep']
ROWS = ['DeFT_P', MAIN] + NEW
HIGHER = {'THR': True, 'LAT': False, 'P99': False}
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
        return '%+.1f' % pct(m)
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


# =====================================================================================================================
# Part D: latency at every load, from the runs of round 25
# =====================================================================================================================
D_REFS = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP']
D_SEEDS = list(range(121, 131))
D_GIVEN = {'2x2': [2.0, -0.5, -0.1, -11.0, -29.2], '3x3': [1.5, 0.0, -0.6, -9.7, -49.7], '4x4': [0.9, 0.4, 0.7, -13.2, -39.4]}      # the independent computation, at 0.2 to 1.2 x Lsat


def part_d():
    R = load_runs(os.path.join(R25, 'eval_runs.csv'))
    P = json.load(open(os.path.join(R25, 'load_points_v25.json')))
    rows_all = [MAIN] + D_REFS

    def lad(z, p):
        return P['%s__%s__%s__p2' % (z, p, FREE[z])]['eval']

    def lat(row, z, p, i, s):
        return R[(row, z, p, FREE[z], lad(z, p)[i], s)]['latency']

    L = ['# v27 Part D: the latency of the main row at every load of the ladder (generated by report_v27.py; no new runs)', '',
         'From `results_v25_confirm/eval_runs.csv`: the six fault-free scenarios, seeds 121-130, `CI_heurLA_X_LF` against the best of DeFT_P, DeFT_B, MTR, RC and XY_SP at each',
         'of the nine loads. The best reference is chosen per scenario, size and load: the reference with the lowest mean latency over the ten seeds at that load; its',
         'per-seed values are the reference. Effect = 100 x (exp(mean over the seeds of R_s) - 1) %, R_s = mean over the six scenarios of ln(LAT_main / LAT_best reference);',
         '95 % t interval over the ten seeds. Negative = the main row is faster. No test. The accepted share is accepted / offered throughput (mean over the scenarios and',
         'seeds): below 1 the row no longer delivers what is offered, and its mean latency is that of the packets that arrived.', '']
    out, cmp_lines = [], []
    for z in SIZES:
        L += ['## %s' % z, '', '| load (x Lsat) | LAT, main row against the best reference [95 % CI] | the best reference is (scenarios): ' + ' / '.join(D_REFS) +
              ' | accepted share: main | ' + ' | '.join(D_REFS) + ' |', '|---|---|---|---|' + '---|' * len(D_REFS)]
        got = []
        for i, mult in enumerate(MULTS):
            best = {}
            for p in SCEN:
                best[p] = min(D_REFS, key=lambda r: mean(lat(r, z, p, i, s) for s in D_SEEDS))
            Rs = [mean(math.log(lat(MAIN, z, p, i, s) / lat(best[p], z, p, i, s)) for p in SCEN) for s in D_SEEDS]
            t = tci(Rs)
            share = {r: mean(R[(r, z, p, FREE[z], lad(z, p)[i], s)]['accepted'] / R[(r, z, p, FREE[z], lad(z, p)[i], s)]['offered'] for p in SCEN for s in D_SEEDS) for r in rows_all}
            got.append(pct(t[0]))
            L.append('| %.1f | %s | %s | %.3f | %s |' % (mult, eff(t), ' / '.join(str(sum(1 for p in SCEN if best[p] == r)) for r in D_REFS), share[MAIN],
                                                       ' | '.join('%.3f' % share[r] for r in D_REFS)))
            out.append(dict(size=z, load_x_lsat=mult, scenario='all', rate='', best_reference='per scenario', effect_pct=round(pct(t[0]), 2), ci_low=round(pct(t[1]), 2),
                            ci_high=round(pct(t[2]), 2), **{'lat_' + r: '' for r in rows_all}, **{'accepted_share_' + r: round(share[r], 4) for r in rows_all}))
            for p in SCEN:
                rate = lad(z, p)[i]
                lm = {r: mean(lat(r, z, p, i, s) for s in D_SEEDS) for r in rows_all}
                sh = {r: mean(R[(r, z, p, FREE[z], rate, s)]['accepted'] / R[(r, z, p, FREE[z], rate, s)]['offered'] for s in D_SEEDS) for r in rows_all}
                t1 = tci([math.log(lat(MAIN, z, p, i, s) / lat(best[p], z, p, i, s)) for s in D_SEEDS])
                out.append(dict(size=z, load_x_lsat=mult, scenario=p, rate=rate, best_reference=best[p], effect_pct=round(pct(t1[0]), 2), ci_low=round(pct(t1[1]), 2),
                                ci_high=round(pct(t1[2]), 2), **{'lat_' + r: round(lm[r], 3) for r in rows_all}, **{'accepted_share_' + r: round(sh[r], 4) for r in rows_all}))
        L.append('')
        cmp_lines.append('| %s | %s | %s | %s |' % (z, ' / '.join('%+.1f' % x for x in got[:5]), ' / '.join('%+.1f' % x for x in D_GIVEN[z]),
                                                   'yes' if all(abs(a - b) < 0.051 for a, b in zip(got[:5], D_GIVEN[z])) else 'no'))
    L += ['## Against the independent computation', '',
          'The prompt of the round gives, from an independent computation, the effect at 0.2 / 0.5 / 0.8 / 1.0 / 1.2 x Lsat.', '',
          '| size | this script | independent computation | equal to the printed decimal |', '|---|---|---|---|'] + cmp_lines + ['']
    L += ['## Per scenario', '', 'Mean latency over the ten seeds in cycles; in bold the best reference of the cell.', '']
    for z in SIZES:
        L += ['### %s' % z, '', '| scenario | load (x Lsat) | main | ' + ' | '.join(D_REFS) + ' | main against the best reference |', '|---|---|---|' + '---|' * (len(D_REFS) + 1)]
        for r in out:
            if r['size'] == z and r['scenario'] != 'all':
                L.append('| %s | %.1f | %.1f | %s | %+.1f %% |' % (r['scenario'], r['load_x_lsat'], r['lat_' + MAIN],
                                                                 ' | '.join(('**%.1f**' if x == r['best_reference'] else '%.1f') % r['lat_' + x] for x in D_REFS), r['effect_pct']))
        L.append('')
    wmd('summary_D.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'latency_by_load_v25.csv'), out)
    print(NL.join(L[:60]))
    return L


# =====================================================================================================================
# Part B: the tuning table, from tune_runs.csv
# =====================================================================================================================
TUNE_SCEN = [('uniform', 'free'), ('hotspot', 'free'), ('chipperm', 'free'), ('chiptrans', 'free'), ('uniform', 'north')]
NORTH = {'2x2': '0x1111', '3x3': '0x111111111', '4x4': '0x1111111111111111'}
TUNE_LOADS = (1, 3, 5, 7)


def part_b():
    f = os.path.join(RES, 'tune_runs.csv')
    if not os.path.exists(f):
        return None
    R = load_runs(f)
    P = json.load(open(os.path.join(HERE, 'results_v24_xy', 'load_points_v24.json')))
    choice = json.load(open(os.path.join(RES, 'tuning_choice_v27.json')))
    cfgs = sorted({k[0] for k in R})
    out = []
    for z in ('2x2', '4x4'):
        for cfg in cfgs:
            if cfg == 'DeFT_P':
                continue
            t, l1, l5 = [], [], []
            ok = True
            for p, kind in TUNE_SCEN:
                m = FREE[z] if kind == 'free' else NORTH[z]
                lad = P['%s__%s__%s__p2' % (z, p, m)]['eval']
                for s in (101, 102):
                    try:
                        a = [R[(cfg, z, p, m, lad[i], s)] for i in TUNE_LOADS]
                        b = [R[('DeFT_P', z, p, m, lad[i], s)] for i in TUNE_LOADS]
                    except KeyError:
                        ok = False
                        continue
                    t.append(math.log(max(x['accepted'] for x in a) / max(x['accepted'] for x in b)))
                    l1.append(math.log(a[1]['latency'] / b[1]['latency']))
                    l5.append(math.log(a[0]['latency'] / b[0]['latency']))
            if not ok or not t:
                continue
            row, beta = (cfg.split('_b')[0], float(cfg.split('_b')[1])) if '_b' in cfg else (cfg, '')
            out.append(dict(size=z, row=row, oracle_beta=beta, score=round(mean(t) - mean(l1) - mean(l5), 5), thr_pct=round(pct(mean(t)), 2), lat10_pct=round(pct(mean(l1)), 2),
                            lat05_pct=round(pct(mean(l5)), 2), chosen=int(row in choice[z] and 'beta' in choice[z][row] and choice[z][row]['beta'] == beta)))
    out.sort(key=lambda r: (r['size'], r['row'], r['oracle_beta'] if r['oracle_beta'] != '' else -1))
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'tuning_v27.csv'), out)
    return out


# =====================================================================================================================
# Part C: the evaluation
# =====================================================================================================================
C_SEEDS = list(range(161, 171))


class Eval:
    """The runs of the evaluation: per-run values and log ratios, paired by scenario and seed."""

    def __init__(self, runs, ladders, seeds):
        self.R, self.P, self.seeds = runs, ladders, seeds
        self.rows = [r for r in ROWS + ['EB_lut'] if any(k[0] == r for k in runs)]

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

    def field(self, row, z, i, key, scen=SCEN):
        """Mean over the scenarios and seeds of a counter column at load index i."""
        v = [self.run(row, z, p, i, s) for p in scen for s in self.seeds]
        v = [x[key] for x in v if x is not None and x.get(key) is not None]
        return mean(v) if v else None


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
    early = [r for r in EARLY if r in rows]
    new = [r for r in NEW + ['EB_lut'] if r in rows]
    seeds_of = {r: [s for s in C_SEEDS if E.has(r, s)] for r in rows}
    design = [(r, z, p, FREE[z], E.lad(z, p)[i], s) for r in rows for z in SIZES for p in SCEN for i in range(9) for s in seeds_of[r]]
    missing = [k for k in design if k not in R]
    dead = sum(x['dead'] for x in R.values())
    multi = sum(int((x.get('hops_chip_multi') or 0) + (x.get('hops_ipos_multi') or 0)) for k, x in R.items() if k[0].startswith('EB_'))
    drops = json.load(open(os.path.join(RES, 'drops.json')))['dropped'] if os.path.exists(os.path.join(RES, 'drops.json')) else []
    L = ['# v27 Part C: early against late binding (seeds 161-170; generated by report_v27.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d; hops of the `EB` rows that offer more than one output: %d.%s' % (
             len(design) - len(missing), len(design), len(missing), dead, multi, (' Dropped by the 30 h rule: %s.' % ', '.join(drops)) if drops else ' Nothing was dropped by the 30 h rule.'),
         'Six fault-free scenarios (uniform, localized, hotspot, chipperm, chiptrans, movinghot), nine loads (0.2 to 2.4 x Lsat of DeFT-P), pipe_all 2, every row with',
         'DeFT-P\'s VN options and `-traffic_rng 1`. **THR** = the largest accepted throughput over the nine loads; **LAT** and **P99** at 1.0 x Lsat. **Effect** of row A',
         'against row B on a size = the mean over the six scenarios and the ten seeds of ln(A / B), as a percentage (THR positive = A higher, LAT and P99 negative = A',
         'lower), with the 95 % t interval and the t test over the ten seeds (per seed the mean over the scenarios). Only the primary table is adjusted (Holm); every',
         'other number is unadjusted and descriptive.', '']

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
    write(os.path.join(OUT, 'primary.csv'), prim, ['size', 'early_row', 'metric', 'n_seeds', 'effect_pct', 'ci_low', 'ci_high', 'p', 'p_holm', 'verdict'])
    cnt = lambda v: sum(1 for x in prim if x['verdict'] == v)  # noqa: E731
    L += ['## C.1 Primary family (Holm over %d): the main row `CI_heurLA_X_LF` against each early row' % len(prim), '',
          'Effect of the main row against the early row: THR positive and LAT negative mean that the main row is ahead.', '',
          '| size | early row | THR: main against it [95 % CI] | p (Holm) | verdict | LAT at 1.0 x Lsat: main against it [95 % CI] | p (Holm) | verdict |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in [r for r in PRIMARY_ROWS if r in rows]:
            a = [x for x in prim if x['size'] == z and x['early_row'] == row and x['metric'] == 'THR'][0]
            b = [x for x in prim if x['size'] == z and x['early_row'] == row and x['metric'] == 'LAT'][0]
            L.append('| %s | `%s` | %s | %s | **%s** | %s | %s | **%s** |' % (z, row, eff(a['_t']), pv(a['p_holm']), a['verdict'], eff(b['_t']), pv(b['p_holm']), b['verdict']))
    L += ['', '**Supported %d of %d; against %d; not significant %d.**' % (cnt('supported'), len(prim), cnt('against'), cnt('n.s.')), '']

    # ---- secondary table (CSV) ----
    METS = ['THR', 'LAT', 'P99']
    sec = []

    def add(z, a, b, bname, n, scen, sname):
        t = E.group(a, b, z, n, scen)
        nm = n if not isinstance(n, tuple) else 'LAT at %.1f x Lsat' % MULTS[n[1]]
        sec.append(dict(size=z, row=a, against=bname, metric=nm, scenario=sname, n_seeds=t[4], effect_pct=round(pct(t[0]), 2) if t[4] else '',
                        ci_low=round(pct(t[1]), 2) if t[4] > 1 else '', ci_high=round(pct(t[2]), 2) if t[4] > 1 else '', p=float('%.4g' % t[3]) if t[4] > 1 else '', _t=t, _n=n))
        return t
    bet = E.better(['EB_vl', 'EB_route']) if 'EB_vl' in rows and 'EB_route' in rows else None
    for z in SIZES:
        for scen, sname in [(SCEN, 'all')] + [([p], p) for p in SCEN]:
            for n in METS + [('LAT', i) for i in (0, 1, 2, 4, 5)]:
                for r in rows:
                    if r != 'DeFT_P':
                        add(z, r, 'DeFT_P', 'DeFT_P', n, scen, sname)
                    if r != MAIN:
                        add(z, r, MAIN, MAIN, n, scen, sname)
                if bet:
                    add(z, MAIN, bet, 'the better of EB_vl and EB_route', n, scen, sname)
                if 'EB_vl64' in rows and 'EB_vl' in rows:
                    add(z, 'EB_vl64', 'EB_vl', 'EB_vl', n, scen, sname)
    write(os.path.join(OUT, 'secondary.csv'), sec, ['size', 'row', 'against', 'metric', 'scenario', 'n_seeds', 'effect_pct', 'ci_low', 'ci_high', 'p'])

    def find(z, a, bname, n, sname='all'):
        return [x for x in sec if x['size'] == z and x['row'] == a and x['against'] == bname and x['_n'] == n and x['scenario'] == sname][0]['_t']

    # ---- C.2 every row against DeFT_P, and the share of the main row's gain ----
    L += ['## C.2 Every row against DeFT_P, and the share of the main row\'s gain that it reaches', '',
          'Share = (mean log ratio of the row against DeFT_P) / (mean log ratio of the main row against DeFT_P), per size; in brackets the smallest and the largest of the',
          'ten per-seed shares. 100 % = the row gains what the main row gains; 0 % = it gains nothing over DeFT_P; a negative share = it is behind DeFT_P.', '',
          '| size | row | THR against DeFT_P | share of the main row\'s THR gain | LAT against DeFT_P | share of the main row\'s LAT gain | P99 against DeFT_P |', '|---|---|---|---|---|---|---|']
    eff_rows = []

    def share(z, r, n):
        a, b = E.Rs(r, 'DeFT_P', z, n), E.Rs(MAIN, 'DeFT_P', z, n)
        ok = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
        if not ok:
            return None
        tot = mean(x for x, _ in ok) / mean(y for _, y in ok)
        per = [x / y for x, y in ok if y != 0]
        return tot, min(per), max(per)
    for z in SIZES:
        for r in rows:
            if r == 'DeFT_P':
                continue
            sh = {n: share(z, r, n) for n in ('THR', 'LAT')}
            L.append('| %s | `%s` | %s | %s | %s | %s | %s |' % (
                z, r, eff(find(z, r, 'DeFT_P', 'THR')), '%.0f %% [%.0f, %.0f]' % tuple(100 * x for x in sh['THR']) if sh['THR'] else 'n/a',
                eff(find(z, r, 'DeFT_P', 'LAT')), '%.0f %% [%.0f, %.0f]' % tuple(100 * x for x in sh['LAT']) if sh['LAT'] else 'n/a', eff(find(z, r, 'DeFT_P', 'P99'))))
            e = dict(size=z, row=r)
            for n in METS:
                for bname, tag in (('DeFT_P', 'vs_DeFT_P'), (MAIN, 'vs_main')):
                    if r == MAIN and bname == MAIN:
                        e.update({'%s_%s_pct' % (n, tag): '', '%s_%s_ci_low' % (n, tag): '', '%s_%s_ci_high' % (n, tag): ''})
                        continue
                    t = find(z, r, bname, n)
                    e.update({'%s_%s_pct' % (n, tag): round(pct(t[0]), 2), '%s_%s_ci_low' % (n, tag): round(pct(t[1]), 2), '%s_%s_ci_high' % (n, tag): round(pct(t[2]), 2)})
            for n in ('THR', 'LAT'):
                e['share_of_main_gain_%s_pct' % n] = round(100 * sh[n][0], 1) if sh[n] else ''
                e['share_%s_seed_min_pct' % n] = round(100 * sh[n][1], 1) if sh[n] else ''
                e['share_%s_seed_max_pct' % n] = round(100 * sh[n][2], 1) if sh[n] else ''
            eff_rows.append(e)
    L.append('')
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'early_late_effects.csv'), eff_rows)

    # ---- C.3 every new row against the main row ----
    L += ['## C.3 Every new row against the main row (effect of the row against `CI_heurLA_X_LF`; THR negative and LAT positive mean that the row is behind)', '',
          '| size | row | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for r in new:
            L.append('| %s | `%s` | %s | %s | %s | %s | %s |' % (z, r, eff(find(z, r, MAIN, 'THR')), eff(find(z, r, MAIN, 'LAT')), eff(find(z, r, MAIN, 'P99')),
                                                              eff(find(z, r, MAIN, ('LAT', 0))), eff(find(z, r, MAIN, ('LAT', 1)))))
    L.append('')
    if bet:
        L += ['## C.4 The main row against the better of `EB_vl` and `EB_route` (chosen per size, scenario and metric by the mean over the ten seeds)', '',
              '| size | THR | LAT at 1.0 x Lsat | P99 | the better one is `EB_vl` / `EB_route` (scenarios): THR | LAT | P99 |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            who = {n: [bet(z, p, n) for p in SCEN] for n in METS}
            L.append('| %s | %s | %s | %s | %s |' % (z, eff(find(z, MAIN, 'the better of EB_vl and EB_route', 'THR')), eff(find(z, MAIN, 'the better of EB_vl and EB_route', 'LAT')),
                                                  eff(find(z, MAIN, 'the better of EB_vl and EB_route', 'P99')),
                                                  ' | '.join('%d / %d' % (who[n].count('EB_vl'), who[n].count('EB_route')) for n in METS)))
        L += ['', '`EB_route` against `EB_vl` (positive THR and negative LAT: `EB_route` is the better one):', '', '| size | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
        for z in SIZES:
            L.append('| %s | %s | %s | %s |' % (z, eff(E.group('EB_route', 'EB_vl', z, 'THR')), eff(E.group('EB_route', 'EB_vl', z, 'LAT')), eff(E.group('EB_route', 'EB_vl', z, 'P99'))))
        L.append('')
    if 'EB_vl64' in rows and 'EB_vl' in rows:
        L += ['## C.5 The age of the information: `EB_vl64` against `EB_vl`, and the main row against `EB_vl64`', '',
              '| size | `EB_vl64` against `EB_vl`: THR | LAT at 1.0 x Lsat | P99 | main against `EB_vl64`: THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|---|']
        for z in SIZES:
            L.append('| %s | %s | %s | %s | %s | %s | %s |' % (z, eff(find(z, 'EB_vl64', 'EB_vl', 'THR')), eff(find(z, 'EB_vl64', 'EB_vl', 'LAT')), eff(find(z, 'EB_vl64', 'EB_vl', 'P99')),
                                                            eff(E.group(MAIN, 'EB_vl64', z, 'THR')), eff(E.group(MAIN, 'EB_vl64', z, 'LAT')), eff(E.group(MAIN, 'EB_vl64', z, 'P99'))))
        L.append('')

    # ---- C.6 per scenario ----
    L += ['## C.6 Each scenario separately: every new row against the main row (THR / LAT at 1.0 x Lsat; the mark says where the row stands, * = the unadjusted interval excludes 0)', '']
    psc = []
    for z in SIZES:
        L += ['### %s' % z, '', '| scenario | ' + ' | '.join('`%s`: THR | LAT' % r for r in new) + ' |', '|---|' + '---|---|' * len(new)]
        for p in SCEN:
            c = []
            for r in new:
                for n in ('THR', 'LAT'):
                    t = find(z, r, MAIN, n, p)
                    c.append('%+.1f (%s)' % (pct(t[0]), side(t, n)) if t[4] else 'n/a')
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
                        e.update({'%s_%s_pct' % (n, tag): round(pct(t[0]), 2) if t[4] else '', '%s_%s_ci_low' % (n, tag): round(pct(t[1]), 2) if t[4] > 1 else '',
                                  '%s_%s_ci_high' % (n, tag): round(pct(t[2]), 2) if t[4] > 1 else ''})
                psc.append(e)
        L.append('')
    write(os.path.join(PD, 'early_late_per_scenario.csv'), psc)
    ahead = []
    for z in SIZES:
        for p in SCEN:
            for r in early:
                for n in METS:
                    t = find(z, r, MAIN, n, p)
                    if t[4] and (t[0] > 0) == HIGHER[n] and t[0] != 0:
                        ahead.append((z, p, r, n, t))
    L += ['### Cells in which an early row is ahead of the main row (mean over the ten seeds; %d of %d cells of size x scenario x early row x metric)' % (
        len(ahead), len(SIZES) * len(SCEN) * len(early) * len(METS)), '', '| size | scenario | early row | metric | the row against the main row [95 % CI] | interval excludes 0 |', '|---|---|---|---|---|---|']
    for z, p, r, n, t in ahead:
        L.append('| %s | %s | `%s` | %s | %s | %s |' % (z, p, r, n, eff(t), 'yes' if (t[1] > 0 or t[2] < 0) else 'no'))
    L.append('')

    # ---- C.7 latency by load ----
    L += ['## C.7 Mean latency at the loads below and above saturation: every row against DeFT_P and against the main row', '']
    for bname in ('DeFT_P', MAIN):
        L += ['Against `%s`:' % bname, '', '| size | row | 0.2 x Lsat | 0.5 x Lsat | 0.8 x Lsat | 1.0 x Lsat | 1.2 x Lsat | 1.4 x Lsat |', '|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            for r in rows:
                if r == bname or (r == 'DeFT_P'):
                    continue
                L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(eff(find(z, r, bname, n)) for n in (('LAT', 0), ('LAT', 1), ('LAT', 2), 'LAT', ('LAT', 4), ('LAT', 5)))))
        L.append('')

    # ---- C.8 entry VLs, hops, age ----
    anc = json.load(open(os.path.join(RES, 'anchor.json'))) if os.path.exists(os.path.join(RES, 'anchor.json')) else None
    L += ['## C.8 Entry VLs, path length and the age of the choice, at 1.0 x Lsat (mean over the six scenarios and the ten seeds)', '',
          '*not DeFT-P\'s VL*: share of the packets that move Up on a VL that is not the LUT\'s entry VL for their destination. *imbalance*: the busiest VL (packets Down plus Up)',
          'over the mean VL. *largest Up count*: packets on the busiest Up VL over the whole run. *hops*: head-flit forwards per delivered packet. *time to the Up move*: mean',
          'time since generation at the Up move minus mean time since generation at the injection; for the three injection-time rows this is the age of their choice when it',
          'takes effect (an estimate from two means over the measured window).', '',
          '| size | row | not DeFT-P\'s VL | imbalance | largest Up count | hops per packet | wait in the source queue (cycles) | time from the injection to the Up move (cycles) |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for r in rows:
            up, nd = E.field(r, z, 3, 'entry_up_moves'), E.field(r, z, 3, 'entry_up_not_default')
            v = [E.run(r, z, p, 3, s) for p in SCEN for s in C_SEEDS]
            v = [x for x in v if x is not None]
            sh = mean(x['entry_up_not_default'] / x['entry_up_moves'] for x in v if x.get('entry_up_moves')) if up else None
            hp = mean((x['hops_chip'] + x['hops_ipos']) / x['packets_measured'] for x in v if x.get('hops_chip') is not None and x.get('packets_measured')) if E.field(r, z, 3, 'hops_chip') is not None else None
            if r == 'DeFT_P' and anc:
                hp = mean(anc['hops']['%s__%s' % (z, p)] for p in SCEN)
            wait, age = E.field(r, z, 3, 'entry_inj_wait_mean'), E.field(r, z, 3, 'entry_up_age_mean')
            L.append('| %s | `%s` | %s | %s | %s | %s | %s | %s |' % (
                z, r, '0 % (by definition)' if r == 'DeFT_P' else ('%.1f %%' % (100 * sh) if sh is not None else 'n/a'),
                '%.2f' % E.field(r, z, 3, 'vl_imbalance') if E.field(r, z, 3, 'vl_imbalance') is not None else 'n/a',
                '%.0f' % E.field(r, z, 3, 'vl_max_up') if E.field(r, z, 3, 'vl_max_up') is not None else 'n/a',
                ('%.2f' % hp + (' (anchor row, seed 101)' if r == 'DeFT_P' else '')) if hp is not None else 'n/a',
                '%.1f' % wait if wait is not None else 'n/a', '%.1f' % (age - wait) if age is not None and wait is not None else 'n/a'))
    L.append('')

    # ---- C.9 THR at the last load, absolute values ----
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
    wmd('summary_C.md', L)
    return L


# =====================================================================================================================
# Part E: the early rows under random VL faults (the design of round 26, rate 4/16)
# =====================================================================================================================
E_ROWS = ['EB_vl', 'EB_route', 'EB_down']
E_REFS = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran']


def part_e():
    f = os.path.join(RES, 'fault_runs.csv')
    if not os.path.exists(f) or sum(1 for _ in open(f)) < 2:
        return None
    sys.path.insert(0, HERE)
    import report_v26 as RP26
    P = json.load(open(os.path.join(R26, 'load_points_v26.json')))
    ents = [e for e in json.load(open(os.path.join(R26, 'masks_v26.json')))['part_b'] if e['rate'] == '4/16']
    R = RP26.load_runs(os.path.join(R26, 'fault_rate_runs.csv'))
    new = RP26.load_runs(f)
    clash = [k for k in new if k in R]
    R.update(new)
    D = RP26.Data(R, lambda e, p: P['%s__%s__%s' % (e['size'], p, e['mask'])]['eval'], ents, RP26.PATTERNS, RP26.SEEDS, E_REFS)
    rows = [r for r in E_ROWS if any(k[0] == r for k in new)]
    design = [(r, e['size'], p, e['mask'], x, s) for e in ents for p in RP26.PATTERNS for r in rows for x in D.lad(e, p) for s in RP26.SEEDS]
    missing = [k for k in design if k not in new]
    dead = sum(x['dead'] for x in new.values())
    multi = sum(int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0) for r in csv.DictReader(open(f)) if r['variant'].startswith('EB_'))
    METS = ['THR', 'LAT', 'P99']
    L = ['# v27 Part E: the early rows under random VL faults (seeds 151, 152; generated by report_v27.py)', '',
         'New runs: %d of %d; missing: %d; dead-end events: %d; hops of the `EB` rows that offer more than one output: %d; keys also present in the file of round 26: %d.' % (
             len(design) - len(missing), len(design), len(missing), dead, multi, len(clash)),
         'The design of round 26 at the rate 4/16: 16 random masks per size with a quarter of the VLs faulty, uniform and hotspot traffic, loads 0.5, 1.0, 1.4 and 2.0 x Lsat of',
         'DeFT-P on the mask. DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran and the main row are the runs of round 26 (`results_v26_faults/fault_rate_runs.csv`; `reuse_check.md`). **Unit =',
         'mask**: the value of a mask is the mean over the two traffic patterns and the two seeds of ln(row / reference); the effect of a size is the mean over its 16 masks,',
         'with the 95 % t interval over the masks. THR = the largest accepted throughput over the four loads; LAT and P99 at 1.0 x Lsat. Best DeFT variant per (mask, traffic,',
         'metric): the one of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran with the best mean over the two seeds. Descriptive; no test.', '']
    out = []

    def line(z, a, b, es=None):
        es = [e for e in ents if e['size'] == z] if es is None else es
        c = []
        for n in METS:
            t = D.group(a, b, es, n)
            vs = [D.vm(a, b, e, n) for e in es]
            out.append(dict(size=z, row=a, against='best DeFT variant' if b == 'best' else b, metric=n, masks=t[4], effect_pct=round(pct(t[0]), 2), ci_low=round(pct(t[1]), 2),
                            ci_high=round(pct(t[2]), 2), masks_behind=sum(1 for v in vs if D.wrong(v, n))))
            c.append(eff(t))
        return ' | '.join(c)
    L += ['## E.1 Each early row against the main row, against DeFT_P and against the best DeFT variant (effect [95 % CI] over the 16 masks)', '',
          '| size | row | against the main row: THR | LAT | P99 | against DeFT_P: THR | LAT | P99 | against the best DeFT variant: THR | LAT | P99 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for r in rows:
            L.append('| %s | `%s` | %s | %s | %s |' % (z, r, line(z, r, MAIN), line(z, r, 'DeFT_P'), line(z, r, 'best')))
        L.append('| %s | `%s` (round 26) | | | | %s | %s |' % (z, MAIN, line(z, MAIN, 'DeFT_P'), line(z, MAIN, 'best')))
    L += ['', '## E.2 The share of the main row\'s gain over DeFT_P that each early row reaches (ratio of the mean log ratios over the 16 masks)', '',
          '| size | row | THR | LAT |', '|---|---|---|---|']
    for z in SIZES:
        es = [e for e in ents if e['size'] == z]
        for r in rows:
            c = []
            for n in ('THR', 'LAT'):
                a, b = D.group(r, 'DeFT_P', es, n)[0], D.group(MAIN, 'DeFT_P', es, n)[0]
                c.append('%.0f %%' % (100 * a / b) if b else 'n/a')
            L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(c)))
    L += ['', '## E.3 By the structure of the mask: masks without and with a chiplet that is left one functional VL (round 26, question 6)', '',
          '| size | chiplets with one functional VL | masks | row | against the main row: THR | LAT | against DeFT_P: THR | LAT |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for name, sel in (('none', lambda e: e['chiplets_with_one_functional_vl'] == 0), ('one or more', lambda e: e['chiplets_with_one_functional_vl'] > 0)):
            es = [e for e in ents if e['size'] == z and sel(e)]
            if not es:
                continue
            for r in rows + [MAIN]:
                L.append('| %s | %s | %d | `%s` | %s | %s | %s | %s |' % (
                    z, name, len(es), r, eff(D.group(r, MAIN, es, 'THR')) if r != MAIN else '', eff(D.group(r, MAIN, es, 'LAT')) if r != MAIN else '',
                    eff(D.group(r, 'DeFT_P', es, 'THR')), eff(D.group(r, 'DeFT_P', es, 'LAT'))))
    L += ['', '## E.4 Each traffic pattern separately: each early row against the main row', '', '| size | row | uniform: THR | LAT | hotspot: THR | LAT |', '|---|---|---|---|---|---|']
    for z in SIZES:
        es = [e for e in ents if e['size'] == z]
        for r in rows:
            L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(eff(D.group(r, MAIN, es, n, [p])) for p in RP26.PATTERNS for n in ('THR', 'LAT'))))
    L += ['', '## E.5 Absolute values (mean over the 16 masks, the two traffic patterns and the two seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '',
          '| size | row | THR | LAT | P99 |', '|---|---|---|---|---|']
    for z in SIZES:
        es = [e for e in ents if e['size'] == z]
        for r in E_REFS + [MAIN] + rows:
            v = {n: [D.smean(r, e, p, n) for e in es for p in RP26.PATTERNS] for n in METS}
            L.append('| %s | `%s` | %s |' % (z, r, ' | '.join(('%.4f' if n == 'THR' else '%.1f') % mean(x for x in v[n] if x is not None) for n in METS)))
    L.append('')
    wmd('summary_E.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'early_late_faults.csv'), out)
    return L


def paper_readme():
    T = [('early_late_effects.csv', 'Part C, per size and row: the effect against DeFT_P and against the main row (THR, LAT, P99) with the 95 % interval over the ten seeds, and the '
          'share of the main row\'s gain over DeFT_P that the row reaches (THR, LAT) with the smallest and the largest per-seed share', 'size x row'),
         ('early_late_per_scenario.csv', 'Part C, per size, scenario and row: THR, LAT and P99 (mean over the ten seeds) and the effects against DeFT_P and against the main row '
          'with their intervals', 'size x scenario x row'),
         ('early_late_faults.csv', 'Part E, per size: each early row and the main row against the main row, DeFT_P and the best DeFT variant under random VL faults at the rate '
          '4/16 (unit = mask; 95 % interval over the 16 masks; `masks_behind` = masks in which the row is on the wrong side)', 'size x row x reference x metric'),
         ('latency_by_load_v25.csv', 'Part D, from the runs of round 25: the mean latency of the main row and of the five references at each of the nine loads, per scenario and '
          'over the six scenarios (`scenario` = all), the best reference of the cell, the effect of the main row against it, and the accepted share of the offered load', 'size x load x scenario'),
         ('tuning_v27.csv', 'Part B: the score of every `oracle_beta` value of `EB_vl`, `EB_route` and `EB_vl64` and of the main row on the tuning seeds, with its three terms', 'size x row x value')]
    L = ['# paper_data (round 27)', '',
         'One CSV per table or figure. Written by `report_v27.py` from the per-run CSVs of `results_v27_early/` (Part D from `results_v25_confirm/eval_runs.csv`, the reused rows',
         'of Part E from `results_v26_faults/fault_rate_runs.csv`); nothing here is edited by hand. Definitions: `../PREREGISTRATION.md`.', '',
         '**Effects** are percentages, 100 x (exp(mean log ratio) - 1). Part C and Part D: per seed the mean over the six scenarios of ln(row / reference); the interval is the',
         '95 % t interval over the ten seeds. Part E: per mask the mean over the two traffic patterns and the two seeds; the interval is over the 16 masks. THR = the largest',
         'accepted throughput over the loads of the ladder (flits/node/cycle; positive effect = higher); LAT, P99 = mean and 99th-percentile packet latency at 1.0 x Lsat of',
         'DeFT-P (cycles; negative effect = lower). Only the 18 tests of the primary family are adjusted (`../report/primary.csv`); everything else is descriptive.', '',
         '| file | table or figure | rows |', '|---|---|---|']
    L += ['| `%s` | %s | %s |' % t for t in T if os.path.exists(os.path.join(PD, t[0]))]
    open(os.path.join(PD, 'README.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


def main(what):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)
    if what in ('d', 'all'):
        part_d()
    if what in ('c', 'all'):
        part_c()
    if what in ('e', 'all'):
        part_e()
    if what == 'all':
        part_b()
        paper_readme()
        H = ['# v27 report: all tables (generated by report_v27.py; the answers in words are in `../FINDINGS.md`)', '',
             'Where the thirteen questions of the round are answered:', '', '| question | tables |', '|---|---|',
             '| 1. Regression and gates; the anchor row | `../regression_before.md`, `../regression.md`, `../anchor.md`, `../unit_checks.md`, `../drain_v27.csv`, `../drain_v27_tuned.csv` |',
             '| 2. The tuned `oracle_beta` and the scores | `../tuning_v27.md` |',
             '| 3. Primary family | C.1; computed a second time in `families_check.md` |',
             '| 4. The share of the main row\'s gain | C.2 |',
             '| 5. `EB_vl` against `EB_route` | C.4 |',
             '| 6. Per scenario | C.6 |',
             '| 7. Latency below saturation | C.7, C.3 |',
             '| 8. `EB_vl64` against `EB_vl` | C.5 |',
             '| 9. Why the injection-time rows lose or win | C.8 |',
             '| 10. `EB_down` against DeFT_P | C.2, C.6 |',
             '| 11. `LB_noVLrep` | C.3, C.6 |',
             '| 12. Latency at every load (round 25) | D |',
             '| 13. The early rows under faults | E |', '', '---', '']
        S = []
        for name in ('summary_C.md', 'summary_D.md', 'summary_E.md'):
            f = os.path.join(OUT, name)
            if os.path.exists(f):
                S += [open(f, encoding='utf-8').read().rstrip(), '', '---', '']
        if S:
            open(os.path.join(OUT, 'summary.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(H + S[:-2]) + NL)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
