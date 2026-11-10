"""v24 report, following results_v24_xy/PREREGISTRATION.md.

Usage: python3 report_v24.py
eval_runs.csv, load_points_v24.json (and drops.json) -> report/primary.csv, secondary.csv, mechanism.csv, saturation.csv, hops.csv, summary.md,
latency_load_4x4.{png,pdf}, accepted_load_4x4.{png,pdf} and their table twin curves_4x4.csv.

Effects are 100 x (exp(mean over seeds of R_s) - 1) %, R_s = mean over the scenarios of ln(metric_row / metric_reference) for seed s; 95 % interval and
two-sided one-sample t test over the seeds. THR = the largest accepted throughput over the 9 loads; LAT and P99 at the 4th load (1.0 x Lsat of DeFT-P).
Best baseline per (size, scenario, metric): the one of DeFT_P, DeFT_B, MTR, RC (with faults: DeFT_P, DeFT_B) with the best mean over the seeds.
"""
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import scipy.stats as st  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v24_xy')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
SEEDS = list(range(111, 116))
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
NORTH = {'2x2': '0x1111', '3x3': '0x111111111', '4x4': '0x1111111111111111'}
BASE = ['DeFT_P', 'DeFT_B', 'MTR', 'RC']
CANDS = ['CI_heurLA_X', 'CI_qlLA_X', 'CI_heurLA_O', 'CI_qlLA_O']
MECHS = ['ideal', 'LF', 'DLY']
SECONDARY = ['FULL_qlLA_X', 'CI_qlLA_G', 'FULL_qlLA_G', 'DeFT_P_O1', 'CI_rand_X', 'CI_heur_X']
CONTROLS = ['CI_qlLA_X_Lnofb', 'CI_qlLA_X_LF0']
PRIMARY = ['CI_qlLA_X_LF', 'CI_qlLA_O_LF']
METRICS = ['THR', 'LAT', 'P99']
IDX = {'LAT': (3, 'latency'), 'P99': (3, 'p99'), 'LAT02': (0, 'latency'), 'LAT05': (1, 'latency'), 'LAT14': (5, 'latency')}
INTS = ('hops_chip', 'hops_chip_multi', 'hops_ipos', 'hops_ipos_multi', 'lookahead_used', 'lookahead_mismatch', 'lookahead_multi', 'lookahead_fb_checks',
        'lookahead_fb_blocked', 'lookahead_fb_requests', 'lookahead_fb_taken', 'packets_measured', 'vl_max_down', 'vl_max_up')
NL = chr(10)
NAN = float('nan')
P, R, DROPPED = {}, {}, []


def mrow(c, k):
    return c if k == 'ideal' else '%s_%s' % (c, k)


ROWS = BASE + [mrow(c, k) for c in CANDS for k in MECHS] + SECONDARY + CONTROLS


def scen(z):
    return [('uniform', FREE[z]), ('hotspot', FREE[z]), ('chipperm', FREE[z]), ('chiptrans', FREE[z]), ('uniform', NORTH[z])]


def sname(sc):
    return sc[0] if int(sc[1], 16) == 0 else 'faulty'


def row_scen(row, z):
    """The scenarios a row was run on."""
    sc = scen(z)
    if row in ('MTR', 'RC'):
        return [x for x in sc if int(x[1], 16) == 0]
    if row in CONTROLS:
        return [sc[0]]
    if 'dly_heur' in DROPPED and row in ('CI_heurLA_X_DLY', 'CI_heurLA_O_DLY'):
        return []
    if 'rand_heur' in DROPPED and row in ('CI_rand_X', 'CI_heur_X'):
        return [x for x in sc if x[0] == 'uniform']
    return sc


def lad(z, sc):
    return P['%s__%s__%s__p2' % (z, sc[0], sc[1])]['eval']


def run(row, z, sc, i, s):
    return R[(row, '%s-%s' % (z, sc[0]), sc[1], lad(z, sc)[i], s)]


def val(row, z, sc, s, name):
    if name == 'THR':
        return max(run(row, z, sc, i, s)['accepted'] for i in range(9))
    i, f = IDX[name]
    return run(row, z, sc, i, s)[f]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else NAN


def smean(row, z, sc, name):
    """Mean over the seeds (seeds with a missing run are skipped)."""
    v = []
    for s in SEEDS:
        try:
            v.append(val(row, z, sc, s, name))
        except KeyError:
            pass
    return mean(v)


_best = {}


def best(z, sc, name):
    """The best baseline of a (size, scenario, metric): highest mean THR, lowest mean LAT / P99."""
    k = (z, sc, name)
    if k not in _best:
        cands = BASE if int(sc[1], 16) == 0 else BASE[:2]
        m = {b: smean(b, z, sc, name) for b in cands}
        m = {b: v for b, v in m.items() if v == v}
        _best[k] = (max if name == 'THR' else min)(m, key=m.get) if m else None
    return _best[k]


def lr(a, ref, z, scs, name, ref_name=None):
    """Per-seed mean over scenarios of ln(metric_a / metric_ref). ref: a row name, or 'best' (the best baseline of each scenario for ref_name or name)."""
    out = []
    for s in SEEDS:
        try:
            rs = [math.log(val(a, z, sc, s, name) / val(best(z, sc, ref_name or name) if ref == 'best' else ref, z, sc, s, name)) for sc in scs]
        except (KeyError, ValueError, ZeroDivisionError):
            continue
        if rs:
            out.append(sum(rs) / len(rs))
    return out


def stat(xs):
    n = len(xs)
    if n < 2:
        return dict(n_seeds=n, effect_pct=NAN, ci_low=NAN, ci_high=NAN, p=NAN)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    p = (0.0 if m != 0 else 1.0) if sd == 0 else 2 * st.t.sf(abs(m / (sd / math.sqrt(n))), n - 1)
    return dict(n_seeds=n, effect_pct=round(100 * (math.exp(m) - 1), 2), ci_low=round(100 * (math.exp(m - h) - 1), 2), ci_high=round(100 * (math.exp(m + h) - 1), 2), p=p)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, runv = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        runv = max(runv, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = runv
    return adj


def isnan(x):
    return x != x


def verdict(x, key='p_holm'):
    if isnan(x[key]) or x[key] >= 0.05:
        return 'n.s.'
    good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
    return 'supported' if good else 'against'


def fmt(x, key='p'):
    if isnan(x['effect_pct']):
        return 'n/a'
    return '%+.1f [%+.1f, %+.1f] (%s %.2g)' % (x['effect_pct'], x['ci_low'], x['ci_high'], key.replace('_', ' '), x[key])


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


def test(a, ref, z, scs, name, **kw):
    refn = ref if ref != 'best' else 'best baseline'
    return dict(size=z, row=a, reference=refn, metric=name, scenarios='+'.join(sname(sc) for sc in scs), **stat(lr(a, ref, z, scs, name, **kw)))


def load():
    global P, R, DROPPED
    P = json.load(open(os.path.join(RES, 'load_points_v24.json')))
    d = os.path.join(RES, 'drops.json')
    DROPPED = json.load(open(d))['dropped'] if os.path.exists(d) else []
    R = {}
    for r in csv.DictReader(open(os.path.join(RES, 'eval_runs.csv'))):
        x = dict(accepted=float(r['accepted']), latency=float(r['latency']), p99=float(r['p99']), dead=int(r['dead_ends']), offered=float(r['offered']))
        for k in INTS:
            x[k] = int(r[k]) if r.get(k) not in (None, '') else None
        R[(r['variant'][:-3], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = x


def design():
    return [(row, '%s-%s' % (z, sc[0]), sc[1], rate, s) for z in SIZES for row in ROWS for sc in row_scen(row, z) for rate in lad(z, sc) for s in SEEDS]


# ---- saturation and behaviour beyond it ----
def saturation(row, z):
    out = []
    for sc in row_scen(row, z):
        ld = lad(z, sc)
        means, ok = [], []
        for i in range(9):
            acc = [run(row, z, sc, i, s)['accepted'] for s in SEEDS if (row, '%s-%s' % (z, sc[0]), sc[1], ld[i], s) in R]
            means.append(mean(acc))
            ok.append(bool(acc) and mean(acc) >= 0.95 * 8 * ld[i])
        valid = [i for i in range(9) if not isnan(means[i])]
        if not valid:
            continue
        arg = max(valid, key=lambda i: means[i])
        peak = means[arg]
        own = max((MULTS[i] for i in range(9) if ok[i] and all(ok[:i + 1])), default=0.0)
        out.append(dict(size=z, row=row, scenario=sname(sc), flagged_at_1_0=not ok[3], own_sat_load=own, thr_max_at=MULTS[arg], thr_at_top=arg == 8,
                        acc_2_0_over_peak=round(means[7] / peak, 4), acc_2_4_over_peak=round(means[8] / peak, 4),
                        monotone=all(means[i + 1] >= means[i] * 0.99 for i in range(8)), peak=round(peak, 5)))
    return out


def hopstats(row, z, idxs=(3,)):
    """Sums of the hop and lookahead counters of a row on a size, at the given load indices, over its scenarios and the seeds."""
    t = {k: 0 for k in INTS}
    n = 0
    for sc in row_scen(row, z):
        for i in idxs:
            for s in SEEDS:
                try:
                    x = run(row, z, sc, i, s)
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


# ---- the report ----
def main():
    load()
    os.makedirs(OUT, exist_ok=True)
    des = design()
    missing = [k for k in des if k not in R]
    dead = sum(x['dead'] for x in R.values())
    L = ['# v24 summary: late binding without path adaptivity (seeds 111-115; generated by report_v24.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d.%s' % (len(des) - len(missing), len(des), len(missing), dead,
                                                                   (' Dropped by the 30 h rule: %s.' % ', '.join(DROPPED)) if DROPPED else ''),
         'pipe_all 2; every VN-based method with DeFT-P\'s VN options and `-traffic_rng 1`; MTR and RC with `-vc_per_hop 1` (fault-free scenarios only). Loads: the 9-load',
         'pipe_all 2 ladders of `load_points_v24.json` (0.2-2.4 x Lsat of DeFT-P). **THR** = the largest accepted throughput over the 9 loads; **LAT** and **P99** at the',
         '4th load (1.0 x Lsat of DeFT-P). Effects are percentages (THR positive = higher, LAT and P99 negative = lower) with the 95 % interval over the five seeds.',
         '**Best baseline** per (size, scenario, metric): the one of DeFT_P, DeFT_B, MTR, RC (with faults: DeFT_P, DeFT_B) with the best mean over the seeds; its per-seed',
         'values are the reference. Scenario names: uniform, hotspot, chipperm, chiptrans (fault-free) and faulty (uniform with one faulty VL per chiplet).',
         'Mechanisms of a candidate: no suffix = ideal (decision_delay 0, no lookahead); `_LF` = lookahead with the fallback and the busy state at its residual delay',
         '(0 heuristic, 1 Q-learning); `_DLY` = no lookahead, decision_delay N_fast (2 heuristic, 3 Q-learning). Only the primary table is adjusted (Holm); every other',
         'p value is unadjusted and descriptive.', '']

    # primary
    prim = [test(a, 'best', z, scen(z), n) for z in SIZES for a in PRIMARY for n in METRICS]
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'primary.csv'), prim)
    L += ['## Primary family (Holm over 18): CI_qlLA_X and CI_qlLA_O in mechanism LF against the best baseline, five scenarios', '',
          '| size | row | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|']
    for x in prim:
        L.append('| %s | %s | %s | %s | **%s** |' % (x['size'], x['row'], x['metric'], fmt(x, 'p_holm'), x['verdict']))
    cnt = lambda vd: sum(1 for x in prim if x['verdict'] == vd)  # noqa: E731
    L += ['', 'Supported %d of 18; against %d; n.s. %d.' % (cnt('supported'), cnt('against'), cnt('n.s.')), '']

    # secondary: every row against the best baseline and against each baseline, over its scenarios and per scenario
    sec, sat = [], []
    for z in SIZES:
        for row in ROWS:
            scs = row_scen(row, z)
            if not scs:
                continue
            sat += saturation(row, z)
            for n in METRICS:
                sec.append(test(row, 'best', z, scs, n))
                sec += [test(row, 'best', z, [sc], n) for sc in scs]
                for b in BASE:
                    if b == row:
                        continue
                    bs = [sc for sc in scs if sc in row_scen(b, z)]
                    if bs:
                        sec.append(test(row, b, z, bs, n))
                        sec += [test(row, b, z, [sc], n) for sc in bs]
            for n in ('LAT02', 'LAT05'):
                sec.append(test(row, 'DeFT_P', z, scs, n))
                sec += [test(row, 'DeFT_P', z, [sc], n) for sc in scs]
    write(os.path.join(OUT, 'secondary.csv'), sec)
    write(os.path.join(OUT, 'saturation.csv'), sat)

    def find(**kw):
        return next(x for x in sec if all(x[k] == v for k, v in kw.items()))

    def allscen(row, z):
        return '+'.join(sname(sc) for sc in row_scen(row, z))

    for z in SIZES:
        L += ['## %s: every row against the best baseline (over the row\'s scenarios)' % z, '',
              '| row | scenarios | THR | LAT @1.0 Lsat | P99 @1.0 Lsat | THR maximum at the top load | saturated at 1.0 x Lsat in |', '|---|---|---|---|---|---|---|']
        for row in ROWS:
            scs = row_scen(row, z)
            if not scs:
                continue
            sv = [x for x in sat if x['size'] == z and x['row'] == row]
            top = '%d of %d' % (sum(1 for x in sv if x['thr_at_top']), len(sv))
            fl = ['%s (own sat. %s x)' % (x['scenario'], x['own_sat_load']) for x in sv if x['flagged_at_1_0']]
            L.append('| %s | %s | %s | %s | %s | %s | %s |' % (row, 'all five' if len(scs) == 5 else allscen(row, z), fmt(find(size=z, row=row, reference='best baseline', metric='THR', scenarios=allscen(row, z))),
                                                              fmt(find(size=z, row=row, reference='best baseline', metric='LAT', scenarios=allscen(row, z))),
                                                              fmt(find(size=z, row=row, reference='best baseline', metric='P99', scenarios=allscen(row, z))), top, '; '.join(fl) if fl else '-'))
        L.append('')

    # per scenario
    L += ['## Per scenario: effect against the best baseline (%, unadjusted; the best baseline and its mean are in the header)', '']
    for z in SIZES:
        for n in METRICS:
            head = []
            for sc in scen(z):
                b = best(z, sc, n)
                v = smean(b, z, sc, n)
                head.append('%s (%s %s)' % (sname(sc), b, ('%.4f' % v) if n == 'THR' else ('%.0f' % v)))
            L += ['**%s, %s**' % (z, n), '', '| row | ' + ' | '.join(head) + ' |', '|---|' + '---|' * 5]
            for row in ROWS:
                if not row_scen(row, z):
                    continue
                cells = []
                for sc in scen(z):
                    cells.append(short(find(size=z, row=row, reference='best baseline', metric=n, scenarios=sname(sc))) if sc in row_scen(row, z) else '-')
                L.append('| %s | %s |' % (row, ' | '.join(cells)))
            L.append('')

    # the two primary rows per scenario, with intervals
    L += ['## The primary rows per scenario: CI_qlLA_X and CI_qlLA_O with LF against the best baseline (%, 95 % CI, unadjusted p)', '',
          '| size | scenario | row | THR | LAT @1.0 Lsat | P99 @1.0 Lsat |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for sc in scen(z):
            for a in PRIMARY:
                L.append('| %s | %s | %s | %s |' % (z, sname(sc), a, ' | '.join(fmt(find(size=z, row=a, reference='best baseline', metric=n, scenarios=sname(sc))) for n in METRICS)))
    L.append('')

    # absolute values
    L += ['## Absolute values: THR / LAT @1.0 Lsat / P99 @1.0 Lsat (mean over the seeds; THR in flits per node per cycle, latencies in cycles)', '']
    for z in SIZES:
        L += ['**%s**' % z, '', '| row | ' + ' | '.join(sname(sc) for sc in scen(z)) + ' |', '|---|' + '---|' * 5]
        for row in ROWS:
            if not row_scen(row, z):
                continue
            cells = []
            for sc in scen(z):
                cells.append('%.4f / %.0f / %.0f' % (smean(row, z, sc, 'THR'), smean(row, z, sc, 'LAT'), smean(row, z, sc, 'P99')) if sc in row_scen(row, z) else '-')
            L.append('| %s | %s |' % (row, ' | '.join(cells)))
        L.append('')

    # mechanisms
    mech = []
    L += ['## Mechanisms: LF and DLY against the ideal decision of the same candidate (five scenarios; %, unadjusted)', '',
          '| size | candidate | mechanism | LAT @0.2 | LAT @0.5 | LAT @1.0 | P99 @1.0 | THR |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for c in CANDS:
            for k in ('LF', 'DLY'):
                a = mrow(c, k)
                scs = row_scen(a, z)
                if not scs:
                    continue
                cells = []
                for n in ('LAT02', 'LAT05', 'LAT', 'P99', 'THR'):
                    x = test(a, c, z, scs, n)
                    mech.append(x)
                    cells.append(fmt(x))
                L.append('| %s | %s | %s | %s |' % (z, c, k, ' | '.join(cells)))
    L += ['', '**DLY against LF** (is the lookahead needed?)', '', '| size | candidate | LAT @0.2 | LAT @0.5 | LAT @1.0 | P99 @1.0 | THR |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for c in CANDS:
            a, b = mrow(c, 'DLY'), mrow(c, 'LF')
            scs = row_scen(a, z)
            if not scs:
                continue
            cells = []
            for n in ('LAT02', 'LAT05', 'LAT', 'P99', 'THR'):
                x = test(a, b, z, scs, n)
                mech.append(x)
                cells.append(fmt(x))
            L.append('| %s | %s | %s |' % (z, c, ' | '.join(cells)))
    L += ['', '**Controls** (CI_qlLA_X, uniform fault-free): lookahead without the fallback at residual 1 (`Lnofb`) and lookahead with the fallback at residual 0 (`LF0`)', '',
          '| size | row | against | LAT @0.2 | LAT @0.5 | LAT @1.0 | P99 @1.0 | THR |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        u = [scen(z)[0]]
        for a, refs in (('CI_qlLA_X_Lnofb', ('CI_qlLA_X', 'CI_qlLA_X_LF')), ('CI_qlLA_X_LF0', ('CI_qlLA_X', 'CI_qlLA_X_LF')), ('CI_qlLA_X_LF', ('CI_qlLA_X',)), ('CI_qlLA_X_DLY', ('CI_qlLA_X',))):
            for b in refs:
                cells = []
                for n in ('LAT02', 'LAT05', 'LAT', 'P99', 'THR'):
                    x = test(a, b, z, u, n)
                    mech.append(x)
                    cells.append(fmt(x))
                L.append('| %s | %s | %s | %s |' % (z, a, b, ' | '.join(cells)))
    write(os.path.join(OUT, 'mechanism.csv'), mech)

    # decision hops
    hops = []
    L += ['', '## Decision hops, fallbacks and stale decisions (counters at 1.0 x Lsat, all scenarios of the row and the five seeds)', '',
          '| size | row | hops per packet | hops offering more than one output: chiplet | interposer | all | decision hops per packet | fallback rate (LF) | stored decisions differing from a fresh one: of all / of decision hops (LF) |',
          '|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for row in ROWS:
            t = hopstats(row, z)
            if not t:
                continue
            h = t['hops_chip'] + t['hops_ipos']
            hm = t['hops_chip_multi'] + t['hops_ipos_multi']
            fb = pc(t['lookahead_fb_taken'], t['lookahead_multi']) if t['lookahead_multi'] else '-'
            mm = '%s / %s' % (pc(t['lookahead_mismatch'], t['lookahead_used']), pc(t['lookahead_mismatch'], t['lookahead_multi'])) if t['lookahead_multi'] else \
                ('%s / -' % pc(t['lookahead_mismatch'], t['lookahead_used']) if t['lookahead_used'] else '-')
            hops.append(dict(size=z, row=row, hops=h, hops_multi=hm, hops_chip=t['hops_chip'], hops_chip_multi=t['hops_chip_multi'], hops_ipos=t['hops_ipos'],
                             hops_ipos_multi=t['hops_ipos_multi'], packets=t['packets_measured'], lookahead_used=t['lookahead_used'], lookahead_multi=t['lookahead_multi'],
                             lookahead_mismatch=t['lookahead_mismatch'], fb_checks=t['lookahead_fb_checks'], fb_blocked=t['lookahead_fb_blocked'],
                             fb_requests=t['lookahead_fb_requests'], fb_taken=t['lookahead_fb_taken']))
            L.append('| %s | %s | %.2f | %s | %s | %s | %.2f | %s | %s |' % (z, row, h / float(t['packets_measured']), pc(t['hops_chip_multi'], t['hops_chip']), pc(t['hops_ipos_multi'], t['hops_ipos']),
                                                                    pc(hm, h), hm / float(t['packets_measured']), fb, mm))
    write(os.path.join(OUT, 'hops.csv'), hops)

    # low load
    L += ['', '## Low-load cost: LAT at 0.2 and 0.5 x Lsat against DeFT-P (over the row\'s scenarios; %, unadjusted; then the mean difference in cycles)', '',
          '| size | row | LAT @0.2 | cycles @0.2 | LAT @0.5 | cycles @0.5 |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for row in ROWS:
            scs = row_scen(row, z)
            if not scs or row == 'DeFT_P':
                continue
            cyc = []
            for n in ('LAT02', 'LAT05'):
                d = [smean(row, z, sc, n) - smean('DeFT_P', z, sc, n) for sc in scs]
                cyc.append(mean(d))
            L.append('| %s | %s | %s | %+.1f | %s | %+.1f |' % (z, row, fmt(find(size=z, row=row, reference='DeFT_P', metric='LAT02', scenarios=allscen(row, z))), cyc[0],
                                                                fmt(find(size=z, row=row, reference='DeFT_P', metric='LAT05', scenarios=allscen(row, z))), cyc[1]))

    # selection ladder
    ladder_rows = ['CI_rand_X', 'CI_heur_X', 'CI_heurLA_X', 'CI_qlLA_X']
    info = {'CI_rand_X': 'random among the offered outputs', 'CI_heur_X': 'occupancy (and busy state)', 'CI_heurLA_X': 'plus one-hop lookahead', 'CI_qlLA_X': 'plus Q-learning'}
    L += ['', '## The selection ladder on relation X (ideal decision): what each piece of information adds', '',
          '| size | row (information) | scenarios | THR against the best baseline | LAT @1.0 | P99 @1.0 | THR against the row above | LAT @1.0 against the row above | LAT @1.4 against the row above |', '|---|---|---|---|---|---|---|---|---|']
    lad_csv = []
    for z in SIZES:
        common = [sc for sc in scen(z) if all(sc in row_scen(r, z) for r in ladder_rows)]
        for i, row in enumerate(ladder_rows):
            cells = [fmt(test(row, 'best', z, common, n)) for n in METRICS]
            if i:
                steps = [test(row, ladder_rows[i - 1], z, common, n) for n in ('THR', 'LAT', 'LAT14')]
                lad_csv += steps
                cells += [fmt(x) for x in steps]
            else:
                cells += ['-', '-', '-']
            L.append('| %s | %s (%s) | %s | %s |' % (z, row, info[row], '+'.join(sname(sc) for sc in common), ' | '.join(cells)))
    L += ['', 'Per scenario on 4x4 (mean over the seeds): accepted / latency at 1.4 x Lsat', '', '| row | ' + ' | '.join(sname(sc) for sc in scen('4x4')) + ' |', '|---|' + '---|' * 5]
    for row in ladder_rows:
        cells = []
        for sc in scen('4x4'):
            if sc in row_scen(row, '4x4'):
                cells.append('%.4f / %.0f' % (mean(run(row, '4x4', sc, 5, s)['accepted'] for s in SEEDS if (row, '4x4-' + sc[0], sc[1], lad('4x4', sc)[5], s) in R), smean(row, '4x4', sc, 'LAT14')))
            else:
                cells.append('-')
        L.append('| %s | %s |' % (row, ' | '.join(cells)))
    write(os.path.join(OUT, 'ladder.csv'), lad_csv)

    # X against O against G
    L += ['', '## Interposer order with an ideal decision: X (XY), O (VN-split) and G (odd-even), CI with Q-learning, per scenario (mean over the seeds)', '',
          '| size | scenario | THR: X / O / G | LAT @1.0: X / O / G | P99 @1.0: X / O / G | best THR | best LAT | best P99 |', '|---|---|---|---|---|---|---|---|']
    trio = ['CI_qlLA_X', 'CI_qlLA_O', 'CI_qlLA_G']
    for z in SIZES:
        for sc in scen(z):
            v = {n: [smean(r, z, sc, n) for r in trio] for n in METRICS}
            bt = 'XOG'[max(range(3), key=lambda i: v['THR'][i])]
            bl = 'XOG'[min(range(3), key=lambda i: v['LAT'][i])]
            bp = 'XOG'[min(range(3), key=lambda i: v['P99'][i])]
            L.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (z, sname(sc), ' / '.join('%.4f' % x for x in v['THR']), ' / '.join('%.0f' % x for x in v['LAT']),
                                                                   ' / '.join('%.0f' % x for x in v['P99']), bt, bl, bp))
    L += ['', '**O against X and G against X** (five scenarios; %, unadjusted)', '', '| size | comparison | THR | LAT @1.0 | P99 @1.0 |', '|---|---|---|---|---|']
    for z in SIZES:
        for a, b in (('CI_qlLA_O', 'CI_qlLA_X'), ('CI_qlLA_G', 'CI_qlLA_X'), ('CI_qlLA_O', 'CI_qlLA_G'), ('CI_heurLA_O', 'CI_heurLA_X'), ('FULL_qlLA_X', 'CI_qlLA_X')):
            L.append('| %s | %s against %s | %s |' % (z, a, b, ' | '.join(fmt(test(a, b, z, scen(z), n)) for n in METRICS)))

    # the VN-split order without late binding, and late binding without it
    L += ['', '## The VN-split order without late binding (DeFT_P_O1 against DeFT_P) and late binding on top of it (CI_qlLA_O against DeFT_P_O1), per scenario (%, unadjusted)', '',
          '| size | scenario | DeFT_P_O1 against DeFT_P: THR | LAT @1.0 | P99 @1.0 | CI_qlLA_O against DeFT_P_O1: THR | LAT @1.0 | P99 @1.0 | CI_qlLA_X against DeFT_P: THR | LAT @1.0 | P99 @1.0 |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for scs, nm in [([sc], sname(sc)) for sc in scen(z)] + [(scen(z), 'all five')]:
            c1 = [short(test('DeFT_P_O1', 'DeFT_P', z, scs, n)) for n in METRICS]
            c2 = [short(test('CI_qlLA_O', 'DeFT_P_O1', z, scs, n)) for n in METRICS]
            c3 = [short(test('CI_qlLA_X', 'DeFT_P', z, scs, n)) for n in METRICS]
            L.append('| %s | %s | %s |' % (z, nm, ' | '.join(c1 + c2 + c3)))

    # beyond saturation
    L += ['', '## Beyond saturation: accepted throughput at 2.0 and 2.4 x Lsat relative to the row\'s peak (mean accepted over the seeds, per scenario; mean and minimum over the scenarios)', '',
          '| size | row | at 2.0 x: mean (min) | at 2.4 x: mean (min) | scenarios where the accepted throughput never falls by more than 1 % from one load to the next |', '|---|---|---|---|---|']
    for z in SIZES:
        for row in ROWS:
            sv = [x for x in sat if x['size'] == z and x['row'] == row]
            if not sv:
                continue
            a20, a24 = [x['acc_2_0_over_peak'] for x in sv], [x['acc_2_4_over_peak'] for x in sv]
            L.append('| %s | %s | %.3f (%.3f) | %.3f (%.3f) | %d of %d |' % (z, row, mean(a20), min(a20), mean(a24), min(a24), sum(1 for x in sv if x['monotone']), len(sv)))
    if missing:
        L += ['', '## Missing runs (%d)' % len(missing), ''] + ['- %s' % (m,) for m in missing[:100]]
    L += ['', 'Figures: `latency_load_4x4.png` / `.pdf` (mean latency against load) and `accepted_load_4x4.png` / `.pdf` (accepted against offered throughput), 4x4, four scenarios;',
          'the plotted values are in `curves_4x4.csv`.']
    open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    figures()
    print(NL.join(L[:45]))


# ---- figures (4x4: uniform, chipperm, chiptrans, faulty) ----
# One hue per method family in the validated order blue, orange, aqua, violet, magenta, green (adjacent pairs pass the CVD and normal-vision checks);
# the variant of a family (DeFT-B, the LF mechanism) is a dashed line with its own marker, so identity never rests on colour alone.
SERIES = [('DeFT_P', 'DeFT-P', '#2a78d6', 'o', '-'), ('DeFT_B', 'DeFT-B', '#2a78d6', '^', '--'), ('MTR', 'MTR', '#eb6834', 's', '-'), ('RC', 'RC', '#1baf7a', 'D', '-'),
          ('CI_qlLA_X', 'CI_qlLA_X (ideal)', '#6250d6', 'v', '-'), ('CI_qlLA_X_LF', 'CI_qlLA_X (LF)', '#6250d6', 'X', '--'),
          ('CI_qlLA_G', 'CI_qlLA_G (odd-even, ideal)', '#e87ba4', 'P', '-'),
          ('CI_qlLA_O', 'CI_qlLA_O (ideal)', '#008300', '<', '-'), ('CI_qlLA_O_LF', 'CI_qlLA_O (LF)', '#008300', '*', '--')]


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def figures():
    z = '4x4'
    panels = [(scen(z)[0], 'uniform'), (scen(z)[2], 'chipperm'), (scen(z)[3], 'chiptrans'), (scen(z)[4], 'uniform, one faulty VL per chiplet')]
    plt.rcParams.update({'font.size': 9, 'font.family': 'sans-serif', 'axes.edgecolor': '#c3c2b7', 'axes.linewidth': 0.8, 'xtick.color': '#52514e', 'ytick.color': '#52514e',
                         'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b', 'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb', 'savefig.facecolor': '#fcfcfb'})
    curves = []
    for kind in ('latency', 'accepted'):
        fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.6))
        for ax, (sc, title) in zip(axes.flat, panels):
            ld = lad(z, sc)
            ax.grid(True, color='#e1e0d9', linewidth=0.6)
            ax.set_axisbelow(True)
            if kind == 'accepted':
                ax.plot([8 * ld[0], 8 * ld[-1]], [8 * ld[0], 8 * ld[-1]], color='#c3c2b7', linewidth=1.0, zorder=1)
            for row, label, col, mk, ls in SERIES:
                if sc not in row_scen(row, z):
                    continue
                xs, ys = [], []
                for i in range(9):
                    v = [run(row, z, sc, i, s)[kind] for s in SEEDS if (row, '%s-%s' % (z, sc[0]), sc[1], ld[i], s) in R]
                    if v:
                        xs.append(8 * ld[i])
                        ys.append(gmean(v) if kind == 'latency' else mean(v))
                        curves.append(dict(figure=kind, scenario=title, row=row, load_x_lsat=MULTS[i], offered_flits_per_node_cycle=round(8 * ld[i], 5), value=round(ys[-1], 5), n_seeds=len(v)))
                ax.plot(xs, ys, color=col, marker=mk, linestyle=ls, linewidth=2, markersize=11 if mk == '*' else 8, markeredgecolor='#fcfcfb', markeredgewidth=1.2,
                        label=label, zorder=3)
            if kind == 'latency':
                ax.set_yscale('log')
                ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
                ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.set_title('4x4, %s' % title, fontsize=9.5, loc='left')
            ax.set_xlabel('offered load (flits / node / cycle)')
            ax.set_ylabel('mean latency (cycles, log scale)' if kind == 'latency' else 'accepted throughput (flits / node / cycle)')
            ax.xaxis.set_major_locator(plt.MaxNLocator(6))
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
        h, lab = axes[0][0].get_legend_handles_labels()
        fig.legend(h, lab, loc='lower center', ncol=5, frameon=False, fontsize=8.5, handlelength=5.0)
        ttl = 'Mean latency against load' if kind == 'latency' else 'Accepted against offered throughput'
        sub = 'geometric mean of seeds 111-115' if kind == 'latency' else 'mean of seeds 111-115; the grey line is accepted = offered'
        fig.suptitle('%s, 4x4, pipe_all 2 (%s; loads 0.2-2.4 x Lsat of DeFT-P)' % (ttl, sub), fontsize=10, x=0.01, ha='left')
        fig.tight_layout(rect=(0, 0.07, 1, 0.96))
        for ext in ('png', 'pdf'):
            fig.savefig(os.path.join(OUT, '%s_load_4x4.%s' % (kind, ext)), dpi=180)
        plt.close(fig)
    write(os.path.join(OUT, 'curves_4x4.csv'), curves)


if __name__ == '__main__':
    main()
