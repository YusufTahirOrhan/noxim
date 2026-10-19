"""v6 step 1: bottleneck diagnosis on 4x4 (descriptive), results_v6/bottleneck*.

Runs (statistics flag on, -deft_lb stats_file): 4x4 uniform and localized fault-free; DeFT_tm(rho*) (through its
traffic-identical DEFT_LB proxy: the statistics hook only runs under DEFT_LB), CI_heurLA and FULL_heurLA (v5
parameters); loads 0.8, 1.0, 1.2 x Lsat (v5 load points); seeds 101-103.
The reference LUT for "entry differs from the LUT" is the uniform DeFT(rho*) LUT of 4x4 for CI and FULL (CI takes
its exit from it; FULL does not use it) and DeFT_tm's own LUT for the proxy (sanity check: 0 differences).
Usage: python3 bottleneck_v6.py run [nproc]   -> results_v6/bottleneck_raw (deleted after aggregation)
       python3 bottleneck_v6.py analyze       -> results_v6/bottleneck_agg.json, bottleneck_*.png, bottleneck_tables.md
"""
import glob
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R6 = os.path.join(HERE, 'results_v6')
RAW = os.path.join(R6, 'bottleneck_raw')
SIZE = '4x4'
SCEN = [('uniform', '0x0'), ('localized', '0x0')]
LOADS = {'0.8': 2, '1.0': 3, '1.2': 4}
SEEDS = (101, 102, 103)
LP = json.load(open(os.path.join(HERE, 'results_v5', 'load_points.json')))
CH = json.load(open(os.path.join(HERE, 'results_v5', 'tuning_choice.json')))
VARS = {'DeFT_tm': (V.inj('lut'), E5.lut_path(SIZE, CH[SIZE]['DeFT_tm'])),
        'CI_heurLA': (V2.VARIANTS['CI_heurLA'], E5.lut_path(SIZE, CH[SIZE]['DeFT'])),
        'FULL_heurLA': (V2.VARIANTS['FULL_heurLA'], E5.lut_path(SIZE, CH[SIZE]['DeFT']))}
CLASSES = ['chip_interior', 'chip_vl', 'ipos_vl', 'ipos_interior']
W = 16


def jobs():
    js = []
    for (p, m), (ld, i), (v, (va, lut)), s in [(a, b, c, d) for a in SCEN for b in LOADS.items()
                                                for c in VARS.items() for d in SEEDS]:
        rate = LP[f'{SIZE}__{p}__{m}']['eval'][i]
        name = f'bn__{v}__{p}__{ld}__s{s}'
        args = common_args(s, m, traffic=E5.REL + f'traffic_{SIZE}/{p}_{rate:.4f}.txt', lut=lut) + \
            E5.size_args(SIZE) + va + E5.SIM + ['-deft_lb', 'stats_file', os.path.join(RAW, name + '.stats.json')]
        js.append((name, args))
    return js


def analyze():
    agg = {}
    for f in sorted(glob.glob(os.path.join(RAW, '*.stats.json'))):
        _, v, p, ld, s = os.path.basename(f)[:-len('.stats.json')].split('__')
        d = json.load(open(f))
        summ = json.load(open(f.replace('.stats.json', '.json')))
        T = d['measured_cycles']
        ps = d['packet_size_flits']
        a = agg.setdefault(f'{v}|{p}|{ld}', {'runs': 0, 'class': {c: [0, 0.0, 0.0] for c in CLASSES},
                                              'link': {}, 'vl': {}, 'inter': 0, 'lut_known': 0, 'entry_diff': 0,
                                              'exit_diff': 0, 'extra': {}, 'entry_fix': {}, 'entry_fix_ipos': {},
                                              'exit_fix': {}, 'latency': [], 'accepted': []})
        a['runs'] += 1
        a['latency'].append(summ['summary']['global_average_delay_cycles'])
        a['accepted'].append(summ['summary']['average_ip_throughput_flits_per_cycle_per_ip'])
        for r in d['routers']:
            c = a['class'][r['class']]
            c[0] += r['heads']
            c[1] += r['resid_sum']
            c[2] += r['front_sum']
            layer = 'ipos' if r['class'].startswith('ipos') else 'chip'
            for dirn in range(4):
                k = f'{layer},{r["x"]},{r["y"]},{dirn}'
                a['link'][k] = a['link'].get(k, 0.0) + r['fwd'][dirn] * ps / T
            if r['class'] in ('chip_vl', 'ipos_vl'):
                k = f'{"down" if layer == "chip" else "up"},{r["x"]},{r["y"]}'
                a['vl'][k] = a['vl'].get(k, 0.0) + r['fwd'][5] * ps / T
        for k in ('inter', 'lut_known'):
            a[k] += d['inter_packets' if k == 'inter' else 'lut_known']
        a['entry_diff'] += d['entry_differs_from_lut']
        a['exit_diff'] += d['exit_differs_from_lut']
        for src, dst in (('extra_hops_vs_lut_path', 'extra'), ('entry_fixed_remaining_hops', 'entry_fix'),
                         ('entry_fixed_after_interposer_hops', 'entry_fix_ipos'), ('exit_fixed_remaining_hops', 'exit_fix')):
            for kk, vv in d[src].items():
                a[dst][kk] = a[dst].get(kk, 0) + vv
    for a in agg.values():           # averages over runs
        for k in a['link']:
            a['link'][k] /= a['runs']
        for k in a['vl']:
            a['vl'][k] /= a['runs']
    json.dump(agg, open(os.path.join(R6, 'bottleneck_agg.json'), 'w'), indent=0)
    return agg


def report(agg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    L = ['# v6 step 1: bottleneck statistics (4x4, fault-free; generated by bottleneck_v6.py)', '',
         'Averages over seeds 101-103. DeFT_tm = DEFT_LB proxy with DeFT_tm(rho*)\'s LUT (traffic-identical to DeFT_tm).', '']
    L += ['## Head-flit waiting per hop, by router class (cycles)', '',
          'resid = input-buffer residence of a head flit (arrival in the buffer to forwarding); front = wait at the '
          'buffer front (routing, arbitration, credits) until forwarding. Per hop = per router traversal.', '',
          '| pattern | load | variant | ' + ' | '.join(f'{c} resid / front' for c in CLASSES) + ' | mean latency | accepted |',
          '|---|---|---|' + '---|' * len(CLASSES) + '---|---|']
    for p, _ in SCEN:
        for ld in LOADS:
            for v in VARS:
                a = agg[f'{v}|{p}|{ld}']
                cells = []
                for c in CLASSES:
                    h, rs, fr = a['class'][c]
                    cells.append(f'{rs / h:.2f} / {fr / h:.2f}' if h else 'n/a')
                L.append(f'| {p} | {ld} | {v} | ' + ' | '.join(cells) +
                         f' | {sum(a["latency"]) / len(a["latency"]):.1f} | {sum(a["accepted"]) / len(a["accepted"]):.4f} |')
    L.append('')
    L += ['## Link and VL utilisation (flits/cycle per direction; mean / max over links)', '',
          '| pattern | load | variant | chiplet links mean / max | interposer links mean / max | VL down mean / max | '
          'VL up mean / max |', '|---|---|---|---|---|---|---|']
    for p, _ in SCEN:
        for ld in LOADS:
            for v in VARS:
                a = agg[f'{v}|{p}|{ld}']

                def mm(sel):
                    xs = [x for k, x in sel]
                    return f'{sum(xs) / len(xs):.3f} / {max(xs):.3f}' if xs else 'n/a'
                ch = [(k, x) for k, x in a['link'].items() if k.startswith('chip') and _exists(k)]
                ip = [(k, x) for k, x in a['link'].items() if k.startswith('ipos') and _exists(k)]
                L.append(f'| {p} | {ld} | {v} | {mm(ch)} | {mm(ip)} | {mm([(k, x) for k, x in a["vl"].items() if k.startswith("down")])} | '
                         f'{mm([(k, x) for k, x in a["vl"].items() if k.startswith("up")])} |')
    L.append('')
    L += ['## Entry/exit VL vs the LUT\'s choice, and the extra hops it costs (inter-chiplet packets)', '',
          '| pattern | load | variant | packets | entry differs | exit differs | extra hops vs LUT path: mean | share with '
          '>0 extra hops | distribution (hops: share) |', '|---|---|---|---|---|---|---|---|---|']
    for p, _ in SCEN:
        for ld in LOADS:
            for v in VARS:
                a = agg[f'{v}|{p}|{ld}']
                n = a['lut_known']
                ex = {int(k): c for k, c in a['extra'].items()}
                tot = sum(ex.values())
                mean = sum(k * c for k, c in ex.items()) / tot if tot else float('nan')
                dist = ', '.join(f'{k}: {100 * c / tot:.1f}%' for k, c in sorted(ex.items()) if c / tot >= 0.005)
                L.append(f'| {p} | {ld} | {v} | {n} | {100 * a["entry_diff"] / n:.1f} % | {100 * a["exit_diff"] / n:.1f} % | '
                         f'{mean:+.2f} | {100 * sum(c for k, c in ex.items() if k > 0) / tot:.1f} % | {dist} |')
    L.append('')
    L += ['## Where the entry decision is fixed (interposer)', '',
          '"remaining hops" = interposer hops still to go to the chosen entry VL when only one candidate was left '
          '(0 = fixed by taking the VL while others were open; -1 = fixed before the interposer, e.g. a fixed pair). '
          '"after k interposer hops" = interposer hops already travelled at that moment.', '',
          '| pattern | load | variant | remaining hops when fixed (share) | interposer hops travelled before fixing (share) |',
          '|---|---|---|---|---|']
    for p, _ in SCEN:
        for ld in LOADS:
            for v in VARS:
                a = agg[f'{v}|{p}|{ld}']
                for key in ('entry_fix', 'entry_fix_ipos'):
                    pass
                def dist(h):
                    h = {int(k): c for k, c in h.items()}
                    t = sum(h.values())
                    return ', '.join(f'{k}: {100 * c / t:.0f}%' for k, c in sorted(h.items()) if c / t >= 0.01)
                L.append(f'| {p} | {ld} | {v} | {dist(a["entry_fix"])} | {dist(a["entry_fix_ipos"])} |')
    L.append('')
    open(os.path.join(R6, 'bottleneck_tables.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))

    # heatmaps: link utilisation per layer, 1.0 x Lsat
    for p, _ in SCEN:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        vmax = max(max(agg[f'{v}|{p}|1.0']['link'].values()) for v in VARS)
        norm = colors.Normalize(0, vmax)
        cmap = cm.get_cmap('viridis')
        for j, v in enumerate(VARS):
            a = agg[f'{v}|{p}|1.0']
            for i, layer in enumerate(('chip', 'ipos')):
                ax = axes[i][j]
                for x in range(W):
                    for y in range(W):
                        for dirn, (dx, dy) in ((1, (1, 0)), (2, (0, 1))):
                            x2, y2 = x + dx, y + dy
                            if x2 >= W or y2 >= W:
                                continue
                            back = 3 if dirn == 1 else 0
                            u = max(a['link'].get(f'{layer},{x},{y},{dirn}', 0.0), a['link'].get(f'{layer},{x2},{y2},{back}', 0.0))
                            if layer == 'chip' and (x // 4 != x2 // 4 or y // 4 != y2 // 4):
                                continue        # no link between chiplets
                            ax.plot([x, x2], [y, y2], color=cmap(norm(u)), lw=3.2, solid_capstyle='butt')
                vk = 'down' if layer == 'chip' else 'up'
                for k, u in a['vl'].items():
                    d, x, y = k.split(',')
                    if d == vk:
                        ax.scatter([int(x)], [int(y)], s=60, color=cmap(norm(u)), edgecolors='#c0392b', linewidths=1.2, zorder=3)
                ax.set_xlim(-0.6, W - 0.4)
                ax.set_ylim(W - 0.4, -0.6)
                ax.set_aspect('equal')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(f'{v}: {"chiplet layer (VL down marked)" if layer == "chip" else "interposer (VL up marked)"}',
                             fontsize=9)
        fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=axes, shrink=0.6,
                     label='link utilisation (flits/cycle, max of the two directions); VL dots: flits/cycle')
        fig.suptitle(f'4x4 {p}, fault-free, 1.0 x Lsat (v5), mean over seeds 101-103', fontsize=11)
        fig.savefig(os.path.join(R6, f'bottleneck_links_{p}.png'), dpi=110)
        plt.close(fig)

    # per-class waiting vs load (uniform and localized)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), sharey=True)
    sty = {'DeFT_tm': ('#52514e', '--', 's'), 'CI_heurLA': ('#4a3aa7', '-', '^'), 'FULL_heurLA': ('#eb6834', '-', 'v')}
    for ax, (p, _) in zip(axes, SCEN):
        width = 0.27
        for j, v in enumerate(VARS):
            a = agg[f'{v}|{p}|1.0']
            vals = [a['class'][c][1] / a['class'][c][0] if a['class'][c][0] else 0 for c in CLASSES]
            ax.bar([i + (j - 1) * width for i in range(len(CLASSES))], vals, width * 0.92, color=sty[v][0], label=v)
        ax.set_xticks(range(len(CLASSES)))
        ax.set_xticklabels(['chiplet\ninterior', 'chiplet\nVL endpoint', 'interposer\nVL endpoint', 'interposer\ninterior'])
        ax.set_title(f'4x4 {p}, 1.0 x Lsat', fontsize=10)
        ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel('mean head-flit buffer residence per hop (cycles)')
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(R6, 'bottleneck_wait.png'), dpi=120)
    plt.close(fig)


def _exists(k):
    layer, x, y, d = k.split(',')
    x, y, d = int(x), int(y), int(d)
    dx, dy = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}[d]
    x2, y2 = x + dx, y + dy
    if not (0 <= x2 < W and 0 <= y2 < W):
        return False
    return layer == 'ipos' or (x // 4 == x2 // 4 and y // 4 == y2 // 4)


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        os.makedirs(RAW, exist_ok=True)
        res = run_jobs(jobs(), RAW, nproc=int(sys.argv[2]) if len(sys.argv) > 2 else 12, timeout=7200)
        print('runs', len(res), 'missing', sum(1 for v in res.values() if v is None))
    else:
        agg = analyze()
        report(agg)
        if len(sys.argv) > 2 and sys.argv[2] == 'cleanup':
            shutil.rmtree(RAW)
            print('raw outputs deleted')
