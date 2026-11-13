"""v26 Part B (results_v26_faults/PREREGISTRATION.md): performance under random VL faults at four rates. Run through experiments_v26.py:
  b_drain   all-pairs drain test of every row of the design on every mask (seed 1) -> drain_v26.csv
  b_sat     DeFT-P sweeps per (mask, traffic) (the D1 rule as run in Part C of round 25: seed 101, pipe_all 2, upwards in batches until the
            first rate above 3 x L0)
  b_points  Lsat and the four loads per (mask, traffic) -> load_points_v26.json, load_points_v26.md
  b_timing  the timing runs (seed 151, 1st and 4th load, masks 1-4 of every (size, rate)): runs of the design, kept -> runtime_estimate.md,
            drops.json
  b_eval    the design: 192 masks x 2 traffic patterns x 6 rows x 4 loads x seeds 151, 152 (raw outputs under ~/lbraw/v26/beval until b_csv)
  b_check   integrity of the raw folder
  b_csv     fault_rate_runs.csv (raw outputs deleted when complete)
Masks: masks_v26.json (experiments_v26.py masks); LUTs luts/v23, one per mask (experiments_v26.py luts).
"""
import json
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
import experiments_v26 as X  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL = X.RES, X.SIZES, X.NL
PATTERNS = ('uniform', 'hotspot')
SEEDS = (151, 152)
MULTS = (0.5, 1.0, 1.4, 2.0)
ROWS = X.ROWS
LP_FILE = os.path.join(RES, 'load_points_v26.json')
DROPS = os.path.join(RES, 'drops.json')
LIMIT_H = 40.0
BATCH = 8


def run_seg(js, out, nproc, timeout, seg=384):
    """run_jobs in segments, each with the number of processes the width file gives at that moment (experiments_v26.width)."""
    res = {}
    for k in range(0, len(js), seg):
        w = X.width(nproc)
        print("%s runs %d-%d of %d with %d processes" % (time.strftime("%H:%M:%S"), k + 1, min(k + seg, len(js)), len(js), w), flush=True)
        res.update(run_jobs(js[k:k + seg], out, nproc=w, timeout=timeout))
    return res


def rtag(e):
    return 'r%s' % e['rate'].split('/')[0]


# ---- drain tests ----
def drain_jobs():
    js = []
    for e in X.part_b():
        z, m = e['size'], e['mask']
        for row in ROWS:
            a = common_args(1, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(z), lut=X23.lut23(z, m)) + E5.size_args(z) + \
                X.row_args(z, row) + X23.pipe(2) + X24.TRNG + (E10.DRAIN_ALLPAIRS_2X2 if z == '2x2' else E10.DRAIN_ALLPAIRS)
            js.append(('allpairs__%s-p2__%s-%s-%02d-%s__s1' % (row, z, rtag(e), e['index'], m), a))
    return js


def drain(nproc):
    js = drain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = run_seg(js, X.raw('bdrain'), nproc, 14400, seg=96)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_v26.csv'))
    print('drain tests: %d, failures %d, wall %.0f s' % (len(js), fails, time.time() - t), flush=True)
    if not fails:
        shutil.rmtree(X.raw('bdrain'))
    return not fails


# ---- ladders (the D1 rule, run upwards) ----
def key(z, p, m):
    return '%s__%s__%s' % (z, p, m)


def cells():
    """[(entry, pattern)] of the design, in the order of masks_v26.json."""
    return [(e, p) for e in X.part_b() for p in PATTERNS]


def sat_name(z, p, m, r):
    return 'bsat__DeFT_P-p2__%s-%s__%s__%.4f__s101' % (z, p, m, r)


def sat_job(z, p, m, r):
    return X.job('bsat', z, 'DeFT_P', X23.methods(z)['DeFT_P'], 2, p, m, r, 101)


def lat_of(z, p, m, r):
    f = os.path.join(X.raw('bsat'), sat_name(z, p, m, r) + '.json')
    return json.load(open(f))['summary']['global_average_delay_cycles'] if os.path.exists(f) else None


def coarse(z, p, m):
    """(Lsat, the first swept rate above 3 x L0 or None, complete): the coarse sweep read as far as it has been run."""
    l0 = lat_of(z, p, m, E5.L0_RATE)
    lsat = None
    for r in E5.SAT_RATES:
        x = lat_of(z, p, m, r)
        if x is None:
            return lsat, None, False
        if x > 3 * l0:
            return lsat, r, True
        lsat = r
    return lsat, None, True


def fine_rates(z, p, m):
    lsat, nxt, done = coarse(z, p, m)
    if nxt is None or (lsat is not None and lsat > E5.LOW_LSAT):
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    cs = [(e['size'], p, e['mask']) for e, p in cells()]
    t = time.time()
    for z in SIZES:
        for p in PATTERNS:
            E5.gen_tables(z, p, E5.SAT_RATES + [E5.L0_RATE])
    run_seg([sat_job(z, p, m, E5.L0_RATE) for z, p, m in cs], X.raw('bsat'), nproc, 7200)
    for b in range(0, len(E5.SAT_RATES), BATCH):
        todo = [c for c in cs if not coarse(*c)[2]]
        if not todo:
            break
        js = [sat_job(z, p, m, r) for z, p, m in todo for r in E5.SAT_RATES[b:b + BATCH]]
        print('%s coarse batch %d: %d ladders, %d jobs' % (time.strftime('%H:%M:%S'), b // BATCH, len(todo), len(js)), flush=True)
        run_seg(js, X.raw('bsat'), nproc, 7200)
    js = []
    for z, p, m in cs:
        fr = fine_rates(z, p, m)
        E5.gen_tables(z, p, fr)
        js += [sat_job(z, p, m, r) for r in fr]
    print('%s fine jobs: %d' % (time.strftime('%H:%M:%S'), len(js)), flush=True)
    res = run_seg(js, X.raw('bsat'), nproc, 7200)
    print('fine runs %d, missing %d; wall of this call %.0f s' % (len(js), sum(1 for v in res.values() if v is None), time.time() - t), flush=True)


def points():
    import glob
    res = {}
    L = ['# v26 Part B: load points per mask and traffic pattern (experiments_v26.py b_sat, b_points)', '',
         'DeFT-P (-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), seed 101, pipe_all 2, the v23-style LUT of the mask.',
         'D1 rule as in Part C of round 25: L0 = latency at 0.0002; Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the',
         'coarse (0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid otherwise. The coarse sweep was run upwards in batches of %d rates and stopped after the first rate' % BATCH,
         'above 3 x L0. Loads: 0.5, 1.0, 1.4, 2.0 x Lsat, rounded to the grid.', '',
         '| size | rate | # | mask | traffic | grid | L0 | Lsat | lat / L0 at Lsat | loads | Lsat < 0.001 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    low = 0
    for e, p in cells():
        z, m = e['size'], e['mask']
        l0 = lat_of(z, p, m, E5.L0_RATE)
        fr = fine_rates(z, p, m)
        grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
        lsat = None
        for r in rates:
            x = lat_of(z, p, m, r)
            if x is None or x > 3 * l0:
                break
            lsat = r
        if lsat is None:
            raise SystemExit('no Lsat for %s %s %s' % (z, p, m))
        ev = []
        for mult in MULTS:
            x = round(max(grid, round(mult * lsat / grid) * grid), 4)
            if ev and x <= ev[-1]:
                x = round(ev[-1] + grid, 4)
            ev.append(x)
        res[key(z, p, m)] = {'size': z, 'rate': e['rate'], 'index': e['index'], 'mask': m, 'pattern': p, 'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0}
        low += lsat < 0.001
        L.append('| %s | %s | %d | %s | %s | %s | %.1f | %s | %.2f | %s | %s |' % (z, e['rate'], e['index'], m, p, grid, l0, lsat, lat_of(z, p, m, lsat) / l0, ev, 'yes' if lsat < 0.001 else ''))
        E5.gen_tables(z, p, ev)
    files = glob.glob(os.path.join(X.raw('bsat'), '*.json'))
    dead = sum(json.load(open(f))['deft_lb']['dead_end_events'] for f in files)
    L += ['', '%d ladders from %d sweep runs; dead-end events in the sweep runs: %d. Ladders with Lsat below 0.001 (L0 is measured at 0.0002, more than a fifth of Lsat): %d.' % (
        len(res), len(files), dead, low), '',
          '## Lsat by size, rate and traffic (mean and range over the 16 masks; fault-free Lsat of round 25 by the same rule)', '',
          '| size | traffic | fault-free | 1/16 | 2/16 | 4/16 | 8/16 |', '|---|---|---|---|---|---|---|']
    ff = json.load(open(os.path.join(HERE, 'results_v25_confirm', 'load_points_v25.json')))
    for z in SIZES:
        for p in PATTERNS:
            c = []
            for r in X.RATES:
                v = [x['lsat'] for x in res.values() if x['size'] == z and x['pattern'] == p and x['rate'] == X.rate_name(r)]
                c.append('%.4f (%.4f-%.4f)' % (sum(v) / len(v), min(v), max(v)))
            L.append('| %s | %s | %s | %s |' % (z, p, ff[X24.lkey(z, p, E5.FREE[z])]['lsat'], ' | '.join(c)))
    json.dump(res, open(LP_FILE, 'w'), indent=1)
    open(os.path.join(RES, 'load_points_v26.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[-12:]))
    if dead:
        raise SystemExit('dead-end events in the sweep runs: %d' % dead)
    shutil.rmtree(X.raw('bsat'))


def lpf():
    return json.load(open(LP_FILE))


# ---- the design ----
def dropped():
    return json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []


def kept(e, drops=None):
    """The pre-registered time rule: above 40 h drop rate 8/16 on 4x4, then masks 13-16 of every remaining (size, rate)."""
    d = dropped() if drops is None else drops
    if 'rate8_4x4' in d and e['size'] == '4x4' and e['rate'] == '8/16':
        return False
    return not ('masks13_16' in d and e['index'] >= 13)


def eval_jobs(seeds=SEEDS, loads=range(4), entries=None, drops=None):
    P = lpf()
    js = []
    for e in (X.part_b() if entries is None else entries):
        if not kept(e, drops):
            continue
        z, m = e['size'], e['mask']
        for p in PATTERNS:
            lad = P[key(z, p, m)]['eval']
            for row in ROWS:
                a = X.row_args(z, row)
                for i in loads:
                    js += [X.job('beval', z, row, a, 2, p, m, lad[i], seed) for seed in seeds]
    return js


def ensure_tables():
    P = lpf()
    for e, p in cells():
        E5.gen_tables(e['size'], p, P[key(e['size'], p, e['mask'])]['eval'])


def timing(nproc):
    """Seed 151, the 1st and 4th load, masks 1-4 of every (size, rate), every row, both traffic patterns: runs of the design (kept), timed."""
    ensure_tables()
    js = eval_jobs(seeds=(151,), loads=(0, 3), entries=[e for e in X.part_b() if e['index'] <= 4], drops=[])
    full = eval_jobs(drops=[])
    nproc = X.width(nproc)
    t = time.time()
    res = run_jobs(js, X.raw('beval'), nproc=nproc, timeout=14400)
    el = time.time() - t
    per = el / len(js)
    est = per * len(full) / 3600
    drops, n, e2 = [], len(full), est
    if e2 > LIMIT_H:
        drops.append('rate8_4x4')
        n = len(eval_jobs(drops=drops))
        e2 = per * n / 3600
    if e2 > LIMIT_H:
        drops.append('masks13_16')
        n = len(eval_jobs(drops=drops))
        e2 = per * n / 3600
    json.dump(dict(dropped=drops, nproc=nproc, timing_runs=len(js), timing_seconds=el, estimate_hours_full=est, estimate_hours_after_drops=e2, runs_full=len(full), runs_after_drops=n),
              open(DROPS, 'w'), indent=1)
    L = ['# Run-time estimate v26 Part B (experiments_v26.py b_timing)', '',
         'Timing runs: the %d runs of seed 151 at the 1st and 4th load (0.5 and 2.0 x Lsat) of masks 1 to 4 of every (size, rate), every row and both traffic patterns.' % len(js),
         'They are runs of the design and are kept; nothing of their results was looked at. %d processes: %.0f s wall; %d missing.' % (nproc, el, sum(1 for x in res.values() if x is None)), '',
         'Full design: %d runs, estimated **%.1f h** with %d processes (the timing runs have the mix of sizes, rates, rows and traffic of the design; their loads are the lowest' % (len(full), est, nproc),
         'and the highest of the four).', '',
         'Rule (pre-registered): above %.0f h drop, in this order, rate 8/16 on 4x4, then masks 13 to 16 of every remaining (size, rate).' % LIMIT_H,
         '', '**Dropped: %s.** Runs to do: %d, estimated %.1f h.' % (', '.join(drops) if drops else 'nothing', n, e2)]
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    keep = {j[0] for j in eval_jobs()}          # timing runs of dropped cells are removed: the raw folder holds the design as run
    for j in js:
        if j[0] not in keep:
            for ext in ('.json', '.log'):
                f = os.path.join(X.raw('beval'), j[0] + ext)
                if os.path.exists(f):
                    os.remove(f)


def run_stage(stage, nproc, extra):
    if stage == 'b_drain':
        sys.exit(0 if drain(nproc) else 1)
    elif stage == 'b_sat':
        sat(nproc)
    elif stage == 'b_points':
        points()
    elif stage == 'b_timing':
        timing(nproc)
    elif stage == 'b_eval':
        ensure_tables()
        js = eval_jobs()
        print('evaluation jobs: %d' % len(js), flush=True)
        t = time.time()
        res = run_seg(js, X.raw('beval'), nproc, 14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'b_check':
        sys.exit(0 if E19.check_raw(X.raw('beval'), eval_jobs(), 'eval') else 1)
    elif stage == 'b_csv':
        import csv
        import experiments_v25_eval as EV
        out = os.path.join(RES, 'fault_rate_runs.csv')
        n = EV.to_csv(X.raw('beval'), out, expect=len(eval_jobs()))
        dead = sum(int(r['dead_ends']) for r in csv.DictReader(open(out)))
        if n == len(eval_jobs()) and dead == 0:
            shutil.rmtree(X.raw('beval'))
        sys.exit(0 if n == len(eval_jobs()) and dead == 0 else 1)
    else:
        raise SystemExit(__doc__)
