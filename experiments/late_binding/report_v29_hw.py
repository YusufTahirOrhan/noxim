"""v29 Part E report (hardware): E3 the references with more buffers, E2 the two RTL variants of the interposer router, E4 power.

Usage: python report_v29_hw.py [e3] [e2] [e4]      (no argument: every part whose inputs exist)
Reads  results_v29_review/hw/area_buffers.csv, system_ratios.csv, buffer_core_check.txt                       (E3)
       hw/area_variants.csv, timing_variants.csv, functional_check_variants.json, router_smoke_variants.txt,
       latency_check_variants.txt                                                                            (E2)
       hw/port_loads.csv, power_runs.csv                                                                     (E4)
       results_v25_confirm/report/hw_system_area.csv (the main row's ratios of round 25, for comparison)
Writes results_v29_review/report/summary_hw_E3.md, summary_hw_E2.md, summary_hw_E4.md, hw_timing_variants.csv, hw_power.csv
       and paper_data/hw_variants.csv (once E2 exists; the power columns once E4 exists).
Conventions are those of round 25 (report_v25_hw.py, whose functions are used): stage time = arrival + setup of the longest path into a
group of registers on the flattened netlist; a stage that starts on a link gets T_CQ added; T_ref of a router type and size = the longest
stage of DeFT's router of that type and size, synthesised in the same run; a cut configuration fits a period when every stage of the
decision path and the route stage at the buffer front fit on the four interposer routers; L_dec = 1 + its cuts; residual = max(0, L_dec - 2).
"""
import csv
import json
import os
import sys

import report_v25_hw as RV

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V29_RES', os.path.join(HERE, 'results_v29_review'))
HW = os.path.join(RES, 'hw')
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
V25 = os.path.join(HERE, 'results_v25_confirm')
NL = chr(10)
SIZES = ['2x2', '3x3', '4x4']
TYPES = ['chip5', 'chip6', 'ipos5', 'ipos6']
ITYPES = ['ipos5', 'ipos6']
COUNT = {'chip5': 12, 'chip6': 4, 'ipos5': 12, 'ipos6': 4}
FORMS = ['hier', 'semi', 'flat']
FNAME = {'hier': 'hierarchy kept', 'semi': 'core kept', 'flat': 'flattened'}
TNAME = RV.TNAME
VARS = [('LF_main', 'main row'), ('LF_noVLrep', '`LB_noVLrep`: no reports across the VLs'), ('LF_noLA', '`LB_noLA`: no reports at all')]
VLABEL = {'LF_main': 'main', 'LF_noVLrep': 'LB_noVLrep', 'LF_noLA': 'LB_noLA'}
T_CQ = RV.T_CQ


def write(name, L):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)
    print('wrote report/%s (%d lines)' % (name, len(L)))


def write_csv(path, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator=NL, restval='')
        w.writeheader()
        w.writerows(rows)


def have(*names):
    return all(os.path.exists(os.path.join(HW, n)) for n in names)


def rd(name):
    return list(csv.DictReader(open(os.path.join(HW, name))))


# =====================================================================================================================
# E3: the references with more buffers
# =====================================================================================================================
def e3_data():
    A = {(r['design'], r['rtype'], r['size']): r for r in rd('area_buffers.csv')}
    SR = {(r['design'], r['size'], r['form']): float(r['ratio']) for r in rd('system_ratios.csv')}
    return A, SR


def depth_equal(SR, z, f):
    """The buffer depth at which DeFT's routers have the main row's area: linear between the measured depths 4, 5 and 6 (beyond 6 with
    the step from 5 to 6)."""
    m, d5, d6 = SR[('main', z, f)], SR[('d5', z, f)], SR[('d6', z, f)]
    if m <= d5:
        return 4.0 + (m - 1.0) / (d5 - 1.0)
    return 5.0 + (m - d5) / (d6 - d5)


def v25_main():
    p = os.path.join(V25, 'report', 'hw_system_area.csv')
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            if (r['design'], r['form'], r['cuts']) == ('LF_X', 'P', '010'):
                out[r['size']] = {f: float(r['rel_deft_%s' % f]) for f in FORMS if r.get('rel_deft_%s' % f)}
    return out


def part_e3():
    A, SR = e3_data()
    chk = open(os.path.join(HW, 'buffer_core_check.txt')).read().splitlines() if have('buffer_core_check.txt') else []
    L = ['# v29 E3: the references with more buffers (report_v29_hw.py e3)', '',
         'DeFT\'s four routers with 5-flit and 6-flit input buffers, and with 7-flit buffers in the interposer routers only, synthesised with the flow of round 25',
         '(NanGate45 typical, Yosys + ABC at 1 GHz) in its three forms, in one run with DeFT at depth 4 and with the main row. RTL: `hw/rtl/router_core29.v`, the',
         'reference core of round 18 with the depths as macros; `DeFT_d4` is the core of round 18 unchanged, `DeFT_d4c` the new core at depth 4.', '',
         'Functional check of the depths (`hw/buffer_core_check.txt`): ' + (chk[-1] if chk else 'not run') + '.', '',
         '## E3.1 Area of a router (um^2 at depth 4; the others relative to depth 4 of the same router, form and size)', '']
    for f in FORMS:
        L += ['### %s' % FNAME[f], '', '| size | router | depth 4 (um^2) | new core at depth 4 | depth 5 | depth 6 | interposer depth 7 | buffers at depth 4 (share of the router) |', '|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            for t in TYPES:
                b = float(A[('DeFT_d4', t, z)]['area_%s_um2' % f])
                cell = []
                for d in ('DeFT_d4c', 'DeFT_d5', 'DeFT_d6', 'DeFT_i7'):
                    r = A.get((d, t, z))
                    cell.append('%.3f' % (float(r['area_%s_um2' % f]) / b) if r else ('1.000 (the router of depth 4)' if d == 'DeFT_i7' else '-'))
                bh = A[('DeFT_d4', t, z)]
                share = float(bh['buffers_hier_um2']) / float(bh['area_hier_um2'])
                L.append('| %s | %s | %.0f | %s | %s |' % (z, TNAME[t], b, ' | '.join(cell), '%.1f %%' % (100 * share) if f == 'hier' else ''))
        L.append('')
    old = v25_main()
    L += ['## E3.2 System: average router area relative to DeFT at depth 4 (%s)' % ' / '.join(FNAME[f] for f in FORMS), '',
          'Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers (round 25). The main row: its interposer routers (one register in',
          'the decision unit, after stage M; the 3x3 routers are the 4x4 ones) and the chiplet routers of round 25.', '',
          '| design | ' + ' | '.join(SIZES) + ' |', '|---|' + '---|' * len(SIZES)]
    names = [('d4c', 'DeFT, new core at depth 4'), ('d5', 'DeFT, 5-flit buffers (`X_d5`)'), ('d6', 'DeFT, 6-flit buffers (`X_d6`)'), ('i7', 'DeFT, 7-flit buffers in the interposer routers (`X_i7`)'),
             ('main', 'main row, this run')]
    for key, nm in names:
        L.append('| %s | ' % nm + ' | '.join(' / '.join('%.3f' % SR[(key, z, f)] for f in FORMS) for z in SIZES) + ' |')
    if old:
        L.append('| main row, round 25 (`results_v25_confirm/report/hw_system_area.csv`) | ' + ' | '.join(' / '.join('%.3f' % old[z][f] if f in old.get(z, {}) else '-' for f in FORMS) for z in SIZES) + ' |')
    L += ['', '## E3.3 Which buffer depth gives a reference the main row\'s area', '',
          'The depth at which DeFT\'s system area equals the main row\'s, read from the measured depths 4, 5 and 6 by linear interpolation (beyond 6: with the step',
          'from 5 to 6). MTR and RC have DeFT\'s routers plus their own small units (round 18), so the same depths are taken for them.', '',
          '| form | ' + ' | '.join(SIZES) + ' |', '|---|' + '---|' * len(SIZES)]
    rows = []
    for f in FORMS:
        L.append('| %s | ' % FNAME[f] + ' | '.join('%.1f flits' % depth_equal(SR, z, f) for z in SIZES) + ' |')
    for z in SIZES:
        for f in FORMS:
            rows.append(dict(size=z, form=f, main=SR[('main', z, f)], d5=SR[('d5', z, f)], d6=SR[('d6', z, f)], i7=SR[('i7', z, f)], d4c=SR[('d4c', z, f)],
                             depth_with_main_row_area=round(depth_equal(SR, z, f), 2)))
    L += ['', 'Read: a reference with 5-flit buffers has %s of DeFT\'s area and one with 6-flit buffers %s (hierarchy kept, 2x2 / 3x3 / 4x4); 7-flit buffers in the' % (
        ' / '.join('%.3f' % SR[('d5', z, 'hier')] for z in SIZES), ' / '.join('%.3f' % SR[('d6', z, 'hier')] for z in SIZES)),
        'interposer routers alone give %s. The main row has %s.' % (' / '.join('%.3f' % SR[('i7', z, 'hier')] for z in SIZES), ' / '.join('%.3f' % SR[('main', z, 'hier')] for z in SIZES)), '']
    write('summary_hw_E3.md', L)
    write_csv(os.path.join(OUT, 'hw_equal_area_depth.csv'), rows)
    return rows


# =====================================================================================================================
# E2: the two RTL variants
# =====================================================================================================================
def e2_data():
    tim = {}
    for r in rd('timing_variants.csv'):
        d = 'DeFT' if r['design'] == 'DeFT_d4' else r['design']
        tim[(d, r['rtype'], r['size'], r['form'], r['cuts'])] = r
    area = {(r['design'], r['rtype'], r['size'], r['cuts']): r for r in rd('area_variants.csv')}
    return tim, area


def chosen(tim, v):
    """{mode: dict} as report_v25_hw.n_fast: the fitting cut configuration with the fewest cuts (ties: the largest worst-case margin)."""
    noise = RV.flow_spread(tim)
    e = {}
    for mode in ('1ns', 'ref'):
        b = RV.choose(tim, v, 'P', 'LF', mode)
        if b is None:
            x = RV.fit(tim, v, 'P', 'LF', '111', mode)
            e[mode] = dict(fits=False, cuts=None, limiting='%s on %s %s' % x[2], over_ns=round(-x[1], 4))
        else:
            cuts, n, margin, lim = b
            e[mode] = dict(fits=True, cuts=cuts, L_dec=1 + n, N_fast=n, residual=max(0, n - 1), worst_margin_ns=round(margin, 4), limiting='%s on %s %s' % lim, marginal=margin < noise)
    return e


def sys_area(A3, area, v, cuts, z, f):
    """Average router area of a system with the interposer routers of variant v (cut configuration cuts)."""
    tot = 0.0
    for t in TYPES:
        if v == 'DeFT':
            a = float(A3[('DeFT_d4', t, z)]['area_%s_um2' % f])
        elif t.startswith('chip'):
            a = float(A3[('CHIP25' if z == '2x2' else 'LBI18', t, z)]['area_%s_um2' % f])
        else:
            a = float(area[(v, t, '4x4' if z == '3x3' else z, cuts)]['area_%s_um2' % f])
        tot += COUNT[t] * a
    return tot / 32.0


def part_e2():
    tim, area = e2_data()
    A3, SR = e3_data()
    fc = json.load(open(os.path.join(HW, 'functional_check_variants.json'))) if have('functional_check_variants.json') else None
    last = lambda n: ([x for x in open(os.path.join(HW, n)).read().splitlines() if x.startswith('configurations')] or ['not run'])[-1] if have(n) else 'not run'   # noqa: E731
    spread = RV.flow_spread(tim)
    L = ['# v29 E2: two RTL variants of the interposer router (report_v29_hw.py e2)', '',
         'The interposer router of the main row (round 25: lookahead routing with a fallback, XY) without the reports across the VLs (`LB_noVLrep`), and without any',
         'report (`LB_noLA`: the decision unit has the credit counts of the router, the static hop terms and the bias). RTL: `hw/rtl/lb29_units.v`, the units of round 25',
         'with two macros; the main row is built from the same file with both macros at 1 and synthesised in the same run. Router top, core, test benches and',
         'checkers are those of round 25. Flow as round 25 (NanGate45 typical, Yosys + ABC at 1 GHz, OpenSTA on the flattened netlists, pre-layout, no wires).', '',
         '## E2.1 Checks', '']
    if fc:
        L += ['Vectors from runs of the matching simulator row through the Verilator checkers of round 25 (`hw/functional_check_variants.txt`): every selection vector with',
              'each of the eight cut configurations, and the front vectors. Control: the selection vectors of a variant through the units of the main row.', '',
              '| design | simulator runs (statistics identical to bin/noxim) | selection vectors | of those with a choice | front vectors | applied in all | mismatches | control: vectors, mismatches |', '|---|---|---|---|---|---|---|---|']
        for name, s in fc['summary'].items():
            L.append('| %s | %d (%d) | %d | %d | %d | %d | %d | %s |' % (name, s['runs'], s['identical'], s['sel'], s['multi'], s['front'], s['sel_applied'] + s['front'], s['mism'],
                                                                    '-' if name == 'main' else '%d, %d' % (s['control_vectors'], s['control_mism'])))
        L += ['', '**All vectors match, every instrumented run equals bin/noxim, the controls give mismatches: %s.**' % ('yes' if fc['ok'] else 'NO'), '']
    L += ['Router-level test under random packets, reports and credit delays (`hw/router_smoke_variants.txt`): %s.' % last('router_smoke_variants.txt'),
          'Cycles of a head through an idle router (`hw/latency_check_variants.txt`): %s.' % last('latency_check_variants.txt'), '']

    # ---- area ----
    ch = {v: chosen(tim, v) for v, _ in VARS}
    L += ['## E2.2 Area of the interposer routers (um^2: %s; in brackets relative to DeFT\'s router of the same type and size)' % ' / '.join(FNAME[f] for f in FORMS), '',
          'Cuts: the registers inside the decision unit (after stage A, M, B). "M" is the configuration of the main row in round 25; the last column of E2.4 gives the',
          'configuration each design needs at T_ref.', '']
    for z in ('2x2', '4x4'):
        L += ['### %s' % z, '', '| design | cuts | ' + ' | '.join(TNAME[t] for t in ITYPES) + ' | flip-flops (%s) | report inputs read (of 150) |' % ', '.join(ITYPES), '|---|---|---|---|---|---|']
        for v, nm in VARS:
            cs = ['000', '010']
            c = ch[v]['ref'].get('cuts')
            if c and c not in cs:
                cs.append(c)
            for c in cs:
                cells, ffs, bits = [], [], []
                for t in ITYPES:
                    r = area[(v, t, z, c)]
                    x = [float(r['area_%s_um2' % f]) for f in FORMS]
                    b = [float(A3[('DeFT_d4', t, z)]['area_%s_um2' % f]) for f in FORMS]
                    cells.append(' / '.join('%.0f' % a for a in x) + ' (' + ' / '.join('%.3f' % (a / y) for a, y in zip(x, b)) + ')')
                    ffs.append(r['ffs'])
                    bits.append(str(r.get('report_bits', '')))
                L.append('| %s | %s | ' % (nm, RV.CUTNAME[c]) + ' | '.join(cells) + ' | %s | %s |' % (', '.join(ffs), ', '.join(bits)))
        L.append('')
    # consistency: the main row built from lb29_units.v against the main row of the E3 run (lb25_units.v of round 25)
    same = []
    for z in ('2x2', '4x4'):
        for t in ITYPES:
            for f in FORMS:
                a, b = float(area[('LF_main', t, z, '010')]['area_%s_um2' % f]), float(A3[('LF_X', t, z)]['area_%s_um2' % f])
                same.append(abs(a - b))
    L += ['The main row built from `lb29_units.v` against the main row built from the units of round 25 (the E3 run), cuts M: largest difference of an area %.3f um^2 over' % max(same),
          'the 12 netlists (%s).' % ('the same netlists' if max(same) < 0.01 else 'not the same netlists: the two texts are synthesised differently'), '']

    # ---- system ratios ----
    L += ['## E2.3 System: average router area relative to DeFT (%s)' % ' / '.join(FNAME[f] for f in FORMS), '',
          'Weights per chiplet: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers. The chiplet routers are those of the main row for every variant',
          '(they send no report in a variant that reads none: wires, no logic). The 3x3 interposer routers are the 4x4 ones.', '',
          '| design | cuts | ' + ' | '.join(SIZES) + ' |', '|---|---|' + '---|' * len(SIZES)]
    sysrows = []
    for v, nm in VARS:
        cs = ['010']
        c = ch[v]['ref'].get('cuts')
        if c and c not in cs:
            cs.append(c)
        for c in cs:
            cells = []
            for z in SIZES:
                rel = [sys_area(A3, area, v, c, z, f) / sys_area(A3, area, 'DeFT', None, z, f) for f in FORMS]
                cells.append(' / '.join('%.3f' % x for x in rel))
                sysrows.append(dict(design=VLABEL[v], cuts=c, size=z, **{'rel_deft_%s' % f: round(x, 4) for f, x in zip(FORMS, rel)}))
            L.append('| %s | %s | ' % (nm, RV.CUTNAME[c]) + ' | '.join(cells) + ' |')
    L.append('')
    for z in SIZES:
        base = [r for r in sysrows if r['design'] == 'main' and r['cuts'] == '010' and r['size'] == z][0]
        for v in ('LB_noVLrep', 'LB_noLA'):
            r = [x for x in sysrows if x['design'] == v and x['cuts'] == '010' and x['size'] == z][0]
            L.append('%s, %s against the main row (cuts M): %s of the main row\'s area; of the main row\'s area above DeFT it keeps %s.' % (
                z, v, ' / '.join('%.3f' % (r['rel_deft_%s' % f] / base['rel_deft_%s' % f]) for f in FORMS),
                ' / '.join('%.0f %%' % (100 * (r['rel_deft_%s' % f] - 1) / (base['rel_deft_%s' % f] - 1)) for f in FORMS)))
    L.append('')

    # ---- timing ----
    L += ['## E2.4 Timing (OpenSTA on the flattened netlists; ns)', '',
          'T_ref of a router type and size = the longest stage of DeFT\'s router of that type and size in this run: %s.' % '; '.join(
              '%s %s %.2f' % (t, z, RV.tref(tim, t, z)) for z in ('2x2', '4x4') for t in ITYPES),
          'Spread of the flow on unchanged logic (the chiplet routers, as round 25): %.2f ns; a margin below it is called marginal.' % spread, '']
    trows = []
    for v, nm in VARS:
        L += ['### Decision path: %s' % nm, '',
              'Each cell: the longest stage over the four routers (ipos5, ipos6 x 2x2, 4x4). First stage: from the link. Route at the front: the relation of the head at the',
              'buffer front into its offered-output register.', '',
              '| cuts | L_dec | first stage | middle stages | last stage | route at the front | fits 1 ns (margin) | fits T_ref (margin) | residual |', '|---|---|---|---|---|---|---|---|---|']
        for cuts in RV.CUTS:
            x1, xr = RV.fit(tim, v, 'P', 'LF', cuts, '1ns'), RV.fit(tim, v, 'P', 'LF', cuts, 'ref')
            if not x1:
                continue
            per = x1[3]
            n = sum(int(c) for c in cuts)
            nst = n + 1
            first = max(per[k][0][1] for k in per)
            lastst = max(per[k][nst - 1][1] for k in per) if nst > 1 else None
            mids = [max(per[k][i][1] for k in per) for i in range(1, nst - 1)]
            offr = max(per[k][-1][1] for k in per)
            L.append('| %s | %d | %.2f | %s | %s | %.2f | %s (%+.2f) | %s (%+.2f) | %d |' % (
                RV.CUTNAME[cuts], n + 1, first, ', '.join('%.2f' % m for m in mids) if mids else '-', '%.2f' % lastst if lastst is not None else '(the first)', offr,
                'yes' if x1[0] else 'no', x1[1], 'yes' if xr[0] else 'no', xr[1], max(0, n - 1)))
            for (t, z), stages in per.items():
                row = dict(design=VLABEL[v], cuts=cuts, L_dec=n + 1, rtype=t, size=z, T_ref=round(RV.tref(tim, t, z), 4))
                for i, (g, val) in enumerate(stages):
                    row['stage%d' % (i + 1)] = '%s:%.4f' % (g, val)
                row['worst_stage_ns'] = round(max(val for _, val in stages), 4)
                row['fits_1ns'] = int(all(val <= 1.0 for _, val in stages))
                row['fits_T_ref'] = int(all(val <= RV.tref(tim, t, z) for _, val in stages))
                trows.append(row)
        for mode, mn in (('1ns', '1 ns'), ('ref', 'T_ref')):
            m = ch[v][mode]
            L.append('')
            if m['fits']:
                L.append('At %s: **L_dec = %d** (cuts: %s; worst margin %+.2f ns, on %s%s); residual %d.' % (
                    mn, m['L_dec'], RV.CUTNAME[m['cuts']], m['worst_margin_ns'], m['limiting'], '; inside the spread of the flow' if m['marginal'] else '', m['residual']))
            else:
                L.append('At %s: **no configuration of the three cuts fits** (with all three cuts %s is %.2f ns over).' % (mn, m['limiting'], m['over_ns']))
        L.append('')

    # ---- link budget and the rest of the router ----
    L += ['## E2.5 The link cycle and the whole router', '',
          'Link stage = the longest path that starts on a link input (DeFT: the buffer write; the designs of this round: the first stage of the decision, which reads the',
          'head on the link) plus T_CQ = %.2f ns. Left for the wire = T_ref minus the link stage: what an interposer link may take of the link cycle. Each design at the' % T_CQ,
          'cut configuration it needs at T_ref (and the main row\'s, M).', '',
          '| design | cuts | router | size | T_ref | link stage + T_CQ | left for the wire | route, one output | VC-allocation stage | whole router | whole router / T_ref |', '|---|---|---|---|---|---|---|---|---|---|---|']
    left, orows = {}, []
    items = [('DeFT', 'S', '000', 'DeFT')]
    for v, nm in VARS:
        cs = ['010']
        c = ch[v]['ref'].get('cuts') or '111'
        if c not in cs:
            cs.append(c)
        items += [(v, 'P', c, nm) for c in cs]
    for d, f, c, nm in items:
        for z in ('2x2', '4x4'):
            for t in ITYPES:
                r = tim.get((d, t, z, f, c))
                if not r:
                    continue
                T = RV.tref(tim, t, z)
                lf = d != 'DeFT'
                route1 = RV.st(r, 'OFFR') if lf else RV.st(r, 'ROUTE')
                va = max(x for x in (RV.st(r, 'VASTATE'), RV.st(r, 'ROUTE') if lf else None) if x is not None)
                whole = 1.0 - float(r['slack_all_ns'])
                link = RV.st(r, 'FROMLINK') + T_CQ
                left.setdefault((d, c), []).append(T - link)
                L.append('| %s | %s | %s | %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.3f |' % (nm, RV.CUTNAME[c], t, z, T, link, T - link, route1, va, whole, whole / T))
                orows.append(dict(design=VLABEL.get(d, d), cuts=c, rtype=t, size=z, T_ref=round(T, 4), link_stage_plus_tcq=round(link, 4), left_for_wire=round(T - link, 4),
                                  route_one_output=route1, va_stage=va, whole_router=round(whole, 4), whole_over_T_ref=round(whole / T, 4)))
    L += ['', 'Left for the wire, range over the four routers: ' + '; '.join('%s%s %.2f to %.2f ns' % (VLABEL.get(d, d), '' if c == '000' else ' (cuts %s)' % RV.CUTNAME[c], min(x), max(x))
                                                                       for (d, c), x in left.items()) + '.', '']
    write('summary_hw_E2.md', L)
    write_csv(os.path.join(OUT, 'hw_timing_variants.csv'), trows)
    write_csv(os.path.join(OUT, 'hw_other_paths_variants.csv'), orows)
    write_csv(os.path.join(OUT, 'hw_system_area_variants.csv'), sysrows)
    return dict(chosen=ch, sysrows=sysrows, left=left, area=area, tim=tim)


# =====================================================================================================================
# E4: power
# =====================================================================================================================
ACTS = [('default', 'default activity of the tool (0.1 transitions per clock period at every input)'),
        ('default_static', 'default activity; reset, position and table inputs constant'),
        ('sim05', 'simulation of the netlist at the load of 0.5 x Lsat'), ('sim10', 'simulation of the netlist at the load of 1.0 x Lsat')]


def e4_data():
    P = {}
    for r in rd('power_runs.csv'):
        if r.get('total_w', '') != '':
            P[(r['design'], r['rtype'], r['activity'])] = r
    return P


def psys(P, label, act, key='total_w'):
    """Average router power of a 4x4 system; the chiplet routers of a variant are the main row's."""
    tot = 0.0
    for t in TYPES:
        lab = label if (label, t, act) in P else ('main' if label in ('noVLrep', 'noLA') and t.startswith('chip') else None)
        if lab is None or (lab, t, act) not in P:
            return None
        tot += COUNT[t] * float(P[(lab, t, act)][key])
    return tot / 32.0


def part_e4():
    P = e4_data()
    loads = rd('port_loads.csv') if have('port_loads.csv') else []
    runs = rd('power_runs.csv')
    L = ['# v29 E4: power (report_v29_hw.py e4)', '',
         'OpenSTA `report_power` on the flattened netlists of the 4x4 routers (NanGate45 typical, 1 ns clock, the netlists of E2 and E3): DeFT\'s four routers, the main',
         'row\'s (its chiplet routers are the routers of round 18 with the exit LUT; its interposer routers have one register in the decision unit, after M) and the',
         'interposer routers of the two variants of E2.', '',
         '**Limits.** Before layout: no wire capacitance, no clock tree, no clock gating, ideal clock. The simulation of a netlist has zero delays, so no glitch is',
         'counted. The library is the typical corner of a 45 nm teaching library. The figures compare designs within this flow; they are not the power of a chip.', '',
         '## E4.1 The load a router carries (`hw/port_loads.csv`)', '',
         'Counted by the instrumented copy of the simulator in the measured window (4x4, uniform traffic, pipe_all 2, seed 1; statistics byte-identical to bin/noxim):',
         'flits per cycle on a mesh input (mean of the four ports and of the routers of the type), from the processing element and from the vertical link; the share',
         'of the flits on VC 1; the mean stay of a flit in an input buffer (cycles).', '',
         '| row | load | router | routers | mesh input | from the PE | from the vertical link | VC 1 share (mesh, vertical) | stay (mesh, vertical) |', '|---|---|---|---|---|---|---|---|---|']
    for r in loads:
        L.append('| %s | %s x Lsat (%s) | %s | %s | %.4f | %.4f | %.4f | %.2f, %.2f | %.2f, %.2f |' % (
            r['design'], {'05': '0.5', '10': '1.0'}[r['load']], r['rate'], r['rtype'], r['routers'], float(r['in_mesh']), float(r['in_local']), float(r['in_hub']),
            float(r['vc1_mesh']), float(r['vc1_hub']), float(r['stay_mesh']), float(r['stay_hub'])))
    sims = [r for r in runs if r['activity'].startswith('sim')]
    if sims:
        L += ['', '## E4.2 The bench carries that load (`hw/tb/tb_act18.v`, `tb_act25.v`)', '',
              'Random 8-flit packets at these rates per port, with the measured share of heads that end at the router or take its vertical link, credits after the measured',
              'stay; calibrated on the RTL until every rate is within 3 % of the simulator\'s (or the closest of ten tries). The netlist is then simulated with the same',
              'stimulus (2,000 + 10,000 cycles; the VCD holds the 10,000) and must print the same result line as the RTL.', '',
              '| design | router | load | flits per cycle: mesh input, PE, vertical in, vertical out, to the PE (simulator -> bench) | tries | netlist = RTL | nets annotated |', '|---|---|---|---|---|---|---|']
        for r in sims:
            pairs = []
            for k in ('mesh', 'local', 'hub', 'vert', 'eject'):
                tg, be = r.get('target_' + k, ''), r.get('bench_' + k, '')
                if tg not in ('', '0', '0.0') and float(tg) > 0:
                    pairs.append('%.4f -> %.4f' % (float(tg), float(be) if be != '' else float('nan')))
                else:
                    pairs.append('-')
            L.append('| %s | %s | %s x Lsat | %s | %s | %s | %s |' % (r['design'], r['rtype'], {'05': '0.5', '10': '1.0'}[r['activity'][3:]], ', '.join(pairs), r.get('tries', ''),
                                                             {'1': 'yes', '0': '**NO**'}.get(str(r.get('gate_equals_rtl', '')), '-'), (r.get('annotation', '') or r.get('note', ''))[:90]))
    rows = []
    L += ['', '## E4.3 Power per router (mW: internal / switching / leakage = total)', '']
    for act, an in ACTS:
        if not any(k[2] == act for k in P):
            continue
        L += ['### %s' % an, '', '| design | ' + ' | '.join(TNAME[t] for t in TYPES) + ' | system: average router | relative to DeFT |', '|---|---|---|---|---|---|---|']
        base = psys(P, 'DeFT', act)
        for label in ('DeFT', 'main', 'noVLrep', 'noLA'):
            cells = []
            for t in TYPES:
                r = P.get((label, t, act))
                if r is None and label in ('noVLrep', 'noLA') and t.startswith('chip'):
                    cells.append('(the main row\'s)')
                    continue
                if r is None:
                    cells.append('-')
                    continue
                d = P.get(('DeFT', t, act))
                cells.append('%.3f / %.3f / %.3f = %.3f%s' % (1e3 * float(r['internal_w']), 1e3 * float(r['switching_w']), 1e3 * float(r['leakage_w']), 1e3 * float(r['total_w']),
                                                             ' (%.3f)' % (float(r['total_w']) / float(d['total_w'])) if d and label != 'DeFT' else ''))
                rows.append(dict(design=label, rtype=t, activity=act, internal_mw=round(1e3 * float(r['internal_w']), 5), switching_mw=round(1e3 * float(r['switching_w']), 5),
                                 leakage_mw=round(1e3 * float(r['leakage_w']), 5), total_mw=round(1e3 * float(r['total_w']), 5),
                                 rel_deft=round(float(r['total_w']) / float(d['total_w']), 4) if d else ''))
            s = psys(P, label, act)
            L.append('| %s | ' % label + ' | '.join(cells) + ' | %s | %s |' % ('%.3f' % (1e3 * s) if s else '-', '%.3f' % (s / base) if s and base else '-'))
            if s:
                comp = {k: psys(P, label, act, k) for k in ('internal_w', 'switching_w', 'leakage_w')}
                rows.append(dict(design=label, rtype='system', activity=act, internal_mw=round(1e3 * comp['internal_w'], 5), switching_mw=round(1e3 * comp['switching_w'], 5),
                                 leakage_mw=round(1e3 * comp['leakage_w'], 5), total_mw=round(1e3 * s, 5), rel_deft=round(s / base, 4) if base else ''))
        L.append('')
    L += ['In brackets: relative to DeFT\'s router of the same type. System: 12 chiplet, 4 boundary, 12 interposer and 4 interposer + VL routers per chiplet; the chiplet',
          'routers of a variant are the main row\'s.', '']
    write('summary_hw_E4.md', L)
    write_csv(os.path.join(OUT, 'hw_power.csv'), rows)
    return rows


# =====================================================================================================================
# paper_data/hw_variants.csv
# =====================================================================================================================
def paper(e2, e4rows):
    A3, SR = e3_data()
    rows = []
    for d in ('DeFT', 'main', 'LB_noVLrep', 'LB_noLA'):
        v = {'main': 'LF_main', 'LB_noVLrep': 'LF_noVLrep', 'LB_noLA': 'LF_noLA'}.get(d)
        for z in SIZES:
            row = dict(design=d, size=z)
            zi = '4x4' if z == '3x3' else z
            if d == 'DeFT':
                row.update(cuts_at_T_ref='', L_dec='', residual='', margin_T_ref_ns='', **{'system_area_rel_deft_%s' % f: 1.0 for f in FORMS})
                c = '000'
            else:
                m = e2['chosen'][v]['ref']
                c = m.get('cuts') or ''
                row.update(cuts_at_T_ref=c, L_dec=m.get('L_dec', ''), residual=m.get('residual', ''), margin_T_ref_ns=m.get('worst_margin_ns', ''), marginal=int(bool(m.get('marginal'))) if m.get('fits') else '')
                for cc, suf in ((c, ''), ('010', '_cutM')):
                    if not cc:
                        continue
                    s = [r for r in e2['sysrows'] if r['design'] == d and r['cuts'] == cc and r['size'] == z]
                    if s:
                        row.update({'system_area_rel_deft_%s%s' % (f, suf): s[0]['rel_deft_%s' % f] for f in FORMS})
                for t in ITYPES:
                    if c and (v, t, zi, c) in e2['area']:
                        r = e2['area'][(v, t, zi, c)]
                        row['%s_area_hier_um2' % t] = r['area_hier_um2']
                        row['%s_ffs' % t] = r['ffs']
                        row['%s_report_inputs_read' % t] = r.get('report_bits', '')
            key = ('DeFT' if d == 'DeFT' else v, c)
            x = e2['left'].get(key)
            if x:      # the four routers ipos5, ipos6 x 2x2, 4x4, in that order of sizes
                per = {}
                k = 0
                for zz in ('2x2', '4x4'):
                    for t in ITYPES:
                        per[(zz, t)] = x[k]
                        k += 1
                row['link_left_for_wire_ns_ipos5'] = round(per[(zi, 'ipos5')], 4)
                row['link_left_for_wire_ns_ipos6'] = round(per[(zi, 'ipos6')], 4)
            if z == '4x4' and e4rows:
                lab = {'DeFT': 'DeFT', 'main': 'main', 'LB_noVLrep': 'noVLrep', 'LB_noLA': 'noLA'}[d]
                for r in e4rows:
                    if r['design'] == lab and r['rtype'] == 'system':
                        a = r['activity']
                        row['power_system_mw_%s' % a] = r['total_mw']
                        row['power_rel_deft_%s' % a] = r['rel_deft']
                        row['power_internal_mw_%s' % a] = r['internal_mw']
                        row['power_switching_mw_%s' % a] = r['switching_mw']
                        row['power_leakage_mw_%s' % a] = r['leakage_mw']
            rows.append(row)
    write_csv(os.path.join(PD, 'hw_variants.csv'), rows)
    print('wrote paper_data/hw_variants.csv (%d rows)' % len(rows))


def main():
    parts = [a for a in sys.argv[1:]] or ['e3', 'e2', 'e4']
    e2 = e4 = None
    if 'e3' in parts and have('area_buffers.csv', 'system_ratios.csv'):
        part_e3()
    if 'e2' in parts and have('area_variants.csv', 'timing_variants.csv', 'area_buffers.csv'):
        e2 = part_e2()
    if 'e4' in parts and have('power_runs.csv'):
        e4 = part_e4()
    if e2:
        paper(e2, e4)


if __name__ == '__main__':
    main()
