"""v25 report, following results_v25_confirm/PREREGISTRATION.md.

Usage: python3 report_v25.py [b] [a] [c] [d] [e]     (default: every part whose per-run CSV exists)
  a  addendum_runs.csv (with eval_runs.csv) -> report/addendum.csv, summary_A.md, paper_data/addendum_effects.csv
  b  eval_runs.csv   -> report/primary.csv, secondary.csv, saturation.csv, hops.csv, absolute.csv, summary_B.md, figures,
     paper_data/ (effects per size and per scenario, absolute values, latency against load)
  c  fault_runs.csv  -> report/fault_family.csv, fault_secondary.csv, summary_C.md, paper_data/fault_sweep.csv
  d  app_runs.csv, pair_runs.csv -> report/apps.csv, summary_D.md, paper_data/apps.csv
  e  pipe0_runs.csv  -> report/pipe0.csv, summary_E.md
report/summary.md is the concatenation of the parts that exist (the hardware tables come from report_v25_hw.py).

Effects are 100 x (exp(mean over seeds of R_s) - 1) %, R_s = mean over the scenarios (or masks) of ln(metric_row / metric_reference) for seed s; 95 %
interval and two-sided one-sample t test over the seeds. THR = the largest accepted throughput over the loads; LAT and P99 at 1.0 x Lsat of DeFT-P.
Best baseline per (size, scenario, metric): the reference row available on the scenario with the best mean over the seeds.
"""
import csv
import json
import math
import os
import sys

import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V25_RES', os.path.join(HERE, 'results_v25_confirm'))
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
SIZES = ['2x2', '3x3', '4x4']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
NORTH = {'2x2': '0x1111', '3x3': '0x111111111', '4x4': '0x1111111111111111'}
MAIN, SECOND, DLY, QL = 'CI_heurLA_X_LF', 'CI_heurLA_O_LF', 'CI_heurLA_X_DLY', 'CI_qlLA_X_LF'
FROZEN = [MAIN, SECOND, DLY, QL]
REF_ALL, REF_FF, REF_FAULT = ['DeFT_P', 'DeFT_B'], ['MTR', 'RC', 'XY_SP'], ['DeFT_Dis', 'DeFT_Ran']
METRICS = ['THR', 'LAT', 'P99']
INTS = ('hops_chip', 'hops_chip_multi', 'hops_ipos', 'hops_ipos_multi', 'lookahead_stored', 'lookahead_used', 'lookahead_mismatch', 'lookahead_multi',
        'lookahead_fb_checks', 'lookahead_fb_blocked', 'lookahead_fb_requests', 'lookahead_fb_taken', 'packets_measured', 'vl_max_down', 'vl_max_up')
NEW = ('localized', 'movinghot', 'hotspot+f')
NL = chr(10)
NAN = float('nan')


def faulty(m):
    return int(m, 16) != 0


def sname(sc):
    return sc[0] + ('+f' if faulty(sc[1]) else '')


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else NAN


def isnan(x):
    return x != x


def stat(xs):
    """Effect (%), 95 % interval and two-sided p of a list of per-seed log ratios."""
    n = len(xs)
    if n < 2:
        return dict(n_seeds=n, effect_pct=NAN, ci_low=NAN, ci_high=NAN, p=NAN)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    p = (0.0 if m != 0 else 1.0) if sd == 0 else 2 * st.t.sf(abs(m / (sd / math.sqrt(n))), n - 1)
    return dict(n_seeds=n, effect_pct=round(100 * (math.exp(m) - 1), 2), ci_low=round(100 * (math.exp(m - h) - 1), 2), ci_high=round(100 * (math.exp(m + h) - 1), 2), p=p)


def mci(xs):
    """Mean and 95 % t interval of a list of values (absolute numbers)."""
    xs = [x for x in xs if not isnan(x)]
    n = len(xs)
    if n == 0:
        return NAN, NAN, NAN
    m = sum(xs) / n
    if n < 2:
        return m, NAN, NAN
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    return m, m - h, m + h


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, runv = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        runv = max(runv, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = runv
    return adj


def verdict(x, key='p_holm'):
    if isnan(x[key]) or x[key] >= 0.05:
        return 'n.s.'
    good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
    return 'supported' if good else 'against'


def fmt(x, key='p'):
    if isnan(x['effect_pct']):
        return 'n/a'
    return '%+.1f [%+.1f, %+.1f] (%s %.2g)' % (x['effect_pct'], x['ci_low'], x['ci_high'], key.replace('_', ' '), x[key])


def eci(x):
    return 'n/a' if isnan(x['effect_pct']) else '%+.1f [%+.1f, %+.1f]' % (x['effect_pct'], x['ci_low'], x['ci_high'])


def short(x):
    return 'n/a' if isnan(x['effect_pct']) else '%+.1f' % x['effect_pct']


def write(path, rows):
    if not rows:
        return
    keys = []
    for x in rows:
        keys += [k for k in x if k not in keys]
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator=NL)
        w.writeheader()
        for x in rows:
            w.writerow({k: ('%.4g' % v if k in ('p', 'p_holm') and isinstance(v, float) else v) for k, v in x.items()})


def wmd(name, L):
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


def load_runs(path):
    R = {}
    for r in csv.DictReader(open(path)):
        x = dict(accepted=float(r['accepted']), latency=float(r['latency']), p99=float(r['p99']), dead=int(r['dead_ends']), offered=float(r['offered']),
                 injected=int(r['injected']), received=int(r['received']))
        for k in INTS:
            x[k] = int(r[k]) if r.get(k) not in (None, '') else None
        R[(r['variant'].rsplit('-p', 1)[0], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = x
    return R


class Design:
    """A load-ladder evaluation: rows x sizes x scenarios x loads x seeds, with the best-baseline rule."""

    def __init__(self, R, P, pipe, seeds, scenarios, row_scen, refs_of, idx):
        self.R, self.P, self.pipe, self.seeds, self.scenarios, self.row_scen, self.refs_of, self.idx = R, P, pipe, seeds, scenarios, row_scen, refs_of, idx
        self._best = {}

    def lad(self, z, sc):
        return self.P['%s__%s__%s__p%d' % (z, sc[0], sc[1], self.pipe)]['eval']

    def run(self, row, z, sc, i, s):
        return self.R[(row, '%s-%s' % (z, sc[0]), sc[1], self.lad(z, sc)[i], s)]

    def val(self, row, z, sc, s, name):
        if name == 'THR':
            return max(self.run(row, z, sc, i, s)['accepted'] for i in range(len(self.lad(z, sc))))
        i, f = self.idx[name]
        return self.run(row, z, sc, i, s)[f]

    def smean(self, row, z, sc, name):
        v = []
        for s in self.seeds:
            try:
                v.append(self.val(row, z, sc, s, name))
            except KeyError:
                pass
        return mean(v)

    def best(self, z, sc, name):
        k = (z, sc, name)
        if k not in self._best:
            m = {b: self.smean(b, z, sc, name) for b in self.refs_of(z, sc)}
            m = {b: v for b, v in m.items() if not isnan(v)}
            self._best[k] = (max if name == 'THR' else min)(m, key=m.get) if m else None
        return self._best[k]

    def lr(self, a, ref, z, scs, name):
        out = []
        for s in self.seeds:
            try:
                rs = [math.log(self.val(a, z, sc, s, name) / self.val(self.best(z, sc, name) if ref == 'best' else ref, z, sc, s, name)) for sc in scs]
            except (KeyError, ValueError, ZeroDivisionError):
                continue
            if rs:
                out.append(sum(rs) / len(rs))
        return out

    def test(self, a, ref, z, scs, name):
        return dict(size=z, row=a, reference=ref if ref != 'best' else 'best baseline', metric=name, scenarios='+'.join(sname(sc) for sc in scs),
                    **stat(self.lr(a, ref, z, scs, name)))

    def design(self, rows):
        return [(row, '%s-%s' % (z, sc[0]), sc[1], rate, s) for z in SIZES for row in rows for sc in self.row_scen(row, z) for rate in self.lad(z, sc)
                for s in self.seeds]

    def saturation(self, row, z):
        out = []
        for sc in self.row_scen(row, z):
            ld = self.lad(z, sc)
            n = len(ld)
            means = [mean(self.R[k]['accepted'] for k in [(row, '%s-%s' % (z, sc[0]), sc[1], ld[i], s) for s in self.seeds] if k in self.R) for i in range(n)]
            valid = [i for i in range(n) if not isnan(means[i])]
            if not valid:
                continue
            arg = max(valid, key=lambda i: means[i])
            peak = means[arg]
            out.append(dict(size=z, row=row, scenario=sname(sc), thr_max_at=MULTS[arg], thr_at_top=arg == n - 1, acc_2_0_over_peak=round(means[7] / peak, 4),
                            acc_2_4_over_peak=round(means[8] / peak, 4), lowest_after_peak=round(min(means[i] for i in valid if i >= arg) / peak, 4),
                            monotone=all(means[i + 1] >= means[i] * 0.99 for i in range(n - 1)), peak=round(peak, 5)))
        return out

    def hopstats(self, row, z, idxs=(3,), scs=None):
        t = {k: 0 for k in INTS}
        n = 0
        for sc in (scs or self.row_scen(row, z)):
            for i in idxs:
                for s in self.seeds:
                    try:
                        x = self.run(row, z, sc, i, s)
                    except KeyError:
                        continue
                    if x['hops_chip'] is None:
                        continue
                    n += 1
                    for k in INTS:
                        t[k] += x[k] or 0
        return t if n else None


def pc(a, b):
    return '%.1f %%' % (100.0 * a / b) if b else 'n/a'


IDX9 = {'LAT': (3, 'latency'), 'P99': (3, 'p99'), 'LAT02': (0, 'latency'), 'LAT05': (1, 'latency'), 'LAT14': (5, 'latency')}


# =====================================================================================================================
# Part B
# =====================================================================================================================
def scen_b(z):
    f, n = FREE[z], NORTH[z]
    return [('uniform', f), ('localized', f), ('hotspot', f), ('chipperm', f), ('chiptrans', f), ('movinghot', f), ('uniform', n), ('hotspot', n)]


def part_b():
    P = json.load(open(os.path.join(RES, 'load_points_v25.json')))
    dfile = os.path.join(RES, 'drops.json')
    dropped = json.load(open(dfile))['dropped'] if os.path.exists(dfile) else []
    seeds = list(range(121, 131))
    ref_ff = [r for r in REF_FF if not (r == 'XY_SP' and 'xy_sp' in dropped)]
    rows = FROZEN + REF_ALL + ref_ff + REF_FAULT

    def row_scen(row, z):
        sc = scen_b(z)
        if row in REF_FF:
            return [x for x in sc if not faulty(x[1])] if row in ref_ff else []
        if row in REF_FAULT:
            return [x for x in sc if faulty(x[1])]
        return sc

    def refs_of(z, sc):
        return REF_ALL + (REF_FAULT if faulty(sc[1]) else ref_ff)

    D = Design(load_runs(os.path.join(RES, 'eval_runs.csv')), P, 2, seeds, scen_b, row_scen, refs_of, IDX9)
    des = D.design(rows)        # with 'ql_seeds' dropped, seeds 126-130 of CI_qlLA_X_LF are not in the design; its comparisons use the seeds it has
    if 'ql_seeds' in dropped:
        des = [k for k in des if not (k[0] == QL and k[4] >= 126)]
    missing = [k for k in des if k not in D.R]
    dead = sum(x['dead'] for x in D.R.values())
    refs_txt = 'DeFT_P, DeFT_B, %s (fault-free scenarios) or DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran (scenarios with faults)' % ', '.join(ref_ff)
    L = ['# v25 Part B: main evaluation (seeds 121-130; generated by report_v25.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d.%s' % (len(des) - len(missing), len(des), len(missing), dead,
                                                                   (' Dropped by the 36 h rule: %s.' % ', '.join(dropped)) if dropped else ' Nothing was dropped by the 36 h rule.'),
         'pipe_all 2; every VN-based method with DeFT-P\'s VN options and `-traffic_rng 1`; MTR and RC with `-vc_per_hop 1`. Loads: the nine points of the pipe_all 2',
         'ladders (0.2-2.4 x Lsat of DeFT-P). **THR** = the largest accepted throughput over the nine loads; **LAT** and **P99** at 1.0 x Lsat. Effects are percentages',
         '(THR positive = higher, LAT and P99 negative = lower) with the 95 % interval over the ten seeds. **Best baseline** per (size, scenario, metric): the one of',
         refs_txt + ' with the best mean over the seeds. Scenarios: uniform, localized, hotspot, chipperm, chiptrans, movinghot (fault-free), uniform+f and hotspot+f',
         '(one faulty VL per chiplet); localized, movinghot and hotspot+f were not seen by the v24 tuning. Only the primary table is adjusted (Holm); every other p value',
         'is unadjusted and descriptive.', '']
    if missing:
        L += ['Missing runs (a seed with a missing run in a scenario of a comparison is dropped from that comparison): ' + '; '.join('%s %s %s %s s%d' % k for k in missing[:40]), '']

    # ---- primary family ----
    prim = [D.test(a, 'best', z, scen_b(z), n) for z in SIZES for a in (MAIN, SECOND) for n in METRICS]
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'primary.csv'), prim)
    L += ['## B.1 Primary family (Holm over 18): `CI_heurLA_X_LF` and `CI_heurLA_O_LF` against the best baseline, eight scenarios', '',
          '| size | row | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|']
    for x in prim:
        L.append('| %s | %s | %s | %s | **%s** |' % (x['size'], x['row'], x['metric'], fmt(x, 'p_holm'), x['verdict']))
    cnt = lambda vd: sum(1 for x in prim if x['verdict'] == vd)  # noqa: E731
    L += ['', '**Supported %d of 18; against %d; n.s. %d.**' % (cnt('supported'), cnt('against'), cnt('n.s.')), '']

    # ---- every comparison (secondary.csv) ----
    sec, sat = [], []
    for z in SIZES:
        for row in rows:
            scs = row_scen(row, z)
            if not scs:
                continue
            sat += D.saturation(row, z)
            names = METRICS + ['LAT02', 'LAT05']
            for n in names:
                sec.append(D.test(row, 'best', z, scs, n))
                sec += [D.test(row, 'best', z, [sc], n) for sc in scs]
                for b in rows:
                    if b == row or (b in FROZEN and not (row in FROZEN)):
                        continue
                    bs = [sc for sc in scs if sc in row_scen(b, z)]
                    if bs:
                        sec.append(D.test(row, b, z, bs, n))
                        sec += [D.test(row, b, z, [sc], n) for sc in bs]
            if row in FROZEN:
                seen = [sc for sc in scs if sname(sc) not in NEW]
                new = [sc for sc in scs if sname(sc) in NEW]
                for n in names:
                    sec.append(D.test(row, 'best', z, seen, n))
                    sec.append(D.test(row, 'best', z, new, n))
    # de-duplicate (a single-scenario row list gives the same test twice)
    seen_k, uniq = set(), []
    for x in sec:
        k = (x['size'], x['row'], x['reference'], x['metric'], x['scenarios'])
        if k not in seen_k:
            seen_k.add(k)
            uniq.append(x)
    sec = uniq
    write(os.path.join(OUT, 'secondary.csv'), sec)
    write(os.path.join(OUT, 'saturation.csv'), sat)
    idx = {(x['size'], x['row'], x['reference'], x['metric'], x['scenarios']): x for x in sec}

    def find(z, row, ref, metric, scs):
        return idx[(z, row, ref if ref != 'best' else 'best baseline', metric, '+'.join(sname(sc) for sc in scs))]

    # ---- per size: every row against the best baseline ----
    for z in SIZES:
        L += ['## B.2 %s: every row against the best baseline (over the row\'s scenarios)' % z, '',
              '| row | scenarios | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |', '|---|---|---|---|---|']
        for row in rows:
            scs = row_scen(row, z)
            if not scs:
                continue
            lab = 'all eight' if len(scs) == 8 else ('six fault-free' if len(scs) == 6 else 'two with faults')
            L.append('| %s | %s | %s | %s | %s |' % (row, lab, fmt(find(z, row, 'best', 'THR', scs)), fmt(find(z, row, 'best', 'LAT', scs)), fmt(find(z, row, 'best', 'P99', scs))))
        L.append('')

    # ---- per scenario ----
    L += ['## B.3 Per scenario: the two primary rows against the best baseline (effect [95 % CI]; 2x2 / 3x3 / 4x4)', '',
          '| scenario | tuning saw it | best baseline THR; LAT | `CI_heurLA_X_LF` THR | LAT | P99 | `CI_heurLA_O_LF` THR | LAT | P99 |', '|---|---|---|---|---|---|---|---|---|']
    for k in range(8):
        scn = sname(scen_b('2x2')[k])
        bb = '; '.join(', '.join(str(D.best(z, scen_b(z)[k], n)) for z in SIZES) for n in ('THR', 'LAT'))
        cells = []
        for row in (MAIN, SECOND):
            for n in METRICS:
                cells.append(' / '.join(eci(find(z, row, 'best', n, [scen_b(z)[k]])) for z in SIZES))
        L.append('| %s | %s | %s | %s |' % (scn, 'no' if scn in NEW else 'yes', bb, ' | '.join(cells)))
    L += ['', '## B.4 Scenarios the tuning saw (five) against those it did not (three): effect against the best baseline [95 % CI]', '',
          '| size | row | metric | five seen | three not seen | all eight |', '|---|---|---|---|---|---|']
    for z in SIZES:
        sc = scen_b(z)
        seen = [x for x in sc if sname(x) not in NEW]
        new = [x for x in sc if sname(x) in NEW]
        for row in (MAIN, SECOND):
            for n in METRICS:
                L.append('| %s | %s | %s | %s | %s | %s |' % (z, row, n, eci(find(z, row, 'best', n, seen)), eci(find(z, row, 'best', n, new)), eci(find(z, row, 'best', n, sc))))
    L.append('')

    # ---- against each reference row ----
    L += ['## B.5 Against each reference row separately (over the scenarios both rows ran on; effect [95 % CI]; 2x2 / 3x3 / 4x4)', '',
          '| row | reference | scenarios | THR | LAT | P99 |', '|---|---|---|---|---|---|']
    for row in FROZEN:
        for b in REF_ALL + ref_ff + REF_FAULT:
            cells = []
            for n in METRICS:
                cells.append(' / '.join(eci(find(z, row, b, n, [sc for sc in row_scen(row, z) if sc in row_scen(b, z)])) for z in SIZES))
            lab = 'all eight' if b in REF_ALL else ('six fault-free' if b in REF_FF else 'two with faults')
            L.append('| %s | %s | %s | %s |' % (row, b, lab, ' | '.join(cells)))
    L.append('')

    # ---- DLY against LF, Q-learning against the heuristic ----
    L += ['## B.6 `CI_heurLA_X_DLY` against `CI_heurLA_X_LF` (the same row with the other mechanism; effect [95 % CI])', '',
          '| size | THR | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|']
    for z in SIZES:
        sc = scen_b(z)
        L.append('| %s | %s |' % (z, ' | '.join(eci(find(z, DLY, MAIN, n, sc)) for n in ('THR', 'LAT02', 'LAT05', 'LAT', 'P99'))))
    L += ['', '## B.7 `CI_qlLA_X_LF` against `CI_heurLA_X_LF` per scenario (does learning help; effect [95 % CI]; 2x2 / 3x3 / 4x4)', '',
          '| scenario | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat |', '|---|---|---|---|---|']
    for k in range(8):
        cells = [' / '.join(eci(find(z, QL, MAIN, n, [scen_b(z)[k]])) for z in SIZES) for n in ('THR', 'LAT', 'P99', 'LAT02')]
        L.append('| %s | %s |' % (sname(scen_b('2x2')[k]), ' | '.join(cells)))
    cells = [' / '.join(eci(find(z, QL, MAIN, n, scen_b(z))) for z in SIZES) for n in ('THR', 'LAT', 'P99', 'LAT02')]
    L += ['| **all eight** | %s |' % ' | '.join(cells), '']

    # ---- low load ----
    L += ['## B.8 Low-load latency against DeFT_P (effect [95 % CI] and the difference in cycles; eight scenarios)', '',
          '| size | row | LAT at 0.2 x Lsat | in cycles | LAT at 0.5 x Lsat | in cycles |', '|---|---|---|---|---|---|']
    for z in SIZES:
        sc = scen_b(z)
        for row in FROZEN + ref_ff[:2]:
            scs = [x for x in sc if x in row_scen(row, z)]
            cyc = []
            for n in ('LAT02', 'LAT05'):
                d = [D.smean(row, z, x, n) - D.smean('DeFT_P', z, x, n) for x in scs]
                cyc.append(mean(d))
            L.append('| %s | %s%s | %s | %+.2f | %s | %+.2f |' % (z, row, '' if len(scs) == 8 else ' (six fault-free)', eci(find(z, row, 'DeFT_P', 'LAT02', scs)), cyc[0],
                                                               eci(find(z, row, 'DeFT_P', 'LAT05', scs)), cyc[1]))
    L.append('')

    # ---- beyond the peak ----
    L += ['## B.9 Accepted throughput beyond the peak (mean accepted throughput over the seeds, relative to the row\'s peak; mean and worst over the row\'s scenarios)', '',
          '| size | row | at 2.0 x Lsat | at 2.4 x Lsat | lowest point after the peak | THR maximum at the top load | never falls by more than 1 % between loads |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in rows:
            sv = [x for x in sat if x['size'] == z and x['row'] == row]
            if not sv:
                continue
            f = lambda k: '%.3f (worst %.3f, %s)' % (mean(x[k] for x in sv), min(x[k] for x in sv), min(sv, key=lambda x: x[k])['scenario'])  # noqa: E731
            L.append('| %s | %s | %s | %s | %s | %d of %d | %d of %d |' % (z, row, f('acc_2_0_over_peak'), f('acc_2_4_over_peak'), f('lowest_after_peak'),
                                                                     sum(1 for x in sv if x['thr_at_top']), len(sv), sum(1 for x in sv if x['monotone']), len(sv)))
    L.append('')

    # ---- hops and the lookahead counters ----
    hops = []
    L += ['## B.10 Decision hops, fallback and stale decisions (counters summed over the scenarios and seeds)', '',
          '| size | row | load | hops per packet | hops with more than one offered output: all / interposer | decision hops per packet | stored decisions that differ from a fresh one: of all / of decision hops | fallback: left through another output (of decision hops) | fallback: stored output not free (of checks) |',
          '|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in FROZEN + REF_FAULT:
            for i in (0, 3, 5):
                t = D.hopstats(row, z, (i,))
                if not t:
                    continue
                h = t['hops_chip'] + t['hops_ipos']
                hm = t['hops_chip_multi'] + t['hops_ipos_multi']
                rec = dict(size=z, row=row, load=MULTS[i], **t)
                hops.append(rec)
                la = t['lookahead_used']
                L.append('| %s | %s | %.1f x | %.2f | %s / %s | %.2f | %s | %s | %s |' % (
                    z, row, MULTS[i], h / float(t['packets_measured']) if t['packets_measured'] else NAN, pc(hm, h), pc(t['hops_ipos_multi'], t['hops_ipos']),
                    hm / float(t['packets_measured']) if t['packets_measured'] else NAN,
                    ('%s / %s' % (pc(t['lookahead_mismatch'], la), pc(t['lookahead_mismatch'], t['lookahead_multi']))) if la else '-',
                    pc(t['lookahead_fb_taken'], t['lookahead_multi']) if t['lookahead_multi'] else '-',
                    pc(t['lookahead_fb_blocked'], t['lookahead_fb_checks']) if t['lookahead_fb_checks'] else '-'))
    write(os.path.join(OUT, 'hops.csv'), hops)
    L.append('')

    # ---- absolute values ----
    absr = []
    for z in SIZES:
        for row in rows:
            for sc in row_scen(row, z):
                rec = dict(size=z, row=row, scenario=sname(sc))
                for n in ('THR', 'LAT', 'P99', 'LAT02', 'LAT05'):
                    m, lo, hi = mci([D.val(row, z, sc, s, n) for s in seeds if _has(D, row, z, sc, s, n)])
                    rec[n] = round(m, 5) if not isnan(m) else ''
                    rec[n + '_ci_low'] = round(lo, 5) if not isnan(lo) else ''
                    rec[n + '_ci_high'] = round(hi, 5) if not isnan(hi) else ''
                rec['best_baseline_THR'] = D.best(z, sc, 'THR')
                rec['best_baseline_LAT'] = D.best(z, sc, 'LAT')
                rec['best_baseline_P99'] = D.best(z, sc, 'P99')
                absr.append(rec)
    write(os.path.join(OUT, 'absolute.csv'), absr)
    L += ['## B.11 Absolute values (mean over the seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '']
    for z in SIZES:
        L += ['### %s' % z, '', '| scenario | ' + ' | '.join(rows) + ' |', '|---|' + '---|' * len(rows)]
        for sc in scen_b(z):
            cells = []
            for row in rows:
                r = [x for x in absr if x['size'] == z and x['row'] == row and x['scenario'] == sname(sc)]
                cells.append('%.4f / %.0f / %.0f' % (r[0]['THR'], r[0]['LAT'], r[0]['P99']) if r and r[0]['THR'] != '' else '-')
            L.append('| %s | %s |' % (sname(sc), ' | '.join(cells)))
        L.append('')
    wmd('summary_B.md', L)

    # ---- paper data ----
    os.makedirs(PD, exist_ok=True)
    per_size, per_scen = [], []
    for z in SIZES:
        for row in FROZEN:
            scs = row_scen(row, z)
            for n in METRICS + ['LAT02', 'LAT05']:
                per_size.append(find(z, row, 'best', n, scs))
                for b in REF_ALL + ref_ff + REF_FAULT:
                    bs = [sc for sc in scs if sc in row_scen(b, z)]
                    per_size.append(find(z, row, b, n, bs))
                for sc in scs:
                    per_scen.append(dict(find(z, row, 'best', n, [sc]), best_baseline=D.best(z, sc, n), seen_by_tuning=sname(sc) not in NEW))
                    for b in refs_of(z, sc):
                        per_scen.append(dict(find(z, row, b, n, [sc]), best_baseline='', seen_by_tuning=sname(sc) not in NEW))
    ps_out = []
    for x in per_size:
        y = dict(x)
        m = [q for q in prim if q['size'] == x['size'] and q['row'] == x['row'] and q['metric'] == x['metric']]
        y['primary_p_holm'] = ('%.4g' % m[0]['p_holm']) if (m and x['reference'] == 'best baseline' and x['scenarios'].count('+') >= 7) else ''
        y['primary_verdict'] = m[0]['verdict'] if (m and x['reference'] == 'best baseline' and x['scenarios'].count('+') >= 7) else ''
        ps_out.append(y)
    write(os.path.join(PD, 'effects_per_size.csv'), ps_out)
    write(os.path.join(PD, 'effects_per_scenario.csv'), per_scen)
    write(os.path.join(PD, 'absolute_values.csv'), absr)
    curves(D, rows, row_scen, seeds)
    return L


def _has(D, row, z, sc, s, n):
    try:
        D.val(row, z, sc, s, n)
        return True
    except KeyError:
        return False


def curves(D, rows, row_scen, seeds):
    """Latency, p99 and accepted throughput against the offered load for every row: paper_data/latency_load_<size>_<scenario>.csv and the figures."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    want = ['uniform', 'hotspot', 'chipperm', 'chiptrans', 'uniform+f']
    for z in ('4x4', '2x2'):
        fig, axes = plt.subplots(1, len(want), figsize=(4.2 * len(want), 3.6))
        for ax, scn in zip(axes, want):
            sc = [x for x in scen_b(z) if sname(x) == scn][0]
            out = []
            for row in rows:
                if sc not in row_scen(row, z):
                    continue
                xs, ys = [], []
                for i, rate in enumerate(D.lad(z, sc)):
                    runs = [D.R[k] for k in [(row, '%s-%s' % (z, sc[0]), sc[1], rate, s) for s in seeds] if k in D.R]
                    if not runs:
                        continue
                    rec = dict(size=z, scenario=scn, row=row, load_x_lsat=MULTS[i], rate=rate, offered_flits_per_node_cycle=round(8 * rate, 6), n_seeds=len(runs))
                    for name, key in (('latency', 'latency'), ('p99', 'p99'), ('accepted', 'accepted')):
                        m, lo, hi = mci([r[key] for r in runs])
                        rec[name + '_mean'], rec[name + '_ci_low'], rec[name + '_ci_high'] = round(m, 5), round(lo, 5) if not isnan(lo) else '', round(hi, 5) if not isnan(hi) else ''
                    out.append(rec)
                    xs.append(8 * rate)
                    ys.append(rec['latency_mean'])
                style = dict(lw=2.0, marker='o', ms=3) if row in (MAIN, SECOND) else dict(lw=1.0, marker='.', ms=3, ls='--' if row in FROZEN else '-')
                ax.plot(xs, ys, label=row, **style)
            write(os.path.join(PD, 'latency_load_%s_%s.csv' % (z, scn.replace('+', '_'))), out)
            ax.set_yscale('log')
            ax.set_title('%s %s' % (z, scn), fontsize=10)
            ax.set_xlabel('offered load (flits/node/cycle)')
            ax.grid(True, which='both', lw=0.3)
        axes[0].set_ylabel('mean packet latency (cycles)')
        axes[-1].legend(fontsize=6, loc='upper left')
        fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(os.path.join(OUT, 'latency_load_%s.%s' % (z, ext)), dpi=130)
        plt.close(fig)


# =====================================================================================================================
# Part C
# =====================================================================================================================
def part_c():
    lpf = json.load(open(os.path.join(RES, 'load_points_faults.json')))
    R = load_runs(os.path.join(RES, 'fault_runs.csv'))
    seeds = list(range(131, 136))
    rows = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran', MAIN, SECOND]
    refs = rows[:4]
    masks = sorted(lpf.values(), key=lambda e: (SIZES.index(e['size']), e['k'], e['mask']))
    IDXC = {'LAT': (1, 'latency'), 'P99': (1, 'p99'), 'LAT05': (0, 'latency')}

    def run(row, e, i, s):
        return R[(row, '%s-uniform' % e['size'], e['mask'], e['eval'][i], s)]

    def val(row, e, s, name):
        if name == 'THR':
            return max(run(row, e, i, s)['accepted'] for i in range(4))
        i, f = IDXC[name]
        return run(row, e, i, s)[f]

    def smean(row, e, name):
        v = []
        for s in seeds:
            try:
                v.append(val(row, e, s, name))
            except KeyError:
                pass
        return mean(v)

    bestc = {}

    def best(e, name):
        k = (e['mask'], e['size'], name)
        if k not in bestc:
            m = {b: smean(b, e, name) for b in refs}
            m = {b: v for b, v in m.items() if not isnan(v)}
            bestc[k] = (max if name == 'THR' else min)(m, key=m.get) if m else None
        return bestc[k]

    def lr(a, ref, es, name):
        out = []
        for s in seeds:
            try:
                rs = [math.log(val(a, e, s, name) / val(best(e, name) if ref == 'best' else ref, e, s, name)) for e in es]
            except (KeyError, ValueError, ZeroDivisionError):
                continue
            if rs:
                out.append(sum(rs) / len(rs))
        return out

    def test(a, ref, z, k, name):
        es = [e for e in masks if e['size'] == z and e['k'] == k]
        return dict(size=z, k=k, row=a, reference=ref if ref != 'best' else 'best reference row', metric=name, masks=len(es), **stat(lr(a, ref, es, name)))

    des = [(row, '%s-uniform' % e['size'], e['mask'], r, s) for e in masks for row in rows for r in e['eval'] for s in seeds]
    missing = [k for k in des if k not in R]
    dead = sum(x['dead'] for x in R.values())
    L = ['# v25 Part C: fault sweep (seeds 131-135; generated by report_v25.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d. Uniform traffic, k = 1, 2, 3 faulty VLs in every chiplet, three masks per (size, k), pipe_all 2.' % (len(des) - len(missing), len(des), len(missing), dead),
         'Loads per mask: 0.5, 1.0, 1.4, 2.0 x Lsat of DeFT_P on that mask (`load_points_faults.md`). **THR** = the largest accepted throughput over the four loads; **LAT** and',
         '**P99** at 1.0 x Lsat. **Best reference row** per (mask, metric): the one of DeFT_P, DeFT_B, DeFT_Dis, DeFT_Ran with the best mean over the five seeds. Effect per',
         '(size, k): mean over the three masks of the per-seed log ratio; 95 % interval and t test over the five seeds.', '']
    fam = [test(MAIN, 'best', z, k, n) for z in SIZES for k in (1, 2) for n in ('THR', 'LAT')]
    for x, q in zip(fam, holm([1.0 if isnan(x['p']) else x['p'] for x in fam])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'fault_family.csv'), fam)
    L += ['## C.1 Family (Holm over 12): `CI_heurLA_X_LF` against the best reference row, k = 1 and 2', '', '| size | k | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|']
    for x in fam:
        L.append('| %s | %d | %s | %s | **%s** |' % (x['size'], x['k'], x['metric'], fmt(x, 'p_holm'), x['verdict']))
    cnt = lambda vd: sum(1 for x in fam if x['verdict'] == vd)  # noqa: E731
    L += ['', '**Supported %d of 12; against %d; n.s. %d.**' % (cnt('supported'), cnt('against'), cnt('n.s.')), '']

    sec = []
    for z in SIZES:
        for k in (1, 2, 3):
            for row in rows:
                for n in ('THR', 'LAT', 'P99', 'LAT05'):
                    sec.append(test(row, 'best', z, k, n))
                    for b in refs:
                        if b != row:
                            sec.append(test(row, b, z, k, n))
    write(os.path.join(OUT, 'fault_secondary.csv'), sec)
    fidx = {(x['size'], x['k'], x['row'], x['reference'], x['metric']): x for x in sec}

    def find(z, k, row, ref, n):
        return fidx[(z, k, row, ref if ref != 'best' else 'best reference row', n)]

    L += ['## C.2 Trend over k: both rows against the best reference row (descriptive; effect [95 % CI])', '',
          '| size | k | `CI_heurLA_X_LF` THR | LAT | P99 | LAT at 0.5 x Lsat | `CI_heurLA_O_LF` THR | LAT | P99 | LAT at 0.5 x Lsat |', '|---|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for k in (1, 2, 3):
            L.append('| %s | %d%s | %s |' % (z, k, ' (check only)' if k == 3 else '', ' | '.join(eci(find(z, k, row, 'best', n)) for row in (MAIN, SECOND) for n in ('THR', 'LAT', 'P99', 'LAT05'))))
    L += ['', '## C.3 `CI_heurLA_X_LF` against each reference row (effect [95 % CI])', '', '| size | k | reference | THR | LAT | P99 | best reference row of the masks (THR; LAT) |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for k in (1, 2, 3):
            es = [e for e in masks if e['size'] == z and e['k'] == k]
            bb = '; '.join(', '.join(str(best(e, n)) for e in es) for n in ('THR', 'LAT'))
            for b in refs:
                L.append('| %s | %d | %s | %s | %s |' % (z, k, b, ' | '.join(eci(find(z, k, MAIN, b, n)) for n in ('THR', 'LAT', 'P99')), bb if b == refs[0] else ''))
    # k = 3 check
    L += ['', '## C.4 k = 3 (a check, in no test): `CI_heurLA_X_LF` against DeFT_P per mask', '',
          'With one functional VL per chiplet there is nothing to bind and the main row takes DeFT-P\'s route. Ratios are main row / DeFT_P (mean over the seeds).', '',
          '| size | mask | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.5 x Lsat | run pairs with identical statistics (of 20) | hops with more than one offered output | stored decisions that differ from a fresh one | fallback took another output |',
          '|---|---|---|---|---|---|---|---|---|---|']
    k3 = []
    for e in [e for e in masks if e['k'] == 3]:
        rat = {n: mean(val(MAIN, e, s, n) / val('DeFT_P', e, s, n) for s in seeds if _hasc(val, MAIN, e, s, n) and _hasc(val, 'DeFT_P', e, s, n)) for n in ('THR', 'LAT', 'P99', 'LAT05')}
        same = n_pairs = 0
        t = {k: 0 for k in INTS}
        for i in range(4):
            for s in seeds:
                try:
                    a, b = run(MAIN, e, i, s), run('DeFT_P', e, i, s)
                except KeyError:
                    continue
                n_pairs += 1
                same += (a['accepted'] == b['accepted'] and a['latency'] == b['latency'] and a['p99'] == b['p99'] and a['received'] == b['received'])
                for kk in INTS:
                    t[kk] += a[kk] or 0
        hm = t['hops_chip_multi'] + t['hops_ipos_multi']
        k3.append(dict(size=e['size'], mask=e['mask'], identical_pairs=same, pairs=n_pairs, **{'ratio_' + n: round(v, 5) for n, v in rat.items()}, hops_multi=hm,
                       lookahead_mismatch=t['lookahead_mismatch'], lookahead_used=t['lookahead_used'], fb_taken=t['lookahead_fb_taken']))
        L.append('| %s | %s | %.4f | %.4f | %.4f | %.4f | %d of %d | %d of %d | %d of %d | %d |' % (e['size'], e['mask'], rat['THR'], rat['LAT'], rat['P99'], rat['LAT05'], same, n_pairs,
                                                                                         hm, t['hops_chip'] + t['hops_ipos'], t['lookahead_mismatch'], t['lookahead_used'], t['lookahead_fb_taken']))
    write(os.path.join(OUT, 'fault_k3_check.csv'), k3)
    # delivered share
    L += ['', '## C.5 Delivered share (received / injected packets over a run; packets in flight at the end count as not delivered; mean over masks and seeds)', '',
          '| size | k | row | at 0.5 x Lsat | 1.0 x | 1.4 x | 2.0 x |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for k in (1, 2, 3):
            es = [e for e in masks if e['size'] == z and e['k'] == k]
            for row in rows:
                cells = []
                for i in range(4):
                    v = [run(row, e, i, s)['received'] / float(run(row, e, i, s)['injected']) for e in es for s in seeds if (row, '%s-uniform' % e['size'], e['mask'], e['eval'][i], s) in R and run(row, e, i, s)['injected']]
                    cells.append('%.4f' % mean(v) if v else 'n/a')
                L.append('| %s | %d | %s | %s |' % (z, k, row, ' | '.join(cells)))
    df = os.path.join(RES, 'drain_faults.csv')
    if os.path.exists(df):
        dr = list(csv.DictReader(open(df)))
        L += ['', 'Drain tests (`drain_faults.csv`, all-pairs burst on every mask, every row): %d of %d pass (every packet delivered, no dead-end event).' % (sum(1 for r in dr if r['result'] == 'PASS'), len(dr))]
    L += ['', 'Dead-end events in the %d runs of the sweep: %d.' % (len(R), dead), '']
    # absolute values and paper data
    pdr = []
    L += ['## C.6 Absolute values (mean over the three masks and five seeds): THR in flits/node/cycle; LAT, P99 in cycles at 1.0 x Lsat', '',
          '| size | k | ' + ' | '.join(rows) + ' |', '|---|---|' + '---|' * len(rows)]
    for z in SIZES:
        for k in (1, 2, 3):
            es = [e for e in masks if e['size'] == z and e['k'] == k]
            cells = []
            for row in rows:
                rec = dict(size=z, k=k, row=row)
                for n in ('THR', 'LAT', 'P99', 'LAT05'):
                    per_seed = [mean(val(row, e, s, n) for e in es) for s in seeds if all(_hasc(val, row, e, s, n) for e in es)]
                    m, lo, hi = mci(per_seed)
                    rec[n], rec[n + '_ci_low'], rec[n + '_ci_high'] = round(m, 5), round(lo, 5) if not isnan(lo) else '', round(hi, 5) if not isnan(hi) else ''
                    x = find(z, k, row, 'best', n)
                    rec[n + '_effect_vs_best_pct'], rec[n + '_effect_ci_low'], rec[n + '_effect_ci_high'] = x['effect_pct'], x['ci_low'], x['ci_high']
                pdr.append(rec)
                cells.append('%.4f / %.0f / %.0f' % (rec['THR'], rec['LAT'], rec['P99']))
            L.append('| %s | %d | %s |' % (z, k, ' | '.join(cells)))
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'fault_sweep.csv'), pdr)
    L.append('')
    wmd('summary_C.md', L)
    return L


def _hasc(val, row, e, s, n):
    try:
        val(row, e, s, n)
        return True
    except KeyError:
        return False


# =====================================================================================================================
# Part D
# =====================================================================================================================
def gmean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else NAN


def part_d():
    rows = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', MAIN, SECOND]
    L = ['# v25 Part D: application traces on 2x2 (descriptive; seeds 41-43; pipe_all 2; generated by report_v25.py)', '']
    out = []
    fa = os.path.join(RES, 'app_runs.csv')
    if os.path.exists(fa):
        A = list(csv.DictReader(open(fa)))
        K = {(r['benchmark'], r['method'], r['mask'], int(r['seed'])): r for r in A}
        bench = []
        for r in A:
            if r['benchmark'] not in bench:
                bench.append(r['benchmark'])
        bad = [r for r in A if r['finished'] != 'True' or r['injected'] != r['delivered']]
        L += ['## D.1 One application (the v13 protocol: nine PARSEC traces, the first 700,000 cycles of region 2)', '',
              'Runs: %d; runs that did not deliver their whole window: %d. Values are relative to DeFT_P of the same trace, mask and seed (geometric mean over the seeds).' % (len(A), len(bad)), '']
        if bad:
            L += ['Excluded (window not delivered): ' + '; '.join('%s %s %s seed %s' % (r['benchmark'], r['method'], r['mask'], r['seed']) for r in bad) + '.', '']
            for r in bad:
                K.pop((r['benchmark'], r['method'], r['mask'], int(r['seed'])), None)
        for mask in ('0x0000', '0x1111'):
            rs = [r for r in rows if not (r in ('MTR', 'RC') and mask != '0x0000')]
            L += ['### %s' % ('fault-free' if mask == '0x0000' else 'one faulty VL per chiplet (0x1111)'), '',
                  '| trace | offered load (flits/node/cycle) | DeFT_P latency (cycles) | mean latency relative to DeFT_P: ' + ' | '.join(rs[1:]) + ' | completion time relative to DeFT_P: ' + ' | '.join(rs[1:]) + ' |',
                  '|---|---|---|' + '---|' * (2 * (len(rs) - 1))]
            gl, gc = {r: [] for r in rs}, {r: [] for r in rs}
            for b in bench:
                base = [K[(b, 'DeFT_P', mask, s)] for s in (41, 42, 43) if (b, 'DeFT_P', mask, s) in K]
                if not base:
                    continue
                lat, comp = {}, {}
                for r in rs:
                    v = [(float(K[(b, r, mask, s)]['latency']) / float(K[(b, 'DeFT_P', mask, s)]['latency']), float(K[(b, r, mask, s)]['completion_cycles']) / float(K[(b, 'DeFT_P', mask, s)]['completion_cycles']))
                         for s in (41, 42, 43) if (b, r, mask, s) in K and (b, 'DeFT_P', mask, s) in K]
                    lat[r], comp[r] = gmean(x[0] for x in v), gmean(x[1] for x in v)
                    gl[r].append(lat[r])
                    gc[r].append(comp[r])
                    out.append(dict(protocol='single', workload=b, mask=mask, s='', row=r, latency_rel_DeFT_P=round(lat[r], 5), completion_rel_DeFT_P=round(comp[r], 5),
                                    latency_cycles=round(mean(float(K[(b, r, mask, s)]['latency']) for s in (41, 42, 43) if (b, r, mask, s) in K), 3),
                                    offered_flits_per_node_cycle=round(mean(float(x['offered_flits_per_node_cycle']) for x in base), 6)))
                L.append('| %s | %.4f | %.1f | %s | %s |' % (b.split('_')[0], mean(float(x['offered_flits_per_node_cycle']) for x in base), mean(float(x['latency']) for x in base),
                                                       ' | '.join('%.3f' % lat[r] for r in rs[1:]), ' | '.join('%.4f' % comp[r] for r in rs[1:])))
            L += ['| **geometric mean** | | | %s | %s |' % (' | '.join('%.3f' % gmean(gl[r]) for r in rs[1:]), ' | '.join('%.4f' % gmean(gc[r]) for r in rs[1:])), '']
            for r in rs:
                out.append(dict(protocol='single', workload='geometric mean', mask=mask, s='', row=r, latency_rel_DeFT_P=round(gmean(gl[r]), 5), completion_rel_DeFT_P=round(gmean(gc[r]), 5)))
    fp = os.path.join(RES, 'pair_runs.csv')
    if os.path.exists(fp):
        A = list(csv.DictReader(open(fp)))
        K = {(r['pair'], r['method'], r['mask'], int(r['s']), int(r['seed'])): r for r in A}
        pairs = []
        for r in A:
            if r['pair'] not in pairs:
                pairs.append(r['pair'])
        bad = [r for r in A if r['finished'] != 'True' or r['injected'] != r['delivered']]
        L += ['## D.2 Two applications at once (the v15 protocol: the six pairs of the four heaviest traces, compression 1 and 2)', '',
              'Runs: %d; runs that did not deliver both windows: %d. Values relative to DeFT_P of the same pair, mask, compression and seed.' % (len(A), len(bad)), '']
        if bad:
            L += ['Excluded (windows not delivered): ' + '; '.join('%s %s %s compression %s seed %s' % (r['pair'], r['method'], r['mask'], r['s'], r['seed']) for r in bad) + '.', '']
            for r in bad:
                K.pop((r['pair'], r['method'], r['mask'], int(r['s']), int(r['seed'])), None)
        for mask in ('0x0000', '0x1111'):
            rs = [r for r in rows if not (r in ('MTR', 'RC') and mask != '0x0000')]
            for sv in (1, 2):
                L += ['### %s, compression %d' % ('fault-free' if mask == '0x0000' else 'one faulty VL per chiplet (0x1111)', sv), '',
                      '| pair | offered load (flits/node/cycle) | DeFT_P latency (cycles) | mean latency relative to DeFT_P: ' + ' | '.join(rs[1:]) + ' | completion time relative to DeFT_P: ' + ' | '.join(rs[1:]) + ' |',
                      '|---|---|---|' + '---|' * (2 * (len(rs) - 1))]
                gl, gc = {r: [] for r in rs}, {r: [] for r in rs}
                for p in pairs:
                    base = [K[(p, 'DeFT_P', mask, sv, s)] for s in (41, 42, 43) if (p, 'DeFT_P', mask, sv, s) in K]
                    if not base:
                        continue
                    lat, comp = {}, {}
                    for r in rs:
                        v = [(float(K[(p, r, mask, sv, s)]['latency']) / float(K[(p, 'DeFT_P', mask, sv, s)]['latency']),
                              float(K[(p, r, mask, sv, s)]['completion_cycles']) / float(K[(p, 'DeFT_P', mask, sv, s)]['completion_cycles']))
                             for s in (41, 42, 43) if (p, r, mask, sv, s) in K and (p, 'DeFT_P', mask, sv, s) in K]
                        lat[r], comp[r] = gmean(x[0] for x in v), gmean(x[1] for x in v)
                        gl[r].append(lat[r])
                        gc[r].append(comp[r])
                        out.append(dict(protocol='pair', workload=p, mask=mask, s=sv, row=r, latency_rel_DeFT_P=round(lat[r], 5), completion_rel_DeFT_P=round(comp[r], 5),
                                        latency_cycles=round(mean(float(K[(p, r, mask, sv, s)]['latency']) for s in (41, 42, 43) if (p, r, mask, sv, s) in K), 3),
                                        offered_flits_per_node_cycle=round(mean(float(x['offered_flits_per_node_cycle']) for x in base), 6)))
                    L.append('| %s | %.4f | %.1f | %s | %s |' % (p, mean(float(x['offered_flits_per_node_cycle']) for x in base), mean(float(x['latency']) for x in base),
                                                           ' | '.join('%.3f' % lat[r] for r in rs[1:]), ' | '.join('%.4f' % comp[r] for r in rs[1:])))
                L += ['| **geometric mean** | | | %s | %s |' % (' | '.join('%.3f' % gmean(gl[r]) for r in rs[1:]), ' | '.join('%.4f' % gmean(gc[r]) for r in rs[1:])), '']
                for r in rs:
                    out.append(dict(protocol='pair', workload='geometric mean', mask=mask, s=sv, row=r, latency_rel_DeFT_P=round(gmean(gl[r]), 5), completion_rel_DeFT_P=round(gmean(gc[r]), 5)))
    write(os.path.join(OUT, 'apps.csv'), out)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'apps.csv'), out)
    wmd('summary_D.md', L)
    return L


# =====================================================================================================================
# Part E
# =====================================================================================================================
def scen_e(z):
    f, n = FREE[z], NORTH[z]
    return [('uniform', f), ('hotspot', f), ('chipperm', f), ('uniform', n)]


def part_e():
    P = json.load(open(os.path.join(RES, 'load_points_v25.json')))
    seeds = list(range(141, 146))
    rows = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'CI_heurLA_X', DLY]

    def row_scen(row, z):
        return [x for x in scen_e(z) if not (row in ('MTR', 'RC') and faulty(x[1]))]

    def refs_of(z, sc):
        return ['DeFT_P', 'DeFT_B'] + ([] if faulty(sc[1]) else ['MTR', 'RC'])

    D = Design(load_runs(os.path.join(RES, 'pipe0_runs.csv')), P, 0, seeds, scen_e, row_scen, refs_of, IDX9)
    des = D.design(rows)
    missing = [k for k in des if k not in D.R]
    dead = sum(x['dead'] for x in D.R.values())
    L = ['# v25 Part E: the one-cycle router model, pipe_all 0 (descriptive; seeds 141-145; generated by report_v25.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d. Scenarios: uniform, hotspot, chipperm fault-free and uniform+f; the nine loads of the pipe_all 0 ladders' % (len(des) - len(missing), len(des), len(missing), dead),
         '(0.2-2.4 x Lsat of DeFT-P at pipe_all 0). Best baseline per (size, scenario, metric): the best of DeFT_P, DeFT_B, MTR, RC (with faults: DeFT_P, DeFT_B).',
         '`CI_heurLA_X` = the main row\'s selection with an ideal decision (no delay, no lookahead routing); `CI_heurLA_X_DLY` = decision_delay 2. No test.', '']
    rec = []
    for z in SIZES:
        for row in rows:
            scs = row_scen(row, z)
            for n in METRICS + ['LAT02', 'LAT05']:
                rec.append(D.test(row, 'best', z, scs, n))
                rec += [D.test(row, 'best', z, [sc], n) for sc in scs]
                if row != 'DeFT_P':
                    rec.append(D.test(row, 'DeFT_P', z, scs, n))
        rec += [D.test(DLY, 'CI_heurLA_X', z, scen_e(z), n) for n in METRICS + ['LAT02', 'LAT05']]
    write(os.path.join(OUT, 'pipe0.csv'), rec)
    idx = {(x['size'], x['row'], x['reference'], x['metric'], x['scenarios']): x for x in rec}

    def find(z, row, ref, n, scs):
        return idx[(z, row, ref if ref != 'best' else 'best baseline', n, '+'.join(sname(sc) for sc in scs))]

    L += ['## E.1 Per size against the best baseline (effect [95 % CI])', '', '| size | row | scenarios | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat (against DeFT_P) |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in rows:
            scs = row_scen(row, z)
            L.append('| %s | %s | %s | %s | %s | %s | %s |' % (z, row, 'all four' if len(scs) == 4 else 'three fault-free', eci(find(z, row, 'best', 'THR', scs)), eci(find(z, row, 'best', 'LAT', scs)),
                                                           eci(find(z, row, 'best', 'P99', scs)), eci(find(z, row, 'DeFT_P', 'LAT02', scs)) if row != 'DeFT_P' else '0'))
    L += ['', '## E.2 Per scenario: `CI_heurLA_X` (ideal) and `CI_heurLA_X_DLY` against the best baseline (2x2 / 3x3 / 4x4)', '',
          '| scenario | best baseline THR; LAT | ideal THR | LAT | P99 | DLY THR | LAT | P99 |', '|---|---|---|---|---|---|---|---|']
    for k in range(4):
        bb = '; '.join(', '.join(str(D.best(z, scen_e(z)[k], n)) for z in SIZES) for n in ('THR', 'LAT'))
        cells = [' / '.join(eci(find(z, row, 'best', n, [scen_e(z)[k]])) for z in SIZES) for row in ('CI_heurLA_X', DLY) for n in METRICS]
        L.append('| %s | %s | %s |' % (sname(scen_e('2x2')[k]), bb, ' | '.join(cells)))
    L += ['', '## E.3 `CI_heurLA_X_DLY` against the ideal decision at pipe_all 0 (effect [95 % CI])', '', '| size | THR | LAT at 0.2 x Lsat | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|']
    for z in SIZES:
        L.append('| %s | %s |' % (z, ' | '.join(eci(find(z, DLY, 'CI_heurLA_X', n, scen_e(z))) for n in ('THR', 'LAT02', 'LAT', 'P99'))))
    # the same four scenarios at pipe_all 2 (Part B), when available
    fb = os.path.join(RES, 'eval_runs.csv')
    if os.path.exists(fb):
        seeds_b = list(range(121, 131))
        dfile = os.path.join(RES, 'drops.json')
        dropped = json.load(open(dfile))['dropped'] if os.path.exists(dfile) else []

        def refs_b(z, sc):
            return ['DeFT_P', 'DeFT_B'] + ([] if faulty(sc[1]) else ['MTR', 'RC'])
        DB = Design(load_runs(fb), P, 2, seeds_b, scen_e, lambda row, z: scen_e(z), refs_b, IDX9)
        L += ['', '## E.4 The same four scenarios and the same four reference rows at pipe_all 2 (Part B runs, seeds 121-130), for comparison', '',
              '| size | row | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|']
        for z in SIZES:
            for row in (MAIN, DLY):
                L.append('| %s | %s | %s |' % (z, row, ' | '.join(eci(DB.test(row, 'best', z, scen_e(z), n)) for n in METRICS)))
    L.append('')
    wmd('summary_E.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'pipe0_effects.csv'), [x for x in rec if x['reference'] == 'best baseline'])
    return L


# =====================================================================================================================
# Addendum: the main row with one residual cycle
# =====================================================================================================================
ADD = 'CI_heurLA_X_LF1'


def part_a():
    """PREREGISTRATION_addendum.md: CI_heurLA_X_LF1 on the Part B design; nine tests with their own Holm correction; the cost of the residual cycle."""
    P = json.load(open(os.path.join(RES, 'load_points_v25.json')))
    dfile = os.path.join(RES, 'drops.json')
    dropped = json.load(open(dfile))['dropped'] if os.path.exists(dfile) else []
    seeds = list(range(121, 131))
    ref_ff = [r for r in REF_FF if not (r == 'XY_SP' and 'xy_sp' in dropped)]

    def row_scen(row, z):
        sc = scen_b(z)
        if row in REF_FF:
            return [x for x in sc if not faulty(x[1])] if row in ref_ff else []
        if row in REF_FAULT:
            return [x for x in sc if faulty(x[1])]
        return sc

    def refs_of(z, sc):
        return REF_ALL + (REF_FAULT if faulty(sc[1]) else ref_ff)

    R = load_runs(os.path.join(RES, 'eval_runs.csv'))
    RA = load_runs(os.path.join(RES, 'addendum_runs.csv'))
    assert not (set(R) & set(RA))
    R.update(RA)
    D = Design(R, P, 2, seeds, scen_b, row_scen, refs_of, IDX9)
    des = D.design([ADD])
    missing = [k for k in des if k not in D.R]
    dead = sum(x['dead'] for x in RA.values())
    names = METRICS + ['LAT02', 'LAT05']
    L = ['# v25 addendum: the main row with one residual cycle, `CI_heurLA_X_LF1` (seeds 121-130; generated by report_v25.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d. The row is `CI_heurLA_X_LF` with `decision_delay 1` (`PREREGISTRATION_addendum.md`): what the RTL of Part F' % (
             len(des) - len(missing), len(des), len(missing), dead),
         'does when its decision takes three cycles (a link wire that leaves no time in the link cycle, or a 1 ns clock). The Part B design; the reference rows and the',
         'best baseline are those of Part B. Effects as in Part B.', '']
    da = os.path.join(RES, 'drain_summary_addendum.csv')
    if os.path.exists(da):
        dr = list(csv.DictReader(open(da)))
        L += ['Drain tests of the row (`drain_summary_addendum.csv`, the A4 protocol): %d of %d pass.' % (sum(1 for r in dr if r['result'] == 'PASS'), len(dr)), '']
    fam = [D.test(ADD, 'best', z, scen_b(z), n) for z in SIZES for n in METRICS]
    for x, q in zip(fam, holm([1.0 if isnan(x['p']) else x['p'] for x in fam])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    rec = list(fam)
    L += ['## A.1 Family of the addendum (Holm over 9): `CI_heurLA_X_LF1` against the best baseline, eight scenarios', '',
          '| size | metric | effect [95 % CI] (p Holm) | verdict | the main row, `CI_heurLA_X_LF` (Part B, for comparison) |', '|---|---|---|---|---|']
    for x in fam:
        L.append('| %s | %s | %s | **%s** | %s |' % (x['size'], x['metric'], fmt(x, 'p_holm'), x['verdict'], eci(D.test(MAIN, 'best', x['size'], scen_b(x['size']), x['metric']))))
    cnt = lambda vd: sum(1 for x in fam if x['verdict'] == vd)  # noqa: E731
    L += ['', '**Supported %d of 9; against %d; n.s. %d.**' % (cnt('supported'), cnt('against'), cnt('n.s.')), '']
    L += ['## A.2 What the residual cycle costs: `CI_heurLA_X_LF1` against `CI_heurLA_X_LF` and against `CI_heurLA_X_DLY` (effect [95 % CI]; eight scenarios)', '',
          '| size | against | THR | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for b in (MAIN, DLY):
            t = {n: D.test(ADD, b, z, scen_b(z), n) for n in names}
            rec += list(t.values())
            L.append('| %s | %s | %s |' % (z, b, ' | '.join(eci(t[n]) for n in ('THR', 'LAT02', 'LAT05', 'LAT', 'P99'))))
    L += ['', 'In cycles (mean over the scenarios of the difference of the seed means): ' + '; '.join(
        '%s LAT at 0.2 x Lsat %+.2f, at 1.0 x Lsat %+.2f' % (z, mean(D.smean(ADD, z, sc, 'LAT02') - D.smean(MAIN, z, sc, 'LAT02') for sc in scen_b(z)),
                                                              mean(D.smean(ADD, z, sc, 'LAT') - D.smean(MAIN, z, sc, 'LAT') for sc in scen_b(z))) for z in SIZES) + '.', '']
    L += ['## A.3 Per scenario against the best baseline and against the main row (effect [95 % CI]; 2x2 / 3x3 / 4x4)', '',
          '| scenario | THR against the best baseline | LAT | P99 | THR against the main row | LAT | P99 |', '|---|---|---|---|---|---|---|']
    for k in range(8):
        cells = []
        for b in ('best', MAIN):
            for n in METRICS:
                ts = [D.test(ADD, b, z, [scen_b(z)[k]], n) for z in SIZES]
                rec += ts
                cells.append(' / '.join(eci(t) for t in ts))
        L.append('| %s | %s |' % (sname(scen_b('2x2')[k]), ' | '.join(cells)))
    L += ['', '## A.4 Low-load latency against DeFT_P (effect [95 % CI]; eight scenarios)', '', '| size | row | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat |', '|---|---|---|---|']
    for z in SIZES:
        for row in (ADD, MAIN, DLY):
            t = [D.test(row, 'DeFT_P', z, scen_b(z), n) for n in ('LAT02', 'LAT05')]
            rec += t if row == ADD else []
            L.append('| %s | %s | %s | %s |' % (z, row, eci(t[0]), eci(t[1])))
    L += ['', '## A.5 Lookahead counters at 1.0 x Lsat (summed over the scenarios and seeds)', '',
          '| size | row | decision hops per packet | fallback: left through another output (of decision hops) | fallback: stored output not free (of checks) |', '|---|---|---|---|---|']
    for z in SIZES:
        for row in (ADD, MAIN):
            t = D.hopstats(row, z, (3,))
            if t:
                hm = t['hops_chip_multi'] + t['hops_ipos_multi']
                L.append('| %s | %s | %.2f | %s | %s |' % (z, row, hm / float(t['packets_measured']) if t['packets_measured'] else NAN,
                                                         pc(t['lookahead_fb_taken'], t['lookahead_multi']) if t['lookahead_multi'] else '-',
                                                         pc(t['lookahead_fb_blocked'], t['lookahead_fb_checks']) if t['lookahead_fb_checks'] else '-'))
    L.append('')
    write(os.path.join(OUT, 'addendum.csv'), rec)
    wmd('summary_A.md', L)
    os.makedirs(PD, exist_ok=True)
    write(os.path.join(PD, 'addendum_effects.csv'), rec)
    return L


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = [a for a in sys.argv[1:] if a in ('b', 'a', 'c', 'd', 'e')]
    have = {'b': 'eval_runs.csv', 'a': 'addendum_runs.csv', 'c': 'fault_runs.csv', 'd': 'app_runs.csv', 'e': 'pipe0_runs.csv'}
    fn = {'b': part_b, 'a': part_a, 'c': part_c, 'd': part_d, 'e': part_e}
    for p in parts or 'bacde':
        if os.path.exists(os.path.join(RES, have[p])):
            L = fn[p]()
            print(NL.join(L[:60]))
        else:
            print('part %s: %s not there yet' % (p, have[p]))
    S = []
    for name in ('summary_B.md', 'summary_A.md', 'summary_C.md', 'summary_D.md', 'summary_E.md', 'summary_F.md'):
        f = os.path.join(OUT, name)
        if os.path.exists(f):
            S += [open(f, encoding='utf-8').read().rstrip(), '', '---', '']
    if S:
        open(os.path.join(OUT, 'summary.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(S[:-2]) + NL)


if __name__ == '__main__':
    main()
