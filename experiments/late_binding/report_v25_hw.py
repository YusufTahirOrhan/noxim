"""v25 Part F report: area and timing of the interposer routers of the final design.

Reads  results_v25_confirm/hw/area_runs.csv, breakdown_runs.csv, timing_runs.csv, functional_check.json, mutation_check.txt
       results_v18_area/area_runs.csv, timing_runs.csv (round 18, same flow), results_v21_fastsel/area_runs_cut1.csv (round 21)
Writes results_v25_confirm/report/summary_F.md, hw_area.csv, hw_system_area.csv, hw_timing.csv, hw/n_fast.json and the same three CSVs in paper_data/.

Conventions (hw/FINDINGS_hw.md, DECISIONS.md):
  * stage time = arrival + setup of the longest path into a group of registers (1 ns - slack), flat netlist, pre-layout, no wires;
  * a stage that starts on a link gets T_CQ added (the clock-to-output delay of the upstream output register, which the port-launched path does not contain);
  * decision path of LF: [stage registers RA / RM / RB if cut] and the stored decision (DMEM); the first stage starts on the link.
    Decision path of DLY: [RA / RM / RB if cut] and the route registers (ROUTE); the first stage starts at the buffer front;
  * a cut configuration fits a period T when every stage of the decision path is <= T on the four routers (ipos5, ipos6 x 2x2, 4x4)
    and, for LF, the route stage at the buffer front (OFFR) is too. L_dec = 1 + cuts of the fitting configuration with the fewest cuts
    (ties: the largest worst-case margin); N_fast = L_dec - 1;
  * LF: residual delay = max(0, L_dec - 2), the two cycles being the link cycle and the route cycle of the head (no sideband request from the
    upstream router). DLY: decision_delay = L_dec - 1;
  * T_ref of a router type and size = the longest stage of the DeFT router of that type and size, synthesised in the same run.
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V25_RES', os.path.join(HERE, 'results_v25_confirm'))
HW = os.path.join(RES, 'hw')
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
R18 = os.path.join(HERE, 'results_v18_area')
R21 = os.path.join(HERE, 'results_v21_fastsel')
NL = chr(10)
T_CQ = 0.11            # ns; DFF_X1 clock-to-output in these netlists is 0.09-0.11 ns
SIZES = ['2x2', '3x3', '4x4']
ISIZES = ['2x2', '4x4']
TYPES = ['chip5', 'chip6', 'ipos5', 'ipos6']
ITYPES = ['ipos5', 'ipos6']
COUNT = {'chip5': 12, 'chip6': 4, 'ipos5': 12, 'ipos6': 4}
TNAME = {'chip5': 'chiplet (5 ports)', 'chip6': 'boundary (6 ports)', 'ipos5': 'interposer (5 ports)', 'ipos6': 'interposer + VL (6 ports)'}
CUTS = ['000', '100', '010', '001', '110', '101', '011', '111']
CUTNAME = {'000': 'none', '100': 'A', '010': 'M', '001': 'B', '110': 'A, M', '101': 'A, B', '011': 'M, B', '111': 'A, M, B'}
D25 = [('LF_X', 'P', 'LF'), ('LF_O', 'P', 'LF'), ('DLY_X', 'P', 'DLY'), ('DLY_X', 'S', 'DLY')]
DNAME = {('LF_X', 'P'): 'LF, XY (main row)', ('LF_O', 'P'): 'LF, VN-split order (second row)', ('DLY_X', 'P'): 'DLY, XY, one unit per input port',
         ('DLY_X', 'S'): 'DLY, XY, one unit per router', ('REL_LF', 'P'): 'relation only, LF structure', ('REL_DLY', 'P'): 'relation only, DLY, per port',
         ('REL_DLY', 'S'): 'relation only, DLY, per router', ('DeFT', 'S'): 'DeFT', ('LBI18', 'S'): 'LB-I heuristic of round 18, one unit per router',
         ('LBI18', 'P'): 'LB-I heuristic of round 18, one unit per input port'}
CATS = ['buffers', 'crossbar', 'allocators', 'routing', 'selection', 'fallback', 'tables', 'ni', 'top']
CNAME = {'buffers': 'buffers', 'crossbar': 'crossbar', 'allocators': 'allocators', 'routing': 'relation', 'selection': 'decision units + reports',
         'fallback': 'fallback', 'tables': 'tables', 'ni': 'NI logic', 'top': 'stored decisions + glue'}


def fnum(v):
    return float(v) if v not in ('', None) else None


def load():
    area = {(r['design'], r['rtype'], r['size'], r['form'], r['cuts']): r for r in csv.DictReader(open(os.path.join(HW, 'area_runs.csv')))}
    tim = {(r['design'], r['rtype'], r['size'], r['form'], r['cuts']): r for r in csv.DictReader(open(os.path.join(HW, 'timing_runs.csv')))}
    brk = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(HW, 'breakdown_runs.csv'))):
        brk[(r['design'], r['rtype'], r['size'], r['form'], r['cuts'])][r['category']] = (float(r['area_um2']), int(r['ffs']))
    return area, tim, brk


def st(r, g):
    return fnum(r.get('stage_' + g, '')) if r else None


KINDS = ['hier', 'semi', 'flat']
KNAME = {'hier': 'hierarchy kept', 'semi': 'core kept', 'flat': 'flattened'}


def ar(area, d, t, z, f='S', c='000', kind='hier'):
    """Area of a design; the interposer routers of this round have no 3x3 netlist of their own (their RTL is the 4x4 one)."""
    if d not in ('DeFT', 'LBI18', 'CHIP25') and z == '3x3':
        z = '4x4'
    r = area.get((d, t, z, f, c))
    v = r.get('area_%s_um2' % kind, '') if r else ''
    return float(v) if v not in ('', None) else None


def kinds(area):
    """The synthesis variants every design has (the core-kept one is an extra run)."""
    return [k for k in KINDS if all(r.get('area_%s_um2' % k, '') not in ('', None) for r in area.values())]


def ff_note(area):
    """Flip-flops that flattening removes, for the note under the area tables."""
    def lost(d, f, c):
        v = [int(area[(d, t, z, f, c)]['ffs']) - int(area[(d, t, z, f, c)]['ffs_flat']) for t in ITYPES for z in ISIZES if (d, t, z, f, c) in area]
        return '%d-%d' % (min(v), max(v))
    return 'flip-flops removed by flattening: DeFT %s, LF with XY %s, DLY per router %s' % (lost('DeFT', 'S', '000'), lost('LF_X', 'P', '010'), lost('DLY_X', 'S', '110'))


def tref(tim, t, z):
    return 1.0 - float(tim[('DeFT', t, z, 'S', '000')]['slack_all_ns'])


def flow_spread(tim):
    """The largest difference of the longest stage between netlists of unchanged logic: the chiplet routers of round 18 with and without the
    tables of this round against DeFT's chiplet routers (their allocation stages, which set the longest stage, are the same logic)."""
    d = []
    for z in SIZES:
        for t in ('chip5', 'chip6'):
            base = 1.0 - float(tim[('DeFT', t, z, 'S', '000')]['slack_all_ns'])
            d += [abs(1.0 - float(tim[(m, t, z, 'S', '000')]['slack_all_ns']) - base) for m in ('LBI18', 'CHIP25') if (m, t, z, 'S', '000') in tim]
    return max(d)


def dec_stages(r, mech):
    """[(name, ns)] of the decision path of one router; the first stage of LF starts on the link."""
    a, m, b = (int(c) for c in r['cuts'])
    names = [g for g, on in (('RA', a), ('RM', m), ('RB', b)) if on] + ['DMEM' if mech == 'LF' else 'ROUTE']
    out = [(g, st(r, g)) for g in names]
    if mech == 'LF':
        g0, v0 = out[0]
        out[0] = (g0, max(v0, st(r, 'FROMLINK') + T_CQ))
    return out


def fit(tim, d, f, mech, cuts, mode):
    """(fits, worst margin, limiting (stage, router), per-router stage lists) of a cut configuration at 1 ns or at T_ref."""
    worst, lim, per = None, None, {}
    for z in ISIZES:
        for t in ITYPES:
            r = tim.get((d, t, z, f, cuts))
            if not r:
                return None
            T = 1.0 if mode == '1ns' else tref(tim, t, z)
            stages = dec_stages(r, mech)
            if mech == 'LF':
                stages = stages + [('OFFR', st(r, 'OFFR'))]
            per[(t, z)] = stages
            for g, v in stages:
                if worst is None or T - v < worst:
                    worst, lim = T - v, (g, t, z)
    return worst >= 0, worst, lim, per


def choose(tim, d, f, mech, mode):
    best = None
    for cuts in CUTS:
        x = fit(tim, d, f, mech, cuts, mode)
        if not x or not x[0]:
            continue
        n = sum(int(c) for c in cuts)
        if best is None or n < best[1] or (n == best[1] and x[1] > best[2]):
            best = (cuts, n, x[1], x[2])
    return best


def n_fast(tim):
    out = {}
    noise = flow_spread(tim)
    for d, f, mech in D25:
        e = {}
        for mode in ('1ns', 'ref'):
            b = choose(tim, d, f, mech, mode)
            if b is None:
                x = fit(tim, d, f, mech, '111', mode)
                e[mode] = dict(fits=False, cuts=None, limiting='%s on %s %s' % x[2], over_ns=round(-x[1], 4),
                               note='no configuration of the three cuts fits; the limiting stage itself would have to be cut')
            else:
                cuts, n, margin, lim = b
                L = 1 + n
                e[mode] = dict(fits=True, cuts=cuts, L_dec=L, N_fast=L - 1, worst_margin_ns=round(margin, 4), limiting='%s on %s %s' % lim,
                               marginal=margin < noise)
                if mech == 'LF':
                    e[mode]['residual'] = max(0, L - 2)
                else:
                    e[mode]['decision_delay'] = L - 1
        out['%s_%s' % (d, f)] = e
    return out


def functional():
    L = ['## F2: the RTL against the simulator', '']
    p = os.path.join(HW, 'functional_check.json')
    if not os.path.exists(p):
        return L + ['(functional_check.json missing)', '']
    j = json.load(open(p))
    L += ['Vectors dumped from simulator runs (an instrumented copy of the simulator whose statistics are byte-identical to `bin/noxim` on every run); a selection '
          'vector is applied to the decision unit with each of the 8 cut configurations. Details: `hw/functional_check.txt`.', '',
          '| design | simulator runs (identical to bin/noxim) | selection vectors | applied (x 8 cut configurations) | of them with more than one offered output | '
          'front vectors (relation, only output, fallback) | fallback evaluated / took another output | total distinct vectors | mismatches |',
          '|---|---|---|---|---|---|---|---|---|']
    for d, s in j['summary'].items():
        L.append('| %s | %d (%d) | %d | %d | %d | %d | %d / %d | **%d** | **%d** |' % (d, s['runs'], s['identical'], s['sel'], s['sel_applied'], s['multi'], s['front'],
                                                                                 s['fb'], s['fb_other'], s['sel'] + s['front'], s['mism']))
    ptr = j.get('pointer_checks')
    if ptr:
        L += ['', 'Tie break: for every selection vector the pointer of the rotating priority was swept over its five positions and the unit had to return the first '
              'output of least cost at or after it, wrapping (%d checks, in the mismatch counts above).' % ptr]
    L += ['', 'All three designs pass: **%s**.' % ('yes' if j.get('ok') else 'NO'), '']
    p = os.path.join(HW, 'mutation_check.txt')
    if os.path.exists(p):
        txt = open(p).read().splitlines()
        L += [x for x in txt if x.startswith('**') or x.startswith('Not caught')] + ['']
    return L


def area_tables(area, nf):
    ks = kinds(area)
    L = ['## F3: area (NanGate45 typical, Yosys + ABC at 1 GHz; um^2: %s; in brackets relative to DeFT of the same type and size)' % ' / '.join(KNAME[k] for k in ks), '',
         '* **Hierarchy kept** (the primary figure, as in round 18): every unit is synthesised on its own. Nothing is shared between the relation units of the input '
         'VCs and the decision units, so it is an upper bound for the designs of this round.',
         '* **Core kept**: the router core (buffers, allocators, crossbar, input-VC state) stays one module and everything around it is flattened into the top. Logic '
         'is shared and constants are propagated within the routing and selection logic, not across the ports of the core.',
         '* **Flattened**: no module boundary. For the designs of this round this also removes logic of the core that the relation can never ask for (the Local '
         'output port of an interposer router, turns the dimension order forbids; %s). The DeFT RTL of round 18 does not express that its interposer router never '
         'uses the Local output either, so this figure favours the designs of this round and is reported for completeness only.' % ff_note(area), '']
    cfg = {}          # (design, form) -> cut configurations shown
    for d, f, mech in D25:
        e = nf['%s_%s' % (d, f)]
        cs = ['000']
        for mode in ('ref', '1ns'):
            if e[mode].get('cuts') and e[mode]['cuts'] not in cs:
                cs.append(e[mode]['cuts'])
        if mech == 'DLY' and '110' not in cs:
            cs.append('110')      # the evaluated row: decision_delay 2
        cfg[(d, f)] = cs
    rows = []
    v21 = {}
    p = os.path.join(R21, 'area_runs_cut1.csv')
    if os.path.exists(p):
        v21 = {(r['method'], r['rtype'], r['size'], r['form']): float(r['area_um2']) for r in csv.DictReader(open(p))}
    for z in ISIZES:
        L += ['### %s' % z, '', '| design | cuts | ' + ' | '.join(TNAME[t] for t in ITYPES) + ' |', '|---|---|---|---|']

        def line(name, d, f, c):
            cells = []
            for t in ITYPES:
                v = [ar(area, d, t, z, f, c, k) for k in ks]
                b = [ar(area, 'DeFT', t, z, kind=k) for k in ks]
                cells.append(' / '.join('%.0f' % x for x in v) + ' (' + ' / '.join('%.3f' % (x / y) for x, y in zip(v, b)) + ')')
                row = dict(size=z, rtype=t, design=d, form=f, cuts=c)
                for k, x, y in zip(ks, v, b):
                    row['area_%s_um2' % k] = round(x, 1)
                    row['rel_deft_%s' % k] = round(x / y, 4)
                rows.append(row)
            L.append('| %s | %s | ' % (name, CUTNAME[c]) + ' | '.join(cells) + ' |')
        line('DeFT', 'DeFT', 'S', '000')
        line(DNAME[('LBI18', 'S')], 'LBI18', 'S', '000')
        line(DNAME[('LBI18', 'P')], 'LBI18', 'P', '000')
        for m, f, nm in (('LBI_fast', 'S', 'fast selection of round 21, per router (its table: hierarchy kept)'), ('LBI_fast', 'P', 'fast selection of round 21, per input port (its table: hierarchy kept)')):
            if (m, 'ipos5', z, f) in v21:
                L.append('| %s | its cut | ' % nm + ' | '.join('%.0f (%.3f)' % (v21[(m, t, z, f)], v21[(m, t, z, f)] / ar(area, 'DeFT', t, z)) for t in ITYPES) + ' |')
        for d, f in (('REL_LF', 'P'), ('REL_DLY', 'P'), ('REL_DLY', 'S')):
            line(DNAME[(d, f)], d, f, '000')
        for d, f, mech in D25:
            for c in cfg[(d, f)]:
                line(DNAME[(d, f)], d, f, c)
        L.append('')
    L += ['### Chiplet routers (um^2: %s; in brackets relative to DeFT)' % ' / '.join(KNAME[k] for k in ks), '',
          'The late-binding designs of this round do not route in the chiplets: their chiplet router is DeFT\'s with the exit LUT of round 18 (the LB-I chiplet router '
          'of rounds 18 and 21) and, on 2x2 only, the table of the default entry VL. The entry mask and the default VL pass through as header bits.', '',
          '| size | design | ' + ' | '.join(TNAME[t] for t in ('chip5', 'chip6')) + ' |', '|---|---|---|---|']
    for z in SIZES:
        for name, d in (('DeFT', 'DeFT'), ('chiplet router of rounds 18 and 21 (exit LUT)', 'LBI18'), ('this round on 2x2: with the default-entry table', 'CHIP25')):
            if ar(area, d, 'chip5', z) is None:
                continue
            cells = []
            for t in ('chip5', 'chip6'):
                v = [ar(area, d, t, z, kind=k) for k in ks]
                b = [ar(area, 'DeFT', t, z, kind=k) for k in ks]
                cells.append(' / '.join('%.0f' % x for x in v) + ' (' + ' / '.join('%.3f' % (x / y) for x, y in zip(v, b)) + ')')
                row = dict(size=z, rtype=t, design=d, form='S', cuts='000')
                for k, x, y in zip(ks, v, b):
                    row['area_%s_um2' % k] = round(x, 1)
                    row['rel_deft_%s' % k] = round(x / y, 4)
                rows.append(row)
            L.append('| %s | %s | ' % (z, name) + ' | '.join(cells) + ' |')
    L.append('')
    return L, rows, cfg


def system(area, d, f, c, z, kind):
    """Average router area of a system: 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL routers per chiplet."""
    tot = 0.0
    for t in TYPES:
        if d == 'DeFT':
            v = ar(area, 'DeFT', t, z, kind=kind)
        elif t.startswith('chip'):
            # chiplet routers of the late-binding designs: the LB-I chiplet router of round 18 (exit LUT); on 2x2 with the default-entry table (D = 2)
            v = ar(area, 'CHIP25', t, z, kind=kind) if (d != 'LBI18' and z == '2x2') else ar(area, 'LBI18', t, z, kind=kind)
        else:
            v = ar(area, d, t, z, f, c, kind)
        tot += COUNT[t] * v
    return tot / 32.0


def system_table(area, cfg):
    ks = kinds(area)
    L = ['### System level: average router area relative to DeFT (%s)' % ' / '.join(KNAME[k] for k in ks), '',
         'Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL routers. Chiplet routers of the late-binding designs: the chiplet router of '
         'round 18 with the exit LUT; on 2x2, where the default-VL penalty is used (D = 2), with the table of the default entry VL (16 (C - 1) x 2 bits) in addition. '
         'The 3x3 interposer routers are the 4x4 ones (the RTL depends on the size through the coordinate width and D only).', '',
         '| design | cuts | ' + ' | '.join(SIZES) + ' |', '|---|---|' + '---|' * len(SIZES)]
    rows = []

    def line(name, d, f, c):
        cells = []
        for z in SIZES:
            row = dict(design=d, form=f, cuts=c, size=z)
            rel = []
            for k in ks:
                v, b = system(area, d, f, c, z, k), system(area, 'DeFT', 'S', '000', z, k)
                rel.append(v / b)
                row['system_um2_%s' % k] = round(v, 1)
                row['rel_deft_%s' % k] = round(v / b, 4)
            cells.append(' / '.join('%.3f' % x for x in rel))
            rows.append(row)
        L.append('| %s | %s | ' % (name, CUTNAME[c]) + ' | '.join(cells) + ' |')
    line('DeFT', 'DeFT', 'S', '000')
    line(DNAME[('LBI18', 'S')], 'LBI18', 'S', '000')
    line(DNAME[('LBI18', 'P')], 'LBI18', 'P', '000')
    for d, f, mech in D25:
        for c in cfg[(d, f)]:
            line(DNAME[(d, f)], d, f, c)
    nch = {'2x2': 4, '3x3': 9, '4x4': 16}
    L += ['', 'All routers of a system (mm^2, hierarchy kept; %s routers):' % ', '.join('%s %d' % (z, 32 * nch[z]) for z in SIZES), '',
          '| design | cuts | ' + ' | '.join(SIZES) + ' |', '|---|---|' + '---|' * len(SIZES)]
    items = [('DeFT', 'DeFT', 'S', '000'), (DNAME[('LBI18', 'S')], 'LBI18', 'S', '000')]
    for d, f, mech in D25:
        items += [(DNAME[(d, f)], d, f, c) for c in cfg[(d, f)]]
    for name, d, f, c in items:
        cells = []
        for z in SIZES:
            tot = system(area, d, f, c, z, 'hier') * 32 * nch[z] / 1e6
            ref = system(area, 'DeFT', 'S', '000', z, 'hier') * 32 * nch[z] / 1e6
            cells.append('%.3f (%+.3f)' % (tot, tot - ref))
            for r in rows:
                if r['design'] == d and r['form'] == f and r['cuts'] == c and r['size'] == z:
                    r['system_total_mm2_hier'] = round(tot, 4)
        L.append('| %s | %s | ' % (name, CUTNAME[c]) + ' | '.join(cells) + ' |')
    return L + [''], rows


def breakdown_table(area, brk, cfg):
    L = ['### Where the area is (hierarchy kept, um^2 and flip-flops)', '']
    for z in ISIZES:
        for t in ITYPES:
            L += ['%s, %s:' % (z, TNAME[t]), '', '| design | cuts | total | FF | ' + ' | '.join(CNAME[c] for c in CATS) + ' |', '|---|---|---|---|' + '---|' * len(CATS)]
            items = [('DeFT', 'S', '000'), ('LBI18', 'S', '000'), ('REL_LF', 'P', '000')]
            for d, f, mech in D25:
                items += [(d, f, c) for c in cfg[(d, f)][1:2] or cfg[(d, f)][:1]]
            for d, f, c in items:
                b = brk.get((d, t, z, f, c))
                if not b:
                    continue
                tot = sum(x[0] for x in b.values())
                ff = sum(x[1] for x in b.values())
                L.append('| %s | %s | %.0f | %d | ' % (DNAME[(d, f)], CUTNAME[c], tot, ff) + ' | '.join('%.0f (%d)' % b[k] if k in b else '-' for k in CATS) + ' |')
            L.append('')
    return L


def timing_tables(tim, nf):
    L = ['## F4: timing (OpenSTA on the flattened netlists, pre-layout, ideal clock, no wires; ns)', '',
         'Stage time = arrival + setup of the longest path into a group of registers. **T_ref** = the longest stage of the DeFT router of the same type and size '
         'in the same run: its clock period in this flow. Margins below %.2f ns (the spread of this flow on unchanged logic, see the chiplet routers below) are '
         'called marginal.' % flow_spread(tim), '',
         '| router | size | T_ref | its longest stage | route stage (XY to the VL) | VC allocation | switch allocation + crossbar | link stage (buffer write) + T_CQ |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        for t in ITYPES:
            r = tim[('DeFT', t, z, 'S', '000')]
            groups = {g: st(r, g) for g in ('ROUTE', 'VASTATE', 'SA', 'OTHER')}
            g = max((v, k) for k, v in groups.items() if v is not None)[1]
            L.append('| %s | %s | %.2f | %s | %.2f | %.2f | %.2f | %.2f |' % (TNAME[t], z, tref(tim, t, z), {'ROUTE': 'route', 'VASTATE': 'VC allocation', 'SA': 'switch allocation', 'OTHER': 'other'}[g],
                                                                           st(r, 'ROUTE'), st(r, 'VASTATE'), st(r, 'SA'), st(r, 'FROMLINK') + T_CQ))
    L += ['', 'T_CQ = %.2f ns is added to every stage that starts on a link: the clock-to-output delay of the upstream output register, which a path launched at an '
          'input port does not contain. Link wires have no delay in this flow.' % T_CQ, '']
    rows = []
    for d, f, mech in D25:
        L += ['### Decision path: %s' % DNAME[(d, f)], '']
        if mech == 'LF':
            L += ['Stages: the head is read on the link (first stage), registers after stage A / M / B where cut, the stored decision at the end. Each cell: the longest '
                  'stage over the four routers (ipos5, ipos6 x 2x2, 4x4) as first stage / middle stages / last stage. Route at the front = the relation of the head at the '
                  'buffer front into its offered-output register (every head). Residual = max(0, L_dec - 2).', '']
        else:
            L += ['Stages: the head is read at the buffer front (first stage), registers after stage A / M / B where cut, the route registers at the end (also the end '
                  'of the one-cycle route of a hop with one offered output). decision_delay = L_dec - 1.', '']
        L += ['| cuts | L_dec | first stage | middle stages | last stage |' + (' route at the front |' if mech == 'LF' else '') + ' fits 1 ns (margin) | fits T_ref (margin) | ' +
              ('residual' if mech == 'LF' else 'decision_delay') + ' |', '|---|---|---|---|---|' + ('---|' if mech == 'LF' else '') + '---|---|---|']
        for cuts in CUTS:
            x1, xr = fit(tim, d, f, mech, cuts, '1ns'), fit(tim, d, f, mech, cuts, 'ref')
            if not x1:
                continue
            per = x1[3]
            n = sum(int(c) for c in cuts)
            nst = n + 1
            first = max(per[k][0][1] for k in per)
            last = max(per[k][nst - 1][1] for k in per) if nst > 1 else None
            mids = [max(per[k][i][1] for k in per) for i in range(1, nst - 1)]
            offr = max(per[k][-1][1] for k in per) if mech == 'LF' else None
            cell = '| %s | %d | %.2f | %s | %s |' % (CUTNAME[cuts], n + 1, first, ', '.join('%.2f' % v for v in mids) if mids else '-', '%.2f' % last if last is not None else '(the first)')
            if mech == 'LF':
                cell += ' %.2f |' % offr
            cell += ' %s (%+.2f) | %s (%+.2f) | %d |' % ('yes' if x1[0] else 'no', x1[1], 'yes' if xr[0] else 'no', xr[1], max(0, n - 1) if mech == 'LF' else n)
            L.append(cell)
            for (t, z), stages in per.items():
                row = dict(design=d, form=f, mechanism=mech, cuts=cuts, L_dec=n + 1, rtype=t, size=z, T_ref=round(tref(tim, t, z), 4))
                for i, (g, v) in enumerate(stages):
                    row['stage%d' % (i + 1)] = '%s:%.4f' % (g, v)
                row['worst_stage_ns'] = round(max(v for _, v in stages), 4)
                row['fits_1ns'] = int(all(v <= 1.0 for _, v in stages))
                row['fits_T_ref'] = int(all(v <= tref(tim, t, z) for _, v in stages))
                rows.append(row)
        e = nf['%s_%s' % (d, f)]
        for mode, nm in (('1ns', '1 ns'), ('ref', 'T_ref')):
            m = e[mode]
            if m['fits']:
                tail = ('residual %d' % m['residual']) if mech == 'LF' else ('decision_delay %d' % m['decision_delay'])
                L.append('')
                L.append('At %s: **L_dec = %d, N_fast = %d** (cuts: %s; worst margin %+.2f ns, on %s%s); %s.' % (
                    nm, m['L_dec'], m['N_fast'], CUTNAME[m['cuts']], m['worst_margin_ns'], m['limiting'],
                    '; inside the spread of the flow, %.2f ns' % flow_spread(tim) if m['marginal'] else '', tail))
            else:
                L.append('')
                L.append('At %s: **no configuration of the three cuts fits** (with all three cuts %s is %.2f ns over): that stage itself would have to be cut, '
                         'which this RTL does not do.' % (nm, m['limiting'], m['over_ns']))
        L.append('')
    return L, rows


def other_paths(tim, nf):
    """Single-output route, the fallback in the VA stage, the valid bits, and the period of the whole router against T_ref."""
    L = ['### Route of a hop with one offered output, the fallback, and the period of the whole router', '',
         'Per router: stage / T_ref of the same type and size. Route, one output: LF = the relation into the offered-output register (then the VC allocation asks for '
         'the only output); DLY and relation-only designs = the relation into the route registers. VC-allocation stage: for LF it contains the fallback (stored '
         'decision, free outputs, the request, the allocator, the route registers written at the grant). Valid bits: the bookkeeping of the stored decisions (set by '
         'the decision, cleared when the head leaves, i.e. behind the switch allocation). Whole router: its longest stage.', '',
         '| design | cuts | router | size | T_ref | link stage + T_CQ | left in the link cycle for the wire | route, one output | VC-allocation stage | valid bits of the stored decisions | switch allocation | whole router | whole router / T_ref |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    rows = []
    items = [('DeFT', 'S', '000', 'REF'), ('REL_LF', 'P', '000', 'LF'), ('REL_DLY', 'P', '000', 'DLY'), ('REL_DLY', 'S', '000', 'DLY')]
    for d, f, mech in D25:
        e = nf['%s_%s' % (d, f)]
        c = e['ref'].get('cuts') or '111'
        items.append((d, f, c, mech))
        if mech == 'DLY' and c != '110':
            items.append((d, f, '110', mech))
    ratios, left = defaultdict(list), defaultdict(list)
    for d, f, c, mech in items:
        for z in ISIZES:
            for t in ITYPES:
                r = tim.get((d, t, z, f, c))
                if not r:
                    continue
                T = tref(tim, t, z)
                route1 = st(r, 'OFFR') if mech == 'LF' else st(r, 'ROUTE')
                va = max(v for v in (st(r, 'VASTATE'), st(r, 'ROUTE') if mech == 'LF' else None) if v is not None)
                dv = st(r, 'DVAL')
                whole = 1.0 - float(r['slack_all_ns'])
                ratios[(d, f, c)].append(whole / T)
                link = st(r, 'FROMLINK') + T_CQ
                left[(d, f, c)].append(T - link)
                L.append('| %s | %s | %s | %s | %.2f | %.2f | %.2f | %.2f | %.2f | %s | %.2f | %.2f | %.3f |' % (DNAME[(d, f)], CUTNAME[c], t, z, T, link, T - link, route1, va,
                                                                                                     '%.2f' % dv if dv is not None else '-', st(r, 'SA'), whole, whole / T))
                rows.append(dict(design=d, form=f, cuts=c, rtype=t, size=z, T_ref=round(T, 4), route_one_output=route1, va_stage=va, valid_bits=dv if dv is not None else '',
                                 switch_alloc=st(r, 'SA'), from_link_plus_tcq=round(st(r, 'FROMLINK') + T_CQ, 4), whole_router=round(whole, 4), whole_over_T_ref=round(whole / T, 4)))
    L += ['', 'Whole router / T_ref, range over the four routers: ' + '; '.join('%s%s %.3f - %.3f' % (DNAME[(d, f)], '' if c == '000' else ' (cuts %s)' % CUTNAME[c], min(v), max(v))
                                                                     for (d, f, c), v in ratios.items() if d != 'DeFT') + '.', '',
          'Link stage = the longest path that starts on a link (DeFT, DLY: the buffer write; LF: the first stage of the decision) plus T_CQ. Left in the link cycle for '
          'the wire, range over the four routers: ' + '; '.join('%s%s %.2f - %.2f ns' % (DNAME[(d, f)], '' if c == '000' else ' (cuts %s)' % CUTNAME[c], min(v), max(v))
                                                                 for (d, f, c), v in left.items() if not d.startswith('REL')) + '.', '']
    return L, rows


def chip_table(tim):
    L = ['### Chiplet routers (unchanged logic; longest stage, ns)', '',
         'The chiplet routers of the late-binding designs are those of round 18 (exit LUT); on 2x2 the table of the default entry VL is added at the NI. Their '
         'allocation stages are those of DeFT; the differences below are the spread of the flow on unchanged logic.', '',
         '| size | router | DeFT | chiplet router of round 18 (exit LUT) | with the default-entry table (2x2) |', '|---|---|---|---|---|']
    spread = []
    for z in SIZES:
        for t in ('chip5', 'chip6'):
            v = [1.0 - float(tim[(d, t, z, 'S', '000')]['slack_all_ns']) if (d, t, z, 'S', '000') in tim else None for d in ('DeFT', 'LBI18', 'CHIP25')]
            spread += [x - v[0] for x in v[1:] if x is not None]
            L.append('| %s | %s | ' % (z, TNAME[t]) + ' | '.join('%.2f' % x if x is not None else '-' for x in v) + ' |')
    L += ['', 'Difference to DeFT over these netlists: %+.2f to %+.2f ns. The largest, %.2f ns, is taken as the spread of the flow: a margin below it is called marginal.'
          % (min(spread), max(spread), flow_spread(tim)), '']
    return L


def latency_lines():
    p = os.path.join(HW, 'latency_check.txt')
    if not os.path.exists(p):
        return []
    rows = [x.split('|') for x in open(p).read().splitlines() if x.startswith('| ') and not x.startswith('| design')]
    last = [x for x in open(p).read().splitlines() if x.startswith('configurations')]
    by = defaultdict(set)
    for r in rows:
        c = [x.strip() for x in r[1:-1]]
        name = c[0].rsplit('_', 1)[0]
        rng = lambda x: x.split(',')[1].strip()  # noqa: E731
        one = lambda x: x.split('-')[0] if len(set(x.split('-'))) == 1 else x  # noqa: E731
        by[(name, c[1], c[2], c[4])].add((one(rng(c[6])), one(rng(c[7])), c[9]))
    L = ['### Cycles through the router, measured in RTL simulation (`hw/latency_check.txt`)', '',
         'A two-flit packet into an idle router; cycles from the head on the input link to the head on the output link. The reference pipeline is link + buffer '
         'write, route, VC allocation, switch allocation + crossbar: 4 cycles. Both sizes, routers with and without an Up link.', '',
         '| design | mechanism | units | cuts (A M B) | head with one offered output | head with a choice | as the rule says |', '|---|---|---|---|---|---|---|']
    for (name, mech, units, cuts), v in by.items():
        one = sorted({x[0] for x in v})
        ch = sorted({x[1] for x in v})
        ok = all(x[2] == 'OK' for x in v)
        L.append('| %s | %s | %s | %s | %s | %s | %s |' % (name, mech, units, cuts, ', '.join(one), ', '.join(ch), 'yes' if ok else '**no**'))
    return L + [''] + last + ['']


def write_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)
    area, tim, brk = load()
    nf = n_fast(tim)
    json.dump(nf, open(os.path.join(HW, 'n_fast.json'), 'w', newline=NL), indent=1)
    L = ['# Part F: hardware of the final design (interposer router; NanGate45, Yosys + ABC, OpenSTA)', '']
    L += functional()
    a_l, a_rows, cfg = area_tables(area, nf)
    s_l, s_rows = system_table(area, cfg)
    t_l, t_rows = timing_tables(tim, nf)
    o_l, o_rows = other_paths(tim, nf)
    L += a_l + s_l + breakdown_table(area, brk, cfg) + t_l + latency_lines() + o_l + chip_table(tim)
    L += ['### Measured decision latency (`hw/n_fast.json`)', '', '| design | at 1 ns: cuts, L_dec, N_fast | at T_ref: cuts, L_dec, N_fast | consequence at T_ref |', '|---|---|---|---|']
    for d, f, mech in D25:
        e = nf['%s_%s' % (d, f)]

        def cell(m):
            return '%s, %d, %d%s' % (CUTNAME[m['cuts']], m['L_dec'], m['N_fast'], ' (marginal)' if m['marginal'] else '') if m['fits'] else 'does not fit with three cuts'
        m = e['ref']
        cons = '-' if not m['fits'] else ('residual %d' % m['residual'] if mech == 'LF' else 'decision_delay %d' % m['decision_delay'])
        L.append('| %s | %s | %s | %s |' % (DNAME[(d, f)], cell(e['1ns']), cell(m), cons))
    L.append('')
    open(os.path.join(OUT, 'summary_F.md'), 'w', newline=NL).write(NL.join(L) + NL)
    for fn, rows in (('hw_area.csv', a_rows), ('hw_system_area.csv', s_rows), ('hw_timing.csv', t_rows), ('hw_paths.csv', o_rows)):
        write_csv(os.path.join(OUT, fn), rows)
        write_csv(os.path.join(PD, fn), rows)
    print(NL.join(L))


if __name__ == '__main__':
    main()
