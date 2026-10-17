"""Second evaluation (results_v2/): stages for directions A, B, C against DeFT and DeFT_tm.

Stages (python3 experiments_v2.py STAGE [nproc] [extra]):
  sat      DeFT load sweep on every evaluation scenario (seed 101), 0.0005 steps to 0.016
  points   Lsat per scenario (largest rate before latency first exceeds 3x the latency at
           0.001) and the load points -> results_v2/load_points.json, load_points.md
  tune     per scope (CI, FULL): heuristic and lookahead heuristic, w x busy grids
  tune_ql  per scope: QL and QL-LA, alpha x key grids (local weights from the heuristics)
  drain    drain-mode correctness tests for the v2 variants -> results_v2/drain_summary.csv
  timing   short timing test and run-time estimate -> results_v2/runtime_estimate.md
  eval     v2 variants x 11 scenarios x 7 loads x seeds (extra = 'first'|'second'|'all')
  evalvl   DEFT_LB with the LUT pairs (traffic-identical to DeFT / DeFT_tm) for VL counts
Simulation: 2000 warm-up + 8000 measured cycles, as in v1.
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
from experiments import EVAL_SCENARIOS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v2')
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
GRID = 0.0005
SAT_RATES = [round(GRID * i, 4) for i in range(1, 33)] + [0.018, 0.020, 0.024]
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
TUNE_SEEDS = (101, 102)
TUNE_CELLS = [('uniform', '0x0000'), ('hotspot', '0x0000'), ('chipperm', '0x0000'), ('uniform', '0x1111')]
SEEDS = {'first': range(1, 6), 'second': range(6, 11), 'all': range(1, 11)}
W_GRID, B_GRID = (0.5, 1.0, 2.0), (0.0, 4.0, 8.0)
ALPHAS, KEYS = (0.005, 0.01, 0.02, 0.05, 0.1), (0, 1)
SCOPES = {'CI': V.CI, 'FULL': V.FULL}


def traffic(pat, rate):
    return REL + f'traffic/{pat}_{rate:.4f}.txt'


def job(stage, variant, vargs, pat, mask, rate, seed, lut=None):
    name = f'{stage}__{variant}__{pat}__{mask}__{rate:.4f}__s{seed}'
    return name, common_args(seed, mask, traffic=traffic(pat, rate), lut=lut) + list(vargs) + SIM


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def load_points():
    return json.load(open(os.path.join(RES, 'load_points.json')))


def key(pat, mask):
    return f'{pat}__{mask}'


# ---- sat / points ----
def sat_jobs():
    return [job('sat', 'DeFT', V2.VARIANTS['DeFT'], p, m, r, 101) for p, m in EVAL_SCENARIOS for r in SAT_RATES]


def snap(x):
    return round(max(GRID, round(x / GRID) * GRID), 4)


def choose_points():
    res = {}
    lines = ['# Load points v2 (experiments_v2.py points; DeFT, seed 101)', '',
             'Lsat = largest swept rate before the mean latency first exceeds 3x the latency at rate 0.001',
             '(rates in packets/cycle/source; 0.0005 steps up to 0.016). Evaluation points: 0.2, 0.5, 0.8,',
             '1.0, 1.2, 1.4, 1.6 x Lsat snapped to the 0.0005 grid (bumped by one step if two coincide).',
             'Tuning points (tuning cells only): ~0.8 and ~1.1 x Lsat, the second strictly above Lsat.', '',
             '| scenario | L0 (cycles) | Lsat | lat/L0 at Lsat | lat/L0 next | accepted/offered at Lsat | eval rates | tune rates |',
             '|---|---|---|---|---|---|---|---|']
    for p, m in EVAL_SCENARIOS:
        pts = {}
        for r in SAT_RATES:
            f = os.path.join(raw('sat'), f'sat__DeFT__{p}__{m}__{r:.4f}__s101.json')
            s = json.load(open(f))['summary']
            pts[r] = (s['global_average_delay_cycles'], s['average_ip_throughput_flits_per_cycle_per_ip'] / (8 * r))
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
        t1 = snap(0.8 * lsat)
        t2 = snap(1.1 * lsat)
        if t2 <= lsat:
            t2 = round(lsat + GRID, 4)
        res[key(p, m)] = {'lsat': lsat, 'eval': ev, 'tune': [t1, t2]}
        lines.append(f'| {p} {m} | {l0:.1f} | {lsat} | {pts[lsat][0] / l0:.2f} | '
                     f'{pts[nxt][0] / l0:.2f} | {pts[lsat][1]:.3f} | {ev} | {[t1, t2]} |')
    json.dump(res, open(os.path.join(RES, 'load_points.json'), 'w'), indent=1)
    open(os.path.join(RES, 'load_points.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


# ---- tuning ----
def heur_grid():
    g = {}
    for scope, base in SCOPES.items():
        for w, b in itertools.product(W_GRID, B_GRID):
            g[f'{scope}-heur-w{w}-b{b}'] = base + V2.heur(w, b)
            g[f'{scope}-heurLA-w{w}-b{b}'] = base + V2.heur(w, b, 1)
    return g


def ql_grid(choice):
    g = {}
    for scope, base in SCOPES.items():
        c = choice[scope]
        for a, k in itertools.product(ALPHAS, KEYS):
            g[f'{scope}-ql-a{a}-k{k}'] = base + V2.ql(c['heur_w'], c['heur_busy'], a, k)
            g[f'{scope}-qlLA-a{a}-k{k}'] = base + V2.ql(c['heurLA_w'], c['heurLA_busy'], a, k, 1)
    return g


def tune_jobs(grid):
    lp = load_points()
    return [job('tune', n, va, p, m, r, s) for n, va in grid.items() for p, m in TUNE_CELLS
            for r in lp[key(p, m)]['tune'] for s in TUNE_SEEDS]


def choose(stage):
    """Geometric-mean latency over the 16 tuning runs of each configuration, per scope and method."""
    import math
    by = {}
    for f in os.listdir(raw('tune')):
        if not f.endswith('.json'):
            continue
        name = f[:-5].split('__')[1]
        d = json.load(open(os.path.join(raw('tune'), f)))
        by.setdefault(name, []).append((d['summary']['global_average_delay_cycles'], d['deft_lb']['dead_end_events']))
    path = os.path.join(RES, 'tuning_choice.json')
    choice = json.load(open(path)) if os.path.exists(path) else {}
    methods = ('heur', 'heurLA') if stage == 'tune' else ('ql', 'qlLA')
    lines = []
    for scope in SCOPES:
        choice.setdefault(scope, {})
        for meth in methods:
            rows = []
            for n, rs in by.items():
                sc, me, *ps = n.split('-')
                if sc == scope and me == meth:
                    gm = math.exp(sum(math.log(x) for x, _ in rs) / len(rs))
                    rows.append((gm, n, len(rs), sum(d for _, d in rs)))
            rows.sort()
            lines.append(f'## {scope} {meth}: geometric mean latency over tuning runs (seeds 101, 102)')
            lines.append('')
            lines.append('| config | runs | geo-mean latency | dead ends |')
            lines.append('|---|---|---|---|')
            lines += [f'| {n} | {k} | {gm:.2f} | {d} |' for gm, n, k, d in rows]
            best = rows[0][1].split('-')
            lines.append(f'\nchosen: {rows[0][1]} ({len(rows)} configurations, {sum(r[2] for r in rows)} runs)\n')
            if meth in ('heur', 'heurLA'):
                choice[scope][f'{meth}_w'] = float(best[2][1:])
                choice[scope][f'{meth}_busy'] = float(best[3][1:])
            else:
                choice[scope][f'{meth}_alpha'] = float(best[2][1:])
                choice[scope][f'{meth}_key'] = int(best[3][1:])
    json.dump(choice, open(path, 'w'), indent=1)
    open(os.path.join(RES, f'tuning_{stage}.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(choice)


# ---- drain ----
def drain_jobs():
    masks = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    js = []
    for v, va in V2.VARIANTS.items():
        luts = [('', None)]
        if v == 'DeFT_tm':
            # allpairs is not one of the patterns: run it with each LUT that differs from DeFT's
            luts = [('-lut' + p, V2.lut_for(v, p)) for p in ('hotspot', 'chipperm')]
        for (tag, lut), m, seed in itertools.product(luts, masks, (1, 2)):
            a = common_args(seed, m, hardcoded=REL + 'traffic/allpairs_burst.txt', lut=lut) + va + \
                ['-drain_mode', '-drain_source_cutoff', '100', '-drain_timeout', '60000', '-warmup', '0', '-sim', '80000']
            js.append((f'allpairs{tag}__{v}__{m}__s{seed}', a))
        for m, pat in itertools.product(['0x0000', '0x1111', '0x9C63', '0x7BDE'], ('uniform', 'chipperm', 'hotspot')):
            a = common_args(1, m, traffic=REL + f'traffic/{pat}_0.0300.txt', lut=V2.lut_for(v, pat)) + va + \
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


# ---- evaluation ----
def eval_jobs(seeds):
    lp = load_points()
    return [job('eval', v, va, p, m, r, s, lut=V2.lut_for(v, p))
            for p, m in EVAL_SCENARIOS for r in lp[key(p, m)]['eval']
            for v, va in V2.VARIANTS.items() for s in seeds]


def evalvl_jobs(seeds):
    lp = load_points()
    js = []
    for p, m in EVAL_SCENARIOS:
        for r in lp[key(p, m)]['eval']:
            for s in seeds:
                js.append(job('evalvl', 'DeFT', V.inj('lut'), p, m, r, s))
                js.append(job('evalvl', 'DeFT_tm', V.inj('lut'), p, m, r, s, lut=V2.lut_for('DeFT_tm', p)))
    return js


def timing(nproc):
    """Run one seed of every (variant, scenario) at the 4th and 7th load (~1.0, 1.6 Lsat) and
    the 2nd load (~0.5 Lsat), time it, and extrapolate to the full evaluation."""
    lp = load_points()
    js = [job('timing', v, va, p, m, lp[key(p, m)]['eval'][i], 1001, lut=V2.lut_for(v, p))
          for p, m in EVAL_SCENARIOS for i in (1, 3, 6) for v, va in V2.VARIANTS.items()]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    per_job = el / len(js)       # wall seconds per job at this parallelism
    n_eval = sum(len(lp[key(p, m)]['eval']) for p, m in EVAL_SCENARIOS) * len(V2.VARIANTS) * 10
    n_vl = sum(len(lp[key(p, m)]['eval']) for p, m in EVAL_SCENARIOS) * 2 * 10
    est = per_job * (n_eval + n_vl) / 3600
    lines = ['# Run-time estimate (experiments_v2.py timing)', '',
             f'Timing test: {len(js)} runs (seed 1001, not used elsewhere; every variant x scenario at the',
             f'2nd, 4th and 7th load), {nproc} parallel processes: {el:.0f} s wall, {per_job:.2f} s per run.',
             'The loads are weighted towards saturation (the slow end), so the estimate leans high.', '',
             f'Full evaluation: {n_eval} runs (11 variants x 11 scenarios x 7 loads x 10 seeds) plus',
             f'{n_vl} VL-count proxy runs: estimated {est:.1f} h wall.',
             f'Decision rule (instructions): over 10 h -> seeds 1-5 first. Estimate {"exceeds" if est > 10 else "is within"} 10 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage == 'points':
        choose_points()
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage in ('choose_tune', 'choose_tune_ql'):
        choose(stage.replace('choose_', ''))
        sys.exit(0)
    if stage in ('eval', 'evalvl') and not V2.FROZEN:
        raise SystemExit('variants_v2.FROZEN is False: finish tuning first')
    if stage == 'sat':
        js, out = sat_jobs(), raw('sat')
    elif stage == 'tune':
        js, out = tune_jobs(heur_grid()), raw('tune')
    elif stage == 'tune_ql':
        js, out = tune_jobs(ql_grid(json.load(open(os.path.join(RES, 'tuning_choice.json'))))), raw('tune')
    elif stage == 'drain':
        js, out = drain_jobs(), raw('drain')
    elif stage == 'eval':
        js, out = eval_jobs(SEEDS[extra]), raw('eval')
    elif stage == 'evalvl':
        js, out = evalvl_jobs(SEEDS[extra]), raw('evalvl')
    else:
        raise SystemExit('unknown stage')
    print(stage, extra, 'jobs:', len(js), flush=True)
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
