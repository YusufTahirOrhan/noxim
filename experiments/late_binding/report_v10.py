"""Analysis of v10 Part B (comparison with the baselines), following results_v10/PREREGISTRATION.md.

Inputs (CSV only): results_v10/eval_runs.csv (new methods; make_eval_csv.py results_v10 eval), results_v9/eval_runs.csv
(DeFT(rho*), CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G; reused), results_v5/load_points.json.
Outputs (results_v10/report/): primary.csv, ablation.csv, secondary.csv, saturation.csv, summary.md,
effects_vs_deft.{png,pdf}
"""
import csv
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from primary_from_csv import holm, ttest  # noqa: E402
from report_v4 import Data, load_csv, pct  # noqa: E402
import report_v5 as R5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.join(HERE, 'results_v10')
SIZES = ['2x2', '3x3', '4x4']
SEEDS = range(41, 51)
OURS = ['CI_qlLA_G', 'FULL_qlLA_G']
BASE_FF = ['MTR', 'RC']                 # fault-free scenarios only
BASE_ALL = ['DeFT_Dis', 'DeFT_Ran']
ALL_METHODS = ['DeFT', 'MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G',
               'FULL_qlLA_G']
NEW = ['MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G']
METRICS = ['LAT', 'P99', 'THR']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
LABEL = {'DeFT': 'DeFT(rho*)', 'DeFT_Dis': 'DeFT-Dis', 'DeFT_Ran': 'DeFT-Ran', 'XY_SP': 'XY-SP'}


def ff(z):
    return [(p, m) for p, m in R5.scen(z) if int(m, 16) == 0]


def scen_for(z, *methods):
    return ff(z) if any(m in ('MTR', 'RC') for m in methods) else R5.scen(z)


def load():
    R = {k: v for k, v in load_csv(os.path.join(HERE, 'results_v9', 'eval_runs.csv')).items()
         if k[0] in ('DeFT', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G') and k[4] in SEEDS}
    R.update({k: v for k, v in load_csv(os.path.join(R10, 'eval_runs.csv')).items() if k[4] in SEEDS})
    return R


def test(D, z, a, b, n, sc):
    xs = D[z].per_seed(a, b, n, sc)
    e, lo, hi = pct(xs)
    return dict(size=z, variant=a, reference=b, metric=n, scenarios='fault-free' if sc == ff(z) else 'all',
                n_seeds=len(xs), effect_pct=round(e, 2), ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs))


def write(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        for x in rows:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})


def verdict(x, holm_key='p_holm'):
    q = x[holm_key]
    good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
    return (('ours better' if good else 'ours worse') if q < 0.05 else 'n.s.')


def saturation(R, z, v):
    """Per scenario: flagged if accepted at 1.0 x Lsat < 95 % of offered (mean over seeds); own saturation load =
    largest sweep load with accepted >= 95 % of offered."""
    out = []
    for p, m in scen_for(z, v):
        lad = R5.ladder(p, m)
        ok = []
        for i, r in enumerate(lad):
            acc = [R[(v, p, m, r, s)]['accepted'] for s in SEEDS if (v, p, m, r, s) in R]
            ok.append(bool(acc) and sum(acc) / len(acc) >= 0.95 * 8 * r)
        own = max((MULTS[i] for i in range(len(lad)) if ok[i] and all(ok[:i + 1])), default=0.0)
        out.append(dict(size=z, method=v, pattern=p.split('-')[1], mask=m, flagged_at_1_0=not ok[3], own_sat_load=own))
    return out


def main():
    out = os.path.join(R10, 'report')
    os.makedirs(out, exist_ok=True)
    R = load()
    D = {z: Data(R, R5.scen(z), R5.ladder, SEEDS) for z in SIZES}
    expected = sum(len(R5.ladder(p, m)) for z in SIZES for v in NEW for p, m in scen_for(z, v)) * len(SEEDS)
    n_new = sum(1 for k in R if k[0] in NEW)
    dead = sum(x['dead'] for k, x in R.items() if k[0] in NEW)
    missing = [(v, p, m, r, s) for z in SIZES for v in NEW for p, m in scen_for(z, v) for r in R5.ladder(p, m)
               for s in SEEDS if (v, p, m, r, s) not in R]

    prim = [test(D, z, a, b, n, scen_for(z, b)) for z in SIZES for a in OURS for b in BASE_FF + BASE_ALL
            for n in ('LAT', 'P99')]
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(out, 'primary.csv'), prim)
    abl = [test(D, z, 'FULL_qlLA_G', 'DeFT_OE_G', n, R5.scen(z)) for z in SIZES for n in ('LAT', 'P99')]
    for x, q in zip(abl, holm([x['p'] for x in abl])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    write(os.path.join(out, 'ablation.csv'), abl)
    sec = [test(D, z, a, b, 'THR', scen_for(z, b)) for z in SIZES for a in OURS for b in BASE_FF + BASE_ALL]
    sec += [test(D, z, 'FULL_qlLA_G', 'DeFT_OE_G', 'THR', R5.scen(z)) for z in SIZES]
    sec += [test(D, z, a, 'XY_SP', n, R5.scen(z)) for z in SIZES for a in OURS for n in METRICS]
    sec += [test(D, z, b, 'DeFT', n, scen_for(z, b)) for z in SIZES for b in NEW for n in METRICS]
    write(os.path.join(out, 'secondary.csv'), sec)
    sat = [x for z in SIZES for v in ALL_METHODS for x in saturation(R, z, v)]
    write(os.path.join(out, 'saturation.csv'), sat)
    flagged = {(x['size'], x['method']) for x in sat if x['flagged_at_1_0']}

    def fmt(x, key='p_holm'):
        return (f'{x["effect_pct"]:+.1f} [{x["ci_low"]:+.1f}, {x["ci_high"]:+.1f}] '
                f'({key.replace("_", " ")} {x[key]:.2g})')

    L = ['# v10 Part B summary: comparison with the baselines (seeds 41-50; generated by report_v10.py)', '',
         f'New runs: {n_new} of {expected}; missing: {len(missing)}; dead-end events: {dead}. DeFT(rho*), CI_heurLA_G, '
         'CI_qlLA_G, FULL_qlLA_G reused from results_v9/eval_runs.csv. MTR and RC: fault-free scenarios only (and every '
         'comparison with them uses those scenarios).', '',
         '## Primary results (Holm over 48): our variant vs baseline, % change (negative = ours lower)', '',
         '| size | ours | baseline | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat |', '|---|---|---|---|---|---|']
    for z in SIZES:
        for a in OURS:
            for b in BASE_FF + BASE_ALL:
                lat = next(x for x in prim if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, b, 'LAT'))
                p99 = next(x for x in prim if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, b, 'P99'))
                L.append(f'| {z} | {a} | {LABEL.get(b, b)} | {lat["scenarios"]} | {fmt(lat)} **{lat["verdict"]}** | '
                         f'{fmt(p99)} **{p99["verdict"]}** |')
    sup = sum(1 for x in prim if x['verdict'] == 'ours better')
    against = sum(1 for x in prim if x['verdict'] == 'ours worse')
    L += ['', f'Supported (significant, ours lower): {sup} of 48; significant against ours: {against}; n.s.: '
          f'{48 - sup - against}.', '',
          '## Ablation (Holm over 6): FULL_qlLA_G vs DeFT_OE_G (late binding vs fixed LUT pair, same selection)', '',
          '| size | LAT | P99 | THR (secondary, unadjusted) |', '|---|---|---|---|']
    for z in SIZES:
        lat = next(x for x in abl if (x['size'], x['metric']) == (z, 'LAT'))
        p99 = next(x for x in abl if (x['size'], x['metric']) == (z, 'P99'))
        thr = next(x for x in sec if (x['size'], x['variant'], x['reference'], x['metric']) ==
                   (z, 'FULL_qlLA_G', 'DeFT_OE_G', 'THR'))
        L.append(f'| {z} | {fmt(lat)} **{lat["verdict"]}** | {fmt(p99)} **{p99["verdict"]}** | {fmt(thr, "p")} |')
    L += ['', '## Secondary: saturation throughput of our variants vs the baselines (unadjusted)', '',
          '| size | ours | baseline | THR |', '|---|---|---|---|']
    for z in SIZES:
        for a in OURS:
            for b in BASE_FF + BASE_ALL:
                x = next(x for x in sec if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, b, 'THR'))
                L.append(f'| {z} | {a} | {LABEL.get(b, b)} | {fmt(x, "p")} |')
    L += ['', '## Secondary: our variants vs XY-SP (unadjusted)', '', '| size | ours | LAT | P99 | THR |',
          '|---|---|---|---|---|']
    for z in SIZES:
        for a in OURS:
            c = [next(x for x in sec if (x['size'], x['variant'], x['reference'], x['metric']) == (z, a, 'XY_SP', n))
                 for n in METRICS]
            L.append(f'| {z} | {a} | ' + ' | '.join(fmt(x, 'p') for x in c) + ' |')
    L += ['']
    for z in SIZES:
        L += [f'## {z}: all methods against DeFT(rho*) (effect %, 95 % CI, unadjusted p; MTR and RC over the fault-free '
              'scenarios)', '',
              '| method | scenarios | LAT @1.0 Lsat | P99 @1.0 Lsat | THR | saturates below 1.0 x Lsat in |', '|---|---|---|---|---|---|']
        for v in ALL_METHODS:
            if v == 'DeFT':
                cells = ['reference'] * 3
                scn = 'all'
            else:
                cells = []
                for n in METRICS:
                    x = test(D, z, v, 'DeFT', n, scen_for(z, v))
                    cells.append(fmt(x, 'p'))
                scn = 'fault-free' if v in BASE_FF else 'all'
            fl = [f'{x["pattern"]} {x["mask"]} (own sat. {x["own_sat_load"]} x Lsat)' for x in sat
                  if x['size'] == z and x['method'] == v and x['flagged_at_1_0']]
            L.append(f'| {LABEL.get(v, v)} | {scn} | ' + ' | '.join(cells) + f' | {"; ".join(fl) if fl else "-"} |')
        L.append('')
    if missing:
        L += ['## Missing runs', ''] + [f'- {m}' for m in missing[:100]] + ['']
    open(os.path.join(out, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')

    # figure: effects against DeFT(rho*) per size and metric
    order = [v for v in ALL_METHODS if v != 'DeFT']
    col = {'MTR': '#c0392b', 'RC': '#eb6834', 'DeFT_Dis': '#8e8d87', 'DeFT_Ran': '#b9b7af', 'XY_SP': '#6b5b95',
           'DeFT_OE_G': '#e0a800', 'CI_heurLA_G': '#4a3aa7', 'CI_qlLA_G': '#1baf7a', 'FULL_qlLA_G': '#2a78d6'}
    fig, axes = plt.subplots(3, 3, figsize=(15, 11))
    for i, z in enumerate(SIZES):
        for j, n in enumerate(METRICS):
            ax = axes[i][j]
            vals = []
            for v in order:
                x = test(D, z, v, 'DeFT', n, scen_for(z, v))
                vals.append(x)
            ys = [x['effect_pct'] for x in vals]
            ax.bar(range(len(order)), ys, color=[col[v] for v in order],
                   yerr=[[x['effect_pct'] - x['ci_low'] for x in vals], [x['ci_high'] - x['effect_pct'] for x in vals]],
                   capsize=2)
            ax.axhline(0, color='#52514e', lw=0.8)
            ax.set_xticks(range(len(order)))
            ax.set_xticklabels([LABEL.get(v, v) + ('*' if v in BASE_FF else '') for v in order], rotation=45,
                               ha='right', fontsize=8)
            ax.set_title(f'{z}: {n} vs DeFT(rho*)', fontsize=10)
            if any(abs(y) > 300 for y in ys):
                ax.set_yscale('symlog', linthresh=50)
            ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
    fig.suptitle('% change against DeFT(rho*), mean over scenarios, 95 % CI over seeds 41-50 (* fault-free scenarios '
                 'only). LAT/P99: lower is better; THR: higher is better.', fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(out, f'effects_vs_deft.{ext}'), dpi=120)
    plt.close(fig)
    print(f'new runs {n_new}/{expected}, missing {len(missing)}, dead {dead}; primary supported {sup}/48, against {against}')
    for x in prim + abl:
        print(x['size'], x['variant'], 'vs', x['reference'], x['metric'], x['effect_pct'], x['ci_low'], x['ci_high'],
              f'{x["p_holm"]:.3g}', x['verdict'])


if __name__ == '__main__':
    main()
