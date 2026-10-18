"""v4: replication on larger systems (3x3 and 4x4 chiplets of 4x4 routers), results_v4/.

Stages (python3 experiments_v4.py STAGE [nproc] [extra]):
  drain    all-pairs burst, fault-free and one faulty VL per chiplet (north), seeds 1-2, for
           DeFT, DeFT_tm (hotspot and chipperm LUTs), CI_heur, CI_heurLA, CI_qlLA, FULL_heurLA
  sat      DeFT load sweep per size and scenario (seed 101), 0.0005 steps to 0.016, then 0.018-0.024
  points   Lsat per size and scenario -> results_v4/load_points.json / .md (amended rule, see
           PREREGISTRATION_AMENDMENT.md; the coarse v2-rule result is kept in load_points_coarse.*)
  satfine  amendment: L0 at rate 0.0002 for every scenario, and 0.0001-step sweeps for the
           scenarios whose coarse Lsat is <= 0.004
  tables   write the traffic tables of the evaluation loads (0.0001 grid where needed)
  timing   short timing test and run-time estimate -> results_v4/runtime_estimate.md
  eval     variants x 2 sizes x 7 scenarios x 7 loads x seeds (extra: first | second | all)
  evalvl   DEFT_LB with the DeFT_tm LUT pairs (traffic-identical to DeFT_tm) for VL counts,
           at ~0.5 and ~1.0 x Lsat
Parameters are frozen from variants_v2.py (no re-tuning); every LUT is the one of the size.
"""
import csv
import itertools
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v4')
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
SIZES = {'3x3': (3, 3), '4x4': (4, 4)}
NORTH = {s: hex(sum(1 << (4 * c) for c in range(cx * cy))) for s, (cx, cy) in SIZES.items()}
GRID = 0.0005
SAT_RATES = [round(GRID * i, 4) for i in range(1, 33)] + [0.018, 0.020, 0.024]
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
SEEDS = {'first': range(1, 6), 'second': range(6, 11), 'all': range(1, 11)}
EVAL_VARIANTS = ['DeFT', 'DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_qlLA', 'FULL_heurLA']
DRAIN_VARIANTS = ['DeFT', 'DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_qlLA', 'FULL_heurLA']
TM_PATTERNS = ('localized', 'hotspot', 'chipperm', 'movinghot')


def scenarios(size):
    return [(p, '0x0') for p in ('uniform', 'localized', 'hotspot', 'chipperm', 'movinghot')] + \
           [(p, NORTH[size]) for p in ('uniform', 'hotspot')]


def size_args(size):
    cx, cy = SIZES[size]
    return ['-deft_chiplets_x', str(cx), '-deft_chiplets_y', str(cy)]


def lut(size, variant, pattern):
    if variant == 'DeFT_tm' and pattern in TM_PATTERNS:
        return os.path.join(HERE, 'luts', f'lut_{size}_rho001_tm_{pattern}.yaml')
    return os.path.join(HERE, 'luts', f'lut_{size}_rho001.yaml')


def key(size, p, m):
    return f'{size}__{p}__{m}'


def job(stage, size, variant, vargs, p, m, rate, seed, lut_pattern=None):
    name = f'{stage}__{variant}__{size}-{p}__{m}__{rate:.4f}__s{seed}'
    args = common_args(seed, m, traffic=REL + f'traffic_{size}/{p}_{rate:.4f}.txt',
                       lut=lut(size, variant, lut_pattern or p))
    return name, args + size_args(size) + list(vargs) + SIM


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def load_points():
    return json.load(open(os.path.join(RES, 'load_points.json')))


# ---- drain ----
def drain_jobs():
    js = []
    for size, v, m, seed in itertools.product(SIZES, DRAIN_VARIANTS, ('0x0', None), (1, 2)):
        m = m or NORTH[size]
        luts = [('', lut(size, v, 'uniform'))] if v != 'DeFT_tm' else \
            [('-lut' + p, lut(size, v, p)) for p in ('hotspot', 'chipperm')]
        for tag, lf in luts:
            a = common_args(seed, m, hardcoded=REL + f'traffic_{size}/allpairs_burst.txt', lut=lf) + size_args(size) + \
                V2.VARIANTS[v] + ['-drain_mode', '-drain_source_cutoff', '1000', '-drain_timeout', '1000000',
                                  '-warmup', '0', '-sim', '1200000']
            js.append((f'allpairs{tag}__{v}__{size}-{m}__s{seed}', a))
    return js


def drain_report(res):
    rows, fails = [], 0
    for name in sorted(res):
        d = res[name]
        wl, v, sm, seed = name.split('__')
        if d is None:
            rows.append([wl, v, sm, seed, 'NO_OUTPUT', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        ok = (s.get('drain_stop_reason') == 'drain_completed' and
              s['measured_received_packets'] == s['measured_injected_packets'] and l['dead_end_events'] == 0)
        fails += not ok
        rows.append([wl, v, sm, seed, s.get('drain_stop_reason'), s['measured_injected_packets'],
                     s['measured_received_packets'], l['dead_end_events'], s.get('drain_completed_cycle'),
                     'PASS' if ok else 'FAIL'])
    with open(os.path.join(RES, 'drain_summary.csv'), 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['workload', 'variant', 'size-mask', 'seed', 'stop_reason', 'injected', 'received',
                    'dead_end_events', 'drain_completed_cycle', 'result'])
        w.writerows(rows)
    print(f'runs={len(rows)} failures={fails}')
    return fails


# ---- sat / points ----
def sat_jobs():
    return [job('sat', s, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, 101)
            for s in SIZES for p, m in scenarios(s) for r in SAT_RATES]


def snap(x, grid=GRID):
    return round(max(grid, round(x / grid) * grid), 4)


FINE = 0.0001
L0_RATE = 0.0002
LOW_LSAT = 0.004


def gen_tables(size, patterns, rates):
    import subprocess
    cx, cy = SIZES[size]
    subprocess.run([sys.executable, os.path.join(HERE, 'gen_traffic.py'), os.path.join(HERE, f'traffic_{size}'),
                    '--chiplets', str(cx), str(cy), '--rates', ','.join(f'{r:.4f}' for r in rates),
                    '--patterns', ','.join(patterns)], check=True)


def coarse():
    return json.load(open(os.path.join(RES, 'load_points_coarse.json')))


def fine_rates(size, p, m):
    """0.0001-step sweep up to the rate where the coarse sweep first crossed 3 x L0."""
    c = coarse()[key(size, p, m)]
    if c['lsat'] > LOW_LSAT:
        return []
    nxt = min(r for r in SAT_RATES if r > c['lsat'])
    return [round(FINE * i, 4) for i in range(1, int(round(nxt / FINE)) + 1)]


def satfine_jobs():
    js = []
    for s in SIZES:
        need = {}
        for p, m in scenarios(s):
            rates = sorted(set(fine_rates(s, p, m)) | {L0_RATE})
            need.setdefault(p, set()).update(rates)
            js += [job('sat', s, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, 101) for r in rates]
        for p, rates in need.items():
            gen_tables(s, [p], sorted(rates))
    return js


def choose_points_amended():
    """Amended rule (PREREGISTRATION_AMENDMENT.md): L0 = DeFT latency at rate 0.0002 (seed 101);
    Lsat = largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid for
    scenarios whose coarse Lsat is <= 0.004 and on the 0.0005 grid otherwise; loads 0.2-1.6 x Lsat
    snapped to the same grid (bumped by one step if two coincide)."""
    res = {}
    lines = ['# Load points v4, amended rule (experiments_v4.py points)', '',
             'L0 = DeFT latency at rate 0.0002 (seed 101). Lsat = largest swept rate before the mean latency first',
             'exceeds 3 x L0: 0.0001 grid where the coarse (v2-rule) Lsat was <= 0.004, 0.0005 grid otherwise.',
             'Loads 0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat on the same grid. The coarse result is in load_points_coarse.md.',
             '', '| size | scenario | grid | L0 (cycles) | Lsat | lat/L0 at Lsat | lat/L0 next | coarse Lsat | eval rates |',
             '|---|---|---|---|---|---|---|---|---|']
    for s in SIZES:
        for p, m in scenarios(s):
            def lat(r):
                f = os.path.join(raw('sat'), f'sat__DeFT__{s}-{p}__{m}__{r:.4f}__s101.json')
                return json.load(open(f))['summary']['global_average_delay_cycles']
            l0 = lat(L0_RATE)
            fr = fine_rates(s, p, m)
            grid, rates = (FINE, fr) if fr else (GRID, SAT_RATES)
            lsat, nxt = None, None
            for r in rates:
                if lat(r) > 3 * l0:
                    nxt = r
                    break
                lsat = r
            ev = []
            for mult in MULTS:
                x = snap(mult * lsat, grid)
                if ev and x <= ev[-1]:
                    x = round(ev[-1] + grid, 4)
                ev.append(x)
            res[key(s, p, m)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0}
            lines.append(f'| {s} | {p} {m} | {grid} | {l0:.1f} | {lsat} | {lat(lsat) / l0:.2f} | '
                         f'{(lat(nxt) / l0) if nxt else float("nan"):.2f} | {coarse()[key(s, p, m)]["lsat"]} | {ev} |')
    json.dump(res, open(os.path.join(RES, 'load_points.json'), 'w'), indent=1)
    open(os.path.join(RES, 'load_points.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def eval_tables():
    lp = load_points()
    for s in SIZES:
        need = {}
        for p, m in scenarios(s):
            need.setdefault(p, set()).update(lp[key(s, p, m)]['eval'])
        for p, rates in need.items():
            gen_tables(s, [p], sorted(rates))


def choose_points():
    res = {}
    lines = ['# Load points v4 (experiments_v4.py points; DeFT, seed 101)', '',
             'Criterion as v2: Lsat = largest swept rate before the mean latency first exceeds 3x the latency at',
             'rate 0.001 (packets/cycle/source; 0.0005 steps to 0.016). Evaluation points: 0.2, 0.5, 0.8, 1.0, 1.2,',
             '1.4, 1.6 x Lsat snapped to the 0.0005 grid (bumped by one step if two coincide).', '',
             '| size | scenario | L0 (cycles) | Lsat | lat/L0 at Lsat | lat/L0 next | accepted/offered at Lsat | eval rates |',
             '|---|---|---|---|---|---|---|---|']
    for s in SIZES:
        for p, m in scenarios(s):
            pts = {}
            for r in SAT_RATES:
                f = os.path.join(raw('sat'), f'sat__DeFT__{s}-{p}__{m}__{r:.4f}__s101.json')
                sm = json.load(open(f))['summary']
                pts[r] = (sm['global_average_delay_cycles'], sm['average_ip_throughput_flits_per_cycle_per_ip'] / (8 * r))
            l0 = pts[0.001][0]
            lsat, nxt = None, None
            for r in SAT_RATES:
                if pts[r][0] > 3 * l0:
                    nxt = r
                    break
                lsat = r
            ev = []
            for mult in MULTS:
                x = snap(mult * lsat)
                if ev and x <= ev[-1]:
                    x = round(ev[-1] + GRID, 4)
                ev.append(x)
            res[key(s, p, m)] = {'lsat': lsat, 'eval': ev}
            lines.append(f'| {s} | {p} {m} | {l0:.1f} | {lsat} | {pts[lsat][0] / l0:.2f} | '
                         f'{(pts[nxt][0] / l0) if nxt else float("nan"):.2f} | {pts[lsat][1]:.3f} | {ev} |')
    json.dump(res, open(os.path.join(RES, 'load_points.json'), 'w'), indent=1)
    open(os.path.join(RES, 'load_points.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


# ---- evaluation ----
def eval_jobs(seeds):
    lp = load_points()
    return [job('eval', s, v, V2.VARIANTS[v], p, m, r, sd)
            for s in SIZES for p, m in scenarios(s) for r in lp[key(s, p, m)]['eval']
            for v in EVAL_VARIANTS for sd in seeds]


def evalvl_jobs(seeds):
    lp = load_points()
    return [job('evalvl', s, 'DeFT_tm', V.inj('lut'), p, m, lp[key(s, p, m)]['eval'][i], sd)
            for s in SIZES for p, m in scenarios(s) for i in (1, 3) for sd in seeds]


def timing(nproc):
    lp = load_points()
    js = [job('timing', s, v, V2.VARIANTS[v], p, m, lp[key(s, p, m)]['eval'][i], 1001)
          for s in SIZES for p, m in scenarios(s) for i in (1, 3, 6) for v in EVAL_VARIANTS]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    per = el / len(js)
    n_eval = len(eval_jobs(SEEDS['all']))
    n_vl = len(evalvl_jobs(SEEDS['all']))
    est = per * (n_eval + n_vl) / 3600
    lines = ['# Run-time estimate v4 (experiments_v4.py timing)', '',
             f'Timing test: {len(js)} runs (seed 1001, not used elsewhere; every variant x size x scenario at the 2nd,',
             f'4th and 7th load), {nproc} processes: {el:.0f} s wall, {per:.2f} s per run (weighted towards saturation).', '',
             f'Full evaluation: {n_eval} runs ({len(EVAL_VARIANTS)} variants x 2 sizes x 7 scenarios x 7 loads x 10 seeds) '
             f'plus {n_vl} VL-proxy runs: estimated {est:.1f} h wall.',
             f'Rule (instructions): over 12 h -> seeds 1-5 first. Estimate {"exceeds" if est > 12 else "is within"} 12 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return est


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage == 'points_coarse':
        choose_points()
        sys.exit(0)
    if stage == 'points':
        choose_points_amended()
        sys.exit(0)
    if stage == 'tables':
        eval_tables()
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    js, out = {'drain': (drain_jobs, 'drain'), 'sat': (sat_jobs, 'sat'), 'satfine': (satfine_jobs, 'sat'),
               'eval': (lambda: eval_jobs(SEEDS[extra]), 'eval'),
               'evalvl': (lambda: evalvl_jobs(SEEDS[extra]), 'evalvl')}[stage]
    js = js()
    print(stage, extra, 'jobs:', len(js), flush=True)
    res = run_jobs(js, raw(out), nproc=nproc, timeout=14400)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
