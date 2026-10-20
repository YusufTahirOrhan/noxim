"""v8: plain DeFT(rho*) as a second reference, and the layer-weighted hop cost (results_v8/).

Stages (python3 experiments_v8.py STAGE [nproc] [extra]):
  deft         step 1: DeFT(rho*) (uniform LUT of DeFT's rho* for every scenario), seeds 31-40 -> deft_runs.csv
  regress      hop_weight_ipos 1.0 vs the v7 binary (BIN_OLD = extra): 66 configurations, default and explicit 1.0
  alpha0       CI_qlLA with alpha 0 vs CI_heurLA, both with gamma != 1 (12 pairs, 3x3 and 4x4)
  select       step 3 grid on 4x4 (seeds 101/102): CI_heurLA, CI_qlLA, FULL_qlLA x gamma {1.25, 1.5, 2, 3},
               FULL_qlLA parent, and a re-run of parent cells to check the reuse of the v7 parent rows
  extend       gamma 4 for the variants whose choice is 3
  choose       step 3 choice -> results_v8/selection_choice.json, selection.md, select_runs.csv
  drain        drain tests of the _G variants (3x3, 4x4)
  timing       timing test and estimate
  eval         evaluation of the _G variants, seeds 31-40 (extra: 4x4 | 3x3 | all)
  vlref        FULL_qlLA VL counts at 1.0 x Lsat, seeds 31-40 (the v6 column is affected by the VL-imbalance bug)
"""
import csv
import glob
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args, run_jobs  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v6 as E6  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v8')
R7 = os.path.join(HERE, 'results_v7')
SIZES = ['3x3', '4x4']
LP5 = E6.LP5
SEEDS = range(31, 41)
GAMMAS = [1.25, 1.5, 2.0, 3.0]
PARENTS = ['CI_heurLA', 'CI_qlLA', 'FULL_qlLA']
SEL_SEEDS = (101, 102)
SEL_LOADS = [2, 3, 4, 5, 6]           # 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat
LAT_LOAD = 3


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def gam(g):
    return ['-deft_lb', 'hop_weight_ipos', repr(float(g))]


def gname(parent, g):
    return f'{parent}-g{g}'


def deft_lut(size):
    return E5.lut_path(size, E6.CH5[size]['DeFT'])


def variants(size):
    """Tuned v6 variants plus the chosen _G ones (once selection_choice.json exists)."""
    tv = E6.tuned_variants(size)
    path = os.path.join(RES, 'selection_choice.json')
    if os.path.exists(path):
        ch = json.load(open(path))
        for p in PARENTS:
            tv[p + '_G'] = tv[p] + gam(ch[p]['gamma'])
    return tv


def job(stage, size, name, vargs, p, m, rate, seed, lut):
    return E6.job(stage, size, name, vargs, p, m, rate, seed, lut)


# ---- step 1 ----
def deft_jobs():
    return [job('deft', size, 'DeFT', V2.VARIANTS['DeFT'], p, m, r, s, deft_lut(size))
            for size in SIZES for p, m in E5.scenarios(size) for r in LP5[f'{size}__{p}__{m}']['eval'] for s in SEEDS]


# ---- regression (gamma = 1) ----
def regress(old_bin, nproc):
    import check_stats_regression as CSR
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = CSR.configs()
    new = os.path.join(BIN, 'noxim')
    tags = (('old', old_bin, []), ('default', new, []), ('one', new, gam(1.0)))
    jobs = [((t, b, extra, n, a), out) for t, b, extra in tags for n, a in cf]
    from multiprocessing import Pool
    with Pool(nproc) as pool:
        res = dict(pool.map(_run_tagged, jobs, chunksize=1))
    ok = {t: 0 for t, _, _ in tags[1:]}
    diffs = []
    for n, _ in cf:
        o = res[('old', n)]
        for t, _, _ in tags[1:]:
            x = res[(t, n)]
            if o and x and o['summary'] == x['summary'] and o['deft_lb'] == x['deft_lb']:
                ok[t] += 1
            else:
                diffs.append(f'{t} differs: {n}')
    L = ['# Regression of the v8 layer-weighted hop cost with hop_weight_ipos 1.0 (experiments_v8.py regress)', '',
         'Old binary: build of 4477b04 (v7, no hop weight). New binary: v8 hop-weight code. Same arguments.',
         f'Configurations: {len(cf)} (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at '
         '1.0 x Lsat of v5; seed 7; v5 rho* LUTs), as the v6 and v7 regressions.', '',
         f'- new binary, default parameters (option absent): {ok["default"]} / {len(cf)} runs with byte-identical summary '
         'and deft_lb blocks (compared as parsed JSON values)',
         f'- new binary, explicit `-deft_lb hop_weight_ipos 1.0`: {ok["one"]} / {len(cf)} identical', '']
    L += diffs or ['No differences.']
    open(os.path.join(RES, 'regression.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(out)
    return not diffs


def _run_tagged(arg):
    (tag, binary, extra, name, args), out_dir = arg
    out = os.path.join(out_dir, f'{tag}__{name}.json')
    if not os.path.exists(out):
        subprocess.run([binary] + args + extra + ['-stats_file', out], cwd=BIN, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    try:
        return (tag, name), json.load(open(out))
    except Exception:
        return (tag, name), None


# ---- alpha = 0 check ----
ALPHA0_GAMMA = 2.0


def alpha0(nproc):
    js = []
    for size, (p, m), s in itertools.product(SIZES, [('uniform', '0x0'), ('hotspot', 'north')], (1, 2, 3)):
        m = E5.NORTH[size] if m == 'north' else m
        rate = LP5[f'{size}__{p}__{m}']['eval'][3]
        c = json.load(open(os.path.join(HERE, 'results_v6', 'tuning_choice.json')))[size]['CI']
        heur = E6.heur_cfg('CI', c['heurLA_w'], c['heurLA_busy']) + gam(ALPHA0_GAMMA)
        ql0 = E6.ql_cfg('CI', c['heurLA_w'], c['heurLA_busy'], 0.0, c['qlLA_key']) + gam(ALPHA0_GAMMA)
        js.append(job('a0', size, 'CI-heurLA', heur, p, m, rate, s, E6.exit_lut(size)))
        js.append(job('a0', size, 'CI-qlLA0', ql0, p, m, rate, s, E6.exit_lut(size)))
    res = run_jobs(js, raw('alpha0'), nproc=nproc, timeout=7200)
    keys = ['delay_mean', 'delay_p99', 'vl_down_packets', 'vl_up_packets', 'adaptive_decisions', 'packets_measured']
    ok, lines = 0, []
    names = sorted(n for n in res if '__CI-heurLA__' in n)
    for n in names:
        a, b = res[n], res[n.replace('__CI-heurLA__', '__CI-qlLA0__')]
        same = a is not None and b is not None and a['summary'] == b['summary'] and \
            all(a['deft_lb'][k] == b['deft_lb'][k] for k in keys)
        ok += same
        lines.append(f'- {"IDENTICAL" if same else "DIFFERENT"} {n}')
    L = [f'# CI_qlLA with alpha = 0 vs CI_heurLA, both with hop_weight_ipos {ALPHA0_GAMMA} (v6 tuned weights; 3x3 and 4x4)',
         '', f'{ok} / {len(names)} identical (summary block + deft_lb delays, VL counts, decisions). Uniform and hotspot '
         'with one faulty VL per chiplet at 1.0 x Lsat, seeds 1-3.', ''] + lines
    open(os.path.join(RES, 'alpha0_check.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('alpha0'))
    return ok == len(names) == 12


# ---- step 3: selection ----
REUSE_CHECK = [('CI_heurLA', 'uniform', '0x0', 3, 101), ('CI_heurLA', 'chipperm', '0x0', 6, 102),
               ('CI_qlLA', 'hotspot', '0x0', 4, 101), ('CI_qlLA', 'uniform', '0x1111111111111111', 2, 102)]


def sel_cfg(name):
    tv = E6.tuned_variants('4x4')
    if '-g' in name:
        p, g = name.split('-g')
        return tv[p] + gam(float(g))
    return tv[name]


def sel_jobs(names):
    js = []
    for name in names:
        for p, m in E5.scenarios('4x4'):
            for i in SEL_LOADS:
                r = LP5[f'4x4__{p}__{m}']['eval'][i]
                js += [job('sel', '4x4', name, sel_cfg(name), p, m, r, s, E6.exit_lut('4x4')) for s in SEL_SEEDS]
    return js


def select_names():
    return [gname(p, g) for p in PARENTS for g in GAMMAS] + ['FULL_qlLA']


def reuse_jobs():
    js = []
    for v, p, m, i, s in REUSE_CHECK:
        r = LP5[f'4x4__{p}__{m}']['eval'][i]
        n, a = job('chk', '4x4', v, sel_cfg(v), p, m, r, s, E6.exit_lut('4x4'))
        js.append((n, a))
    return js


def reuse_check():
    v7 = {(r['config'], r['pattern'], r['mask'], float(r['rate']), int(r['seed'])): r
          for r in csv.DictReader(open(os.path.join(R7, 'select_runs.csv')))}
    res = run_jobs(reuse_jobs(), raw('chk'), nproc=4, timeout=7200)
    ok, lines = 0, []
    for v, p, m, i, s in REUSE_CHECK:
        r = LP5[f'4x4__{p}__{m}']['eval'][i]
        d = res[f'chk__{v}__4x4-{p}__{m}__{r:.4f}__s{s}']
        ref = v7[(v, p, m, r, s)]
        same = d is not None and repr(d['summary']['global_average_delay_cycles']) == ref['latency'] and \
            repr(d['summary']['average_ip_throughput_flits_per_cycle_per_ip']) == ref['accepted'] and \
            repr(d['deft_lb']['delay_p99']) == ref['p99']
        ok += same
        lines.append(f'{v} {p} {m} load {i} seed {s}: {"identical" if same else "DIFFERENT"}')
    shutil.rmtree(raw('chk'))
    return ok == len(REUSE_CHECK), lines


SEL_COLS = ['config', 'pattern', 'mask', 'rate', 'load_index', 'seed', 'accepted', 'latency', 'p99', 'injected',
            'received', 'dead_ends', 'source']


def select_rows():
    rows = []
    v7 = [r for r in csv.DictReader(open(os.path.join(R7, 'select_runs.csv'))) if r['config'] in ('CI_heurLA', 'CI_qlLA')]
    for r in v7:
        rows.append({k: r[k] for k in SEL_COLS if k != 'source'} | {'source': 'v7 select_runs.csv'})
    for f in sorted(glob.glob(os.path.join(raw('sel'), '*.json'))):
        _, name, sp, m, rate, seed = os.path.basename(f)[:-5].split('__')
        p = sp.split('-')[1]
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        rows.append(dict(config=name, pattern=p, mask=m, rate=repr(float(rate)),
                         load_index=LP5[f'4x4__{p}__{m}']['eval'].index(float(rate)), seed=int(seed[1:]),
                         accepted=repr(su['average_ip_throughput_flits_per_cycle_per_ip']),
                         latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         injected=su['total_injected_packets'], received=su['total_received_packets'],
                         dead_ends=l['dead_end_events'], source='v8 run'))
    path = os.path.join(RES, 'select_runs.csv')
    if os.path.exists(path):           # keep rows of earlier stages whose raw files were already deleted
        have = {(r['config'], r['pattern'], r['mask'], r['rate'], str(r['seed'])) for r in rows}
        for r in csv.DictReader(open(path)):
            if (r['config'], r['pattern'], r['mask'], r['rate'], r['seed']) not in have:
                rows.append(r)
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=SEL_COLS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    return rows


def geo(xs):
    return math.exp(sum(map(math.log, xs)) / len(xs))


def scores(rows):
    by = {}
    for r in rows:
        by.setdefault(r['config'], []).append(r)
    out = {}
    for c, rs in by.items():
        thr, lat = [], []
        for p, m in E5.scenarios('4x4'):
            cell = [r for r in rs if r['pattern'] == p and r['mask'] == m]
            per_seed = [max(float(r['accepted']) for r in cell if int(r['seed']) == s) for s in SEL_SEEDS]
            thr.append(sum(per_seed) / len(per_seed))
            l1 = [float(r['latency']) for r in cell if int(r['load_index']) == LAT_LOAD]
            lat.append(sum(l1) / len(l1))
        out[c] = dict(thr=geo(thr), lat=geo(lat), dead=sum(int(r['dead_ends']) for r in rs), n=len(rs),
                      thr_s=thr, lat_s=lat)
    return out


def pick(sc, parent):
    names = sorted([n for n in sc if n.startswith(parent + '-g')], key=lambda n: float(n.split('-g')[1]))
    base = sc[parent]
    feas = [n for n in names if sc[n]['lat'] <= 1.05 * base['lat']]
    if not feas:
        return min(names, key=lambda n: sc[n]['lat']), names, [], False
    best = max(sc[n]['thr'] for n in feas)
    tied = [n for n in feas if sc[n]['thr'] >= best * (1 - 0.005)]
    return sorted(tied, key=lambda n: (sc[n]['lat'], float(n.split('-g')[1])))[0], names, tied, True


def extension_names(sc):
    return [gname(p, 4.0) for p in PARENTS if float(pick(sc, p)[0].split('-g')[1]) == 3.0 and gname(p, 4.0) not in sc]


def choose_stage(reuse_lines):
    rows = select_rows()
    sc = scores(rows)
    choice = {}
    L = ['# v8 step 3: selection of the interposer hop weight gamma (4x4, seeds 101/102)', '',
         'Grid: CI_heurLA, CI_qlLA, FULL_qlLA (v6 tuned parameters) x gamma (`hop_weight_ipos`) {1.25, 1.5, 2, 3}, '
         'extended by gamma = 4 where the choice was 3; gamma = 1 = the parents. Cells as v7 step 3: the 7 v5 scenarios of '
         '4x4 x loads 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat x seeds 101/102 = 70 runs per configuration. Per-run data: '
         'select_runs.csv (column source).', '',
         'Parents: the CI_heurLA and CI_qlLA rows are reused from results_v7/select_runs.csv (same cells, same seeds; the '
         'binary with gamma = 1 is identical to v7, regression.md). Spot check of the reuse, 4 parent cells re-run with the '
         'v8 binary: ' + '; '.join(reuse_lines) + '. FULL_qlLA (not in v7) was run.', '',
         'Criterion (fixed in the task): maximise THR = geometric mean over the 7 scenarios of the saturation throughput '
         '(max accepted over the 5 loads, mean over the 2 seeds), subject to LAT = geometric mean over the scenarios of '
         'the mean latency at 1.0 x Lsat (mean over the 2 seeds) at most 5 % above the parent\'s. Ties (THR within 0.5 % '
         'of the best feasible): lower LAT, then smaller gamma.', '']
    for par in PARENTS:
        name, names, tied, feas = pick(sc, par)
        base = sc[par]
        g = float(name.split('-g')[1])
        choice[par] = dict(gamma=g, name=name, feasible=feas, tied=tied)
        L += [f'## {par}', '', '| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | '
              'feasible | runs | dead ends |', '|---|---|---|---|---|---|---|---|']
        for n in [par] + names:
            s = sc[n]
            tag = ' **(chosen)**' if n == name else (' (parent, gamma 1)' if n == par else '')
            fz = '-' if n == par else ('yes' if s['lat'] <= 1.05 * base['lat'] else 'no')
            L.append(f'| {n}{tag} | {s["thr"]:.5f} | {100 * (s["thr"] / base["thr"] - 1):+.2f} % | {s["lat"]:.2f} | '
                     f'{100 * (s["lat"] / base["lat"] - 1):+.2f} % | {fz} | {s["n"]} | {s["dead"]} |')
        L += ['', f'Chosen for {par}_G: gamma **{g}**' + (f' (within 0.5 % of the best feasible THR: {", ".join(tied)})'
                                                          if feas else ' (no configuration feasible; smallest LAT taken)'), '',
              f'Per scenario ({par}, parent vs chosen): saturation throughput / latency at 1.0 x Lsat', '',
              '| scenario | THR parent | THR chosen | LAT parent | LAT chosen |', '|---|---|---|---|---|']
        for j, (p, m) in enumerate(E5.scenarios('4x4')):
            L.append(f'| {p} {m if m != "0x0" else ""} | {base["thr_s"][j]:.5f} | {sc[name]["thr_s"][j]:.5f} | '
                     f'{base["lat_s"][j]:.1f} | {sc[name]["lat_s"][j]:.1f} |')
        L.append('')
    json.dump(choice, open(os.path.join(RES, 'selection_choice.json'), 'w'), indent=1)
    open(os.path.join(RES, 'selection.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


# ---- drain, timing, evaluation ----
GVARS = [p + '_G' for p in PARENTS]


def drain_jobs():
    js = []
    for size in SIZES:
        tv = variants(size)
        for v, m, s in itertools.product(GVARS, (E5.FREE[size], E5.NORTH[size]), (1, 2)):
            a = common_args(s, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt', lut=E6.exit_lut(size)) + \
                E5.size_args(size) + tv[v] + ['-drain_mode', '-drain_source_cutoff', '1000', '-drain_timeout', '1000000',
                                              '-warmup', '0', '-sim', '1200000']
            js.append((f'allpairs__{v}__{size}-{m}__s{s}', a))
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


def eval_jobs(sizes, seeds=SEEDS):
    js = []
    for size in sizes:
        tv = variants(size)
        for p, m in E5.scenarios(size):
            for r in LP5[f'{size}__{p}__{m}']['eval']:
                for v in GVARS:
                    js += [job('eval', size, v, tv[v], p, m, r, s, E6.exit_lut(size)) for s in seeds]
    return js


def vlref_jobs():
    js = []
    for size in SIZES:
        tv = E6.tuned_variants(size)
        for p, m in E5.scenarios(size):
            r = LP5[f'{size}__{p}__{m}']['eval'][LAT_LOAD]
            js += [job('vlref', size, 'FULL_qlLA', tv['FULL_qlLA'], p, m, r, s, E6.exit_lut(size)) for s in SEEDS]
    return js


def timing(nproc):
    js = []
    for size in SIZES:
        tv = variants(size)
        for p, m in E5.scenarios(size):
            for i in (1, 3, 6):
                js += [job('timing', size, v, tv[v], p, m, LP5[f'{size}__{p}__{m}']['eval'][i], 1001,
                           E6.exit_lut(size)) for v in GVARS]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs(SIZES)) + len(vlref_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v8', '', f'Timing test: {len(js)} runs (seed 1001; the three _G variants x size x scenario '
         f'at the 2nd, 4th and 7th load), {nproc} processes: {el:.0f} s wall, {el / len(js):.2f} s per run.', '',
         f'Evaluation: {len(eval_jobs(SIZES))} runs plus {len(vlref_jobs())} FULL_qlLA VL-count runs: estimated {est:.1f} h. '
         f'Rule: over 14 h -> 4x4 first, analysed first. Estimate {"exceeds" if est > 14 else "is within"} 14 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('timing'))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(extra, nproc) else 1)
    if stage == 'alpha0':
        sys.exit(0 if alpha0(nproc) else 1)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'choose':
        ok, lines = reuse_check()
        print('reuse check:', ok, lines)
        if not ok:
            sys.exit(1)
        sc = scores(select_rows())
        ext = extension_names(sc)
        if ext:
            print('extension:', ext, flush=True)
            res = run_jobs(sel_jobs(ext), raw('sel'), nproc=nproc, timeout=14400)
            print('extension done; missing:', sum(1 for v in res.values() if v is None))
        choose_stage(lines)
        sys.exit(0)
    if stage == 'deft':
        js, out = deft_jobs(), 'deft'
    elif stage == 'select':
        js, out = sel_jobs(select_names()), 'sel'
    elif stage == 'drain':
        js, out = drain_jobs(), 'drain'
    elif stage == 'eval':
        js, out = eval_jobs(SIZES if extra == 'all' else [extra]), 'eval'
    elif stage == 'vlref':
        js, out = vlref_jobs(), 'vlref'
    else:
        raise SystemExit('unknown stage')
    print(stage, extra, 'jobs:', len(js), flush=True)
    res = run_jobs(js, raw(out), nproc=nproc, timeout=14400)
    print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    if stage == 'drain':
        sys.exit(1 if drain_report(res) else 0)
