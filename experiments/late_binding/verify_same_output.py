"""Check that two Noxim binaries give identical results on the same arguments.

Used to verify that commit 8b343ad (traffic table indexed per source) does not
change behaviour: the "summary" and "deft_lb" blocks of the JSON outputs must be
identical for every run.
Runs: table-based uniform and movinghot traffic, DeFT and FULL + DEFT_QL,
seeds 1 and 2, two loads, fault masks 0x0000 and 0x1111.
Usage: python3 verify_same_output.py BIN_OLD BIN_NEW OUT_DIR [nproc]
"""
import itertools
import json
import os
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args  # noqa: E402
import variants as V  # noqa: E402

REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
CASES = {'DeFT': V.VARIANTS['DeFT'], 'FULL_ql': V.VARIANTS['FULL_ql']}


def jobs():
    js = []
    for pat, rate, mask, seed, v in itertools.product(
            ('uniform', 'movinghot'), (0.010, 0.020), ('0x0000', '0x1111'), (1, 2), CASES):
        name = f'{v}__{pat}__{mask}__{rate:.4f}__s{seed}'
        args = common_args(seed, mask, traffic=REL + f'traffic/{pat}_{rate:.4f}.txt') + CASES[v] + SIM
        js.append((name, args))
    return js


def run(job):
    binary, out_dir, name, args = job
    out = os.path.join(out_dir, name + '.json')
    subprocess.run([binary] + args + ['-stats_file', out], cwd=BIN, env=ENV,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
    return name


if __name__ == '__main__':
    old, new, out = sys.argv[1], sys.argv[2], sys.argv[3]
    nproc = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    dirs = {'old': os.path.join(out, 'old'), 'new': os.path.join(out, 'new')}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    work = [(b, dirs[k], n, a) for k, b in (('old', old), ('new', new)) for n, a in jobs()]
    with Pool(nproc) as pool:
        pool.map(run, work, chunksize=1)
    same = diff = missing = 0
    for name, _ in jobs():
        try:
            a = json.load(open(os.path.join(dirs['old'], name + '.json')))
            b = json.load(open(os.path.join(dirs['new'], name + '.json')))
        except Exception:
            print('MISSING', name)
            missing += 1
            continue
        if a['summary'] == b['summary'] and a['deft_lb'] == b['deft_lb']:
            same += 1
            print('IDENTICAL', name, 'packets', a['summary']['total_received_packets'],
                  'delay', round(a['summary']['global_average_delay_cycles'], 3))
        else:
            diff += 1
            keys = [k for blk in ('summary', 'deft_lb') for k in a[blk] if a[blk][k] != b[blk].get(k)]
            print('DIFFERENT', name, keys)
    print(f'runs={same + diff + missing} identical={same} different={diff} missing={missing}')
