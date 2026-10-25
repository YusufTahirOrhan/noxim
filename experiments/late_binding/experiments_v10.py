"""v10: baselines (MTR, RC, DeFT-Dis, DeFT-Ran, XY-SP, DeFT_OE_G) and their comparison (results_v10/).

Stages (python3 experiments_v10.py STAGE [nproc] [extra]; any stage accepts --shard i/n, see runner.py):
  regress   defaults byte-identical: the 66-configuration regression set, v9 binary (extra = BIN_OLD) vs new binary,
            option absent and with every new option at its default value
  drain     drain tests of the new methods (2x2: v2 protocol; 3x3/4x4: all-pairs burst + over-saturated tables)
  reuse     20 v9 evaluation runs drawn at random (draw seed 1010) re-run with the new binary, compared with
            results_v9/eval_runs.csv
  sanity    2x2 uniform, DeFT(rho*) vs MTR and RC at 0.8-1.6 x Lsat (seeds 1001-1003; not evaluation seeds)
  timing    Part B timing test and estimate
  eval      Part B evaluation (new methods only; v9 runs reused), seeds 41-50
Method definitions: methods(size). Design: results_v10/BASELINES_DESIGN.md.
"""
import csv
import itertools
import json
import os
import random
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args, run_jobs  # noqa: E402
import variants_v2 as V2  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v6 as E6  # noqa: E402
import experiments_v9 as E9  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v10')
SIZES = ['2x2', '3x3', '4x4']
LP5 = E6.LP5
CH5 = E6.CH5
MTR_TABLE = os.path.join(RES, 'mtr_config.json')
XY = ['-deft_lb', 'chip_tm', 'XY', '-deft_lb', 'ipos_tm', 'XY']
NEW = ['MTR', 'RC', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G']
FAULT_FREE_ONLY = ('MTR', 'RC')
REUSED = ['DeFT', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
SEEDS = range(41, 51)


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def lb(exit_p, entry_p):
    return ['-routing', 'DEFT_LB', '-deft_lb', 'exit', exit_p, '-deft_lb', 'entry', entry_p]


def methods(size):
    """Noxim arguments of every method of the comparison (new and reused)."""
    v9 = E9.variant_args(size)
    oe = list(v9['FULL_qlLA_G'])
    oe[oe.index('exit') + 1] = 'lut'
    oe[oe.index('entry') + 1] = 'lut'
    m = {
        'DeFT': V2.VARIANTS['DeFT'],
        'MTR': lb('mtr', 'mtr') + XY + ['-deft_lb', 'vn_rules', '0', '-deft_lb', 'mtr_table', MTR_TABLE],
        'RC': lb('near', 'near') + XY + ['-deft_lb', 'vn_rules', '0', '-deft_lb', 'rc', '1', '-deft_lb', 'rc_slots', '4'],
        'DeFT_Dis': lb('near', 'near') + XY,
        'DeFT_Ran': lb('ran', 'ran') + XY,
        'XY_SP': ['-routing', 'INTERPOSER_AWARE_XY'],
        'DeFT_OE_G': oe,
    }
    m.update({k: v9[k] for k in ('CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G')})
    return m


def lut(size, v, p):
    """DeFT's rho* uniform LUT for every method (CI exit, DeFT_OE_G pair); plain DEFT as in v9."""
    return E9.lut(size, v, p)


def scenarios(size, v):
    sc = E5.scenarios(size)
    if v in FAULT_FREE_ONLY:
        sc = [(p, m) for p, m in sc if int(m, 16) == 0]
    return sc


# ---- regression ----
DEFAULTS = ['-deft_lb', 'vn_rules', '1', '-deft_lb', 'rc', '0', '-deft_lb', 'count_vl', '0']


def regress(old_bin, nproc):
    import check_stats_regression as CSR
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = CSR.configs()
    new = os.path.join(BIN, 'noxim')
    tags = (('old', old_bin, []), ('default', new, []), ('explicit', new, DEFAULTS))
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
    L = ['# Regression of the v10 options with their defaults (experiments_v10.py regress)', '',
         'Old binary: build of 4953092 (v9). New binary: v10 baseline code (A1-A4). Same arguments.',
         f'Configurations: {len(cf)} (the 11 v2 variants x 2x2/3x3/4x4 x fault-free / one faulty VL per chiplet; uniform at '
         '1.0 x Lsat of v5; seed 7; v5 rho* LUTs), the regression set of v6-v8.', '',
         f'- new binary, options absent: {ok["default"]} / {len(cf)} runs with byte-identical summary and deft_lb blocks',
         f'- new binary, `-deft_lb vn_rules 1 rc 0 count_vl 0` explicit: {ok["explicit"]} / {len(cf)} identical', '']
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


# ---- drain ----
DRAIN_ALLPAIRS_2X2 = ['-drain_mode', '-drain_source_cutoff', '100', '-drain_timeout', '60000', '-warmup', '0',
                      '-sim', '80000']
DRAIN_OVERSAT_2X2 = ['-drain_mode', '-drain_source_cutoff', '3000', '-drain_timeout', '100000', '-warmup', '1000',
                     '-sim', '120000']
DRAIN_ALLPAIRS = ['-drain_mode', '-drain_source_cutoff', '1000', '-drain_timeout', '1000000', '-warmup', '0',
                  '-sim', '1200000']
DRAIN_OVERSAT = ['-drain_mode', '-drain_source_cutoff', '3000', '-drain_timeout', '1000000', '-warmup', '1000',
                 '-sim', '1200000']


def drain_jobs():
    js = []
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    for size in SIZES:
        mm = methods(size)
        for v in NEW:
            if size == '2x2':
                # v2 protocol; the v2 uniform LUT holds all 11 masks (identical to the v5 LUT on its 3 masks)
                ms = ['0x0000'] if v in FAULT_FREE_ONLY else masks2
                for m, seed in itertools.product(ms, (1, 2)):
                    a = common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=None) + mm[v] + \
                        DRAIN_ALLPAIRS_2X2
                    js.append((f'allpairs__{v}__2x2-{m}__s{seed}', a))
                ms = ['0x0000'] if v in FAULT_FREE_ONLY else ['0x0000', '0x1111', '0x9C63', '0x7BDE']
                for m, pat in itertools.product(ms, ('uniform', 'chipperm', 'hotspot')):
                    a = common_args(1, m, traffic=E5.REL + f'traffic/{pat}_0.0300.txt', lut=None) + mm[v] + \
                        DRAIN_OVERSAT_2X2
                    js.append((f'{pat}0.03__{v}__2x2-{m}__s1', a))
                continue
            ms = [E5.FREE[size]] if v in FAULT_FREE_ONLY else [E5.FREE[size], E5.NORTH[size]]
            for m, seed in itertools.product(ms, (1, 2)):
                a = common_args(seed, m, hardcoded=E5.REL + f'{E5.tdir(size)}/allpairs_burst.txt',
                                lut=lut(size, v, 'uniform')) + E5.size_args(size) + mm[v] + DRAIN_ALLPAIRS
                js.append((f'allpairs__{v}__{size}-{m}__s{seed}', a))
            # added in v10: over-saturated drain tests on 3x3/4x4 (top v5 load of the pattern)
            for m, pat in itertools.product(ms, ('uniform', 'chipperm', 'hotspot')):
                key = f'{size}__{pat}__{m}' if f'{size}__{pat}__{m}' in LP5 else f'{size}__{pat}__{E5.FREE[size]}'
                r = LP5[key]['eval'][6]
                a = common_args(1, m, traffic=E5.REL + f'{E5.tdir(size)}/{pat}_{r:.4f}.txt', lut=lut(size, v, pat)) + \
                    E5.size_args(size) + mm[v] + DRAIN_OVERSAT
                js.append((f'{pat}{r:.4f}__{v}__{size}-{m}__s1', a))
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
    by = {}
    for r in rows:
        by.setdefault(r[1], [0, 0])
        by[r[1]][0] += 1
        by[r[1]][1] += r[-1] == 'PASS'
    print(f'runs={len(rows)} failures={fails}', {k: f'{p}/{n}' for k, (n, p) in by.items()})
    return fails, by


# ---- v9 reuse check ----
REUSE_DRAW_SEED = 1010


def reuse(nproc):
    rows = list(csv.DictReader(open(os.path.join(HERE, 'results_v9', 'eval_runs.csv'))))
    rows = [r for r in rows if r['variant'] in REUSED]
    pick = random.Random(REUSE_DRAW_SEED).sample(rows, 20)
    js = []
    for r in pick:
        size, p = r['pattern'].split('-')
        rate = float(r['rate'])
        mm = methods(size)
        js.append(E5.job('reuse', size, r['variant'], mm[r['variant']], p, r['mask'], rate, int(r['seed']),
                         lut(size, r['variant'], p)))
    res = run_jobs(js, raw('reuse'), nproc=nproc, timeout=7200)
    ok, lines = 0, []
    for r, (n, _) in zip(pick, js):
        d = res.get(n)
        su, l = (d['summary'], d['deft_lb']) if d else ({}, {})
        new = dict(accepted=repr(su.get('average_ip_throughput_flits_per_cycle_per_ip')),
                   latency=repr(su.get('global_average_delay_cycles')), p99=repr(l.get('delay_p99')),
                   injected=str(su.get('total_injected_packets')), received=str(su.get('total_received_packets')),
                   dead_ends=str(l.get('dead_end_events')))
        same = d is not None and all(new[k] == r[k] for k in new)
        ok += same
        lines.append(f'| {r["variant"]} | {r["pattern"]} {r["mask"]} | {r["rate"]} | {r["seed"]} | '
                     f'{r["latency"][:9]} / {new["latency"][:9]} | {r["accepted"][:9]} / {new["accepted"][:9]} | '
                     f'{"identical" if same else "DIFFERENT"} |')
    L = ['# v9 reuse check (v10 A5)', '',
         f'20 runs drawn at random (Python random.Random({REUSE_DRAW_SEED}).sample) from the v9 evaluation runs of '
         'DeFT(rho*), CI_heurLA_G, CI_qlLA_G and FULL_qlLA_G, re-run with the v10 binary and compared field by field '
         '(repr of the JSON values) with results_v9/eval_runs.csv: accepted, latency, p99, injected, received, dead ends.',
         '', f'**{ok} / 20 identical.**', '',
         '| variant | scenario | rate | seed | latency v9 / v10 | accepted v9 / v10 | result |',
         '|---|---|---|---|---|---|---|'] + lines
    open(os.path.join(RES, 'reuse_check.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    shutil.rmtree(raw('reuse'))
    return ok == 20


# ---- sanity check against the DeFT paper ----
def sanity(nproc):
    js = []
    mm = methods('2x2')
    for v in ('DeFT', 'MTR', 'RC'):
        for i in (2, 3, 4, 5, 6):
            r = LP5['2x2__uniform__0x0000']['eval'][i]
            js += [E5.job('san', '2x2', v, mm[v], 'uniform', '0x0000', r, s, lut('2x2', v, 'uniform'))
                   for s in (1001, 1002, 1003)]
    res = run_jobs(js, raw('sanity'), nproc=nproc, timeout=7200)
    L = ['# Sanity check against the DeFT paper (v10 A5): 2x2 uniform, fault-free', '',
         'Mean over seeds 1001-1003 (not evaluation seeds). Load = multiple of DeFT(rho*)\'s Lsat (v5 load points).', '',
         '| load | rate | DeFT(rho*) latency | MTR latency | RC latency | DeFT accepted | MTR accepted | RC accepted |',
         '|---|---|---|---|---|---|---|---|']
    out = {}
    for i, mult in zip((2, 3, 4, 5, 6), (0.8, 1.0, 1.2, 1.4, 1.6)):
        r = LP5['2x2__uniform__0x0000']['eval'][i]
        row = {}
        for v in ('DeFT', 'MTR', 'RC'):
            ds = [res[f'san__{v}__2x2-uniform__0x0000__{r:.4f}__s{s}'] for s in (1001, 1002, 1003)]
            row[v] = (sum(d['summary']['global_average_delay_cycles'] for d in ds) / 3,
                      sum(d['summary']['average_ip_throughput_flits_per_cycle_per_ip'] for d in ds) / 3)
        out[mult] = row
        L.append(f'| {mult} | {r} | {row["DeFT"][0]:.1f} | {row["MTR"][0]:.1f} | {row["RC"][0]:.1f} | '
                 f'{row["DeFT"][1]:.4f} | {row["MTR"][1]:.4f} | {row["RC"][1]:.4f} |')
    open(os.path.join(RES, 'sanity_check.md'), 'w', newline='\n').write('\n'.join(L) + '\n')
    json.dump({str(k): v for k, v in out.items()}, open(os.path.join(RES, 'sanity_check.json'), 'w'), indent=1)
    print('\n'.join(L))
    shutil.rmtree(raw('sanity'))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(extra, nproc) else 1)
    if stage == 'reuse':
        sys.exit(0 if reuse(nproc) else 1)
    if stage == 'sanity':
        sanity(nproc)
        sys.exit(0)
    if stage == 'drain':
        res = run_jobs(drain_jobs(), raw('drain'), nproc=nproc, timeout=14400)
        fails, _ = drain_report(res)
        sys.exit(1 if fails else 0)
    raise SystemExit('unknown stage')
