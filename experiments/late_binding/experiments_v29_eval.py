"""v29 simulation parts (results_v29_review/PREREGISTRATION.md), run through experiments_v29.py:
  b_sat, b_points   B0: DeFT-P's ladders of tornado, neighbour and randperm (the D1 rule of round 23 as round 25 ran it: seed 101,
                    pipe_all 2, 3 x L0, nine loads) -> load_points_v29.json, load_points_v29.md
  t_timing          timing runs (runs of the designs, kept) and the 48 h rule -> runtime_estimate.md, drops.json
  <part>_eval, <part>_check, <part>_csv   the runs of a part, the integrity of its raw folder, its per-run CSV (raw outputs deleted):
      b1  the held-out scenarios, seeds 181-190                               -> heldout_runs.csv
      b2  LB_b0 on 2x2 on the six scenarios of round 25, seeds 121-130        -> lb_b0_runs.csv
      c1  the references at depth 6 and 5 and LB_d6, seeds 121-130            -> depth_runs.csv
      c2  the references with interposer depth 7, four loads, seeds 121-130   -> ipos7_runs.csv
      c3  DeFT_P_d6 and DeFT_B_d6 on the masks of round 26 (1/16, 4/16)       -> depth_fault_runs.csv
      d1  MTR_static, RC_static, seeds 121-130                                -> vc_static_runs.csv
      d2  the set-up of the DeFT paper on 2x2, pipe_all 2 and 0, seeds 191-195 -> deft_setup_runs.csv
      e1  LB_noLA, seeds 121-130                                              -> nola_runs.csv
      f1  EB_first, seeds 171-180                                             -> early_first_runs.csv
      f2  EB_best16, EB_best256, seeds 171-180                                -> early_age_runs.csv
  f_rule            the tuning rule of Part F -> tuning_v29.md (written before any tuning run)
  f1_tune, f1_choose   lut_bias of EB_first (seeds 101, 102) -> tuning_v29.md, tuning_choice_v29.json, tune_first_runs.csv
  f2_tune, f2_choose   T of EB_best16 and EB_best256         -> tuning_v29.md, tuning_choice_v29.json, tune_age_runs.csv
Row definitions: experiments_v29_rows.py. Raw outputs under ~/lbraw/v29/<stage> until the stage that writes the CSV.
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
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v26 as X26  # noqa: E402
import experiments_v26_eval as EV26  # noqa: E402
import experiments_v27_eval as EV27  # noqa: E402
import experiments_v28_eval as EV28  # noqa: E402
import experiments_v29 as X  # noqa: E402
import experiments_v29_rows as R  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL, MAIN = X.RES, X.SIZES, X.NL, X.MAIN
lb, wmd, fmt = X.lb, R.wmd, R.fmt
DROPS = os.path.join(RES, 'drops.json')
SEEDS_B = range(181, 191)                      # never used before (Part B)
SEEDS_25 = range(121, 131)                     # round 25 (Parts B2, C1, C2, D1, E1)
SEEDS_26 = (151, 152)                          # round 26 (Part C3)
SEEDS_28 = range(171, 181)                     # round 28 (Part F)
SEEDS_D2 = range(191, 196)                     # never used before (Part D2)
LIMIT_H = 48.0
G_HOURS = 3.0                                  # Part G: at most 3 h (PROMPT.md)
C1_D6 = ['DeFT_P_d6', 'DeFT_B_d6', 'MTR_d6', 'RC_d6']
C1_D5 = ['DeFT_P_d5', 'DeFT_B_d5', 'MTR_d5', 'RC_d5']
C2_ROWS = ['DeFT_P_i7', 'DeFT_B_i7', 'MTR_i7', 'RC_i7']
C2_LOADS = (1, 3, 5, 7)                        # 0.5, 1.0, 1.4, 2.0 x Lsat
C3_ROWS = ['DeFT_P_d6', 'DeFT_B_d6']
C3_RATES = ('1/16', '4/16')
D1_ROWS = ['MTR_static', 'RC_static']
D2_ROWS = ['DeFT_P', 'MTR', 'RC', 'MTR_static', 'RC_static']
D2_PATTERNS = ('uniform', 'localized', 'hotspot')
D2_PIPES = (2, 0)
F2_ROWS = ['EB_best16', 'EB_best256']
DROP_ORDER = ['G', 'F2', 'C3_rate_1_16', 'C2', 'D1_3x3_4x4', 'LB_d6', 'C1_d5_seeds126_130']
DROP_TEXT = {'G': 'Part G', 'F2': 'Part F2 (`EB_best16`, `EB_best256`: tuning and evaluation)', 'C3_rate_1_16': 'the rate 1/16 of C3', 'C2': 'Part C2',
             'D1_3x3_4x4': 'D1 on 3x3 and 4x4', 'LB_d6': '`LB_d6`', 'C1_d5_seeds126_130': 'seeds 126-130 of the rows at depth 5'}


def run_seg(js, out, nproc, timeout, seg=384):
    """run_jobs in segments, each with the number of processes that ~/lbraw/v29/width.txt gives at that moment."""
    res = {}
    for k in range(0, len(js), seg):
        w = X.width(nproc)
        print('%s runs %d-%d of %d with %d processes' % (time.strftime('%H:%M:%S'), k + 1, min(k + seg, len(js)), len(js), w), flush=True)
        res.update(run_jobs(js[k:k + seg], out, nproc=w, timeout=timeout))
    return res


def drops():
    return json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []


# =====================================================================================================================
# B0: ladders of the three new scenarios
# =====================================================================================================================
SAT_EXTRA = [round(0.028 + 0.004 * i, 4) for i in range(9)]      # 0.028 ... 0.060: only if a scenario is not saturated at 0.024


def sat_name(z, p, m, r):
    return 'sat__DeFT_P-p2__%s-%s__%s__%.4f__s101' % (z, p, m, r)


def sat_job(z, p, m, r):
    return X.job('sat', z, 'DeFT_P', X23.methods(z)['DeFT_P'], 2, p, m, r, 101)


def lat_of(z, p, m, r):
    f = os.path.join(X.raw('sat'), sat_name(z, p, m, r) + '.json')
    return json.load(open(f))['summary']['global_average_delay_cycles'] if os.path.exists(f) else None


def coarse_lsat(z, p, m):
    """(Lsat, the first swept rate above 3 x L0 or None) on the 0.0005 grid (and its extension above 0.024), as far as it has been run."""
    l0 = lat_of(z, p, m, E5.L0_RATE)
    lsat = None
    for r in E5.SAT_RATES + SAT_EXTRA:
        x = lat_of(z, p, m, r)
        if x is None:
            return lsat, None
        if x > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(z, p, m):
    lsat, nxt = coarse_lsat(z, p, m)
    if nxt is None or (lsat is not None and lsat > E5.LOW_LSAT):
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    cells = [(z, p, m) for z in SIZES for p, m in R.new_scenarios(z)]
    js = []
    for z, p, m in cells:
        E5.gen_tables(z, p, E5.SAT_RATES + [E5.L0_RATE])
        js += [sat_job(z, p, m, r) for r in E5.SAT_RATES + [E5.L0_RATE]]
    print('coarse jobs: %d' % len(js), flush=True)
    run_jobs(js, X.raw('sat'), nproc=X.width(nproc), timeout=7200)
    for r in SAT_EXTRA:                        # upwards, one rate at a time, for the cells that 0.024 does not saturate
        js = []
        for z, p, m in cells:
            lsat, nxt = coarse_lsat(z, p, m)
            if nxt is None and lat_of(z, p, m, r) is None and lat_of(z, p, m, E5.SAT_RATES[-1]) is not None:
                E5.gen_tables(z, p, [r])
                js.append(sat_job(z, p, m, r))
        if not js:
            break
        print('not saturated at the last swept rate: %d cells, next rate %.4f' % (len(js), r), flush=True)
        run_jobs(js, X.raw('sat'), nproc=X.width(nproc), timeout=7200)
    js = []
    for z, p, m in cells:
        fr = fine_rates(z, p, m)
        E5.gen_tables(z, p, fr)
        js += [sat_job(z, p, m, r) for r in fr]
    print('fine jobs: %d' % len(js), flush=True)
    res = run_jobs(js, X.raw('sat'), nproc=X.width(nproc), timeout=7200)
    miss = sum(1 for v in res.values() if v is None)
    print('fine runs %d, missing %d' % (len(js), miss))
    return miss == 0


def points():
    res = {}
    L = ['# Load points of v29 (experiments_v29.py b_sat, b_points)', '',
         'The three scenarios that no earlier round ran (tornado, neighbour, randperm, fault-free) get their ladders by the D1 rule of round 23 as round 25 ran it',
         '(`results_v25_confirm/load_points_v25.md`): DeFT-P (`-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1`), seed 101,',
         'pipe_all 2; L0 = latency at 0.0002; Lsat = the largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse',
         '(0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid otherwise; 9 loads at 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat. The coarse sweep ends at',
         '0.016, 0.018, 0.020, 0.024 as in every round; a scenario that is not saturated at 0.024 is swept further in steps of 0.004 (0.028, 0.032, ...) until it is.',
         'The six scenarios of round 25 keep their ladders (`results_v25_confirm/load_points_v25.json`).', '',
         '| size | scenario | grid | L0 | Lsat | lat / L0 at Lsat | first rate above 3 x L0 | ladder (pipe_all 2) |', '|---|---|---|---|---|---|---|---|']
    ok = True
    for z in SIZES:
        for p, m in R.new_scenarios(z):
            l0 = lat_of(z, p, m, E5.L0_RATE)
            fr = fine_rates(z, p, m)
            grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES + SAT_EXTRA)
            lsat, nxt = None, None
            for r in rates:
                x = lat_of(z, p, m, r)
                if x is None:
                    break
                if x > 3 * l0:
                    nxt = r
                    break
                lsat = r
            if lsat is None or nxt is None:
                ok = False
                L.append('| %s | %s | %s | %s | **no Lsat** (%s, %s) | | | |' % (z, p, grid, l0, lsat, nxt))
                continue
            ev = []
            for mult in X25.MULTS9:
                x = round(max(grid, round(mult * lsat / grid) * grid), 4)
                if ev and x <= ev[-1]:
                    x = round(ev[-1] + grid, 4)
                ev.append(x)
            res[X.lkey(z, p, m)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0, 'pipe_all': 2}
            E5.gen_tables(z, p, ev)
            L.append('| %s | %s | %s | %.1f | %s | %.2f | %s | %s |' % (z, p, grid, l0, lsat, lat_of(z, p, m, lsat) / l0, nxt, ev))
    if not ok:
        print(NL.join(L))
        return False
    json.dump(res, open(R.LP_FILE, 'w'), indent=1)
    wmd('load_points_v29.md', L)
    shutil.rmtree(X.raw('sat'))
    return True


# =====================================================================================================================
# The designs
# =====================================================================================================================
def ladder_jobs(stage, rows, sizes, scen_of, P, seeds, loads, keep=None, pipe=2):
    js = []
    for row in rows:
        for z in sizes:
            a = R.row_args(z, row)
            for p, m in scen_of(z):
                lad = P[X.lkey(z, p, m, pipe)]['eval']
                E5.gen_tables(z, p, [lad[i] for i in loads])
                for i in loads:
                    js += [R.job(stage, z, row, a, p, m, lad[i], s, pipe=pipe) for s in seeds if keep is None or keep(row, z, s)]
    return js


def b1_jobs(seeds=SEEDS_B, loads=range(9), sizes=SIZES, d=None):
    P = R.lp()
    js = ladder_jobs('heldout', R.REFS5 + [MAIN], sizes, R.new_scenarios, P, seeds, loads)
    if '2x2' in sizes:
        js += ladder_jobs('heldout', ['LB_b0'], ['2x2'], R.new_scenarios, P, seeds, loads)
    return js


def b2_jobs(seeds=SEEDS_25, loads=range(9), sizes=('2x2',), d=None):
    return ladder_jobs('lbb0', ['LB_b0'], ['2x2'], R.ff_scenarios, X25.lp(), seeds, loads)


def c1_jobs(seeds=SEEDS_25, loads=range(9), sizes=SIZES, d=None, rows=None):
    d = drops() if d is None else d
    rows = rows or (C1_D6 + ([] if 'LB_d6' in d else ['LB_d6']) + C1_D5)
    return ladder_jobs('depth', rows, sizes, R.ff_scenarios, X25.lp(), seeds, loads,
                       keep=lambda row, z, s: not ('C1_d5_seeds126_130' in d and row in C1_D5 and s >= 126))


def c2_jobs(seeds=SEEDS_25, loads=C2_LOADS, sizes=SIZES, d=None):
    d = drops() if d is None else d
    return [] if 'C2' in d else ladder_jobs('ipos7', C2_ROWS, sizes, R.ff_scenarios, X25.lp(), seeds, loads)


def c3_entries(d):
    rates = ('4/16',) if 'C3_rate_1_16' in d else C3_RATES
    return [e for e in X26.part_b() if e['rate'] in rates]


def c3_jobs(seeds=SEEDS_26, loads=range(4), sizes=SIZES, d=None, entries=None):
    d = drops() if d is None else d
    P = EV26.lpf()
    js = []
    for e in (c3_entries(d) if entries is None else entries):
        z, m = e['size'], e['mask']
        if z not in sizes:
            continue
        for p in EV26.PATTERNS:
            lad = P[EV26.key(z, p, m)]['eval']
            E5.gen_tables(z, p, [lad[i] for i in loads])
            for row in C3_ROWS:
                a = R.row_args(z, row)
                for i in loads:
                    js += [R.job('depthfault', z, row, a, p, m, lad[i], s) for s in seeds]
    return js


def d1_jobs(seeds=SEEDS_25, loads=range(9), sizes=SIZES, d=None):
    d = drops() if d is None else d
    return ladder_jobs('static', D1_ROWS, [z for z in sizes if z == '2x2' or 'D1_3x3_4x4' not in d], R.ff_scenarios, X25.lp(), seeds, loads)


def d2_rates(p, pipe):
    """The twelve rates of D2: 0.1 to 1.2 x Lsat of DeFT_P (the ladder of round 25 at pipe_all 2, of round 23 at pipe_all 0; both in
    load_points_v25.json), rounded to the 0.0001 grid (halves up; in integers, so that the rounding does not depend on a float)."""
    lsat = X25.lp()[X.lkey('2x2', p, E5.FREE['2x2'], pipe)]['lsat']
    u = int(round(lsat * 10000))
    out = []
    for k in range(1, 13):
        x = (k * u + 5) // 10
        if out and x <= out[-1]:
            x = out[-1] + 1
        out.append(x)
    return [round(x / 10000.0, 4) for x in out]


def d2_jobs(seeds=SEEDS_D2, idx=range(12), sizes=('2x2',), d=None):
    js = []
    z, m = '2x2', E5.FREE['2x2']
    for pipe in D2_PIPES:
        for row in D2_ROWS:
            a = R.row_args(z, row)
            for p in D2_PATTERNS:
                rates = d2_rates(p, pipe)
                E5.gen_tables(z, p, [rates[i] for i in idx])
                for i in idx:
                    js += [R.job('deftpaper', z, row, a, p, m, rates[i], s, pipe=pipe) for s in seeds]
    return js


def e1_jobs(seeds=SEEDS_25, loads=range(9), sizes=SIZES, d=None):
    return ladder_jobs('nola', ['LB_noLA'], sizes, R.ff_scenarios, X25.lp(), seeds, loads)


def f1_jobs(seeds=SEEDS_28, loads=range(9), sizes=SIZES, d=None):
    return ladder_jobs('first', ['EB_first'], sizes, R.ff_scenarios, X25.lp(), seeds, loads)


def f2_jobs(seeds=SEEDS_28, loads=range(9), sizes=SIZES, d=None):
    d = drops() if d is None else d
    return [] if 'F2' in d else ladder_jobs('age', F2_ROWS, sizes, R.ff_scenarios, X25.lp(), seeds, loads)


PARTS = {      # part: (raw folder, per-run CSV, jobs, columns of the CSV or None for the v25 columns and the counters of rounds 27-29)
    'b1': ('heldout', 'heldout_runs.csv', b1_jobs, R.V25_COLS),
    'b2': ('lbb0', 'lb_b0_runs.csv', b2_jobs, R.V25_COLS),
    'c1': ('depth', 'depth_runs.csv', c1_jobs, R.V25_COLS),
    'c2': ('ipos7', 'ipos7_runs.csv', c2_jobs, R.V25_COLS),
    'c3': ('depthfault', 'depth_fault_runs.csv', c3_jobs, R.V25_COLS),
    'd1': ('static', 'vc_static_runs.csv', d1_jobs, R.V25_COLS),
    'd2': ('deftpaper', 'deft_setup_runs.csv', d2_jobs, R.V25_COLS),
    'e1': ('nola', 'nola_runs.csv', e1_jobs, R.V25_COLS),
    'f1': ('first', 'early_first_runs.csv', f1_jobs, None),
    'f2': ('age', 'early_age_runs.csv', f2_jobs, None),
}


def part_eval(part, nproc):
    raw, fn, jobs, _ = PARTS[part]
    js = jobs()
    print('%s jobs: %d' % (part, len(js)), flush=True)
    if not js:
        return True
    t = time.time()
    res = run_seg(js, X.raw(raw), X.width(nproc), 14400)
    miss = sum(1 for v in res.values() if v is None)
    print('done in %.0f s; missing outputs: %d' % (time.time() - t, miss), flush=True)
    return miss == 0


def part_check(part):
    raw, fn, jobs, _ = PARTS[part]
    js = jobs()
    return True if not js else E19.check_raw(X.raw(raw), js, 'eval')


def part_csv(part):
    raw, fn, jobs, cols = PARTS[part]
    js = jobs()
    if not js:
        print('%s: nothing to do (dropped by the time rule)' % part)
        return True
    out = os.path.join(RES, fn)
    full = os.path.join(X.RAW, fn + '.full')
    n = R.to_csv(X.raw(raw), full)                         # with every counter, for the checks below
    rows = list(csv.DictReader(open(full)))
    dead = sum(int(r['dead_ends']) for r in rows)
    eb = [r for r in rows if r['variant'].startswith('EB')]
    multi = sum(int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0) for r in eb)
    twice = sum(1 for r in eb if r['entry_commit_first_max_per_head'] not in ('', '0', '1'))
    print('%s: %d rows of %d; dead-end events %d; hops of EB rows that offer more than one output %d; runs with a head bound twice %d' % (
        fn, n, len(js), dead, multi, twice), flush=True)
    ok = n == len(js) and dead == 0 and multi == 0 and twice == 0
    if ok:
        if cols is None:
            shutil.move(full, out)
        else:
            R.to_csv(X.raw(raw), out, expect=len(js), cols=cols)
            os.remove(full)
        shutil.rmtree(X.raw(raw), ignore_errors=True)
    return ok


# =====================================================================================================================
# Timing runs and the 48 h rule
# =====================================================================================================================
def timing_sets():
    """[(kind, size, raw folder, jobs)]: runs of the designs, timed one set after the other. B: the held-out scenarios (seed 181, all nine
    loads); L: ladder runs on the scenarios of round 25 (the references at depth 6, seeds 121 and 122, the 2nd, 5th and 9th load); F: the
    fault runs of C3 (seed 151, the 1st and 4th load, masks 1-4 of both rates); P: the runs of D2 (seed 191, both pipe depths)."""
    sets = []
    for z in SIZES:
        sets.append(('B', z, 'heldout', b1_jobs(seeds=(181,), sizes=[z])))
        sets.append(('L', z, 'depth', c1_jobs(seeds=(121, 122), loads=(1, 4, 8), sizes=[z], d=[], rows=C1_D6)))
        sets.append(('F', z, 'depthfault', c3_jobs(seeds=(151,), loads=(0, 3), sizes=[z], d=[], entries=[e for e in X26.part_b() if e['rate'] in C3_RATES and e['index'] <= 4])))
    sets.append(('P', '2x2', 'deftpaper', d2_jobs(seeds=(191,))))
    return sets


def count_by_size(js):
    c = {z: 0 for z in SIZES}
    for n, _ in js:
        c[n.split('__')[2].split('-')[0]] += 1
    return c


TUNE_F1_RUNS = 5 * 40 + 2 * 40                 # per tuning size: five values of lut_bias, and DeFT_P and the main row, on the 40 tuning cells
TUNE_F2_RUNS = 2 * 6 * 40                      # per tuning size: two rows, six values of T


def estimate(per, d):
    """{part: hours} with the per-run seconds per[(kind, size)] and the drops d. Tuning runs of Part F are counted at their grids (no
    extension); Part G at its limit of 3 h."""
    H = {}

    def hours(js, kind):
        c = count_by_size(js)
        return sum(c[z] * per[(kind, z)] for z in SIZES) / 3600.0, sum(c.values())
    H['B1'] = hours(b1_jobs(d=d), 'B')
    H['B2'] = hours(b2_jobs(d=d), 'L')
    H['C1'] = hours(c1_jobs(d=d), 'L')
    H['C2'] = hours(c2_jobs(d=d), 'L')
    H['C3'] = hours(c3_jobs(d=d), 'F')
    H['D1'] = hours(d1_jobs(d=d), 'L')
    n = len(d2_jobs(d=d))
    H['D2'] = (n * per[('P', '2x2')] / 3600.0, n)
    H['E1'] = hours(e1_jobs(d=d), 'L')
    # Part F: the rows are defined by the tuning, which comes later; a row of the evaluation is 6 scenarios x 9 loads x 10 seeds per size
    row = {z: len(R.ff_scenarios(z)) * 9 * len(SEEDS_28) for z in SIZES}
    row_h = sum(row[z] * per[('L', z)] for z in SIZES) / 3600.0
    H['F1'] = (row_h + sum(TUNE_F1_RUNS * per[('L', z)] for z in EV24.TUNE_SIZES) / 3600.0, sum(row.values()) + TUNE_F1_RUNS * 2)
    if 'F2' in d:
        H['F2'] = (0.0, 0)
    else:
        H['F2'] = (len(F2_ROWS) * row_h + sum(TUNE_F2_RUNS * per[('L', z)] for z in EV24.TUNE_SIZES) / 3600.0, len(F2_ROWS) * sum(row.values()) + TUNE_F2_RUNS * 2)
    H['G'] = (0.0 if 'G' in d else G_HOURS, 0)
    return H


def timing(nproc):
    nproc = X.width(nproc)
    T, miss = {}, {}
    for kind, z, raw, js in timing_sets():
        t = time.time()
        r = run_jobs(js, X.raw(raw), nproc=nproc, timeout=14400)
        T[(kind, z)] = (time.time() - t, len(js))
        miss[(kind, z)] = sum(1 for x in r.values() if x is None)
        print('%s timing set %s %s: %d runs, %.0f s' % (time.strftime('%H:%M:%S'), kind, z, len(js), T[(kind, z)][0]), flush=True)
    per = {k: v[0] / v[1] for k, v in T.items()}
    d = []
    for name in DROP_ORDER:
        if sum(h for h, _ in estimate(per, d).values()) <= LIMIT_H:
            break
        d.append(name)
    full, kept = estimate(per, []), estimate(per, d)
    tot_full, tot_kept = sum(h for h, _ in full.values()), sum(h for h, _ in kept.values())
    json.dump(dict(dropped=d, nproc=nproc, timing={'%s_%s' % k: dict(seconds=v[0], runs=v[1], per_run=per[k]) for k, v in T.items()},
                   estimate_hours=tot_full, estimate_hours_after_drops=tot_kept, parts={k: dict(hours=v[0], runs=v[1]) for k, v in kept.items()},
                   parts_before_drops={k: dict(hours=v[0], runs=v[1]) for k, v in full.items()}), open(DROPS, 'w'), indent=1)
    KIND = {'B': 'held-out scenarios (Part B1), seed 181, the nine loads', 'L': 'ladder runs on the scenarios of round 25 (the references at depth 6), seeds 121 and 122, the 2nd, 5th and 9th load',
            'F': 'fault runs (C3), seed 151, the 1st and 4th load, masks 1-4 of both rates', 'P': 'the set-up of the DeFT paper (D2), seed 191, both pipe depths'}
    L = ['# Run-time estimate v29, Parts B to G (experiments_v29.py t_timing)', '',
         'Timing runs (runs of the designs, kept; nothing of their results was looked at), %d processes, one set after the other, no other job of this round next to a' % nproc,
         'set; what else ran on the PC at that time is in `DECISIONS.md`. The estimate is taken as measured (`PREREGISTRATION.md`, "Time rule"). A part is estimated with',
         'the seconds per run of the set of its kind and size: Parts B2, C1, C2, D1, E1 and F (evaluation and tuning runs) with the ladder runs, C3 with the fault runs.',
         'The tuning runs of Part F are counted at their grids (%d and %d runs per tuning size, no extension); Part G at its limit of %.0f h.' % (TUNE_F1_RUNS, TUNE_F2_RUNS, G_HOURS), '',
         '| set | size | timing runs | wall | per run |', '|---|---|---|---|---|']
    for kind, z, _, _ in timing_sets():
        L.append('| %s | %s | %d (%d missing) | %.0f s | %.2f s |' % (KIND[kind], z, T[(kind, z)][1], miss[(kind, z)], T[(kind, z)][0], per[(kind, z)]))
    L += ['', '| part | runs | estimate | after the drops: runs | estimate |', '|---|---|---|---|---|']
    for k in ('B1', 'B2', 'C1', 'C2', 'C3', 'D1', 'D2', 'E1', 'F1', 'F2', 'G'):
        L.append('| %s | %s | %.1f h | %s | %.1f h |' % (k, full[k][1] or '-', full[k][0], kept[k][1] or '-', kept[k][0]))
    L += ['', 'Together **%.1f h**. Rule (pre-registered): above %.0f h in total drop, in this order: %s.' % (tot_full, LIMIT_H, '; '.join(DROP_TEXT[x] for x in DROP_ORDER)), '',
          '**Dropped: %s.** Estimate of what is run: %.1f h.' % (', '.join(DROP_TEXT[x] for x in d) if d else 'nothing', tot_kept)]
    wmd('runtime_estimate.md', L)
    keep = set()                               # timing runs of dropped cells are removed
    for jobs in (b1_jobs, c1_jobs, c3_jobs, d2_jobs):
        keep |= {j[0] for j in jobs(d=d)}
    for kind, z, raw, js in timing_sets():
        for j in js:
            if j[0] not in keep:
                for ext in ('.json', '.log'):
                    f = os.path.join(X.raw(raw), j[0] + ext)
                    if os.path.exists(f):
                        os.remove(f)
    return not any(miss.values())


# =====================================================================================================================
# Part F: tuning
# =====================================================================================================================
TUNE_SEEDS, TUNE_SIZES, TUNE_LOADS = EV24.TUNE_SEEDS, EV24.TUNE_SIZES, EV24.TUNE_LOADS
F1_GRID, F1_MAX = (0.0, 1.0, 2.0, 4.0, 8.0), 64.0
F2_GRID, F2_MAX = (0.0, 2.0, 4.0, 8.0, 16.0, 32.0), 128.0
F2_PERIODS = (16, 256)
STATE1 = os.path.join(X.RAW, 'tune_state_f1.json')
STATE2 = os.path.join(X.RAW, 'tune_state_f2.json')
CSV1 = os.path.join(RES, 'tune_first_runs.csv')
CSV2 = os.path.join(RES, 'tune_age_runs.csv')
V27_TUNE = os.path.join(EV27.RES, 'tune_runs.csv')
TUNING_RULE = [
    '## The rule (written before any tuning run of this round)', '',
    '* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged, as rounds 27 and 28 applied it to their early rows: pipe_all 2, DeFT-P VN options,',
    '  `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3 takes the 4x4 choice); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and',
    '  uniform with one faulty VL per chiplet); the ladder indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102. 80 runs per',
    '  configuration.',
    '* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where',
    '  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.',
    '  DeFT-P scores 0. DeFT-P and the main row are run again on the 80 tuning cells with the build of this round (160 runs); their rows must equal those of',
    '  `results_v27_early/tune_runs.csv`, which gave rounds 27 and 28 their scores.',
    '* **F1, `EB_first`:** the main row with `entry_commit first` and `lut_bias` D in {0, 1, 2, 4, 8}, everything else the frozen main row. If the best D is 8, 16 is',
    '  added, then 32 and 64 (at most), one value at a time, until the best D is no longer the largest (the extension rule of `EB_down_t` in round 28). The choice',
    '  per size: the D with the largest score; of two equal scores, the larger D. A `lut_bias` of infinity is DeFT_P\'s routing (`anchor_first.md`); if the best',
    '  score is below 0, the best member of the family is DeFT_P itself: that is said first where the row is reported, the finite D stays `EB_first` so that there',
    '  is a row to run, and every share is also reported against the better of `EB_first` and DeFT_P.',
    '* **F2, `EB_best16` and `EB_best256`:** S, P and B of `EB_best` (per size, `results_v28_anchor/tuning_choice_v28.json`), `oracle_period` 16 or 256, T in',
    '  {0, 2, 4, 8, 16, 32}; if the best T is the largest, it is doubled (64, 128 at most), one value at a time (B2 of round 28, unchanged). The choice as for',
    '  `EB_best64` there: the largest score; of two equal scores, the larger T; a best score below 0 is treated as for `EB_first`.',
    '* Runs: F1 5 x 80 = 400, plus the 160 runs of DeFT-P and the main row; F2 2 x 6 x 80 = 960; 40 per value and size that an extension adds. (The prompt gives',
    '  800 runs for F1; the grid of five values on two sizes is 400 by this rule. See `DECISIONS.md`.) The main row is not tuned; its score is reported next to the',
    '  others.', '']


def f1_name(D):
    return 'EBfirst_D%s' % fmt(D)


def f2_name(z, per, T):
    b = EV28.choice()[z]['EB_best']
    return 'EBf%d_%s_P%d_B%s_T%s' % (per, b['S'], b['P'], fmt(b['B']), fmt(T))


def f2_args(z, per, T):
    b = EV28.choice()[z]['EB_best']
    return EV28.ebf_args(b['S'], b['P'], b['B'], T, period=per)


def load_state(path, new):
    return json.load(open(path)) if os.path.exists(path) else new


def save_state(path, st):
    json.dump(st, open(path + '.tmp', 'w'), indent=1)
    os.replace(path + '.tmp', path)


def tune_jobs1(st):
    js = []
    for z in TUNE_SIZES:
        for p, m, rate, seed in EV24.tune_cells(z):
            js.append(R.job('tune1', z, 'DeFT_P', X25.row_args(z, 'DeFT_P'), p, m, rate, seed))
            js.append(R.job('tune1', z, MAIN, X25.row_args(z, MAIN) + R.ES, p, m, rate, seed))
            for D in st[z]:
                js.append(R.job('tune1', z, f1_name(D), R.first_args(z, D), p, m, rate, seed))
    return js


def tune_jobs2(st):
    js = []
    for z in TUNE_SIZES:
        for p, m, rate, seed in EV24.tune_cells(z):
            for per in F2_PERIODS:
                for T in st[z][str(per)]:
                    js.append(R.job('tune2', z, f2_name(z, per, T), f2_args(z, per, T), p, m, rate, seed))
    return js


def load_tune():
    """{(configuration name, size, pattern, mask, rate, seed): (THR, LAT)} of the tuning runs of this round: from the raw folders, and from
    the per-run CSVs once they are written."""
    T = {}
    for path in (CSV1, CSV2):
        if os.path.exists(path):
            for r in csv.DictReader(open(path)):
                z, p = r['pattern'].split('-')
                T[(r['variant'][:-3], z, p, r['mask'], float(r['rate']), int(r['seed']))] = (float(r['accepted']), float(r['latency']))
    for stage in ('tune1', 'tune2'):
        for f in glob.glob(os.path.join(X.raw(stage), '*.json')):
            (v, sp, m, rate, seed), d = MK.parse(f)
            z, p = sp.split('-')
            T[(v[:-3], z, p, m, rate, seed)] = (d['summary']['average_ip_throughput_flits_per_cycle_per_ip'], d['summary']['global_average_delay_cycles'])
    return T


def best_of(T, names, z):
    """(index of the best, scores): the largest score; of two equal scores, the later in the list (the larger D or T). Raises if a run is missing."""
    sc = []
    for n in names:
        s = EV28.score(T, n, z)
        if s is None:
            raise RuntimeError('missing tuning runs of %s on %s' % (n, z))
        sc.append(s)
    return max(range(len(names)), key=lambda i: (sc[i][0], i)), sc


def f1_tune(nproc):
    st = load_state(STATE1, {z: list(F1_GRID) for z in TUNE_SIZES})
    save_state(STATE1, st)
    step = 0
    while True:
        js = tune_jobs1(st)
        print('%s F1 tuning step %d: %d jobs of the state (finished runs are skipped)' % (time.strftime('%H:%M:%S'), step, len(js)), flush=True)
        res = run_seg(js, X.raw('tune1'), X.width(nproc), 14400)
        if any(v is None for v in res.values()):
            print('missing outputs; stop', flush=True)
            return False
        T = load_tune()
        added = 0
        for z in TUNE_SIZES:
            i, _ = best_of(T, [f1_name(D) for D in st[z]], z)
            if st[z][i] == max(st[z]) and max(st[z]) >= F1_GRID[-1] and max(st[z]) * 2 <= F1_MAX:
                st[z] = sorted(st[z] + [max(st[z]) * 2])
                added += 1
                print('extension %s EB_first: the best lut_bias is the largest; new value %s' % (z, fmt(max(st[z]))), flush=True)
        if not added:
            break
        save_state(STATE1, st)
        step += 1
    return True


def f2_tune(nproc):
    if 'F2' in drops():
        print('F2 is dropped by the time rule')
        return True
    st = load_state(STATE2, {z: {str(per): list(F2_GRID) for per in F2_PERIODS} for z in TUNE_SIZES})
    save_state(STATE2, st)
    step = 0
    while True:
        js = tune_jobs2(st)
        print('%s F2 tuning step %d: %d jobs of the state (finished runs are skipped)' % (time.strftime('%H:%M:%S'), step, len(js)), flush=True)
        res = run_seg(js, X.raw('tune2'), X.width(nproc), 14400)
        if any(v is None for v in res.values()):
            print('missing outputs; stop', flush=True)
            return False
        T = load_tune()
        added = 0
        for z in TUNE_SIZES:
            for per in F2_PERIODS:
                g = st[z][str(per)]
                i, _ = best_of(T, [f2_name(z, per, t) for t in g], z)
                if g[i] == max(g) and max(g) >= F2_GRID[-1] and max(g) * 2 <= F2_MAX:
                    st[z][str(per)] = sorted(g + [max(g) * 2])
                    added += 1
                    print('extension %s EB_best%d: the best T is the largest; new value %s' % (z, per, fmt(max(g) * 2)), flush=True)
        if not added:
            break
        save_state(STATE2, st)
        step += 1
    return True


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def tuning_md(ch):
    """tuning_v29.md from the rule, the runs that exist and the choices made so far."""
    T = load_tune()
    L = ['# v29 Part F: tuning of `EB_first`, `EB_best16` and `EB_best256` (experiments_v29.py f_rule, f1_tune, f1_choose, f2_tune, f2_choose)', ''] + TUNING_RULE
    if not ch:
        return L + ['## Results', '', 'Not run yet.']
    L += ['## Results', '', 'Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P',
          '(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better). DeFT-P scores 0.', '']
    for z in TUNE_SIZES:
        c = ch[z]
        ms = EV28.score(T, MAIN, z)
        if 'EB_first' in c:
            L += ['### %s: F1, `EB_first` (`entry_commit first` with `lut_bias` D)' % z, '', '| D | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|',
                  '| `%s` (frozen, not tuned here) | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | |' % (MAIN, ms[0], pct(ms[1]), pct(ms[2]), pct(ms[3])),
                  '| DeFT_P (D = infinity) | 0 | 0 | 0 | 0 | |']
            for D in c['grids']['EB_first']:
                s = EV28.score(T, f1_name(D), z)
                note = (['**EB_first**'] if D == c['EB_first']['D'] else []) + (['extension'] if D not in F1_GRID else [])
                L.append('| %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (fmt(D), s[0], pct(s[1]), pct(s[2]), pct(s[3]), ', '.join(note)))
            L.append('')
        for per in F2_PERIODS:
            row = 'EB_best%d' % per
            if row not in c:
                continue
            b = EV28.choice()[z]['EB_best']
            L += ['### %s: F2, `%s` (S %s, P %d, B %s of `EB_best`, `oracle_period %d`)' % (z, row, b['S'], b['P'], fmt(b['B']), per), '',
                  '| T | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|']
            for t in c['grids'][row]:
                s = EV28.score(T, f2_name(z, per, t), z)
                note = (['**%s**' % row] if t == c[row]['T'] else []) + (['extension'] if t not in F2_GRID else [])
                L.append('| %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (fmt(t), s[0], pct(s[1]), pct(s[2]), pct(s[3]), ', '.join(note)))
            L.append('')
        named = [('main row', MAIN)] + ([('`EB_first`', f1_name(c['EB_first']['D']))] if 'EB_first' in c else []) + [
            ('`EB_best%d`' % per, f2_name(z, per, c['EB_best%d' % per]['T'])) for per in F2_PERIODS if 'EB_best%d' % per in c]
        scen = [(p, m) for p, m in X24.scenarios(z)]
        L += ['### %s: the chosen rows by scenario' % z, '', 'Score of the scenario (mean over the two seeds) and, in brackets, THR and LAT1.0 against DeFT-P.', '',
              '| row | configuration | ' + ' | '.join(X25.sname(z, p, m) for p, m in scen) + ' |', '|---|---|' + '---|' * len(scen)]
        for label, n in named:
            bs = EV28.score_by_scenario(T, n, z)
            L.append('| %s | `%s` | %s |' % (label, n, ' | '.join('%+.3f (%+.1f / %+.1f)' % (bs[sc][0], pct(bs[sc][1]), pct(bs[sc][2])) for sc in scen)))
        L.append('')
    L += ['## Chosen configurations', '', '| size | `EB_first`: lut_bias (score) | `EB_best16`: T (score) | `EB_best256`: T (score) | main row (score) |', '|---|---|---|---|---|']
    for z in SIZES:
        c = ch[z]

        def cell(row, key):
            return '%s (%.4f)' % (fmt(c[row][key]), c[row]['score']) if row in c else 'not tuned'
        L.append('| %s%s | %s | %s | %s | %.4f |' % (z, ' (the 4x4 choice)' if z == '3x3' else '', cell('EB_first', 'D'), cell('EB_best16', 'T'), cell('EB_best256', 'T'), c['main']['score']))
    below = ['%s %s' % (z, r) for z in TUNE_SIZES for r in ('EB_first', 'EB_best16', 'EB_best256') if r in ch[z] and ch[z][r]['below_zero']]
    L += ['', 'Chosen configurations with a score below 0 (DeFT_P is then the best member of the family): %s.' % (', '.join(below) if below else 'none')]
    for k in ('repro', 'multi'):
        if k in ch.get('notes', {}):
            L.append(ch['notes'][k])
    L.append('Per-run values: `tune_first_runs.csv` (F1, with DeFT-P and the main row) and `tune_age_runs.csv` (F2).')
    return L


def tune_finish(stage, out_csv):
    """Per-run CSV of a tuning raw folder; the raw folder is deleted. Returns the hops of the EB runs that offer more than one output."""
    raw = X.raw(stage)
    if not os.path.isdir(raw):
        return 0
    multi = 0
    for f in glob.glob(os.path.join(raw, '*.json')):
        if os.path.basename(f).split('__')[1].startswith('EB'):
            multi += R.multi_hops(json.load(open(f)))
    n = R.to_csv(raw, out_csv)
    if n == len(glob.glob(os.path.join(raw, '*.json'))) and multi == 0:
        shutil.rmtree(raw)
    return multi


def f1_choose():
    st = load_state(STATE1, None)
    T = load_tune()
    ch = json.load(open(R.CHOICE)) if os.path.exists(R.CHOICE) else {}
    for z in TUNE_SIZES:
        i, sc = best_of(T, [f1_name(D) for D in st[z]], z)
        c = ch.setdefault(z, {})
        c['EB_first'] = dict(D=st[z][i], name=f1_name(st[z][i]), score=sc[i][0], below_zero=sc[i][0] < 0)
        c['main'] = dict(score=EV28.score(T, MAIN, z)[0])
        c.setdefault('grids', {})['EB_first'] = list(st[z])
    ch['3x3'] = json.loads(json.dumps(ch['4x4']))
    # DeFT-P and the main row of this round's tuning runs against the rows of round 27 (every column of that file, as text)
    tmp = os.path.join(X.RAW, 'tune1_check.csv')
    same = total = 0
    if os.path.isdir(X.raw('tune1')):
        EV27_cols = list(csv.DictReader(open(V27_TUNE)).fieldnames)
        R.to_csv(X.raw('tune1'), tmp)
        old = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(V27_TUNE))}
        for r in csv.DictReader(open(tmp)):
            if r['variant'][:-3] in ('DeFT_P', MAIN):
                total += 1
                o = old.get((r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
                same += o is not None and all(o[c] == r[c] for c in EV27_cols)
        os.remove(tmp)
        ch.setdefault('notes', {})['repro'] = ('DeFT-P and the main row on the tuning cells, run again with the build of this round, against the rows of '
                                             '`results_v27_early/tune_runs.csv` (every column, as text): **%d / %d identical.**' % (same, total))
    multi = tune_finish('tune1', CSV1)
    ch.setdefault('notes', {})['multi'] = 'Hops of the tuning runs of the early rows that offer more than one output after the commit (must be 0): %d.' % multi
    json.dump(ch, open(R.CHOICE, 'w'), indent=1)
    wmd('tuning_v29.md', tuning_md(ch))
    return multi == 0 and same == total


def f2_choose():
    if 'F2' in drops():
        print('F2 is dropped by the time rule')
        return True
    st = load_state(STATE2, None)
    T = load_tune()
    ch = json.load(open(R.CHOICE))
    for z in TUNE_SIZES:
        for per in F2_PERIODS:
            g = st[z][str(per)]
            i, sc = best_of(T, [f2_name(z, per, t) for t in g], z)
            ch[z]['EB_best%d' % per] = dict(T=g[i], name=f2_name(z, per, g[i]), score=sc[i][0], below_zero=sc[i][0] < 0)
            ch[z]['grids']['EB_best%d' % per] = list(g)
    notes = ch.get('notes', {})
    ch['3x3'] = json.loads(json.dumps(ch['4x4']))
    multi = tune_finish('tune2', CSV2)
    notes['multi'] = notes.get('multi', '') + ' The same for the tuning runs of F2: %d.' % multi
    ch['notes'] = notes
    json.dump(ch, open(R.CHOICE, 'w'), indent=1)
    wmd('tuning_v29.md', tuning_md(ch))
    return multi == 0


def run_stage(stage, nproc, extra):
    if stage == 'b_sat':
        sys.exit(0 if sat(nproc) else 1)
    elif stage == 'b_points':
        sys.exit(0 if points() else 1)
    elif stage == 't_timing':
        sys.exit(0 if timing(nproc) else 1)
    elif stage == 'f_rule':
        wmd('tuning_v29.md', tuning_md(None))
    elif stage == 'f1_tune':
        sys.exit(0 if f1_tune(nproc) else 1)
    elif stage == 'f1_choose':
        sys.exit(0 if f1_choose() else 1)
    elif stage == 'f2_tune':
        sys.exit(0 if f2_tune(nproc) else 1)
    elif stage == 'f2_choose':
        sys.exit(0 if f2_choose() else 1)
    elif '_' in stage and stage.split('_')[0] in PARTS and stage.split('_')[1] in ('eval', 'check', 'csv'):
        part, what = stage.split('_')
        fn = {'eval': lambda: part_eval(part, nproc), 'check': lambda: part_check(part), 'csv': lambda: part_csv(part)}[what]
        sys.exit(0 if fn() else 1)
    else:
        raise SystemExit(__doc__)
