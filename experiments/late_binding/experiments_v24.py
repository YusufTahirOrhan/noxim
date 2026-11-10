"""v24 (results_v24_xy/): late binding without path adaptivity (XY and a VN-split order on the interposer).

Stages (python3 experiments_v24.py STAGE [nproc] [extra]; --shard i/n accepted by the run stages):
  repro     A0: the ten probe rows of the review, existing options only, the 8d84634 build -> repro_a0.json
  regress   B4: the 84-configuration set, bin/noxim with the v24 options absent and explicitly off, against the 8d84634 build
            (extra = the reference binary), whole stats JSON byte by byte -> regression.md
  busy      B3: busy_state on against off without lookahead (CI_qlLA_G, 2x2 and 4x4 uniform, 5 runs) -> busy_state_check.md
  equiv     B4: Q-learning with alpha = 0 against the heuristic under lookahead + fallback + busy_state -> equivalence.md
  repro2    B4: the six probe values that need the new options -> repro_b4.json
  formal    A2: formal/xy_check.py -> formal_xy.md
  drain     A3: drain tests (extra = v10 | bias | lf) -> drain_summary.csv (the rows of the three parts are kept)
  sat, points   B5: DeFT-P's chiptrans ladders (seed 101, pipe_all 2) -> load_points_v24.json
  b5        B5: the six chiptrans probe rows -> repro_b5.json
  reprodoc  reproduction.md from repro_a0.json, repro_b4.json and repro_b5.json
The tuning (C2), the centre-cut statistics (A4) and the Part D stages are in experiments_v24_eval.py and dispatched from here
(tunerule, tune1, choose1, tune2, choose2, cut, timing, eval, check, csv, sanity).
Raw outputs stay under ~/lbraw/v24 (not in the repository). Reference binary: ~/lbbin/noxim_8d84634.
Every VN-based method runs with DeFT-P's VN options and -traffic_rng 1; MTR and RC with -vc_per_hop 1; LUTs luts/v23.
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args, run_jobs, shard_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v24_xy')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v24')
REF_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_8d84634')
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)

# ---- options ----
VN_P, DST, TRNG, VCPH, LOOK = X23.VN_P, X23.DST, X23.TRNG, X23.VCPH, X23.LOOK


def lb(*kv):
    """['-deft_lb', k1, v1, '-deft_lb', k2, v2, ...]"""
    out = []
    for i in range(0, len(kv), 2):
        out += ['-deft_lb', str(kv[i]), str(kv[i + 1])]
    return out


IPX = lb('ipos_tm', 'XY')
IPOE = lb('ipos_tm', 'OE')
IPO1 = lb('ipos_tm', 'O1')
REL_X = lb('chip_tm', 'XY', 'ipos_tm', 'XY')
REL_O = lb('chip_tm', 'XY', 'ipos_tm', 'O1')
FALLBACK = lb('lookahead_fallback', 1)
BUSY = lb('busy_state', 1)
HOPS = lb('hop_stats', 1)
EXPLICIT_OFF = X23.EXPLICIT_OFF + lb('lut_bias', 0, 'lookahead_fallback', 0, 'busy_state', 0)


def raw(stage):
    return os.path.join(RAW, stage)


def dd(n):
    return lb('decision_delay', n)


def mask_of(size, kind):
    return E5.FREE[size] if kind == 'free' else E5.NORTH[size]


def job(stage, size, name, method_args, pipe, p, m, rate, seed, extra=()):
    """One run. method_args: the Noxim arguments of the method without pipe depth and without -traffic_rng (both are added here)."""
    rname = '%s__%s-p%d__%s-%s__%s__%.4f__s%d' % (stage, name, pipe, size, p, m, rate, seed)
    args = common_args(seed, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), p, rate), lut=X23.lut23(size, m)) + \
        E5.size_args(size) + list(method_args) + X23.pipe(pipe) + TRNG + list(extra) + E5.SIM
    return rname, args


def run_with(binary, jobs, out, nproc, timeout=7200):
    """Run (name, args) jobs with a given binary; returns {name: parsed JSON or None}. Existing outputs are kept."""
    from multiprocessing import Pool
    os.makedirs(out, exist_ok=True)
    tagged = [(('bin', binary, [], n, a), out) for n, a in jobs]
    with Pool(nproc) as pool:
        res = pool.map(E10._run_tagged, tagged, chunksize=1)
    return {k[1]: v for k, v in res}


def tagged_path(out, name):
    return os.path.join(out, 'bin__%s.json' % name)


def stat(d):
    """(accepted flits/node/cycle, mean latency, received packets, p99) of a run's JSON."""
    s = d['summary']
    return (s['average_ip_throughput_flits_per_cycle_per_ip'], s['global_average_delay_cycles'], s['total_received_packets'], d['deft_lb']['delay_p99'])


# ---- A0 ----
A0_ROWS = [
    # no, size, v23 method, extra, pipe, pattern, mask kind, rate, received, latency (the review's probe values)
    (1, '4x4', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0050, 10469, 98.7693189416),
    (2, '4x4', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0070, 13434, 456.9803483698),
    (3, '4x4', 'CI_qlLA_G', IPX, 0, 'uniform', 'free', 0.0100, 20549, 185.3428877318),
    (4, '4x4', 'CI_qlLA_G', IPX, 0, 'uniform', 'north', 0.0075, 15317, 215.4711105308),
    (5, '4x4', 'CI_qlLA_G', IPX, 0, 'hotspot', 'free', 0.0022, 4567, 74.2583753011),
    (6, '4x4', 'DeFT_Dis', IPOE, 0, 'chipperm', 'free', 0.0050, 4397, 1833.8910620878),
    (7, '4x4', 'CI_qlLA_G', IPX + dd(1), 2, 'uniform', 'free', 0.0080, 16575, 95.7701357466),
    (8, '4x4', 'CI_qlLA_G', IPX + LOOK + dd(1), 2, 'uniform', 'free', 0.0080, 16569, 101.4833122095),
    (9, '3x3', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0100, 11657, 108.3540362014),
    (10, '2x2', 'CI_qlLA_G', IPX, 0, 'uniform', 'free', 0.0160, 8162, 247.8145062485),
]


def repro(nproc, binary=REF_BIN):
    out = raw('repro')
    js, meta = [], []
    for no, size, meth, extra, pipe, p, kind, rate, rec, lat in A0_ROWS:
        m = mask_of(size, kind)
        E5.gen_tables(size, p, [rate])
        n, a = job('a0', size, 'row%d' % no, X23.methods(size)[meth], pipe, p, m, rate, 91, extra)
        js.append((n, a))
        meta.append((no, size, meth, ' '.join(extra), pipe, p, m, rate, rec, lat, n))
    res = run_with(binary, js, out, nproc)
    rows = []
    for no, size, meth, extra, pipe, p, m, rate, rec, lat, n in meta:
        d = res[n]
        acc, l, r, _ = stat(d) if d else (None, None, None, None)
        rows.append(dict(no=no, size=size, method=meth, extra=extra, pipe_all=pipe, pattern=p, mask=m, rate=rate, probe_received=rec, probe_latency=lat,
                         received=r, latency=l, accepted=acc, same=bool(d) and r == rec and abs(l - lat) < 5e-10))
    json.dump(dict(binary=os.path.basename(binary), md5=E19.md5(binary), rows=rows), open(os.path.join(RES, 'repro_a0.json'), 'w'), indent=1)
    for r in rows:
        print(r['no'], r['size'], r['method'], r['extra'], r['received'], r['probe_received'], r['latency'], r['probe_latency'], 'same' if r['same'] else 'DIFFERENT')
    if all(r['same'] for r in rows):
        shutil.rmtree(out)
    return rows


# ---- variants of this round (Part C names) ----
CI = ['-routing', 'DEFT_LB'] + lb('exit', 'lut', 'entry', 'late')
FULL = ['-routing', 'DEFT_LB'] + lb('exit', 'late', 'entry', 'late')
REL = {'X': REL_X, 'O': REL_O, 'G': lb('chip_tm', 'XY', 'ipos_tm', 'OE')}
N_FAST = {'heur': 2, 'ql': 3}          # cycles of the fast selection (v21): heuristic CI 2, Q-learning 3
PART_C = ['CI_heurLA_X', 'CI_qlLA_X', 'CI_heurLA_O', 'CI_qlLA_O', 'FULL_qlLA_X']
MULTS9 = X23.MULTS9


def fmt(x):
    return '%g' % x


def heurLA(W, B, G, D, la=1):
    return ['-sel', 'DEFT_HEUR'] + lb('heur_w', fmt(W), 'heur_busy', fmt(B), 'heur_lookahead', la, 'hop_weight_ipos', fmt(G), 'lut_bias', fmt(D))


def qlLA(W, B, A, G, D):
    return ['-sel', 'DEFT_QL'] + lb('ql_w', fmt(W), 'ql_busy', fmt(B), 'ql_alpha', fmt(A), 'ql_key', 1, 'ql_eps', '0.0', 'ql_lookahead', 1,
                                    'hop_weight_ipos', fmt(G), 'lut_bias', fmt(D))


def sel_kind(name):
    """'heur', 'ql' or None (no tuned selection) of a variant name."""
    s = name.split('_')[1] if name.count('_') >= 2 else ''
    return {'heurLA': 'heur', 'heur': 'heur', 'qlLA': 'ql'}.get(s)


def variant(name, P=None):
    """Noxim arguments of a variant of this round, with DeFT-P's VN options. P: dict W, B, G, D (and A for Q-learning)."""
    if name == 'DeFT_P_O1':
        return ['-routing', 'DEFT_LB'] + lb('exit', 'lut', 'entry', 'lut') + REL_O + DST + VN_P
    scope, sel, rel = name.split('_')
    base = (CI if scope == 'CI' else FULL) + REL[rel]
    if sel == 'heurLA':
        a = heurLA(P['W'], P['B'], P['G'], P['D'])
    elif sel == 'heur':
        a = heurLA(P['W'], P['B'], P['G'], P['D'], la=0)
    elif sel == 'qlLA':
        a = qlLA(P['W'], P['B'], P['A'], P['G'], P['D'])
    elif sel == 'rand':
        a = ['-sel', 'RANDOM']
    else:
        raise ValueError(name)
    return base + a + VN_P


def mech(kind, sel):
    """Timing mechanism of a candidate: ideal (decision_delay 0, no lookahead), LF (lookahead with the fallback and the busy state, residual
    delay max(0, N_fast + 1 - W), W = pipe_all + 1 = 3) or DLY (no lookahead, decision_delay N_fast)."""
    if kind == 'ideal':
        return []
    if kind == 'LF':
        return LOOK + FALLBACK + BUSY + dd(max(0, N_FAST[sel] + 1 - 3))
    if kind == 'DLY':
        return dd(N_FAST[sel])
    raise ValueError(kind)


def _val(args, key):
    return float(args[args.index(key) + 1])


def params_v10(size):
    """The v10 selection parameters of the CI variants (experiments_v10.methods): gamma = 2, no lut_bias."""
    m = E10.methods(size)
    h, q = m['CI_heurLA_G'], m['CI_qlLA_G']
    return {'heur': dict(W=_val(h, 'heur_w'), B=_val(h, 'heur_busy'), G=2.0, D=0.0),
            'ql': dict(W=_val(q, 'ql_w'), B=_val(q, 'ql_busy'), A=_val(q, 'ql_alpha'), G=2.0, D=0.0)}


def variant_v10(size, name, **over):
    k = sel_kind(name)
    P = dict(params_v10(size)[k], **over) if k else None
    return variant(name, P)


def scenarios(size):
    """The five scenarios of this round."""
    f, n = E5.FREE[size], E5.NORTH[size]
    return [('uniform', f), ('hotspot', f), ('chipperm', f), ('chiptrans', f), ('uniform', n)]


LP_FILE = os.path.join(RES, 'load_points_v24.json')


def lkey(size, p, m, pipe=2):
    return '%s__%s__%s__p%d' % (size, p, m, pipe)


def lp23():
    return json.load(open(os.path.join(X23.RES, 'load_points_v23.json')))


def lp():
    return json.load(open(LP_FILE))


# ---- B4: regression ----
def regress(ref, nproc):
    import check_stats_regression as CSR
    from multiprocessing import Pool
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in SIZES:
        mm = E10.methods(size)
        r = E10.LP5['%s__uniform__%s' % (size, E5.FREE[size])]['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append(('%s__%s' % (v, size), a))
    new = os.path.join(BIN, 'noxim')
    tags = [('ref', ref, []), ('new', new, []), ('explicit', new, EXPLICIT_OFF)]
    jobs = [((t, b, ex, n, a), out) for t, b, ex in tags for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = {t: 0 for t, _, _ in tags[1:]}, []
    for n, _ in cf:
        base = os.path.join(out, 'ref__%s.json' % n)
        for t, _, _ in tags[1:]:
            f = os.path.join(out, '%s__%s.json' % (t, n))
            if os.path.exists(base) and os.path.exists(f) and open(base, 'rb').read() == open(f, 'rb').read():
                ok[t] += 1
            else:
                diffs.append('- %s differs: %s' % (t, n))
    L = ['# Regression with the v24 options off (experiments_v24.py regress)', '',
         'Reference: the 8d84634 build (round 23), md5 %s. New binary: md5 %s (A1: `-deft_lb ipos_tm YX | O1`; B1: `-deft_lb lut_bias`; '
         'B2: `-deft_lb lookahead_fallback`; B3: `-deft_lb busy_state`).' % (E19.md5(ref), E19.md5(new)),
         'Configurations: %d = the 84-configuration set of v14-v23. Comparison: the whole stats JSON file, byte by byte, against the reference build.' % len(cf), '',
         '* New binary, options absent: **%d / %d byte-identical**.' % (ok['new'], len(cf)),
         '* New binary, `%s` given: **%d / %d byte-identical**.' % (' '.join(EXPLICIT_OFF), ok['explicit'], len(cf)), ''] + (diffs or ['No differences.'])
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if not diffs:
        shutil.rmtree(out)
    return not diffs


# ---- B3 / B4: equivalence checks ----
CHECK_LOADS = (1, 3, 5, 7, 8)       # ladder indices of the five runs of a check (0.5, 1.0, 1.4, 2.0, 2.4 x Lsat), seeds 1-5
EQ_PARAMS = [(1, 4, 2, 4), (2, 0, 1, 0), (2, 4, 2, 2), (1, 0, 1, 4), (1, 4, 2, 0)]     # (W, B, G, D) of the five runs


def _strip(d, drop):
    return {k: v for k, v in d.items() if not any(k == x or (x.endswith('_') and k.startswith(x)) for x in drop)}


def busy_check(nproc):
    """B3: without lookahead, busy_state 1 must not change any statistic."""
    P = lp23()
    js, pairs = [], []
    for size in ('2x2', '4x4'):
        lad = P[lkey(size, 'uniform', E5.FREE[size], 0)]['eval']
        for i, seed in zip(CHECK_LOADS, range(1, 6)):
            E5.gen_tables(size, 'uniform', [lad[i]])
            a = job('busy', size, 'CI_qlLA_G_off', X23.methods(size)['CI_qlLA_G'], 0, 'uniform', E5.FREE[size], lad[i], seed)
            b = job('busy', size, 'CI_qlLA_G_on', X23.methods(size)['CI_qlLA_G'], 0, 'uniform', E5.FREE[size], lad[i], seed, BUSY)
            js += [a, b]
            pairs.append((size, lad[i], seed, a[0], b[0]))
    res = run_jobs(js, raw('busy'), nproc=nproc, timeout=7200)
    L = ['# B3: `-deft_lb busy_state 1` without lookahead (experiments_v24.py busy)', '',
         'CI_qlLA_G (the v23 odd-even variant, v10 parameters, DeFT-P VN options, `-traffic_rng 1`), uniform fault-free, pipe_all 0, no lookahead; five runs per size',
         '(the loads 0.5, 1.0, 1.4, 2.0 and 2.4 x Lsat of the v23 ladder with seeds 1-5). Compared: the whole `summary` block and the whole `deft_lb` block of the',
         'stats JSON except the field `busy_state` itself.', '',
         '| size | rate | seed | accepted off / on | latency off / on | p99 off / on | all statistics identical |', '|---|---|---|---|---|---|---|']
    same = 0
    for size, rate, seed, na, nb in pairs:
        a, b = res[na], res[nb]
        eq = a['summary'] == b['summary'] and _strip(a['deft_lb'], ['busy_state']) == _strip(b['deft_lb'], ['busy_state'])
        same += eq
        sa, sb = stat(a), stat(b)
        L.append('| %s | %.4f | %d | %.6f / %.6f | %.4f / %.4f | %s / %s | %s |' % (size, rate, seed, sa[0], sb[0], sa[1], sb[1], sa[3], sb[3], 'yes' if eq else '**no**'))
    L += ['', '**%d / %d runs identical.**' % (same, len(pairs)), '',
          'Why they must be: with the head at the front of its input VC, the old test (`checkReservation` = RT_OUTVC_BUSY) and the new one (a reservation entry of the',
          'output with that output VC that is not the head\'s own) differ only once the head itself holds an output; from then on the head keeps that output and the',
          'result of the selection is not used. The two tests differ in effect only when the decision is computed for a head that is not in the router yet',
          '(lookahead routing).']
    open(os.path.join(RES, 'busy_state_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if same == len(pairs):
        shutil.rmtree(raw('busy'))
    return same == len(pairs)


def equiv(nproc):
    """B4: Q-learning with alpha = 0 against the heuristic with the same w, beta, gamma and D, under lookahead + fallback + busy_state."""
    P = lp23()
    lfx = LOOK + FALLBACK + BUSY + dd(1)
    js, pairs = [], []
    for size in ('2x2', '4x4'):
        lad = P[lkey(size, 'uniform', E5.FREE[size], 2)]['eval']
        for i, seed, (W, B, G, D) in zip(CHECK_LOADS, range(1, 6), EQ_PARAMS):
            E5.gen_tables(size, 'uniform', [lad[i]])
            h = job('equiv', size, 'heur', variant('CI_heurLA_X', dict(W=W, B=B, G=G, D=D)), 2, 'uniform', E5.FREE[size], lad[i], seed, lfx)
            q = job('equiv', size, 'ql0', variant('CI_qlLA_X', dict(W=W, B=B, G=G, D=D, A=0)), 2, 'uniform', E5.FREE[size], lad[i], seed, lfx)
            js += [h, q]
            pairs.append((size, lad[i], seed, (W, B, G, D), h[0], q[0]))
    res = run_jobs(js, raw('equiv'), nproc=nproc, timeout=7200)
    drop = ['selection_strategy', 'heur_', 'ql_']
    L = ['# B4: Q-learning with alpha = 0 against the heuristic under lookahead (experiments_v24.py equiv)', '',
         'CI with XY on the interposer (relation X), uniform fault-free, pipe_all 2, both with `lookahead_route 1 lookahead_fallback 1 busy_state 1 decision_delay 1`;',
         'five runs per size (loads 0.5, 1.0, 1.4, 2.0 and 2.4 x Lsat of the v23 pipe_all 2 ladder, seeds 1-5), each with its own (w, beta, gamma, D).',
         'Compared: the whole `summary` block and every field of `deft_lb` except the selection\'s name and parameters (`selection_strategy`, `heur_*`, `ql_*`).', '',
         '| size | rate | seed | w, beta, gamma, D | accepted heuristic / alpha 0 | latency heuristic / alpha 0 | fallbacks taken heuristic / alpha 0 | identical |', '|---|---|---|---|---|---|---|---|']
    same = 0
    for size, rate, seed, prm, nh, nq in pairs:
        a, b = res[nh], res[nq]
        eq = a['summary'] == b['summary'] and _strip(a['deft_lb'], drop) == _strip(b['deft_lb'], drop)
        same += eq
        sa, sb = stat(a), stat(b)
        L.append('| %s | %.4f | %d | %s | %.6f / %.6f | %.4f / %.4f | %d / %d | %s |' % (size, rate, seed, ', '.join(fmt(x) for x in prm), sa[0], sb[0], sa[1], sb[1],
                                                                              a['deft_lb']['lookahead_fb_taken'], b['deft_lb']['lookahead_fb_taken'], 'yes' if eq else '**no**'))
    L += ['', '**%d / %d pairs identical.**' % (same, len(pairs))]
    open(os.path.join(RES, 'equivalence.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if same == len(pairs):
        shutil.rmtree(raw('equiv'))
    return same == len(pairs)


# ---- B5: chiptrans ladders (the v23 D1 rule: DeFT-P, seed 101, pipe_all 2, 3 x L0, 9 loads) ----
def sat_name(size, r):
    return 'sat__DeFT_P-p2__%s-chiptrans__%s__%.4f__s101' % (size, E5.FREE[size], r)


def sat_job(size, r):
    return job('sat', size, 'DeFT_P', X23.methods(size)['DeFT_P'], 2, 'chiptrans', E5.FREE[size], r, 101)


def lat_of(size, r):
    return json.load(open(os.path.join(raw('sat'), sat_name(size, r) + '.json')))['summary']['global_average_delay_cycles']


def coarse_lsat(size):
    l0 = lat_of(size, E5.L0_RATE)
    lsat = None
    for r in E5.SAT_RATES:
        if lat_of(size, r) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(size):
    lsat, nxt = coarse_lsat(size)
    if lsat is None or nxt is None or lsat > E5.LOW_LSAT:
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    js = []
    for s in SIZES:
        E5.gen_tables(s, 'chiptrans', E5.SAT_RATES + [E5.L0_RATE])
        js += [sat_job(s, r) for r in E5.SAT_RATES + [E5.L0_RATE]]
    print('coarse jobs:', len(js), flush=True)
    run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    js = []
    for s in SIZES:
        fr = fine_rates(s)
        E5.gen_tables(s, 'chiptrans', fr)
        js += [sat_job(s, r) for r in fr]
    print('fine jobs:', len(js), flush=True)
    res = run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    print('fine runs', len(js), 'missing', sum(1 for v in res.values() if v is None))


def points():
    old = lp23()
    res = dict(old)          # the other scenarios keep their v23 ladders
    L = ['# Load points of v24 (experiments_v24.py sat, points)', '',
         'New in this round: the pattern `chiptrans` (chiplet (cx, cy) sends to chiplet (cy, cx); a chiplet on the diagonal to its own other routers). Its ladders follow the',
         'v23 D1 rule: DeFT-P (-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), seed 101, pipe_all 2; L0 = latency at 0.0002;',
         'Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse (0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid',
         'otherwise; 9 loads at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat. The other scenarios keep their v23 ladders (`results_v23_fidelity/load_points_v23.json`,',
         'copied unchanged into `load_points_v24.json`). All runs of this round use the pipe_all = 2 ladders.', '',
         '| size | scenario | source | grid | L0 | Lsat | lat / L0 at Lsat | ladder (pipe_all 2) |', '|---|---|---|---|---|---|---|---|']
    for s in SIZES:
        m = E5.FREE[s]
        l0 = lat_of(s, E5.L0_RATE)
        fr = fine_rates(s)
        grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
        lsat = None
        for r in rates:
            if lat_of(s, r) > 3 * l0:
                break
            lsat = r
        ev = []
        for mult in MULTS9:
            x = round(max(grid, round(mult * lsat / grid) * grid), 4)
            if ev and x <= ev[-1]:
                x = round(ev[-1] + grid, 4)
            ev.append(x)
        res[lkey(s, 'chiptrans', m)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0, 'pipe_all': 2}
        E5.gen_tables(s, 'chiptrans', ev)
        for p, mm in scenarios(s):
            e = res[lkey(s, p, mm)]
            lr = '%.2f' % (lat_of(s, e['lsat']) / e['l0']) if p == 'chiptrans' else '(v23)'
            L.append('| %s | %s %s | %s | %s | %.1f | %s | %s | %s |' % (s, p, mm, 'v24' if p == 'chiptrans' else 'v23', e['grid'], e['l0'], e['lsat'], lr, e['eval']))
            E5.gen_tables(s, p, e['eval'])
    json.dump(res, open(LP_FILE, 'w'), indent=1)
    open(os.path.join(RES, 'load_points_v24.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('sat'))


# ---- A3: drain tests ----
def drain_cfgs(part, size):
    """(variant label, arguments, pipe_all) of a drain part: v10 = the Part C variants with their v10 parameters and DeFT_P_O1, ideal decision, at pipe_all 2
    and 0; bias = lut_bias 4; lf = lookahead with the fallback and the busy state at its residual delay."""
    out = []
    if part == 'v10':
        for pipe in (2, 0):
            out += [('%s-p%d' % (v, pipe), variant_v10(size, v), pipe) for v in PART_C + ['DeFT_P_O1']]
    elif part == 'bias':
        out += [('%s_bias4-p2' % v, variant_v10(size, v, D=4.0), 2) for v in PART_C]
    elif part == 'lf':
        out += [('%s_LF-p2' % v, variant_v10(size, v) + mech('LF', sel_kind(v)), 2) for v in PART_C]
    else:
        raise ValueError(part)
    return out


def drain_jobs(part):
    """v10 protocol and masks (experiments_v10.drain_jobs) with the v23 LUT of each mask, plus over-saturated 4x4 runs at 2.4 x Lsat on uniform, chipperm, chiptrans."""
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    P = lp()
    js = []
    for size in SIZES:
        for v, a0, pipe in drain_cfgs(part, size):
            a0 = a0 + X23.pipe(pipe) + TRNG
            if size == '2x2':
                for m in masks2:
                    for seed in (1, 2):
                        js.append(('allpairs__%s__2x2-%s__s%d' % (v, m, seed),
                                   common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=X23.lut23('2x2', m)) + a0 + E10.DRAIN_ALLPAIRS_2X2))
                for m in ['0x0000', '0x1111', '0x9C63', '0x7BDE']:
                    for pat in ('uniform', 'chipperm', 'hotspot'):
                        js.append(('%s0.03__%s__2x2-%s__s1' % (pat, v, m),
                                   common_args(1, m, traffic=E5.REL + 'traffic/%s_0.0300.txt' % pat, lut=X23.lut23('2x2', m)) + a0 + E10.DRAIN_OVERSAT_2X2))
                continue
            for m in [E5.FREE[size], E5.NORTH[size]]:
                for seed in (1, 2):
                    js.append(('allpairs__%s__%s-%s__s%d' % (v, size, m, seed),
                               common_args(seed, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(size), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_ALLPAIRS))
                for pat in ('uniform', 'chipperm', 'hotspot'):
                    key = '%s__%s__%s' % (size, pat, m) if '%s__%s__%s' % (size, pat, m) in E10.LP5 else '%s__%s__%s' % (size, pat, E5.FREE[size])
                    r = E10.LP5[key]['eval'][6]
                    js.append(('%s%.4f__%s__%s-%s__s1' % (pat, r, v, size, m),
                               common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), pat, r), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
            if size == '4x4':
                m = E5.FREE[size]
                for pat in ('uniform', 'chipperm', 'chiptrans'):
                    r = P[lkey(size, pat, m)]['eval'][8]          # 2.4 x Lsat of the pipe_all 2 ladder
                    E5.gen_tables(size, pat, [r])
                    js.append(('sat24-%s%.4f__%s__%s-%s__s1' % (pat, r, v, size, m),
                               common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), pat, r), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
    return js


def drain(part, nproc):
    import csv
    js = drain_jobs(part)
    print('drain jobs (%s): %d' % (part, len(js)), flush=True)
    res = run_jobs(js, raw('drain_' + part), nproc=nproc, timeout=14400)
    part_csv = os.path.join(raw('drain_' + part), 'report.csv')
    fails = E19.drain_report(res, part_csv)
    # one summary file for all parts: the rows of this part replace its earlier rows
    summary = os.path.join(RES, 'drain_summary.csv')
    r = list(csv.reader(open(part_csv)))
    head = ['part'] + r[0]
    rows = [x for x in csv.reader(open(summary))][1:] if os.path.exists(summary) else []
    rows = [x for x in rows if x[0] != part] + [[part] + x for x in r[1:]]
    with open(summary, 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator=NL)
        w.writerow(head)
        w.writerows(rows)
    print('drain_summary.csv: %d rows, %d PASS' % (len(rows), sum(1 for r in rows if r[-1] == 'PASS')))
    if not fails:
        shutil.rmtree(raw('drain_' + part))
    return not fails


# ---- B4: probe values that need the new options ----
B4_ROWS = [
    # v23 method, extra, pipe, pattern, rate, probe accepted, probe latency
    ('CI_qlLA_G', lb('ipos_tm', 'XY', 'lut_bias', 4), 0, 'chipperm', 0.0040, 0.0326, 70.8),
    ('CI_qlLA_G', lb('ipos_tm', 'XY', 'hop_weight_ipos', '1.0'), 0, 'chipperm', 0.0070, 0.0532, 378.9),
    ('CI_qlLA_G', IPX + LOOK + FALLBACK + dd(1), 2, 'uniform', 0.0080, 0.0647, 94.4),
    ('CI_qlLA_G', IPX + LOOK + FALLBACK + dd(1), 2, 'uniform', 0.0110, 0.0831, 467.5),
    ('CI_qlLA_G', IPO1, 0, 'uniform', 0.0100, 0.0793, 253.2),
    ('CI_qlLA_G', IPO1, 0, 'chipperm', 0.0070, 0.0479, 735.3),
]
B4_NOTE = ('Note on the two fallback rows: "downstream buffer not full" is read from the input buffer of the neighbour, as the selection reads its occupancy term. '
           'With the buffer-full signal of the router itself (one cycle older) the same two runs give 0.0647 / 95.4 and 0.0831 / 446.9 (+1.1 % and -4.4 % latency); '
           'see `DECISIONS.md`, B2, for the A/B on the tuning seeds.')
B5_ROWS = [
    # v23 method, extra, probe accepted, probe latency (4x4 chiptrans, pipe_all 0, rate 0.0060)
    ('DeFT_P', [], 0.0421, 514), ('MTR', [], 0.0420, 465), ('CI_qlLA_G', [], 0.0485, 66), ('CI_qlLA_G', IPX, 0.0431, 461),
    ('CI_qlLA_G', IPO1, 0.0486, 49), ('DeFT_Dis', IPO1, 0.0485, 52),
]


def probe_rows(stage, rows, nproc, fixed=None):
    """Runs 4x4 seed-91 probe rows with bin/noxim; rows: (method, extra, pipe, pattern, rate, acc, lat) or, with fixed = (pipe, pattern, rate),
    (method, extra, acc, lat)."""
    out = raw(stage)
    size, js, meta = '4x4', [], []
    for k, row in enumerate(rows):
        if fixed:
            meth, extra, pacc, plat = row
            pipe, p, rate = fixed
        else:
            meth, extra, pipe, p, rate, pacc, plat = row
        E5.gen_tables(size, p, [rate])
        n, a = job(stage, size, 'row%d' % k, X23.methods(size)[meth], pipe, p, E5.FREE[size], rate, 91, extra)
        js.append((n, a))
        meta.append((meth, ' '.join(extra), pipe, p, rate, pacc, plat, n))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    recs = []
    for meth, extra, pipe, p, rate, pacc, plat, n in meta:
        acc, lat, rec, _ = stat(res[n])
        recs.append(dict(method=meth, extra=extra.replace('-deft_lb ', ''), pipe_all=pipe, pattern=p, rate=rate, probe_accepted=pacc, probe_latency=plat,
                         accepted=acc, latency=lat, received=rec, within=abs(acc / pacc - 1) <= 0.03 and abs(lat / plat - 1) <= 0.03))
        print(meth, extra, pipe, p, rate, 'probe %.4f / %.1f' % (pacc, plat), 'now %.4f / %.1f' % (acc, lat), 'ok' if recs[-1]['within'] else 'OUTSIDE 3 %')
    shutil.rmtree(out)
    return recs


def _load(name):
    f = os.path.join(RES, name)
    return json.load(open(f)) if os.path.exists(f) else None


def reprodoc():
    """reproduction.md from the JSON files of the reproduction stages (A0, B4, B5); sections of stages not yet run are left out."""
    L = ['# v24 reproduction of the review\'s probe numbers (experiments_v24.py repro, repro2, b5, reprodoc)', '',
         'The probes were single runs on a scratch build of 8d84634: 4x4 unless stated, seed 91, DeFT-P VN options, `-traffic_rng 1`, the v10 selection',
         'parameters, v23 LUTs and traffic tables, `-sim 10000 -warmup 2000`. Where a value differs, both are listed; the measurement of this round is the one used.', '']
    a0 = _load('repro_a0.json')
    if a0:
        L += ['## A0: existing options only (binary %s, md5 %s)' % (a0['binary'], a0['md5']), '',
              'Method = key of `experiments_v23.methods(size)`, plus the extra arguments, plus the pipe depth and `-traffic_rng 1`.', '',
              '| # | size | method + extra arguments | pipe_all | scenario (mask) | rate | received: probe / this round | latency: probe / this round | result |', '|---|---|---|---|---|---|---|---|---|']
        for r in a0['rows']:
            L.append('| %d | %s | %s `%s` | %d | %s (%s) | %.4f | %d / %s | %.10f / %s | %s |' % (
                r['no'], r['size'], r['method'], r['extra'], r['pipe_all'], r['pattern'], r['mask'], r['rate'], r['probe_received'], r['received'],
                r['probe_latency'], '%.10f' % r['latency'] if r['latency'] is not None else 'no output', 'identical' if r['same'] else '**different**'))
        L += ['', '**%d / %d rows identical** (received packets equal and latency equal to the 10 printed decimals).' % (sum(r['same'] for r in a0['rows']), len(a0['rows'])), '']
    b4 = _load('repro_b4.json')
    if b4:
        L += ['## B4: probe values that need the options of this round (binary md5 %s)' % b4['md5'], '',
              'The probe code was throw-away and may differ from this round\'s implementation in tie-breaking; the target is agreement within 3 %.', '',
              '| variant | pipe_all | scenario, rate | accepted / latency: probe | this round | deviation (accepted, latency) | within 3 % |', '|---|---|---|---|---|---|---|']
        for r in b4['rows']:
            L.append('| %s `%s` | %d | %s %.4f | %.4f / %.1f | %.4f / %.1f | %+.1f %%, %+.1f %% | %s |' % (
                r['method'], r['extra'], r['pipe_all'], r['pattern'], r['rate'], r['probe_accepted'], r['probe_latency'], r['accepted'], r['latency'],
                100 * (r['accepted'] / r['probe_accepted'] - 1), 100 * (r['latency'] / r['probe_latency'] - 1), 'yes' if r['within'] else '**no**'))
        L += ['', '**%d / %d rows within 3 %% on both values.**' % (sum(r['within'] for r in b4['rows']), len(b4['rows'])), '']
        if b4.get('note'):
            L += [b4['note'], '']
    b5 = _load('repro_b5.json')
    if b5:
        L += ['## B5: the new pattern `chiptrans` (4x4, seed 91, pipe_all 0, rate 0.0060; binary md5 %s)' % b5['md5'], '',
              '| method | accepted / latency: probe | this round | deviation (accepted, latency) |', '|---|---|---|---|']
        for r in b5['rows']:
            L.append('| %s%s | %.4f / %.0f | %.4f / %.1f | %+.1f %%, %+.1f %% |' % (
                r['method'], (' `%s`' % r['extra']) if r['extra'] else '', r['probe_accepted'], r['probe_latency'], r['accepted'], r['latency'],
                100 * (r['accepted'] / r['probe_accepted'] - 1), 100 * (r['latency'] / r['probe_latency'] - 1)))
        L.append('')
        if b5.get('note'):
            L += [b5['note'], '']
    open(os.path.join(RES, 'reproduction.md'), 'w', newline=NL).write(NL.join(L))
    print(NL.join(L))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'repro':
        repro(nproc)
        reprodoc()
    elif stage == 'reprodoc':
        reprodoc()
    elif stage == 'repro2':
        json.dump(dict(md5=E19.md5(os.path.join(BIN, 'noxim')), rows=probe_rows('b4', B4_ROWS, nproc), note=B4_NOTE), open(os.path.join(RES, 'repro_b4.json'), 'w'), indent=1)
        reprodoc()
    elif stage == 'b5':
        json.dump(dict(md5=E19.md5(os.path.join(BIN, 'noxim')), rows=probe_rows('b5', B5_ROWS, nproc, fixed=(0, 'chiptrans', 0.0060))),
                  open(os.path.join(RES, 'repro_b5.json'), 'w'), indent=1)
        reprodoc()
    elif stage == 'regress':
        sys.exit(0 if regress(extra or REF_BIN, nproc) else 1)
    elif stage == 'busy':
        sys.exit(0 if busy_check(nproc) else 1)
    elif stage == 'equiv':
        sys.exit(0 if equiv(nproc) else 1)
    elif stage == 'formal':
        sys.exit(subprocess.call([sys.executable, os.path.join(HERE, 'formal', 'xy_check.py'), str(nproc), os.path.join(RES, 'formal_xy.md')]))
    elif stage == 'sat':
        sat(nproc)
    elif stage == 'points':
        points()
    elif stage == 'drain':
        sys.exit(0 if drain(extra, nproc) else 1)
    else:
        import experiments_v24_eval as EV   # tuning, centre cut and the Part D stages
        EV.run_stage(stage, nproc, extra)
