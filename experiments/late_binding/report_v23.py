"""v23 report, following results_v23_fidelity/PREREGISTRATION.md.

Usage: python3 report_v23.py [all | d2 | d5 | d4]
d2: eval_runs.csv, load_points_v23.json -> report/primary.csv, secondary.csv, saturation.csv, summary.md, latency_load.{png,pdf}
d5: look_runs.csv (+ eval_runs.csv)     -> report/lookahead.csv (and its table in summary.md)
d4: herd_runs.csv                        -> report/herding.csv (and its table in summary.md)
all (default): d2, then d5 and d4 where their CSVs exist. summary.md also carries the VC-split table of A2 (vc_split.md).
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primary_from_csv import holm, ttest  # noqa: E402
from report_v4 import Data, load_csv, pct  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v23_fidelity')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
SEEDS = list(range(91, 96))
HERD_SEEDS = [101, 102]
PIPES = (0, 2)
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
NORTH = {'2x2': '0x1111', '3x3': '0x111111111', '4x4': '0x1111111111111111'}
OURS = ['CI_qlLA_G', 'FULL_qlLA_G']
FF = ['MTR', 'RC']
METHODS = {0: ['DeFT_P', 'DeFT_B', 'DeFT_old', 'MTR', 'RC', 'MTR_static', 'RC_static', 'DeFT_Dis', 'CI_qlLA_G', 'FULL_qlLA_G'],
           2: ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'DeFT_Dis', 'CI_qlLA_G', 'FULL_qlLA_G']}
LABEL = {'DeFT_P': 'DeFT-P', 'DeFT_B': 'DeFT-B', 'DeFT_old': 'DeFT (v19-v21)', 'DeFT_Dis': 'DeFT-Dis',
         'MTR_static': 'MTR (static VC)', 'RC_static': 'RC (static VC)'}
METRICS = ['LAT', 'P99', 'THR']
NL = chr(10)
P = {}


def lab(v):
    return LABEL.get(v, v)


def scen(z):
    return [(z + '-uniform', FREE[z]), (z + '-hotspot', FREE[z]), (z + '-chipperm', FREE[z]), (z + '-uniform', NORTH[z])]


def ff(z):
    return [(p, m) for p, m in scen(z) if int(m, 16) == 0]


def is_ff(v):
    return v.startswith('MTR') or v.startswith('RC')


def scen_for(z, *vs):
    return ff(z) if any(is_ff(v) for v in vs) else scen(z)


def vn(v, pipe):
    return '%s-p%d' % (v, pipe)


def ladder(pipe):
    def f(p, m):
        z, pat = p.split('-')
        return P['%s__%s__%s__p%d' % (z, pat, m, pipe)]['eval']
    return f


def isnan(x):
    return x != x


def stat(xs):
    if len(xs) < 2:
        return dict(n_seeds=len(xs), effect_pct=float('nan'), ci_low=float('nan'), ci_high=float('nan'), p=float('nan'))
    e, lo, hi = pct(xs)
    return dict(n_seeds=len(xs), effect_pct=round(e, 2), ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs))


def scn_name(z, sc):
    if sc == ff(z):
        return 'fault-free'
    if sc == scen(z):
        return 'all'
    return ' '.join('%s %s' % (p.split('-')[1], m) for p, m in sc)


def test(D, z, pipe, a, b, n, sc):
    xs = D[(z, pipe)].per_seed(vn(a, pipe), vn(b, pipe), n, sc)
    return dict(size=z, pipe_all=pipe, variant=a, reference=b, metric=n, scenarios=scn_name(z, sc), **stat(xs))


def verdict(x, key='p_holm'):
    if isnan(x[key]) or x[key] >= 0.05:
        return 'n.s.'
    good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
    return 'supported' if good else 'against'


def fmt(x, key='p'):
    if isnan(x['effect_pct']):
        return 'n/a (%d seeds)' % x['n_seeds']
    return '%+.1f [%+.1f, %+.1f] (%s %.2g)' % (x['effect_pct'], x['ci_low'], x['ci_high'], key.replace('_', ' '), x[key])


def write(path, rows):
    if not rows:
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        for x in rows:
            w.writerow({k: ('%.4g' % v if k in ('p', 'p_holm') and isinstance(v, float) else v) for k, v in x.items()})


def find(rows, **kw):
    return next(x for x in rows if all(x[k] == v for k, v in kw.items()))


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def saturation(R, z, pipe, v):
    """Per scenario: the v10 flag (mean accepted at 1.0 x Lsat below 95 % of offered), the own saturation load, and where the
    THR maximum (mean accepted over seeds) sits on the 9-load ladder."""
    out = []
    for p, m in scen_for(z, v):
        lad = ladder(pipe)(p, m)
        means, ok = [], []
        for r in lad:
            acc = [R[(vn(v, pipe), p, m, r, s)]['accepted'] for s in SEEDS if (vn(v, pipe), p, m, r, s) in R]
            means.append(sum(acc) / len(acc) if acc else float('nan'))
            ok.append(bool(acc) and sum(acc) / len(acc) >= 0.95 * 8 * r)
        own = max((MULTS[i] for i in range(len(lad)) if ok[i] and all(ok[:i + 1])), default=0.0)
        valid = [i for i in range(len(lad)) if not isnan(means[i])]
        arg = max(valid, key=lambda i: means[i]) if valid else -1
        out.append(dict(size=z, pipe_all=pipe, method=v, pattern=p.split('-')[1], mask=m, flagged_at_1_0=not ok[3], own_sat_load=own,
                        thr_max_at=MULTS[arg] if arg >= 0 else float('nan'), thr_at_top=arg == len(lad) - 1))
    return out


# ---- D2 / D3 ----
def d2():
    R = load_csv(os.path.join(RES, 'eval_runs.csv'))
    D = {(z, q): Data(R, scen(z), ladder(q), SEEDS) for z in SIZES for q in PIPES}
    design = [(vn(v, q), p, m, r, s) for q in PIPES for z in SIZES for v in METHODS[q] for p, m in scen_for(z, v) for r in ladder(q)(p, m) for s in SEEDS]
    missing = [k for k in design if k not in R]
    dead = sum(x['dead'] for x in R.values())

    prim = [dict(test(D, z, 0, 'DeFT_P', 'DeFT_old', n, scen(z)), family='H1') for z in SIZES for n in ('THR', 'LAT')]
    prim += [dict(test(D, z, 0, a, 'DeFT_P', n, scen(z)), family='H2') for z in SIZES for a in OURS for n in ('LAT', 'P99')]
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'primary.csv'), prim)

    sec = []
    for q in PIPES:
        for z in SIZES:
            for b in FF:
                sec += [test(D, z, q, 'DeFT_P', b, n, ff(z)) for n in METRICS]
                sec += [test(D, z, q, 'DeFT_P', b, n, [sc]) for sc in ff(z) for n in METRICS]
            sec += [test(D, z, q, 'DeFT_P', 'DeFT_B', n, scen(z)) for n in METRICS]
            sec += [test(D, z, q, v, 'DeFT_P', n, scen_for(z, v)) for v in METHODS[q] if v != 'DeFT_P' for n in METRICS]
    for z in SIZES:
        sec += [test(D, z, 0, b, b + '_static', n, ff(z)) for b in FF for n in METRICS]
    write(os.path.join(OUT, 'secondary.csv'), sec)
    sat = [x for q in PIPES for z in SIZES for v in METHODS[q] for x in saturation(R, z, q, v)]
    write(os.path.join(OUT, 'saturation.csv'), sat)

    L = ['# v23 summary: reference measurements under the paper\'s rules (seeds 91-95; generated by report_v23.py)', '',
         'Runs: %d of %d; missing: %d; dead-end events: %d. DeFT-P = `-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst`; '
         'DeFT-B = the same VN options with the v1-v21 entry; DeFT (v19-v21) = `-deft_vn_rr 1` alone. Every VN-based method carries '
         'DeFT-P\'s VN options and `-traffic_rng 1`; MTR and RC carry `-vc_per_hop 1` (the static-VC rows without it). Loads: the 9-load '
         'ladders of `load_points_v23.json` (0.2-2.4 x Lsat of DeFT-P, per pipe depth); LAT and P99 at the 4th load (1.0 x Lsat), THR = the '
         'maximum accepted throughput over the 9 loads. MTR and RC: fault-free scenarios only (every comparison with them uses those).'
         % (len(design) - len(missing), len(design), len(missing), dead), '',
         '## Primary results (Holm over 18), pipe_all = 0: % change (THR positive = higher; LAT, P99 negative = lower)', '',
         '| family | size | variant | reference | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|---|---|']
    for x in prim:
        L.append('| %s | %s | %s | %s | %s | %s | **%s** |' % (x['family'], x['size'], lab(x['variant']), lab(x['reference']), x['metric'], fmt(x, 'p_holm'), x['verdict']))
    cnt = lambda fam, vd: sum(1 for x in prim if x['family'] == fam and x['verdict'] == vd)  # noqa: E731
    L += ['', 'H1 (DeFT-P against DeFT (v19-v21), THR and LAT, 3 sizes): supported %d of 6; against %d; n.s. %d.' % (cnt('H1', 'supported'), cnt('H1', 'against'), cnt('H1', 'n.s.')),
          'H2 (CI_qlLA_G and FULL_qlLA_G against DeFT-P, LAT and P99, 3 sizes): supported %d of 12; against %d; n.s. %d.' % (cnt('H2', 'supported'), cnt('H2', 'against'), cnt('H2', 'n.s.')), '']

    L += ['## Secondary: DeFT-P against MTR and RC, fault-free scenarios (unadjusted)', '', '| pipe_all | size | reference | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat | THR |', '|---|---|---|---|---|---|---|']
    for q in PIPES:
        for z in SIZES:
            for b in FF:
                for sc in [ff(z)] + [[s] for s in ff(z)]:
                    nm = scn_name(z, sc)
                    L.append('| %d | %s | %s | %s | %s |' % (q, z, b, nm, ' | '.join(fmt(find(sec, size=z, pipe_all=q, variant='DeFT_P', reference=b, metric=n, scenarios=nm)) for n in METRICS)))
    L += ['', '## Secondary: DeFT-P against DeFT-B (the paper\'s entry against the v1-v21 entry; unadjusted)', '', '| pipe_all | size | LAT | P99 | THR |', '|---|---|---|---|---|']
    for q in PIPES:
        for z in SIZES:
            L.append('| %d | %s | %s |' % (q, z, ' | '.join(fmt(find(sec, size=z, pipe_all=q, variant='DeFT_P', reference='DeFT_B', metric=n)) for n in METRICS)))
    L += ['', '## Secondary: the per-hop VC of MTR and RC (with against without `-vc_per_hop`, pipe_all 0, fault-free; unadjusted)', '', '| size | method | LAT | P99 | THR |', '|---|---|---|---|---|']
    for z in SIZES:
        for b in FF:
            L.append('| %s | %s | %s |' % (z, b, ' | '.join(fmt(find(sec, size=z, pipe_all=0, variant=b, reference=b + '_static', metric=n)) for n in METRICS)))
    L.append('')
    for q in PIPES:
        for z in SIZES:
            L += ['## %s, pipe_all = %d: every method against DeFT-P (effect %%, 95 %% CI, unadjusted p; MTR and RC over the fault-free scenarios)' % (z, q), '',
                  '| method | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat | THR | THR max at the top load | saturates below 1.0 x Lsat in |', '|---|---|---|---|---|---|---|']
            for v in METHODS[q]:
                cells = ['reference'] * 3 if v == 'DeFT_P' else [fmt(find(sec, size=z, pipe_all=q, variant=v, reference='DeFT_P', metric=n)) for n in METRICS]
                sv = [x for x in sat if (x['size'], x['pipe_all'], x['method']) == (z, q, v)]
                top = '%d of %d' % (sum(1 for x in sv if x['thr_at_top']), len(sv))
                nt = ['%s %s (max at %s x)' % (x['pattern'], x['mask'], x['thr_max_at']) for x in sv if not x['thr_at_top']]
                fl = ['%s %s (own sat. %s x Lsat)' % (x['pattern'], x['mask'], x['own_sat_load']) for x in sv if x['flagged_at_1_0']]
                L.append('| %s | %s | %s | %s | %s |' % (lab(v), 'fault-free' if is_ff(v) else 'all', ' | '.join(cells),
                                                        top + ('; ' + '; '.join(nt) if nt else ''), '; '.join(fl) if fl else '-'))
            L.append('')
    vcs = os.path.join(RES, 'vc_split.md')
    if os.path.exists(vcs):
        lines = open(vcs).read().split(NL)
        L += ['## VC split per link class (A2, `vc_split.md`)', ''] + [l for l in lines if l.startswith('|') or l.startswith('Uniform')] + ['']
    if missing:
        L += ['## Missing runs (%d)' % len(missing), ''] + ['- %s' % (m,) for m in missing[:100]] + ['']
    L += ['Figure: `latency_load.png` / `.pdf` (mean latency against load, uniform fault-free, both pipe depths; log axis).']
    figure(R)
    return L


def figure(R):
    # one hue per family (the DeFT variants share blue and differ by line style and marker), markers as the secondary encoding
    series = [('DeFT_P', '#2a78d6', 'o', '-'), ('DeFT_B', '#2a78d6', '^', '--'), ('DeFT_old', '#2a78d6', 'x', ':'), ('MTR', '#eb6834', 's', '-'),
              ('RC', '#1baf7a', 'D', '-'), ('CI_qlLA_G', '#e87ba4', 'v', '-'), ('FULL_qlLA_G', '#008300', 'P', '-')]
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ad', 'axes.linewidth': 0.8, 'xtick.color': '#52514e', 'ytick.color': '#52514e',
                         'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.6), sharey=True)
    for i, q in enumerate(PIPES):
        for ax, z in zip(axes[i], SIZES):
            p, m = z + '-uniform', FREE[z]
            lad = ladder(q)(p, m)
            ax.grid(True, color='#e6e5e0', linewidth=0.6)
            ax.set_axisbelow(True)
            for v, col, mk, ls in series:
                if v not in METHODS[q]:
                    continue
                xs, ys = [], []
                for r in lad:
                    vals = [R[(vn(v, q), p, m, r, s)]['latency'] for s in SEEDS if (vn(v, q), p, m, r, s) in R]
                    if vals:
                        xs.append(r)
                        ys.append(gmean(vals))
                ax.plot(xs, ys, color=col, marker=mk, linestyle=ls, linewidth=2, markersize=7, markeredgecolor='white', markeredgewidth=1.0, label=lab(v))
            ax.set_yscale('log')
            ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.set_title('%s, uniform, pipe_all = %d' % (z, q), fontsize=9.5, loc='left')
            if i == 1:
                ax.set_xlabel('injection rate (packets / cycle / node)')
            ax.xaxis.set_major_locator(plt.MaxNLocator(5))
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
        axes[i][0].set_ylabel('mean latency (cycles, log)')
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=7, frameon=False, fontsize=8.5)
    fig.suptitle('Mean latency against load, uniform traffic, fault-free (geometric mean of seeds 91-95; loads 0.2-2.4 x Lsat of DeFT-P)', fontsize=10, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT, 'latency_load.' + ext), dpi=180)
    plt.close(fig)


# ---- D5 ----
def load_extra(path, fields):
    out = {}
    for r in csv.DictReader(open(path)):
        out[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = {k: float(r[k]) if r.get(k) not in (None, '') else float('nan') for k in fields}
    return out


def d5():
    fn = os.path.join(RES, 'look_runs.csv')
    if not os.path.exists(fn):
        return []
    R = load_csv(os.path.join(RES, 'eval_runs.csv'))
    R.update(load_csv(fn))
    X = load_extra(fn, ('lookahead_used', 'lookahead_mismatch', 'lookahead_stored'))
    rows, L = [], ['## D5: lookahead routing at pipe_all = 2 (lookahead_route 1, decision_delay 1) against the same variant at decision_delay 0 (uniform, seeds 91-95; unadjusted)', '',
                   '| size | variant | LAT @0.2 | LAT @1.0 | LAT @2.0 | THR | share of the ideal LAT gain over DeFT-P kept at 1.0 x Lsat | stored decisions differing at the next router |', '|---|---|---|---|---|---|---|---|']
    for z in ('2x2', '4x4'):
        p, m = z + '-uniform', FREE[z]
        lad = ladder(2)(p, m)
        D = Data(R, [(p, m)], ladder(2), SEEDS)
        for v in OURS:
            a, b, ref = v + '_look', v, 'DeFT_P'
            cells = []
            for name, idx in (('LAT@0.2', 0), ('LAT@1.0', 3), ('LAT@2.0', 7)):
                x = dict(size=z, variant=a, reference=b, metric=name, **stat(D.per_seed(vn(a, 2), vn(b, 2), 'LAT', [(p, m)], idx)))
                rows.append(x)
                cells.append(fmt(x))
            x = dict(size=z, variant=a, reference=b, metric='THR', **stat(D.per_seed(vn(a, 2), vn(b, 2), 'THR', [(p, m)])))
            rows.append(x)
            cells.append(fmt(x))
            g_ideal = D.per_seed(vn(ref, 2), vn(b, 2), 'LAT', [(p, m)], 3)
            g_look = D.per_seed(vn(ref, 2), vn(a, 2), 'LAT', [(p, m)], 3)
            share = (sum(g_look) / len(g_look)) / (sum(g_ideal) / len(g_ideal)) if g_ideal and g_look and sum(g_ideal) != 0 else float('nan')
            used = sum(X[(vn(a, 2), p, m, r, s)]['lookahead_used'] for r in lad for s in SEEDS if (vn(a, 2), p, m, r, s) in X)
            mism = sum(X[(vn(a, 2), p, m, r, s)]['lookahead_mismatch'] for r in lad for s in SEEDS if (vn(a, 2), p, m, r, s) in X)
            per_load = []
            for idx in (0, 3, 7):
                u = sum(X[(vn(a, 2), p, m, lad[idx], s)]['lookahead_used'] for s in SEEDS if (vn(a, 2), p, m, lad[idx], s) in X)
                mm = sum(X[(vn(a, 2), p, m, lad[idx], s)]['lookahead_mismatch'] for s in SEEDS if (vn(a, 2), p, m, lad[idx], s) in X)
                per_load.append('%.1f %%' % (100 * mm / u) if u else 'n/a')
            rows.append(dict(size=z, variant=a, reference=ref, metric='share_of_ideal_gain_kept', n_seeds=len(g_look), effect_pct=round(100 * share, 1) if not isnan(share) else share,
                             ci_low=float('nan'), ci_high=float('nan'), p=float('nan')))
            rows.append(dict(size=z, variant=a, reference='', metric='mismatch_share_all_loads', n_seeds=len(SEEDS), effect_pct=round(100 * mism / used, 2) if used else float('nan'),
                             ci_low=float('nan'), ci_high=float('nan'), p=float('nan')))
            L.append('| %s | %s | %s | %s | %s (at 0.2 / 1.0 / 2.0 x Lsat: %s; over the 9 loads) |' % (
                z, v, ' | '.join(cells), ('%.0f %%' % (100 * share)) if not isnan(share) else 'n/a', ('%.1f %%' % (100 * mism / used)) if used else 'n/a', ' / '.join(per_load)))
    L += ['', 'The ideal gain is ln(LAT of DeFT-P) - ln(LAT of the variant at decision_delay 0), per seed; the share is the ratio of the seed means with the lookahead variant in the numerator.', '']
    write(os.path.join(OUT, 'lookahead.csv'), rows)
    return L


# ---- D4 ----
def d4():
    fn = os.path.join(RES, 'herd_runs.csv')
    if not os.path.exists(fn):
        return []
    R = load_csv(fn)
    rows, L = [], ['## D4: hysteresis A/B (4x4, loads 1.0-2.4 x Lsat, seeds 101-102; accepted throughput, flits/cycle/node, mean of the seeds; exploratory)', '']
    for v in OURS:
        for pat in ('uniform', 'hotspot'):
            for cfg, q in (('dd0', 0), ('look', 2)):
                p, m = '4x4-' + pat, FREE['4x4']
                lad = ladder(q)(p, m)[3:]
                L += ['**%s, %s, %s (pipe_all %d)**' % (v, pat, 'decision_delay 0' if cfg == 'dd0' else 'lookahead_route 1, decision_delay 1', q), '',
                      '| D | ' + ' | '.join('%.1f x' % x for x in MULTS[3:]) + ' | THR | monotone in load |', '|---|' + '---|' * (len(lad) + 2)]
                best, best_thr = None, -1
                for Dh in (0, 1, 2, 4):
                    name = vn('%s_h%d_%s' % (v, Dh, cfg), q)
                    acc = []
                    for r in lad:
                        a = [R[(name, p, m, r, s)]['accepted'] for s in HERD_SEEDS if (name, p, m, r, s) in R]
                        acc.append(sum(a) / len(a) if a else float('nan'))
                    valid = [a for a in acc if not isnan(a)]
                    thr = max(valid) if valid else float('nan')
                    mono = all(acc[i + 1] >= acc[i] - 1e-9 for i in range(len(acc) - 1)) if len(valid) == len(acc) else False
                    if not isnan(thr) and thr > best_thr:
                        best, best_thr = Dh, thr
                    rows.append(dict(variant=v, pattern=pat, config=cfg, pipe_all=q, D=Dh, **{'acc_%.1f' % MULTS[3 + i]: round(acc[i], 5) for i in range(len(lad))}, thr=round(thr, 5), monotone=mono))
                    L.append('| %d | %s | %.4f | %s |' % (Dh, ' | '.join('%.4f' % a for a in acc), thr, 'yes' if mono else 'no'))
                L += ['', 'Highest THR: D = %s.' % best, '']
    write(os.path.join(OUT, 'herding.csv'), rows)
    return L


def main():
    global P
    P = json.load(open(os.path.join(RES, 'load_points_v23.json')))
    os.makedirs(OUT, exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    L = []
    if what in ('all', 'd2'):
        L += d2()
    if what in ('all', 'd5'):
        L += d5()
    if what in ('all', 'd4'):
        L += d4()
    if what == 'all':
        open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[:60]))


if __name__ == '__main__':
    main()
