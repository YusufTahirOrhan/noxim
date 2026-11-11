"""v25 Part B stages (results_v25_confirm/PREREGISTRATION.md), run through experiments_v25.py:
  timing    B1: the seed-121 runs at the 2nd, 5th and 9th load of every cell (runs of the design, kept), timed -> runtime_estimate.md, drops.json
  eval      B1: the design, seeds 121-130 (raw outputs under ~/lbraw/v25/eval until csv)
  check     integrity of the raw evaluation folder
  csv       eval_runs.csv (raw outputs deleted when complete)
  sanity    report/sanity.md (observation-only options, the largest VL flit rate, hops per packet)
Row names carry the pipe depth as a suffix (-p2); the mechanism of a frozen row is part of its name (_LF, _DLY).
to_csv() is shared with Parts C and E.
"""
import csv
import glob
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X  # noqa: E402
import make_eval_csv as MK  # noqa: E402
from runner import run_jobs  # noqa: E402

RES, SIZES, NL = X.RES, X.SIZES, X.NL
SEEDS = range(121, 131)
DROPS = os.path.join(RES, 'drops.json')
LIMIT_H = 36.0
ROWS = list(X.FROZEN) + X.REFS_ALL + X.REFS_FF + X.REFS_FAULT       # 4 + 2 + 3 + 2
EXTRA_FIELDS = EV24.EXTRA_FIELDS


def row_scenarios(size, row):
    sc = X.scenarios(size)
    if row in X.REFS_FF:
        return [(p, m) for p, m in sc if not X.faulty(m)]
    if row in X.REFS_FAULT:
        return [(p, m) for p, m in sc if X.faulty(m)]
    return sc


def dropped(row, seed):
    """The pre-registered time rule: above 36 h drop XY_SP, then seeds 126-130 of CI_qlLA_X_LF."""
    d = json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []
    if 'xy_sp' in d and row == 'XY_SP':
        return True
    return 'ql_seeds' in d and row == 'CI_qlLA_X_LF' and seed >= 126


def eval_jobs(seeds=SEEDS, loads=range(9), with_dropped=False):
    P = X.lp()
    js = []
    for size in SIZES:
        for row in ROWS:
            a = X.row_args(size, row)
            for p, m in row_scenarios(size, row):
                lad = P[X.lkey(size, p, m)]['eval']
                for i in loads:
                    js += [X.job('eval', size, row, a, 2, p, m, lad[i], seed) for seed in seeds if with_dropped or not dropped(row, seed)]
    return js


def ensure_tables():
    P = X.lp()
    for size in SIZES:
        for p, m in X.scenarios(size):
            E5.gen_tables(size, p, P[X.lkey(size, p, m)]['eval'])


def timing(nproc):
    """The seed-121 runs at the 2nd, 5th and 9th load of every cell: part of the design (kept), timed for the estimate."""
    ensure_tables()
    js = eval_jobs(seeds=(121,), loads=(1, 4, 8), with_dropped=True)
    full = eval_jobs(with_dropped=True)
    t = time.time()
    res = run_jobs(js, X.raw('eval'), nproc=nproc, timeout=14400)
    el = time.time() - t
    per = el / len(js)
    est = per * len(full) / 3600
    xy = [j for j in full if '__XY_SP-p2__' in j[0]]
    ql = [j for j in full if '__CI_qlLA_X_LF-p2__' in j[0] and int(j[0].rsplit('__s', 1)[1]) >= 126]
    drops, n, e2 = [], len(full), est
    if e2 > LIMIT_H:
        drops.append('xy_sp')
        n -= len(xy)
        e2 = per * n / 3600
    if e2 > LIMIT_H:
        drops.append('ql_seeds')
        n -= len(ql)
        e2 = per * n / 3600
    json.dump(dict(dropped=drops, nproc=nproc, timing_runs=len(js), timing_seconds=el, estimate_hours_full=est, estimate_hours_after_drops=e2, runs_full=len(full), runs_after_drops=n),
              open(DROPS, 'w'), indent=1)
    L = ['# Run-time estimate v25 Part B (experiments_v25.py timing)', '',
         'Timing runs: the %d runs of seed 121 at the 2nd, 5th and 9th load (0.5, 1.2 and 2.4 x Lsat) of every (row, size, scenario) cell. They are runs of the design and are kept;' % len(js),
         'nothing of their results was looked at. %d processes (two cores are left to Part F): %.0f s wall; %d missing.' % (nproc, el, sum(1 for x in res.values() if x is None)), '',
         'Full design: %d runs, estimated **%.1f h** with %d processes.' % (len(full), est, nproc), '',
         'Rule (pre-registered): above %.0f h drop, in this order, XY_SP (%d runs), then seeds 126-130 of `CI_qlLA_X_LF` (%d runs).' % (LIMIT_H, len(xy), len(ql)),
         '', '**Dropped: %s.** Runs to do: %d, estimated %.1f h.' % (', '.join(drops) if drops else 'nothing', n, e2)]
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    keep = {j[0] for j in eval_jobs()}          # timing runs of dropped cells are removed: the raw folder holds the design as run
    for j in js:
        if j[0] not in keep:
            for ext in ('.json', '.log'):
                f = os.path.join(X.raw('eval'), j[0] + ext)
                if os.path.exists(f):
                    os.remove(f)


# ---- per-run CSV (Parts B, C and E) ----
def to_csv(raw_dir, out, expect=None):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.json'))):
        if f.endswith('.vc.json'):
            continue
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


# ---- sanity ----
def sanity(nproc):
    P = X.lp()
    out = X.raw('sanity')
    js, meta = [], []
    twins = [('DeFT_P', 'count_vl', 'uniform', False), ('XY_SP', 'count_vl', 'uniform', False), ('CI_heurLA_X_LF', 'hop_stats', 'uniform', False),
             ('CI_heurLA_O_LF', 'hop_stats', 'uniform', False), ('DeFT_Dis', 'hop_stats', 'uniform', True)]
    for size in SIZES:
        for row, opt, p, flt in twins:
            if dropped(row, 121):
                continue
            m = E5.NORTH[size] if flt else E5.FREE[size]
            r = P[X.lkey(size, p, m)]['eval'][3]
            a = X.row_args(size, row)
            k = [i for i in range(len(a) - 2) if a[i] == '-deft_lb' and a[i + 1] == opt][0]
            n, args = X.job('sanity', size, row + '_no' + opt, a[:k] + a[k + 3:], 2, p, m, r, 121)
            js.append((n, args))
            meta.append((size, row, opt, p, m, r, n))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    E = {}
    for r in csv.DictReader(open(os.path.join(RES, 'eval_runs.csv'))):
        E[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = r
    L = ['# Sanity checks v25 Part B (experiments_v25.py sanity)', '', '## Observation-only options', '',
         'DeFT_P, DeFT_B and XY_SP run with `-deft_lb count_vl 1` (VL counts for plain routing) and every DEFT_LB row with `-deft_lb hop_stats 1`. The same run without the',
         'option (seed 121, 1.0 x Lsat) must give the same accepted throughput, latency, p99 and received packets as the evaluation run.', '',
         '| size | row | option removed | scenario | result |', '|---|---|---|---|---|']
    allsame = True
    for size, row, opt, p, m, r, n in meta:
        d = res[n]
        e = E[(row + '-p2', size + '-' + p, m, r, 121)]
        same = bool(d) and (repr(d['summary']['average_ip_throughput_flits_per_cycle_per_ip']) == e['accepted'] and repr(d['summary']['global_average_delay_cycles']) == e['latency'] and
                            repr(d['deft_lb']['delay_p99']) == e['p99'] and str(d['summary']['total_received_packets']) == e['received'])
        allsame = allsame and same
        L.append('| %s | %s | %s | %s | %s |' % (size, row, opt, X.sname(size, p, m), 'identical' if same else '**different**'))
    L += ['', '**All identical: %s.**' % ('yes' if allsame else 'NO'), '', '## Hops per packet (uniform fault-free, seed 121, 1.0 x Lsat, pipe_all 2)', '',
          'Head-flit forwards counted by `hop_stats` in the measured window, divided by the packets delivered in the window; and the share of hops that offer more than one output.', '',
          '| size | CI_heurLA_X_LF | CI_heurLA_O_LF | CI_heurLA_X_LF: decision hops (chiplet / interposer) | CI_heurLA_O_LF |', '|---|---|---|---|---|']

    def hp(e):
        return (int(e['hops_chip']) + int(e['hops_ipos'])) / float(e['packets_measured'])

    def multi(e):
        return '%.1f %% / %.1f %%' % (100.0 * int(e['hops_chip_multi']) / int(e['hops_chip']), 100.0 * int(e['hops_ipos_multi']) / int(e['hops_ipos']))
    for size in SIZES:
        m = E5.FREE[size]
        r = P[X.lkey(size, 'uniform', m)]['eval'][3]
        ex = E[('CI_heurLA_X_LF-p2', size + '-uniform', m, r, 121)]
        eo = E[('CI_heurLA_O_LF-p2', size + '-uniform', m, r, 121)]
        L.append('| %s | %.2f | %.2f | %s | %s |' % (size, hp(ex), hp(eo), multi(ex), multi(eo)))
    L += ['', '## Largest flit rate of a vertical link', '',
          'Per run, the largest number of packets any Down VL and any Up VL carried (head flits forwarded over the whole 10,000 simulated cycles), times 8 flits, per cycle. A link',
          'carries one flit per two cycles, so the value must not exceed 0.5.', '', '| file | runs with VL counts | largest Down VL rate (run) | largest Up VL rate (run) | above 0.5 |', '|---|---|---|---|---|']
    worst = 0.0
    for fn in ('eval_runs.csv', 'fault_runs.csv', 'pipe0_runs.csv'):
        f = os.path.join(RES, fn)
        if not os.path.exists(f):
            continue
        rows = [r for r in csv.DictReader(open(f)) if r['vl_max_down'] != '']
        bd = max(rows, key=lambda r: int(r['vl_max_down']))
        bu = max(rows, key=lambda r: int(r['vl_max_up']))
        rd, ru = int(bd['vl_max_down']) * 8 / 10000.0, int(bu['vl_max_up']) * 8 / 10000.0
        worst = max(worst, rd, ru)
        L.append('| %s | %d | %.4f (%s, %s, rate %s, seed %s) | %.4f (%s, %s, rate %s, seed %s) | %d |' % (
            fn, len(rows), rd, bd['variant'], bd['pattern'], bd['rate'], bd['seed'], ru, bu['variant'], bu['pattern'], bu['rate'], bu['seed'],
            sum(1 for r in rows if int(r['vl_max_down']) * 8 / 10000.0 > 0.5 or int(r['vl_max_up']) * 8 / 10000.0 > 0.5)))
    L += ['', '**Largest VL flit rate: %.4f flits/cycle (%s 0.5).**' % (worst, 'at most' if worst <= 0.5 else 'ABOVE')]
    os.makedirs(os.path.join(RES, 'report'), exist_ok=True)
    open(os.path.join(RES, 'report', 'sanity.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


def run_stage(stage, nproc, extra):
    if stage == 'timing':
        timing(nproc)
    elif stage == 'eval':
        ensure_tables()
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, X.raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'check':
        sys.exit(0 if E19.check_raw(X.raw('eval'), eval_jobs(), 'eval') else 1)
    elif stage == 'csv':
        n = to_csv(X.raw('eval'), os.path.join(RES, 'eval_runs.csv'), expect=len(eval_jobs()))
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('eval'))
    elif stage == 'sanity':
        sanity(nproc)
    else:
        raise SystemExit(__doc__)
