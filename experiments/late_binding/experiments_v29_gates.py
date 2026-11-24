"""v29 gates (results_v29_review/PROMPT.md, A2), run through experiments_v29.py:
  a2_bufid     -buffer_ipos 4 with -buffer 4 against the option absent (DeFT_P, MTR, RC, the main row; uniform, 1.0 x Lsat, seed 121): the
               whole stats file byte by byte; and the unit check of the depths with the diagnostic -deft_lb buffer_stats 1 (the configured
               depth and the largest fill of the input buffers per layer, for -buffer 5, -buffer 6 and -buffer_ipos 7) -> buffer_checks.md
  a2_bufdrain  all-pairs drain tests of DeFT_P, DeFT_B, MTR, RC and the main row with -buffer 5, -buffer 6 and -buffer_ipos 7 on the
               fault-free mask, and on the north mask for the VN-based rows -> drain_buffers.csv
  a2_fanchor   EB_first with lut_bias 1e9 against DeFT_P on the runs of the anchor gate of round 28, as the row draws its tie-breaks and
               with the diagnostic tie_stream 1 -> anchor_first.md, anchor_first.json
  a2_funits    unit checks of entry_commit first -> unit_checks_first.md
  a2_fdrain    all-pairs drain tests of EB_first on the six masks per size of round 27 (extra = tuned: with the tuned lut_bias)
               -> drain_first.csv / drain_first_tuned.csv
  a2_traffic   the tables of tornado, neighbour and randperm (every table of the three patterns that exists) -> traffic_checks.md,
               randperm_<size>.txt
  a2_tdrain    drain tests of all rows of Part B on the three new patterns at 0.5 and 1.0 x Lsat (after B0) -> drain_traffic.csv
  a2_formal    formal/lb_cdg_check.py (the referee's independent check), modes main, turnmodels, rules, placements, with python3 -I
               -> formal_independent/
  a2_reuse     the reused rows of rounds 25, 26 and 28 with the build of this round -> reuse_check.md
"""
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v26 as X26  # noqa: E402
import experiments_v26_eval as EV26  # noqa: E402
import experiments_v27_eval as EV27  # noqa: E402
import experiments_v28_eval as EV28  # noqa: E402
import experiments_v29 as X  # noqa: E402
import experiments_v29_rows as R  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL, MAIN = X.RES, X.SIZES, X.NL, X.MAIN
lb, job, wmd, stats4, strip = X.lb, R.job, R.wmd, R.stats4, R.strip
INF = R.INF
BS = lb('buffer_stats', 1)                     # diagnostic of the depth check: observation only


def run_seg(js, out, nproc, timeout, seg=96):
    """run_jobs in segments, each with the number of processes that ~/lbraw/v29/width.txt gives at that moment."""
    res = {}
    for k in range(0, len(js), seg):
        w = X.width(nproc)
        print('%s runs %d-%d of %d with %d processes' % (time.strftime('%H:%M:%S'), k + 1, min(k + seg, len(js)), len(js), w), flush=True)
        res.update(run_jobs(js[k:k + seg], out, nproc=w, timeout=timeout))
    return res


def allpairs(name, z, m, a0):
    """An all-pairs drain test (the protocol of round 10): in cycle k every chiplet router s sends one packet to (s + k) mod N."""
    a = common_args(1, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(z), lut=X23.lut23(z, m)) + E5.size_args(z) + \
        list(a0) + X23.pipe(2) + X24.TRNG + (E10.DRAIN_ALLPAIRS_2X2 if z == '2x2' else E10.DRAIN_ALLPAIRS)
    return 'allpairs__%s-p2__%s-%s__s1' % (name, z, m), a


# =====================================================================================================================
# buffers
# =====================================================================================================================
BUFID_ROWS = ['DeFT_P', 'MTR', 'RC', MAIN]
BUFID_EXTRA = ['-buffer_ipos', '4', '-buffer', '4']
DEPTH_CASES = [('d5', R.DEPTH['d5'], 5, 5), ('d6', R.DEPTH['d6'], 6, 6), ('i7', R.DEPTH['i7'], 4, 7), ('b6i3', ['-buffer', '6', '-buffer_ipos', '3'], 6, 3)]


def bufid(nproc):
    P = X25.lp()
    out = X.raw('bufid')
    js, ident, depth, obs = [], [], [], []
    for z in SIZES:
        p, m = 'uniform', E5.FREE[z]
        lad = P[X.lkey(z, p, m)]['eval']
        E5.gen_tables(z, p, [lad[3], lad[8]])
        for row in BUFID_ROWS:
            a = job('bufid', z, row, R.row_args(z, row), p, m, lad[3], 121)
            b = job('bufid', z, row + '_i4b4', R.row_args(z, row), p, m, lad[3], 121, BUFID_EXTRA)
            js += [a, b]
            ident.append((z, row, lad[3], a[0], b[0]))
        for row in ('DeFT_P', MAIN):
            for tag, ex, dc, di in DEPTH_CASES:
                a = job('bufid', z, '%s_%s_bs' % (row, tag), R.row_args(z, row), p, m, lad[8], 121, ex + BS)
                js.append(a)
                depth.append((z, row, tag, ' '.join(ex), dc, di, lad[8], a[0]))
            a = job('bufid', z, row + '_d6', R.row_args(z, row), p, m, lad[8], 121, R.DEPTH['d6'])
            js.append(a)
            obs.append((z, row, lad[8], a[0], [n for zz, rr, tag, _, _, _, _, n in depth if (zz, rr, tag) == (z, row, 'd6')][0]))
    res = run_jobs(js, out, nproc=X.width(nproc), timeout=7200)
    ok = all(res[n] for n, _ in js)
    L = ['# A2: the buffer options (experiments_v29.py a2_bufid)', '',
         '## 1. `-buffer_ipos 4` with `-buffer 4` is the option absent', '',
         'DeFT_P, MTR, RC and the main row `%s` on uniform traffic at 1.0 x Lsat of DeFT_P, seed 121, pipe_all 2, `-traffic_rng 1`: the run of the row as round 25' % MAIN,
         'defines it, and the same run with `%s`. Compared: the whole statistics file, byte by byte.' % ' '.join(BUFID_EXTRA), '',
         '| size | row | rate | accepted | latency | byte-identical |', '|---|---|---|---|---|---|']
    n = 0
    for z, row, r, na, nb in ident:
        fa, fb = os.path.join(out, na + '.json'), os.path.join(out, nb + '.json')
        eq = os.path.exists(fa) and os.path.exists(fb) and open(fa, 'rb').read() == open(fb, 'rb').read()
        n += eq
        s = stats4(res[na]) if res[na] else (float('nan'),) * 4
        L.append('| %s | %s | %.4f | %.6f | %.4f | %s |' % (z, row, r, s[0], s[1], 'yes' if eq else '**no**'))
    ok = ok and n == len(ident)
    L += ['', '**%d / %d byte-identical.**' % (n, len(ident)), '',
          '## 2. The depths are the real ones', '',
          'DeFT_P and the main row on uniform traffic at 2.4 x Lsat of DeFT_P (seed 121) with the diagnostic `-deft_lb buffer_stats 1`, which records at every flit',
          'written into an input buffer the capacity of that buffer and its fill after the write, per layer (chiplet routers, interposer routers; the smallest and',
          'the largest capacity seen, and the largest fill). The capacity must be the one asked for on every buffer that received a flit, and at this load the',
          'largest fill must reach it and cannot pass it. `-buffer 6 -buffer_ipos 3` is a fourth case, to show that the interposer depth can also be the smaller one.', '',
          '| size | row | options | asked: chiplet / interposer | capacity seen: chiplet | interposer | largest fill: chiplet | interposer | as asked |', '|---|---|---|---|---|---|---|---|---|']
    n = 0
    for z, row, tag, ex, dc, di, r, na in depth:
        l = res[na]['deft_lb'] if res[na] else {}
        cc, ci, fc, fi = l.get('buffer_depth_chip'), l.get('buffer_depth_ipos'), l.get('buffer_fill_max_chip'), l.get('buffer_fill_max_ipos')
        eq = cc == [dc, dc] and ci == [di, di] and fc == dc and fi == di
        n += eq
        L.append('| %s | %s | `%s` | %d / %d | %s | %s | %s | %s | %s |' % (z, row, ex, dc, di, cc, ci, fc, fi, 'yes' if eq else '**no**'))
    ok = ok and n == len(depth)
    L += ['', '**%d / %d as asked.**' % (n, len(depth)), '', '## 3. `buffer_stats` reads only', '',
          'The runs of check 2 with `-buffer 6`, with and without the diagnostic. Compared: the whole `summary` block and every field of `deft_lb` except those of the diagnostic.',
          '', '| size | row | accepted without / with | latency without / with | identical |', '|---|---|---|---|---|']
    n = 0
    for z, row, r, na, nb in obs:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and a['deft_lb'] == {k: v for k, v in b['deft_lb'].items() if not k.startswith('buffer_')}
        n += eq
        L.append('| %s | %s | %.6f / %.6f | %.4f / %.4f | %s |' % (z, row, stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1], 'yes' if eq else '**no**'))
    ok = ok and n == len(obs)
    L += ['', '**%d / %d identical.**' % (n, len(obs)), '', '**All checks of the buffer options pass: %s.**' % ('yes' if ok else 'NO')]
    wmd('buffer_checks.md', L)
    if ok:
        shutil.rmtree(out)
    return ok


def bufdrain_jobs():
    js = []
    for z in SIZES:
        for tag in ('d5', 'd6', 'i7'):
            for row in ('DeFT_P', 'DeFT_B', 'MTR', 'RC', MAIN):
                for m in [E5.FREE[z]] + ([E5.NORTH[z]] if row in R.VN_ROWS else []):
                    js.append(allpairs('%s_%s' % (row, tag), z, m, X25.row_args(z, row) + R.DEPTH[tag]))
    return js


def bufdrain(nproc):
    js = bufdrain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = run_seg(js, X.raw('bufdrain'), nproc, 14400)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_buffers.csv'))
    print('drain tests: %d, failures %d, wall %.0f s' % (len(js), fails, time.time() - t), flush=True)
    if not fails:
        shutil.rmtree(X.raw('bufdrain'))
    return not fails


# =====================================================================================================================
# entry_commit first
# =====================================================================================================================
def main_d(z):
    """The frozen lut_bias of the main row on this size."""
    a = X25.row_args(z, MAIN)
    return float(a[a.index('lut_bias') + 1])


ANCHOR_ROWS = [('EB_first_inf', lambda z: R.first_args(z, INF)), ('EB_first_inf_ts', lambda z: R.first_args(z, INF, tie=True))]


def fanchor(nproc):
    js, meta = [], []
    for z in SIZES:
        for p, m, r, seed in EV28.gate_runs(z):
            a = job('fanchor', z, 'DeFT_P', X25.row_args(z, 'DeFT_P'), p, m, r, seed)
            js.append(a)
            names = {}
            for row, f in ANCHOR_ROWS:
                b = job('fanchor', z, row, f(z), p, m, r, seed)
                js.append(b)
                names[row] = b[0]
            meta.append((z, p, m, r, seed, a[0], names))
    res = run_jobs(js, X.raw('fanchor'), nproc=X.width(nproc), timeout=7200)
    out = {}
    L = ['# A2: `EB_first` with `lut_bias 1e9` against DeFT_P (experiments_v29.py a2_fanchor)', '',
         'Is DeFT_P the member of the family of `EB_first` at `lut_bias` towards infinity? `EB_first_inf` = the main row with `-deft_lb entry_commit first` and',
         '`lut_bias 1e9` (and `-deft_lb entry_stats 1`, which only counts). Against `DeFT_P`. The runs of the anchor gate of round 28: the six fault-free',
         'scenarios at 1.0 x Lsat with seed 101, and uniform traffic on mask 1 of rate 4/16 of round 26 at 1.0 x Lsat of that mask with seed 151; pipe_all 2,',
         '`-traffic_rng 1`. Compared: every field of the `summary` block except the three energy fields, and the delay statistics, the packets per VL and the',
         'dead-end events of the `deft_lb` block. `_ts`: the same row with the diagnostic `-deft_lb tie_stream 1`, with which the two tie-breaks of the commit',
         '(the output, then the candidate) draw from a stream of their own instead of `rand()`, from which the routers\' crossbar arbitration draws. Off packets:',
         'the measured Up moves on a VL that is not DeFT-P\'s entry VL (`entry_stats`); 0 means every packet took DeFT-P\'s entry VL.', '']
    for row, _ in ANCHOR_ROWS:
        L += ['## `%s`' % row, '', '| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | heads bound | identical |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
        same = off = 0
        lr = []
        for z, p, m, r, seed, na, names in meta:
            a, b = res[na], res[names[row]]
            eq = EV28.same_as_deft(a, b)
            same += eq
            nd = b['deft_lb']['entry_up_not_default'] if b else -1
            off += nd != 0
            sa, sb = stats4(a), stats4(b)
            lr.append((math.log(sb[0] / sa[0]), math.log(sb[1] / sa[1]), math.log(sb[2] / sa[2])))
            L.append('| %s | %s | %s | %.4f | %d | %.6f / %.6f | %.3f / %.3f | %s / %s | %d | %s | %s |' % (
                z, p, m, r, seed, sa[0], sb[0], sa[1], sb[1], sa[2], sb[2], nd, b['deft_lb'].get('entry_commit_first_bound') if b else '', 'yes' if eq else '**no**'))
        n = len(meta)
        mean = [100.0 * (math.exp(sum(x[k] for x in lr) / n) - 1.0) for k in range(3)]
        L += ['', '**%d / %d identical.** Runs with a packet off DeFT-P\'s entry VL: %d. Mean of the %d runs against DeFT_P: THR %+.2f %%, LAT %+.2f %%, P99 %+.2f %%.' % (
            same, n, off, n, mean[0], mean[1], mean[2]), '']
        out[row] = dict(identical=same == n, same=same, runs=n, runs_off_default=off, mean_thr=mean[0], mean_lat=mean[1], mean_p99=mean[2])
    o, t = out['EB_first_inf'], out['EB_first_inf_ts']
    if o['identical']:
        L.append('* `EB_first_inf` is identical to DeFT_P in every run: the family of `EB_first` contains DeFT_P.')
    elif t['identical'] and o['runs_off_default'] == 0:
        L.append('* `EB_first_inf` is not byte-identical to DeFT_P, but every packet takes DeFT-P\'s entry VL, and with its tie-breaks on a stream of their own '
                 '(`EB_first_inf_ts`) it is identical in every run. So the only difference is the random stream: the two draws of a commit shift every later draw of '
                 'the crossbar arbitration (as for the anchors of round 28, `results_v28_anchor/anchor.md`). With `lut_bias` towards infinity the row is DeFT_P\'s '
                 'routing with another arbitration sequence.')
    else:
        L.append('* **`EB_first_inf` is not DeFT_P\'s routing** (`EB_first_inf_ts` identical: %s; runs off DeFT-P\'s VL: %d). The gate fails.' % (
            'yes' if t['identical'] else 'no', o['runs_off_default']))
    multi = sum(R.multi_hops(res[names[row]]) for _, _, _, _, _, _, names in meta for row, _ in ANCHOR_ROWS if res[names[row]])
    mx = max([res[names[row]]['deft_lb'].get('entry_commit_first_max_per_head', 0) for _, _, _, _, _, _, names in meta for row, _ in ANCHOR_ROWS if res[names[row]]] or [0])
    L += ['', 'Hops of the anchor runs at which a head that has left its commit router is offered more than one output (must be 0): %d. Largest number of commits of one' % multi,
          'head (must be at most 1): %d.' % mx]
    json.dump(out, open(os.path.join(RES, 'anchor_first.json'), 'w'), indent=1)
    wmd('anchor_first.md', L)
    ok = multi == 0 and mx <= 1 and all(res[x] for x in res) and (o['identical'] or (t['identical'] and o['runs_off_default'] == 0))
    if ok:
        shutil.rmtree(X.raw('fanchor'))
    return ok


CHECK_N = 1000                                 # heads per run of the commit check: two values of lut_bias x six scenarios = 12,000 per size
CHECK_D = (None, 4.0)                          # the frozen lut_bias of the main row on the size, and 4


def funits(nproc):
    P = X25.lp()
    out = X.raw('funits')
    js, one, chk, ro = [], [], [], []
    for z in SIZES:
        for p, m in R.ff_scenarios(z):
            r = P[X.lkey(z, p, m)]['eval'][3]
            E5.gen_tables(z, p, [r])
            for D in CHECK_D:
                d = main_d(z) if D is None else D
                c = job('funits', z, 'EB_first_D%s_check' % R.fmt(d), R.first_args(z, d, check=CHECK_N), p, m, r, 101)
                js.append(c)
                chk.append((z, p, d, c[0]))
            if p == 'uniform':
                d = main_d(z)
                a = job('funits', z, 'EB_first_D%s' % R.fmt(d), R.first_args(z, d), p, m, r, 101)
                js.append(a)
                ro.append((z, p, d, a[0], [n for zz, pp, dd, n in chk if (zz, pp, dd) == (z, p, d)][0]))
        m3, r3 = EV27.k3_mask(z)
        E5.gen_tables(z, 'uniform', [r3])
        a = job('funits', z, 'main_stats', X25.row_args(z, MAIN) + R.ES, 'uniform', m3, r3, 101)
        b = job('funits', z, 'EB_first_D%s' % R.fmt(main_d(z)), R.first_args(z, main_d(z)), 'uniform', m3, r3, 101)
        js += [a, b]
        one.append((z, m3, r3, a[0], b[0]))
    res = run_jobs(js, out, nproc=X.width(nproc), timeout=7200)
    ok = all(res[n] for n, _ in js)
    FIRST = ('entry_commit', 'entry_commit_first_bound', 'entry_commit_first_below', 'entry_commit_first_max_per_head')
    L = ['# A2: unit checks of `-deft_lb entry_commit first` (experiments_v29.py a2_funits)', '', 'Seed 101, pipe_all 2, `-traffic_rng 1`, 1.0 x Lsat of DeFT_P.', '',
         '## 1. `entry_commit first` changes nothing when the entry mask has one candidate', '',
         '`EB_first` (the main row with `entry_commit first`) against the main row on a mask of round 25 that leaves every chiplet one functional VL (uniform traffic at',
         '1.0 x Lsat of that mask). Compared: the whole `summary` block and every field of `deft_lb` except the counters of the option.', '',
         '| size | mask | rate | accepted main / EB_first | latency main / EB_first | heads bound | identical |', '|---|---|---|---|---|---|---|']
    n = 0
    for z, m3, r3, na, nb in one:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and a['deft_lb'] == strip(b['deft_lb'], FIRST) and b['deft_lb']['entry_commit_first_bound'] == 0
        n += eq
        L.append('| %s | %s | %.4f | %.6f / %.6f | %.4f / %.4f | %s | %s |' % (z, m3, r3, stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1],
                                                                         b['deft_lb'].get('entry_commit_first_bound'), 'yes' if eq else '**no**'))
    ok = ok and n == len(one)
    L += ['', '**%d / %d identical.**' % (n, len(one)), '',
          '## 2. The committed VL against the main row\'s selection at the commit router', '',
          '`EB_first` with `-deft_lb commit_check %d`: for the first %d heads of the measured window that are bound, the costs that the main row\'s selection gives the' % (CHECK_N, CHECK_N),
          'outputs of the commit router (the full entry mask, the state of that router at the moment the decision for it is computed, `lut_bias` as the selection charges',
          'it) are computed a second time, next to the commit. *unique*: the output towards the committed VL is the one cheapest output of the main row\'s selection.',
          '*tie*: the selection has more than one cheapest output and the output towards the committed VL is among them. *different*: it is not a cheapest output (must be',
          '0 on every size, 2x2 with its penalty included: the commit follows the selection\'s own choice). *not least*: the committed VL is not a candidate of least cost',
          'among those that the selected output keeps (must be 0). Two values of `lut_bias` per size: the frozen value of the main row, and 4.', '',
          '| size | lut_bias | scenario | heads checked | unique | tie | different | not least | largest difference of the least cost |', '|---|---|---|---|---|---|---|---|---|']
    tot = {}
    for z, p, d, nc in chk:
        l = res[nc]['deft_lb'] if res[nc] else {}
        t = tot.setdefault(z, [0, 0, 0, 0, 0])
        vals = [l.get(k, 0) for k in ('commit_checked', 'commit_check_unique', 'commit_check_tie', 'commit_check_different', 'commit_check_not_least')]
        for i, v in enumerate(vals):
            t[i] += v
        L.append('| %s | %s | %s | %d | %d | %d | %d | %d | %g |' % tuple([z, R.fmt(d), p] + vals + [l.get('commit_check_max_gap', -1)]))
    L += ['', '| size | heads checked | unique | tie | different | not least |', '|---|---|---|---|---|---|']
    for z in SIZES:
        L.append('| %s | %d | %d | %d | %d | %d |' % tuple([z] + tot[z]))
    bad = sum(tot[z][3] + tot[z][4] for z in SIZES)
    short = [z for z in SIZES if tot[z][0] != CHECK_N * len(CHECK_D) * 6]
    ok = ok and bad == 0 and not short
    L += ['', '**Different or not least, over the three sizes: %d.** Sizes with fewer than %d checked heads: %s.' % (bad, CHECK_N * len(CHECK_D) * 6, ', '.join(short) or 'none'), '',
          '## 3. `commit_check` reads only', '',
          '`EB_first` on uniform traffic with and without `commit_check`. Compared: the whole `summary` block and every field of `deft_lb` except those of the check.', '',
          '| size | lut_bias | accepted without / with | latency without / with | identical |', '|---|---|---|---|---|']
    n = 0
    for z, p, d, na, nb in ro:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and a['deft_lb'] == {k: v for k, v in b['deft_lb'].items() if not k.startswith('commit_check')}
        n += eq
        L.append('| %s | %s | %.6f / %.6f | %.4f / %.4f | %s |' % (z, R.fmt(d), stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1], 'yes' if eq else '**no**'))
    ok = ok and n == len(ro)
    L += ['', '**%d / %d identical.**' % (n, len(ro)), '',
          '## 4. At most one decision with more than one offered output per head', '',
          'Per run of check 2: the measured heads that were bound (a commit is a decision at which the routing function offers the head more than one output), the',
          'largest number of commits of one head (counted per packet; must be 1), the hops at which a head is offered more than one output after it left the router',
          'before its commit router (`hops_chip_multi` + `hops_ipos_multi`; must be 0), and where the commit is made: at the router below the exit VL (the decision',
          'computed at the Down move) or further on.', '',
          '| size | lut_bias | scenario | Up moves | heads bound | share bound | bound below the exit VL | share | most commits of one head | multi-output hops after |', '|---|---|---|---|---|---|---|---|---|---|']
    mx_all = multi_all = 0
    for z, p, d, nc in chk:
        l = res[nc]['deft_lb'] if res[nc] else {}
        up, bd, bl, mx = l.get('entry_up_moves', 0), l.get('entry_commit_first_bound', 0), l.get('entry_commit_first_below', 0), l.get('entry_commit_first_max_per_head', 99)
        mh = R.multi_hops(res[nc]) if res[nc] else 99
        mx_all, multi_all = max(mx_all, mx), multi_all + mh
        L.append('| %s | %s | %s | %d | %d | %.1f %% | %d | %.1f %% | %d | %d |' % (z, R.fmt(d), p, up, bd, 100.0 * bd / max(1, up), bl, 100.0 * bl / max(1, bd), mx, mh))
    ok = ok and mx_all == 1 and multi_all == 0
    L += ['', '**Most commits of one head over all runs: %d. Multi-output hops after the commit: %d.**' % (mx_all, multi_all), '',
          '**All unit checks pass: %s.**' % ('yes' if ok else 'NO')]
    wmd('unit_checks_first.md', L)
    if ok:
        shutil.rmtree(out)
    return ok


def fdrain_rows(tuned):
    if tuned:
        return [('EB_first', lambda z: R.row_args(z, 'EB_first'))]
    return [('EB_first_Dmain', lambda z: R.first_args(z, main_d(z))), ('EB_first_D4', lambda z: R.first_args(z, 4.0))]


def first_drain_report(res, path):
    """The drain-test CSV of round 19 with two more columns: the hops that offer more than one output after the commit, and the largest
    number of commits of one head."""
    rows, fails = [], 0
    for name in sorted(res):
        d = res[name]
        wl, v, sm, seed = name.split('__')
        if d is None:
            rows.append([wl, v, sm, seed, 'NO_OUTPUT', '', '', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        mx = l.get('entry_commit_first_max_per_head', '')
        ok = (s.get('drain_stop_reason') == 'drain_completed' and s['measured_received_packets'] == s['measured_injected_packets'] and
              l['dead_end_events'] == 0 and R.multi_hops(d) == 0 and mx != '' and int(mx) <= 1)
        fails += not ok
        rows.append([wl, v, sm, seed, s.get('drain_stop_reason'), s['measured_injected_packets'], s['measured_received_packets'],
                     l['dead_end_events'], s.get('drain_completed_cycle'), R.multi_hops(d), mx, 'PASS' if ok else 'FAIL'])
    with open(path, 'w', newline='') as f:
        w = csv.writer(f, lineterminator=NL)
        w.writerow(['workload', 'variant', 'size-mask', 'seed', 'stop_reason', 'injected', 'received', 'dead_end_events', 'drain_completed_cycle',
                    'hops_multi', 'max_commits_per_head', 'result'])
        w.writerows(rows)
    print('runs=%d failures=%d' % (len(rows), fails))
    return fails


def fdrain(nproc, tuned):
    js = [allpairs(row, z, m, f(z)) for z in SIZES for row, f in fdrain_rows(tuned) for m in EV27.drain_masks(z)]
    stage = 'fdrain_tuned' if tuned else 'fdrain'
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = run_seg(js, X.raw(stage), nproc, 14400)
    fails = first_drain_report(res, os.path.join(RES, 'drain_first_tuned.csv' if tuned else 'drain_first.csv'))
    print('drain tests: %d, failures %d (a failure includes a hop that offers more than one output after the commit, or a head with more than one commit), wall %.0f s' % (
        len(js), fails, time.time() - t), flush=True)
    if not fails:
        shutil.rmtree(X.raw(stage))
    return not fails


# =====================================================================================================================
# the three new traffic patterns
# =====================================================================================================================
CHECK_RATE = 0.0050


def read_table(path):
    """{source: [(destination, rate)]} of a traffic table without time phases."""
    T = {}
    for line in open(path):
        if line.startswith('%') or not line.strip():
            continue
        f = line.split()
        assert len(f) == 3, (path, line)
        T.setdefault(int(f[0]), []).append((int(f[1]), float(f[2])))
    return T


def traffic():
    import glob
    import gen_traffic as G
    ok = True
    L = ['# A2: the tables of the three new traffic patterns (experiments_v29.py a2_traffic)', '',
         '`gen_traffic.py --patterns tornado,neighbour,randperm`. Checked on every table of the three patterns that exists in the traffic folders when the stage is run',
         '(the table at %.4f packets/cycle/source, written for this check, and the tables of the ladders once B0 has made them), read back from the files:' % CHECK_RATE,
         '*sources*: every router of the chiplet layer sends; *sum*: the rates of a source add up to the nominal rate of the table (largest deviation over the sources,',
         'in packets/cycle; the tables have nine decimals per line); *pattern*: `tornado`: one destination per source, in the same row, ((x + FW / 2 - 1) mod FW, y);',
         '`neighbour`: the destinations of a source are exactly the routers of the chiplets that share an edge with its chiplet, each with the same rate; `randperm`:',
         'one destination per source, the destinations are a permutation of the routers, no router sends to itself, and the table is the one of',
         '`gen_traffic.randperm_table()` (`random.Random(2901)`), which is written to `randperm_<size>.txt`.', '',
         '| size | pattern | tables | routers | sources | largest deviation of a sum | pattern | destinations in the own chiplet |', '|---|---|---|---|---|---|---|---|']
    for z in SIZES:
        cx, cy = E5.SIZES[z]
        G.set_size(cx, cy, 4, 4)
        perm = G.randperm_table()
        with open(os.path.join(RES, 'randperm_%s.txt' % z), 'w', newline='') as f:
            f.write('% randperm on ' + z + ': source destination (random.Random(2901).shuffle on list(range(N)), shuffled again until no fixed point)' + NL)
            f.write(''.join('%d %d' % (s, perm[s]) + NL for s in range(G.N)))
        for pat in R.NEW_PATTERNS:
            E5.gen_tables(z, pat, [CHECK_RATE])
            files = sorted(glob.glob(os.path.join(HERE, E5.tdir(z), '%s_*.txt' % pat)))
            src_ok = pat_ok = True
            dev = 0.0
            intra = None
            for path in files:
                rate = float(os.path.basename(path)[len(pat) + 1:-4])
                T = read_table(path)
                src_ok = src_ok and sorted(T) == list(range(G.N))
                for s, ds in T.items():
                    dev = max(dev, abs(sum(r for _, r in ds) - rate))
                    dst = [d for d, _ in ds]
                    if pat == 'tornado':
                        x, y = s % G.FW, s // G.FW
                        pat_ok = pat_ok and dst == [y * G.FW + (x + G.FW // 2 - 1) % G.FW] and dst[0] // G.FW == y and dst[0] != s
                    elif pat == 'randperm':
                        pat_ok = pat_ok and dst == [perm[s]] and dst[0] != s
                    else:
                        c = G.chiplet(s)
                        adj = {k for k in range(G.C) if abs(k % cx - c % cx) + abs(k // cx - c // cx) == 1}
                        want = sorted(d for d in range(G.N) if G.chiplet(d) in adj)
                        pat_ok = pat_ok and sorted(dst) == want and len({r for _, r in ds}) == 1
                if pat == 'randperm':
                    pat_ok = pat_ok and sorted(ds[0][0] for ds in T.values()) == list(range(G.N))
                intra = sum(r for s, ds in T.items() for d, r in ds if G.chiplet(d) == G.chiplet(s)) / sum(r for ds in T.values() for _, r in ds)
            good = bool(files) and src_ok and pat_ok and dev < 1e-7
            ok = ok and good
            L.append('| %s | %s | %d | %d | %s | %.1e | %s | %.1f %% |' % (z, pat, len(files), G.N, 'all' if src_ok else '**NOT ALL**', dev, 'yes' if pat_ok else '**NO**',
                                                                       100.0 * (intra or 0.0)))
    L += ['', '**All tables pass: %s.**' % ('yes' if ok else 'NO')]
    wmd('traffic_checks.md', L)
    return ok


def tdrain_jobs():
    P = R.lp()
    js = []
    for z in SIZES:
        rows = R.REFS5 + [MAIN] + (['LB_b0'] if z == '2x2' else [])
        for p, m in R.new_scenarios(z):
            lad = P[X.lkey(z, p, m)]['eval']
            E5.gen_tables(z, p, [lad[1], lad[3]])
            for row in rows:
                for i in (1, 3):
                    a = common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(z), p, lad[i]), lut=X23.lut23(z, m)) + E5.size_args(z) + \
                        R.row_args(z, row) + X23.pipe(2) + X24.TRNG + (E10.DRAIN_OVERSAT_2X2 if z == '2x2' else E10.DRAIN_OVERSAT)
                    js.append(('%s%.4f__%s-p2__%s-%s__s1' % (p, lad[i], row, z, m), a))
    return js


def tdrain(nproc):
    js = tdrain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = run_seg(js, X.raw('tdrain'), nproc, 14400)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_traffic.csv'))
    print('drain tests: %d, failures %d, wall %.0f s' % (len(js), fails, time.time() - t), flush=True)
    if not fails:
        shutil.rmtree(X.raw('tdrain'))
    return not fails


# =====================================================================================================================
# the referee's independent check
# =====================================================================================================================
FORMAL_MODES = ('main', 'turnmodels', 'rules', 'placements')
FORMAL_WRAP = ('import sys, runpy; sys.path.append(sys.argv[1]); script, mode = sys.argv[2], sys.argv[3]; sys.argv = [script, mode]; '
               'runpy.run_path(script, run_name="__main__")')


def formal():
    script = os.path.join(HERE, 'formal', 'lb_cdg_check.py')
    out = os.path.join(RES, 'formal_independent')
    os.makedirs(out, exist_ok=True)
    if not os.path.exists(script):
        wmd('formal_independent/README.md', ['# A2: the referee\'s independent check (experiments_v29.py a2_formal)', '', '`formal/lb_cdg_check.py` is missing; the check was not run.'])
        return True
    sha = hashlib.sha256(open(script, 'rb').read()).hexdigest()
    git = subprocess.run(['git', '-C', HERE, 'status', '--porcelain', '--', 'formal/lb_cdg_check.py'], capture_output=True, text=True).stdout.strip()
    pkgs = os.path.join(os.path.expanduser('~'), 'lbpkgs')
    info = {}
    for mode in FORMAL_MODES:
        t = time.time()
        r = subprocess.run([sys.executable, '-I', '-c', FORMAL_WRAP, pkgs, script, mode], capture_output=True, text=True, cwd=out, timeout=6 * 3600)
        open(os.path.join(out, mode + '.txt'), 'w', newline=NL).write(r.stdout + (('--- stderr ---' + NL + r.stderr) if r.stderr.strip() else ''))
        info[mode] = dict(rc=r.returncode, seconds=time.time() - t, lines=r.stdout.splitlines())
        print('%s: exit %d, %.0f s' % (mode, r.returncode, time.time() - t), flush=True)

    def blocks(mode):
        """[(title, {dead ends, paths > d0, exits outside M0, down dependencies, acyclic})] of an output."""
        B = []
        for ln in info[mode]['lines']:
            if not ln.startswith(' ') and ':' in ln and 'channels' in ln:
                B.append((ln.split(':')[0], {}))
            elif B and 'dead ends:' in ln:
                f = ln.replace('paths > d0:', '|').replace('exits outside M0:', '|').replace('N/S-moving', '|').replace('dead ends:', '').split('|')
                B[-1][1].update(dead=int(f[0]), long=int(f[1]), wrong=int(f[2]))
            elif B and 'CDG acyclic:' in ln:
                B[-1][1].update(down=int(ln.split('lower class:')[1].split()[0]), acyclic=ln.strip().endswith('True'))
        return B
    main_b, rules_b, tm_b, pl_b = blocks('main'), blocks('rules'), blocks('turnmodels'), blocks('placements')
    ok_main = len(main_b) == 6 and all(b.get('dead') == 0 and b.get('long') == 0 and b.get('wrong') == 0 and b.get('acyclic') for _, b in main_b)
    ok_rules = len(rules_b) == 3 and all(b.get('acyclic') is False for _, b in rules_b)
    ok_rc = all(v['rc'] == 0 for v in info.values())
    L = ['# A2: the referee\'s independent check (experiments_v29.py a2_formal)', '',
         '`formal/lb_cdg_check.py` is the independent referee\'s re-implementation of the routing function, the VN rules and the channel dependency graph. It was placed',
         'in the repository for this round and is not edited (sha256 %s; `git status` of the file when this was written: %s).' % (sha, git or 'clean, as committed'),
         'Each mode is run with `python3 -I` (isolated: no environment variables, no user site, the script\'s folder not on the path). The script needs `networkx`,',
         'which this machine has only under `~/lbpkgs`; so the interpreter is started as `python3 -I -c WRAP ~/lbpkgs formal/lb_cdg_check.py MODE`, where WRAP',
         'appends that one folder to the end of `sys.path` and runs the script unchanged with `runpy` (`experiments_v29_gates.FORMAL_WRAP`). The outputs are',
         '`main.txt`, `turnmodels.txt`, `rules.txt` and `placements.txt` in this folder, as printed.', '',
         '| mode | exit code | seconds | configurations |', '|---|---|---|---|'] + [
        '| %s | %d | %.0f | %d |' % (m, info[m]['rc'], info[m]['seconds'], len(blocks(m))) for m in FORMAL_MODES] + [
        '', '## What the prompt asks the check to report', '',
        '* **`main`: no dead end, no path longer than d0, an acyclic CDG for XY and for the VN-split order on 4, 9 and 16 chiplets: %s.**' % ('yes' if ok_main else 'NO'), '',
        '  | configuration | dead ends | paths > d0 | exits outside M0 | dependencies to a lower class | CDG acyclic |', '  |---|---|---|---|---|---|'] + [
        '  | %s | %s | %s | %s | %s | %s |' % (t, b.get('dead'), b.get('long'), b.get('wrong'), b.get('down'), b.get('acyclic')) for t, b in main_b] + [
        '', '* **`rules`: a cycle when R2, R3 or R1 is dropped: %s.**' % ('yes' if ok_rules else 'NO'), '',
        '  | configuration | dead ends | paths > d0 | dependencies to a lower class | CDG acyclic |', '  |---|---|---|---|---|'] + [
        '  | %s | %s | %s | %s | %s |' % (t, b.get('dead'), b.get('long'), b.get('down'), b.get('acyclic')) for t, b in rules_b] + [
        '', '## The two other modes (stored; the prompt names no requirement for them)', '',
        '| mode | configuration | dead ends | paths > d0 | CDG acyclic |', '|---|---|---|---|---|'] + [
        '| %s | %s | %s | %s | %s |' % (m, t, b.get('dead'), b.get('long'), b.get('acyclic')) for m, B in (('turnmodels', tm_b), ('placements', pl_b)) for t, b in B] + [
        '', '**The check reports what the prompt asks: %s.**' % ('yes' if ok_main and ok_rules and ok_rc else 'NO')]
    wmd('formal_independent/README.md', L)
    return ok_main and ok_rules and ok_rc


# =====================================================================================================================
# reuse of the rows of rounds 25, 26 and 28
# =====================================================================================================================
def reuse(nproc):
    import experiments_v25_eval as EV25
    P25, P26 = X25.lp(), EV26.lpf()
    out = X.raw('reuse')
    parts = []
    # round 25: the main row and DeFT_P, uniform and movinghot, 1.0 x Lsat, seeds 121 and 122
    js = []
    for z in SIZES:
        for p in ('uniform', 'movinghot'):
            m = E5.FREE[z]
            r = P25[X.lkey(z, p, m)]['eval'][3]
            E5.gen_tables(z, p, [r])
            for row in ('DeFT_P', MAIN):
                js += [X.job('r25', z, row, X25.row_args(z, row), 2, p, m, r, s) for s in (121, 122)]
    parts.append(('25', 'r25', js, os.path.join(X25.RES, 'eval_runs.csv'), EV25.to_csv,
                  'the main row and DeFT_P (`experiments_v25.row_args`), uniform and movinghot traffic at 1.0 x Lsat, seeds 121 and 122'))
    # round 26: the same two rows on mask 1 of the rates 1/16 (hotspot) and 4/16 (uniform), 1.0 x Lsat of the mask, seeds 151 and 152
    js = []
    for e in X26.part_b():
        if e['index'] != 1 or e['rate'] not in ('1/16', '4/16'):
            continue
        z, m, p = e['size'], e['mask'], ('hotspot' if e['rate'] == '1/16' else 'uniform')
        r = P26[EV26.key(z, p, m)]['eval'][1]
        E5.gen_tables(z, p, [r])
        for row in ('DeFT_P', MAIN):
            js += [X.job('r26', z, row, X26.row_args(z, row), 2, p, m, r, s) for s in (151, 152)]
    parts.append(('26', 'r26', js, os.path.join(X26.RES, 'fault_rate_runs.csv'), EV25.to_csv,
                  'the main row and DeFT_P on mask 1 of the rate 1/16 (hotspot traffic) and of the rate 4/16 (uniform traffic), at 1.0 x Lsat of the mask, seeds 151 and 152'))
    # round 28: DeFT_P, the main row (with entry_stats, as that round ran it) and the three tuned early rows, uniform and chiptrans, seeds 171 and 172
    js = []
    for z in SIZES:
        for p in ('uniform', 'chiptrans'):
            m = E5.FREE[z]
            r = P25[X.lkey(z, p, m)]['eval'][3]
            E5.gen_tables(z, p, [r])
            for row in ('DeFT_P', MAIN, 'EB_best', 'EB_best64', 'EB_down_t'):
                js += [X.job('r28', z, row, EV28.row_args(z, row), 2, p, m, r, s) for s in (171, 172)]
    parts.append(('28', 'r28', js, os.path.join(EV28.RES, 'eval_runs.csv'), EV28.to_csv,
                  'DeFT_P, the main row and the tuned early rows `EB_best`, `EB_best64` and `EB_down_t` (`experiments_v28_eval.row_args`), uniform and chiptrans traffic at 1.0 x Lsat, seeds 171 and 172'))
    alljobs = [j for _, _, js, _, _, _ in parts for j in js]
    print('reuse jobs: %d' % len(alljobs), flush=True)
    run_jobs(alljobs, out, nproc=X.width(nproc), timeout=14400)
    L = ['# The reused rows of rounds 25, 26 and 28 are reproduced by the build of this round (experiments_v29.py a2_reuse)', '',
         'Before a part pairs new rows with rows of an earlier round, runs of that round are made again with the `bin/noxim` of this round and the row definitions of',
         'that round, and compared with the rows of its per-run file: every column of that file, as text.', '']
    ok = True
    for rnd, stage, js, path, tocsv, what in parts:
        sub = os.path.join(out, 'csv_' + stage)
        os.makedirs(sub, exist_ok=True)
        for n, _ in js:
            src = os.path.join(out, n + '.json')
            dst = os.path.join(sub, n + '.json')
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy(src, dst)
        tmp = os.path.join(X.RAW, 'reuse_%s.csv' % stage)
        tocsv(sub, tmp)
        old = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(path))}
        new = list(csv.DictReader(open(tmp)))
        by, diff = {}, []
        for r in new:
            o = old.get((r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
            k = (r['pattern'].split('-')[0], r['variant'][:-3])
            t = by.setdefault(k, [0, 0])
            t[0] += 1
            if o is not None and all(o[c] == r[c] for c in o):
                t[1] += 1
            else:
                diff.append('%s %s %s %s s%s' % (r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
        same = sum(v[1] for v in by.values())
        good = same == len(js) and len(new) == len(js)
        ok = ok and good
        L += ['## Round %s' % rnd, '', 'Runs: %s. Compared with `%s`.' % (what, os.path.relpath(path, HERE).replace(os.sep, '/')), '',
              '| size | row | runs | identical |', '|---|---|---|---|'] + ['| %s | %s | %d | %d |' % (k[0], k[1], v[0], v[1]) for k, v in sorted(by.items())] + [
            '', '**%d / %d runs identical.**' % (same, len(js))] + (['', 'Different: ' + '; '.join(diff[:40])] if diff else []) + ['']
        os.remove(tmp)
    L += ['**Every reused row is reproduced: %s.**' % ('yes' if ok else 'NO')]
    wmd('reuse_check.md', L)
    if ok:
        shutil.rmtree(out)
    return ok


def run_stage(stage, nproc, extra):
    if stage == 'a2_bufid':
        sys.exit(0 if bufid(nproc) else 1)
    elif stage == 'a2_bufdrain':
        sys.exit(0 if bufdrain(nproc) else 1)
    elif stage == 'a2_fanchor':
        sys.exit(0 if fanchor(nproc) else 1)
    elif stage == 'a2_funits':
        sys.exit(0 if funits(nproc) else 1)
    elif stage == 'a2_fdrain':
        sys.exit(0 if fdrain(nproc, extra == 'tuned') else 1)
    elif stage == 'a2_traffic':
        sys.exit(0 if traffic() else 1)
    elif stage == 'a2_tdrain':
        sys.exit(0 if tdrain(nproc) else 1)
    elif stage == 'a2_formal':
        sys.exit(0 if formal() else 1)
    elif stage == 'a2_reuse':
        sys.exit(0 if reuse(nproc) else 1)
    else:
        raise SystemExit(__doc__)
