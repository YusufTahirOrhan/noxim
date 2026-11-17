"""v28 gates, tuning, evaluation, fault runs and the reports across the VLs under faults (results_v28_anchor/PREREGISTRATION.md), run
through experiments_v28.py:
  a2_anchor   the two anchors against DeFT_P: EBf(route, 1, 1, infinity) (oracle_bias 1e9) and EB_down with lut_bias 1e9, each as the rows
              of the round draw their tie-breaks (rand()) and with the diagnostic tie_stream 1 -> anchor.md, anchor.json
  a2_repro    v27 reproduced: EB_vl_b1 = EBf(vl, 0, 1, 0) and EB_route_b4 = EBf(route, 0, 4, 0), with DeFT_P and the main row, on the tuning
              cells of 2x2 and 4x4, against results_v27_early/tune_runs.csv (every column) -> repro_v27.md
  a2_units    unit checks: the pending counters against a scan of the network; pending_check reads only; the snapshots of oracle_period;
              the share of packets off DeFT-P's entry VL by T (description) -> unit_checks.md
  a2_drain    all-pairs drain tests (extra = tuned: the tuned rows) -> drain_v28.csv / drain_v28_tuned.csv
  b_rule      the tuning rule -> tuning_v28.md (written before any tuning run)
  b_tune      B1 and B3 (grids and extensions), then the B1 choice and B2 (grid and extensions); resumable (state in ~/lbraw/v28/tune_state.json)
  b_choose    scores and choice -> tuning_v28.md, tuning_choice_v28.json, tune_runs.csv, paper_data/tuning_v28.csv (raw outputs deleted)
  c_timing    timing runs of Parts C, D and E (runs of the designs, kept) -> runtime_estimate.md, drops.json
  c_eval, c_check, c_csv      Part C: seeds 171-180 -> eval_runs.csv
  d_reuse     DeFT_P and the main row of round 26 on masks 1 and 2 of every rate and size, against results_v26_faults/fault_rate_runs.csv
              -> reuse_check.md
  d_eval, d_check, d_csv      Part D: the early rows on the masks of rates 1/16 and 4/16 of round 26 -> fault_runs.csv
  e_eval, e_check, e_csv      Part E: LB_noVLrep on the 192 masks of round 26 -> novlrep_runs.csv
Row names carry the pipe depth as a suffix (-p2). Tuning configurations: EBf_<S>_P<P>_B<B>_T<T> (B1), EBf64_... (B2, oracle_period 64),
EBd_D<D> (B3, EB_down with lut_bias D).
"""
import csv
import glob
import json
import math
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v26 as X26  # noqa: E402
import experiments_v26_eval as EV26  # noqa: E402
import experiments_v27_eval as EV27  # noqa: E402
import experiments_v28 as X  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL, MAIN = X.RES, X.SIZES, X.NL, X.MAIN
lb = X.lb
ENERGY = EV27.ENERGY
ES = lb('entry_stats', 1)                      # observation only (v27 unit_checks.md)
INF = 1e9                                      # T = infinity: oracle_bias (or lut_bias) 1e9
V27_TUNE = os.path.join(EV27.RES, 'tune_runs.csv')
CHOICE = os.path.join(RES, 'tuning_choice_v28.json')
ANCHOR = os.path.join(RES, 'anchor.json')
DROPS = os.path.join(RES, 'drops.json')
SEEDS_C = range(171, 181)
SEEDS_D = (151, 152)
D_RATES = ('1/16', '4/16')
LIMIT_H = 30.0
V28_FIELDS = ('oracle_pending_left_abs', 'oracle_pending_left_nonzero', 'oracle_samples')
EXTRA_FIELDS = EV27.EXTRA_FIELDS + V28_FIELDS
PCHECK = 3000                                  # cycles of the pending check (unit checks): 3000, 6000, 9000


def fmt(x):
    return '%g' % x


def tstr(T):
    return 'inf' if T >= INF else fmt(T)


# =====================================================================================================================
# Rows
# =====================================================================================================================
def ebf_args(S, P, B, T, period=0, tie=False):
    """The early family EBf(S, P, B, T): the entry VL e of least hops(e) + B (occ_S(e) + P pending(e)) + B T [e is not DeFT-P's entry
    VL]. T >= INF stands for infinity (oracle_bias 1e9). period: oracle_period. tie: the diagnostic tie_stream 1 (anchor gate only)."""
    bias = INF if T >= INF else B * T
    a = ['-routing', 'DEFT_LB'] + lb('exit', 'lut', 'entry', 'oracle', 'oracle_scope', S, 'oracle_pending', P, 'oracle_beta', fmt(B),
                                     'oracle_bias', fmt(bias)) + X24.REL_X + X24.HOPS
    if period:
        a += lb('oracle_period', period)
    if tie:
        a += lb('tie_stream', 1)
    return a + X23.VN_P + ES


def down_args(size, D, tie=False):
    """EB_down of v27 (the main row with entry_commit down) with lut_bias D (D >= INF: 1e9). Everything else is the frozen main row."""
    a = list(X25.row_args(size, MAIN))
    assert a.count('lut_bias') == 1
    i = a.index('lut_bias')
    a[i + 1] = fmt(D)
    a += lb('entry_commit', 'down')
    if tie:
        a += lb('tie_stream', 1)
    return a + ES


def fname(S, P, B, T, period=0):
    return '%s_%s_P%d_B%s_T%s' % ('EBf64' if period else 'EBf', S, P, fmt(B), tstr(T))


def dname(D):
    return 'EBd_D%s' % tstr(D)


def choice():
    return json.load(open(CHOICE))


def anchors_extra():
    """The anchor rows that join the evaluation because they are not identical to DeFT_P (anchor.json)."""
    a = json.load(open(ANCHOR)) if os.path.exists(ANCHOR) else {}
    return [r for r in ('EB_inf', 'EB_down_inf') if r in a and not a[r]['identical']]


def row_args(size, row):
    """Noxim arguments of a row of this round, without the pipe depth and -traffic_rng (job() adds both)."""
    if row == 'DeFT_P':
        return X25.row_args(size, 'DeFT_P')
    if row == MAIN:
        return X25.row_args(size, MAIN) + ES
    if row == 'LB_noVLrep':
        return X25.row_args(size, MAIN) + lb('up_report', 0) + ES
    c = choice()[size]
    if row == 'EB_best':
        b = c['EB_best']
        return ebf_args(b['S'], b['P'], b['B'], b['T'])
    if row == 'EB_best64':
        b = c['EB_best64']
        return ebf_args(b['S'], b['P'], b['B'], b['T'], period=64)
    if row == 'EB_down_t':
        return down_args(size, c['EB_down_t']['D'])
    if row == 'EB_inf':                       # the T = infinity member of EB_best's sub-family
        b = c['EB_best']
        return ebf_args(b['S'], b['P'], b['B'], INF)
    if row == 'EB_down_inf':
        return down_args(size, INF)
    raise ValueError(row)


def run_seg(js, out, nproc, timeout, seg=384):
    """run_jobs in segments, each with the number of processes that ~/lbraw/v28/width.txt gives at that moment (experiments_v28.width;
    experiments_v26_eval.run_seg reads the width file of round 26)."""
    res = {}
    for k in range(0, len(js), seg):
        w = X.width(nproc)
        print('%s runs %d-%d of %d with %d processes' % (time.strftime('%H:%M:%S'), k + 1, min(k + seg, len(js)), len(js), w), flush=True)
        res.update(run_jobs(js[k:k + seg], out, nproc=w, timeout=timeout))
    return res


def ff_scenarios(size):
    """The six fault-free scenarios of round 25."""
    return [(p, m) for p, m in X25.scenarios(size) if not X25.faulty(m)]


def job(stage, size, name, args, p, m, rate, seed, extra=()):
    return X.job(stage, size, name, args, 2, p, m, rate, seed, extra)


def strip(d, drop):
    return {k: v for k, v in d.items() if k not in drop}


def stats4(d):
    s = d['summary']
    return (s['average_ip_throughput_flits_per_cycle_per_ip'], s['global_average_delay_cycles'], d['deft_lb']['delay_p99'], s['total_received_packets'])


def wmd(name, L):
    open(os.path.join(RES, name), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


def multi_hops(d):
    l = d['deft_lb']
    return int(l.get('hops_chip_multi', 0)) + int(l.get('hops_ipos_multi', 0))


# =====================================================================================================================
# A2: gates
# =====================================================================================================================
def gate_runs(size):
    """The runs of the anchor gate: the six fault-free scenarios at 1.0 x Lsat with seed 101, and uniform traffic on mask 1 of rate 4/16 of
    round 26 at 1.0 x Lsat (of that mask) with seed 151."""
    P = X25.lp()
    out = []
    for p, m in ff_scenarios(size):
        r = P[X.lkey(size, p, m)]['eval'][3]
        E5.gen_tables(size, p, [r])
        out.append((p, m, r, 101))
    e = [e for e in X26.part_b() if e['size'] == size and e['rate'] == '4/16' and e['index'] == 1][0]
    r = EV26.lpf()[EV26.key(size, 'uniform', e['mask'])]['eval'][1]
    E5.gen_tables(size, 'uniform', [r])
    out.append(('uniform', e['mask'], r, 151))
    return out


ANCHOR_ROWS = [('EB_inf', lambda z: ebf_args('route', 1, 1.0, INF)), ('EB_inf_ts', lambda z: ebf_args('route', 1, 1.0, INF, tie=True)),
               ('EB_down_inf', lambda z: down_args(z, INF)), ('EB_down_inf_ts', lambda z: down_args(z, INF, tie=True))]
OTHER_INF = ('EB_inf_other', lambda z: ebf_args('vl', 0, 0.5, INF, period=64))     # T = infinity with other S, P, B and oracle_period 64
ANCHOR_KEYS = ('packets_measured', 'delay_mean', 'delay_p50', 'delay_p95', 'delay_p99', 'delay_inter_mean', 'delay_inter_p99', 'delay_intra_mean',
               'packets_inter', 'packets_intra', 'vl_down_packets', 'vl_up_packets', 'dead_end_events')


def same_as_deft(a, b):
    return bool(a) and bool(b) and strip(a['summary'], ENERGY) == strip(b['summary'], ENERGY) and all(a['deft_lb'][k] == b['deft_lb'][k] for k in ANCHOR_KEYS)


def anchor(nproc):
    js, meta = [], []
    for z in SIZES:
        for p, m, r, seed in gate_runs(z):
            a = job('anchor', z, 'DeFT_P', X25.row_args(z, 'DeFT_P'), p, m, r, seed)
            js.append(a)
            names = {}
            for row, f in ANCHOR_ROWS + [OTHER_INF]:
                b = job('anchor', z, row, f(z), p, m, r, seed)
                js.append(b)
                names[row] = b[0]
            meta.append((z, p, m, r, seed, a[0], names))
    res = run_jobs(js, X.raw('anchor'), nproc=nproc, timeout=7200)
    out = {}
    L = ['# A2: the two anchors against DeFT_P (experiments_v28.py a2_anchor)', '',
         'Is DeFT_P a member of the two early families? `EB_inf` = EBf(route, 1, 1, infinity): `-routing DEFT_LB -deft_lb exit lut -deft_lb entry oracle`',
         '`-deft_lb oracle_scope route -deft_lb oracle_pending 1 -deft_lb oracle_beta 1 -deft_lb oracle_bias 1e9` with XY in both layers; `EB_down_inf` =',
         '`EB_down` of round 27 (the main row with `entry_commit down`) with `lut_bias 1e9`. Both with DeFT-P\'s VN options and `-deft_lb entry_stats 1`',
         '(it only counts). Against `DeFT_P` (`-routing DEFT -deft_lut_entry dst` with the same VN options). Runs: the six fault-free scenarios at 1.0 x Lsat',
         'with seed 101, and uniform traffic on mask 1 of rate 4/16 of round 26 at 1.0 x Lsat of that mask with seed 151; pipe_all 2, `-traffic_rng 1`.',
         'Compared: every field of the `summary` block except the three energy fields, and the delay statistics, the packets per VL and the dead-end',
         'events of the `deft_lb` block. `_ts`: the same row with the diagnostic `-deft_lb tie_stream 1`, with which the tie-breaks of the injection-time',
         'choice and of the commit draw from a stream of their own instead of `rand()`, the stream the routers\' crossbar arbitration draws from',
         '(`Router.cpp`, `rand() % reservations.size()`). Off packets: the share of the measured Up moves on a VL that is not DeFT-P\'s entry VL',
         '(`entry_stats`); 0 means every packet took DeFT-P\'s entry VL.', '']
    for row, _ in ANCHOR_ROWS:
        L += ['## `%s`' % row, '', '| size | scenario | mask | rate | seed | THR DeFT_P / row | LAT DeFT_P / row | P99 DeFT_P / row | off packets | identical |',
              '|---|---|---|---|---|---|---|---|---|---|']
        same = off = 0
        lr = []
        for z, p, m, r, seed, na, names in meta:
            a, b = res[na], res[names[row]]
            eq = same_as_deft(a, b)
            same += eq
            nd = b['deft_lb']['entry_up_not_default'] if b else -1
            off += nd != 0
            sa, sb = stats4(a), stats4(b)
            lr.append((math.log(sb[0] / sa[0]), math.log(sb[1] / sa[1]), math.log(sb[2] / sa[2])))
            L.append('| %s | %s | %s | %.4f | %d | %.6f / %.6f | %.3f / %.3f | %s / %s | %d | %s |' % (z, p, m, r, seed, sa[0], sb[0], sa[1], sb[1], sa[2], sb[2], nd,
                                                                                            'yes' if eq else '**no**'))
        n = len(meta)
        mean = [100.0 * (math.exp(sum(x[k] for x in lr) / n) - 1.0) for k in range(3)]
        L += ['', '**%d / %d identical.** Runs with a packet off DeFT-P\'s entry VL: %d. Mean of the %d runs against DeFT_P: THR %+.2f %%, LAT %+.2f %%, P99 %+.2f %%.' % (
            same, n, off, n, mean[0], mean[1], mean[2]), '']
        out[row] = dict(identical=same == n, same=same, runs=n, runs_off_default=off, mean_thr=mean[0], mean_lat=mean[1], mean_p99=mean[2])
    for row in ('EB_inf', 'EB_down_inf'):
        o, t = out[row], out[row + '_ts']
        if o['identical']:
            L.append('* `%s` is identical to DeFT_P in every run: the family contains DeFT_P.' % row)
        elif t['identical'] and o['runs_off_default'] == 0:
            L.append('* `%s` is not identical to DeFT_P, but every packet takes DeFT-P\'s entry VL, and with its tie-breaks on a stream of their own (`%s_ts`) it is '
                     'identical in every run. So the only difference is the random stream: one more draw per injection (`EB_inf`) or per commit (`EB_down_inf`) '
                     'shifts every later draw of the crossbar arbitration. The row is DeFT_P\'s routing with another arbitration sequence; it joins Parts C and D as an '
                     'anchor (`DECISIONS.md`).' % (row, row))
        else:
            L.append('* `%s` is not identical to DeFT_P and the tie stream does not explain it (`%s_ts` identical: %s; runs off DeFT-P\'s VL: %d). See `DECISIONS.md`.' % (
                row, row, 'yes' if t['identical'] else 'no', o['runs_off_default']))
    oth = sum(1 for _, _, _, _, _, _, names in meta if res[names['EB_inf']] and res[names['EB_inf_other']] and
              res[names['EB_inf']]['summary'] == res[names['EB_inf_other']]['summary'] and
              all(res[names['EB_inf']]['deft_lb'][k] == res[names['EB_inf_other']]['deft_lb'][k] for k in ANCHOR_KEYS + ('entry_up_moves', 'entry_up_not_default')))
    out['EB_inf_other'] = dict(same_as_EB_inf=oth, runs=len(meta))
    L += ['', '* **T = infinity does not depend on S, P, B or the age of the information.** EBf(vl, 0, 0.5, infinity) with `oracle_period 64` (`EB_inf_other`)',
          '  against `EB_inf` = EBf(route, 1, 1, infinity): **%d / %d runs identical** (the whole `summary` block, the fields compared above and the counters of' % (oth, len(meta)),
          '  `entry_stats`). Every choice is the entry VL of DeFT-P and every injection draws once, whatever the cost reads; so one anchor row stands for the',
          '  T = infinity member of every sub-family, of `EB_best` and of `EB_best64`.']
    multi = sum(multi_hops(res[names[row]]) for _, _, _, _, _, _, names in meta for row, _ in ANCHOR_ROWS + [OTHER_INF] if res[names[row]])
    L += ['', 'Hops of the anchor runs that offer more than one output (must be 0): %d.' % multi]
    json.dump(out, open(ANCHOR, 'w'), indent=1)
    wmd('anchor.md', L)
    ok = multi == 0 and all(res[x] for x in res)
    if ok:
        shutil.rmtree(X.raw('anchor'))
    return ok          # not identical is a result (the anchor joins Parts C and D), not a failed gate


TUNE_SEEDS, TUNE_SIZES, TUNE_LOADS = EV24.TUNE_SEEDS, EV24.TUNE_SIZES, EV24.TUNE_LOADS
REPRO_ROWS = [('EB_vl_b1', lambda z: ebf_args('vl', 0, 1.0, 0)), ('EB_route_b4', lambda z: ebf_args('route', 0, 4.0, 0)),
              ('DeFT_P', lambda z: X25.row_args(z, 'DeFT_P')), (MAIN, lambda z: X25.row_args(z, MAIN) + ES)]


def repro(nproc):
    """v27 reproduced by this build: the two v27 rows (named as in round 27) with the v28 arguments at P = 0, T = 0, and DeFT_P and the
    main row (whose runs give every tuning score its denominator), on the 40 tuning cells of 2x2 and 4x4."""
    js = []
    for z in TUNE_SIZES:
        for p, m, rate, seed in EV24.tune_cells(z):
            for name, f in REPRO_ROWS:
                js.append(job('repro', z, name, f(z), p, m, rate, seed))
    print('repro jobs: %d' % len(js), flush=True)
    run_jobs(js, X.raw('repro'), nproc=X.width(nproc), timeout=14400)
    tmp = os.path.join(X.RAW, 'repro.csv')
    to_csv(X.raw('repro'), tmp)
    old = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(V27_TUNE))}
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
    L = ['# A2: round 27 reproduced by the build of this round (experiments_v28.py a2_repro)', '',
         'The two rows of `results_v27_early/tune_runs.csv` that the prompt names, run with the arguments of this round at `oracle_pending 0` and',
         '`oracle_bias 0` (given explicitly): `EB_vl_b1` = EBf(vl, 0, 1, 0) and `EB_route_b4` = EBf(route, 0, 4, 0). Also DeFT_P and the main row, whose',
         'runs of that file give every tuning score of this round its denominator and the main row\'s score. All 40 tuning cells of 2x2 and of 4x4 (five',
         'scenarios, loads 0.5, 1.0, 1.4, 2.0 x Lsat, seeds 101 and 102). Compared: every column of that file, as text.', '',
         '| size | row | runs | identical |', '|---|---|---|---|'] + ['| %s | %s | %d | %d |' % (k[0], k[1], v[0], v[1]) for k, v in sorted(by.items())] + [
        '', '**%d / %d runs identical.**' % (same, len(js))] + (['', 'Different: ' + '; '.join(diff[:40])] if diff else [])
    wmd('repro_v27.md', L)
    ok = same == len(js) and len(new) == len(js)
    if ok:
        shutil.rmtree(X.raw('repro'))
        os.remove(tmp)
    return ok


UNIT_ROWS = [('EBf_route_P1_B1_T4', ('route', 1, 1.0, 4, 0)), ('EBf_vl_P1_B1_T4', ('vl', 1, 1.0, 4, 0)),
             ('EBf64_route_P1_B1_T4', ('route', 1, 1.0, 4, 64)), ('EBf64_vl_P1_B1_T4', ('vl', 1, 1.0, 4, 64))]
SWEEP_T = [(0, 0), (1, 0), (1, 2), (1, 8), (1, 32), (1, INF)]         # (P, T) of EBf(route, P, 1, T) in check 4


def units(nproc):
    P = X25.lp()
    out = X.raw('units')
    js, chk, swp = [], [], []
    for z in SIZES:
        p, m = 'uniform', E5.FREE[z]
        r = P[X.lkey(z, p, m)]['eval'][3]
        E5.gen_tables(z, p, [r])
        for name, (S, Pp, B, T, per) in UNIT_ROWS:
            a = job('units', z, name, ebf_args(S, Pp, B, T, per), p, m, r, 101)
            b = job('units', z, name + '_chk', ebf_args(S, Pp, B, T, per) + lb('pending_check', PCHECK), p, m, r, 101)
            js += [a, b]
            chk.append((z, name, per, a[0], b[0]))
    z = '4x4'
    for p in ('uniform', 'hotspot'):
        m = E5.FREE[z]
        r = P[X.lkey(z, p, m)]['eval'][3]
        E5.gen_tables(z, p, [r])
        for Pp, T in SWEEP_T:
            a = job('units', z, fname('route', Pp, 1.0, T), ebf_args('route', Pp, 1.0, T), p, m, r, 101)
            js.append(a)
            swp.append((p, Pp, T, a[0]))
        a = job('units', z, 'DeFT_P', X25.row_args(z, 'DeFT_P'), p, m, r, 101)
        js.append(a)
        swp.append((p, 'DeFT_P', None, a[0]))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    ok = all(res[n] for n, _ in js)
    L = ['# A2: unit checks of the new options (experiments_v28.py a2_units)', '',
         'Seed 101, pipe_all 2, `-traffic_rng 1`, uniform traffic at 1.0 x Lsat of DeFT_P, fault-free.', '',
         '## 1. The pending counters against a scan of the network', '',
         'With `-deft_lb pending_check %d`, at the first three cycles that are multiples of %d, the sum of the pending counters is compared with a scan of the' % (PCHECK, PCHECK),
         'network that does not use them: every head of an inter-chiplet packet that has not moved Up (in an input buffer of a router of its source chiplet or',
         'of the interposer, or on the link into such a router and not yet taken), counted with the length of its packet, per entry VL. *VL mismatches*: the',
         '(cycle, VL) pairs in which the counter of a VL is not the scan of that VL (must be 0).', '',
         '| size | row | cycles | counters (sum over the VLs) | scan | VL mismatches | equal |', '|---|---|---|---|---|---|---|']
    n_eq = 0
    for z, name, per, na, nb in chk:
        l = res[nb]['deft_lb'] if res[nb] else {}
        cyc, cnt, scn, mm = l.get('pending_check_cycles', []), l.get('pending_check_counters', []), l.get('pending_check_scan', []), l.get('pending_check_vl_mismatch', -1)
        eq = len(cyc) == 3 and cnt == scn and mm == 0 and min(cnt or [0]) > 0
        n_eq += eq
        L.append('| %s | `%s` | %s | %s | %s | %s | %s |' % (z, name, cyc, cnt, scn, mm, 'yes' if eq else '**no**'))
    ok = ok and n_eq == len(chk)
    L += ['', '**%d / %d runs equal** (and the counters are positive at every check: the network holds bound packets).' % (n_eq, len(chk)), '',
          '## 2. `pending_check` reads only', '', 'The same runs without the option. Compared: the whole `summary` block and every field of `deft_lb` except those of the check.',
          '', '| size | row | THR without / with | LAT without / with | identical |', '|---|---|---|---|---|']
    n_eq = 0
    for z, name, per, na, nb in chk:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and a['deft_lb'] == {k: v for k, v in b['deft_lb'].items() if not k.startswith('pending_check')}
        n_eq += eq
        L.append('| %s | `%s` | %.6f / %.6f | %.4f / %.4f | %s |' % (z, name, stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1], 'yes' if eq else '**no**'))
    ok = ok and n_eq == len(chk)
    L += ['', '**%d / %d identical.**' % (n_eq, len(chk)), '', '## 3. The snapshots of `oracle_period 64`', '',
          'Samples taken (`oracle_samples`) in the runs with `oracle_period 64`: one at every cycle that is a multiple of 64 after the reset. The pending counters',
          'left at the end of a run (`oracle_pending_left_abs`, the sum of their absolute values) are the packets still on their way; they must be 0 only after a',
          'drain test.', '', '| size | row | samples | pending flits left at the end |', '|---|---|---|---|']
    for z, name, per, na, nb in chk:
        l = res[na]['deft_lb']
        L.append('| %s | `%s` | %s | %s |' % (z, name, l.get('oracle_samples', '-'), l.get('oracle_pending_left_abs')))
        if per and not l.get('oracle_samples'):
            ok = False
    L += ['', '## 4. The anchor at work (description, not a gate)', '',
          '4x4, 1.0 x Lsat, seed 101: EBf(route, P, 1, T) for growing T. *Off*: the share of the measured Up moves on a VL that is not DeFT-P\'s entry VL.', '',
          '| traffic | P | T | off | THR | LAT | P99 |', '|---|---|---|---|---|---|---|']
    for p, Pp, T, na in swp:
        d = res[na]
        s = stats4(d)
        l = d['deft_lb']
        off = ('%.1f %%' % (100.0 * l['entry_up_not_default'] / max(1, l['entry_up_moves']))) if 'entry_up_moves' in l else 'n/a'
        L.append('| %s | %s | %s | %s | %.6f | %.3f | %s |' % (p, Pp, '' if T is None else tstr(T), off, s[0], s[1], s[2]))
    multi = sum(multi_hops(res[n]) for n, _ in js if res[n] and '__DeFT_P-' not in n)
    L += ['', 'Hops of these EB runs that offer more than one output (must be 0): %d.' % multi, '', '**All unit checks pass: %s.**' % ('yes' if ok and multi == 0 else 'NO')]
    ok = ok and multi == 0
    wmd('unit_checks.md', L)
    if ok:
        shutil.rmtree(out)
    return ok


def drain_masks(size):
    """Fault-free, the same VL faulty in every chiplet, and mask 1 of each rate of round 26 (as round 27)."""
    return EV27.drain_masks(size)


def drain_rows(tuned):
    if tuned:
        return [(r, (lambda z, r=r: row_args(z, r))) for r in ('EB_best', 'EB_best64', 'EB_down_t')]
    return [(n, (lambda z, a=a: ebf_args(*a[:4], period=a[4]))) for n, a in UNIT_ROWS] + [('EBd_D4', lambda z: down_args(z, 4))]


def drain_jobs(tuned):
    js = []
    for z in SIZES:
        for row, f in drain_rows(tuned):
            a0 = f(z)
            for m in drain_masks(z):
                a = common_args(1, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(z), lut=X23.lut23(z, m)) + E5.size_args(z) + \
                    a0 + X23.pipe(2) + X24.TRNG + (E10.DRAIN_ALLPAIRS_2X2 if z == '2x2' else E10.DRAIN_ALLPAIRS)
                js.append(('allpairs__%s-p2__%s-%s__s1' % (row, z, m), a))
    return js


def drain_report(res, path):
    """The drain-test CSV of round 19 (experiments_v19.drain_report) with three more columns: the hops that offer more than one output,
    the pending flits left at the end (oracle_pending 1 only) and the result of those two checks."""
    rows, fails = [], 0
    for name in sorted(res):
        d = res[name]
        wl, v, sm, seed = name.split('__')
        if d is None:
            rows.append([wl, v, sm, seed, 'NO_OUTPUT', '', '', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        left = l.get('oracle_pending_left_abs', '')
        ok = (s.get('drain_stop_reason') == 'drain_completed' and s['measured_received_packets'] == s['measured_injected_packets'] and
              l['dead_end_events'] == 0 and multi_hops(d) == 0 and (left == '' or int(left) == 0))
        fails += not ok
        rows.append([wl, v, sm, seed, s.get('drain_stop_reason'), s['measured_injected_packets'], s['measured_received_packets'],
                     l['dead_end_events'], s.get('drain_completed_cycle'), multi_hops(d), left, 'PASS' if ok else 'FAIL'])
    with open(path, 'w', newline='') as f:
        w = csv.writer(f, lineterminator=NL)
        w.writerow(['workload', 'variant', 'size-mask', 'seed', 'stop_reason', 'injected', 'received', 'dead_end_events', 'drain_completed_cycle',
                    'hops_multi', 'pending_left_abs', 'result'])
        w.writerows(rows)
    by = {}
    for r in rows:
        by.setdefault(r[1], [0, 0])
        by[r[1]][0] += 1
        by[r[1]][1] += r[-1] == 'PASS'
    print(f'runs={len(rows)} failures={fails}', {k: f'{p}/{n}' for k, (n, p) in by.items()})
    return fails


def drain(nproc, tuned):
    js = drain_jobs(tuned)
    stage = 'drain_tuned' if tuned else 'drain'
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = run_seg(js, X.raw(stage), X.width(nproc), 14400, seg=96)
    fails = drain_report(res, os.path.join(RES, 'drain_v28_tuned.csv' if tuned else 'drain_v28.csv'))
    print('drain tests: %d, failures %d (a failure includes a hop that offers more than one output, or a pending counter that is not 0 at the end), wall %.0f s' % (
        len(js), fails, time.time() - t), flush=True)
    if not fails:
        shutil.rmtree(X.raw(stage))
    return not fails


# =====================================================================================================================
# Part B: tuning
# =====================================================================================================================
GRID_S = ('vl', 'route')
GRID_P = (0, 1)
GRID_B = (0.5, 1.0, 2.0, 4.0)
GRID_T = (0, 2, 4, 8, 16)
GRID_T64 = (0, 2, 4, 8, 16, 32)
GRID_D = (0, 1, 2, 4, 8, 16)
T_MAX, D_MAX = 128, 64
V27_GRID = EV27.GRID
STATE = os.path.join(X.RAW, 'tune_state.json')
TUNE_CSV = os.path.join(RES, 'tune_runs.csv')
TUNING_RULE = [
    '## The rule (written before any tuning run)', '',
    '* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged: pipe_all 2, DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3',
    '  takes the 4x4 choice); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet); the ladder',
    '  indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds. 80 runs per configuration.',
    '* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where',
    '  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.',
    '  DeFT-P scores 0. DeFT-P and the main row are the runs of `results_v27_early/tune_runs.csv` (reproduced by this build, `repro_v27.md`).',
    '* **B1, the early family** EBf(S, P, B, T), cost(e) = hops(e) + B (occ_S(e) + P pending(e)) + B T [e is not DeFT-P\'s entry VL]: S in {vl, route} x P in',
    '  {0, 1} x B in {0.5, 1, 2, 4} x T in {0, 2, 4, 8, 16} (`oracle_bias` = B x T). The 8 configurations with P = 0 and T = 0 are rows of',
    '  `results_v27_early/tune_runs.csv` (`EB_vl_b<B>`, `EB_route_b<B>`) and are taken from there; so is any configuration with P = 0 and T = 0 that an',
    '  extension adds, if round 27 ran its B.',
    '  * Extension, per size and sub-family (S, P): if its best configuration has the largest T run so far (16 at first), T is doubled (32, 64, 128 at most),',
    '    one value at a time, for every B of the sub-family, until the best T is no longer the largest. If its best B is 0.5 or 4, B / 2 or 2 B is added for',
    '    every T of the sub-family, once per sub-family. The best configuration of a set is the one with the largest score; of two equal scores, the one',
    '    with the larger T.',
    '  * **`EB_best`** per size = the configuration with a finite T that has the largest score over the four sub-families (of two equal scores, the larger T).',
    '    If its score is below 0, the best member of the family is DeFT_P itself (T = infinity): that is said first in the answer to question 2, the finite',
    '    configuration stays `EB_best` so that there is a row to run, and every share is also reported against the better of `EB_best` and DeFT_P.',
    '* **B2, `EB_best64`:** S, P and B of `EB_best` (per size), `oracle_period 64`, T in {0, 2, 4, 8, 16, 32}; if the best T is the largest, it is doubled',
    '  (64, 128 at most), one value at a time. The choice as for `EB_best`.',
    '* **B3, `EB_down_t`:** `EB_down` of round 27 with `lut_bias` D in {0, 1, 2, 4, 8, 16}, everything else the frozen main row; if the best D is 16, 32 is added,',
    '  and 64 if then 32 is the best. A `lut_bias` of infinity is DeFT_P\'s routing (anchor gate). Of two equal scores, the larger D; a best score below 0 is',
    '  treated as for `EB_best`.',
    '* B3 does not depend on B1, so its runs share the batches of B1 (grid and extension steps); B2 starts when B1 is complete.',
    '* Runs: 72 x 80 = 5,760 (B1 grid) + 480 (B2 grid) + 480 (B3 grid) + 40 per configuration and size of an extension. The main row is not tuned; its score',
    '  is reported next to the others (from the runs of round 27).', '']


def fam_names():
    """v27 row name -> v28 configuration name of the members of the family that round 27 ran (P = 0, T = 0)."""
    return {'EB_%s_b%s' % (S, fmt(B)): fname(S, 0, B, 0) for S in GRID_S for B in V27_GRID}


def from_v27(c):
    return c[0] == 'f' and c[2] == 0 and c[4] == 0 and c[3] in V27_GRID


def cname(c):
    return dname(c[1]) if c[0] == 'd' else fname(c[1], c[2], c[3], c[4], 64 if c[0] == 'f64' else 0)


def cargs(size, c):
    return down_args(size, c[1]) if c[0] == 'd' else ebf_args(c[1], c[2], c[3], c[4], 64 if c[0] == 'f64' else 0)


def new_state():
    st = {}
    for z in TUNE_SIZES:
        st[z] = {'f': {'%s|%d' % (S, P): dict(B=list(GRID_B), T=list(GRID_T), bext=False) for S in GRID_S for P in GRID_P},
                 'd': dict(D=list(GRID_D))}
    return st


def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else new_state()


def save_state(st):
    tmp = STATE + '.tmp'
    json.dump(st, open(tmp, 'w'), indent=1)
    os.replace(tmp, STATE)


def members(st, z):
    """[configuration] of the state on size z."""
    out = []
    for k, g in st[z]['f'].items():
        S, P = k.split('|')
        out += [('f', S, int(P), B, T) for B in g['B'] for T in g['T']]
    out += [('d', D) for D in st[z]['d']['D']]
    if 'f64' in st[z]:
        g = st[z]['f64']
        out += [('f64', g['S'], g['P'], g['B'], T) for T in g['T']]
    return out


def member_jobs(st):
    js = []
    for z in TUNE_SIZES:
        cfgs = [c for c in members(st, z) if not from_v27(c)]
        for p, m, rate, seed in EV24.tune_cells(z):
            for c in cfgs:
                js.append(job('tune', z, cname(c), cargs(z, c), p, m, rate, seed))
    return js


def load_tune():
    """{(configuration name, size, pattern, mask, rate, seed): (THR, LAT)}: DeFT_P, the main row and the members of the family that round 27
    ran, from results_v27_early/tune_runs.csv; the runs of this round from the raw folder, or from tune_runs.csv once it is written."""
    R = {}
    ren = fam_names()
    for r in csv.DictReader(open(V27_TUNE)):
        v = r['variant'][:-3]
        name = v if v in ('DeFT_P', MAIN) else ren.get(v)
        if name is None:
            continue
        z, p = r['pattern'].split('-')
        R[(name, z, p, r['mask'], float(r['rate']), int(r['seed']))] = (float(r['accepted']), float(r['latency']))
    raw = X.raw('tune')
    if os.path.isdir(raw):
        for f in glob.glob(os.path.join(raw, '*.json')):
            (v, sp, m, rate, seed), d = MK.parse(f)
            z, p = sp.split('-')
            R[(v[:-3], z, p, m, rate, seed)] = (d['summary']['average_ip_throughput_flits_per_cycle_per_ip'], d['summary']['global_average_delay_cycles'])
    elif os.path.exists(TUNE_CSV):
        for r in csv.DictReader(open(TUNE_CSV)):
            z, p = r['pattern'].split('-')
            R[(r['variant'][:-3], z, p, r['mask'], float(r['rate']), int(r['seed']))] = (float(r['accepted']), float(r['latency']))
    return R


def score_parts(R, name, size):
    """Per tuning cell (scenario, seed): (ln THR ratio, ln LAT1.0 ratio, ln LAT0.5 ratio) against DeFT-P; None if a run is missing."""
    P = X24.lp()
    out = []
    for p, m in X24.scenarios(size):
        lad = P[X.lkey(size, p, m)]['eval']
        for seed in TUNE_SEEDS:
            try:
                a = [R[(name, size, p, m, lad[i], seed)] for i in TUNE_LOADS]
                b = [R[('DeFT_P', size, p, m, lad[i], seed)] for i in TUNE_LOADS]
            except KeyError:
                return None
            out.append(((p, m), math.log(max(x[0] for x in a) / max(x[0] for x in b)), math.log(a[1][1] / b[1][1]), math.log(a[0][1] / b[0][1])))
    return out


def score(R, name, size):
    """(score, mean ln THR ratio, mean ln LAT1.0 ratio, mean ln LAT0.5 ratio), as experiments_v24_eval.score; None if a run is missing."""
    x = score_parts(R, name, size)
    if x is None:
        return None
    n = float(len(x))
    t, l1, l5 = sum(v[1] for v in x) / n, sum(v[2] for v in x) / n, sum(v[3] for v in x) / n
    return t - l1 - l5, t, l1, l5


def score_by_scenario(R, name, size):
    x = score_parts(R, name, size)
    out = {}
    for sc, t, l1, l5 in x:
        out.setdefault(sc, []).append((t - l1 - l5, t, l1, l5))
    return {sc: tuple(sum(v[k] for v in vs) / len(vs) for k in range(4)) for sc, vs in out.items()}


def best_of(R, cfgs, size, tkey):
    """The configuration with the largest score; of two equal scores, the one with the larger tkey(c). Raises if a run is missing."""
    sc = {}
    for c in cfgs:
        s = score(R, cname(c), size)
        if s is None:
            raise RuntimeError('missing tuning runs of %s on %s' % (cname(c), size))
        sc[c] = s
    best = max(cfgs, key=lambda c: (sc[c][0], tkey(c)))
    return best, sc


def ext_step(R, st):
    """One extension step on the state (changed in place). Returns the number of configurations added."""
    added = 0
    for z in TUNE_SIZES:
        if 'f64' not in st[z]:
            for k, g in st[z]['f'].items():
                S, P = k.split('|')
                cfgs = [('f', S, int(P), B, T) for B in g['B'] for T in g['T']]
                best, _ = best_of(R, cfgs, z, lambda c: c[4])
                newT = [max(g['T']) * 2] if best[4] == max(g['T']) and max(g['T']) >= GRID_T[-1] and max(g['T']) * 2 <= T_MAX else []
                newB = []
                if not g['bext'] and best[3] in (GRID_B[0], GRID_B[-1]):
                    newB = [best[3] / 2 if best[3] == GRID_B[0] else best[3] * 2]
                    g['bext'] = True
                Bs, Ts = sorted(g['B'] + newB), sorted(g['T'] + newT)
                added += len(Bs) * len(Ts) - len(g['B']) * len(g['T'])
                g['B'], g['T'] = Bs, Ts
                if newT or newB:
                    print('extension %s %s: best %s; new T %s, new B %s' % (z, k, cname(best), newT, newB), flush=True)
            g = st[z]['d']
            best, _ = best_of(R, [('d', D) for D in g['D']], z, lambda c: c[1])
            if best[1] == max(g['D']) and max(g['D']) >= GRID_D[-1] and max(g['D']) * 2 <= D_MAX:
                g['D'] = sorted(g['D'] + [max(g['D']) * 2])
                added += 1
                print('extension %s EB_down_t: best %s; new D %s' % (z, cname(best), max(g['D'])), flush=True)
        else:
            g = st[z]['f64']
            best, _ = best_of(R, [('f64', g['S'], g['P'], g['B'], T) for T in g['T']], z, lambda c: c[4])
            if best[4] == max(g['T']) and max(g['T']) >= GRID_T64[-1] and max(g['T']) * 2 <= T_MAX:
                g['T'] = sorted(g['T'] + [max(g['T']) * 2])
                added += 1
                print('extension %s EB_best64: best %s; new T %s' % (z, cname(best), max(g['T'])), flush=True)
    return added


def b1_all(st, z):
    return [c for c in members(st, z) if c[0] == 'f']


def tune(nproc):
    st = load_state()
    save_state(st)
    t0 = time.time()
    step = 0
    while True:
        js = member_jobs(st)
        print('%s tuning step %d: %d jobs of the state (finished runs are skipped)' % (time.strftime('%H:%M:%S'), step, len(js)), flush=True)
        res = run_seg(js, X.raw('tune'), X.width(nproc), 14400)
        miss = sum(1 for v in res.values() if v is None)
        if miss:
            print('missing outputs: %d; stop' % miss, flush=True)
            return False
        R = load_tune()
        if ext_step(R, st):
            save_state(st)
            step += 1
            continue
        if any('f64' not in st[z] for z in TUNE_SIZES):
            for z in TUNE_SIZES:
                best, _ = best_of(R, b1_all(st, z), z, lambda c: c[4])
                st[z]['f64'] = dict(S=best[1], P=best[2], B=best[3], T=list(GRID_T64))
                print('B1 complete on %s: EB_best = %s; B2 starts' % (z, cname(best)), flush=True)
            save_state(st)
            step += 1
            continue
        break
    print('tuning runs done in %.0f s' % (time.time() - t0), flush=True)
    return True


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def to_csv(raw_dir, out, expect=None):
    """Per-run CSV: the columns of results_v25_confirm/eval_runs.csv, then the counters of rounds 24, 27 and 28."""
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.json'))):
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up = l['vl_down_packets'], l['vl_up_packets']
        has = any(down)
        row = dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed,
                   accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']), latency=repr(s['global_average_delay_cycles']),
                   p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                   dead_ends=l['dead_end_events'], vl_imbalance=repr(MK.imbalance(m, down, up)) if has else '', vl_source='run' if has else 'none',
                   vl_max_down=max(down) if has else '', vl_max_up=max(up) if has else '')
        for k in EXTRA_FIELDS:
            row[k] = l.get(k, '')
        rows.append(row)
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS + ['vl_max_down', 'vl_max_up'] + list(EXTRA_FIELDS), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('%s: %d rows%s; dead ends %d' % (out, len(rows), '' if expect is None else ' (expected %d)' % expect, sum(int(r['dead_ends']) for r in rows)))
    return len(rows)


def eb_multi(path):
    """Hops of the early rows (names starting with EB) that offer more than one output, in a per-run CSV (must be 0)."""
    n = 0
    for r in csv.DictReader(open(path)):
        if r['variant'].startswith('EB'):
            n += int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0)
    return n


def choose():
    """Scores and choices of Part B -> tuning_v28.md, tuning_choice_v28.json, tune_runs.csv, paper_data/tuning_v28.csv."""
    st = load_state()
    R = load_tune()
    raw = X.raw('tune')
    multi = 0
    if os.path.isdir(raw):
        for f in glob.glob(os.path.join(raw, '*.json')):
            multi += multi_hops(json.load(open(f)))
    out, rows_csv = {}, []
    L = ['# v28 Part B: tuning of the early family, `EB_best64` and `EB_down_t` (experiments_v28.py b_rule, b_tune, b_choose)', ''] + TUNING_RULE
    L += ['## Results', '', 'Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P',
          '(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better). DeFT-P scores 0. *v27*: the runs of `results_v27_early/tune_runs.csv`.', '']
    for z in TUNE_SIZES:
        ms = score(R, MAIN, z)
        fam = b1_all(st, z)
        best, sc = best_of(R, fam, z, lambda c: c[4])
        sub = {}
        for k in st[z]['f']:
            S, P = k.split('|')
            cf = [c for c in fam if c[1] == S and c[2] == int(P)]
            b, _ = best_of(R, cf, z, lambda c: c[4])
            sub[k] = b
        g = st[z]['f64']
        c64 = [('f64', g['S'], g['P'], g['B'], T) for T in g['T']]
        b64, sc64 = best_of(R, c64, z, lambda c: c[4])
        cd = [('d', D) for D in st[z]['d']['D']]
        bd, scd = best_of(R, cd, z, lambda c: c[1])
        out[z] = dict(EB_best=dict(S=best[1], P=best[2], B=best[3], T=best[4], name=cname(best), score=sc[best][0], below_zero=sc[best][0] < 0),
                      EB_best64=dict(S=b64[1], P=b64[2], B=b64[3], T=b64[4], name=cname(b64), score=sc64[b64][0], below_zero=sc64[b64][0] < 0),
                      EB_down_t=dict(D=bd[1], name=cname(bd), score=scd[bd][0], below_zero=scd[bd][0] < 0),
                      sub={k: dict(S=b[1], P=b[2], B=b[3], T=b[4], name=cname(b), score=sc[b][0]) for k, b in sub.items()},
                      main=dict(score=ms[0]), grids=st[z])
        L += ['### %s: B1, the early family' % z, '',
              '| S | P | B | T | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|---|---|---|',
              '| `%s` (frozen, not tuned here) | | | | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | |' % (MAIN, ms[0], pct(ms[1]), pct(ms[2]), pct(ms[3])),
              '| DeFT_P (T = infinity) | | | | 0 | 0 | 0 | 0 | |']
        for c in sorted(fam, key=lambda c: (c[1], c[2], c[3], c[4])):
            s = sc[c]
            note = []
            if c == best:
                note.append('**EB_best**')
            if sub['%s|%d' % (c[1], c[2])] == c:
                note.append('best of (%s, %d)' % (c[1], c[2]))
            if from_v27(c):
                note.append('v27')
            if c[3] not in GRID_B or c[4] not in GRID_T:
                note.append('extension')
            L.append('| %s | %d | %s | %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (c[1], c[2], fmt(c[3]), tstr(c[4]), s[0], pct(s[1]), pct(s[2]), pct(s[3]),
                                                                                       ', '.join(note)))
            rows_csv.append(dict(size=z, part='B1', config=cname(c), S=c[1], P=c[2], B=fmt(c[3]), T=tstr(c[4]), D='', period=0, score='%.6f' % s[0],
                                 thr_pct='%.3f' % pct(s[1]), lat10_pct='%.3f' % pct(s[2]), lat05_pct='%.3f' % pct(s[3]), source='v27' if from_v27(c) else 'v28',
                                 chosen='EB_best' if c == best else ''))
        L += ['', '### %s: B2, `EB_best64` (S %s, P %d, B %s, `oracle_period 64`)' % (z, g['S'], g['P'], fmt(g['B'])), '',
              '| T | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|']
        for c in c64:
            s = sc64[c]
            L.append('| %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (tstr(c[4]), s[0], pct(s[1]), pct(s[2]), pct(s[3]),
                                                                       ', '.join((['**EB_best64**'] if c == b64 else []) + (['extension'] if c[4] not in GRID_T64 else []))))
            rows_csv.append(dict(size=z, part='B2', config=cname(c), S=c[1], P=c[2], B=fmt(c[3]), T=tstr(c[4]), D='', period=64, score='%.6f' % s[0],
                                 thr_pct='%.3f' % pct(s[1]), lat10_pct='%.3f' % pct(s[2]), lat05_pct='%.3f' % pct(s[3]), source='v28', chosen='EB_best64' if c == b64 else ''))
        L += ['', '### %s: B3, `EB_down_t` (`EB_down` with `lut_bias` D)' % z, '', '| D | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|']
        for c in cd:
            s = scd[c]
            L.append('| %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (fmt(c[1]), s[0], pct(s[1]), pct(s[2]), pct(s[3]),
                                                                       ', '.join((['**EB_down_t**'] if c == bd else []) + (['extension'] if c[1] not in GRID_D else []))))
            rows_csv.append(dict(size=z, part='B3', config=cname(c), S='', P='', B='', T='', D=fmt(c[1]), period=0, score='%.6f' % s[0],
                                 thr_pct='%.3f' % pct(s[1]), lat10_pct='%.3f' % pct(s[2]), lat05_pct='%.3f' % pct(s[3]), source='v28', chosen='EB_down_t' if c == bd else ''))
        # the best of each sub-family and the chosen rows, by scenario
        L += ['', '### %s: the best of each sub-family, and the chosen rows, by scenario' % z, '',
              'Score of the scenario (mean over the two seeds) and, in brackets, THR and LAT1.0 against DeFT-P.', '']
        named = [('main row', MAIN)] + [('best of (%s, %s)' % tuple(k.split('|')), cname(b)) for k, b in sorted(sub.items())] + [
            ('`EB_best64`', cname(b64)), ('`EB_down_t`', cname(bd))]
        scen = [(p, m) for p, m in X24.scenarios(z)]
        L += ['| row | configuration | ' + ' | '.join(X25.sname(z, p, m) for p, m in scen) + ' |', '|---|---|' + '---|' * len(scen)]
        for label, n in named:
            bs = score_by_scenario(R, n, z)
            L.append('| %s | `%s` | %s |' % (label, n, ' | '.join('%+.3f (%+.1f / %+.1f)' % (bs[sc][0], pct(bs[sc][1]), pct(bs[sc][2])) for sc in scen)))
        L.append('')
    out['3x3'] = json.loads(json.dumps(out['4x4']))
    json.dump(out, open(CHOICE, 'w'), indent=1)
    L += ['## Chosen configurations', '', '| size | `EB_best` (score) | `EB_best64` (score) | `EB_down_t` (score) | main row (score) |', '|---|---|---|---|---|']
    for z in SIZES:
        c = out[z]
        b, b6, d = c['EB_best'], c['EB_best64'], c['EB_down_t']
        L.append('| %s%s | S %s, P %d, B %s, T %s (%.4f) | T %s (%.4f) | D %s (%.4f) | %.4f |' % (
            z, ' (the 4x4 choice)' if z == '3x3' else '', b['S'], b['P'], fmt(b['B']), tstr(b['T']), b['score'], tstr(b6['T']), b6['score'], fmt(d['D']), d['score'],
            c['main']['score']))
    below = ['%s %s' % (z, r) for z in TUNE_SIZES for r in ('EB_best', 'EB_best64', 'EB_down_t') if out[z][r]['below_zero']]
    L += ['', 'Chosen configurations with a score below 0 (DeFT_P, the T = infinity member, is then the best member of the family): %s.' % (
        ', '.join(below) if below else 'none'), 'Hops of the tuning runs of this round that offer more than one output (must be 0): %d.' % multi,
          'Per-run values: `tune_runs.csv` (the runs of this round) and `results_v27_early/tune_runs.csv` (DeFT_P, the main row, P = 0 and T = 0).']
    wmd('tuning_v28.md', L)
    os.makedirs(os.path.join(RES, 'paper_data'), exist_ok=True)
    with open(os.path.join(RES, 'paper_data', 'tuning_v28.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_csv[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows_csv)
    if os.path.isdir(raw):
        n = to_csv(raw, TUNE_CSV)
        if n == len(glob.glob(os.path.join(raw, '*.json'))) and multi == 0:
            shutil.rmtree(raw)
    return multi == 0


# =====================================================================================================================
# Parts C, D and E
# =====================================================================================================================
def drops():
    return json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []


def rows_c():
    """The five rows of the design; an anchor row joins them if it is not identical to DeFT_P (anchor.json)."""
    return ['DeFT_P', MAIN, 'EB_best', 'EB_best64', 'EB_down_t'] + anchors_extra()


def kept_c(row, seed, d):
    return not ('C_EB_best64_seeds176_180' in d and row == 'EB_best64' and seed >= 176)


def eval_jobs(seeds=SEEDS_C, loads=range(9), d=None):
    d = drops() if d is None else d
    P = X25.lp()
    js = []
    for z in SIZES:
        for row in rows_c():
            a = row_args(z, row)
            for p, m in ff_scenarios(z):
                lad = P[X.lkey(z, p, m)]['eval']
                for i in loads:
                    js += [job('eval', z, row, a, p, m, lad[i], s) for s in seeds if kept_c(row, s, d)]
    return js


def d_masks():
    """The 96 masks of rates 1/16 and 4/16 of round 26."""
    return [e for e in X26.part_b() if e['rate'] in D_RATES]


def d_rows(rate, d):
    if 'D_rate_1_16' in d and rate == '1/16':
        return []
    rows = ['EB_best', 'EB_down_t']
    if rate == '4/16' and 'D_EB_best64' not in d:
        rows.append('EB_best64')
    if 'D_anchors' not in d:
        rows += anchors_extra()
    return rows


def fault_jobs(stage, entries, rows_of, seeds=SEEDS_D, loads=range(4), args=None):
    P = EV26.lpf()
    js = []
    for e in entries:
        z, m = e['size'], e['mask']
        for p in EV26.PATTERNS:
            lad = P[EV26.key(z, p, m)]['eval']
            for row in rows_of(e):
                a = (args or row_args)(z, row)
                for i in loads:
                    js += [job(stage, z, row, a, p, m, lad[i], s) for s in seeds]
    return js


def d_jobs(seeds=SEEDS_D, loads=range(4), entries=None, d=None):
    d = drops() if d is None else d
    return fault_jobs('fault', d_masks() if entries is None else entries, lambda e: d_rows(e['rate'], d), seeds, loads)


def e_rates(d):
    return ('4/16', '8/16') if 'E_rates_1_2' in d else ('1/16', '2/16', '4/16', '8/16')


def e_jobs(seeds=SEEDS_D, loads=range(4), entries=None, d=None):
    d = drops() if d is None else d
    ents = [e for e in X26.part_b() if e['rate'] in e_rates(d)] if entries is None else entries
    return fault_jobs('novlrep', ents, lambda e: ['LB_noVLrep'], seeds, loads)


def ensure_tables():
    P = X25.lp()
    for z in SIZES:
        for p, m in ff_scenarios(z):
            E5.gen_tables(z, p, P[X.lkey(z, p, m)]['eval'])
    P = EV26.lpf()
    for e in X26.part_b():
        for p in EV26.PATTERNS:
            E5.gen_tables(e['size'], p, P[EV26.key(e['size'], p, e['mask'])]['eval'])


DROP_ORDER = ['D_anchors', 'D_EB_best64', 'E_rates_1_2', 'C_EB_best64_seeds176_180', 'D_rate_1_16']
DROP_TEXT = {'D_anchors': 'the anchor rows in Part D', 'D_EB_best64': '`EB_best64` in Part D', 'E_rates_1_2': 'rates 1/16 and 2/16 of Part E',
             'C_EB_best64_seeds176_180': 'seeds 176-180 of `EB_best64` in Part C', 'D_rate_1_16': 'rate 1/16 of Part D'}


def timing(nproc):
    """Timing runs: Part C, the seed-171 runs at the 2nd, 5th and 9th load of every cell; Part D, seed 151 at the 1st and 4th load of masks 1-4
    of every size and rate; Part E the same for LB_noVLrep at the four rates. Runs of the designs (kept), timed one set after the other; no other
    job of the round runs next to a set. The estimate is taken as measured (PREREGISTRATION.md)."""
    ensure_tables()
    nproc = X.width(nproc)
    sets = [('C', eval_jobs(seeds=(171,), loads=(1, 4, 8), d=[]), 'eval'),
            ('D', d_jobs(seeds=(151,), loads=(0, 3), entries=[e for e in d_masks() if e['index'] <= 4], d=[]), 'fault'),
            ('E', e_jobs(seeds=(151,), loads=(0, 3), entries=[e for e in X26.part_b() if e['index'] <= 4], d=[]), 'novlrep')]
    T, miss = {}, {}
    for part, js, stage in sets:
        t = time.time()
        r = run_jobs(js, X.raw(stage), nproc=nproc, timeout=14400)
        T[part] = (time.time() - t, len(js))
        miss[part] = sum(1 for x in r.values() if x is None)
    per = {k: v[0] / v[1] for k, v in T.items()}

    def est(d):
        n = dict(C=len(eval_jobs(d=d)), D=len(d_jobs(d=d)), E=len(e_jobs(d=d)))
        return sum(per[k] * n[k] for k in n) / 3600.0, n
    full, nfull = est([])
    d = []
    for name in DROP_ORDER:
        if name == 'D_anchors' and not anchors_extra():
            continue
        if est(d)[0] <= LIMIT_H:
            break
        d.append(name)
    e2, n2 = est(d)
    json.dump(dict(dropped=d, nproc=nproc, timing={k: dict(seconds=v[0], runs=v[1], per_run=per[k]) for k, v in T.items()},
                   estimate_hours=full, runs=nfull, estimate_hours_after_drops=e2, runs_after_drops=n2), open(DROPS, 'w'), indent=1)
    L = ['# Run-time estimate v28, Parts C, D and E (experiments_v28.py c_timing)', '',
         'Timing runs (runs of the designs, kept; nothing of their results was looked at), %d processes, one set after the other, no other job of this round next' % nproc,
         'to a set; what else ran on the PC at that time is in `DECISIONS.md`. The estimate is taken as measured (`PREREGISTRATION.md`).', '',
         '| part | timing runs | wall | per run | runs of the design | estimate |', '|---|---|---|---|---|---|']
    for k in ('C', 'D', 'E'):
        L.append('| %s | %d (%d missing) | %.0f s | %.2f s | %d | %.1f h |' % (k, T[k][1], miss[k], T[k][0], per[k], nfull[k], per[k] * nfull[k] / 3600.0))
    L += ['', 'Together **%.1f h**. Rule (pre-registered): above %.0f h in total drop, in this order: %s.' % (
        full, LIMIT_H, '; '.join(DROP_TEXT[x] for x in DROP_ORDER if x != 'D_anchors' or anchors_extra())), '',
          '**Dropped: %s.** Runs to do: %d (C), %d (D), %d (E), estimated %.1f h.' % (', '.join(DROP_TEXT[x] for x in d) if d else 'nothing', n2['C'], n2['D'], n2['E'], e2)]
    wmd('runtime_estimate.md', L)
    keep = {j[0] for j in eval_jobs()} | {j[0] for j in d_jobs()} | {j[0] for j in e_jobs()}     # timing runs of dropped cells are removed
    for part, js, stage in sets:
        for j in js:
            if j[0] not in keep:
                for ext in ('.json', '.log'):
                    f = os.path.join(X.raw(stage), j[0] + ext)
                    if os.path.exists(f):
                        os.remove(f)
    return True


def finish(stage, jobs, fn):
    out = os.path.join(RES, fn)
    n = to_csv(X.raw(stage), out, expect=len(jobs))
    dead = sum(int(r['dead_ends']) for r in csv.DictReader(open(out)))
    multi = eb_multi(out)
    print('%s: %d rows of %d; dead-end events %d; hops of EB rows with more than one output %d' % (fn, n, len(jobs), dead, multi), flush=True)
    ok = n == len(jobs) and dead == 0 and multi == 0
    if ok:
        shutil.rmtree(X.raw(stage), ignore_errors=True)
    return ok


def reuse(nproc):
    """Parts D and E: DeFT_P and the main row as round 26 defined them, on masks 1 and 2 of every rate and size, with the new build, against the
    rows of results_v26_faults/fault_rate_runs.csv. Every column of that file is compared as text."""
    ensure_tables()
    ents = [e for e in X26.part_b() if e['index'] <= 2]
    js = fault_jobs('reuse', ents, lambda e: ['DeFT_P', MAIN], args=X26.row_args)
    print('reuse jobs: %d' % len(js), flush=True)
    run_jobs(js, X.raw('reuse'), nproc=X.width(nproc), timeout=14400)
    tmp = os.path.join(X.RAW, 'reuse_check.csv')
    import experiments_v25_eval as EV25
    EV25.to_csv(X.raw('reuse'), tmp)
    old = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(os.path.join(X26.RES, 'fault_rate_runs.csv')))}
    rate_of = {(e['size'], e['mask']): e['rate'] for e in X26.part_b()}
    new = list(csv.DictReader(open(tmp)))
    by, diff = {}, []
    for r in new:
        o = old.get((r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
        k = (r['pattern'].split('-')[0], rate_of[(r['pattern'].split('-')[0], r['mask'])], r['variant'])
        t = by.setdefault(k, [0, 0])
        t[0] += 1
        if o is not None and all(o[c] == r[c] for c in o):
            t[1] += 1
        else:
            diff.append('%s %s %s %s s%s' % (r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
    same = sum(v[1] for v in by.values())
    L = ['# Parts D and E: the reused rows are reproduced by the new build (experiments_v28.py d_reuse)', '',
         'DeFT_P and the main row `CI_heurLA_X_LF`, with the row definitions of round 26 (`experiments_v25.row_args`, no option of this round), on masks 1 and 2 of',
         'every rate (1/16, 2/16, 4/16, 8/16) and size: uniform and hotspot traffic, the four loads, seeds 151 and 152, run with the `bin/noxim` of this round.',
         'Compared with the rows of `results_v26_faults/fault_rate_runs.csv`: every column of that file, as text. DeFT_B, DeFT_Dis and DeFT_Ran are taken',
         'from that file without a run of their own, as in round 27.', '', '| size | rate | row | runs | identical |', '|---|---|---|---|---|'] + [
        '| %s | %s | %s | %d | %d |' % (k[0], k[1], k[2][:-3], v[0], v[1]) for k, v in sorted(by.items())] + [
        '', '**%d / %d runs identical.**' % (same, len(js))] + (['', 'Different: ' + '; '.join(diff[:40])] if diff else [])
    wmd('reuse_check.md', L)
    ok = same == len(js) and len(new) == len(js)
    if ok:
        shutil.rmtree(X.raw('reuse'))
        os.remove(tmp)
    return ok


def run_stage(stage, nproc, extra):
    if stage == 'a2_anchor':
        sys.exit(0 if anchor(nproc) else 1)
    elif stage == 'a2_repro':
        sys.exit(0 if repro(nproc) else 1)
    elif stage == 'a2_units':
        sys.exit(0 if units(nproc) else 1)
    elif stage == 'a2_drain':
        sys.exit(0 if drain(nproc, extra == 'tuned') else 1)
    elif stage == 'b_rule':
        wmd('tuning_v28.md', ['# v28 Part B: tuning of the early family, `EB_best64` and `EB_down_t` (experiments_v28.py b_rule, b_tune, b_choose)', ''] +
            TUNING_RULE + ['## Results', '', 'Not run yet.'])
    elif stage == 'b_tune':
        sys.exit(0 if tune(nproc) else 1)
    elif stage == 'b_choose':
        sys.exit(0 if choose() else 1)
    elif stage == 'c_timing':
        timing(nproc)
    elif stage in ('c_eval', 'd_eval', 'e_eval'):
        ensure_tables()
        js, raw_stage = {'c_eval': (eval_jobs, 'eval'), 'd_eval': (d_jobs, 'fault'), 'e_eval': (e_jobs, 'novlrep')}[stage]
        js = js()
        print('%s jobs: %d' % (stage, len(js)), flush=True)
        t = time.time()
        res = run_seg(js, X.raw(raw_stage), X.width(nproc), 14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'c_check':
        sys.exit(0 if E19.check_raw(X.raw('eval'), eval_jobs(), 'eval') else 1)
    elif stage == 'd_check':
        sys.exit(0 if E19.check_raw(X.raw('fault'), d_jobs(), 'eval') else 1)
    elif stage == 'e_check':
        sys.exit(0 if E19.check_raw(X.raw('novlrep'), e_jobs(), 'eval') else 1)
    elif stage == 'c_csv':
        sys.exit(0 if finish('eval', eval_jobs(), 'eval_runs.csv') else 1)
    elif stage == 'd_csv':
        sys.exit(0 if finish('fault', d_jobs(), 'fault_runs.csv') else 1)
    elif stage == 'e_csv':
        sys.exit(0 if finish('novlrep', e_jobs(), 'novlrep_runs.csv') else 1)
    elif stage == 'd_reuse':
        sys.exit(0 if reuse(nproc) else 1)
    else:
        raise SystemExit(__doc__)
