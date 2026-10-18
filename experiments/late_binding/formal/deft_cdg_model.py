"""Abstract formal model of DeFT-style 2.5D routing relations.

Fixed instance: four 4x4 chiplets in a 2x2 arrangement on an 8x8 interposer,
16 vertical links (VLs) at the slot positions used by the Noxim implementation
(N=(1,0), E=(3,1), S=(2,3), W=(0,2) in chiplet-local coordinates).

The model enumerates the routing states of all packet types (source,
destination, candidate set, virtual network) that a routing relation allows,
builds the channel dependency graph (CDG, channels = (link, VN)), and checks

  * CDG acyclicity  -> deadlock freedom (Dally & Seitz condition),
  * dead-end states -> reachability (a state with no legal output),
  * state-graph acyclicity and longest path -> livelock freedom / hop bound.

It abstracts away buffers, timing, arbitration and the Noxim reservation
table. It checks the *intended routing relation*, not the simulator code.
Results are valid only for this fixed topology (see notebook Section 10).

Written on 2026-10-07 during the thesis direction review. Pure Python 3,
requires networkx.
"""
import functools
import networkx as nx

CX, CY, CW, CH = 2, 2, 4, 4                      # chiplet grid and chiplet size (set_size)
W = 8
CHIP_ORIG = {c: ((c % 2) * 4, (c // 2) * 4) for c in range(4)}
SLOTS = [(1, 0), (3, 1), (2, 3), (0, 2)]          # N,E,S,W slots (local coords), as in DeftTopology
VLPOS = {c * 4 + s: (ox + lx, oy + ly) for c, (ox, oy) in CHIP_ORIG.items() for s, (lx, ly) in enumerate(SLOTS)}
POS2VL = {p: v for v, p in VLPOS.items()}
DIRS = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}


def chiplet_of(p):
    return (p[1] // CH) * CX + (p[0] // CW)


def chip_nodes(c):
    ox, oy = CHIP_ORIG[c]
    return [(ox + x, oy + y) for y in range(CH) for x in range(CW)]


ALL_CHIP_NODES = [p for c in range(4) for p in chip_nodes(c)]


def set_size(cx, cy, cw, ch):
    """Parametric instance (as DeftTopology::configure in Noxim): cx x cy chiplets of
    cw x ch routers, 4 VLs per chiplet at N=(1,0), E=(cw-1,1), S=(cw-2,ch-1), W=(0,ch-2)."""
    global CX, CY, CW, CH, W, CHIP_ORIG, SLOTS, VLPOS, POS2VL, ALL_CHIP_NODES
    CX, CY, CW, CH = cx, cy, cw, ch
    W = cx * cw
    CHIP_ORIG = {c: ((c % cx) * cw, (c // cx) * ch) for c in range(cx * cy)}
    SLOTS = [(1, 0), (cw - 1, 1), (cw - 2, ch - 1), (0, ch - 2)]
    VLPOS = {c * 4 + s: (ox + lx, oy + ly) for c, (ox, oy) in CHIP_ORIG.items() for s, (lx, ly) in enumerate(SLOTS)}
    POS2VL = {p: v for v, p in VLPOS.items()}
    ALL_CHIP_NODES = [p for c in range(cx * cy) for p in chip_nodes(c)]


def step(p, d):
    return (p[0] + DIRS[d][0], p[1] + DIRS[d][1])


def productive(p, t):
    out = []
    if t[0] > p[0]:
        out.append('E')
    if t[0] < p[0]:
        out.append('W')
    if t[1] > p[1]:
        out.append('S')
    if t[1] < p[1]:
        out.append('N')
    return out


def legal_turn(model, p, last, new):
    if last is None:
        return True
    if new == OPP[last]:
        return False                     # no U-turns
    if model == 'XY':
        return not (last in ('N', 'S') and new in ('E', 'W'))
    if model == 'WF':                    # west-first
        return not (new == 'W' and last in ('N', 'S'))
    if model == 'OE':                    # Chiu odd-even
        even = (p[0] % 2 == 0)
        if even and last == 'E' and new in ('N', 'S'):
            return False
        if (not even) and last in ('N', 'S') and new == 'W':
            return False
        return True
    raise ValueError(model)


@functools.lru_cache(maxsize=None)
def reach(model, p, last, t):
    """Exists a minimal, turn-legal path from p (arrived via `last`) to t."""
    if p == t:
        return True
    return any(legal_turn(model, p, last, m) and reach(model, step(p, m), m, t) for m in productive(p, t))


@functools.lru_cache(maxsize=None)
def moves_to(model, p, last, t):
    """Maximally adaptive minimal moves toward t that keep t reachable."""
    if model == 'XY':
        ms = productive(p, t)
        ms = [m for m in ms if m in ('E', 'W')] or ms   # XY: X first
        return tuple(m for m in ms if legal_turn('XY', p, last, m) and reach('XY', step(p, m), m, t))
    return tuple(m for m in productive(p, t) if legal_turn(model, p, last, m) and reach(model, step(p, m), m, t))


class Relation:
    """A routing relation configuration.

    exit_policy / entry_policy:
        'fixed' : target VL chosen once (at injection / at interposer entry);
                  all functional VLs are explored as possible choices.
        'late'  : any functional VL stays a candidate, no pruning.
        'prune' : monotone candidate pruning (late binding with minimality).
    vn_rule:
        'current' : boundary source may get VN1 even if it will not use its own VL
                    (the rule implemented in the simulator at commit d948d11).
        'fixed'   : boundary source uses VN1 only if it commits to its own VL.
    ipos_vn:
        'vn0'    : interposer uses only VN0 (as in the current implementation),
        'both'   : VN chosen on arrival at the interposer (DeFT round-robin),
        'switch' : VN0->VN1 switch allowed at every interposer hop.
    chip_model / ipos_model: turn models for chiplet layers / interposer (per VN).
    """

    def __init__(self, chip_model='XY', ipos_model=('XY', 'XY'), exit_policy='fixed', entry_policy='fixed',
                 vn_rule='fixed', ipos_vn='vn0', faulty=frozenset()):
        self.cm = chip_model
        self.im = ipos_model
        self.exit_policy = exit_policy
        self.entry_policy = entry_policy
        self.vn_rule = vn_rule
        self.ipos_vn = ipos_vn
        self.faulty = frozenset(faulty)

    def functional(self, c):
        return frozenset(v for v in range(c * 4, c * 4 + 4) if v not in self.faulty)


def horizontal_moves(model, policy, p, last, cand):
    """Returns list of (move, next_candidate_set)."""
    out = []
    if policy == 'fixed':
        (v,) = tuple(cand)
        for m in moves_to(model, p, last, VLPOS[v]):
            out.append((m, cand))
        return out
    allm = {}
    for v in cand:
        for m in moves_to(model, p, last, VLPOS[v]):
            allm.setdefault(m, set()).add(v)
    for m, vs in allm.items():
        out.append((m, cand if policy == 'late' else frozenset(vs)))
    return out


def explore(rel):
    """DFS over routing states of all packets. Returns (CDG, state graph, dead-end list)."""
    cdg = nx.DiGraph()
    sg = nx.DiGraph()
    dead = []
    init_states = []
    for s in ALL_CHIP_NODES:
        cs = chiplet_of(s)
        for d in ALL_CHIP_NODES:
            if d == s:
                continue
            cd = chiplet_of(d)
            if cd == cs:                                    # intra-chiplet, both VNs
                for vn in (0, 1):
                    init_states.append(('intra', s, None, d, vn, None))
                continue
            func = rel.functional(cs)
            own = POS2VL.get(s)
            if rel.exit_policy == 'fixed':
                cand_sets = [frozenset([v]) for v in func]
            else:
                cand_sets = [func]
            for cand in cand_sets:
                vns = [0]
                if own is not None and own in func:
                    if rel.vn_rule == 'current':
                        vns = [0, 1]                         # RR may give VN1 regardless of chosen exit
                    elif rel.vn_rule == 'fixed' and cand == frozenset([own]):
                        vns = [0, 1]
                for vn in vns:
                    init_states.append(('S', s, None, cand, vn, (cd, d)))
    seen = set()
    stack = [(st, None) for st in init_states]
    while stack:
        st, ch = stack.pop()
        node = (st, ch)
        if node in seen:
            continue
        seen.add(node)
        nxt = successors(rel, st)
        if nxt is None:                 # delivered
            continue
        if not nxt:
            dead.append(st)
            continue
        for st2, ch2 in nxt:
            if ch is not None and ch2 is not None:
                cdg.add_edge(ch, ch2)
            sg.add_edge(node, (st2, ch2))
            stack.append((st2, ch2))
    return cdg, sg, dead


def successors(rel, st):
    phase = st[0]
    if phase == 'intra':
        _, p, last, d, vn, _ = st
        if p == d:
            return None
        return [(('intra', step(p, m), m, d, vn, None), ('C', p, step(p, m), vn)) for m in moves_to(rel.cm, p, last, d)]
    if phase == 'S':
        _, p, last, cand, vn, dst = st
        out = []
        v_here = POS2VL.get(p)
        if v_here is not None and v_here in cand:
            # Down allowed unless Horizontal->Down in VN1 (Rule 3)
            if not (vn == 1 and last is not None):
                out.append((('DN', VLPOS[v_here], None, v_here, vn, dst), ('D', v_here, vn)))
        rest = cand - {v_here} if (v_here in cand and rel.exit_policy != 'fixed') else cand
        if rel.exit_policy == 'fixed' and v_here in cand:
            return out
        if rest:
            for m, nc in horizontal_moves(rel.cm, rel.exit_policy, p, last, rest):
                out.append((('S', step(p, m), m, nc, vn, dst), ('C', p, step(p, m), vn)))
        return out
    if phase == 'DN':                 # just crossed Down; now at interposer node p
        _, p, _, v, vn, (cd, d) = st
        ents = rel.functional(cd)
        cand_sets = [frozenset([e]) for e in ents] if rel.entry_policy == 'fixed' else [ents]
        vns = [vn] if rel.ipos_vn == 'vn0' else sorted({vn, 1})
        out = []
        for cand in cand_sets:
            for vn2 in vns:
                out.extend(ipos_moves(rel, p, None, cand, vn2, (cd, d), cur_vn_floor=vn))
        return out
    if phase == 'I':
        _, p, last, cand, vn, dst = st
        return ipos_moves(rel, p, last, cand, vn, dst, cur_vn_floor=vn)
    if phase == 'D':
        _, p, last, d, vn, _ = st
        if p == d:
            return None
        return [(('D', step(p, m), m, d, 1, None), ('C', p, step(p, m), 1)) for m in moves_to(rel.cm, p, last, d)]
    raise ValueError(phase)


def ipos_moves(rel, p, last, cand, vn, dst, cur_vn_floor):
    out = []
    e_here = POS2VL.get(p)
    if e_here is not None and e_here in cand:
        # Horizontal->Up allowed in both VNs; Up channel is VN1 (switch VN0->VN1 allowed by Rule 1)
        out.append((('D', VLPOS[e_here], None, dst[1], 1, None), ('U', e_here, 1)))
        if rel.entry_policy == 'fixed':
            return out
    rest = cand - {e_here} if e_here in cand else cand
    if not rest:
        return out
    model = rel.im[vn]
    pol = rel.entry_policy
    for m, nc in horizontal_moves(model, pol, p, last, rest):
        q = step(p, m)
        vnext = [vn] if rel.ipos_vn != 'switch' else sorted({vn, 1})
        for v2 in vnext:
            if v2 < cur_vn_floor:
                continue
            # when switching VN the turn legality of the new VN's model must also hold
            if v2 != vn and not legal_turn(rel.im[v2], p, last, m):
                continue
            out.append((('I', q, m, nc, v2, dst), ('I', p, q, v2)))
    return out


def check(rel, label):
    cdg, sg, dead = explore(rel)
    acyclic = nx.is_directed_acyclic_graph(cdg)
    cyc = None if acyclic else nx.find_cycle(cdg)
    sg_acyclic = nx.is_directed_acyclic_graph(sg)
    longest = nx.dag_longest_path_length(sg) if sg_acyclic else None
    print(f"[{label}] CDG nodes={cdg.number_of_nodes()} edges={cdg.number_of_edges()} acyclic={acyclic}"
          f" | dead-ends={len(dead)} | state-graph acyclic (no livelock)={sg_acyclic} longest-path(hops)={longest}")
    if dead:
        print("   example dead-end state:", dead[0])
    if cyc:
        print("   example CDG cycle:", cyc[:6])
    return cdg, sg, dead
