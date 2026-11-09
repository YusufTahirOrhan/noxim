"""v24 (results_v24_xy/): late binding without path adaptivity (XY and a VN-split order on the interposer).

Stages (python3 experiments_v24.py STAGE [nproc] [extra]; --shard i/n accepted by the run stages):
  repro     A0: the ten probe rows of the review, existing options only, the 8d84634 build -> repro_a0.json
  regress   B4: the 84-configuration set, bin/noxim with the v24 options absent and explicitly off, against the 8d84634 build
            (extra = the reference binary), whole stats JSON byte by byte -> regression.md
  busy      B3: busy_state on against off without lookahead (CI_qlLA_G, 2x2 and 4x4 uniform, 5 runs) -> busy_state_check.md
  equiv     B4: Q-learning with alpha = 0 against the heuristic under lookahead + fallback + busy_state -> equivalence.md
  repro2    B4: the six probe values that need the new options -> repro_b4.json
  formal    A2: formal/xy_check.py -> formal_xy.md
  drain     A3: drain tests (extra = v10 | tuned | b13) -> drain_summary.csv (rows of all three parts are kept)
  sat, points   B5: DeFT-P's chiptrans ladders (seed 101, pipe_all 2) -> load_points_v24.json
  b5        B5: the six chiptrans probe rows -> repro_b5.json
  reprodoc  reproduction.md from repro_a0.json, repro_b4.json and repro_b5.json
The tuning (C2), the centre-cut statistics (A4) and the Part D stages are in experiments_v24_eval.py and dispatched from here.
Raw outputs stay under ~/lbraw/v24 (not in the repository). Reference binary: ~/lbbin/noxim_8d84634.
Every VN-based method runs with DeFT-P's VN options and -traffic_rng 1; MTR and RC with -vc_per_hop 1; LUTs luts/v23.
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args, run_jobs, shard_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v24_xy')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v24')
REF_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_8d84634')
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)

# ---- options ----
VN_P, DST, TRNG, VCPH, LOOK = X23.VN_P, X23.DST, X23.TRNG, X23.VCPH, X23.LOOK


def lb(*kv):
    """['-deft_lb', k1, v1, '-deft_lb', k2, v2, ...]"""
    out = []
    for i in range(0, len(kv), 2):
        out += ['-deft_lb', str(kv[i]), str(kv[i + 1])]
    return out


IPX = lb('ipos_tm', 'XY')
IPOE = lb('ipos_tm', 'OE')
IPO1 = lb('ipos_tm', 'O1')
REL_X = lb('chip_tm', 'XY', 'ipos_tm', 'XY')
REL_O = lb('chip_tm', 'XY', 'ipos_tm', 'O1')
FALLBACK = lb('lookahead_fallback', 1)
BUSY = lb('busy_state', 1)
HOPS = lb('hop_stats', 1)
EXPLICIT_OFF = X23.EXPLICIT_OFF + lb('lut_bias', 0, 'lookahead_fallback', 0, 'busy_state', 0)


def raw(stage):
    return os.path.join(RAW, stage)


def dd(n):
    return lb('decision_delay', n)


def mask_of(size, kind):
    return E5.FREE[size] if kind == 'free' else E5.NORTH[size]


def job(stage, size, name, method_args, pipe, p, m, rate, seed, extra=()):
    """One run. method_args: the Noxim arguments of the method without pipe depth and without -traffic_rng (both are added here)."""
    rname = '%s__%s-p%d__%s-%s__%s__%.4f__s%d' % (stage, name, pipe, size, p, m, rate, seed)
    args = common_args(seed, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), p, rate), lut=X23.lut23(size, m)) + \
        E5.size_args(size) + list(method_args) + X23.pipe(pipe) + TRNG + list(extra) + E5.SIM
    return rname, args


def run_with(binary, jobs, out, nproc, timeout=7200):
    """Run (name, args) jobs with a given binary; returns {name: parsed JSON or None}. Existing outputs are kept."""
    from multiprocessing import Pool
    os.makedirs(out, exist_ok=True)
    tagged = [(('bin', binary, [], n, a), out) for n, a in jobs]
    with Pool(nproc) as pool:
        res = pool.map(E10._run_tagged, tagged, chunksize=1)
    return {k[1]: v for k, v in res}


def tagged_path(out, name):
    return os.path.join(out, 'bin__%s.json' % name)


def stat(d):
    """(accepted flits/node/cycle, mean latency, received packets, p99) of a run's JSON."""
    s = d['summary']
    return (s['average_ip_throughput_flits_per_cycle_per_ip'], s['global_average_delay_cycles'], s['total_received_packets'], d['deft_lb']['delay_p99'])


# ---- A0 ----
A0_ROWS = [
    # no, size, v23 method, extra, pipe, pattern, mask kind, rate, received, latency (the review's probe values)
    (1, '4x4', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0050, 10469, 98.7693189416),
    (2, '4x4', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0070, 13434, 456.9803483698),
    (3, '4x4', 'CI_qlLA_G', IPX, 0, 'uniform', 'free', 0.0100, 20549, 185.3428877318),
    (4, '4x4', 'CI_qlLA_G', IPX, 0, 'uniform', 'north', 0.0075, 15317, 215.4711105308),
    (5, '4x4', 'CI_qlLA_G', IPX, 0, 'hotspot', 'free', 0.0022, 4567, 74.2583753011),
    (6, '4x4', 'DeFT_Dis', IPOE, 0, 'chipperm', 'free', 0.0050, 4397, 1833.8910620878),
    (7, '4x4', 'CI_qlLA_G', IPX + dd(1), 2, 'uniform', 'free', 0.0080, 16575, 95.7701357466),
    (8, '4x4', 'CI_qlLA_G', IPX + LOOK + dd(1), 2, 'uniform', 'free', 0.0080, 16569, 101.4833122095),
    (9, '3x3', 'CI_qlLA_G', IPX, 0, 'chipperm', 'free', 0.0100, 11657, 108.3540362014),
    (10, '2x2', 'CI_qlLA_G', IPX, 0, 'uniform', 'free', 0.0160, 8162, 247.8145062485),
]


def repro(nproc, binary=REF_BIN):
    out = raw('repro')
    js, meta = [], []
    for no, size, meth, extra, pipe, p, kind, rate, rec, lat in A0_ROWS:
        m = mask_of(size, kind)
        E5.gen_tables(size, p, [rate])
        n, a = job('a0', size, 'row%d' % no, X23.methods(size)[meth], pipe, p, m, rate, 91, extra)
        js.append((n, a))
        meta.append((no, size, meth, ' '.join(extra), pipe, p, m, rate, rec, lat, n))
    res = run_with(binary, js, out, nproc)
    rows = []
    for no, size, meth, extra, pipe, p, m, rate, rec, lat, n in meta:
        d = res[n]
        acc, l, r, _ = stat(d) if d else (None, None, None, None)
        rows.append(dict(no=no, size=size, method=meth, extra=extra, pipe_all=pipe, pattern=p, mask=m, rate=rate, probe_received=rec, probe_latency=lat,
                         received=r, latency=l, accepted=acc, same=bool(d) and r == rec and abs(l - lat) < 5e-10))
    json.dump(dict(binary=os.path.basename(binary), md5=E19.md5(binary), rows=rows), open(os.path.join(RES, 'repro_a0.json'), 'w'), indent=1)
    for r in rows:
        print(r['no'], r['size'], r['method'], r['extra'], r['received'], r['probe_received'], r['latency'], r['probe_latency'], 'same' if r['same'] else 'DIFFERENT')
    if all(r['same'] for r in rows):
        shutil.rmtree(out)
    return rows


def _load(name):
    f = os.path.join(RES, name)
    return json.load(open(f)) if os.path.exists(f) else None


def reprodoc():
    """reproduction.md from the JSON files of the reproduction stages (A0, B4, B5); sections of stages not yet run are left out."""
    L = ['# v24 reproduction of the review\'s probe numbers (experiments_v24.py repro, repro2, b5, reprodoc)', '',
         'The probes were single runs on a scratch build of 8d84634: 4x4 unless stated, seed 91, DeFT-P VN options, `-traffic_rng 1`, the v10 selection',
         'parameters, v23 LUTs and traffic tables, `-sim 10000 -warmup 2000`. Where a value differs, both are listed; the measurement of this round is the one used.', '']
    a0 = _load('repro_a0.json')
    if a0:
        L += ['## A0: existing options only (binary %s, md5 %s)' % (a0['binary'], a0['md5']), '',
              'Method = key of `experiments_v23.methods(size)`, plus the extra arguments, plus the pipe depth and `-traffic_rng 1`.', '',
              '| # | size | method + extra arguments | pipe_all | scenario (mask) | rate | received: probe / this round | latency: probe / this round | result |', '|---|---|---|---|---|---|---|---|---|']
        for r in a0['rows']:
            L.append('| %d | %s | %s `%s` | %d | %s (%s) | %.4f | %d / %s | %.10f / %s | %s |' % (
                r['no'], r['size'], r['method'], r['extra'], r['pipe_all'], r['pattern'], r['mask'], r['rate'], r['probe_received'], r['received'],
                r['probe_latency'], '%.10f' % r['latency'] if r['latency'] is not None else 'no output', 'identical' if r['same'] else '**different**'))
        L += ['', '**%d / %d rows identical** (received packets equal and latency equal to the 10 printed decimals).' % (sum(r['same'] for r in a0['rows']), len(a0['rows'])), '']
    b4 = _load('repro_b4.json')
    if b4:
        L += ['## B4: probe values that need the options of this round (binary md5 %s)' % b4['md5'], '',
              'The probe code was throw-away and may differ from this round\'s implementation in tie-breaking; the target is agreement within 3 %.', '',
              '| variant | pipe_all | scenario, rate | accepted / latency: probe | this round | deviation (accepted, latency) | within 3 % |', '|---|---|---|---|---|---|---|']
        for r in b4['rows']:
            L.append('| %s `%s` | %d | %s %.4f | %.4f / %.1f | %.4f / %.1f | %+.1f %%, %+.1f %% | %s |' % (
                r['method'], r['extra'], r['pipe_all'], r['pattern'], r['rate'], r['probe_accepted'], r['probe_latency'], r['accepted'], r['latency'],
                100 * (r['accepted'] / r['probe_accepted'] - 1), 100 * (r['latency'] / r['probe_latency'] - 1), 'yes' if r['within'] else '**no**'))
        L += ['', '**%d / %d rows within 3 %% on both values.**' % (sum(r['within'] for r in b4['rows']), len(b4['rows'])), '']
        if b4.get('note'):
            L += [b4['note'], '']
    b5 = _load('repro_b5.json')
    if b5:
        L += ['## B5: the new pattern `chiptrans` (4x4, seed 91, pipe_all 0, rate 0.0060; binary md5 %s)' % b5['md5'], '',
              '| method | accepted / latency: probe | this round | deviation (accepted, latency) |', '|---|---|---|---|']
        for r in b5['rows']:
            L.append('| %s%s | %.4f / %.0f | %.4f / %.1f | %+.1f %%, %+.1f %% |' % (
                r['method'], (' `%s`' % r['extra']) if r['extra'] else '', r['probe_accepted'], r['probe_latency'], r['accepted'], r['latency'],
                100 * (r['accepted'] / r['probe_accepted'] - 1), 100 * (r['latency'] / r['probe_latency'] - 1)))
        L.append('')
        if b5.get('note'):
            L += [b5['note'], '']
    open(os.path.join(RES, 'reproduction.md'), 'w', newline=NL).write(NL.join(L))
    print(NL.join(L))


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'repro':
        repro(nproc)
        reprodoc()
    elif stage == 'reprodoc':
        reprodoc()
    else:
        raise SystemExit(__doc__)
