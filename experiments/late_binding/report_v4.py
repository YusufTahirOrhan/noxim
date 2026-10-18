"""Analysis of the v4 larger-system replication (results_v4/PREREGISTRATION.md).

Inputs (CSV only): results_v4/eval_runs.csv (make_eval_csv.py results_v4 eval; DeFT_tm VL counts from
the evalvl proxy at ~0.5 and ~1.0 x Lsat), results_v4/load_points.json, and for the earlier 2x2
values results_v2/eval_runs.csv, results_v3/confirm_runs.csv, results_v2/load_points.json.
Outputs (results_v4/report/): primary.csv, summary.md, latency_<size>.png, effect_vs_size.png.
Usage: python3 report_v4.py [first]   (first: seeds 1-5 only, written to report_seeds1-5/)
"""
import collections
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from primary_from_csv import SCEN as SCEN_2X2, ci, holm, ttest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R4 = os.path.join(HERE, 'results_v4')
LP = json.load(open(os.path.join(R4, 'load_points.json')))
LP2 = json.load(open(os.path.join(HERE, 'results_v2', 'load_points.json')))
SIZES = ['3x3', '4x4']
CHIPLETS = {'2x2': 4, '3x3': 9, '4x4': 16}
NORTH = {'3x3': '0x111111111', '4x4': '0x1111111111111111'}
PRIMARY = [('CI_heur', 'DeFT_tm'), ('CI_heurLA', 'DeFT_tm'), ('CI_qlLA', 'DeFT_tm'), ('FULL_heurLA', 'DeFT_tm')]
SECONDARY = [('CI_qlLA', 'CI_heurLA'), ('DeFT_tm', 'DeFT')]
METRICS = ['LAT', 'P99', 'THR']
VARIANTS = ['DeFT', 'DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_qlLA', 'FULL_heurLA']
STYLE = {'DeFT': ('#b0afa9', 's', ':'), 'DeFT_tm': ('#52514e', 's', '--'), 'CI_heur': ('#2a78d6', 'o', '-'),
         'CI_heurLA': ('#4a3aa7', '^', '-'), 'CI_qlLA': ('#1baf7a', 'D', '-'), 'FULL_heurLA': ('#eb6834', 'v', '-')}
CSTYLE = {'CI_heur': '#2a78d6', 'CI_heurLA': '#4a3aa7', 'CI_qlLA': '#1baf7a', 'FULL_heurLA': '#eb6834'}


def scen(size):
    return [(f'{size}-{p}', '0x0') for p in ('uniform', 'localized', 'hotspot', 'chipperm', 'movinghot')] + \
           [(f'{size}-{p}', NORTH[size]) for p in ('uniform', 'hotspot')]


def ladder(p, m):
    size, pat = p.split('-')
    return LP[f'{size}__{pat}__{m}']['eval']


def load_csv(path):
    out = {}
    for r in csv.DictReader(open(path)):
        out[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = dict(
            latency=float(r['latency']), p99=float(r['p99']), accepted=float(r['accepted']),
            dead=int(r['dead_ends']), imb=float(r['vl_imbalance']) if r['vl_imbalance'] else float('nan'))
    return out


def pct(xs):
    mu, h = ci(xs)
    return 100 * (math.exp(mu) - 1), 100 * (math.exp(mu - h) - 1), 100 * (math.exp(mu + h) - 1)


class Data:
    """Metric access for one data set (runs, scenario list, load ladder, seeds)."""

    def __init__(self, runs, scenarios, ladder_fn, seeds):
        self.R, self.S, self.L, self.seeds = runs, scenarios, ladder_fn, list(seeds)

    def thr(self, v, p, m, s):
        lad = self.L(p, m)
        acc = [(self.R[(v, p, m, r, s)]['accepted'], r) for r in lad]
        best, at = max(acc)
        return best, at == lad[-1] and best >= 0.95 * 8 * lad[-1]

    def metric(self, v, p, m, s, name, idx=3):
        if name == 'THR':
            return self.thr(v, p, m, s)[0]
        r = self.R[(v, p, m, self.L(p, m)[idx], s)]
        return r['p99'] if name == 'P99' else r['latency']

    def per_seed(self, a, b, name, scenarios=None, idx=3):
        out = []
        for s in self.seeds:
            try:
                rs = [math.log(self.metric(a, p, m, s, name, idx) / self.metric(b, p, m, s, name, idx))
                      for p, m in (scenarios or self.S)]
            except KeyError:
                continue
            out.append(sum(rs) / len(rs))
        return out

    def capped(self, a, b):
        return sum(1 for p, m in self.S for s in self.seeds if self.thr(a, p, m, s)[1] or self.thr(b, p, m, s)[1])


def main():
    first = len(sys.argv) > 1 and sys.argv[1] == 'first'
    seeds = range(1, 6) if first else range(1, 11)
    out = os.path.join(R4, 'report_seeds1-5' if first else 'report')
    os.makedirs(out, exist_ok=True)
    R = {k: v for k, v in load_csv(os.path.join(R4, 'eval_runs.csv')).items() if k[4] in seeds}
    D = {z: Data(R, scen(z), ladder, seeds) for z in SIZES}
    expected = sum(len(ladder(p, m)) for z in SIZES for p, m in scen(z)) * len(VARIANTS) * len(seeds)
    dead = sum(x['dead'] for x in R.values())

    # earlier 2x2 values (context only)
    lad2 = lambda p, m: LP2[f'{p}__{m}']['eval']  # noqa: E731
    v2 = Data(load_csv(os.path.join(HERE, 'results_v2', 'eval_runs.csv')), SCEN_2X2, lad2, range(1, 11))
    v3runs = load_csv(os.path.join(HERE, 'results_v3', 'confirm_runs.csv'))
    v3 = Data(v3runs, SCEN_2X2, lad2, range(11, 21))
    early = {}
    for a, b in PRIMARY + SECONDARY:
        for name in METRICS:
            try:
                src = v2 if name == 'THR' else v3
                early[(a, b, name)] = (pct(src.per_seed(a, b, name)), 'v2 seeds 1-10' if name == 'THR' else 'v3 seeds 11-20')
            except (KeyError, ZeroDivisionError, ValueError):
                early[(a, b, name)] = None
            if early[(a, b, name)] is None and name != 'THR':
                try:
                    early[(a, b, name)] = (pct(v2.per_seed(a, b, name)), 'v2 seeds 1-10')
                except (KeyError, ZeroDivisionError, ValueError):
                    pass

    # ---- primary ----
    prim = []
    for z in SIZES:
        for a, b in PRIMARY:
            for name in METRICS:
                xs = D[z].per_seed(a, b, name)
                e, lo, hi = pct(xs)
                prim.append(dict(size=z, variant=a, reference=b, metric=name, n_seeds=len(xs), effect_pct=round(e, 2),
                                 ci_low=round(lo, 2), ci_high=round(hi, 2), p=ttest(xs),
                                 capped_cells=D[z].capped(a, b) if name == 'THR' else 0))
    for x, q in zip(prim, holm([x['p'] for x in prim])):
        x['p_holm'] = q
        good = x['effect_pct'] > 0 if x['metric'] == 'THR' else x['effect_pct'] < 0
        x['verdict'] = ('better' if good else 'worse') if q < 0.05 else 'n.s.'
    with open(os.path.join(out, 'primary.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(prim[0]), lineterminator='\n')
        w.writeheader()
        for x in prim:
            w.writerow({k: (f'{v:.4g}' if k in ('p', 'p_holm') else v) for k, v in x.items()})

    L = [f'# v4 summary (seeds {min(seeds)}-{max(seeds)}; generated by report_v4.py)', '',
         f'Runs: {len(R)} of {expected}; dead-end events: {dead}.', '',
         '## Primary results (pre-registered; Holm over 24 tests)', '',
         'Effect: mean over the 7 scenarios of the size of the per-seed log ratio, as % change with a 95 % CI. '
         'LAT/P99 at 1.0 x Lsat (lower is better); THR = saturation throughput (higher is better). '
         'The 2x2 column is context from earlier runs (11 scenarios), not part of the test.', '',
         '| size | variant | reference | metric | effect % [95 % CI] | p | p (Holm) | verdict | THR capped cells | '
         '2x2 earlier runs |', '|---|---|---|---|---|---|---|---|---|---|']
    for x in prim:
        e2 = early.get((x['variant'], x['reference'], x['metric']))
        e2s = f'{e2[0][0]:+.1f} [{e2[0][1]:+.1f}, {e2[0][2]:+.1f}] ({e2[1]})' if e2 else 'n/a'
        L.append(f'| {x["size"]} | {x["variant"]} | {x["reference"]} | {x["metric"]} | {x["effect_pct"]:+.2f} '
                 f'[{x["ci_low"]:+.2f}, {x["ci_high"]:+.2f}] | {x["p"]:.3g} | {x["p_holm"]:.3g} | **{x["verdict"]}** | '
                 f'{x["capped_cells"] if x["metric"] == "THR" else "-"} | {e2s} |')
    L.append('')

    # ---- secondary: comparisons ----
    L += ['## Secondary: CI_qlLA vs CI_heurLA and DeFT_tm vs DeFT (unadjusted 95 % CI; descriptive)', '',
          '| size | variant | reference | LAT 1.0 | P99 1.0 | THR | LAT 0.5 | 2x2 earlier (LAT 1.0; P99 1.0; THR) |',
          '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for a, b in SECONDARY:
            cells = [pct(D[z].per_seed(a, b, n)) for n in METRICS] + [pct(D[z].per_seed(a, b, 'LAT', idx=1))]
            e2 = [early.get((a, b, n)) for n in METRICS]
            L.append(f'| {z} | {a} | {b} | ' + ' | '.join(f'{c[0]:+.1f} [{c[1]:+.1f}, {c[2]:+.1f}]' for c in cells) + ' | '
                     + '; '.join(f'{x[0][0]:+.1f}' if x else 'n/a' for x in e2) + ' |')
    L.append('')

    # ---- secondary: per scenario ----
    for name in METRICS:
        L += [f'## Secondary: per-scenario {name} (unadjusted; `°` = 95 % CI excludes 0)', '']
        for z in SIZES:
            L += [f'**{z}**', '', '| variant vs ref | ' + ' | '.join(f'{p.split("-")[1]} {m}' for p, m in scen(z)) + ' |',
                  '|---|' + '---|' * len(scen(z))]
            for a, b in PRIMARY + SECONDARY:
                cells = []
                for p, m in scen(z):
                    e, lo, hi = pct(D[z].per_seed(a, b, name, [(p, m)]))
                    capped = name == 'THR' and any(D[z].thr(a, p, m, s)[1] or D[z].thr(b, p, m, s)[1] for s in seeds)
                    cells.append(f'{"≥" if capped else ""}{e:+.1f}{"°" if hi < 0 or lo > 0 else ""}')
                L.append(f'| {a} vs {b} | ' + ' | '.join(cells) + ' |')
            L.append('')

    # ---- VL imbalance ----
    L += ['## Secondary: VL usage imbalance (max/mean over functional VLs), mean over seeds', '',
          'DeFT_tm from the traffic-identical proxy; DeFT has no VL counts in v4 (not measured).', '']
    for idx, lab in ((1, '~0.5 x Lsat'), (3, '~1.0 x Lsat')):
        for z in SIZES:
            L += [f'**{z}, {lab}**', '', '| variant | ' + ' | '.join(f'{p.split("-")[1]} {m}' for p, m in scen(z)) + ' |',
                  '|---|' + '---|' * len(scen(z))]
            for v in VARIANTS[1:]:
                cells = []
                for p, m in scen(z):
                    xs = [R[(v, p, m, ladder(p, m)[idx], s)]['imb'] for s in seeds if (v, p, m, ladder(p, m)[idx], s) in R]
                    xs = [x for x in xs if not math.isnan(x)]
                    cells.append(f'{sum(xs) / len(xs):.2f}' if xs else 'n/a')
                L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
            L.append('')

    # ---- saturation throughput absolute ----
    L += ['## Saturation throughput (flits/node/cycle), mean over seeds; `≥` = capped on some seed', '']
    for z in SIZES:
        L += [f'**{z}**', '', '| variant | ' + ' | '.join(f'{p.split("-")[1]} {m}' for p, m in scen(z)) + ' |',
              '|---|' + '---|' * len(scen(z))]
        for v in VARIANTS:
            cells = []
            for p, m in scen(z):
                t = [D[z].thr(v, p, m, s) for s in seeds]
                cells.append(('≥' if any(c for _, c in t) else '') + f'{sum(x for x, _ in t) / len(t):.4f}')
            L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
        L.append('')
    open(os.path.join(out, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')

    # ---- figure: latency vs load per size ----
    for z in SIZES:
        sc = scen(z)
        fig, axes = plt.subplots(2, 4, figsize=(18, 8))
        for ax, (p, m) in zip(axes.flat, sc):
            for v in VARIANTS:
                xs, ys, es = [], [], []
                for r in ladder(p, m):
                    lat = [R[(v, p, m, r, s)]['latency'] for s in seeds if (v, p, m, r, s) in R]
                    if len(lat) < 2:
                        continue
                    mu, h = ci([math.log(x) for x in lat])
                    xs.append(8 * r)
                    ys.append(math.exp(mu))
                    es.append((math.exp(mu) - math.exp(mu - h), math.exp(mu + h) - math.exp(mu)))
                c, mk, ls = STYLE[v]
                ax.errorbar(xs, ys, yerr=list(zip(*es)) if es else None, label=v, color=c, marker=mk, ls=ls, lw=1.5,
                            ms=4, capsize=2, elinewidth=0.8)
            size_, pat = p.split('-')
            ax.axvline(8 * LP[f'{size_}__{pat}__{m}']['lsat'], color='#b0afa9', lw=0.8, ls=':')
            ax.set_yscale('log')
            ax.set_title(f'{pat}, mask {m if m == "0x0" else "north per chiplet"}', fontsize=9)
            ax.set_xlabel('offered load (flits/node/cycle)', fontsize=8)
            ax.grid(True, color='#e6e5e1', lw=0.6)
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
        axes.flat[-1].axis('off')
        h, lab = axes.flat[0].get_legend_handles_labels()
        axes.flat[-1].legend(h, lab, loc='center', frameon=False, fontsize=10)
        axes[0][0].set_ylabel('mean latency (cycles, log)\ngeo-mean over seeds, 95 % CI')
        axes[1][0].set_ylabel('mean latency (cycles, log)\ngeo-mean over seeds, 95 % CI')
        fig.suptitle(f'{z} chiplets of 4x4 routers ({CHIPLETS[z]} chiplets): latency vs offered load '
                     '(dotted: DeFT Lsat of the scenario; beyond saturation not a steady state)', fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out, f'latency_{z}.png'), dpi=120)
        plt.close(fig)

    # ---- figure: effect vs system size ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    titles = {'LAT': 'Mean latency at 1.0 x Lsat (lower is better)', 'P99': 'p99 latency at 1.0 x Lsat (lower is better)',
              'THR': 'Saturation throughput (higher is better)'}
    for ax, name in zip(axes, METRICS):
        for j, (a, b) in enumerate(PRIMARY):
            col = CSTYLE[a]
            off = (j - 1.5) * 0.25
            e2 = early.get((a, b, name))
            if e2:
                e, lo, hi = e2[0]
                ax.errorbar([CHIPLETS['2x2'] + off], [e], yerr=[[e - lo], [hi - e]], fmt='o', mfc='white', color=col,
                            capsize=3, ms=6)
            pts = [x for x in prim if x['variant'] == a and x['metric'] == name]
            xs = [CHIPLETS[x['size']] + off for x in pts]
            ax.errorbar(xs, [x['effect_pct'] for x in pts],
                        yerr=[[x['effect_pct'] - x['ci_low'] for x in pts], [x['ci_high'] - x['effect_pct'] for x in pts]],
                        fmt='o-', color=col, capsize=3, ms=6, lw=1.4, label=f'{a} vs {b}')
            if e2:
                ax.plot([CHIPLETS['2x2'] + off, xs[0]], [e2[0][0], pts[0]['effect_pct']], ls=':', color=col, lw=1)
        ax.axhline(0, color='#52514e', lw=0.8)
        ax.set_xticks([4, 9, 16])
        ax.set_xticklabels(['4 (2x2)\nearlier runs', '9 (3x3)', '16 (4x4)'])
        ax.set_xlabel('chiplets')
        ax.set_ylabel('% change vs DeFT_tm, mean over scenarios')
        ax.set_title(titles[name], fontsize=10)
        ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=4, frameon=False, fontsize=9)
    fig.suptitle('Primary effects vs system size (95 % CI over seeds). Hollow markers at 4 chiplets: earlier 2x2 runs '
                 '(LAT/P99: v3 seeds 11-20; THR: v2 seeds 1-10; 11 scenarios) - context, not part of the v4 test',
                 fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(out, 'effect_vs_size.png'), dpi=130)
    plt.close(fig)
    print(f'runs {len(R)}/{expected}, dead {dead}')
    for x in prim:
        print(x['size'], x['variant'], x['metric'], x['effect_pct'], x['ci_low'], x['ci_high'], f'{x["p_holm"]:.3g}',
              x['verdict'], x['capped_cells'])


if __name__ == '__main__':
    main()
