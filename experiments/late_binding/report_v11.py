"""Analysis of v11 (Part C, fault-rate sweep), following results_v11/PREREGISTRATION.md.

Input: results_v11/eval_runs.csv (make_eval_csv.py results_v11 eval), results_v11/masks.json, mask_count.json.
Outputs (results_v11/report/): primary.csv, secondary.csv, summary.md, fault_sweep.{png,pdf}
"""
import csv
import json
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from primary_from_csv import ci, holm, ttest  # noqa: E402
from report_v4 import load_csv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R11 = os.path.join(HERE, 'results_v11')
LP5 = json.load(open(os.path.join(HERE, 'results_v5', 'load_points.json')))
SIZES = ['2x2', '3x3', '4x4']
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
KS = [1, 2, 3]
PATTERNS = ['uniform', 'hotspot']
SEEDS = (51, 52)
METHODS = ['DeFT', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
OURS = ['CI_qlLA_G', 'FULL_qlLA_G']
LABEL = {'DeFT': 'DeFT(rho*)', 'DeFT_Dis': 'DeFT-Dis', 'DeFT_Ran': 'DeFT-Ran', 'XY_SP': 'XY-SP'}


def ladder(size, p):
    return LP5[f'{size}__{p}__{FREE[size]}']['eval']


class Sweep:
    def __init__(self):
        self.R = load_csv(os.path.join(R11, 'eval_runs.csv'))
        self.masks = json.load(open(os.path.join(R11, 'masks.json')))
        n = json.load(open(os.path.join(R11, 'mask_count.json')))['n_masks']
        self.masks = {k: v[:n] for k, v in self.masks.items()}

    def metric(self, v, size, p, m, s, name):
        lad = ladder(size, p)
        if name == 'THR':
            acc = [(self.R[(v, f'{size}-{p}', m, r, s)]['accepted'], r) for r in lad]
            return max(acc)[0]
        x = self.R[(v, f'{size}-{p}', m, lad[3], s)]
        return x['p99'] if name == 'P99' else x['latency']

    def capped(self, v, size, p, m, s):
        lad = ladder(size, p)
        acc = [(self.R[(v, f'{size}-{p}', m, r, s)]['accepted'], r) for r in lad]
        best, at = max(acc)
        return at == lad[-1] and best >= 0.95 * 8 * lad[-1]

    def units(self, a, b, size, k, name):
        out = []
        for m in self.masks[f'{size}__k{k}']:
            for s in SEEDS:
                try:
                    rs = [math.log(self.metric(a, size, p, m, s, name) / self.metric(b, size, p, m, s, name))
                          for p in PATTERNS]
                except KeyError:
                    continue
                out.append(sum(rs) / len(rs))
        return out

    def geo(self, v, size, k, name):
        xs = []
        for m in self.masks[f'{size}__k{k}']:
            for s in SEEDS:
                for p in PATTERNS:
                    try:
                        xs.append(math.log(self.metric(v, size, p, m, s, name)))
                    except KeyError:
                        pass
        return math.exp(sum(xs) / len(xs)) if xs else float('nan')


def effect(xs):
    mu, h = ci(xs)
    return 100 * (math.exp(mu) - 1), 100 * (math.exp(mu - h) - 1), 100 * (math.exp(mu + h) - 1)


def row(S, a, b, size, k, name):
    xs = S.units(a, b, size, k, name)
    e, lo, hi = effect(xs)
    return dict(size=size, k=k, variant=a, reference=b, metric=name, n_units=len(xs), effect_pct=round(e, 2),
                ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs))


def main():
    out = os.path.join(R11, 'report')
    os.makedirs(out, exist_ok=True)
    S = Sweep()
    nm = len(next(iter(S.masks.values())))
    expected = len(SIZES) * len(KS) * nm * len(PATTERNS) * len(METHODS) * 7 * len(SEEDS)
    present = [(v, f'{z}-{p}', m, r, s) for z in SIZES for k in KS for m in S.masks[f'{z}__k{k}'] for p in PATTERNS
               for r in ladder(z, p) for v in METHODS for s in SEEDS]
    missing = [x for x in present if x not in S.R]
    dead = sum(x['dead'] for x in S.R.values())
    prim = [row(S, a, 'DeFT', z, k, 'LAT') for z in SIZES for k in KS for a in OURS]
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = ('ours better' if x['effect_pct'] < 0 else 'ours worse') if q < 0.05 else 'n.s.'
    sec = [row(S, a, 'DeFT', z, k, n) for z in SIZES for k in KS for a in OURS for n in ('P99', 'THR')]
    sec += [row(S, a, b, z, k, n) for z in SIZES for k in KS for a in OURS for b in ('DeFT_Dis', 'DeFT_Ran')
            for n in ('LAT', 'P99', 'THR')]
    allm = [row(S, v, 'DeFT', z, k, n) for z in SIZES for k in KS for v in METHODS if v != 'DeFT'
            for n in ('LAT', 'P99', 'THR')]
    for path, rows in (('primary.csv', prim), ('secondary.csv', sec + allm)):
        with open(os.path.join(out, path), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
            w.writeheader()
            for x in rows:
                w.writerow({kk: (f'{v:.4g}' if kk in ('p', 'p_holm') else v) for kk, v in x.items()})

    def fmt(x, key='p'):
        return f'{x["effect_pct"]:+.1f} [{x["ci_low"]:+.1f}, {x["ci_high"]:+.1f}] ({key.replace("_", " ")} {x[key]:.2g})'

    sup = sum(x['verdict'] == 'ours better' for x in prim)
    L = [f'# v11 summary: fault-rate sweep (seeds 51-52, {nm} masks per (size, k); generated by report_v11.py)', '',
         f'Runs: {len(present) - len(missing)} of {expected}; missing {len(missing)}; dead-end events {dead}.', '',
         '## Primary (Holm over 18): LAT at 1.0 x (fault-free) Lsat vs DeFT(rho*), pooled over masks, seeds, patterns',
         '', '| size | k | CI_qlLA_G | FULL_qlLA_G |', '|---|---|---|---|']
    for z in SIZES:
        for k in KS:
            c = [next(x for x in prim if (x['size'], x['k'], x['variant']) == (z, k, a)) for a in OURS]
            L.append(f'| {z} | {k} | ' + ' | '.join(f'{fmt(x, "p_holm")} **{x["verdict"]}**' for x in c) + ' |')
    L += ['', f'Supported: {sup} of 18.', '',
          '## Secondary: P99 and THR vs DeFT(rho*) (unadjusted)', '',
          '| size | k | variant | P99 | THR |', '|---|---|---|---|---|']
    for z in SIZES:
        for k in KS:
            for a in OURS:
                c = [next(x for x in sec if (x['size'], x['k'], x['variant'], x['reference'], x['metric']) ==
                          (z, k, a, 'DeFT', n)) for n in ('P99', 'THR')]
                L.append(f'| {z} | {k} | {a} | {fmt(c[0])} | {fmt(c[1])} |')
    L += ['', '## Secondary: vs DeFT-Dis and DeFT-Ran (unadjusted)', '',
          '| size | k | variant | reference | LAT | P99 | THR |', '|---|---|---|---|---|---|---|']
    for z in SIZES:
        for k in KS:
            for a in OURS:
                for b in ('DeFT_Dis', 'DeFT_Ran'):
                    c = [next(x for x in sec if (x['size'], x['k'], x['variant'], x['reference'], x['metric']) ==
                              (z, k, a, b, n)) for n in ('LAT', 'P99', 'THR')]
                    L.append(f'| {z} | {k} | {a} | {LABEL[b]} | ' + ' | '.join(fmt(x) for x in c) + ' |')
    L += ['', '## All methods: geometric mean over masks, seeds and patterns (LAT, P99 cycles at 1.0 x Lsat; THR '
          'flits/cycle/IP)', '']
    for z in SIZES:
        L += [f'**{z}**', '', '| method | ' + ' | '.join(f'k={k} LAT | k={k} P99 | k={k} THR' for k in KS) + ' |',
              '|---|' + '---|' * (3 * len(KS))]
        for v in METHODS:
            cells = []
            for k in KS:
                cells += [f'{S.geo(v, z, k, "LAT"):.1f}', f'{S.geo(v, z, k, "P99"):.0f}', f'{S.geo(v, z, k, "THR"):.4f}']
            L.append(f'| {LABEL.get(v, v)} | ' + ' | '.join(cells) + ' |')
        L.append('')
    # saturation flags at the 4th load
    L += ['## Saturation flags: cells (mask x seed x pattern) where accepted < 95 % of offered at 1.0 x Lsat', '',
          '| size | k | ' + ' | '.join(LABEL.get(v, v) for v in METHODS) + ' |', '|---|---|' + '---|' * len(METHODS)]
    for z in SIZES:
        for k in KS:
            cells = []
            for v in METHODS:
                n = t = 0
                for m in S.masks[f'{z}__k{k}']:
                    for s in SEEDS:
                        for p in PATTERNS:
                            r = ladder(z, p)[3]
                            x = S.R.get((v, f'{z}-{p}', m, r, s))
                            if x:
                                t += 1
                                n += x['accepted'] < 0.95 * 8 * r
                cells.append(f'{n}/{t}')
            L.append(f'| {z} | {k} | ' + ' | '.join(cells) + ' |')
    if missing:
        L += ['', '## Missing runs', ''] + [f'- {m}' for m in missing[:100]]
    open(os.path.join(out, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')

    col = {'DeFT': '#52514e', 'DeFT_Dis': '#8e8d87', 'DeFT_Ran': '#b9b7af', 'XY_SP': '#6b5b95', 'DeFT_OE_G': '#e0a800',
           'CI_heurLA_G': '#4a3aa7', 'CI_qlLA_G': '#1baf7a', 'FULL_qlLA_G': '#2a78d6'}
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
    for j, z in enumerate(SIZES):
        for i, n in enumerate(('LAT', 'THR')):
            ax = axes[i][j]
            for v in METHODS:
                ys = [S.geo(v, z, k, n) for k in KS]
                ax.plot(KS, ys, marker='o', color=col[v], lw=2.2 if v in OURS else 1.2,
                        ls='-' if v in OURS or v == 'DeFT' else '--', label=LABEL.get(v, v))
            ax.set_xticks(KS)
            ax.set_xlabel('faulty VLs per chiplet (k)')
            ax.set_ylabel('mean latency at 1.0 x Lsat (cycles)' if n == 'LAT' else 'saturation throughput (flits/cycle/IP)')
            if n == 'LAT':
                ax.set_yscale('log')
            ax.set_title(f'{z}: {"latency" if n == "LAT" else "saturation throughput"}', fontsize=10)
            ax.grid(True, color='#e6e5e1', lw=0.6)
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
    h, lab = axes[0][0].get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=8, frameon=False, fontsize=8)
    fig.suptitle(f'Fault-rate sweep: k faulty VLs in every chiplet; geometric mean over {nm} masks x 2 seeds x '
                 '{uniform, hotspot}', fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(out, f'fault_sweep.{ext}'), dpi=125)
    plt.close(fig)
    print(f'runs {len(present) - len(missing)}/{expected}, missing {len(missing)}, dead {dead}; supported {sup}/18')
    for x in prim:
        print(x['size'], x['k'], x['variant'], x['effect_pct'], x['ci_low'], x['ci_high'], f'{x["p_holm"]:.3g}',
              x['verdict'])


if __name__ == '__main__':
    main()
