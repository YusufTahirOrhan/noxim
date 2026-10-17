"""Stage-8 analysis of the evaluation runs (seeds 1..5).

Inputs: results/eval_raw (11 variants) and results/evalvl_raw (DEFT_LB with the
DeFT LUT pairs: traffic-identical to DeFT, used only for DeFT's VL counts; the
script checks that its latency equals DeFT's on every run).

Outputs (results/eval_report/):
  latency_<pattern>_<mask>.png  latency vs offered load, mean and 95 % CI, panels A / CI / FULL
  saturation.csv                saturation throughput per variant and scenario
  saturation.png                saturation throughput relative to DeFT, per scenario
  tail_vl.csv                   p99 latency and VL usage imbalance at every load
  paired.csv                    paired differences on the same seeds (variant vs DeFT, B vs C)
  summary.md                    tables used by the write-up

Definitions
  saturation throughput: per seed, the maximum accepted throughput (flits/node/cycle)
    over the 7 loads; marked "lower bound" if the maximum is at the highest load and the
    variant still accepts >= 95 % of it there (not saturated within the sweep).
  VL imbalance: per run, max / mean of the per-VL packet count (down + up) over the
    functional VLs (1.0 = perfectly balanced).
  paired differences: per seed s, the variant's value minus the reference's value on
    the same seed, scenario and load; mean and 95 % t-interval over the 5 seeds.
    Latency and p99 are compared as ratios (log scale, reported as % change);
    saturation throughput as a % change.
  low load = 2nd evaluation rate (0.45-0.57 Lsat); near-Lsat = 4th evaluation rate (~0.9-1.0 Lsat).
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
from scipy import stats as st  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import load_runs  # noqa: E402
from experiments import EVAL_SCENARIOS, EVAL_SEEDS  # noqa: E402
import variants as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'eval_report')
VARS = list(V.VARIANTS)
LP = json.load(open(os.path.join(HERE, 'results', 'load_points.json')))
LOW, NEAR = 1, 3          # indices into the evaluation rates
# DeFT saturation rates (packets/cycle/source), seed 101, fault-free: results/load_points.md
LSAT = {'uniform': 0.011, 'localized': 0.013, 'hotspot': 0.007, 'chipperm': 0.004, 'movinghot': 0.007}

# Colour by role, validated set (blue, orange, aqua, violet; all-pairs CVD dE >= 9.2);
# markers give a second encoding. DeFT is the neutral reference in every panel.
REF = dict(color='#52514e', marker='s', ls='--')
STYLE = {
    'A_mindist': ('#2a78d6', 'o'), 'A_random': ('#eb6834', 'v'), 'A_oracle': ('#1baf7a', 'D'),
    'CI_random': ('#eb6834', 'v'), 'CI_heur': ('#2a78d6', 'o'), 'CI_ql': ('#1baf7a', 'D'),
    'FULL_random': ('#eb6834', 'v'), 'FULL_heur': ('#2a78d6', 'o'), 'FULL_heurLA': ('#4a3aa7', '^'),
    'FULL_ql': ('#1baf7a', 'D'),
}
PANELS = [('A: injection-time VL choice', ['A_mindist', 'A_random', 'A_oracle']),
          ('CI: late binding on the interposer', ['CI_random', 'CI_heur', 'CI_ql']),
          ('FULL: late binding on chiplets and interposer', ['FULL_random', 'FULL_heur', 'FULL_heurLA', 'FULL_ql'])]
LABEL = {'A_oracle': 'A_oracle (upper bound)'}
PAIRS = [(v, 'DeFT') for v in VARS if v != 'DeFT'] + [('FULL_ql', 'FULL_heur'), ('CI_ql', 'CI_heur'),
                                                      ('FULL_ql', 'FULL_heurLA')]


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, float('nan')
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)


def imbalance(r):
    faulty = int(r['mask'], 16)
    c = [r['vl_down'][v] + r['vl_up'][v] for v in range(16) if not faulty >> v & 1]
    m = sum(c) / len(c)
    return max(c) / m if m > 0 else float('nan')


def fmt_pct(m, h):
    return f'{m:+.1f} [{m - h:+.1f}, {m + h:+.1f}]'


def main():
    os.makedirs(OUT, exist_ok=True)
    runs = load_runs('eval')
    R = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in runs}
    vl = {(r['pattern'], r['mask'], r['rate'], r['seed']): r for r in load_runs('evalvl')}
    expected = sum(len(LP[p]['eval']) for p, _ in EVAL_SCENARIOS) * len(VARS) * len(EVAL_SEEDS)
    print('eval runs', len(runs), 'of', expected, '; DeFT VL-proxy runs', len(vl))
    print('dead-end events in eval:', sum(r['dead_ends'] for r in runs))

    # DeFT's VL counts come from the traffic-identical proxy; check it really is identical.
    mism = 0
    for (p, m, rate, s), pr in vl.items():
        d = R.get(('DeFT', p, m, rate, s))
        if d is None:
            continue
        if (d['latency'], d['p99'], d['received']) != (pr['latency'], pr['p99'], pr['received']):
            mism += 1
        d['vl_down'], d['vl_up'] = pr['vl_down'], pr['vl_up']
    print('proxy/DeFT mismatches:', mism)
    for r in runs:
        r['imb'] = imbalance(r) if any(r['vl_down']) else float('nan')

    def vals(v, p, m, rate, key):
        return [R[(v, p, m, rate, s)][key] for s in EVAL_SEEDS if (v, p, m, rate, s) in R]

    # ---- latency curves ----
    for p, m in EVAL_SCENARIOS:
        rates = LP[p]['eval']
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), sharey=True)
        for ax, (title, vs) in zip(axes, PANELS):
            for v in ['DeFT'] + vs:
                xs, ys, es = [], [], []
                for rate in rates:
                    lat = vals(v, p, m, rate, 'latency')
                    if len(lat) < 2:
                        continue
                    # CI on the log scale (the axis is logarithmic), back-transformed
                    mu, h = ci([math.log(x) for x in lat])
                    xs.append(8 * rate)
                    ys.append(math.exp(mu))
                    es.append((math.exp(mu) - math.exp(mu - h), math.exp(mu + h) - math.exp(mu)))
                kw = dict(REF) if v == 'DeFT' else dict(color=STYLE[v][0], marker=STYLE[v][1], ls='-')
                ax.errorbar(xs, ys, yerr=list(zip(*es)) if es else None, label=LABEL.get(v, v),
                            lw=1.6, ms=5, capsize=3, elinewidth=1, **kw)
            ax.axvline(8 * LSAT[p], color='#b0afa9', lw=0.8, ls=':')
            ax.set_yscale('log')
            ax.set_title(title, fontsize=10)
            ax.set_xlabel('offered load (flits/node/cycle)')
            ax.grid(True, which='major', color='#e6e5e1', lw=0.6)
            ax.legend(fontsize=8, frameon=False, loc='upper left')
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
        axes[0].set_ylabel('mean packet latency (cycles, log)\ngeometric mean over 5 seeds, 95 % CI')
        fig.suptitle(f'{p}, fault mask {m}   (dotted: fault-free DeFT Lsat = {8 * LSAT[p]:.3f}; '
                     f'beyond saturation the fixed-window latency is not a steady state)', fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f'latency_{p}_{m}.png'), dpi=130)
        plt.close(fig)

    # ---- saturation throughput ----
    sat = {}       # (v, p, m) -> per-seed list
    lower_bound = {}
    rows = []
    for p, m in EVAL_SCENARIOS:
        top = LP[p]['eval'][-1]
        for v in VARS:
            per_seed, lb = [], 0
            for s in EVAL_SEEDS:
                acc = [(R[(v, p, m, rate, s)]['accepted'], rate) for rate in LP[p]['eval'] if (v, p, m, rate, s) in R]
                if not acc:
                    continue
                best, at = max(acc)
                per_seed.append(best)
                lb += at == top and best >= 0.95 * 8 * top
            sat[(v, p, m)] = per_seed
            lower_bound[(v, p, m)] = lb > 0
            mu, h = ci(per_seed)
            rows.append(dict(pattern=p, mask=m, variant=v, n=len(per_seed), sat_throughput=round(mu, 5),
                             ci95=round(h, 5), seeds_not_saturated_in_sweep=lb))
    with open(os.path.join(OUT, 'saturation.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    # ---- p99 and VL imbalance ----
    rows = []
    for p, m in EVAL_SCENARIOS:
        for rate in LP[p]['eval']:
            for v in VARS:
                p99, imb = ci(vals(v, p, m, rate, 'p99')), ci(vals(v, p, m, rate, 'imb'))
                rows.append(dict(pattern=p, mask=m, rate=rate, offered=8 * rate, variant=v,
                                 p99=round(p99[0], 1), p99_ci=round(p99[1], 1),
                                 vl_imbalance=round(imb[0], 3), vl_imbalance_ci=round(imb[1], 3)))
    with open(os.path.join(OUT, 'tail_vl.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    # ---- paired differences ----
    def paired(a, b, p, m, key, idx=None):
        if key == 'sat':
            xa, xb = sat[(a, p, m)], sat[(b, p, m)]
            d = [100 * (x / y - 1) for x, y in zip(xa, xb)]
            return ci(d)
        rate = LP[p]['eval'][idx]
        d = []
        for s in EVAL_SEEDS:
            ra, rb = R.get((a, p, m, rate, s)), R.get((b, p, m, rate, s))
            if ra and rb:
                d.append(math.log(ra[key] / rb[key]))
        mu, h = ci(d)
        # back-transform: % change of the geometric-mean ratio
        return 100 * (math.exp(mu) - 1), 100 * (math.exp(mu + h) - math.exp(mu))

    prow = []
    for a, b in PAIRS:
        for p, m in EVAL_SCENARIOS:
            rec = dict(variant=a, reference=b, pattern=p, mask=m)
            for name, key, idx in (('sat_thr_pct', 'sat', None), ('lat_low_pct', 'latency', LOW),
                                   ('lat_near_pct', 'latency', NEAR), ('p99_near_pct', 'p99', NEAR)):
                mu, h = paired(a, b, p, m, key, idx)
                rec[name] = round(mu, 2)
                rec[name + '_ci'] = round(h, 2)
            prow.append(rec)
    with open(os.path.join(OUT, 'paired.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(prow[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(prow)

    # ---- saturation figure: % change vs DeFT with 95 % CI ----
    labels = [f'{p}\n{m}' for p, m in EVAL_SCENARIOS]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    for ax, (title, vs) in zip(axes, PANELS):
        width = 0.8 / len(vs)
        for k, v in enumerate(vs):
            ms = [paired(v, 'DeFT', p, m, 'sat') for p, m in EVAL_SCENARIOS]
            xs = [i + (k - (len(vs) - 1) / 2) * width for i in range(len(labels))]
            bars = ax.bar(xs, [x[0] for x in ms], width * 0.9, yerr=[x[1] for x in ms], color=STYLE[v][0],
                          label=LABEL.get(v, v), capsize=2, error_kw=dict(elinewidth=0.8, ecolor='#52514e'))
            for bar, (p, m) in zip(bars, EVAL_SCENARIOS):
                if lower_bound[(v, p, m)]:
                    bar.set_hatch('////')
                    bar.set_edgecolor('white')
        ax.axhline(0, color='#52514e', lw=0.8)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=7, rotation=90)
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8, frameon=False)
        ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel('saturation throughput vs DeFT (%)\npaired over 5 seeds, 95 % CI')
    fig.suptitle('hatched: variant not saturated within the load sweep on some seed (the gain is a lower bound)',
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'saturation.png'), dpi=130)
    plt.close(fig)

    # ---- summary.md ----
    L = ['# Evaluation summary (seeds 1-5; generated by report_eval.py)', '',
         f'Runs: {len(runs)} of {expected}; dead-end events: {sum(r["dead_ends"] for r in runs)}; '
         f'DeFT VL-proxy mismatches: {mism} of {len(vl)}.', '',
         'Cells: mean change vs reference with 95 % t-interval over 5 paired seeds. '
         '`*` marks intervals that exclude 0 (no multiplicity correction).', '']

    def table(metric, title, pairs):
        L.append(f'## {title}')
        L.append('')
        L.append('| variant vs ref | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
        L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
        for a, b in pairs:
            cells = []
            for p, m in EVAL_SCENARIOS:
                r = next(x for x in prow if x['variant'] == a and x['reference'] == b and x['pattern'] == p and x['mask'] == m)
                mu, h = r[metric], r[metric + '_ci']
                star = '*' if (mu - h > 0 or mu + h < 0) else ''
                cells.append(f'{mu:+.1f}±{h:.1f}{star}')
            L.append(f'| {a} vs {b} | ' + ' | '.join(cells) + ' |')
        L.append('')

    sat_note = []
    for p, m in EVAL_SCENARIOS:
        rate = LP[p]['eval'][NEAR]
        acc = ci(vals('DeFT', p, m, rate, 'accepted'))[0]
        if acc < 0.95 * 8 * rate:
            sat_note.append(f'{p} {m} (DeFT accepts {100 * acc / (8 * rate):.0f} % of the offered load)')
    L.append('DeFT is already saturated at the near-Lsat rate in: ' + ('; '.join(sat_note) or 'none') +
             '. There the near-Lsat latency ratios compare window-dependent, non-steady-state values.')
    L.append('')
    vs_deft = [x for x in PAIRS if x[1] == 'DeFT']
    bc = [x for x in PAIRS if x[1] != 'DeFT']
    table('sat_thr_pct', 'Saturation throughput, % change vs reference (higher is better)', vs_deft + bc)
    table('lat_low_pct', 'Mean latency at low load (2nd rate, 0.45-0.57 Lsat), % change (lower is better)', vs_deft + bc)
    table('lat_near_pct', 'Mean latency near DeFT Lsat (4th rate), % change (lower is better)', vs_deft + bc)
    table('p99_near_pct', 'p99 latency near DeFT Lsat (4th rate), % change (lower is better)', vs_deft + bc)

    L.append('## Saturation throughput (flits/node/cycle), mean ± 95 % CI; `≥` = not saturated within the sweep on some seed')
    L.append('')
    L.append('| variant | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
    L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
    satrows = list(csv.DictReader(open(os.path.join(OUT, 'saturation.csv'))))
    for v in VARS:
        cells = []
        for p, m in EVAL_SCENARIOS:
            r = next(x for x in satrows if x['variant'] == v and x['pattern'] == p and x['mask'] == m)
            cells.append(('≥' if int(r['seeds_not_saturated_in_sweep']) else '') +
                         f'{float(r["sat_throughput"]):.4f}±{float(r["ci95"]):.4f}')
        L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
    L.append('')

    L.append('## VL usage imbalance (max/mean over functional VLs) near DeFT Lsat (4th rate)')
    L.append('')
    L.append('| variant | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
    L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
    for v in VARS:
        cells = []
        for p, m in EVAL_SCENARIOS:
            mu, h = ci(vals(v, p, m, LP[p]['eval'][NEAR], 'imb'))
            cells.append(f'{mu:.2f}±{h:.2f}')
        L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
    L.append('')

    L.append('## Win/loss count vs DeFT over the 11 scenarios (CI excludes 0)')
    L.append('')
    L.append('| variant | sat. thr. better / worse | latency low better / worse | latency near better / worse | p99 near better / worse |')
    L.append('|---|---|---|---|---|')
    for a, b in vs_deft + bc:
        rs = [x for x in prow if x['variant'] == a and x['reference'] == b]
        cnt = []
        for metric, up in (('sat_thr_pct', True), ('lat_low_pct', False), ('lat_near_pct', False), ('p99_near_pct', False)):
            better = sum(1 for x in rs if (x[metric] - x[metric + '_ci'] > 0) == up and abs(x[metric]) > x[metric + '_ci'])
            worse = sum(1 for x in rs if abs(x[metric]) > x[metric + '_ci']) - better
            cnt.append(f'{better} / {worse}')
        L.append(f'| {a} vs {b} | ' + ' | '.join(cnt) + ' |')
    L.append('')
    open(os.path.join(OUT, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('written', OUT)


if __name__ == '__main__':
    main()
