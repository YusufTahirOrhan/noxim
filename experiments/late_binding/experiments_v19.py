"""v19 (Part K): DeFT's boundary round-robin as in its paper, -deft_vn_rr 1 (results_v19_vnrr/).

Stages (python3 experiments_v19.py STAGE [nproc] [extra]; --shard i/n accepted):
  regress   options off: bin/noxim against the 3ac1bae and d6f65f8 builds (extra = "BIN1,BIN2") on the 84-configuration set, whole stats
            files byte by byte; also with -deft_vn_rr 0 -deft_lb decision_delay 0 given explicitly -> regression.md
  drain     K2: drain tests of the 8 VN-based methods with -deft_vn_rr 1 (v10 protocol and masks) -> drain_summary.csv
  vcbal     K3: VC split per link class, 2x2 and 4x4, uniform, 1.0 x old Lsat, seeds 41-43, 3 methods with and without the option
  sat       K4: DeFT(rho*) with the option, coarse sweep (seed 101), then the fine sweep where the coarse Lsat <= 0.004
  points    K4: Lsat and the 7 loads (v5 rule) -> load_points_rr.json, load_points_rr.md
  timing    K5: timing test and estimate
  eval      K5: evaluation, seeds 61-70
  csv       K5: eval_runs.csv; raw outputs deleted
  fsweep    K6: DeFT(rho*) with the option on the v11 masks at the 7 new load points, uniform and hotspot, seeds 51-52
  fchoose   K6: test load per (size, k, pattern), v14 rule -> fault_load_choice.json / .md
  feval     K6: 8 methods at the chosen load, seeds 71-75
  fcsv      K6: fault_runs.csv; raw outputs deleted
  apps      K7: PARSEC, single application, 9 benchmarks x 2 masks x 3 methods x seeds 41-43
  appscsv   K7: app_runs.csv; raw outputs deleted
Raw outputs stay under ~/lbraw/v19 (not in the repository). Method parameters: experiments_v10.methods, unchanged (tuned without the round-robin).
"""
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v11 as E11  # noqa: E402
import experiments_v13 as E13  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v19_vnrr')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v19')
SIZES = ['2x2', '3x3', '4x4']
RR = ['-deft_vn_rr', '1']
VN_METHODS = ['DeFT', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
NO_VN = ['MTR', 'RC']
REF_NORR = 'DeFT_noRR'
SEEDS = range(61, 71)
FAULT_SEEDS = (51, 52)
FAULT_CONF_SEEDS = range(71, 76)
APP_METHODS = ['DeFT', 'CI_qlLA_G', 'FULL_qlLA_G']
APP_SEEDS = (41, 42, 43)
MULTS = E5.MULTS
NL = chr(10)


def raw(stage):
    return os.path.join(RAW, stage)


def args_of(size, v):
    """Arguments of a method of this round: VN-based methods with the option, MTR and RC as they are, DeFT_noRR = DeFT without it."""
    mm = E10.methods(size)
    if v == REF_NORR:
        return list(mm['DeFT'])
    if v in NO_VN:
        return list(mm[v])
    return list(mm[v]) + RR


def md5(f):
    return subprocess.run(['md5sum', f], capture_output=True, text=True).stdout.split()[0]


# ---- regression ----
def regress(refs, nproc):
    import check_stats_regression as CSR
    from multiprocessing import Pool
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in SIZES:
        mm = E10.methods(size)
        r = E10.LP5[f'{size}__uniform__{E5.FREE[size]}']['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append((f'{v}__{size}', a))
    new = os.path.join(BIN, 'noxim')
    explicit = ['-deft_vn_rr', '0', '-deft_lb', 'decision_delay', '0', '-deft_lb', 'hop_stats', '0']
    tags = [('ref0', refs[0], []), ('ref1', refs[1], []), ('new', new, []), ('explicit', new, explicit)]
    jobs = [((t, b, ex, n, a), out) for t, b, ex in tags for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = {t: 0 for t, _, _ in tags[1:]}, []
    for n, _ in cf:
        base = os.path.join(out, f'ref0__{n}.json')
        for t, _, _ in tags[1:]:
            f = os.path.join(out, f'{t}__{n}.json')
            if os.path.exists(base) and os.path.exists(f) and open(base, 'rb').read() == open(f, 'rb').read():
                ok[t] += 1
            else:
                diffs.append(f'- {t} differs: {n}')
    L = ['# Regression with the v19 and v20 options off (experiments_v19.py regress)', '',
         f'References: 3ac1bae build md5 {md5(refs[0])}; d6f65f8 build md5 {md5(refs[1])}. New binary: md5 {md5(new)} (code with -deft_vn_rr, -deft_lb decision_delay, -deft_lb hop_stats).',
         f'Configurations: {len(cf)} = the 84-configuration set of v14-v18. Comparison: the whole stats JSON file, byte by byte, against the 3ac1bae build.', '',
         f'* d6f65f8 build: **{ok["ref1"]} / {len(cf)} byte-identical**.',
         f'* New binary, options absent: **{ok["new"]} / {len(cf)} byte-identical**.',
         f'* New binary, `-deft_vn_rr 0 -deft_lb decision_delay 0 -deft_lb hop_stats 0` given: **{ok["explicit"]} / {len(cf)} byte-identical**.', ''] + (diffs or ['No differences.'])
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return not diffs


# ---- K2 drain ----
def drain_jobs(methods=VN_METHODS, extra=RR):
    """v10 protocol and masks (experiments_v10.drain_jobs), with the option."""
    js = []
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    for size in SIZES:
        mm = E10.methods(size)
        for v in methods:
            a0 = list(mm[v]) + list(extra)
            if size == '2x2':
                for m in masks2:
                    for seed in (1, 2):
                        a = common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=None) + a0 + E10.DRAIN_ALLPAIRS_2X2
                        js.append((f'allpairs__{v}__2x2-{m}__s{seed}', a))
                for m in ['0x0000', '0x1111', '0x9C63', '0x7BDE']:
                    for pat in ('uniform', 'chipperm', 'hotspot'):
                        a = common_args(1, m, traffic=E5.REL + f'traffic/{pat}_0.0300.txt', lut=None) + a0 + E10.DRAIN_OVERSAT_2X2
                        js.append((f'{pat}0.03__{v}__2x2-{m}__s1', a))
                continue
            for m in [E5.FREE[size], E5.NORTH[size]]:
                for seed in (1, 2):
                    a = common_args(seed, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt', lut=E10.lut(size, v, 'uniform')) + \
                        E5.size_args(size) + a0 + E10.DRAIN_ALLPAIRS
                    js.append((f'allpairs__{v}__{size}-{m}__s{seed}', a))
                for pat in ('uniform', 'chipperm', 'hotspot'):
                    key = f'{size}__{pat}__{m}' if f'{size}__{pat}__{m}' in E10.LP5 else f'{size}__{pat}__{E5.FREE[size]}'
                    r = E10.LP5[key]['eval'][6]
                    a = common_args(1, m, traffic=E5.REL + f'{E5.tdir(size)}/{pat}_{r:.4f}.txt', lut=E10.lut(size, v, pat)) + \
                        E5.size_args(size) + a0 + E10.DRAIN_OVERSAT
                    js.append((f'{pat}{r:.4f}__{v}__{size}-{m}__s1', a))
    return js


def drain_report(res, path):
    rows, fails = [], 0
    for name in sorted(res):
        d = res[name]
        wl, v, sm, seed = name.split('__')
        if d is None:
            rows.append([wl, v, sm, seed, 'NO_OUTPUT', '', '', '', '', 'FAIL'])
            fails += 1
            continue
        s, l = d['summary'], d['deft_lb']
        ok = (s.get('drain_stop_reason') == 'drain_completed' and s['measured_received_packets'] == s['measured_injected_packets'] and
              l['dead_end_events'] == 0)
        fails += not ok
        rows.append([wl, v, sm, seed, s.get('drain_stop_reason'), s['measured_injected_packets'], s['measured_received_packets'],
                     l['dead_end_events'], s.get('drain_completed_cycle'), 'PASS' if ok else 'FAIL'])
    with open(path, 'w', newline='') as f:
        w = csv.writer(f, lineterminator=NL)
        w.writerow(['workload', 'variant', 'size-mask', 'seed', 'stop_reason', 'injected', 'received', 'dead_end_events', 'drain_completed_cycle', 'result'])
        w.writerows(rows)
    by = {}
    for r in rows:
        by.setdefault(r[1], [0, 0])
        by[r[1]][0] += 1
        by[r[1]][1] += r[-1] == 'PASS'
    print(f'runs={len(rows)} failures={fails}', {k: f'{p}/{n}' for k, (n, p) in by.items()})
    return fails


# ---- K3 VC balance ----
CLASSES = ['chip_towards', 'chip_away', 'ipos', 'vl_down', 'vl_up']
CNAME = {'chip_towards': 'chiplet, towards VL', 'chip_away': 'chiplet, away from VL', 'ipos': 'interposer', 'vl_down': 'Down VL', 'vl_up': 'Up VL'}
VCB = ['DeFT', 'CI_qlLA_G', 'FULL_qlLA_G']


def vcbal(nproc):
    out = raw('vcbal')
    os.makedirs(out, exist_ok=True)
    js = []
    for z in ('2x2', '4x4'):
        r = E10.LP5[f'{z}__uniform__{E5.FREE[z]}']['eval'][3]
        for v in VCB:
            for tag, ex in (('off', []), ('on', RR)):
                for s in (41, 42, 43):
                    n = f'vcb__{v}__{z}__{tag}__s{s}'
                    _, a = E5.job('vcb', z, v, list(E10.methods(z)[v]) + ex, 'uniform', E5.FREE[z], r, s, E10.lut(z, 'DeFT', 'uniform'))
                    js.append((n, a + ['-deft_lb', 'vc_stats', os.path.join(out, n + '.vc.json')]))
    run_jobs(js, out, nproc=nproc, timeout=7200)
    L = ['# K3: VC split per link class with and without the round-robin (exploratory)', '',
         'Uniform, 1.0 x the old Lsat (v5 load points), seeds 41-43. Each cell: share of flits VC0:VC1 (%), then VC-wait cycles per flit. Link classes as v17.', '',
         '| size | method | option | ' + ' | '.join(CNAME[c] for c in CLASSES) + ' | latency |', '|---|---|---|' + '---|' * (len(CLASSES) + 1)]
    rows = []
    for z in ('2x2', '4x4'):
        for v in VCB:
            for tag in ('off', 'on'):
                cells, lat = [], []
                agg = {c: [0, 0, 0] for c in CLASSES}
                for s in (41, 42, 43):
                    n = f'vcb__{v}__{z}__{tag}__s{s}'
                    d = json.load(open(os.path.join(out, n + '.vc.json')))
                    lat.append(json.load(open(os.path.join(out, n + '.json')))['summary']['global_average_delay_cycles'])
                    for l in d['links']:
                        a = agg[l['cls']]
                        a[0] += l['f'][0]
                        a[1] += l['f'][1]
                        a[2] += sum(l['held']) + sum(l['nocredit'])
                for c in CLASSES:
                    a = agg[c]
                    t = a[0] + a[1]
                    cells.append(f'{100 * a[0] / t:.0f}:{100 * a[1] / t:.0f} / {a[2] / t:.2f}')
                    rows.append(dict(size=z, method=v, option=tag, cls=c, f0=a[0], f1=a[1], wait=a[2]))
                L.append(f'| {z} | {v} | {tag} | ' + ' | '.join(cells) + f' | {sum(lat) / 3:.1f} |')
    open(os.path.join(RES, 'vc_balance.md'), 'w', newline=NL).write(NL.join(L) + NL)
    with open(os.path.join(RES, 'vc_balance_runs.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(NL.join(L))
    shutil.rmtree(out)


# ---- K4 load points (v5 rule, seed 101) ----
def sat_name(s, p, m, r):
    return f'sat__DeFT__{s}-{p}__{m}__{r:.4f}__s101'


def sat_job(s, p, m, r):
    return E5.job('sat', s, 'DeFT', args_of(s, 'DeFT'), p, m, r, 101, E10.lut(s, 'DeFT', p))


def lat_of(s, p, m, r):
    return json.load(open(os.path.join(raw('sat'), sat_name(s, p, m, r) + '.json')))['summary']['global_average_delay_cycles']


def coarse_lsat(s, p, m):
    l0 = lat_of(s, p, m, 0.001)
    lsat = None
    for r in E5.SAT_RATES:
        if lat_of(s, p, m, r) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(s, p, m):
    lsat, nxt = coarse_lsat(s, p, m)
    if lsat > E5.LOW_LSAT:
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    js = []
    for s in SIZES:
        for p, m in E5.scenarios(s):
            E5.gen_tables(s, p, E5.SAT_RATES)
            js += [sat_job(s, p, m, r) for r in E5.SAT_RATES]
    run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    js = []
    for s in SIZES:
        for p, m in E5.scenarios(s):
            rates = sorted(set(fine_rates(s, p, m)) | {E5.L0_RATE})
            E5.gen_tables(s, p, rates)
            js += [sat_job(s, p, m, r) for r in rates]
    res = run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    print('fine runs', len(js), 'missing', sum(1 for v in res.values() if v is None))


def points():
    res = {}
    old = E10.LP5
    L = ['# Load points with the round-robin (DeFT(rho*) with -deft_vn_rr 1, seed 101; v5 rule)', '',
         'L0 = DeFT latency at 0.0002; Lsat = largest swept rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse Lsat is <= 0.004 and on the 0.0005 grid otherwise; loads 0.2-1.6 x Lsat.', '',
         '| size | scenario | grid | L0 | Lsat | old Lsat (v5) | Lsat new / old | lat/L0 at Lsat | eval rates |', '|---|---|---|---|---|---|---|---|---|']
    for s in SIZES:
        for p, m in E5.scenarios(s):
            l0 = lat_of(s, p, m, E5.L0_RATE)
            fr = fine_rates(s, p, m)
            grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
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
            k = E5.key(s, p, m)
            res[k] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0}
            ol = old[k]['lsat']
            L.append(f'| {s} | {p} {m} | {grid} | {l0:.1f} | {lsat} | {ol} | {lsat / ol:.3f} | {lat_of(s, p, m, lsat) / l0:.2f} | {ev} |')
            E5.gen_tables(s, p, ev)
    json.dump(res, open(os.path.join(RES, 'load_points_rr.json'), 'w'), indent=1)
    open(os.path.join(RES, 'load_points_rr.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('sat'))


def lp():
    return json.load(open(os.path.join(RES, 'load_points_rr.json')))


# ---- K5 evaluation ----
def scen(size, v):
    sc = E5.scenarios(size)
    if v in NO_VN:
        sc = [(p, m) for p, m in sc if int(m, 16) == 0]
    return sc


def eval_jobs(seeds=SEEDS):
    P = lp()
    js = []
    for z in SIZES:
        for v in VN_METHODS + NO_VN + [REF_NORR]:
            a0 = args_of(z, v)
            lutv = 'DeFT' if v == REF_NORR else v
            for p, m in scen(z, v):
                for r in P[E5.key(z, p, m)]['eval']:
                    js += [E5.job('eval', z, v, a0, p, m, r, s, E10.lut(z, lutv, p)) for s in seeds]
    return js


def timing(nproc):
    P = lp()
    js = []
    for z in SIZES:
        for v in VN_METHODS + NO_VN:
            for p, m in scen(z, v):
                for i in (1, 3, 6):
                    js.append(E5.job('timing', z, v, args_of(z, v), p, m, P[E5.key(z, p, m)]['eval'][i], 1001, E10.lut(z, v, p)))
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=7200)
    el = time.time() - t
    n = len(eval_jobs())
    est = el / len(js) * n / 3600
    L = ['# Run-time estimate v19 K5', '', f'Timing test: {len(js)} runs (seed 1001; every method x size x scenario at the 2nd, 4th and 7th load), {nproc} processes: {el:.0f} s wall; '
         f'{sum(1 for x in res.values() if x is None)} missing.', '', f'K5: {n} runs, estimated **{est:.1f} h**. The full design is run.']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('timing'))


def to_csv(stage, fn):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw(stage), '*.json'))):
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up = l['vl_down_packets'], l['vl_up_packets']
        has = any(down)
        rows.append(dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed,
                         accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']), latency=repr(s['global_average_delay_cycles']),
                         p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'], vl_imbalance=repr(MK.imbalance(m, down, up)) if has else '', vl_source='run' if has else 'none'))
    out = os.path.join(RES, fn)
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(f'{out}: {len(rows)} rows; dead ends {sum(int(r["dead_ends"]) for r in rows)}')
    return len(rows)


# ---- K6 faults ----
def fmasks():
    m = json.load(open(os.path.join(HERE, 'results_v11', 'masks.json')))
    return {k: v[:5] for k, v in m.items()}


def fladder(z, p):
    return lp()[f'{z}__{p}__{E5.FREE[z]}']['eval']


def fsweep_jobs():
    ms = fmasks()
    js = []
    for z in E11.SIZES:
        for k in E11.KS:
            for m in ms[f'{z}__k{k}']:
                for p in E11.PATTERNS:
                    for r in fladder(z, p):
                        js += [E5.job('fsweep', z, 'DeFT', args_of(z, 'DeFT'), p, m, r, s, E11.lut_path(z, m)) for s in FAULT_SEEDS]
    return js


def fchoose():
    ms = fmasks()
    R = {}
    for f in glob.glob(os.path.join(raw('fsweep'), '*.json')):
        (v, p, m, rate, seed), d = MK.parse(f)
        R[(p, m, rate, seed)] = d['summary']['global_average_delay_cycles']
    choice = {}
    L = ['# K6: test load per (size, k, pattern) (v14 rule, DeFT(rho*) with the round-robin)', '',
         'Mean latency pooled over the 5 v11 masks and seeds 51-52 per load point. Unsaturated: pooled latency <= 3 x the pooled latency at the lowest load point. Test load = the highest unsaturated load point.', '',
         '| size | k | pattern | zero-load latency | pooled latency per load point (cycles; * = unsaturated) | test load (rate, x fault-free Lsat) |', '|---|---|---|---|---|---|']
    for z in E11.SIZES:
        for k in E11.KS:
            for p in E11.PATTERNS:
                lad = fladder(z, p)
                pooled = []
                for r in lad:
                    xs = [R[(f'{z}-{p}', m, r, s)] for m in ms[f'{z}__k{k}'] for s in FAULT_SEEDS]
                    pooled.append(sum(xs) / len(xs))
                ok = [x <= 3 * pooled[0] for x in pooled]
                idx = max((i for i in range(len(lad)) if ok[i]), default=0)
                choice[f'{z}__k{k}__{p}'] = dict(rate=lad[idx], index=idx, mult=MULTS[idx], zero_load=pooled[0], pooled=pooled, all_lower_ok=all(ok[:idx + 1]))
                cells = ' / '.join(f'{x:.0f}{"*" if o else ""}' for x, o in zip(pooled, ok))
                L.append(f'| {z} | {k} | {p} | {pooled[0]:.1f} | {cells} | {lad[idx]} ({MULTS[idx]} x) |')
    json.dump(choice, open(os.path.join(RES, 'fault_load_choice.json'), 'w'), indent=1)
    open(os.path.join(RES, 'fault_load_choice.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


def feval_jobs():
    ms = fmasks()
    ch = json.load(open(os.path.join(RES, 'fault_load_choice.json')))
    js = []
    for z in E11.SIZES:
        for k in E11.KS:
            for m in ms[f'{z}__k{k}']:
                for p in E11.PATTERNS:
                    r = ch[f'{z}__k{k}__{p}']['rate']
                    for v in VN_METHODS:
                        js += [E5.job('feval', z, v, args_of(z, v), p, m, r, s, E11.lut_path(z, m)) for s in FAULT_CONF_SEEDS]
    return js


# ---- K7 PARSEC ----
def app_jobs():
    win = json.load(open(os.path.join(HERE, 'results_v13_apps', 'window.json')))
    js = []
    for b in E13.BENCH:
        for m in E13.MASKS:
            for v in APP_METHODS:
                for s in APP_SEEDS:
                    n, a = E13.job('app', b, v, m, s, win['window_cycles'][b])
                    js.append((n, a + RR))
    return js


def apps_csv():
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('app'), '*.json'))):
        _, v, b, m, s = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        rows.append(dict(benchmark=b, method=v, mask=m, seed=int(s[1:]), latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         completion_cycles=l['netrace_completion_cycle'], packets=l['netrace_packets'], injected=l['netrace_injected'],
                         delivered=l['netrace_delivered'], finished=l['netrace_finished'], dead_ends=l['dead_end_events']))
    with open(os.path.join(RES, 'app_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r['finished'] is not True or r['injected'] != r['delivered']]
    print(f'app_runs.csv: {len(rows)} rows; not finished or not drained: {len(bad)}')
    return len(rows), bad


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(sys.argv[3].split(','), nproc) else 1)
    elif stage == 'drain':
        res = run_jobs(drain_jobs(), raw('drain'), nproc=nproc, timeout=14400)
        fails = drain_report(res, os.path.join(RES, 'drain_summary.csv'))
        if not fails:
            shutil.rmtree(raw('drain'))
        sys.exit(1 if fails else 0)
    elif stage == 'vcbal':
        vcbal(nproc)
    elif stage == 'sat':
        sat(nproc)
    elif stage == 'points':
        points()
    elif stage == 'timing':
        timing(nproc)
    elif stage == 'eval':
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'csv':
        n = to_csv('eval', 'eval_runs.csv')
        if n == len(eval_jobs()):
            shutil.rmtree(raw('eval'))
    elif stage == 'fsweep':
        js = fsweep_jobs()
        print('fsweep jobs:', len(js), flush=True)
        res = run_jobs(js, raw('fsweep'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'fchoose':
        fchoose()
        to_csv('fsweep', 'fault_sweep_runs.csv')
        shutil.rmtree(raw('fsweep'))
    elif stage == 'feval':
        js = feval_jobs()
        print('feval jobs:', len(js), flush=True)
        res = run_jobs(js, raw('feval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'fcsv':
        n = to_csv('feval', 'fault_runs.csv')
        if n == len(feval_jobs()):
            shutil.rmtree(raw('feval'))
    elif stage == 'apps':
        js = app_jobs()
        print('app jobs:', len(js), flush=True)
        res = run_jobs(js, raw('app'), nproc=nproc, timeout=6 * 3600)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'appscsv':
        n, bad = apps_csv()
        if n == len(app_jobs()) and not bad:
            shutil.rmtree(raw('app'))
    else:
        raise SystemExit(__doc__)
