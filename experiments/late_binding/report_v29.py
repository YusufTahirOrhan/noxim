"""v29 report, following results_v29_review/PREREGISTRATION.md.

Usage: python3 report_v29.py [b] [c] [d] [e] [f] [g] | all      (default: every part whose per-run CSVs exist)
  b  heldout_runs.csv, lb_b0_runs.csv (with results_v25_confirm/eval_runs.csv) -> report/primary_B.csv, secondary_B.csv, summary_B.md,
     paper_data/heldout_effects.csv, lb_b0.csv
  c  depth_runs.csv, ipos7_runs.csv, depth_fault_runs.csv (with the rows of rounds 25 and 26) -> report/primary_C.csv, secondary_C.csv,
     summary_C.md, paper_data/equal_area_effects.csv, equal_area_faults.csv
  d  vc_static_runs.csv, deft_setup_runs.csv -> report/summary_D.md, figures, paper_data/vc_policy.csv, deft_paper_setup.csv
  e  nola_runs.csv -> report/summary_E.md, paper_data/nola_effects.csv (the hardware tables come from report_v29_hw.py)
  f  early_first_runs.csv, early_age_runs.csv (with results_v28_anchor/eval_runs.csv) -> report/summary_F.md, paper_data/early_more.csv
  g  trace_runs.csv -> report/summary_G.md
report/summary.md is the concatenation of the parts that exist.

Effects are 100 x (exp(mean over seeds of R_s) - 1) %, R_s = mean over the scenarios of ln(metric_row / metric_reference) for seed s; 95 %
interval and two-sided one-sample t test over the seeds. THR = the largest accepted throughput over the loads; LAT and P99 at 1.0 x Lsat of
DeFT-P (4-flit buffers). The best of a set of rows per (size, scenario, metric): the row of the set with the best mean over the seeds.
The statistics (stat, holm, the verdicts) are those of report_v25.py; check_v29_family.py computes the two primary families again
without this code.
"""
import csv
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_v25 as R25  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get('V29_RES', os.path.join(HERE, 'results_v29_review'))
V25 = os.environ.get('V29_V25', os.path.join(HERE, 'results_v25_confirm'))
V26 = os.environ.get('V29_V26', os.path.join(HERE, 'results_v26_faults'))
V28 = os.environ.get('V29_V28', os.path.join(HERE, 'results_v28_anchor'))
OUT = os.path.join(RES, 'report')
PD = os.path.join(RES, 'paper_data')
SIZES = ['2x2', '3x3', '4x4']
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
MAIN = 'CI_heurLA_X_LF'
REFS4 = ['DeFT_P', 'DeFT_B', 'MTR', 'RC']
REFS5 = REFS4 + ['XY_SP']
DEFT2 = ['DeFT_P', 'DeFT_B']
MR2 = ['MTR', 'RC']
NEWP = ('tornado', 'neighbour', 'randperm')
TUNE4 = ('uniform', 'hotspot', 'chipperm', 'chiptrans')
OTHER2 = ('localized', 'movinghot')
SIX = ('uniform', 'localized', 'hotspot', 'chipperm', 'chiptrans', 'movinghot')
IDX = {'LAT': (3, 'latency'), 'P99': (3, 'p99'), 'LAT02': (0, 'latency'), 'LAT05': (1, 'latency'), 'LAT08': (2, 'latency'), 'LAT10': (3, 'latency'),
       'LAT12': (4, 'latency'), 'LAT14': (5, 'latency'), 'LAT16': (6, 'latency'), 'LAT20': (7, 'latency'), 'LAT24': (8, 'latency')}
NL = chr(10)
NAN = float('nan')
stat, holm, verdict, eci, fmt, mean, isnan, mci, write, side = R25.stat, R25.holm, R25.verdict, R25.eci, R25.fmt, R25.mean, R25.isnan, R25.mci, R25.write, R25.side


def ensure():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)


def wmd(name, L):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


def load(*paths):
    """{(row, size-pattern, mask, rate, seed): run} of several per-run CSVs (R25.load_runs; a key that is in two files must be the same run)."""
    R = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        for k, v in R25.load_runs(p).items():
            if k in R and (R[k]['accepted'], R[k]['latency']) != (v['accepted'], v['latency']):
                raise SystemExit('two different runs for %s (%s)' % (k, p))
            R[k] = v
    return R


def ladders():
    P = json.load(open(os.path.join(V25, 'load_points_v25.json')))
    f = os.path.join(RES, 'load_points_v29.json')
    if os.path.exists(f):
        P.update(json.load(open(f)))
    return P


def scen(z, patterns):
    return [(p, FREE[z]) for p in patterns]


def label(ref):
    return ref if isinstance(ref, str) else 'best of ' + ', '.join(ref)


class Design:
    """Runs on DeFT-P's ladders: rows x sizes x scenarios x loads x seeds. A reference is a row, or a tuple of rows: then the best of them
    per (size, scenario, metric) by the mean over the seeds. loads: the ladder indices THR is taken over."""

    def __init__(self, R, P, seeds, loads=range(9), pipe=2):
        self.R, self.P, self.seeds, self.loads, self.pipe = R, P, list(seeds), list(loads), pipe
        self._best = {}

    def lad(self, z, sc):
        return self.P['%s__%s__%s__p%d' % (z, sc[0], sc[1], self.pipe)]['eval']

    def run(self, row, z, sc, i, s):
        return self.R[(row, '%s-%s' % (z, sc[0]), sc[1], self.lad(z, sc)[i], s)]

    def val(self, row, z, sc, s, name):
        if name == 'THR':
            return max(self.run(row, z, sc, i, s)['accepted'] for i in self.loads)
        i, f = IDX[name]
        return self.run(row, z, sc, i, s)[f]

    def has(self, row, z, sc, s, name):
        try:
            self.val(row, z, sc, s, name)
            return True
        except KeyError:
            return False

    def smean(self, row, z, sc, name):
        return mean([self.val(row, z, sc, s, name) for s in self.seeds if self.has(row, z, sc, s, name)])

    def best(self, rows, z, sc, name):
        k = (tuple(rows), z, sc, name)
        if k not in self._best:
            m = {b: self.smean(b, z, sc, name) for b in rows}
            m = {b: v for b, v in m.items() if not isnan(v)}
            self._best[k] = (max if name == 'THR' else min)(m, key=m.get) if m else None
        return self._best[k]

    def pick(self, ref, z, sc, name):
        return ref if isinstance(ref, str) else self.best(ref, z, sc, name)

    def lr(self, a, ref, z, scs, name):
        """Per seed: the mean over the scenarios of ln(metric_a / metric_ref). A seed with a missing run in a scenario is left out."""
        out = []
        for s in self.seeds:
            try:
                rs = [math.log(self.val(self.pick(a, z, sc, name), z, sc, s, name) / self.val(self.pick(ref, z, sc, name), z, sc, s, name)) for sc in scs]
            except (KeyError, ValueError, ZeroDivisionError, TypeError):
                continue
            if rs:
                out.append(sum(rs) / len(rs))
        return out

    def test(self, a, ref, z, scs, name, group=''):
        return dict(size=z, row=label(a), reference=label(ref), metric=name, scenarios='+'.join(sc[0] for sc in scs), group=group, **stat(self.lr(a, ref, z, scs, name)))

    def missing(self, rows, sizes, scen_of, loads=None):
        return [(row, z, sc[0], i, s) for row in rows for z in sizes for sc in scen_of(z) for i in (self.loads if loads is None else loads) for s in self.seeds
                if (row, '%s-%s' % (z, sc[0]), sc[1], self.lad(z, sc)[i], s) not in self.R]

    def top_count(self, row, z, scs):
        """(cells in which the largest accepted throughput is at the last load, cells): a cell is a scenario and a seed."""
        n = t = 0
        for sc in scs:
            for s in self.seeds:
                try:
                    a = [self.run(row, z, sc, i, s)['accepted'] for i in self.loads]
                except KeyError:
                    continue
                n += 1
                t += a.index(max(a)) == len(a) - 1
        return t, n

    def after_peak(self, row, z, sc):
        """The lowest mean accepted throughput after the peak, relative to the peak (means over the seeds)."""
        m = [mean([self.run(row, z, sc, i, s)['accepted'] for s in self.seeds if (row, '%s-%s' % (z, sc[0]), sc[1], self.lad(z, sc)[i], s) in self.R]) for i in self.loads]
        k = max(range(len(m)), key=lambda i: m[i])
        return min(m[k:]) / m[k]

    def counter(self, row, z, scs, i, keys):
        t = {k: 0 for k in keys}
        n = 0
        for sc in scs:
            for s in self.seeds:
                try:
                    x = self.run(row, z, sc, i, s)
                except KeyError:
                    continue
                if x.get(keys[0]) is None:
                    continue
                n += 1
                for k in keys:
                    t[k] += x[k] or 0
        return t if n else None


def e3(D, a, ref, scen_of, name, group=''):
    """Effect [CI] on 2x2 / 3x3 / 4x4 as one table cell, and the three tests."""
    ts = [D.test(a, ref, z, scen_of(z), name, group) for z in SIZES]
    return ' / '.join(eci(t) for t in ts), ts


def holm_family(prim):
    for x, q in zip(prim, holm([1.0 if isnan(x['p']) else x['p'] for x in prim])):
        x['p_holm'] = q
        x['verdict'] = verdict(x)
    return prim


def count_line(prim):
    c = lambda vd: sum(1 for x in prim if x['verdict'] == vd)  # noqa: E731
    return '**Supported %d of %d; against %d; n.s. %d.**' % (c('supported'), len(prim), c('against'), c('n.s.'))


# =====================================================================================================================
# Part B: scenarios never used
# =====================================================================================================================
def part_b():
    ensure()
    P = ladders()
    Rn = load(os.path.join(RES, 'heldout_runs.csv'))
    Ro = load(os.path.join(V25, 'eval_runs.csv'), os.path.join(RES, 'lb_b0_runs.csv'))
    Dn = Design(Rn, P, range(181, 191))
    Do = Design(Ro, P, range(121, 131))
    new = lambda z: scen(z, NEWP)  # noqa: E731
    rows = REFS5 + [MAIN]
    miss = Dn.missing(rows, SIZES, new) + Dn.missing(['LB_b0'], ['2x2'], new) + Do.missing(['LB_b0'], ['2x2'], lambda z: scen(z, SIX))
    dead = sum(x['dead'] for x in Rn.values()) + sum(x['dead'] for k, x in Ro.items() if k[0] == 'LB_b0')
    L = ['# v29 Part B: scenarios never used (generated by report_v29.py)', '',
         'Runs: B1 %d of 5,130 (seeds 181-190), B2 %d of 540 (`LB_b0` on 2x2, seeds 121-130); missing %d; dead-end events %d.' % (
             len(Rn), sum(1 for k in Ro if k[0] == 'LB_b0'), len(miss), dead),
         'pipe_all 2; the three scenarios `tornado`, `neighbour` and `randperm` (fault-free), which no earlier round ran and which the tuning of round 24 never saw.',
         'Loads: the nine points of DeFT-P\'s ladders (`load_points_v29.md`). **THR** = the largest accepted throughput over the nine loads; **LAT** and **P99** at',
         '1.0 x Lsat of DeFT-P. Effects in per cent (THR positive = higher, LAT and P99 negative = lower) with the 95 % interval over the ten seeds. **The best of a set',
         'of references** is taken per size, scenario and metric by the mean over the seeds. Only the primary table is adjusted (Holm); every other interval is',
         'unadjusted and descriptive.', '']
    if miss:
        L += ['Missing runs (a seed with a missing run in a scenario of a comparison is left out of that comparison): ' + '; '.join('%s %s %s load %d s%d' % m for m in miss[:30]), '']

    # ---- primary family 1 ----
    prim = []
    for z in SIZES:
        for ref, g in (('DeFT_P', 'a'), (tuple(REFS5), 'b')):
            for n in ('THR', 'LAT'):
                prim.append(Dn.test(MAIN, ref, z, new(z), n, g))
    holm_family(prim)
    write(os.path.join(OUT, 'primary_B.csv'), prim)
    L += ['## B.1 Primary family 1 (Holm over 12): the main row against (a) DeFT_P and (b) the best of the five references, over the three new scenarios', '',
          '| size | against | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|']
    for x in prim:
        L.append('| %s | (%s) %s | %s | %s | **%s** |' % (x['size'], x['group'], 'DeFT_P' if x['group'] == 'a' else 'the best of DeFT_P, DeFT_B, MTR, RC, XY_SP', x['metric'],
                                                    fmt(x, 'p_holm'), x['verdict']))
    L += ['', count_line(prim), '']

    sec = list(prim)
    # ---- per scenario ----
    L += ['## B.2 Per scenario: the main row against DeFT_P and against the best of the five references (effect [95 % CI]; 2x2 / 3x3 / 4x4)', '',
          '| scenario | metric | against DeFT_P | against the best reference | the best reference (2x2, 3x3, 4x4) |', '|---|---|---|---|---|']
    for p in NEWP + ('all three',):
        so = (lambda z: scen(z, NEWP)) if p == 'all three' else (lambda z, p=p: scen(z, [p]))
        for n in ('THR', 'LAT', 'P99'):
            a, ta = e3(Dn, MAIN, 'DeFT_P', so, n)
            b, tb = e3(Dn, MAIN, tuple(REFS5), so, n)
            sec += ta + tb
            bb = '' if p == 'all three' else ', '.join(str(Dn.best(REFS5, z, so(z)[0], n)) for z in SIZES)
            L.append('| %s | %s | %s | %s | %s |' % (p, n, a, b, bb))
    L.append('')

    # ---- against the two kinds of references ----
    L += ['## B.3 Against the references that tolerate VL faults (the best of DeFT_P and DeFT_B) and against the best of MTR and RC (2x2 / 3x3 / 4x4)', '',
          '| scenario | metric | against the best of DeFT_P, DeFT_B | against the best of MTR, RC | against XY_SP |', '|---|---|---|---|---|']
    for p in NEWP + ('all three',):
        so = (lambda z: scen(z, NEWP)) if p == 'all three' else (lambda z, p=p: scen(z, [p]))
        for n in ('THR', 'LAT', 'P99'):
            cells = []
            for ref in (tuple(DEFT2), tuple(MR2), 'XY_SP'):
                c, ts = e3(Dn, MAIN, ref, so, n)
                sec += ts
                cells.append(c)
            L.append('| %s | %s | %s |' % (p, n, ' | '.join(cells)))
    L.append('')
    L += ['Every row against DeFT_P over the three new scenarios (2x2 / 3x3 / 4x4):', '', '| row | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
    for row in ['DeFT_B', 'MTR', 'RC', 'XY_SP', MAIN]:
        cells = []
        for n in ('THR', 'LAT', 'P99'):
            c, ts = e3(Dn, row, 'DeFT_P', new, n)
            sec += ts
            cells.append(c)
        L.append('| %s | %s |' % (row, ' | '.join(cells)))
    L.append('')

    # ---- below saturation ----
    L += ['## B.4 Latency below saturation: the main row at 0.2, 0.5 and 0.8 x Lsat, over the three new scenarios (2x2 / 3x3 / 4x4)', '',
          'The best reference is taken per scenario at each load.', '', '| load | against DeFT_P | against the best of the five references | per scenario against the best reference: tornado; neighbour; randperm |', '|---|---|---|---|']
    for n, t in (('LAT02', '0.2'), ('LAT05', '0.5'), ('LAT08', '0.8')):
        a, ta = e3(Dn, MAIN, 'DeFT_P', new, n)
        b, tb = e3(Dn, MAIN, tuple(REFS5), new, n)
        sec += ta + tb
        per = []
        for p in NEWP:
            c, ts = e3(Dn, MAIN, tuple(REFS5), lambda z, p=p: scen(z, [p]), n)
            sec += ts
            per.append(c)
        L.append('| %s x Lsat | %s | %s | %s |' % (t, a, b, '; '.join(per)))
    L.append('')

    # ---- the five scenarios that the tuning never saw ----
    five = [(p, Dn) for p in NEWP] + [(p, Do) for p in OTHER2]
    untuned = []
    L += ['## B.5 The five scenarios that the tuning never saw, taken together', '',
          'The three new scenarios (seeds 181-190) and localized and movinghot of round 25 (seeds 121-130, `results_v25_confirm/eval_runs.csv`), each on its own seeds.',
          'Per scenario the effect of the main row with its interval; then the mean of the five per-scenario effects (the mean of the five mean log ratios, as a',
          'percentage) and their range. No test.', '']
    for ref, title in ((tuple(REFS5), 'the best of the five references'), (tuple(DEFT2), 'the best of DeFT_P and DeFT_B'), (tuple(MR2), 'the best of MTR and RC'), ('DeFT_P', 'DeFT_P')):
        L += ['Against **%s**:' % title, '', '| size | metric | ' + ' | '.join(p for p, _ in five) + ' | mean of the five | range |', '|---|---|' + '---|' * 7]
        for z in SIZES:
            for n in ('THR', 'LAT', 'P99'):
                ts = [D.test(MAIN, ref, z, scen(z, [p]), n, 'untuned') for p, D in five]
                ms = [mean(D.lr(MAIN, ref, z, scen(z, [p]), n)) for p, D in five]
                m = 100.0 * (math.exp(mean(ms)) - 1.0)
                lo, hi = min(t['effect_pct'] for t in ts), max(t['effect_pct'] for t in ts)
                untuned.append(dict(size=z, row=MAIN, reference=label(ref), metric=n, scenarios='+'.join(p for p, _ in five), group='five untuned', n_seeds='',
                                    effect_pct=round(m, 2), ci_low='', ci_high='', p='', range_low=lo, range_high=hi))
                sec += ts
                L.append('| %s | %s | %s | **%+.1f** | %+.1f to %+.1f |' % (z, n, ' | '.join(eci(t) for t in ts), m, lo, hi))
        L.append('')

    # ---- LB_b0 ----
    lb0 = []
    L += ['## B.6 `LB_b0` on 2x2: the main row with `lut_bias 0` (the value of 3x3 and 4x4) instead of 2', '',
          '| scenarios | seeds | metric | `LB_b0` against the main row | `LB_b0` against the best reference | the main row against the best reference |', '|---|---|---|---|---|---|']
    groups = [('the three new scenarios', Dn, NEWP, '181-190')] + [(p, Dn, (p,), '181-190') for p in NEWP] + [
        ('the six of round 25', Do, SIX, '121-130'), ('the four tuning scenarios', Do, TUNE4, '121-130'), ('localized and movinghot', Do, OTHER2, '121-130')] + [
        (p, Do, (p,), '121-130') for p in SIX]
    for title, D, pats, sd in groups:
        scs = scen('2x2', pats)
        for n in ('THR', 'LAT', 'P99', 'LAT05'):
            a, b, c = D.test('LB_b0', MAIN, '2x2', scs, n, title), D.test('LB_b0', tuple(REFS5), '2x2', scs, n, title), D.test(MAIN, tuple(REFS5), '2x2', scs, n, title)
            lb0 += [a, b, c]
            L.append('| %s | %s | %s | %s | %s | %s |' % (title, sd, n, eci(a), eci(b), eci(c)))
    L.append('')

    # ---- where THR is a lower bound, and beyond the peak ----
    L += ['## B.7 The largest accepted throughput at the last load, and the accepted throughput beyond the peak', '',
          'Cells (scenario x seed, 30 per size and row) in which the largest accepted throughput is at 2.4 x Lsat: THR is then a lower bound. Beyond the peak: the lowest',
          'mean accepted throughput after the peak, relative to the peak (mean over the three scenarios; the worst scenario in brackets).', '',
          '| size | row | THR at the last load | lowest point after the peak |', '|---|---|---|---|']
    for z in SIZES:
        for row in rows + (['LB_b0'] if z == '2x2' else []):
            t, n = Dn.top_count(row, z, new(z))
            ap = [(Dn.after_peak(row, z, sc), sc[0]) for sc in new(z)]
            L.append('| %s | %s | %d of %d | %.3f (worst %.3f, %s) |' % (z, row, t, n, mean(a for a, _ in ap), min(ap)[0], min(ap)[1]))
    L.append('')

    # ---- hops with a choice ----
    L += ['## B.8 Hops with a choice of the main row at 1.0 x Lsat (counters summed over the seeds; 2x2 / 3x3 / 4x4)', '',
          '| scenario | hops per packet | hops with more than one offered output per packet | of them left through another output than the stored one |', '|---|---|---|---|']
    keys = ('hops_chip', 'hops_chip_multi', 'hops_ipos', 'hops_ipos_multi', 'lookahead_multi', 'lookahead_fb_taken', 'packets_measured')
    for p in NEWP:
        c1, c2, c3 = [], [], []
        for z in SIZES:
            t = Dn.counter(MAIN, z, scen(z, [p]), 3, keys)
            if not t or not t['packets_measured']:
                c1.append('n/a'), c2.append('n/a'), c3.append('n/a')
                continue
            c1.append('%.2f' % ((t['hops_chip'] + t['hops_ipos']) / float(t['packets_measured'])))
            c2.append('%.2f' % ((t['hops_chip_multi'] + t['hops_ipos_multi']) / float(t['packets_measured'])))
            c3.append(R25.pc(t['lookahead_fb_taken'], t['lookahead_multi']) if t['lookahead_multi'] else '-')
        L.append('| %s | %s | %s | %s |' % (p, ' / '.join(c1), ' / '.join(c2), ' / '.join(c3)))
    L.append('')

    # ---- absolute values ----
    absr = []
    L += ['## B.9 Absolute values (mean over the seeds): THR in flits/node/cycle, LAT and P99 in cycles at 1.0 x Lsat', '']
    for z in SIZES:
        rz = rows + (['LB_b0'] if z == '2x2' else [])
        L += ['### %s' % z, '', '| scenario | ' + ' | '.join(rz) + ' |', '|---|' + '---|' * len(rz)]
        for sc in new(z):
            cells = []
            for row in rz:
                rec = dict(size=z, row=row, scenario=sc[0])
                for n in ('THR', 'LAT', 'P99', 'LAT02', 'LAT05', 'LAT08'):
                    m, lo, hi = mci([Dn.val(row, z, sc, s, n) for s in Dn.seeds if Dn.has(row, z, sc, s, n)])
                    rec[n], rec[n + '_ci_low'], rec[n + '_ci_high'] = [round(x, 5) if not isnan(x) else '' for x in (m, lo, hi)]
                absr.append(rec)
                cells.append('%.4f / %.0f / %.0f' % (rec['THR'], rec['LAT'], rec['P99']) if rec['THR'] != '' else '-')
            L.append('| %s | %s |' % (sc[0], ' | '.join(cells)))
        L.append('')
    write(os.path.join(OUT, 'secondary_B.csv'), sec + untuned)
    write(os.path.join(OUT, 'absolute_B.csv'), absr)
    wmd('summary_B.md', L)

    # ---- paper data ----
    os.makedirs(PD, exist_ok=True)
    out = []
    for z in SIZES:
        for p in NEWP + ('all three',):
            scs = scen(z, NEWP if p == 'all three' else [p])
            for ref in ('DeFT_P', tuple(REFS5), tuple(DEFT2), tuple(MR2)):
                for n in ('THR', 'LAT', 'P99'):
                    t = Dn.test(MAIN, ref, z, scs, n)
                    q = [x for x in prim if p == 'all three' and x['size'] == z and x['metric'] == n and x['reference'] == label(ref)]
                    out.append(dict(size=z, scenario=p, comparison='main row against ' + label(ref), metric=n, effect_pct=t['effect_pct'], ci_low=t['ci_low'], ci_high=t['ci_high'],
                                    p=t['p'], p_holm=q[0]['p_holm'] if q else '', verdict=q[0]['verdict'] if q else '',
                                    best_reference='' if isinstance(ref, str) or p == 'all three' else Dn.best(ref, z, scs[0], n), seeds='181-190'))
    for u in untuned:
        out.append(dict(size=u['size'], scenario='the five untuned (tornado, neighbour, randperm, localized, movinghot)', comparison='main row against ' + u['reference'], metric=u['metric'],
                        effect_pct=u['effect_pct'], ci_low=u['range_low'], ci_high=u['range_high'], p='', p_holm='', verdict='',
                        best_reference='mean of the five per-scenario effects; ci_low and ci_high are the range of the five', seeds='181-190 and 121-130'))
    write(os.path.join(PD, 'heldout_effects.csv'), out)
    write(os.path.join(PD, 'lb_b0.csv'), [dict(size=x['size'], scenarios=x['group'], row=x['row'], reference=x['reference'], metric=x['metric'], effect_pct=x['effect_pct'],
                                              ci_low=x['ci_low'], ci_high=x['ci_high'], p=x['p'], n_seeds=x['n_seeds']) for x in lb0])
    return L


# =====================================================================================================================
# Part C: references with the area of the main row
# =====================================================================================================================
D6 = ['%s_d6' % r for r in REFS4]
D5 = ['%s_d5' % r for r in REFS4]
I7 = ['%s_i7' % r for r in REFS4]
SETS = [('d6', '6-flit buffers', D6), ('d5', '5-flit buffers', D5), ('i7', '7-flit buffers in the interposer routers', I7), ('d4', '4-flit buffers (round 25)', REFS4)]
FORMS = (('hier', 'hierarchy kept'), ('semi', 'core kept'), ('flat', 'flattened'))


def area_ratios():
    """{(design, size, form): system area relative to DeFT at depth 4} from hw/system_ratios.csv (report_v29_hw.py), if it exists."""
    f = os.path.join(RES, 'hw', 'system_ratios.csv')
    if not os.path.exists(f):
        return {}
    return {(r['design'], r['size'], r['form']): float(r['ratio']) for r in csv.DictReader(open(f))}


def area_cell(A, design):
    """hierarchy kept / core kept / flattened on 2x2 and 4x4 (3x3: the routers of 4x4), or 'not measured yet'."""
    if not A:
        return 'E3 not run yet'
    out = []
    for z in ('2x2', '3x3', '4x4'):
        v = [A.get((design, z, f)) for f, _ in FORMS]
        out.append(' / '.join('%.3f' % x if x is not None else '-' for x in v))
    return '; '.join(out)


class Faults:
    """The design of round 26 (unit = mask): V_m = the mean over the traffic patterns and the two seeds of ln(metric_A / metric_B)."""
    SEEDS = (151, 152)
    PATS = ('uniform', 'hotspot')

    def __init__(self, R):
        self.R = R
        self.P = json.load(open(os.path.join(V26, 'load_points_v26.json')))
        self.masks = json.load(open(os.path.join(V26, 'masks_v26.json')))['part_b']
        self._best = {}

    def val(self, row, e, p, s, name):
        lad = self.P['%s__%s__%s' % (e['size'], p, e['mask'])]['eval']
        runs = [self.R[(row, '%s-%s' % (e['size'], p), e['mask'], r, s)] for r in lad]
        if name == 'THR':
            return max(x['accepted'] for x in runs)
        return runs[1]['latency' if name == 'LAT' else 'p99']

    def best(self, rows, e, p, name):
        k = (tuple(rows), e['size'], e['mask'], p, name)
        if k not in self._best:
            m = {b: mean([self.val(b, e, p, s, name) for s in self.SEEDS]) for b in rows}
            self._best[k] = (max if name == 'THR' else min)(m, key=m.get)
        return self._best[k]

    def pick(self, ref, e, p, name):
        return ref if isinstance(ref, str) else self.best(ref, e, p, name)

    def test(self, a, ref, z, rate, name, pats=None):
        pats = pats or self.PATS
        vm = []
        for e in self.masks:
            if e['size'] != z or e['rate'] != rate:
                continue
            try:
                vm.append(mean([math.log(self.val(self.pick(a, e, p, name), e, p, s, name) / self.val(self.pick(ref, e, p, name), e, p, s, name)) for p in pats for s in self.SEEDS]))
            except KeyError:
                continue
        x = stat(vm)
        x['n_masks'] = x.pop('n_seeds')
        return dict(size=z, rate=rate, traffic='+'.join(pats), row=label(a), reference=label(ref), metric=name, **x)


def part_c():
    ensure()
    P = ladders()
    R = load(os.path.join(V25, 'eval_runs.csv'), os.path.join(RES, 'depth_runs.csv'), os.path.join(RES, 'ipos7_runs.csv'))
    D = Design(R, P, range(121, 131))
    D4 = Design(R, P, range(121, 131), loads=(1, 3, 5, 7))      # every comparison with an X_i7 row: THR over the four loads of C2
    A = area_ratios()
    six = lambda z: scen(z, SIX)  # noqa: E731
    t4 = lambda z: scen(z, TUNE4)  # noqa: E731
    o2 = lambda z: scen(z, OTHER2)  # noqa: E731
    have = lambda rows: all((r, '2x2-uniform', FREE['2x2'], D.lad('2x2', ('uniform', FREE['2x2']))[3], 121) in R for r in rows)  # noqa: E731
    has_i7, has_d5, has_lb6 = have(I7), have(D5), have(['LB_d6'])
    miss = D.missing(D6, SIZES, six) + (D.missing(D5, SIZES, six) if has_d5 else []) + (D.missing(['LB_d6'], SIZES, six) if has_lb6 else []) + (
        D4.missing(I7, SIZES, six) if has_i7 else [])
    new_rows = D6 + D5 + I7 + ['LB_d6']
    n_new = sum(1 for k in R if k[0] in new_rows)
    dead = sum(x['dead'] for k, x in R.items() if k[0] in new_rows)
    L = ['# v29 Part C: references with the area of the main row (generated by report_v29.py)', '',
         'New runs: %d (C1: the four references at depth 6%s%s; C2: %s); missing %d; dead-end events %d. The main row and the references at depth 4 are the runs of round 25' % (
             n_new, ', at depth 5' if has_d5 else ' (depth 5: not run)', ', `LB_d6`' if has_lb6 else ' (`LB_d6`: not run)',
             'the four references with interposer depth 7 on four loads' if has_i7 else 'not run', len(miss), dead),
         '(`results_v25_confirm/eval_runs.csv`; `reuse_check.md`). Seeds 121-130, the six fault-free scenarios of round 25, the ladders of DeFT_P at depth 4, so that every row',
         'is measured at the same loads. **THR** = the largest accepted throughput over the nine loads (over the four loads 0.5, 1.0, 1.4, 2.0 x Lsat in every comparison',
         'with an `X_i7` row, for both rows); **LAT** and **P99** at 1.0 x Lsat of DeFT_P at depth 4. Effects in per cent with the 95 % interval over the ten seeds. Only the',
         'primary table is adjusted (Holm).', '',
         'Area of all routers of a system relative to DeFT with 4-flit buffers (E3; hierarchy kept / core kept / flattened; 2x2; 3x3; 4x4):', '',
         '| design | area ratio |', '|---|---|',
         '| the main row | %s |' % area_cell(A, 'main'), '| references with 5-flit buffers (`X_d5`) | %s |' % area_cell(A, 'd5'),
         '| references with 6-flit buffers (`X_d6`) | %s |' % area_cell(A, 'd6'), '| references with 7-flit buffers in the interposer routers (`X_i7`) | %s |' % area_cell(A, 'i7'), '']
    if miss:
        L += ['Missing runs: ' + '; '.join('%s %s %s load %d s%d' % m for m in miss[:30]), '']

    # ---- primary family 2 ----
    prim = []
    for z in SIZES:
        for ref, g in ((('DeFT_P_d6', 'DeFT_B_d6'), 'a'), (tuple(D6), 'b')):
            for n in ('THR', 'LAT'):
                prim.append(D.test(MAIN, ref, z, six(z), n, g))
    holm_family(prim)
    write(os.path.join(OUT, 'primary_C.csv'), prim)
    L += ['## C.1 Primary family 2 (Holm over 12): the main row at depth 4 against (a) the best of `DeFT_P_d6` and `DeFT_B_d6` and (b) the best of the four references at depth 6', '',
          '| size | against | metric | effect [95 % CI] (p Holm) | verdict |', '|---|---|---|---|---|']
    for x in prim:
        L.append('| %s | (%s) the best of %s | %s | %s | **%s** |' % (x['size'], x['group'], 'DeFT_P_d6, DeFT_B_d6' if x['group'] == 'a' else 'DeFT_P_d6, DeFT_B_d6, MTR_d6, RC_d6', x['metric'],
                                                              fmt(x, 'p_holm'), x['verdict']))
    L += ['', count_line(prim), '']
    sec = list(prim)

    # ---- what the buffers buy a reference ----
    L += ['## C.2 What the buffers buy a reference: each reference against itself with 4-flit buffers (six scenarios; 2x2 / 3x3 / 4x4)', '',
          '| reference | buffers | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|']
    for b in REFS4:
        for tag, title, rows in SETS[:3]:
            if (tag == 'd5' and not has_d5) or (tag == 'i7' and not has_i7):
                continue
            DD = D4 if tag == 'i7' else D
            cells = []
            for n in ('THR', 'LAT', 'P99'):
                c, ts = e3(DD, '%s_%s' % (b, tag), b, six, n, 'buffers')
                sec += ts
                cells.append(c)
            L.append('| %s | %s%s | %s |' % (b, title, ' (THR over four loads)' if tag == 'i7' else '', ' | '.join(cells)))
    L += ['', 'Per scenario, THR of each reference at depth 6 against itself at depth 4 (2x2 / 3x3 / 4x4):', '', '| scenario | ' + ' | '.join(REFS4) + ' |', '|---|' + '---|' * 4]
    for p in SIX:
        L.append('| %s | %s |' % (p, ' | '.join(e3(D, b + '_d6', b, lambda z, p=p: scen(z, [p]), 'THR')[0] for b in REFS4)))
    L.append('')

    # ---- the main row against each set ----
    sets = [(t, ti, rows) for t, ti, rows in SETS if not ((t == 'd5' and not has_d5) or (t == 'i7' and not has_i7))]
    ea = []
    L += ['## C.3 The main row (4-flit buffers) against the references of each depth, over the six scenarios (2x2 / 3x3 / 4x4)', '',
          'In the rows with `X_i7` THR is the largest accepted throughput over the four loads of C2 for both rows; the last line of each block repeats the comparison at depth 4',
          'with that THR, so that the two can be read next to each other.', '',
          '| buffers of the references | against | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|---|']
    for tag, title, rows in sets:
        DD = D4 if tag == 'i7' else D
        deft = tuple(r for r in rows if r.startswith('DeFT'))
        mr = tuple(r for r in rows if not r.startswith('DeFT'))
        for ref, name in ((deft, 'the best of the two DeFT variants'), (mr, 'the best of MTR and RC'), (tuple(rows), 'the best of the four')) + tuple((r, r) for r in rows):
            cells = []
            for n in ('THR', 'LAT', 'P99'):
                c, ts = e3(DD, MAIN, ref, six, n, tag)
                sec += ts
                cells.append(c)
                for t in ts:
                    ea.append(dict(size=t['size'], reference_set=tag, buffers=title, against=name, scenarios='all six', metric=n, effect_pct=t['effect_pct'], ci_low=t['ci_low'],
                                   ci_high=t['ci_high'], p=t['p'], thr_over='four loads' if tag == 'i7' else 'nine loads'))
            L.append('| %s | %s | %s |' % (title, name, ' | '.join(cells)))
        if tag == 'i7':
            for ref, name in ((tuple(DEFT2), 'depth 4, THR over four loads: the best of the two DeFT variants'), (tuple(REFS4), 'depth 4, THR over four loads: the best of the four')):
                L.append('| %s | %s | %s |' % ('4-flit buffers (round 25)', name, ' | '.join(e3(D4, MAIN, ref, six, n)[0] for n in ('THR', 'LAT', 'P99'))))
    L.append('')

    # ---- tuning four / other two / each scenario ----
    L += ['## C.4 By group of scenarios: the main row against the best of the two DeFT variants and against the best of the four references (2x2 / 3x3 / 4x4)', '',
          '| buffers of the references | scenarios | metric | against the best DeFT variant | against the best of the four |', '|---|---|---|---|---|']
    for tag, title, rows in sets:
        DD = D4 if tag == 'i7' else D
        deft = tuple(r for r in rows if r.startswith('DeFT'))
        for gname, so in [('the four tuning scenarios', t4), ('localized and movinghot', o2)] + [(p, (lambda z, p=p: scen(z, [p]))) for p in SIX]:
            for n in ('THR', 'LAT'):
                a, ta = e3(DD, MAIN, deft, so, n, tag)
                b, tb = e3(DD, MAIN, tuple(rows), so, n, tag)
                sec += ta + tb
                for name, ts in (('the best of the two DeFT variants', ta), ('the best of the four', tb)):
                    for t in ts:
                        ea.append(dict(size=t['size'], reference_set=tag, buffers=title, against=name, scenarios=gname, metric=n, effect_pct=t['effect_pct'], ci_low=t['ci_low'],
                                       ci_high=t['ci_high'], p=t['p'], thr_over='four loads' if tag == 'i7' else 'nine loads'))
                L.append('| %s | %s | %s | %s | %s |' % (title, gname, n, a, b))
    L.append('')

    # ---- LB_d6 ----
    if has_lb6:
        L += ['## C.5 `LB_d6`: the main row with 6-flit buffers (nothing retuned), over the six scenarios (2x2 / 3x3 / 4x4)', '',
              '| against | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
        for ref, name in ((MAIN, 'the main row (4-flit buffers)'), (('DeFT_P_d6', 'DeFT_B_d6'), 'the best of `DeFT_P_d6`, `DeFT_B_d6`'), (('MTR_d6', 'RC_d6'), 'the best of `MTR_d6`, `RC_d6`'),
                          (tuple(D6), 'the best of the four references at depth 6'), ('DeFT_P_d6', '`DeFT_P_d6`')):
            cells = []
            for n in ('THR', 'LAT', 'P99'):
                c, ts = e3(D, 'LB_d6', ref, six, n, 'LB_d6')
                sec += ts
                cells.append(c)
                for t in ts:
                    ea.append(dict(size=t['size'], reference_set='LB_d6', buffers='6-flit buffers on both sides', against=name.replace('`', ''), scenarios='all six', metric=n,
                                   effect_pct=t['effect_pct'], ci_low=t['ci_low'], ci_high=t['ci_high'], p=t['p'], thr_over='nine loads'))
            L.append('| %s | %s |' % (name, ' | '.join(cells)))
        L += ['', 'For comparison, the main row against the best of the four references, both with 4-flit buffers (round 25, the same six scenarios): THR %s; LAT %s; P99 %s.' % tuple(
            e3(D, MAIN, tuple(REFS4), six, n)[0] for n in ('THR', 'LAT', 'P99')), '',
              '`LB_d6` against the best of the four references at depth 6, by group of scenarios:', '', '| scenarios | THR | LAT at 1.0 x Lsat |', '|---|---|---|']
        for gname, so in [('the four tuning scenarios', t4), ('localized and movinghot', o2)] + [(p, (lambda z, p=p: scen(z, [p]))) for p in SIX]:
            L.append('| %s | %s | %s |' % (gname, e3(D, 'LB_d6', tuple(D6), so, 'THR')[0], e3(D, 'LB_d6', tuple(D6), so, 'LAT')[0]))
        L.append('')

    # ---- below saturation ----
    L += ['## C.6 Latency at 0.5 and 0.8 x Lsat: the main row against the best of the four references of each depth (the best per scenario at that load; 2x2 / 3x3 / 4x4)', '',
          '| buffers of the references | at 0.5 x Lsat | at 0.8 x Lsat | at 1.0 x Lsat |', '|---|---|---|---|']
    for tag, title, rows in sets:
        cells = []
        for n in ('LAT05', 'LAT08', 'LAT'):
            c, ts = e3(D, MAIN, tuple(rows), six, n, tag)
            sec += ts
            cells.append(c)
        L.append('| %s | %s |' % (title, ' | '.join(cells)))
    L.append('')

    # ---- THR at the last load ----
    L += ['## C.7 The largest accepted throughput at the last load (cells of scenario x seed, 60 per size and row; THR is then a lower bound)', '',
          '| row | 2x2 | 3x3 | 4x4 |', '|---|---|---|---|']
    for row in [MAIN] + REFS4 + D6 + (D5 if has_d5 else []) + (['LB_d6'] if has_lb6 else []):
        L.append('| %s | %s |' % (row, ' | '.join('%d of %d' % D.top_count(row, z, six(z)) for z in SIZES)))
    L.append('')

    # ---- C3: under faults ----
    ff = os.path.join(RES, 'depth_fault_runs.csv')
    fa = []
    if os.path.exists(ff):
        Rf = load(os.path.join(V26, 'fault_rate_runs.csv'), ff)
        F = Faults(Rf)
        rates = [r for r in ('1/16', '4/16') if any(k[0] == 'DeFT_P_d6' and (k[1].split('-')[0], k[2]) in {(e['size'], e['mask']) for e in F.masks if e['rate'] == r} for k in Rf)]
        nf = sum(1 for k in Rf if k[0] in ('DeFT_P_d6', 'DeFT_B_d6'))
        deadf = sum(x['dead'] for k, x in Rf.items() if k[0] in ('DeFT_P_d6', 'DeFT_B_d6'))
        L += ['## C.8 Under random VL faults (C3): the main row at depth 4 against the DeFT variants at depth 6', '',
              'New runs: %d (`DeFT_P_d6`, `DeFT_B_d6` on the masks of the rates %s of round 26, uniform and hotspot traffic, four loads, seeds 151 and 152); dead-end events %d.' % (
                  nf, ' and '.join(rates), deadf),
              'The main row and the variants at depth 4 are the runs of round 26. Unit = mask (16 per size and rate): the value of a mask is the mean over the two traffic patterns',
              'and the two seeds of ln(metric_A / metric_B); the best variant per mask, traffic and metric by the mean of the two seeds. THR = the largest accepted throughput over',
              'the four loads; LAT at 1.0 x Lsat of DeFT_P on the mask. Effect [95 % interval over the masks]. Descriptive.', '',
              '| size | rate | traffic | metric | against the best of `DeFT_P_d6`, `DeFT_B_d6` | against `DeFT_P_d6` | against `DeFT_B_d6` | at depth 4 (round 26): against the best of DeFT_P, DeFT_B |',
              '|---|---|---|---|---|---|---|---|']
        for z in SIZES:
            for rate in rates:
                for pats in (None, ('uniform',), ('hotspot',)):
                    for n in ('THR', 'LAT'):
                        ts = [F.test(MAIN, ref, z, rate, n, pats) for ref in (('DeFT_P_d6', 'DeFT_B_d6'), 'DeFT_P_d6', 'DeFT_B_d6', ('DeFT_P', 'DeFT_B'))]
                        fa += ts
                        L.append('| %s | %s | %s | %s | %s |' % (z, rate, 'both' if pats is None else pats[0], n, ' | '.join(eci(t) for t in ts)))
        L += ['', 'What 6-flit buffers buy a DeFT variant under faults (each against itself at depth 4; both traffic patterns):', '',
              '| size | rate | `DeFT_P_d6`: THR | LAT | `DeFT_B_d6`: THR | LAT |', '|---|---|---|---|---|---|']
        for z in SIZES:
            for rate in rates:
                ts = [F.test(b + '_d6', b, z, rate, n) for b in ('DeFT_P', 'DeFT_B') for n in ('THR', 'LAT')]
                fa += ts
                L.append('| %s | %s | %s |' % (z, rate, ' | '.join(eci(t) for t in ts)))
        L.append('')
    write(os.path.join(OUT, 'secondary_C.csv'), sec)
    wmd('summary_C.md', L)

    # ---- paper data ----
    for x in ea:
        for f, _ in FORMS:
            x['area_ratio_' + f] = A.get((x['reference_set'] if x['reference_set'] != 'LB_d6' else 'main_d6', x['size'], f), '') if x['reference_set'] != 'd4' else 1.0
            x['area_ratio_main_' + f] = A.get(('main', x['size'], f), '')
    for x in prim:
        for y in ea:
            if y['reference_set'] == 'd6' and y['scenarios'] == 'all six' and y['size'] == x['size'] and y['metric'] == x['metric'] and \
                    y['against'] == ('the best of the two DeFT variants' if x['group'] == 'a' else 'the best of the four'):
                y['primary_p_holm'], y['primary_verdict'] = x['p_holm'], x['verdict']
    write(os.path.join(PD, 'equal_area_effects.csv'), ea)
    if fa:
        write(os.path.join(PD, 'equal_area_faults.csv'), fa)
    return L


# =====================================================================================================================
# Part D: the references against the DeFT paper
# =====================================================================================================================
STATIC = ['MTR_static', 'RC_static']
D2_ROWS = ['DeFT_P', 'MTR', 'RC', 'MTR_static', 'RC_static']
D2_PATTERNS = ('uniform', 'localized', 'hotspot')
LOADN = ['LAT02', 'LAT05', 'LAT08', 'LAT10', 'LAT12', 'LAT14', 'LAT16', 'LAT20', 'LAT24']


def d2_rates(P, p, pipe):
    """The twelve rates of D2 (experiments_v29_eval.d2_rates): k / 10 x Lsat of DeFT_P, rounded to the 0.0001 grid, halves up."""
    u = int(round(P['2x2__%s__%s__p%d' % (p, FREE['2x2'], pipe)]['lsat'] * 10000))
    out = []
    for k in range(1, 13):
        x = (k * u + 5) // 10
        if out and x <= out[-1]:
            x = out[-1] + 1
        out.append(x)
    return [round(x / 10000.0, 4) for x in out]


def lowest_word(t):
    """How DeFT_P stands against the better of the two others at a load: its effect in latency and what the interval says."""
    if isnan(t['effect_pct']):
        return 'n/a'
    if t['effect_pct'] < 0:
        return 'lowest' if t['ci_high'] < 0 else 'lowest, within the interval'
    return 'not the lowest' if t['ci_low'] > 0 else 'not the lowest, within the interval'


def part_d():
    ensure()
    P = ladders()
    L = ['# v29 Part D: the references against the DeFT paper (generated by report_v29.py)', '', 'Descriptive; no test. Effects in per cent with the unadjusted 95 % interval over the seeds.', '']
    vc = []
    f1 = os.path.join(RES, 'vc_static_runs.csv')
    if os.path.exists(f1):
        R = load(os.path.join(V25, 'eval_runs.csv'), f1)
        D = Design(R, P, range(121, 131))
        sizes = [z for z in SIZES if ('MTR_static', '%s-uniform' % z, FREE[z], D.lad(z, ('uniform', FREE[z]))[3], 121) in R]
        six = lambda z: scen(z, SIX)  # noqa: E731
        miss = D.missing(STATIC, sizes, six)
        L += ['## D.1 One VC per packet for MTR and RC (`MTR_static`, `RC_static`) at pipe_all 2', '',
              'New runs: %d (seeds 121-130, the six fault-free scenarios, the ladders of round 25; sizes %s); missing %d; dead-end events %d. The per-hop rows `MTR` and `RC`, DeFT_P,' % (
                  sum(1 for k in R if k[0] in STATIC), ', '.join(sizes), len(miss), sum(x['dead'] for k, x in R.items() if k[0] in STATIC)),
              'DeFT_B, XY_SP and the main row are the runs of round 25.', '',
              '### D.1.1 Each static row against its per-hop row (what the per-hop VC choice gives: a negative THR means that the static row accepts less)', '',
              '| size | row | THR | ' + ' | '.join('LAT at %.1f x' % m for m in MULTS) + ' |', '|---|---|---|' + '---|' * 9]
        for z in sizes:
            for b in MR2:
                ts = [D.test(b + '_static', b, z, six(z), n, 'static against per-hop') for n in ['THR'] + LOADN]
                vc += ts
                L.append('| %s | %s_static against %s | %s |' % (z, b, b, ' | '.join(eci(t) for t in ts)))
        L += ['', 'Per scenario (THR; LAT at 1.0 x Lsat):', '', '| size | row | ' + ' | '.join(SIX) + ' |', '|---|---|' + '---|' * 6]
        for z in sizes:
            for b in MR2:
                cells = []
                for p in SIX:
                    a, c = D.test(b + '_static', b, z, scen(z, [p]), 'THR', 'static against per-hop'), D.test(b + '_static', b, z, scen(z, [p]), 'LAT', 'static against per-hop')
                    vc += [a, c]
                    cells.append('%s; %s' % (eci(a), eci(c)))
                L.append('| %s | %s_static against %s | %s |' % (z, b, b, ' | '.join(cells)))
        L += ['', '### D.1.2 DeFT_P against the better of the two static rows, and against the better of the two per-hop rows, at every load (mean latency; the better row per scenario and load)', '',
              'Negative = DeFT_P is faster.', '', '| size | scenario | against | ' + ' | '.join('%.1f x' % m for m in MULTS) + ' | THR |', '|---|---|---|' + '---|' * 10]
        for z in sizes:
            for p in SIX + ('all six',):
                scs = six(z) if p == 'all six' else scen(z, [p])
                for ref, name in ((tuple(STATIC), 'static'), (tuple(MR2), 'per-hop')):
                    ts = [D.test('DeFT_P', ref, z, scs, n, 'DeFT_P against the better ' + name) for n in LOADN + ['THR']]
                    vc += ts
                    L.append('| %s | %s | the better of the two %s rows | %s |' % (z, p, name, ' | '.join(eci(t) for t in ts)))
        L += ['', 'The loads at which DeFT_P has the lowest mean latency of DeFT_P, MTR and RC (the interval of its effect against the better of the two others is below 0), per scenario:', '',
              '| size | scenario | with the static rows | with the per-hop rows |', '|---|---|---|---|']
        for z in sizes:
            for p in SIX:
                cells = []
                for ref in (tuple(STATIC), tuple(MR2)):
                    ts = [D.test('DeFT_P', ref, z, scen(z, [p]), n) for n in LOADN]
                    low = ['%.1f' % m for m, t in zip(MULTS, ts) if not isnan(t['effect_pct']) and t['effect_pct'] < 0 and t['ci_high'] < 0]
                    lvl = ['%.1f' % m for m, t in zip(MULTS, ts) if not isnan(t['effect_pct']) and t['ci_low'] <= 0 <= t['ci_high']]
                    cells.append('%s%s' % (', '.join(low) if low else 'none', (' (level at ' + ', '.join(lvl) + ')') if lvl else ''))
                L.append('| %s | %s | %s |' % (z, p, ' | '.join(cells)))
        refs_s = tuple(['DeFT_P', 'DeFT_B'] + STATIC + ['XY_SP'])
        L += ['', '### D.1.3 The main comparison of the paper with the other VC policy: the main row against the best of DeFT_P, DeFT_B, `MTR_static`, `RC_static` and XY_SP', '',
              '| size | scenarios | metric | against the best with static MTR and RC | against the best with per-hop MTR and RC (round 25) | against the better of the two static rows | against the better of the two per-hop rows |',
              '|---|---|---|---|---|---|---|']
        for z in sizes:
            for gname, pats in (('all six', SIX), ('the four tuning scenarios', TUNE4), ('localized and movinghot', OTHER2)):
                for n in ('THR', 'LAT', 'P99'):
                    ts = [D.test(MAIN, ref, z, scen(z, pats), n, gname) for ref in (refs_s, tuple(REFS5), tuple(STATIC), tuple(MR2))]
                    vc += ts
                    L.append('| %s | %s | %s | %s |' % (z, gname, n, ' | '.join(eci(t) for t in ts)))
        L.append('')
        write(os.path.join(PD, 'vc_policy.csv'), [dict(size=t['size'], row=t['row'], reference=t['reference'], scenarios=t['scenarios'], metric=t['metric'], comparison=t['group'],
                                                    effect_pct=t['effect_pct'], ci_low=t['ci_low'], ci_high=t['ci_high'], p=t['p'], n_seeds=t['n_seeds']) for t in vc])

    f2 = os.path.join(RES, 'deft_setup_runs.csv')
    if os.path.exists(f2):
        R2 = {}
        for r in csv.DictReader(open(f2)):
            row, pipe = r['variant'].rsplit('-p', 1)
            R2[(row, int(pipe), r['pattern'].split('-')[1], float(r['rate']), int(r['seed']))] = (float(r['latency']), float(r['accepted']), float(r['p99']), int(r['dead_ends']))
        seeds = sorted({k[4] for k in R2})
        tab, low = [], []
        L += ['## D.2 The set-up of the DeFT paper', '',
              '2x2 (4 chiplets of 4x4 routers, 4 VLs per chiplet), 8-flit packets, 4-flit buffers, two VCs, DeFT\'s table with rho = 0.01; uniform, localized (40 % of a source\'s',
              'traffic stays in its chiplet) and hotspot traffic (three routers receive 10 % each). Twelve rates per pattern and pipe depth, k / 10 x Lsat of DeFT_P for k = 1 ... 12',
              '(Lsat of the ladder at that pipe depth). Seeds %d-%d. Runs: %d of 1,800; dead-end events %d. Mean latency in cycles with the half-width of the 95 %% interval over the' % (
                  seeds[0], seeds[-1], len(R2), sum(v[3] for v in R2.values())),
              'seeds. *DeFT_P against the better of the two others*: the effect in mean latency (negative = DeFT_P is faster), the better row chosen at each rate by the mean over the',
              'seeds.', '']
        for p in D2_PATTERNS:
            for pipe in (2, 0):
                rates = d2_rates(P, p, pipe)
                lsat = P['2x2__%s__%s__p%d' % (p, FREE['2x2'], pipe)]['lsat']
                L += ['### %s traffic, pipe_all %d (Lsat of DeFT_P %.4f packets/cycle/source)' % (p, pipe, lsat), '',
                      '| load (x Lsat) | rate | ' + ' | '.join(D2_ROWS) + ' | DeFT_P against the better of MTR, RC (per hop) | DeFT_P against the better of `MTR_static`, `RC_static` |',
                      '|---|---|' + '---|' * 7]
                for k, rate in enumerate(rates):
                    cells, m = [], {}
                    for row in D2_ROWS:
                        v = [R2[(row, pipe, p, rate, s)] for s in seeds if (row, pipe, p, rate, s) in R2]
                        mu, lo, hi = mci([x[0] for x in v])
                        m[row] = mu
                        cells.append('%.1f +- %.1f' % (mu, (hi - lo) / 2.0) if not isnan(mu) and not isnan(lo) else 'n/a')
                        tab.append(dict(pattern=p, pipe_all=pipe, load_x_lsat=(k + 1) / 10.0, rate=rate, row=row, latency=round(mu, 3) if not isnan(mu) else '',
                                        ci_low=round(lo, 3) if not isnan(lo) else '', ci_high=round(hi, 3) if not isnan(hi) else '',
                                        accepted=round(mean([x[1] for x in v]), 6) if v else '', p99=round(mean([x[2] for x in v]), 1) if v else '', n_seeds=len(v)))
                    cmp = []
                    for others, name in ((MR2, 'per-hop'), (STATIC, 'static')):
                        o = min(others, key=lambda r: m[r] if not isnan(m[r]) else 1e30)
                        lr = [math.log(R2[('DeFT_P', pipe, p, rate, s)][0] / R2[(o, pipe, p, rate, s)][0]) for s in seeds if ('DeFT_P', pipe, p, rate, s) in R2 and (o, pipe, p, rate, s) in R2]
                        t = stat(lr)
                        w = lowest_word(t)
                        low.append(dict(pattern=p, pipe_all=pipe, load_x_lsat=(k + 1) / 10.0, rate=rate, policy=name, better_other=o, effect_pct=t['effect_pct'], ci_low=t['ci_low'],
                                        ci_high=t['ci_high'], verdict=w))
                        cmp.append('%s against %s: %s' % (eci(t), o, w))
                    L.append('| %.1f | %.4f | %s | %s |' % ((k + 1) / 10.0, rate, ' | '.join(cells), ' | '.join(cmp)))
                L.append('')
        L += ['### D.2.1 At which loads DeFT_P has the lowest mean latency of DeFT_P, MTR and RC', '',
              '*lowest*: its mean is the lowest and the interval of its effect against the better of the two others is below 0; *within*: its mean is the lowest or not, and the',
              'interval includes 0; *not*: another row is faster and the interval is above 0. Loads in multiples of Lsat.', '',
              '| pattern | pipe_all | VC policy of MTR and RC | lowest | within the interval | not the lowest |', '|---|---|---|---|---|---|']
        for p in D2_PATTERNS:
            for pipe in (2, 0):
                for name in ('per-hop', 'static'):
                    x = [r for r in low if (r['pattern'], r['pipe_all'], r['policy']) == (p, pipe, name)]
                    g = lambda words: ', '.join('%.1f' % r['load_x_lsat'] for r in x if r['verdict'] in words) or 'none'  # noqa: E731
                    L.append('| %s | %d | %s | %s | %s | %s |' % (p, pipe, name, g(('lowest',)), g(('lowest, within the interval', 'not the lowest, within the interval')), g(('not the lowest',))))
        L.append('')
        write(os.path.join(PD, 'deft_paper_setup.csv'), tab)
        write(os.path.join(OUT, 'deft_setup_lowest.csv'), low)
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            style = {'DeFT_P': ('#1f4e9c', '-', 'o'), 'MTR': ('#c8501e', '-', 's'), 'RC': ('#2e8b57', '-', '^'), 'MTR_static': ('#c8501e', '--', 's'), 'RC_static': ('#2e8b57', '--', '^')}
            for p in D2_PATTERNS:
                fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
                for ax, pipe in zip(axes, (2, 0)):
                    for row in D2_ROWS:
                        x = [r for r in tab if (r['pattern'], r['pipe_all'], r['row']) == (p, pipe, row) and r['latency'] != '']
                        c, ls, mk = style[row]
                        ax.errorbar([r['load_x_lsat'] for r in x], [r['latency'] for r in x], yerr=[[r['latency'] - r['ci_low'] for r in x], [r['ci_high'] - r['latency'] for r in x]],
                                    color=c, linestyle=ls, marker=mk, markersize=4, linewidth=1.3, capsize=2, label=row)
                    ax.set_yscale('log')
                    ax.set_xlabel('offered load (x Lsat of DeFT_P)')
                    ax.set_ylabel('mean packet latency (cycles)')
                    ax.set_title('%s traffic, 2x2, pipe_all %d' % (p, pipe))
                    ax.grid(True, which='both', linewidth=0.3, alpha=0.5)
                axes[0].legend(fontsize=8, frameon=False)
                fig.tight_layout()
                fig.savefig(os.path.join(OUT, 'deft_setup_%s.png' % p), dpi=150)
                plt.close(fig)
            L += ['Figures: `deft_setup_uniform.png`, `deft_setup_localized.png`, `deft_setup_hotspot.png` (mean latency against the load, one panel per pipe depth, 95 % intervals;',
                  'solid: per-hop VC choice, dashed: one VC per packet).', '']
        except Exception as e:      # the tables do not depend on the figures
            L += ['Figures not written (%s).' % type(e).__name__, '']
    wmd('summary_D.md', L)
    return L


# =====================================================================================================================
# Part E1: the main row without the lookahead term
# =====================================================================================================================
GROUPS = [('all six', SIX), ('the four tuning scenarios', TUNE4), ('localized and movinghot', OTHER2)]


def part_e():
    ensure()
    P = ladders()
    R = load(os.path.join(V25, 'eval_runs.csv'), os.path.join(RES, 'nola_runs.csv'))
    D = Design(R, P, range(121, 131))
    six = lambda z: scen(z, SIX)  # noqa: E731
    miss = D.missing(['LB_noLA'], SIZES, six)
    L = ['# v29 Part E1: the main row without the lookahead term (generated by report_v29.py)', '',
         '`LB_noLA` = the main row with `heur_lookahead 0`: the cost of an output is 2 x the fill of the buffer behind it + the hops left (+ `lut_bias`); lookahead routing,',
         'the fallback and the busy state stay. New runs: %d of 1,620 (seeds 121-130, the six fault-free scenarios, the ladders of round 25); missing %d; dead-end events %d.' % (
             sum(1 for k in R if k[0] == 'LB_noLA'), len(miss), sum(x['dead'] for k, x in R.items() if k[0] == 'LB_noLA')),
         'The main row, DeFT_P and the references are the runs of round 25. Descriptive; effects in per cent with the unadjusted 95 % interval over the ten seeds;',
         '2x2 / 3x3 / 4x4. The hardware of the row is in `summary_E_hw.md`.', '']
    out = []

    def cell(a, ref, pats, n, g):
        c, ts = e3(D, a, ref, lambda z: scen(z, pats), n, g)
        for t in ts:
            out.append(dict(size=t['size'], row=t['row'], reference=t['reference'], scenarios=g, metric=n, effect_pct=t['effect_pct'], ci_low=t['ci_low'], ci_high=t['ci_high'],
                            p=t['p'], n_seeds=t['n_seeds']))
        return c
    for ref, name in ((MAIN, 'the main row'), ('DeFT_P', 'DeFT_P'), (tuple(REFS5), 'the best of the five references')):
        L += ['## `LB_noLA` against %s' % name, '', '| scenarios | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 0.8 x Lsat |', '|---|---|---|---|---|---|---|']
        for g, pats in GROUPS + [(p, (p,)) for p in SIX]:
            L.append('| %s | %s |' % (g, ' | '.join(cell('LB_noLA', ref, pats, n, g) for n in ('THR', 'LAT', 'P99', 'LAT02', 'LAT05', 'LAT08'))))
        L.append('')
    L += ['## For comparison: the main row against DeFT_P and against the best of the five references (round 25, the same seeds)', '',
          '| against | scenarios | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat |', '|---|---|---|---|---|---|---|']
    for ref, name in (('DeFT_P', 'DeFT_P'), (tuple(REFS5), 'the best of the five references')):
        for g, pats in GROUPS:
            L.append('| %s | %s | %s |' % (name, g, ' | '.join(cell(MAIN, ref, pats, n, g) for n in ('THR', 'LAT', 'P99', 'LAT02', 'LAT05'))))
    L += ['', '## The share of the main row\'s gain over DeFT_P that the row without the lookahead term keeps', '',
          '(mean log ratio of `LB_noLA` against DeFT_P) / (mean log ratio of the main row against DeFT_P), over the six scenarios.', '',
          '| size | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
    for z in SIZES:
        cells = []
        for n in ('THR', 'LAT', 'P99'):
            a, b = mean(D.lr('LB_noLA', 'DeFT_P', z, six(z), n)), mean(D.lr(MAIN, 'DeFT_P', z, six(z), n))
            cells.append('%.0f %%' % (100.0 * a / b) if b else 'n/a')
            out.append(dict(size=z, row='LB_noLA', reference='share of the gain of the main row over DeFT_P', scenarios='all six', metric=n,
                            effect_pct=round(100.0 * a / b, 1) if b else '', ci_low='', ci_high='', p='', n_seeds=len(D.seeds)))
        L.append('| %s | %s |' % (z, ' | '.join(cells)))
    keys = ('hops_chip', 'hops_chip_multi', 'hops_ipos', 'hops_ipos_multi', 'lookahead_multi', 'lookahead_fb_taken', 'lookahead_mismatch', 'packets_measured')
    L += ['', '## Decisions at 1.0 x Lsat (counters summed over the six scenarios and the seeds; 2x2 / 3x3 / 4x4)', '',
          '| row | hops with a choice per packet | of them left through another output than the stored one | stored decisions that differ from a fresh one (of the hops with a choice) |', '|---|---|---|---|']
    for row in (MAIN, 'LB_noLA'):
        c1, c2, c3 = [], [], []
        for z in SIZES:
            t = D.counter(row, z, six(z), 3, keys)
            if not t or not t['packets_measured']:
                c1.append('n/a'), c2.append('n/a'), c3.append('n/a')
                continue
            c1.append('%.2f' % ((t['hops_chip_multi'] + t['hops_ipos_multi']) / float(t['packets_measured'])))
            c2.append(R25.pc(t['lookahead_fb_taken'], t['lookahead_multi']))
            c3.append(R25.pc(t['lookahead_mismatch'], t['lookahead_multi']))
        L.append('| %s | %s | %s | %s |' % (row, ' / '.join(c1), ' / '.join(c2), ' / '.join(c3)))
    L.append('')
    write(os.path.join(PD, 'nola_effects.csv'), out)
    wmd('summary_E.md', L)
    return L


# =====================================================================================================================
# Part F: two more early binders
# =====================================================================================================================
def raw_rows(path):
    """{(row, size-pattern, mask, rate, seed): the CSV row} (every column, as text)."""
    return {(r['variant'].rsplit('-p', 1)[0], r['pattern'], r['mask'], float(r['rate']), int(r['seed'])): r for r in csv.DictReader(open(path))} if os.path.exists(path) else {}


def share(D, row, z, scs, n):
    """(share of the main row's gain over DeFT_P, lowest and highest per-seed share): mean log ratio of the row against DeFT_P over that of the main row."""
    a, b = D.lr(row, 'DeFT_P', z, scs, n), D.lr(MAIN, 'DeFT_P', z, scs, n)
    if not a or not b or len(a) != len(b):
        return NAN, NAN, NAN
    per = [x / y for x, y in zip(a, b) if y]
    return 100.0 * mean(a) / mean(b), 100.0 * min(per), 100.0 * max(per)


def part_f():
    ensure()
    P = ladders()
    f1, f2 = os.path.join(RES, 'early_first_runs.csv'), os.path.join(RES, 'early_age_runs.csv')
    R = load(os.path.join(V28, 'eval_runs.csv'), f1, f2)
    X = raw_rows(f1)
    D = Design(R, P, range(171, 181))
    ch = json.load(open(os.path.join(RES, 'tuning_choice_v29.json'))) if os.path.exists(os.path.join(RES, 'tuning_choice_v29.json')) else {}
    six = lambda z: scen(z, SIX)  # noqa: E731
    hot = lambda z: scen(z, ['hotspot'])  # noqa: E731
    five = lambda z: scen(z, [p for p in SIX if p != 'hotspot'])  # noqa: E731
    has = lambda row: (row, '2x2-uniform', FREE['2x2'], D.lad('2x2', ('uniform', FREE['2x2']))[3], 171) in R  # noqa: E731
    new = [r for r in ('EB_first', 'EB_best16', 'EB_best256') if has(r)]
    miss = D.missing(new, SIZES, six)
    L = ['# v29 Part F: two more early binders (generated by report_v29.py)', '',
         'New runs: %d (%s; seeds 171-180, the six fault-free scenarios, the ladders of round 25); missing %d; dead-end events %d. DeFT_P, the main row, `EB_best`, `EB_best64` and' % (
             sum(1 for k in R if k[0] in new), ', '.join('`%s`' % r for r in new), len(miss), sum(x['dead'] for k, x in R.items() if k[0] in new)),
         '`EB_down_t` are the runs of round 28 on the same seeds (`results_v28_anchor/eval_runs.csv`; `reuse_check.md`). Descriptive, no test; effects in per cent with the',
         'unadjusted 95 % interval over the ten seeds; 2x2 / 3x3 / 4x4. **Share** of the main row\'s gain over DeFT_P that a row reaches = (mean log ratio of the row against',
         'DeFT_P) / (mean log ratio of the main row against DeFT_P), with the range of the ten per-seed shares; above 100 % = ahead of the main row.', '']
    if ch:
        L += ['Tuned values (`tuning_v29.md`): ' + '; '.join('%s: %s' % (z, ', '.join(
            '`%s` %s %s (score %+.3f)' % (r, 'lut_bias' if r == 'EB_first' else 'T', fmt_g(ch[z][r]['D' if r == 'EB_first' else 'T']), ch[z][r]['score']) for r in new if r in ch.get(z, {})))
            for z in SIZES) + '.', '']
        below = ['%s on %s' % (r, z) for z in SIZES for r in new if ch.get(z, {}).get(r, {}).get('below_zero')]
        if below:
            L += ['**Tuning score below 0: %s. For these the best member of the family is DeFT_P itself; the shares of the better of the row and DeFT_P are given below.**' % ', '.join(below), '']
    out = []

    def cells(a, ref, so, names, g):
        cs = []
        for n in names:
            c, ts = e3(D, a, ref, so, n, g)
            cs.append(c)
            for t in ts:
                out.append(dict(size=t['size'], row=t['row'], reference=t['reference'], scenarios=g, metric=n, kind='effect', value=t['effect_pct'], ci_low=t['ci_low'],
                                ci_high=t['ci_high'], p=t['p']))
        return cs

    def share_cells(row, so, g):
        cs = []
        for n in ('THR', 'LAT'):
            v = [share(D, row, z, so(z), n) for z in SIZES]
            cs.append(' / '.join('%.0f %% [%.0f, %.0f]' % x if not isnan(x[0]) else 'n/a' for x in v))
            for z, x in zip(SIZES, v):
                out.append(dict(size=z, row=row, reference='share of the gain of the main row over DeFT_P', scenarios=g, metric=n, kind='share', value=round(x[0], 1) if not isnan(x[0]) else '',
                                ci_low=round(x[1], 1) if not isnan(x[1]) else '', ci_high=round(x[2], 1) if not isnan(x[2]) else '', p=''))
        return cs

    rows = ['EB_best', 'EB_best16', 'EB_best64', 'EB_best256', 'EB_down_t', 'EB_first']
    rows = [r for r in rows if has(r)]
    L += ['## F.1 Every row against DeFT_P and against the main row, over the six scenarios', '',
          '| row | binds the entry VL | THR against DeFT_P | LAT against DeFT_P | THR against the main row | LAT against the main row |', '|---|---|---|---|---|---|']
    what = {'EB_best': 'at injection, ideal information', 'EB_best16': 'at injection, information up to 16 cycles old', 'EB_best64': 'at injection, up to 64 cycles old',
            'EB_best256': 'at injection, up to 256 cycles old', 'EB_down_t': 'at the Down move (the router below the exit VL)', 'EB_first': 'at its first choice on the interposer'}
    L.append('| %s | hop by hop (late) | %s | - | - |' % (MAIN, ' | '.join(cells(MAIN, 'DeFT_P', six, ('THR', 'LAT'), 'all six'))))
    for r in rows:
        L.append('| %s | %s | %s | %s |' % (r, what[r], ' | '.join(cells(r, 'DeFT_P', six, ('THR', 'LAT'), 'all six')), ' | '.join(cells(r, MAIN, six, ('THR', 'LAT'), 'all six'))))
    L += ['', '## F.2 The share of the main row\'s gain over DeFT_P', '',
          '| row | all six: THR | LAT | hotspot alone: THR | LAT | the other five: THR | LAT |', '|---|---|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s |' % (r, ' | '.join(share_cells(r, six, 'all six') + share_cells(r, hot, 'hotspot') + share_cells(r, five, 'the other five'))))
    L.append('')
    if 'EB_first' in rows:
        L += ['## F.3 `EB_first`: one decision at the first choice', '',
              '| against | THR | LAT at 1.0 x Lsat | P99 | LAT at 0.2 x Lsat | LAT at 0.5 x Lsat | LAT at 0.8 x Lsat | LAT at 1.2 x Lsat |', '|---|---|---|---|---|---|---|---|']
        for ref in ('DeFT_P', MAIN, 'EB_best', 'EB_down_t'):
            L.append('| %s | %s |' % (ref, ' | '.join(cells('EB_first', ref, six, ('THR', 'LAT', 'P99', 'LAT02', 'LAT05', 'LAT08', 'LAT12'), 'all six'))))
        L += ['', 'Per scenario, `EB_first` against the main row and against `EB_down_t` (THR; LAT at 1.0 x Lsat):', '',
              '| scenario | against the main row: THR | LAT | against `EB_down_t`: THR | LAT |', '|---|---|---|---|---|']
        for p in SIX:
            so = lambda z, p=p: scen(z, [p])  # noqa: E731
            L.append('| %s | %s | %s |' % (p, ' | '.join(cells('EB_first', MAIN, so, ('THR', 'LAT'), p)), ' | '.join(cells('EB_first', 'EB_down_t', so, ('THR', 'LAT'), p))))
        L += ['', 'Where the single decision is made (measured heads, summed over the six scenarios and the seeds; 2x2 / 3x3 / 4x4): the heads that are bound as a share of the heads',
              'that move Up, the bound heads whose commit router is the one below the exit VL, and the heads that move Up on a VL that is not DeFT-P\'s entry VL.', '',
              '| load | bound | bound at the router below the exit VL | off DeFT-P\'s entry VL | most commits of one head |', '|---|---|---|---|---|']
        for i, t in ((1, '0.5 x Lsat'), (3, '1.0 x Lsat'), (5, '1.4 x Lsat')):
            c = [[], [], [], []]
            for z in SIZES:
                s = dict(up=0, bound=0, below=0, off=0, mx=0)
                for sc in six(z):
                    for seed in D.seeds:
                        x = X.get(('EB_first', '%s-%s' % (z, sc[0]), sc[1], D.lad(z, sc)[i], seed))
                        if not x:
                            continue
                        s['up'] += int(x['entry_up_moves'] or 0)
                        s['bound'] += int(x['entry_commit_first_bound'] or 0)
                        s['below'] += int(x['entry_commit_first_below'] or 0)
                        s['off'] += int(x['entry_up_not_default'] or 0)
                        s['mx'] = max(s['mx'], int(x['entry_commit_first_max_per_head'] or 0))
                c[0].append(R25.pc(s['bound'], s['up']))
                c[1].append(R25.pc(s['below'], s['bound']))
                c[2].append(R25.pc(s['off'], s['up']))
                c[3].append(str(s['mx']))
                out.append(dict(size=z, row='EB_first', reference='', scenarios='all six', metric='load %s' % t, kind='share of the bound heads bound below the exit VL',
                                value=round(100.0 * s['below'] / s['bound'], 1) if s['bound'] else '', ci_low='', ci_high='', p=''))
            L.append('| %s | %s |' % (t, ' | '.join(' / '.join(x) for x in c)))
        L.append('')
    age = [(0, 'EB_best'), (16, 'EB_best16'), (64, 'EB_best64'), (256, 'EB_best256')]
    if True:
        notrun = [r for _, r in age if r not in rows]
        L += ['## F.4 The share of the main row\'s gain against the age of the source\'s knowledge', ''] + ([
            '**Not run: %s** (Part F2 was dropped by the time rule: `runtime_estimate.md`, `time_rule.md`). The table has the ages that were run.' % ', '.join('`%s`' % r for r in notrun), ''] if notrun else [])
        L += ['The occupancies and the counts of the bound packets that the source reads are sampled every 0 (read at the moment of the choice), 16, 64 or 256 cycles; T is tuned for',
              'each age. Share of the main row\'s gain over DeFT_P [range of the per-seed shares].', '',
              '| scenarios | metric | size | ' + ' | '.join('%d cycles (`%s`)' % a for a in age) + ' |', '|---|---|---|' + '---|' * len(age)]
        for g, so in (('all six', six), ('hotspot alone', hot), ('the other five', five)):
            for n in ('THR', 'LAT'):
                for z in SIZES:
                    cs = []
                    for a, r in age:
                        x = share(D, r, z, so(z), n) if r in rows else (NAN, NAN, NAN)
                        cs.append('%.0f %% [%.0f, %.0f]' % x if not isnan(x[0]) else 'not run')
                        if not isnan(x[0]):
                            out.append(dict(size=z, row=r, reference='share of the gain of the main row over DeFT_P', scenarios=g, metric=n, kind='share by age %d' % a, value=round(x[0], 1),
                                            ci_low=round(x[1], 1), ci_high=round(x[2], 1), p=''))
                    L.append('| %s | %s | %s | %s |' % (g, n, z, ' | '.join(cs)))
        L += ['', 'Each aged row against `EB_best` (what the age costs; six scenarios):', '', '| row | THR | LAT at 1.0 x Lsat | P99 |', '|---|---|---|---|']
        for _, r in age[1:]:
            if r in rows:
                L.append('| %s | %s |' % (r, ' | '.join(cells(r, 'EB_best', six, ('THR', 'LAT', 'P99'), 'all six'))))
        L.append('')
    below = [(z, r) for z in SIZES for r in new if ch.get(z, {}).get(r, {}).get('below_zero')]
    if below:
        L += ['## F.5 Rows whose tuning score is below 0: the better of the row and DeFT_P', '',
              'For these sizes DeFT_P is the best member of the row\'s family by the tuning score. The better of the two is taken per scenario and metric by the mean over the seeds.', '',
              '| size | row | THR against the main row | LAT against the main row |', '|---|---|---|---|']
        for z, r in below:
            L.append('| %s | the better of %s and DeFT_P | %s | %s |' % (z, r, eci(D.test((r, 'DeFT_P'), MAIN, z, six(z), 'THR')), eci(D.test((r, 'DeFT_P'), MAIN, z, six(z), 'LAT'))))
        L.append('')
    write(os.path.join(PD, 'early_more.csv'), out)
    wmd('summary_F.md', L)
    return L


def fmt_g(x):
    return '%g' % x


# =====================================================================================================================
# Part G: application traces that load the network
# =====================================================================================================================
G_ROWS = ['DeFT_P', 'MTR', 'RC', MAIN]
G_SEEDS = (41, 42, 43)
G_S = (1, 2, 4, 8, 16, 32)


def part_g():
    ensure()
    A = list(csv.DictReader(open(os.path.join(RES, 'trace_runs.csv'))))
    ch = json.load(open(os.path.join(RES, 'trace_compress.json')))
    K = {(r['benchmark'], r['method'], int(r['compress']), int(r['seed'])): r for r in A}
    bench = list(ch)
    name = lambda b: b.split('_')[0]  # noqa: E731
    bad = [r for r in A if r['finished'] != 'True' or r['injected'] != r['delivered'] or r['dead_ends'] != '0']
    badk = {(r['benchmark'], r['method'], int(r['compress']), int(r['seed'])) for r in bad}
    sat = 8 * ladders()['2x2__uniform__%s__p2' % FREE['2x2']]['lsat']
    withs = [b for b in bench if ch[b]['S']]
    full = lambda b: all((b, r, ch[b]['S'], s) in K and (b, r, ch[b]['S'], s) not in badk for r in G_ROWS for s in G_SEEDS)  # noqa: E731
    chosen = [b for b in withs if full(b)]
    L = ['# v29 Part G: application traces that load the network (descriptive, no test; generated by report_v29.py)', '',
         'The Netrace runs of round 25 load the network with less than a tenth of the saturation load. Here the protocol of those runs (2x2, pipe_all 2, one application: the',
         'first 700,000 cycles of region 2 of each of the nine PARSEC traces, dependency mode, 2- and 18-flit packets) is run with `-netrace_compress S`, which divides the',
         'time stamps of the trace by S. Per trace S is the smallest value in {2, 4, 8, 16, 32} at which the mean latency of DeFT_P (seed 41) is at least 1.5 times its',
         'latency at S = 1 (`trace_compress.md`); at that S DeFT_P, MTR, RC and the main row are run on seeds 41-43. Runs in `trace_runs.csv`: %d; runs that did not deliver' % len(A),
         'their whole window or had a dead-end event: %d. *Offered*: received flits per node and cycle up to the completion of the window, a mean over a bursty trace; for' % len(bad),
         'scale, DeFT_P saturates under uniform traffic at 8 x Lsat = %.3f flits/node/cycle (`load_points_v25.json`).' % sat, '',
         '## G.1 The compression at which a trace loads the network (DeFT_P, seed 41)', '',
         '| trace | S = 1: latency (cycles) | offered | as round 25 | ' + ' | '.join('S = %d: latency (factor)' % s for s in G_S[1:]) + ' | chosen S | offered at the chosen S |',
         '|---|---|---|---|' + '---|' * (len(G_S) + 1)]
    for b in bench:
        l, o, s = ch[b]['latency'], ch[b]['offered'], ch[b]['S']
        L.append('| %s | %.1f | %.4f | %s | %s | %s | %s |' % (name(b), l['1'], o['1'], 'yes' if ch[b].get('same_as_v25') else '**no**',
                                                         ' | '.join('%.1f (%.2f)' % (l[str(x)], l[str(x)] / l['1']) for x in G_S[1:]),
                                                         s if s else 'none reaches 1.5', '%.4f (%.0f %% of 8 x Lsat)' % (o[str(s)], 100 * o[str(s)] / sat) if s else '-'))
    L += ['', '**Traces with a chosen S: %d of %d.** The runs at S = 1 equal the rows of round 25 (`results_v25_confirm/app_runs.csv`: mean latency, p99, completion cycle) for %d of %d traces.' % (
        len(withs), len(bench), sum(1 for b in bench if ch[b].get('same_as_v25')), len(bench)), '']
    out = []
    if not withs:
        L += ['**No S in {2, ..., 32} reaches the factor of 1.5 for any trace: Part G stops here, as pre-registered.**', '']
        wmd('summary_G.md', L)
        return L
    if len(chosen) < len(withs):
        L += ['**Left out of G.2 and G.3 (a run at the chosen S is missing, did not deliver its window or had a dead-end event): %s.**' % ', '.join(name(b) for b in withs if b not in chosen), '']

    def ratios(b, a, ref, col):
        s = ch[b]['S']
        return [float(K[(b, a, s, sd)][col]) / float(K[(b, ref, s, sd)][col]) for sd in G_SEEDS]

    def over(a, ref, col, bs):
        """Per seed the mean over the traces of ln(a / ref): the statistic of the other parts, over the three seeds."""
        return stat([mean(math.log(float(K[(b, a, ch[b]['S'], sd)][col]) / float(K[(b, ref, ch[b]['S'], sd)][col])) for b in bs) for sd in G_SEEDS])

    others = G_ROWS[1:]
    L += ['## G.2 At the chosen S: mean latency, p99 and completion time relative to DeFT_P', '',
          'Per trace the geometric mean over the three seeds of the ratio to DeFT_P of the same seed. **Bold**: the lowest mean latency of the four rows (DeFT_P is 1).', '',
          '| trace | S | offered (flits/node/cycle) | DeFT_P latency (cycles) | latency relative to DeFT_P: ' + ' | '.join(others) + ' | p99 relative to DeFT_P: ' + ' | '.join(others)
          + ' | completion time relative to DeFT_P: ' + ' | '.join(others) + ' |', '|---|---|---|---|' + '---|' * (3 * len(others))]
    g = {(r, c): [] for r in others for c in ('latency', 'p99', 'completion_cycles')}
    low = {r: 0 for r in G_ROWS}
    for b in chosen:
        s = ch[b]['S']
        base = [K[(b, 'DeFT_P', s, sd)] for sd in G_SEEDS]
        v = {(r, c): R25.gmean(ratios(b, r, 'DeFT_P', c)) for r in others for c in ('latency', 'p99', 'completion_cycles')}
        for k, x in v.items():
            g[k].append(x)
        lat = dict([('DeFT_P', 1.0)] + [(r, v[(r, 'latency')]) for r in others])
        best = min(lat, key=lambda r: lat[r])
        low[best] += 1
        L.append('| %s | %d | %.4f | %.1f | %s | %s | %s |' % (
            name(b), s, mean(float(x['offered_flits_per_node_cycle']) for x in base), mean(float(x['latency']) for x in base),
            ' | '.join(('**%.3f**' if r == best else '%.3f') % v[(r, 'latency')] for r in others), ' | '.join('%.3f' % v[(r, 'p99')] for r in others),
            ' | '.join('%.4f' % v[(r, 'completion_cycles')] for r in others)))
        for r in G_ROWS:
            out.append(dict(workload=name(b), compress=s, row=r, latency_cycles=round(mean(float(K[(b, r, s, sd)]['latency']) for sd in G_SEEDS), 3),
                            latency_rel_DeFT_P=round(lat[r], 5), p99_rel_DeFT_P=1.0 if r == 'DeFT_P' else round(v[(r, 'p99')], 5),
                            completion_rel_DeFT_P=1.0 if r == 'DeFT_P' else round(v[(r, 'completion_cycles')], 5),
                            offered_flits_per_node_cycle=round(mean(float(x['offered_flits_per_node_cycle']) for x in base), 6), effect_pct='', ci_low='', ci_high=''))
    L += ['| **geometric mean** | | | | %s | %s | %s |' % (' | '.join('%.3f' % R25.gmean(g[(r, 'latency')]) for r in others), ' | '.join('%.3f' % R25.gmean(g[(r, 'p99')]) for r in others),
                                                        ' | '.join('%.4f' % R25.gmean(g[(r, 'completion_cycles')]) for r in others)), '',
          'The lowest mean latency of the four rows: %s.' % '; '.join('%s in %d of %d traces' % (r, low[r], len(chosen)) for r in sorted(G_ROWS, key=lambda r: -low[r]) if low[r]), '']
    for r in G_ROWS:
        out.append(dict(workload='geometric mean', compress='', row=r, latency_cycles='', latency_rel_DeFT_P=1.0 if r == 'DeFT_P' else round(R25.gmean(g[(r, 'latency')]), 5),
                        p99_rel_DeFT_P=1.0 if r == 'DeFT_P' else round(R25.gmean(g[(r, 'p99')]), 5),
                        completion_rel_DeFT_P=1.0 if r == 'DeFT_P' else round(R25.gmean(g[(r, 'completion_cycles')]), 5), offered_flits_per_node_cycle='', effect_pct='', ci_low='', ci_high=''))
    L += ['## G.3 Over the traces, in the form of the other parts', '',
          'Effect in per cent = 100 x (exp(mean over the seeds of R_s) - 1), R_s = the mean over the %d traces of ln(row / reference) for seed s; unadjusted 95 %% interval over the' % len(chosen),
          'three seeds (two degrees of freedom: the intervals are wide by construction). Negative = lower.', '',
          '| comparison | mean latency | p99 | completion time |', '|---|---|---|---|']
    for a, ref in (('MTR', 'DeFT_P'), ('RC', 'DeFT_P'), (MAIN, 'DeFT_P'), (MAIN, 'MTR'), (MAIN, 'RC')):
        st = [over(a, ref, c, chosen) for c in ('latency', 'p99', 'completion_cycles')]
        L.append('| %s against %s | %s |' % ('the main row' if a == MAIN else a, ref, ' | '.join(eci(x) for x in st)))
        out.append(dict(workload='over the traces', compress='', row=a, latency_cycles='', latency_rel_DeFT_P='', p99_rel_DeFT_P='', completion_rel_DeFT_P='', offered_flits_per_node_cycle='',
                        effect_pct='%s against %s: %.3f' % (a, ref, st[0]['effect_pct']), ci_low=st[0]['ci_low'], ci_high=st[0]['ci_high']))
    # the same traces without compression: the rows of round 25
    f25 = os.path.join(V25, 'app_runs.csv')
    if os.path.exists(f25):
        K25 = {(r['benchmark'], r['method'], int(r['seed'])): r for r in csv.DictReader(open(f25)) if int(r['mask'], 16) == 0}
        L += ['', '## G.4 The same traces without compression (S = 1, the runs of round 25)', '',
              'Geometric mean over the traces of the mean latency relative to DeFT_P (geometric mean over seeds 41-43 per trace), next to the value at the chosen S.', '',
              '| traces | ' + ' | '.join('%s: S = 1 | chosen S' % r for r in others) + ' |', '|---|' + '---|---|' * len(others)]
        for lab, bs in (('the %d traces of G.2' % len(chosen), chosen), ('all nine', bench)):
            cs = []
            for r in others:
                one = R25.gmean([R25.gmean([float(K25[(b, r, sd)]['latency']) / float(K25[(b, 'DeFT_P', sd)]['latency']) for sd in G_SEEDS]) for b in bs])
                cs.append('%.3f | %s' % (one, '%.3f' % R25.gmean(g[(r, 'latency')]) if bs is chosen else '-'))
            L.append('| %s | %s |' % (lab, ' | '.join(cs)))
    L.append('')
    write(os.path.join(PD, 'apps_loaded.csv'), out)
    wmd('summary_G.md', L)
    return L


def paper_readme():
    """paper_data/README.md: the files that exist, with what they hold."""
    T = [('heldout_effects.csv', 'Part B, the three scenarios that no round had run (seeds 181-190): the main row against DeFT_P, the best of the five references, the best of '
          'DeFT_P and DeFT_B, the best of MTR and RC and XY_SP; per scenario and over the three; the primary family with its Holm-adjusted p and verdict; and the five '
          'scenarios that the tuning never saw (with localized and movinghot of round 25) as the mean of the five per-scenario effects', 'size x scenario x comparison x metric'),
         ('lb_b0.csv', 'Part B: `LB_b0` (the main row with `lut_bias 0`) on 2x2 against the main row and against the best reference, and the main row against the best '
          'reference, on the three new scenarios and on the scenarios of round 25 (all six, the four of the tuning, the other two, each one)', 'scenario set x row x reference x metric'),
         ('equal_area_effects.csv', 'Part C: the main row at depth 4 against the references with 5-flit and 6-flit buffers and with 7-flit buffers in the interposer routers '
          '(each, the best of the set, the best of the two DeFT variants), each reference against itself at depth 4, and `LB_d6`; with the measured area of the set and of '
          'the main row relative to DeFT at depth 4 in the three forms of the synthesis, and the primary family 2 with its Holm-adjusted p and verdict. `thr_over`: the '
          'loads THR is taken over (four for the comparisons with `X_i7`)', 'size x reference set x comparison x scenario set x metric'),
         ('equal_area_faults.csv', 'Part C3: under random VL faults (the masks of round 26, rates 1/16 and 4/16; unit = mask) the main row at depth 4 against the DeFT '
          'variants at depth 6, and each variant at depth 6 against itself at depth 4', 'size x rate x traffic x row x reference x metric'),
         ('vc_policy.csv', 'Part D1: MTR and RC with one VC per packet against their per-hop rows, DeFT_P against the better static row, and the main row against the best '
          'reference with either VC policy', 'size x row x reference x scenario set x metric'),
         ('deft_paper_setup.csv', 'Part D2, the set-up of the DeFT paper on 2x2: mean latency with its 95 % interval over five seeds, accepted throughput and P99 of DeFT_P, '
          'MTR, RC and the two static rows at twelve loads (0.1 to 1.2 x Lsat of DeFT_P), three traffic patterns, `pipe_all` 2 and 0', 'pattern x pipe_all x load x row'),
         ('nola_effects.csv', 'Part E1: `LB_noLA` (the main row without the lookahead term) against the main row, DeFT_P and the best of the five references; all six '
          'scenarios, the four of the tuning, the other two', 'size x row x reference x scenario set x metric'),
         ('hw_variants.csv', 'Parts E2 and E4 (`report_v29_hw.py`): DeFT, the main row and its two RTL variants: system area relative to DeFT in the three forms, the '
          'cut configuration needed at T_ref with its margin, the delay left for an interposer link in the link cycle, the report inputs read, and on 4x4 the power of '
          'the average router with each activity', 'design x size'),
         ('early_more.csv', 'Part F: `EB_first` (and the aged rows `EB_best16`, `EB_best256` if they were run) against DeFT_P, the main row, `EB_best` and `EB_down_t`; the '
          'share of the main row' + chr(39) + 's gain over DeFT_P; the share of the bound heads whose commit is made below the exit VL', 'size x row x reference x scenario set x metric'),
         ('apps_loaded.csv', 'Part G: the PARSEC traces of round 25 on 2x2, each compressed in time by the smallest S at which the latency of DeFT_P is at least 1.5 times its '
          'latency at S = 1: mean latency, p99 and completion time of DeFT_P, MTR, RC and the main row relative to DeFT_P, per trace, as the geometric mean over the traces, '
          'and as an effect with its 95 % interval over the three seeds', 'trace x row')]
    L = ['# paper_data (round 29)', '',
         'One CSV per table or figure. Written by `report_v29.py` and `report_v29_hw.py` from the per-run CSVs of `results_v29_review/` and of the rounds whose rows are',
         'reused (`results_v25_confirm/eval_runs.csv`, `results_v26_faults/fault_rate_runs.csv`, `results_v28_anchor/eval_runs.csv`; `../reuse_check.md`); nothing here is',
         'edited by hand. Definitions: `../PREREGISTRATION.md`.', '',
         '**Effects** are percentages, 100 x (exp(mean log ratio) - 1): per seed the mean over the scenarios of ln(row / reference), with the 95 % t interval over the seeds',
         '(Part C3: per mask the mean over the two traffic patterns and the two seeds, the interval over the 16 masks). THR = the largest accepted throughput over the loads',
         'of the ladder (flits/node/cycle; positive = higher); LAT, P99 = mean and 99th-percentile packet latency at 1.0 x Lsat of DeFT-P with 4-flit buffers (cycles;',
         'negative = lower). Only the two primary families are adjusted (`../report/primary_B.csv`, `../report/primary_C.csv`); everything else is descriptive.', '',
         '| file | table or figure | rows |', '|---|---|---|']
    L += ['| `%s` | %s | %s |' % t for t in T if os.path.exists(os.path.join(PD, t[0]))]
    open(os.path.join(PD, 'README.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)


DROP_TEXT = {'G': 'Part G (traces that load the network)', 'F2': 'Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation)', 'C3_rate_1_16': 'the rate 1/16 of C3',
             'C2': 'Part C2', 'D1_3x3_4x4': 'D1 on 3x3 and 4x4', 'LB_d6': '`LB_d6`', 'C1_d5_seeds126_130': 'seeds 126-130 of the rows at depth 5'}


def time_rule_lines():
    """What the time rule dropped: drops.json, written by the timing stage and updated by restore_v29.py."""
    f = os.path.join(RES, 'drops.json')
    if not os.path.exists(f):
        return []
    D = json.load(open(f))
    dr, rs, lift = D.get('dropped', []), D.get('restored', []), D.get('limit_lifted') or {}
    names = lambda xs: '; '.join(DROP_TEXT.get(x, x) for x in xs)  # noqa: E731
    s = '**Time rule** (`runtime_estimate.md`, `time_rule.md`): the timing runs estimated Parts B to G at %.1f h against the limit of 48 h. ' % D['estimate_hours']
    by_user = [x for x in rs if x in lift.get('taken_back', [])]
    by_rule = [x for x in rs if x not in by_user]
    if by_user:
        day = time.strftime('%d %B', time.strptime(lift['when'], '%Y-%m-%d %H:%M:%S')).lstrip('0')
        files = {'F2': 'early_age_runs.csv', 'G': 'trace_runs.csv'}
        ran = all(os.path.exists(os.path.join(RES, files[x])) for x in by_user if x in files)
        s += ('Dropped at first, in the pre-registered order: %s. On %s the user lifted the limit ("%s"; `DECISIONS.md`), so these parts were taken back%s; the round takes '
              'longer than 48 h. ' % (names(by_user), day, lift['words'], ' and run' if ran else ' (their runs follow)'))
    if by_rule:
        s += 'Dropped at first and taken back by the restore rule, so run: %s. ' % names(by_rule)
    s += ('Dropped in the pre-registered order and not run: %s.' % names(dr)) if dr else 'Nothing is dropped: every part of the prompt is run.'
    return [s, '']


PARTS = {'b': ('heldout_runs.csv', None), 'c': ('depth_runs.csv', None), 'd': ('deft_setup_runs.csv', None), 'e': ('nola_runs.csv', None), 'f': ('early_first_runs.csv', None),
         'g': ('trace_runs.csv', None)}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PD, exist_ok=True)
    args = [a for a in sys.argv[1:] if a != 'all']
    todo = args or [k for k, (f, _) in sorted(PARTS.items()) if os.path.exists(os.path.join(RES, f))]
    for k in todo:
        globals()['part_' + k]()
        print('part', k, 'written')
    L = ['# v29 report (generated by report_v29.py and report_v29_hw.py)', ''] + time_rule_lines()
    for name in ['summary_%s.md' % k.upper() for k in 'bcdefg'] + ['summary_hw_E3.md', 'summary_hw_E2.md', 'summary_hw_E4.md']:
        f = os.path.join(OUT, name)
        if os.path.exists(f):
            L += open(f, encoding='utf-8').read().rstrip(NL).split(NL) + ['', '---', '']
    wmd('summary.md', L)
    paper_readme()


if __name__ == '__main__':
    main()
