"""v16 (Part H): Q-table entry width (results_v16_qbits/).

Stages (python3 experiments_v16.py STAGE [nproc] [extra]; --shard i/n accepted):
  range    residual range: CI_qlLA_G, FULL_qlLA_G, every size, uniform and hotspot at 1.0 and 1.6 x Lsat, seed 1001,
           -deft_lb ql_range 1 (extra = binary; default bin/noxim) -> range.json, choice of I and F per size -> qformat.json
  reuse    ql_bits 0: 20 random v9 runs of CI_qlLA_G and FULL_qlLA_G re-run, compared with results_v9/eval_runs.csv
  eval     equivalence test: B in {16, 12, 8}, 5 scenarios, 7 v9 loads, seeds 41-45 (v9 float runs reused)
Design: PREREGISTRATION.md.
"""
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v16_qbits')
SIZES = ['2x2', '3x3', '4x4']
VARIANTS = ['CI_qlLA_G', 'FULL_qlLA_G']
BITS = [16, 12, 8]
SEEDS = range(41, 46)
NL = chr(10)


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def faulty(size):
    return '0x1111' if size == '2x2' else E5.NORTH[size]


def scenarios(size):
    f = E5.FREE[size]
    return [('uniform', f), ('hotspot', f), ('chipperm', f), ('movinghot', f), ('uniform', faulty(size))]


def _run(arg):
    binary, a, f = arg
    if not os.path.exists(f):
        subprocess.run([binary] + a + ['-stats_file', f], cwd=BIN, env=ENV, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=7200)
    try:
        return f, json.load(open(f))
    except Exception:
        return f, None


def rangejob(binary, nproc):
    out = raw('range')
    os.makedirs(out, exist_ok=True)
    jobs = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            for p in ('uniform', 'hotspot'):
                lad = E10.LP5[f'{z}__{p}__{E5.FREE[z]}']['eval']
                for i, ld in ((3, '1.0'), (6, '1.6')):
                    n, a = E5.job('range', z, v, mm[v] + ['-deft_lb', 'ql_range', '1'], p, E5.FREE[z], lad[i], 1001,
                                  E10.lut(z, v, p))
                    jobs.append((binary, a, os.path.join(out, n + '.json')))
    with Pool(nproc) as pool:
        res = dict(pool.map(_run, jobs))
    rows, per_size = [], {}
    for _, a, f in jobs:
        d = res[f]['deft_lb']
        n = os.path.basename(f)[:-5]
        rows.append(dict(run=n, r_min=d['ql_residual_min'], r_max=d['ql_residual_max'], updates=d['ql_updates']))
        z = n.split('__')[2].split('-')[0]
        per_size[z] = max(per_size.get(z, 0.0), abs(d['ql_residual_min']), abs(d['ql_residual_max']))
    fmt = {}
    for z, m in per_size.items():
        ib = max(0, math.ceil(math.log2(2 * m))) if m > 0 else 0       # factor-2 margin
        fmt[z] = {'max_abs_R': m, 'integer_bits': ib, 'frac_bits': {str(b): b - 1 - ib for b in BITS}}
    json.dump({'runs': rows, 'per_size': fmt}, open(os.path.join(RES, 'range.json'), 'w'), indent=1)
    json.dump(fmt, open(os.path.join(RES, 'qformat.json'), 'w'), indent=1)
    L = ['# Residual range and fixed-point format (v16 H1)', '',
         'CI_qlLA_G and FULL_qlLA_G (v10 parameters), every size, uniform and hotspot at 1.0 and 1.6 x Lsat, seed 1001, '
         '`-deft_lb ql_range 1` (float residuals; min / max of the stored residual R over all updates of the run).', '',
         '| run | R min | R max | updates |', '|---|---|---|---|']
    L += [f'| {r["run"]} | {r["r_min"]:.4g} | {r["r_max"]:.4g} | {r["updates"]} |' for r in rows]
    L += ['', 'Integer bits I = ceil(log2(2 x max |R|)) per size (factor-2 margin), sign bit separate; F = B - 1 - I.', '',
          '| size | max abs R | I | F for B = 16 / 12 / 8 |', '|---|---|---|---|']
    for z in SIZES:
        f = fmt[z]
        L.append(f'| {z} | {f["max_abs_R"]:.4g} | {f["integer_bits"]} | '
                 + ' / '.join(str(f['frac_bits'][str(b)]) for b in BITS) + ' |')
    open(os.path.join(RES, 'range.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


def qargs(size, b):
    f = json.load(open(os.path.join(RES, 'qformat.json')))[size]['frac_bits'][str(b)]
    return ['-deft_lb', 'ql_bits', str(b), '-deft_lb', 'ql_frac', str(f)]


def reuse(nproc):
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'results_v9', 'eval_runs.csv')))
            if r['variant'] in VARIANTS]
    pick = random.Random(1016).sample(rows, 20)
    js = []
    for r in pick:
        z, p = r['pattern'].split('-')
        js.append(E5.job('reuse', z, r['variant'], E10.methods(z)[r['variant']] + ['-deft_lb', 'ql_bits', '0'], p,
                         r['mask'], float(r['rate']), int(r['seed']), E10.lut(z, r['variant'], p)))
    res = run_jobs(js, raw('reuse'), nproc=nproc, timeout=7200)
    ok, lines = 0, []
    for r, (n, _) in zip(pick, js):
        d = res.get(n)
        same = d is not None and repr(d['summary']['global_average_delay_cycles']) == r['latency'] and \
            repr(d['summary']['average_ip_throughput_flits_per_cycle_per_ip']) == r['accepted'] and \
            repr(d['deft_lb']['delay_p99']) == r['p99']
        ok += same
        lines.append(f'| {r["variant"]} | {r["pattern"]} {r["mask"]} | {r["rate"]} | {r["seed"]} | '
                     f'{"identical" if same else "DIFFERENT"} |')
    L = ['# v16 reuse check: ql_bits 0 reproduces v9 (random.Random(1016), 20 runs of CI_qlLA_G / FULL_qlLA_G)', '',
         f'**{ok} / 20 identical** (latency, accepted, p99).', '', '| variant | scenario | rate | seed | result |',
         '|---|---|---|---|---|'] + lines
    open(os.path.join(RES, 'reuse_check.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('reuse'))
    return ok == 20


def eval_jobs():
    js = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            for b in BITS:
                for p, m in scenarios(z):
                    for r in E10.LP5[f'{z}__{p}__{m}']['eval']:
                        js += [E5.job('eval', z, f'{v}-b{b}', mm[v] + qargs(z, b), p, m, r, s, E10.lut(z, v, p))
                               for s in SEEDS]
    return js


def qlstats():
    """Per-run learning statistics of the evaluation (ql_stats.csv), before the raw outputs are deleted."""
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('eval'), '*.json'))):
        _, v, sp, m, rate, seed = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))['deft_lb']
        var, b = v.rsplit('-b', 1)
        rows.append(dict(size=sp.split('-')[0], pattern=sp.split('-')[1], mask=m, rate=rate, seed=seed[1:],
                         variant=var, bits=b, updates=d['ql_updates'], changed=d['ql_updates_changed'],
                         changed_share=repr(d['ql_updates_changed'] / max(1, d['ql_updates'])),
                         r_min=d['ql_residual_min'], r_max=d['ql_residual_max']))
    with open(os.path.join(RES, 'ql_stats.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('ql_stats.csv:', len(rows), 'rows')


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    if stage == 'range':
        rangejob(sys.argv[3] if len(sys.argv) > 3 else os.path.join(BIN, 'noxim'), nproc)
    elif stage == 'qlstats':
        qlstats()
    elif stage == 'reuse':
        sys.exit(0 if reuse(nproc) else 1)
    elif stage == 'eval':
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    else:
        raise SystemExit('unknown stage')
