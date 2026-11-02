"""v17 report: VC imbalance, VC shares and VC-wait per method and link class (results_v17_vcdiag/report/).

Reads vc_runs.csv and run_summary.csv. Means over seeds 41-43.
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v17_vcdiag')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
PATTERNS = ['uniform', 'hotspot']
CLASSES = ['chip_towards', 'chip_away', 'ipos', 'vl_down', 'vl_up']
CNAME = {'chip_towards': 'chiplet, towards VL', 'chip_away': 'chiplet, away from VL', 'ipos': 'interposer',
         'vl_down': 'Down VL', 'vl_up': 'Up VL'}
METHODS = ['DeFT', 'MTR_VN', 'DeFT_Dis', 'CI_qlLA_G', 'FULL_qlLA_G', 'MTR', 'RC', 'DeFT_LUT_noVN']
MNAME = {'DeFT': 'DeFT(rho*)', 'MTR_VN': 'MTR routes + DeFT VNs', 'DeFT_Dis': 'DeFT-Dis', 'CI_qlLA_G': 'LB-I (CI_qlLA_G)',
         'FULL_qlLA_G': 'LB-F (FULL_qlLA_G)', 'MTR': 'MTR', 'RC': 'RC', 'DeFT_LUT_noVN': 'DeFT LUT routes, no VNs'}
NL = chr(10)
INT = ('links', 'f0', 'f1', 'abs_diff', 'held0', 'held1', 'nocredit0', 'nocredit1', 'ph0_src', 'ph0_ipos', 'ph0_dst',
       'ph0_intra', 'ph1_src', 'ph1_ipos', 'ph1_dst', 'ph1_intra')


def load():
    rows = list(csv.DictReader(open(os.path.join(RES, 'vc_runs.csv'))))
    summ = list(csv.DictReader(open(os.path.join(RES, 'run_summary.csv'))))
    for r in rows:
        for k in INT:
            r[k] = int(r[k])
        r['occ0'], r['occ1'] = float(r['occ0']), float(r['occ1'])
    return rows, summ


def metrics(rs):
    """Over runs: per-run values averaged (each run has the same weight)."""
    imb, sh1, wait, held, nocr, occ0, occ1, tot = [], [], [], [], [], [], [], []
    for r in rs:
        t = r['f0'] + r['f1']
        if not t:
            continue
        imb.append(r['abs_diff'] / t)
        sh1.append(r['f1'] / t)
        wait.append((r['held0'] + r['held1'] + r['nocredit0'] + r['nocredit1']) / t)
        held.append((r['held0'] + r['held1']) / t)
        nocr.append((r['nocredit0'] + r['nocredit1']) / t)
        occ0.append(r['occ0'])
        occ1.append(r['occ1'])
        tot.append(t)
    m = lambda x: sum(x) / len(x) if x else float('nan')
    return dict(imb=m(imb), sh1=m(sh1), wait=m(wait), held=m(held), nocredit=m(nocr), occ0=m(occ0), occ1=m(occ1), flits=m(tot))


def combined(rs_by_seed):
    """Sum several classes within each run first, then average over runs."""
    per = defaultdict(lambda: defaultdict(float))
    for r in rs_by_seed:
        p = per[r['seed']]
        for k in ('f0', 'f1', 'abs_diff', 'held0', 'held1', 'nocredit0', 'nocredit1'):
            p[k] += r[k]
    return metrics([dict(p, occ0=0.0, occ1=0.0) for p in per.values()])


def table(rows, load_):
    idx = defaultdict(list)
    for r in rows:
        if r['load'] == load_:
            idx[(r['size'], r['pattern'], r['method'], r['cls'])].append(r)
    L = []
    for size in SIZES:
        for p in PATTERNS:
            L += [f'### {size} {p}, {load_} x Lsat', '',
                  '| method | ' + ' | '.join(CNAME[c] for c in CLASSES) + ' |', '|---|' + '---|' * len(CLASSES)]
            for m in METHODS:
                cells = []
                for c in CLASSES:
                    rs = idx.get((size, p, m, c), [])
                    if not rs:
                        cells.append('-')
                        continue
                    x = metrics(rs)
                    cells.append(f"{x['imb']:.2f} / {100 * (1 - x['sh1']):.0f}:{100 * x['sh1']:.0f} / {x['wait']:.2f}")
                if any(ce != '-' for ce in cells):
                    L.append(f'| {MNAME[m]} | ' + ' | '.join(cells) + ' |')
            L.append('')
    return L


def phase_table(rows):
    """DeFT: what share of each chiplet class is source-phase, destination-phase, intra-chiplet, per VC."""
    L = ['## Packet phase of the flits on chiplet links, DeFT(rho*), 1.0 x Lsat', '',
         'Share of the flits on the class, % (VC0 source / VC0 dest / VC0 intra ; VC1 source / VC1 dest / VC1 intra).', '',
         '| size | pattern | chiplet, towards VL | chiplet, away from VL |', '|---|---|---|---|']
    for size in SIZES:
        for p in PATTERNS:
            cells = []
            for c in ('chip_towards', 'chip_away'):
                rs = [r for r in rows if r['load'] == '1.0' and r['method'] == 'DeFT' and r['size'] == size and
                      r['pattern'] == p and r['cls'] == c]
                t = sum(r['f0'] + r['f1'] for r in rs)
                s = lambda k: 100.0 * sum(r[k] for r in rs) / t
                cells.append(f"{s('ph0_src'):.0f} / {s('ph0_dst'):.0f} / {s('ph0_intra'):.0f} ; "
                             f"{s('ph1_src'):.0f} / {s('ph1_dst'):.0f} / {s('ph1_intra'):.0f}")
            L.append(f'| {size} | {p} | ' + ' | '.join(cells) + ' |')
    return L + ['']


def combined_table(rows):
    """All chiplet links together, and the VC wait split on the VLs and the interposer, 1.0 x Lsat."""
    L = ['## All chiplet links together, 1.0 x Lsat', '', 'VC imbalance, both chiplet classes summed within each run.', '',
         '| size | pattern | ' + ' | '.join(MNAME[m] for m in METHODS[:-1]) + ' |', '|---|---|' + '---|' * (len(METHODS) - 1)]
    for size in SIZES:
        for p in PATTERNS:
            cells = []
            for m in METHODS[:-1]:
                rs = [r for r in rows if r['load'] == '1.0' and r['method'] == m and r['size'] == size and r['pattern'] == p and
                      r['cls'] in ('chip_towards', 'chip_away')]
                cells.append(f"{combined(rs)['imb']:.2f}")
            L.append(f'| {size} | {p} | ' + ' | '.join(cells) + ' |')
    L += ['', '## VC wait on the VLs and the interposer, 1.0 x Lsat', '',
          'Per cell: VC held / no credit, head-flit cycles per flit forwarded; then the mean downstream occupancy VC0 / VC1 (flits, capacity 4).',
          '', '| size | pattern | method | interposer | Down VL | Up VL |', '|---|---|---|---|---|---|']
    for size in SIZES:
        for p in PATTERNS:
            for m in ('DeFT', 'MTR_VN', 'CI_qlLA_G', 'FULL_qlLA_G', 'MTR', 'RC'):
                cells = []
                for c in ('ipos', 'vl_down', 'vl_up'):
                    rs = [r for r in rows if r['load'] == '1.0' and r['method'] == m and r['size'] == size and r['pattern'] == p and r['cls'] == c]
                    x = metrics(rs)
                    cells.append(f"{x['held']:.2f} / {x['nocredit']:.2f}; {x['occ0']:.2f} / {x['occ1']:.2f}")
                L.append(f'| {size} | {p} | {MNAME[m]} | ' + ' | '.join(cells) + ' |')
    return L + ['']


def rc_table(summ):
    L = ['## RC buffer and injection permission', '',
         'Mean over seeds. Occupancy per boundary router; capacity 4 slots x 8 flits.', '',
         '| size | pattern | load | mean flits | mean slots | peak flits | peak slots | permission wait per outbound packet (cycles) |',
         '|---|---|---|---|---|---|---|---|']
    for size in SIZES:
        for p in PATTERNS:
            for ld in ('0.8', '1.0'):
                rs = [r for r in summ if r['method'] == 'RC' and r['size'] == size and r['pattern'] == p and r['load'] == ld]
                m = lambda k: sum(float(r[k]) for r in rs) / len(rs)
                L.append(f"| {size} | {p} | {ld} | {m('rc_mean_flits'):.2f} | {m('rc_mean_slots'):.2f} | "
                         f"{max(int(r['rc_peak_flits']) for r in rs)} | {max(int(r['rc_peak_slots']) for r in rs)} | "
                         f"{m('rc_permission_wait'):.1f} |")
    return L + ['']


def latency_table(summ):
    L = ['## Mean latency (cycles) and accepted throughput (flits/cycle/IP), mean over seeds', '',
         '| size | pattern | load | ' + ' | '.join(MNAME[m] for m in METHODS) + ' |', '|---|---|---|' + '---|' * len(METHODS)]
    for size in SIZES:
        for p in PATTERNS:
            for ld in ('0.8', '1.0'):
                cells = []
                for m_ in METHODS:
                    rs = [r for r in summ if r['method'] == m_ and r['size'] == size and r['pattern'] == p and r['load'] == ld]
                    if not rs:
                        cells.append('-')
                        continue
                    a = sum(float(r['latency']) for r in rs) / len(rs)
                    t = sum(float(r['accepted']) for r in rs) / len(rs)
                    flag = ' **deadlock flag**' if any(r['deadlock_flag'] == '1' for r in rs) else ''
                    cells.append(f'{a:.1f} / {t:.3f}{flag}')
                L.append(f'| {size} | {p} | {ld} | ' + ' | '.join(cells) + ' |')
    return L + ['']


# Fixed order from the reference categorical palette; marker shapes are the secondary encoding, and each
# point is also identified by the legend.
COLORS = {'DeFT': '#2a78d6', 'MTR': '#eb6834', 'RC': '#1baf7a', 'DeFT_Dis': '#eda100', 'CI_qlLA_G': '#e87ba4',
          'FULL_qlLA_G': '#008300', 'MTR_VN': '#6250d6'}
MARK = {'DeFT': 'o', 'MTR': 's', 'RC': 'D', 'DeFT_Dis': '^', 'CI_qlLA_G': 'v', 'FULL_qlLA_G': 'P', 'MTR_VN': 'X'}
SIZE_LABEL_OFFSET = {'2x2': (5, 4), '3x3': (5, 4), '4x4': (5, 4)}


def figure(rows, summ):
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ad', 'axes.linewidth': 0.8, 'xtick.color': '#52514e',
                         'ytick.color': '#52514e', 'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.2), sharex=True)
    for ip, p in enumerate(PATTERNS):
        for iz, size in enumerate(SIZES):
            ax = axes[ip][iz]
            ax.grid(True, color='#e6e5e0', linewidth=0.6)
            ax.set_axisbelow(True)
            for m in COLORS:
                sel = [r for r in rows if r['method'] == m and r['size'] == size and r['pattern'] == p and r['load'] == '1.0'
                       and r['cls'] in ('chip_towards', 'chip_away')]
                x = combined(sel)['imb']
                la = [float(r['latency']) for r in summ if r['method'] == m and r['size'] == size and r['pattern'] == p
                      and r['load'] == '1.0']
                ax.scatter([x], [sum(la) / len(la)], color=COLORS[m], marker=MARK[m], s=60, edgecolor='white', linewidth=1.0,
                           label=MNAME[m], zorder=3)
            ax.set_title(f'{size}, {p}', fontsize=9.5, loc='left')
            ax.set_xlim(-0.03, 1.0)
            if iz == 0:
                ax.set_ylabel('mean latency (cycles)')
            if ip == 1:
                ax.set_xlabel('VC imbalance on chiplet links')
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, frameon=False, fontsize=8.5)
    fig.suptitle('VC imbalance on chiplet links against mean latency at 1.0 x Lsat (mean of seeds 41-43)', fontsize=10.5, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    fig.savefig(os.path.join(OUT, 'imbalance_vs_latency.png'), dpi=180)
    fig.savefig(os.path.join(OUT, 'imbalance_vs_latency.pdf'))


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, summ = load()
    L = ['# v17 report: VC usage per link class', '',
         'Means over seeds 41-43. Each cell: **VC imbalance** (sum over link directions of |f0 - f1| / sum of f0 + f1, the '
         'traffic-weighted mean of |f0 - f1| / (f0 + f1)) / **share of flits VC0:VC1** (%) / **VC-wait cycles per flit** '
         '(head-flit cycles waiting for the downstream VC, no credit or VC held, per flit forwarded).', '',
         '## Method by link class at 1.0 x Lsat', ''] + table(rows, '1.0') + \
        ['## Method by link class at 0.8 x Lsat', ''] + table(rows, '0.8') + combined_table(rows) + phase_table(rows) + rc_table(summ) + latency_table(summ) + \
        ['Figure: `imbalance_vs_latency.png` / `.pdf`.']
    open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    figure(rows, summ)
    print('\n'.join(L[L.index('## All chiplet links together, 1.0 x Lsat'):L.index('## RC buffer and injection permission')]))


if __name__ == '__main__':
    main()
