"""v26 A3 (results_v26_faults/PREREGISTRATION.md): conformance of the formal model with the simulator. Run through experiments_v26.py:
  a3_build    instrumented copy of the simulator (results_v26_faults/conf/patch_hopdump.py, hopdump.inc) -> ~/lbbin/noxim_v26_hop
  a3_control  the comparison must be able to fail: 2x2 hops replayed through deliberately wrong models -> conformance_controls.md
  a3_run      per (row, size, mask, seed): the uniform and the hotspot run at 1.0 x Lsat with bin/noxim and with the instrumented copy
              (statistics file byte-identical?), and every recorded hop of a head flit replayed through the model
              -> ~/lbraw/v26/a3/<job>.json. extra = SEEDS[:SIZES[:base]], e.g. "1" (default), "2,3:2x2", "1::base" (the two masks with ladders of round 25)
  a3_report   conformance.csv, conformance.md; prints the (row, size) with fewer than 1,000,000 compared hops
The replay does not re-implement the routing rules. For every destination it lets formal/impl_relation_check.explore() build the
model's state graph (the function the model check uses, unchanged) and looks every recorded hop up in that graph:
  1. the simulator's state before the hop must be a node of the graph;
  2. the set of outputs the simulator offers must equal the set of moves on the edges leaving that node;
  3. the hop taken (next router, VN, candidate masks) must be one of those edges.
Rows and relations: CI_heurLA_X_LF -> CI_XY_XY, CI_heurLA_O_LF -> CI_XY_O1, DeFT_P -> A_fixed_XY (the fixed pair).
"""
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'formal'))
from runner import BIN, ENV  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v26 as X  # noqa: E402

RES, NL = X.RES, X.NL
CONF = os.path.join(RES, 'conf')
HOPBIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_v26_hop')
RELATION = {'DeFT_P': 'A_fixed_XY', X.MAIN: 'CI_XY_XY', X.SECOND: 'CI_XY_O1'}
ROWS = ['DeFT_P', X.MAIN, X.SECOND]
PATTERNS = ('uniform', 'hotspot')
NEED = 1000000
LETTER = {0: 'N', 1: 'E', 2: 'S', 3: 'W', 4: 'L', 5: 'H'}
OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
DIRS = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}


def build():
    dst = X.raw('hop_build')
    os.makedirs(X.RAW, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(CONF, 'patch_hopdump.py'), os.path.abspath(os.path.join(HERE, '..', '..')), dst], check=True)
    with open(os.path.join(X.RAW, 'hop_build.log'), 'w') as lf:
        subprocess.run(['make', '-C', os.path.join(dst, 'bin'), '-j4', 'MODULE=noxim_hop'], stdout=lf, stderr=subprocess.STDOUT, check=True)
    shutil.copy(os.path.join(dst, 'bin', 'noxim_hop'), HOPBIN)
    print('built', HOPBIN)


# ---- runs ----
def a3_masks(size):
    """(label, mask): fault-free, the same VL faulty in every chiplet, and mask 1 of each rate of Part B."""
    return [('fault-free', E5.FREE[size]), ('same VL in every chiplet', E5.NORTH[size])] + \
        [('rate %s, mask 1' % e['rate'], e['mask']) for e in X.part_b() if e['size'] == size and e['index'] == 1]


def rate_of(size, pattern, mask):
    """1.0 x Lsat of DeFT_P: the ladders of round 25 for the fault-free and the same-VL mask, those of Part B otherwise."""
    if mask in (E5.FREE[size], E5.NORTH[size]):
        return json.load(open(os.path.join(HERE, 'results_v25_confirm', 'load_points_v25.json')))[X24.lkey(size, pattern, mask)]['eval'][3]
    return json.load(open(os.path.join(RES, 'load_points_v26.json')))['%s__%s__%s' % (size, pattern, mask)]['eval'][1]


def jobs(seeds, sizes, base=False):
    """base: the fault-free and the same-VL mask only (their ladders are those of round 25, so they can run before the ladders of Part B)."""
    return [(row, size, label, mask, seed) for size in sizes for row in ROWS for label, mask in (a3_masks(size)[:2] if base else a3_masks(size)) for seed in seeds]


def jname(row, size, mask, seed):
    return 'a3__%s__%s__%s__s%d' % (row, size, mask, seed)


def read_topo(path):
    t = {'vl': {}, 'dir': {}}
    for line in open(path):
        k = line.split()
        if k[0] == 'vl':
            t['vl'][int(k[1])] = [int(x) for x in k[2:]]
        elif k[0] == 'dir':
            t['dir'][int(k[1])] = (int(k[2]), int(k[3]))
        else:
            t[k[0]] = int(k[1]) if k[1].lstrip('-').isdigit() else k[1]
    return t


def dtype():
    import numpy as np
    return np.dtype([(n, '<i4') for n in ('router', 'dir_in', 'vc_in', 'src', 'dst', 'offered', 'out_dir', 'out_vc', 'lut_exit', 'lut_entry')] +
                    [(n, '<u8') for n in ('exit_before', 'entry_before', 'exit_after', 'entry_after')])


def bits(m):
    m = int(m)
    return frozenset(v for v in range(64) if m >> v & 1)


def check_topo(I, row, size, mask, t):
    """The geometry and the options of the run against the model's instance. Returns the list of differences."""
    import deft_cdg_model as dcm
    cx, cy = E5.SIZES[size]
    bad = []

    def want(name, got, exp):
        if got != exp:
            bad.append('%s: simulator %r, model %r' % (name, got, exp))
    want('footprint width', t['W'], dcm.W)
    want('footprint height', t['H'], cy * dcm.CH)
    want('chiplet routers', t['NCHIP_ROUTERS'], dcm.W * cy * dcm.CH)
    want('VLs', t['NVL'], 4 * cx * cy)
    want('Local port', t['DIRECTION_LOCAL'], 4)
    want('Hub port', t['DIRECTION_HUB'], 5)
    for d, let in ((0, 'N'), (1, 'E'), (2, 'S'), (3, 'W')):
        want('direction %d' % d, t['dir'][d], DIRS[let])
    faulty = X.mask_set(mask)
    for v in range(4 * cx * cy):
        fun, cep, iep, slot, chip = t['vl'][v]
        want('VL %d: position of the chiplet end' % v, (cep % t['W'], cep // t['W']), I.VLPOS[v])
        want('VL %d: interposer end' % v, iep - t['NCHIP_ROUTERS'], cep)
        want('VL %d: chiplet' % v, chip, v // 4)
        want('VL %d: functional' % v, fun, 0 if v in faulty else 1)
    for k in ('vn_rules', 'vn_rr', 'up_keep', 'rr_fallback'):
        want(k, t[k], 1)
    want('virtual channels', t['n_vc'], 2)
    if row == 'DeFT_P':
        want('routing', t['routing'], 'DEFT')
        want('lb_active', t['lb_active'], 0)
    else:
        want('routing', t['routing'], 'DEFT_LB')
        want('chip_tm (0 = XY)', t['chip_tm'], 0)
        want('ipos_tm (0 = XY, 3 = O1)', t['ipos_tm'], 0 if row == X.MAIN else 3)
        want('exit policy', t['exit_policy'], 'lut')
        want('entry policy', t['entry_policy'], 'late')
    return bad


def replay(I, relation, mask, t, u, cnt):
    """u: the distinct hop records, cnt: how often each occurred; relation, mask: the model's. Returns the counters and the first mismatches."""
    import numpy as np
    cfg = I.ALL_CONFIGS[relation]
    faulty = X.mask_set(mask)
    W, NCH, lb = t['W'], t['NCHIP_ROUTERS'], t['lb_active']
    res = dict(hops=0, ejections=0, distinct=int(len(u)), multi_offer_hops=0, by_phase=dict(X=0, S=0, I=0, D=0), mismatches=0, by_kind={}, first=[])

    def miss(kind, r, c, **kw):
        res['mismatches'] += c
        res['by_kind'][kind] = res['by_kind'].get(kind, 0) + c
        if len(res['first']) < 20:
            res['first'].append(dict(kind=kind, count=c, record={n: int(r[n]) for n in r.dtype.names}, **{k: repr(v) for k, v in kw.items()}))

    order = np.argsort(u['dst'], kind='stable')
    k = 0
    while k < len(order):
        dst = int(u['dst'][order[k]])
        d = (dst % W, dst // W)
        cdg, sg, dead, init, dead_nodes, nseen, delivered = I.explore(cfg, faulty, detail=True, dest=d)
        initset = {(st, None) for st in init}
        while k < len(order) and int(u['dst'][order[k]]) == dst:
            r, c = u[order[k]], int(cnt[order[k]])
            k += 1
            cur, din, vn, src, o, ovc = int(r['router']), int(r['dir_in']), int(r['vc_in']), int(r['src']), int(r['out_dir']), int(r['out_vc'])
            ip = cur >= NCH
            idx = cur - NCH if ip else cur
            p, s = (idx % W, idx // W), (src % W, src // W)
            cs, cd = I.chiplet_of(s), I.chiplet_of(d)
            if lb:
                ex, en, ex2, en2 = bits(r['exit_before']), bits(r['entry_before']), bits(r['exit_after']), bits(r['entry_after'])
            else:
                ex = ex2 = frozenset([int(r['lut_exit'])])
                en = en2 = frozenset([int(r['lut_entry'])])
            last = LETTER[(din + 2) % 4] if din < 4 else None
            prev = (p[0] - DIRS[last][0], p[1] - DIRS[last][1]) if last else None
            here = I.POS2VL.get(p)
            # the model's node for the state before the hop
            if not ip and cs == cd and I.chiplet_of(p) == cs and din != 5:
                ph = 'X'
                node = (('X', p, last, d, vn, None), ('C', prev, p, vn) if last else None)
            elif not ip and cs != cd and I.chiplet_of(p) == cs and din != 5:
                ph = 'S'
                node = (('S', p, last, (ex, en), vn, d), ('C', prev, p, vn) if last else None)
            elif ip and cs != cd and din != 4:
                ph = 'I'
                node = (('I', p, last, (ex, en), vn, d), ('I', prev, p, vn) if last else ('D', here, vn))
            elif not ip and cs != cd and I.chiplet_of(p) == cd and din != 4:
                ph = 'D'
                node = (('D', p, last, None, 1, d), ('C', prev, p, vn) if last else ('U', here, vn))
            else:
                miss('the packet is in a place the model has no phase for', r, c)
                continue
            res['by_phase'][ph] += c
            if node not in sg and node not in initset:
                miss('state before the hop is not a state of the model', r, c, model_node=node)
                continue
            succ = list(sg.successors(node)) if node in sg else []
            if node in delivered:
                moff = {'L'}
            else:
                moff = set()
                for st2, ch2 in succ:
                    if ch2[0] in ('C', 'I'):
                        dx, dy = ch2[2][0] - ch2[1][0], ch2[2][1] - ch2[1][1]
                        moff.add([let for let, v in DIRS.items() if v == (dx, dy)][0])
                    else:
                        moff.add('H')
            soff = {LETTER.get(b, '?%d' % b) for b in range(31) if int(r['offered']) >> b & 1}
            if soff != moff:
                miss('offered outputs differ', r, c, model_node=node, simulator_offers=sorted(soff), model_offers=sorted(moff))
                continue
            if o == 4:
                res['ejections'] += c
                if node not in delivered:
                    miss('the simulator delivers where the model does not', r, c, model_node=node)
                continue
            res['hops'] += c
            if len(soff) > 1:
                res['multi_offer_hops'] += c
            if o == 5:
                if ph == 'S':
                    nxt = (('I', p, None, (ex2, en2), ovc, d), ('D', here, ovc))
                elif ph == 'I':
                    nxt = (('D', p, None, None, 1, d), ('U', here, ovc))
                else:
                    nxt = None
            else:
                mv = LETTER[o]
                q = (p[0] + DIRS[mv][0], p[1] + DIRS[mv][1])
                if ph == 'X':
                    nxt = (('X', q, mv, d, ovc, None), ('C', p, q, ovc))
                elif ph == 'S':
                    nxt = (('S', q, mv, (ex2, en2), ovc, d), ('C', p, q, ovc))
                elif ph == 'I':
                    nxt = (('I', q, mv, (ex2, en2), ovc, d), ('I', p, q, ovc))
                else:
                    nxt = (('D', q, mv, None, 1, d), ('C', p, q, ovc))
            if nxt is None or not sg.has_edge(node, nxt):
                miss('the hop taken is not a transition of the model', r, c, model_node=node, simulator_next=nxt, model_next=succ)
    return res


def _sim(binary, args, out, env):
    subprocess.run([binary] + list(args) + ['-stats_file', out], cwd=BIN, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=14400)


def model(size):
    import impl_relation_check as I
    cx, cy = E5.SIZES[size]
    I.set_size(cx, cy, 4, 4)
    I.UP_KEEP = True
    I.NO_R3 = False
    return I


def collect(I, row, size, mask, seed, patterns=PATTERNS):
    """The runs of one (row, size, mask, seed) with bin/noxim and with the instrumented copy. Returns (run records, topology differences,
    the topology the simulator reported, the distinct hop records, their counts)."""
    import numpy as np
    runs, parts, topo_bad, topo = [], [], [], None
    for p in patterns:
        rate = rate_of(size, p, mask)
        name, args = X.job('a3', size, row, X.row_args(size, row), 2, p, mask, rate, seed)
        pre = os.path.join(X.raw('a3'), name)
        _sim('./noxim', args, pre + '.ref.json', ENV)
        _sim(HOPBIN, args, pre + '.hop.json', dict(ENV, LB26_HOP=pre))
        same = os.path.exists(pre + '.ref.json') and os.path.exists(pre + '.hop.json') and open(pre + '.ref.json', 'rb').read() == open(pre + '.hop.json', 'rb').read()
        st = json.load(open(pre + '.ref.json'))
        topo = read_topo(pre + '.topo.txt')
        assert topo['record_bytes'] == dtype().itemsize, topo['record_bytes']
        a = np.fromfile(pre + '.hop.bin', dtype=dtype())
        topo_bad += ['%s: %s' % (p, x) for x in check_topo(I, row, size, mask, topo)]
        runs.append(dict(pattern=p, rate=rate, statistics_identical=bool(same), records=int(len(a)), received_packets=st['summary']['total_received_packets'],
                         dead_end_events=st['deft_lb']['dead_end_events']))
        parts.append(a)
        for ext in ('.ref.json', '.hop.json', '.hop.bin', '.topo.txt'):
            os.remove(pre + ext)
    a = np.concatenate(parts)
    del parts
    v = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize)))
    uv, cnt = np.unique(v, return_counts=True)
    return runs, topo_bad, topo, uv.view(a.dtype), cnt


def _job(arg):
    row, size, label, mask, seed = arg
    out = os.path.join(X.raw('a3'), jname(row, size, mask, seed) + '.json')
    if os.path.exists(out):
        return json.load(open(out))
    t0 = time.time()
    I = model(size)
    res = dict(row=row, size=size, label=label, mask=mask, seed=seed, relation=RELATION[row])
    res['runs'], res['topology_differences'], topo, u, cnt = collect(I, row, size, mask, seed)
    res.update(replay(I, RELATION[row], mask, topo, u, cnt))
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(out + '.tmp', 'w'), indent=1)
    os.replace(out + '.tmp', out)
    return res


def control():
    """The comparison must be able to fail: hops of 2x2 runs replayed through a model that is deliberately not the simulator's."""
    os.makedirs(X.raw('a3'), exist_ok=True)
    size, free, north = '2x2', E5.FREE['2x2'], E5.NORTH['2x2']
    for p in PATTERNS:
        E5.gen_tables(size, p, [rate_of(size, p, free), rate_of(size, p, north)])
    I = model(size)
    L = ['# v26 A3: controls of the comparison (experiments_v26.py a3_control)', '',
         'The comparison must be able to fail. Hops of 2x2 runs (uniform and hotspot at 1.0 x Lsat, seed 1) are replayed through a model that is deliberately not the',
         'one of the run; each control must report mismatches. "The right model" lines replay the same hops through the model of the run and must report none.', '',
         '| control | hops of | replayed through | records compared | mismatches | kinds |', '|---|---|---|---|---|---|']
    ok = True

    def line(name, row, mask, relation, model_mask, expect, **flags):
        runs, tb, topo, u, cnt = collect(I, row, size, mask, 1)
        for k, v in flags.items():
            setattr(I, k, v)
        r = replay(I, relation, model_mask, topo, u, cnt)
        model(size)
        good = (r['mismatches'] > 0) == expect
        L.append('| %s | %s, mask %s | %s, mask %s%s | %d | %d%s | %s |' % (name, row, mask, relation, model_mask, ''.join(', %s = %s' % kv for kv in flags.items()), int(cnt.sum()),
                                                                         r['mismatches'], '' if good else ' **(unexpected)**', '; '.join('%s: %d' % kv for kv in sorted(r['by_kind'].items())) or '-'))
        return good
    ok &= line('the right model', X.SECOND, free, 'CI_XY_O1', free, False)
    ok &= line('the other interposer order', X.SECOND, free, 'CI_XY_XY', free, True)
    ok &= line('the right model', X.MAIN, free, 'CI_XY_XY', free, False)
    ok &= line('the Up rule of rounds 1-22 (the Up channel is VN1)', X.MAIN, free, 'CI_XY_XY', free, True, UP_KEEP=False)
    ok &= line('the entry fixed at injection', X.MAIN, free, 'A_fixed_XY', free, True)
    ok &= line('the right model', 'DeFT_P', north, 'A_fixed_XY', north, False)
    ok &= line('another fault mask (VL 1 faulty in every chiplet instead of VL 0)', 'DeFT_P', north, 'A_fixed_XY', '0x2222', True)
    L += ['', '**Every control behaves as expected: %s.**' % ('yes' if ok else 'NO')]
    open(os.path.join(RES, 'conformance_controls.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok


def run(nproc, extra):
    from multiprocessing import Pool
    f = (extra or '1').split(':')
    seeds = [int(x) for x in f[0].split(',')]
    sizes = f[1].split(',') if len(f) > 1 and f[1] else X.SIZES
    base = len(f) > 2 and f[2] == 'base'
    os.makedirs(X.raw('a3'), exist_ok=True)
    js = jobs(seeds, sizes, base)
    for size in sizes:
        for p in PATTERNS:
            E5.gen_tables(size, p, sorted({rate_of(size, p, j[3]) for j in js if j[1] == size}))
    print('A3 jobs: %d (seeds %s, sizes %s)' % (len(js), seeds, sizes), flush=True)
    t, ok = time.time(), True
    with Pool(nproc) as pool:
        for k, r in enumerate(pool.imap_unordered(_job, js, chunksize=1)):
            good = r['mismatches'] == 0 and not r['topology_differences'] and all(x['statistics_identical'] for x in r['runs'])
            ok = ok and good
            print('%s %3d / %d  %s %s %s s%d: hops %d, ejections %d, distinct %d, mismatches %d, statistics identical %s%s' % (
                time.strftime('%H:%M:%S'), k + 1, len(js), r['row'], r['size'], r['mask'], r['seed'], r['hops'], r['ejections'], r['distinct'], r['mismatches'],
                all(x['statistics_identical'] for x in r['runs']), '' if good else '   <== NOT CLEAN'), flush=True)
    print('wall %.0f s; all clean: %s' % (time.time() - t, ok), flush=True)
    return ok


def report():
    rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(X.raw('a3'), 'a3__*.json')))]
    if not rs:
        raise SystemExit('no A3 results')
    order = {(z, r): i for i, (z, r) in enumerate((z, r) for z in X.SIZES for r in ROWS)}
    rs.sort(key=lambda r: (order[(r['size'], r['row'])], [m for _, m in a3_masks(r['size'])].index(r['mask']), r['seed']))
    cols = ['row', 'relation', 'size', 'mask', 'mask_kind', 'seed', 'hops_compared', 'ejections_compared', 'distinct_records', 'hops_with_a_choice', 'hops_intra', 'hops_source_chiplet',
            'hops_interposer', 'hops_destination_chiplet', 'mismatches', 'topology_differences', 'runs', 'runs_with_identical_statistics', 'dead_end_events']
    with open(os.path.join(RES, 'conformance.csv'), 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator=NL)
        w.writerow(cols)
        for r in rs:
            w.writerow([r['row'], r['relation'], r['size'], r['mask'], r['label'], r['seed'], r['hops'], r['ejections'], r['distinct'], r['multi_offer_hops'], r['by_phase']['X'], r['by_phase']['S'],
                        r['by_phase']['I'], r['by_phase']['D'], r['mismatches'], len(r['topology_differences']), len(r['runs']), sum(1 for x in r['runs'] if x['statistics_identical']),
                        sum(x['dead_end_events'] for x in r['runs'])])
    L = ['# v26 A3: conformance of the model with the simulator (experiments_v26.py a3_build, a3_run, a3_report)', '',
         'An instrumented copy of the simulator (`conf/patch_hopdump.py`, `conf/hopdump.inc`; the repository\'s sources and `bin/noxim` are unchanged) records every hop of a',
         'head flit: router, input port, VN before, candidate masks before, destination, the outputs the routing function and the VN rule offer, the output taken, the VN and',
         'the masks after. Every record is looked up in the state graph that `formal/impl_relation_check.explore()` builds for the destination (the function the model check',
         'uses, unchanged, with the settings of `xy_check.py`): (1) the state before the hop is a node of the graph, (2) the offered outputs equal the moves on the edges',
         'leaving the node, (3) the hop taken is one of those edges. The arrival at the destination router is compared too (the model must have delivered there).',
         'Relations: DeFT_P -> `A_fixed_XY`, `CI_heurLA_X_LF` -> `CI_XY_XY`, `CI_heurLA_O_LF` -> `CI_XY_O1`. Runs: pipe_all 2, uniform and hotspot at 1.0 x Lsat of DeFT_P, six',
         'masks per size (fault-free, the same VL faulty in every chiplet, mask 1 of each rate of Part B). Before the replay the geometry and the options the simulator',
         'reports (VL positions, functional VLs, directions, turn models, VN options) are compared with the model\'s instance.', '',
         '| row | relation | size | seeds | runs | statistics byte-identical to bin/noxim | hops compared | of them with more than one offered output | arrivals at the destination compared | '
         'distinct records | topology differences | mismatches |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    need, tot = [], dict(hops=0, ej=0, mis=0, runs=0, ident=0, topo=0)
    for size in X.SIZES:
        for row in ROWS:
            g = [r for r in rs if r['row'] == row and r['size'] == size]
            if not g:
                continue
            h, e, m = sum(r['hops'] for r in g), sum(r['ejections'] for r in g), sum(r['mismatches'] for r in g)
            nr, ni, nt = sum(len(r['runs']) for r in g), sum(1 for r in g for x in r['runs'] if x['statistics_identical']), sum(len(r['topology_differences']) for r in g)
            L.append('| %s | %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | **%d** |' % (row, g[0]['relation'], size, ', '.join(str(s) for s in sorted({r['seed'] for r in g})), nr, ni, h,
                                                                                          sum(r['multi_offer_hops'] for r in g), e, sum(r['distinct'] for r in g), nt, m))
            for k, v in (('hops', h), ('ej', e), ('mis', m), ('runs', nr), ('ident', ni), ('topo', nt)):
                tot[k] += v
            if h < NEED:
                need.append((row, size, h))
    clean = tot['mis'] == 0 and tot['topo'] == 0 and tot['ident'] == tot['runs']
    L += ['', '**Total: %d hops and %d arrivals compared in %d runs; mismatches: %d; topology differences: %d; runs with statistics byte-identical to `bin/noxim`: %d of %d.**' % (
        tot['hops'], tot['ej'], tot['runs'], tot['mis'], tot['topo'], tot['ident'], tot['runs']), '',
          'Hops by phase of the model (all rows and sizes): intra-chiplet %d, source chiplet %d, interposer %d, destination chiplet %d. Dead-end events in these runs: %d.' % (
              sum(r['by_phase']['X'] for r in rs), sum(r['by_phase']['S'] for r in rs), sum(r['by_phase']['I'] for r in rs), sum(r['by_phase']['D'] for r in rs),
              sum(x['dead_end_events'] for r in rs for x in r['runs'])),
          'Per (row, size, mask, seed): `conformance.csv`.', '']
    if need:
        L += ['Fewer than %d compared hops so far: %s.' % (NEED, '; '.join('%s %s (%d)' % x for x in need)), '']
    bad = [r for r in rs if r['mismatches'] or r['topology_differences']]
    if bad:
        L += ['## Mismatches', '']
        for r in bad:
            L += ['### %s %s %s seed %d' % (r['row'], r['size'], r['mask'], r['seed']), '', 'By kind: %s' % r['by_kind'], ''] + ['* ' + x for x in r['topology_differences']]
            for x in r['first'][:5]:
                L += ['* %s (%d hops): record %s' % (x['kind'], x['count'], x['record'])] + ['  * %s: %s' % (k, x[k]) for k in x if k not in ('kind', 'count', 'record')]
            L.append('')
    L += ['**0 mismatches, as required: %s.**' % ('yes' if clean else 'NO')]
    open(os.path.join(RES, 'conformance.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    print('need more seeds:', need)
    return clean, need


def run_stage(stage, nproc, extra):
    if stage == 'a3_build':
        build()
    elif stage == 'a3_control':
        sys.exit(0 if control() else 1)
    elif stage == 'a3_run':
        sys.exit(0 if run(nproc, extra) else 1)
    elif stage == 'a3_report':
        clean, need = report()
        sys.exit(0 if clean else 1)
    else:
        raise SystemExit(__doc__)
