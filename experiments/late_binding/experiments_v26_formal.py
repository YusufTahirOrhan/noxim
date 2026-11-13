"""v26 Part A (results_v26_faults/PREREGISTRATION.md): the model check on all fault patterns. Run through experiments_v26.py:
  aneg    the controls: R3 and the F1 source rule removed (the CDG must be cyclic); the subset check between two relations (must fail)
          -> formal_controls.md
  a1      2x2, all 50,625 masks x CI_XY_XY, CI_XY_O1, in chunks under ~/lbraw/v26/a1 (a finished chunk is not run again)
  a1csv   formal_all_2x2.csv, formal_all_2x2.md from the chunks (the chunks are deleted when the file is complete)
  a2      3x3 and 4x4 (extra: the size), the four sets -> formal_a2_<size>.csv; with both sizes done: formal_a2.csv, formal_a2.md
  a2sub   the second half of the argument for set 2, on 2x2 -> formal_subset_2x2.csv, formal_subset_2x2.md
Model: formal/impl_relation_check.py with the settings of formal/xy_check.py (UP_KEEP = True, both VNs explored on Horizontal -> Down,
R3 on the input VN, the F1 source rule). The model is not changed. Checks per mask and relation: (1) CDG acyclic, (2) no dead-end state,
(3) state graph acyclic and its longest path, (4) the CDG edges are a subset of the CDG edges of the fault-free mask of the same relation.
"""
import csv
import glob
import json
import os
import pickle
import random
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'formal'))
import experiments_v5 as E5  # noqa: E402
import experiments_v26 as X  # noqa: E402

RES, NL = X.RES, X.NL
RELS = ['CI_XY_XY', 'CI_XY_O1']
COLS = ['size', 'set', 'mask', 'relation', 'faulty_vls', 'cdg_acyclic', 'dead_ends', 'state_graph_acyclic', 'longest_path', 'cdg_nodes', 'cdg_edges',
        'edges_outside_fault_free', 'pass']
N2 = 15 ** 4
CHUNK = 375                      # masks per chunk of A1 (135 chunks)
SUB_MASKS = 1000                 # masks of the second-half test
FF = {}                          # relation -> the CDG edges of the fault-free mask (per process)


def _model(size):
    import impl_relation_check as I
    cx, cy = E5.SIZES[size]
    I.set_size(cx, cy, 4, 4)
    I.UP_KEEP = True
    I.NO_R3 = False
    return I


def explore_all(I, rel, faulty, lean):
    """(CDG edge set, CDG node count, dead ends, state graph acyclic, longest path, CDG acyclic). lean: one destination at a time, as
    impl_relation_check.job_lean (the state graph is the disjoint union of the per-destination graphs)."""
    import networkx as nx
    if not lean:
        cdg, sg, dead = I.explore(I.ALL_CONFIGS[rel], faulty)
        sga = nx.is_directed_acyclic_graph(sg)
        return set(cdg.edges()), cdg.number_of_nodes(), len(dead), sga, (nx.dag_longest_path_length(sg) if sga else -1), nx.is_directed_acyclic_graph(cdg)
    allg = nx.DiGraph()
    dead, sga, longest = 0, True, 0
    for d in I.ALL_CHIP_NODES:
        cdg, sg, dl = I.explore(I.ALL_CONFIGS[rel], faulty, dest=d)
        allg.add_edges_from(cdg.edges())
        dead += len(dl)
        if sga and nx.is_directed_acyclic_graph(sg):
            longest = max(longest, nx.dag_longest_path_length(sg) if sg.number_of_nodes() else 0)
        else:
            sga = False
    return set(allg.edges()), allg.number_of_nodes(), dead, sga, (longest if sga else -1), nx.is_directed_acyclic_graph(allg)


def ff_file(size):
    return os.path.join(X.raw('ff'), 'ff_edges_%s.pkl' % size)


def ff_edges(size):
    """{relation: CDG edge set of the fault-free mask}; computed once per size and kept under ~/lbraw/v26/ff."""
    f = ff_file(size)
    if not os.path.exists(f):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        I = _model(size)
        d = {rel: explore_all(I, rel, frozenset(), size != '2x2')[0] for rel in RELS}
        pickle.dump(d, open(f + '.tmp', 'wb'))
        os.replace(f + '.tmp', f)
    return pickle.load(open(f, 'rb'))


def check(I, size, set_name, mask, rel):
    """One line of the tables: the four checks of one (mask, relation). mask: the hex string."""
    faulty = X.mask_set(mask)
    edges, nodes, dead, sga, longest, acyc = explore_all(I, rel, faulty, size != '2x2')
    outside = len(edges - FF[rel])
    ok = acyc and dead == 0 and sga and outside == 0
    return dict(zip(COLS, [size, set_name, mask, rel, len(faulty), int(acyc), dead, int(sga), longest, nodes, len(edges), outside, int(ok)]))


def _init(size):
    global FF, MODEL
    MODEL = _model(size)
    FF = ff_edges(size)


def write_csv(path, rows, cols=COLS):
    with open(path + '.tmp', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    os.replace(path + '.tmp', path)


# ---- A1: 2x2, exhaustive ----
def a1_mask(i):
    """Mask number i of the 15^4: digit c of i in base 15 is the fault pattern of chiplet c (0 = no fault, 1..14)."""
    v = 0
    for c in range(4):
        v |= (i % 15) << (4 * c)
        i //= 15
    return '0x%04X' % v


def _a1_chunk(k):
    out = os.path.join(X.raw('a1'), 'chunk_%03d.csv' % k)
    if os.path.exists(out):
        return k, 0.0, None
    t = time.time()
    rows = [check(MODEL, '2x2', 'all', a1_mask(i), rel) for i in range(k * CHUNK, min((k + 1) * CHUNK, N2)) for rel in RELS]
    write_csv(out, rows)
    return k, time.time() - t, all(r['pass'] for r in rows)


def a1(nproc):
    from multiprocessing import Pool
    os.makedirs(X.raw('a1'), exist_ok=True)
    ff_edges('2x2')
    nchunks = (N2 + CHUNK - 1) // CHUNK
    t, cpu, ok, done = time.time(), 0.0, True, 0
    with Pool(nproc, initializer=_init, initargs=('2x2',)) as pool:
        for k, sec, good in pool.imap_unordered(_a1_chunk, range(nchunks), chunksize=1):
            cpu += sec
            done += 1
            if good is False:
                ok = False
                print('chunk %d: A CHECK FAILED' % k, flush=True)
            if done % 10 == 0 or done == nchunks:
                print('%s chunks %d / %d, wall %.0f s, CPU of this call %.0f s' % (time.strftime('%H:%M:%S'), done, nchunks, time.time() - t, cpu), flush=True)
    json.dump(dict(nproc=nproc, wall_seconds=time.time() - t, cpu_seconds_this_call=cpu), open(os.path.join(X.raw('a1'), 'time_%d.json' % int(t)), 'w'))
    print('A1 chunks complete: %d; all pass in the chunks of this call: %s' % (len(glob.glob(os.path.join(X.raw('a1'), 'chunk_*.csv'))), ok), flush=True)
    return ok


def summary_lines(rows, title):
    """Per relation: masks, checks failed per kind, longest path, largest CDG."""
    L = [title, '', '| relation | masks | cyclic CDG | masks with dead ends | masks with a cyclic state graph | masks with CDG edges outside the fault-free CDG | '
         'all four checks pass | longest path (hops) | largest CDG (nodes / edges) | fault-free CDG (nodes / edges) |', '|---|---|---|---|---|---|---|---|---|---|']
    for rel in RELS:
        r = [x for x in rows if x['relation'] == rel]
        if not r:
            continue
        big = max(r, key=lambda x: int(x['cdg_edges']))
        ff = [x for x in r if int(x['faulty_vls']) == 0]
        L.append('| %s | %d | %d | %d | %d | %d | %d | %d | %s / %s | %s |' % (
            rel, len(r), sum(1 for x in r if not int(x['cdg_acyclic'])), sum(1 for x in r if int(x['dead_ends']) > 0), sum(1 for x in r if not int(x['state_graph_acyclic'])),
            sum(1 for x in r if int(x['edges_outside_fault_free']) > 0), sum(1 for x in r if int(x['pass'])), max(int(x['longest_path']) for x in r), big['cdg_nodes'], big['cdg_edges'],
            ('%s / %s' % (ff[0]['cdg_nodes'], ff[0]['cdg_edges'])) if ff else '-'))
    return L


def a1csv():
    files = sorted(glob.glob(os.path.join(X.raw('a1'), 'chunk_*.csv')))
    rows = []
    for f in files:
        rows += list(csv.DictReader(open(f)))
    want = [(a1_mask(i), rel) for i in range(N2) for rel in RELS]
    have = [(r['mask'], r['relation']) for r in rows]
    print('A1 lines: %d (expected %d); in the expected order: %s' % (len(rows), len(want), have == want))
    if have != want:
        return False
    write_csv(os.path.join(RES, 'formal_all_2x2.csv'), rows)
    times = [json.load(open(f)) for f in glob.glob(os.path.join(X.raw('a1'), 'time_*.json'))]
    ok = all(int(r['pass']) for r in rows)
    byk = {}
    for r in rows:
        byk.setdefault(int(r['faulty_vls']), []).append(r)
    L = ['# v26 A1: the model check on all fault patterns of 2x2 (experiments_v26.py a1, a1csv)', '',
         'All 15^4 = %d masks that leave every chiplet a functional VL (the fault-free mask included), relations `CI_XY_XY` (the main row) and `CI_XY_O1` (the second row):' % N2,
         '%d checks, one line each in `formal_all_2x2.csv`. Model: `formal/impl_relation_check.py` with the settings of `formal/xy_check.py` (the paper\'s Up rule,' % len(rows),
         'both VNs explored on Horizontal -> Down, R3 on the input VN, the F1 source rule). Per mask and relation: (1) CDG acyclic, (2) no dead-end state, (3) state graph',
         'acyclic and its longest path, (4) every CDG edge is an edge of the fault-free CDG of the same relation.', '']
    L += summary_lines(rows, '## Result') + ['', '**%d lines, all four checks pass on every line: %s.**' % (len(rows), 'yes' if ok else 'NO'), '']
    L += ['## By the number of faulty VLs', '', '| faulty VLs | masks | checks | pass | longest path (hops): min - max | CDG edges: min - max |', '|---|---|---|---|---|---|']
    for k in sorted(byk):
        r = byk[k]
        L.append('| %d | %d | %d | %d | %d - %d | %d - %d |' % (k, len(r) // len(RELS), len(r), sum(int(x['pass']) for x in r), min(int(x['longest_path']) for x in r),
                                                              max(int(x['longest_path']) for x in r), min(int(x['cdg_edges']) for x in r), max(int(x['cdg_edges']) for x in r)))
    if times:
        L += ['', 'Time: %.0f CPU-seconds in %d call(s) (%.2f s per check), %.0f s wall in all.' % (
            sum(x['cpu_seconds_this_call'] for x in times), len(times), sum(x['cpu_seconds_this_call'] for x in times) / len(rows), sum(x['wall_seconds'] for x in times))]
    open(os.path.join(RES, 'formal_all_2x2.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if ok:
        shutil.rmtree(X.raw('a1'))
    return ok


# ---- controls ----
def aneg():
    import networkx as nx
    I = _model('2x2')
    L = ['# v26 Part A: controls (experiments_v26.py aneg)', '', 'The checks must be able to fail. 2x2, the fault-free mask.', '',
         '## (a) R3 and the F1 source rule removed (`impl_relation_check.NO_R3 = True`)', '', '| relation | CDG acyclic | expected |', '|---|---|---|']
    res = {}
    I.NO_R3 = True
    for rel, exp in (('A_fixed_XY', 'no (the control of `xy_check.py`)'), ('CI_XY_XY', 'reported'), ('CI_XY_O1', 'reported')):
        cdg, sg, dead = I.explore(I.ALL_CONFIGS[rel], frozenset())
        res[rel] = nx.is_directed_acyclic_graph(cdg)
        L.append('| %s | %s | %s |' % (rel, 'yes' if res[rel] else '**no: cyclic**', exp))
    I.NO_R3 = False
    ff = {rel: explore_all(I, rel, frozenset(), False) for rel in RELS + ['A_fixed_XY']}
    a, b = ff['CI_XY_O1'][0], ff['CI_XY_XY'][0]
    L += ['', '## (b) The subset check between two relations', '',
          'Fault-free CDG: `CI_XY_XY` %d nodes / %d edges, `CI_XY_O1` %d nodes / %d edges, the fixed pair `A_fixed_XY` %d / %d (all three acyclic: %s).' % (
              ff['CI_XY_XY'][1], len(b), ff['CI_XY_O1'][1], len(a), ff['A_fixed_XY'][1], len(ff['A_fixed_XY'][0]), 'yes' if all(x[5] for x in ff.values()) else 'NO'),
          'Edges of `CI_XY_O1` that are not edges of `CI_XY_XY`: **%d** (expected: more than 0, so the subset check reports a failure here). Edges of `CI_XY_XY` that are' % len(a - b),
          'not edges of `CI_XY_O1`: %d. Edges of the fixed pair that are not edges of `CI_XY_XY`: %d (the fixed pair is the late entry with one candidate).' % (
              len(b - a), len(ff['A_fixed_XY'][0] - b)), '']
    good = (not res['A_fixed_XY']) and len(a - b) > 0
    L += ['**Both controls behave as expected: %s.**' % ('yes' if good else 'NO')]
    open(os.path.join(RES, 'formal_controls.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return good


# ---- A2: 3x3 and 4x4 ----
def a2_jobs(size, n_set3=None):
    mf = X.masks_file()
    a = mf['a2'][size]
    s3 = a['set3'] if n_set3 is None else a['set3'][:n_set3]
    sets = [('1 fault-free', a['set1']), ('2 one chiplet', a['set2']), ('3 random', s3), ('4 Part B', [e['mask'] for e in mf['part_b'] if e['size'] == size])]
    return [(size, name, m, rel) for name, ms in sets for m in ms for rel in RELS]


def _a2_name(j):
    return '%s__%s__%s__%s' % (j[0], j[1].split()[0], j[2], j[3])


def _a2_job(j):
    out = os.path.join(X.raw('a2'), _a2_name(j) + '.json')
    if os.path.exists(out):
        return json.load(open(out))
    t = time.time()
    r = check(MODEL, *j)
    r['seconds'] = round(time.time() - t, 1)
    json.dump(r, open(out + '.tmp', 'w'))
    os.replace(out + '.tmp', out)
    return r


def a2(nproc, size):
    """The four sets of one size. 4x4: the time rule of the pre-registration (24 checks spread evenly first)."""
    from multiprocessing import Pool
    os.makedirs(X.raw('a2'), exist_ok=True)
    ff_edges(size)
    jobs = a2_jobs(size)
    note = ''
    t = time.time()
    with Pool(nproc, initializer=_init, initargs=(size,)) as pool:
        if size == '4x4':
            rule = os.path.join(X.raw('a2'), 'time_rule_4x4.json')
            if not os.path.exists(rule):
                step = len(jobs) // 24
                sample = jobs[::step][:24]
                t0 = time.time()
                rs = pool.map(_a2_job, sample, chunksize=1)
                per = sum(r['seconds'] for r in rs) / len(rs)
                est = per * len(jobs) / nproc / 3600.0
                json.dump(dict(sample=len(sample), step=step, mean_seconds=per, wall_seconds=time.time() - t0, checks=len(jobs), nproc=nproc, estimate_hours=est,
                               set3_masks=30 if est > 4.0 else X.A2_RANDOM['4x4']), open(rule, 'w'), indent=1)
            rl = json.load(open(rule))
            print('time rule 4x4: %d checks, mean %.0f s, estimate %.2f h with %d processes -> set 3 has %d masks' % (
                rl['sample'], rl['mean_seconds'], rl['estimate_hours'], rl['nproc'], rl['set3_masks']), flush=True)
            jobs = a2_jobs(size, rl['set3_masks'])
        res, n = [], 0
        for r in pool.imap(_a2_job, jobs, chunksize=1):
            res.append(r)
            n += 1
            if not r['pass']:
                print('A CHECK FAILED: %s' % r, flush=True)
            if n % 50 == 0 or n == len(jobs):
                print('%s %s checks %d / %d, wall %.0f s' % (time.strftime('%H:%M:%S'), size, n, len(jobs), time.time() - t), flush=True)
    write_csv(os.path.join(RES, 'formal_a2_%s.csv' % size), res, COLS + ['seconds'])
    ok = all(r['pass'] for r in res)
    print('%s: %d checks, all pass: %s; wall of this call %.0f s; CPU %.0f s%s' % (size, len(res), ok, time.time() - t, sum(r['seconds'] for r in res), note), flush=True)
    return ok


def a2md():
    rows = []
    for size in ('3x3', '4x4'):
        f = os.path.join(RES, 'formal_a2_%s.csv' % size)
        if os.path.exists(f):
            rows += list(csv.DictReader(open(f)))
    if not rows:
        return
    write_csv(os.path.join(RES, 'formal_a2.csv'), rows, COLS + ['seconds'])
    L = ['# v26 A2: the model check on 3x3 and 4x4 (experiments_v26.py a2)', '',
         'Relations `CI_XY_XY` and `CI_XY_O1`, the model and the four checks of A1, with the per-destination exploration. Sets: 1 the fault-free mask; 2 every fault',
         'combination of one chiplet with all other chiplets fault-free; 3 random masks from the whole space (every chiplet draws one of its 15 patterns);',
         '4 the masks of Part B. One line per size, set, mask and relation in `formal_a2.csv`.', '',
         '| size | set | masks | checks | cyclic CDG | dead ends | cyclic state graph | CDG edges outside the fault-free CDG | pass | longest path (hops) | faulty VLs: min - max | CPU-seconds: mean (max) |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for size in ('3x3', '4x4'):
        for s in sorted({r['set'] for r in rows if r['size'] == size}):
            r = [x for x in rows if x['size'] == size and x['set'] == s]
            sec = [float(x['seconds']) for x in r]
            L.append('| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d - %d | %.0f (%.0f) |' % (
                size, s, len({x['mask'] for x in r}), len(r), sum(1 for x in r if not int(x['cdg_acyclic'])), sum(1 for x in r if int(x['dead_ends']) > 0),
                sum(1 for x in r if not int(x['state_graph_acyclic'])), sum(1 for x in r if int(x['edges_outside_fault_free']) > 0), sum(int(x['pass']) for x in r),
                max(int(x['longest_path']) for x in r), min(int(x['faulty_vls']) for x in r), max(int(x['faulty_vls']) for x in r), sum(sec) / len(sec), max(sec)))
    for size in ('3x3', '4x4'):
        r = [x for x in rows if x['size'] == size]
        if r:
            L += [''] + summary_lines(r, '## %s, per relation over the four sets' % size)
    rule = os.path.join(X.raw('a2'), 'time_rule_4x4.json')
    if os.path.exists(rule):
        rl = json.load(open(rule))
        L += ['', 'Time rule of 4x4 (pre-registered): %d checks spread evenly over the list took %.0f CPU-seconds on average; estimate for the %d checks with %d processes: %.2f h.' % (
            rl['sample'], rl['mean_seconds'], rl['checks'], rl['nproc'], rl['estimate_hours']),
              'Set 3 on 4x4 has %d masks%s.' % (rl['set3_masks'], '' if rl['set3_masks'] == X.A2_RANDOM['4x4'] else ' (reduced from %d by the 4 h rule)' % X.A2_RANDOM['4x4'])]
    ok = all(int(r['pass']) for r in rows)
    L += ['', '**%d checks, all four checks pass on every line: %s.**' % (len(rows), 'yes' if ok else 'NO')]
    open(os.path.join(RES, 'formal_a2.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


# ---- the second half of the argument for set 2, on 2x2 ----
def sub_masks():
    """1,000 masks of A1 with faults in at least two chiplets, drawn with their own random.Random(2611)."""
    rnd = random.Random(X.MASK_SEED)
    out = []
    while len(out) < SUB_MASKS:
        m = a1_mask(rnd.randrange(N2))
        if m not in out and sum(1 for x in X.per_chiplet('2x2', m) if x) >= 2:
            out.append(m)
    return out


def reach_states(I, rel, faulty, c):
    """The reachable (state, channel) nodes of the packets with a destination in chiplet c."""
    out = set()
    for d in I.ALL_CHIP_NODES:
        if I.chiplet_of(d) != c:
            continue
        cdg, sg, dead, init, dead_nodes, nseen, delivered = I.explore(I.ALL_CONFIGS[rel], faulty, detail=True, dest=d)
        nodes = set(sg.nodes()) | {(st, None) for st in init} | dead_nodes | delivered
        assert len(nodes) == nseen, (len(nodes), nseen)
        out |= nodes
    return out


def _sub_job(m):
    I = MODEL
    faulty = X.mask_set(m)
    rows = []
    for rel in RELS:
        for c in range(4):
            own = frozenset(v for v in faulty if v // 4 == c)
            a = reach_states(I, rel, faulty, c)
            b = reach_states(I, rel, own, c)
            rows.append(dict(mask=m, relation=rel, chiplet=c, faults_of_the_chiplet=len(own), faults_elsewhere=len(faulty) - len(own), states_mask=len(a), states_restricted=len(b),
                             states_outside=len(a - b), subset=int(a <= b)))
    return rows


def a2sub(nproc):
    from multiprocessing import Pool
    ms = sub_masks()
    t = time.time()
    rows = []
    with Pool(nproc, initializer=_init, initargs=('2x2',)) as pool:
        for k, r in enumerate(pool.imap(_sub_job, ms, chunksize=4)):
            rows += r
            if (k + 1) % 100 == 0:
                print('%s masks %d / %d, wall %.0f s' % (time.strftime('%H:%M:%S'), k + 1, len(ms), time.time() - t), flush=True)
    cols = ['mask', 'relation', 'chiplet', 'faults_of_the_chiplet', 'faults_elsewhere', 'states_mask', 'states_restricted', 'states_outside', 'subset']
    write_csv(os.path.join(RES, 'formal_subset_2x2.csv'), rows, cols)
    ok = all(r['subset'] for r in rows)
    L = ['# v26 A2: the second half of the argument for set 2, tested on 2x2 (experiments_v26.py a2sub)', '',
         'For %d masks of A1 with faults in at least two chiplets (drawn with `random.Random(%d)`), both relations and each chiplet c: the reachable states of the packets with a' % (
             len(ms), X.MASK_SEED),
         'destination in chiplet c under the mask must be a subset of those under the mask that keeps only the faults of chiplet c. A state is the model\'s search node:',
         '(phase, router, last move, candidate masks, VN, destination) and the channel it arrived on.', '',
         '| relation | comparisons (mask, chiplet) | subset holds | states under the mask: mean | states under the restricted mask: mean | the two sets are equal | comparisons with faults elsewhere |',
         '|---|---|---|---|---|---|---|']
    for rel in RELS:
        r = [x for x in rows if x['relation'] == rel]
        L.append('| %s | %d | %d | %.0f | %.0f | %d | %d |' % (rel, len(r), sum(x['subset'] for x in r), sum(x['states_mask'] for x in r) / len(r), sum(x['states_restricted'] for x in r) / len(r),
                                                            sum(1 for x in r if x['states_mask'] == x['states_restricted'] and x['subset']), sum(1 for x in r if x['faults_elsewhere'] > 0)))
    L += ['', '**%d comparisons, the subset holds in every one: %s.** Wall time %.0f s with %d processes.' % (len(rows), 'yes' if ok else 'NO', time.time() - t, nproc)]
    open(os.path.join(RES, 'formal_subset_2x2.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok


def run_stage(stage, nproc, extra):
    if stage == 'a1':
        sys.exit(0 if a1(nproc) else 1)
    elif stage == 'a1csv':
        sys.exit(0 if a1csv() else 1)
    elif stage == 'aneg':
        sys.exit(0 if aneg() else 1)
    elif stage == 'a2':
        ok = a2(nproc, extra)
        a2md()
        sys.exit(0 if ok else 1)
    elif stage == 'a2md':
        a2md()
    elif stage == 'a2sub':
        sys.exit(0 if a2sub(nproc) else 1)
    else:
        raise SystemExit(__doc__)
