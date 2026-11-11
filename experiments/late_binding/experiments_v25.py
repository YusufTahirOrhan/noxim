"""v25 (results_v25_confirm/): confirmatory round for late binding with XY on the interposer, and the hardware of the final design.

Stages (python3 experiments_v25.py STAGE [nproc] [extra]; --shard i/n accepted by the run stages):
  regress   A5: the 84-configuration set, bin/noxim with every option absent and explicitly off, against the ce6ab6a build
            (~/lbbin/noxim_ce6ab6a, made by build_ref.sh) and the 8d84634 build; whole stats JSON byte by byte -> regression.md
  reuse     A5: 24 evaluation runs of v24 (three per row: the four frozen rows, DeFT_P, DeFT_B, MTR, RC; drawn with
            random.Random(2511)) re-run with the row definitions of this round and compared with results_v24_xy/eval_runs.csv
            -> reuse_check.md
  sat, points   A3: DeFT-P's ladders of the three scenarios the v24 tuning did not see (v23 D1 rule: seed 101, pipe_all 2)
            -> load_points_v25.json, load_points_v25.md
  drain     A4: drain tests of the frozen rows with their tuned values (v10 protocol and masks, plus over-saturated 4x4 runs on
            localized and movinghot) -> drain_summary.csv
The other parts live in their own modules and are dispatched from here:
  Part B (timing, eval, check, csv, sanity)   experiments_v25_eval.py
  Part C (c_*)                                experiments_v25_faults.py
  Part D (d_*)                                experiments_v25_apps.py
  Part E (e_*)                                experiments_v25_pipe0.py
  Part F (f_*)                                experiments_v25_hw.py
Nothing is tuned in this round: the selection parameters are read from results_v24_xy/tuning_choice.json and the row definitions
are those of experiments_v24_eval.row_args. Raw outputs stay under ~/lbraw/v25 (not in the repository).
Every VN-based method runs with DeFT-P's VN options and -traffic_rng 1; MTR and RC with -vc_per_hop 1; LUTs luts/v23.
"""
import csv
import json
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v25_confirm')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v25')
REF_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_ce6ab6a')     # the build this round's results must stay identical to
OLD_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_8d84634')     # the reference of the v24 regression
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)
MULTS9 = X23.MULTS9
lb, job, lkey, stat = X24.lb, X24.job, X24.lkey, X24.stat

# ---- the frozen configuration (results_v24_xy/tuning_choice.json; no retuning) ----
FROZEN = {                                   # row: (variant of v24, mechanism)
    'CI_heurLA_X_LF': ('CI_heurLA_X', 'LF'),      # main
    'CI_heurLA_O_LF': ('CI_heurLA_O', 'LF'),      # second
    'CI_heurLA_X_DLY': ('CI_heurLA_X', 'DLY'),    # the mechanism to fall back on
    'CI_qlLA_X_LF': ('CI_qlLA_X', 'LF'),          # Q-learning with the v24 values
}
MAIN, SECOND = 'CI_heurLA_X_LF', 'CI_heurLA_O_LF'
IDEAL = ['CI_heurLA_X', 'CI_heurLA_O', 'CI_qlLA_X']      # the same variants with an ideal decision (Part E, checks)
REFS_ALL = ['DeFT_P', 'DeFT_B']              # on every scenario
REFS_FF = ['MTR', 'RC', 'XY_SP']             # fault-free scenarios only
REFS_FAULT = ['DeFT_Dis', 'DeFT_Ran']        # scenarios with faults only (fault-free they are DeFT-P's routes, v24 FINDINGS question 1)


def raw(stage):
    return os.path.join(RAW, stage)


def row_args(size, row):
    """Noxim arguments of a row, without the pipe depth and -traffic_rng (job() adds both). The frozen rows and DeFT_P, DeFT_B, MTR,
    RC are built by the v24 code itself, so they are the v24 rows argument for argument."""
    if row in FROZEN:
        base, kind = FROZEN[row]
        return EV24.row_args(size, row, base, kind)
    if row in IDEAL:
        return EV24.row_args(size, row, row, 'ideal')
    if row in ('DeFT_P', 'DeFT_B', 'MTR', 'RC'):
        return EV24.row_args(size, row, row, None)
    if row == 'XY_SP':                       # v10 definition with the VN options (experiments_v23.methods); count_vl only counts
        return X23.methods(size)['XY_SP'] + lb('count_vl', 1)
    if row in ('DeFT_Dis', 'DeFT_Ran'):      # DEFT_LB rows: hop_stats only counts
        return X23.methods(size)[row] + X24.HOPS
    raise ValueError(row)


def scenarios(size):
    """The eight scenarios of this round: six fault-free, two with one faulty VL per chiplet (the v9 masks)."""
    f, n = E5.FREE[size], E5.NORTH[size]
    return [('uniform', f), ('localized', f), ('hotspot', f), ('chipperm', f), ('chiptrans', f), ('movinghot', f), ('uniform', n), ('hotspot', n)]


def new_scenarios(size):
    """Not seen by the v24 tuning."""
    f, n = E5.FREE[size], E5.NORTH[size]
    return [('localized', f), ('movinghot', f), ('hotspot', n)]


def is_new(size, p, m):
    return (p, m) in new_scenarios(size)


def faulty(m):
    return int(m, 16) != 0


def sname(size, p, m):
    """Short scenario name of the tables: the pattern, with '+f' for one faulty VL per chiplet."""
    return p + ('+f' if faulty(m) else '')


LP_FILE = os.path.join(RES, 'load_points_v25.json')


def lp():
    return json.load(open(LP_FILE))


# ---- A5: regression ----
def regress(nproc):
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
    tags = [('ref', REF_BIN, []), ('old', OLD_BIN, []), ('new', new, []), ('explicit', new, X24.EXPLICIT_OFF)]
    jobs = [((t, b, ex, n, a), out) for t, b, ex in tags for n, a in cf]
    with Pool(nproc) as pool:
        pool.map(E10._run_tagged, jobs, chunksize=1)
    ok, diffs = {t: 0 for t, _, _ in tags[1:]}, []
    for n, _ in cf:
        base = os.path.join(out, 'ref__%s.json' % n)
        for t, _, _ in tags[1:]:
            f = os.path.join(out, '%s__%s.json' % (t, n))
            if os.path.exists(base) and os.path.exists(f) and open(base, 'rb').read() == open(f, 'rb').read():
                ok[t] += 1
            else:
                diffs.append('- %s differs: %s' % (t, n))
    md = {t: E19.md5(b) for t, b, _ in tags[:3]}
    L = ['# A5: regression before the confirmatory round (experiments_v25.py regress)', '',
         'Reference: the ce6ab6a build (the last commit of round 24), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 %s.' % md['ref'],
         'Current binary `bin/noxim`: md5 %s (%s the reference build). The 8d84634 build (round 23, the reference of the v24 regression): md5 %s.' % (
             md['new'], 'the same file as' if md['new'] == md['ref'] else '**not the same file as**', md['old']),
         'Configurations: %d = the 84-configuration set of v14-v24. Comparison: the whole stats JSON file, byte by byte, against the ce6ab6a build.' % len(cf), '',
         '* 8d84634 build: **%d / %d byte-identical**.' % (ok['old'], len(cf)),
         '* `bin/noxim`, options absent: **%d / %d byte-identical**.' % (ok['new'], len(cf)),
         '* `bin/noxim`, `%s` given: **%d / %d byte-identical**.' % (' '.join(X24.EXPLICIT_OFF), ok['explicit'], len(cf)), ''] + (diffs or ['No differences.'])
    import subprocess
    changed = subprocess.run(['git', '-C', os.path.join(HERE, '..', '..'), 'diff', '--name-only', 'ce6ab6a', '--', 'src', 'bin/Makefile'],
                             capture_output=True, text=True).stdout.split()
    L += ['', 'Simulator sources against ce6ab6a when this file was written (`git diff --name-only ce6ab6a -- src bin/Makefile`): %s.' % (
        'no difference' if not changed else 'changed: ' + ', '.join(changed))]
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if not diffs:
        shutil.rmtree(out)
    return not diffs


# ---- A5: the rows of this round reproduce the v24 runs ----
REUSE_DRAW_SEED = 2511
REUSE_ROWS = list(FROZEN) + ['DeFT_P', 'DeFT_B', 'MTR', 'RC']
REUSE_FIELDS = ('accepted', 'latency', 'p99', 'injected', 'received', 'dead_ends') + EV24.EXTRA_FIELDS


def reuse(nproc):
    rows = list(csv.DictReader(open(os.path.join(X24.RES, 'eval_runs.csv'))))
    rnd = random.Random(REUSE_DRAW_SEED)
    pick = []
    for row in REUSE_ROWS:
        pick += rnd.sample([r for r in rows if r['variant'] == row + '-p2'], 3)
    js = []
    for r in pick:
        size, p = r['pattern'].split('-')
        js.append(job('reuse', size, r['variant'][:-3], row_args(size, r['variant'][:-3]), 2, p, r['mask'], float(r['rate']), int(r['seed'])))
    res = run_jobs(js, raw('reuse'), nproc=nproc, timeout=7200)
    ok, lines = 0, []
    for r, (n, _) in zip(pick, js):
        d = res.get(n)
        new = {}
        if d:
            s, l = d['summary'], d['deft_lb']
            new = dict(accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']), latency=repr(s['global_average_delay_cycles']), p99=repr(l['delay_p99']),
                       injected=str(s['total_injected_packets']), received=str(s['total_received_packets']), dead_ends=str(l['dead_end_events']))
            for k in EV24.EXTRA_FIELDS:
                new[k] = str(l.get(k, ''))
        same = bool(d) and all(new[k] == r[k] for k in REUSE_FIELDS)
        ok += same
        lines.append('| %s | %s %s | %s | %s | %s / %s | %s / %s | %s |' % (r['variant'], r['pattern'], r['mask'], r['rate'], r['seed'], r['latency'][:10], new.get('latency', 'no output')[:10],
                                                                    r['accepted'][:9], new.get('accepted', '')[:9], 'identical' if same else '**DIFFERENT**'))
    L = ['# A5: the rows of this round reproduce the v24 runs (experiments_v25.py reuse)', '',
         'Three evaluation runs of round 24 per row (the four frozen rows and DeFT_P, DeFT_B, MTR, RC; drawn with `random.Random(%d).sample` from' % REUSE_DRAW_SEED,
         '`results_v24_xy/eval_runs.csv`, seeds 111-115) were run again with `bin/noxim` and the row definitions of this round (`experiments_v25.row_args`) and compared',
         'field by field (repr of the JSON values): accepted, latency, p99, injected, received, dead ends and the hop and lookahead counters.', '',
         '**%d / %d identical.**' % (ok, len(pick)), '', '| row | scenario | rate | seed | latency v24 / now | accepted v24 / now | result |', '|---|---|---|---|---|---|---|'] + lines
    open(os.path.join(RES, 'reuse_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if ok == len(pick):
        shutil.rmtree(raw('reuse'))
    return ok == len(pick)


# ---- A3: ladders of the three new scenarios (the v23 D1 rule: DeFT-P, seed 101, pipe_all 2, 3 x L0, 9 loads) ----
def sat_name(size, p, m, r):
    return 'sat__DeFT_P-p2__%s-%s__%s__%.4f__s101' % (size, p, m, r)


def sat_job(size, p, m, r):
    return job('sat', size, 'DeFT_P', X23.methods(size)['DeFT_P'], 2, p, m, r, 101)


def lat_of(size, p, m, r):
    return json.load(open(os.path.join(raw('sat'), sat_name(size, p, m, r) + '.json')))['summary']['global_average_delay_cycles']


def coarse_lsat(size, p, m):
    l0 = lat_of(size, p, m, E5.L0_RATE)
    lsat = None
    for r in E5.SAT_RATES:
        if lat_of(size, p, m, r) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_rates(size, p, m):
    lsat, nxt = coarse_lsat(size, p, m)
    if lsat is None or nxt is None or lsat > E5.LOW_LSAT:
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sat(nproc):
    js = []
    for s in SIZES:
        for p, m in new_scenarios(s):
            E5.gen_tables(s, p, E5.SAT_RATES + [E5.L0_RATE])
            js += [sat_job(s, p, m, r) for r in E5.SAT_RATES + [E5.L0_RATE]]
    print('coarse jobs:', len(js), flush=True)
    run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    js = []
    for s in SIZES:
        for p, m in new_scenarios(s):
            fr = fine_rates(s, p, m)
            E5.gen_tables(s, p, fr)
            js += [sat_job(s, p, m, r) for r in fr]
    print('fine jobs:', len(js), flush=True)
    res = run_jobs(js, raw('sat'), nproc=nproc, timeout=7200)
    print('fine runs', len(js), 'missing', sum(1 for v in res.values() if v is None))


def points():
    old = X24.lp()
    res = dict(old)          # the five scenarios of v24 keep their ladders; the pipe_all 0 ladders of v23 are kept for Part E
    L = ['# Load points of v25 (experiments_v25.py sat, points)', '',
         'The five scenarios of round 24 keep their ladders (`results_v24_xy/load_points_v24.json`). The three scenarios the v24 tuning did not see (localized and',
         'movinghot fault-free, hotspot with one faulty VL per chiplet) get their ladders by the v23 D1 rule, run again in this round with `bin/noxim`: DeFT-P',
         '(-deft_up_keep 1 -deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst -traffic_rng 1), seed 101, pipe_all 2; L0 = latency at 0.0002; Lsat = the largest swept',
         'rate before the latency first exceeds 3 x L0, on the 0.0001 grid where the coarse (0.0005-grid) Lsat is <= 0.004 and on the 0.0005 grid otherwise; 9 loads at',
         '0.2, 0.5, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4 x Lsat. Round 23 had made ladders for the same three scenarios by the same rule; the last column says whether',
         'this round\'s ladder equals it. Part E uses the pipe_all 0 ladders of round 23, copied unchanged.', '',
         '| size | scenario | source | grid | L0 | Lsat | lat / L0 at Lsat | ladder (pipe_all 2) | equal to the v23 ladder |', '|---|---|---|---|---|---|---|---|---|']
    alleq = True
    for s in SIZES:
        new = {}
        for p, m in new_scenarios(s):
            l0 = lat_of(s, p, m, E5.L0_RATE)
            fr = fine_rates(s, p, m)
            grid, rates = (E5.FINE, fr) if fr else (E5.GRID, E5.SAT_RATES)
            lsat = None
            for r in rates:
                if lat_of(s, p, m, r) > 3 * l0:
                    break
                lsat = r
            ev = []
            for mult in MULTS9:
                x = round(max(grid, round(mult * lsat / grid) * grid), 4)
                if ev and x <= ev[-1]:
                    x = round(ev[-1] + grid, 4)
                ev.append(x)
            new[(p, m)] = {'lsat': lsat, 'eval': ev, 'grid': grid, 'l0': l0, 'pipe_all': 2}
        for p, m in scenarios(s):
            k = lkey(s, p, m)
            if (p, m) in new:
                e = new[(p, m)]
                eq = k in old and old[k]['eval'] == e['eval'] and old[k]['lsat'] == e['lsat'] and old[k]['l0'] == e['l0']
                alleq = alleq and eq
                res[k] = e
                L.append('| %s | %s %s | v25 | %s | %.1f | %s | %.2f | %s | %s |' % (s, p, m, e['grid'], e['l0'], e['lsat'], lat_of(s, p, m, e['lsat']) / e['l0'], e['eval'],
                                                                              'yes' if eq else '**no** (v23: %s)' % (old[k]['eval'] if k in old else 'none')))
            else:
                e = res[k]
                L.append('| %s | %s %s | v24 | %s | %.1f | %s | (v24) | %s | |' % (s, p, m, e['grid'], e['l0'], e['lsat'], e['eval']))
            E5.gen_tables(s, p, e['eval'])
    L += ['', '**The three ladders made in this round equal those of round 23 on every size: %s.**' % ('yes' if alleq else 'no; this round\'s ladders are used')]
    json.dump(res, open(LP_FILE, 'w'), indent=1)
    open(os.path.join(RES, 'load_points_v25.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(raw('sat'))


# ---- A4: drain tests of the frozen rows with their tuned values ----
def drain_cfgs(size):
    """(label, arguments, pipe_all): the four frozen rows at pipe_all 2 (Parts B-D), and the two rows of Part E at pipe_all 0."""
    out = [('%s-p2' % r, row_args(size, r), 2) for r in FROZEN]
    out += [('%s-p0' % r, row_args(size, r), 0) for r in ('CI_heurLA_X', 'CI_heurLA_X_DLY')]
    return out


def drain_jobs():
    """v10 protocol and masks (experiments_v10.drain_jobs) with the v23 LUT of each mask, plus over-saturated 4x4 runs at 2.4 x Lsat on localized and movinghot."""
    masks2 = [l.strip() for l in open(os.path.join(HERE, 'drain_masks.txt')) if l.strip()]
    P = lp()
    js = []
    for size in SIZES:
        for v, a0, pipe in drain_cfgs(size):
            a0 = a0 + X23.pipe(pipe) + X24.TRNG
            if size == '2x2':
                for m in masks2:
                    for seed in (1, 2):
                        js.append(('allpairs__%s__2x2-%s__s%d' % (v, m, seed),
                                   common_args(seed, m, hardcoded=E5.REL + 'traffic/allpairs_burst.txt', lut=X23.lut23('2x2', m)) + a0 + E10.DRAIN_ALLPAIRS_2X2))
                for m in ['0x0000', '0x1111', '0x9C63', '0x7BDE']:
                    for pat in ('uniform', 'chipperm', 'hotspot'):
                        js.append(('%s0.03__%s__2x2-%s__s1' % (pat, v, m),
                                   common_args(1, m, traffic=E5.REL + 'traffic/%s_0.0300.txt' % pat, lut=X23.lut23('2x2', m)) + a0 + E10.DRAIN_OVERSAT_2X2))
                continue
            for m in [E5.FREE[size], E5.NORTH[size]]:
                for seed in (1, 2):
                    js.append(('allpairs__%s__%s-%s__s%d' % (v, size, m, seed),
                               common_args(seed, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(size), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_ALLPAIRS))
                for pat in ('uniform', 'chipperm', 'hotspot'):
                    key = '%s__%s__%s' % (size, pat, m) if '%s__%s__%s' % (size, pat, m) in E10.LP5 else '%s__%s__%s' % (size, pat, E5.FREE[size])
                    r = E10.LP5[key]['eval'][6]
                    js.append(('%s%.4f__%s__%s-%s__s1' % (pat, r, v, size, m),
                               common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), pat, r), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
            if size == '4x4':
                m = E5.FREE[size]
                for pat in ('localized', 'movinghot'):
                    r = P[lkey(size, pat, m, pipe)]['eval'][8]          # 2.4 x Lsat of the ladder of this pipe depth
                    E5.gen_tables(size, pat, [r])
                    js.append(('sat24-%s%.4f__%s__%s-%s__s1' % (pat, r, v, size, m),
                               common_args(1, m, traffic=E5.REL + '%s/%s_%.4f.txt' % (E5.tdir(size), pat, r), lut=X23.lut23(size, m)) +
                               E5.size_args(size) + a0 + E10.DRAIN_OVERSAT))
    return js


def drain(nproc):
    js = drain_jobs()
    print('drain jobs: %d' % len(js), flush=True)
    res = run_jobs(js, raw('drain'), nproc=nproc, timeout=14400)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_summary.csv'))
    if not fails:
        shutil.rmtree(raw('drain'))
    return not fails


MODULES = {'c': 'experiments_v25_faults', 'd': 'experiments_v25_apps', 'e': 'experiments_v25_pipe0', 'f': 'experiments_v25_hw'}

if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(nproc) else 1)
    elif stage == 'reuse':
        sys.exit(0 if reuse(nproc) else 1)
    elif stage == 'sat':
        sat(nproc)
    elif stage == 'points':
        points()
    elif stage == 'drain':
        sys.exit(0 if drain(nproc) else 1)
    else:
        import importlib
        pre = stage.split('_', 1)[0]
        mod = importlib.import_module(MODULES[pre] if pre in MODULES and '_' in stage else 'experiments_v25_eval')
        mod.run_stage(stage, nproc, extra)
