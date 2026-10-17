"""Aggregate fixed-window results (mean and 95 % t-confidence intervals over seeds).

Usage: python3 analyze.py STAGE        (STAGE = sat | tune | eval)
Writes results/<stage>_runs.csv (one row per run) and results/<stage>_agg.csv.
Accepted throughput is in flits/node/cycle (Noxim average IP throughput);
offered load = 8 * rate (packet size 8 flits).
"""
import collections
import csv
import glob
import json
import math
import os
import sys

from scipy import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))


def load_runs(stage):
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, 'results', f'{stage}_raw', '*.json'))):
        name = os.path.basename(f)[:-5]
        _, variant, pat, mask, rate, seed = name.split('__')
        try:
            d = json.load(open(f))
        except Exception:
            continue
        s, l = d['summary'], d['deft_lb']
        rows.append(dict(variant=variant, pattern=pat, mask=mask, rate=float(rate), seed=int(seed[1:]),
                         offered=8 * float(rate),
                         latency=s['global_average_delay_cycles'],
                         p99=l['delay_p99'],
                         accepted=s['average_ip_throughput_flits_per_cycle_per_ip'],
                         injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'],
                         lat_inter=l['delay_inter_mean'], lat_intra=l['delay_intra_mean'],
                         vl_down=l['vl_down_packets'], vl_up=l['vl_up_packets']))
    return rows


def ci95(xs):
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, float('nan')
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, st.t.ppf(0.975, n - 1) * sd / math.sqrt(n)


def aggregate(rows):
    g = collections.defaultdict(list)
    for r in rows:
        g[(r['variant'], r['pattern'], r['mask'], r['rate'])].append(r)
    out = []
    for k, rs in sorted(g.items()):
        rec = dict(variant=k[0], pattern=k[1], mask=k[2], rate=k[3], offered=8 * k[3], n=len(rs))
        for key in ('latency', 'p99', 'accepted', 'lat_inter', 'lat_intra'):
            m, h = ci95([r[key] for r in rs])
            rec[key] = m
            rec[key + '_ci'] = h
        rec['dead_ends'] = sum(r['dead_ends'] for r in rs)
        out.append(rec)
    return out


def write_csv(path, rows, cols):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == '__main__':
    stage = sys.argv[1]
    runs = load_runs(stage)
    write_csv(os.path.join(HERE, 'results', f'{stage}_runs.csv'), runs,
              ['variant', 'pattern', 'mask', 'rate', 'offered', 'seed', 'latency', 'p99', 'accepted',
               'injected', 'received', 'dead_ends', 'lat_inter', 'lat_intra'])
    agg = aggregate(runs)
    write_csv(os.path.join(HERE, 'results', f'{stage}_agg.csv'), agg,
              ['variant', 'pattern', 'mask', 'rate', 'offered', 'n', 'latency', 'latency_ci', 'p99', 'p99_ci',
               'accepted', 'accepted_ci', 'lat_inter', 'lat_intra', 'dead_ends'])
    print(stage, 'runs', len(runs), 'cells', len(agg), 'dead-end events', sum(r['dead_ends'] for r in runs))
