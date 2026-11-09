"""v24 Part C (tuning), A4 (centre cut) and Part D stages (results_v24_xy/), run through experiments_v24.py:
  tunerule  C2: the pre-registered tuning rule -> tuning.md (written before any tuning run)
  tune1     C2 stage 1: the heuristic grid for relations X and O (24 configurations each) on 2x2 and 4x4, and DeFT-P on the same loads and seeds
  choose1   C2: stage-1 scores and choice -> tuning_choice.json
  tune2     C2 stage 2: Q-learning, alpha grid at the stage-1 choice (plus the v10 values where they are not in it)
  choose2   C2: tuning.md (rule, score tables, chosen values, the v10 values), tuning_choice.json, tune_runs.csv (raw outputs deleted)
  cut       A4: centre-cut statistics, 4x4 chipperm at 0.8 x Lsat, pipe_all 0, seeds 101-102 -> centre_cut.md, centre_cut.csv
  timing    D1: the seed-111 runs at the 2nd, 5th and 9th load of every cell (part of the design), timed -> runtime_estimate.md, drops.json
  eval      D1: the design, seeds 111-115 (raw outputs under ~/lbraw/v24/eval until csv)
  check     integrity of the raw evaluation folder
  csv       eval_runs.csv (raw outputs deleted when complete)
  sanity    report/sanity.md (hops per packet against DeFT_Dis, the largest VL flit rate, observation-only options)
Variant names carry the pipe depth as a suffix (-p2); a candidate's mechanism is a suffix of its name (none = ideal, _LF, _DLY).
"""
import csv
import glob
import json
import math
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X  # noqa: E402
import make_eval_csv as MK  # noqa: E402
from runner import run_jobs  # noqa: E402

RES, RAW, SIZES, NL = X.RES, X.RAW, X.SIZES, X.NL
TUNE_SEEDS = (101, 102)
TUNE_SIZES = ('2x2', '4x4')
TUNE_LOADS = (1, 3, 5, 7)            # ladder indices: 0.5, 1.0, 1.4, 2.0 x Lsat
SEEDS = range(111, 116)
GRID_W, GRID_B, GRID_G, GRID_D, GRID_A = (1, 2), (0, 4), (1, 2), (0, 2, 4), (0.01, 0.05, 0.1)
CHOICE = os.path.join(RES, 'tuning_choice.json')
DROPS = os.path.join(RES, 'drops.json')

REFS = ['DeFT_P', 'DeFT_B', 'MTR', 'RC']
CANDS = ['CI_heurLA_X', 'CI_qlLA_X', 'CI_heurLA_O', 'CI_qlLA_O']
MECHS = ['ideal', 'LF', 'DLY']
SECONDARY = ['FULL_qlLA_X', 'CI_qlLA_G', 'FULL_qlLA_G', 'DeFT_P_O1', 'CI_rand_X', 'CI_heur_X']
CONTROLS = ['CI_qlLA_X_Lnofb', 'CI_qlLA_X_LF0']
EXTRA_FIELDS = ('decision_delay', 'hops_chip', 'hops_chip_multi', 'hops_ipos', 'hops_ipos_multi', 'lookahead_stored', 'lookahead_used', 'lookahead_mismatch',
                'lookahead_multi', 'lookahead_fb_checks', 'lookahead_fb_blocked', 'lookahead_fb_requests', 'lookahead_fb_taken', 'packets_measured')

TUNING_RULE = [
    '## The rule (written before any tuning run)', '',
    '* **Runs.** pipe_all 2, decision_delay 0 (ideal decision), DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3 inherits the 4x4',
    '  values); the five scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet, the v9 masks); the ladder indices',
    '  1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat of the pipe_all 2 ladders, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds.',
    '* **Stage 1, heuristic** (`CI_heurLA_X` and `CI_heurLA_O`): W (heur_w) in {1, 2} x B (heur_busy) in {0, 4} x G (hop_weight_ipos) in {1, 2} x D (lut_bias) in',
    '  {0, 2, 4}: 24 configurations per relation.',
    '* **Stage 2, Q-learning** (`CI_qlLA_X` and `CI_qlLA_O`): W, B, G, D of the stage-1 choice of the relation and size; A (ql_alpha) in {0.01, 0.05, 0.1}.',
    '  `FULL_qlLA_X` takes the parameters of `CI_qlLA_X`; `CI_heur_X` those of `CI_heurLA_X`.',
    '* **Score** of a configuration on a size = mean over the five scenarios and the two seeds of',
    '  `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four',
    '  loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.',
    '* **Choice, stage 1:** the largest score; among the configurations within 0.02 of it, prefer D = 0, then G = 1, then B = 0, then W = 1 (the simplest',
    '  hardware; applied in this order as successive filters, a filter that would leave nothing is skipped), then the larger score.',
    '* **Choice, stage 2:** the A with the largest score.',
    '* Also reported, not used for the choice: the score of the v10 values (2x2: W 1, B 4, G 2, D 0, A 0.05; 4x4: W 2, B 0, G 2, D 0, A 0.1) on both relations.',
    '  For the heuristic they are grid points; for Q-learning they are run in addition where the stage-1 choice differs from them.',
    '* Runs: (48 + 6) configurations x 2 sizes x 5 scenarios x 4 loads x 2 seeds = 4,320, plus 80 for DeFT-P, plus at most 160 for the v10 Q-learning values.', '']


# ---- naming ----
def cfg_name(sel, rel, P):
    n = '%s%s_W%g_B%g_G%g_D%g' % ('h' if sel == 'heur' else 'q', rel, P['W'], P['B'], P['G'], P['D'])
    return n + ('_A%g' % P['A'] if sel == 'ql' else '')


def heur_grid():
    return [dict(W=float(w), B=float(b), G=float(g), D=float(d)) for w in GRID_W for b in GRID_B for g in GRID_G for d in GRID_D]


def tune_cells(size):
    P = X.lp()
    for p, m in X.scenarios(size):
        lad = P[X.lkey(size, p, m)]['eval']
        E5.gen_tables(size, p, [lad[i] for i in TUNE_LOADS])
        for i in TUNE_LOADS:
            for seed in TUNE_SEEDS:
                yield p, m, lad[i], seed


def tune1_jobs():
    js = []
    for size in TUNE_SIZES:
        for p, m, rate, seed in tune_cells(size):
            js.append(X.job('tune', size, 'DeFT_P', X23.methods(size)['DeFT_P'], 2, p, m, rate, seed))
            for rel in 'XO':
                for P in heur_grid():
                    js.append(X.job('tune', size, cfg_name('heur', rel, P), X.variant('CI_heurLA_' + rel, P), 2, p, m, rate, seed))
    return js


def ql_configs(size, rel, choice):
    """Stage-2 configurations: the alpha grid at the stage-1 choice, plus the v10 values (reported only)."""
    h = choice[size][rel]['heur']
    out = [dict(W=h['W'], B=h['B'], G=h['G'], D=h['D'], A=a) for a in GRID_A]
    v10 = X.params_v10(size)['ql']
    if not any(all(abs(c[k] - v10[k]) < 1e-12 for k in 'WBGDA') for c in out):
        out.append(dict(v10))
    return out


def tune2_jobs():
    choice = json.load(open(CHOICE))
    js = []
    for size in TUNE_SIZES:
        for p, m, rate, seed in tune_cells(size):
            for rel in 'XO':
                for P in ql_configs(size, rel, choice):
                    js.append(X.job('tune', size, cfg_name('ql', rel, P), X.variant('CI_qlLA_' + rel, P), 2, p, m, rate, seed))
    return js


# ---- scores ----
def load_tune():
    """{(cfg, size, pattern, mask, rate, seed): (accepted, latency)} of the raw tuning folder."""
    R = {}
    for f in glob.glob(os.path.join(X.raw('tune'), '*.json')):
        (v, sp, m, rate, seed), d = MK.parse(f)
        size, p = sp.split('-')
        R[(v[:-3], size, p, m, rate, seed)] = (d['summary']['average_ip_throughput_flits_per_cycle_per_ip'], d['summary']['global_average_delay_cycles'])
    return R


def score(R, cfg, size):
    """(score, mean ln THR ratio, mean ln LAT1.0 ratio, mean ln LAT0.5 ratio) of a configuration against DeFT-P; None if a run is missing."""
    P = X.lp()
    t, l1, l5 = [], [], []
    for p, m in X.scenarios(size):
        lad = P[X.lkey(size, p, m)]['eval']
        for seed in TUNE_SEEDS:
            try:
                a = [R[(cfg, size, p, m, lad[i], seed)] for i in TUNE_LOADS]
                b = [R[('DeFT_P', size, p, m, lad[i], seed)] for i in TUNE_LOADS]
            except KeyError:
                return None
            t.append(math.log(max(x[0] for x in a) / max(x[0] for x in b)))
            l1.append(math.log(a[1][1] / b[1][1]))      # TUNE_LOADS[1] = index 3 = 1.0 x Lsat
            l5.append(math.log(a[0][1] / b[0][1]))      # TUNE_LOADS[0] = index 1 = 0.5 x Lsat
    n = len(t)
    return sum(t) / n - sum(l1) / n - sum(l5) / n, sum(t) / n, sum(l1) / n, sum(l5) / n


def pick_heur(rows):
    """rows: [(score, P)]. The largest score; within 0.02 of it prefer D = 0, then G = 1, then B = 0, then W = 1, then the larger score."""
    best = max(s for s, _ in rows)
    cand = [(s, P) for s, P in rows if s >= best - 0.02]
    for k, v in (('D', 0), ('G', 1), ('B', 0), ('W', 1)):
        f = [(s, P) for s, P in cand if P[k] == v]
        if f:
            cand = f
    return max(cand, key=lambda x: x[0])


def choose1():
    R = load_tune()
    choice = {}
    for size in TUNE_SIZES:
        choice[size] = {}
        for rel in 'XO':
            rows = [(score(R, cfg_name('heur', rel, P), size)[0], P) for P in heur_grid()]
            s, P = pick_heur(rows)
            choice[size][rel] = {'heur': dict(P, score=s)}
            print(size, rel, 'stage 1:', P, 'score %.4f' % s, '(best %.4f)' % max(x for x, _ in rows))
    choice['3x3'] = json.loads(json.dumps(choice['4x4']))
    json.dump(choice, open(CHOICE, 'w'), indent=1)


def choose2():
    R = load_tune()
    choice = json.load(open(CHOICE))
    L = ['# v24 C2: tuning of the selection parameters (experiments_v24.py tunerule, tune1, choose1, tune2, choose2)', ''] + TUNING_RULE
    L += ['## Results', '', 'Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P',
          '(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better).', '']
    for size in TUNE_SIZES:
        v10 = X.params_v10(size)
        for rel in 'XO':
            h = choice[size][rel]['heur']
            L += ['### %s, relation %s: stage 1 (heuristic)' % (size, rel), '', '| W | B | G | D | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|---|---|---|']
            rows = []
            for P in heur_grid():
                sc = score(R, cfg_name('heur', rel, P), size)
                rows.append((sc, P))
            best = max(sc[0] for sc, _ in rows)
            for sc, P in sorted(rows, key=lambda x: -x[0][0]):
                note = []
                if all(P[k] == h[k] for k in 'WBGD'):
                    note.append('**chosen**')
                if sc[0] == best:
                    note.append('largest score')
                elif sc[0] >= best - 0.02:
                    note.append('within 0.02')
                if all(P[k] == v10['heur'][k] for k in 'WBGD'):
                    note.append('v10 values')
                L.append('| %g | %g | %g | %g | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (P['W'], P['B'], P['G'], P['D'], sc[0], 100 * (math.exp(sc[1]) - 1),
                                                                                         100 * (math.exp(sc[2]) - 1), 100 * (math.exp(sc[3]) - 1), ', '.join(note)))
            L += ['', '### %s, relation %s: stage 2 (Q-learning at W %g, B %g, G %g, D %g)' % (size, rel, h['W'], h['B'], h['G'], h['D']), '',
                  '| W | B | G | D | A | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|---|---|---|---|']
            qrows = [(score(R, cfg_name('ql', rel, P), size), P) for P in ql_configs(size, rel, choice)]
            grid = [(sc, P) for sc, P in qrows if all(P[k] == h[k] for k in 'WBGD') and P['A'] in GRID_A]
            bsc, bP = max(grid, key=lambda x: x[0][0])
            choice[size][rel]['ql'] = dict(bP, score=bsc[0])
            for sc, P in qrows:
                note = []
                if P is bP:
                    note.append('**chosen**')
                if all(abs(P[k] - v10['ql'][k]) < 1e-12 for k in 'WBGDA'):
                    note.append('v10 values' + ('' if (sc, P) in grid else ' (reported only)'))
                L.append('| %g | %g | %g | %g | %g | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (P['W'], P['B'], P['G'], P['D'], P['A'], sc[0], 100 * (math.exp(sc[1]) - 1),
                                                                                              100 * (math.exp(sc[2]) - 1), 100 * (math.exp(sc[3]) - 1), ', '.join(note)))
            L.append('')
    choice['3x3'] = json.loads(json.dumps(choice['4x4']))
    json.dump(choice, open(CHOICE, 'w'), indent=1)
    L += ['## Chosen values', '', '| size | relation | heuristic: W, B, G, D (score) | Q-learning: W, B, G, D, A (score) |', '|---|---|---|---|']
    for size in SIZES:
        for rel in 'XO':
            h, q = choice[size][rel]['heur'], choice[size][rel]['ql']
            L.append('| %s%s | %s | %g, %g, %g, %g (%.4f) | %g, %g, %g, %g, %g (%.4f) |' % (size, ' (the 4x4 values)' if size == '3x3' else '', rel, h['W'], h['B'], h['G'], h['D'], h['score'],
                                                                                    q['W'], q['B'], q['G'], q['D'], q['A'], q['score']))
    L += ['', '`FULL_qlLA_X` runs with the Q-learning values of relation X; `CI_heur_X` with the heuristic values of relation X and `heur_lookahead 0`.',
          'Per-run values: `tune_runs.csv`.']
    open(os.path.join(RES, 'tuning.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


def tuned(size, rel, sel):
    c = json.load(open(CHOICE))[size][rel][sel]
    return {k: c[k] for k in c if k != 'score'}


def tuned_variant(size, name):
    """Arguments of a Part C / Part D variant with the tuned parameters (FULL_qlLA_X and CI_heur_X take those of their CI lookahead parent)."""
    scope, sel, rel = name.split('_')
    if sel == 'rand':
        return X.variant(name)
    return X.variant(name, tuned(size, rel, X.sel_kind(name)))


# ---- per-run CSV ----
def to_csv(stage, fn, expect=None):
    rows = []
    for f in sorted(glob.glob(os.path.join(X.raw(stage), '*.json'))):
        if f.endswith('.vc.json'):
            continue
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        down, up = l['vl_down_packets'], l['vl_up_packets']
        has = any(down)
        row = dict(variant=v, pattern=p, mask=m, rate=repr(rate), offered=repr(8 * rate), seed=seed,
                   accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']), latency=repr(s['global_average_delay_cycles']),
                   p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                   dead_ends=l['dead_end_events'], vl_imbalance=repr(MK.imbalance(m, down, up)) if has else '', vl_source='run' if has else 'none',
                   vl_max_down=max(down) if has else '', vl_max_up=max(up) if has else '')
        for k in EXTRA_FIELDS:
            row[k] = l.get(k, '')
        rows.append(row)
    out = os.path.join(RES, fn)
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS + ['vl_max_down', 'vl_max_up'] + list(EXTRA_FIELDS), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('%s: %d rows%s; dead ends %d' % (out, len(rows), '' if expect is None else ' (expected %d)' % expect, sum(int(r['dead_ends']) for r in rows)))
    return len(rows)


# ---- A4: centre cut ----
CUT_RATE, CUT_SIZE = 0.0040, '4x4'


def cut_methods():
    z = CUT_SIZE
    dis = X23.methods(z)['DeFT_Dis']
    h = X.params_v10(z)['heur']
    return [('DeFT_Dis', 'DeFT_Dis (fixed nearest VLs, XY on the interposer)', dis),
            ('DeFT_Dis_OE_heur', 'DeFT_Dis with `ipos_tm OE` and `-sel DEFT_HEUR` (fixed VLs, odd-even paths chosen by the v10 heuristic)',
             dis + X.IPOE + X.heurLA(h['W'], h['B'], h['G'], h['D'])),
            ('DeFT_Dis_O1', 'DeFT_Dis with `ipos_tm O1` (fixed VLs, XY in VN0 and YX in VN1)', dis + X.IPO1),
            ('CI_qlLA_X', 'CI_qlLA_X (late entry, XY on the interposer, v10 parameters)', X.variant_v10(z, 'CI_qlLA_X'))]


def cut(nproc):
    z, m, out = CUT_SIZE, E5.FREE[CUT_SIZE], X.raw('cut')
    os.makedirs(out, exist_ok=True)
    E5.gen_tables(z, 'chipperm', [CUT_RATE])
    js = []
    for key, _, a in cut_methods():
        for seed in TUNE_SEEDS:
            n, args = X.job('cut', z, key, a, 0, 'chipperm', m, CUT_RATE, seed)
            js.append((n, args + X.lb('vc_stats', os.path.join(out, n + '.vc.json'))))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    fw, nchip = 16, 256
    cuts = [('vertical cut, eastward (x 7 -> 8)', lambda x, y, d: x == 7 and d == 1, lambda x, y: y),
            ('vertical cut, westward (x 8 -> 7)', lambda x, y, d: x == 8 and d == 3, lambda x, y: y),
            ('horizontal cut, southward (y 7 -> 8)', lambda x, y, d: y == 7 and d == 2, lambda x, y: x),
            ('horizontal cut, northward (y 8 -> 7)', lambda x, y, d: y == 8 and d == 0, lambda x, y: x)]
    L = ['# A4: flits on the interposer channels that cross the centre (experiments_v24.py cut)', '',
         '4x4 chipperm at 0.8 x Lsat of DeFT-P (rate %.4f, offered %.4f flits/node/cycle), pipe_all 0, DeFT-P VN options, `-traffic_rng 1`, seeds 101-102, `-deft_lb vc_stats`.' % (CUT_RATE, 8 * CUT_RATE),
         'The footprint is 16 x 16. A cut is crossed by 16 interposer channels in each direction: the vertical cut between columns 7 and 8 (one channel per row), the',
         'horizontal cut between rows 7 and 8 (one channel per column). Values: flits per cycle over the measured window, both VCs, mean of the two seeds. A channel',
         'carries at most 0.5 flits per cycle (one flit per two cycles).', '']
    rows_csv = []
    summary = ['| method | accepted (offered %.4f) | latency | saturated | largest flit rate of any interposer channel (router x, y, direction) | of any Down VL | of any Up VL |' % (8 * CUT_RATE), '|---|---|---|---|---|---|---|']
    blocks = []
    for key, label, _ in cut_methods():
        vals = {c[0]: [0.0] * 16 for c in cuts}
        vn = {c[0]: [0.0, 0.0] for c in cuts}
        wait = {c[0]: 0.0 for c in cuts}
        acc, lat, big, dn, up, mc = [], [], (0.0, None), 0.0, 0.0, 8000.0
        for seed in TUNE_SEEDS:
            n = [x for x, _ in js if x.split('__')[1] == key + '-p0' and x.endswith('__s%d' % seed)][0]
            d = json.load(open(os.path.join(out, n + '.vc.json')))
            s = X.stat(res[n])
            acc.append(s[0])
            lat.append(s[1])
            mc = float(d['measured_cycles'])
            for l in d['links']:
                f = (l['f'][0] + l['f'][1]) / mc / len(TUNE_SEEDS)
                if l['cls'] == 'vl_down':
                    dn = max(dn, (l['f'][0] + l['f'][1]) / mc)
                if l['cls'] == 'vl_up':
                    up = max(up, (l['f'][0] + l['f'][1]) / mc)
                if l['cls'] != 'ipos':
                    continue
                x, y = (l['r'] - nchip) % fw, (l['r'] - nchip) // fw
                if (l['f'][0] + l['f'][1]) / mc > big[0]:
                    big = ((l['f'][0] + l['f'][1]) / mc, (x, y, 'NESW'[l['d']]))
                for name, sel, idx in cuts:
                    if sel(x, y, l['d']):
                        vals[name][idx(x, y)] += f
                        vn[name][0] += l['f'][0] / mc / len(TUNE_SEEDS)
                        vn[name][1] += l['f'][1] / mc / len(TUNE_SEEDS)
                        wait[name] += (sum(l['held']) + sum(l['nocredit'])) / len(TUNE_SEEDS)
        a, la = sum(acc) / len(acc), sum(lat) / len(lat)
        summary.append('| %s | %.4f | %.1f | %s | %.3f (%d, %d, %s) | %.3f | %.3f |' % (key, a, la, 'yes' if a < 0.95 * 8 * CUT_RATE else 'no', big[0], big[1][0], big[1][1], big[1][2], dn, up))
        B = ['## %s' % label, '', '| cut and direction | the 16 channels (row 0-15 for the vertical cut, column 0-15 for the horizontal cut) | sum | max | max / mean | VN0 : VN1 | wait cycles per flit |', '|---|---|---|---|---|---|---|']
        for name, _, _ in cuts:
            v = vals[name]
            tot = sum(v)
            flits = tot * mc
            B.append('| %s | %s | %.2f | %.3f | %.2f | %.0f : %.0f | %.2f |' % (name, ' '.join('%.2f' % x for x in v), tot, max(v), max(v) / (tot / 16) if tot else 0.0,
                                                                         100 * vn[name][0] / tot if tot else 0, 100 * vn[name][1] / tot if tot else 0, wait[name] / flits if flits else 0.0))
            rows_csv.append([key, name] + ['%.4f' % x for x in v] + ['%.4f' % tot, '%.4f' % max(v), '%.3f' % (max(v) / (tot / 16) if tot else 0.0)])
        blocks += B + ['']
    L += summary + [''] + blocks
    with open(os.path.join(RES, 'centre_cut.csv'), 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator=NL)
        w.writerow(['method', 'cut'] + ['ch%d' % i for i in range(16)] + ['sum', 'max', 'max_over_mean'])
        w.writerows(rows_csv)
    open(os.path.join(RES, 'centre_cut_tables.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


# ---- Part D ----
def rows_of_design():
    """[(row name, base variant, mechanism or None)] of the evaluation, in report order."""
    out = [(r, r, None) for r in REFS]
    for c in CANDS:
        for k in MECHS:
            out.append((c if k == 'ideal' else '%s_%s' % (c, k), c, k))
    out += [(r, r, None) for r in SECONDARY]
    out += [(r, 'CI_qlLA_X', r.rsplit('_', 1)[1]) for r in CONTROLS]
    return out


def row_args(size, row, base, kind):
    if row in ('DeFT_P', 'DeFT_B'):
        return X23.methods(size)[row] + X.lb('count_vl', 1)
    if row in ('MTR', 'RC'):
        return list(X23.methods(size)[row])
    if row in ('CI_qlLA_G', 'FULL_qlLA_G'):
        return X23.methods(size)[row] + X.HOPS
    if row == 'DeFT_P_O1':
        return X.variant(row) + X.HOPS
    a = tuned_variant(size, base) + X.HOPS
    if kind in ('LF', 'DLY'):
        return a + X.mech(kind, X.sel_kind(base))
    if kind == 'Lnofb':        # control: lookahead without the fallback at residual 1
        return a + X.LOOK + X.BUSY + X.dd(1)
    if kind == 'LF0':          # control: lookahead with the fallback at residual 0
        return a + X.LOOK + X.FALLBACK + X.BUSY + X.dd(0)
    return a


def row_scenarios(size, row):
    sc = X.scenarios(size)
    if row in ('MTR', 'RC'):
        return [(p, m) for p, m in sc if int(m, 16) == 0]
    if row in CONTROLS:
        return [sc[0]]
    return sc


def dropped(row, p):
    d = json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []
    if 'dly_heur' in d and row in ('CI_heurLA_X_DLY', 'CI_heurLA_O_DLY'):
        return True
    return 'rand_heur' in d and row in ('CI_rand_X', 'CI_heur_X') and p in ('hotspot', 'chipperm', 'chiptrans')


def eval_jobs(seeds=SEEDS, loads=range(9), with_dropped=False):
    P = X.lp()
    js = []
    for size in SIZES:
        for row, base, kind in rows_of_design():
            a = row_args(size, row, base, kind)
            for p, m in row_scenarios(size, row):
                if dropped(row, p) and not with_dropped:
                    continue
                lad = P[X.lkey(size, p, m)]['eval']
                for i in loads:
                    js += [X.job('eval', size, row, a, 2, p, m, lad[i], seed) for seed in seeds]
    return js


def ensure_tables():
    P = X.lp()
    for size in SIZES:
        for p, m in X.scenarios(size):
            E5.gen_tables(size, p, P[X.lkey(size, p, m)]['eval'])


def timing(nproc):
    """The seed-111 runs at the 2nd, 5th and 9th load of every cell: part of the design (kept), timed for the estimate."""
    ensure_tables()
    js = eval_jobs(seeds=(111,), loads=(1, 4, 8), with_dropped=True)
    full = eval_jobs(with_dropped=True)
    t = time.time()
    res = run_jobs(js, X.raw('eval'), nproc=nproc, timeout=14400)
    el = time.time() - t
    est = el / len(js) * len(full) / 3600
    drops = []
    n = len(full)
    dly = [j for j in full if '__CI_heurLA_X_DLY-p2__' in j[0] or '__CI_heurLA_O_DLY-p2__' in j[0]]
    rh = [j for j in full if ('__CI_rand_X-p2__' in j[0] or '__CI_heur_X-p2__' in j[0]) and any('-%s__' % p in j[0] for p in ('hotspot', 'chipperm', 'chiptrans'))]
    e2 = est
    if e2 > 30:
        drops.append('dly_heur')
        n -= len(dly)
        e2 = el / len(js) * n / 3600
    if e2 > 30:
        drops.append('rand_heur')
        n -= len(rh)
        e2 = el / len(js) * n / 3600
    json.dump(dict(dropped=drops, timing_runs=len(js), timing_seconds=el, estimate_hours_full=est, estimate_hours_after_drops=e2, runs_full=len(full), runs_after_drops=n),
              open(DROPS, 'w'), indent=1)
    L = ['# Run-time estimate v24 D1 (experiments_v24.py timing)', '',
         'Timing runs: the %d runs of seed 111 at the 2nd, 5th and 9th load (0.5, 1.2 and 2.4 x Lsat) of every (row, size, scenario) cell. They are runs of the design and are kept;' % len(js),
         'nothing of their results was looked at. %d processes: %.0f s wall; %d missing.' % (nproc, el, sum(1 for x in res.values() if x is None)), '',
         'Full design: %d runs (14,580 + 270 controls), estimated **%.1f h**.' % (len(full), est), '',
         'Rule (pre-registered): above 30 h drop, in this order, DLY for the heuristic variants (%d runs), then `CI_rand_X` and `CI_heur_X` on hotspot, chipperm and chiptrans (%d runs).' % (len(dly), len(rh)),
         '', '**Dropped: %s.** Runs to do: %d, estimated %.1f h.' % (', '.join(drops) if drops else 'nothing', n, e2)]
    open(os.path.join(RES, 'runtime_estimate.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    # timing runs of dropped cells are removed, so that the raw folder holds the design as run
    keep = {j[0] for j in eval_jobs()}
    for j in js:
        if j[0] not in keep:
            for ext in ('.json', '.log'):
                f = os.path.join(X.raw('eval'), j[0] + ext)
                if os.path.exists(f):
                    os.remove(f)


# ---- sanity ----
def sanity(nproc):
    P = X.lp()
    out = X.raw('sanity')
    js, meta = [], []
    for size in SIZES:
        m = E5.FREE[size]
        r = P[X.lkey(size, 'uniform', m)]['eval'][3]
        mm = X23.methods(size)
        for tag, a in (('DeFT_Dis', mm['DeFT_Dis'] + X.HOPS), ('DeFT_P_nocount', mm['DeFT_P']), ('CI_qlLA_G_nohops', mm['CI_qlLA_G'])):
            n, args = X.job('sanity', size, tag, a, 2, 'uniform', m, r, 111)
            js.append((n, args))
            meta.append((size, tag, r, n))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    E = {}
    for r in csv.DictReader(open(os.path.join(RES, 'eval_runs.csv'))):
        E[(r['variant'], r['pattern'], r['mask'], float(r['rate']), int(r['seed']))] = r
    L = ['# Sanity checks v24 (experiments_v24.py sanity)', '', '## Hops per packet (uniform fault-free, seed 111, 1.0 x Lsat, pipe_all 2)', '',
         'Head-flit forwards counted by `-deft_lb hop_stats 1` in the measured window (router-to-router and vertical hops; the ejection is not counted), divided by the packets',
         'delivered in the window. DeFT_Dis takes the nearest VL at both ends; the CI variants take the LUT exit and bind the entry late, on minimal paths.', '',
         '| size | rate | DeFT_Dis | CI_qlLA_X | CI_qlLA_O | CI_qlLA_X: hops offering more than one output (chiplet / interposer) | CI_qlLA_O |', '|---|---|---|---|---|---|---|']

    def hp(l, n):
        return (int(l['hops_chip']) + int(l['hops_ipos'])) / float(n)

    def multi(e):
        return '%.1f %% / %.1f %%' % (100.0 * int(e['hops_chip_multi']) / int(e['hops_chip']), 100.0 * int(e['hops_ipos_multi']) / int(e['hops_ipos']))
    for size in SIZES:
        m = E5.FREE[size]
        r = P[X.lkey(size, 'uniform', m)]['eval'][3]
        d = res[[n for z, t, _, n in meta if z == size and t == 'DeFT_Dis'][0]]
        ex = E[('CI_qlLA_X-p2', size + '-uniform', m, r, 111)]
        eo = E[('CI_qlLA_O-p2', size + '-uniform', m, r, 111)]
        L.append('| %s | %.4f | %.2f | %.2f | %.2f | %s | %s |' % (size, r, hp(d['deft_lb'], d['deft_lb']['packets_measured']), hp(ex, ex['packets_measured']), hp(eo, eo['packets_measured']), multi(ex), multi(eo)))
    L += ['', '## Observation-only options', '',
          'The reference rows DeFT_P and DeFT_B run with `-deft_lb count_vl 1` (VL counts for plain DEFT routing) and every DEFT_LB row with `-deft_lb hop_stats 1`. Same run',
          'with and without the option (uniform fault-free, seed 111, 1.0 x Lsat): the `summary` block and the delay statistics must be identical.', '',
          '| size | DeFT_P with / without count_vl | CI_qlLA_G with / without hop_stats |', '|---|---|---|']
    for size in SIZES:
        m = E5.FREE[size]
        r = P[X.lkey(size, 'uniform', m)]['eval'][3]
        cells = []
        for tag, row in (('DeFT_P_nocount', 'DeFT_P-p2'), ('CI_qlLA_G_nohops', 'CI_qlLA_G-p2')):
            d = res[[n for z, t, _, n in meta if z == size and t == tag][0]]
            e = E[(row, size + '-uniform', m, r, 111)]
            same = (repr(d['summary']['average_ip_throughput_flits_per_cycle_per_ip']) == e['accepted'] and repr(d['summary']['global_average_delay_cycles']) == e['latency'] and
                    repr(d['deft_lb']['delay_p99']) == e['p99'] and str(d['summary']['total_received_packets']) == e['received'])
            cells.append('identical' if same else '**different**')
        L.append('| %s | %s | %s |' % (size, cells[0], cells[1]))
    # the largest VL flit rate of the round: packets x 8 flits over the 10,000 simulated cycles
    L += ['', '## Largest flit rate of a vertical link', '',
          'Per run, the largest number of packets any Down VL and any Up VL carried (head flits forwarded over the whole 10,000 simulated cycles), times 8 flits, per cycle. A link',
          'carries one flit per two cycles, so the value must not exceed 0.5.', '', '| file | runs with VL counts | largest Down VL rate (run) | largest Up VL rate (run) | above 0.5 |', '|---|---|---|---|---|']
    worst = 0.0
    for fn in ('tune_runs.csv', 'eval_runs.csv'):
        f = os.path.join(RES, fn)
        if not os.path.exists(f):
            continue
        rows = [r for r in csv.DictReader(open(f)) if r['vl_max_down'] != '']
        bd = max(rows, key=lambda r: int(r['vl_max_down']))
        bu = max(rows, key=lambda r: int(r['vl_max_up']))
        rd, ru = int(bd['vl_max_down']) * 8 / 10000.0, int(bu['vl_max_up']) * 8 / 10000.0
        worst = max(worst, rd, ru)
        L.append('| %s | %d | %.4f (%s, %s, rate %s, seed %s) | %.4f (%s, %s, rate %s, seed %s) | %d |' % (
            fn, len(rows), rd, bd['variant'], bd['pattern'], bd['rate'], bd['seed'], ru, bu['variant'], bu['pattern'], bu['rate'], bu['seed'],
            sum(1 for r in rows if int(r['vl_max_down']) * 8 / 10000.0 > 0.5 or int(r['vl_max_up']) * 8 / 10000.0 > 0.5)))
    L += ['', '**Largest VL flit rate of the round: %.4f flits/cycle (%s 0.5).**' % (worst, 'at most' if worst <= 0.5 else 'ABOVE')]
    os.makedirs(os.path.join(RES, 'report'), exist_ok=True)
    open(os.path.join(RES, 'report', 'sanity.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


def run_stage(stage, nproc, extra):
    if stage == 'tunerule':
        L = ['# v24 C2: tuning of the selection parameters (experiments_v24.py tunerule, tune1, choose1, tune2, choose2)', ''] + TUNING_RULE + ['## Results', '', 'Not run yet.']
        open(os.path.join(RES, 'tuning.md'), 'w', newline=NL).write(NL.join(L) + NL)
    elif stage in ('tune1', 'tune2'):
        js = tune1_jobs() if stage == 'tune1' else tune2_jobs()
        print(stage, 'jobs:', len(js), flush=True)
        res = run_jobs(js, X.raw('tune'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'choose1':
        choose1()
    elif stage == 'choose2':
        choose2()
        n = to_csv('tune', 'tune_runs.csv')
        if n == len({j[0] for j in tune1_jobs() + tune2_jobs()}):
            shutil.rmtree(X.raw('tune'))
    elif stage == 'cut':
        cut(nproc)
    elif stage == 'timing':
        timing(nproc)
    elif stage == 'eval':
        ensure_tables()
        js = eval_jobs()
        print('eval jobs:', len(js), flush=True)
        res = run_jobs(js, X.raw('eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'check':
        sys.exit(0 if E19.check_raw(X.raw('eval'), eval_jobs(), 'eval') else 1)
    elif stage == 'csv':
        n = to_csv('eval', 'eval_runs.csv', expect=len(eval_jobs()))
        if n == len(eval_jobs()):
            shutil.rmtree(X.raw('eval'))
    elif stage == 'sanity':
        sanity(nproc)
    else:
        raise SystemExit(__doc__)
