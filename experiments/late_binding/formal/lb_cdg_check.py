"""
Independent re-implementation of the late-binding (LB) routing function of the draft
(Algorithm 1, moves_T, DeFT's VN rules R1-R3) and of its channel dependency graph (CDG).

Purpose: try to find a counterexample to Lemma 1, Theorem 1 or Theorem 2:
  - a reachable interposer state with no offered output (dead end),
  - a path longer than d0 or ending at a VL outside the initial candidate set,
  - a dependency from a higher to a lower channel class,
  - a cycle in the CDG.

The CDG is built as the UNION over
  - every exit VL for every source router (a superset of any DeFT look-up table),
  - every non-empty initial candidate set M of the destination chiplet
    (a superset of every fault pattern that leaves each chiplet one functional VL),
  - both VNs after the Down move,
  - every output the routing function offers (so any selection function and the
    fallback of Section III-D are covered: a blocked head may wait on any offered output).
If the union is acyclic, every fault pattern and every selection function is acyclic.

Usage (needs networkx):
    python3 lbmodel.py main         XY in both VNs, and XY in VN0 / YX in VN1, on 4, 9, 16 chiplets
    python3 lbmodel.py turnmodels   odd-even, west-first, north-last on 9 chiplets; odd-even without (iii)
    python3 lbmodel.py rules        R2, R3, R1 dropped one at a time on 4 chiplets (each gives a cycle)
    python3 lbmodel.py placements   random VL placement per chiplet on 9 chiplets

Limits: the model checks the routing function and the CDG only. It does not simulate
traffic, timing, the decision unit or starvation, and it assumes the VL placement of Fig. 1
(N in column 1, E in row 1, S in column 2, W in row 2 of each 4x4 chiplet) unless
'placements' is used.
"""
import sys, itertools, random
from functools import lru_cache
import networkx as nx

DIRS = {"E": (1, 0), "W": (-1, 0), "N": (0, -1), "S": (0, 1)}   # row 0 is the north edge
OPP = {"E": "W", "W": "E", "N": "S", "S": "N"}
XDIR, YDIR = ("E", "W"), ("N", "S")

# ---------------------------------------------------------------- turn models
def allowed_xy(p, a, o):
    if a is None: return True
    if o == OPP[a]: return False
    if a in YDIR: return o == a            # no Y->X turn
    return True

def allowed_yx(p, a, o):
    if a is None: return True
    if o == OPP[a]: return False
    if a in XDIR: return o == a            # no X->Y turn
    return True

def allowed_oddeven(p, a, o):
    # Chiu 2000: no EN/ES turn in an even column, no NW/SW turn in an odd column
    if a is None: return True
    if o == OPP[a]: return False
    col = p[0]
    if a == "E" and o in YDIR and col % 2 == 0: return False
    if a in YDIR and o == "W" and col % 2 == 1: return False
    return True

def allowed_westfirst(p, a, o):
    if a is None: return True
    if o == OPP[a]: return False
    if o == "W" and a != "W": return False  # no turn into west
    return True

def allowed_northlast(p, a, o):
    if a is None: return True
    if o == OPP[a]: return False
    if a == "N" and o != "N": return False  # no turn out of north
    return True

TURN_MODELS = {"XY": allowed_xy, "YX": allowed_yx, "OE": allowed_oddeven,
               "WF": allowed_westfirst, "NL": allowed_northlast}

def dist(p, t): return abs(p[0] - t[0]) + abs(p[1] - t[1])
def step(p, o): return (p[0] + DIRS[o][0], p[1] + DIRS[o][1])

def make_moves(allowed, use_iii=True):
    @lru_cache(maxsize=None)
    def moves(p, a, t):
        out = []
        for o in DIRS:
            q = step(p, o)
            if dist(q, t) >= dist(p, t): continue          # (i) reduces the distance
            if not allowed(p, a, o): continue              # (ii) allowed by T after a
            if use_iii and not (q == t or moves(q, o, t)): continue   # (iii) no dead end behind o
            out.append(o)
        return tuple(out)
    return moves

# ---------------------------------------------------------------- topology
FIG1 = {"N": (1, 0), "E": (3, 1), "S": (2, 3), "W": (0, 2)}   # VL positions read off Fig. 1 (col,row)

class System:
    def __init__(self, G, placement=None):
        self.G = G; self.N = 4 * G
        self.chiplets = [(cx, cy) for cy in range(G) for cx in range(G)]
        self.vl = {}                       # (chiplet, name) -> global interposer coordinate
        for c in self.chiplets:
            pl = placement(c) if callable(placement) else (placement or FIG1)
            for name, (x, y) in pl.items():
                self.vl[(c, name)] = (4 * c[0] + x, 4 * c[1] + y)
        self.vl_at = {pos: key for key, pos in self.vl.items()}
    def chiplet_of(self, p): return (p[0] // 4, p[1] // 4)
    def routers(self, c): return [(4 * c[0] + x, 4 * c[1] + y) for y in range(4) for x in range(4)]
    def vls(self, c): return [k for k in self.vl if k[0] == c]

def xy_path_dirs(s, t):
    out = []
    p = s
    while p[0] != t[0]:
        o = "E" if t[0] > p[0] else "W"; out.append((p, o)); p = step(p, o)
    while p[1] != t[1]:
        o = "S" if t[1] > p[1] else "N"; out.append((p, o)); p = step(p, o)
    return out

# ---------------------------------------------------------------- LB routing function (Algorithm 1)
def offered(sysm, moves, p, a, M):
    """Outputs offered at interposer router p for candidate set M and previous move a."""
    O = []
    h = sysm.vl_at.get(p)
    if h is not None and h in M:
        O.append("Up")
        if len(M) == 1: return O
    for v in M:
        if v == h: continue
        for o in moves(p, a, sysm.vl[v]):
            if o not in O: O.append(o)
    return O

def prune(sysm, moves, p, a, M, o):
    return frozenset(v for v in M if o in moves(p, a, sysm.vl[v]))

# ---------------------------------------------------------------- CDG construction
def klass(ch):
    kind = ch[0]
    if kind == "C": return 0 if ch[3] == 0 else 5      # chiplet horizontal, VN0 / VN1
    if kind == "D": return 1
    if kind == "I": return 2 if ch[3] == 0 else 3      # interposer, VN0 / VN1
    if kind == "U": return 4
    raise ValueError(ch)

def build(sysm, T0="XY", T1="XY", use_iii=True, variant="LB", subsets="all", stats=None):
    """variant: 'LB' (rules as in the draft), 'noR2' (a VN0 packet stays in VN0 after Up),
    'noR3' (source phase may also run in VN1), 'noR1' (after the first VN1 hop in the
    destination chiplet the packet falls back to VN0)."""
    mv = {0: make_moves(TURN_MODELS[T0], use_iii), 1: make_moves(TURN_MODELS[T1], use_iii)}
    g = nx.DiGraph()
    viol = {"dead_end": [], "too_long": [], "wrong_vl": [], "ns_multi": 0}
    def dep(a, b):
        if a is not None: g.add_edge(a, b)

    for A in sysm.chiplets:
        # ---- source phase (XY, VN0) to every possible exit VL, then Down in VN0 or VN1
        src_vns = (0, 1) if variant == "noR3" else (0,)
        for e in sysm.vls(A):
            b = sysm.vl[e]
            for s in sysm.routers(A):
                for svn in src_vns:
                    prev = None
                    for (p, o) in xy_path_dirs(s, b):
                        ch = ("C", p, o, svn); dep(prev, ch); prev = ch
                    for vn in (0, 1):
                        if svn == 1 and vn == 0: continue        # R1 kept in this variant
                        dep(prev, ("D", e, vn)); g.add_node(("D", e, vn))
        # ---- intra-chiplet packets: XY, stay in one VN
        for s in sysm.routers(A):
            for t in sysm.routers(A):
                for vn in (0, 1):
                    prev = None
                    for (p, o) in xy_path_dirs(s, t):
                        ch = ("C", p, o, vn); dep(prev, ch); prev = ch

    # ---- interposer phase: explore every reachable (p, a, M) state
    for A in sysm.chiplets:
        for e in sysm.vls(A):
            p0 = sysm.vl[e]
            for B in sysm.chiplets:
                if B == A: continue
                vlsB = sysm.vls(B)
                if subsets == "all":
                    inits = [frozenset(c) for r in range(1, 5) for c in itertools.combinations(vlsB, r)]
                else:
                    inits = [frozenset(vlsB)]
                for M0 in inits:
                    d0 = max(dist(p0, sysm.vl[v]) for v in M0)
                    for vn in (0, 1):
                        moves = mv[vn]
                        seen = set()
                        stack = [(p0, None, M0, 0)]
                        while stack:
                            p, a, M, hops = stack.pop()
                            if (p, a, M) in seen: continue
                            seen.add((p, a, M))
                            inch = ("D", e, vn) if a is None else ("I", step(p, OPP[a]), a, vn)
                            O = offered(sysm, moves, p, a, M)
                            if stats is not None:
                                stats["states"] = stats.get("states", 0) + 1
                                if len(O) > 1: stats["choice"] = stats.get("choice", 0) + 1
                                stats["maxO"] = max(stats.get("maxO", 0), len(O))
                            if not O: viol["dead_end"].append((e, B, sorted(M0), vn, p, a, sorted(M)))
                            if a in YDIR and len(M) > 1: viol["ns_multi"] += 1
                            for o in O:
                                if o == "Up":
                                    h = sysm.vl_at[p]
                                    if h not in M0: viol["wrong_vl"].append((e, sorted(M0), h))
                                    dep(inch, ("U", h, vn))
                                else:
                                    M2 = prune(sysm, moves, p, a, M, o)
                                    if hops + 1 > d0: viol["too_long"].append((e, sorted(M0), p, o))
                                    dep(inch, ("I", p, o, vn))
                                    stack.append((step(p, o), o, M2, hops + 1))

    # ---- destination phase: after Up, XY to the destination
    for B in sysm.chiplets:
        for v in sysm.vls(B):
            b = sysm.vl[v]
            for t in sysm.routers(B):
                for vn in (0, 1):
                    prev = ("U", v, vn)
                    if not g.has_node(prev): continue
                    for i, (p, o) in enumerate(xy_path_dirs(b, t)):
                        if variant == "noR2": dvn = vn                 # VN0 packet turns Up->horizontal in VN0
                        elif variant == "noR1": dvn = 1 if i == 0 else 0   # VN1 -> VN0 after the first hop
                        else: dvn = 1
                        ch = ("C", p, o, dvn); dep(prev, ch); prev = ch
    return g, viol

def analyse(g):
    down = [(a, b) for a, b in g.edges if klass(a) > klass(b)]
    acyclic = nx.is_directed_acyclic_graph(g)
    cyc = None
    if not acyclic:
        cyc = nx.find_cycle(g)
    return down, acyclic, cyc

def run(G, T0, T1, variant="LB", use_iii=True, placement=None, subsets="all", label=None):
    sysm = System(G, placement)
    stats = {}
    g, viol = build(sysm, T0, T1, use_iii, variant, subsets, stats)
    down, acyclic, cyc = analyse(g)
    tag = label or f"{G}x{G} chiplets, T(VN0)={T0}, T(VN1)={T1}, variant={variant}, (iii)={'on' if use_iii else 'off'}"
    print(f"{tag}: {g.number_of_nodes()} channels, {g.number_of_edges()} dependencies, "
          f"{stats.get('states',0)} interposer states (max {stats.get('maxO',0)} outputs offered)")
    print(f"    dead ends: {len(viol['dead_end'])}   paths > d0: {len(viol['too_long'])}   exits outside M0: {len(viol['wrong_vl'])}"
          f"   N/S-moving states with |M|>1: {viol['ns_multi']}")
    print(f"    dependencies from a higher to a lower class: {len(down)}   CDG acyclic: {acyclic}")
    if cyc:
        print("    example cycle (%d channels):" % len(cyc))
        for a, b in cyc[:14]:
            print("       ", a, "k%d" % klass(a), "->", b, "k%d" % klass(b))
    if viol["dead_end"]:
        print("    example dead end:", viol["dead_end"][0])
    return g, viol, down, acyclic

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "main"
    if mode == "main":
        for G in (2, 3, 4):
            run(G, "XY", "XY")
        for G in (2, 3, 4):
            run(G, "XY", "YX")
    elif mode == "turnmodels":
        for T in ("OE", "WF", "NL"):
            run(3, T, T)
        run(3, "OE", "OE", use_iii=False)
        run(3, "WF", "NL")
    elif mode == "rules":
        for var in ("noR2", "noR3", "noR1"):
            run(2, "XY", "XY", variant=var)
    elif mode == "placements":
        rnd = random.Random(7)
        edge = {"N": [(x, 0) for x in range(4)], "S": [(x, 3) for x in range(4)],
                "W": [(0, y) for y in range(4)], "E": [(3, y) for y in range(4)]}
        for trial in range(6):
            cache = {}
            def placement(c, cache=cache):
                if c not in cache:
                    while True:
                        pl = {k: rnd.choice(v) for k, v in edge.items()}
                        if len(set(pl.values())) == 4: break
                    cache[c] = pl
                return cache[c]
            run(3, "XY", "XY", placement=placement, label=f"3x3 chiplets, random VL placement per chiplet #{trial}, XY/XY")
            run(3, "XY", "YX", placement=placement, label=f"3x3 chiplets, random VL placement per chiplet #{trial}, XY/YX")
