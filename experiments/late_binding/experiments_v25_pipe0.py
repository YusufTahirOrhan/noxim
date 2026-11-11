"""v25 Part E (descriptive; results_v25_confirm/PREREGISTRATION.md): sensitivity to the router model, -pipe_all 0 (Noxim's
one-cycle router). Run through experiments_v25.py:
  e_eval    uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; three sizes; the nine loads of
            the v23 pipe_all 0 ladders; seeds 141-145 (raw outputs under ~/lbraw/v25/pipe0 until e_csv)
  e_check   integrity of the raw folder
  e_csv     pipe0_runs.csv (raw outputs deleted when complete)
Rows: DeFT_P, DeFT_B, MTR, RC (fault-free), CI_heurLA_X with an ideal decision (decision_delay 0, no lookahead routing) and
CI_heurLA_X_DLY (decision_delay 2), with the frozen selection values of round 24.
"""
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v25 as X  # noqa: E402

RES, SIZES = X.RES, X.SIZES
SEEDS = range(141, 146)
ROWS = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', 'CI_heurLA_X', 'CI_heurLA_X_DLY']
FF_ONLY = ('MTR', 'RC')


def scenarios(size):
    f, n = E5.FREE[size], E5.NORTH[size]
    return [('uniform', f), ('hotspot', f), ('chipperm', f), ('uniform', n)]


def row_scenarios(size, row):
    return [(p, m) for p, m in scenarios(size) if not (row in FF_ONLY and X.faulty(m))]


def eval_jobs(seeds=SEEDS):
    P = X.lp()
    js = []
    for size in SIZES:
        for row in ROWS:
            a = X.row_args(size, row)
            for p, m in row_scenarios(size, row):
                for r in P[X.lkey(size, p, m, 0)]['eval']:
                    js += [X.job('pipe0', size, row, a, 0, p, m, r, seed) for seed in seeds]
    return js


def run_stage(stage, nproc, extra):
    if stage == 'e_eval':
        P = X.lp()
        for size in SIZES:
            for p, m in scenarios(size):
                E5.gen_tables(size, p, P[X.lkey(size, p, m, 0)]['eval'])
        js = eval_jobs()
        print('pipe_all 0 jobs:', len(js), flush=True)
        t = time.time()
        res = run_jobs(js, X.raw('pipe0'), nproc=nproc, timeout=14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'e_check':
        sys.exit(0 if E19.check_raw(X.raw('pipe0'), eval_jobs(), 'eval') else 1)
    elif stage == 'e_csv':
        import experiments_v25_eval as EV
        n = EV.to_csv(X.raw('pipe0'), os.path.join(RES, 'pipe0_runs.csv'), expect=len(eval_jobs()))
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('pipe0'))
    else:
        raise SystemExit(__doc__)
