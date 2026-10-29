"""v14 (Part F): fault-sweep latency below DeFT(rho*)'s faulty saturation point (results_v14_faultload/).

Stages (python3 experiments_v14.py STAGE [nproc]; --shard i/n accepted):
  choose   F1: test load per (size, k, pattern) from results_v11/eval_runs.csv (no runs) -> load_choice.json, and the
           exploratory v11 effects at these loads -> load_choice.md
  timing   timing test of the F2 design (seed 1001, first mask)
  eval     F2: the v11 masks, uniform and hotspot at the F1 load, all 8 v11 methods, seeds 53-57
  report   F2 analysis (Holm over 18) -> report/, run CSV
Rule (v5): a load point is unsaturated for DeFT(rho*) if its mean latency (pooled over the 5 masks and seeds 51-52) is
at most 3 x the zero-load latency (the pooled mean latency at the lowest load point).
"""
import csv
import json
import math
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v11 as E11  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v14_faultload')
R11 = os.path.join(HERE, 'results_v11')
SIZES, KS, PATTERNS = E11.SIZES, E11.KS, E11.PATTERNS
METHODS = E11.METHODS
OURS = ['CI_qlLA_G', 'FULL_qlLA_G']
SEEDS = range(53, 58)
LABEL = {'DeFT': 'DeFT(rho*)', 'DeFT_Dis': 'DeFT-Dis', 'DeFT_Ran': 'DeFT-Ran', 'XY_SP': 'XY-SP'}
NL = chr(10)


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def masks():
    m = json.load(open(os.path.join(R11, 'masks.json')))
    return {k: v[:5] for k, v in m.items()}


def ladder(size, p):
    return E10.LP5[f'{size}__{p}__{E5.FREE[size]}']['eval']


def v11_rows():
    out = {}
    for r in csv.DictReader(open(os.path.join(R11, 'eval_runs.csv'))):
        out[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = r
    return out


def choose():
    R = v11_rows()
    ms = masks()
    choice, L = {}, ['# F1: test load per (size, k, pattern) (experiments_v14.py choose; no new runs)', '',
                     'DeFT(rho*) in results_v11/eval_runs.csv (seeds 51-52), mean latency pooled over the 5 masks and '
                     'both seeds per load point. Unsaturated: pooled latency <= 3 x the pooled latency at the lowest '
                     'load point. Test load = the highest unsaturated load point.', '',
                     '| size | k | pattern | zero-load latency | pooled latency per load point (cycles; * = unsaturated) '
                     '| test load (rate, x fault-free Lsat) |', '|---|---|---|---|---|---|']
    mult = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
    for z in SIZES:
        for k in KS:
            for p in PATTERNS:
                lad = ladder(z, p)
                pooled = []
                for r in lad:
                    xs = [float(R[('DeFT', f'{z}-{p}', m, r, s)]['latency']) for m in ms[f'{z}__k{k}'] for s in (51, 52)]
                    pooled.append(sum(xs) / len(xs))
                ok = [x <= 3 * pooled[0] for x in pooled]
                idx = max((i for i in range(len(lad)) if ok[i]), default=None)
                note = ''
                if idx is None:
                    idx, note = 0, ' (none qualifies: lowest point)'
                choice[f'{z}__k{k}__{p}'] = dict(rate=lad[idx], index=idx, mult=mult[idx], zero_load=pooled[0],
                                                 pooled=pooled, all_lower_ok=all(ok[:idx + 1]))
                cells = ' / '.join(f'{x:.0f}{"*" if o else ""}' for x, o in zip(pooled, ok))
                L.append(f'| {z} | {k} | {p} | {pooled[0]:.1f} | {cells} | {lad[idx]} ({mult[idx]} x){note} |')
    json.dump(choice, open(os.path.join(RES, 'load_choice.json'), 'w'), indent=1)
    # exploratory v11 effects at these loads (not pre-registered)
    L += ['', '## Exploratory: v11 effects at these loads (seeds 51-52; not pre-registered)', '',
          'Unit = (mask, seed), mean over uniform and hotspot of ln(LAT_variant / LAT_DeFT) at the chosen load of each '
          'pattern; 10 units; unadjusted t-test.', '', '| size | k | CI_qlLA_G | FULL_qlLA_G |', '|---|---|---|---|']
    from primary_from_csv import ci, ttest
    for z in SIZES:
        for k in KS:
            cells = []
            for a in OURS:
                us = []
                for m in ms[f'{z}__k{k}']:
                    for s in (51, 52):
                        rs = []
                        for p in PATTERNS:
                            r = choice[f'{z}__k{k}__{p}']['rate']
                            rs.append(math.log(float(R[(a, f'{z}-{p}', m, r, s)]['latency']) /
                                               float(R[('DeFT', f'{z}-{p}', m, r, s)]['latency'])))
                        us.append(sum(rs) / 2)
                mu, h = ci(us)
                cells.append(f'{100 * (math.exp(mu) - 1):+.1f} [{100 * (math.exp(mu - h) - 1):+.1f}, '
                             f'{100 * (math.exp(mu + h) - 1):+.1f}] (p {ttest(us):.2g})')
            L.append(f'| {z} | {k} | ' + ' | '.join(cells) + ' |')
    open(os.path.join(RES, 'load_choice.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))


def cells():
    ms = masks()
    ch = json.load(open(os.path.join(RES, 'load_choice.json')))
    return [(z, k, m, p, ch[f'{z}__k{k}__{p}']['rate']) for z in SIZES for k in KS for m in ms[f'{z}__k{k}']
            for p in PATTERNS]


def eval_jobs(seeds=SEEDS):
    js = []
    for z, k, m, p, r in cells():
        mm = E10.methods(z)
        js += [E5.job('eval', z, v, mm[v], p, m, r, s, E11.lut_path(z, m)) for v in METHODS for s in seeds]
    return js


def timing(nproc):
    js = [j for j in eval_jobs((1001,))]
    first = {(z, k): masks()[f'{z}__k{k}'][0] for z in SIZES for k in KS}
    js = [j for j in js if any(f'{z}-' in j[0] and f'__{first[(z, k)]}__' in j[0] for z, k in first)]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v14 (F2)', '', f'Timing test: {len(js)} runs (seed 1001, first mask of each (size, k), '
         f'both patterns, all methods, at the F1 load), {nproc} processes: {el:.0f} s wall; '
         f'{sum(1 for x in res.values() if x is None)} missing.', '', f'F2: {n} runs, estimated **{est:.1f} h**.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('timing'))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    if stage == 'choose':
        choose()
    elif stage == 'timing':
        timing(nproc)
    elif stage == 'eval':
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    else:
        raise SystemExit('unknown stage')
