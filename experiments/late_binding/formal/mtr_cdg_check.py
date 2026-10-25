"""Full-system channel dependency graph of MTR (results_v10/mtr_config.json), fault-free, on cx x cy grids of 4x4
chiplets with DeFT's VL positions.

Routes (deterministic): intra-chiplet XY; inter-chiplet: XY to the exit boundary router (outbound table of the source's
local position), Down, XY on the interposer to the entry VL's interposer endpoint (inbound table of the destination's
local position), Up, XY to the destination. Channels are physical (router, output port); the routing function uses the
VC drawn at injection on every hop, so an acyclic physical-channel CDG implies deadlock freedom for any VC use.
Also checks that every route uses only turns the MTR configuration allows at boundary routers.
Usage: python3 formal/mtr_cdg_check.py CONFIG.json OUT.md
"""
import json
import sys

import networkx as nx

W = H = 4
SLOTS = [(1, 0), (W - 1, 1), (W - 2, H - 1), (0, H - 2)]
SLOT_NAMES = ['N', 'E', 'S', 'W']
DIRS = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def xy_hops(a, b):
    (x, y), (tx, ty) = a, b
    out = []
    while x != tx:
        d = 'E' if tx > x else 'W'
        out.append(((x, y), d))
        x += DIRS[d][0]
    while y != ty:
        d = 'S' if ty > y else 'N'
        out.append(((x, y), d))
        y += DIRS[d][1]
    return out


def check(cfg, cx, cy):
    allowed_in = {SLOT_NAMES.index(k): set(v) for k, v in cfg['allowed_inbound_turns'].items()}
    allowed_out = {SLOT_NAMES.index(k): set(v) for k, v in cfg['allowed_outbound_turns'].items()}
    chips = [(ox * W, oy * H) for oy in range(cy) for ox in range(cx)]
    nodes = [(c, (ox + x, oy + y)) for c, (ox, oy) in enumerate(chips) for y in range(H) for x in range(W)]
    g = nx.DiGraph()
    violations = 0
    for (cs, s), (cd, d) in ((a, b) for a in nodes for b in nodes if a != b):
        chans = []
        if cs == cd:
            chans = [('C',) + h for h in xy_hops(s, d)]
        else:
            ls = (s[0] - chips[cs][0], s[1] - chips[cs][1])
            ld = (d[0] - chips[cd][0], d[1] - chips[cd][1])
            ex = cfg['outbound'][ls[1] * W + ls[0]]
            en = cfg['inbound'][ld[1] * W + ld[0]]
            b = (chips[cs][0] + SLOTS[ex][0], chips[cs][1] + SLOTS[ex][1])
            e = (chips[cd][0] + SLOTS[en][0], chips[cd][1] + SLOTS[en][1])
            out_leg = xy_hops(s, b)
            in_leg = xy_hops(e, d)
            if out_leg and out_leg[-1][1] not in allowed_out[ex]:
                violations += 1
            if in_leg and in_leg[0][1] not in allowed_in[en]:
                violations += 1
            chans = [('C',) + h for h in out_leg] + [('D', b)] + [('I',) + h for h in xy_hops(b, e)] + \
                [('U', e)] + [('C',) + h for h in in_leg]
        for u, v in zip(chans, chans[1:]):
            g.add_edge(u, v)
    acyclic = nx.is_directed_acyclic_graph(g)
    cyc = [] if acyclic else nx.find_cycle(g)
    return acyclic, violations, g.number_of_nodes(), g.number_of_edges(), cyc


def main():
    cfg = json.load(open(sys.argv[1]))
    L = ['# MTR: full-system CDG check (formal/mtr_cdg_check.py), fault-free', '',
         'Physical-channel CDG of the complete MTR routing function (all ordered pairs of chiplet routers), and a check '
         'that every route uses only allowed boundary turns.', '',
         '| chiplets | CDG nodes / edges | acyclic | turn violations |', '|---|---|---|---|']
    ok = True
    for cx, cy in ((2, 2), (3, 3), (4, 4)):
        acyclic, viol, n, e, cyc = check(cfg, cx, cy)
        ok &= acyclic and viol == 0
        L.append(f'| {cx}x{cy} | {n} / {e} | {acyclic} | {viol} |')
        print(cx, cy, acyclic, viol, n, e, cyc[:6])
    L += ['', f'**All checks pass: {ok}.**']
    open(sys.argv[2], 'w', newline='\n').write('\n'.join(L) + '\n')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
