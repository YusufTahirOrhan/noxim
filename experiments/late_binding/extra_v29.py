"""v29: descriptive tables that were added after the results of a part were seen (DECISIONS.md says why). Nothing here is a test and
nothing of report_v29.py is changed; FINDINGS.md marks every number it takes from here.

  python3 extra_v29.py [b]      ->  results_v29_review/report/extra_B.md
     X.1  the one test of family 1 that is against the main row (THR against the best reference on 2x2) comes from randperm: accepted
          throughput and latency of every row at each of the nine loads on 2x2 randperm (mean over the ten seeds), and the load at which
          each row's accepted throughput is the largest
  python3 extra_v29.py c        ->  results_v29_review/report/extra_C.md, extra_C_area.csv
     X.2  the comparisons of Part C read at the area of the main row (defined before the results of C1 were read)
     X.3  THR and LAT of every row per scenario, and which reference is the best of the four at each depth (added after they were read)
"""
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V29_RES', os.path.join(HERE, 'results_v29_review'))
OUT = os.path.join(RES, 'report')
NL = chr(10)
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]


def write(name, L):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)
    print('wrote report/%s (%d lines)' % (name, len(L)))


def part_b():
    P = json.load(open(os.path.join(RES, 'load_points_v29.json')))
    R = defaultdict(list)
    for r in csv.DictReader(open(os.path.join(RES, 'heldout_runs.csv'))):
        R[(r['variant'][:-3], r['pattern'], float(r['rate']))].append((float(r['accepted']), float(r['latency'])))
    L = ['# v29 Part B: tables added after the results were seen (extra_v29.py b)', '',
         'Descriptive; not in the pre-registration. `DECISIONS.md` ("Tables added after the results") says why each is here.', '',
         '## X.1 Accepted throughput (flits/node/cycle) and mean latency (cycles) at each load, mean over the ten seeds', '',
         'The one test of primary family 1 that is against the main row is THR against the best reference on 2x2, and it comes from `randperm` (B.2). THR is the largest',
         'accepted throughput over the nine loads. The table shows at which loads the rows differ. **Bold**: the largest accepted throughput of the load.', '']
    for z, pat in (('2x2', 'randperm'), ('2x2', 'tornado'), ('2x2', 'neighbour'), ('3x3', 'randperm'), ('4x4', 'randperm')):
        key = [k for k in P if k.startswith('%s__%s__' % (z, pat))][0]
        rates = P[key]['eval']
        rows = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP', 'CI_heurLA_X_LF'] + (['LB_b0'] if z == '2x2' else [])
        L += ['### %s, %s (Lsat of DeFT_P %.4f packets/cycle/source)' % (z, pat, P[key]['lsat']), '',
              '| load | offered | ' + ' | '.join(rows) + ' |', '|---|---|' + '---|' * len(rows)]
        peak = {}
        for m, x in zip(MULTS, rates):
            acc = {r: sum(a for a, _ in R[(r, '%s-%s' % (z, pat), x)]) / len(R[(r, '%s-%s' % (z, pat), x)]) for r in rows}
            lat = {r: sum(l for _, l in R[(r, '%s-%s' % (z, pat), x)]) / len(R[(r, '%s-%s' % (z, pat), x)]) for r in rows}
            best = max(acc.values())
            for r in rows:
                if r not in peak or acc[r] > peak[r][1]:
                    peak[r] = (m, acc[r])
            L.append('| %.1f x Lsat | %.4f | ' % (m, 8 * x) + ' | '.join(('**%.4f** / %.0f' if abs(acc[r] - best) < 5e-5 else '%.4f / %.0f') % (acc[r], lat[r]) for r in rows) + ' |')
        L += ['| the load of the largest mean accepted throughput | | ' + ' | '.join('%.1f x Lsat' % peak[r][0] for r in rows) + ' |', '']
    write('extra_B.md', L)


def part_c():
    """X.2: the comparisons of Part C read at the area of the main row. Written on 25 November while C1 was running, before any of its
    results had been read (DECISIONS.md); it is not in the pre-registration and it is no test."""
    import math
    import report_v29 as RV
    P = RV.ladders()
    R = RV.load(os.path.join(RV.V25, 'eval_runs.csv'), os.path.join(RES, 'depth_runs.csv'))
    D = RV.Design(R, P, range(121, 131))
    A = RV.area_ratios()
    six = lambda z: RV.scen(z, RV.SIX)  # noqa: E731
    have_d5 = ('DeFT_P_d5', '2x2-uniform', RV.FREE['2x2'], D.lad('2x2', ('uniform', RV.FREE['2x2']))[3], 121) in R
    if not A or not have_d5:
        print('extra part c needs hw/system_ratios.csv and the rows at depth 5; not written')
        return
    groups = [('the best of the two DeFT variants', ('DeFT_P', 'DeFT_B')), ('the best of MTR and RC', ('MTR', 'RC')), ('the best of the four', tuple(RV.REFS4))]
    pct = lambda v: 100 * (math.exp(v) - 1)  # noqa: E731

    def at(xs, ys, x):
        """Piecewise linear through (xs, ys), xs ascending; None outside."""
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                w = (x - xs[i]) / (xs[i + 1] - xs[i])
                return [(1 - w) * a + w * b for a, b in zip(ys[i], ys[i + 1])]
        return None

    def zero(xs, m, name):
        """The first x at which the piecewise linear mean effect stops being in favour of the main row (THR: > 0, LAT: < 0)."""
        good = (lambda v: v > 0) if name == 'THR' else (lambda v: v < 0)
        if not good(m[0]):
            return 'behind or level already with 4-flit buffers'
        for i in range(len(xs) - 1):
            if good(m[i]) and not good(m[i + 1]):
                w = m[i] / (m[i] - m[i + 1])
                return xs[i] + w * (xs[i + 1] - xs[i])
        return None

    L = ['# v29 Part C: tables added to the report (extra_v29.py c)', '',
         'Descriptive; not in the pre-registration and no test. X.2 was defined on 25 November while C1 was running, before any of its results had been read; X.3 was',
         'added after they had been read (`DECISIONS.md`, "Tables added after the results").', '',
         '## X.2 The main row against the best reference, read at the area of the main row', '',
         'A reference with 5-flit buffers has less area than the main row when the hierarchy is kept and more in the other two forms of the synthesis; one with 6-flit',
         'buffers has more in every form (`report/summary_hw_E3.md`). The table reads the three measured comparisons (references with 4-flit buffers: round 25; with 5-flit and',
         '6-flit buffers: C1; six scenarios, ten seeds, the best row of the set per scenario and metric at each depth) at the area of the main row: per seed the log ratio is',
         'interpolated linearly in the system area between the two neighbouring depths, then the effect and its 95 % interval over the seeds are computed as everywhere.',
         'No router with 4.6 or 5.4-flit buffers exists; the column says where the main row would stand against a reference that spent the same area on buffers, if the',
         'effect moved evenly with the area. The areas are taken as exact (the flow spreads by about 1 % on unchanged logic). **Break-even**: the buffer depth of the',
         'references (and its area relative to DeFT at depth 4, in the form of the block) at which the interpolated mean effect stops being in favour of the main row.', '']
    rows = []
    for f, ftitle in RV.FORMS:
        L += ['### %s' % ftitle, '', '| size | area: main row; d5; d6 | against | metric | 4-flit | 5-flit | 6-flit | at the area of the main row | break-even depth (area) |',
              '|---|---|---|---|---|---|---|---|---|']
        for z in RV.SIZES:
            xs = [1.0, A[('d5', z, f)], A[('d6', z, f)]]
            am = A[('main', z, f)]
            for gname, g in groups:
                for n in ('THR', 'LAT'):
                    ys = [D.lr(RV.MAIN, tuple('%s%s' % (b, t) for b in g), z, six(z), n) for t in ('', '_d5', '_d6')]
                    if len(set(len(y) for y in ys)) != 1 or not ys[0]:
                        raise SystemExit('unequal seed sets in %s %s %s' % (z, gname, n))
                    st = [RV.stat(y) for y in ys]
                    m = [sum(y) / len(y) for y in ys]
                    ya = at(xs, ys, am)
                    sa = RV.stat(ya) if ya else None
                    x0 = zero(xs, m, n)
                    if x0 is None:
                        be = 'not up to 6-flit buffers'
                    elif isinstance(x0, str):
                        be = x0
                    else:
                        i = 0 if x0 <= xs[1] else 1
                        dep = 4 + i + (x0 - xs[i]) / (xs[i + 1] - xs[i])
                        be = '%.1f flits (%.3f)' % (dep, x0)
                    L.append('| %s | %.3f; %.3f; %.3f | %s | %s | %s | %s | %s | %s | %s |' % (z, am, xs[1], xs[2], gname, n, RV.eci(st[0]), RV.eci(st[1]), RV.eci(st[2]),
                                                                                  '**%s**' % RV.eci(sa) if sa else 'outside the measured areas', be))
                    rows.append(dict(form=f, size=z, against=gname, metric=n, area_main=am, area_d5=xs[1], area_d6=xs[2], effect_d4=pct(m[0]), effect_d5=pct(m[1]), effect_d6=pct(m[2]),
                                     effect_at_main_area=sa['effect_pct'] if sa else '', ci_low=sa['ci_low'] if sa else '', ci_high=sa['ci_high'] if sa else '',
                                     break_even=be))
        L.append('')
    # X.3 was added after the results of C1 had been read (DECISIONS.md): the values behind C.3 and C.4 and which row "the best" is
    L += ['## X.3 Absolute values per scenario (mean over the ten seeds), and which reference is the best of the four at each depth', '',
          'Added on 25 November after the results of C1 had been read: C.3 and C.4 compare with "the best of the four" and do not say which row that is in a scenario.',
          'THR in flits/node/cycle (the largest accepted throughput over the nine loads), LAT in cycles at 1.0 x Lsat of DeFT_P with 4-flit buffers. Each reference with',
          '4-flit / 5-flit / 6-flit buffers; **bold**: the best of the four at that depth, which is the row that the main row is compared with.', '']
    tags = ('', '_d5', '_d6')
    count = {t: defaultdict(int) for t in tags}
    for n, f in (('THR', '%.4f'), ('LAT', '%.1f')):
        for z in RV.SIZES:
            L += ['### %s, %s' % (n, z), '', '| scenario | the main row | `LB_d6` | ' + ' | '.join(RV.REFS4) + ' |', '|---|---|---|' + '---|' * len(RV.REFS4)]
            for sc in six(z):
                best = {t: D.best(tuple(b + t for b in RV.REFS4), z, sc, n) for t in tags}
                for t in tags:
                    count[t][best[t][:len(best[t]) - len(t)]] += 1
                cells = [' / '.join(('**%s**' if best[t] == b + t else '%s') % (f % D.smean(b + t, z, sc, n)) for t in tags) for b in RV.REFS4]
                L.append('| %s | %s | %s | %s |' % (sc[0], f % D.smean(RV.MAIN, z, sc, n), f % D.smean('LB_d6', z, sc, n), ' | '.join(cells)))
            L.append('')
    L += ['The best of the four references, counted over the 36 cells of size, scenario and metric (THR and LAT):', '',
          '| buffers of the references | ' + ' | '.join(RV.REFS4) + ' |', '|---|' + '---|' * len(RV.REFS4)]
    for t, name in zip(tags, ('4-flit (round 25)', '5-flit', '6-flit')):
        L.append('| %s | %s |' % (name, ' | '.join(str(count[t][b]) for b in RV.REFS4)))
    L.append('')
    write('extra_C.md', L)
    with open(os.path.join(OUT, 'extra_C_area.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('wrote report/extra_C_area.csv (%d rows)' % len(rows))


if __name__ == '__main__':
    parts = sys.argv[1:] or ['b']
    for p in parts:
        globals()['part_' + p]()
