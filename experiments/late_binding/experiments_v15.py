"""v15 (Part G): two PARSEC applications at once (Netrace overlay), compression s = 1 and 2 (results_v15_apps2/).

Stages (python3 experiments_v15.py STAGE [nproc] [extra]; --shard i/n accepted):
  regress   new options off: old binary (extra) vs bin/noxim on the 84-configuration set (66 regression configurations
            + six v10 baselines x 3 sizes); whole stats files compared byte by byte -> regression.md (also copied to
            results_v16_qbits, since the v15 and v16 code is one build)
  v13check  single-trace runs with s = 1 (DeFT(rho*), seed 41, one per benchmark) reproduce results_v13_apps exactly
            (extra = binary to test; default bin/noxim)
  timing    timing test (seed 1001, DeFT and FULL_qlLA_G, every pair, s = 1 and 2) and the s rule (8 h)
  eval      all pairs x methods x masks x seeds 41-43 for the chosen s
  csv       per-run CSV (pair_runs.csv); raw outputs deleted
Design: APPS2_DESIGN.md, PREREGISTRATION.md.
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
from runner import BIN, ENV, run_jobs  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v13 as E13  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v15_apps2')
TOP4 = ['blackscholes_64c_simsmall', 'vips_64c_simmedium', 'x264_64c_simsmall', 'swaptions_64c_simlarge']
PAIRS = [(TOP4[i], TOP4[j]) for i in range(4) for j in range(i + 1, 4)]
WINDOW = 700000
SEEDS = (41, 42, 43)
BUDGET_H = 8.0
NL = chr(10)


def raw(stage):
    return os.path.join(RES, stage + '_raw')


def short(b):
    return b.split('_')[0]


def job(stage, pair, v, m, seed, s):
    a, b = pair
    args = E13.common_args(seed, m, lut=E10.lut('2x2', v, 'uniform')) + E10.methods('2x2')[v] + \
        ['-netrace', os.path.join(E13.WIN_DIR, f'{a}_r2.txt'), '-netrace2', os.path.join(E13.WIN_DIR, f'{b}_r2.txt'),
         '-netrace_window', str(WINDOW), '-netrace_deps', '1', '-netrace_compress', str(s),
         '-warmup', '0', '-sim', str(E13.SIM_LIMIT), '-size', '2', '18']
    return f'{stage}__{v}__{short(a)}+{short(b)}__{m}__s{s}__seed{seed}', args


def cells():
    return [(p, v, m) for p in PAIRS for m in E13.MASKS for v in (E13.METHODS if m == '0x0000' else E13.FAULTY_OK)]


def _run_one(arg):
    binary, a, f = arg
    subprocess.run([binary] + a + ['-stats_file', f], cwd=BIN, env=ENV, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=4 * 3600)


def v13check(binary):
    rows = {(r['benchmark'], r['method'], r['mask'], r['seed']): r
            for r in csv.DictReader(open(os.path.join(HERE, 'results_v13_apps', 'app_runs.csv')))}
    out = raw('v13check')
    os.makedirs(out, exist_ok=True)
    ok, lines = 0, []
    from multiprocessing import Pool
    jobs = []
    for b in E13.BENCH:
        n, a = E13.job('chk', b, 'DeFT', '0x0000', 41, WINDOW)
        jobs.append((binary, a, os.path.join(out, n + '.json')))
    with Pool(len(jobs)) as pool:
        pool.map(_run_one, jobs)
    for b in E13.BENCH:
        n, a = E13.job('chk', b, 'DeFT', '0x0000', 41, WINDOW)
        d = json.load(open(os.path.join(out, n + '.json')))
        su, l = d['summary'], d['deft_lb']
        ref = rows[(b, 'DeFT', '0x0000', '41')]
        same = (repr(su['global_average_delay_cycles']) == ref['latency'] and repr(l['delay_p99']) == ref['p99'] and
                str(l['netrace_completion_cycle']) == ref['completion_cycles'] and
                str(l['netrace_delivered']) == ref['delivered'])
        ok += same
        lines.append(f'| {short(b)} | {ref["latency"][:9]} / {repr(su["global_average_delay_cycles"])[:9]} | '
                     f'{ref["completion_cycles"]} / {l["netrace_completion_cycle"]} | {"identical" if same else "DIFFERENT"} |')
    L = ['# v15 check: single trace, s = 1, reproduces v13 (DeFT(rho*), seed 41, fault-free)', '',
         f'**{ok} / {len(E13.BENCH)} identical** (mean latency, p99, completion cycle, delivered packets).', '',
         '| benchmark | latency v13 / v15 | completion v13 / v15 | result |', '|---|---|---|---|'] + lines
    open(os.path.join(RES, 'v13_check.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return ok == len(E13.BENCH)


def timing(nproc):
    js = [job('timing', p, v, '0x0000', 1001, s) for p in PAIRS for v in ('DeFT', 'FULL_qlLA_G') for s in (1, 2)]
    t = time.time()
    res = run_jobs(js, raw('timing'), nproc=nproc, timeout=6 * 3600)
    el = time.time() - t
    cyc = {s: sum(res[n]['deft_lb']['netrace_completion_cycle'] for n, _ in js if f'__s{s}__' in n and res.get(n))
           for s in (1, 2)}
    spc = el * nproc / (cyc[1] + cyc[2])            # cpu-seconds per simulated cycle
    n_per_s = len(cells()) * len(SEEDS)
    est = {s: cyc[s] / (2 * len(PAIRS)) * n_per_s * spc / nproc / 3600 for s in (1, 2)}
    both = est[1] + est[2]
    choice = [1, 2] if both <= BUDGET_H else [1]
    json.dump({'s_values': choice, 'estimate_h': {str(k): round(v, 2) for k, v in est.items()}},
              open(os.path.join(RES, 'compress_choice.json'), 'w'), indent=1)
    L = ['# Run-time estimate v15 and choice of s', '', f'Timing test: {len(js)} runs (seed 1001, DeFT(rho*) and '
         f'FULL_qlLA_G, every pair, s = 1 and 2, fault-free), {nproc} processes: {el:.0f} s wall; '
         f'{spc * 1e6:.0f} cpu-us per simulated cycle.', '',
         f'Estimate for the {n_per_s} runs per s: s = 1 {est[1]:.1f} h, s = 2 {est[2]:.1f} h, both {both:.1f} h. Rule: '
         f'both if <= {BUDGET_H:.0f} h, else s = 1 only. **s: {", ".join(map(str, choice))}.**']
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline='\n').write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('timing'))


def eval_jobs():
    ss = json.load(open(os.path.join(RES, 'compress_choice.json')))['s_values']
    return [job('pair', p, v, m, seed, s) for s in ss for p, v, m in cells() for seed in SEEDS]


def make_csv():
    rows = []
    for f in sorted(glob.glob(os.path.join(raw('pair'), '*.json'))):
        _, v, pair, m, s, seed = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        su, l = d['summary'], d['deft_lb']
        cyc = l['netrace_completion_cycle']
        rows.append(dict(pair=pair, method=v, mask=m, s=int(s[1:]), seed=int(seed[4:]),
                         latency=repr(su['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                         completion_cycles=cyc, app1_completion=l['netrace1_completion_cycle'],
                         app2_completion=l['netrace2_completion_cycle'], app1_latency=repr(l['netrace1_latency_mean']),
                         app2_latency=repr(l['netrace2_latency_mean']),
                         packets=l['netrace_packets'] + l['netrace2_packets'],
                         injected=l['netrace_injected'] + l['netrace2_injected'],
                         delivered=l['netrace_delivered'] + l['netrace2_delivered'], finished=l['netrace_finished'],
                         received_flits=su['total_received_flits'],
                         offered_flits_per_node_cycle=repr(su['total_received_flits'] / 64.0 / max(cyc, 1)),
                         dead_ends=l['dead_end_events']))
    with open(os.path.join(RES, 'pair_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r['finished'] is not True or r['injected'] != r['delivered']]
    print(f'pair_runs.csv: {len(rows)} rows; not finished or not drained: {len(bad)}')
    return bad


def regress(old_bin, nproc):
    import check_stats_regression as CSR
    import experiments_v5 as E5
    from multiprocessing import Pool
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in ('2x2', '3x3', '4x4'):
        mm = E10.methods(size)
        r = E10.LP5[f'{size}__uniform__{E5.FREE[size]}']['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append((f'{v}__{size}', a))
    new_bin = os.path.join(BIN, 'noxim')
    jobs = [((t, b, [], n, a), out) for t, b in (('old', old_bin), ('new', new_bin)) for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = 0, []
    for n, _ in cf:
        fo, fn = (os.path.join(out, f'{t}__{n}.json') for t in ('old', 'new'))
        if os.path.exists(fo) and os.path.exists(fn) and open(fo, 'rb').read() == open(fn, 'rb').read():
            ok += 1
        else:
            diffs.append(f'- differs: {n}')
    md5 = lambda f: subprocess.run(['md5sum', f], capture_output=True, text=True).stdout.split()[0]
    L = ['# Regression with the v15/v16 options off (experiments_v15.py regress)', '',
         f'Old binary: md5 {md5(old_bin)} (the v11-v14 binary). New binary: md5 {md5(new_bin)} (code with -netrace2, '
         '-netrace_compress, -deft_lb ql_bits / ql_frac / ql_range; all off).',
         f'Configurations: {len(cf)} = the 66-configuration regression set + the six v10 baselines x 2x2/3x3/4x4 '
         '(uniform, fault-free, 1.0 x Lsat, seed 7). Comparison: the whole stats JSON file, byte by byte.', '',
         f'**{ok} / {len(cf)} byte-identical.**', ''] + (diffs or ['No differences.'])
    for d in (RES, os.path.join(HERE, 'results_v16_qbits')):
        open(os.path.join(d, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return not diffs


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(sys.argv[3], nproc) else 1)
    if stage == 'v13check':
        sys.exit(0 if v13check(sys.argv[3] if len(sys.argv) > 3 else os.path.join(BIN, 'noxim')) else 1)
    if stage == 'timing':
        timing(nproc)
        sys.exit(0)
    if stage == 'eval':
        js = eval_jobs()
        print('pair jobs:', len(js), flush=True)
        res = run_jobs(js, raw('pair'), nproc=nproc, timeout=12 * 3600)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
        sys.exit(0)
    if stage == 'csv':
        bad = make_csv()
        if not bad:
            shutil.rmtree(raw('pair'))
        sys.exit(1 if bad else 0)
    raise SystemExit('unknown stage')
