"""Analysis of the v2 evaluation (results_v2/), following PREREGISTRATION.md.

Inputs: results_v2/eval_raw (11 variants, seeds 1-10) and results_v2/evalvl_raw (DEFT_LB
with the LUT pairs, traffic-identical to DeFT / DeFT_tm, for VL counts; checked here).
Outputs (results_v2/report/):
  primary.csv / primary.md     16 pre-registered tests with Holm-adjusted p-values
  paired.csv                   secondary per-scenario paired differences
  saturation.csv, tail_vl.csv  per-variant saturation throughput, p99 and VL imbalance
  latency_<pattern>_<mask>.png, saturation.png, primary.png
  summary.md                   tables used by FINDINGS.md
Usage: python3 report_v2.py [seeds]   (seeds: 'all' = 1-10 (default), 'first' = 1-5)
"""
import collections
import csv
import glob
import json
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from scipy import stats as st  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from experiments import EVAL_SCENARIOS  # noqa: E402
import variants_v2 as V2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v2')
LP = json.load(open(os.path.join(RES, 'load_points.json')))
VARS = list(V2.VARIANTS)
LOW, NEAR = 1, 3
PRIMARY = [('CI_heur', 'DeFT_tm'), ('CI_heurLA', 'DeFT_tm'), ('FULL_heurLA', 'DeFT_tm'),
           ('CI_ql', 'CI_heur'), ('FULL_ql', 'FULL_heur'), ('CI_qlLA', 'CI_heurLA'),
           ('FULL_qlLA', 'FULL_heurLA'), ('DeFT_tm', 'DeFT')]
SECONDARY = [(v, 'DeFT_tm') for v in VARS if v not in ('DeFT_tm',)] + \
            [(v, 'DeFT') for v in VARS if v not in ('DeFT', 'DeFT_tm')] + \
            [('FULL_qlLA', 'FULL_ql'), ('CI_qlLA', 'CI_ql'), ('FULL_heurLA', 'FULL_heur'), ('CI_heurLA', 'CI_heur')]
REF = dict(color='#52514e', marker='s', ls='--')
STYLE = {'DeFT': ('#b0afa9', 's', ':'), 'DeFT_tm': ('#52514e', 's', '--'), 'A_oracle': ('#1baf7a', 'D', '-')}
for sc in ('CI', 'FULL'):
    STYLE.update({f'{sc}_heur': ('#2a78d6', 'o', '-'), f'{sc}_heurLA': ('#4a3aa7', '^', '-'),
                  f'{sc}_ql': ('#1baf7a', 'D', '-'), f'{sc}_qlLA': ('#eb6834', 'v', '-')})
PANELS = [('Baselines (A_oracle: unimplementable upper bound)', ['DeFT', 'DeFT_tm', 'A_oracle']),
          ('CI: late binding on the interposer', ['DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_ql', 'CI_qlLA']),
          ('FULL: late binding on chiplets and interposer', ['DeFT_tm', 'FULL_heur', 'FULL_heurLA', 'FULL_ql', 'FULL_qlLA'])]


def k(p, m):
    return f'{p}__{m}'


def load(stage):
    out = {}
    for f in glob.glob(os.path.join(RES, f'{stage}_raw', '*.json')):
        _, v, p, m, rate, seed = os.path.basename(f)[:-5].split('__')
        try:
            d = json.load(open(f))
        except Exception:
            continue
        s, l = d['summary'], d['deft_lb']
        out[(v, p, m, float(rate), int(seed[1:]))] = dict(
            latency=s['global_average_delay_cycles'], p99=l['delay_p99'],
            accepted=s['average_ip_throughput_flits_per_cycle_per_ip'], received=s['total_received_packets'],
            dead_ends=l['dead_end_events'], vl_down=l['vl_down_packets'], vl_up=l['vl_up_packets'], mask=m)
    return out


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, float('nan')
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)


def ttest(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    if sd == 0:
        return 0.0 if m != 0 else 1.0
    t = m / (sd / math.sqrt(n))
    return 2 * st.t.sf(abs(t), n - 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def imbalance(r):
    faulty = int(r['mask'], 16)
    c = [r['vl_down'][v] + r['vl_up'][v] for v in range(16) if not faulty >> v & 1]
    mu = sum(c) / len(c)
    return max(c) / mu if mu > 0 else float('nan')


def pct(mu, h):
    return 100 * (math.exp(mu) - 1), 100 * (math.exp(mu + h) - math.exp(mu))


def main():
    seeds = list(range(1, 6)) if (len(sys.argv) > 1 and sys.argv[1] == 'first') else list(range(1, 11))
    out_dir = os.path.join(RES, 'report' if len(seeds) == 10 else 'report_seeds1-5')
    os.makedirs(out_dir, exist_ok=True)
    R = {kk: v for kk, v in load('eval').items() if kk[4] in seeds}
    vl = {kk: v for kk, v in load('evalvl').items() if kk[4] in seeds}
    expected = sum(len(LP[k(p, m)]['eval']) for p, m in EVAL_SCENARIOS) * len(VARS) * len(seeds)
    missing = [(v, p, m, r, s) for p, m in EVAL_SCENARIOS for r in LP[k(p, m)]['eval'] for v in VARS for s in seeds
               if (v, p, m, r, s) not in R]
    mism = 0
    for (v, p, m, r, s), pr in vl.items():
        d = R.get((v, p, m, r, s))
        if d is None:
            continue
        if (d['latency'], d['p99'], d['received']) != (pr['latency'], pr['p99'], pr['received']):
            mism += 1
        d['vl_down'], d['vl_up'] = pr['vl_down'], pr['vl_up']
    for d in R.values():
        d['imb'] = imbalance(d) if any(d['vl_down']) else float('nan')
    dead = sum(d['dead_ends'] for d in R.values())
    # DeFT_tm vs DeFT identity where the LUTs are identical
    ident = sum(1 for (v, p, m, r, s) in R if v == 'DeFT_tm' and p in ('uniform', 'localized', 'movinghot'))
    ident_ok = sum(1 for (v, p, m, r, s), d in R.items()
                   if v == 'DeFT_tm' and p in ('uniform', 'localized', 'movinghot')
                   and (R.get(('DeFT', p, m, r, s)) or {}).get('latency') == d['latency'])
    print(f'runs {len(R)} of {expected}; missing {len(missing)}; dead ends {dead}; VL proxy mismatches {mism} of {len(vl)}; '
          f'DeFT_tm == DeFT on identical-LUT scenarios: {ident_ok} of {ident}')

    def vals(v, p, m, rate, key):
        return [R[(v, p, m, rate, s)][key] for s in seeds if (v, p, m, rate, s) in R]

    # ---- saturation throughput per seed ----
    sat, lower = {}, {}
    for p, m in EVAL_SCENARIOS:
        rates = LP[k(p, m)]['eval']
        for v in VARS:
            for s in seeds:
                acc = [(R[(v, p, m, r, s)]['accepted'], r) for r in rates if (v, p, m, r, s) in R]
                if len(acc) == len(rates):
                    best, at = max(acc)
                    sat[(v, p, m, s)] = best
                    lower[(v, p, m, s)] = at == rates[-1] and best >= 0.95 * 8 * rates[-1]

    def metric(v, p, m, s, name):
        if name == 'THR':
            return sat.get((v, p, m, s))
        idx = {'LAT': LOW, 'LATnear': NEAR, 'P99near': NEAR}[name]
        r = R.get((v, p, m, LP[k(p, m)]['eval'][idx], s))
        if r is None:
            return None
        return r['p99'] if name == 'P99near' else r['latency']

    # ---- primary tests ----
    prim = []
    for a, b in PRIMARY:
        for name in ('THR', 'LAT'):
            per_seed, dropped = [], 0
            for s in seeds:
                rs = []
                for p, m in EVAL_SCENARIOS:
                    x, y = metric(a, p, m, s, name), metric(b, p, m, s, name)
                    if x is None or y is None:
                        rs = None
                        break
                    rs.append(math.log(x / y))
                if rs is None:
                    dropped += 1
                    continue
                per_seed.append(sum(rs) / len(rs))
            mu, h = ci(per_seed)
            e, eh = pct(mu, h)
            lo, hi = 100 * (math.exp(mu - h) - 1), 100 * (math.exp(mu + h) - 1)
            nlb = sum(1 for p, m in EVAL_SCENARIOS for s in seeds
                      if name == 'THR' and (lower.get((a, p, m, s)) or lower.get((b, p, m, s))))
            prim.append(dict(variant=a, reference=b, metric=name, n_seeds=len(per_seed), dropped_seeds=dropped,
                             effect_pct=round(e, 2), ci_low=round(lo, 2), ci_high=round(hi, 2),
                             p=ttest(per_seed), lower_bound_cells=nlb))
    adj = holm([x['p'] for x in prim])
    for x, q in zip(prim, adj):
        x['p_holm'] = q
        good = (x['effect_pct'] > 0) if x['metric'] == 'THR' else (x['effect_pct'] < 0)
        x['verdict'] = ('better' if good else 'worse') if q < 0.05 else 'n.s.'
    with open(os.path.join(out_dir, 'primary.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(prim[0]), lineterminator='\n')
        w.writeheader()
        for x in prim:
            w.writerow({kk: (f'{vv:.4g}' if kk in ('p', 'p_holm') else vv) for kk, vv in x.items()})

    # ---- secondary per-scenario paired differences ----
    def paired(a, b, p, m, name):
        d = []
        for s in seeds:
            x, y = metric(a, p, m, s, name), metric(b, p, m, s, name)
            if x is not None and y is not None:
                d.append(math.log(x / y))
        mu, h = ci(d)
        e, eh = pct(mu, h)
        return e, eh, ttest(d) if len(d) > 1 else float('nan'), d

    rows = []
    for a, b in PRIMARY + [x for x in SECONDARY if x not in PRIMARY]:
        for p, m in EVAL_SCENARIOS:
            rec = dict(variant=a, reference=b, primary_pair=(a, b) in PRIMARY, pattern=p, mask=m)
            for name in ('THR', 'LAT', 'LATnear', 'P99near'):
                e, eh, pv, _ = paired(a, b, p, m, name)
                rec[name + '_pct'] = round(e, 2)
                rec[name + '_ci'] = round(eh, 2)
                rec[name + '_p'] = pv
            rec['THR_lower_bound_seeds'] = sum(1 for s in seeds if lower.get((a, p, m, s)) or lower.get((b, p, m, s)))
            rows.append(rec)
    cells = [(i, nm) for i, r in enumerate(rows) if r['primary_pair'] for nm in ('THR', 'LAT')]
    adj = holm([rows[i][nm + '_p'] if not math.isnan(rows[i][nm + '_p']) else 1.0 for i, nm in cells])
    for (i, nm), q in zip(cells, adj):
        rows[i][nm + '_p_holm176'] = q
    fields = list(rows[0]) + ['THR_p_holm176', 'LAT_p_holm176']
    with open(os.path.join(out_dir, 'paired.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({kk: (f'{vv:.4g}' if isinstance(vv, float) and kk.endswith(('_p', '_holm176')) else vv)
                        for kk, vv in r.items()})

    # ---- per-variant tables ----
    srow, trow = [], []
    for p, m in EVAL_SCENARIOS:
        for v in VARS:
            xs = [sat[(v, p, m, s)] for s in seeds if (v, p, m, s) in sat]
            mu, h = ci(xs)
            srow.append(dict(pattern=p, mask=m, variant=v, n=len(xs), sat_throughput=round(mu, 5), ci95=round(h, 5),
                             lower_bound_seeds=sum(1 for s in seeds if lower.get((v, p, m, s)))))
            for r in LP[k(p, m)]['eval']:
                p99, imb, lat = ci(vals(v, p, m, r, 'p99')), ci(vals(v, p, m, r, 'imb')), ci(vals(v, p, m, r, 'latency'))
                trow.append(dict(pattern=p, mask=m, rate=r, offered=8 * r, variant=v, latency=round(lat[0], 2),
                                 latency_ci=round(lat[1], 2), p99=round(p99[0], 1), p99_ci=round(p99[1], 1),
                                 vl_imbalance=round(imb[0], 3), vl_imbalance_ci=round(imb[1], 3)))
    for name, rr in (('saturation.csv', srow), ('tail_vl.csv', trow)):
        with open(os.path.join(out_dir, name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rr[0]), lineterminator='\n')
            w.writeheader()
            w.writerows(rr)

    # ---- figures ----
    for p, m in EVAL_SCENARIOS:
        rates = LP[k(p, m)]['eval']
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), sharey=True)
        for ax, (title, vs) in zip(axes, PANELS):
            for v in vs:
                xs, ys, es = [], [], []
                for r in rates:
                    lat = vals(v, p, m, r, 'latency')
                    if len(lat) < 2:
                        continue
                    mu, h = ci([math.log(x) for x in lat])
                    xs.append(8 * r)
                    ys.append(math.exp(mu))
                    es.append((math.exp(mu) - math.exp(mu - h), math.exp(mu + h) - math.exp(mu)))
                c, mk, ls = STYLE[v]
                ax.errorbar(xs, ys, yerr=list(zip(*es)) if es else None, label=v, color=c, marker=mk, ls=ls,
                            lw=1.6, ms=5, capsize=3, elinewidth=1)
            ax.axvline(8 * LP[k(p, m)]['lsat'], color='#b0afa9', lw=0.8, ls=':')
            ax.set_yscale('log')
            ax.set_title(title, fontsize=10)
            ax.set_xlabel('offered load (flits/node/cycle)')
            ax.grid(True, which='major', color='#e6e5e1', lw=0.6)
            ax.legend(fontsize=8, frameon=False, loc='upper left')
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
        axes[0].set_ylabel(f'mean packet latency (cycles, log)\ngeometric mean over {len(seeds)} seeds, 95 % CI')
        fig.suptitle(f'{p}, fault mask {m}   (dotted: DeFT Lsat = {8 * LP[k(p, m)]["lsat"]:.3f} for this scenario; '
                     'beyond saturation the fixed-window latency is not a steady state)', fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f'latency_{p}_{m}.png'), dpi=130)
        plt.close(fig)

    labels = [f'{p}\n{m}' for p, m in EVAL_SCENARIOS]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    bar_panels = [('vs DeFT_tm: baselines', ['DeFT', 'A_oracle']),
                  ('CI vs DeFT_tm', ['CI_heur', 'CI_heurLA', 'CI_ql', 'CI_qlLA']),
                  ('FULL vs DeFT_tm', ['FULL_heur', 'FULL_heurLA', 'FULL_ql', 'FULL_qlLA'])]
    for ax, (title, vs) in zip(axes, bar_panels):
        width = 0.8 / len(vs)
        for j, v in enumerate(vs):
            ms = [paired(v, 'DeFT_tm', p, m, 'THR')[:2] for p, m in EVAL_SCENARIOS]
            xs = [i + (j - (len(vs) - 1) / 2) * width for i in range(len(labels))]
            bars = ax.bar(xs, [x[0] for x in ms], width * 0.9, yerr=[x[1] for x in ms], color=STYLE[v][0], label=v,
                          capsize=2, error_kw=dict(elinewidth=0.8, ecolor='#52514e'))
            for bar, (p, m) in zip(bars, EVAL_SCENARIOS):
                if any(lower.get((v, p, m, s)) or lower.get(('DeFT_tm', p, m, s)) for s in seeds):
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
    axes[0].set_ylabel(f'saturation throughput vs DeFT_tm (%)\npaired over {len(seeds)} seeds, 95 % CI (secondary)')
    fig.suptitle('hatched: the variant or DeFT_tm is not saturated within the load sweep on some seed (capped)', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'saturation.png'), dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, name, better in ((axes[0], 'THR', 'higher'), (axes[1], 'LAT', 'lower')):
        xs = [x for x in prim if x['metric'] == name]
        ys = list(range(len(xs)))[::-1]
        for y, x in zip(ys, xs):
            col = '#2a78d6' if x['verdict'] == 'better' else ('#eb6834' if x['verdict'] == 'worse' else '#b0afa9')
            ax.errorbar([x['effect_pct']], [y], xerr=[[x['effect_pct'] - x['ci_low']], [x['ci_high'] - x['effect_pct']]],
                        fmt='o', color=col, capsize=3, ms=6)
        ax.axvline(0, color='#52514e', lw=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels([f'{x["variant"]} vs {x["reference"]}' for x in xs], fontsize=8)
        ax.set_xlabel(f'% change, mean over 11 scenarios ({better} is better)')
        ax.set_title({'THR': 'Saturation throughput', 'LAT': 'Mean latency at ~0.5 Lsat'}[name], fontsize=10)
        ax.grid(True, axis='x', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    fig.suptitle('Primary comparisons: 95 % CI over seeds; blue = significantly better, orange = significantly worse '
                 '(Holm, 16 tests), gray = not significant', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'primary.png'), dpi=130)
    plt.close(fig)

    # ---- summary.md ----
    L = [f'# v2 evaluation summary (seeds {seeds[0]}-{seeds[-1]}; generated by report_v2.py)', '',
         f'Runs: {len(R)} of {expected}; missing: {len(missing)}; dead-end events: {dead}; '
         f'VL-proxy mismatches: {mism} of {len(vl)}; DeFT_tm identical to DeFT on uniform/localized/movinghot: '
         f'{ident_ok} of {ident} runs.', '',
         '## Primary results (pre-registered; Holm over 16 tests)', '',
         'Effect: mean over the 11 scenarios of the per-seed log ratio, shown as % change with a 95 % CI over seeds.',
         'THR: higher is better. LAT (mean latency at ~0.5 Lsat): lower is better.', '',
         '| variant | reference | metric | effect % | 95 % CI | p | p (Holm) | verdict | THR lower-bound cells |',
         '|---|---|---|---|---|---|---|---|---|']
    for x in prim:
        L.append(f'| {x["variant"]} | {x["reference"]} | {x["metric"]} | {x["effect_pct"]:+.2f} | '
                 f'[{x["ci_low"]:+.2f}, {x["ci_high"]:+.2f}] | {x["p"]:.3g} | {x["p_holm"]:.3g} | {x["verdict"]} | '
                 f'{x["lower_bound_cells"] if x["metric"] == "THR" else "-"} |')
    L.append('')

    def table(name, title, pairs):
        L.append(f'## {title} (secondary: per-scenario, unadjusted 95 % CI; `°` = CI excludes 0, not a significance claim)')
        L.append('')
        L.append('| variant vs ref | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
        L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
        for a, b in pairs:
            cells = []
            for p, m in EVAL_SCENARIOS:
                r = next(x for x in rows if x['variant'] == a and x['reference'] == b and x['pattern'] == p and x['mask'] == m)
                mu, h = r[name + '_pct'], r[name + '_ci']
                mark = '°' if (mu - h > 0 or mu + h < 0) else ''
                lb = '≥' if name == 'THR' and r['THR_lower_bound_seeds'] else ''
                cells.append(f'{lb}{mu:+.1f}±{h:.1f}{mark}')
            L.append(f'| {a} vs {b} | ' + ' | '.join(cells) + ' |')
        L.append('')

    allpairs = PRIMARY + [x for x in SECONDARY if x not in PRIMARY]
    table('THR', 'Saturation throughput, % change (`≥`: a capped seed involved)', allpairs)
    table('LAT', 'Mean latency at ~0.5 Lsat, % change', allpairs)
    table('LATnear', 'Mean latency at ~1.0 Lsat (4th load), % change', allpairs)
    table('P99near', 'p99 latency at ~1.0 Lsat (4th load), % change', allpairs)

    L.append('## Saturation throughput (flits/node/cycle), mean ± 95 % CI; `≥` = capped on some seed')
    L.append('')
    L.append('| variant | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
    L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
    for v in VARS:
        cells = []
        for p, m in EVAL_SCENARIOS:
            r = next(x for x in srow if x['variant'] == v and x['pattern'] == p and x['mask'] == m)
            cells.append(('≥' if r['lower_bound_seeds'] else '') + f'{r["sat_throughput"]:.4f}±{r["ci95"]:.4f}')
        L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
    L.append('')
    for idx, nm in ((LOW, '~0.5 Lsat'), (NEAR, '~1.0 Lsat')):
        L.append(f'## VL usage imbalance (max/mean over functional VLs) at {nm}')
        L.append('')
        L.append('| variant | ' + ' | '.join(f'{p} {m}' for p, m in EVAL_SCENARIOS) + ' |')
        L.append('|---|' + '---|' * len(EVAL_SCENARIOS))
        for v in VARS:
            cells = []
            for p, m in EVAL_SCENARIOS:
                mu, h = ci(vals(v, p, m, LP[k(p, m)]['eval'][idx], 'imb'))
                cells.append(f'{mu:.2f}±{h:.2f}')
            L.append(f'| {v} | ' + ' | '.join(cells) + ' |')
        L.append('')
    if missing:
        L.append('## Missing runs')
        L += [f'- {x}' for x in missing]
    open(os.path.join(out_dir, 'summary.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('written', out_dir)


if __name__ == '__main__':
    main()
