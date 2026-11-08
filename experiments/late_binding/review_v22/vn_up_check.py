"""Review v22: model check of the DeFT relations with the paper's Up-link rule.

The repository's model (formal/impl_relation_check.py) and code put every Up vertical-link channel in VN1. The DeFT paper
(Algorithm 1, Theorem III.4, Rule 2) switches to VN1 at the destination chiplet's boundary router, so the Up link itself
carries the VN the packet had on the interposer (VN0 or VN1). This script re-runs the repository's exploration with that one
change (Up channel = ('U', vl, vn_on_interposer); first hop inside the destination chiplet in VN1) and checks CDG acyclicity,
dead ends and livelock, on the 2x2 instance for the three relations (fixed pair XY, CI, FULL) and a set of fault masks, and
on 3x3 fault-free for the fixed pair. Usage: python3 vn_up_check.py
"""
import os
import sys
import time

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'formal'))
import impl_relation_check as I  # noqa: E402
import deft_cdg_model as dcm  # noqa: E402


def explore(cfg, faulty, up_keep):
    chip_tm, ipos_tm, exit_pol, entry_pol = cfg
    ALL, POS2VL, VLPOS = dcm.ALL_CHIP_NODES, dcm.POS2VL, dcm.VLPOS
    init = []
    for s in ALL:
        for d in ALL:
            if d == s:
                continue
            cs, cd = dcm.chiplet_of(s), dcm.chiplet_of(d)
            if cs == cd:
                for vn in (0, 1):
                    init.append(('X', s, None, d, vn, None))
                continue
            fs, fd = I.functional(cs, faulty), I.functional(cd, faulty)
            exits = [frozenset([v]) for v in fs] if exit_pol == 'fixed' else [fs]
            entries = [frozenset([e]) for e in fd] if entry_pol == 'fixed' else [fd]
            own = POS2VL.get(s)
            for ex in exits:
                vns = [0, 1] if (own is not None and ex == frozenset([own])) else [0]
                for en in entries:
                    for vn in vns:
                        init.append(('S', s, None, (ex, en), vn, d))

    def moves_towards(tm, p, last, cand, skip):
        out = {}
        for v in cand:
            if v == skip:
                continue
            for m in dcm.moves_to(tm, p, last, VLPOS[v]):
                out.setdefault(m, set()).add(v)
        return {m: frozenset(vs) for m, vs in out.items()}

    def succ(st):
        ph, p, last, m, vn, d = st
        out = []
        if ph == 'X' or ph == 'D':
            tgt = m if ph == 'X' else d
            if p == tgt:
                return None
            for mv in dcm.moves_to(chip_tm, p, last, tgt):
                q = dcm.step(p, mv)
                out.append(((ph, q, mv, m, vn, d), ('C', p, q, vn)))
            return out
        if ph == 'S':
            ex, en = m
            here = POS2VL.get(p)
            if here is not None and here in ex:
                down_vns = [vn] if last is None else ([0, 1] if vn == 0 else [])
                for dv in down_vns:
                    out.append((('I', p, None, (frozenset([here]), en), dv, d), ('D', here, dv)))
                if ex == frozenset([here]):
                    return out
            for mv, nex in moves_towards(chip_tm, p, last, ex, here).items():
                q = dcm.step(p, mv)
                out.append((('S', q, mv, (nex, en), vn, d), ('C', p, q, vn)))
            return out
        if ph == 'I':
            ex, en = m
            here = POS2VL.get(p)
            if here is not None and here in en:
                # paper: the Up link keeps the interposer VN, the destination chiplet is VN1; repository: Up link VN1
                out.append((('D', p, None, None, 1, d), ('U', here, vn if up_keep else 1)))
                if en == frozenset([here]):
                    return out
            for mv, nen in moves_towards(ipos_tm, p, last, en, here).items():
                q = dcm.step(p, mv)
                out.append((('I', q, mv, (ex, nen), vn, d), ('I', p, q, vn)))
            return out
        raise ValueError(ph)

    cdg, sg, dead, seen = nx.DiGraph(), nx.DiGraph(), 0, set()
    stack = [(st, None) for st in init]
    while stack:
        st, ch = stack.pop()
        node = (st, ch)
        if node in seen:
            continue
        seen.add(node)
        nxt = succ(st)
        if nxt is None:
            continue
        if not nxt:
            dead += 1
            continue
        for st2, ch2 in nxt:
            if ch is not None:
                cdg.add_edge(ch, ch2)
            sg.add_edge(node, (st2, ch2))
            stack.append((st2, ch2))
    acyc = nx.is_directed_acyclic_graph(cdg)
    sga = nx.is_directed_acyclic_graph(sg)
    return acyc, dead, sga, (nx.dag_longest_path_length(sg) if sga else -1), cdg.number_of_nodes(), cdg.number_of_edges()


def main():
    masks = [('fault-free', frozenset()), ('0x1111', frozenset({0, 4, 8, 12})), ('0x9C63', frozenset({0, 1, 5, 6, 10, 11, 12, 15})),
             ('0x7BDE', frozenset({1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14}))]
    L = ['# Model check of the paper\'s Up-link VN rule (review v22, vn_up_check.py)', '',
         'Same exploration as formal/impl_relation_check.py, with the Up channel in the VN the packet has on the interposer and the first hop inside the destination chiplet in VN1 (the paper\'s Algorithm 1 / Theorem III.4), against the repository\'s rule (Up channel always VN1).', '',
         '| instance | mask | relation | Up rule | CDG acyclic | dead ends | livelock-free | longest path | CDG nodes / edges |', '|---|---|---|---|---|---|---|---|---|']
    ok = True
    t = time.time()
    for name, m in masks:
        for rel in ('A_fixed_XY', 'CI_XY_OE', 'FULL_OE_OE'):
            for up_keep in (False, True):
                r = explore(I.CONFIGS[rel], m, up_keep)
                ok = ok and r[0] and r[1] == 0 and r[2]
                L.append('| 2x2 | %s | %s | %s | %s | %d | %s | %d | %d / %d |' % (name, rel, 'paper (keep)' if up_keep else 'repository (VN1)', r[0], r[1], r[2], r[3], r[4], r[5]))
    I.set_size(3, 3, 4, 4)
    for up_keep in (False, True):
        r = explore(I.CONFIGS['A_fixed_XY'], frozenset(), up_keep)
        ok = ok and r[0] and r[1] == 0 and r[2]
        L.append('| 3x3 | fault-free | A_fixed_XY | %s | %s | %d | %s | %d | %d / %d |' % ('paper (keep)' if up_keep else 'repository (VN1)', r[0], r[1], r[2], r[3], r[4], r[5]))
    L += ['', '**All checks pass: %s** (%.0f s).' % (ok, time.time() - t)]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vn_up_check.md')
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
