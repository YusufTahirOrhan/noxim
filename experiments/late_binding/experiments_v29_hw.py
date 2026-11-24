"""v29 Part E, hardware (results_v29_review/hw/). Run through experiments_v29.py, on a few threads (the simulations keep the others):
  e3_tb      the buffer depths of rtl/router_core29.v under random packets and late credits (tb/tb_core29.v, Icarus), with two controls
             that must fail -> hw/buffer_core_check.txt
  e3_synth   Yosys + ABC (NanGate45 typical, abc -D 1000; the flow of rounds 18, 21 and 25) in three forms (hierarchy kept, router core
             kept, flattened): DeFT's routers with 4-flit buffers (the core of round 18, and the core of this round at its defaults),
             with 5-flit and 6-flit buffers, with 7-flit buffers in the interposer routers; the main row's routers of round 25
             (extra = a regular expression on the design tag; default all)
  e3_csv     hw/area_buffers.csv, hw/system_ratios.csv
The flow, the library and the constraints are those of rounds 18, 21 and 25 (synth_v18.py, experiments_v25_hw2.py); the reference
designs are synthesised again in the same run. Netlists and logs stay under ~/lbraw/v29/hw.
Designs of E3 (tag DESIGN__TYPE__SIZE; router types chip5, chip6 = chiplet router without / with a VL, ipos5, ipos6 = interposer router
without / under a VL):
  DeFT_d4    DeFT's router of round 18, results_v18_area/rtl/router_core.v (4-flit buffers): the reference of every ratio
  DeFT_d4c   the same RTL with rtl/router_core29.v at its defaults (4-flit buffers): must have the area of DeFT_d4
  DeFT_d5, DeFT_d6   every input buffer 5 or 6 flits deep, the credit counters count against the same depth (-buffer 5, -buffer 6)
  DeFT_i7    interposer routers with 7-flit input buffers; chiplet routers with 4-flit buffers; a credit counter counts against the
             depth of the buffer behind its output (-buffer_ipos 7). The chiplet router without a VL is DeFT_d4c.
  LF_X       the interposer router of the main row (round 25, one register in the decision unit: cuts 010), with the core of round 18
  LBI18, CHIP25   the chiplet routers of the main row (round 18's with the exit LUT; on 2x2 with the table of the default entry VL)
"""
import csv
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v25_hw as H25  # noqa: E402
import experiments_v25_hw2 as H2  # noqa: E402
import experiments_v29 as X  # noqa: E402
import synth_v18 as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(X.RES, 'hw')
RTL = os.path.join(HW, 'rtl')
TB = os.path.join(HW, 'tb')
R25 = H25.RTL
R18 = S.RTL
RAW = os.path.join(X.RAW, 'hw')
OSS = H25.OSS
NL = chr(10)
THREADS = 3
SIZES = X.SIZES
TYPES = ['chip5', 'chip6', 'ipos5', 'ipos6']
COUNT = {'chip5': 12, 'chip6': 4, 'ipos5': 12, 'ipos6': 4}        # routers per chiplet (round 25)
FORMS = ['hier', 'semi', 'flat']
CORE18 = os.path.join(R18, 'router_core.v')
CORE29 = os.path.join(RTL, 'router_core29.v')


def src18(core):
    return [core] + [os.path.join(R18, f) for f in ('lb_units.v', 'method_units.v', 'router_top.v')]


def src25(core):
    return [core, os.path.join(R25, 'core25.v'), os.path.join(R25, 'lb25_units.v'), os.path.join(R25, 'router25_top.v')]


def env_eda():
    return dict(os.environ, PATH=OSS + os.pathsep + os.environ['PATH'])


# ---- E3: the functional check of the buffer depths ----
TB_CASES = [(4, 4, 4), (5, 5, 5), (6, 6, 6), (7, 7, 4), (4, 4, 7)]      # (input buffers, behind the link outputs, behind the VL output)
TB_CONTROLS = [((4, 4, 4), (6, 4, 4), 'the RTL has 4-flit input buffers, the test fills 6'), ((4, 6, 6), (4, 4, 4), 'the RTL counts against 6-flit buffers behind its outputs, the test has 4')]


def tb_one(rtl, tbp, hub, name):
    out = os.path.join(RAW, 'tbcore', name + '.vvp')
    cmd = [os.path.join(OSS, 'iverilog'), '-g2012', '-DBUF_DEPTH=%d' % rtl[0], '-DCRED_DEPTH=%d' % rtl[1], '-DCRED_DEPTH_HUB=%d' % rtl[2], '-s', 'tb_core29',
           '-Ptb_core29.HAS_HUB=%d' % hub, '-Ptb_core29.BD=%d' % tbp[0], '-Ptb_core29.CD=%d' % tbp[1], '-Ptb_core29.CH=%d' % tbp[2], '-o', out, CORE29, os.path.join(TB, 'tb_core29.v')]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env_eda())
    if r.returncode != 0:
        return 'RESULT compile failed: ' + (r.stdout + r.stderr)[-300:]
    r = subprocess.run([os.path.join(OSS, 'vvp'), out], capture_output=True, text=True, env=env_eda())
    os.remove(out)
    res = [l for l in r.stdout.splitlines() if l.startswith('RESULT')]
    return res[0] if res else 'RESULT none'


def tb():
    os.makedirs(os.path.join(RAW, 'tbcore'), exist_ok=True)
    L = ['# v29 E3: the buffer depths of rtl/router_core29.v (experiments_v29.py e3_tb; tb/tb_core29.v, Icarus Verilog)', '',
         'The router core with the depths bd (input buffers), cd (the buffers behind the N, E, S, W and Local outputs) and ch (behind the vertical-link output) under random',
         'packets on every input port and credits that come back late and in bursts. Checked: every flit that enters leaves; the flits of a packet leave in order on the',
         'port and VC its head named; packets stay contiguous per output VC; the unreturned flits of an output VC never exceed the depth behind it; the largest fill of an',
         'input buffer and the largest number of unreturned flits reach the depths (the last slot is used). Cases: the depths of DeFT_d4, DeFT_d5, DeFT_d6, of an',
         'interposer router of DeFT_i7 (7, 7, 4) and of a boundary router of DeFT_i7 (4, 4, 7); without and with the vertical-link port.', '']
    ok = True
    for c in TB_CASES:
        for hub in (0, 1):
            res = tb_one(c, c, hub, 'c_%d_%d_%d_%d' % (c + (hub,)))
            ok = ok and res.rstrip().endswith('OK')
            L.append(res)
    L += ['', 'Controls: the test bench is given other depths than the RTL was compiled with; each must FAIL.', '']
    for rtl, tbp, why in TB_CONTROLS:
        res = tb_one(rtl, tbp, 1, 'n_%d_%d_%d' % rtl)
        ok = ok and res.rstrip().endswith('FAIL')
        L.append('%s  [%s]' % (res, why))
    L += ['', 'All cases pass and both controls fail: %s' % ('yes' if ok else 'NO')]
    open(os.path.join(HW, 'buffer_core_check.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok


# ---- E3: synthesis ----
def designs_e3():
    out = []

    def add(design, t, z, top, srcs, params, defs=None):
        out.append(dict(tag='%s__%s__%s' % (design, t, z), design=design, rtype=t, size=z, top=top, srcs=srcs, params=params, defs=defs or {}))
    for z in SIZES:
        for t in TYPES:
            layer = S.TYPES[t][0]
            p = S.params(1, t, z, 0)
            add('DeFT_d4', t, z, 'router_top', src18(CORE18), p)
            add('DeFT_d4c', t, z, 'router_top', src18(CORE29), p)
            add('DeFT_d5', t, z, 'router_top', src18(CORE29), p, dict(BUF_DEPTH=5))
            add('DeFT_d6', t, z, 'router_top', src18(CORE29), p, dict(BUF_DEPTH=6))
            if layer == 1:          # interposer router: 7-flit buffers; behind its Up output the 4-flit buffer of the boundary router
                add('DeFT_i7', t, z, 'router_top', src18(CORE29), p, dict(BUF_DEPTH=7, CRED_DEPTH=7, CRED_DEPTH_HUB=4))
            elif t == 'chip6':      # boundary router: 4-flit buffers; behind its Down output the 7-flit buffer of the interposer router
                add('DeFT_i7', t, z, 'router_top', src18(CORE29), p, dict(BUF_DEPTH=4, CRED_DEPTH=4, CRED_DEPTH_HUB=7))
            if layer == 0:          # the chiplet routers of the main row (round 18's with the exit LUT)
                add('LBI18', t, z, 'router_top', src18(CORE18), S.params(6, t, z, 0))
    for z in ('2x2', '4x4'):        # the interposer router of the main row; its 3x3 router is the 4x4 one (round 25)
        for t in ('ipos5', 'ipos6'):
            add('LF_X', t, z, 'router25_top', src25(CORE18),
                dict(MECH=0, ORDER_O=0, DBIAS=H25.dbias(z), HAS_HUB=S.TYPES[t][1], RS_PER_PORT=1, CUT_A=0, CUT_M=1, CUT_B=0, XW=H25.XW[z], NOSEL=0))
    p18 = S.SIZES['2x2']
    for t in ('chip5', 'chip6'):    # on 2x2 the chiplet router has the table of the default entry VL (D = 2)
        add('CHIP25', t, '2x2', 'chip25_top', src18(CORE18) + [os.path.join(R25, 'chip25_top.v')],
            dict(HAS_HUB=S.TYPES[t][1], C=p18['C'], GX=p18['GX'], XW=p18['XW'], KW=p18['KW'], F=p18['F']))
    return out


def script(d, form, odir, net=False):
    """The Yosys script of round 25 (experiments_v25_hw2.yosys_script and semi_script) with the macros of the design."""
    ch = ' '.join('-set %s %s' % kv for kv in d['params'].items())
    defs = ' '.join('-D%s=%s' % kv for kv in d['defs'].items())
    n, top = d['tag'], d['top']
    L = ['read_verilog -sv %s -I%s -I%s -I%s %s' % (defs, RTL, R25, R18, ' '.join(d['srcs'])), 'chparam %s %s' % (ch, top), 'hierarchy -top %s' % top]
    if form == 'semi':
        L += ['setattr -mod -set keep_hierarchy 1 *router_core*', 'flatten', 'synth -top %s' % top]
    else:
        L += ['flatten t:*pipe_reg* t:*pipe25*', 'synth -top %s' % top + (' -flatten' if form == 'flat' else '')]
    L += ['dfflibmap -liberty %s' % S.LIB, 'abc -liberty %s -D %d -constr %s' % (S.LIB, S.CLOCK_PS, os.path.join(S.RAW, 'abc.constr')),
          'opt_clean -purge', 'setundef -zero', 'hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 ZN', 'insbuf -buf BUF_X1 A Z',
          'tee -q -o %s stat -liberty %s -top %s' % (os.path.join(odir, n + '.stat.txt'), S.LIB, top),
          'tee -q -o %s stat -json -liberty %s -top %s' % (os.path.join(odir, n + '.stat.json'), S.LIB, top)]
    if net:
        L.append('write_verilog -noattr -noexpr -nohex -nodec %s' % os.path.join(odir, n + '.net.v'))
    return NL.join(L) + NL


def run_one(arg):
    d, form = arg
    n = d['tag']
    odir = os.path.join(RAW, form)
    os.makedirs(odir, exist_ok=True)
    net = os.path.join(odir, n + '.net.v')
    if os.path.exists(os.path.join(odir, n + '.stat.json')) and (form != 'flat' or os.path.exists(net + '.gz')):
        return n, form, True
    ys = os.path.join(odir, n + '.ys')
    open(ys, 'w').write(script(d, form, odir, net=(form == 'flat')))
    r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0 and os.path.exists(os.path.join(odir, n + '.stat.json')):
        os.remove(os.path.join(odir, n + '.stat.json'))
    if r.returncode == 0 and form == 'flat':          # the flattened netlist is kept, compressed (timing and power: E2, E4)
        subprocess.run(['gzip', '-f', net], check=True)
    return n, form, r.returncode == 0


def synth(pattern, nthreads=THREADS):
    from multiprocessing import Pool
    S.constr_file()
    ds = [d for d in designs_e3() if not pattern or re.search(pattern, d['tag'])]
    jobs = [(d, f) for f in FORMS for d in ds]
    print('designs %d, runs %d, threads %d' % (len(ds), len(jobs), nthreads), flush=True)
    with Pool(nthreads) as pool:
        res = pool.map(run_one, jobs, chunksize=1)
    bad = sorted('%s (%s)' % (n, f) for n, f, ok in res if not ok)
    print('synthesis: %d / %d runs done; failed: %s' % (len(res) - len(bad), len(res), bad))
    return not bad


def area_of(d, form, areas):
    """(area in um^2, flip-flops): the sum over the cells of the netlist, checked against the tool's own design area."""
    f = os.path.join(RAW, form, d['tag'] + '.stat.json')
    tot = H2.parse_stat(f, areas, d['top'])
    a = sum(x['area'] for x in tot.values())
    own = H2.design_area(f)[0]
    if abs(a - own) > 0.01:
        raise SystemExit('%s (%s): the cells add up to %.3f, the tool reports %.3f' % (d['tag'], form, a, own))
    return a, sum(x['ffs'] for x in tot.values()), tot


def make_csv():
    areas = S.lib_areas()
    A, rows = {}, []
    for d in designs_e3():
        row = dict(design=d['design'], rtype=d['rtype'], size=d['size'], macros=' '.join('%s=%s' % kv for kv in d['defs'].items()))
        for f in FORMS:
            a, ffs, tot = area_of(d, f, areas)
            A[(d['design'], d['rtype'], d['size'], f)] = a
            row['area_%s_um2' % f] = round(a, 3)
            row['ffs_%s' % f] = ffs
            if f == 'hier':
                row['buffers_hier_um2'] = round(tot.get('buffers', {}).get('area', 0.0), 3)
        rows.append(row)
    with open(os.path.join(HW, 'area_buffers.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)

    def ar(design, t, z, f):
        if design == 'DeFT_i7' and t == 'chip5':
            design = 'DeFT_d4c'                  # the chiplet router without a VL has no 7-flit buffer anywhere near it
        if design == 'LF_X' and z == '3x3':
            z = '4x4'                            # round 25: the interposer router of 3x3 is the one of 4x4
        return A[(design, t, z, f)]

    def system(design, z, f):
        """Average router area of a system: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers per chiplet (round 25)."""
        tot = 0.0
        for t in TYPES:
            if design == 'main':
                v = ar('LF_X', t, z, f) if t.startswith('ipos') else (ar('CHIP25', t, z, f) if z == '2x2' else ar('LBI18', t, z, f))
            else:
                v = ar(design, t, z, f)
            tot += COUNT[t] * v
        return tot / 32.0
    out = []
    names = [('d4c', 'DeFT_d4c'), ('d5', 'DeFT_d5'), ('d6', 'DeFT_d6'), ('i7', 'DeFT_i7'), ('main', 'main')]
    for key, design in names:
        for z in SIZES:
            for f in FORMS:
                out.append(dict(design=key, size=z, form=f, system_um2=round(system(design, z, f), 2), ratio=round(system(design, z, f) / system('DeFT_d4', z, f), 5)))
    with open(os.path.join(HW, 'system_ratios.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(out)
    for key, _ in names:
        print(key, {z: ' / '.join('%.3f' % r['ratio'] for r in out if r['design'] == key and r['size'] == z) for z in SIZES})
    # the main row's ratios of round 25, for the check that this run reproduces them
    v25 = os.path.join(H25.HW, '..', 'report', 'hw_system_area.csv')
    if os.path.exists(v25):
        for r in csv.DictReader(open(v25)):
            if (r['design'], r['form'], r['cuts']) == ('LF_X', 'P', '010'):
                print('round 25, main row, %s: %s / %s / %s' % (r['size'], r.get('rel_deft_hier'), r.get('rel_deft_semi'), r.get('rel_deft_flat')))
    return True


def run_stage(stage, nproc, extra):
    os.makedirs(HW, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'e3_tb':
        sys.exit(0 if tb() else 1)
    elif stage == 'e3_synth':
        sys.exit(0 if synth(extra, min(nproc, 6)) else 1)
    elif stage == 'e3_csv':
        sys.exit(0 if make_csv() else 1)
    else:
        raise SystemExit(__doc__)
