"""v29 Part F2: a check added after the tuning (results_v29_review/DECISIONS.md, "F2: the T of EB_best256 on 2x2 is the cap of the
rule"). It changes no row of the round and no choice of the tuning.

The rule of tuning_v29.md doubles T up to 128 at most (B2 of round 28). On 2x2 the T it chose for EB_best256 is that 128, and the score
still rises there (T 64: -0.19, T 128: +0.10): a larger T, which the rule does not allow, may serve the early row better. This script
runs the tuning cells of 2x2 with T beyond the cap and, if one of them scores higher than T = 128, the cells of the evaluation of Part F
on 2x2 with that T, as an extra row next to the pre-registered EB_best256.

  python3 extra_v29_age.py tune [NPROC]   2x2, oracle_period 256, T = 256, 512, ... (doubled while the best T is the largest, 4096 at
                                          most): 40 runs per value -> tune_age_extra_runs.csv, tuning_v29_extra.md
  python3 extra_v29_age.py eval [NPROC]   2x2, the T of the largest score, as the row EB_best256x on the cells of Part F (six scenarios,
                                          nine loads, seeds 171-180: 540 runs) -> early_age_extra_runs.csv. Nothing is run if no T beyond
                                          the cap scores higher than T = 128.
Raw outputs under ~/lbraw/v29/tune2x and ~/lbraw/v29/agex until the CSV is written.
"""
import csv
import glob
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v28_eval as EV28  # noqa: E402
import experiments_v29 as X  # noqa: E402
import experiments_v29_eval as EV  # noqa: E402
import experiments_v29_rows as R  # noqa: E402
import make_eval_csv as MK  # noqa: E402

Z, PER, CAP, T_MAX = '2x2', 256, 128.0, 4096.0
ROW = 'EB_best256x'
STATE = os.path.join(X.RAW, 'tune_state_f2x.json')
CSV_T = os.path.join(X.RES, 'tune_age_extra_runs.csv')
CSV_E = os.path.join(X.RES, 'early_age_extra_runs.csv')
MD = 'tuning_v29_extra.md'
fmt, NL = R.fmt, X.NL


def tune_jobs(grid):
    return [R.job('tune2x', Z, EV.f2_name(Z, PER, T), EV.f2_args(Z, PER, T), p, m, rate, seed) for p, m, rate, seed in EV24.tune_cells(Z) for T in grid]


def load():
    """The tuning runs of the round (per-run CSVs) and the runs of this check (raw folder, or its CSV)."""
    T = EV.load_tune()
    if os.path.exists(CSV_T):
        for r in csv.DictReader(open(CSV_T)):
            z, p = r['pattern'].split('-')
            T[(r['variant'][:-3], z, p, r['mask'], float(r['rate']), int(r['seed']))] = (float(r['accepted']), float(r['latency']))
    for f in glob.glob(os.path.join(X.raw('tune2x'), '*.json')):
        (v, sp, m, rate, seed), d = MK.parse(f)
        z, p = sp.split('-')
        T[(v[:-3], z, p, m, rate, seed)] = (d['summary']['average_ip_throughput_flits_per_cycle_per_ip'], d['summary']['global_average_delay_cycles'])
    return T


def scores(T, grid):
    out = []
    for t in grid:
        s = EV28.score(T, EV.f2_name(Z, PER, t), Z)
        if s is None:
            raise SystemExit('missing tuning runs of T = %s' % fmt(t))
        out.append(s)
    return out


def tune(nproc):
    st = json.load(open(STATE)) if os.path.exists(STATE) else [CAP * 2, CAP * 4]
    ch = json.load(open(R.CHOICE))
    base = [t for t in ch[Z]['grids']['EB_best%d' % PER]]
    if ch[Z]['EB_best%d' % PER]['T'] != CAP:
        raise SystemExit('the chosen T of EB_best%d on %s is not the cap; nothing to check' % (PER, Z))
    while True:
        json.dump(st, open(STATE, 'w'))
        js = tune_jobs(st)
        print('%s tuning cells of %s with T in {%s}: %d jobs (finished runs are skipped)' % (time.strftime('%H:%M:%S'), Z, ', '.join(fmt(t) for t in st), len(js)), flush=True)
        res = run_jobs(js, X.raw('tune2x'), nproc=nproc, timeout=14400)
        if any(v is None for v in res.values()):
            raise SystemExit('missing outputs; stop')
        T = load()
        sc = scores(T, base + st)
        best = max(range(len(sc)), key=lambda i: (sc[i][0], i))
        if (base + st)[best] == max(st) and max(st) * 2 <= T_MAX:
            st.append(max(st) * 2)
            print('extension: the best T is the largest; new value %s' % fmt(max(st)), flush=True)
            continue
        break
    grid = base + st
    multi = dead = 0
    for f in glob.glob(os.path.join(X.raw('tune2x'), '*.json')):
        d = json.load(open(f))
        multi += R.multi_hops(d)
        dead += int(d['deft_lb'].get('dead_end_events', 0))
    n = R.to_csv(X.raw('tune2x'), CSV_T)
    by = {t: EV28.score_by_scenario(T, EV.f2_name(Z, PER, t), Z) for t in grid}
    scen = list(by[grid[0]].keys())
    pct = EV.pct
    L = ['# v29 Part F2: T of `EB_best256` on 2x2 beyond the cap of the rule (extra_v29_age.py tune)', '',
         'A check added after the tuning (`DECISIONS.md`). The rule of `tuning_v29.md` doubles T up to 128 at most; on 2x2 it chose T = 128 for `EB_best256`, the largest',
         'value it allows, with the score still rising. The table adds the values beyond the cap on the same 40 tuning cells (five scenarios, four loads, seeds 101 and',
         '102; DeFT-P from `tune_first_runs.csv`). **The pre-registered row stays `EB_best256` with T = 128.** Scores in natural-log units against DeFT-P; T = infinity is',
         'DeFT_P (score 0).', '',
         '| T (`oracle_bias` = 0.5 x T) | score | THR | LAT1.0 | LAT0.5 | ' + ' | '.join('%s%s' % (p, '' if not X25.faulty(m) else '+f') for p, m in scen) + ' | note |',
         '|---|---|---|---|---|' + '---|' * len(scen) + '---|']
    ibest = max(range(len(sc)), key=lambda i: (sc[i][0], i))
    for i, t in enumerate(grid):
        note = []
        if t == CAP:
            note.append('**`EB_best256`** (the choice of the rule)')
        if t > CAP:
            note.append('beyond the cap')
        if i == ibest:
            note.append('the largest score')
        L.append('| %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s | %s |' % (fmt(t), sc[i][0], pct(sc[i][1]), pct(sc[i][2]), pct(sc[i][3]),
                                                                          ' | '.join('%+.3f' % by[t][s][0] for s in scen), '; '.join(note)))
    L += ['', 'Runs of this check: %d (`tune_age_extra_runs.csv`); dead-end events %d; hops that offer more than one output after the commit %d.' % (n, dead, multi), '']
    tb = grid[ibest]
    if tb > CAP:
        L += ['The largest score is at T = %s (%+.4f against %+.4f at T = 128). `extra_v29_age.py eval` runs the cells of the evaluation of Part F on 2x2 with it, as the extra' % (
            fmt(tb), sc[ibest][0], sc[grid.index(CAP)][0]),
              'row `EB_best256x` (`early_age_extra_runs.csv`), reported next to the pre-registered row.', '']
    else:
        L += ['No T beyond the cap scores higher than T = 128: the cap did not bind the choice, and no extra row is run.', '']
    R.wmd(MD, L)
    json.dump(dict(grid=grid, scores=[s[0] for s in sc], best=tb, beyond=tb > CAP, runs=n, dead=dead, multi=multi), open(os.path.join(X.RES, 'tuning_v29_extra.json'), 'w'), indent=1)
    if n == len(glob.glob(os.path.join(X.raw('tune2x'), '*.json'))) and multi == 0 and dead == 0:
        shutil.rmtree(X.raw('tune2x'))
    return multi == 0 and dead == 0


def eval_jobs(tb):
    P = X25.lp()
    a = EV.f2_args(Z, PER, tb)
    js = []
    for p, m in R.ff_scenarios(Z):
        lad = P[X.lkey(Z, p, m, 2)]['eval']
        js += [R.job('agex', Z, ROW, a, p, m, lad[i], s) for i in range(9) for s in EV.SEEDS_28]
    return js


def evaluate(nproc):
    x = json.load(open(os.path.join(X.RES, 'tuning_v29_extra.json')))
    if not x['beyond']:
        print('no T beyond the cap scores higher than T = 128: nothing to run')
        return True
    js = eval_jobs(x['best'])
    print('%s %s on %s with T = %s: %d jobs' % (time.strftime('%H:%M:%S'), ROW, Z, fmt(x['best']), len(js)), flush=True)
    res = run_jobs(js, X.raw('agex'), nproc=nproc, timeout=14400)
    if any(v is None for v in res.values()):
        raise SystemExit('missing outputs; stop')
    full = CSV_E + '.tmp'
    n = R.to_csv(X.raw('agex'), full)
    rows = list(csv.DictReader(open(full)))
    dead = sum(int(r['dead_ends']) for r in rows)
    multi = sum(int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0) for r in rows)
    print('%s: %d rows of %d; dead-end events %d; hops that offer more than one output %d' % (os.path.basename(CSV_E), n, len(js), dead, multi), flush=True)
    ok = n == len(js) and dead == 0 and multi == 0
    if ok:
        os.replace(full, CSV_E)
        shutil.rmtree(X.raw('agex'), ignore_errors=True)
    return ok


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else ''
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    if stage == 'tune':
        sys.exit(0 if tune(nproc) else 1)
    if stage == 'eval':
        sys.exit(0 if evaluate(nproc) else 1)
    print(__doc__)
    sys.exit(2)
