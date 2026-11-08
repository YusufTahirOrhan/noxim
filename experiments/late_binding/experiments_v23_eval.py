"""v23 Part D stages (results_v23_fidelity/PREREGISTRATION.md), run through experiments_v23.py:
  sat       D1: DeFT-P sweeps per size, v9 scenario and pipe_all (0, 2), seed 101: coarse 0.0005 grid, then the fine 0.0001
            grid where the coarse Lsat <= 0.004, plus L0 at 0.0002
  points    D1: Lsat (3 x L0 rule) and the 9-load ladders -> load_points_v23.json, load_points_v23.md; traffic tables generated
  timing    D2: timing test (seed 1001) and the wall-time estimate -> runtime_estimate.md
  eval      D2: the design, seeds 91-95 (the raw outputs stay under ~/lbraw/v23/eval until csv)
  csv       D2: eval_runs.csv (raw outputs deleted when complete)
  look      D5: lookahead routing with the residual at pipe_all 2, CI_qlLA_G and FULL_qlLA_G, 2x2 and 4x4 uniform, seeds 91-95
  lookcsv   D5: look_runs.csv (with the lookahead counters)
  herd      D4: hysteresis A/B, 4x4 uniform and hotspot, seeds 101-102
  herdcsv   D4: herd_runs.csv
  check     integrity of a raw folder (extra = eval | look | herd)
Variant names carry the pipe depth as a suffix (-p0, -p2) so that the per-run CSV rows are self-describing.
"""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X  # noqa: E402
from runner import common_args, run_jobs  # noqa: E402

RES, RAW, SIZES, NL = X.RES, X.RAW, X.SIZES, X.NL
SEEDS = range(91, 96)
HERD_SEEDS = (101, 102)
PIPES = (0, 2)
LP_FILE = os.path.join(RES, 'load_points_v23.json')
VN_METHODS = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'CI_qlLA_G', 'FULL_qlLA_G']
FF_METHODS = ['MTR', 'RC']
STATIC = ['MTR_static', 'RC_static']


def d2_scenarios(size, method):
    sc = [('uniform', E5.FREE[size]), ('hotspot', E5.FREE[size]), ('chipperm', E5.FREE[size]), ('uniform', E5.NORTH[size])]
    if method.startswith('MTR') or method.startswith('RC'):
        sc = [(p, m) for p, m in sc if int(m, 16) == 0]
    return sc


def lkey(size, p, m, pipe):
    return '%s__%s__%s__p%d' % (size, p, m, pipe)


def args_of(size, v, pipe):
    return list(X.methods(size, pipe_all=pipe)[v]) + X.TRNG


def job(stage, size, name, method, pipe, p, m, rate, seed, extra=()):
    """One run: `name` is the variant of the CSV row (the -p<pipe> suffix is appended), `method` the key of X.methods."""
    rname = '%s__%s-p%d__%s-%s__%s__%.4f__s%d' % (stage, name, pipe, size, p, m, rate, seed)
    args = common_args(seed, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), p, rate), lut=X.lut23(size, m)) + \
        E5.size_args(size) + args_of(size, method, pipe) + list(extra) + E5.SIM
    return rname, args


# ---- D1 ----
def sat_name(size, p, m, r, pipe):
    return 'sat__DeFT_P-p%d__%s-%s__%s__%.4f__s101' % (pipe, size, p, m, r)


def lat_of(size, p, m, r, pipe):
    return json.load(open(os.path.join(X.raw('sat'), sat_name(size, p, m, r, pipe) + '.json')))['summary']['global_average_delay_cycles']


def coarse_lsat(size, p, m, pipe):
    l0 = lat_of(size, p, m, E5.L0_RATE, pipe)
    lsat = None
    for r in E5.SAT_RATES:
        if lat_of(size, p, m, r, pipe) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(size, p, m, pipe):
    lsat, nxt = coarse_lsat(size, p, m, pipe)
    if lsat is None or nxt is None or lsat > E5.LOW_LSAT:
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    js = []
    for s in SIZES:
        for p, m in E5.scenarios(s):
            E5.gen_tables(s, p, E5.SAT_RATES + [E5.L0_RATE])
            for pipe in PIPES:
                js += [job('sat', s, 'DeFT_P', 'DeFT_P', pipe, p, m, r, 101) for r in E5.SAT_RATES + [E5.L0_RATE]]
    print('coarse jobs:', len(js), flush=True)
    run_jobs(js, X.raw('sat'), nproc=nproc, timeout=7200)
    js = []
    for s in SIZES:
        for p, m in E5.scenarios(s):
            rates = set()
            for pipe in PIPES:
                rates |= set(fine_rates(s, p, m, pipe))
            E5.gen_tables(s, p, sorted(rates))
            for pipe in PIPES:
                js += [job('sat', s, 'DeFT_P', 'DeFT_P', pipe, p, m, r, 101) for r in sorted(set(fine_rates(s, p, m, pipe)))]
    print('fine jobs:', len(js), flush=True)
    res = run_jobs(js, X.raw('sat'), nproc=nproc, timeout=7200)
    print('fine runs', len(js), 'missing', sum(1 for v in res.values() if v is None))


def points():
    old = E19.lp()
    res = {}
    L = ['# D1: load points of DeFT-P (experiments_v23_eval.py points)', '',
         'DeFT-P (-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), seed 101. L0 = latency at 0.0002; Lsat = the largest swept rate '
         'before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse Lsat is <= 0.004 and on the 0.0005 grid otherwise; 9 loads at 0.2-2.4 x Lsat.', '',
         '| size | scenario | pipe_all | grid | L0 | Lsat | v19 Lsat (old DeFT) | ratio | lat / L0 at Lsat | ladder |', '|---|---|---|---|---|---|---|---|---|---|']
    for s in SIZES:
        for p, m in E5.scenarios(s):
            for pipe in PIPES:
                l0 = lat_of(s, p, m, E5.L0_RATE, pipe)
                fr = fine_rates(s, p, m, pipe)
                grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
                lsat = None
                for r in rates:
                    if lat_of(s, p, m, r, pipe) > 3 * l0:
                        break
                    lsat = r
                ev = []
                for mult in X.MULTS9:
                    x = round(max(grid, round(mult * lsat / grid) * grid), 4)
                    if ev and x <= ev[-1]:
                        x = round(ev[-1] + grid, 4)
                    ev.append(x)
                res[lkey(s, p, m, pipe)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0, 'pipe_all': pipe}
                ol = old[E5.key(s, p, m)]['lsat']
                L.append('| %s | %s %s | %d | %s | %.1f | %s | %s | %.3f | %.2f | %s |' % (s, p, m, pipe, grid, l0, lsat, ol, lsat / ol, lat_of(s, p, m, lsat, pipe) / l0, ev))
                E5.gen_tables(s, p, ev)
    json.dump(res, open(LP_FILE, 'w'), indent=1)
    open(os.path.join(RES, 'load_points_v23.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(X.raw('sat'))


def lp():
    return json.load(open(LP_FILE))


# ---- D2 ----
def eval_jobs(seeds=SEEDS):
    P = lp()
    js = []
    for s in SIZES:
        for pipe in PIPES:
            for v in VN_METHODS + FF_METHODS + (STATIC + ['DeFT_old'] if pipe == 0 else []):
                for p, m in d2_scenarios(s, v):
                    for r in P[lkey(s, p, m, pipe)]['eval']:
                        js += [job('eval', s, v, v, pipe, p, m, r, seed) for seed in seeds]
    return js


def timing(nproc):
    P = lp()
    js = []
    for s in SIZES:
        for pipe in PIPES:
            for v in VN_METHODS + FF_METHODS:
                for p, m in d2_scenarios(s, v):
                    for i in (1, 4, 8):
                        js.append(job('timing', s, v, v, pipe, p, m, P[lkey(s, p, m, pipe)]['eval'][i], 1001))
    t = time.time()
    res = run_jobs(js, X.raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v23 D2', '', 'Timing test: %d runs (seed 1001; every method x size x scenario x pipe depth at the 2nd, 5th and 9th load), %d processes: %.0f s wall; %d missing.' %
         (len(js), nproc, el, sum(1 for x in res.values() if x is None)), '', 'D2: %d runs, estimated **%.1f h**. Rule: above 20 h, pipe_all = 2 is dropped for DeFT-Dis.' % (n, est)]
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(X.raw('timing'))


# ---- D5 ----
def look_jobs(seeds=SEEDS):
    P = lp()
    js = []
    for s in ('2x2', '4x4'):
        for v in ('CI_qlLA_G', 'FULL_qlLA_G'):
            extra = X.LOOK + ['-deft_lb', 'decision_delay', str(X.residual(v, 2))]
            for r in P[lkey(s, 'uniform', E5.FREE[s], 2)]['eval']:
                js += [job('look', s, v + '_look', v, 2, 'uniform', E5.FREE[s], r, seed, extra) for seed in seeds]
    return js


# ---- D4 ----
def herd_jobs():
    P = lp()
    js = []
    for v in ('CI_qlLA_G', 'FULL_qlLA_G'):
        for p in ('uniform', 'hotspot'):
            for cfg, pipe, extra in (('dd0', 0, []), ('look', 2, X.LOOK + ['-deft_lb', 'decision_delay', str(X.residual(v, 2))])):
                lad = P[lkey('4x4', p, E5.FREE['4x4'], pipe)]['eval'][3:]
                for D in (0, 1, 2, 4):
                    for r in lad:
                        js += [job('herd', '4x4', '%s_h%d_%s' % (v, D, cfg), v, pipe, p, E5.FREE['4x4'], r, seed,
                                   extra + (['-deft_lb', 'hysteresis', str(D)] if D else [])) for seed in HERD_SEEDS]
    return js


def run_stage(stage, nproc, extra):
    if stage == 'sat':
        sat(nproc)
    elif stage == 'points':
        points()
    elif stage == 'timing':
        timing(nproc)
    elif stage in ('eval', 'look', 'herd'):
        js = {'eval': eval_jobs, 'look': look_jobs, 'herd': herd_jobs}[stage]()
        print(stage, 'jobs:', len(js), flush=True)
        res = run_jobs(js, X.raw(stage), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'csv':
        n = X.to_csv('eval', 'eval_runs.csv')
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('eval'))
    elif stage == 'lookcsv':
        n = X.to_csv('look', 'look_runs.csv', extra_fields=('lookahead_stored', 'lookahead_used', 'lookahead_mismatch', 'decision_delay'))
        if n == len(look_jobs()):
            shutil.rmtree(X.raw('look'))
    elif stage == 'herdcsv':
        n = X.to_csv('herd', 'herd_runs.csv', extra_fields=('hysteresis', 'lookahead_mismatch', 'lookahead_used'))
        if n == len(herd_jobs()):
            shutil.rmtree(X.raw('herd'))
    elif stage == 'check':
        kind = extra
        jobs = {'eval': eval_jobs, 'look': look_jobs, 'herd': herd_jobs}[kind]()
        sys.exit(0 if E19.check_raw(X.raw(kind), jobs, 'eval') else 1)
    else:
        raise SystemExit(__doc__)
