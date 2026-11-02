"""v18 (Part J): synthesis flow (results_v18_area/). One library, one flow for every method.

Usage: python3 synth_v18.py STAGE [nproc]
  tools     records tool versions -> results_v18_area/tools.md
  hier      hierarchy kept, per-module breakdown: all methods x router types x C (S form), plus the P form of the LB methods
  flat      flattened: the same designs for timing (OpenSTA)
  csv       parses the outputs -> area_runs.csv, breakdown_runs.csv, timing_runs.csv; raw outputs deleted with 'csv cleanup'
Yosys netlists and logs stay under ~/lbraw/v18 (not in the repository).
"""
import json
import os
import re
import subprocess
import sys
import csv
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v18_area')
RTL = os.path.join(RES, 'rtl')
HOME = os.path.expanduser('~')
RAW = os.path.join(HOME, 'lbraw', 'v18')
EDA = os.path.join(HOME, 'eda')
YOSYS = os.path.join(EDA, 'oss-cad-suite', 'bin', 'yosys')
STA = os.path.join(EDA, 'dl_sta', 'OpenSTA', 'build', 'sta')
LIB = os.path.join(EDA, 'dl_lib', 'NangateOpenCellLibrary_typical.lib')
CLOCK_PS = 1000
NL = chr(10)

METHODS = {0: 'REF', 1: 'DeFT', 2: 'DeFT14', 3: 'MTR', 4: 'RC', 5: 'DeFT_Dis', 6: 'LBI_heur', 7: 'LBI_ql', 8: 'LBF_heur', 9: 'LBF_ql'}
TYPES = {'chip5': (0, 0), 'chip6': (0, 1), 'ipos5': (1, 0), 'ipos6': (1, 1)}
SIZES = {'2x2': dict(C=4, GX=2, XW=3, KW=2, F=10), '3x3': dict(C=9, GX=3, XW=4, KW=4, F=8), '4x4': dict(C=16, GX=4, XW=4, KW=4, F=8)}
# Frozen parameters of experiments_v10.methods: w = 2^W_SHIFT, beta, alpha = 2^-S1 + 2^-S2
LBP = {('I', '2x2'): dict(W_SHIFT=0, BETA=4, S1=5, S2=6), ('I', '3x3'): dict(W_SHIFT=1, BETA=0, S1=4, S2=5),
       ('I', '4x4'): dict(W_SHIFT=1, BETA=0, S1=4, S2=5), ('F', '2x2'): dict(W_SHIFT=1, BETA=0, S1=7, S2=9),
       ('F', '3x3'): dict(W_SHIFT=1, BETA=0, S1=6, S2=8), ('F', '4x4'): dict(W_SHIFT=0, BETA=4, S1=5, S2=6)}


def params(m, t, z, per_port):
    layer, hub = TYPES[t]
    p = dict(METHOD=m, LAYER=layer, HAS_HUB=hub, RS_PER_PORT=per_port, **SIZES[z])
    if m in (6, 7):
        p.update(LBP[('I', z)])
    elif m in (8, 9):
        p.update(LBP[('F', z)])
    return p


def tag(m, t, z, per_port):
    return f'{METHODS[m]}__{t}__{z}' + ('__P' if per_port else '__S')


def designs():
    out = []
    for z in SIZES:
        for t in TYPES:
            for m in METHODS:
                out.append((m, t, z, 0))
                layer = TYPES[t][0]
                # the P form exists where the routing + selection logic lives
                if (m in (6, 7) and layer == 1) or m in (8, 9):
                    out.append((m, t, z, 1))
    return out


def constr_file():
    os.makedirs(RAW, exist_ok=True)
    f = os.path.join(RAW, 'abc.constr')
    open(f, 'w').write('set_driving_cell BUF_X2' + NL + 'set_load 2.0' + NL)
    return f


def yosys_script(d, flat, odir):
    m, t, z, pp = d
    p = params(m, t, z, pp)
    ch = ' '.join(f'-set {k} {v}' for k, v in p.items())
    n = tag(m, t, z, pp)
    srcs = ' '.join(os.path.join(RTL, f) for f in ('router_core.v', 'lb_units.v', 'method_units.v', 'router_top.v'))
    L = [f'read_verilog -sv -I{RTL} {srcs}', f'chparam {ch} router_top', 'synth -top router_top' + (' -flatten' if flat else ''),
         f'dfflibmap -liberty {LIB}', f'abc -liberty {LIB} -D {CLOCK_PS} -constr {os.path.join(RAW, "abc.constr")}',
         'opt_clean -purge', 'setundef -zero', 'hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 ZN', 'insbuf -buf BUF_X1 A Z',
         f'tee -q -o {os.path.join(odir, n + ".stat.txt")} stat -liberty {LIB} -top router_top',
         f'tee -q -o {os.path.join(odir, n + ".stat.json")} stat -json -liberty {LIB} -top router_top',
         f'write_verilog -noattr -noexpr -nohex -nodec {os.path.join(odir, n + ".net.v")}']
    return NL.join(L) + NL


STA_TCL = """
read_liberty {lib}
read_verilog {net}
link_design router_top
create_clock -name clk -period {period} [get_ports clk]
set_input_delay 0 -clock clk [lsearch -inline -all -not -exact [all_inputs] [get_ports clk]]
set_output_delay 0 -clock clk [all_outputs]
puts "ALL"
report_checks -path_delay max -format short -digits 4
report_wns -digits 4
puts "WNS_ALL [sta::worst_slack -max]"
proc ends {{pat}} {{
    set out {{}}
    foreach n [get_nets -quiet $pat] {{
        foreach p [get_pins -quiet -of_objects $n -filter "direction == output"] {{
            set c [get_cells -of_objects $p]
            set d [get_pins -quiet [get_full_name $c]/D]
            if {{[llength $d]}} {{ lappend out $d }}
        }}
    }}
    return $out
}}
proc rep {{name pat}} {{
    set e [ends $pat]
    puts "GROUP $name [llength $e]"
    if {{[llength $e]}} {{
        report_checks -to $e -path_delay max -digits 4 -fields {{}}
    }}
}}
rep ROUTE_REG {{*ctl.out_port*}}
rep ROUTE_HDR {{*ctl.hdr*}}
rep OVC_REG {{*ctl.out_vc*}}
rep QTABLE {{*.m.mem*}}
rep CORE_OUT {{*xb.op*.r*}}
report_checks -to [get_ports fb_out_g*] -path_delay max -digits 4
exit
"""


def run_one(arg):
    d, flat = arg
    n = tag(*d)
    odir = os.path.join(RAW, 'flat' if flat else 'hier')
    os.makedirs(odir, exist_ok=True)
    if os.path.exists(os.path.join(odir, n + ('.sta.txt' if flat else '.stat.json'))):
        return n, True
    ys = os.path.join(odir, n + '.ys')
    open(ys, 'w').write(yosys_script(d, flat, odir))
    r = subprocess.run([YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return n, False
    if flat:
        tcl = os.path.join(odir, n + '.tcl')
        open(tcl, 'w').write(STA_TCL.format(lib=LIB, net=os.path.join(odir, n + '.net.v'), period=CLOCK_PS / 1000.0))
        with open(os.path.join(odir, n + '.sta.txt'), 'w') as o:
            subprocess.run([STA, '-no_init', '-no_splash', '-exit', tcl], stdout=o, stderr=subprocess.STDOUT, timeout=3600)
    return n, True


def tools():
    y = subprocess.run([YOSYS, '-V'], capture_output=True, text=True).stdout.strip()
    s = subprocess.run([STA, '-version'], capture_output=True, text=True).stdout.strip()
    iv = subprocess.run([os.path.join(EDA, 'oss-cad-suite', 'bin', 'iverilog'), '-V'], capture_output=True, text=True).stdout.splitlines()[0]
    h = subprocess.run(['md5sum', LIB], capture_output=True, text=True).stdout.split()[0]
    L = ['# v18 tools', '', f'* Yosys with bundled ABC: {y} (OSS CAD Suite, release 2026-11-01).', f'* OpenSTA: {s}, built from the OpenROAD project repository, without root.',
         f'* Icarus Verilog: {iv}.', f'* Library: NanGate45 Open Cell Library, typical corner, `NangateOpenCellLibrary_typical.lib`, OpenROAD-flow-scripts '
         f'`flow/platforms/nangate45/lib/`, md5 {h}.', f'* Clock target: 1 GHz (`abc -D {CLOCK_PS}`, OpenSTA clock period 1 ns).', '* ABC constraints: driving cell BUF_X2, load 2 fF.']
    open(os.path.join(RES, 'tools.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


# ---- parsing ----
def lib_areas():
    a, cur = {}, None
    for l in open(LIB):
        m = re.match(r'\s*cell\s*\(\s*"?([A-Za-z0-9_]+)"?\s*\)', l)
        if m:
            cur = m.group(1)
        m = re.match(r'\s*area\s*:\s*([0-9.]+)', l)
        if m and cur and cur not in a:
            a[cur] = float(m.group(1))
    return a


CATS = [('ibuf', 'buffers'), ('rc_buffer', 'rc_buffer'), ('xbar', 'crossbar'), ('vc_alloc', 'allocators'), ('sw_alloc', 'allocators'),
        ('ivc_ctrl', 'allocators'), ('credit_ctrs', 'allocators'), ('router_core', 'crossbar'),
        ('lb_route', 'routing'), ('rt_', 'routing'), ('vn_unit', 'routing'), ('xy_dir', 'routing'),
        ('lb_sel', 'selection'), ('lbi_fb_chip', 'selection'), ('occ_regs', 'selection'),
        ('cfg_table', 'tables'), ('q_bank', 'tables'), ('q_update', 'learning'), ('q_fb_regs', 'learning'),
        ('ni_', 'ni'), ('near_vl', 'ni'), ('rc_ni', 'ni'), ('rc_opic_br', 'ni')]


def cat_of(mod):
    parts = mod.split(chr(92))
    s = parts[1] if mod.startswith('$paramod') else parts[-1]
    for pre, c in CATS:
        if s.startswith(pre):
            return c
    return None


def parse_hier(path, areas):
    """Area, cells and FF count per category. A cell inherits the category of its nearest categorized ancestor."""
    j = json.load(open(path))
    mods = j['modules']
    def base(n):
        return n
    def walk(mod, cat, totals):
        info = mods[mod]
        c = cat_of(mod) or cat
        for ty, cnt in info['num_cells_by_type'].items():
            if ty in mods or ty.lstrip('\\') in mods:
                sub = ty if ty in mods else ty.lstrip('\\')
                for _ in range(cnt):
                    walk(sub, c, totals)
            else:
                t = totals.setdefault(c, dict(area=0.0, cells=0, ffs=0))
                t['area'] += areas.get(ty, 0.0) * cnt
                t['cells'] += cnt
                if ty.startswith('DFF'):
                    t['ffs'] += cnt
    tops = [m for m in mods if 'router_top' in m]
    totals = {}
    walk(tops[0], 'top', totals)
    return totals


def parse_sta(path):
    """Worst slack overall and per group (ns; period 1 ns)."""
    txt = open(path).read()
    out = {}
    m = re.search(r'WNS_ALL (-?[0-9.e+-]+)', txt)
    out['slack_all_ns'] = float(m.group(1)) if m else None
    for g in ('ROUTE_REG', 'ROUTE_HDR', 'OVC_REG', 'QTABLE', 'CORE_OUT'):
        m = re.search(r'GROUP ' + g + r' (\d+)(.*?)(GROUP|\Z)', txt, re.S)
        if m and int(m.group(1)) > 0:
            s = re.search(r'(-?[0-9.]+)\s+slack', m.group(2))
            d = re.search(r'(-?[0-9.]+)\s+data arrival time', m.group(2))
            out['slack_' + g] = float(s.group(1)) if s else None
            out['arrival_' + g] = float(d.group(1)) if d else None
        else:
            out['slack_' + g] = None
            out['arrival_' + g] = None
    return out


def make_csv():
    areas = lib_areas()
    rows, brk, tim = [], [], []
    for d in designs():
        m, t, z, pp = d
        n = tag(*d)
        base = dict(method=METHODS[m], rtype=t, size=z, form='P' if pp else 'S')
        f = os.path.join(RAW, 'hier', n + '.stat.json')
        if os.path.exists(f):
            tot = parse_hier(f, areas)
            rows.append(dict(base, area_um2=round(sum(x['area'] for x in tot.values()), 3), cells=sum(x['cells'] for x in tot.values()),
                             ffs=sum(x['ffs'] for x in tot.values())))
            for c, x in sorted(tot.items()):
                brk.append(dict(base, category=c, area_um2=round(x['area'], 3), cells=x['cells'], ffs=x['ffs']))
        fs = os.path.join(RAW, 'flat', n + '.sta.txt')
        fj = os.path.join(RAW, 'flat', n + '.stat.json')
        if os.path.exists(fs):
            tot = parse_hier(fj, areas)
            tim.append(dict(base, area_flat_um2=round(sum(x['area'] for x in tot.values()), 3), **parse_sta(fs)))
    for fn, rr in (('area_runs.csv', rows), ('breakdown_runs.csv', brk), ('timing_runs.csv', tim)):
        if rr:
            with open(os.path.join(RES, fn), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rr[0]), lineterminator=NL)
                w.writeheader()
                w.writerows(rr)
    print(f'area {len(rows)}, breakdown {len(brk)}, timing {len(tim)} rows; designs {len(designs())}')


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    os.makedirs(RES, exist_ok=True)
    constr_file()
    if stage == 'tools':
        tools()
    elif stage in ('hier', 'flat'):
        flat = stage == 'flat'
        ds = designs()
        if len(sys.argv) > 3:
            ds = [d for d in ds if re.search(sys.argv[3], tag(*d))]
        with Pool(nproc) as pool:
            res = pool.map(run_one, [(d, flat) for d in ds], chunksize=1)
        bad = [n for n, ok in res if not ok]
        print(f'{stage}: {len(res) - len(bad)} / {len(res)} done; failed: {bad}')
    elif stage == 'csv':
        make_csv()
    else:
        raise SystemExit(__doc__)
