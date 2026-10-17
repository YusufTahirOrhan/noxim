"""Model check of the routing relations implemented by DEFT_LB (Noxim).

Reproduces the rules of src/DeftLateBinding.cpp and src/DeftVirtualNetwork.cpp
(at the commit that adds DEFT_LB) on the abstract 4-chiplet instance of
deft_cdg_model.py:

  * candidate masks: exit / entry either fixed (any functional singleton, which
    covers the lut, random, mindist and oracle injection policies) or late
    (all functional VLs), with monotone pruning after every move;
  * source VN: a boundary source may start in VN1 only if its exit mask is
    exactly its own VL (F1 fix); intra-chiplet packets may use either VN;
  * Down: forbidden as Horizontal->Down in VN1; a VN0 packet arriving
    horizontally gets VN0 or VN1 on the down link (round robin, both explored);
    Local->Down keeps the VN;
  * interposer: the VN does not change; Up uses VN1; destination chiplet VN1;
  * turn models: chip_tm on all chiplet phases, ipos_tm on the interposer.

Checks CDG acyclicity (deadlock freedom), dead-end states (reachability) and
state-graph acyclicity with the longest path (livelock freedom / hop bound).
Valid only for this fixed topology instance.

Usage: python3 impl_relation_check.py [all] [n_proc]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import networkx as nx  # noqa: E402
from deft_cdg_model import (ALL_CHIP_NODES, POS2VL, VLPOS, chiplet_of, moves_to, step)  # noqa: E402

CONFIGS = {
    # name: (chip_tm, ipos_tm, exit, entry)
    'A_fixed_XY': ('XY', 'XY', 'fixed', 'fixed'),          # DeFT LUT and all injection-time policies
    'CI_XY_OE': ('XY', 'OE', 'fixed', 'late'),             # interposer-only late binding
    'FULL_OE_OE': ('OE', 'OE', 'late', 'late'),            # full late binding
}


def functional(c, faulty):
    return frozenset(v for v in range(c * 4, c * 4 + 4) if v not in faulty)


def moves_towards(tm, p, last, cand, skip):
    out = {}
    for v in cand:
        if v == skip:
            continue
        for m in moves_to(tm, p, last, VLPOS[v]):
            out.setdefault(m, set()).add(v)
    return {m: frozenset(vs) for m, vs in out.items()}


def explore(cfg, faulty):
    chip_tm, ipos_tm, exit_pol, entry_pol = cfg
    cdg, sg, dead = nx.DiGraph(), nx.DiGraph(), []
    init = []
    for s in ALL_CHIP_NODES:
        for d in ALL_CHIP_NODES:
            if d == s:
                continue
            cs, cd = chiplet_of(s), chiplet_of(d)
            if cs == cd:
                for vn in (0, 1):
                    init.append(('X', s, None, d, vn, None))
                continue
            fs, fd = functional(cs, faulty), functional(cd, faulty)
            exits = [frozenset([v]) for v in fs] if exit_pol == 'fixed' else [fs]
            entries = [frozenset([e]) for e in fd] if entry_pol == 'fixed' else [fd]
            own = POS2VL.get(s)
            for ex in exits:
                vns = [0, 1] if (own is not None and ex == frozenset([own])) else [0]
                for en in entries:
                    for vn in vns:
                        init.append(('S', s, None, (ex, en), vn, d))

    def succ(st):
        ph, p, last, m, vn, d = st
        out = []
        if ph == 'X' or ph == 'D':
            if p == m if ph == 'X' else p == d:
                return None
            tgt = m if ph == 'X' else d
            for mv in moves_to(chip_tm, p, last, tgt):
                q = step(p, mv)
                out.append(((ph, q, mv, m, vn, d), ('C', p, q, vn)))
            return out
        if ph == 'S':
            ex, en = m
            here = POS2VL.get(p)
            if here is not None and here in ex:
                down_vns = []
                if last is None:
                    down_vns = [vn]               # Local->Down keeps the VN
                elif vn == 0:
                    down_vns = [0, 1]             # Horizontal->Down VN0, round robin
                # Horizontal->Down in VN1: forbidden (rule R3)
                for dv in down_vns:
                    out.append((('I', p, None, (frozenset([here]), en), dv, d), ('D', here, dv)))
                if ex == frozenset([here]):
                    return out
            for mv, nex in moves_towards(chip_tm, p, last, ex, here).items():
                q = step(p, mv)
                out.append((('S', q, mv, (nex, en), vn, d), ('C', p, q, vn)))
            return out
        if ph == 'I':
            ex, en = m
            here = POS2VL.get(p)
            if here is not None and here in en:
                out.append((('D', p, None, None, 1, d), ('U', here, 1)))
                if en == frozenset([here]):
                    return out
            for mv, nen in moves_towards(ipos_tm, p, last, en, here).items():
                q = step(p, mv)
                out.append((('I', q, mv, (ex, nen), vn, d), ('I', p, q, vn)))
            return out
        raise ValueError(ph)

    seen = set()
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
            dead.append(st)
            continue
        for st2, ch2 in nxt:
            if ch is not None:
                cdg.add_edge(ch, ch2)
            sg.add_edge(node, (st2, ch2))
            stack.append((st2, ch2))
    return cdg, sg, dead


def job(args):
    name, faulty = args
    cdg, sg, dead = explore(CONFIGS[name], faulty)
    acyc = nx.is_directed_acyclic_graph(cdg)
    sga = nx.is_directed_acyclic_graph(sg)
    return (name, len(faulty), acyc, len(dead), sga,
            nx.dag_longest_path_length(sg) if sga else -1,
            cdg.number_of_nodes(), cdg.number_of_edges())


def masks():
    import itertools
    import random
    ms = []
    for k in range(0, 4):
        for comb in itertools.combinations(range(16), k):
            ms.append(frozenset(comb))
    rnd = random.Random(7)
    extra = set()
    while len(extra) < 200:
        k = rnd.randint(4, 12)
        comb = frozenset(rnd.sample(range(16), k))
        if all(sum(1 for v in comb if v // 4 == c) <= 3 for c in range(4)):
            extra.add(comb)
    return ms + sorted(extra, key=sorted)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        from multiprocessing import Pool
        nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        ms = masks()
        t = time.time()
        jobs = [(n, f) for n in CONFIGS for f in ms]
        with Pool(nproc) as pool:
            res = pool.map(job, jobs, chunksize=4)
        print('masks per config:', len(ms), 'elapsed s:', round(time.time() - t))
        for n in CONFIGS:
            r = [x for x in res if x[0] == n]
            print(f"{n}: masks={len(r)} cyclic_CDG={sum(not x[2] for x in r)} "
                  f"masks_with_dead_ends={sum(x[3] > 0 for x in r)} livelock_masks={sum(not x[4] for x in r)} "
                  f"max_hops={max(x[5] for x in r)}")
    else:
        for faulty in [frozenset(), frozenset({0, 4, 8, 12}), frozenset({0, 1, 2, 5, 6, 15})]:
            for n in CONFIGS:
                r = job((n, faulty))
                print(f"faulty={sorted(faulty)} {n}: CDG nodes={r[6]} edges={r[7]} acyclic={r[2]} "
                      f"dead_ends={r[3]} livelock_free={r[4]} longest_path={r[5]}")
