"""v29 Part E2 and E4, hardware (results_v29_review/hw/). Run through experiments_v29.py:
  e2_build   an instrumented copy of the simulator of this round (the patch of round 25, results_v25_confirm/hw/tb/patch_vecdump.py)
             -> ~/lbbin/noxim_v29_vec
  e2_vec     vectors from simulator runs of the matching rows against the RTL units of each variant (Verilator checkers of round 25),
             every pipeline cut; each instrumented run is compared with bin/noxim (statistics file byte-identical); controls: the
             vectors of each variant against the units of the main row must give mismatches -> hw/functional_check_variants.txt, .json
  e2_smoke   router-level test of every router configuration of the two variants (tb_router25.v of round 25) -> hw/router_smoke_variants.txt
  e2_lat     cycles of a head through an idle router (tb_lat25.v of round 25) -> hw/latency_check_variants.txt
  e2_synth   Yosys + ABC and OpenSTA as round 25: the main row and the two variants, interposer routers of 2x2 and 4x4, the eight cut
             configurations, three forms; DeFT's and the chiplet routers are those of e3_synth (extra = a regular expression on the tag)
  e2_csv     hw/area_variants.csv, hw/timing_variants.csv
  e4_loads   the instrumented copy counts the flits per input port of every router on 4x4 under uniform traffic at 0.5 and 1.0 x Lsat
             (the rows DeFT_P, main, LB_noVLrep, LB_noLA; statistics byte-identical to bin/noxim) -> hw/port_loads.csv
  e4_power   OpenSTA report_power on the flattened netlists of the 4x4 routers: with the default activity of the tool, and with the
             activity of a simulation of the netlist that carries the load of port_loads.csv (hw/tb/tb_act18.v, tb_act25.v; the bench is
             calibrated on the RTL, the netlist must give the same RESULT line) -> hw/power_runs.csv
Variants of the interposer router (rtl/lb29_units.v with macros; router top, core, test benches and checkers are those of round 25):
  main      LB_UP_REP 1, LB_LOOKAHEAD 1: the units of round 25                 simulator row CI_heurLA_X_LF
  noVLrep   LB_UP_REP 0: no reports across the VLs                             simulator row LB_noVLrep (-deft_lb up_report 0)
  noLA      LB_LOOKAHEAD 0: no report of any neighbour is read or registered   simulator row LB_noLA (heur_lookahead 0)
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v25_hw as H25  # noqa: E402
import experiments_v25_hw2 as H2  # noqa: E402
import experiments_v29 as X  # noqa: E402
import experiments_v29_hw as H  # noqa: E402
import experiments_v29_rows as R  # noqa: E402
import synth_v18 as S  # noqa: E402
from runner import BIN, ENV  # noqa: E402

HW, RTL, RAW, OSS, NL = H.HW, H.RTL, H.RAW, H.OSS, H.NL
R25, R18 = H.R25, H.R18
TB25 = H25.TB
VECBIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_v29_vec')
UNITS = os.path.join(RTL, 'lb29_units.v')
CUTS = H25.CUTS
SIZES = X.SIZES
VARIANTS = {'main': dict(defs={}, row=lambda z: X25.row_args(z, X.MAIN)),
            'noVLrep': dict(defs={'LB_UP_REP': 0}, row=lambda z: X25.row_args(z, X.MAIN) + X.lb('up_report', 0)),
            'noLA': dict(defs={'LB_LOOKAHEAD': 0}, row=lambda z: R.row_args(z, 'LB_noLA'))}
ROUTER_SRCS = [H.CORE18, os.path.join(R25, 'core25.v'), UNITS, os.path.join(R25, 'router25_top.v')]


def dflags(defs):
    return ['-D%s=%s' % kv for kv in defs.items()]


def env_eda():
    return H.env_eda()


# ---- E2: instrumented simulator ----
def build(nthreads):
    dst = os.path.join(RAW, 'vecsrc')
    os.makedirs(RAW, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(TB25, 'patch_vecdump.py'), os.path.abspath(os.path.join(H.HERE, '..', '..')), dst], check=True)
    subprocess.run([sys.executable, os.path.join(H.TB, 'patch_ports.py'), dst], check=True)        # E4: the port counters
    with open(os.path.join(RAW, 'vecbuild.log'), 'w') as lf:
        subprocess.run(['make', '-C', os.path.join(dst, 'bin'), '-j%d' % nthreads, 'MODULE=noxim_vec'], stdout=lf, stderr=subprocess.STDOUT, check=True)
    shutil.copy(os.path.join(dst, 'bin', 'noxim_vec'), VECBIN)
    print('built', VECBIN, subprocess.run(['md5sum', VECBIN], capture_output=True, text=True).stdout.split()[0])
    return True


# ---- E2: vectors ----
VEC_SEED, VEC_MAX = H25.VEC_SEED, H25.VEC_MAX


def vec_runs():
    """(variant, size, pattern, mask, rate): per variant the 12 runs of round 25 (uniform at 1.0 and 1.4 x Lsat, chipperm at 1.0 x Lsat,
    uniform with one faulty VL per chiplet at 1.0 x Lsat, on the three sizes)."""
    P = X25.lp()
    out = []
    for name in VARIANTS:
        for z in SIZES:
            f, n = E5.FREE[z], E5.NORTH[z]
            for p, m, i in (('uniform', f, 3), ('uniform', f, 5), ('chipperm', f, 3), ('uniform', n, 3)):
                out.append((name, z, p, m, P[X.lkey(z, p, m)]['eval'][i]))
    return out


def checker_path(variant, kind, db, cuts):
    return os.path.join(RAW, 'vec', 'vl_%s_%s_d%d_c%d%d%d' % (variant, kind, db, cuts[0], cuts[1], cuts[2]), 'Vvl_%s25' % kind)


def checker_build(arg):
    variant, kind, db, cuts = arg
    exe = checker_path(variant, kind, db, cuts)
    if os.path.exists(exe):
        return exe
    g = ['-GORDER_O=0'] + (['-GDBIAS=%d' % db, '-GCUT_A=%d' % cuts[0], '-GCUT_M=%d' % cuts[1], '-GCUT_B=%d' % cuts[2]] if kind == 'sel' else [])
    cmd = [os.path.join(OSS, 'verilator'), '--cc', '--exe', '--build', '-O2', '-j', '1', '-Wno-fatal', '--top-module', 'vl_%s25' % kind, '-I' + R25,
           '--Mdir', os.path.dirname(exe)] + g + dflags(VARIANTS[variant]['defs']) + [UNITS, os.path.join(TB25, 'vl25.v'), os.path.join(TB25, 'vl_%s25.cpp' % kind)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env_eda())
    if r.returncode != 0 or not os.path.exists(exe):
        raise SystemExit('verilator failed: ' + (r.stdout + r.stderr)[-3000:])
    return exe


def check(variant, kind, db, cuts, vecfile):
    args = ['0', str(db), str(cuts[0]), str(cuts[1]), str(cuts[2])] if kind == 'sel' else ['0']
    r = subprocess.run([checker_path(variant, kind, db, cuts), vecfile] + args, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.startswith('RESULT') or l.startswith('MISMATCH')]


def vec_one(run):
    name, z, p, m, rate = run
    wd = os.path.join(RAW, 'vec')
    rname, args = X.job('vec', z, 'LF_X_' + name, VARIANTS[name]['row'](z), 2, p, m, rate, VEC_SEED)
    E5.gen_tables(z, p, [rate])
    pre = os.path.join(wd, rname)
    res = dict(design=name, size=z, pattern=p, mask=m, rate=rate, run=rname)
    done = pre + '.done.json'
    if os.path.exists(done):
        return json.load(open(done))
    for tag, binary, env in (('ref', os.path.join(BIN, 'noxim'), ENV), ('vec', VECBIN, dict(ENV, LB25_VEC=pre, LB25_VEC_MAX=str(VEC_MAX)))):
        subprocess.run([binary] + args + ['-stats_file', pre + '.%s.json' % tag], cwd=BIN, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    res['identical'] = os.path.exists(pre + '.ref.json') and os.path.exists(pre + '.vec.json') and open(pre + '.ref.json', 'rb').read() == open(pre + '.vec.json', 'rb').read()
    db = H25.dbias(z)
    lines = []
    for cuts in CUTS:
        lines += check(name, 'sel', db, cuts, pre + '.sel.txt')
    lines += check(name, 'front', 0, (0, 0, 0), pre + '.fb.txt')
    res['lines'] = lines
    # control: the vectors of a variant against the units of the main row (no cut); a variant that differs from the main row must mismatch
    res['control'] = check('main', 'sel', db, (0, 0, 0), pre + '.sel.txt') if name != 'main' else []
    keep = os.path.join(wd, 'keep_%s_%s' % (name, z))        # the uniform run at 1.0 x Lsat is kept (activity of E4, mutation-style controls)
    if p == 'uniform' and not X25.faulty(m) and rate == X25.lp()[X.lkey(z, p, m)]['eval'][3]:
        shutil.move(pre + '.sel.txt', keep + '.sel.txt')
        shutil.move(pre + '.fb.txt', keep + '.fb.txt')
    for ext in ('.sel.txt', '.fb.txt', '.ref.json', '.vec.json'):
        if os.path.exists(pre + ext):
            os.remove(pre + ext)
    json.dump(res, open(done, 'w'))
    return res


def vec(nthreads):
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'vec'), exist_ok=True)
    builds = [(v, 'sel', db, c) for v in VARIANTS for db in sorted({H25.dbias(z) for z in SIZES}) for c in CUTS] + [(v, 'front', 0, (0, 0, 0)) for v in VARIANTS]
    with Pool(nthreads) as pool:
        pool.map(checker_build, builds, chunksize=1)
        res = pool.map(vec_one, vec_runs(), chunksize=1)
    num = H25._num
    L = ['# v29 E2: the RTL units of the variants against vectors from simulator runs (experiments_v29.py e2_vec)', '',
         'Instrumented copy of the simulator of this round: %s (the patch of round 25, results_v25_confirm/hw/tb/patch_vecdump.py). Runs: pipe_all 2, seed %d, at most %d lines' % (
             os.path.basename(VECBIN), VEC_SEED, VEC_MAX),
         'per vector file. Per variant the 12 runs of round 25 (uniform traffic at 1.0 and 1.4 x Lsat, chipperm at 1.0 x Lsat, uniform with one faulty VL per chiplet at 1.0 x Lsat;',
         'three sizes) of the simulator row that the variant builds: main = CI_heurLA_X_LF, noVLrep = the same with -deft_lb up_report 0, noLA = the same with heur_lookahead 0.',
         'Units: rtl/lb29_units.v with the macros of the variant. Checkers and checks as round 25 (hw/tb/vl25.v, vl_sel25.cpp, vl_front25.cpp): offered outputs, pruned masks,',
         'the cost of every offered output, the choice with the pointer sweep, and the output requested through the fallback; every selection vector with each of the %d cut' % len(CUTS),
         'configurations. Control: the selection vectors of a variant applied to the units of the main row (no cut) must give mismatches, or the check could not tell the',
         'designs apart.', '']
    summ, allok = {}, True
    for r in res:
        L.append('## %s %s %s %s rate %.4f: statistics of the instrumented run %s' % (r['design'], r['size'], r['pattern'], r['mask'], r['rate'],
                                                                                 'byte-identical to bin/noxim' if r['identical'] else '**DIFFERENT from bin/noxim**'))
        L += r['lines'] + (['control (units of the main row): ' + l for l in r['control'] if l.startswith('RESULT')]) + ['']
        s = summ.setdefault(r['design'], dict(sel=0, sel_applied=0, front=0, mism=0, runs=0, identical=0, multi=0, fb=0, fb_other=0, control_vectors=0, control_mism=0))
        s['runs'] += 1
        s['identical'] += bool(r['identical'])
        first, nres = True, 0
        for l in r['lines']:
            if l.startswith('RESULT sel'):
                nres += 1
                s['sel_applied'] += num(l, 'vectors')
                s['mism'] += num(l, 'mismatches')
                if first:
                    s['sel'] += num(l, 'vectors')
                    s['multi'] += num(l, 'multi')
                    first = False
            elif l.startswith('RESULT front'):
                nres += 1
                s['front'] += num(l, 'vectors')
                s['mism'] += num(l, 'mismatches')
                s['fb'] += num(l, 'fallback_checked')
                s['fb_other'] += num(l, 'fallback_took_other')
            elif l.startswith('MISMATCH'):
                allok = False
        for l in r['control']:
            if l.startswith('RESULT sel'):
                s['control_vectors'] += num(l, 'vectors')
                s['control_mism'] += num(l, 'mismatches')
        allok = allok and r['identical'] and nres == len(CUTS) + 1
    L += ['## Summary', '', '| variant | runs (statistics identical to bin/noxim) | selection vectors | of those with a choice | front vectors | fallback evaluated (took another output) | vectors in all | applied with the %d cuts | mismatches | control: vectors, mismatches against the units of the main row |' % len(CUTS),
          '|---|---|---|---|---|---|---|---|---|---|']
    for name, s in summ.items():
        allok = allok and s['mism'] == 0 and (name == 'main' or s['control_mism'] > 0)
        L.append('| %s | %d (%d) | %d | %d | %d | %d (%d) | %d | %d | %d | %s |' % (name, s['runs'], s['identical'], s['sel'], s['multi'], s['front'], s['fb'], s['fb_other'], s['sel'] + s['front'],
                                                                           s['sel_applied'] + s['front'], s['mism'], '-' if name == 'main' else '%d, %d' % (s['control_vectors'], s['control_mism'])))
    L += ['', '**All vectors match, every instrumented run equals bin/noxim, and both controls give mismatches: %s.**' % ('yes' if allok else 'NO')]
    open(os.path.join(HW, 'functional_check_variants.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    json.dump(dict(summary=summ, ok=allok), open(os.path.join(HW, 'functional_check_variants.json'), 'w'), indent=1)
    print(NL.join(L[-(len(summ) + 5):]))
    return allok


# ---- E2: router-level test and cycles ----
def iverilog(top, params, out, srcs, defs):
    cmd = [os.path.join(OSS, 'iverilog'), '-g2012', '-I' + R25, '-s', top] + dflags(defs) + ['-P%s.%s=%s' % (top, k, v) for k, v in params.items()] + ['-o', out] + srcs
    r = subprocess.run(cmd, capture_output=True, text=True, env=env_eda())
    if r.returncode != 0:
        raise SystemExit('iverilog failed: ' + (r.stdout + r.stderr)[-2000:])


def router_cfgs():
    """(name, variant, DBIAS, HAS_HUB, cuts, XW): the two variants (and the main row, as the reference of the test) on 2x2 and 4x4."""
    return [('%s_%s' % (v, z), v, H25.dbias(z), hub, c, H25.XW[z]) for v in VARIANTS for z in ('2x2', '4x4') for hub in (0, 1) for c in CUTS]


def _tb_one(arg):
    tbname, cfg = arg
    name, v, db, hub, (ca, cm, cb), xw = cfg
    out = os.path.join(RAW, tbname, '%s_%d.vvp' % (name, os.getpid()))
    p = dict(MECH=0, ORDER_O=0, DBIAS=db, HAS_HUB=hub, RS_PER_PORT=1, CUT_A=ca, CUT_M=cm, CUT_B=cb, XW=xw, NOSEL=0, SEED=1)
    if tbname == 'lat':
        p['NPKT'] = 2000
    iverilog('tb_router25' if tbname == 'smoke' else 'tb_lat25', p, out, ROUTER_SRCS + [os.path.join(TB25, 'tb_router25.v' if tbname == 'smoke' else 'tb_lat25.v')], VARIANTS[v]['defs'])
    r = subprocess.run([os.path.join(OSS, 'vvp'), out], capture_output=True, text=True, env=env_eda())
    os.remove(out)
    return ['%s %s' % (name, l) for l in r.stdout.splitlines() if l.startswith('RESULT') or 'did not leave' in l or 'packet' in l.split('RESULT')[0] and 'RESULT' not in l]


def smoke(nthreads):
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'smoke'), exist_ok=True)
    cfgs = router_cfgs()
    with Pool(nthreads) as pool:
        res = pool.map(_tb_one, [('smoke', c) for c in cfgs], chunksize=1)
    L = ['# v29 E2: router-level test of the variants (experiments_v29.py e2_smoke; tb_router25.v of round 25, Icarus Verilog)', '',
         'Each interposer router configuration (main, noVLrep, noLA; 2x2 and 4x4; without and with the Up link; the eight cut configurations) under random packets,',
         'random reports and randomly delayed credits: every flit that enters leaves, packets stay contiguous per output VC, every head leaves through an output the',
         'relation offers, on its VC, with the mask the relation gives.', ''] + [l for r in res for l in r]
    ok = sum(1 for r in res for l in r if l.rstrip().endswith(' OK'))
    fail = [l for r in res for l in r if 'RESULT' in l and not l.rstrip().endswith(' OK')]
    L += ['', 'configurations %d, OK %d, FAIL %d' % (len(cfgs), ok, len(fail))]
    open(os.path.join(HW, 'router_smoke_variants.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-1:] + fail[:10]))
    return not fail and ok == len(cfgs)


def latency(nthreads):
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'lat'), exist_ok=True)
    cfgs = router_cfgs()
    with Pool(nthreads) as pool:
        res = pool.map(_tb_one, [('lat', c) for c in cfgs], chunksize=1)
    L = ['# v29 E2: cycles of a head through an idle interposer router of each variant (experiments_v29.py e2_lat; tb_lat25.v of round 25, Icarus Verilog)', '',
         'Two-flit packets, one at a time, into an idle router with free outputs: cycles from the cycle the head is on the input link to the cycle it is on the output link.',
         'Expected as for the main row (round 25): 4 cycles for a head with one offered output, 4 + max(0, cuts - 1) for a head with a choice.', '',
         '| variant and size | Up link | cuts (A M B) | heads with one output: n, cycles | heads with a choice: n, cycles | expected | result |', '|---|---|---|---|---|---|---|']
    ok = True
    for (name, v, db, hub, cuts, xw), lines in zip(cfgs, res):
        m = re.search(r'one_output=(\d+) min=(\d+) max=(\d+) choice=(\d+) min=(\d+) max=(\d+) errors=(\d+)', ' '.join(lines))
        exp = 4 + max(0, sum(cuts) - 1)
        good = bool(m) and int(m.group(7)) == 0 and len(lines) == 1 and int(m.group(1)) > 0 and m.group(2) == m.group(3) == '4' and int(m.group(4)) > 0 and \
            int(m.group(5)) == int(m.group(6)) == exp
        ok = ok and good
        g = m.groups() if m else ('?',) * 7
        L.append('| %s | %s | %d %d %d | %s, %s-%s | %s, %s-%s | %d | %s |' % (name, 'yes' if hub else 'no', cuts[0], cuts[1], cuts[2], g[0], g[1], g[2], g[3], g[4], g[5], exp, 'OK' if good else '**FAIL**'))
    L += ['', 'configurations %d, all as expected: **%s**' % (len(cfgs), 'yes' if ok else 'NO')]
    open(os.path.join(HW, 'latency_check_variants.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-1:]))
    return ok


# ---- E2: synthesis and timing ----
def designs_e2():
    out = []
    for v in VARIANTS:
        for z in ('2x2', '4x4'):
            for t in ('ipos5', 'ipos6'):
                for ca, cm, cb in CUTS:
                    out.append(dict(tag='LF_%s__%s__%s__c%d%d%d' % (v, t, z, ca, cm, cb), design='LF_' + v, rtype=t, size=z, cuts='%d%d%d' % (ca, cm, cb), top='router25_top',
                                    srcs=ROUTER_SRCS, defs=dict(VARIANTS[v]['defs']),
                                    params=dict(MECH=0, ORDER_O=0, DBIAS=H25.dbias(z), HAS_HUB=S.TYPES[t][1], RS_PER_PORT=1, CUT_A=ca, CUT_M=cm, CUT_B=cb, XW=H25.XW[z], NOSEL=0)))
    return out


def sta_designs():
    """The designs whose flattened netlist is timed: the routers of E2, and of E3 DeFT's routers at depth 4 (T_ref of a type and size) and the
    chiplet routers of the main row (their allocation stages are DeFT's logic: the spread of the flow on unchanged logic, as round 25)."""
    e3 = [dict(d, cuts='000') for d in H.designs_e3() if d['design'] in ('DeFT_d4', 'LBI18', 'CHIP25')]
    return designs_e2() + e3


def run_flat_sta(d):
    """The flattened synthesis of E3's driver (the netlist is kept, gzip) and the timing report of round 25 (the same endpoint groups)."""
    n = d['tag']
    odir = os.path.join(RAW, 'flat')
    out = os.path.join(odir, n + '.sta.txt')
    if os.path.exists(out):
        return n, True
    if not H.run_one((d, 'flat'))[2]:
        return n, False
    wd = os.path.join(RAW, 'sta')
    os.makedirs(wd, exist_ok=True)
    net = os.path.join(wd, n + '.net.v')
    subprocess.run('gunzip -c %s > %s' % (os.path.join(odir, n + '.net.v.gz'), net), shell=True, check=True)
    reps = NL.join('rep %s {%s}' % g for g in H2.GROUPS)
    tcl = os.path.join(wd, n + '.tcl')
    open(tcl, 'w').write(H2.STA_TCL.format(lib=S.LIB, net=net, top=d['top'], period=S.CLOCK_PS / 1000.0, reps=reps))
    with open(os.path.join(wd, n + '.sta.tmp'), 'w') as o:
        subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tcl], stdout=o, stderr=subprocess.STDOUT, timeout=3600)
    os.replace(os.path.join(wd, n + '.sta.tmp'), out)
    os.remove(net)
    return n, True


def run_any(arg):
    d, form = arg
    if form == 'flat':
        return run_flat_sta(d)
    n, f, ok = H.run_one((d, form))
    return n, ok


def synth(pattern, nthreads):
    from multiprocessing import Pool
    S.constr_file()
    flat = [d for d in sta_designs() if not pattern or re.search(pattern, d['tag'])]
    other = [d for d in designs_e2() if not pattern or re.search(pattern, d['tag'])]
    jobs = [(d, 'flat') for d in flat] + [(d, f) for f in ('hier', 'semi') for d in other]
    print('runs %d (flattened with timing %d, hierarchy kept and core kept %d), threads %d' % (len(jobs), len(flat), 2 * len(other), nthreads), flush=True)
    with Pool(nthreads) as pool:
        res = pool.map(run_any, jobs, chunksize=1)
    bad = sorted({n for n, ok in res if not ok})
    print('synthesis: %d / %d runs done; failed: %s' % (len(res) - sum(1 for _, ok in res if not ok), len(res), bad))
    return not bad


def report_bits(tag):
    """How many of the 150 report inputs (five neighbours x five of their outputs x two VCs x three bits) the flattened netlist reads."""
    import gzip
    gz = os.path.join(RAW, 'flat', tag + '.net.v.gz')
    if not os.path.exists(gz):
        return ''
    bits = set()
    with gzip.open(gz, 'rt') as f:
        for line in f:
            if 'nb_report[' in line:
                bits.update(int(x) for x in re.findall(r'nb_report\[(\d+)\]', line))
    return len(bits)


def make_csv():
    areas = S.lib_areas()
    ar, tm = [], []
    for d in designs_e2():
        row = dict(design=d['design'], rtype=d['rtype'], size=d['size'], form='P', cuts=d['cuts'], report_bits=report_bits(d['tag']))
        ok = True
        for f in H.FORMS:
            if not os.path.exists(os.path.join(RAW, f, d['tag'] + '.stat.json')):
                ok = False
                continue
            a, ffs, tot = H.area_of(d, f, areas)
            row['area_%s_um2' % f] = round(a, 3)
            row['ffs' if f == 'hier' else 'ffs_%s' % f] = ffs
            if f == 'hier':
                for c in ('selection', 'routing', 'fallback', 'top', 'buffers'):
                    row['hier_%s_um2' % c] = round(tot.get(c, {}).get('area', 0.0), 3)
        if ok:
            ar.append(row)
    for d in sta_designs():
        fs = os.path.join(RAW, 'flat', d['tag'] + '.sta.txt')
        if not os.path.exists(fs):
            continue
        txt = open(fs).read()
        m = re.search(r'WNS_ALL (-?[0-9.e+-]+)', txt)
        if not m:
            continue
        row = dict(design=d['design'], rtype=d['rtype'], size=d['size'], form='P' if d['design'].startswith('LF_') else 'S', cuts=d['cuts'], slack_all_ns=float(m.group(1)))
        for g in H2.ALLGROUPS:
            a, s = H2.group(txt, g)
            m = re.search(r'GROUP ' + g + r' (\d+)', txt)
            row['n_' + g] = int(m.group(1)) if m else 0
            row['stage_' + g] = '' if s is None else round(S.CLOCK_PS / 1000.0 - s, 4)
        tm.append(row)
    for fn, rows in (('area_variants.csv', ar), ('timing_variants.csv', tm)):
        if rows:
            keys = []
            for r in rows:
                keys += [k for k in r if k not in keys]
            with open(os.path.join(HW, fn), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=keys, lineterminator=NL)
                w.writeheader()
                w.writerows(rows)
    print('area %d rows of %d designs, timing %d rows of %d designs' % (len(ar), len(designs_e2()), len(tm), len(sta_designs())))
    return len(ar) == len(designs_e2()) and len(tm) == len(sta_designs())


# ---- E4: power ----
E4_SIZE = '4x4'
E4_LOADS = {'05': 1, '10': 3}            # 0.5 and 1.0 x Lsat: the 2nd and 4th load of the ladder of round 25 (uniform traffic, 4x4)
POS = {'chip5': (5, 5), 'chip6': (5, 4), 'ipos5': (6, 4), 'ipos6': (5, 4)}      # in chiplet (1, 1): a router without a VL, and the N slot
PKT_LEN, WARM, NCYC, DMIN = 8, 2000, 10000, 2
TOL = 0.03                               # the bench is calibrated until every rate is within 3 % of the simulator's


def e4_rows():
    """label -> arguments of the simulator row whose load a design carries (DeFT's routers: DeFT_P)."""
    return {'DeFT': X25.row_args(E4_SIZE, 'DeFT_P'), 'main': VARIANTS['main']['row'](E4_SIZE), 'noVLrep': VARIANTS['noVLrep']['row'](E4_SIZE),
            'noLA': VARIANTS['noLA']['row'](E4_SIZE)}


def e4_rate(lt):
    return X25.lp()[X.lkey(E4_SIZE, 'uniform', E5.FREE[E4_SIZE])]['eval'][E4_LOADS[lt]]


def _load_one(arg):
    """One simulator run with the port counters (and the same run with bin/noxim: the statistics must be the same file)."""
    label, lt = arg
    wd = os.path.join(RAW, 'loads')
    rate = e4_rate(lt)
    rname, args = X.job('loads', E4_SIZE, 'E4_' + label, e4_rows()[label], 2, 'uniform', E5.FREE[E4_SIZE], rate, VEC_SEED)
    E5.gen_tables(E4_SIZE, 'uniform', [rate])
    pre = os.path.join(wd, rname)
    if not (os.path.exists(pre + '.ports.txt') and os.path.exists(pre + '.same')):
        for tag, binary, env in (('ref', os.path.join(BIN, 'noxim'), ENV), ('vec', VECBIN, dict(ENV, LB29_PORTS=pre + '.ports.tmp'))):
            subprocess.run([binary] + args + ['-stats_file', pre + '.%s.json' % tag], cwd=BIN, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
        same = os.path.exists(pre + '.ref.json') and os.path.exists(pre + '.vec.json') and open(pre + '.ref.json', 'rb').read() == open(pre + '.vec.json', 'rb').read()
        os.replace(pre + '.ports.tmp', pre + '.ports.txt')
        open(pre + '.same', 'w').write('1' if same else '0')
        for tag in ('ref', 'vec'):
            if os.path.exists(pre + '.%s.json' % tag):
                os.remove(pre + '.%s.json' % tag)
    T = {}
    for line in open(pre + '.ports.txt'):
        f = line.split()
        t = ('ipos' if f[2] == '1' else 'chip') + ('6' if f[3] == '1' else '5')
        v = [int(x) for x in f[5:]]
        a = T.setdefault(t, dict(n=0, cyc=0, fl=[0] * 12, fill=[0] * 12))
        a['n'] += 1
        a['cyc'] += int(f[4])
        for i in range(12):
            a['fl'][i] += v[3 * i]
            a['fill'][i] += v[3 * i + 2]
    return label, lt, rate, open(pre + '.same').read() == '1', T


def loads(nthreads):
    """hw/port_loads.csv: per row, load and router type the flits per cycle and input port, the share on VC 1 and the mean stay of a flit in
    an input buffer, counted by the instrumented copy of the simulator in the measured window."""
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'loads'), exist_ok=True)
    with Pool(nthreads) as pool:
        res = pool.map(_load_one, [(label, lt) for label in e4_rows() for lt in E4_LOADS], chunksize=1)
    rows, ok = [], True
    for label, lt, rate, same, T in res:
        ok = ok and same and len(T) == 4
        for t in sorted(T):
            a = T[t]
            fl, fill, c = a['fl'], a['fill'], float(a['cyc'])
            fm, lm = sum(fl[:8]), sum(fill[:8])
            rows.append(dict(design=label, load=lt, rate=rate, statistics_identical=int(same), rtype=t, routers=a['n'], cycles=a['cyc'] // a['n'],
                             in_mesh=round(fm / (4 * c), 6), in_local=round((fl[8] + fl[9]) / c, 6), in_hub=round((fl[10] + fl[11]) / c, 6),
                             vc1_mesh=round(sum(fl[1:8:2]) / max(1, fm), 4), vc1_hub=round(fl[11] / max(1, fl[10] + fl[11]), 4),
                             stay_mesh=round(lm / max(1, fm), 3), stay_local=round((fill[8] + fill[9]) / max(1, fl[8] + fl[9]), 3),
                             stay_hub=round((fill[10] + fill[11]) / max(1, fl[10] + fl[11]), 3), flits_mesh=fm, fill_mesh=lm))
    with open(os.path.join(HW, 'port_loads.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r['design'], r['load'], r['rtype'], 'mesh %.4f local %.4f vertical %.4f; VC1 %.2f %.2f; stay %.2f %.2f' % (
            r['in_mesh'], r['in_local'], r['in_hub'], r['vc1_mesh'], r['vc1_hub'], r['stay_mesh'], r['stay_hub']))
    print('every instrumented run equals bin/noxim and has the four router types:', 'yes' if ok else 'NO')
    return ok


def power_designs():
    """(label, router type, design dict): the 4x4 routers of DeFT, of the main row and of the two variants (the interposer routers in the
    cut configuration of round 25: one register in the decision unit, after M)."""
    e3 = {d['tag']: d for d in H.designs_e3()}
    e2 = {d['tag']: d for d in designs_e2()}
    out = []
    for t in ('chip5', 'chip6', 'ipos5', 'ipos6'):
        out.append(('DeFT', t, dict(e3['DeFT_d4__%s__4x4' % t], cuts='000')))
        if t.startswith('chip'):
            out.append(('main', t, dict(e3['LBI18__%s__4x4' % t], cuts='000')))
        else:
            for v in VARIANTS:
                out.append((v, t, e2['LF_%s__%s__4x4__c010' % (v, t)]))
    return out


def load_table():
    return {(r['design'], r['load'], r['rtype']): r for r in csv.DictReader(open(os.path.join(HW, 'port_loads.csv')))}


def act_targets(label, t, lt, L):
    """(targets, start parameters) of the bench for a router of type t under the load of a row: flits per cycle on a mesh input, from the
    processing element and from the vertical link, flits per cycle that leave over the vertical link and to the processing element."""
    r = L[(label, lt, t)]
    ipos = t.startswith('ipos')
    m, l, h = float(r['in_mesh']), float(r['in_local']), float(r['in_hub'])
    pool = [L[(label, lt, x)] for x in (('ipos5', 'ipos6') if ipos else ('chip5', 'chip6'))]
    stay_mesh = sum(float(x['fill_mesh']) for x in pool) / max(1.0, sum(float(x['flits_mesh']) for x in pool))
    other = L[(label, lt, 'chip6' if ipos else 'ipos6')]            # the router at the other end of a VL
    vert = float(other['in_hub']) if t.endswith('6') else 0.0        # what leaves over the vertical link arrives at its other end
    eject = 0.0 if ipos else l                                       # uniform traffic: a router receives what it sends
    tg = dict(mesh=m, local=0.0 if ipos else l, hub=h if t.endswith('6') else 0.0, vert=vert, eject=eject)

    def q(rate):
        return 0.0 if rate <= 0 else 65536.0 / (PKT_LEN / rate - PKT_LEN + 1)

    def pr(w):
        return 65536 if w <= DMIN else int(round(65536.0 / (w - DMIN + 1)))
    par = dict(Q_MESH=q(m), Q_HUB=q(tg['hub']), S_VC1_MESH=256 * float(r['vc1_mesh']), S_VC1_HUB=256 * float(r['vc1_hub']),
               PR_MESH=pr(stay_mesh), PR_HUB=pr(float(other['stay_hub'])))
    if ipos:
        par['S_VERT'] = 256 * vert / max(1e-9, 4 * m)
    else:
        par['Q_LOCAL'] = q(l)
        par['S_EJECT'] = 256 * eject / max(1e-9, 4 * m + tg['hub'])
        par['S_VERT'] = 256 * max(0.0, vert - l * 240.0 / 255.0) / max(1e-9, 4 * m)     # the router's own packets for other chiplets go down here
        par['EXIT_SLOT'] = 0
    return tg, par, dict(stay_mesh=stay_mesh, stay_hub=float(other['stay_hub']))


def bench_of(d):
    return 'tb_act25' if d['top'] == 'router25_top' else 'tb_act18'


def bench_run(d, t, par, out, gate=None, vcd=None):
    """Compile and run the activity bench of a design: the RTL, or (gate = netlist file) the synthesised netlist. Returns the RESULT line."""
    tb = bench_of(d)
    P = dict(d['params'], MX=POS[t][0], MY=POS[t][1], WARM=WARM, NCYC=NCYC, LEN=PKT_LEN, DMIN=DMIN, SEED=1)
    P.update({k: int(round(v)) for k, v in par.items()})
    cmd = [os.path.join(OSS, 'iverilog'), '-g2012', '-I' + R25, '-I' + R18, '-I' + RTL, '-s', tb] + ['-P%s.%s=%s' % (tb, k, v) for k, v in P.items()] + ['-o', out]
    if gate:
        cmd += ['-DGATE', os.path.join(RAW, 'power', 'cells.v'), gate] + ([UNITS] if tb == 'tb_act25' else [])
    else:
        cmd += dflags(d['defs']) + d['srcs']
    cmd.append(os.path.join(H.TB, tb + '.v'))
    r = subprocess.run(cmd, capture_output=True, text=True, env=env_eda())
    if r.returncode != 0:
        return 'RESULT compile failed: ' + ' '.join((r.stdout + r.stderr).split())[-400:]
    r = subprocess.run([os.path.join(OSS, 'vvp'), out] + (['+vcd=' + vcd] if vcd else []), capture_output=True, text=True, env=env_eda())
    os.remove(out)
    res = [l for l in r.stdout.splitlines() if l.startswith('RESULT')]
    return res[0] if res else 'RESULT none: ' + ' '.join(r.stdout.split())[-300:]


def achieved(line):
    m = re.search(r' in=([\d,]+) out=([\d,]+) ', line)
    if not m:
        return None
    i, o = ([int(x) for x in m.group(k).split(',')] for k in (1, 2))
    c = float(WARM + NCYC)
    return dict(mesh=sum(i[:4]) / (4 * c), local=i[4] / c, hub=i[5] / c, vert=o[5] / c, eject=o[4] / c)


KNOB = {'mesh': 'Q_MESH', 'local': 'Q_LOCAL', 'hub': 'Q_HUB', 'vert': 'S_VERT', 'eject': 'S_EJECT'}


def calibrate(d, label, t, lt, L):
    """The parameters of the bench with which the RTL carries the simulator's load: each rate within TOL of its target, or the closest of
    ten tries. Returns (parameters, RESULT line, targets, achieved, tries)."""
    tg, par, _ = act_targets(label, t, lt, L)
    wd = os.path.join(RAW, 'act')
    best = None
    for k in range(10):
        line = bench_run(d, t, par, os.path.join(wd, '%s__%s.rtl.vvp' % (d['tag'], lt)))
        a = achieved(line)
        if a is None or not line.rstrip().endswith('OK'):
            return par, line, tg, a, k + 1
        err = max(abs(a[x] / tg[x] - 1.0) for x in tg if tg[x] > 0)
        if best is None or err < best[0]:
            best = (err, dict(par), line, a)
        if err <= TOL:
            break
        for x in tg:
            if tg[x] > 0 and KNOB[x] in par:
                f = min(2.0, max(0.5, tg[x] / max(a[x], 1e-9)))
                par[KNOB[x]] = (max(par[KNOB[x]], 2.0) if f > 1.0 else par[KNOB[x]]) * f       # a knob at 0 can still be raised
        tot = par.get('S_EJECT', 0.0) + par.get('S_VERT', 0.0)
        if tot > 256.0:
            for x in ('S_EJECT', 'S_VERT'):
                if x in par:
                    par[x] *= 256.0 / tot
    return best[1], best[2], tg, best[3], k + 1


CLEAN_YS = """read_liberty -lib {lib}
read_verilog {net}
hierarchy -top {top}
splitnets
rename -hide
rename -enumerate
write_verilog -noattr {out}
"""

POWER_TCL = """
read_liberty {lib}
read_verilog {net}
link_design {top}
create_clock -name clk -period {period} [get_ports clk]
{activity}
puts "POWER_BEGIN"
report_power -digits 6
puts "POWER_END"
puts "ANNOT_BEGIN"
report_activity_annotation
puts "ANNOT_END"
exit
"""
STATIC = 'set_power_activity -input_ports [get_ports {rst my_x* my_y*}] -activity 0 -duty 0' + NL + \
    'if {[llength [get_ports -quiet cfg_*]]} {set_power_activity -input_ports [get_ports cfg_*] -activity 0 -duty 0}'


def cells_file():
    """Verilog models of the library cells, written by Yosys from the liberty file; every register of a model starts at 0."""
    wd = os.path.join(RAW, 'power')
    os.makedirs(wd, exist_ok=True)
    out = os.path.join(wd, 'cells.v')
    if not os.path.exists(out):
        subprocess.run([S.YOSYS, '-q', '-p', 'read_liberty -ignore_miss_func %s; write_verilog -noattr %s' % (S.LIB, out + '.tmp')], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        s = open(out + '.tmp').read()
        s = re.sub(r'^(\s*)reg (\w+);$', lambda m: '%sreg %s;%s%sinitial %s = 1\'b0;' % (m.group(1), m.group(2), NL, m.group(1), m.group(2)), s, flags=re.M)
        open(out, 'w').write(s)
        os.remove(out + '.tmp')
    return out


def clean_netlist(d):
    """The flattened netlist with every internal net split into bits and given a plain name (so that the names of the simulation and of
    the timing tool are the same); the ports keep theirs."""
    wd = os.path.join(RAW, 'power')
    n = d['tag']
    out = os.path.join(wd, n + '.clean.v')
    if os.path.exists(out):
        return out
    gz = os.path.join(RAW, 'flat', n + '.net.v.gz')
    if not os.path.exists(gz):
        return None
    net = os.path.join(wd, n + '.net.v')
    subprocess.run('gunzip -c %s > %s' % (gz, net), shell=True, check=True)
    ys = os.path.join(wd, n + '.clean.ys')
    open(ys, 'w').write(CLEAN_YS.format(lib=S.LIB, net=net, top=d['top'], out=out + '.tmp'))
    r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(wd, n + '.clean.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(net)
    if r.returncode != 0:
        return None
    # The flow of rounds 18 and 25 maps a constant 0 to LOGIC0_X1 with the pin name ZN; the cell's pin is Z. For area and timing the name is
    # of no consequence; in a simulation the net would float. Here the pin gets its name.
    s = open(out + '.tmp').read()
    s, k = re.subn(r'(LOGIC0_X1\s+\S+\s*\(\s*)\.ZN\(', r'\1.Z(', s)
    open(out, 'w').write(s)
    os.remove(out + '.tmp')
    return out


def sta_power(d, net, name, activity):
    wd = os.path.join(RAW, 'power')
    tcl = os.path.join(wd, '%s__%s.tcl' % (d['tag'], name))
    open(tcl, 'w').write(POWER_TCL.format(lib=S.LIB, net=net, top=d['top'], period=S.CLOCK_PS / 1000.0, activity=activity))
    r = subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tcl], capture_output=True, text=True, timeout=14400)
    open(os.path.join(wd, '%s__%s.txt' % (d['tag'], name)), 'w').write(r.stdout + r.stderr)
    m = re.search(r'POWER_BEGIN(.*?)POWER_END', r.stdout, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        f = line.split()
        if len(f) >= 5 and f[0] in ('Sequential', 'Combinational', 'Clock', 'Macro', 'Pad', 'Total'):
            try:
                out[f[0].lower()] = [float(x) for x in f[1:5]]
            except ValueError:
                pass
    a = re.search(r'ANNOT_BEGIN(.*?)ANNOT_END', r.stdout, re.S)
    out['annotation'] = ' '.join(a.group(1).split()) if a else ''
    return out


def power_one(arg):
    """One router and one activity: the default of the tool ('default'), the default with the reset, position and table inputs constant
    ('default_static'), or the simulation of the netlist at a load ('sim05', 'sim10')."""
    label, t, d, act = arg
    res = dict(design=label, rtype=t, tag=d['tag'], activity=act, clock_ns=S.CLOCK_PS / 1000.0)
    net = clean_netlist(d)
    if net is None:
        return dict(res, note='no netlist')
    if act.startswith('default'):
        out = sta_power(d, net, act, STATIC if act == 'default_static' else '# the default activity of the tool')
    else:
        lt = act[3:]
        wd = os.path.join(RAW, 'act')
        os.makedirs(wd, exist_ok=True)
        L = load_table()
        par, rtl, tg, a, tries = calibrate(d, label, t, lt, L)
        res.update(rtl_result=rtl, tries=tries, **{'par_' + k: int(round(v)) for k, v in par.items()})
        res.update({'target_' + k: round(v, 5) for k, v in tg.items()})
        if a:
            res.update({'bench_' + k: round(v, 5) for k, v in a.items()})
        if a is None or not rtl.rstrip().endswith('OK'):
            return dict(res, note='the bench failed on the RTL')
        vcd = os.path.join(wd, '%s__%s.vcd' % (d['tag'], lt))
        gate = bench_run(d, t, par, os.path.join(wd, '%s__%s.gate.vvp' % (d['tag'], lt)), gate=net, vcd=vcd)
        res['gate_equals_rtl'] = int(gate == rtl)
        if gate != rtl:
            res['gate_result'] = gate
        if not os.path.exists(vcd) or not gate.rstrip().endswith('OK'):
            return dict(res, note='the simulation of the netlist failed')
        out = sta_power(d, net, act, 'read_vcd -scope %s/dut %s' % (bench_of(d), vcd))
        os.remove(vcd)
    if not out or 'total' not in out:
        return dict(res, note='no power report')
    i, s, l, tot = out['total']
    res.update(internal_w=i, switching_w=s, leakage_w=l, total_w=tot, annotation=out['annotation'][:400])
    for g in ('sequential', 'combinational', 'clock'):
        if g in out:
            res[g + '_w'] = out[g][3]
    return res


def power(nthreads, extra):
    """hw/power_runs.csv: OpenSTA report_power per router and activity (extra: a regular expression on 'label_type_activity')."""
    from multiprocessing import Pool
    cells_file()
    acts = ['default', 'default_static'] + ['sim' + lt for lt in E4_LOADS]
    jobs = [(label, t, d, a) for label, t, d in power_designs() for a in acts if not extra or re.search(extra, '%s_%s_%s' % (label, t, a))]
    with Pool(nthreads) as pool:
        pool.map(clean_netlist, [d for _, _, d in power_designs()], chunksize=1)
        res = pool.map(power_one, jobs, chunksize=1)
    path = os.path.join(HW, 'power_runs.csv')
    old = []
    if extra and os.path.exists(path):       # a partial run replaces its own rows only
        done = {(r['design'], r['rtype'], r['activity']) for r in res}
        old = [r for r in csv.DictReader(open(path)) if (r['design'], r['rtype'], r['activity']) not in done]
    rows = old + res
    keys = ['design', 'rtype', 'tag', 'activity', 'clock_ns', 'internal_w', 'switching_w', 'leakage_w', 'total_w', 'sequential_w', 'combinational_w', 'clock_w']
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator=NL, restval='')
        w.writeheader()
        w.writerows(rows)
    ok = True
    for r in res:
        good = r.get('total_w', '') != '' and (not r['activity'].startswith('sim') or r.get('gate_equals_rtl') == 1)
        ok = ok and good
        print(r['design'], r['rtype'], r['activity'], r.get('internal_w', ''), r.get('switching_w', ''), r.get('leakage_w', ''), r.get('total_w', ''),
              '' if good else '<-- ' + str(r.get('note', r.get('gate_result', ''))), flush=True)
    return ok


def run_stage(stage, nproc, extra):
    os.makedirs(HW, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    n = min(nproc, 6)
    if stage == 'e2_build':
        sys.exit(0 if build(n) else 1)
    elif stage == 'e2_vec':
        sys.exit(0 if vec(n) else 1)
    elif stage == 'e2_smoke':
        sys.exit(0 if smoke(n) else 1)
    elif stage == 'e2_lat':
        sys.exit(0 if latency(n) else 1)
    elif stage == 'e2_synth':
        sys.exit(0 if synth(extra, n) else 1)
    elif stage == 'e2_csv':
        sys.exit(0 if make_csv() else 1)
    elif stage == 'e4_loads':
        sys.exit(0 if loads(n) else 1)
    elif stage == 'e4_power':
        sys.exit(0 if power(n, extra) else 1)
    else:
        raise SystemExit(__doc__)
