"""Performance experiments for directions A, B and C (fixed-window mode).

Stages:
  sat   - DeFT load sweep per traffic pattern (seed 101) to locate saturation
  tune  - parameter grids on tuning seeds 101, 102 (never used for evaluation)
  eval  - all variants, evaluation seeds 1..5
Simulation: 2000 warm-up + 8000 measured cycles (Noxim -sim 10000 -warmup 2000).
Usage: python3 experiments.py STAGE [nproc]
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
PATTERNS = ['uniform', 'localized', 'hotspot', 'chipperm', 'movinghot']
RATES = [round(0.001 * i, 4) for i in range(1, 41)]


def traffic(pat, rate):
    return REL + f'traffic/{pat}_{rate:.4f}.txt'


def job(stage, variant, vargs, pat, mask, rate, seed, extra=()):
    name = f'{stage}__{variant}__{pat}__{mask}__{rate:.4f}__s{seed}'
    return name, common_args(seed, mask, traffic=traffic(pat, rate)) + list(vargs) + list(extra) + SIM


def sat_jobs():
    js = []
    for pat in PATTERNS:
        for rate in [0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.020, 0.024]:
            js.append(job('sat', 'DeFT', V.VARIANTS['DeFT'], pat, '0x0000', rate, 101))
    return js


def load_points():
    return json.load(open(os.path.join(HERE, 'results', 'load_points.json')))


TUNE_SEEDS = (101, 102)
TUNE_CELLS = [('uniform', '0x0000'), ('hotspot', '0x0000'), ('chipperm', '0x0000'), ('uniform', '0x1111')]


def tune_grid():
    g = {}
    for w, b in itertools.product([0.5, 1.0, 2.0], [0.0, 4.0, 8.0]):
        g[f'heur_w{w}_b{b}'] = V.FULL + ['-sel', 'DEFT_HEUR'] + V.kv(heur_w=w, heur_busy=b)
    for beta in [0.25, 0.5, 1.0, 2.0]:
        g[f'oracle_b{beta}'] = V.inj('oracle') + V.kv(oracle_beta=beta)
    return g


def tune_ql_grid(w, b):
    g = {}
    for alpha, key, eps in itertools.product([0.05, 0.2, 0.5], [0, 1], [0.0, 0.05]):
        g[f'ql_a{alpha}_k{key}_e{eps}'] = V.FULL + ['-sel', 'DEFT_QL'] + \
            V.kv(ql_w=w, ql_busy=b, ql_alpha=alpha, ql_key=key, ql_eps=eps)
    return g


def tune_jobs(grid):
    lp = load_points()
    js = []
    for name, va in grid.items():
        for pat, mask in TUNE_CELLS:
            for rate in lp[pat]['tune']:
                for seed in TUNE_SEEDS:
                    js.append(job('tune', name, va, pat, mask, rate, seed))
    return js


EVAL_SEEDS = (1, 2, 3, 4, 5)
EVAL_SCENARIOS = [(p, '0x0000') for p in PATTERNS] + \
                 [(p, m) for p in ('uniform', 'hotspot', 'chipperm') for m in ('0x1111', '0x9C63')]


def eval_jobs():
    lp = load_points()
    js = []
    for pat, mask in EVAL_SCENARIOS:
        for rate in lp[pat]['eval']:
            for v, va in V.VARIANTS.items():
                for seed in EVAL_SEEDS:
                    js.append(job('eval', v, va, pat, mask, rate, seed))
    return js


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    if stage == 'sat':
        js = sat_jobs()
    elif stage == 'tune':
        js = tune_jobs(tune_grid())
    elif stage == 'tune_ql':
        best = json.load(open(os.path.join(HERE, 'results', 'tuning_choice.json')))
        js = tune_jobs(tune_ql_grid(best['heur_w'], best['heur_busy']))
    elif stage == 'eval':
        js = eval_jobs()
    else:
        raise SystemExit('unknown stage')
    print(stage, 'jobs:', len(js), flush=True)
    res = run_jobs(js, os.path.join(HERE, 'results', stage.split('_')[0] + '_raw'), nproc=nproc, timeout=7200)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
