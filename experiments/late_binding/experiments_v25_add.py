"""v25 addendum (results_v25_confirm/PREREGISTRATION_addendum.md): the main row with one residual cycle.

  python3 experiments_v25_add.py drain [N]    drain tests of the row (the A4 protocol) -> drain_summary_addendum.csv
  python3 experiments_v25_add.py eval [N]     the row on the Part B design: 8 scenarios x 3 sizes x 9 loads x seeds 121-130 = 2,160 runs
  python3 experiments_v25_add.py check        integrity of the raw folder
  python3 experiments_v25_add.py csv          addendum_runs.csv (raw outputs deleted when complete)

Row `CI_heurLA_X_LF1`: `CI_heurLA_X_LF` argument for argument, with `-deft_lb decision_delay 1` in place of `decision_delay 0`
(a head with more than one offered output waits one cycle more at every router; the stored decision and the fallback are unchanged).
Nothing else differs from Part B: the same binary, ladders, traffic tables, seeds and options. The references it is compared with are
the Part B runs in eval_runs.csv.
"""
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v19 as E19  # noqa: E402
import experiments_v25 as X  # noqa: E402
import experiments_v25_eval as EV  # noqa: E402
from runner import run_jobs  # noqa: E402

RES, SIZES = X.RES, X.SIZES
ROW = 'CI_heurLA_X_LF1'


def row_args(size):
    a = list(X.row_args(size, X.MAIN))
    k = [i for i in range(len(a) - 2) if a[i] == '-deft_lb' and a[i + 1] == 'decision_delay']
    assert len(k) == 1 and a[k[0] + 2] == '0', a          # the main row carries its residual delay explicitly, as 0
    a[k[0] + 2] = '1'
    return a


def eval_jobs():
    P = X.lp()
    js = []
    for size in SIZES:
        a = row_args(size)
        for p, m in X.scenarios(size):
            lad = P[X.lkey(size, p, m)]['eval']
            for i in range(9):
                js += [X.job('aeval', size, ROW, a, 2, p, m, lad[i], seed) for seed in EV.SEEDS]
    return js


def drain(nproc):
    """The A4 protocol (experiments_v25.drain_jobs) for the one row, at pipe_all 2."""
    X.drain_cfgs = lambda size: [('%s-p2' % ROW, row_args(size), 2)]
    js = X.drain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    res = run_jobs(js, X.raw('adrain'), nproc=nproc, timeout=14400)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_summary_addendum.csv'))
    if not fails:
        shutil.rmtree(X.raw('adrain'))
    return not fails


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    if stage == 'args':
        for z in SIZES:
            print(z, ' '.join(row_args(z)))
            print(z, 'main:', ' '.join(X.row_args(z, X.MAIN)))
        print('jobs', len(eval_jobs()), eval_jobs()[0][0])
    elif stage == 'drain':
        sys.exit(0 if drain(nproc) else 1)
    elif stage == 'eval':
        EV.ensure_tables()
        js = eval_jobs()
        print('addendum jobs:', len(js), flush=True)
        t = time.time()
        res = run_jobs(js, X.raw('aeval'), nproc=nproc, timeout=14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'check':
        sys.exit(0 if E19.check_raw(X.raw('aeval'), eval_jobs(), 'eval') else 1)
    elif stage == 'csv':
        n = EV.to_csv(X.raw('aeval'), os.path.join(RES, 'addendum_runs.csv'), expect=len(eval_jobs()))
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('aeval'))
        sys.exit(0 if n == len(eval_jobs()) else 1)
    else:
        raise SystemExit(__doc__)
