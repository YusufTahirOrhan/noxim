"""v19 K2: model check of the relations with DeFT's boundary round-robin (-deft_vn_rr 1) (results_v19_vnrr/formal_vnrr.md).

The model (impl_relation_check.explore) explores both VNs on every Horizontal -> Down hop of a VN0 packet and forbids
Horizontal -> Down in VN1, which is the option's relation: the round-robin picks one of the two explored successors, and a packet
waiting for a busy VC holds no other channel than the model's. It also explores both source VNs where the F1 rule allows them, so it covers
any state of the per-router counters.

Masks: all 897 masks of `impl_relation_check.py all` on 2x2; the v4 masks on 3x3 (fault-free, north, 20 random) and on 4x4 (fault-free, north).
Relations: fixed pair with XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP), CI, FULL, and fixed pair with odd-even (DeFT_OE_G).
Negative control: R3 and the F1 source rule removed on 2x2 fault-free; the check must then report a cyclic CDG.
Usage: python3 vnrr_check.py NPROC OUT.md
"""
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import impl_relation_check as I  # noqa: E402

RELATIONS = ['A_fixed_XY', 'CI_XY_OE', 'FULL_OE_OE', 'FIXED_OE_OE']
LABEL = {'A_fixed_XY': 'fixed pair, XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP)', 'CI_XY_OE': 'CI', 'FULL_OE_OE': 'FULL',
         'FIXED_OE_OE': 'fixed pair, odd-even (DeFT_OE_G)'}


def _init(cx, cy):
    I.set_size(cx, cy, 4, 4)


def _neg(_):
    I.NO_R3 = True
    r = I.job(('A_fixed_XY', frozenset()))
    I.NO_R3 = False
    return r


def run(cx, cy, nproc, masks, lean):
    jobs = [(n, m) for n in RELATIONS for m in masks]
    t = time.time()
    with Pool(nproc, initializer=_init, initargs=(cx, cy)) as pool:
        res = pool.map(I.job_lean if lean else I.job, jobs, chunksize=2)
    return res, time.time() - t


def main():
    nproc, out = int(sys.argv[1]), sys.argv[2]
    L = ['# v19 K2: model check with the boundary round-robin (formal/vnrr_check.py)', '',
         'Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).', '']
    all_ok = True
    for name, (cx, cy), masks, lean in (
            ('2x2', (2, 2), I.masks(), False),
            ('3x3', (3, 3), [m for _, m in I.size_masks(3, 3, 20)], True),
            ('4x4', (4, 4), [m for _, m in I.size_masks(4, 4, 0)], True)):
        res, el = run(cx, cy, nproc, masks, lean)
        L += [f'## {name}: {len(masks)} masks x {len(RELATIONS)} relations, {el:.0f} s wall', '',
              '| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |',
              '|---|---|---|---|---|---|---|']
        for n in RELATIONS:
            r = [x for x in res if x[0] == n]
            bad = sum(not x[2] for x in r), sum(x[3] > 0 for x in r), sum(not x[4] for x in r)
            all_ok = all_ok and not any(bad)
            big = max(r, key=lambda x: x[6])
            L.append(f'| {LABEL[n]} | {len(r)} | {bad[0]} | {bad[1]} | {bad[2]} | {max(x[5] for x in r)} | {big[6]} / {big[7]} |')
        L.append('')
        print('\n'.join(L[-len(RELATIONS) - 3:]), flush=True)
    with Pool(1, initializer=_init, initargs=(2, 2)) as pool:
        neg = pool.map(_neg, [0])[0]
    L += ['## Negative control', '', f'2x2, fault-free, fixed pair with XY, R3 and the F1 source rule removed: CDG acyclic = {neg[2]} '
          f'(expected False). The check can fail.', '', f'**All checks pass: {all_ok}.**']
    all_ok = all_ok and not neg[2]
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L[-5:]))
    return all_ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
