"""v20 (Part L): decision-delay sensitivity (results_v20_delay/).

Stages (python3 experiments_v20.py STAGE [nproc]; --shard i/n accepted):
  drain    drain tests of the 3 variants with -deft_vn_rr 1 -deft_lb decision_delay 4 (v10 protocol and masks) -> drain_summary.csv
  eval     CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G with -deft_vn_rr 1 at N = 1, 2, 4: all sizes, the K4 load points, uniform, hotspot and chipperm fault-free, uniform with
           one faulty VL per chiplet, seeds 61-65
  csv      delay_runs.csv; raw outputs deleted
N = 0 and the DeFT(rho*) reference come from results_v19_vnrr/eval_runs.csv (same binary, seeds, loads).
"""
import csv
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v20_delay')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v20')
SIZES = ['2x2', '3x3', '4x4']
VARIANTS = ['CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
DELAYS = (1, 2, 4)
SEEDS = range(61, 66)
NL = chr(10)


def scenarios(z):
    return [('uniform', E5.FREE[z]), ('hotspot', E5.FREE[z]), ('chipperm', E5.FREE[z]), ('uniform', E5.NORTH[z])]


def delay_args(n):
    return E19.RR + ['-deft_lb', 'decision_delay', str(n)]


def eval_jobs():
    P = E19.lp()
    js = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            for n in DELAYS:
                a0 = list(mm[v]) + delay_args(n)
                for p, m in scenarios(z):
                    for r in P[E5.key(z, p, m)]['eval']:
                        js += [E5.job('delay', z, f'{v}-N{n}', a0, p, m, r, s, E10.lut(z, v, p)) for s in SEEDS]
    return js


def to_csv():
    import make_eval_csv as MK
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, 'eval', '*.json'))):
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        var, n = v.rsplit('-N', 1)
        rows.append(dict(variant=var, delay=int(n), pattern=p, mask=m, rate=repr(rate), seed=seed, accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']),
                         latency=repr(s['global_average_delay_cycles']), p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'], hops_chip=l['hops_chip'], hops_chip_multi=l['hops_chip_multi'], hops_ipos=l['hops_ipos'], hops_ipos_multi=l['hops_ipos_multi']))
    with open(os.path.join(RES, 'delay_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(f'delay_runs.csv: {len(rows)} rows; dead ends {sum(r["dead_ends"] for r in rows)}')
    return len(rows)


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'drain':
        d = os.path.join(RAW, 'drain')
        res = run_jobs(E19.drain_jobs(methods=VARIANTS, extra=delay_args(4)), d, nproc=nproc, timeout=14400)
        fails = E19.drain_report(res, os.path.join(RES, 'drain_summary.csv'))
        if not fails:
            shutil.rmtree(d)
        sys.exit(1 if fails else 0)
    elif stage == 'eval':
        js = eval_jobs()
        print('delay jobs:', len(js), flush=True)
        res = run_jobs(js, os.path.join(RAW, 'eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'csv':
        n = to_csv()
        if n == len(eval_jobs()):
            shutil.rmtree(os.path.join(RAW, 'eval'))
    else:
        raise SystemExit(__doc__)
