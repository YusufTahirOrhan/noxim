"""v11 (Part C): fault-rate sweep, k = 1, 2, 3 faulty VLs in every chiplet (results_v11/).

Stages (python3 experiments_v11.py STAGE [nproc] [extra]; --shard i/n accepted, see runner.py):
  masks     draw 5 masks per (size, k) with random.Random(3110) -> results_v11/masks.json (recorded)
  luttime   generate the LUT of one 4x4 mask per k and estimate the time for all 4x4 LUTs (rule: > 4 h -> 3 masks)
  luts      DeFT's rho* uniform LUT for every mask (luts/v11/), in parallel
  drain     all-pairs burst drain test of every method on every mask (seed 1)
  timing    timing test and estimate (rule: > 16 h -> 3 masks per (size, k))
  eval      evaluation, seeds 51-52
Methods: DeFT(rho*) (its LUT for the mask), DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G, CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G
(experiments_v10.methods). Traffic: uniform and hotspot at the 7 fault-free v5 load points of each pattern.
"""
import itertools
import json
import os
import random
import shutil
import subprocess
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v11')
LUTD = os.path.join(HERE, 'luts', 'v11')
SIZES = ['2x2', '3x3', '4x4']
KS = [1, 2, 3]
N_MASKS = 5
MASK_SEED = 3110
PATTERNS = ['uniform', 'hotspot']
METHODS = ['DeFT', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
SEEDS = (51, 52)
GEN = E5.GEN


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def draw_masks():
    rnd = random.Random(MASK_SEED)
    out = {}
    for size in SIZES:
        cx, cy = E5.SIZES[size]
        nvl = 4 * cx * cy
        digits = (nvl + 3) // 4
        for k in KS:
            ms = []
            while len(ms) < N_MASKS:
                bits = 0
                for c in range(cx * cy):
                    for s in rnd.sample(range(4), k):
                        bits |= 1 << (4 * c + s)
                m = '0x' + format(bits, f'0{digits}X')
                if m not in ms:
                    ms.append(m)
            out[f'{size}__k{k}'] = ms
    json.dump(out, open(os.path.join(RES, 'masks.json'), 'w'), indent=1)
    return out


def masks():
    return json.load(open(os.path.join(RES, 'masks.json')))


def n_masks():
    path = os.path.join(RES, 'mask_count.json')
    return json.load(open(path))['n_masks'] if os.path.exists(path) else N_MASKS


def lut_path(size, m):
    return os.path.join(LUTD, f'lut_{size}_rho{E10.CH5[size]["DeFT"]}_{m}.yaml')


def _gen(arg):
    size, m = arg
    out = lut_path(size, m)
    if os.path.exists(out):
        return out, 0.0
    cx, cy = E5.SIZES[size]
    t = time.time()
    subprocess.run([sys.executable, GEN, '--chiplets-x', str(cx), '--chiplets-y', str(cy), '--rho',
                    E10.CH5[size]['DeFT'], '--fault-mask', m, '--output', out], check=True)
    return out, time.time() - t


def cells():
    """(size, k, mask, pattern) of the design (first n_masks() masks of each (size, k))."""
    ms = masks()
    return [(size, k, m, p) for size in SIZES for k in KS for m in ms[f'{size}__k{k}'][:n_masks()] for p in PATTERNS]


def eval_jobs(seeds=SEEDS):
    js = []
    for size, k, m, p in cells():
        mm = E10.methods(size)
        for r in E10.LP5[f'{size}__{p}__{E5.FREE[size]}']['eval']:
            for v in METHODS:
                js += [E5.job('eval', size, v, mm[v], p, m, r, s, lut_path(size, m)) for s in seeds]
    return js


def drain_jobs():
    js = []
    ms = masks()
    for size in SIZES:
        mm = E10.methods(size)
        for k in KS:
            for m in ms[f'{size}__k{k}'][:n_masks()]:
                for v in METHODS:
                    a = common_args(1, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt',
                                    lut=lut_path(size, m)) + E5.size_args(size) + mm[v] + E10.DRAIN_ALLPAIRS
                    js.append((f'allpairs__{v}__{size}-k{k}-{m}__s1', a))
    return js


def timing(nproc):
    js = []
    ms = masks()
    for size in SIZES:
        mm = E10.methods(size)
        for k in KS:
            m = ms[f'{size}__k{k}'][0]
            for p in PATTERNS:
                lad = E10.LP5[f'{size}__{p}__{E5.FREE[size]}']['eval']
                for i in (1, 3, 6):
                    js += [E5.job('timing', size, v, mm[v], p, m, lad[i], 1001, lut_path(size, m)) for v in METHODS]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    per_cell = el / len(js)
    n5 = len(SIZES) * len(KS) * N_MASKS * len(PATTERNS) * 7 * len(METHODS) * len(SEEDS)
    est = per_cell * n5 / 3600
    use = N_MASKS if est <= 16 else 3
    json.dump({'n_masks': use, 'estimate_h_5_masks': round(est, 2)}, open(os.path.join(RES, 'mask_count.json'), 'w'))
    L = ['# Run-time estimate v11 (Part C)', '', f'Timing test: {len(js)} runs (seed 1001; every method x size x k (first '
         f'mask) x pattern at the 2nd, 4th and 7th load), {nproc} processes: {el:.0f} s wall, {per_cell:.2f} s per run; '
         f'{sum(1 for x in res.values() if x is None)} missing.', '',
         f'Full design with 5 masks per (size, k): {n5} runs, estimated **{est:.1f} h** on one machine. Rule: over 16 h '
         f'-> 3 masks per (size, k). **Masks per (size, k): {use}.**']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('timing'))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    os.makedirs(LUTD, exist_ok=True)
    if stage == 'masks':
        print(json.dumps(draw_masks(), indent=1))
        sys.exit(0)
    if stage == 'luttime':
        ms = masks()
        jobs = [('4x4', ms[f'4x4__k{k}'][0]) for k in KS]
        with Pool(min(nproc, len(jobs))) as pool:
            res = pool.map(_gen, jobs)
        per = [t for _, t in res]
        est = sum(per) / len(per) * N_MASKS * len(KS) / 3600
        L = ['# LUT generation time, 4x4 (v11)', '', f'One mask per k, generated in parallel ({len(jobs)} processes): '
             + ', '.join(f'k {k}: {t:.0f} s' for k, t in zip(KS, per)) + '.', '',
             f'All {N_MASKS * len(KS)} 4x4 LUTs, sequential: **{est:.2f} h** (rule: over 4 h -> 3 masks per (size, k)). '
             f'Generated in parallel with the other sizes, the wall time is lower.']
        open(os.path.join(RES, 'lut_timing.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
        print('\n'.join(L))
        sys.exit(0)
    if stage == 'luts':
        ms = masks()
        jobs = [(size, m) for size in SIZES for k in KS for m in ms[f'{size}__k{k}'][:n_masks()]]
        t = time.time()
        with Pool(nproc) as pool:
            res = pool.map(_gen, jobs, chunksize=1)
        print(f'{len(res)} LUTs, {time.time() - t:.0f} s wall')
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'drain':
        res = run_jobs(drain_jobs(), raw('drain'), nproc=nproc, timeout=14400)
        rows, fails = [], 0
        for name in sorted(res):
            d = res[name]
            wl, v, sm, seed = name.split('__')
            ok = d is not None and d['summary'].get('drain_stop_reason') == 'drain_completed' and \
                d['summary']['measured_received_packets'] == d['summary']['measured_injected_packets'] and \
                d['deft_lb']['dead_end_events'] == 0
            fails += not ok
            rows.append(','.join([wl, v, sm, seed, str(d['summary'].get('drain_stop_reason')) if d else 'NO_OUTPUT',
                                  str(d['summary']['measured_injected_packets']) if d else '',
                                  str(d['summary']['measured_received_packets']) if d else '',
                                  str(d['deft_lb']['dead_end_events']) if d else '', 'PASS' if ok else 'FAIL']))
        open(os.path.join(RES, 'drain_summary.csv'), 'w', newline='\n').write(
            'workload,variant,size-k-mask,seed,stop_reason,injected,received,dead_end_events,result\n' + '\n'.join(rows) + '\n')
        print(f'runs={len(rows)} failures={fails}')
        shutil.rmtree(raw('drain'))
        sys.exit(1 if fails else 0)
    if stage == 'eval':
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
        sys.exit(0)
    raise SystemExit('unknown stage')
