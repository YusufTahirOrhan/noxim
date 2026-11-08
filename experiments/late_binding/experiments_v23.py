"""v23 (results_v23_fidelity/): DeFT as in the paper, modelling fixes, cross-validation and the new reference measurements.

Stages (python3 experiments_v23.py STAGE [nproc] [extra]; --shard i/n accepted by the run stages):
  regress   84-configuration set, bin/noxim with the v23 options absent and explicit, against ~/lbbin/noxim_780fa6b and
            ~/lbbin/noxim_v16_3ac1bae (extra = "BIN780,BIN3AC"), whole stats JSON byte by byte -> regression.md
  luts      v23 LUTs (--entry-model both: the v1-v21 `entries` and `entries_by_destination`) for every mask of the rounds,
            rho* of the size -> luts/v23/lut_<size>_<mask>.yaml; lutcheck -> lut_check.md (old `entries` reproduced?)
  probe     B1: head latency of one and three hops with -pipe_all 0, 2, 3 -> probe_pipe.md
  formal    A2: formal/upkeep_check.py -> formal_upkeep.md
  drain     A2 (every VN-based method with the DeFT-P options), B2 (lookahead_route 1) and B3 (vc_per_hop 1 for MTR, RC);
            v10 protocol and masks -> drain_summary.csv
  vcsplit   A2: v17 statistics, DeFT-P and DeFT-B, 2x2 and 4x4 uniform at 1.0 x Lsat (K4 ladders), seeds 41-43 -> vc_split.md
  sat, points   D1: DeFT-P's Lsat per size, scenario and pipe_all (seed 101, 3 x L0, L0 at 0.0002) -> load_points_v23.json
  eval, csv     D2/D3: the pre-registered design, seeds 91-95 -> eval_runs.csv (raw outputs deleted)
  look, lookcsv D5: lookahead check -> look_runs.csv;  herd, herdcsv  D4: hysteresis A/B -> herd_runs.csv
Raw outputs stay under ~/lbraw/v23 (not in the repository). DeFT-P = -deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1
-deft_lut_entry dst; DeFT-B = the same VN options with the v1-v21 entry (src). Every VN-based method of Part D runs with the
DeFT-P VN options and -traffic_rng 1; MTR and RC with -vc_per_hop 1 (and without, as a secondary row).
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
import experiments_v19 as E19  # noqa: E402
import experiments_v21 as E21  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v23_fidelity')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v23')
LUTD = os.path.join(HERE, 'luts', 'v23')
GEN = os.path.join(HERE, '..', '..', 'other', 'deft_vl_lut_generator.py')
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)

# ---- the options of this round ----
VN_P = ['-deft_up_keep', '1', '-deft_rr_fallback', '1', '-deft_vn_rr', '1']   # DeFT-P's VN rules (every VN-based method)
VN_OLD = ['-deft_vn_rr', '1']                                                 # the v19-v21 reference (up_keep 0, fallback 0)
DST = ['-deft_lut_entry', 'dst']
TRNG = ['-traffic_rng', '1']
VCPH = ['-vc_per_hop', '1']
LOOK = ['-deft_lb', 'lookahead_route', '1']
XY = E10.XY
EXPLICIT_OFF = ['-deft_up_keep', '0', '-deft_rr_fallback', '0', '-deft_lut_entry', 'src', '-traffic_rng', '0', '-pipe_all', '0',
                '-vc_per_hop', '0', '-deft_lb', 'lookahead_route', '0', '-deft_lb', 'hysteresis', '0']
MULTS9 = [0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]
N_FAST = {'CI_heurLA_G': 2, 'CI_qlLA_G': 3, 'FULL_heurLA_G': 2, 'FULL_qlLA_G': 3, 'CI_fast': 2, 'CI_fastQL': 3, 'FULL_fast': 3, 'FULL_fastQL': 3}


def raw(stage):
    return os.path.join(RAW, stage)


def pipe(n):
    return ['-pipe_all', str(n)] if n else []


def residual(variant, pipe_all):
    """D5: the decision-delay residual of lookahead routing, max(0, N_fast + 1 - W) with W = pipe_all + 1."""
    return max(0, N_FAST[variant] - pipe_all)


# ---- masks and LUTs ----
def round_masks(size):
    """Every fault mask a run of the rounds can use on this size: v5/v9 masks, the 2x2 drain masks, the v11 masks."""
    ms = [E5.FREE[size], E5.NORTH[size]]
    if size == '2x2':
        ms += [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    v11 = json.load(open(os.path.join(HERE, 'results_v11', 'masks.json')))
    for k in E11.KS:
        ms += v11['%s__k%d' % (size, k)]
    out = []
    for m in ms:
        if m not in out:
            out.append(m)
    return out


def lut23(size, mask):
    return os.path.join(LUTD, 'lut_%s_%s.yaml' % (size, mask))


def _gen(arg):
    size, mask = arg
    cx, cy = E5.SIZES[size]
    out = lut23(size, mask)
    if os.path.exists(out):
        return out, 0.0
    t = time.time()
    subprocess.run([sys.executable, GEN, '--chiplets-x', str(cx), '--chiplets-y', str(cy), '--rho', E10.CH5[size]['DeFT'],
                    '--fault-mask', mask, '--entry-model', 'both', '--output', out], check=True)
    return out, time.time() - t


def luts(nproc):
    from multiprocessing import Pool
    os.makedirs(LUTD, exist_ok=True)
    jobs = [(z, m) for z in SIZES for m in round_masks(z)]
    with Pool(nproc) as pool:
        res = pool.map(_gen, jobs, chunksize=1)
    print('%d LUTs; generation seconds: %s' % (len(res), ' '.join('%.0f' % t for _, t in res)))


def _selected(path):
    """{(mask, source router, destination chiplet): (exit VL, entry VL)} of a LUT's `entries`."""
    import yaml
    d = yaml.safe_load(open(path))
    return {(e['key']['fault_mask_id'].lower(), e['key']['source_router_id'], e['key']['destination_chiplet_id']):
            (e['value']['source_exit']['selected_vl_id'], e['value']['destination_entry']['selected_vl_id']) for e in d['entries']}


def lutcheck():
    """Are the v23 `entries` the ones of the LUTs used in v1-v21 (same rho, same masks)?"""
    L = ['# v23 LUTs against the LUTs of the earlier rounds (experiments_v23.py lutcheck)', '',
         'Per size and mask: the `entries` (exit and entry VL per key) of luts/v23/lut_<size>_<mask>.yaml against the file the earlier rounds used for that mask '
         '(2x2: luts/lut_rho001.yaml for the drain masks, luts/v5 for the v5 masks, luts/v11 for the v11 masks; 3x3 and 4x4: luts/v5 and luts/v11). '
         'identical = every key has the same exit and the same entry VL.', '', '| size | mask | reference file | keys | differing exits | differing entries |', '|---|---|---|---|---|---|']
    ok = True
    for z in SIZES:
        v11 = json.load(open(os.path.join(HERE, 'results_v11', 'masks.json')))
        v11m = [m for k in E11.KS for m in v11['%s__k%d' % (z, k)]]
        for m in round_masks(z):
            if m in v11m:
                ref = E11.lut_path(z, m)
            elif z == '2x2' and m not in (E5.FREE[z], E5.NORTH[z], '0x9C63'):
                ref = os.path.join(HERE, 'luts', 'lut_rho001.yaml')
            else:
                ref = E5.lut_path(z, E10.CH5[z]['DeFT'])
            new, old = _selected(lut23(z, m)), _selected(ref)
            keys = [k for k in new if k in old]
            de = sum(1 for k in keys if new[k][0] != old[k][0])
            dn = sum(1 for k in keys if new[k][1] != old[k][1])
            ok = ok and de == 0 and dn == 0 and len(keys) == len(new)
            L.append('| %s | %s | %s | %d (%d in the reference) | %d | %d |' % (z, m, os.path.relpath(ref, HERE), len(new), len(keys), de, dn))
    L += ['', '**All v23 `entries` identical to the earlier LUTs: %s.** If so, DeFT-B can use the v23 files; otherwise DeFT-B keeps the old files.' % ok]
    open(os.path.join(RES, 'lut_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return ok


def lut_for(size, mask, variant):
    """The LUT of a run: the v23 file of the mask for every method (its `entries` equal the old ones, lut_check.md)."""
    return lut23(size, mask)


# ---- methods ----
def methods(size, vn=None, pipe_all=0):
    """Noxim arguments of the methods of this round. vn: VN options of the VN-based methods (default DeFT-P's)."""
    vn = list(VN_P if vn is None else vn)
    mm = E10.methods(size)
    m = {
        'DeFT_P': ['-routing', 'DEFT'] + vn + DST,
        'DeFT_B': ['-routing', 'DEFT'] + vn,
        'DeFT_old': ['-routing', 'DEFT'] + VN_OLD,
        'DeFT_Dis': list(mm['DeFT_Dis']) + vn,
        'DeFT_Ran': list(mm['DeFT_Ran']) + vn,
        'XY_SP': list(mm['XY_SP']) + vn,
        'DeFT_OE_G': list(mm['DeFT_OE_G']) + vn,
        'DeFT_OE_G_dst': list(mm['DeFT_OE_G']) + vn + DST,
        'CI_heurLA_G': list(mm['CI_heurLA_G']) + vn,
        'CI_qlLA_G': list(mm['CI_qlLA_G']) + vn,
        'FULL_qlLA_G': list(mm['FULL_qlLA_G']) + vn,
        'MTR': list(mm['MTR']) + VCPH,
        'RC': list(mm['RC']) + VCPH,
        'MTR_static': list(mm['MTR']),
        'RC_static': list(mm['RC']),
    }
    for v in E21.FAST:
        m[v] = E21.variant_args(size, v, 0) + vn      # at N_fast (E21 adds -deft_vn_rr 1; repeated flags are harmless)
    return {k: a + pipe(pipe_all) for k, a in m.items()}


# ---- regression ----
def regress(refs, nproc):
    import check_stats_regression as CSR
    from multiprocessing import Pool
    out = raw('regress')
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in SIZES:
        mm = E10.methods(size)
        r = E10.LP5['%s__uniform__%s' % (size, E5.FREE[size])]['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append(('%s__%s' % (v, size), a))
    new = os.path.join(BIN, 'noxim')
    tags = [('ref0', refs[0], []), ('ref1', refs[1], []), ('new', new, []), ('explicit', new, EXPLICIT_OFF)]
    jobs = [((t, b, ex, n, a), out) for t, b, ex in tags for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = {t: 0 for t, _, _ in tags[1:]}, []
    for n, _ in cf:
        base = os.path.join(out, 'ref0__%s.json' % n)
        for t, _, _ in tags[1:]:
            f = os.path.join(out, '%s__%s.json' % (t, n))
            if os.path.exists(base) and os.path.exists(f) and open(base, 'rb').read() == open(f, 'rb').read():
                ok[t] += 1
            else:
                diffs.append('- %s differs: %s' % (t, n))
    L = ['# Regression with the v23 options off (experiments_v23.py regress)', '',
         'References: 780fa6b build md5 %s; 3ac1bae build md5 %s. New binary: md5 %s (A1: -deft_up_keep, -deft_rr_fallback, -deft_lut_entry, -traffic_rng; '
         'B1-B4: -pipe_all, -deft_lb lookahead_route, -vc_per_hop, -deft_lb hysteresis).' % (E19.md5(refs[0]), E19.md5(refs[1]), E19.md5(new)),
         'Configurations: %d = the 84-configuration set of v14-v21. Comparison: the whole stats JSON file, byte by byte, against the 780fa6b build.' % len(cf), '',
         '* 3ac1bae build: **%d / %d byte-identical**.' % (ok['ref1'], len(cf)),
         '* New binary, options absent: **%d / %d byte-identical**.' % (ok['new'], len(cf)),
         '* New binary, `%s` given: **%d / %d byte-identical**.' % (' '.join(EXPLICIT_OFF), ok['explicit'], len(cf)), ''] + (diffs or ['No differences.'])
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if not diffs:
        shutil.rmtree(out)
    return not diffs


# ---- B1 probe ----
def probe(nproc):
    out = raw('probe')
    os.makedirs(out, exist_ok=True)
    pairs = {'1hop': (0, 1), '3hop': (0, 3), '16hop': (0, 63)}
    for name, (s, d) in pairs.items():
        open(os.path.join(out, name + '.txt'), 'w', newline=NL).write('%% one pair%s%d %d 0.0005%s' % (NL, s, d, NL))
    js = []
    for name in pairs:
        for n in (0, 2, 3):
            a = ['-config', '../config_examples/deft_2_5d_traffic_uniform.yaml', '-seed', '1', '-deft_vl_lut', lut23('2x2', E5.FREE['2x2']),
                 '-stats_format', 'json', '-routing', 'DEFT', '-traffic', 'table', os.path.join(out, name + '.txt'), '-sim', '6000', '-warmup', '1000'] + pipe(n)
            js.append(('probe__%s__pipe%d' % (name, n), a))
    res = run_jobs(js, out, nproc=nproc, timeout=600)
    L = ['# B1: head latency against -pipe_all (experiments_v23.py probe)', '',
         'One source-destination pair at rate 0.0005, DEFT routing, 2x2 fault-free; latency = head latency from generation (cycles). '
         'Without the option a hop costs 2 cycles (link + router) and the PE-to-router and router-to-PE links 2 each; -pipe_all N must add N per router on the path.', '',
         '| pair (routers on the path) | pipe_all 0 | pipe_all 2 | pipe_all 3 | per-router increment at 2 / 3 |', '|---|---|---|---|---|']
    hops = {'1hop': 2, '3hop': 4, '16hop': 17}
    for name in pairs:
        lat = [res['probe__%s__pipe%d' % (name, n)]['summary']['global_average_delay_cycles'] for n in (0, 2, 3)]
        L.append('| %s (%d routers) | %.1f | %.1f | %.1f | %.2f / %.2f |' % (name, hops[name], lat[0], lat[1], lat[2], (lat[1] - lat[0]) / hops[name], (lat[2] - lat[0]) / hops[name]))
    open(os.path.join(RES, 'probe_pipe.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


# ---- A2 / B2 / B3 drain tests ----
def drain_jobs():
    """v10 protocol and masks (experiments_v10.drain_jobs), with the v23 LUT of each mask."""
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    groups = []
    vn_methods = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran', 'XY_SP', 'DeFT_OE_G', 'DeFT_OE_G_dst', 'CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
    look_methods = ['CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G'] + E21.FAST
    js = []
    for size in SIZES:
        mm = methods(size)
        cfg = [('A2', v, mm[v], False) for v in vn_methods]
        cfg += [('B2', v + '_look', mm[v] + LOOK, False) for v in look_methods]
        cfg += [('B3', v, mm[v], True) for v in ('MTR', 'RC')]
        for part, v, a0, ff_only in cfg:
            if size == '2x2':
                for m in (['0x0000'] if ff_only else masks2):
                    for seed in (1, 2):
                        js.append(('allpairs__%s__2x2-%s__s%d' % (v, m, seed),
                                   common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=lut23('2x2', m)) + a0 + E10.DRAIN_ALLPAIRS_2X2))
                for m in (['0x0000'] if ff_only else ['0x0000', '0x1111', '0x9C63', '0x7BDE']):
                    for pat in ('uniform', 'chipperm', 'hotspot'):
                        js.append(('%s0.03__%s__2x2-%s__s1' % (pat, v, m),
                                   common_args(1, m, traffic=E5.REL + 'traffic/%s_0.0300.txt' % pat, lut=lut23('2x2', m)) + a0 + E10.DRAIN_OVERSAT_2X2))
                continue
            for m in ([E5.FREE[size]] if ff_only else [E5.FREE[size], E5.NORTH[size]]):
                for seed in (1, 2):
                    js.append(('allpairs__%s__%s-%s__s%d' % (v, size, m, seed),
                               common_args(seed, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(size), lut=lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_ALLPAIRS))
                for pat in ('uniform', 'chipperm', 'hotspot'):
                    key = '%s__%s__%s' % (size, pat, m) if '%s__%s__%s' % (size, pat, m) in E10.LP5 else '%s__%s__%s' % (size, pat, E5.FREE[size])
                    r = E10.LP5[key]['eval'][6]
                    js.append(('%s%.4f__%s__%s-%s__s1' % (pat, r, v, size, m),
                               common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), pat, r), lut=lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
        groups.append(size)
    return js


# ---- A2 VC split ----
CLASSES = E19.CLASSES
CNAME = E19.CNAME


def vcsplit(nproc):
    out = raw('vcsplit')
    os.makedirs(out, exist_ok=True)
    P = E19.lp()
    js = []
    for z in ('2x2', '4x4'):
        r = P['%s__uniform__%s' % (z, E5.FREE[z])]['eval'][3]
        for v in ('DeFT_P', 'DeFT_B', 'DeFT_old'):
            for s in (41, 42, 43):
                n = 'vcs__%s__%s__s%d' % (v, z, s)
                _, a = E5.job('vcs', z, v, methods(z)[v], 'uniform', E5.FREE[z], r, s, lut23(z, E5.FREE[z]))
                js.append((n, a + ['-deft_lb', 'vc_stats', os.path.join(out, n + '.vc.json')]))
    run_jobs(js, out, nproc=nproc, timeout=7200)
    L = ['# A2: VC split per link class with the paper\'s rules (experiments_v23.py vcsplit)', '',
         'Uniform, 1.0 x Lsat of the K4 ladders (load_points_rr.json), seeds 41-43, v17 statistics. Each cell: share of flits VC0:VC1 (%), then VC-wait cycles per flit. '
         'DeFT_old = the v19-v21 reference (-deft_vn_rr 1 only).', '',
         '| size | method | ' + ' | '.join(CNAME[c] for c in CLASSES) + ' | latency |', '|---|---|' + '---|' * (len(CLASSES) + 1)]
    rows = []
    for z in ('2x2', '4x4'):
        for v in ('DeFT_P', 'DeFT_B', 'DeFT_old'):
            cells, lat = [], []
            agg = {c: [0, 0, 0] for c in CLASSES}
            for s in (41, 42, 43):
                n = 'vcs__%s__%s__s%d' % (v, z, s)
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
                cells.append('%.0f:%.0f / %.2f' % (100 * a[0] / t, 100 * a[1] / t, a[2] / t))
                rows.append(dict(size=z, method=v, cls=c, f0=a[0], f1=a[1], wait=a[2]))
            L.append('| %s | %s | %s | %.1f |' % (z, v, ' | '.join(cells), sum(lat) / 3))
    open(os.path.join(RES, 'vc_split.md'), 'w', newline=NL).write(NL.join(L) + NL)
    with open(os.path.join(RES, 'vc_split_runs.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(NL.join(L))
    shutil.rmtree(out)


# ---- per-run CSV ----
def to_csv(stage, fn, extra_fields=()):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw(stage), '*.json'))):
        if f.endswith('.vc.json'):
            continue
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up = l['vl_down_packets'], l['vl_up_packets']
        has = any(down)
        row = dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed,
                   accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']), latency=repr(s['global_average_delay_cycles']),
                   p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                   dead_ends=l['dead_end_events'], vl_imbalance=repr(MK.imbalance(m, down, up)) if has else '', vl_source='run' if has else 'none')
        for k in extra_fields:
            row[k] = l.get(k, '')
        rows.append(row)
    out = os.path.join(RES, fn)
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS + list(extra_fields), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('%s: %d rows; dead ends %d' % (out, len(rows), sum(int(r['dead_ends']) for r in rows)))
    return len(rows)


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(extra.split(','), nproc) else 1)
    elif stage == 'luts':
        luts(nproc)
    elif stage == 'lutcheck':
        sys.exit(0 if lutcheck() else 1)
    elif stage == 'probe':
        probe(nproc)
    elif stage == 'formal':
        sys.exit(subprocess.call([sys.executable, os.path.join(HERE, 'formal', 'upkeep_check.py'), str(nproc), os.path.join(RES, 'formal_upkeep.md')]))
    elif stage == 'drain':
        js = drain_jobs()
        print('drain jobs:', len(js), flush=True)
        res = run_jobs(js, raw('drain'), nproc=nproc, timeout=14400)
        fails = E19.drain_report(res, os.path.join(RES, 'drain_summary.csv'))
        if not fails:
            shutil.rmtree(raw('drain'))
        sys.exit(1 if fails else 0)
    elif stage == 'vcsplit':
        vcsplit(nproc)
    else:
        import experiments_v23_eval as EV   # D stages live in a second module (written with the pre-registration)
        EV.run_stage(stage, nproc, extra)
