"""Analysis of v19 (Part K), following results_v19_vnrr/PREREGISTRATION.md.

Usage: python3 report_v19.py k5 | k6 | k7
k5: eval_runs.csv, load_points_rr.json -> report/primary.csv, secondary.csv, saturation.csv, summary.md, latency_load.{png,pdf}
k6: fault_runs.csv, fault_load_choice.json -> report/faults_primary.csv, faults_secondary.csv, faults_summary.md
k7: app_runs.csv, results_v13_apps/app_runs.csv -> report/apps_ratios.csv, apps_summary.md
"""
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from primary_from_csv import ci, holm, ttest  # noqa: E402
from report_v4 import Data, load_csv, pct  # noqa: E402
import report_v5 as R5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v19_vnrr')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
SEEDS = range(61, 71)
OURS = ['CI_qlLA_G', 'FULL_qlLA_G']
BASE_FF = ['MTR', 'RC']
BASE_ALL = ['DeFT_Dis', 'DeFT_Ran']
VN = ['DeFT', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
ALL_METHODS = ['DeFT', 'DeFT_noRR', 'MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
METRICS = ['LAT', 'P99', 'THR']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
LABEL = {'DeFT': 'DeFT(rho*)', 'DeFT_noRR': 'DeFT(rho*) without round-robin', 'DeFT_Dis': 'DeFT-Dis', 'DeFT_Ran': 'DeFT-Ran', 'XY_SP': 'XY-SP'}
NL = chr(10)


def ff(z):
    return [(p, m) for p, m in R5.scen(z) if int(m, 16) == 0]


def scen_for(z, *methods):
    return ff(z) if any(m in BASE_FF for m in methods) else R5.scen(z)


def write(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        for x in rows:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})


def verdict(x):
    good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
    return ('ours better' if good else 'ours worse') if x['p_holm'] < 0.05 else 'n.s.'


def fmt(x, key='p'):
    return f'{x["effect_pct"]:+.1f} [{x["ci_low"]:+.1f}, {x["ci_high"]:+.1f}] ({key.replace("_", " ")} {x[key]:.2g})'


def k5():
    os.makedirs(OUT, exist_ok=True)
    P = json.load(open(os.path.join(RES, 'load_points_rr.json')))

    def ladder(p, m):
        size, pat = p.split('-')
        return P[f'{size}__{pat}__{m}']['eval']
    R = load_csv(os.path.join(RES, 'eval_runs.csv'))
    D = {z: Data(R, R5.scen(z), ladder, SEEDS) for z in SIZES}

    def test(z, a, b, n, sc):
        xs = D[z].per_seed(a, b, n, sc)
        e, lo, hi = pct(xs)
        return dict(size=z, variant=a, reference=b, metric=n, scenarios='fault-free' if sc == ff(z) else 'all', n_seeds=len(xs),
                    effect_pct=round(e, 2), ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs))

    expected = sum(len(ladder(p, m)) for z in SIZES for v in ALL_METHODS for p, m in scen_for(z, v)) * len(SEEDS)
    missing = [(v, p, m, r, s) for z in SIZES for v in ALL_METHODS for p, m in scen_for(z, v) for r in ladder(p, m) for s in SEEDS if (v, p, m, r, s) not in R]
    dead = sum(x['dead'] for x in R.values())

    prim = [dict(test(z, a, 'DeFT', n, R5.scen(z)), family='H1') for z in SIZES for a in OURS for n in ('LAT', 'P99')]
    prim += [dict(test(z, a, b, n, scen_for(z, b)), family='H2') for z in SIZES for a in OURS for b in BASE_FF + BASE_ALL for n in ('LAT', 'P99')]
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'primary.csv'), prim)

    sec = [test(z, a, b, 'THR', scen_for(z, b)) for z in SIZES for a in OURS for b in ['DeFT'] + BASE_FF + BASE_ALL]
    sec += [test(z, 'DeFT', b, n, ff(z)) for z in SIZES for b in BASE_FF for n in METRICS]
    sec += [test(z, 'DeFT', 'DeFT_noRR', n, R5.scen(z)) for z in SIZES for n in METRICS]
    sec += [test(z, 'FULL_qlLA_G', 'DeFT_OE_G', n, R5.scen(z)) for z in SIZES for n in METRICS]
    sec += [test(z, 'CI_qlLA_G', 'CI_heurLA_G', n, R5.scen(z)) for z in SIZES for n in METRICS]
    write(os.path.join(OUT, 'secondary.csv'), sec)

    def find(rows, z, a, b, n):
        return next(x for x in rows if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, b, n))

    def saturation(z, v):
        out = []
        for p, m in scen_for(z, v):
            lad = ladder(p, m)
            ok = []
            for r in lad:
                acc = [R[(v, p, m, r, s)]['accepted'] for s in SEEDS if (v, p, m, r, s) in R]
                ok.append(bool(acc) and sum(acc) / len(acc) >= 0.95 * 8 * r)
            own = max((MULTS[i] for i in range(len(lad)) if ok[i] and all(ok[:i + 1])), default=0.0)
            out.append(dict(size=z, method=v, pattern=p.split('-')[1], mask=m, flagged_at_1_0=not ok[3], own_sat_load=own))
        return out
    sat = [x for z in SIZES for v in ALL_METHODS for x in saturation(z, v)]
    write(os.path.join(OUT, 'saturation.csv'), sat)

    L = ['# v19 K5 summary: DeFT with the boundary round-robin (seeds 61-70; generated by report_v19.py)', '',
         f'Runs: {expected - len(missing)} of {expected}; missing: {len(missing)}; dead-end events: {dead}. All VN-based methods with -deft_vn_rr 1, except the reference row DeFT(rho*) without round-robin. '
         'MTR and RC: fault-free scenarios only (the option does not apply; every comparison with them uses those scenarios). Loads: `load_points_rr.json`.', '',
         '## Primary results (Holm over 60): our variant vs reference, % change (negative = ours lower)', '',
         '| family | size | ours | reference | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat |', '|---|---|---|---|---|---|---|']
    for fam, refs in (('H1', ['DeFT']), ('H2', BASE_FF + BASE_ALL)):
        for z in SIZES:
            for a in OURS:
                for b in refs:
                    lat, p99 = find(prim, z, a, b, 'LAT'), find(prim, z, a, b, 'P99')
                    L.append(f'| {fam} | {z} | {a} | {LABEL.get(b, b)} | {lat["scenarios"]} | {fmt(lat, "p_holm")} **{lat["verdict"]}** | {fmt(p99, "p_holm")} **{p99["verdict"]}** |')
    cnt = lambda fam, vd: sum(1 for x in prim if x['family'] == fam and x['verdict'] == vd)  # noqa: E731
    L += ['', f'H1: supported {cnt("H1", "ours better")} of 12; against ours {cnt("H1", "ours worse")}; n.s. {cnt("H1", "n.s.")}.',
          f'H2: supported {cnt("H2", "ours better")} of 48; against ours {cnt("H2", "ours worse")}; n.s. {cnt("H2", "n.s.")}.', '',
          '## Secondary: the effect of the fix on DeFT(rho*) (with against without round-robin; unadjusted)', '', '| size | LAT | P99 | THR |', '|---|---|---|---|']
    for z in SIZES:
        L.append(f'| {z} | ' + ' | '.join(fmt(find(sec, z, 'DeFT', 'DeFT_noRR', n)) for n in METRICS) + ' |')
    L += ['', '## Secondary: DeFT(rho*) with round-robin against MTR and RC, fault-free (check against the DeFT paper; unadjusted)', '', '| size | reference | LAT | P99 | THR |', '|---|---|---|---|---|']
    for z in SIZES:
        for b in BASE_FF:
            L.append(f'| {z} | {b} | ' + ' | '.join(fmt(find(sec, z, 'DeFT', b, n)) for n in METRICS) + ' |')
    L += ['', '## Secondary: saturation throughput of our variants (unadjusted)', '', '| size | ours | reference | THR |', '|---|---|---|---|']
    for z in SIZES:
        for a in OURS:
            for b in ['DeFT'] + BASE_FF + BASE_ALL:
                L.append(f'| {z} | {a} | {LABEL.get(b, b)} | {fmt(find(sec, z, a, b, "THR"))} |')
    L += ['', '## Secondary: ablation, FULL_qlLA_G vs DeFT_OE_G (unadjusted)', '', '| size | LAT | P99 | THR |', '|---|---|---|---|']
    for z in SIZES:
        L.append(f'| {z} | ' + ' | '.join(fmt(find(sec, z, 'FULL_qlLA_G', 'DeFT_OE_G', n)) for n in METRICS) + ' |')
    L += ['', '## Secondary: CI_qlLA_G vs CI_heurLA_G (unadjusted)', '', '| size | LAT | P99 | THR |', '|---|---|---|---|']
    for z in SIZES:
        L.append(f'| {z} | ' + ' | '.join(fmt(find(sec, z, 'CI_qlLA_G', 'CI_heurLA_G', n)) for n in METRICS) + ' |')
    L.append('')
    for z in SIZES:
        L += [f'## {z}: all methods against DeFT(rho*) with round-robin (effect %, 95 % CI, unadjusted p; MTR and RC over the fault-free scenarios)', '',
              '| method | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat | THR | saturates below 1.0 x Lsat in |', '|---|---|---|---|---|---|']
        for v in ALL_METHODS:
            if v == 'DeFT':
                cells, scn = ['reference'] * 3, 'all'
            else:
                cells = [fmt(test(z, v, 'DeFT', n, scen_for(z, v))) for n in METRICS]
                scn = 'fault-free' if v in BASE_FF else 'all'
            fl = [f'{x["pattern"]} {x["mask"]} (own sat. {x["own_sat_load"]} x Lsat)' for x in sat if x['size'] == z and x['method'] == v and x['flagged_at_1_0']]
            L.append(f'| {LABEL.get(v, v)} | {scn} | ' + ' | '.join(cells) + f' | {"; ".join(fl) if fl else "-"} |')
        L.append('')
    if missing:
        L += ['## Missing runs', ''] + [f'- {m}' for m in missing[:100]] + ['']
    L += ['Figure: `latency_load.png` / `.pdf`.']
    open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)

    # latency against load, uniform, fault-free. Hues in the reference categorical order; markers are the secondary encoding.
    series = [('DeFT', '#2a78d6', 'o', '-'), ('DeFT_noRR', '#2a78d6', 'o', ':'), ('MTR', '#eb6834', 's', '-'), ('RC', '#1baf7a', 'D', '-'),
              ('CI_qlLA_G', '#e87ba4', 'v', '-'), ('FULL_qlLA_G', '#008300', 'P', '-')]
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ad', 'axes.linewidth': 0.8, 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), sharey=True)
    for ax, z in zip(axes, SIZES):
        p, m = f'{z}-uniform', [mm for pp, mm in R5.scen(z) if pp == f'{z}-uniform' and int(mm, 16) == 0][0]
        lad = ladder(p, m)
        ax.grid(True, color='#e6e5e0', linewidth=0.6)
        ax.set_axisbelow(True)
        for v, col, mk, ls in series:
            ys = [math.exp(sum(math.log(R[(v, p, m, r, s)]['latency']) for s in SEEDS) / len(SEEDS)) for r in lad]
            ax.plot(lad, ys, color=col, marker=mk, linestyle=ls, linewidth=2, markersize=8 if v != 'DeFT_noRR' else 6, markeredgecolor='white', markeredgewidth=1.0,
                    label=LABEL.get(v, v))
        ax.set_title(f'{z}, uniform', fontsize=9.5, loc='left')
        ax.set_xlabel('injection rate (packets / cycle / node)')
        ax.set_ylim(0, 300)
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel('mean latency (cycles)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=6, frameon=False, fontsize=8.5)
    fig.suptitle('Mean latency against load, uniform traffic, fault-free (geometric mean of seeds 61-70; axis clipped at 300 cycles)', fontsize=10, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT, f'latency_load.{ext}'), dpi=180)
    plt.close(fig)
    print(NL.join(L[:80]))


def k6():
    os.makedirs(OUT, exist_ok=True)
    seeds = range(71, 76)
    pats = ['uniform', 'hotspot']
    kk = [1, 2, 3]
    R = load_csv(os.path.join(RES, 'fault_runs.csv'))
    ch = json.load(open(os.path.join(RES, 'fault_load_choice.json')))
    ms = {k: v[:5] for k, v in json.load(open(os.path.join(HERE, 'results_v11', 'masks.json'))).items()}

    def val(v, z, k, p, m, s, name):
        x = R[(v, f'{z}-{p}', m, ch[f'{z}__k{k}__{p}']['rate'], s)]
        return x['p99'] if name == 'P99' else x['latency']

    def units(a, b, z, k, name):
        us = []
        for m in ms[f'{z}__k{k}']:
            for s in seeds:
                try:
                    us.append(sum(math.log(val(a, z, k, p, m, s, name) / val(b, z, k, p, m, s, name)) for p in pats) / 2)
                except KeyError:
                    pass
        return us

    def row(a, b, z, k, name):
        us = units(a, b, z, k, name)
        mu, h = ci(us)
        return dict(size=z, k=k, variant=a, reference=b, metric=name, n_units=len(us), effect_pct=round(100 * (math.exp(mu) - 1), 2),
                    ci_low=round(100 * (math.exp(mu - h) - 1), 2), ci_high=round(100 * (math.exp(mu + h) - 1), 2), p=ttest(us))
    prim = [row(a, 'DeFT', z, k, 'LAT') for z in SIZES for k in kk for a in OURS]
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = ('ours better' if x['effect_pct'] < 0 else 'ours worse') if q < 0.05 else 'n.s.'
    sec = [row(v, 'DeFT', z, k, n) for z in SIZES for k in kk for v in VN if v != 'DeFT' for n in ('LAT', 'P99')]
    write(os.path.join(OUT, 'faults_primary.csv'), prim)
    write(os.path.join(OUT, 'faults_secondary.csv'), sec)
    v14 = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'results_v14_faultload', 'report', 'primary.csv'))):
        v14[(r['size'], int(r['k']), r['variant'])] = float(r['effect_pct'])
    expected = 3 * 3 * 5 * 2 * len(VN) * len(seeds)
    sup = sum(x['verdict'] == 'ours better' for x in prim)
    against = sum(x['verdict'] == 'ours worse' for x in prim)
    L = ['# v19 K6 summary: faults with the round-robin (seeds 71-75; generated by report_v19.py)', '', f'Runs: {len(R)} of {expected}; dead-end events: {sum(x["dead"] for x in R.values())}.', '',
         '## Primary (Holm over 18): mean latency at the test load vs DeFT(rho*) with the round-robin', '', 'Unit = (mask, seed), mean over uniform and hotspot of the log ratio; 25 units. In brackets after each cell: the v14 effect (no round-robin, for comparison).', '',
         '| size | k | test load uniform / hotspot (x fault-free Lsat) | CI_qlLA_G | FULL_qlLA_G |', '|---|---|---|---|---|']
    for z in SIZES:
        for k in kk:
            c = [next(x for x in prim if (x['size'], x['k'], x['variant']) == (z, k, a)) for a in OURS]
            lu, lh = ch[f'{z}__k{k}__uniform'], ch[f'{z}__k{k}__hotspot']
            L.append(f'| {z} | {k} | {lu["rate"]} ({lu["mult"]}) / {lh["rate"]} ({lh["mult"]}) | ' +
                     ' | '.join(f'{fmt(x, "p_holm")} **{x["verdict"]}** (v14: {v14[(z, k, x["variant"])]:+.1f})' for x in c) + ' |')
    L += ['', f'Supported: {sup} of 18; significant against ours: {against}.', '', '## Secondary: P99 and all methods vs DeFT(rho*) (unadjusted)', '', '| size | k | method | LAT | P99 |', '|---|---|---|---|---|']
    for z in SIZES:
        for k in kk:
            for v in VN[1:]:
                c = [next(x for x in sec if (x['size'], x['k'], x['variant'], x['metric']) == (z, k, v, n)) for n in ('LAT', 'P99')]
                L.append(f'| {z} | {k} | {LABEL.get(v, v)} | {fmt(c[0])} | {fmt(c[1])} |')
    open(os.path.join(OUT, 'faults_summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[:24]))


def k7():
    os.makedirs(OUT, exist_ok=True)
    new = list(csv.DictReader(open(os.path.join(RES, 'app_runs.csv'))))
    old = [r for r in csv.DictReader(open(os.path.join(HERE, 'results_v13_apps', 'app_runs.csv'))) if r['method'] in ('MTR', 'RC') and r['mask'] == '0x0000' and r['seed'] in ('41', '42', '43')]
    idx = {}
    for r in new + old:
        idx[(r['benchmark'], r['method'], r['mask'], int(r['seed']))] = r
    benches = sorted({r['benchmark'] for r in new})
    seeds = (41, 42, 43)

    def geo(xs):
        return math.exp(sum(math.log(x) for x in xs) / len(xs))

    rows = []
    for mask in ('0x0000', '0x1111'):
        for m in ('CI_qlLA_G', 'FULL_qlLA_G', 'MTR', 'RC'):
            if m in ('MTR', 'RC') and mask != '0x0000':
                continue
            for b in benches:
                for col, name in (('latency', 'latency'), ('p99', 'p99'), ('completion_cycles', 'completion')):
                    rt = geo([float(idx[(b, m, mask, s)][col]) / float(idx[(b, 'DeFT', mask, s)][col]) for s in seeds])
                    rows.append(dict(mask=mask, method=m, benchmark=b.split('_')[0], metric=name, ratio=round(rt, 4)))
    write(os.path.join(OUT, 'apps_ratios.csv'), rows)
    L = ['# v19 K7 summary: PARSEC, ratios to DeFT(rho*) with the round-robin (seeds 41-43; descriptive)', '',
         'Single-application traces, 700,000-cycle window. MTR and RC reused from v13 (fault-free), so their traces and injection are the same; the other methods run with -deft_vn_rr 1. Ratio per benchmark is the geometric mean over seeds. Below 1 = lower than DeFT.', '']
    for mask in ('0x0000', '0x1111'):
        ms = ('CI_qlLA_G', 'FULL_qlLA_G', 'MTR', 'RC') if mask == '0x0000' else ('CI_qlLA_G', 'FULL_qlLA_G')
        L += [f'## Mask {mask}', '', '| benchmark | ' + ' | '.join(f'{m}: latency / p99 / completion' for m in ms) + ' |', '|---|' + '---|' * len(ms)]
        get = lambda m, b, n: next(r['ratio'] for r in rows if (r['mask'], r['method'], r['benchmark'], r['metric']) == (mask, m, b, n))  # noqa: E731
        bs = [b.split('_')[0] for b in benches]
        for b in bs:
            L.append(f'| {b} | ' + ' | '.join(f"{get(m, b, 'latency'):.3f} / {get(m, b, 'p99'):.3f} / {get(m, b, 'completion'):.3f}" for m in ms) + ' |')
        L.append('| **geometric mean** | ' + ' | '.join(' / '.join(f"{geo([get(m, b, n) for b in bs]):.3f}" for n in ('latency', 'p99', 'completion')) for m in ms) + ' |')
        L.append('')
    open(os.path.join(OUT, 'apps_summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


if __name__ == '__main__':
    {'k5': k5, 'k6': k6, 'k7': k7}[sys.argv[1]]()
