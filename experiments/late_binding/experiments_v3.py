"""v3 runs (results_v3/): confirmatory near-Lsat test, window sensitivity, exploratory tuning.

Stages (python3 experiments_v3.py STAGE [nproc]):
  confirm  7 variants x 11 scenarios x loads 0.8/1.0/1.2 x Lsat (3rd-5th v2 rates) x seeds 11-20,
           2000 + 8000 cycles (as v2); parameters frozen in variants_v2.py
  window   DeFT_tm, CI_heurLA, CI_qlLA on uniform/hotspot/movinghot 0x0000 at 1.0 x Lsat,
           seeds 11-15, 2000 + 40000 cycles
  tunex    exploratory CI tuning beyond the v2 grid edges (seeds 101, 102 only):
           heuristic w {2, 4, 8} x busy {0, 4}; CI_ql alpha {0.001, 0.002, 0.005}
           (key = chiplet and local weights from the frozen CI heuristic, as in v2)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402
from experiments import EVAL_SCENARIOS  # noqa: E402
from experiments_v2 import TUNE_CELLS, TUNE_SEEDS, traffic  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v3')
LP = json.load(open(os.path.join(HERE, 'results_v2', 'load_points.json')))
VARIANTS = ['DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_ql', 'CI_qlLA', 'FULL_heurLA', 'FULL_qlLA']
LOAD_IDX = {'0.8': 2, '1.0': 3, '1.2': 4}
SEEDS = range(11, 21)
WINDOW_SEEDS = range(11, 16)
WINDOW_VARIANTS = ['DeFT_tm', 'CI_heurLA', 'CI_qlLA']
WINDOW_SCEN = [('uniform', '0x0000'), ('hotspot', '0x0000'), ('movinghot', '0x0000')]
SIM = ['-sim', '10000', '-warmup', '2000']
SIM_LONG = ['-sim', '42000', '-warmup', '2000']


def k(p, m):
    return f'{p}__{m}'


def job(stage, variant, vargs, p, m, rate, seed, sim=SIM, lut=None):
    name = f'{stage}__{variant}__{p}__{m}__{rate:.4f}__s{seed}'
    return name, common_args(seed, m, traffic=traffic(p, rate), lut=lut) + list(vargs) + sim


def confirm_jobs():
    return [job('confirm', v, V2.VARIANTS[v], p, m, LP[k(p, m)]['eval'][i], s, lut=V2.lut_for(v, p))
            for p, m in EVAL_SCENARIOS for i in LOAD_IDX.values() for v in VARIANTS for s in SEEDS]


def window_jobs():
    return [job('window', v, V2.VARIANTS[v], p, m, LP[k(p, m)]['eval'][LOAD_IDX['1.0']], s, sim=SIM_LONG,
                lut=V2.lut_for(v, p))
            for p, m in WINDOW_SCEN for v in WINDOW_VARIANTS for s in WINDOW_SEEDS]


def tunex_grid():
    c = V2.PARAMS['CI']
    g = {}
    for w in (2.0, 4.0, 8.0):
        for b in (0.0, 4.0):
            g[f'CI-heur-w{w}-b{b}'] = V.CI + V2.heur(w, b)
    for a in (0.001, 0.002, 0.005):
        g[f'CI-ql-a{a}-k1'] = V.CI + V2.ql(c['heur_w'], c['heur_busy'], a, 1)
    return g


def tunex_jobs():
    return [job('tunex', n, va, p, m, r, s) for n, va in tunex_grid().items() for p, m in TUNE_CELLS
            for r in LP[k(p, m)]['tune'] for s in TUNE_SEEDS]


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    js = {'confirm': confirm_jobs, 'window': window_jobs, 'tunex': tunex_jobs}[stage]()
    print(stage, 'jobs:', len(js), flush=True)
    res = run_jobs(js, os.path.join(RES, stage + '_raw'), nproc=nproc, timeout=7200)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
