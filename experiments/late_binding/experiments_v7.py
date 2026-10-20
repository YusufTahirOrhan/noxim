"""v7: bounded-deviation entry for interposer-only late binding (results_v7/).

Stages (python3 experiments_v7.py STAGE [nproc] [extra]):
  regress      entry_bound_mode off vs the v6 binary (BIN_OLD = extra): 66 configurations, default and explicit off
  determinism  20 v6 evaluation runs re-run with the new binary, compared with results_v6/eval_runs.csv
  select       step 3 grid on 4x4 (seeds 101/102): CI_heurLA, CI_qlLA x {min, lut} x k {0, 1, 2, 4} + parents
  choose       step 3 choice -> results_v7/selection_choice.json, selection.md, select_runs.csv
  drain        drain tests of the chosen configurations (3x3, 4x4)
  timing       timing test and estimate
  eval         evaluation of CI_heurLA_B, CI_qlLA_B, seeds 31-40 (extra: 4x4 | 3x3 | all)
  vlref        VL counts at 1.0 x Lsat for DeFT_tm (DEFT_LB proxy), CI_heurLA, CI_qlLA (seeds 31-40)
The tuned parameters are v6's (results_v6/tuning_choice.json); Lsat and load points are v5's.
"""
import csv
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
import variants as V  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v6 as E6  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v7')
R6 = os.path.join(HERE, 'results_v6')
SIZES = ['3x3', '4x4']
LP5 = E6.LP5
MODES, KS = ['min', 'lut'], [0, 1, 2, 4]
PARENTS = ['CI_heurLA', 'CI_qlLA']
SEL_SEEDS = (101, 102)
SEL_LOADS = [2, 3, 4, 5, 6]           # indices of the v5 load points: 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat
LAT_LOAD = 3                          # 1.0 x Lsat
SEEDS = range(31, 41)


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def bound(mode, k):
    return ['-deft_lb', 'entry_bound_mode', mode, '-deft_lb', 'entry_bound_k', str(k)]


def bname(parent, mode, k):
    return f'{parent}-{mode}-k{k}'


def chosen():
    return json.load(open(os.path.join(RES, 'selection_choice.json')))


def variants(size):
    """Tuned v6 variants plus the chosen bounded ones (once selection_choice.json exists)."""
    tv = E6.tuned_variants(size)
    path = os.path.join(RES, 'selection_choice.json')
    if os.path.exists(path):
        ch = chosen()
        for p in PARENTS:
            tv[p + '_B'] = tv[p] + bound(ch[p]['mode'], ch[p]['k'])
    return tv


def job(stage, size, name, vargs, p, m, rate, seed, lut, extra=()):
    n, a = E6.job(stage, size, name, vargs, p, m, rate, seed, lut)
    return n, a + list(extra)


# ---- regression (entry_bound_mode off) ----
def regress(old_bin, nproc):
    import check_stats_regression as CSR
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = CSR.configs()
    tags = (('old', old_bin, []), ('default', os.path.join(BIN, 'noxim'), []),
            ('off', os.path.join(BIN, 'noxim'), bound('off', 2)))
    jobs = [(t, b, extra, n, a) for t, b, extra in tags for n, a in cf]
    from multiprocessing import Pool
    with Pool(nproc) as pool:
        res = dict(pool.map(_regress_run, [(j, out) for j in jobs], chunksize=1))
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
    L = ['# Regression of the v7 entry bound with entry_bound_mode off (experiments_v7.py regress)', '',
         'Old binary: build of 2d93fef (v6, no entry-bound code). New binary: v7 entry-bound code. Same arguments.',
         f'Configurations: {len(cf)} (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at '
         '1.0 x Lsat of v5; seed 7; v5 rho* LUTs), as the v6 statistics regression.', '',
         f'- new binary, default parameters (option absent): {ok["default"]} / {len(cf)} runs with byte-identical summary '
         'and deft_lb blocks (compared as parsed JSON values; the deft_lb block has no new field when the option is off)',
         f'- new binary, explicit `-deft_lb entry_bound_mode off -deft_lb entry_bound_k 2`: {ok["off"]} / {len(cf)} identical',
         '']
    L += diffs or ['No differences.']
    open(os.path.join(RES, 'regression.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(out)
    return not diffs


def _regress_run(arg):
    (tag, binary, extra, name, args), out_dir = arg
    out = os.path.join(out_dir, f'{tag}__{name}.json')
    if not os.path.exists(out):
        subprocess.run([binary] + args + extra + ['-stats_file', out], cwd=BIN, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200)
    try:
        return (tag, name), json.load(open(out))
    except Exception:
        return (tag, name), None


# ---- determinism (v6 runs re-run) ----
def determinism_cells():
    """20 v6 evaluation runs: sizes alternate, variants DeFT_tm / CI_heurLA / CI_qlLA cycle, scenarios, loads and
    seeds 31-40 are spread by a fixed rule."""
    cells = []
    for i in range(20):
        size = SIZES[i % 2]
        v = ['DeFT_tm', 'CI_heurLA', 'CI_qlLA'][(i // 2) % 3]
        p, m = E5.scenarios(size)[i % 7]
        r = LP5[f'{size}__{p}__{m}']['eval'][(3 * i) % 7]
        cells.append((size, v, p, m, r, 31 + i % 10))
    return cells


def v6_rows():
    out = {}
    for r in csv.DictReader(open(os.path.join(R6, 'eval_runs.csv'))):
        out[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = r
    return out


def determinism(nproc):
    js = []
    for size, v, p, m, r, s in determinism_cells():
        tv = E6.tuned_variants(size)
        js.append(job('det', size, v, tv[v], p, m, r, s, E6.variant_lut(size, v, p)))
    res = run_jobs(js, raw('det'), nproc=nproc, timeout=7200)
    v6 = v6_rows()
    fields = ['accepted', 'latency', 'p99', 'injected', 'received', 'dead_ends']
    ok, lines = 0, []
    for size, v, p, m, r, s in determinism_cells():
        n = f'det__{v}__{size}-{p}__{m}__{r:.4f}__s{s}'
        d = res.get(n)
        ref = v6[(v, f'{size}-{p}', m, r, s)]
        if d is None:
            lines.append(f'| {size} | {v} | {p} {m} | {r} | {s} | NO OUTPUT |')
            continue
        su, l = d['summary'], d['deft_lb']
        new = dict(accepted=repr(su['average_ip_throughput_flits_per_cycle_per_ip']),
                   latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                   injected=str(su['total_injected_packets']), received=str(su['total_received_packets']),
                   dead_ends=str(l['dead_end_events']))
        same = all(new[f] == ref[f] for f in fields)
        ok += same
        lines.append(f'| {size} | {v} | {p} {m} | {r} | {s} | {ref["latency"][:8]} / {new["latency"][:8]} | '
                     f'{ref["accepted"][:8]} / {new["accepted"][:8]} | {"identical" if same else "DIFFERENT"} |')
    L = ['# Determinism check (v7 step 1)', '',
         'Twenty v6 evaluation runs (seeds 31-40; DeFT_tm(rho*), CI_heurLA, CI_qlLA with the v6 tuned parameters; 3x3 '
         'and 4x4; scenarios, loads and seeds spread by a fixed rule) re-run with the v7 binary (entry_bound_mode off) and '
         'compared field by field (repr of the JSON values) with results_v6/eval_runs.csv: accepted throughput, mean '
         'latency, p99, injected, received, dead ends.', '',
         f'**{ok} / {len(lines)} identical.**', '',
         '| size | variant | scenario | rate | seed | latency v6 / v7 | accepted v6 / v7 | result |',
         '|---|---|---|---|---|---|---|---|'] + lines
    open(os.path.join(RES, 'determinism.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('det'))
    return ok == len(lines) == 20


# ---- step 3: selection ----
def select_configs():
    tv = E6.tuned_variants('4x4')
    cfg = [(p, tv[p]) for p in PARENTS]
    cfg += [(bname(p, mo, k), tv[p] + bound(mo, k)) for p in PARENTS for mo in MODES for k in KS]
    return cfg


def select_jobs():
    js = []
    for name, va in select_configs():
        for p, m in E5.scenarios('4x4'):
            for i in SEL_LOADS:
                r = LP5[f'4x4__{p}__{m}']['eval'][i]
                js += [job('sel', '4x4', name, va, p, m, r, s, E6.exit_lut('4x4')) for s in SEL_SEEDS]
    return js


SEL_COLS = ['config', 'pattern', 'mask', 'rate', 'load_index', 'seed', 'accepted', 'latency', 'p99', 'injected',
            'received', 'dead_ends', 'entry_candidates_after_mean', 'lut_fallbacks']


def select_csv():
    rows = []
    for name, _ in select_configs():
        for p, m in E5.scenarios('4x4'):
            for i in SEL_LOADS:
                r = LP5[f'4x4__{p}__{m}']['eval'][i]
                for s in SEL_SEEDS:
                    f = os.path.join(raw('sel'), f'sel__{name}__4x4-{p}__{m}__{r:.4f}__s{s}.json')
                    d = json.load(open(f))
                    su, l = d['summary'], d['deft_lb']
                    rows.append(dict(config=name, pattern=p, mask=m, rate=repr(r), load_index=i, seed=s,
                                     accepted=repr(su['average_ip_throughput_flits_per_cycle_per_ip']),
                                     latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                                     injected=su['total_injected_packets'], received=su['total_received_packets'],
                                     dead_ends=l['dead_end_events'],
                                     entry_candidates_after_mean=repr(l['entry_candidates_after_mean'] if 'entry_candidates_after_mean' in l
                                                                     else 4.0 - bin(int(m, 16) & 0xF).count('1')),
                                     lut_fallbacks=l.get('entry_bound_lut_fallbacks', '')))
    with open(os.path.join(RES, 'select_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=SEL_COLS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    return rows


def geo(xs):
    return math.exp(sum(map(math.log, xs)) / len(xs))


def select_scores(rows):
    """Per configuration: geometric mean over the 7 scenarios of (max over the 5 loads of the accepted throughput,
    mean over the 2 seeds) and of the mean latency at 1.0 x Lsat (mean over the 2 seeds); candidate count at
    1.0 x Lsat (mean over scenarios and seeds)."""
    by = {}
    for r in rows:
        by.setdefault(r['config'], []).append(r)
    out = {}
    for c, rs in by.items():
        thr, lat, cand, dead = [], [], [], 0
        for p, m in E5.scenarios('4x4'):
            cell = [r for r in rs if r['pattern'] == p and r['mask'] == m]
            per_seed = [max(float(r['accepted']) for r in cell if r['seed'] == s) for s in SEL_SEEDS]
            thr.append(sum(per_seed) / len(per_seed))
            l1 = [float(r['latency']) for r in cell if r['load_index'] == LAT_LOAD]
            lat.append(sum(l1) / len(l1))
            cand += [float(r['entry_candidates_after_mean']) for r in cell if r['load_index'] == LAT_LOAD]
        dead = sum(int(r['dead_ends']) for r in rs)
        fb = sum(int(r['lut_fallbacks'] or 0) for r in rs)
        out[c] = dict(fallbacks=fb, thr=geo(thr), lat=geo(lat), cand=sum(cand) / len(cand), dead=dead, thr_s=thr, lat_s=lat)
    return out


def choose_stage():
    rows = select_csv()
    sc = select_scores(rows)
    choice = {}
    L = ['# v7 step 3: selection of the entry bound (4x4, seeds 101/102)', '',
         'Grid: CI_heurLA and CI_qlLA (v6 tuned parameters) x entry_bound_mode {min, lut} x entry_bound_k {0, 1, 2, 4}, '
         'plus the unbounded parents. Cells: the 7 v5 scenarios of 4x4 x loads 0.8, 1.0, 1.2, 1.4, 1.6 x Lsat (v5 load '
         'points) x seeds 101/102 = 70 runs per configuration, 1260 runs. Per-run data: select_runs.csv.', '',
         'Criterion (fixed in the task before any run): maximise THR = geometric mean over the 7 scenarios of the '
         'saturation throughput (max accepted over the 5 loads, mean over the 2 seeds), subject to LAT = geometric mean '
         'over the scenarios of the mean latency at 1.0 x Lsat (mean over the 2 seeds) being at most 5 % above the '
         'unbounded parent\'s. Ties (THR within 0.5 % of the best feasible): smaller LAT, then larger k.', '',
         '"candidates" = mean number of entry candidates after bounding at 1.0 x Lsat (4 = unbounded on fault-free '
         'scenarios; 3 on the two faulty ones).', '']
    for par in PARENTS:
        base = sc[par]
        names = [bname(par, mo, k) for mo in MODES for k in KS]
        feas = [n for n in names if sc[n]['lat'] <= 1.05 * base['lat']]
        if feas:
            best = max(sc[n]['thr'] for n in feas)
            tied = [n for n in feas if sc[n]['thr'] >= best * (1 - 0.005)]
            pick = sorted(tied, key=lambda n: (sc[n]['lat'], -int(n.split('-k')[1])))[0]
        else:
            pick = min(names, key=lambda n: sc[n]['lat'])
        mo, k = pick.split('-')[1], int(pick.split('-k')[1])
        choice[par] = dict(mode=mo, k=k, name=pick, feasible=bool(feas), tied=tied if feas else [])
        L += [f'## {par}', '', '| configuration | THR (geo-mean) | THR vs parent | LAT @1.0 (geo-mean) | LAT vs parent | '
              'feasible (LAT <= +5 %) | candidates | dead ends | LUT fallbacks |', '|---|---|---|---|---|---|---|---|---|']
        for n in [par] + names:
            s = sc[n]
            tag = ' **(chosen)**' if n == pick else (' (parent)' if n == par else '')
            fz = '-' if n == par else ('yes' if s['lat'] <= 1.05 * base['lat'] else 'no')
            L.append(f'| {n}{tag} | {s["thr"]:.5f} | {100 * (s["thr"] / base["thr"] - 1):+.2f} % | {s["lat"]:.2f} | '
                     f'{100 * (s["lat"] / base["lat"] - 1):+.2f} % | {fz} | {s["cand"]:.2f} | {s["dead"]} | {s["fallbacks"]} |')
        L.append('')
        L += [f'Chosen for {par}_B: mode **{mo}**, k **{k}**' +
              (f' (configurations within 0.5 % of the best feasible THR: {", ".join(tied)})' if feas else
               ' (no configuration met the latency constraint; the one with the smallest LAT was taken)'), '']
        L += [f'Per scenario ({par}, parent vs chosen): saturation throughput / latency at 1.0 x Lsat', '',
              '| scenario | THR parent | THR chosen | LAT parent | LAT chosen |', '|---|---|---|---|---|']
        for j, (p, m) in enumerate(E5.scenarios('4x4')):
            L.append(f'| {p} {m if m != "0x0" else ""} | {base["thr_s"][j]:.5f} | {sc[pick]["thr_s"][j]:.5f} | '
                     f'{base["lat_s"][j]:.1f} | {sc[pick]["lat_s"][j]:.1f} |')
        L.append('')
    json.dump(choice, open(os.path.join(RES, 'selection_choice.json'), 'w'), indent=1)
    open(os.path.join(RES, 'selection.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


# ---- drain, timing, evaluation ----
def drain_jobs():
    js = []
    for size in SIZES:
        tv = variants(size)
        for v, m, s in itertools.product(['CI_heurLA_B', 'CI_qlLA_B'], (E5.FREE[size], E5.NORTH[size]), (1, 2)):
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
            rows.append([wl, v, sm, seed, 'NO_OUTPUT', '', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        ok = (s.get('drain_stop_reason') == 'drain_completed' and
              s['measured_received_packets'] == s['measured_injected_packets'] and l['dead_end_events'] == 0)
        fails += not ok
        rows.append([wl, v, sm, seed, s.get('drain_stop_reason'), s['measured_injected_packets'],
                     s['measured_received_packets'], l['dead_end_events'], s.get('drain_completed_cycle'),
                     l.get('entry_candidates_after_mean', ''), 'PASS' if ok else 'FAIL'])
    with open(os.path.join(RES, 'drain_summary.csv'), 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['workload', 'variant', 'size-mask', 'seed', 'stop_reason', 'injected', 'received',
                    'dead_end_events', 'drain_completed_cycle', 'entry_candidates_after_mean', 'result'])
        w.writerows(rows)
    print(f'runs={len(rows)} failures={fails}')
    return fails


EVAL_VARIANTS = ['CI_heurLA_B', 'CI_qlLA_B']


def eval_jobs(sizes, seeds=SEEDS):
    js = []
    for size in sizes:
        tv = variants(size)
        for p, m in E5.scenarios(size):
            for r in LP5[f'{size}__{p}__{m}']['eval']:
                for v in EVAL_VARIANTS:
                    js += [job('eval', size, v, tv[v], p, m, r, s, E6.exit_lut(size)) for s in seeds]
    return js


def vlref_jobs():
    js = []
    for size in SIZES:
        tv = E6.tuned_variants(size)
        for p, m in E5.scenarios(size):
            r = LP5[f'{size}__{p}__{m}']['eval'][LAT_LOAD]
            for s in SEEDS:
                js.append(job('vlref', size, 'DeFT_tm', V.inj('lut'), p, m, r, s, E6.variant_lut(size, 'DeFT_tm', p)))
                js += [job('vlref', size, v, tv[v], p, m, r, s, E6.exit_lut(size)) for v in PARENTS]
    return js


def timing(nproc):
    js = []
    for size in SIZES:
        tv = variants(size)
        for p, m in E5.scenarios(size):
            for i in (1, 3, 6):
                js += [job('timing', size, v, tv[v], p, m, LP5[f'{size}__{p}__{m}']['eval'][i], 1001,
                           E6.exit_lut(size)) for v in EVAL_VARIANTS]
    t = time.time()
    run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs(SIZES)) + len(vlref_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v7', '', f'Timing test: {len(js)} runs (seed 1001; both bounded variants x size x scenario at '
         f'the 2nd, 4th and 7th load), {nproc} processes: {el:.0f} s wall, {el / len(js):.2f} s per run.', '',
         f'Evaluation: {len(eval_jobs(SIZES))} runs plus {len(vlref_jobs())} VL-count reference runs: estimated {est:.1f} h. '
         f'Rule: over 14 h -> 4x4 first, analysed first, then 3x3. Estimate {"exceeds" if est > 14 else "is within"} 14 h.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('timing'))


def eval_cand():
    """Per-run entry-candidate counts and LUT fallbacks of the evaluation (results_v7/eval_cand.csv)."""
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('eval'), '*.json'))):
        _, v, p, m, rate, seed = os.path.basename(f)[:-5].split('__')
        l = json.load(open(f))['deft_lb']
        rows.append([v, p, m, repr(float(rate)), int(seed[1:]), repr(l['entry_candidates_before_mean']),
                     repr(l['entry_candidates_after_mean']), l['entry_bound_lut_fallbacks']])
    with open(os.path.join(RES, 'eval_cand.csv'), 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(['variant', 'pattern', 'mask', 'rate', 'seed', 'entry_candidates_before_mean',
                    'entry_candidates_after_mean', 'lut_fallbacks'])
        w.writerows(rows)
    print(f'eval_cand.csv: {len(rows)} rows; LUT fallbacks {sum(r[-1] for r in rows)}')


if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'evalcand':
        eval_cand()
        sys.exit(0)
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else 'all'
    os.makedirs(RES, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(extra, nproc) else 1)
    if stage == 'determinism':
        sys.exit(0 if determinism(nproc) else 1)
    if stage == 'choose':
        choose_stage()
        sys.exit(0)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'select':
        js, out = select_jobs(), 'sel'
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
