"""v18 report: area and timing tables (results_v18_area/report/). Reads area_runs.csv, breakdown_runs.csv, timing_runs.csv."""
import csv
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v18_area')
OUT = os.path.join(RES, 'report')
SIZES = ['2x2', '3x3', '4x4']
CHIPS = {'2x2': 4, '3x3': 9, '4x4': 16}
TYPES = ['chip5', 'chip6', 'ipos5', 'ipos6']
TNAME = {'chip5': 'chiplet (5 ports)', 'chip6': 'boundary (6 ports)', 'ipos5': 'interposer (5 ports)', 'ipos6': 'interposer + VL (6 ports)'}
COUNT = {'chip5': 12, 'chip6': 4, 'ipos5': 12, 'ipos6': 4}    # per chiplet: routers of each type
METHODS = ['REF', 'DeFT', 'DeFT14', 'MTR', 'RC', 'DeFT_Dis', 'LBI_heur', 'LBI_ql', 'LBF_heur', 'LBF_ql']
MNAME = {'REF': 'Reference (XY, no VNs)', 'DeFT': 'DeFT', 'DeFT14': 'DeFT, 14 scenarios', 'MTR': 'MTR', 'RC': 'RC', 'DeFT_Dis': 'DeFT-Dis',
         'LBI_heur': 'LB-I heuristic', 'LBI_ql': 'LB-I Q-learning', 'LBF_heur': 'LB-F heuristic', 'LBF_ql': 'LB-F Q-learning'}
CATS = ['buffers', 'rc_buffer', 'crossbar', 'allocators', 'routing', 'selection', 'tables', 'learning', 'ni', 'top']
CNAME = {'buffers': 'buffers', 'rc_buffer': 'RC buffer', 'crossbar': 'crossbar', 'allocators': 'allocators', 'routing': 'routing unit',
         'selection': 'selection', 'tables': 'tables', 'learning': 'Q update + feedback regs', 'ni': 'NI logic', 'top': 'other'}
NL = chr(10)


def load():
    area = {(r['method'], r['rtype'], r['size'], r['form']): r for r in csv.DictReader(open(os.path.join(RES, 'area_runs.csv')))}
    brk = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(RES, 'breakdown_runs.csv'))):
        brk[(r['method'], r['rtype'], r['size'], r['form'])][r['category']] = (float(r['area_um2']), int(r['ffs']))
    tim = {(r['method'], r['rtype'], r['size'], r['form']): r for r in csv.DictReader(open(os.path.join(RES, 'timing_runs.csv')))}
    return area, brk, tim


def a(area, m, t, z, form='S'):
    r = area.get((m, t, z, form))
    return float(r['area_um2']) if r else None


def lb_form(area, m, t, z, form):
    """P form where it exists, otherwise the method's S form (LB-I chiplet routers have no routing + selection unit)."""
    v = a(area, m, t, z, form)
    return v if v is not None else a(area, m, t, z, 'S')


def system(area, m, z, form='S'):
    tot = n = 0.0
    for t in TYPES:
        tot += COUNT[t] * lb_form(area, m, t, z, form)
        n += COUNT[t]
    return tot / n


def area_tables(area):
    L = ['## Area per router type (um^2 / relative to DeFT / relative to the reference router)', '',
         'Hierarchical synthesis, 1 GHz target, form S (one routing + selection unit per router). Cell counts: `area_runs.csv`.', '']
    for z in SIZES:
        L += [f'### {z} (C = {CHIPS[z]})', '', '| method | ' + ' | '.join(TNAME[t] for t in TYPES) + ' |', '|---|' + '---|' * len(TYPES)]
        for m in METHODS:
            cells = []
            for t in TYPES:
                v = a(area, m, t, z)
                cells.append(f"{v:.0f} / {v / a(area, 'DeFT', t, z):.3f} / {v / a(area, 'REF', t, z):.3f}")
            L.append(f'| {MNAME[m]} | ' + ' | '.join(cells) + ' |')
        L.append('')
    return L


def form_p_table(area):
    L = ['## Form P: one routing + selection unit per input port (upper bound)', '', 'Relative to DeFT, per router type.', '',
         '| size | method | ' + ' | '.join(TNAME[t] for t in TYPES) + ' | system average |', '|---|---|' + '---|' * (len(TYPES) + 1)]
    for z in SIZES:
        for m in ('LBI_heur', 'LBI_ql', 'LBF_heur', 'LBF_ql'):
            cells = [f"{lb_form(area, m, t, z, 'P') / a(area, 'DeFT', t, z):.3f}" for t in TYPES]
            L.append(f"| {z} | {MNAME[m]} | " + ' | '.join(cells) + f" | {system(area, m, z, 'P') / system(area, 'DeFT', z):.3f} |")
    return L + ['']


def share_tables(area, brk):
    L = ['## Share of the router area (%)', '', 'Form S. FF = flip-flops in the router.', '']
    for z in SIZES:
        for t in TYPES:
            L += [f'### {z}, {TNAME[t]}', '', '| method | area | FF | ' + ' | '.join(CNAME[c] for c in CATS) + ' |', '|---|---|---|' + '---|' * len(CATS)]
            for m in METHODS:
                b = brk[(m, t, z, 'S')]
                tot = sum(x[0] for x in b.values())
                ff = sum(x[1] for x in b.values())
                L.append(f'| {MNAME[m]} | {tot:.0f} | {ff} | ' + ' | '.join(f'{100 * b[c][0] / tot:.1f}' if c in b else '-' for c in CATS) + ' |')
            L.append('')
    return L


def system_table(area):
    L = ['## System-level average router area', '', 'Weighted by the router counts of a chiplet: 12 chiplet, 4 boundary, 12 interposer, 4 interposer + VL. Relative to DeFT.', '',
         '| method | ' + ' | '.join(f'{z}: um^2 / rel.' for z in SIZES) + ' |', '|---|' + '---|' * len(SIZES)]
    for m in METHODS:
        cells = [f"{system(area, m, z):.0f} / {system(area, m, z) / system(area, 'DeFT', z):.3f}" for z in SIZES]
        L.append(f'| {MNAME[m]} | ' + ' | '.join(cells) + ' |')
    return L + ['']


def paper_table(area):
    L = ['## Comparison with the DeFT paper (normalized to MTR)', '', 'Paper: logic synthesis (Cadence Genus) plus ORION 3.0.', '',
         '| ratio | paper | ' + ' | '.join(SIZES) + ' |', '|---|---|' + '---|' * len(SIZES)]
    rows = [('DeFT / MTR, boundary router', 'DeFT', 'chip6', 1.016), ('DeFT / MTR, chiplet router', 'DeFT', 'chip5', 1.016),
            ('DeFT / MTR, interposer router', 'DeFT', 'ipos5', None), ('RC boundary / MTR boundary', 'RC', 'chip6', 1.133), ('RC non-boundary / MTR non-boundary', 'RC', 'chip5', 1.017)]
    for name, m, t, p in rows:
        L.append(f'| {name} | {p if p else "-"} | ' + ' | '.join(f"{a(area, m, t, z) / a(area, 'MTR', t, z):.3f}" for z in SIZES) + ' |')
    L += ['', 'Without the NI table of MTR (16C x 2 bits, stored in flip-flops here), the same ratios:', '',
          '| ratio | ' + ' | '.join(SIZES) + ' |', '|---|' + '---|' * len(SIZES)]
    return L


def paper_table2(area, brk):
    L = []
    for name, m, t in (('DeFT / MTR, boundary router', 'DeFT', 'chip6'), ('DeFT / MTR, chiplet router', 'DeFT', 'chip5'),
                       ('RC boundary / MTR boundary', 'RC', 'chip6'), ('RC non-boundary / MTR non-boundary', 'RC', 'chip5')):
        cells = []
        for z in SIZES:
            mt = a(area, 'MTR', t, z) - brk[('MTR', t, z, 'S')].get('tables', (0, 0))[0]
            cells.append(f'{a(area, m, t, z) / mt:.3f}')
        L.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    # flip-flop share of buffers
    L += ['', 'Reference router, buffers as share of its area (flip-flop buffers): ' +
          ', '.join(f"{z}: {100 * brk[('REF', 'chip5', z, 'S')]['buffers'][0] / a(area, 'REF', 'chip5', z):.1f} %" for z in SIZES), '']
    return L


def timing_tables(tim):
    L = ['## Critical path of the routing + selection stage against the 1 GHz cycle', '',
         'OpenSTA on the flattened design, pre-layout, ideal clock, no wires. Stage: from the input-buffer flip-flops through arbitration and routing + selection to the '
         'route registers of the input VCs. Arrival and slack in ns; stages = ceil(arrival + setup / 1 ns) with no register overhead added, so a lower bound on the stages needed.', '',
         '| size | method | form | ' + ' | '.join(TNAME[t] for t in TYPES) + ' |', '|---|---|---|' + '---|' * len(TYPES)]
    for z in SIZES:
        for m in METHODS:
            for form in ('S', 'P'):
                if not any((m, t, z, form) in tim for t in TYPES):
                    continue
                cells = []
                for t in TYPES:
                    r = tim.get((m, t, z, form))
                    if not r or r['slack_ROUTE_REG'] == '':
                        cells.append('-')
                        continue
                    arr, sl = float(r['arrival_ROUTE_REG']), float(r['slack_ROUTE_REG'])
                    cells.append(f'{arr:.2f} / {sl:+.2f} / {math.ceil(1.0 - sl - 1e-9) if sl < 0 else 1}')
                L.append(f'| {z} | {MNAME[m]} | {form} | ' + ' | '.join(cells) + ' |')
    L += ['', '## Other paths, form S (slack in ns against 1 ns)', '',
          '| size | method | router type | whole design | Q table write (update path) |', '|---|---|---|---|---|']
    for z in SIZES:
        for m in METHODS:
            for t in TYPES:
                r = tim.get((m, t, z, 'S'))
                if not r:
                    continue
                q = f"{float(r['slack_QTABLE']):+.2f}" if r['slack_QTABLE'] else '-'
                L.append(f"| {z} | {MNAME[m]} | {TNAME[t]} | {float(r['slack_all_ns']):+.2f} | {q} |")
    return L + ['']


def main():
    os.makedirs(OUT, exist_ok=True)
    area, brk, tim = load()
    L = ['# v18 report: area and timing (NanGate45, Yosys + ABC, OpenSTA)', ''] + system_table(area) + area_tables(area) + form_p_table(area) + \
        paper_table(area) + paper_table2(area, brk) + timing_tables(tim) + share_tables(area, brk)
    open(os.path.join(OUT, 'summary.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


if __name__ == '__main__':
    main()
