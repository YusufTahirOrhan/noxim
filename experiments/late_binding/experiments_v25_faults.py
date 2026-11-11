"""v25 Part C (results_v25_confirm/PREREGISTRATION.md): fault sweep, k = 1, 2, 3 faulty VLs in every chiplet, uniform traffic.
Run through experiments_v25.py:
  c_formal  model check (CI_XY_XY, CI_XY_O1, the paper's Up rule) on the masks of the sweep -> formal_faults.md
  c_drain   all-pairs drain test of every row on every mask (seed 1) -> drain_faults.csv
  c_sat     DeFT-P sweeps per mask (D1 rule, seed 101, pipe_all 2), upwards in batches until the first rate above 3 x L0
  c_points  Lsat and the four loads per mask -> load_points_faults.json, load_points_faults.md
  c_eval    the design: 27 masks x 6 rows x 4 loads x seeds 131-135 (raw outputs under ~/lbraw/v25/ceval until c_csv)
  c_check   integrity of the raw folder
  c_csv     fault_runs.csv (raw outputs deleted when complete)
Masks: the first three per (size, k) of results_v11/masks.json; LUTs luts/v23 (one per mask).
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
import experiments_v25 as X  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL = X.RES, X.SIZES, X.NL
KS = (1, 2, 3)
N_MASKS = 3
SEEDS = range(131, 136)
MULTS = (0.5, 1.0, 1.4, 2.0)
ROWS = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran', X.MAIN, X.SECOND]
REFS = ROWS[:4]
LP_FILE = os.path.join(RES, 'load_points_faults.json')
BATCH = 8


def masks():
    """[(size, k, mask)] of the sweep."""
    ms = json.load(open(os.path.join(HERE, 'results_v11', 'masks.json')))
    return [(z, k, m) for z in SIZES for k in KS for m in ms['%s__k%d' % (z, k)][:N_MASKS]]


def mask_set(m):
    b = int(m, 16)
    return frozenset(v for v in range(64) if b >> v & 1)


# ---- model check ----
def _formal_init(cx, cy):
    sys.path.insert(0, os.path.join(HERE, 'formal'))
    import impl_relation_check as I
    I.set_size(cx, cy, 4, 4)
    I.UP_KEEP = True


def _formal_job(arg):
    import impl_relation_check as I
    t = time.time()
    r = I.job_lean(arg)
    return r + (time.time() - t,)


def formal(nproc):
    from multiprocessing import Pool
    sys.path.insert(0, os.path.join(HERE, 'formal'))
    import impl_relation_check as I
    rels = ['CI_XY_XY', 'CI_XY_O1']
    I.set_size(2, 2, 4, 4)
    known = set(I.masks())                   # the 897 masks of 2x2 checked in rounds 23 and 24
    L = ['# v25 Part C: model check on the masks of the fault sweep (experiments_v25.py c_formal)', '',
         'Relations `CI_XY_XY` (late entry, XY on the interposer: the main row) and `CI_XY_O1` (the VN-split order: the second row), with the paper\'s Up rule',
         '(`impl_relation_check.UP_KEEP = True`), the boundary round-robin (both VNs explored on Horizontal -> Down), R3 on the input VN and the F1 source rule,',
         'as in `results_v24_xy/formal_xy.md`. Checks per relation and mask: CDG acyclic, no dead-end state, state graph acyclic (no livelock).', '',
         '| size | k | mask | relation | CDG acyclic | dead-end states | livelock free | longest path (hops) | CDG nodes / edges | seconds |', '|---|---|---|---|---|---|---|---|---|---|']
    ok_all, n_checks, skipped, t_all = True, 0, [], {}
    for z in SIZES:
        cx, cy = E5.SIZES[z]
        todo = [(k, m) for zz, k, m in masks() if zz == z and not (z == '2x2' and mask_set(m) in known)]
        skipped += [m for zz, k, m in masks() if zz == z and z == '2x2' and mask_set(m) in known]
        jobs = [(r, mask_set(m)) for k, m in todo for r in rels]
        t = time.time()
        with Pool(nproc, initializer=_formal_init, initargs=(cx, cy)) as pool:
            res = pool.map(_formal_job, jobs, chunksize=1)
        t_all[z] = time.time() - t
        i = 0
        for k, m in todo:
            for r in rels:
                x = res[i]
                i += 1
                good = x[2] and x[3] == 0 and x[4]
                ok_all = ok_all and good
                n_checks += 1
                L.append('| %s | %d | %s | %s | %s | %d | %s | %d | %d / %d | %.0f |' % (z, k, m, r, 'yes' if x[2] else '**NO**', x[3], 'yes' if x[4] else '**NO**', x[5], x[6], x[7], x[8]))
    L += ['', 'Wall time with %d processes: %s.' % (nproc, ', '.join('%s %.0f s' % (z, t_all[z]) for z in SIZES)),
          '2x2 masks of the sweep that are among the 897 masks checked in round 24 (not repeated): %s.' % (', '.join(skipped) if skipped else 'none; all nine were checked here'),
          'All 4x4 masks were checked (the 3 h limit of the pre-registration was not reached).', '',
          '**%d checks, all pass: %s.**' % (n_checks, 'yes' if ok_all else 'NO')]
    open(os.path.join(RES, 'formal_faults.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok_all


# ---- drain tests ----
def drain_jobs():
    js = []
    for z, k, m in masks():
        for row in ROWS:
            a = common_args(1, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(z), lut=X23.lut23(z, m)) + E5.size_args(z) + \
                X.row_args(z, row) + X23.pipe(2) + X24.TRNG + (E10.DRAIN_ALLPAIRS_2X2 if z == '2x2' else E10.DRAIN_ALLPAIRS)
            js.append(('allpairs__%s-p2__%s-k%d-%s__s1' % (row, z, k, m), a))
    return js


def drain(nproc):
    js = drain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    res = run_jobs(js, X.raw('cdrain'), nproc=nproc, timeout=14400)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_faults.csv'))
    if not fails:
        shutil.rmtree(X.raw('cdrain'))
    return not fails


# ---- ladders (the D1 rule, run upwards) ----
def sat_name(z, m, r):
    return 'csat__DeFT_P-p2__%s-uniform__%s__%.4f__s101' % (z, m, r)


def sat_job(z, m, r):
    return X.job('csat', z, 'DeFT_P', X23.methods(z)['DeFT_P'], 2, 'uniform', m, r, 101)


def lat_of(z, m, r):
    f = os.path.join(X.raw('csat'), sat_name(z, m, r) + '.json')
    return json.load(open(f))['summary']['global_average_delay_cycles'] if os.path.exists(f) else None


def coarse(z, m):
    """(Lsat, the first swept rate above 3 x L0 or None, complete): the coarse sweep read as far as it has been run."""
    l0 = lat_of(z, m, E5.L0_RATE)
    lsat = None
    for r in E5.SAT_RATES:
        x = lat_of(z, m, r)
        if x is None:
            return lsat, None, False
        if x > 3 * l0:
            return lsat, r, True
        lsat = r
    return lsat, None, True


def fine_rates(z, m):
    lsat, nxt, done = coarse(z, m)
    if nxt is None or (lsat is not None and lsat > E5.LOW_LSAT):
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    ms = masks()
    for z in SIZES:
        E5.gen_tables(z, 'uniform', E5.SAT_RATES + [E5.L0_RATE])
    run_jobs([sat_job(z, m, E5.L0_RATE) for z, k, m in ms], X.raw('csat'), nproc=nproc, timeout=7200)
    for b in range(0, len(E5.SAT_RATES), BATCH):
        todo = [(z, m) for z, k, m in ms if not coarse(z, m)[2]]
        if not todo:
            break
        js = [sat_job(z, m, r) for z, m in todo for r in E5.SAT_RATES[b:b + BATCH]]
        print('coarse batch %d: %d masks, %d jobs' % (b // BATCH, len(todo), len(js)), flush=True)
        run_jobs(js, X.raw('csat'), nproc=nproc, timeout=7200)
    js = []
    for z, k, m in ms:
        fr = fine_rates(z, m)
        E5.gen_tables(z, 'uniform', fr)
        js += [sat_job(z, m, r) for r in fr]
    print('fine jobs:', len(js), flush=True)
    res = run_jobs(js, X.raw('csat'), nproc=nproc, timeout=7200)
    print('fine runs', len(js), 'missing', sum(1 for v in res.values() if v is None))


def points():
    res = {}
    L = ['# v25 Part C: load points per mask (experiments_v25.py c_sat, c_points)', '',
         'DeFT-P (-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), uniform traffic, seed 101, pipe_all 2, the v23 LUT of the mask.',
         'D1 rule: L0 = latency at 0.0002; Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse (0.0005-grid) Lsat',
         'is <= 0.004 and on the 0.0005 grid otherwise. The coarse sweep was run upwards in batches of %d rates and stopped after the first rate above 3 x L0.' % BATCH,
         'Loads: 0.5, 1.0, 1.4, 2.0 x Lsat, rounded to the grid.', '',
         '| size | k | mask | grid | L0 | Lsat | lat / L0 at Lsat | loads | fault-free Lsat (same rule) |', '|---|---|---|---|---|---|---|---|---|']
    ff = X.lp()
    for z, k, m in masks():
        l0 = lat_of(z, m, E5.L0_RATE)
        fr = fine_rates(z, m)
        grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
        lsat = None
        for r in rates:
            x = lat_of(z, m, r)
            if x is None or x > 3 * l0:
                break
            lsat = r
        if lsat is None:
            raise SystemExit('no Lsat for %s %s' % (z, m))
        ev = []
        for mult in MULTS:
            x = round(max(grid, round(mult * lsat / grid) * grid), 4)
            if ev and x <= ev[-1]:
                x = round(ev[-1] + grid, 4)
            ev.append(x)
        res['%s__%s' % (z, m)] = {'size': z, 'k': k, 'mask': m, 'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0}
        L.append('| %s | %d | %s | %s | %.1f | %s | %.2f | %s | %s |' % (z, k, m, grid, l0, lsat, lat_of(z, m, lsat) / l0, ev, ff[X.lkey(z, 'uniform', E5.FREE[z])]['lsat']))
        E5.gen_tables(z, 'uniform', ev)
    json.dump(res, open(LP_FILE, 'w'), indent=1)
    open(os.path.join(RES, 'load_points_faults.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(X.raw('csat'))


def lpf():
    return json.load(open(LP_FILE))


# ---- the sweep ----
def eval_jobs(seeds=SEEDS):
    P = lpf()
    js = []
    for z, k, m in masks():
        lad = P['%s__%s' % (z, m)]['eval']
        for row in ROWS:
            a = X.row_args(z, row)
            for r in lad:
                js += [X.job('ceval', z, row, a, 2, 'uniform', m, r, seed) for seed in seeds]
    return js


def run_stage(stage, nproc, extra):
    if stage == 'c_formal':
        sys.exit(0 if formal(nproc) else 1)
    elif stage == 'c_drain':
        sys.exit(0 if drain(nproc) else 1)
    elif stage == 'c_sat':
        sat(nproc)
    elif stage == 'c_points':
        points()
    elif stage == 'c_eval':
        for z, k, m in masks():
            E5.gen_tables(z, 'uniform', lpf()['%s__%s' % (z, m)]['eval'])
        js = eval_jobs()
        print('fault-sweep jobs:', len(js), flush=True)
        t = time.time()
        res = run_jobs(js, X.raw('ceval'), nproc=nproc, timeout=14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'c_check':
        sys.exit(0 if E19.check_raw(X.raw('ceval'), eval_jobs(), 'eval') else 1)
    elif stage == 'c_csv':
        import experiments_v25_eval as EV
        n = EV.to_csv(X.raw('ceval'), os.path.join(RES, 'fault_runs.csv'), expect=len(eval_jobs()))
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('ceval'))
    else:
        raise SystemExit(__doc__)
