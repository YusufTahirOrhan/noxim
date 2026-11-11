"""v25 Part D (descriptive; results_v25_confirm/PREREGISTRATION.md): application traces on the 2x2 system, pipe_all 2.
Run through experiments_v25.py:
  d_eval    the v13 protocol (nine PARSEC traces through Netrace, one application) and the v15 protocol (the six pairs of the four
            heaviest traces, compression 1 and 2), fault-free and with mask 0x1111, seeds 41-43 (extra: single | pair | all)
  d_check   every run finished and delivered its whole window
  d_csv     app_runs.csv and pair_runs.csv (raw outputs deleted when complete)
Rows: DeFT_P, DeFT_B, MTR, RC (fault-free only), CI_heurLA_X_LF, CI_heurLA_O_LF. Trace windows: the first 700,000 cycles of region 2
(results_v13_apps/window.json), dependency mode, 2- and 18-flit packets. Windows under /mnt/d/netrace_v13/windows (not in git).
"""
import csv
import glob
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import experiments_v13 as E13  # noqa: E402
import experiments_v15 as E15  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v25 as X  # noqa: E402

RES, NL = X.RES, X.NL
ROWS = ['DeFT_P', 'DeFT_B', 'MTR', 'RC', X.MAIN, X.SECOND]
FF_ONLY = ('MTR', 'RC')
MASKS = ['0x0000', '0x1111']
SEEDS = (41, 42, 43)
WINDOW = 700000
S_VALUES = (1, 2)
Z = '2x2'


def cells():
    return [(row, m) for m in MASKS for row in ROWS if not (row in FF_ONLY and m != '0x0000')]


def base_args(row, m, seed):
    return common_args(seed, m, lut=X23.lut23(Z, m)) + X.row_args(Z, row) + X23.pipe(2) + X24.TRNG


def trace(b):
    return os.path.join(E13.WIN_DIR, '%s_r2.txt' % b)


TAIL = ['-warmup', '0', '-sim', str(E13.SIM_LIMIT), '-size', '2', '18']


def single_jobs():
    js = []
    for b in E13.BENCH:
        for row, m in cells():
            for seed in SEEDS:
                a = base_args(row, m, seed) + ['-netrace', trace(b), '-netrace_window', str(WINDOW), '-netrace_deps', '1'] + TAIL
                js.append(('app__%s__%s__%s__s%d' % (row, b, m, seed), a))
    return js


def pair_jobs():
    js = []
    for s in S_VALUES:
        for a1, a2 in E15.PAIRS:
            for row, m in cells():
                for seed in SEEDS:
                    a = base_args(row, m, seed) + ['-netrace', trace(a1), '-netrace2', trace(a2), '-netrace_window', str(WINDOW), '-netrace_deps', '1',
                                                  '-netrace_compress', str(s)] + TAIL
                    js.append(('pair__%s__%s+%s__%s__s%d__seed%d' % (row, E15.short(a1), E15.short(a2), m, s, seed), a))
    return js


def make_csv():
    rows = []
    for f in sorted(glob.glob(os.path.join(X.raw('app'), 'app__*.json'))):
        _, v, b, m, s = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        cyc = l['netrace_completion_cycle']
        rows.append(dict(benchmark=b, method=v, mask=m, seed=int(s[1:]), latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         max_delay=repr(su['max_delay_cycles']), packets=l['netrace_packets'], injected=l['netrace_injected'], delivered=l['netrace_delivered'],
                         self_packets=l['netrace_self_packets'], waited=l['netrace_waited_for_dependencies'], finished=l['netrace_finished'],
                         completion_cycles=cyc, window_cycles=l['netrace_window_cycles'], dead_ends=l['dead_end_events'], received_flits=su['total_received_flits'],
                         offered_flits_per_node_cycle=repr(su['total_received_flits'] / 64.0 / max(cyc, 1))))
    prs = []
    for f in sorted(glob.glob(os.path.join(X.raw('app'), 'pair__*.json'))):
        _, v, pair, m, s, seed = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        cyc = l['netrace_completion_cycle']
        prs.append(dict(pair=pair, method=v, mask=m, s=int(s[1:]), seed=int(seed[4:]), latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                        completion_cycles=cyc, app1_completion=l['netrace1_completion_cycle'], app2_completion=l['netrace2_completion_cycle'],
                        app1_latency=repr(l['netrace1_latency_mean']), app2_latency=repr(l['netrace2_latency_mean']),
                        packets=l['netrace_packets'] + l['netrace2_packets'], injected=l['netrace_injected'] + l['netrace2_injected'],
                        delivered=l['netrace_delivered'] + l['netrace2_delivered'], finished=l['netrace_finished'], received_flits=su['total_received_flits'],
                        offered_flits_per_node_cycle=repr(su['total_received_flits'] / 64.0 / max(cyc, 1)), dead_ends=l['dead_end_events']))
    for fn, rr in (('app_runs.csv', rows), ('pair_runs.csv', prs)):
        if rr:
            with open(os.path.join(RES, fn), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rr[0]), lineterminator=NL)
                w.writeheader()
                w.writerows(rr)
    bad = [r for r in rows + prs if r['finished'] is not True or r['injected'] != r['delivered'] or r['dead_ends'] != 0]
    print('app_runs.csv: %d rows (expected %d); pair_runs.csv: %d rows (expected %d); not finished, not drained or with dead ends: %d' % (
        len(rows), len(single_jobs()), len(prs), len(pair_jobs()), len(bad)))
    for r in bad[:20]:
        print('  ', r.get('benchmark', r.get('pair')), r['method'], r['mask'], r['seed'])
    return len(rows) == len(single_jobs()) and len(prs) == len(pair_jobs()), bad


def run_stage(stage, nproc, extra):
    if stage == 'd_eval':
        js = (single_jobs() if extra in (None, 'all', 'single') else []) + (pair_jobs() if extra in (None, 'all', 'pair') else [])
        print('trace jobs:', len(js), flush=True)
        t = time.time()
        res = run_jobs(js, X.raw('app'), nproc=nproc, timeout=12 * 3600)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'd_check':
        have = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(X.raw('app'), '*.json'))}
        want = {n for n, _ in single_jobs() + pair_jobs()}
        print('trace runs: wanted %d, complete %d, missing %d, not in the list %d' % (len(want), len(have & want), len(want - have), len(have - want)))
        sys.exit(0 if want <= have else 1)
    elif stage == 'd_csv':
        complete, bad = make_csv()
        if complete and not bad:
            shutil.rmtree(X.raw('app'))
        sys.exit(0 if complete and not bad else 1)
    else:
        raise SystemExit(__doc__)
