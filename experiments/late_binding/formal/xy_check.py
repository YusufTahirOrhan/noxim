"""v24 A2: model check of the relations without path adaptivity on the interposer, results_v24_xy/formal_xy.md.

Run as upkeep_check.py: impl_relation_check.UP_KEEP = True (the Up channel carries the VN the packet has on the interposer,
the destination chiplet is VN1), both VNs explored on every Horizontal -> Down hop of a VN0 packet, R3 on the input VN, the F1
source rule. Relations (chip_tm, ipos_tm, exit, entry):
  CI_XY_XY    (XY, XY, fixed, late)    late entry, XY on the interposer (CI_heurLA_X, CI_qlLA_X, CI_rand_X, CI_heur_X)
  FULL_XY_XY  (XY, XY, late, late)     late exit and entry, XY on both layers (FULL_qlLA_X)
  CI_XY_O1    (XY, O1, fixed, late)    late entry, the VN-split order (CI_heurLA_O, CI_qlLA_O)
  FULL_XY_O1  (XY, O1, late, late)     late exit and entry with the VN-split order
  FIXED_XY_O1 (XY, O1, fixed, fixed)   fixed pair with the VN-split order (DeFT_P_O1, DeFT_Dis with ipos_tm O1)
O1: on the interposer a VN0 packet is routed XY and a VN1 packet YX; the model takes the interposer turn model from the VN of the
state, as the simulator does. Two extra relations cover the plain option ipos_tm YX on 2x2: CI_XY_YX and FIXED_XY_YX.

Masks: all 897 masks of `impl_relation_check.py all` on 2x2; the v4 masks on 3x3 (fault-free, north, 20 random) and on 4x4
(fault-free, north). Negative control: R3 and the F1 source rule removed on 2x2 fault-free; the check must then report a cycle.
Usage: python3 xy_check.py NPROC OUT.md
"""
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import impl_relation_check as I  # noqa: E402

RELATIONS = ['CI_XY_XY', 'FULL_XY_XY', 'CI_XY_O1', 'FULL_XY_O1', 'FIXED_XY_O1']
EXTRA_2X2 = ['CI_XY_YX', 'FIXED_XY_YX']
LABEL = {'CI_XY_XY': 'CI_XY_XY (XY, XY, fixed, late)', 'FULL_XY_XY': 'FULL_XY_XY (XY, XY, late, late)', 'CI_XY_O1': 'CI_XY_O1 (XY, O1, fixed, late)',
         'FULL_XY_O1': 'FULL_XY_O1 (XY, O1, late, late)', 'FIXED_XY_O1': 'FIXED_XY_O1 (XY, O1, fixed, fixed)',
         'CI_XY_YX': 'CI_XY_YX (XY, YX, fixed, late), extra', 'FIXED_XY_YX': 'FIXED_XY_YX (XY, YX, fixed, fixed), extra'}


def _init(cx, cy):
    I.set_size(cx, cy, 4, 4)
    I.UP_KEEP = True


def _neg(_):
    I.UP_KEEP = True
    I.NO_R3 = True
    r = I.job(('A_fixed_XY', frozenset()))
    I.NO_R3 = False
    return r


def run(cx, cy, nproc, masks, lean, relations):
    jobs = [(n, m) for n in relations for m in masks]
    t = time.time()
    with Pool(nproc, initializer=_init, initargs=(cx, cy)) as pool:
        res = pool.map(I.job_lean if lean else I.job, jobs, chunksize=2)
    return res, time.time() - t


def main():
    nproc, out = int(sys.argv[1]), sys.argv[2]
    L = ['# v24 A2: model check of the XY and VN-split relations (formal/xy_check.py; impl_relation_check.UP_KEEP = True)', '',
         'Relations are (chip_tm, ipos_tm, exit, entry). O1: on the interposer a VN0 packet is routed XY and a VN1 packet YX; the model takes the',
         'interposer turn model from the VN of the state. Up channel = the VN the packet has on the interposer, destination chiplet VN1, the boundary',
         'round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN, the F1 source rule.',
         'Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).', '']
    all_ok = True
    for name, (cx, cy), masks, lean, rels in (
            ('2x2', (2, 2), I.masks(), False, RELATIONS + EXTRA_2X2),
            ('3x3', (3, 3), [m for _, m in I.size_masks(3, 3, 20)], True, RELATIONS),
            ('4x4', (4, 4), [m for _, m in I.size_masks(4, 4, 0)], True, RELATIONS)):
        res, el = run(cx, cy, nproc, masks, lean, rels)
        L += ['## %s: %d masks x %d relations, %.0f s wall' % (name, len(masks), len(rels), el), '',
              '| relation | checks | cyclic CDG | masks with dead ends | masks with livelock | longest path (hops) | largest CDG (nodes / edges) |',
              '|---|---|---|---|---|---|---|']
        for n in rels:
            r = [x for x in res if x[0] == n]
            bad = sum(not x[2] for x in r), sum(x[3] > 0 for x in r), sum(not x[4] for x in r)
            all_ok = all_ok and not any(bad)
            big = max(r, key=lambda x: x[6])
            L.append('| %s | %d | %d | %d | %d | %d | %d / %d |' % (LABEL[n], len(r), bad[0], bad[1], bad[2], max(x[5] for x in r), big[6], big[7]))
        L.append('')
        print('\n'.join(L[-len(rels) - 3:]), flush=True)
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
