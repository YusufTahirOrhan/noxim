"""v6: per-size tuning of the proposed methods and re-test on 3x3/4x4 (results_v6/).

Stages (python3 experiments_v6.py STAGE [nproc] [extra]):
  tune_heur   CI_heurLA, FULL_heurLA: w x busy grid (v2, 9 configurations) per size (3x3, 4x4)
  extend      one-step grid extension where a heuristic optimum lies on an extendable edge
  choose_heur choice -> results_v6/tuning_choice.json (heur part)
  tune_ql     CI_qlLA, FULL_qlLA: alpha x key grid (v2, 10 configurations), local weights from the tuned heurLA
  choose_ql   choice -> tuning_choice.json (ql part), tuning.md
  alpha0      check: QL-LA with alpha = 0 reproduces the lookahead heuristic (12 runs, 3x3 and 4x4)
  drain       drain tests with the tuned parameters (3x3, 4x4; CI_heurLA, CI_qlLA, FULL_heurLA, FULL_qlLA)
  timing      timing test and estimate
  eval        evaluation, seeds 31-40 (extra: first = 31-35 | second = 36-40 | all)
  evalvl      DeFT_tm(rho*) VL-count proxy at ~0.5 and ~1.0 x Lsat
Cells, loads, seeds and criterion of the tuning are those of the v5 rho tuning; Lsat and load points are v5's.
"""
import csv
import itertools
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v6')
SIZES = ['3x3', '4x4']
LP5 = json.load(open(os.path.join(HERE, 'results_v5', 'load_points.json')))
CH5 = json.load(open(os.path.join(HERE, 'results_v5', 'tuning_choice.json')))
W_GRID, B_GRID = [0.5, 1.0, 2.0], [0.0, 4.0, 8.0]
ALPHAS, KEYS = [0.005, 0.01, 0.02, 0.05, 0.1], [0, 1]
SCOPES = {'CI': V.CI, 'FULL': V.FULL}
TUNE_SEEDS = (101, 102)
SEEDS = {'first': range(31, 36), 'second': range(36, 41), 'all': range(31, 41)}
EVAL_VARIANTS = ['DeFT_tm', 'CI_heurLA', 'CI_qlLA', 'FULL_heurLA', 'FULL_qlLA']


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def exit_lut(size):
    """CI exit (and the LUT passed to every late-binding run): uniform LUT of DeFT's rho* (as v5)."""
    return E5.lut_path(size, CH5[size]['DeFT'])


def tune_cells(size):
    return E5.tune_cells(size)


def tune_rates(size, p, m):
    lp = LP5[f'{size}__{p}__{m}']
    g, lsat = lp['grid'], lp['lsat']
    t1 = round(max(g, round(0.8 * lsat / g) * g), 4)
    t2 = round(max(g, round(1.1 * lsat / g) * g), 4)
    if t2 <= lsat:
        t2 = round(lsat + g, 4)
    return [t1, t2]


def job(stage, size, name, vargs, p, m, rate, seed, lut):
    n = f'{stage}__{name}__{size}-{p}__{m}__{rate:.4f}__s{seed}'
    return n, common_args(seed, m, traffic=E5.REL + f'{E5.tdir(size)}/{p}_{rate:.4f}.txt', lut=lut) + \
        E5.size_args(size) + list(vargs) + E5.SIM


def heur_cfg(scope, w, b):
    return SCOPES[scope] + V2.heur(w, b, 1)


def ql_cfg(scope, w, b, a, k):
    return SCOPES[scope] + V2.ql(w, b, a, k, 1)


def tune_jobs(grid):
    js = []
    for size, name, va in grid:
        for p, m in tune_cells(size):
            rates = tune_rates(size, p, m)
            E5.gen_tables(size, p, rates)
            for r, s in itertools.product(rates, TUNE_SEEDS):
                js.append(job('tune', size, name, va, p, m, r, s, exit_lut(size)))
    return js


def heur_grid(ws=W_GRID, bs=B_GRID, sizes=SIZES, scopes=SCOPES):
    return [(z, f'{sc}-heurLA-w{w}-b{b}', heur_cfg(sc, w, b)) for z in sizes for sc in scopes for w in ws for b in bs]


def results():
    out = {}
    for f in os.listdir(raw('tune')):
        if f.endswith('.json'):
            _, name, sp, m, rate, seed = f[:-5].split('__')
            size, p = sp.split('-')
            d = json.load(open(os.path.join(raw('tune'), f)))['summary']
            out[(name, size, p, m, float(rate), int(seed[1:]))] = (d['global_average_delay_cycles'],
                                                                  d['average_ip_throughput_flits_per_cycle_per_ip'])
    return out


def score(res, size, name):
    lat, acc = [], []
    for p, m in tune_cells(size):
        rates = tune_rates(size, p, m)
        for r, s in itertools.product(rates, TUNE_SEEDS):
            lt, ac = res[(name, size, p, m, r, s)]
            lat.append(lt)
            if r == rates[-1]:
                acc.append(ac)
    return math.exp(sum(map(math.log, lat)) / len(lat)), math.exp(sum(map(math.log, acc)) / len(acc)), len(lat)


def heur_names(size, scope, res):
    return sorted({n for (n, z, *_r) in res if z == size and n.startswith(f'{scope}-heurLA-')})


def parse_wb(name):
    parts = name.split('-')
    return float(parts[2][1:]), float(parts[3][1:])


def extension_grid(res):
    """One step beyond an edge optimum (w: x2 above 2 / x0.5 below 0.5; busy: +4 above 8; busy 0 is a hard bound)."""
    ext = []
    for size, scope in itertools.product(SIZES, SCOPES):
        names = heur_names(size, scope, res)
        best = min(names, key=lambda n: score(res, size, n)[0])
        w, b = parse_wb(best)
        ws = sorted({x for x, _ in map(parse_wb, names)})
        bs = sorted({y for _, y in map(parse_wb, names)})
        new_w = [ws[-1] * 2] if w == ws[-1] else ([ws[0] / 2] if w == ws[0] else [])
        new_b = [bs[-1] + 4] if b == bs[-1] else []
        cfg = [(nw, nb) for nw in new_w for nb in bs] + [(nw, nb) for nw in ws for nb in new_b] + \
              [(nw, nb) for nw in new_w for nb in new_b]
        ext += [(size, f'{scope}-heurLA-w{x}-b{y}', heur_cfg(scope, x, y)) for x, y in cfg
                if f'{scope}-heurLA-w{x}-b{y}' not in names]
    return ext


def choose(part):
    res = results()
    path = os.path.join(RES, 'tuning_choice.json')
    ch = json.load(open(path)) if os.path.exists(path) else {}
    for size, scope in itertools.product(SIZES, SCOPES):
        ch.setdefault(size, {}).setdefault(scope, {})
        if part == 'heur':
            names = heur_names(size, scope, res)
            best = min(names, key=lambda n: score(res, size, n)[0])
            w, b = parse_wb(best)
            ch[size][scope].update(heurLA_w=w, heurLA_busy=b)
        else:
            names = sorted({n for (n, z, *_r) in res if z == size and n.startswith(f'{scope}-qlLA-')})
            best = min(names, key=lambda n: score(res, size, n)[0])
            a, k = best.split('-')[2:4]
            ch[size][scope].update(qlLA_alpha=float(a[1:]), qlLA_key=int(k[1:]))
    json.dump(ch, open(path, 'w'), indent=1)
    if part == 'ql':
        write_tuning_md(res, ch)
    print(json.dumps(ch, indent=1))


def write_tuning_md(res, ch):
    v2 = V2.PARAMS
    L = ['# v6 tuning of the proposed methods per size (seeds 101, 102)', '',
         'Protocol of the v5 rho tuning: uniform, hotspot, chipperm fault-free and uniform with one faulty VL per chiplet; '
         '~0.8 and ~1.1 x Lsat (v5 load points); 2 seeds = 16 runs per configuration; criterion = geometric mean of the '
         'mean latency. "accepted @1.1" = geometric mean of the accepted throughput at the ~1.1 x Lsat load. CI takes its '
         'exit from the uniform LUT of DeFT\'s rho* of the size. QL-LA inherits the tuned (w, busy) of the lookahead '
         'heuristic of its scope and size.', '']
    for size, scope in itertools.product(SIZES, SCOPES):
        for kind in ('heurLA', 'qlLA'):
            names = sorted({n for (n, z, *_r) in res if z == size and n.startswith(f'{scope}-{kind}-')})
            rows = sorted((score(res, size, n), n) for n in names)
            if kind == 'heurLA':
                ref = f'{scope}-heurLA-w{v2[scope]["heurLA_w"]}-b{v2[scope]["heurLA_busy"]}'
            else:
                w, b = ch[size][scope]['heurLA_w'], ch[size][scope]['heurLA_busy']
                ref = None
            L += [f'## {size} {scope}_{kind}', '', '| configuration | runs | geo-mean latency | vs best | accepted @1.1 |',
                  '|---|---|---|---|---|']
            for (g, a, n_), name in rows:
                tag = ' **(chosen)**' if name == rows[0][1] else ''
                tag += ' (2x2 parameters)' if name == ref else ''
                L.append(f'| {name}{tag} | {n_} | {g:.2f} | {100 * (g / rows[0][0][0] - 1):+.2f} % | {a:.4f} |')
            L.append('')
    L += ['## Distance of the tuned optimum from the 2x2 parameters', '',
          '| size | scope | heurLA (w, busy): 2x2 -> tuned | criterion of the 2x2 heurLA setting vs tuned | qlLA (alpha, key): 2x2 -> tuned |',
          '|---|---|---|---|---|']
    for size, scope in itertools.product(SIZES, SCOPES):
        c = ch[size][scope]
        ref = f'{scope}-heurLA-w{v2[scope]["heurLA_w"]}-b{v2[scope]["heurLA_busy"]}'
        best = f'{scope}-heurLA-w{c["heurLA_w"]}-b{c["heurLA_busy"]}'
        d = 100 * (score(res, size, ref)[0] / score(res, size, best)[0] - 1)
        L.append(f'| {size} | {scope} | ({v2[scope]["heurLA_w"]}, {v2[scope]["heurLA_busy"]}) -> ({c["heurLA_w"]}, {c["heurLA_busy"]}) | '
                 f'{d:+.2f} % | ({v2[scope]["qlLA_alpha"]}, {v2[scope]["qlLA_key"]}) -> ({c["qlLA_alpha"]}, {c["qlLA_key"]}) |')
    L.append('')
    n_cfg = len({n for (n, *_r) in res})
    L += [f'Budget: {len(res)} tuning runs in total ({n_cfg} configuration names over both sizes); per size and scope 9 '
          'heuristic configurations (+ the extension, if any) and 10 learner configurations.']
    open(os.path.join(RES, 'tuning.md'), 'w', newline='\n').write('\n'.join(L) + '\n')


def ql_grid():
    ch = json.load(open(os.path.join(RES, 'tuning_choice.json')))
    return [(z, f'{sc}-qlLA-a{a}-k{k}', ql_cfg(sc, ch[z][sc]['heurLA_w'], ch[z][sc]['heurLA_busy'], a, k))
            for z in SIZES for sc in SCOPES for a in ALPHAS for k in KEYS]


# ---- tuned variants ----
def tuned_variants(size):
    c = json.load(open(os.path.join(RES, 'tuning_choice.json')))[size]
    out = {'DeFT_tm': V2.VARIANTS['DeFT']}
    for sc in SCOPES:
        p = c[sc]
        out[f'{sc}_heurLA'] = heur_cfg(sc, p['heurLA_w'], p['heurLA_busy'])
        out[f'{sc}_qlLA'] = ql_cfg(sc, p['heurLA_w'], p['heurLA_busy'], p['qlLA_alpha'], p['qlLA_key'])
    return out


def variant_lut(size, v, p):
    if v == 'DeFT_tm':
        return E5.lut_path(size, CH5[size]['DeFT_tm'], p)
    return exit_lut(size)


def alpha0_jobs():
    js = []
    for size, (p, m), s, sc in itertools.product(SIZES, [('uniform', '0x0'), ('hotspot', E5.NORTH['4x4'])], (1, 2, 3),
                                                  ['FULL']):
        m = m if size == '4x4' or m == '0x0' else E5.NORTH[size]
        rate = LP5[f'{size}__{p}__{m}']['eval'][3]
        c = json.load(open(os.path.join(RES, 'tuning_choice.json')))[size][sc]
        for tag, va in (('heurLA', heur_cfg(sc, c['heurLA_w'], c['heurLA_busy'])),
                        ('qlLA0', ql_cfg(sc, c['heurLA_w'], c['heurLA_busy'], 0.0, c['qlLA_key']))):
            js.append(job('a0', size, f'{sc}-{tag}', va, p, m, rate, s, exit_lut(size)))
    return js


def alpha0_report(res):
    keys = ['delay_mean', 'delay_p99', 'vl_down_packets', 'vl_up_packets', 'adaptive_decisions', 'packets_measured']
    ok, lines = 0, []
    names = sorted(n for n in res if '-heurLA__' in n)
    for n in names:
        a, b = res[n], res[n.replace('-heurLA__', '-qlLA0__')]
        same = a['summary'] == b['summary'] and all(a['deft_lb'][k] == b['deft_lb'][k] for k in keys)
        ok += same
        lines.append(f'- {"IDENTICAL" if same else "DIFFERENT"} {n}')
    L = ['# FULL_qlLA with alpha = 0 vs FULL_heurLA (tuned weights), 3x3 and 4x4', '',
         f'{ok} / {len(names)} identical (summary block + deft_lb delays, VL counts, decisions).', ''] + lines
    open(os.path.join(RES, 'alpha0_check.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return ok == len(names)


def drain_jobs():
    js = []
    for size in SIZES:
        tv = tuned_variants(size)
        for v, m, s in itertools.product(['CI_heurLA', 'CI_qlLA', 'FULL_heurLA', 'FULL_qlLA'],
                                         (E5.FREE[size], E5.NORTH[size]), (1, 2)):
            a = common_args(s, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt', lut=exit_lut(size)) + \
                E5.size_args(size) + tv[v] + ['-drain_mode', '-drain_source_cutoff', '1000', '-drain_timeout', '1000000',
                                              '-warmup', '0', '-sim', '1200000']
            js.append((f'allpairs__{v}__{size}-{m}__s{s}', a))
    return js


def eval_jobs(seeds):
    js = []
    for size in SIZES:
        tv = tuned_variants(size)
        for p, m in E5.scenarios(size):
            for r in LP5[f'{size}__{p}__{m}']['eval']:
                for v in EVAL_VARIANTS:
                    js += [job('eval', size, v, tv[v], p, m, r, s, variant_lut(size, v, p)) for s in seeds]
    return js


def evalvl_jobs(seeds):
    return [job('evalvl', size, 'DeFT_tm', V.inj('lut'), p, m, LP5[f'{size}__{p}__{m}']['eval'][i], s,
                variant_lut(size, 'DeFT_tm', p))
            for size in SIZES for p, m in E5.scenarios(size) for i in (1, 3) for s in seeds]


def timing(nproc):
    js = []
    for size in SIZES:
        tv = tuned_variants(size)
        for p, m in E5.scenarios(size):
            for i in (1, 3, 6):
                js += [job('timing', size, v, tv[v], p, m, LP5[f'{size}__{p}__{m}']['eval'][i], 1001,
                           variant_lut(size, v, p)) for v in EVAL_VARIANTS]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs(SEEDS['all'])) + len(evalvl_jobs(SEEDS['all']))
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v6', '', f'Timing test: {len(js)} runs (seed 1001; every variant x size x scenario at the 2nd, '
         f'4th and 7th load), {nproc} processes: {el:.0f} s wall, {el / len(js):.2f} s per run.', '',
         f'Full evaluation: {n} runs (incl. VL proxies): estimated {est:.1f} h. Rule: over 30 h -> seeds 31-35 first. '
         f'Estimate {"exceeds" if est > 30 else "is within"} 30 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


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


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage in ('choose_heur', 'choose_ql'):
        choose(stage.split('_')[1])
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'tune_heur':
        js, out = tune_jobs(heur_grid()), 'tune'
    elif stage == 'extend':
        ext = extension_grid(results())
        print('extension configurations:', [n for _, n, _ in ext])
        js, out = tune_jobs(ext), 'tune'
    elif stage == 'tune_ql':
        js, out = tune_jobs(ql_grid()), 'tune'
    elif stage == 'alpha0':
        js, out = alpha0_jobs(), 'alpha0'
    elif stage == 'drain':
        js, out = drain_jobs(), 'drain'
    elif stage == 'eval':
        js, out = eval_jobs(SEEDS[extra]), 'eval'
    elif stage == 'evalvl':
        js, out = evalvl_jobs(SEEDS[extra]), 'evalvl'
    else:
        raise SystemExit('unknown stage')
    print(stage, extra, 'jobs:', len(js), flush=True)
    res = run_jobs(js, raw(out), nproc=nproc, timeout=14400)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
    if stage == 'alpha0':
        sys.exit(0 if alpha0_report(res) else 1)
