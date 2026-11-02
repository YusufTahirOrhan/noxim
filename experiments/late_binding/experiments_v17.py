"""v17 (Part I): VC usage per link direction, descriptive (results_v17_vcdiag/).

Stages (python3 experiments_v17.py STAGE [nproc] [extra]; --shard i/n accepted):
  regress   option off: old binary (extra = 3ac1bae build) vs bin/noxim on the 84-configuration set of v14-v16; whole
            stats files compared byte by byte -> regression.md
  oncheck   option on vs off with the new binary on 5 runs: the stats file (latency statistics included) must not change
            -> oncheck.md
  run       the I2 runs: 6 methods + MTR_VN x 2x2/3x3/4x4 x uniform/hotspot x 0.8/1.0 x Lsat x seeds 41-43, plus
            DeFT_LUT_noVN at 0.8 x Lsat only
  csv       per-run CSVs (vc_runs.csv, run_summary.csv); raw outputs deleted
Definitions of the link classes and counters: results_v17_vcdiag/DECISIONS.md. Method parameters: experiments_v10.methods.
"""
import csv
import glob
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v17_vcdiag')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v17')     # Linux file system: faster, not in the repository
SIZES = ['2x2', '3x3', '4x4']
PATTERNS = ['uniform', 'hotspot']
LOAD_INDEX = {0.8: 2, 1.0: 3}          # positions in the v5 evaluation load list
SEEDS = (41, 42, 43)
METHODS = ['DeFT', 'MTR', 'RC', 'DeFT_Dis', 'CI_qlLA_G', 'FULL_qlLA_G']
DEADLOCK_FRACTION = 0.5                # diagnostic flag: accepted flits below this fraction of DeFT(rho*) in the same cell
NL = chr(10)


def raw(stage):
    return os.path.join(RAW, stage)


def configs(size):
    """Noxim arguments of the evaluated methods and the two diagnostic configurations (as in sanity_diag_v10.py)."""
    m = E10.methods(size)
    out = {v: m[v] for v in METHODS}
    mtr_vn = list(m['MTR'])
    mtr_vn[mtr_vn.index('vn_rules') + 1] = '1'
    out['MTR_VN'] = mtr_vn
    out['DeFT_LUT_noVN'] = E10.lb('lut', 'lut') + E10.XY + ['-deft_lb', 'vn_rules', '0']
    return out


def rate(size, p, mult):
    return E10.LP5[f'{size}__{p}__{E5.FREE[size]}']['eval'][LOAD_INDEX[mult]]


def name_of(v, size, p, mult, seed):
    return f'vc__{v}__{size}__{p}__{mult}__s{seed}'


def job(v, size, p, mult, seed, out_dir):
    va = configs(size)[v]
    lut = E10.lut(size, 'DeFT', p)     # DeFT's rho* uniform LUT (CI exit, DeFT, DeFT_LUT_noVN); ignored by the others
    _, args = E5.job('vc', size, v, va, p, E5.FREE[size], rate(size, p, mult), seed, lut)
    n = name_of(v, size, p, mult, seed)
    return n, args + ['-deft_lb', 'vc_stats', os.path.join(out_dir, n + '.vc.json')]


def cells():
    out = []
    for size in SIZES:
        for p in PATTERNS:
            for mult in LOAD_INDEX:
                for v in METHODS + ['MTR_VN']:
                    out += [(v, size, p, mult, s) for s in SEEDS]
            out += [('DeFT_LUT_noVN', size, p, 0.8, s) for s in SEEDS]
    return out


def ensure_tables():
    for size in SIZES:
        for p in PATTERNS:
            E5.gen_tables(size, p, [rate(size, p, m) for m in LOAD_INDEX])


# ---- checks ----
def md5(f):
    return subprocess.run(['md5sum', f], capture_output=True, text=True).stdout.split()[0]


def regress(old_bin, nproc):
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
    L = ['# Regression with the v17 option off (experiments_v17.py regress)', '',
         f'Old binary: md5 {md5(old_bin)} (commit 3ac1bae, built in a separate worktree). New binary: md5 {md5(new_bin)} '
         '(code with -deft_lb vc_stats; option off).',
         f'Configurations: {len(cf)} = the 84-configuration set of v14-v16 (experiments_v15.py regress). Comparison: the '
         'whole stats JSON file, byte by byte.', '',
         f'**{ok} / {len(cf)} byte-identical.**', ''] + (diffs or ['No differences.'])
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return not diffs


def oncheck(nproc):
    out = raw('oncheck')
    os.makedirs(out, exist_ok=True)
    five = [('DeFT', '2x2', 'uniform'), ('MTR', '3x3', 'uniform'), ('RC', '4x4', 'hotspot'),
            ('CI_qlLA_G', '2x2', 'hotspot'), ('FULL_qlLA_G', '3x3', 'uniform')]
    from multiprocessing import Pool
    jobs = []
    for v, size, p in five:
        n, a = job(v, size, p, 1.0, 41, out)
        off = a[:a.index('vc_stats') - 1] + a[a.index('vc_stats') + 2:]
        jobs.append((a, os.path.join(out, n + '.on.json')))
        jobs.append((off, os.path.join(out, n + '.off.json')))
    with Pool(nproc) as pool:
        pool.map(_run_one, jobs)
    rows, ok = [], 0
    for v, size, p in five:
        n = name_of(v, size, p, 1.0, 41)
        fon, foff = (os.path.join(out, f'{n}.{t}.json') for t in ('on', 'off'))
        same = open(fon, 'rb').read() == open(foff, 'rb').read()
        ok += same
        d = json.load(open(fon))
        vc = json.load(open(os.path.join(out, n + '.vc.json')))
        rows.append(f"| {v} | {size} | {p} | {d['summary']['global_average_delay_cycles']:.3f} | {d['deft_lb']['delay_p99']:.1f} | "
                    f"{sum(sum(l['f']) for l in vc['links'])} | {'identical' if same else 'DIFFERENT'} |")
    L = ['# v17: statistics option on vs off (experiments_v17.py oncheck)', '',
         f'**{ok} / {len(five)} stats files byte-identical** (latency statistics included; the VC counters go to their own '
         'file). Load 1.0 x Lsat, seed 41.', '',
         '| method | size | pattern | mean latency | p99 | flits counted on links | stats file on vs off |',
         '|---|---|---|---|---|---|---|'] + rows
    open(os.path.join(RES, 'oncheck.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return ok == len(five)


def _run_one(arg):
    a, f = arg
    subprocess.run([os.path.join(BIN, 'noxim')] + a + ['-stats_file', f], cwd=BIN, env=ENV, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=7200)


# ---- aggregation ----
CLASSES = ['chip_towards', 'chip_away', 'ipos', 'vl_down', 'vl_up']


def aggregate(links):
    """Per class: VC totals, traffic-weighted link imbalance, waits, mean occupancy per link."""
    out = {}
    for c in CLASSES:
        ls = [l for l in links if l['cls'] == c]
        f0 = sum(l['f'][0] for l in ls)
        f1 = sum(l['f'][1] for l in ls)
        out[c] = dict(links=len(ls), f0=f0, f1=f1, abs_diff=sum(abs(l['f'][0] - l['f'][1]) for l in ls),
                      held0=sum(l['held'][0] for l in ls), held1=sum(l['held'][1] for l in ls),
                      nocredit0=sum(l['nocredit'][0] for l in ls), nocredit1=sum(l['nocredit'][1] for l in ls),
                      occ0=sum(l['occ'][0] for l in ls) / max(len(ls), 1), occ1=sum(l['occ'][1] for l in ls) / max(len(ls), 1),
                      **{f'ph{v}_{ph}': sum(l['phase'][v][k] for l in ls) for v in (0, 1)
                         for k, ph in enumerate(('src', 'ipos', 'dst', 'intra'))})
    return out


def make_csv():
    out = raw('run')
    rows, summ = [], []
    missing = 0
    for v, size, p, mult, s in cells():
        n = name_of(v, size, p, mult, s)
        try:
            d = json.load(open(os.path.join(out, n + '.json')))
            vc = json.load(open(os.path.join(out, n + '.vc.json')))
        except Exception:
            missing += 1
            print('missing', n)
            continue
        su, l = d['summary'], d['deft_lb']
        base = dict(method=v, size=size, pattern=p, load=mult, seed=s)
        ag = aggregate(vc['links'])
        for c in CLASSES:
            rows.append(dict(base, cls=c, **ag[c]))
        rc = vc.get('rc_buffer', {})
        summ.append(dict(base, rate=rate(size, p, mult), latency=repr(su['global_average_delay_cycles']),
                         p99=repr(l['delay_p99']), accepted=repr(su['average_ip_throughput_flits_per_cycle_per_ip']),
                         received_flits=su['total_received_flits'], dead_ends=l['dead_end_events'],
                         packets_inter=l['packets_inter'], packets_intra=l['packets_intra'],
                         rc_mean_flits=rc.get('mean_flits', ''), rc_mean_slots=rc.get('mean_slots', ''),
                         rc_peak_flits=rc.get('peak_flits', ''), rc_peak_slots=rc.get('peak_slots', ''),
                         rc_permission_wait=rc.get('permission_wait_mean', ''), rc_grants=rc.get('permission_grants', '')))
    # deadlock flag: accepted flits far below DeFT(rho*) in the same cell (same size, pattern, load, seed)
    ref = {(r['size'], r['pattern'], r['load'], r['seed']): r['received_flits'] for r in summ if r['method'] == 'DeFT'}
    for r in summ:
        k = (r['size'], r['pattern'], r['load'], r['seed'])
        r['deadlock_flag'] = int(k in ref and r['received_flits'] < DEADLOCK_FRACTION * ref[k])
    for fn, rr in (('vc_runs.csv', rows), ('run_summary.csv', summ)):
        with open(os.path.join(RES, fn), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rr[0]), lineterminator=NL)
            w.writeheader()
            w.writerows(rr)
    print(f'vc_runs.csv: {len(rows)} rows; run_summary.csv: {len(summ)} runs; missing {missing}; '
          f'deadlock flags: {[(r["method"], r["size"], r["pattern"], r["load"], r["seed"]) for r in summ if r["deadlock_flag"]]}')
    return missing == 0


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    if stage == 'regress':
        ensure_tables()
        sys.exit(0 if regress(sys.argv[3], nproc) else 1)
    elif stage == 'oncheck':
        ensure_tables()
        sys.exit(0 if oncheck(nproc) else 1)
    elif stage == 'run':
        ensure_tables()
        d = raw('run')
        os.makedirs(d, exist_ok=True)
        js = [job(v, size, p, mult, s, d) for v, size, p, mult, s in cells()]
        res = run_jobs(js, d, nproc=nproc, timeout=7200)
        print(f'{sum(1 for x in res.values() if x)} / {len(js)} runs done')
    elif stage == 'csv':
        ok = make_csv()
        if ok:
            shutil.rmtree(raw('run'))
        sys.exit(0 if ok else 1)
    else:
        raise SystemExit(__doc__)
