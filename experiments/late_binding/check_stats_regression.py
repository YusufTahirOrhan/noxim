"""Regression for the v6 statistics flag (results_v6/stats_regression.md).

Old binary (e4752bf build) vs new binary, same arguments: all 11 v2 variants x 2x2/3x3/4x4 x fault-free and
one faulty VL per chiplet (66 configurations; uniform traffic at the v5 1.0 x Lsat load, seed 7, v5 rho* LUTs).
  * flag off: "summary" and "deft_lb" JSON blocks must be byte-identical (as parsed values);
  * flag on (-deft_lb stats_file ...): "summary" must be identical as well (deft_lb is compared too).
Usage: python3 check_stats_regression.py BIN_OLD BIN_NEW
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results_v6', 'statsreg_raw')
LP = json.load(open(os.path.join(HERE, 'results_v5', 'load_points.json')))
CH = json.load(open(os.path.join(HERE, 'results_v5', 'tuning_choice.json')))


def configs():
    out = []
    for size in E5.SIZES:
        for m in (E5.FREE[size], E5.NORTH[size]):
            rate = LP[f'{size}__uniform__{m}']['eval'][3]
            for v, va in V2.VARIANTS.items():
                lut = E5.variant_lut(size, v, 'uniform', CH) if v in ('DeFT', 'DeFT_tm') or v.startswith('CI') \
                    else E5.lut_path(size, CH[size]['DeFT'])
                a = common_args(7, m, traffic=E5.REL + f'{E5.tdir(size)}/uniform_{rate:.4f}.txt', lut=lut) + \
                    E5.size_args(size) + va + E5.SIM
                out.append((f'{v}__{size}__{m}', a))
    return out


def run(job):
    tag, binary, name, args = job
    out = os.path.join(OUT, f'{tag}__{name}.json')
    extra = ['-deft_lb', 'stats_file', out + '.stats'] if tag == 'on' else []
    if not os.path.exists(out):
        subprocess.run([binary] + args + extra + ['-stats_file', out], cwd=BIN, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    try:
        return (tag, name), json.load(open(out))
    except Exception:
        return (tag, name), None


def main():
    old, new = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    cf = configs()
    jobs = [(t, b, n, a) for t, b in (('old', old), ('off', new), ('on', new)) for n, a in cf]
    with Pool(12) as pool:
        res = dict(pool.map(run, jobs, chunksize=1))
    off_ok = on_ok = stats_files = 0
    diffs = []
    for n, _ in cf:
        o, f, s = res[('old', n)], res[('off', n)], res[('on', n)]
        if o and f and o['summary'] == f['summary'] and o['deft_lb'] == f['deft_lb']:
            off_ok += 1
        else:
            diffs.append(f'flag off differs: {n}')
        if o and s and o['summary'] == s['summary'] and o['deft_lb'] == s['deft_lb']:
            on_ok += 1
        else:
            diffs.append(f'flag on differs: {n}')
        stats_files += os.path.exists(os.path.join(OUT, f'on__{n}.json.stats'))
    L = ['# Regression of the v6 statistics flag (check_stats_regression.py)', '',
         'Old binary: build of e4752bf (no statistics code). New binary: v6 statistics code.',
         f'Configurations: {len(cf)} (11 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at '
         '1.0 x Lsat of v5; seed 7).', '',
         f'- flag off: {off_ok} / {len(cf)} runs with identical summary and deft_lb blocks',
         f'- flag on: {on_ok} / {len(cf)} runs with identical summary (and deft_lb) blocks; {stats_files} statistics files '
         'written (only DEFT_LB runs write one: the hook is inactive for DEFT routing)', '']
    L += diffs or ['No differences.']
    open(os.path.join(HERE, 'results_v6', 'stats_regression.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return not diffs


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
