"""Drain-mode correctness tests for every variant (no performance meaning).

Pass criterion per run: drain_stop_reason == drain_completed, every measured
packet received, and zero DEFT_LB dead-end events.
Workloads: all-pairs burst (4032 packets) on 11 fault masks x 2 seeds, and
over-saturated random tables (uniform / chipperm / hotspot at 0.03
packets/cycle/source, sources cut off after 3000 cycles) on 4 masks.
Usage: python3 drain_tests.py [nproc]
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
from variants import VARIANTS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'drain_raw')
REL = '../experiments/late_binding/'
MASKS = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
TABLE_MASKS = ['0x0000', '0x1111', '0x9C63', '0x7BDE']


def jobs():
    js = []
    for v, va in VARIANTS.items():
        for m in MASKS:
            for seed in (1, 2):
                a = common_args(seed, m, hardcoded=REL + 'traffic/allpairs_burst.txt') + va + \
                    ['-drain_mode', '-drain_source_cutoff', '100', '-drain_timeout', '60000',
                     '-warmup', '0', '-sim', '80000']
                js.append((f'allpairs__{v}__{m}__s{seed}', a))
        for m in TABLE_MASKS:
            for pat in ('uniform', 'chipperm', 'hotspot'):
                a = common_args(1, m, traffic=REL + f'traffic/{pat}_0.0300.txt') + va + \
                    ['-drain_mode', '-drain_source_cutoff', '3000', '-drain_timeout', '100000',
                     '-warmup', '1000', '-sim', '120000']
                js.append((f'{pat}0.03__{v}__{m}__s1', a))
    return js


if __name__ == '__main__':
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    res = run_jobs(jobs(), OUT, nproc=nproc, timeout=3600)
    rows, fails = [], 0
    for name in sorted(res):
        d = res[name]
        wl, v, m, seed = name.split('__')
        if d is None:
            rows.append([wl, v, m, seed, 'NO_OUTPUT', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        ok = (s.get('drain_stop_reason') == 'drain_completed' and
              s['measured_received_packets'] == s['measured_injected_packets'] and
              l['dead_end_events'] == 0)
        fails += not ok
        rows.append([wl, v, m, seed, s.get('drain_stop_reason'), s['measured_injected_packets'],
                     s['measured_received_packets'], l['dead_end_events'], s.get('drain_completed_cycle'),
                     'PASS' if ok else 'FAIL'])
    with open(os.path.join(HERE, 'results', 'drain_summary.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['workload', 'variant', 'mask', 'seed', 'stop_reason', 'injected', 'received',
                    'dead_end_events', 'drain_completed_cycle', 'result'])
        w.writerows(rows)
    print(f'runs={len(rows)} failures={fails}')
