"""v29 Part G (optional, descriptive; results_v29_review/PREREGISTRATION.md): application traces that load the network. Run through
experiments_v29.py:
  g_find    DeFT_P on each of the nine PARSEC traces of round 25 (one application, 2x2, pipe_all 2, the first 700,000 cycles of region 2,
            dependency mode, 2- and 18-flit packets) with -netrace_compress S for S in 1, 2, 4, 8, 16, 32 (seed 41): the smallest S in
            {2, ..., 32} at which its mean latency is at least 1.5 times its latency at S = 1 -> trace_compress.json, trace_compress.md.
            The S = 1 runs are compared with the rows of results_v25_confirm/app_runs.csv (the trace path of the reuse check).
  g_eval    at that S, per trace: DeFT_P, MTR, RC and the main row, seeds 41-43 (the seeds of the trace runs of round 25)
  g_csv     trace_runs.csv (raw outputs deleted when complete)
A trace for which no S reaches the factor is not run in g_eval; if none does, g_eval and g_csv do nothing.
Trace windows under /mnt/d/netrace_v13/windows (not in git).
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
import experiments_v13 as E13  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v25_apps as A25  # noqa: E402
import experiments_v29 as X  # noqa: E402

RES, NL, MAIN = X.RES, X.NL, X.MAIN
ROWS = ['DeFT_P', 'MTR', 'RC', MAIN]
S_VALUES = (1, 2, 4, 8, 16, 32)
FACTOR = 1.5
SEEDS = (41, 42, 43)
MASK = '0x0000'
CHOICE = os.path.join(RES, 'trace_compress.json')


def job(row, b, s, seed):
    a = A25.base_args(row, MASK, seed) + ['-netrace', A25.trace(b), '-netrace_window', str(A25.WINDOW), '-netrace_deps', '1'] + (
        ['-netrace_compress', str(s)] if s != 1 else []) + A25.TAIL
    return 'trace__%s__%s__c%d__s%d' % (row, b, s, seed), a


def find_jobs():
    return [job('DeFT_P', b, s, SEEDS[0]) for b in E13.BENCH for s in S_VALUES]


def lat(d):
    return d['summary']['global_average_delay_cycles']


def find(nproc):
    js = find_jobs()
    print('trace jobs (search): %d' % len(js), flush=True)
    t = time.time()
    res = run_jobs(js, X.raw('trace'), nproc=X.width(nproc), timeout=6 * 3600)
    print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    old = {(r['benchmark'], r['method'], r['mask'], r['seed']): r for r in csv.DictReader(open(os.path.join(X25.RES, 'app_runs.csv')))}
    out, same = {}, 0
    L = ['# v29 Part G: the compression at which a trace loads the network (experiments_v29.py g_find)', '',
         'DeFT_P on 2x2, pipe_all 2, one application: the first %d cycles of region 2 of each trace, dependency mode, 2- and 18-flit packets, seed %d (the protocol of the' % (A25.WINDOW, SEEDS[0]),
         'trace runs of round 25), with `-netrace_compress S`: the time stamps of the trace are divided by S. Chosen per trace: the smallest S in {2, 4, 8, 16, 32} at which',
         'the mean latency of DeFT_P is at least %.1f times its latency at S = 1. *Offered*: received flits per node and cycle up to the completion of the window.' % FACTOR,
         'The runs at S = 1 are runs of round 25 made again with the build of this round; *as round 25*: mean latency, p99 and completion cycle equal the row of',
         '`results_v25_confirm/app_runs.csv`.', '',
         '| trace | S = 1: latency (cycles), offered | as round 25 | ' + ' | '.join('S = %d: latency / factor' % s for s in S_VALUES[1:]) + ' | chosen S | offered at the chosen S |',
         '|---|---|---|' + '---|' * (len(S_VALUES) + 1)]
    ok = True
    for b in E13.BENCH:
        d = {s: res.get(job('DeFT_P', b, s, SEEDS[0])[0]) for s in S_VALUES}
        if any(v is None for v in d.values()):
            ok = False
            L.append('| %s | **missing output** | | | | | | | | |' % b)
            continue
        bad = [s for s in S_VALUES if d[s]['deft_lb']['netrace_finished'] is not True or d[s]['deft_lb']['dead_end_events'] != 0]
        ok = ok and not bad
        off = {s: d[s]['summary']['total_received_flits'] / 64.0 / max(d[s]['deft_lb']['netrace_completion_cycle'], 1) for s in S_VALUES}
        o = old.get((b, 'DeFT_P', MASK, str(SEEDS[0])))
        eq = o is not None and o['latency'] == repr(lat(d[1])) and o['p99'] == repr(d[1]['deft_lb']['delay_p99']) and o['completion_cycles'] == str(d[1]['deft_lb']['netrace_completion_cycle'])
        same += eq
        s_ch = next((s for s in S_VALUES[1:] if lat(d[s]) >= FACTOR * lat(d[1])), None)
        out[b] = dict(S=s_ch, latency={str(s): lat(d[s]) for s in S_VALUES}, offered={str(s): off[s] for s in S_VALUES}, same_as_v25=eq)
        L.append('| %s | %.1f, %.4f | %s | %s | %s | %s |%s' % (
            b.split('_')[0], lat(d[1]), off[1], 'yes' if eq else '**no**', ' | '.join('%.1f / %.2f' % (lat(d[s]), lat(d[s]) / lat(d[1])) for s in S_VALUES[1:]),
            s_ch if s_ch else 'none reaches %.1f' % FACTOR, '%.4f' % off[s_ch] if s_ch else '-', (' not finished or dead end at S = %s' % bad) if bad else ''))
    n = sum(1 for v in out.values() if v['S'])
    L += ['', '**Traces with a chosen S: %d of %d.** Runs at S = 1 equal to round 25: %d of %d.%s' % (
        n, len(E13.BENCH), same, len(E13.BENCH), '' if n else ' No S in {2, ..., 32} reaches the factor for any trace: Part G stops here.')]
    json.dump(out, open(CHOICE, 'w'), indent=1)
    open(os.path.join(RES, 'trace_compress.md'), 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok


def eval_jobs():
    ch = json.load(open(CHOICE))
    return [job(row, b, ch[b]['S'], seed) for b in E13.BENCH if ch.get(b, {}).get('S') for row in ROWS for seed in SEEDS]


def make_csv():
    want = {n for n, _ in eval_jobs() + find_jobs()}
    rows = []
    for f in sorted(glob.glob(os.path.join(X.raw('trace'), 'trace__*.json'))):
        name = os.path.basename(f)[:-5]
        if name not in want:
            continue
        _, v, b, c, s = name.split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        cyc = l['netrace_completion_cycle']
        rows.append(dict(benchmark=b, method=v, mask=MASK, compress=int(c[1:]), seed=int(s[1:]), latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         max_delay=repr(su['max_delay_cycles']), packets=l['netrace_packets'], injected=l['netrace_injected'], delivered=l['netrace_delivered'],
                         self_packets=l['netrace_self_packets'], waited=l['netrace_waited_for_dependencies'], finished=l['netrace_finished'],
                         completion_cycles=cyc, window_cycles=l['netrace_window_cycles'], dead_ends=l['dead_end_events'], received_flits=su['total_received_flits'],
                         offered_flits_per_node_cycle=repr(su['total_received_flits'] / 64.0 / max(cyc, 1))))
    with open(os.path.join(RES, 'trace_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r['finished'] is not True or r['injected'] != r['delivered'] or r['dead_ends'] != 0]
    print('trace_runs.csv: %d rows (expected %d); not finished, not drained or with dead ends: %d' % (len(rows), len(want), len(bad)))
    for r in bad[:20]:
        print('  ', r['benchmark'], r['method'], r['compress'], r['seed'])
    return len(rows) == len(want), bad


def run_stage(stage, nproc, extra):
    if stage == 'g_find':
        sys.exit(0 if find(nproc) else 1)
    elif stage == 'g_eval':
        js = eval_jobs()
        print('trace jobs (evaluation): %d' % len(js), flush=True)
        if js:
            t = time.time()
            res = run_jobs(js, X.raw('trace'), nproc=X.width(nproc), timeout=6 * 3600)
            miss = sum(1 for v in res.values() if v is None)
            print('done in %.0f s; missing outputs: %d' % (time.time() - t, miss), flush=True)
            sys.exit(1 if miss else 0)
    elif stage == 'g_csv':
        complete, bad = make_csv()
        if complete and not bad:
            shutil.rmtree(X.raw('trace'))
        sys.exit(0 if complete and not bad else 1)
    else:
        raise SystemExit(__doc__)
