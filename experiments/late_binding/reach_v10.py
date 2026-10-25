"""v10 A6: network reachability versus VL fault rate (as DeFT's Fig. 7), results_v10/report/reachability.{csv,png,pdf}.

Masks: rates 1/16, 2/16 and 4/16 of all VLs per size (k = floor(rate x #VLs): 2x2 1/2/4, 3x3 2/4/9, 4x4 4/8/16).
Faulty VLs are bidirectional. Up to 1000 distinct random masks per (size, rate), drawn with random.Random(2210),
keeping only masks with at least one functional VL per chiplet (for 2x2, k = 1 and 2 enumerate all masks).
Reachability = fraction of ordered (source, destination) chiplet-router pairs (source != destination) with a legal
path under the method; mean and worst case over the masks. Inter-chiplet-only fractions are reported as well.
Method definitions (DECISIONS.md, BASELINES_DESIGN.md):
* DeFT: its LUT for the mask assigns a functional exit and entry VL to every pair (the LUT loader rejects a faulty
  selection), and every fixed functional pair is deliverable (formal checks v1/v4) -> reachable iff both chiplets
  have a functional VL (always, for the kept masks).
* CI, FULL: no dead end for any VL mask (formal checks v1/v4/v7) -> reachable.
* MTR (best case): fixed turn restrictions (results_v10/mtr_config.json). A source may use any functional boundary
  router it can reach under them; a destination may be entered through any functional boundary router that can
  reach it.
* RC: fixed permission tree. A source can use only its own (fault-free) nearest boundary router's RC buffer; the
  entry may be any functional boundary router of the destination chiplet.
"""
import csv
import itertools
import json
import math
import os
import random

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.join(HERE, 'results_v10')
W = H = 4
SLOTS = [(1, 0), (W - 1, 1), (W - 2, H - 1), (0, H - 2)]
SLOT_NAMES = ['N', 'E', 'S', 'W']
SIZES = {'2x2': (2, 2), '3x3': (3, 3), '4x4': (4, 4)}
RATES = [1 / 16, 2 / 16, 4 / 16]
MAX_MASKS = 1000
DRAW_SEED = 2210
METHODS = ['DeFT', 'CI', 'FULL', 'MTR', 'RC']
LOCAL = [(x, y) for y in range(H) for x in range(W)]


def xy_first_last(a, b):
    (x, y), (tx, ty) = a, b
    first = 'E' if tx > x else 'W' if tx < x else 'S' if ty > y else 'N'
    last = 'S' if ty > y else 'N' if ty < y else 'E' if tx > x else 'W'
    return first, last


def local_reach(cfg):
    """For one chiplet: outbound[r] = slots r can exit through; inbound[r] = slots that can deliver to r (MTR); and
    RC's nearest slot of each router."""
    ain = {SLOT_NAMES.index(k): set(v) for k, v in cfg['allowed_inbound_turns'].items()}
    aout = {SLOT_NAMES.index(k): set(v) for k, v in cfg['allowed_outbound_turns'].items()}
    outb, inb, near = {}, {}, {}
    for r in LOCAL:
        outb[r] = {i for i, b in enumerate(SLOTS) if r == b or xy_first_last(r, b)[1] in aout[i]}
        inb[r] = {i for i, b in enumerate(SLOTS) if r == b or xy_first_last(b, r)[0] in ain[i]}
        near[r] = min(range(len(SLOTS)), key=lambda i: (abs(SLOTS[i][0] - r[0]) + abs(SLOTS[i][1] - r[1]), i))
    return outb, inb, near


def masks(size, k, rnd):
    cx, cy = SIZES[size]
    nc, nvl = cx * cy, 4 * cx * cy

    def valid(m):
        return all(any(v not in m for v in range(4 * c, 4 * c + 4)) for c in range(nc))
    total = math.comb(nvl, k)
    if total <= 4 * MAX_MASKS:
        allm = [frozenset(c) for c in itertools.combinations(range(nvl), k)]
        allm = [m for m in allm if valid(m)]
        if len(allm) <= MAX_MASKS:
            return allm
        return rnd.sample(allm, MAX_MASKS)
    out, seen, tries = [], set(), 0
    while len(out) < MAX_MASKS and tries < 200 * MAX_MASKS:
        tries += 1
        m = frozenset(rnd.sample(range(nvl), k))
        if m in seen or not valid(m):
            continue
        seen.add(m)
        out.append(m)
    return out


def reach(size, mask, method, tables):
    cx, cy = SIZES[size]
    nc = cx * cy
    n = nc * len(LOCAL)
    pairs_all = n * (n - 1)
    intra = nc * len(LOCAL) * (len(LOCAL) - 1)
    inter_total = pairs_all - intra
    func = {c: {s for s in range(4) if 4 * c + s not in mask} for c in range(nc)}
    if method in ('DeFT', 'CI', 'FULL'):
        ok_inter = inter_total if all(func[c] for c in range(nc)) else None
        assert ok_inter is not None
    else:
        outb, inb, near = tables
        # per chiplet: sources able to leave, destinations able to be entered
        can_out = {c: sum(1 for r in LOCAL if (outb[r] & func[c] if method == 'MTR' else near[r] in func[c]))
                   for c in range(nc)}
        can_in = {c: sum(1 for r in LOCAL if (inb[r] & func[c] if method == 'MTR' else func[c])) for c in range(nc)}
        ok_inter = sum(can_out[a] * can_in[b] for a in range(nc) for b in range(nc) if a != b)
    return (intra + ok_inter) / pairs_all, ok_inter / inter_total


def main():
    cfg = json.load(open(os.path.join(R10, 'mtr_config.json')))
    tables = local_reach(cfg)
    rnd = random.Random(DRAW_SEED)
    rows = []
    for size in SIZES:
        nvl = 4 * SIZES[size][0] * SIZES[size][1]
        for rate in RATES:
            k = int(math.floor(rate * nvl))
            ms = masks(size, k, rnd)
            for method in METHODS:
                vals = [reach(size, m, method, tables) for m in ms]
                rows.append(dict(size=size, fault_rate=rate, faulty_vls=k, n_masks=len(ms), method=method,
                                 mean_all=sum(v[0] for v in vals) / len(vals), worst_all=min(v[0] for v in vals),
                                 mean_inter=sum(v[1] for v in vals) / len(vals), worst_inter=min(v[1] for v in vals)))
    os.makedirs(os.path.join(R10, 'report'), exist_ok=True)
    with open(os.path.join(R10, 'report', 'reachability.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: (f'{v:.6f}' if isinstance(v, float) else v) for k, v in r.items()})
    sty = {'DeFT': ('#52514e', 's', '--'), 'CI': ('#1baf7a', 'o', '-'), 'FULL': ('#2a78d6', 'D', '-'),
           'MTR': ('#c0392b', 'v', '-'), 'RC': ('#eb6834', '^', '-')}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, size in zip(axes, SIZES):
        for method in METHODS:
            rs = [r for r in rows if r['size'] == size and r['method'] == method]
            xs = [100 * r['fault_rate'] for r in rs]
            off = {'DeFT': -0.6, 'CI': -0.3, 'FULL': 0.0, 'MTR': 0.3, 'RC': 0.6}[method]
            ax.plot([x + off for x in xs], [100 * r['mean_all'] for r in rs], marker=sty[method][1], ls=sty[method][2],
                    color=sty[method][0], label=method if method not in ('CI', 'FULL') else f'{method} (ours)')
            ax.scatter([x + off for x in xs], [100 * r['worst_all'] for r in rs], marker='_', s=120,
                       color=sty[method][0])
        ax.set_title(f'{size} ({4 * SIZES[size][0] * SIZES[size][1]} VLs)', fontsize=10)
        ax.set_xticks([100 * r for r in RATES])
        ax.set_xticklabels([f'{100 * r:g} %\n({int(math.floor(r * 4 * SIZES[size][0] * SIZES[size][1]))} VLs)'
                            for r in RATES])
        ax.set_xlabel('faulty VLs')
        ax.grid(True, axis='y', color='#e6e5e1', lw=0.6)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel('network reachability (% of ordered pairs)')
    axes[0].legend(frameon=False, fontsize=8, loc='lower left')
    fig.suptitle('Reachability vs VL fault rate: mean over up to 1000 random masks (line), worst mask (dash)',
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(R10, 'report', f'reachability.{ext}'), dpi=130)
    plt.close(fig)
    for r in rows:
        print(r['size'], f'{r["fault_rate"]:.4f}', r['faulty_vls'], r['n_masks'], r['method'],
              f'{100 * r["mean_all"]:.2f}', f'{100 * r["worst_all"]:.2f}', f'{100 * r["mean_inter"]:.2f}',
              f'{100 * r["worst_inter"]:.2f}')


if __name__ == '__main__':
    main()
