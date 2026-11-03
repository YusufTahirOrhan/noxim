"""Analysis of v21, following results_v21_fastsel/PREREGISTRATION.md.

Usage: python3 report_v21.py
eval_runs.csv, n_fast.json, tuning_choice.json, area_runs_cut1.csv, timing_runs_cut*.csv, results_v18_area/area_runs.csv, results_v19_vnrr/load_points_rr.json
-> report/primary.csv, secondary.csv, sensitivity.csv, saturation.csv, area.csv, summary.md, latency_load.{png,pdf}
Comparisons whose runs are not complete yet are reported as missing: the design runs in stages.
"""
import csv
import json
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from primary_from_csv import holm, ttest  # noqa: E402
from report_v4 import Data, load_csv, pct  # noqa: E402
import report_v5 as R5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v21_fastsel')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
SEEDS = range(81, 91)
SENS = range(81, 86)
FAST = ['CI_fast', 'CI_fastQL', 'FULL_fast', 'FULL_fastQL']
BASE_FF = ['MTR', 'RC']
BASE_ALL = ['DeFT_Dis', 'DeFT_Ran']
METRICS = ['LAT', 'P99', 'THR']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
LABEL = {'DeFT': 'DeFT(rho*)', 'DeFT_Dis': 'DeFT-Dis', 'DeFT_Ran': 'DeFT-Ran'}
COUNT = {'chip5': 12, 'chip6': 4, 'ipos5': 12, 'ipos6': 4}
NL = chr(10)


def ff(z):
    return [(p, m) for p, m in R5.scen(z) if int(m, 16) == 0]


def write(path, rows):
    if not rows:
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        for x in rows:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})


def fmt(x, key='p'):
    if x is None:
        return 'missing'
    return f'{x["effect_pct"]:+.1f} [{x["ci_low"]:+.1f}, {x["ci_high"]:+.1f}] ({key.replace("_", " ")} {x[key]:.2g})'


def area_section():
    base = {(r['method'], r['rtype'], r['size'], r['form']): float(r['area_um2']) for r in csv.DictReader(open(os.path.join(HERE, 'results_v18_area', 'area_runs.csv')))}
    fast = {(r['method'], r['rtype'], r['size'], r['form']): float(r['area_um2']) for r in csv.DictReader(open(os.path.join(RES, 'area_runs_cut1.csv')))}

    def system(get):
        return sum(COUNT[t] * get(t) for t in COUNT) / sum(COUNT.values())

    def deft(z):
        return system(lambda t: base[('DeFT', t, z, 'S')])

    def ratio(m, z, form):
        return system(lambda t: fast.get((m, t, z, form), fast[(m, t, z, 'S')])) / deft(z)
    rows = []
    L = ['## Area: system-level average router area relative to DeFT (hierarchical, as v18)', '', 'Routers weighted 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL. RTL with the cost register (the design N_fast applies to). Form P: one unit per input port, the form the simulator models. Form S: one unit per router; a head on the link cannot enter stage A when another port holds the unit, which the simulator does not charge.', '',
         '| variant | form P: 2x2 / 3x3 / 4x4 | form S: 2x2 / 3x3 / 4x4 | v18 slow form S, same scope and kind |', '|---|---|---|---|']
    names = {'LBI_fast': ('CI_fast', 'LBI_heur'), 'LBI_fastQL': ('CI_fastQL', 'LBI_ql'), 'LBF_fast': ('FULL_fast', 'LBF_heur'), 'LBF_fastQL': ('FULL_fastQL', 'LBF_ql')}
    for m, (v, old) in names.items():
        p = [ratio(m, z, 'P') for z in SIZES]
        s = [ratio(m, z, 'S') for z in SIZES]
        o = [system(lambda t: base[(old, t, z, 'S')]) / deft(z) for z in SIZES]
        for z, a, b, c in zip(SIZES, p, s, o):
            rows.append(dict(variant=v, size=z, form_P=round(a, 3), form_S=round(b, 3), v18_slow_form_S=round(c, 3)))
        L.append(f'| {v} | ' + ' / '.join(f'{x:.2f}' for x in p) + ' | ' + ' / '.join(f'{x:.2f}' for x in s) + ' | ' + ' / '.join(f'{x:.2f}' for x in o) + ' |')
    write(os.path.join(OUT, 'area.csv'), rows)
    return L + ['']


def main():
    os.makedirs(OUT, exist_ok=True)
    P = json.load(open(os.path.join(HERE, 'results_v19_vnrr', 'load_points_rr.json')))
    nf = json.load(open(os.path.join(RES, 'n_fast.json')))
    ch = json.load(open(os.path.join(RES, 'tuning_choice.json')))

    def ladder(p, m):
        size, pat = p.split('-')
        return P[f'{size}__{pat}__{m}']['eval']
    R = load_csv(os.path.join(RES, 'eval_runs.csv'))
    D = {z: Data(R, R5.scen(z), ladder, SEEDS) for z in SIZES}
    DS = {z: Data(R, R5.scen(z), ladder, SENS) for z in SIZES}

    def test(z, a, b, n, sc, idx=3, data=None):
        xs = (data or D)[z].per_seed(a, b, n, sc, idx)
        if len(xs) < 3:
            return None
        e, lo, hi = pct(xs)
        return dict(size=z, variant=a, reference=b, metric=n if idx == 3 else f'{n}@{MULTS[idx]}', scenarios='fault-free' if sc == ff(z) else 'all', n_seeds=len(xs),
                    effect_pct=round(e, 2), ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs))

    def verdict(x):
        return ('ours better' if x['effect_pct'] < 0 else 'ours worse') if x['p_holm'] < 0.05 else 'n.s.'

    best = {z: {sc: ch[z][sc]['best'] for sc in ('CI', 'FULL')} for z in SIZES}
    prim = []
    for z in SIZES:
        for sc in ('CI', 'FULL'):
            a = best[z][sc]
            for n in ('LAT', 'P99'):
                x = test(z, a, 'DeFT', n, R5.scen(z))
                if x:
                    prim.append(dict(x, family='vs DeFT', scope=sc))
            for b in BASE_FF:
                for n in ('LAT', 'P99'):
                    x = test(z, a, b, n, ff(z))
                    if x:
                        prim.append(dict(x, family='vs baseline', scope=sc))
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(OUT, 'primary.csv'), prim)

    sec = []
    for z in SIZES:
        for v in FAST:
            for n in METRICS:
                sec.append(test(z, v, 'DeFT', n, R5.scen(z)))
            sec.append(test(z, v, 'DeFT', 'LAT', R5.scen(z), idx=0))
            for b in BASE_FF:
                sec.append(test(z, v, b, 'THR', ff(z)))
                sec.append(test(z, v, b, 'LAT', ff(z), idx=0))
            for b in BASE_ALL:
                for n in METRICS:
                    sec.append(test(z, v, b, n, R5.scen(z)))
        for b in BASE_FF:
            for n in METRICS:
                sec.append(test(z, 'DeFT', b, n, ff(z)))
    sec = [x for x in sec if x]
    write(os.path.join(OUT, 'secondary.csv'), sec)

    sens = []
    for z in SIZES:
        for v in FAST:
            for tag, name in ((v, 'N_fast'), (f'{v}-plus1', 'N_fast + 1')):
                for n, idx in (('LAT', 3), ('P99', 3), ('THR', 3), ('LAT', 0)):
                    x = test(z, tag, 'DeFT', n, R5.scen(z), idx, DS)
                    if x:
                        sens.append(dict(x, base=v, delay=name))
        for n, idx in (('LAT', 3), ('P99', 3), ('THR', 3), ('LAT', 0)):
            x = test(z, 'CI_fast-n1', 'DeFT', n, R5.scen(z), idx, DS)
            if x:
                sens.append(dict(x, base='CI_fast', delay='N = 1 (misses timing)'))
            x = test(z, 'FULL_fast-n2', 'DeFT', n, R5.scen(z), idx, DS)
            if x:
                sens.append(dict(x, base='FULL_fast', delay='N = 2 (misses timing)'))
    write(os.path.join(OUT, 'sensitivity.csv'), sens)

    def find(rows, z, a, b, n):
        return next((x for x in rows if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, b, n)), None)

    def saturation(z, v):
        out = []
        sc = ff(z) if v in BASE_FF else R5.scen(z)
        for p, m in sc:
            lad = ladder(p, m)
            ok = []
            for r in lad:
                acc = [R[(v, p, m, r, s)]['accepted'] for s in SEEDS if (v, p, m, r, s) in R]
                ok.append(bool(acc) and sum(acc) / len(acc) >= 0.95 * 8 * r)
            if any((v, p, m, r, s) in R for r in lad for s in SEEDS):
                out.append(dict(size=z, method=v, pattern=p.split('-')[1], mask=m, flagged_at_1_0=not ok[3], own_sat_load=max((MULTS[i] for i in range(len(lad)) if ok[i] and all(ok[:i + 1])), default=0.0)))
        return out
    sat = [x for z in SIZES for v in ['DeFT'] + BASE_FF + BASE_ALL + FAST for x in saturation(z, v)]
    write(os.path.join(OUT, 'saturation.csv'), sat)

    dead = sum(x['dead'] for x in R.values())
    L = ['# v21 summary: DEFT_FAST (seeds 81-90; generated by report_v21.py)', '', f'Runs in `eval_runs.csv`: {len(R)}; dead-end events: {dead}. All VN-based methods with -deft_vn_rr 1. MTR and RC: fault-free scenarios only. Loads: `results_v19_vnrr/load_points_rr.json`.', '',
         '## N_fast and the chosen variants', '', '| variant | N_fast | age of the registered terms, extra cycles | worst router |', '|---|---|---|---|']
    for v in FAST:
        L.append(f'| {v} | {nf[v]["n"]} | {nf[v]["stale"]} | {" ".join(nf[v]["worst_router"][1:3])} |')
    L += ['', '| size | best CI (tuning seeds) | best FULL (tuning seeds) |', '|---|---|---|'] + [f'| {z} | {best[z]["CI"]} | {best[z]["FULL"]} |' for z in SIZES] + ['']
    L += [f'## Primary results (Holm over {len(prim)} of 36): chosen variant vs reference, % change (negative = ours lower)', '', '| size | scope | ours | reference | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for sc in ('CI', 'FULL'):
            a = best[z][sc]
            for b in ['DeFT'] + BASE_FF:
                lat = find(prim, z, a, b, 'LAT')
                p99 = find(prim, z, a, b, 'P99')
                if lat and p99:
                    L.append(f'| {z} | {sc} | {a} | {LABEL.get(b, b)} | {lat["scenarios"]} | {fmt(lat, "p_holm")} **{lat["verdict"]}** | {fmt(p99, "p_holm")} **{p99["verdict"]}** |')
    cnt = lambda fam, vd: sum(1 for x in prim if x['family'] == fam and x['verdict'] == vd)  # noqa: E731
    L += ['', f'vs DeFT: supported {cnt("vs DeFT", "ours better")}; against ours {cnt("vs DeFT", "ours worse")}; n.s. {cnt("vs DeFT", "n.s.")}.',
          f'vs MTR and RC: supported {cnt("vs baseline", "ours better")}; against ours {cnt("vs baseline", "ours worse")}; n.s. {cnt("vs baseline", "n.s.")}.', '',
          '## Secondary: all variants against DeFT(rho*) with the round-robin (unadjusted)', '', '| size | variant | LAT @1.0 Lsat | LAT @0.2 Lsat | P99 @1.0 Lsat | THR |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for v in FAST:
            L.append(f'| {z} | {v} | ' + ' | '.join(fmt(find(sec, z, v, 'DeFT', n)) for n in ('LAT', 'LAT@0.2', 'P99', 'THR')) + ' |')
    L += ['', '## Secondary: against MTR and RC at low load and in throughput, fault-free (unadjusted)', '', '| size | variant | reference | LAT @0.2 Lsat | THR |', '|---|---|---|---|---|']
    for z in SIZES:
        for v in FAST:
            for b in BASE_FF:
                L.append(f'| {z} | {v} | {b} | {fmt(find(sec, z, v, b, "LAT@0.2"))} | {fmt(find(sec, z, v, b, "THR"))} |')
    L += ['', '## Secondary: against DeFT-Dis and DeFT-Ran (unadjusted)', '', '| size | variant | reference | LAT | P99 | THR |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for v in FAST:
            for b in BASE_ALL:
                L.append(f'| {z} | {v} | {LABEL[b]} | ' + ' | '.join(fmt(find(sec, z, v, b, n)) for n in METRICS) + ' |')
    L += ['', '## Secondary: DeFT(rho*) with the round-robin against MTR and RC (unadjusted)', '', '| size | reference | LAT | P99 | THR |', '|---|---|---|---|---|']
    for z in SIZES:
        for b in BASE_FF:
            L.append(f'| {z} | {b} | ' + ' | '.join(fmt(find(sec, z, 'DeFT', b, n)) for n in METRICS) + ' |')
    L += ['', '## Sensitivity: N_fast + 1 against DeFT(rho*), seeds 81-85 (unadjusted)', '', '| size | variant | delay | LAT @1.0 Lsat | LAT @0.2 Lsat | P99 | THR |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for v in FAST:
            for name in ('N_fast', 'N_fast + 1') + (('N = 1 (misses timing)',) if v == 'CI_fast' else ('N = 2 (misses timing)',) if v == 'FULL_fast' else ()):
                g = {x['metric']: x for x in sens if (x['size'], x['base'], x['delay']) == (z, v, name)}
                L.append(f'| {z} | {v} | {name} | ' + ' | '.join(fmt(g.get(n)) for n in ('LAT', 'LAT@0.2', 'P99', 'THR')) + ' |')
    L.append('')
    fl = [x for x in sat if x['flagged_at_1_0']]
    L += ['## Saturates below 1.0 x Lsat', '', '| size | method | scenario | own saturation load (x Lsat) |', '|---|---|---|---|'] + [f'| {x["size"]} | {x["method"]} | {x["pattern"]} {x["mask"]} | {x["own_sat_load"]} |' for x in fl] + ['']
    L += area_section()
    L += ['Figure: `latency_load.png` / `.pdf`.']
    open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)

    series = [('DeFT', '#2a78d6', 'o', '-'), ('MTR', '#eb6834', 's', '-'), ('RC', '#1baf7a', 'D', '-'), ('CI_fast', '#e87ba4', 'v', '-'), ('CI_fastQL', '#e87ba4', 'v', ':'),
              ('FULL_fast', '#008300', 'P', '-'), ('FULL_fastQL', '#008300', 'P', ':')]
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ad', 'axes.linewidth': 0.8, 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.7), sharey=True)
    for ax, z in zip(axes, SIZES):
        p, m = f'{z}-uniform', [mm for pp, mm in R5.scen(z) if pp == f'{z}-uniform' and int(mm, 16) == 0][0]
        lad = ladder(p, m)
        ax.grid(True, color='#e6e5e0', linewidth=0.6)
        ax.set_axisbelow(True)
        for v, col, mk, ls in series:
            if all((v, p, m, r, s) in R for r in lad for s in SEEDS):
                ys = [math.exp(sum(math.log(R[(v, p, m, r, s)]['latency']) for s in SEEDS) / len(SEEDS)) for r in lad]
                ax.plot(lad, ys, color=col, marker=mk, linestyle=ls, linewidth=2, markersize=7, markeredgecolor='white', markeredgewidth=1.0, label=LABEL.get(v, v))
        ax.set_title(f'{z}, uniform', fontsize=9.5, loc='left')
        ax.set_xlabel('injection rate (packets / cycle / node)')
        ax.set_ylim(0, 300)
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel('mean latency (cycles)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=7, frameon=False, fontsize=8.5)
    fig.suptitle('Mean latency against load, uniform traffic, fault-free (geometric mean of seeds 81-90; axis clipped at 300 cycles)', fontsize=10, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT, f'latency_load.{ext}'), dpi=180)
    plt.close(fig)
    print(NL.join(L[:60]))


if __name__ == '__main__':
    main()
