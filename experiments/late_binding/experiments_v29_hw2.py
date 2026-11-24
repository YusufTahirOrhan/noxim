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
  e4_power   OpenSTA report_power on the flattened netlists of the 4x4 routers (default activity, and the activity of a VCD if one is
             given for the design under ~/lbraw/v29/hw/vcd) -> hw/power_runs.csv
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


def make_csv():
    areas = S.lib_areas()
    ar, tm = [], []
    for d in designs_e2():
        row = dict(design=d['design'], rtype=d['rtype'], size=d['size'], form='P', cuts=d['cuts'])
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
POWER_TCL = """
read_liberty {lib}
read_verilog {net}
link_design {top}
create_clock -name clk -period {period} [get_ports clk]
set_input_delay 0 -clock clk [lsearch -inline -all -not -exact [all_inputs] [get_ports clk]]
set_output_delay 0 -clock clk [all_outputs]
{activity}
puts "POWER_BEGIN"
report_power -digits 6
puts "POWER_END"
puts "ANNOT_BEGIN"
report_activity_annotation
puts "ANNOT_END"
exit
"""


def power_designs():
    """(label, design dict): the 4x4 routers of DeFT, of the main row and of the two variants (the cut configuration of round 25: one
    register in the decision unit, after M)."""
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


def power_one(arg):
    label, t, d, period, act_name, act_tcl = arg
    odir = os.path.join(RAW, 'power')
    os.makedirs(odir, exist_ok=True)
    n = d['tag']
    gz = os.path.join(RAW, 'flat', n + '.net.v.gz')
    net = os.path.join(odir, n + '.net.v')
    if not os.path.exists(gz):
        return label, t, act_name, None
    subprocess.run('gunzip -c %s > %s' % (gz, net), shell=True, check=True)
    tcl = os.path.join(odir, '%s__%s.tcl' % (n, act_name))
    open(tcl, 'w').write(POWER_TCL.format(lib=S.LIB, net=net, top=d['top'], period=period, activity=act_tcl))
    r = subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tcl], capture_output=True, text=True, timeout=7200)
    open(os.path.join(odir, '%s__%s.txt' % (n, act_name)), 'w').write(r.stdout + r.stderr)
    os.remove(net)
    m = re.search(r'POWER_BEGIN(.*?)POWER_END', r.stdout, re.S)
    if not m:
        return label, t, act_name, None
    out = {}
    for line in m.group(1).splitlines():
        f = line.split()
        if len(f) >= 5 and f[0] in ('Sequential', 'Combinational', 'Total', 'Clock'):
            try:
                out[f[0].lower()] = [float(x) for x in f[1:5]]
            except ValueError:
                pass
    a = re.search(r'ANNOT_BEGIN(.*?)ANNOT_END', r.stdout, re.S)
    out['annotation'] = ' '.join(a.group(1).split()) if a else ''
    return label, t, act_name, out


def power(nthreads, period=None):
    """report_power per router with the default activity of OpenSTA (inputs 0.1 transitions per clock period, duty 0.5, propagated), and
    with the activity of a VCD where ~/lbraw/v29/hw/vcd/<tag>__<load>.vcd exists (written by the replay test bench, e4_vcd)."""
    from multiprocessing import Pool
    tim = {(r['design'], r['rtype'], r['size'], r['cuts']): r for r in csv.DictReader(open(os.path.join(HW, 'timing_variants.csv')))}
    if period is None:      # the clock of the reference pipeline: the longest stage of DeFT's 4x4 routers in this run
        st = []
        for t in ('chip5', 'chip6', 'ipos5', 'ipos6'):
            r = tim[('DeFT_d4', t, '4x4', '000')]
            st.append(max(float(r[k]) for k in r if k.startswith('stage_') and k != 'stage_FROMLINK' and r[k] not in ('', None)))
        period = round(max(st), 3)
    jobs = []
    for label, t, d in power_designs():
        jobs.append((label, t, d, period, 'default', '# default activity: inputs 0.1 transitions per clock period, duty 0.5'))
        for load in ('05', '10'):
            vcd = os.path.join(RAW, 'vcd', '%s__%s.vcd' % (d['tag'], load))
            if os.path.exists(vcd) or os.path.exists(vcd + '.gz'):
                jobs.append((label, t, d, period, 'vcd' + load, 'read_vcd -scope tb/dut %s' % (vcd if os.path.exists(vcd) else vcd + '.gz')))
    with Pool(nthreads) as pool:
        res = pool.map(power_one, jobs, chunksize=1)
    rows = []
    for label, t, act, out in res:
        if not out or 'total' not in out:
            rows.append(dict(design=label, rtype=t, activity=act, clock_ns=period, internal_w='', switching_w='', leakage_w='', total_w='', note='no result'))
            continue
        i, s, l, tot = out['total']
        rows.append(dict(design=label, rtype=t, activity=act, clock_ns=period, internal_w=i, switching_w=s, leakage_w=l, total_w=tot,
                         sequential_w=out.get('sequential', ['', '', '', ''])[3], combinational_w=out.get('combinational', ['', '', '', ''])[3], note=out['annotation'][:300]))
    with open(os.path.join(HW, 'power_runs.csv'), 'w', newline='') as fh:
        keys = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r['design'], r['rtype'], r['activity'], r['internal_w'], r['switching_w'], r['leakage_w'], r['total_w'])
    return all(r['total_w'] != '' for r in rows)


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
    elif stage == 'e4_power':
        sys.exit(0 if power(n) else 1)
    else:
        raise SystemExit(__doc__)
