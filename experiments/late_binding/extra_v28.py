"""v28, extra comparisons for Part D that are outside the pre-registration (descriptive; written after the results of Part D were seen, DECISIONS.md).

Usage: python3 extra_v28.py        (V28_RES overrides the results directory)
Reads eval_runs.csv and fault_runs.csv of this round, results_v26_faults/fault_rate_runs.csv and results_v27_early/fault_runs.csv; writes report/extra_D.md.
  X.1  Without faults (Part C, seeds 171-180) on the two traffic patterns of the fault design: shares and effects, with THR over the nine loads and over
       the four loads of the fault design, next to the shares under faults of Part D.
  X.2  The early rows of round 27 (EB_vl, EB_route, EB_down) against the rows of this round on the same 48 masks of rate 4/16.
  X.3  EB_best64 against EB_best without faults on the two traffic patterns, next to the same comparison under faults.
The statistics are those of report_v28.py (Part C: effect over the ten seeds; Part D: unit = mask). No test, unadjusted 95 % intervals.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import report_v28 as RP
import report_v26 as RP26

FOUR = (1, 3, 5, 7)   # indices of 0.5, 1.0, 1.4, 2.0 x Lsat in the ladder of nine loads
SETS = [('uniform', ['uniform']), ('hotspot', ['hotspot']), ('both', ['uniform', 'hotspot'])]
Q = chr(39)


class Eval4(RP.Eval):
    """Eval with THR4 = the largest accepted throughput over the four loads of the fault design."""

    def val(self, row, z, p, s, name):
        if name == 'THR4':
            v = [self.run(row, z, p, i, s) for i in FOUR]
            return None if any(x is None for x in v) else max(x['accepted'] for x in v)
        return RP.Eval.val(self, row, z, p, s, name)


def three(f):
    return ' | '.join(f(z) for z in RP.SIZES)


def part1(E, tuned):
    D, ents = RP.fault_data(os.path.join(RP.RES, 'fault_runs.csv'), RP.D_RATES, RP.REFS26)[:2]

    def fshare(z, rate, row, traffic, n):
        """The share under faults, computed as in summary_D.md (D.3)."""
        es = [e for e in ents if e['size'] == z and e['rate'] == rate]
        pats = None if traffic == 'both' else [traffic]
        x, y = D.group(row, 'DeFT_P', es, n, pats)[0], D.group(RP.MAIN, 'DeFT_P', es, n, pats)[0]
        return '' if RP.isnan(x) or RP.isnan(y) or y == 0 else '%.0f %%' % (100 * x / y)
    L = ['## X.1 Without faults on the two traffic patterns of the fault design, next to the shares under faults', '',
         'Part C has six scenarios and nine loads, Part D uniform and hotspot traffic and four loads (0.5, 1.0, 1.4, 2.0 x Lsat). Here the fault-free runs of Part C are',
         'restricted to uniform and hotspot traffic; *THR (four loads)* is the largest accepted throughput over the four loads of the fault design, *THR (nine loads)*',
         'the THR of `summary_C.md`. Share of the main row' + Q + 's gain over DeFT_P that a row reaches, 2x2 | 3x3 | 4x4:', '',
         '| row | traffic | without faults: THR (nine loads) | | | THR (four loads) | | | LAT | | | rate 1/16: THR | | | LAT | | | rate 4/16: THR | | | LAT | | |',
         '|' + '---|' * 23]
    for row in tuned:
        for nm, sc in SETS:
            c = [three(lambda z, n=n: '%.0f %%' % (100 * E.share(row, z, n, sc)[0])) for n in ('THR', 'THR4', 'LAT')]
            for rate in RP.D_RATES:
                for n in ('THR', 'LAT'):
                    c.append(three(lambda z, n=n, rate=rate: fshare(z, rate, row, nm, n)))
            L.append('| `%s` | %s | %s |' % (row, nm, ' | '.join(c)))
    L += ['', 'The effects behind the fault-free shares (effect [95 % CI] over the ten seeds), 2x2 | 3x3 | 4x4:', '',
          '| row | against | traffic | THR (nine loads) | | | THR (four loads) | | | LAT at 1.0 x Lsat | | |', '|' + '---|' * 12]
    for ref in ('DeFT_P', RP.MAIN):
        for row in ([RP.MAIN] if ref == 'DeFT_P' else []) + tuned:
            for nm, sc in SETS:
                c = [three(lambda z, n=n: RP.eff(E.group(row, ref, z, n, sc))) for n in ('THR', 'THR4', 'LAT')]
                L.append('| `%s` | `%s` | %s | %s |' % (row, ref, nm, ' | '.join(c)))
    return L


def part2(E):
    P = json.load(open(os.path.join(RP.R26, 'load_points_v26.json')))
    ents = [e for e in json.load(open(os.path.join(RP.R26, 'masks_v26.json')))['part_b'] if e['rate'] == '4/16']
    R = RP26.load_runs(os.path.join(RP.R26, 'fault_rate_runs.csv'))
    R27 = RP26.load_runs(os.path.join(RP.R27, 'fault_runs.csv'))
    R28 = RP26.load_runs(os.path.join(RP.RES, 'fault_runs.csv'))
    clash = sum(1 for k in R27 if k in R or k in R28) + sum(1 for k in R28 if k in R)
    R.update(R27)
    R.update(R28)
    D = RP26.Data(R, lambda e, p: P['%s__%s__%s' % (e['size'], p, e['mask'])]['eval'], ents, RP26.PATTERNS, RP26.SEEDS, RP.REFS26)
    old = sorted({k[0] for k in R27})

    def es(z):
        return [e for e in ents if e['size'] == z]

    def cells(a, b, pats, mets=('THR', 'LAT', 'P99')):
        return ' | '.join(three(lambda z, n=n: RP.eff(D.group(a, b, es(z), n, pats))) for n in mets)
    PSETS = [('both', None), ('uniform', ['uniform']), ('hotspot', ['hotspot'])]
    L = ['', '## X.2 The early rows of round 27 on the same masks (rate 4/16)', '',
         'Round 27 ran `EB_vl`, `EB_route` and `EB_down` on the 48 masks of rate 4/16 with the same traffic patterns, loads and seeds',
         '(`results_v27_early/fault_runs.csv`: %d runs, rows %s; keys shared between the three files of per-run values: %d). `EB_route` is the member' % (
             len(R27), ', '.join('`%s`' % r for r in old), clash),
         '(route, P = 0, T = 0) of this round' + Q + 's family with round 27' + Q + 's `oracle_beta`, `EB_vl` the member (vl, P = 0, T = 0), and `EB_down` is `EB_down_t` with the main',
         'row' + Q + 's `lut_bias`. Effect of the first row against the second [95 % CI] over the 16 masks, 2x2 | 3x3 | 4x4:', '',
         '| row | against | traffic | THR | | | LAT at 1.0 x Lsat | | | P99 | | |', '|' + '---|' * 12]
    pairs = [('EB_best', 'EB_route'), ('EB_best', 'EB_vl'), ('EB_best64', 'EB_route'), ('EB_down_t', 'EB_down')]
    pairs += [(r, RP.MAIN) for r in ('EB_best', 'EB_best64', 'EB_route', 'EB_vl', 'EB_down_t', 'EB_down')]
    pairs += [(r, 'DeFT_P') for r in ('EB_best', 'EB_best64', 'EB_route', 'EB_vl', 'EB_down_t', 'EB_down', RP.MAIN)]
    for a, b in pairs:
        for nm, pats in PSETS:
            L.append('| `%s` | `%s` | %s | %s |' % (a, b, nm, cells(a, b, pats)))
    L += ['', 'Masks (of 16) in which the first row is behind the second (both traffic patterns):', '', '| row | against | THR: 2x2 | 3x3 | 4x4 | LAT: 2x2 | 3x3 | 4x4 |',
          '|---|---|---|---|---|---|---|---|']
    for a, b in pairs[:4] + [('EB_best', RP.MAIN), ('EB_route', RP.MAIN)]:
        c = [three(lambda z, n=n: '%d' % sum(1 for e in es(z) if D.wrong(D.vm(a, b, e, n, None), n))) for n in ('THR', 'LAT')]
        L.append('| `%s` | `%s` | %s |' % (a, b, ' | '.join(c)))
    L += ['', '## X.3 Old information: `EB_best64` against `EB_best` without faults on the two traffic patterns, and under faults at the rate 4/16', '',
          '| | traffic | THR: 2x2 | 3x3 | 4x4 | LAT at 1.0 x Lsat: 2x2 | 3x3 | 4x4 | P99: 2x2 | 3x3 | 4x4 |', '|' + '---|' * 11]
    for nm, sc in SETS:
        L.append('| without faults (nine loads, ten seeds) | %s | %s |' % (nm, ' | '.join(three(lambda z, n=n: RP.eff(E.group('EB_best64', 'EB_best', z, n, sc))) for n in ('THR', 'LAT', 'P99'))))
    for nm, sc in SETS:
        L.append('| without faults (THR over the four loads) | %s | %s | | | | | | |' % (nm, three(lambda z: RP.eff(E.group('EB_best64', 'EB_best', z, 'THR4', sc)))))
    for nm, pats in [('uniform', ['uniform']), ('hotspot', ['hotspot']), ('both', None)]:
        L.append('| rate 4/16 (16 masks, four loads) | %s | %s |' % (nm, cells('EB_best64', 'EB_best', pats)))
    return L


def main():
    RP.HIGHER['THR4'] = True
    E = Eval4(RP.load_runs(os.path.join(RP.RES, 'eval_runs.csv')), json.load(open(os.path.join(RP.R25, 'load_points_v25.json'))), RP.C_SEEDS)
    tuned = [r for r in RP.TUNED if r in E.rows]
    L = ['# v28 Part D, extra: comparisons outside the pre-registration (descriptive; generated by extra_v28.py)', '',
         'Written after the results of Part D were seen (`DECISIONS.md`). No test; the intervals are unadjusted 95 % intervals. Without faults: effect over the ten seeds',
         '(171-180) as in `summary_C.md`; under faults: unit = mask, 16 masks per size and rate, seeds 151 and 152, as in `summary_D.md`.', '']
    L += part1(E, tuned) + part2(E)
    RP.wmd('extra_D.md', L)
    print('extra_D.md: %d lines' % len(L))


if __name__ == '__main__':
    main()
