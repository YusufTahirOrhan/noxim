"""v29: descriptive tables that were added after the results of a part were seen (DECISIONS.md says why). Nothing here is a test and
nothing of report_v29.py is changed; FINDINGS.md marks every number it takes from here.

  python3 extra_v29.py [b]      ->  results_v29_review/report/extra_B.md
     X.1  the one test of family 1 that is against the main row (THR against the best reference on 2x2) comes from randperm: accepted
          throughput and latency of every row at each of the nine loads on 2x2 randperm (mean over the ten seeds), and the load at which
          each row's accepted throughput is the largest
  python3 extra_v29.py c        ->  results_v29_review/report/extra_C.md, extra_C_area.csv
     X.2  the comparisons of Part C read at the area of the main row (defined before the results of C1 were read)
     X.3  THR and LAT of every row per scenario, and which reference is the best of the four at each depth (added after they were read)
     X.5  under faults (C3), counted over the masks: which DeFT variant with 6-flit buffers is the better one, and on how many masks the
          main row is ahead of it (added after the results of C3 were read)
  python3 extra_v29.py d        ->  results_v29_review/report/extra_D.md
     X.6  D1 in the direction of the question (the per-hop row against its static row), which reference is the best of the five with
          each VC policy, and the main row against the best per scenario (added after the results of D1 were read)
  python3 extra_v29.py e        ->  results_v29_review/report/extra_E.md, extra_E_noLA.csv
     X.4  LB_noLA against the references with 4-flit, 5-flit and 6-flit buffers, next to the main row, with the areas of E2 and E3
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
    # X.5 was added after the results of C3 had been read (DECISIONS.md): counts over the masks behind C.8
    ff = os.path.join(RES, 'depth_fault_runs.csv')
    if os.path.exists(ff):
        F = RV.Faults(RV.load(os.path.join(RV.V26, 'fault_rate_runs.csv'), ff))
        mean2 = lambda row, e, p, n: sum(F.val(row, e, p, s, n) for s in F.SEEDS) / len(F.SEEDS)  # noqa: E731
        L += ['## X.5 Under faults (C3), counted over the masks: which DeFT variant is the better one, and on how many masks the main row is ahead', '',
              'Added on 26 November after the results of C3 had been read: C.8 gives effects with intervals over the 16 masks of a size and rate and does not say which variant',
              '"the best" is nor how the masks split. Per mask and traffic pattern the mean over the two seeds; THR over the four loads, LAT at 1.0 x Lsat of DeFT_P on the mask.',
              '*Ahead*: the main row (4-flit buffers) has the higher THR, or the lower LAT, than the better of the two variants on that mask.', '',
              '| size | rate | traffic | `DeFT_B_d6` is the better variant: THR | LAT | the main row ahead of the better variant with 6-flit buffers: THR | LAT | with 4-flit buffers (round 26): THR | LAT |',
              '|---|---|---|---|---|---|---|---|---|']
        tot = defaultdict(int)
        for z in RV.SIZES:
            for rate in ('1/16', '4/16'):
                es = [e for e in F.masks if e['size'] == z and e['rate'] == rate]
                for p in F.PATS:
                    cells = []
                    for n in ('THR', 'LAT'):
                        k = sum(1 for e in es if F.best(('DeFT_P_d6', 'DeFT_B_d6'), e, p, n) == 'DeFT_B_d6')
                        tot[(p, n, 'B')] += k
                        cells.append('%d of %d' % (k, len(es)))
                    for refs in (('DeFT_P_d6', 'DeFT_B_d6'), ('DeFT_P', 'DeFT_B')):
                        for n in ('THR', 'LAT'):
                            sign = 1 if n == 'THR' else -1
                            k = sum(1 for e in es if sign * (mean2(RV.MAIN, e, p, n) - mean2(F.best(refs, e, p, n), e, p, n)) > 0)
                            tot[(p, n, refs[0])] += k
                            cells.append('%d of %d' % (k, len(es)))
                    tot[(p, 'masks')] += len(es)
                    L.append('| %s | %s | %s | %s |' % (z, rate, p, ' | '.join(cells)))
        for p in F.PATS:
            L.append('| all | both | %s | %s |' % (p, ' | '.join('%d of %d' % (tot[(p, n, c)], tot[(p, 'masks')]) for c in ('B', 'DeFT_P_d6', 'DeFT_P') for n in ('THR', 'LAT'))))
        L.append('')
    write('extra_C.md', L)
    with open(os.path.join(OUT, 'extra_C_area.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('wrote report/extra_C_area.csv (%d rows)' % len(rows))


def part_e():
    """X.4: LB_noLA next to the references of each buffer depth, with the areas of E2 and E3. Added on 25 November after the results of
    C1 and of E1 had been read (DECISIONS.md); not in the pre-registration and no test."""
    import report_v29 as RV
    P = RV.ladders()
    R = RV.load(os.path.join(RV.V25, 'eval_runs.csv'), os.path.join(RES, 'depth_runs.csv'), os.path.join(RES, 'nola_runs.csv'))
    D = RV.Design(R, P, range(121, 131))
    A = RV.area_ratios()
    six = lambda z: RV.scen(z, RV.SIX)  # noqa: E731
    f = os.path.join(RES, 'paper_data', 'hw_variants.csv')
    if not A or not os.path.exists(f) or ('LB_noLA', '2x2-uniform', RV.FREE['2x2'], D.lad('2x2', ('uniform', RV.FREE['2x2']))[3], 121) not in R:
        print('extra part e needs hw/system_ratios.csv, paper_data/hw_variants.csv and nola_runs.csv; not written')
        return
    hv = {(r['design'], r['size']): r for r in csv.DictReader(open(f))}

    def area(design, z, form):
        """System area relative to DeFT; the variants with the cut of the main row, as summary_hw_E2.md prints them."""
        r = hv[(design, z)]
        return float(r.get('system_area_rel_deft_%s_cutM' % form) or r['system_area_rel_deft_%s' % form])

    forms = [x for x, _ in RV.FORMS]
    tri = lambda g: ' / '.join('%.3f' % (g(x) + 1e-9) for x in forms)  # noqa: E731  (the files hold four decimals: a 5 in the fourth goes up, as in the hardware report)
    L = ['# v29 Part E1: a table added after the results were seen (extra_v29.py e)', '',
         'Descriptive; not in the pre-registration and no test. Added on 25 November after the results of C1 and of E1 had been read (`DECISIONS.md`, "Tables added after the',
         'results").', '',
         '## X.4 `LB_noLA` against the references of each buffer depth, with the areas', '',
         'The row without the lookahead term needs no report wire and no report register (E2). The table puts it where Part C puts the main row: against the best reference with',
         '4-flit buffers (round 25), with 5-flit and with 6-flit buffers (C1); six scenarios, seeds 121-130, the best row of a set per scenario and metric, effect [95 % interval',
         'over the seeds]. The main row stands next to it (the figures of C.3). Areas: all routers of a system relative to DeFT with 4-flit buffers, hierarchy kept / core kept /',
         'flattened (`report/summary_hw_E2.md`, `summary_hw_E3.md`; the variant with the register cut of the main row).', '',
         '| size | `LB_noLA` | the main row (the netlists of E2) | references with 5-flit buffers | with 6-flit buffers |', '|---|---|---|---|---|']
    for z in RV.SIZES:
        L.append('| %s | %s | %s | %s | %s |' % (z, tri(lambda x: area('LB_noLA', z, x)), tri(lambda x: area('main', z, x)), tri(lambda x: A[('d5', z, x)]), tri(lambda x: A[('d6', z, x)])))
    L.append('')
    rows = []
    for gname, g in (('the best of the four references', tuple(RV.REFS4)), ('the best of the two DeFT variants', ('DeFT_P', 'DeFT_B')), ('the best of MTR and RC', ('MTR', 'RC'))):
        L += ['### Against %s' % gname, '', '| size | buffers of the references | `LB_noLA`: THR | LAT at 1.0 x Lsat | P99 | the main row: THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|---|---|---|']
        for z in RV.SIZES:
            for t, tname in (('', '4-flit (round 25)'), ('_d5', '5-flit'), ('_d6', '6-flit')):
                ref = tuple(b + t for b in g)
                cells = []
                for row in ('LB_noLA', RV.MAIN):
                    for n in ('THR', 'LAT', 'P99'):
                        x = D.test(row, ref, z, six(z), n)
                        cells.append(RV.eci(x))
                        rows.append(dict(size=z, row=row, against=gname, buffers=tname, metric=n, effect_pct=x['effect_pct'], ci_low=x['ci_low'], ci_high=x['ci_high'], n_seeds=x['n_seeds']))
                L.append('| %s | %s | %s |' % (z, tname, ' | '.join(cells)))
        L.append('')
    write('extra_E.md', L)
    with open(os.path.join(OUT, 'extra_E_noLA.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('wrote report/extra_E_noLA.csv (%d rows)' % len(rows))


def part_d():
    """X.6: D1 in the direction the question asks (what the per-hop VC choice gives), which reference is the best with each VC policy,
    and the main comparison per scenario. Added on 26 November after the results of D1 had been read (DECISIONS.md); no test."""
    import report_v29 as RV
    P = RV.ladders()
    f = os.path.join(RES, 'vc_static_runs.csv')
    if not os.path.exists(f):
        print('extra part d needs vc_static_runs.csv; not written')
        return
    R = RV.load(os.path.join(RV.V25, 'eval_runs.csv'), f)
    D = RV.Design(R, P, range(121, 131))
    six = lambda z: RV.scen(z, RV.SIX)  # noqa: E731
    S5 = ('DeFT_P', 'DeFT_B', 'MTR_static', 'RC_static', 'XY_SP')
    R5 = tuple(RV.REFS5)
    tri = lambda a, ref, so, n: ' / '.join(RV.eci(D.test(a, ref, z, so(z), n)) for z in RV.SIZES)  # noqa: E731
    L = ['# v29 Part D1: tables added after the results were seen (extra_v29.py d)', '',
         'Descriptive; not in the pre-registration and no test. Added on 26 November after the results of D1 had been read (`DECISIONS.md`, "Tables added after the results").',
         'Runs: `vc_static_runs.csv` (D1) and the rows of round 25, seeds 121-130; effect [95 % interval over the seeds]; 2x2 / 3x3 / 4x4.', '',
         '## X.6 One VC per packet for MTR and RC: what the per-hop choice gives, which reference is then the best, and the main comparison per scenario', '',
         '### The per-hop row against its static row (D.1.1 in the other direction: what the per-hop VC choice gives MTR and RC)', '',
         '| row | scenarios | THR | LAT at 0.5 x Lsat | LAT at 0.8 x Lsat | LAT at 1.0 x Lsat | LAT at 1.2 x Lsat | P99 |', '|---|---|---|---|---|---|---|---|']
    for b in ('MTR', 'RC'):
        L.append('| %s against %s_static | all six | %s |' % (b, b, ' | '.join(tri(b, b + '_static', six, n) for n in ('THR', 'LAT05', 'LAT08', 'LAT', 'LAT12', 'P99'))))
    for p in RV.SIX:
        so = lambda z, p=p: RV.scen(z, [p])  # noqa: E731
        for b in ('MTR', 'RC'):
            L.append('| %s against %s_static | %s | %s | | | %s | | %s |' % (b, b, p, tri(b, b + '_static', so, 'THR'), tri(b, b + '_static', so, 'LAT'), tri(b, b + '_static', so, 'P99')))
    L += ['', '### Which reference is the best of the five (the mean over the ten seeds)', '',
          '*static*: of DeFT_P, DeFT_B, `MTR_static`, `RC_static`, XY_SP; *per hop*: of DeFT_P, DeFT_B, MTR, RC, XY_SP (round 25).', '',
          '| size | metric | VC policy of MTR and RC | ' + ' | '.join(RV.SIX) + ' |', '|---|---|---|' + '---|' * len(RV.SIX)]
    count = {'static': defaultdict(int), 'per hop': defaultdict(int)}
    for z in RV.SIZES:
        for n in ('THR', 'LAT', 'P99'):
            for name, refs in (('static', S5), ('per hop', R5)):
                best = [D.best(refs, z, sc, n) for sc in six(z)]
                if n != 'P99':
                    for x in best:
                        count[name][x.replace('_static', '')] += 1
                L.append('| %s | %s | %s | %s |' % (z, n, name, ' | '.join(best)))
    L += ['', 'Counted over the 36 cells of size, scenario and metric (THR and LAT):', '', '| VC policy of MTR and RC | DeFT_P | DeFT_B | MTR | RC | XY_SP |', '|---|---|---|---|---|---|']
    for name in ('static', 'per hop'):
        L.append('| %s | %s |' % (name, ' | '.join(str(count[name][b]) for b in ('DeFT_P', 'DeFT_B', 'MTR', 'RC', 'XY_SP'))))
    L += ['', '### The main row against the best of the five, per scenario', '',
          '| scenario | THR: with static MTR and RC | with per-hop MTR and RC (round 25) | LAT at 1.0 x Lsat: with static MTR and RC | with per-hop MTR and RC (round 25) |', '|---|---|---|---|---|']
    for p in RV.SIX:
        so = lambda z, p=p: RV.scen(z, [p])  # noqa: E731
        L.append('| %s | %s | %s | %s | %s |' % (p, tri(RV.MAIN, S5, so, 'THR'), tri(RV.MAIN, R5, so, 'THR'), tri(RV.MAIN, S5, so, 'LAT'), tri(RV.MAIN, R5, so, 'LAT')))
    L += ['', 'The main row against each row alone, over the six scenarios:', '', '| against | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
    for ref in ('DeFT_P', 'DeFT_B', 'MTR_static', 'RC_static', 'MTR', 'RC', ('DeFT_P', 'DeFT_B')):
        L.append('| %s | %s |' % (RV.label(ref), ' | '.join(tri(RV.MAIN, ref, six, n) for n in ('THR', 'LAT', 'P99'))))
    L += ['', 'DeFT_P against each static row, over the six scenarios:', '', '| against | THR | LAT at 0.5 x Lsat | LAT at 0.8 x Lsat | LAT at 1.0 x Lsat | LAT at 1.2 x Lsat |', '|---|---|---|---|---|---|']
    for ref in ('MTR_static', 'RC_static'):
        L.append('| %s | %s |' % (ref, ' | '.join(tri('DeFT_P', ref, six, n) for n in ('THR', 'LAT05', 'LAT08', 'LAT', 'LAT12'))))
    rows = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'MTR_static', 'RC_static', RV.MAIN]
    L += ['', '### Absolute values: THR (flits/node/cycle) and mean latency at 1.0 x Lsat of DeFT_P (cycles), mean over the ten seeds', '',
          '| size | scenario | ' + ' | '.join(rows) + ' |', '|---|---|' + '---|' * len(rows)]
    for z in RV.SIZES:
        for sc in six(z):
            L.append('| %s | %s | %s |' % (z, sc[0], ' | '.join('%.4f; %.1f' % (D.smean(r, z, sc, 'THR'), D.smean(r, z, sc, 'LAT')) for r in rows)))
    L.append('')
    write('extra_D.md', L)


if __name__ == '__main__':
    parts = sys.argv[1:] or ['b']
    for p in parts:
        globals()['part_' + p]()
