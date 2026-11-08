"""LUT entry-selection analysis (review v22): path lengths of DeFT's LUT pairs against alternatives.

For every inter-chiplet (source router, destination router) pair of the fault-free instance:
  * LUT pair       : source -> LUT exit VL -> Down -> interposer -> LUT entry VL -> Up -> destination (XY distances + 2)
  * dest-nearest   : same exit, entry = the functional VL of the destination chiplet nearest to the destination router
                     (the entry rule of DeFT-Dis, and the natural reading of the paper's second selection, which is
                     "based on the packets headed for the destination-chiplet routers")
  * minimal pair   : the pair minimising the total path (XY-SP's choice)
Also: the LUT's entry load per VL, in (source router, destination chiplet) keys, and the share of boundary-router
sources whose LUT exit is not their own VL (the F1 rule matters only for those).
Usage: python3 lut_path_analysis.py LUT.yaml CX CY
"""
import sys
import yaml

path, cx, cy = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
W, H = 4, 4
FW = cx * W
C = cx * cy
SLOTS = [(1, 0), (W - 1, 1), (W - 2, H - 1), (0, H - 2)]


def rid(c, lx, ly):
    return ((c // cx) * H + ly) * FW + (c % cx) * W + lx


def chip(r):
    return (r // FW // H) * cx + (r % FW) // W


def xy(r):
    return r % FW, r // FW


def man(a, b):
    (x0, y0), (x1, y1) = xy(a), xy(b)
    return abs(x0 - x1) + abs(y0 - y1)


VL = {c * 4 + s: rid(c, lx, ly) for c in range(C) for s, (lx, ly) in enumerate(SLOTS)}   # vl id -> chiplet endpoint router
OWN = {r: v for v, r in VL.items()}
d = yaml.safe_load(open(path))
free = [e for e in d['entries'] if int(e['key']['fault_mask_id'], 16) == 0]
lut = {(e['key']['source_router_id'], e['key']['destination_chiplet_id']):
       (e['value']['source_exit']['selected_vl_id'], e['value']['destination_entry']['selected_vl_id']) for e in free}
N = FW * cy * H
tot_lut = tot_dn = tot_min = 0.0
npairs = 0
entry_load = {v: 0 for v in VL}
exit_load = {v: 0 for v in VL}
for (s, cd), (ex, en) in lut.items():
    entry_load[en] += 1
    exit_load[ex] += 1
bnd_other = sum(1 for (s, cd), (ex, en) in lut.items() if s in OWN and ex != OWN[s])
for s in range(N):
    for t in range(N):
        if chip(s) == chip(t):
            continue
        ex, en = lut[(s, chip(t))]
        L = man(s, VL[ex]) + 1 + man(VL[ex], VL[en]) + 1 + man(VL[en], t)
        en2 = min((v for v in VL if v // 4 == chip(t)), key=lambda v: (man(VL[v], t), v))
        L2 = man(s, VL[ex]) + 1 + man(VL[ex], VL[en2]) + 1 + man(VL[en2], t)
        Lm = min(man(s, VL[a]) + 1 + man(VL[a], VL[b]) + 1 + man(VL[b], t)
                 for a in VL if a // 4 == chip(s) for b in VL if b // 4 == chip(t))
        tot_lut += L
        tot_dn += L2
        tot_min += Lm
        npairs += 1
print('%s: %d inter-chiplet router pairs (fault-free)' % (path, npairs))
print('  mean hops  LUT pair: %.3f   LUT exit + destination-nearest entry: %.3f   minimal pair: %.3f'
      % (tot_lut / npairs, tot_dn / npairs, tot_min / npairs))
print('  LUT exit load per VL (keys):  %s' % exit_load)
print('  LUT entry load per VL (keys): %s' % entry_load)
print('  boundary-router sources whose LUT exit is not their own VL: %d of %d' % (bnd_other, sum(1 for (s, cd) in lut if s in OWN)))
