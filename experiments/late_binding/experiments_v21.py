"""v21: a selection that decides within one cycle, DEFT_FAST (results_v21_fastsel/).

Stages (python3 experiments_v21.py STAGE [nproc] [extra]; --shard i/n accepted):
  regress   options off: bin/noxim against the 3ac1bae and K5 builds (extra = "BIN1,BIN2") on the 84-configuration set, whole stats files -> regression.md
  drain     F3: drain tests of the 4 variants with -deft_vn_rr 1 (v10 protocol and masks) -> drain_summary.csv
  alpha0    F3: fastQL with alpha 0 against the fast heuristic, whole stats summary
  synth     F2: yosys and OpenSTA of the v18 flow on the fast designs, hierarchy kept and flattened (extra = hier | flat | one)
  synthcsv  F2: timing_runs_cutC.csv, area_runs_cutC.csv (environment V21_CUT = C; 1 by default)
  nfast     F2: N_fast and the staleness per variant, from the timing -> n_fast.json, timing.md
  tune      F4: heuristic grid (w x beta), then the learners' alpha (extra = heur | ext | ql), seeds 101/102
  choose    F4: choice per size and scope (extra = heur | ql) -> tuning_choice.json, tuning.md
  k5check   F4: 20 K5 baseline runs on the current binary against results_v19_vnrr/eval_runs.csv
  timing    F4: timing test and estimate
  eval      F4: confirmatory runs, seeds 81-90, and N_fast + 1 on seeds 81-85
  check     integrity of the eval outputs; prints no results
  csv       eval_runs.csv; raw outputs deleted when complete
Raw outputs stay under ~/lbraw/v21. N_fast: results_v21_fastsel/n_fast.json.
"""
import csv
import glob
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v21_fastsel')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v21')
SIZES = ['2x2', '3x3', '4x4']
SCOPES = {'CI': V.CI, 'FULL': V.FULL}
FAST = ['CI_fast', 'CI_fastQL', 'FULL_fast', 'FULL_fastQL']
QF = {'2x2': 10, '3x3': 8, '4x4': 8}     # fractional bits of the 16-bit residual, as v18
W_GRID, B_GRID = [0.5, 1.0, 2.0], [0.0, 4.0, 8.0]
ALPHAS = [0.005, 0.01, 0.02, 0.05, 0.1]
TUNE_SEEDS = (101, 102)
SEEDS = range(81, 91)
SENS_SEEDS = range(81, 86)
BASE_ORDER = ['DeFT', 'MTR', 'RC']        # run first, with the four variants; if time is short DeFT-Dis and DeFT-Ran follow
BASE_LATER = ['DeFT_Dis', 'DeFT_Ran']
NL = chr(10)


def raw(stage):
    return os.path.join(RAW, stage)


def n_fast():
    return json.load(open(os.path.join(RES, 'n_fast.json')))


def delay_args(v, extra=0):
    """The round-robin, and the decision delay and the age of the registered terms that the timing of variant v implies."""
    p = n_fast()[v]
    return E19.RR + ['-deft_lb', 'decision_delay', str(p['n'] + extra), '-deft_lb', 'fast_stale', str(p['stale'])]


def fast_args(scope, size, w, b, alpha=None):
    a = list(SCOPES[scope]) + ['-sel', 'DEFT_FAST', '-deft_lb', 'hop_weight_ipos', '2.0'] + V.kv(heur_w=w, heur_busy=b)
    if alpha is not None:
        a += V.kv(fast_ql=1, ql_alpha=alpha, ql_key=1, ql_eps=0.0, ql_bits=16, ql_frac=QF[size])
    return a


def choice():
    return json.load(open(os.path.join(RES, 'tuning_choice.json')))


def variant_args(size, v, extra_delay=0):
    """Tuned arguments of a fast variant at its N_fast (+ extra_delay)."""
    c = choice()[size]
    scope, kind = v.split('_')
    p = c[scope]
    a = fast_args(scope, size, p['w'], p['beta'], p['alpha'] if kind == 'fastQL' else None)
    return a + delay_args(v, extra_delay)


# ---- regression ----
def regress(refs, nproc):
    import check_stats_regression as CSR
    from multiprocessing import Pool
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in SIZES:
        mm = E10.methods(size)
        r = E10.LP5[f'{size}__uniform__{E5.FREE[size]}']['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append((f'{v}__{size}', a))
    new = os.path.join(BIN, 'noxim')
    tags = [('ref0', refs[0], []), ('ref1', refs[1], []), ('new', new, []), ('explicit', new, ['-deft_lb', 'fast_ql', '0'])]
    jobs = [((t, b, ex, n, a), out) for t, b, ex in tags for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = {t: 0 for t, _, _ in tags[1:]}, []
    for n, _ in cf:
        base = os.path.join(out, f'ref0__{n}.json')
        for t, _, _ in tags[1:]:
            f = os.path.join(out, f'{t}__{n}.json')
            if os.path.exists(base) and os.path.exists(f) and open(base, 'rb').read() == open(f, 'rb').read():
                ok[t] += 1
            else:
                diffs.append(f'- {t} differs: {n}')
    L = ['# Regression with the v21 options off (experiments_v21.py regress)', '',
         f'References: 3ac1bae build md5 {E19.md5(refs[0])}; K5 build md5 {E19.md5(refs[1])}. New binary: md5 {E19.md5(new)}.',
         f'Configurations: {len(cf)} = the 84-configuration set of v14-v20. Comparison: the whole stats JSON file, byte by byte, against the 3ac1bae build.', '',
         f'* K5 build: **{ok["ref1"]} / {len(cf)} byte-identical**.',
         f'* New binary, options absent: **{ok["new"]} / {len(cf)} byte-identical**.',
         f'* New binary, `-deft_lb fast_ql 0` given: **{ok["explicit"]} / {len(cf)} byte-identical**.', ''] + (diffs or ['No differences.'])
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return not diffs


# ---- F3 ----
def drain_jobs(tuned):
    """v10 protocol and masks. tuned = False: (w, beta, alpha) = (1, 4, 0.05) at N = 0; tuned = True: the tuned variants at N_fast."""
    js = []
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    for size in SIZES:
        if tuned:
            cfg = {v: variant_args(size, v) for v in FAST}
        else:
            cfg = {'CI_fast': fast_args('CI', size, 1.0, 4.0), 'CI_fastQL': fast_args('CI', size, 1.0, 4.0, 0.05),
                   'FULL_fast': fast_args('FULL', size, 1.0, 4.0), 'FULL_fastQL': fast_args('FULL', size, 1.0, 4.0, 0.05)}
            cfg = {v: a + E19.RR for v, a in cfg.items()}
        for v, a0 in cfg.items():
            if size == '2x2':
                for m in masks2:
                    for seed in (1, 2):
                        js.append((f'allpairs__{v}__2x2-{m}__s{seed}', common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=E10.lut(size, 'DeFT', 'uniform')) + a0 + E10.DRAIN_ALLPAIRS_2X2))
                for m in ['0x0000', '0x1111', '0x9C63', '0x7BDE']:
                    for pat in ('uniform', 'chipperm', 'hotspot'):
                        js.append((f'{pat}0.03__{v}__2x2-{m}__s1', common_args(1, m, traffic=E5.REL + f'traffic/{pat}_0.0300.txt', lut=E10.lut(size, 'DeFT', 'uniform')) + a0 + E10.DRAIN_OVERSAT_2X2))
                continue
            for m in [E5.FREE[size], E5.NORTH[size]]:
                for seed in (1, 2):
                    js.append((f'allpairs__{v}__{size}-{m}__s{seed}', common_args(seed, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt', lut=E10.lut(size, 'DeFT', 'uniform')) +
                               E5.size_args(size) + a0 + E10.DRAIN_ALLPAIRS))
                for pat in ('uniform', 'chipperm', 'hotspot'):
                    key = f'{size}__{pat}__{m}' if f'{size}__{pat}__{m}' in E10.LP5 else f'{size}__{pat}__{E5.FREE[size]}'
                    r = E10.LP5[key]['eval'][6]
                    js.append((f'{pat}{r:.4f}__{v}__{size}-{m}__s1', common_args(1, m, traffic=E5.REL + f'{E5.tdir(size)}/{pat}_{r:.4f}.txt', lut=E10.lut(size, 'DeFT', pat)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
    return js


def alpha0(nproc):
    js = []
    P = E19.lp()
    for z in SIZES:
        for sc in SCOPES:
            r = P[E5.key(z, 'uniform', E5.FREE[z])]['eval'][3]
            base = E5.job('heur', z, sc, fast_args(sc, z, 1.0, 4.0) + E19.RR, 'uniform', E5.FREE[z], r, 7, E10.lut(z, 'DeFT', 'uniform'))
            a0 = E5.job('ql0', z, sc, fast_args(sc, z, 1.0, 4.0, 0.0) + E19.RR, 'uniform', E5.FREE[z], r, 7, E10.lut(z, 'DeFT', 'uniform'))
            js += [base, a0]
    res = run_jobs(js, raw('alpha0'), nproc=nproc, timeout=14400)
    L = ['# fastQL with alpha = 0 against the fast heuristic', '', 'Every size and scope, uniform at 1.0 x Lsat, seed 7, -deft_vn_rr 1. Compared: the whole `summary` block of the stats file. The residuals stay 0, so the two must be the same run.', '']
    same = 0
    n = 0
    for name, d in res.items():
        if not name.startswith('heur__'):
            continue
        n += 1
        o = res[name.replace('heur__', 'ql0__', 1)]
        s = d['summary'] == o['summary']
        same += s
        L.append(f'- {"IDENTICAL" if s else "DIFFERENT"} {name}')
    L = L[:4] + [f'**{same} / {n} identical.**', ''] + L[4:]
    open(os.path.join(RES, 'alpha0_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('alpha0'))
    return same == n


# ---- F2: synthesis ----
FM = {10: 'LBI_fast', 11: 'LBI_fastQL', 12: 'LBF_fast', 13: 'LBF_fastQL'}
SYNTH_CUT = int(os.environ.get('V21_CUT', '1'))


def fix_position(t, z):
    """The router whose ROM is synthesised: a central chiplet; a VL slot where the type has a Hub, otherwise an inner router."""
    gx = {'2x2': 2, '3x3': 3, '4x4': 4}[z]
    base = (gx // 2) * 4
    return (base + 1, base + 0) if t.endswith('6') else (base + 1, base + 1)


def synth_designs():
    import synth_v18 as S
    out = []
    for z in S.SIZES:
        for t in S.TYPES:
            for m in FM:
                out.append((m, t, z, 0))
                if m >= 12 or S.TYPES[t][0] == 1:
                    out.append((m, t, z, 1))
    return out


def synth_script(d, flat, odir, name):
    import synth_v18 as S
    m, t, z, pp = d
    layer, hub = S.TYPES[t]
    scope = 'I' if m in (10, 11) else 'F'
    ws, b = tuned_rtl_w(scope, z)
    fx, fy = fix_position(t, z)
    p = dict(METHOD=m, LAYER=layer, HAS_HUB=hub, RS_PER_PORT=pp, PIPE=0, FIX_X=fx, FIX_Y=fy, W_SHIFT=ws, BETA=b, CUT=SYNTH_CUT, **S.SIZES[z])
    if m in (11, 13):
        p.update(S1=4, S2=5)
    ch = ' '.join(f'-set {k} {v}' for k, v in p.items())
    R21 = os.path.join(RES, 'rtl')
    srcs = ' '.join([os.path.join(S.RTL, f) for f in ('router_core.v', 'lb_units.v', 'method_units.v')] + [os.path.join(R21, 'fast_units.v'), os.path.join(R21, 'router_top.v')])
    L = [f'read_verilog -sv -I{S.RTL} {srcs}', f'chparam {ch} router_top', 'hierarchy -top router_top', 'flatten t:*pipe_reg*', 'synth -top router_top' + (' -flatten' if flat else ''),
         f'dfflibmap -liberty {S.LIB}', f'abc -liberty {S.LIB} -D {S.CLOCK_PS} -constr {os.path.join(S.RAW, "abc.constr")}',
         'opt_clean -purge', 'setundef -zero', 'hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 ZN', 'insbuf -buf BUF_X1 A Z',
         f'tee -q -o {os.path.join(odir, name + ".stat.txt")} stat -liberty {S.LIB} -top router_top',
         f'tee -q -o {os.path.join(odir, name + ".stat.json")} stat -json -liberty {S.LIB} -top router_top',
         f'write_verilog -noattr -noexpr -nohex -nodec {os.path.join(odir, name + ".net.v")}']
    return NL.join(L) + NL


def tuned_rtl_w(scope, z):
    """w = 2^shift, beta from the tuning when it exists, otherwise the frozen placeholder (1, 4)."""
    f = os.path.join(RES, 'tuning_choice.json')
    if os.path.exists(f):
        p = json.load(open(f))[z]['CI' if scope == 'I' else 'FULL']
        return int(round(math.log2(max(p['w'], 1.0)))), int(p['beta'])
    return 0, 4


def synth_one(arg):
    import synth_v18 as S
    d, flat = arg
    m, t, z, pp = d
    n = f'{FM[m]}__{t}__{z}__{"P" if pp else "S"}'
    odir = os.path.join(RAW, f'cut{SYNTH_CUT}', 'flat' if flat else 'hier')
    os.makedirs(odir, exist_ok=True)
    if os.path.exists(os.path.join(odir, n + ('.sta.txt' if flat else '.stat.json'))):
        return n, True
    ys = os.path.join(odir, n + '.ys')
    open(ys, 'w').write(synth_script(d, flat, odir, n))
    r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return n, False
    if flat:
        tcl = S.STA_TCL.format(lib=S.LIB, net=os.path.join(odir, n + '.net.v'), period=S.CLOCK_PS / 1000.0)
        extra = NL.join(['rep DECIDE_F {*regs.pre_f*}', 'rep PRE_P {*pre_p*}', 'rep STAGE_A {*ra_t* *ra_offered* *ra_pruned* *ra_g*}', 'rep STAGE_Q {*ra_q*}', 'rep DEC_CUT {*cost_all*}',
                         'puts "L_OUT"', 'report_checks -to [get_ports l_out*] -path_delay max -digits 4', 'puts "END_L"'])
        tcl = tcl.replace('report_checks -to [get_ports fb_out_g*]', extra + NL + 'report_checks -to [get_ports fb_out_g*]')
        tf = os.path.join(odir, n + '.tcl')
        open(tf, 'w').write(tcl)
        with open(os.path.join(odir, n + '.sta.txt'), 'w') as o:
            subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tf], stdout=o, stderr=subprocess.STDOUT, timeout=3600)
    return n, True


def group(txt, g):
    m = re.search(r'GROUP ' + g + r' (\d+)(.*?)(GROUP|L_OUT|\Z)', txt, re.S)
    if not m or int(m.group(1)) == 0:
        return None, None
    d = re.search(r'(-?[0-9.]+)\s+data arrival time', m.group(2))
    s = re.search(r'(-?[0-9.]+)\s+slack', m.group(2))
    return (float(d.group(1)), float(s.group(1))) if d and s else (None, None)


def synth_csv():
    import synth_v18 as S
    areas = S.lib_areas()
    tim, ar = [], []
    for d in synth_designs():
        m, t, z, pp = d
        n = f'{FM[m]}__{t}__{z}__{"P" if pp else "S"}'
        f = os.path.join(RAW, f'cut{SYNTH_CUT}', 'flat', n + '.sta.txt')
        if os.path.exists(f):
            txt = open(f).read()
            row = dict(method=FM[m], rtype=t, size=z, form='P' if pp else 'S', cut=SYNTH_CUT)
            for g, k in (('ROUTE_REG', 'route'), ('ROUTE_HDR', 'hdr'), ('OVC_REG', 'ovc'), ('STAGE_A', 'stage_a'), ('STAGE_Q', 'stage_q'), ('DEC_CUT', 'dec_cut'), ('QTABLE', 'qtable'), ('DECIDE_F', 'pre_f'), ('PRE_P', 'pre_p')):
                a, s = group(txt, g)
                row[f'arrival_{k}'], row[f'slack_{k}'] = a, s
            lo = re.search(r'L_OUT(.*?)END_L', txt, re.S)
            d2 = re.search(r'(-?[0-9.]+)\s+data arrival time', lo.group(1)) if lo else None
            row['arrival_l_out'] = float(d2.group(1)) if d2 else None
            tot = S.parse_hier(os.path.join(RAW, f'cut{SYNTH_CUT}', 'flat', n + '.stat.json'), areas)
            row['area_flat_um2'] = round(sum(x['area'] for x in tot.values()), 1)
            tim.append(row)
        f = os.path.join(RAW, f'cut{SYNTH_CUT}', 'hier', n + '.stat.json')
        if os.path.exists(f):
            tot = S.parse_hier(f, areas)
            ar.append(dict(method=FM[m], rtype=t, size=z, form='P' if pp else 'S', cut=SYNTH_CUT, area_um2=round(sum(x['area'] for x in tot.values()), 1)))
    for fn, rows in ((f'timing_runs_cut{SYNTH_CUT}.csv', tim), (f'area_runs_cut{SYNTH_CUT}.csv', ar)):
        if rows:
            with open(os.path.join(RES, fn), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
                w.writeheader()
                w.writerows(rows)
    print(f'timing {len(tim)}, area {len(ar)} rows')


def nfast_table():
    """N = (cycles of stage A - 1) + (cycles of the decision - 1), per variant, the worst over sizes and router types of the form with one unit per port (the
    form the simulator models). Cycles of a stage: ceil(arrival + setup) at 1 GHz, v18's convention. The decision: 1 cycle if the path without a cut fits, 2 if
    both stages with the cut fit, otherwise 3. Staleness: the cycles from the cost registers to the choice."""
    cut0 = {(r['method'], r['rtype'], r['size'], r['form']): r for r in csv.DictReader(open(os.path.join(RES, 'timing_runs_cut0.csv')))}
    cut1 = {(r['method'], r['rtype'], r['size'], r['form']): r for r in csv.DictReader(open(os.path.join(RES, 'timing_runs_cut1.csv')))}

    def num(r, k):
        return float(r[k]) if r.get(k) not in (None, '', 'None') else None

    def worst(r, *keys):
        return min(x for x in (num(r, k) for k in keys) if x is not None)
    table = {}
    L = ['# v21 F2: the decision path per router (flattened, NanGate45 typical, pre-layout)', '', 'Arrival + setup = 1 ns - slack, in ns. Stage A: relation + path totals + Q read, from the buffer or the link into the stage registers. '
         'Without a cut: registered inputs to the route registers. With the cut: first stage (into the cost registers), second stage (into the route registers).', '',
         '| size | variant | router | form | stage A | no cut | cut: first | cut: second | value on the link | N_stage_A | N_decision |', '|---|---|---|---|---|---|---|---|---|---|---|']
    res = {}
    for key in sorted(cut1):
        m, t, z, f = key
        a, b = cut0[key], cut1[key]
        if b['arrival_stage_a'] in ('', 'None'):
            continue
        sa = 1 - worst(b, 'slack_stage_a', 'slack_stage_q')
        d0 = 1 - worst(a, 'slack_route', 'slack_ovc', 'slack_hdr')
        d1, d2 = 1 - worst(b, 'slack_dec_cut'), 1 - worst(b, 'slack_route', 'slack_ovc', 'slack_hdr')
        nd = 0 if d0 <= 1.0 else 1 if max(d1, d2) <= 1.0 else 2
        na = math.ceil(sa) - 1
        scope, kind = m.split('_')
        v = ('CI_' if scope == 'LBI' else 'FULL_') + kind
        lo = num(b, 'arrival_l_out')
        L.append(f'| {z} | {v} | {t} | {f} | {sa:.2f} | {d0:.2f} | {d1:.2f} | {d2:.2f} | {lo:.2f} | {na} | {nd} |')
        if f == 'P':
            res.setdefault(v, []).append((na + nd, nd, key, sa, d0, d1, d2))
    for v, rows in res.items():
        w = max(rows, key=lambda x: x[0])
        table[v] = dict(n=w[0], stale=max(x[1] for x in rows), worst_router=list(w[2]))
    json.dump(table, open(os.path.join(RES, 'n_fast.json'), 'w'), indent=1)
    open(os.path.join(RES, 'timing.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-40:]))
    print(json.dumps(table, indent=1))


# ---- F4: tuning (v6 protocol at the K5 load points) ----
def tune_rates(z, p, m):
    lp = E19.lp()[E5.key(z, p, m)]
    g, lsat = lp['grid'], lp['lsat']
    t1 = round(max(g, round(0.8 * lsat / g) * g), 4)
    t2 = round(max(g, round(1.1 * lsat / g) * g), 4)
    if t2 <= lsat:
        t2 = round(lsat + g, 4)
    return [t1, t2]


def tune_jobs(grid):
    js = []
    for z, name, var, args in grid:
        for p, m in E5.tune_cells(z):
            rates = tune_rates(z, p, m)
            E5.gen_tables(z, p, rates)
            for r, s in itertools.product(rates, TUNE_SEEDS):
                n = f'tune__{name}__{z}-{p}__{m}__{r:.4f}__s{s}'
                js.append((n, common_args(s, m, traffic=E5.REL + f'{E5.tdir(z)}/{p}_{r:.4f}.txt', lut=E10.lut(z, 'DeFT', 'uniform')) + E5.size_args(z) + args + delay_args(var) + E5.SIM))
    return js


def heur_grid(ws=W_GRID, bs=B_GRID):
    return [(z, f'{sc}-heur-w{w}-b{b}', f'{sc}_fast', fast_args(sc, z, w, b)) for z in SIZES for sc in SCOPES for w in ws for b in bs]


def tune_results():
    out = {}
    for f in glob.glob(os.path.join(raw('tune'), '*.json')):
        _, name, sp, m, rate, seed = os.path.basename(f)[:-5].split('__')
        z, p = sp.split('-')
        d = json.load(open(f))['summary']
        out[(name, z, p, m, float(rate), int(seed[1:]))] = (d['global_average_delay_cycles'], d['average_ip_throughput_flits_per_cycle_per_ip'])
    return out


def score(res, z, name):
    lat, acc = [], []
    for p, m in E5.tune_cells(z):
        rates = tune_rates(z, p, m)
        for r, s in itertools.product(rates, TUNE_SEEDS):
            lt, ac = res[(name, z, p, m, r, s)]
            lat.append(lt)
            if r == rates[-1]:
                acc.append(ac)
    return math.exp(sum(map(math.log, lat)) / len(lat)), math.exp(sum(map(math.log, acc)) / len(acc)), len(lat)


def parse_wb(name):
    parts = name.split('-')
    return float(parts[2][1:]), float(parts[3][1:])


def ext_grid(res):
    """v6: one step beyond an edge optimum (w x2 above 2, x0.5 below 0.5; beta +4 above 8; beta 0 is a hard bound)."""
    ext = []
    for z, sc in itertools.product(SIZES, SCOPES):
        names = sorted({n for (n, y, *_r) in res if y == z and n.startswith(f'{sc}-heur-')})
        best = min(names, key=lambda n: score(res, z, n)[0])
        w, b = parse_wb(best)
        ws = [w] + ([2 * w] if w == max(parse_wb(n)[0] for n in names) else []) + ([w / 2] if w == min(parse_wb(n)[0] for n in names) else [])
        bs = [b] + ([b + 4] if b == max(parse_wb(n)[1] for n in names) else [])
        for w2, b2 in itertools.product(ws, bs):
            name = f'{sc}-heur-w{w2}-b{b2}'
            if name not in names:
                ext.append((z, name, f'{sc}_fast', fast_args(sc, z, w2, b2)))
    return ext


def ql_grid():
    ch = choice()
    return [(z, f'{sc}-ql-a{a}', f'{sc}_fastQL', fast_args(sc, z, ch[z][sc]['w'], ch[z][sc]['beta'], a)) for z in SIZES for sc in SCOPES for a in ALPHAS]


def choose(part):
    res = tune_results()
    path = os.path.join(RES, 'tuning_choice.json')
    ch = json.load(open(path)) if os.path.exists(path) else {}
    for z, sc in itertools.product(SIZES, SCOPES):
        ch.setdefault(z, {}).setdefault(sc, {})
        if part == 'heur':
            names = sorted({n for (n, y, *_r) in res if y == z and n.startswith(f'{sc}-heur-')})
            best = min(names, key=lambda n: score(res, z, n)[0])
            ch[z][sc]['w'], ch[z][sc]['beta'] = parse_wb(best)
            ch[z][sc]['heur_score'] = score(res, z, best)[0]
        else:
            names = sorted({n for (n, y, *_r) in res if y == z and n.startswith(f'{sc}-ql-')})
            best = min(names, key=lambda n: score(res, z, n)[0])
            ch[z][sc]['alpha'] = float(best.split('-')[2][1:])
            ch[z][sc]['ql_score'] = score(res, z, best)[0]
            # the variant of the scope for the primary hypotheses, chosen on the tuning seeds by the same criterion
            ch[z][sc]['best'] = f'{sc}_fastQL' if ch[z][sc]['ql_score'] < ch[z][sc]['heur_score'] else f'{sc}_fast'
    json.dump(ch, open(path, 'w'), indent=1)
    if part == 'ql':
        L = ['# v21 tuning of the fast variants per size (seeds 101, 102)', '',
             'v6 protocol at the K5 load points (`load_points_rr.json`): uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; ~0.8 and ~1.1 x Lsat; 2 seeds = 16 runs per configuration; '
             'criterion = geometric mean of the mean latency. All runs with -deft_vn_rr 1 and the decision delay N_fast of the variant. The learners inherit (w, beta) of the heuristic of their scope and size, are keyed by the destination chiplet and use 16-bit residuals.', '']
        for z, sc in itertools.product(SIZES, SCOPES):
            for kind in ('heur', 'ql'):
                names = sorted({n for (n, y, *_r) in res if y == z and n.startswith(f'{sc}-{kind}-')})
                rows = sorted((score(res, z, n), n) for n in names)
                L += [f'## {z} {sc} {kind}', '', '| configuration | runs | geo-mean latency | vs best | accepted @1.1 |', '|---|---|---|---|---|']
                for (g, a, k), n in rows:
                    L.append(f'| {n}{" **(chosen)**" if n == rows[0][1] else ""} | {k} | {g:.2f} | {100 * (g / rows[0][0][0] - 1):+.2f} % | {a:.4f} |')
                L.append('')
            L += [f'Variant for the primary hypotheses, {z} {sc}: **{ch[z][sc]["best"]}**.', '']
        open(os.path.join(RES, 'tuning.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(json.dumps(ch, indent=1))


# ---- F4: confirmatory ----
def k5check(nproc):
    K5 = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(os.path.join(E19.RES, 'eval_runs.csv')))}
    P = E19.lp()
    js = []
    for k, (z, v, p, m, i, s) in enumerate(itertools.product(SIZES, ['DeFT', 'MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran'], ['uniform'], [None], [1, 3], [61, 62])):
        m = E5.FREE[z]
        r = P[E5.key(z, p, m)]['eval'][i]
        if k % 3 != 2:
            js.append(E5.job('eval', z, v, E19.args_of(z, v), p, m, r, s, E10.lut(z, v, p)))
    js = js[:20]
    res = run_jobs(js, raw('k5check'), nproc=nproc, timeout=14400)
    same = 0
    L = ['# K5 baseline runs on the current binary', '', f'{len(js)} runs of `results_v19_vnrr/eval_runs.csv`, every value in the CSV row compared exactly (the raw K5 files were deleted after that round).', '']
    bad = []
    for n, d in res.items():
        (v, p, m, rate, seed), _ = MK.parse(os.path.join(raw('k5check'), n + '.json'))
        row = K5[(v, p, m, repr(rate), str(seed))]
        s, l = d['summary'], d['deft_lb']
        ok = (repr(s['global_average_delay_cycles']) == row['latency'] and repr(s['average_ip_throughput_flits_per_cycle_per_ip']) == row['accepted'] and repr(l['delay_p99']) == row['p99'] and
              str(s['total_injected_packets']) == row['injected'] and str(s['total_received_packets']) == row['received'])
        same += ok
        if not ok:
            bad.append(f'- differs: {n}')
    L += [f'**{same} / {len(js)} reproduce exactly.**'] + bad
    open(os.path.join(RES, 'k5_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('k5check'))
    return same == len(js)


def eval_jobs(seeds=SEEDS):
    """In the order of the prompt: DeFT, MTR, RC and the four variants; then DeFT-Dis and DeFT-Ran; then N_fast + 1 on seeds 81-85."""
    P = E19.lp()
    first, later, sens = [], [], []

    def cells(z, v):
        for p, m in E19.scen(z, v):
            for r in P[E5.key(z, p, m)]['eval']:
                yield p, m, r
    for z in SIZES:
        for v in BASE_ORDER:
            first += [E5.job('eval', z, v, E19.args_of(z, v), p, m, r, s, E10.lut(z, v, p)) for p, m, r in cells(z, v) for s in seeds]
        for v in FAST:
            first += [E5.job('eval', z, v, variant_args(z, v), p, m, r, s, E10.lut(z, 'DeFT', 'uniform')) for p, m, r in cells(z, v) for s in seeds]
        for v in BASE_LATER:
            later += [E5.job('eval', z, v, E19.args_of(z, v), p, m, r, s, E10.lut(z, v, p)) for p, m, r in cells(z, v) for s in seeds]
        for v in FAST:
            sens += [E5.job('eval', z, f'{v}-plus1', variant_args(z, v, 1), p, m, r, s, E10.lut(z, 'DeFT', 'uniform')) for p, m, r in cells(z, v) for s in SENS_SEEDS]
    return first + later + sens


def timing(nproc):
    js = [j for j in eval_jobs((1001,)) if '__s1001' in j[0]]
    js = [j for j in js if any(f'__{r:.4f}__' in j[0] for r in [])] or js[::9][:480]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v21 F4', '', f'Timing test: {len(js)} runs (seed 1001), {nproc} processes: {el:.0f} s wall; {sum(1 for x in res.values() if x is None)} missing.', '', f'F4: {n} runs, estimated **{est:.1f} h**.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('timing'))


def to_csv():
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('eval'), '*.json'))):
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up = l['vl_down_packets'], l['vl_up_packets']
        has = any(down)
        rows.append(dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed, accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']),
                         latency=repr(s['global_average_delay_cycles']), p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'], vl_imbalance=repr(MK.imbalance(m, down, up)) if has else '', vl_source='run' if has else 'none'))
    out = os.path.join(RES, 'eval_runs.csv')
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(f'{out}: {len(rows)} rows; dead ends {sum(int(r["dead_ends"]) for r in rows)}')
    return len(rows)


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else ''
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(extra.split(','), nproc) else 1)
    elif stage == 'drain':
        tuned = extra == 'tuned'
        d = raw(f'drain_{extra or "n0"}')
        res = run_jobs(drain_jobs(tuned), d, nproc=nproc, timeout=14400)
        fails = E19.drain_report(res, os.path.join(RES, 'drain_summary_tuned.csv' if tuned else 'drain_summary.csv'))
        if not fails:
            shutil.rmtree(d)
        sys.exit(1 if fails else 0)
    elif stage == 'alpha0':
        sys.exit(0 if alpha0(nproc) else 1)
    elif stage == 'synth':
        import synth_v18 as S
        from multiprocessing import Pool
        S.constr_file()
        ds = synth_designs()
        if extra == 'one':
            todo = [(next(d for d in ds if d[0] == m and d[1] in ('ipos6', 'chip6') and d[2] == '4x4' and d[3] == 1), True) for m in FM]
        else:
            todo = [(d, f) for d in ds for f in ([True] if extra == 'flat' else [False] if extra == 'hier' else [True, False])]
        with Pool(nproc) as pool:
            res = pool.map(synth_one, todo, chunksize=1)
        print('failed:', [n for n, ok in res if not ok], flush=True)
    elif stage == 'synthcsv':
        synth_csv()
    elif stage == 'nfast':
        nfast_table()
    elif stage == 'tune':
        if extra == 'heur':
            js = tune_jobs(heur_grid())
        elif extra == 'ext':
            js = tune_jobs(ext_grid(tune_results()))
        else:
            js = tune_jobs(ql_grid())
        print(f'tuning jobs {extra}: {len(js)}', flush=True)
        r = run_jobs(js, raw('tune'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in r.values() if v is None), flush=True)
    elif stage == 'choose':
        choose(extra)
    elif stage == 'k5check':
        sys.exit(0 if k5check(nproc) else 1)
    elif stage == 'timing':
        timing(nproc)
    elif stage == 'eval':
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        r = run_jobs(js, raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in r.values() if v is None), flush=True)
    elif stage == 'check':
        sys.exit(0 if E19.check_raw(raw('eval'), eval_jobs(), 'eval') else 1)
    elif stage == 'csv':
        n = to_csv()
        if n == len(eval_jobs()):
            shutil.rmtree(raw('eval'))
    else:
        raise SystemExit(__doc__)
