"""MTR (Yin et al., ISCA 2018) offline configuration for one 4x4 chiplet with DeFT's 4 VL routers as boundary routers.

Model (BASELINES_DESIGN.md, MTR):
* XY routing inside the chiplet. The rest of the system is the virtual node x: Up channels go into x, Down channels
  come out of x.
* Candidate turns at the boundary routers: inbound Down->d (d = first direction of the XY route from the boundary
  router to the destination) and outbound d->Up (d = direction of the last hop into the boundary router).
* Horizontal turns at boundary routers are candidates as well, but every XY-legal turn is used by an intra-chiplet
  XY route, so prohibiting one disconnects the chiplet; they are listed and excluded by the connectivity constraint.
* With XY inside the chiplet, a dependency path Down(a) -> ... -> Up(c) is an X-then-Y monotone path. The only such
  path from a to c is the XY route a -> c (unique). So a cycle through x exists iff, for some boundary routers a != c,
  the inbound turn Down -> first_dir(XY a->c) at a and the outbound turn last_dir(XY a->c) -> Up at c are both
  allowed.
* Search: all subsets of the inbound candidates; for each, the maximal set of outbound turns without a cycle (more
  allowed outbound turns never worsen the objective). Constraints: every router reaches at least one boundary router
  (outbound) and is reached from at least one (inbound). Objective (paper Sec. IV-B): minimise
  Average_distance / Average_reachability. Ties: fewer prohibited turns, then lexicographic.
* Boundary assignment: the paper's Sec. IV-C procedure (A_i, C_i, E_ij; steps 1-3), separately for inbound
  (destination -> entry boundary router) and outbound (source -> exit boundary router).
Output: results_v10/mtr_config.json (tables indexed by local_y * 4 + local_x, value = VL slot 0..3 = N, E, S, W) and
results_v10/mtr_search.md.
Usage: python3 formal/mtr_search.py OUT_DIR
"""
import itertools
import json
import os
import sys

W = H = 4
SLOTS = [(1, 0), (W - 1, 1), (W - 2, H - 1), (0, H - 2)]        # VL_SLOT_NORTH, EAST, SOUTH, WEST (DeftTopology.cpp)
SLOT_NAMES = ['N', 'E', 'S', 'W']
DIRS = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
NODES = [(x, y) for y in range(H) for x in range(W)]


def xy_path(a, b):
    """Directions of the XY route a -> b (X first, then Y)."""
    (x, y), (tx, ty) = a, b
    out = []
    while x != tx:
        d = 'E' if tx > x else 'W'
        out.append(d)
        x += DIRS[d][0]
    while y != ty:
        d = 'S' if ty > y else 'N'
        out.append(d)
        y += DIRS[d][1]
    return out


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def inbound_reach(b, allowed_in):
    return {r for r in NODES if r == b or xy_path(b, r)[0] in allowed_in}


def outbound_reach(c, allowed_out):
    return {r for r in NODES if r == c or xy_path(r, c)[-1] in allowed_out}


def candidates():
    cin = {i: sorted({xy_path(b, r)[0] for r in NODES if r != b}) for i, b in enumerate(SLOTS)}
    cout = {i: sorted({xy_path(r, c)[-1] for r in NODES if r != c}) for i, c in enumerate(SLOTS)}
    return cin, cout


def horizontal_candidates():
    """XY-legal turns at boundary routers (X -> Y). Each is used by some intra-chiplet XY route."""
    out = []
    for i, b in enumerate(SLOTS):
        for s, d in itertools.product(NODES, NODES):
            p = xy_path(s, d)
            pos = s
            for k in range(len(p) - 1):
                pos = (pos[0] + DIRS[p[k]][0], pos[1] + DIRS[p[k]][1])
                if pos == b and p[k] != p[k + 1]:
                    out.append((SLOT_NAMES[i], p[k], p[k + 1]))
    return sorted(set(out))


def evaluate(allowed_in, allowed_out):
    ins = {i: inbound_reach(b, allowed_in[i]) for i, b in enumerate(SLOTS)}
    outs = {i: outbound_reach(c, allowed_out[i]) for i, c in enumerate(SLOTS)}
    if any(not any(r in ins[i] for i in ins) for r in NODES) or any(not any(r in outs[i] for i in outs) for r in NODES):
        return None
    ind = {r: min(dist(SLOTS[i], r) for i in ins if r in ins[i]) for r in NODES}
    outd = {r: min(dist(r, SLOTS[i]) for i in outs if r in outs[i]) for r in NODES}
    avg_dist = sum((ind[r] + outd[r]) / 2 for r in NODES) / len(NODES)
    avg_reach = sum((len(ins[i]) + len(outs[i])) / (2 * len(NODES)) for i in ins) / len(SLOTS)
    return avg_dist / avg_reach, avg_dist, avg_reach, ins, outs


def search():
    cin, cout = candidates()
    in_vars = [(i, d) for i in cin for d in cin[i]]
    best = None
    for mask in range(1 << len(in_vars)):
        allowed_in = {i: set() for i in cin}
        for k, (i, d) in enumerate(in_vars):
            if mask >> k & 1:
                allowed_in[i].add(d)
        # maximal outbound set: drop outbound turns closing a cycle a -> c with an allowed inbound turn at a
        allowed_out = {c: set(cout[c]) for c in cout}
        for a, c in itertools.permutations(range(len(SLOTS)), 2):
            p = xy_path(SLOTS[a], SLOTS[c])
            if p[0] in allowed_in[a]:
                allowed_out[c].discard(p[-1])
        ev = evaluate(allowed_in, allowed_out)
        if ev is None:
            continue
        prohibited = sorted([('in', SLOT_NAMES[i], d) for i, d in in_vars if d not in allowed_in[i]] +
                            [('out', SLOT_NAMES[c], d) for c in cout for d in cout[c] if d not in allowed_out[c]])
        key = (round(ev[0], 12), len(prohibited), prohibited)
        if best is None or key < best[0]:
            best = (key, allowed_in, allowed_out, ev, prohibited)
    return best, cin, cout


def assign(reach, inbound):
    """Paper Sec. IV-C: A_i (only i), C_i (strictly closest to i), E_ij (equidistant, two lowest-id routers)."""
    n = len(SLOTS)
    d = (lambda i, r: dist(SLOTS[i], r)) if inbound else (lambda i, r: dist(r, SLOTS[i]))
    A = {i: set() for i in range(n)}
    C = {i: [] for i in range(n)}
    E = {}
    for r in NODES:
        by = [i for i in range(n) if r in reach[i]]
        if len(by) == 1:
            A[by[0]].add(r)
            continue
        m = min(d(i, r) for i in by)
        near = sorted(i for i in by if d(i, r) == m)
        if len(near) == 1:
            C[near[0]].append(r)
        else:
            E.setdefault((near[0], near[1]), []).append(r)
    for i in C:
        C[i].sort(key=lambda r: (d(i, r), r[1], r[0]))
    for k in E:
        E[k].sort(key=lambda r: (r[1], r[0]))

    def pending(i):
        return bool(C[i]) or any(E[k] for k in E if i in k)

    while any(pending(i) for i in range(n)):
        cand = [i for i in range(n) if pending(i)]
        i = min(cand, key=lambda j: (len(A[j]), j))

        def smallest():
            return all(len(A[i]) <= len(A[j]) for j in cand if j != i)
        while C[i] and smallest():                      # step 2: from C_i
            A[i].add(C[i].pop(0))
        if smallest():                                  # step 2: from E_ij
            for k in sorted(k for k in E if i in k):
                while E[k] and smallest():
                    A[i].add(E[k].pop(0))
    table = {}
    for i in range(n):
        for r in A[i]:
            table[r] = i
    return [table[(x, y)] for y in range(H) for x in range(W)], {SLOT_NAMES[i]: len(A[i]) for i in A}


def main():
    out_dir = sys.argv[1]
    best, cin, cout = search()
    key, allowed_in, allowed_out, ev, prohibited = best
    objective, avg_dist, avg_reach, ins, outs = ev
    inbound, in_sizes = assign(ins, True)
    outbound, out_sizes = assign(outs, False)
    # sanity: every assignment respects the restrictions
    for r in NODES:
        idx = r[1] * W + r[0]
        assert r in ins[inbound[idx]] and r in outs[outbound[idx]]
    cfg = {
        'chiplet': [W, H], 'slots': {SLOT_NAMES[i]: list(SLOTS[i]) for i in range(len(SLOTS))},
        'allowed_inbound_turns': {SLOT_NAMES[i]: sorted(allowed_in[i]) for i in allowed_in},
        'allowed_outbound_turns': {SLOT_NAMES[i]: sorted(allowed_out[i]) for i in allowed_out},
        'prohibited_turns': [list(p) for p in prohibited],
        'objective': objective, 'average_distance': avg_dist, 'average_reachability': avg_reach,
        'inbound_reachability': {SLOT_NAMES[i]: len(ins[i]) / len(NODES) for i in ins},
        'outbound_reachability': {SLOT_NAMES[i]: len(outs[i]) / len(NODES) for i in outs},
        'outbound': outbound, 'inbound': inbound,
        'table_index': 'local_y * 4 + local_x', 'table_value': 'VL slot (0 N, 1 E, 2 S, 3 W)',
    }
    json.dump(cfg, open(os.path.join(out_dir, 'mtr_config.json'), 'w'), indent=1)
    hc = horizontal_candidates()
    L = ['# MTR configuration (formal/mtr_search.py)', '',
         'One 4x4 chiplet, XY routing, boundary routers = the 4 DeFT VL routers N (1,0), E (3,1), S (2,3), W (0,2).', '',
         f'Inbound turn candidates: {sum(len(v) for v in cin.values())} '
         f'({", ".join(f"{SLOT_NAMES[i]}: {cin[i]}" for i in cin)}); outbound turn candidates: '
         f'{sum(len(v) for v in cout.values())} ({", ".join(f"{SLOT_NAMES[i]}: {cout[i]}" for i in cout)}).',
         f'Horizontal turns at boundary routers (X->Y, all used by intra-chiplet XY routes, so excluded by the '
         f'connectivity constraint): {len(hc)}: ' + ', '.join(f'{b}:{a}->{c}' for b, a, c in hc) + '.', '',
         f'Exhaustive search over {2 ** sum(len(v) for v in cin.values())} inbound subsets (maximal outbound set each).', '',
         f'**Chosen configuration:** objective Average_distance / Average_reachability = {objective:.4f} '
         f'(Average_distance {avg_dist:.4f}, Average_reachability {avg_reach:.4f}); {len(prohibited)} prohibited turns: '
         + ', '.join(f'{k} {b} {d}' for k, b, d in prohibited) + '.', '',
         '| boundary | allowed inbound (Down->) | allowed outbound (->Up, by direction of arrival) | InR | OutR | '
         'inbound nodes assigned | outbound nodes assigned |', '|---|---|---|---|---|---|---|']
    for i, n in enumerate(SLOT_NAMES):
        L.append(f'| {n} {SLOTS[i]} | {sorted(allowed_in[i])} | {sorted(allowed_out[i])} | {len(ins[i])}/16 | '
                 f'{len(outs[i])}/16 | {in_sizes[n]} | {out_sizes[n]} |')
    L += ['', 'Tables (rows y = 0..3, columns x = 0..3; entry = boundary router used):', '',
          'Outbound (source -> exit):', '```'] + \
         [' '.join(SLOT_NAMES[outbound[y * W + x]] for x in range(W)) for y in range(H)] + \
         ['```', '', 'Inbound (destination -> entry):', '```'] + \
         [' '.join(SLOT_NAMES[inbound[y * W + x]] for x in range(W)) for y in range(H)] + ['```', '']
    open(os.path.join(out_dir, 'mtr_search.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
