"""Per-run CSV of an evaluation from its raw Noxim JSON outputs.

One row per run: variant, pattern, mask, rate, offered, seed, accepted throughput, mean
latency, p99, injected, received, dead ends, VL imbalance. Floats are written with repr()
so that the CSV round-trips the JSON values exactly. Plain DEFT routing does not count VL
usage; for DeFT and DeFT_tm the VL imbalance comes from the traffic-identical DEFT_LB proxy
runs (<stage>vl_raw), and the row records this in vl_source (and checks the identity).
VL imbalance = max / mean of the per-VL packet count (down + up) over the functional VLs.
Usage: python3 make_eval_csv.py RESULTS_DIR [STAGE]   e.g. results_v2 eval -> results_v2/eval_runs.csv
"""
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ['variant', 'pattern', 'mask', 'rate', 'offered', 'seed', 'accepted', 'latency', 'p99', 'injected',
        'received', 'dead_ends', 'vl_imbalance', 'vl_source']


def parse(path):
    _, v, p, m, rate, seed = os.path.basename(path)[:-5].split('__')
    d = json.load(open(path))
    return (v, p, m, float(rate), int(seed[1:])), d


def imbalance(mask, down, up):
    faulty = int(mask, 16)
    c = [down[v] + up[v] for v in range(16) if not faulty >> v & 1]
    mu = sum(c) / len(c)
    return max(c) / mu if mu > 0 else float('nan')


def main():
    res = os.path.join(HERE, sys.argv[1])
    stage = sys.argv[2] if len(sys.argv) > 2 else 'eval'
    proxy = {}
    for f in glob.glob(os.path.join(res, f'{stage}vl_raw', '*.json')):
        key, d = parse(f)
        proxy[key] = d
    rows, mism = [], 0
    for f in sorted(glob.glob(os.path.join(res, f'{stage}_raw', '*.json'))):
        (v, p, m, rate, seed), d = parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up, src = l['vl_down_packets'], l['vl_up_packets'], 'run'
        if not any(down):
            pr = proxy.get((v, p, m, rate, seed))
            if pr is not None:
                ps = pr['summary']
                if (ps['global_average_delay_cycles'], pr['deft_lb']['delay_p99'], ps['total_received_packets']) != \
                        (s['global_average_delay_cycles'], l['delay_p99'], s['total_received_packets']):
                    mism += 1
                down, up, src = pr['deft_lb']['vl_down_packets'], pr['deft_lb']['vl_up_packets'], 'proxy'
            else:
                src = 'none'
        rows.append(dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed,
                         accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']),
                         latency=repr(s['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'],
                         vl_imbalance=repr(imbalance(m, down, up)) if src != 'none' else '', vl_source=src))
    out = os.path.join(res, f'{stage}_runs.csv')
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'{out}: {len(rows)} rows; proxy rows {sum(r["vl_source"] == "proxy" for r in rows)}; '
          f'proxy/run mismatches {mism}; rows without VL counts {sum(r["vl_source"] == "none" for r in rows)}')


if __name__ == '__main__':
    main()
