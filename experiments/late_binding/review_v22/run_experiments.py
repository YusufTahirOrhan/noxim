"""Confirming experiments of the review (v22). Runs a PATCHED COPY of the simulator (~/lbrev/noxim/bin/noxim_review, built
from a copy of src/ with scratchpad/patch_review.py; the repository's bin/noxim is never replaced) with cwd = the
repository's bin/ so that the relative config and traffic paths of the other experiments apply unchanged.

Stages (python3 run_experiments.py STAGE [nproc]):
  prep      the balanced-nearest entry table (paper-style second selection, fault-free) -> nearbal_table.json
  regress   options off: noxim_review against bin/noxim on 3 configurations, whole stats JSON byte by byte
  gap       DeFT variants (round-robin as v19; + Up link keeps its VN; + round-robin fallback; + paper-style entry) against
            MTR and RC; uniform, fault-free, 2x2 / 3x3 / 4x4; the K4 load ladders (+ 2.0 x Lsat on 2x2); seeds 1001-1003 (4x4: 1001-1002)
  vcsplit   VC usage per link class (-deft_lb vc_stats) at 1.0 x Lsat, 2x2 uniform, DeFT with and without up_keep
  pipe      uniform per-hop head delay for every method (-deft_lb pipe_all N): DeFT, MTR, CI_fastQL (N_fast = 3) on 2x2 uniform;
            a multi-output hop of CI_fastQL costs pipe_all + N_fast cycles, every other hop pipe_all (binary noxim_review2, which
            adds this to the first build; REVIEW_BIN selects the binary)
  summarize tables of every stage that has raw outputs -> *_runs.csv, SUMMARY.md
Raw outputs stay under ~/lbrev/raw (not in the repository).
"""
import csv
import glob
import itertools
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
LB = os.path.dirname(HERE)
NOXIM_ROOT = os.path.dirname(os.path.dirname(LB))
BIN = os.path.join(NOXIM_ROOT, 'bin')
REVIEW_BIN = os.environ.get('REVIEW_BIN', os.path.expanduser('~/lbrev/noxim/bin/noxim_review'))
RAW = os.path.expanduser('~/lbrev/raw')
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.join(BIN, 'libs', 'systemc-2.3.1', 'lib-linux64'))
CONFIG = '../config_examples/deft_2_5d_traffic_uniform.yaml'
REL = '../experiments/late_binding/'
LUT = {'2x2': os.path.join(LB, 'luts', 'v5', 'lut_2x2_rho0.01.yaml'), '3x3': os.path.join(LB, 'luts', 'v5', 'lut_3x3_rho0.01.yaml'),
       '4x4': os.path.join(LB, 'luts', 'v5', 'lut_4x4_rho0.001.yaml')}
MTR_TABLE = os.path.join(LB, 'results_v10', 'mtr_config.json')
NEARBAL = os.path.join(HERE, 'nearbal_table.json')
TDIR = {'2x2': 'traffic', '3x3': 'traffic_3x3', '4x4': 'traffic_4x4'}
SIZE_ARGS = {'2x2': [], '3x3': ['-deft_chiplets_x', '3', '-deft_chiplets_y', '3'], '4x4': ['-deft_chiplets_x', '4', '-deft_chiplets_y', '4']}
FREE = {'2x2': '0x0000', '3x3': '0x0', '4x4': '0x0'}
MULTS = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6]
XY = ['-deft_lb', 'chip_tm', 'XY', '-deft_lb', 'ipos_tm', 'XY']
RR = ['-deft_vn_rr', '1']
SIM = ['-sim', '10000', '-warmup', '2000']
NL = chr(10)


def ladder(size):
    P = json.load(open(os.path.join(LB, 'results_v19_vnrr', 'load_points_rr.json')))
    return P['%s__uniform__%s' % (size, FREE[size])]['eval']


def variants(size):
    deft = ['-routing', 'DEFT'] + RR
    up = ['-deft_lb', 'up_keep', '1']
    fb = ['-deft_lb', 'rr_fallback', '1']
    pe = ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'lut', '-deft_lb', 'entry', 'mtr', '-deft_lb', 'mtr_table', NEARBAL] + XY + RR
    return {
        'DeFT': deft,
        'DeFT_up': deft + up,
        'DeFT_fb': deft + fb,
        'DeFT_up_fb': deft + up + fb,
        'DeFT_pe': pe,
        'DeFT_pe_up_fb': pe + up + fb,
        'MTR': ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'mtr', '-deft_lb', 'entry', 'mtr'] + XY +
               ['-deft_lb', 'vn_rules', '0', '-deft_lb', 'mtr_table', MTR_TABLE],
        'RC': ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'near', '-deft_lb', 'entry', 'near'] + XY +
              ['-deft_lb', 'vn_rules', '0', '-deft_lb', 'rc', '1', '-deft_lb', 'rc_slots', '4'],
    }


def ci_fastql_2x2(pipe=0):
    """CI_fastQL of v21 on 2x2 (tuning_choice.json: w 2, beta 4, alpha 0.1; n_fast.json: N 3, age 2)."""
    a = ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'lut', '-deft_lb', 'entry', 'late', '-deft_lb', 'chip_tm', 'XY', '-deft_lb', 'ipos_tm', 'OE',
         '-sel', 'DEFT_FAST', '-deft_lb', 'hop_weight_ipos', '2.0', '-deft_lb', 'heur_w', '2.0', '-deft_lb', 'heur_busy', '4.0',
         '-deft_lb', 'fast_ql', '1', '-deft_lb', 'ql_alpha', '0.1', '-deft_lb', 'ql_key', '1', '-deft_lb', 'ql_eps', '0.0',
         '-deft_lb', 'ql_bits', '16', '-deft_lb', 'ql_frac', '10'] + RR + ['-deft_lb', 'decision_delay', '3', '-deft_lb', 'fast_stale', '2']
    return a + (['-deft_lb', 'pipe_all', str(pipe)] if pipe else [])


def common(size, rate, seed):
    t = REL + '%s/uniform_%.4f.txt' % (TDIR[size], rate)
    assert os.path.exists(os.path.join(BIN, t)), t
    return ['-config', CONFIG, '-seed', str(seed), '-deft_vl_lut', LUT[size], '-stats_format', 'json', '-traffic', 'table', t] + SIZE_ARGS[size]


def job(stage, name, size, vargs, rate, seed, extra=()):
    n = '%s__%s__%s__%.4f__s%d' % (stage, name, size, rate, seed)
    return n, common(size, rate, seed) + list(vargs) + SIM + list(extra)


def _run(a):
    name, args, out_dir, binary = a
    out = os.path.join(out_dir, name + '.json')
    if not os.path.exists(out):
        log = os.path.join(out_dir, name + '.log')
        with open(log, 'w') as lf:
            subprocess.run([binary] + args + ['-stats_file', out], cwd=BIN, env=ENV, stdout=lf, stderr=subprocess.STDOUT, timeout=7200)
        if os.path.exists(out):
            os.remove(log)
    try:
        return name, json.load(open(out))
    except Exception:
        return name, None


def run_jobs(jobs, stage, nproc, binary=REVIEW_BIN):
    out = os.path.join(RAW, stage)
    os.makedirs(out, exist_ok=True)
    with Pool(nproc) as pool:
        return dict(pool.imap_unordered(_run, [(n, a, out, binary) for n, a in jobs], chunksize=1))


# ---- prep: balanced-nearest entry table (paper-style second selection, uniform demand, fault-free) ----
SLOTS = [(1, 0), (3, 1), (2, 3), (0, 2)]


def prep():
    nodes = [(x, y) for y in range(4) for x in range(4)]
    dist = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])  # noqa: E731
    # exact DP over per-VL counts: 16 points, 4 VLs, minimise total distance subject to the balance 4/4/4/4
    states = {(0, 0, 0, 0): (0, ())}
    for r in nodes:
        nxt = {}
        for counts, (d, asg) in states.items():
            for v in range(4):
                c = list(counts)
                c[v] += 1
                if c[v] > 4:
                    continue
                key = (d + dist(r, SLOTS[v]), asg + (v,))
                if tuple(c) not in nxt or key < nxt[tuple(c)]:
                    nxt[tuple(c)] = key
        states = nxt
    d, asg = states[(4, 4, 4, 4)]
    near = [min(range(4), key=lambda v: (dist(r, SLOTS[v]), v)) for r in nodes]
    near_counts = [near.count(v) for v in range(4)]
    cfg = {'inbound': list(asg), 'outbound': list(asg), 'table_index': 'local_y * 4 + local_x', 'table_value': 'VL slot (0 N, 1 E, 2 S, 3 W)',
           'total_distance': d, 'note': 'balanced (4/4/4/4) minimum-distance assignment of the 16 routers of a 4x4 chiplet to its 4 VLs; '
           'the paper-style second (entry) selection for uniform demand, keyed by the destination router. The same table serves as the '
           'nearest-VL entry of DeFT-Dis/RC with ties broken for balance. near_counts = loads of the `near` policy (ties to the lowest VL id).',
           'near_counts': near_counts, 'near_total_distance': sum(dist(r, SLOTS[v]) for r, v in zip(nodes, near))}
    json.dump(cfg, open(NEARBAL, 'w'), indent=1)
    print('balanced-nearest entry table: total distance %d, table %s; near policy: counts %s, distance %d' %
          (d, list(asg), near_counts, cfg['near_total_distance']))


# ---- regress ----
def regress(nproc):
    v = variants('2x2')
    r = ladder('2x2')[3]
    cf = [('DeFT_rr', v['DeFT']), ('MTR', v['MTR']), ('CI_fastQL', ci_fastql_2x2())]
    jobs_old = [('old__' + n, common('2x2', r, 1001) + a + SIM) for n, a in cf]
    jobs_new = [('new__' + n, common('2x2', r, 1001) + a + SIM) for n, a in cf]
    run_jobs(jobs_old, 'regress', nproc, binary=os.path.join(BIN, 'noxim'))
    run_jobs(jobs_new, 'regress', nproc)
    L = ['# Regression of the review binary with its options off', '', 'Same arguments, 2x2 uniform at 1.0 x Lsat, seed 1001; whole stats JSON compared byte by byte.', '']
    for n, _ in cf:
        a = open(os.path.join(RAW, 'regress', 'old__' + n + '.json'), 'rb').read()
        b = open(os.path.join(RAW, 'regress', 'new__' + n + '.json'), 'rb').read()
        L.append('- %s: %s' % (n, 'byte-identical' if a == b else 'DIFFERENT'))
    open(os.path.join(HERE, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


# ---- gap ----
def gap_jobs():
    js = []
    for size in ('2x2', '3x3', '4x4'):
        lad = list(ladder(size))
        if size == '2x2':
            lad = lad + [0.022]
        seeds = (1001, 1002, 1003) if size != '4x4' else (1001, 1002)
        for name, a in variants(size).items():
            for r in lad:
                for s in seeds:
                    js.append(job('gap', name, size, a, r, s))
    return js


# ---- vcsplit ----
def vcsplit_jobs():
    r = ladder('2x2')[3]
    v = variants('2x2')
    js = []
    for name in ('DeFT', 'DeFT_up', 'DeFT_up_fb', 'MTR'):
        n, a = job('vcsplit', name, '2x2', v[name], r, 1001)
        js.append((n, a + ['-deft_lb', 'vc_stats', os.path.join(RAW, 'vcsplit', n + '.vc.json')]))
    return js


# ---- pipe ----
def pipe_jobs():
    js = []
    v = variants('2x2')
    for r in ladder('2x2'):
        for s in (1001, 1002, 1003):
            for N in (0, 2, 3):
                js.append(job('pipe', 'DeFT_pipe%d' % N, '2x2', v['DeFT'], r, s, ['-deft_lb', 'pipe_all', str(N)] if N else []))
                js.append(job('pipe', 'CIfastQL_pipe%d' % N, '2x2', ci_fastql_2x2(N), r, s))
            for N in (0, 2):
                js.append(job('pipe', 'MTR_pipe%d' % N, '2x2', v['MTR'], r, s, ['-deft_lb', 'pipe_all', str(N)] if N else []))
    return js


# ---- summarize ----
def rows_of(stage):
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, stage, '*.json'))):
        if f.endswith('.vc.json'):
            continue
        _, name, size, rate, seed = os.path.basename(f)[:-5].split('__')
        d = json.load(open(f))
        s, l = d['summary'], d['deft_lb']
        rows.append(dict(variant=name, size=size, rate=float(rate), seed=int(seed[1:]), accepted=s['average_ip_throughput_flits_per_cycle_per_ip'],
                         latency=s['global_average_delay_cycles'], p99=l['delay_p99'], received=s['total_received_packets'],
                         injected=s['total_injected_packets'], dead_ends=l['dead_end_events']))
    return rows


def gmean(xs):
    xs = list(xs)
    if not xs:
        return float('nan')
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def summarize():
    L = ['# Review v22: confirming experiments (summary; generated by run_experiments.py summarize)', '']
    for stage in ('gap', 'pipe'):
        rows = rows_of(stage)
        if not rows:
            continue
        with open(os.path.join(HERE, stage + '_runs.csv'), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
            w.writeheader()
            w.writerows(rows)
        dead = sum(r['dead_ends'] for r in rows)
        L += ['## %s: %d runs, dead-end events %d' % (stage, len(rows), dead), '']
        for size in ('2x2', '3x3', '4x4'):
            rs = [r for r in rows if r['size'] == size]
            if not rs:
                continue
            lad = sorted({r['rate'] for r in rs})
            vs = sorted({r['variant'] for r in rs})
            L += ['### %s uniform, fault-free (geometric mean over seeds; latency = head latency from generation, cycles)' % size, '',
                  '| variant | ' + ' | '.join('acc @%.4f' % r for r in lad) + ' | THR (max acc) | LAT @1.0 Lsat | LAT @0.2 Lsat | P99 @1.0 Lsat |',
                  '|---|' + '---|' * (len(lad) + 4)]
            l10, l02 = ladder(size)[3], ladder(size)[0]
            ref = None
            for v in vs:
                cells, acc = [], {}
                for r in lad:
                    xs = [x['accepted'] for x in rs if x['variant'] == v and x['rate'] == r]
                    acc[r] = sum(xs) / len(xs) if xs else float('nan')
                    cells.append('%.4f' % acc[r] if xs else '-')
                thr = max((acc[r] for r in ladder(size) if r in acc and acc[r] == acc[r]), default=float('nan'))
                lat = gmean([x['latency'] for x in rs if x['variant'] == v and x['rate'] == l10])
                lat0 = gmean([x['latency'] for x in rs if x['variant'] == v and x['rate'] == l02])
                p99 = gmean([x['p99'] for x in rs if x['variant'] == v and x['rate'] == l10])
                L.append('| %s | %s | %.4f | %.1f | %.1f | %.1f |' % (v, ' | '.join(cells), thr, lat, lat0, p99))
            L.append('')
            # relative table against the first DeFT variant of the stage
            base = 'DeFT' if 'DeFT' in vs else ('DeFT_pipe0' if 'DeFT_pipe0' in vs else vs[0])
            L += ['Relative to %s (per-seed log ratios, geometric mean over seeds; THR over the 7 ladder loads):' % base, '',
                  '| variant | THR | LAT @1.0 Lsat | LAT @0.2 Lsat | P99 @1.0 Lsat |', '|---|---|---|---|---|']
            seeds = sorted({r['seed'] for r in rs})

            def m(v, s, which):
                if which == 'THR':
                    return max(x['accepted'] for x in rs if x['variant'] == v and x['seed'] == s and x['rate'] in ladder(size))
                rate = l10 if which in ('LAT', 'P99') else l02
                x = next(x for x in rs if x['variant'] == v and x['seed'] == s and x['rate'] == rate)
                return x['p99'] if which == 'P99' else x['latency']
            for v in vs:
                if v == base:
                    continue
                cells = []
                for which in ('THR', 'LAT', 'LAT0', 'P99'):
                    try:
                        e = 100 * (gmean([m(v, s, which) / m(base, s, which) for s in seeds]) - 1)
                        cells.append('%+.1f %%' % e)
                    except (StopIteration, ValueError, ZeroDivisionError):
                        cells.append('-')
                L.append('| %s | %s |' % (v, ' | '.join(cells)))
            L.append('')
    # vcsplit
    files = sorted(glob.glob(os.path.join(RAW, 'vcsplit', '*.vc.json')))
    if files:
        L += ['## vcsplit: VC share VC0:VC1 (%) / VC-wait cycles per flit, per link class, 2x2 uniform at 1.0 x Lsat, seed 1001', '',
              '| variant | chiplet towards VL | chiplet away | interposer | Down VL | Up VL | latency |', '|---|---|---|---|---|---|---|']
        for f in files:
            name = os.path.basename(f).split('__')[1]
            d = json.load(open(f))
            lat = json.load(open(f[:-8] + '.json'))['summary']['global_average_delay_cycles']
            agg = {}
            for l in d['links']:
                a = agg.setdefault(l['cls'], [0, 0, 0])
                a[0] += l['f'][0]
                a[1] += l['f'][1]
                a[2] += sum(l['held']) + sum(l['nocredit'])
            cells = []
            for c in ('chip_towards', 'chip_away', 'ipos', 'vl_down', 'vl_up'):
                a = agg.get(c, [0, 0, 0])
                t = a[0] + a[1]
                cells.append('%.0f:%.0f / %.2f' % (100 * a[0] / t, 100 * a[1] / t, a[2] / t) if t else '-')
            L.append('| %s | %s | %.1f |' % (name, ' | '.join(cells), lat))
        L.append('')
    open(os.path.join(HERE, 'SUMMARY.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RAW, exist_ok=True)
    if stage == 'prep':
        prep()
    elif stage == 'regress':
        regress(nproc)
    elif stage in ('gap', 'vcsplit', 'pipe'):
        js = {'gap': gap_jobs, 'vcsplit': vcsplit_jobs, 'pipe': pipe_jobs}[stage]()
        print(stage, 'jobs:', len(js), flush=True)
        res = run_jobs(js, stage, nproc)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'summarize':
        summarize()
    else:
        raise SystemExit(__doc__)
