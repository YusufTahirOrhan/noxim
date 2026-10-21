"""Analysis of v9 (confirmatory test of gamma = 2 against plain DeFT(rho*)), following results_v9/PREREGISTRATION.md.

Inputs (CSV only): results_v9/eval_runs.csv (make_eval_csv.py results_v9 eval), results_v9/seed_choice.json,
results_v5/load_points.json.
Outputs (results_v9/report/): primary.csv, confirmation.csv, summary.md, effect_vs_size.png
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
R9 = os.path.join(HERE, 'results_v9')
SIZES = ['2x2', '3x3', '4x4']
G = ['CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
METRICS = ['LAT', 'P99', 'THR']
CHIPLETS = {'2x2': 4, '3x3': 9, '4x4': 16}
COL = {'CI_heurLA_G': '#4a3aa7', 'CI_qlLA_G': '#1baf7a', 'FULL_qlLA_G': '#2a78d6'}
# v8 values against DeFT(rho*) (results_v8/report/summary.md, seeds 31-40); P = predicted (pre-registered)
V8 = {('3x3', 'CI_heurLA_G', 'LAT'): (-16.70, 'P'), ('3x3', 'CI_heurLA_G', 'P99'): (-37.13, 'P'),
      ('3x3', 'CI_heurLA_G', 'THR'): (2.42, 'P'), ('3x3', 'CI_qlLA_G', 'LAT'): (-20.82, 'P'),
      ('3x3', 'CI_qlLA_G', 'P99'): (-45.04, 'P'), ('3x3', 'CI_qlLA_G', 'THR'): (3.15, 'P'),
      ('3x3', 'FULL_qlLA_G', 'LAT'): (-28.66, 'P'), ('3x3', 'FULL_qlLA_G', 'P99'): (-53.92, 'P'),
      ('3x3', 'FULL_qlLA_G', 'THR'): (-0.35, '-'),
      ('4x4', 'CI_heurLA_G', 'LAT'): (-24.42, 'P'), ('4x4', 'CI_heurLA_G', 'P99'): (-48.99, 'P'),
      ('4x4', 'CI_heurLA_G', 'THR'): (-0.18, '-'), ('4x4', 'CI_qlLA_G', 'LAT'): (-26.31, 'P'),
      ('4x4', 'CI_qlLA_G', 'P99'): (-52.69, 'P'), ('4x4', 'CI_qlLA_G', 'THR'): (2.84, 'P'),
      ('4x4', 'FULL_qlLA_G', 'LAT'): (-39.14, 'P'), ('4x4', 'FULL_qlLA_G', 'P99'): (-63.00, 'P'),
      ('4x4', 'FULL_qlLA_G', 'THR'): (5.00, 'P')}


def main():
    choice = json.load(open(os.path.join(R9, 'seed_choice.json')))['seeds']
    seeds = range(41, 51) if choice == 'all' else range(41, 46)
    out = os.path.join(R9, 'report')
    os.makedirs(out, exist_ok=True)
    R = {k: v for k, v in load_csv(os.path.join(R9, 'eval_runs.csv')).items() if k[4] in seeds}
    D = {z: Data(R, R5.scen(z), R5.ladder, seeds) for z in SIZES}
    expected = sum(len(R5.ladder(p, m)) for z in SIZES for p, m in R5.scen(z)) * 5 * len(seeds)
    missing = [(v, p, m, r, s) for z in SIZES for p, m in R5.scen(z) for r in R5.ladder(p, m) for s in seeds
               for v in ['DeFT', 'DeFT_tm'] + G if (v, p, m, r, s) not in R]
    dead = sum(x['dead'] for x in R.values())

    prim = []
    for z in SIZES:
        for a in G:
            for n in METRICS:
                xs = D[z].per_seed(a, 'DeFT', n)
                e, lo, hi = pct(xs)
                prim.append(dict(size=z, variant=a, reference='DeFT', metric=n, n_seeds=len(xs), effect_pct=round(e, 2),
                                 ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs),
                                 capped_cells=D[z].capped(a, 'DeFT') if n == 'THR' else 0))
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
        x['verdict'] = ('better' if good else 'worse') if q < 0.05 else 'n.s.'
    with open(os.path.join(out, 'primary.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(prim[0]), lineterminator='\n')
        w.writeheader()
        for x in prim:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})

    conf = []
    for x in prim:
        k = (x['size'], x['variant'], x['metric'])
        v8, kind = V8.get(k, (None, 'new'))
        if kind == 'P':
            ok = x['p_holm'] < 0.05 and (x['effect_pct'] > 0) == (v8 > 0)
            status = 'confirmed' if ok else 'not confirmed'
        else:
            status = 'no prediction'
        conf.append(dict(size=x['size'], variant=x['variant'], metric=x['metric'],
                         v8_effect_pct='' if v8 is None else v8, v9_effect_pct=x['effect_pct'],
                         v9_ci=f'[{x["ci_low"]:+.2f}, {x["ci_high"]:+.2f}]', p_holm=f'{x["p_holm"]:.3g}',
                         v9_verdict=x['verdict'], status=status))
    with open(os.path.join(out, 'confirmation.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(conf[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(conf)
    n_pred = sum(c['status'] != 'no prediction' for c in conf)
    n_conf = sum(c['status'] == 'confirmed' for c in conf)

    sl = f'{min(seeds)}-{max(seeds)}'

    def row(a, b, z, sc=None):
        cells = []
        for n in METRICS:
            e, lo, hi = pct(D[z].per_seed(a, b, n, sc))
            cells.append(f'{e:+.2f} [{lo:+.2f}, {hi:+.2f}]')
        return f'| {z} | {a} vs {b} | ' + ' | '.join(cells) + ' |'

    L = [f'# v9 summary (seeds {sl}; generated by report_v9.py)', '',
         f'Runs: {len(R)} of {expected}; missing: {len(missing)}; dead-end events: {dead}.', '',
         '## Primary results (pre-registered; Holm over 27 tests; reference DeFT(rho*))', '',
         f'Effect: mean over the scenarios of the size of the per-seed log ratio, % change, 95 % CI over seeds {sl}.', '',
         '| size | variant | metric | effect % [95 % CI] | p (Holm) | verdict | THR capped cells |',
         '|---|---|---|---|---|---|---|']
    for x in prim:
        L.append(f'| {x["size"]} | {x["variant"]} | {x["metric"]} | {x["effect_pct"]:+.2f} [{x["ci_low"]:+.2f}, '
                 f'{x["ci_high"]:+.2f}] | {x["p_holm"]:.3g} | **{x["verdict"]}** | '
                 f'{x["capped_cells"] if x["metric"] == "THR" else "-"} |')
    L += ['', f'## Confirmation of the v8 results ({n_conf} of {n_pred} predicted results confirmed)', '',
          '| size | variant | metric | v8 (seeds 31-40) | v9 | p (Holm) | status |', '|---|---|---|---|---|---|---|']
    for c in conf:
        v8 = f'{c["v8_effect_pct"]:+.2f}' if c['v8_effect_pct'] != '' else 'not run'
        L.append(f'| {c["size"]} | {c["variant"]} | {c["metric"]} | {v8} | {c["v9_effect_pct"]:+.2f} {c["v9_ci"]} | '
                 f'{c["p_holm"]} | **{c["status"]}** |')
    L += ['', '## Secondary: against DeFT_tm(rho*) (unadjusted)', '', '| size | comparison | LAT | P99 | THR |',
          '|---|---|---|---|---|']
    L += [row(a, 'DeFT_tm', z) for z in SIZES for a in G]
    L += ['', '## Secondary: DeFT_tm(rho*) vs DeFT(rho*) (unadjusted)', '', '| size | comparison | LAT | P99 | THR |',
          '|---|---|---|---|---|']
    L += [row('DeFT_tm', 'DeFT', z) for z in SIZES]
    L += ['', '## Secondary: saturation throughput without chipperm (unadjusted)', '',
          '| size | variant | vs DeFT(rho*) | vs DeFT_tm(rho*) |', '|---|---|---|---|']
    for z in SIZES:
        sc = [s for s in R5.scen(z) if 'chipperm' not in s[0]]
        for a in G + ['DeFT_tm']:
            e, lo, hi = pct(D[z].per_seed(a, 'DeFT', 'THR', sc))
            if a == 'DeFT_tm':
                L.append(f'| {z} | DeFT_tm | {e:+.2f} [{lo:+.2f}, {hi:+.2f}] | - |')
                continue
            e2, lo2, hi2 = pct(D[z].per_seed(a, 'DeFT_tm', 'THR', sc))
            L.append(f'| {z} | {a} | {e:+.2f} [{lo:+.2f}, {hi:+.2f}] | {e2:+.2f} [{lo2:+.2f}, {hi2:+.2f}] |')
    L.append('')
    for n in METRICS:
        L += [f'## Secondary: per-scenario {n} (unadjusted; `°` = CI excludes 0; `≥` = capped)', '']
        for z in SIZES:
            sc = R5.scen(z)
            L += [f'**{z}**', '', '| comparison | ' + ' | '.join(f'{p.split("-")[1]} {m}' for p, m in sc) + ' |',
                  '|---|' + '---|' * len(sc)]
            for a, b in [(g, 'DeFT') for g in G] + [(g, 'DeFT_tm') for g in G] + [('DeFT_tm', 'DeFT')]:
                cells = []
                for p, m in sc:
                    e, lo, hi = pct(D[z].per_seed(a, b, n, [(p, m)]))
                    capped = n == 'THR' and any(D[z].thr(a, p, m, s)[1] or D[z].thr(b, p, m, s)[1] for s in seeds)
                    cells.append(f'{"≥" if capped else ""}{e:+.1f}{"°" if hi < 0 or lo > 0 else ""}')
                L.append(f'| {a} vs {b} | ' + ' | '.join(cells) + ' |')
            L.append('')
    L += ['## Secondary: VL usage imbalance of the variants (max/mean over all functional VLs) at 1.0 x Lsat', '',
          'DEFT routing does not count VL use, so no reference values (no proxy runs in v9).', '']
    for z in SIZES:
        sc = R5.scen(z)
        L += [f'**{z}**', '', '| variant | ' + ' | '.join(f'{p.split("-")[1]} {m}' for p, m in sc) + ' |',
              '|---|' + '---|' * len(sc)]
        for v in G:
            cells = []
            for p, m in sc:
                r = R5.ladder(p, m)[3]
                xs = [R[(v, p, m, r, s)]['imb'] for s in seeds if (v, p, m, r, s) in R]
                xs = [x for x in xs if not math.isnan(x)]
                cells.append(f'{sum(xs) / len(xs):.2f}' if xs else 'n/a')
            L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
        L.append('')
    if missing:
        L += ['## Missing runs', ''] + [f'- {m}' for m in missing] + ['']
    open(os.path.join(out, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    titles = {'LAT': 'Mean latency at 1.0 x Lsat (lower is better)', 'P99': 'p99 latency at 1.0 x Lsat (lower is better)',
              'THR': 'Saturation throughput (higher is better)'}
    for ax, n in zip(axes, METRICS):
        for j, a in enumerate(G):
            pts = [x for x in prim if x['variant'] == a and x['metric'] == n]
            xs = [CHIPLETS[x['size']] + (j - 1) * 0.35 for x in pts]
            ax.errorbar(xs, [x['effect_pct'] for x in pts],
                        yerr=[[x['effect_pct'] - x['ci_low'] for x in pts], [x['ci_high'] - x['effect_pct'] for x in pts]],
                        fmt='o-', color=COL[a], capsize=3, ms=6, lw=1.6, label=f'{a} vs DeFT(rho*)')
        ax.axhline(0, color='#52514e', lw=0.8)
        ax.set_xticks([4, 9, 16])
        ax.set_xticklabels(['4 (2x2)', '9 (3x3)', '16 (4x4)'])
        ax.set_xlabel('chiplets')
        ax.set_ylabel('% change vs DeFT(rho*), mean over scenarios')
        ax.set_title(titles[n], fontsize=10)
        ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=3, frameon=False, fontsize=9)
    fig.suptitle(f'v9 confirmatory test, gamma = 2, seeds {sl}: effect vs size against plain DeFT(rho*), 95 % CI over seeds',
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.savefig(os.path.join(out, 'effect_vs_size.png'), dpi=130)
    plt.close(fig)
    print(f'runs {len(R)}/{expected}, missing {len(missing)}, dead {dead}; confirmed {n_conf}/{n_pred}')
    for c in conf:
        print(c['size'], c['variant'], c['metric'], 'v8', c['v8_effect_pct'], 'v9', c['v9_effect_pct'], c['v9_ci'],
              c['p_holm'], c['status'])


if __name__ == '__main__':
    main()
