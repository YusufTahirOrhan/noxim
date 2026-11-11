"""v25 Part F (results_v25_confirm/hw/): hardware of the final design. Run through experiments_v25.py (stages f_*), on two threads.

  f_build   F2: instrumented copy of the simulator (hw/tb/patch_vecdump.py, vecdump.inc) -> ~/lbbin/noxim_v25_vec
  f_smoke   F2: router-level test of every interposer router configuration (hw/tb/tb_router25.v) -> hw/router_smoke.txt
  f_vec     F2: vectors from simulator runs against the RTL units (Verilator: hw/tb/vl25.v, vl_sel25.cpp, vl_front25.cpp), every
            pipeline cut; each instrumented run is compared with bin/noxim (statistics file byte-identical); a sample of every kept
            vector file is also run through the Icarus test bench (hw/tb/tb25.v) -> hw/functional_check.txt, hw/functional_check.json
  f_mut, f_synth, f_csv   experiments_v25_hw2.py (mutation check, synthesis and timing)
The flow, the library and the constraints are those of rounds 18 and 21 (synth_v18.py). Raw files stay under ~/lbraw/v25/hw.
Designs of this round (interposer routers, hw/rtl/router25_top.v):
  LF_X   CI_heurLA_X_LF   lookahead routing with the fallback, XY, one decision unit per input port
  LF_O   CI_heurLA_O_LF   the same with the order of the VN
  DLY_X  CI_heurLA_X_DLY  the decision at the buffer front, forms P (one unit per input port) and S (one unit per router)
Chiplet routers: the LB-I chiplet router of round 18 (exit LUT, fault table, XY, VN rules), on 2x2 with the table of the
default entry VL (hw/rtl/chip25_top.v).
"""
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v25 as X  # noqa: E402
import synth_v18 as S  # noqa: E402
from runner import BIN, ENV  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(X.RES, 'hw')
RTL = os.path.join(HW, 'rtl')
TB = os.path.join(HW, 'tb')
R18 = S.RTL
RAW = os.path.join(X.RAW, 'hw')
VECBIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_v25_vec')
OSS = os.path.join(S.EDA, 'oss-cad-suite', 'bin')
NL = chr(10)
THREADS = 2
SIZES = X.SIZES
DESIGNS = {'LF_X': dict(row='CI_heurLA_X_LF', mech=0, order_o=0), 'LF_O': dict(row='CI_heurLA_O_LF', mech=0, order_o=1),
           'DLY_X': dict(row='CI_heurLA_X_DLY', mech=1, order_o=0)}
# pipeline cuts of the decision: a register after stage A (relation, static terms), M (occupancies), B (candidate costs)
CUTS = [(a, m, b) for a in (0, 1) for m in (0, 1) for b in (0, 1)]
XW = {'2x2': 3, '3x3': 4, '4x4': 4}


def dbias(size):
    """The default-VL penalty of the frozen configuration: lut_bias 2 on 2x2, 0 on 3x3 and 4x4."""
    a = X.row_args(size, 'CI_heurLA_X_LF')
    return int(float(a[a.index('lut_bias') + 1]))


def sh(cmd, **kw):
    return subprocess.run(cmd, **kw)


def env_eda():
    return dict(os.environ, PATH=OSS + os.pathsep + os.environ['PATH'])


# ---- F2: instrumented simulator ----
def build():
    dst = os.path.join(RAW, 'vecsrc')
    os.makedirs(RAW, exist_ok=True)
    sh([sys.executable, os.path.join(TB, 'patch_vecdump.py'), os.path.abspath(os.path.join(HERE, '..', '..')), dst], check=True)
    with open(os.path.join(RAW, 'vecbuild.log'), 'w') as lf:
        sh(['make', '-C', os.path.join(dst, 'bin'), '-j%d' % THREADS, 'MODULE=noxim_vec'], stdout=lf, stderr=subprocess.STDOUT, check=True)
    shutil.copy(os.path.join(dst, 'bin', 'noxim_vec'), VECBIN)
    print('built', VECBIN)


# ---- F2: router-level test ----
def iverilog(top, params, out, srcs):
    cmd = [os.path.join(OSS, 'iverilog'), '-g2012', '-I' + RTL, '-s', top] + ['-P%s.%s=%s' % (top, k, v) for k, v in params.items()] + ['-o', out] + srcs
    r = sh(cmd, capture_output=True, text=True, env=env_eda())
    msg = NL.join(l for l in (r.stdout + r.stderr).splitlines() if 'sorry' not in l)
    if r.returncode != 0:
        raise SystemExit('iverilog failed: ' + msg)
    return msg


def vvp(vvp_file, plus=()):
    r = sh([os.path.join(OSS, 'vvp'), vvp_file] + list(plus), capture_output=True, text=True, env=env_eda())
    return [l for l in r.stdout.splitlines() if l.startswith('RESULT') or l.startswith('MISMATCH') or 'packet' in l or 'flit' in l]


ROUTER_SRCS = [os.path.join(R18, 'router_core.v'), os.path.join(RTL, 'core25.v'), os.path.join(RTL, 'lb25_units.v'), os.path.join(RTL, 'router25_top.v')]


def _smoke_one(cfg):
    name, mech, oo, db, hub, pp, (ca, cm, cb), xw, nosel = cfg
    out = os.path.join(RAW, 'smoke', '%s_%d.vvp' % (name, os.getpid()))
    iverilog('tb_router25', dict(MECH=mech, ORDER_O=oo, DBIAS=db, HAS_HUB=hub, RS_PER_PORT=pp, CUT_A=ca, CUT_M=cm, CUT_B=cb, XW=xw, NOSEL=nosel, SEED=1), out,
             ROUTER_SRCS + [os.path.join(TB, 'tb_router25.v')])
    res = vvp(out)
    os.remove(out)
    return ['%s %s' % (name, l) for l in res]


def smoke():
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'smoke'), exist_ok=True)
    cfgs = []
    for z in ('2x2', '4x4'):
        for name, d in DESIGNS.items():
            for pp in ((1,) if d['mech'] == 0 else (1, 0)):
                for hub in (0, 1):
                    cfgs += [('%s_%s' % (name, z), d['mech'], d['order_o'], dbias(z), hub, pp, c, XW[z], 0) for c in CUTS]
        for mech, pp in ((0, 1), (1, 1), (1, 0)):          # the relation without a selection
            for hub in (0, 1):
                cfgs.append(('REL_%s' % z, mech, 0, 0, hub, pp, (0, 0, 0), XW[z], 1))
    with Pool(THREADS) as pool:
        res = pool.map(_smoke_one, cfgs, chunksize=1)
    L = [l for r in res for l in r]
    ok = sum(1 for l in L if l.endswith(' OK'))
    fail = [l for l in L if 'RESULT' in l and not l.endswith(' OK')]
    L += ['', 'configurations %d, OK %d, FAIL %d' % (len(cfgs), ok, len(fail))]
    open(os.path.join(HW, 'router_smoke.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-3:] + fail[:10]))
    return not fail and ok == len(cfgs)


# ---- F2: vectors from simulator runs ----
VEC_SEED = 1               # not an evaluation seed: these runs give vectors, no result
VEC_MAX = 600000           # lines per vector file and run (keeps the files small; the count is reported)
ICARUS_SAMPLE = 2000       # lines of every kept vector file that also go through the Icarus test bench


def vec_runs():
    """(design, size, pattern, mask, rate): per design 12 runs at pipe_all 2 (uniform at 1.0 and 1.4 x Lsat, chipperm at 1.0 x Lsat,
    uniform with one faulty VL per chiplet at 1.0 x Lsat, on the three sizes)."""
    P = X.lp()
    out = []
    for name, d in DESIGNS.items():
        for z in SIZES:
            f, n = E5.FREE[z], E5.NORTH[z]
            for p, m, i in (('uniform', f, 3), ('uniform', f, 5), ('chipperm', f, 3), ('uniform', n, 3)):
                out.append((name, z, p, m, P[X.lkey(z, p, m)]['eval'][i]))
    return out


def _vec_path(key):
    """The Verilator checker of a parameter set (hw/tb/vl25.v with vl_sel25.cpp or vl_front25.cpp)."""
    kind, oo, db, ca, cm, cb = key
    return os.path.join(RAW, 'vec', 'vl_%s_o%d_d%d_c%d%d%d' % (kind, oo, db, ca, cm, cb), 'Vvl_%s25' % kind)


def _vec_compile(key):
    kind, oo, db, ca, cm, cb = key
    exe = _vec_path(key)
    if os.path.exists(exe):
        return exe
    g = ['-GORDER_O=%d' % oo] + (['-GDBIAS=%d' % db, '-GCUT_A=%d' % ca, '-GCUT_M=%d' % cm, '-GCUT_B=%d' % cb] if kind == 'sel' else [])
    cmd = [os.path.join(OSS, 'verilator'), '--cc', '--exe', '--build', '-O2', '-j', '1', '-Wno-fatal', '--top-module', 'vl_%s25' % kind, '-I' + RTL,
           '--Mdir', os.path.dirname(exe)] + g + [os.path.join(RTL, 'lb25_units.v'), os.path.join(TB, 'vl25.v'), os.path.join(TB, 'vl_%s25.cpp' % kind)]
    r = sh(cmd, capture_output=True, text=True, env=env_eda())
    if r.returncode != 0 or not os.path.exists(exe):
        raise SystemExit('verilator failed: ' + (r.stdout + r.stderr)[-3000:])
    return exe


def _vec_check(key, vecfile):
    kind, oo, db, ca, cm, cb = key
    args = [str(oo), str(db), str(ca), str(cm), str(cb)] if kind == 'sel' else [str(oo)]
    r = sh([_vec_path(key), vecfile] + args, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.startswith('RESULT') or l.startswith('MISMATCH')]


def _vec_one(run):
    name, z, p, m, rate = run
    d = DESIGNS[name]
    wd = os.path.join(RAW, 'vec')
    rname, args = X.job('vec', z, d['row'], X.row_args(z, d['row']), 2, p, m, rate, VEC_SEED)
    E5.gen_tables(z, p, [rate])
    pre = os.path.join(wd, rname)
    res = dict(design=name, size=z, pattern=p, mask=m, rate=rate, run=rname)
    done = pre + '.done.json'
    if os.path.exists(done):
        return json.load(open(done))
    # the same run with bin/noxim and with the instrumented copy: the statistics must be the same file
    for tag, binary, env in (('ref', os.path.join(BIN, 'noxim'), ENV), ('vec', VECBIN, dict(ENV, LB25_VEC=pre, LB25_VEC_MAX=str(VEC_MAX)))):
        sh([binary] + args + ['-stats_file', pre + '.%s.json' % tag], cwd=BIN, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    res['identical'] = os.path.exists(pre + '.ref.json') and os.path.exists(pre + '.vec.json') and open(pre + '.ref.json', 'rb').read() == open(pre + '.vec.json', 'rb').read()
    lines = []
    db = dbias(z)
    for ca, cm, cb in CUTS:
        lines += _vec_check(('sel', d['order_o'], db, ca, cm, cb), pre + '.sel.txt')
    lines += _vec_check(('front', d['order_o'], 0, 0, 0, 0), pre + '.fb.txt')
    res['lines'] = lines
    keep = os.path.join(wd, 'keep_%s_%s' % (name, z))        # one run per design and size is kept for the mutation check
    if p == 'uniform' and not X.faulty(m) and rate == X.lp()[X.lkey(z, p, m)]['eval'][3]:
        shutil.move(pre + '.sel.txt', keep + '.sel.txt')
        shutil.move(pre + '.fb.txt', keep + '.fb.txt')
    for ext in ('.sel.txt', '.fb.txt', '.ref.json', '.vec.json'):
        if os.path.exists(pre + ext):
            os.remove(pre + ext)
    json.dump(res, open(done, 'w'))
    return res


def _num(line, key):
    m = re.search(key + r'=(\d+)', line)
    return int(m.group(1)) if m else 0


def _icarus_one(arg):
    """A sample of a kept vector file through the Icarus test bench (cuts 000 and 111, and the front bench)."""
    name, z = arg
    d = DESIGNS[name]
    wd = os.path.join(RAW, 'vec')
    keep = os.path.join(wd, 'keep_%s_%s' % (name, z))
    out = []
    for kind in ('sel', 'fb'):
        with open(keep + '.%s.txt' % kind) as f, open(keep + '.%s.sample.txt' % kind, 'w') as g:
            for k, line in enumerate(f):
                if k >= ICARUS_SAMPLE:
                    break
                g.write(line)
    srcs = [os.path.join(RTL, 'lb25_units.v'), os.path.join(TB, 'tb25.v')]
    exe = os.path.join(wd, 'ic_%s_%s.vvp' % (name, z))
    for ca, cm, cb in ((0, 0, 0), (1, 1, 1)):
        iverilog('tb_sel25', dict(ORDER_O=d['order_o'], DBIAS=dbias(z), CUT_A=ca, CUT_M=cm, CUT_B=cb), exe, srcs)
        out += ['%s %s icarus %s' % (name, z, l) for l in vvp(exe, ['+vec=' + keep + '.sel.sample.txt'])]
    iverilog('tb_front25', dict(ORDER_O=d['order_o']), exe, srcs)
    out += ['%s %s icarus %s' % (name, z, l) for l in vvp(exe, ['+vec=' + keep + '.fb.sample.txt'])]
    for f in (exe, keep + '.sel.sample.txt', keep + '.fb.sample.txt'):
        os.remove(f)
    return out


def vec():
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'vec'), exist_ok=True)
    runs = vec_runs()
    for name, d in DESIGNS.items():          # the checkers are built once, before the pool
        for db in sorted({dbias(z) for z in SIZES}):
            for ca, cm, cb in CUTS:
                _vec_compile(('sel', d['order_o'], db, ca, cm, cb))
        _vec_compile(('front', d['order_o'], 0, 0, 0, 0))
    with Pool(THREADS) as pool:
        res = pool.map(_vec_one, runs, chunksize=1)
        ica = pool.map(_icarus_one, [(name, z) for name in DESIGNS for z in SIZES], chunksize=1)
    L = ['# v25 F2: RTL units against vectors from simulator runs (experiments_v25.py f_vec)', '',
         'Instrumented copy of the simulator: %s (hw/tb/patch_vecdump.py). Runs: pipe_all 2, seed %d, at most %d lines per vector file.' % (os.path.basename(VECBIN), VEC_SEED, VEC_MAX),
         'A selection vector is one evaluation of the decision (computed ahead for the next router, or at the buffer front) or one stored decision of a hop with one',
         'offered output; it is applied to the unit with each of the %d pipeline cut configurations, so it counts %d times in the totals of applied vectors. A front vector' % (len(CUTS), len(CUTS)),
         'is one evaluation of Router::selectionFunction (relation, the only output, the fallback). Checkers: Verilator (hw/tb/vl25.v, vl_sel25.cpp, vl_front25.cpp).', '']
    summ = {}
    allok = True
    for r in res:
        L.append('## %s %s %s %s rate %.4f: statistics of the instrumented run %s' % (r['design'], r['size'], r['pattern'], r['mask'], r['rate'],
                                                                                 'byte-identical to bin/noxim' if r['identical'] else '**DIFFERENT from bin/noxim**'))
        L += r['lines'] + ['']
        s = summ.setdefault(r['design'], dict(sel=0, sel_applied=0, front=0, mism=0, runs=0, identical=0, multi=0, fb=0, fb_other=0, multi_last=[0] * 5))
        s['runs'] += 1
        s['identical'] += bool(r['identical'])
        first = True
        nres = 0
        for l in r['lines']:
            if l.startswith('RESULT sel'):
                nres += 1
                s['sel_applied'] += _num(l, 'vectors')
                s['mism'] += _num(l, 'mismatches')
                if first:
                    s['sel'] += _num(l, 'vectors')
                    s['multi'] += _num(l, 'multi')
                    ml = re.search(r'multi_by_last=([\d,]+)', l).group(1).split(',')
                    s['multi_last'] = [a + int(b) for a, b in zip(s['multi_last'], ml)]
                    first = False
            elif l.startswith('RESULT front'):
                nres += 1
                s['front'] += _num(l, 'vectors')
                s['mism'] += _num(l, 'mismatches')
                s['fb'] += _num(l, 'fallback_checked')
                s['fb_other'] += _num(l, 'fallback_took_other')
            elif l.startswith('MISMATCH'):
                allok = False
        allok = allok and r['identical'] and nres == len(CUTS) + 1
    L += ['## Icarus cross-check of the Verilator checkers', '',
          'The first %d lines of every kept vector file (uniform fault-free at 1.0 x Lsat, one per design and size) through hw/tb/tb25.v (cuts 000 and 111, and the front bench).' % ICARUS_SAMPLE, '']
    for r in ica:
        L += r
        for l in r:
            if 'RESULT' in l and _num(l, 'mismatches') != 0:
                allok = False
            if 'MISMATCH' in l:
                allok = False
    L += ['', '## Summary', '', '| design | runs (statistics identical to bin/noxim) | selection vectors | of those with a choice (by last move N, E, S, W, none) | front vectors | fallback evaluated (took another output) | vectors in all | applied with the %d cuts | mismatches |' % len(CUTS), '|---|---|---|---|---|---|---|---|---|']
    for name, s in summ.items():
        allok = allok and s['mism'] == 0
        L.append('| %s | %d (%d) | %d | %d (%s) | %d | %d (%d) | %d | %d | %d |' % (name, s['runs'], s['identical'], s['sel'], s['multi'], ', '.join(str(a) for a in s['multi_last']), s['front'], s['fb'], s['fb_other'],
                                                                           s['sel'] + s['front'], s['sel_applied'] + s['front'], s['mism']))
    L += ['', '**All vectors match and every instrumented run equals bin/noxim: %s.**' % ('yes' if allok else 'NO')]
    open(os.path.join(HW, 'functional_check.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    json.dump(dict(summary=summ, ok=allok), open(os.path.join(HW, 'functional_check.json'), 'w'), indent=1)
    print(NL.join(L[-(len(summ) + 5):]))
    return allok


def run_stage(stage, nproc, extra):
    os.makedirs(HW, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'f_build':
        build()
    elif stage == 'f_smoke':
        sys.exit(0 if smoke() else 1)
    elif stage == 'f_vec':
        sys.exit(0 if vec() else 1)
    else:
        import experiments_v25_hw2 as H2        # mutation check, synthesis and timing
        H2.run_stage(stage, nproc, extra)
