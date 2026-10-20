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

Horizontal-link (HL) faults (`hl` mode): a set of faulty bidirectional links,
on a chiplet layer ('C') or the interposer ('I'), known only to the adjacent
router. The router never takes a move onto a faulty link and adds no detour;
candidate pruning is unchanged (the relation is fault-unaware). Reported per
relation: fraction of source-destination pairs always delivered (no reachable
dead end from any of the pair's initial states: every injection choice, VN and
adaptive path), fraction of reachable states that are dead ends, CDG acyclicity.

Usage: python3 impl_relation_check.py [all] [n_proc]
       python3 impl_relation_check.py hl [n_proc] [out.md]
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import networkx as nx  # noqa: E402
from deft_cdg_model import (ALL_CHIP_NODES, POS2VL, VLPOS, chiplet_of, legal_turn, moves_to,  # noqa: E402
                            productive, step)

CONFIGS = {
    # name: (chip_tm, ipos_tm, exit, entry)
    'A_fixed_XY': ('XY', 'XY', 'fixed', 'fixed'),          # DeFT LUT and all injection-time policies
    'CI_XY_OE': ('XY', 'OE', 'fixed', 'late'),             # interposer-only late binding
    'FULL_OE_OE': ('OE', 'OE', 'late', 'late'),            # full late binding
}
# v7 bounded-deviation entry: the initial entry mask is any non-empty subset of the functional
# entries (covers every entry_bound_mode / entry_bound_k and any LUT); 'size' mode with 'bounded'.
CONFIGS_BOUNDED = {
    'CI_XY_OE_anysubset': ('XY', 'OE', 'fixed', 'subsets'),
    'FULL_OE_OE_anysubset': ('OE', 'OE', 'late', 'subsets'),
}
ALL_CONFIGS = dict(CONFIGS, **CONFIGS_BOUNDED)


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


def set_size(cx, cy, cw, ch):
    """Switch the model to a cx x cy grid of cw x ch chiplets (rebinds the imported names)."""
    import deft_cdg_model as dcm
    global ALL_CHIP_NODES, POS2VL, VLPOS
    dcm.set_size(cx, cy, cw, ch)
    ALL_CHIP_NODES, POS2VL, VLPOS = dcm.ALL_CHIP_NODES, dcm.POS2VL, dcm.VLPOS


def link(layer, p, q):
    return (layer, frozenset((p, q)))


def explore(cfg, faulty, hl_faulty=frozenset(), detail=False, hl_aware=False, dest=None):
    """hl_faulty: set of link(layer, p, q). detail=True also returns the initial
    state of every source-destination pair, the set of dead-end nodes, the number
    of reachable nodes and the set of delivered nodes.
    hl_aware: routers know every HL fault of their own layer (chiplet or interposer)
    and never take a move after which no remaining candidate (VL, or the destination
    router in the intra/destination phases) is reachable on a minimal, turn-legal,
    fault-free path of that layer. Other layers' faults stay unknown."""
    chip_tm, ipos_tm, exit_pol, entry_pol = cfg

    def ok(layer, p, q):
        return not hl_faulty or link(layer, p, q) not in hl_faulty

    memo = {}

    def reach_ff(layer, tm, p, last, t):
        if p == t:
            return True
        key = (layer, tm, p, last, t)
        if key not in memo:
            memo[key] = any(legal_turn(tm, p, last, mv) and ok(layer, p, step(p, mv)) and
                            reach_ff(layer, tm, step(p, mv), mv, t) for mv in productive(p, t))
        return memo[key]

    def aware(layer, tm, q, mv, targets):
        return not hl_aware or any(reach_ff(layer, tm, q, mv, t) for t in targets)
    delivered = set()
    cdg, sg, dead = nx.DiGraph(), nx.DiGraph(), []
    dead_nodes = set()
    init = []
    for s in ALL_CHIP_NODES:
        for d in ALL_CHIP_NODES:
            if d == s or (dest is not None and d != dest):
                continue
            cs, cd = chiplet_of(s), chiplet_of(d)
            if cs == cd:
                for vn in (0, 1):
                    init.append(('X', s, None, d, vn, None))
                continue
            fs, fd = functional(cs, faulty), functional(cd, faulty)
            exits = [frozenset([v]) for v in fs] if exit_pol == 'fixed' else [fs]
            if entry_pol == 'subsets':
                fl = sorted(fd)
                entries = [frozenset(e for i, e in enumerate(fl) if b >> i & 1) for b in range(1, 1 << len(fl))]
            else:
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
                if not ok('C', p, q) or not aware('C', chip_tm, q, mv, (tgt,)):
                    continue
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
                if not ok('C', p, q) or not aware('C', chip_tm, q, mv, [VLPOS[v] for v in nex]):
                    continue
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
                if not ok('I', p, q) or not aware('I', ipos_tm, q, mv, [VLPOS[e] for e in nen]):
                    continue
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
            delivered.add(node)
            continue
        if not nxt:
            dead.append(st)
            dead_nodes.add(node)
            continue
        for st2, ch2 in nxt:
            if ch is not None:
                cdg.add_edge(ch, ch2)
            sg.add_edge(node, (st2, ch2))
            stack.append((st2, ch2))
    if detail:
        return cdg, sg, dead, init, dead_nodes, len(seen), delivered
    return cdg, sg, dead


def job(args):
    name, faulty = args
    cdg, sg, dead = explore(ALL_CONFIGS[name], faulty)
    acyc = nx.is_directed_acyclic_graph(cdg)
    sga = nx.is_directed_acyclic_graph(sg)
    return (name, len(faulty), acyc, len(dead), sga,
            nx.dag_longest_path_length(sg) if sga else -1,
            cdg.number_of_nodes(), cdg.number_of_edges())


def job_lean(args):
    """Same result as job(), exploring one destination at a time (bounded memory).

    States carry their destination and no transition changes it, so the state graph is
    the disjoint union of the per-destination graphs: dead ends add up, the state graph is
    acyclic iff every part is, the longest path is the maximum, and the CDG is the union
    of the per-destination channel dependencies."""
    name, faulty = args
    cdg_all = nx.DiGraph()
    dead, sga, longest = 0, True, 0
    for d in ALL_CHIP_NODES:
        cdg, sg, dl = explore(ALL_CONFIGS[name], faulty, dest=d)
        cdg_all.add_edges_from(cdg.edges())
        dead += len(dl)
        if sga and nx.is_directed_acyclic_graph(sg):
            longest = max(longest, nx.dag_longest_path_length(sg) if sg.number_of_nodes() else 0)
        else:
            sga = False
    return (name, len(faulty), nx.is_directed_acyclic_graph(cdg_all), dead, sga,
            longest if sga else -1, cdg_all.number_of_nodes(), cdg_all.number_of_edges())


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


def hl_links():
    """All bidirectional horizontal links: chiplet layers (within a chiplet) and interposer."""
    out = []
    for p in ALL_CHIP_NODES:
        for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)):
            if q in ALL_CHIP_NODES and chiplet_of(q) == chiplet_of(p):
                out.append(link('C', p, q))
    for y in range(8):
        for x in range(8):
            for q in ((x + 1, y), (x, y + 1)):
                if q[0] < 8 and q[1] < 8:
                    out.append(link('I', (x, y), q))
    return sorted(out, key=lambda l: (l[0], sorted(l[1])))


def hl_job(args):
    name, vl_label, vl_faulty, kind, hl = args
    cdg, sg, dead, init, dead_nodes, nseen, _ = explore(CONFIGS[name], vl_faulty, frozenset(hl), detail=True)
    bad = set(dead_nodes)
    frontier = [n for n in dead_nodes if n in sg]
    while frontier:
        n = frontier.pop()
        for pred in sg.predecessors(n):
            if pred not in bad:
                bad.add(pred)
                frontier.append(pred)
    pair_ok = {}
    for st in init:
        pair = (st[1], st[3] if st[0] == 'X' else st[5])
        pair_ok[pair] = pair_ok.get(pair, True) and (st, None) not in bad
    layers = ''.join(sorted(l[0] for l in hl))
    return (name, vl_label, kind, layers, sum(pair_ok.values()) / len(pair_ok),
            len(dead_nodes) / nseen, nx.is_directed_acyclic_graph(cdg))


def _closure(sg, seeds):
    """Nodes that can reach any node of `seeds` (including them)."""
    out = set(seeds)
    frontier = [n for n in seeds if n in sg]
    while frontier:
        n = frontier.pop()
        for pred in sg.predecessors(n):
            if pred not in out:
                out.add(pred)
                frontier.append(pred)
    return out


def _pairs(init, good):
    """Per pair: (all initial states good, any initial state good)."""
    allg, anyg = {}, {}
    for st in init:
        pair = (st[1], st[3] if st[0] == 'X' else st[5])
        g = (st, None) in good
        allg[pair] = allg.get(pair, True) and g
        anyg[pair] = anyg.get(pair, False) or g
    return allg, anyg


def hl3_job(args):
    """v3 HL metrics for one (relation, VL mask, HL fault set):
    unaware relation (v2): pairs always delivered, pairs with some delivered path (exists-path);
    fault-aware pruning: pairs always delivered, dead-state share, CDG acyclic, exists-path."""
    name, vl_label, vl_faulty, kind, hl = args
    out = [name, vl_label, kind, ''.join(sorted(l[0] for l in hl))]
    for aware_flag in (False, True):
        cdg, sg, dead, init, dead_nodes, nseen, delivered = explore(
            CONFIGS[name], vl_faulty, frozenset(hl), detail=True, hl_aware=aware_flag)
        bad = _closure(sg, dead_nodes)
        reach = _closure(sg, delivered)
        always, _ = _pairs(init, {(st, None) for st in init} - bad)
        _, exists = _pairs(init, reach)
        out += [sum(always.values()) / len(always), sum(exists.values()) / len(exists),
                len(dead_nodes) / nseen, nx.is_directed_acyclic_graph(cdg)]
    return tuple(out)


def hl3_main(nproc, out_md, v2_csv=None):
    import itertools
    import random
    from multiprocessing import Pool
    links = hl_links()
    singles = [(l,) for l in links]
    doubles = random.Random(7).sample(list(itertools.combinations(links, 2)), 500)   # as v2
    vls = [('none', frozenset()), ('0x1111', frozenset({0, 4, 8, 12}))]
    jobs = [(n, vl, vf, kind, hl) for n in CONFIGS for vl, vf in vls
            for kind, sets in (('single', singles), ('double', doubles)) for hl in sets]
    t = time.time()
    with Pool(nproc) as pool:
        res = pool.map(hl3_job, jobs, chunksize=4)
    el = time.time() - t
    cols = ['relation', 'vl_mask', 'kind', 'layers', 'always_unaware', 'exists_unaware', 'dead_unaware',
            'cdg_acyclic_unaware', 'always_aware', 'exists_aware', 'dead_aware', 'cdg_acyclic_aware']
    csv_path = os.path.splitext(out_md)[0] + '.csv'
    with open(csv_path, 'w') as f:
        f.write(','.join(cols) + '\n')
        for r in res:
            f.write(','.join(str(x) for x in r) + '\n')
    # cross-check: the unaware "always delivered" share must equal the v2 table, row by row
    check = 'v2 cross-check not run'
    if v2_csv and os.path.exists(v2_csv):
        v2 = [l.strip().split(',') for l in open(v2_csv).read().splitlines()[1:]]
        same = sum(1 for a, b in zip(res, v2) if list(map(str, a[:4])) == b[:4] and str(a[4]) == b[4]
                   and str(a[6]) == b[5])
        check = f'v2 cross-check: {same} of {len(v2)} rows identical (relation, mask, kind, layers, always, dead)'
    L = ['# Horizontal-link fault coverage v3: exists-path and fault-aware pruning (formal model)', '',
         'Model: formal/impl_relation_check.py `hl3` mode. Fault sets as results_v2/hl_coverage.md: all',
         f'{len(singles)} single HL faults and the same 500 sampled double faults (seed 7), each without VL',
         'faults and with VL mask 0x1111; relations A_fixed_XY (every VL pair explored), CI_XY_OE, FULL_OE_OE.',
         '',
         'Metrics (share of the 4032 source-destination pairs):',
         '* **always (v2, unaware):** no reachable state of the pair is a dead end, with routers that only',
         '  refuse a faulty link next to them (as v2).',
         '* **exists-path:** at least one routing path of the relation (some injection choice, some',
         '  adaptive choice) is delivered. Fault-aware pruning only removes moves that cannot lead to',
         '  delivery, so this share is the same with and without pruning (checked: column `exists aware`).',
         '* **always (aware):** with fault-aware pruning. Routers know every HL fault of their own layer',
         '  (all chiplet links for chiplet routers, all interposer links for interposer routers, as ReD',
         '  distributes VL faults) and never take a move after which no remaining candidate (VL, or the',
         '  destination in the intra/destination phase) is reachable on a minimal, turn-legal, fault-free path',
         '  of that layer. Candidate sets and injection choices are unchanged, and faults of the other layer',
         '  stay unknown (the exit VL is chosen without knowing the interposer, the entry VL without knowing',
         '  the destination chiplet).',
         f'Elapsed: {el:.0f} s on {nproc} processes. {check}.', '',
         '| relation | VL mask | HL faults | sets | always (v2, unaware): mean (min) | exists-path: mean (min) | '
         'always (aware): mean (min) | sets 100 % aware | dead states aware: mean | CDG acyclic aware | exists aware = unaware |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    groups = [('single', 'C', 'single, chiplet'), ('single', 'I', 'single, interposer'), ('single', None, 'single, all'),
              ('double', None, 'double (sample)')]
    for n in CONFIGS:
        for vl, _ in vls:
            for kind, layer, label in groups:
                rs = [r for r in res if r[0] == n and r[1] == vl and r[2] == kind and (layer is None or r[3] == layer)]

                def mm(i):
                    xs = [r[i] for r in rs]
                    return f'{100 * sum(xs) / len(xs):.2f} % ({100 * min(xs):.2f} %)'
                L.append(f'| {n} | {vl} | {label} | {len(rs)} | {mm(4)} | {mm(5)} | {mm(8)} | '
                         f'{sum(1 for r in rs if r[8] == 1.0)} | {100 * sum(r[10] for r in rs) / len(rs):.3f} % | '
                         f'{sum(1 for r in rs if r[11])}/{len(rs)} | {sum(1 for r in rs if r[5] == r[9])}/{len(rs)} |')
    open(out_md, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def hl_main(nproc, out_md):
    import itertools
    import random
    from multiprocessing import Pool
    links = hl_links()
    singles = [(l,) for l in links]
    doubles = random.Random(7).sample(list(itertools.combinations(links, 2)), 500)
    vls = [('none', frozenset()), ('0x1111', frozenset({0, 4, 8, 12}))]
    jobs = [(n, vl, vf, kind, hl) for n in CONFIGS for vl, vf in vls
            for kind, sets in (('single', singles), ('double', doubles)) for hl in sets]
    t = time.time()
    with Pool(nproc) as pool:
        res = pool.map(hl_job, jobs, chunksize=4)
    el = time.time() - t
    base = {}
    for n in CONFIGS:
        for vl, vf in vls:
            base[(n, vl)] = hl_job((n, vl, vf, 'none', ()))
    csv_path = os.path.splitext(out_md)[0] + '.csv'
    with open(csv_path, 'w') as f:
        f.write('relation,vl_mask,kind,layers,pairs_always_delivered,dead_state_fraction,cdg_acyclic\n')
        for r in res:
            f.write(','.join(str(x) for x in r) + '\n')
    L = ['# Horizontal-link fault coverage of the implemented relations (formal model)', '',
         'Model: formal/impl_relation_check.py `hl` mode. Faulty horizontal links are bidirectional,',
         'on a chiplet layer (C) or the interposer (I), and known only to the adjacent router: it never',
         'takes a move onto a faulty link and adds no detour (candidate pruning stays fault-unaware).',
         'Relations: A_fixed_XY (DeFT LUT and every injection-time policy: all functional VL pairs are',
         'explored), CI_XY_OE (interposer-only late binding), FULL_OE_OE (full late binding).',
         f'Fault sets: all {len(singles)} single HL faults ({sum(1 for l in links if l[0] == "C")} chiplet, '
         f'{sum(1 for l in links if l[0] == "I")} interposer) and 500 random double faults (seed 7),',
         'each without VL faults and with VL mask 0x1111.',
         '"Pairs always delivered": share of the 4032 source-destination pairs for which no reachable',
         'routing state (over every injection choice, VN and adaptive path) is a dead end. Because the',
         'fixed-pair relation explores every VL pair, its figure is the worst case over all injection',
         'policies, not the DeFT LUT pair alone. "Dead states": share of reachable routing states with no',
         f'legal move. Elapsed: {el:.0f} s on {nproc} processes.', '',
         'Without HL faults every relation delivers 100 % of the pairs with 0 dead states (both VL masks): '
         + ', '.join(f'{n}/{vl}: {base[(n, vl)][4]:.3f}, {base[(n, vl)][5]:.4f}' for n in CONFIGS for vl, _ in vls) + '.', '',
         '| relation | VL mask | HL faults | sets | pairs always delivered: mean (min) | sets with 100 % pairs | '
         'dead states: mean (max) | CDG acyclic |',
         '|---|---|---|---|---|---|---|---|']
    groups = [('single', 'C', 'single, chiplet'), ('single', 'I', 'single, interposer'), ('single', None, 'single, all'),
              ('double', None, 'double (sample)')]
    for n in CONFIGS:
        for vl, _ in vls:
            for kind, layer, label in groups:
                rs = [r for r in res if r[0] == n and r[1] == vl and r[2] == kind and (layer is None or r[3] == layer)]
                pd = [r[4] for r in rs]
                ds = [r[5] for r in rs]
                L.append(f'| {n} | {vl} | {label} | {len(rs)} | {100 * sum(pd) / len(pd):.2f} % ({100 * min(pd):.2f} %) | '
                         f'{sum(1 for x in pd if x == 1.0)} | {100 * sum(ds) / len(ds):.3f} % ({100 * max(ds):.3f} %) | '
                         f'{sum(1 for r in rs if r[6])}/{len(rs)} |')
    L += ['', 'Removing links can only remove CDG edges, so the CDG stays acyclic by construction; the',
          'column confirms it. The relations add no fault-aware detour, so every pair whose minimal',
          'turn-legal paths all cross a faulty link is lost; the table measures how much path diversity',
          '(late binding) recovers.']
    open(out_md, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def size_masks(cx, cy, n_random, seed=7):
    """Fault-free, one VL per chiplet (north), and n_random masks with 0-3 faulty VLs drawn
    uniformly per chiplet (seed 7; empty and duplicate masks rejected)."""
    import random
    nc = cx * cy
    ms = [('fault-free', frozenset()), ('north per chiplet', frozenset(4 * c for c in range(nc)))]
    rnd = random.Random(seed)
    seen = {m for _, m in ms}
    while len(ms) < 2 + n_random:
        m = frozenset(v for c in range(nc) for v in rnd.sample(range(4 * c, 4 * c + 4), rnd.randint(0, 3)))
        if m and m not in seen:
            seen.add(m)
            ms.append((f'random {len(ms) - 1}', m))
    return ms


LEAN = False


def _timed_job(args):
    t = time.time()
    r = job_lean(args) if LEAN else job(args)
    return r + (time.time() - t,)


def _init_size(cx, cy, lean):
    global LEAN
    set_size(cx, cy, 4, 4)
    LEAN = lean


def size_main(cx, cy, nproc, out_md, n_random, lean=False, configs=None):
    """The three relations on a cx x cy grid of 4x4 chiplets (v4 step 3). lean: per-destination
    exploration (job_lean), needed for 4x4 within the available memory."""
    from multiprocessing import Pool
    set_size(cx, cy, 4, 4)
    ms = size_masks(cx, cy, n_random)
    configs = configs or CONFIGS
    jobs = [(n, m) for _, m in ms for n in configs]
    t = time.time()
    with Pool(nproc, initializer=_init_size, initargs=(cx, cy, lean)) as pool:
        res = pool.map(_timed_job, jobs, chunksize=1)
    el = time.time() - t
    nvl = 4 * cx * cy
    L = [f'## {cx}x{cy} chiplets of 4x4 routers ({16 * cx * cy} chiplet routers, {nvl} VLs)', '',
         f'{len(ms)} fault masks x {len(configs)} relations = {len(jobs)} checks; {nproc} processes, {el:.0f} s wall'
         f'{"; per-destination exploration (job_lean)" if lean else ""}.', '',
         '| mask | faulty VLs | relation | CDG acyclic | dead ends | livelock-free | longest path (hops) | '
         'CDG nodes / edges | time (s) |', '|---|---|---|---|---|---|---|---|---|']
    names = {m: lab for lab, m in ms}
    for (n, m), r in zip(jobs, res):
        L.append(f'| {names[m]} | {len(m)} | {n} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} / {r[7]} | {r[8]:.0f} |')
    ok = all(r[2] and r[3] == 0 and r[4] for r in res)
    L += ['', f'**All checks pass: {ok}** (acyclic CDG, no dead ends, no livelock).', '']
    if n_random:
        L.append('Random masks: ' + '; '.join(f'{lab}: {sorted(m)}' for lab, m in ms[2:]))
        L.append('')
    with open(out_md, 'a', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return ok


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'size':
        # size CX CY NPROC OUT.md N_RANDOM [lean]
        # size CX CY NPROC OUT.md N_RANDOM [lean] [bounded]
        ok = size_main(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], int(sys.argv[6]),
                       lean='lean' in sys.argv[7:],
                       configs=CONFIGS_BOUNDED if 'bounded' in sys.argv[7:] else None)
        sys.exit(0 if ok else 1)
    if len(sys.argv) > 1 and sys.argv[1] == 'hl3':
        hl3_main(int(sys.argv[2]) if len(sys.argv) > 2 else 2,
                 sys.argv[3] if len(sys.argv) > 3 else 'hl_coverage_v3.md',
                 sys.argv[4] if len(sys.argv) > 4 else None)
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == 'hl':
        hl_main(int(sys.argv[2]) if len(sys.argv) > 2 else 2,
                sys.argv[3] if len(sys.argv) > 3 else 'hl_coverage.md')
        sys.exit(0)
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
