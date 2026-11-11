"""v25 Part F, second module (run through experiments_v25.py):
  f_mut     F2: single-line mutations of the RTL must produce mismatches on kept vectors -> hw/mutation_check.txt
  f_lat     F4: cycles of a head through an idle router, per design and cut configuration (hw/tb/tb_lat25.v) -> hw/latency_check.txt
  f_synth   F3/F4: Yosys + ABC (NanGate45 typical, abc -D 1000), hierarchy kept and flattened; OpenSTA on the flat netlists
            (extra = a regular expression on the design tag; default all)
  f_semi    F3: a third synthesis with the hierarchy kept for the router core only (buffers, allocators, crossbar), the rest flattened
  f_csv     F3/F4: hw/area_runs.csv, hw/breakdown_runs.csv, hw/timing_runs.csv
Flow, library, constraints and conventions are those of rounds 18 and 21 (synth_v18.py): one flow for every design, the
reference designs (DeFT, the LB-I heuristic of round 18) are synthesised again in the same run.
Netlists and logs stay under ~/lbraw/v25/hw.
"""
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v25_hw as H  # noqa: E402
import synth_v18 as S  # noqa: E402

HW, RTL, TB, R18, RAW, OSS, NL, THREADS = H.HW, H.RTL, H.TB, H.R18, H.RAW, H.OSS, H.NL, H.THREADS
CUTS = H.CUTS

# ---- F2: mutation check ----
# (name, file, old text, new text, checker, ORDER_O, design of the kept vectors, size of the kept vectors)
MUTATIONS = [
    ('xy_order: a Y move before the X moves are done', 'lb25_units.v', '(xz && ylt && !ls)', '(ylt && !ls)', 'sel', 0, 'LF_X', '4x4'),
    ('xy_turn: an X move after a Y move', 'lb25_units.v', '(xgt && !lw && !ly)', '(xgt && !lw)', 'sel', 0, 'LF_X', '4x4'),
    ('prune: the mask is not pruned by the move', 'lb25_units.v', 'cand[s] && !here[s] && mv[4*s+d]', 'cand[s] && !here[s]', 'sel', 0, 'LF_X', '4x4'),
    ('hub_prune: the Up link keeps every candidate', 'lb25_units.v', 'assign pruned[19:16] = HAS_HUB ? (cand & here) : 4\'b0;', 'assign pruned[19:16] = HAS_HUB ? cand : 4\'b0;', 'sel', 0, 'LF_X', '4x4'),
    ('t_up_hop: the Up link is not counted in the path total', 'lb25_units.v', "+ 6'd1 + {3'b0, rloc}", "+ {3'b0, rloc}", 'sel', 0, 'LF_X', '4x4'),
    ('t_rloc: wrong coordinate in the distance VL -> destination', 'lb25_units.v', 'absd2(slot_ly(SLOT), dst_y[1:0])', 'absd2(slot_lx(SLOT), dst_y[1:0])', 'sel', 0, 'LF_X', '4x4'),
    ('z_turn: the neighbour turns before its X moves are done', 'lb25_units.v', '(xmove && !x2 && !yx && ylt)', '(xmove && !yx && ylt)', 'sel', 0, 'LF_X', '4x4'),
    ('zh: the boundary router moves in Y before X', 'lb25_units.v', 'wire [3:0] zh = {dxlt, dxz && dygt, dxgt, dxz && dylt};', 'wire [3:0] zh = {dxlt, dygt, dxgt, dylt};', 'sel', 0, 'LF_X', '4x4'),
    ('occ_vc: the neighbour report is read on VC0 only', 'lb25_units.v', '(vn_a ? occ_nb[(oo*5+zz)*6+3+:3] : occ_nb[(oo*5+zz)*6+:3])', 'occ_nb[(oo*5+zz)*6+:3]', 'sel', 0, 'LF_X', '4x4'),
    ('up_vc1: behind the Up link VC0 is read', 'lb25_units.v', 'gs = gs | occ_nb[(4*5+zz)*6+3+:3];', 'gs = gs | occ_nb[(4*5+zz)*6+:3];', 'sel', 0, 'LF_X', '4x4'),
    ('own_occ: the own occupancy is read on VC0 only', 'lb25_units.v', '(vn_a ? occ_self[(oo*2+1)*3+:3] : occ_self[(oo*2)*3+:3])', 'occ_self[(oo*2)*3+:3]', 'sel', 0, 'LF_X', '4x4'),
    ('weight: w = 1 instead of 2', 'lb25_units.v', '({3\'b0, occ_m[4*s+:4]} << W_SHIFT)', '({3\'b0, occ_m[4*s+:4]})', 'sel', 0, 'LF_X', '4x4'),
    ('bias: no default-VL penalty', 'lb25_units.v', '(bias_m[s] ? DBIAS : 0)', '0', 'sel', 0, 'LF_X', '2x2'),
    ('bias_def: the penalty also when the default VL is not a candidate', 'lb25_units.v', '(DBIAS != 0) && cand[def_slot] && !pruned[o*4+def_slot]', '(DBIAS != 0) && !pruned[o*4+def_slot]', 'sel', 0, 'LF_X', '2x2'),
    ('tie_lt: strict comparison of the candidate costs', 'lb25_units.v', '(cost_b[7*s+:7] <= cost_b[7*t+:7])', '(cost_b[7*s+:7] < cost_b[7*t+:7])', 'sel', 0, 'LF_X', '4x4'),
    ('tie_drop: candidate 3 is left out of the outputs of least cost', 'lb25_units.v', ' || (ismin[3] && o1h_b[15+o]);', ';', 'sel', 0, 'LF_X', '4x4'),
    ('rot: the tie break ignores its pointer', 'lb25_units.v', 'wire [4:0] hi = tie & ge;', 'wire [4:0] hi = tie;', 'sel', 0, 'LF_X', '4x4'),
    ('rot_wrap: the tie break does not wrap around', 'lb25_units.v', 'wire [4:0] pk = (|hi) ? hi : tie;', 'wire [4:0] pk = hi;', 'sel', 0, 'LF_X', '4x4'),
    ('yx_order (VN-split order): an X move before the Y moves are done in VN1', 'lb25_units.v', '(yz && xgt && !lw)', '(xgt && !lw)', 'sel', 1, 'LF_O', '4x4'),
    ('vn_order (VN-split order): the two VNs swap their orders', 'lb25_units.v', '(VNFIX >= 0) ? (VNFIX != 0) : vn;', '(VNFIX >= 0) ? (VNFIX == 0) : !vn;', 'sel', 1, 'LF_O', '4x4'),
    ('fb_free: the fallback never leaves the stored output', 'lb25_units.v', 'wire stored_free = |(st1 & free);', "wire stored_free = 1'b1;", 'front', 0, 'LF_X', '4x4'),
    ('fb_none: with no free output the first alternative is asked, not the stored output', 'lb25_units.v', 'assign req = (stored_free || !(|alt)) ? stored : first;', 'assign req = stored_free ? stored : first;', 'front', 0, 'LF_X', '4x4'),
    ('fb_order: the fallback tries N before the Up link', 'lb25_units.v', "alt[4] ? 3'd4 : alt[0] ? 3'd0 :", "alt[0] ? 3'd0 : alt[4] ? 3'd4 :", 'front', 0, 'LF_X', '4x4'),
    ('fb_order2: the fallback tries W, S, E before N', 'lb25_units.v', "alt[0] ? 3'd0 : alt[1] ? 3'd1 : alt[2] ? 3'd2 : 3'd3;", "alt[3] ? 3'd3 : alt[2] ? 3'd2 : alt[1] ? 3'd1 : 3'd0;", 'front', 0, 'LF_X', '4x4'),
    ('fb_offered: the fallback may ask for an output that is not offered', 'lb25_units.v', 'wire [4:0] alt = offered & free & ~st1;', 'wire [4:0] alt = free & ~st1;', 'front', 0, 'LF_X', '4x4'),
]


def build_checker(kind, params, rtl_dir, mdir):
    exe = os.path.join(mdir, 'Vvl_%s25' % kind)
    g = ['-G%s=%s' % kv for kv in params.items()]
    cmd = [os.path.join(OSS, 'verilator'), '--cc', '--exe', '--build', '-O2', '-j', '1', '-Wno-fatal', '--top-module', 'vl_%s25' % kind, '-I' + rtl_dir,
           '--Mdir', mdir] + g + [os.path.join(rtl_dir, 'lb25_units.v'), os.path.join(TB, 'vl25.v'), os.path.join(TB, 'vl_%s25.cpp' % kind)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=H.env_eda())
    return exe if r.returncode == 0 and os.path.exists(exe) else None


def mutation():
    wd = os.path.join(RAW, 'mut')
    L = ['# v25 F2: can the vector checks fail? (experiments_v25.py f_mut)', '',
         'Each mutation changes one piece of text in a copy of the RTL; the checker is built from the copy and run on the vectors kept from one simulator run',
         '(uniform fault-free at 1.0 x Lsat) of the named design and size, without pipeline cuts. A mutation is caught when the checker reports mismatches.', '',
         '| mutation | file | vectors | applied | mismatches | caught |', '|---|---|---|---|---|---|']
    caught, missed = 0, []
    for k, (name, fn, old, new, kind, oo, design, z) in enumerate(MUTATIONS):
        shutil.rmtree(wd, ignore_errors=True)
        shutil.copytree(RTL, os.path.join(wd, 'rtl'))
        p = os.path.join(wd, 'rtl', fn)
        s = io.open(p, encoding='utf-8').read()
        if s.count(old) != 1:
            L.append('| %s | %s | | | | **the mutation did not apply (%d matches)** |' % (name, fn, s.count(old)))
            missed.append(name)
            continue
        io.open(p, 'w', encoding='utf-8', newline=NL).write(s.replace(old, new))
        params = dict(ORDER_O=oo, DBIAS=H.dbias(z), CUT_A=0, CUT_M=0, CUT_B=0) if kind == 'sel' else dict(ORDER_O=oo)
        exe = build_checker(kind, params, os.path.join(wd, 'rtl'), os.path.join(wd, 'obj'))
        vecf = os.path.join(RAW, 'vec', 'keep_%s_%s.%s.txt' % (design, z, 'sel' if kind == 'sel' else 'fb'))
        if not exe or not os.path.exists(vecf):
            L.append('| %s | %s | %s %s | | | **could not be run** |' % (name, fn, design, z))
            missed.append(name)
            continue
        args = [str(oo), str(H.dbias(z)), '0', '0', '0'] if kind == 'sel' else [str(oo)]
        out = subprocess.run([exe, vecf] + args, capture_output=True, text=True).stdout
        res = [l for l in out.splitlines() if l.startswith('RESULT')]
        n, m = (H._num(res[0], 'vectors'), H._num(res[0], 'mismatches')) if res else (0, 0)
        if m > 0:
            caught += 1
        else:
            missed.append(name)
        L.append('| %s | %s | %s %s (%s) | %d | %d | %s |' % (name, fn, design, z, 'selection' if kind == 'sel' else 'front', n, m, 'yes' if m > 0 else '**no**'))
    shutil.rmtree(wd, ignore_errors=True)
    L += ['', '**%d of %d mutations caught.**' % (caught, len(MUTATIONS))]
    if missed:
        L += ['', 'Not caught: ' + '; '.join(missed) + '. See `hw/FINDINGS_hw.md` for whether each is redundant logic on reachable inputs.']
    open(os.path.join(HW, 'mutation_check.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return caught, missed


# ---- F4: cycles through the router ----
def _lat_one(cfg):
    name, mech, oo, db, hub, pp, (ca, cm, cb), xw, nosel = cfg
    out = os.path.join(RAW, 'lat', '%s_%d.vvp' % (name, os.getpid()))
    H.iverilog('tb_lat25', dict(MECH=mech, ORDER_O=oo, DBIAS=db, HAS_HUB=hub, RS_PER_PORT=pp, CUT_A=ca, CUT_M=cm, CUT_B=cb, XW=xw, NOSEL=nosel, SEED=1, NPKT=2000), out,
               H.ROUTER_SRCS + [os.path.join(TB, 'tb_lat25.v')])
    r = subprocess.run([os.path.join(OSS, 'vvp'), out], capture_output=True, text=True, env=H.env_eda())
    os.remove(out)
    return [l for l in r.stdout.splitlines() if l.startswith('RESULT') or 'did not leave' in l]


def latency():
    """hw/latency_check.txt: link-to-link cycles of a head through an idle router, per design and cut configuration, against the rule the
    timing tables use: 4 cycles for a head with one offered output; for a head with a choice 4 + max(0, cuts - 1) in LF (the decision has the
    link cycle and the route cycle) and 4 + cuts in DLY (the decision starts at the buffer front)."""
    from multiprocessing import Pool
    os.makedirs(os.path.join(RAW, 'lat'), exist_ok=True)
    cfgs = []
    for z in ('2x2', '4x4'):
        for name, d in H.DESIGNS.items():
            for pp in ((1,) if d['mech'] == 0 else (1, 0)):
                for hub in (0, 1):
                    cfgs += [('%s_%s' % (name, z), d['mech'], d['order_o'], H.dbias(z), hub, pp, c, H.XW[z], 0) for c in CUTS]
        for mech, pp in ((0, 1), (1, 1), (1, 0)):          # the relation without a selection
            for hub in (0, 1):
                cfgs.append(('REL_%s' % z, mech, 0, 0, hub, pp, (0, 0, 0), H.XW[z], 1))
    with Pool(THREADS) as pool:
        res = pool.map(_lat_one, cfgs, chunksize=1)
    L = ['# v25 F4: cycles of a head through an idle interposer router (experiments_v25.py f_lat; hw/tb/tb_lat25.v, Icarus Verilog)', '',
         'Two-flit packets, one at a time, into an idle router with free outputs: cycles from the cycle the head is on the input link to the cycle it is on the',
         'output link. The pipeline of the reference core is link + buffer write, route, VC allocation, switch allocation + crossbar: 4 cycles.',
         'Expected for a head with a choice: LF 4 + max(0, cuts - 1), DLY 4 + cuts; relation only (the first offered output is taken): 4.', '',
         '| design | mechanism | units | Up link | cuts (A M B) | L_dec | heads with one output: n, cycles | heads with a choice: n, cycles | expected | result |', '|---|---|---|---|---|---|---|---|---|---|']
    ok = True
    for (name, mech, oo, db, hub, pp, cuts, xw, nosel), lines in zip(cfgs, res):
        m = re.search(r'one_output=(\d+) min=(\d+) max=(\d+) choice=(\d+) min=(\d+) max=(\d+) errors=(\d+)', ' '.join(lines))
        n = sum(cuts)
        exp = 4 if nosel else 4 + (max(0, n - 1) if mech == 0 else n)
        good = bool(m) and int(m.group(7)) == 0 and len(lines) == 1 and int(m.group(1)) > 0 and m.group(2) == m.group(3) == '4' and \
            int(m.group(4)) > 0 and int(m.group(5)) == int(m.group(6)) == exp
        ok = ok and good
        g = m.groups() if m else ('?',) * 7
        L.append('| %s | %s | %s | %s | %d %d %d | %d | %s, %s-%s | %s, %s-%s | %d | %s |' % (name, 'LF' if mech == 0 else 'DLY', 'per port' if pp else 'per router', 'yes' if hub else 'no',
                                                                                     cuts[0], cuts[1], cuts[2], 1 + n, g[0], g[1], g[2], g[3], g[4], g[5], exp, 'OK' if good else '**FAIL**'))
    L += ['', 'configurations %d, all as expected: **%s**' % (len(cfgs), 'yes' if ok else 'NO')]
    open(os.path.join(HW, 'latency_check.txt'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-1:]))
    return ok


# ---- F3 / F4: synthesis ----
# Interposer routers of this round. Their RTL depends on the size only through the coordinate width and the penalty, so the
# 3x3 routers are the 4x4 ones (XW 4, D 0).
R25 = [('LF_X', 0, 0, 1), ('LF_O', 0, 1, 1), ('DLY_X', 1, 0, 1), ('DLY_X', 1, 0, 0)]       # (name, MECH, ORDER_O, RS_PER_PORT)
SRC25 = [os.path.join(R18, 'router_core.v'), os.path.join(RTL, 'core25.v'), os.path.join(RTL, 'lb25_units.v'), os.path.join(RTL, 'router25_top.v')]
SRC18 = [os.path.join(R18, f) for f in ('router_core.v', 'lb_units.v', 'method_units.v', 'router_top.v')]
SRCCHIP = SRC18 + [os.path.join(RTL, 'chip25_top.v')]
ISIZES = ('2x2', '4x4')


def designs():
    out = []
    for z in ISIZES:
        for t in ('ipos5', 'ipos6'):
            hub = S.TYPES[t][1]
            for name, mech, oo, pp in R25:
                for ca, cm, cb in CUTS:
                    out.append(dict(tag='%s__%s__%s__%s__c%d%d%d' % (name, t, z, 'P' if pp else 'S', ca, cm, cb), top='router25_top', srcs=SRC25, design=name, rtype=t, size=z,
                                    form='P' if pp else 'S', cuts='%d%d%d' % (ca, cm, cb),
                                    params=dict(MECH=mech, ORDER_O=oo, DBIAS=H.dbias(z), HAS_HUB=hub, RS_PER_PORT=pp, CUT_A=ca, CUT_M=cm, CUT_B=cb, XW=H.XW[z], NOSEL=0)))
            # the relation without a selection: the route computation of a hop with one offered output, on its own
            for name, mech, oo, pp in (('REL_LF', 0, 0, 1), ('REL_DLY', 1, 0, 1), ('REL_DLY', 1, 0, 0)):
                out.append(dict(tag='%s__%s__%s__%s__c000' % (name, t, z, 'P' if pp else 'S'), top='router25_top', srcs=SRC25, design=name, rtype=t, size=z,
                                form='P' if pp else 'S', cuts='000',
                                params=dict(MECH=mech, ORDER_O=oo, DBIAS=0, HAS_HUB=hub, RS_PER_PORT=pp, CUT_A=0, CUT_M=0, CUT_B=0, XW=H.XW[z], NOSEL=1)))
    # references of round 18, synthesised again in this run: DeFT (every type and size), the LB-I heuristic (chiplet routers of
    # every size = the chiplet routers of this round where the penalty is 0; interposer routers in both forms)
    for z in S.SIZES:
        for t in S.TYPES:
            out.append(dict(tag='DeFT__%s__%s__S__c000' % (t, z), top='router_top', srcs=SRC18, design='DeFT', rtype=t, size=z, form='S', cuts='000', params=S.params(1, t, z, 0)))
            layer = S.TYPES[t][0]
            for pp in ((0,) if layer == 0 else (0, 1)):
                out.append(dict(tag='LBI18__%s__%s__%s__c000' % (t, z, 'P' if pp else 'S'), top='router_top', srcs=SRC18, design='LBI18', rtype=t, size=z,
                                form='P' if pp else 'S', cuts='000', params=S.params(6, t, z, pp)))
    # chiplet routers with the table of the default entry VL (2x2, where the penalty is 2)
    for t in ('chip5', 'chip6'):
        p18 = S.SIZES['2x2']
        out.append(dict(tag='CHIP25__%s__2x2__S__c000' % t, top='chip25_top', srcs=SRCCHIP, design='CHIP25', rtype=t, size='2x2', form='S', cuts='000',
                        params=dict(HAS_HUB=S.TYPES[t][1], C=p18['C'], GX=p18['GX'], XW=p18['XW'], KW=p18['KW'], F=p18['F'])))
    return out


def yosys_script(d, flat, odir):
    ch = ' '.join('-set %s %s' % kv for kv in d['params'].items())
    n, top = d['tag'], d['top']
    L = ['read_verilog -sv -I%s -I%s %s' % (RTL, R18, ' '.join(d['srcs'])), 'chparam %s %s' % (ch, top), 'hierarchy -top %s' % top,
         'flatten t:*pipe_reg* t:*pipe25*', 'synth -top %s' % top + (' -flatten' if flat else ''),
         'dfflibmap -liberty %s' % S.LIB, 'abc -liberty %s -D %d -constr %s' % (S.LIB, S.CLOCK_PS, os.path.join(S.RAW, 'abc.constr')),
         'opt_clean -purge', 'setundef -zero', 'hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 ZN', 'insbuf -buf BUF_X1 A Z',
         'tee -q -o %s stat -liberty %s -top %s' % (os.path.join(odir, n + '.stat.txt'), S.LIB, top),
         'tee -q -o %s stat -json -liberty %s -top %s' % (os.path.join(odir, n + '.stat.json'), S.LIB, top),
         'write_verilog -noattr -noexpr -nohex -nodec %s' % os.path.join(odir, n + '.net.v')]
    return NL.join(L) + NL


# Endpoint groups: registers found by the names of their output nets (the registers of this round carry the attribute v25r, which
# keeps their names through flattening; the round-18 registers are found by the names round 18 used and by the names their nets
# take in a flat netlist). Stage time of a group = arrival + setup = 1 ns - slack. OTHER = every register in no group;
# FROMLINK = the longest path that starts at a link input (in LF the first stage of the decision reads the head from the link).
GROUPS = [
    ('RA', '*.ra.g.r* *.va.g.r*'),                   # decision, after stage A (relation and static terms)
    ('RM', '*.rm.g.r* *.vm.g.r*'),                   # decision, after stage M (occupancies of the candidates)
    ('RB', '*.rb.g.r* *.vb.g.r*'),                   # decision, after stage B (candidate costs)
    ('DMEM', '*dec.dmem*'),                          # LF: the stored decision (end of the decision)
    ('DVAL', '*dec.dval* *dec.wsel* *dec.rsel*'),    # LF: valid bits and entry pointers of the stored decisions (set by the decision, cleared when the head leaves)
    ('OFFR', '*.off_r*'),                            # LF: route stage at the buffer front (the relation)
    ('ROUTE', '*ctl.out_port* *ctl.hdr* *ctl.out_vc* *core.hdr_v*'),      # route registers (DLY and the references: end of the route stage; LF: written in the VA stage)
    ('INFL', '*.infl*'),                             # DLY: decision in flight
    ('VASTATE', '*ctl.st* busy* *va.busy_r* *va.ovc*arb.ptr*'),           # VC allocation: input-VC state, output-VC state, arbiter pointers
    ('SA', '*sa.inp*arb.ptr* *sa.outp*arb.ptr* occ_report* *cc.c*n* out_flit* out_vc* out_valid* *xb.op*r*'),      # switch allocation, credit counters, crossbar registers
    ('MISC', 'rnd* *regs.d*k.r*'),                   # tie-break LFSR, the neighbours' reports registered on arrival
]
ALLGROUPS = [g for g, _ in GROUPS] + ['OTHER', 'FROMLINK']

STA_TCL = """
read_liberty {lib}
read_verilog {net}
link_design {top}
create_clock -name clk -period {period} [get_ports clk]
set_input_delay 0 -clock clk [lsearch -inline -all -not -exact [all_inputs] [get_ports clk]]
set_output_delay 0 -clock clk [all_outputs]
puts "ALL"
report_checks -path_delay max -format short -digits 4
puts "WNS_ALL [sta::worst_slack -max]"
set seen [dict create]
proc ends {{pat}} {{
    set out {{}}
    foreach n [get_nets -quiet [split $pat]] {{
        foreach p [get_pins -quiet -of_objects $n -filter "direction == output"] {{
            set c [get_cells -of_objects $p]
            set d [get_pins -quiet [get_full_name $c]/D]
            if {{[llength $d]}} {{ lappend out $d }}
        }}
    }}
    return $out
}}
proc rep {{name pat}} {{
    global seen
    set e [ends $pat]
    foreach p $e {{ dict set seen [get_full_name $p] 1 }}
    puts "GROUP $name [llength $e]"
    if {{[llength $e]}} {{
        report_checks -to $e -path_delay max -digits 4 -fields {{}}
    }}
}}
{reps}
set other {{}}
foreach p [all_registers -data_pins] {{
    if {{![dict exists $seen [get_full_name $p]]}} {{ lappend other $p }}
}}
puts "GROUP OTHER [llength $other]"
if {{[llength $other]}} {{
    report_checks -to $other -path_delay max -digits 4 -fields {{}}
}}
set lk [get_ports -quiet {{in_flit* in_valid* in_vc*}}]
puts "GROUP FROMLINK [llength $lk]"
if {{[llength $lk]}} {{
    report_checks -from $lk -path_delay max -digits 4 -fields {{}}
}}
puts "GROUP END 0"
exit
"""


def run_one(arg):
    d, flat = arg
    n = d['tag']
    odir = os.path.join(RAW, 'flat' if flat else 'hier')
    os.makedirs(odir, exist_ok=True)
    net = os.path.join(odir, n + '.net.v')
    resta = flat and os.environ.get('V25_RESTA') == '1'          # run the timing analysis again (new groups) from the kept netlist
    if os.path.exists(os.path.join(odir, n + ('.sta.txt' if flat else '.stat.json'))) and not resta:
        return n, True
    if resta and os.path.exists(net + '.gz') and os.path.exists(os.path.join(odir, n + '.stat.json')):
        subprocess.run(['gunzip', '-k', '-f', net + '.gz'], check=True)
    else:
        ys = os.path.join(odir, n + '.ys')
        open(ys, 'w').write(yosys_script(d, flat, odir))
        r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            return n, False
        if flat:
            subprocess.run(['gzip', '-k', '-f', net], check=True)      # the flat netlist is kept compressed
    if flat:
        reps = NL.join('rep %s {%s}' % g for g in GROUPS)
        tcl = os.path.join(odir, n + '.tcl')
        open(tcl, 'w').write(STA_TCL.format(lib=S.LIB, net=os.path.join(odir, n + '.net.v'), top=d['top'], period=S.CLOCK_PS / 1000.0, reps=reps))
        with open(os.path.join(odir, n + '.sta.tmp'), 'w') as o:
            subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tcl], stdout=o, stderr=subprocess.STDOUT, timeout=3600)
        os.replace(os.path.join(odir, n + '.sta.tmp'), os.path.join(odir, n + '.sta.txt'))
    if os.path.exists(os.path.join(odir, n + '.net.v')):
        os.remove(os.path.join(odir, n + '.net.v'))        # the netlists are large; the statistics and the timing report are kept
    return n, True


def synth(pattern):
    from multiprocessing import Pool
    S.constr_file()
    ds = [d for d in designs() if not pattern or re.search(pattern, d['tag'])]
    jobs = [(d, flat) for flat in (True, False) for d in ds]
    print('designs %d, runs %d' % (len(ds), len(jobs)), flush=True)
    with Pool(THREADS) as pool:
        res = pool.map(run_one, jobs, chunksize=1)
    bad = sorted({n for n, ok in res if not ok})
    print('synthesis: %d / %d runs done; failed: %s' % (len(res) - sum(1 for _, ok in res if not ok), len(res), bad))
    return not bad


# ---- parsing ----
CATS = [('ibuf', 'buffers'), ('xbar', 'crossbar'), ('vc_alloc', 'allocators'), ('sw_alloc', 'allocators'), ('ivc_ctrl', 'allocators'),
        ('credit_ctrs', 'allocators'), ('router_core', 'crossbar'), ('rr_arb', 'allocators'),
        ('lb25_dec', 'selection'), ('occ_regs', 'selection'), ('lb_sel', 'selection'),
        ('lb25_rel', 'routing'), ('lb25_single', 'routing'), ('lb25_fallback', 'fallback'), ('lb_route', 'routing'), ('rt_', 'routing'), ('vn_unit', 'routing'),
        ('xy_dir', 'routing'), ('cfg_table', 'tables'), ('ni_', 'ni'), ('near_vl', 'ni'), ('chip_index', 'ni')]


def cat_of(mod):
    parts = mod.split(chr(92))
    s = parts[1] if mod.startswith('$paramod') else parts[-1]
    for pre, c in CATS:
        if s.startswith(pre):
            return c
    return None


def parse_stat(path, areas, topname):
    """Area, cells and flip-flops per category; a cell inherits the category of its nearest categorised ancestor. Cells directly in the top
    module of a v25 interposer router are its stored decisions, offered-output registers, tie-break LFSR and glue ('top')."""
    mods = json.load(open(path))['modules']

    def walk(mod, cat, totals):
        info = mods[mod]
        c = cat_of(mod) or cat
        for ty, cnt in info['num_cells_by_type'].items():
            # a sub-module without parameters is listed without the leading backslash of its module name
            sub = ty if ty in mods else (chr(92) + ty if chr(92) + ty in mods else None)
            if sub:
                for _ in range(cnt):
                    walk(sub, c, totals)
            else:
                t = totals.setdefault(c, dict(area=0.0, cells=0, ffs=0))
                t['area'] += areas.get(ty, 0.0) * cnt
                t['cells'] += cnt
                if ty.startswith('DFF'):
                    t['ffs'] += cnt
    tops = [m for m in mods if m.lstrip(chr(92)) == topname or (m.startswith('$paramod') and m.split(chr(92))[1] == topname)]
    totals = {}
    walk(tops[0], 'top', totals)
    return totals


def group(txt, g):
    m = re.search(r'GROUP ' + g + r' (\d+)(.*?)GROUP ', txt, re.S)
    if not m or int(m.group(1)) == 0:
        return None, None
    d = re.search(r'(-?[0-9.]+)\s+data arrival time', m.group(2))
    s = re.search(r'(-?[0-9.]+)\s+slack', m.group(2))
    return (float(d.group(1)), float(s.group(1))) if d and s else (None, None)


def semi_script(d, odir):
    """Hierarchy kept for the router core only: the core (buffers, allocators, crossbar, input-VC state) is one module and everything
    around it (relation, decision units, stored decisions, the units of the references) is flattened into the top. Shared logic and
    constants are optimised within each of the two, not across the core's ports."""
    ch = ' '.join('-set %s %s' % kv for kv in d['params'].items())
    n, top = d['tag'], d['top']
    L = ['read_verilog -sv -I%s -I%s %s' % (RTL, R18, ' '.join(d['srcs'])), 'chparam %s %s' % (ch, top), 'hierarchy -top %s' % top,
         'setattr -mod -set keep_hierarchy 1 *router_core*', 'flatten', 'synth -top %s' % top,
         'dfflibmap -liberty %s' % S.LIB, 'abc -liberty %s -D %d -constr %s' % (S.LIB, S.CLOCK_PS, os.path.join(S.RAW, 'abc.constr')),
         'opt_clean -purge', 'setundef -zero', 'hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 ZN', 'insbuf -buf BUF_X1 A Z',
         'tee -q -o %s stat -liberty %s -top %s' % (os.path.join(odir, n + '.stat.txt'), S.LIB, top),
         'tee -q -o %s stat -json -liberty %s -top %s' % (os.path.join(odir, n + '.stat.json'), S.LIB, top)]
    return NL.join(L) + NL


def run_semi(d):
    n = d['tag']
    odir = os.path.join(RAW, 'semi')
    os.makedirs(odir, exist_ok=True)
    if os.path.exists(os.path.join(odir, n + '.stat.json')):
        return n, True
    ys = os.path.join(odir, n + '.ys')
    open(ys, 'w').write(semi_script(d, odir))
    r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', ys], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return n, r.returncode == 0


def synth_semi(pattern):
    from multiprocessing import Pool
    S.constr_file()
    ds = [d for d in designs() if not pattern or re.search(pattern, d['tag'])]
    print('designs %d' % len(ds), flush=True)
    with Pool(THREADS) as pool:
        res = pool.map(run_semi, ds, chunksize=1)
    bad = sorted(n for n, ok in res if not ok)
    print('core-kept synthesis: %d / %d runs done; failed: %s' % (len(res) - len(bad), len(res), bad))
    return not bad


def design_area(path):
    """The synthesis tool's own total of a netlist, and its module names."""
    j = json.load(open(path))
    return float(j['design']['area']), list(j['modules'])


def make_csv():
    areas = S.lib_areas()
    ar, br, tm = [], [], []
    bad_tot, kept = [], 0
    for d in designs():
        n = d['tag']
        base = dict(design=d['design'], rtype=d['rtype'], size=d['size'], form=d['form'], cuts=d['cuts'])
        fh = os.path.join(RAW, 'hier', n + '.stat.json')
        ff = os.path.join(RAW, 'flat', n + '.stat.json')
        fs = os.path.join(RAW, 'flat', n + '.sta.txt')
        fm = os.path.join(RAW, 'semi', n + '.stat.json')
        if os.path.exists(fh) and os.path.exists(ff):
            th, tf = parse_stat(fh, areas, d['top']), parse_stat(ff, areas, d['top'])
            row = dict(base, area_hier_um2=round(sum(x['area'] for x in th.values()), 3), area_flat_um2=round(sum(x['area'] for x in tf.values()), 3),
                       cells_hier=sum(x['cells'] for x in th.values()), ffs=sum(x['ffs'] for x in th.values()), ffs_flat=sum(x['ffs'] for x in tf.values()))
            for path, key in ((fh, 'area_hier_um2'), (ff, 'area_flat_um2')):      # every cell of the netlist is in the total
                if abs(design_area(path)[0] - row[key]) > 0.01:
                    bad_tot.append((n, key, design_area(path)[0], row[key]))
            row['area_semi_um2'] = ''
            if os.path.exists(fm):
                a, mods = design_area(fm)
                row['area_semi_um2'] = round(a, 3)
                kept += 1 if len(mods) == 2 else 0
            ar.append(row)
            for c, x in sorted(th.items()):
                br.append(dict(base, category=c, area_um2=round(x['area'], 3), cells=x['cells'], ffs=x['ffs']))
        if os.path.exists(fs):
            txt = open(fs).read()
            m = re.search(r'WNS_ALL (-?[0-9.e+-]+)', txt)
            row = dict(base, slack_all_ns=float(m.group(1)) if m else '')
            for g in ALLGROUPS:
                a, s = group(txt, g)
                m = re.search(r'GROUP ' + g + r' (\d+)', txt)
                row['n_' + g] = int(m.group(1)) if m else 0
                row['stage_' + g] = '' if s is None else round(S.CLOCK_PS / 1000.0 - s, 4)      # arrival + setup
            tm.append(row)
    for fn, rows in (('area_runs.csv', ar), ('breakdown_runs.csv', br), ('timing_runs.csv', tm)):
        if rows:
            with open(os.path.join(HW, fn), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
                w.writeheader()
                w.writerows(rows)
    print('area %d, breakdown %d, timing %d rows; designs %d' % (len(ar), len(br), len(tm), len(designs())))
    print('totals equal to the synthesis tool\'s own design area: %d of %d; core-kept netlists with exactly two modules: %d' % (2 * len(ar) - len(bad_tot), 2 * len(ar), kept))
    for x in bad_tot[:10]:
        print('  MISMATCH', x)
    if bad_tot:
        sys.exit(1)


def run_stage(stage, nproc, extra):
    if stage == 'f_mut':
        mutation()
    elif stage == 'f_synth':
        sys.exit(0 if synth(extra) else 1)
    elif stage == 'f_semi':
        sys.exit(0 if synth_semi(extra) else 1)
    elif stage == 'f_lat':
        sys.exit(0 if latency() else 1)
    elif stage == 'f_csv':
        make_csv()
    else:
        raise SystemExit(__doc__)
