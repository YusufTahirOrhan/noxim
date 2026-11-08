"""v23 A2: model check of the relations with the paper's Up-link rule (-deft_up_keep 1), results_v23_fidelity/formal_upkeep.md.

impl_relation_check.UP_KEEP = True: the Up channel carries the VN the packet has on the interposer, the destination chiplet is
VN1 (DeFT paper, Algorithm 1 and Theorem III.4; review v22 R1). Everything else as vnrr_check.py: both VNs explored on every
Horizontal -> Down hop of a VN0 packet, R3 on the input VN, the F1 source rule.

Masks: all 897 masks of `impl_relation_check.py all` on 2x2; the v4 masks on 3x3 (fault-free, north, 20 random) and on 4x4
(fault-free, north). Relations: fixed pair with XY (DeFT, DeFT-Dis, DeFT-Ran, XY-SP), CI, FULL, fixed pair with odd-even
(DeFT_OE_G). Negative control: R3 and the F1 source rule removed on 2x2 fault-free; the check must then report a cycle.
Usage: python3 upkeep_check.py NPROC OUT.md
"""
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import impl_relation_check as I  # noqa: E402

RELATIONS = ['A_fixed_XY', 'CI_XY_OE', 'FULL_OE_OE', 'FIXED_OE_OE']
LABEL = {'A_fixed_XY': 'fixed pair, XY (DeFT-P, DeFT-B, DeFT-Dis, DeFT-Ran, XY-SP)', 'CI_XY_OE': 'CI', 'FULL_OE_OE': 'FULL',
         'FIXED_OE_OE': 'fixed pair, odd-even (DeFT_OE_G)'}


def _init(cx, cy):
    I.set_size(cx, cy, 4, 4)
    I.UP_KEEP = True


def _neg(_):
    I.UP_KEEP = True
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
    L = ['# v23 A2: model check with the paper\'s Up-link rule (formal/upkeep_check.py, impl_relation_check.UP_KEEP)', '',
         'Up channel = the VN the packet has on the interposer (both VCs of a VL form one class), destination chiplet VN1, the',
         'boundary round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN, the F1 source rule.',
         'Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).', '']
    all_ok = True
    for name, (cx, cy), masks, lean in (
            ('2x2', (2, 2), I.masks(), False),
            ('3x3', (3, 3), [m for _, m in I.size_masks(3, 3, 20)], True),
            ('4x4', (4, 4), [m for _, m in I.size_masks(4, 4, 0)], True)):
        res, el = run(cx, cy, nproc, masks, lean)
        L += ['## %s: %d masks x %d relations, %.0f s wall' % (name, len(masks), len(RELATIONS), el), '',
              '| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |',
              '|---|---|---|---|---|---|---|']
        for n in RELATIONS:
            r = [x for x in res if x[0] == n]
            bad = sum(not x[2] for x in r), sum(x[3] > 0 for x in r), sum(not x[4] for x in r)
            all_ok = all_ok and not any(bad)
            big = max(r, key=lambda x: x[6])
            L.append('| %s | %d | %d | %d | %d | %d | %d / %d |' % (LABEL[n], len(r), bad[0], bad[1], bad[2], max(x[5] for x in r), big[6], big[7]))
        L.append('')
        print('\n'.join(L[-len(RELATIONS) - 3:]), flush=True)
    with Pool(1, initializer=_init, initargs=(2, 2)) as pool:
        neg = pool.map(_neg, [0])[0]
    L += ['## Negative control', '', '2x2, fault-free, fixed pair with XY, R3 and the F1 source rule removed (Up rule of the paper): CDG acyclic = %s '
          '(expected False). The check can fail.' % neg[2], '', '**All checks pass: %s.**' % all_ok]
    all_ok = all_ok and not neg[2]
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L[-5:]))
    return all_ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
