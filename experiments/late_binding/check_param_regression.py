"""Regression of the parametric topology on the default instance (results_v4/regression.md).

Runs the same arguments with the binary built before the parametrisation (4a3b345) and
the new one, and requires identical "summary" and "deft_lb" JSON blocks:
  * fixed-window: all 11 v2 variants x uniform/hotspot/chipperm x masks 0x0000/0x1111 x
    2 loads (2nd and 5th v2 evaluation rates, ~0.5 and ~1.2 x Lsat) x seed 1 (132 runs);
  * drain: all-pairs burst for all 11 variants on 0x0000 (seed 1) and 0x9C63 (seed 2) (22 runs).
DeFT_tm uses the traffic-matched LUT of the pattern (chipperm LUT for the drain runs).
Usage: python3 check_param_regression.py BIN_OLD BIN_NEW
"""
import itertools
import json
import os
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args  # noqa: E402
import variants_v2 as V2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results_v4', 'regression_raw')
REL = '../experiments/late_binding/'
LP = json.load(open(os.path.join(HERE, 'results_v2', 'load_points.json')))
SIM = ['-sim', '10000', '-warmup', '2000']
DRAIN = ['-drain_mode', '-drain_source_cutoff', '100', '-drain_timeout', '60000', '-warmup', '0', '-sim', '80000']


def jobs():
    js = []
    for v, (p, m), i in itertools.product(V2.VARIANTS, [(p, m) for p in ('uniform', 'hotspot', 'chipperm')
                                                         for m in ('0x0000', '0x1111')], (1, 4)):
        rate = LP[f'{p}__{m}']['eval'][i]
        js.append((f'win__{v}__{p}__{m}__{rate:.4f}__s1',
                   common_args(1, m, traffic=REL + f'traffic/{p}_{rate:.4f}.txt', lut=V2.lut_for(v, p))
                   + V2.VARIANTS[v] + SIM))
    for v, (m, seed) in itertools.product(V2.VARIANTS, (('0x0000', 1), ('0x9C63', 2))):
        js.append((f'drain__{v}__{m}__s{seed}',
                   common_args(seed, m, hardcoded=REL + 'traffic/allpairs_burst.txt', lut=V2.lut_for(v, 'chipperm'))
                   + V2.VARIANTS[v] + DRAIN))
    return js


def run(job):
    binary, tag, name, args = job
    out = os.path.join(OUT, tag, name + '.json')
    if not os.path.exists(out):
        subprocess.run([binary] + args + ['-stats_file', out], cwd=BIN, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    try:
        return (tag, name), json.load(open(out))
    except Exception:
        return (tag, name), None


def main():
    old, new = sys.argv[1], sys.argv[2]
    for t in ('old', 'new'):
        os.makedirs(os.path.join(OUT, t), exist_ok=True)
    work = [(b, t, n, a) for t, b in (('old', old), ('new', new)) for n, a in jobs()]
    with Pool(11) as pool:
        res = dict(pool.map(run, work, chunksize=1))
    lines = ['# Default-instance regression of the parametric topology (check_param_regression.py)', '',
             f'Old binary: build of 4a3b345 (before parametrisation). New binary: feat/parametric-topology.',
             'Criterion: identical "summary" and "deft_lb" JSON blocks.', '']
    ok = {'win': [0, 0], 'drain': [0, 0]}
    diffs = []
    for name, _ in jobs():
        a, b = res[('old', name)], res[('new', name)]
        kind = name.split('__')[0]
        ok[kind][1] += 1
        if a is None or b is None:
            diffs.append(f'MISSING {name}')
            continue
        if a['summary'] == b['summary'] and a['deft_lb'] == b['deft_lb']:
            ok[kind][0] += 1
        else:
            keys = [k for blk in ('summary', 'deft_lb') for k in set(a[blk]) | set(b[blk])
                    if a[blk].get(k) != b[blk].get(k)]
            diffs.append(f'DIFFERENT {name}: {keys}')
    lines += [f'- fixed-window runs: {ok["win"][0]} / {ok["win"][1]} identical',
              f'- drain runs: {ok["drain"][0]} / {ok["drain"][1]} identical', '']
    lines += diffs or ['No differences.']
    open(os.path.join(HERE, 'results_v4', 'regression.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return not diffs


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
