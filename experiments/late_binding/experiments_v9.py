"""v9: confirmatory test of the layer-weighted cost (gamma = 2) against plain DeFT(rho*) (results_v9/).

Stages (python3 experiments_v9.py STAGE [nproc] [extra]):
  drain    2x2 drain tests of CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G (v2 protocol and masks)
  timing   timing test on all sizes and variants; seed rule (<= 9 h for seeds 41-50 -> 41-50, else 41-45)
  eval     evaluation of DeFT, DeFT_tm and the three _G variants, all sizes (extra: seeds 'all' = 41-50 | 'half' = 41-45)
Frozen design: results_v9/PREREGISTRATION.md. No tuning; no C++ change.
"""
import csv
import itertools
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v6 as E6  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v9')
SIZES = ['2x2', '3x3', '4x4']
LP5 = E6.LP5
CH5 = E6.CH5
GAMMA = ['-deft_lb', 'hop_weight_ipos', '2.0']
GVARS = ['CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
VARIANTS = ['DeFT', 'DeFT_tm'] + GVARS
SEEDS = {'all': range(41, 51), 'half': range(41, 46)}
RULE_HOURS = 9.0


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def variant_args(size):
    if size == '2x2':
        base = {v: V2.VARIANTS[v] for v in ('CI_heurLA', 'CI_qlLA', 'FULL_qlLA')}
    else:
        tv = E6.tuned_variants(size)
        base = {v: tv[v] for v in ('CI_heurLA', 'CI_qlLA', 'FULL_qlLA')}
    out = {'DeFT': V2.VARIANTS['DeFT'], 'DeFT_tm': V2.VARIANTS['DeFT_tm']}
    out.update({v + '_G': list(a) + GAMMA for v, a in base.items()})
    return out


def lut(size, v, p):
    if v == 'DeFT_tm':
        return E5.lut_path(size, CH5[size]['DeFT_tm'], p)
    return E5.lut_path(size, CH5[size]['DeFT'])


def ensure_tables():
    for size in SIZES:
        for p, m in E5.scenarios(size):
            E5.gen_tables(size, p, LP5[f'{size}__{p}__{m}']['eval'])


def eval_jobs(seeds, sizes=SIZES, variants=VARIANTS):
    js = []
    for size in sizes:
        va = variant_args(size)
        for p, m in E5.scenarios(size):
            for r in LP5[f'{size}__{p}__{m}']['eval']:
                for v in variants:
                    js += [E5.job('eval', size, v, va[v], p, m, r, s, lut(size, v, p)) for s in seeds]
    return js


# ---- drain (2x2, v2 protocol) ----
def drain_jobs():
    masks = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    va = variant_args('2x2')
    js = []
    for v in GVARS:
        for m, seed in itertools.product(masks, (1, 2)):
            a = common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=None) + va[v] + \
                ['-drain_mode', '-drain_source_cutoff', '100', '-drain_timeout', '60000', '-warmup', '0', '-sim', '80000']
            js.append((f'allpairs__{v}__{m}__s{seed}', a))
        for m, pat in itertools.product(['0x0000', '0x1111', '0x9C63', '0x7BDE'], ('uniform', 'chipperm', 'hotspot')):
            a = common_args(1, m, traffic=E5.REL + f'traffic/{pat}_0.0300.txt', lut=None) + va[v] + \
                ['-drain_mode', '-drain_source_cutoff', '3000', '-drain_timeout', '100000', '-warmup', '1000', '-sim', '120000']
            js.append((f'{pat}0.03__{v}__{m}__s1', a))
    return js


def drain_report(res):
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
              s['measured_received_packets'] == s['measured_injected_packets'] and l['dead_end_events'] == 0)
        fails += not ok
        rows.append([wl, v, m, seed, s.get('drain_stop_reason'), s['measured_injected_packets'],
                     s['measured_received_packets'], l['dead_end_events'], s.get('drain_completed_cycle'),
                     'PASS' if ok else 'FAIL'])
    with open(os.path.join(RES, 'drain_summary.csv'), 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['workload', 'variant', 'mask', 'seed', 'stop_reason', 'injected', 'received',
                    'dead_end_events', 'drain_completed_cycle', 'result'])
        w.writerows(rows)
    print(f'runs={len(rows)} failures={fails}')
    return fails


# ---- timing and seed rule ----
def timing(nproc):
    js = []
    for size in SIZES:
        va = variant_args(size)
        for p, m in E5.scenarios(size):
            for i in (1, 3, 6):
                r = LP5[f'{size}__{p}__{m}']['eval'][i]
                js += [E5.job('timing', size, v, va[v], p, m, r, 1001, lut(size, v, p)) for v in VARIANTS]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    missing = sum(1 for x in res.values() if x is None)
    n10 = len(eval_jobs(SEEDS['all']))
    est = el / len(js) * n10 / 3600
    seeds = 'all' if est <= RULE_HOURS else 'half'
    L = ['# Run-time estimate v9 and seed choice', '',
         f'Timing test: {len(js)} runs (seed 1001; every variant x size x scenario at the 2nd, 4th and 7th load), '
         f'{nproc} processes: {el:.0f} s wall, {el / len(js):.2f} s per run; {missing} missing.', '',
         f'Full evaluation with seeds 41-50: {n10} runs, estimated **{est:.1f} h**. Rule (pre-registered): at most '
         f'{RULE_HOURS:.0f} h -> seeds 41-50, otherwise seeds 41-45.', '',
         f'**Seeds: {"41-50" if seeds == "all" else "41-45"}** ({len(eval_jobs(SEEDS[seeds]))} runs).']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    json.dump({'seeds': seeds, 'estimate_h_41_50': round(est, 2), 'timing_runs': len(js), 'wall_s': round(el)},
              open(os.path.join(RES, 'seed_choice.json'), 'w'), indent=1)
    print('\n'.join(L))
    shutil.rmtree(raw('timing'))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    if stage == 'timing':
        ensure_tables()
        timing(nproc)
        sys.exit(0)
    if stage == 'drain':
        js, out = drain_jobs(), 'drain'
    elif stage == 'eval':
        choice = json.load(open(os.path.join(RES, 'seed_choice.json')))['seeds']
        if extra and extra != choice:
            raise SystemExit(f'seed set {extra} differs from the recorded choice {choice}')
        ensure_tables()
        js, out = eval_jobs(SEEDS[choice]), 'eval'
    else:
        raise SystemExit('unknown stage')
    print(stage, 'jobs:', len(js), flush=True)
    res = run_jobs(js, raw(out), nproc=nproc, timeout=14400)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
