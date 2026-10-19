"""v5: DeFT with a tuned LUT weight rho, re-test of the size results (results_v5/).

Stages (python3 experiments_v5.py STAGE [nproc] [extra]):
  luts      LUTs for rho in RHOS per size (uniform + traffic-matched hotspot/chipperm) -> luts/v5/
  tune      DeFT and DeFT_tm per rho on the tuning cells (seeds 101, 102)
  choose    rho* per size and variant (geometric-mean latency) -> results_v5/tuning_choice.json, tuning.md
  sat       DeFT(rho*) coarse sweep per size and scenario (seed 101)
  satfine   L0 at 0.0002 and 0.0001-step sweeps where the coarse Lsat <= 0.004 (v4 amendment)
  points    Lsat and load points (v4 amended rule) -> results_v5/load_points.json/.md; writes tables
  drain     drain tests: DeFT(rho*), DeFT_tm(rho*), CI_heur, CI_heurLA, CI_qlLA (new exit LUT)
  timing    timing test and run-time estimate
  eval      evaluation, seeds 21-30 (extra: first = 21-25 | second = 26-30 | all)
  evalvl    DeFT_tm(rho*) VL-count proxy at ~0.5 and ~1.0 x Lsat
Parameters of the late-binding variants are frozen from variants_v2.py.
"""
import csv
import itertools
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402
from experiments import EVAL_SCENARIOS as SCEN_2X2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v5')
LUTD = os.path.join(HERE, 'luts', 'v5')
REL = '../experiments/late_binding/'
GEN = os.path.join(HERE, '..', '..', 'other', 'deft_vl_lut_generator.py')
SIM = ['-sim', '10000', '-warmup', '2000']
SIZES = {'2x2': (2, 2), '3x3': (3, 3), '4x4': (4, 4)}
NORTH = {'2x2': '0x1111', '3x3': '0x111111111', '4x4': '0x1111111111111111'}
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
LUT_MASKS = {'2x2': ['0x0000', '0x1111', '0x9C63'], '3x3': ['0x0', NORTH['3x3']], '4x4': ['0x0', NORTH['4x4']]}
RHOS = ['0.01', '0.003', '0.001', '0.0003', '0.0001', '0']
TM_LUT_PATTERNS = ('hotspot', 'chipperm')      # localized / movinghot give exactly the uniform LUT
TUNE_SEEDS = (101, 102)
GRID, FINE, L0_RATE, LOW_LSAT = 0.0005, 0.0001, 0.0002, 0.004
SAT_RATES = [round(GRID * i, 4) for i in range(1, 33)] + [0.018, 0.020, 0.024]
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
SEEDS = {'first': range(21, 26), 'second': range(26, 31), 'all': range(21, 31)}
EVAL_VARIANTS = ['DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_qlLA', 'FULL_heurLA']


def scenarios(size):
    if size == '2x2':
        return list(SCEN_2X2)
    return [(p, '0x0') for p in ('uniform', 'localized', 'hotspot', 'chipperm', 'movinghot')] + \
           [(p, NORTH[size]) for p in ('uniform', 'hotspot')]


def tdir(size):
    return 'traffic' if size == '2x2' else f'traffic_{size}'


def size_args(size):
    if size == '2x2':
        return []
    cx, cy = SIZES[size]
    return ['-deft_chiplets_x', str(cx), '-deft_chiplets_y', str(cy)]


def lut_path(size, rho, pattern='uniform'):
    tag = '' if pattern not in TM_LUT_PATTERNS else f'_tm_{pattern}'
    return os.path.join(LUTD, f'lut_{size}_rho{rho}{tag}.yaml')


def key(size, p, m):
    return f'{size}__{p}__{m}'


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def choice():
    return json.load(open(os.path.join(RES, 'tuning_choice.json')))


def variant_lut(size, variant, pattern, ch=None):
    """LUT for a run: DeFT_tm -> traffic-matched LUT of its rho*; everything else (DeFT, CI exit) ->
    uniform LUT of DeFT's rho*."""
    ch = ch or choice()
    if variant == 'DeFT_tm':
        return lut_path(size, ch[size]['DeFT_tm'], pattern)
    return lut_path(size, ch[size]['DeFT'], 'uniform')


def job(stage, size, variant, vargs, p, m, rate, seed, lut):
    name = f'{stage}__{variant}__{size}-{p}__{m}__{rate:.4f}__s{seed}'
    return name, common_args(seed, m, traffic=REL + f'{tdir(size)}/{p}_{rate:.4f}.txt', lut=lut) + \
        size_args(size) + list(vargs) + SIM


def gen_tables(size, pattern, rates):
    cx, cy = SIZES[size]
    missing = [r for r in rates if not os.path.exists(os.path.join(HERE, tdir(size), f'{pattern}_{r:.4f}.txt'))]
    if missing:
        subprocess.run([sys.executable, os.path.join(HERE, 'gen_traffic.py'), os.path.join(HERE, tdir(size)),
                        '--chiplets', str(cx), str(cy), '--rates', ','.join(f'{r:.4f}' for r in missing),
                        '--patterns', pattern], check=True)


# ---- LUTs ----
def _gen(args):
    size, rho, pattern = args
    out = lut_path(size, rho, pattern)
    if os.path.exists(out):
        return out
    cx, cy = SIZES[size]
    cmd = [sys.executable, GEN, '--chiplets-x', str(cx), '--chiplets-y', str(cy), '--rho', rho, '--output', out]
    for m in LUT_MASKS[size]:
        cmd += ['--fault-mask', m]
    if pattern != 'uniform':
        cmd += ['--demand-table', os.path.join(HERE, tdir(size), f'{pattern}_0.0100.txt'),
                '--traffic-profile-id', f'table-{pattern}-time-averaged']
    subprocess.run(cmd, check=True)
    return out


def make_luts(nproc):
    os.makedirs(LUTD, exist_ok=True)
    jobs = [(s, r, p) for s in SIZES for r in RHOS for p in ('uniform',) + TM_LUT_PATTERNS]
    # slow ones first (2x2 weighted DP)
    jobs.sort(key=lambda j: (j[0] != '2x2' or j[2] == 'uniform', j))
    with Pool(nproc) as pool:
        for out in pool.imap_unordered(_gen, jobs):
            print('lut', os.path.basename(out), flush=True)


# ---- tuning ----
def tune_cells(size):
    return [('uniform', FREE[size]), ('hotspot', FREE[size]), ('chipperm', FREE[size]), ('uniform', NORTH[size])]


def tune_rates(size, p, m):
    if size == '2x2':
        return json.load(open(os.path.join(HERE, 'results_v2', 'load_points.json')))[f'{p}__{m}']['tune']
    lp = json.load(open(os.path.join(HERE, 'results_v4', 'load_points.json')))[f'{size}__{p}__{m}']
    g, lsat = lp['grid'], lp['lsat']
    t1 = round(max(g, round(0.8 * lsat / g) * g), 4)
    t2 = round(max(g, round(1.1 * lsat / g) * g), 4)
    if t2 <= lsat:
        t2 = round(lsat + g, 4)
    return [t1, t2]


def tune_jobs():
    js = []
    for s in SIZES:
        for p, m in tune_cells(s):
            rates = tune_rates(s, p, m)
            if s != '2x2':
                gen_tables(s, p, rates)
            for rho, r, seed in itertools.product(RHOS, rates, TUNE_SEEDS):
                js.append(job('tune', s, f'DeFT-rho{rho}', V2.VARIANTS['DeFT'], p, m, r, seed, lut_path(s, rho)))
                # DeFT_tm differs from DeFT only where the traffic-matched LUT differs (hotspot, chipperm);
                # on the uniform cells it is the same run and is not repeated.
                if p in TM_LUT_PATTERNS:
                    js.append(job('tune', s, f'DeFT_tm-rho{rho}', V2.VARIANTS['DeFT'], p, m, r, seed,
                                  lut_path(s, rho, p)))
    return js


def choose():
    import math
    from lut_scaling import analyze
    res = {}
    for f in os.listdir(raw('tune')):
        if f.endswith('.json'):
            _, v, sp, m, rate, seed = f[:-5].split('__')
            size, p = sp.split('-')
            d = json.load(open(os.path.join(raw('tune'), f)))['summary']
            res[(v, size, p, m, float(rate), int(seed[1:]))] = (d['global_average_delay_cycles'],
                                                                 d['average_ip_throughput_flits_per_cycle_per_ip'])
    ch, L = {}, ['# Tuning of the DeFT LUT weight rho (seeds 101, 102)', '',
                 'Cells and criterion as for the other methods: uniform, hotspot, chipperm fault-free and uniform with '
                 'one faulty VL per chiplet; loads ~0.8 and ~1.1 x Lsat (2x2: v2 tuning loads; 3x3/4x4: from the v4 '
                 'Lsat); 2 seeds = 16 runs per configuration; criterion = geometric mean of the mean latency. '
                 'DeFT_tm uses the traffic-matched LUT on hotspot/chipperm and the uniform LUT (= DeFT) on the uniform '
                 'cells. "Accepted @1.1" = geometric mean of the accepted throughput at the ~1.1 x Lsat load (the '
                 'tuning loads do not reach saturation everywhere, so this stands in for saturation throughput). '
                 'VL imbalance = analytic max/mean of the LUT fault-free (lut_scaling.py), under the LUT\'s own '
                 'demand (uniform LUT: uniform; DeFT_tm: hotspot / chipperm).', '']
    for s in SIZES:
        ch[s] = {}
        cells = tune_cells(s)
        for variant in ('DeFT', 'DeFT_tm'):
            rows = []
            for rho in RHOS:
                lat, acc = [], []
                for p, m in cells:
                    vv = f'{variant}-rho{rho}' if (variant == 'DeFT' or p in TM_LUT_PATTERNS) else f'DeFT-rho{rho}'
                    rates = tune_rates(s, p, m)
                    for r, seed in itertools.product(rates, TUNE_SEEDS):
                        lt, ac = res[(vv, s, p, m, r, seed)]
                        lat.append(lt)
                        if r == rates[-1]:
                            acc.append(ac)
                gl = math.exp(sum(math.log(x) for x in lat) / len(lat))
                ga = math.exp(sum(math.log(x) for x in acc) / len(acc))
                if variant == 'DeFT':
                    imb = f'{analyze(s, rho, "uniform")["imbalance"]:.3f}'
                else:
                    imb = ' / '.join(f'{analyze(s, rho, p)["imbalance"]:.3f}' for p in TM_LUT_PATTERNS)
                rows.append((gl, rho, ga, len(lat), imb))
            best = min(rows)
            # ties (identical LUTs give identical runs): keep the larger rho (closer to the original 0.01)
            tied = [r for r in rows if abs(r[0] - best[0]) < 1e-12]
            pick = max(tied, key=lambda r: float(r[1]))
            ch[s][variant] = pick[1]
            ref = next(r for r in rows if r[1] == '0.01')
            L += [f'## {s} {variant}', '', '| rho | runs | geo-mean latency | vs rho = 0.01 | accepted @1.1 (geo-mean) | '
                  'analytic VL imbalance |', '|---|---|---|---|---|---|']
            for gl, rho, ga, n, imb in rows:
                L.append(f'| {rho}{" (chosen)" if rho == pick[1] else ""} | {n} | {gl:.2f} | {100 * (gl / ref[0] - 1):+.2f} % | '
                         f'{ga:.4f} | {imb} |')
            L.append('')
    L += ['Budget: 6 configurations (rho values) per size and variant, 16 runs each; DeFT_tm reuses the DeFT runs on '
          'the uniform cells. The CI variants take their exit VL from the uniform LUT of DeFT\'s rho*.']
    json.dump(ch, open(os.path.join(RES, 'tuning_choice.json'), 'w'), indent=1)
    open(os.path.join(RES, 'tuning.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print(ch)


# ---- Lsat ----
def sat_jobs():
    ch = choice()
    js = []
    for s in SIZES:
        for p, m in scenarios(s):
            gen_tables(s, p, SAT_RATES) if s == '2x2' else None
            js += [job('sat', s, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, 101, variant_lut(s, 'DeFT', p, ch))
                   for r in SAT_RATES]
    return js


def lat_of(s, p, m, r):
    f = os.path.join(raw('sat'), f'sat__DeFT__{s}-{p}__{m}__{r:.4f}__s101.json')
    return json.load(open(f))['summary']['global_average_delay_cycles']


def coarse_lsat(s, p, m):
    l0 = lat_of(s, p, m, 0.001)
    lsat = None
    for r in SAT_RATES:
        if lat_of(s, p, m, r) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(s, p, m):
    lsat, nxt = coarse_lsat(s, p, m)
    if lsat > LOW_LSAT:
        return []
    return [round(FINE * i, 4) for i in range(1, int(round(nxt / FINE)) + 1)]


def satfine_jobs():
    ch = choice()
    js = []
    for s in SIZES:
        for p, m in scenarios(s):
            rates = sorted(set(fine_rates(s, p, m)) | {L0_RATE})
            gen_tables(s, p, rates)
            js += [job('sat', s, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, 101, variant_lut(s, 'DeFT', p, ch)) for r in rates]
    return js


def choose_points():
    res = {}
    L = ['# Load points v5 (DeFT with rho*, seed 101; v4 amended rule)', '',
         'L0 = DeFT latency at 0.0002; Lsat = largest swept rate before the latency first exceeds 3 x L0, on the 0.0001',
         'grid where the coarse Lsat (v2 rule) is <= 0.004 and on the 0.0005 grid otherwise; loads 0.2-1.6 x Lsat.', '',
         '| size | scenario | grid | L0 | Lsat | lat/L0 at Lsat | eval rates |', '|---|---|---|---|---|---|---|']
    for s in SIZES:
        for p, m in scenarios(s):
            l0 = lat_of(s, p, m, L0_RATE)
            fr = fine_rates(s, p, m)
            grid, rates = (FINE, fr) if fr else (GRID, SAT_RATES)
            lsat = None
            for r in rates:
                if lat_of(s, p, m, r) > 3 * l0:
                    break
                lsat = r
            ev = []
            for mult in MULTS:
                x = round(max(grid, round(mult * lsat / grid) * grid), 4)
                if ev and x <= ev[-1]:
                    x = round(ev[-1] + grid, 4)
                ev.append(x)
            res[key(s, p, m)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0}
            L.append(f'| {s} | {p} {m} | {grid} | {l0:.1f} | {lsat} | {lat_of(s, p, m, lsat) / l0:.2f} | {ev} |')
            gen_tables(s, p, ev)
    json.dump(res, open(os.path.join(RES, 'load_points.json'), 'w'), indent=1)
    open(os.path.join(RES, 'load_points.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


def load_points():
    return json.load(open(os.path.join(RES, 'load_points.json')))


# ---- drain ----
def drain_jobs():
    ch = choice()
    js = []
    for s in SIZES:
        burst = REL + f'{tdir(s)}/allpairs_burst.txt'
        for v, m, seed in itertools.product(['DeFT', 'DeFT_tm', 'CI_heur', 'CI_heurLA', 'CI_qlLA'],
                                            (FREE[s], NORTH[s]), (1, 2)):
            luts = [('', variant_lut(s, v, 'uniform', ch))] if v != 'DeFT_tm' else \
                [('-lut' + p, variant_lut(s, v, p, ch)) for p in TM_LUT_PATTERNS]
            for tag, lf in luts:
                a = common_args(seed, m, hardcoded=burst, lut=lf) + size_args(s) + V2.VARIANTS[v] + \
                    ['-drain_mode', '-drain_source_cutoff', '1000', '-drain_timeout', '1000000', '-warmup', '0',
                     '-sim', '1200000']
                js.append((f'allpairs{tag}__{v}__{s}-{m}__s{seed}', a))
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


# ---- evaluation ----
def deft_scenarios(size):
    """Scenarios where DeFT(rho*) differs from DeFT_tm(rho*): those whose traffic-matched LUT differs
    (hotspot, chipperm); elsewhere both use the uniform LUT (if the two rho* coincide)."""
    ch = choice()[size]
    if ch['DeFT'] != ch['DeFT_tm']:
        return scenarios(size)
    return [(p, m) for p, m in scenarios(size) if p in TM_LUT_PATTERNS]


def eval_jobs(seeds):
    lp, ch = load_points(), choice()
    js = []
    for s in SIZES:
        for p, m in scenarios(s):
            for r in lp[key(s, p, m)]['eval']:
                for v in EVAL_VARIANTS:
                    js += [job('eval', s, v, V2.VARIANTS[v], p, m, r, sd, variant_lut(s, v, p, ch)) for sd in seeds]
                if (p, m) in deft_scenarios(s):
                    js += [job('eval', s, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, sd, variant_lut(s, 'DeFT', p, ch))
                           for sd in seeds]
    return js


def evalvl_jobs(seeds):
    lp, ch = load_points(), choice()
    return [job('evalvl', s, 'DeFT_tm', V.inj('lut'), p, m, lp[key(s, p, m)]['eval'][i], sd,
                variant_lut(s, 'DeFT_tm', p, ch))
            for s in SIZES for p, m in scenarios(s) for i in (1, 3) for sd in seeds]


def timing(nproc):
    lp, ch = load_points(), choice()
    js = [job('timing', s, v, V2.VARIANTS[v], p, m, lp[key(s, p, m)]['eval'][i], 1001, variant_lut(s, v, p, ch))
          for s in SIZES for p, m in scenarios(s) for i in (1, 3, 6) for v in EVAL_VARIANTS]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    per = el / len(js)
    n_eval, n_vl = len(eval_jobs(SEEDS['all'])), len(evalvl_jobs(SEEDS['all']))
    est = per * (n_eval + n_vl) / 3600
    L = ['# Run-time estimate v5', '',
         f'Timing test: {len(js)} runs (seed 1001; every variant x size x scenario at the 2nd, 4th and 7th load), '
         f'{nproc} processes: {el:.0f} s wall, {per:.2f} s per run (weighted towards saturation).', '',
         f'Full evaluation: {n_eval} runs plus {n_vl} VL-proxy runs: estimated {est:.1f} h wall.',
         f'Rule: over 12 h -> seeds 21-25 first. Estimate {"exceeds" if est > 12 else "is within"} 12 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage == 'luts':
        make_luts(nproc)
        sys.exit(0)
    if stage == 'choose':
        choose()
        sys.exit(0)
    if stage == 'points':
        choose_points()
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    fn = {'tune': tune_jobs, 'sat': sat_jobs, 'satfine': satfine_jobs, 'drain': drain_jobs,
          'eval': lambda: eval_jobs(SEEDS[extra]), 'evalvl': lambda: evalvl_jobs(SEEDS[extra])}[stage]
    out = {'satfine': 'sat'}.get(stage, stage)
    js = fn()
    print(stage, extra, 'jobs:', len(js), flush=True)
    res = run_jobs(js, raw(out), nproc=nproc, timeout=14400)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
