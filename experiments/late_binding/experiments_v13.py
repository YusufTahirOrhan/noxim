"""v13 (Part E): PARSEC application traces (Netrace) on the 2x2 system (results_v13_apps/).

Stages (python3 experiments_v13.py STAGE [nproc]; --shard i/n accepted):
  timing   timing test (first 200000 packets of each benchmark, DeFT and FULL_qlLA_G, seed 1001) and choice of the
           window: the largest N (packets of region 2, at most 3000000, a multiple of 100000) for which the whole part
           is estimated to take <= 8 h -> window.json
  eval     all methods of Part B, fault-free and (fault-tolerant methods) VL mask 0x1111, seeds 41-43
  csv      per-run CSV (results_v13_apps/app_runs.csv); raw outputs deleted
Design: APPS_DESIGN.md, PREREGISTRATION.md. Trace windows: D:/netrace_v13/windows/<benchmark>_r2.txt (not in git).
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
import experiments_v10 as E10  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v13_apps')
WIN_DIR = '/mnt/d/netrace_v13/windows'
BENCH = ['blackscholes_64c_simsmall', 'bodytrack_64c_simlarge', 'canneal_64c_simmedium', 'dedup_64c_simmedium',
         'fluidanimate_64c_simsmall', 'swaptions_64c_simlarge', 'ferret_64c_simmedium', 'vips_64c_simmedium',
         'x264_64c_simsmall']
METHODS = ['DeFT', 'MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
FAULTY_OK = ['DeFT', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
MASKS = ['0x0000', '0x1111']
SEEDS = (41, 42, 43)
BUDGET_H = 8.0
SIM_LIMIT = 400000000      # cycles; a run stops earlier when its window is delivered


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def window_cycles(bench, n_packets):
    """Cycle bound of the first n_packets packets of region 2 (region start from the header line)."""
    path = os.path.join(WIN_DIR, f'{bench}_r2.txt')
    with open(path) as f:
        head = f.readline().split()
        start = int(head[4])
        k, last = 0, start
        for line in f:
            k += 1
            if k == n_packets:
                last = int(line.split(' ', 1)[0])
                break
    return last - start + 1


def cells():
    return [(b, v, m) for b in BENCH for m in MASKS for v in (METHODS if m == '0x0000' else FAULTY_OK)]


def job(stage, bench, v, m, seed, wcycles):
    a = common_args(seed, m, lut=E10.lut('2x2', v, 'uniform')) + E10.methods('2x2')[v] + \
        ['-netrace', os.path.join(WIN_DIR, f'{bench}_r2.txt'), '-netrace_window', str(wcycles), '-netrace_deps', '1',
         '-warmup', '0', '-sim', str(SIM_LIMIT), '-size', '2', '18']
    return f'{stage}__{v}__{bench}__{m}__s{seed}', a


def timing(nproc):
    n_test = 200000
    js = []
    for b in BENCH:
        w = window_cycles(b, n_test)
        js += [job('timing', b, v, '0x0000', 1001, w) for v in ('DeFT', 'FULL_qlLA_G')]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=14400)
    el = time.time() - t
    # cost model: simulated cycles dominate; seconds per simulated cycle from the test
    per = {}
    for (n, _), b in zip(js[::2], BENCH):
        cyc = [res[x]['deft_lb']['netrace_completion_cycle'] for x in (n, n.replace('DeFT', 'FULL_qlLA_G', 1))
               if res.get(x)]
        per[b] = sum(cyc) / len(cyc) if cyc else float('nan')
    total_cycles_test = sum(per.values())
    sec_per_cycle = el * nproc / (2 * total_cycles_test)     # cpu-seconds per simulated cycle (per run)
    runs_per_bench = len([c for c in cells() if c[0] == BENCH[0]]) * len(SEEDS)
    choice = 100000
    for n in range(100000, 3000001, 100000):
        cyc = sum(window_cycles(b, n) * per[b] / window_cycles(b, n_test) for b in BENCH)
        est_h = cyc * runs_per_bench * sec_per_cycle / nproc / 3600
        if est_h <= BUDGET_H:
            choice = n
        else:
            break
    wins = {b: window_cycles(b, choice) for b in BENCH}
    cyc = sum(wins[b] * per[b] / window_cycles(b, n_test) for b in BENCH)
    est_h = cyc * runs_per_bench * sec_per_cycle / nproc / 3600
    json.dump({'n_packets': choice, 'window_cycles': wins, 'estimate_h': round(est_h, 2)},
              open(os.path.join(RES, 'window.json'), 'w'), indent=1)
    L = ['# Run-time estimate and trace window (v13)', '',
         f'Timing test: first {n_test} packets of region 2 of each benchmark, DeFT(rho*) and FULL_qlLA_G, seed 1001, '
         f'{nproc} processes: {el:.0f} s wall; {sec_per_cycle * 1e6:.2f} cpu-us per simulated cycle.', '',
         f'Rule: the largest window N (packets, multiple of 100000, at most 3000000) whose estimated total time '
         f'({len(cells()) * len(SEEDS)} runs) is <= {BUDGET_H:.0f} h.', '',
         f'**Window: the first {choice} packets of region 2** (estimated {est_h:.1f} h).', '',
         '| benchmark | window cycles | completion cycles in the test (mean of 2 methods) |', '|---|---|---|']
    L += [f'| {b} | {wins[b]} | {per[b]:.0f} |' for b in BENCH]
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('timing'))


def eval_jobs():
    w = json.load(open(os.path.join(RES, 'window.json')))['window_cycles']
    return [job('app', b, v, m, s, w[b]) for b, v, m in cells() for s in SEEDS]


def make_csv():
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('app'), '*.json'))):
        _, v, b, m, s = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        rows.append(dict(benchmark=b, method=v, mask=m, seed=int(s[1:]),
                         latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         max_delay=repr(su['max_delay_cycles']), packets=l['netrace_packets'],
                         injected=l['netrace_injected'], delivered=l['netrace_delivered'],
                         self_packets=l['netrace_self_packets'], waited=l['netrace_waited_for_dependencies'],
                         finished=l['netrace_finished'], completion_cycles=l['netrace_completion_cycle'],
                         window_cycles=l['netrace_window_cycles'], dead_ends=l['dead_end_events'],
                         total_energy_j=repr(su['total_energy_j']), received_flits=su['total_received_flits']))
    with open(os.path.join(RES, 'app_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r['finished'] is not True or r['injected'] != r['delivered']]
    print(f'app_runs.csv: {len(rows)} rows; runs not finished or not drained: {len(bad)}')
    return rows, bad


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'eval':
        js = eval_jobs()
        print('app jobs:', len(js), flush=True)
        res = run_jobs(js, raw('app'), nproc=nproc, timeout=6 * 3600)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
        sys.exit(0)
    if stage == 'csv':
        rows, bad = make_csv()
        sys.exit(1 if bad else 0)
    raise SystemExit('unknown stage')
