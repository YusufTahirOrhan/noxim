"""v27 gates, tuning, evaluation and fault runs (results_v27_early/PREREGISTRATION.md), run through experiments_v27.py:
  a2_anchor   the anchor row EB_lut (DEFT_LB, exit lut, entry lut, XY in both layers, DeFT-P's options) against DeFT_P: the six fault-free
              scenarios at 1.0 x Lsat, seed 101 -> anchor.md, anchor.json
  a2_units    unit checks of the new options -> unit_checks.md: entry_stats is observation only (the main row with and without it);
              entry_commit down changes nothing when every chiplet has one functional VL; the committed output against the main row's
              selection (commit_check); EB_vl with oracle_beta 0 against DeFT-P's entry VL
  a2_drain    all-pairs drain tests of the five new rows on six masks per size (extra = tuned: the three tuned rows with their chosen
              oracle_beta) -> drain_v27.csv / drain_v27_tuned.csv
  b_rule      the tuning rule -> tuning_v27.md (written before any tuning run)
  b_tune      the grid of oracle_beta for EB_vl, EB_route and EB_vl64 on 2x2 and 4x4, with DeFT-P and the main row on the same loads and
              seeds; extends the grid by factors of 2 (at most three steps) while the largest score lies at an end
  b_choose    scores and choice -> tuning_v27.md, tuning_choice_v27.json, tune_runs.csv (raw outputs deleted)
  c_timing    timing runs of Parts C and E (runs of the two designs, kept) -> runtime_estimate.md, drops.json
  c_eval, c_check, c_csv      Part C: the design, seeds 161-170 -> eval_runs.csv
  e_reuse     DeFT_P and the main row on masks 1 and 2 of rate 4/16 of every size, against results_v26_faults/fault_rate_runs.csv -> reuse_check.md
  e_eval, e_check, e_csv      Part E: EB_vl, EB_route and EB_down on the 48 masks of rate 4/16 of round 26 -> fault_runs.csv
Row names carry the pipe depth as a suffix (-p2). A tuning candidate is named ROW_b<beta>.
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
from runner import common_args, run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v26 as X26  # noqa: E402
import experiments_v26_eval as EV26  # noqa: E402
import experiments_v27 as X  # noqa: E402
import make_eval_csv as MK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES, SIZES, NL, MAIN = X.RES, X.SIZES, X.NL, X.MAIN
lb = X.lb
ENERGY = ('total_energy_j', 'dynamic_energy_j', 'static_energy_j')

# ---- rows ----
ES = lb('entry_stats', 1)                      # observation only (unit_checks.md)
ROWS_C = ['DeFT_P', MAIN, 'EB_vl', 'EB_route', 'EB_vl64', 'EB_down', 'LB_noVLrep']
NEW = ['EB_vl', 'EB_route', 'EB_vl64', 'EB_down', 'LB_noVLrep']
EB = ['EB_vl', 'EB_route', 'EB_vl64', 'EB_down']       # one entry candidate on every interposer hop
TUNED = ['EB_vl', 'EB_route', 'EB_vl64']
TUNED_EXTRA = {'EB_vl': [], 'EB_route': lb('oracle_scope', 'route'), 'EB_vl64': lb('oracle_period', 64)}
ROWS_E = ['EB_vl', 'EB_route', 'EB_down']
GRID = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
MAX_EXT = 3
CHOICE = os.path.join(RES, 'tuning_choice_v27.json')
ANCHOR = os.path.join(RES, 'anchor.json')
DROPS = os.path.join(RES, 'drops.json')
SEEDS_C = range(161, 171)
SEEDS_E = (151, 152)
LIMIT_H = 30.0
STAT_FIELDS = ('entry_up_moves', 'entry_up_not_default', 'entry_up_age_mean', 'entry_inj', 'entry_inj_wait_mean', 'entry_commit_down_moves', 'entry_commit_bound')
EXTRA_FIELDS = EV24.EXTRA_FIELDS + STAT_FIELDS


def fmt(x):
    return '%g' % x


def beta_of(size, row):
    return json.load(open(CHOICE))[size][row]['beta']


def row_args(size, row, beta=None):
    """Noxim arguments of a row of this round, without the pipe depth and -traffic_rng (job() adds both). DeFT_P and the main row are
    built by experiments_v25.row_args; the main row and every new row carry -deft_lb entry_stats 1, which only counts."""
    if row == 'DeFT_P':
        return X25.row_args(size, row)
    if row == MAIN:
        return X25.row_args(size, row) + ES
    if row == 'EB_lut':                        # the anchor: DEFT_LB with both VLs from the LUT, XY in both layers, DeFT-P's options
        return ['-routing', 'DEFT_LB'] + lb('exit', 'lut', 'entry', 'lut') + X24.REL_X + X24.HOPS + X23.DST + X23.VN_P + ES
    if row in TUNED:
        b = beta_of(size, row) if beta is None else beta
        return ['-routing', 'DEFT_LB'] + lb('exit', 'lut', 'entry', 'oracle', 'oracle_beta', fmt(b)) + X24.REL_X + X24.HOPS + TUNED_EXTRA[row] + X23.VN_P + ES
    if row == 'EB_down':
        return X25.row_args(size, MAIN) + lb('entry_commit', 'down') + ES
    if row == 'LB_noVLrep':
        return X25.row_args(size, MAIN) + lb('up_report', 0) + ES
    raise ValueError(row)


def ff_scenarios(size):
    """The six fault-free scenarios of round 25."""
    return [(p, m) for p, m in X25.scenarios(size) if not X25.faulty(m)]


def lp():
    return X25.lp()


def job(stage, size, name, args, p, m, rate, seed, extra=()):
    return X.job(stage, size, name, args, 2, p, m, rate, seed, extra)


def strip(d, drop):
    return {k: v for k, v in d.items() if k not in drop}


def stats4(d):
    s = d['summary']
    return (s['average_ip_throughput_flits_per_cycle_per_ip'], s['global_average_delay_cycles'], d['deft_lb']['delay_p99'], s['total_received_packets'])


def wmd(name, L):
    open(os.path.join(RES, name), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


# =====================================================================================================================
# A2: gates
# =====================================================================================================================
def anchor(nproc):
    P = lp()
    js, meta = [], []
    for z in SIZES:
        for p, m in ff_scenarios(z):
            r = P[X.lkey(z, p, m)]['eval'][3]
            E5.gen_tables(z, p, [r])
            a = job('anchor', z, 'DeFT_P', row_args(z, 'DeFT_P'), p, m, r, 101)
            b = job('anchor', z, 'EB_lut', row_args(z, 'EB_lut'), p, m, r, 101)
            js += [a, b]
            meta.append((z, p, r, a[0], b[0]))
    res = run_jobs(js, X.raw('anchor'), nproc=nproc, timeout=7200)
    L = ['# A2: the anchor row against DeFT_P (experiments_v27.py a2_anchor)', '',
         '`EB_lut` = `-routing DEFT_LB -deft_lb exit lut -deft_lb entry lut -deft_lb chip_tm XY -deft_lb ipos_tm XY` with DeFT-P\'s options (`-deft_up_keep 1',
         '-deft_rr_fallback 1 -deft_vn_rr 1 -deft_lut_entry dst`) against `DeFT_P` (`-routing DEFT` with the same options): the six fault-free scenarios at 1.0 x Lsat,',
         'seed 101, pipe_all 2, `-traffic_rng 1`. Compared: every field of the `summary` block of the stats file except the three energy fields (injected and received',
         'packets and flits, mean and largest delay, throughput), and the delay statistics of the `deft_lb` block (mean, median, p95, p99, inter- and intra-chiplet).', '',
         '| size | scenario | rate | accepted DeFT_P / EB_lut | latency DeFT_P / EB_lut | p99 DeFT_P / EB_lut | received DeFT_P / EB_lut | identical |', '|---|---|---|---|---|---|---|---|']
    same = energy = 0
    keys = ('packets_measured', 'delay_mean', 'delay_p50', 'delay_p95', 'delay_p99', 'delay_inter_mean', 'delay_inter_p99', 'delay_intra_mean', 'packets_inter', 'packets_intra',
            'vl_down_packets', 'vl_up_packets', 'dead_end_events')
    hops = {}
    for z, p, r, na, nb in meta:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and strip(a['summary'], ENERGY) == strip(b['summary'], ENERGY) and all(a['deft_lb'][k] == b['deft_lb'][k] for k in keys)
        same += eq
        energy += bool(a) and bool(b) and a['summary'] == b['summary']
        sa, sb = stats4(a), stats4(b)
        hops[(z, p)] = (b['deft_lb']['hops_chip'] + b['deft_lb']['hops_ipos']) / float(b['deft_lb']['packets_measured'])
        L.append('| %s | %s | %.4f | %.6f / %.6f | %.4f / %.4f | %s / %s | %d / %d | %s |' % (z, p, r, sa[0], sb[0], sa[1], sb[1], sa[2], sb[2], sa[3], sb[3], 'yes' if eq else '**no**'))
    ident = same == len(meta)
    L += ['', '**%d / %d identical.** The energy fields of the summary are equal as well in %d of %d runs (the power model charges the routing function by its name).' % (
        same, len(meta), energy, len(meta)), '',
          'Also identical in every one of these runs: the packets per Down VL and per Up VL (`vl_down_packets`, `vl_up_packets`), which DeFT_P counts with `count_vl`.' if ident else
          'The rows are not identical: `EB_lut` is added to Part C (see `DECISIONS.md`).', '',
          'Hops per packet of DeFT-P\'s paths (head-flit forwards of `EB_lut` in the measured window per delivered packet; the ejection is not counted):', '',
          '| size | ' + ' | '.join(p for p, _ in ff_scenarios('2x2')) + ' |', '|---|' + '---|' * 6]
    for z in SIZES:
        L.append('| %s | %s |' % (z, ' | '.join('%.2f' % hops[(z, p)] for p, _ in ff_scenarios(z))))
    json.dump(dict(identical=ident, runs=len(meta), same=same, hops={'%s__%s' % k: v for k, v in hops.items()}), open(ANCHOR, 'w'), indent=1)
    wmd('anchor.md', L)
    if ident:
        shutil.rmtree(X.raw('anchor'))
    return True          # not identical is a result (EB_lut joins Part C), not a failed gate


def k3_mask(size):
    """The first mask of round 25 with one functional VL in every chiplet, and its uniform load at 1.0 x Lsat."""
    P = json.load(open(os.path.join(X25.RES, 'load_points_faults.json')))
    e = sorted((v for v in P.values() if v['size'] == size and v['k'] == 3), key=lambda v: v['mask'])[0]
    return e['mask'], e['eval'][1]


def units(nproc):
    P = lp()
    out = X.raw('units')
    js, obs, one, chk, b0 = [], [], [], [], []
    for z in SIZES:
        for p, m in ff_scenarios(z):
            r = P[X.lkey(z, p, m)]['eval'][3]
            E5.gen_tables(z, p, [r])
            a = job('units', z, 'main_nostats', X25.row_args(z, MAIN), p, m, r, 101)
            b = job('units', z, 'main_stats', row_args(z, MAIN), p, m, r, 101)
            c = job('units', z, 'EB_down_check', row_args(z, 'EB_down') + lb('commit_check', 1000), p, m, r, 101)
            d = job('units', z, 'EB_vl_b0', row_args(z, 'EB_vl', 0.0), p, m, r, 101)
            js += [a, b, c, d]
            obs.append((z, p, a[0], b[0]))
            chk.append((z, p, c[0]))
            b0.append((z, p, d[0]))
        m3, r3 = k3_mask(z)
        E5.gen_tables(z, 'uniform', [r3])
        a = job('units', z, 'main_stats', row_args(z, MAIN), 'uniform', m3, r3, 101)
        b = job('units', z, 'EB_down', row_args(z, 'EB_down'), 'uniform', m3, r3, 101)
        js += [a, b]
        one.append((z, m3, r3, a[0], b[0]))
    res = run_jobs(js, out, nproc=nproc, timeout=7200)
    ok = True
    L = ['# A1 / A2: unit checks of the new options (experiments_v27.py a2_units)', '', 'Seed 101, pipe_all 2, `-traffic_rng 1`, 1.0 x Lsat of DeFT_P.', '',
         '## 1. `-deft_lb entry_stats 1` is observation only', '',
         'The main row as round 25 defines it (`experiments_v25.row_args`) and the same row with `entry_stats 1`, on the six fault-free scenarios. Compared: the whole',
         '`summary` block and every field of the `deft_lb` block that the row without the option has.', '',
         '| size | scenario | accepted without / with | latency without / with | identical |', '|---|---|---|---|---|']
    n = 0
    for z, p, na, nb in obs:
        a, b = res[na], res[nb]
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and all(b['deft_lb'].get(k) == v for k, v in a['deft_lb'].items())
        n += eq
        L.append('| %s | %s | %.6f / %.6f | %.4f / %.4f | %s |' % (z, p, stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1], 'yes' if eq else '**no**'))
    ok = ok and n == len(obs)
    L += ['', '**%d / %d identical.**' % (n, len(obs)), '',
          '## 2. `entry_commit down` changes nothing when the entry mask has one candidate', '',
          '`EB_down` against the main row on a mask of round 25 that leaves every chiplet one functional VL (uniform traffic at 1.0 x Lsat of that mask). Compared: the',
          'whole `summary` block and every field of `deft_lb` except the two counters of the option.', '',
          '| size | mask | rate | accepted main / EB_down | latency main / EB_down | Down moves counted | of them bound | identical |', '|---|---|---|---|---|---|---|---|']
    n = 0
    for z, m3, r3, na, nb in one:
        a, b = res[na], res[nb]
        drop = ('entry_commit', 'entry_commit_down_moves', 'entry_commit_bound')
        eq = bool(a) and bool(b) and a['summary'] == b['summary'] and a['deft_lb'] == strip(b['deft_lb'], drop) and b['deft_lb']['entry_commit_bound'] == 0
        n += eq
        L.append('| %s | %s | %.4f | %.6f / %.6f | %.4f / %.4f | %d | %d | %s |' % (z, m3, r3, stats4(a)[0], stats4(b)[0], stats4(a)[1], stats4(b)[1],
                                                                              b['deft_lb']['entry_commit_down_moves'], b['deft_lb']['entry_commit_bound'], 'yes' if eq else '**no**'))
    ok = ok and n == len(one)
    L += ['', '**%d / %d identical.**' % (n, len(one)), '',
          '## 3. The output of the committed candidate against the main row\'s selection', '',
          '`EB_down` with `-deft_lb commit_check 1000`: for the first 1,000 heads of the measured window that move Down with more than one entry candidate, the costs the',
          'main row\'s selection gives the outputs of the interposer router below (full entry mask, the same state, the same moment) are computed next to the costs of the',
          'candidates. *unique*: the output of the committed candidate is the one cheapest output of the main row\'s selection. *tie*: the main row\'s selection has more than',
          'one cheapest output and the committed one is among them (the two break ties differently: the selection among outputs, the commit among candidates). *different*:',
          'the output of the committed candidate is not a cheapest output of the main row\'s selection. On 3x3 and 4x4 (D = 0) *different* must be 0; on 2x2 (D = 2) the',
          'penalty is charged differently (to an output that drops the default VL, or to a candidate that is not the default VL), so the two can differ.', '',
          '| size | D | scenario | heads checked | unique | tie | different | largest difference of the least cost |', '|---|---|---|---|---|---|---|---|']
    tot = {}
    for z, p, nc in chk:
        l = res[nc]['deft_lb']
        D = X25.row_args(z, MAIN)
        D = D[D.index('lut_bias') + 1]
        t = tot.setdefault(z, [0, 0, 0, 0])
        for i, k in enumerate(('commit_checked', 'commit_check_unique', 'commit_check_tie', 'commit_check_different')):
            t[i] += l[k]
        L.append('| %s | %s | %s | %d | %d | %d | %d | %g |' % (z, D, p, l['commit_checked'], l['commit_check_unique'], l['commit_check_tie'], l['commit_check_different'], l['commit_check_max_gap']))
    L += ['', '| size | heads checked | unique | tie | different |', '|---|---|---|---|---|']
    for z in SIZES:
        L.append('| %s | %d | %d | %d | %d |' % tuple([z] + tot[z]))
    bad = sum(tot[z][3] for z in ('3x3', '4x4'))
    ok = ok and bad == 0
    L += ['', '**Different on 3x3 and 4x4 (D = 0): %d.**' % bad, '',
          '## 4. `EB_vl` with `oracle_beta 0`: the entry VL of least total hops (description, not a gate)', '',
          'With `oracle_beta 0` the injection-time choice is the entry VL with the fewest hops from the source through the LUT\'s exit VL to the destination, ties at random.',
          'Share of the packets that move Up on DeFT-P\'s entry VL (`entry_stats`, measured window), fault-free:', '',
          '| size | ' + ' | '.join(p for p, _ in ff_scenarios('2x2')) + ' |', '|---|' + '---|' * 6]
    by = {}
    for z, p, nd in b0:
        l = res[nd]['deft_lb']
        by[(z, p)] = 100.0 * (1.0 - l['entry_up_not_default'] / float(l['entry_up_moves']))
    for z in SIZES:
        L.append('| %s | %s |' % (z, ' | '.join('%.1f %%' % by[(z, p)] for p, _ in ff_scenarios(z))))
    L += ['', 'No hop of these `EB_vl` runs offers more than one output: %s.' % ('yes' if all(res[nd]['deft_lb']['hops_chip_multi'] == 0 and res[nd]['deft_lb']['hops_ipos_multi'] == 0 for _, _, nd in b0) else '**NO**'),
          'No hop of the `EB_down` runs of check 3 offers more than one output: %s.' % ('yes' if all(res[nc]['deft_lb']['hops_chip_multi'] == 0 and res[nc]['deft_lb']['hops_ipos_multi'] == 0 for _, _, nc in chk) else '**NO**'),
          '', '**All unit checks pass: %s.**' % ('yes' if ok else 'NO')]
    wmd('unit_checks.md', L)
    if ok:
        shutil.rmtree(out)
    return ok


def drain_masks(size):
    """Fault-free, the same VL faulty in every chiplet, and mask 1 of each rate of round 26."""
    return [E5.FREE[size], E5.NORTH[size]] + [e['mask'] for e in X26.part_b() if e['size'] == size and e['index'] == 1]


def drain_jobs(tuned):
    js = []
    for z in SIZES:
        for row in (TUNED if tuned else NEW):
            a0 = row_args(z, row, None if tuned or row not in TUNED else 1.0)
            for m in drain_masks(z):
                a = common_args(1, m, hardcoded=E5.REL + '%s/allpairs_burst.txt' % E5.tdir(z), lut=X23.lut23(z, m)) + E5.size_args(z) + \
                    a0 + X23.pipe(2) + X24.TRNG + (E10.DRAIN_ALLPAIRS_2X2 if z == '2x2' else E10.DRAIN_ALLPAIRS)
                js.append(('allpairs__%s-p2__%s-%s__s1' % (row, z, m), a))
    return js


def drain(nproc, tuned):
    js = drain_jobs(tuned)
    stage = 'drain_tuned' if tuned else 'drain'
    print('drain jobs: %d' % len(js), flush=True)
    t = time.time()
    res = EV26.run_seg(js, X.raw(stage), X.width(nproc), 14400, seg=96)
    fails = E19.drain_report(res, os.path.join(RES, 'drain_v27_tuned.csv' if tuned else 'drain_v27.csv'))
    multi = [n for n, d in res.items() if d and n.split('__')[1][:-3] in EB and (d['deft_lb'].get('hops_chip_multi', 0) or d['deft_lb'].get('hops_ipos_multi', 0))]
    print('drain tests: %d, failures %d, EB runs with a hop that offers more than one output: %d, wall %.0f s' % (len(js), fails, len(multi), time.time() - t), flush=True)
    if not fails and not multi:
        shutil.rmtree(X.raw(stage))
    return not fails and not multi


# =====================================================================================================================
# Part B: tuning of oracle_beta
# =====================================================================================================================
TUNE_SEEDS, TUNE_SIZES, TUNE_LOADS = EV24.TUNE_SEEDS, EV24.TUNE_SIZES, EV24.TUNE_LOADS
TUNING_RULE = [
    '## The rule (written before any tuning run)', '',
    '* **Runs.** The rule of round 24 (`results_v24_xy/tuning.md`), unchanged: pipe_all 2, DeFT-P VN options, `-traffic_rng 1`, LUTs `luts/v23`; sizes 2x2 and 4x4 (3x3',
    '  takes the 4x4 value); the five tuning scenarios (uniform, hotspot, chipperm, chiptrans fault-free and uniform with one faulty VL per chiplet); the ladder',
    '  indices 1, 3, 5, 7 (0.5, 1.0, 1.4, 2.0 x Lsat, `load_points_v24.json`); seeds 101 and 102; DeFT-P on the same loads and seeds.',
    '* **Grid.** `oracle_beta` in {0.125, 0.25, 0.5, 1, 2, 4, 8}, separately for `EB_vl`, `EB_route` and `EB_vl64`.',
    '* **Score** of a value on a size = mean over the five scenarios and the two seeds of `ln(THR / THR_P) - ln(LAT1.0 / LAT1.0_P) - ln(LAT0.5 / LAT0.5_P)`, where',
    '  `_P` is DeFT-P on the same seed, THR the largest accepted throughput over the four loads, and LAT1.0 and LAT0.5 the mean latency at 1.0 and 0.5 x Lsat.',
    '* **Choice:** per row and size, the value with the largest score. If it lies at an end of the grid, the grid is extended at that end by factors of 2, one value',
    '  at a time, at most three times, until the largest score is no longer at the end.',
    '* **Also run and reported, not tuned:** the main row `CI_heurLA_X_LF` with its frozen parameters on the same loads and seeds (it was tuned by the same rule in',
    '  round 24, with an ideal decision; here it runs as the row is defined, with the lookahead mechanism).',
    '* `EB_down` and `LB_noVLrep` take the frozen parameters of the main row. Nothing is tuned for them.',
    '* Runs: 3 rows x 7 values x 2 sizes x 5 scenarios x 4 loads x 2 seeds = 1,680, plus 80 for DeFT-P and 80 for the main row, plus 40 per extension step of a row on a size.', '']


def tname(row, b):
    return '%s_b%s' % (row, fmt(b))


def grid_of(size, row, R):
    """The values of a row that have been run completely on a size, in increasing order (the grid and its extensions)."""
    vs = set(GRID)
    for k in R:
        if k[1] == size and k[0].startswith(row + '_b'):
            vs.add(float(k[0][len(row) + 2:]))
    return sorted(v for v in vs if score(R, tname(row, v), size) is not None)


def tune_jobs(extra=None):
    """extra: {(size, row): [values]} of the extension steps."""
    js = []
    for z in TUNE_SIZES:
        for p, m, rate, seed in EV24.tune_cells(z):
            if extra is None:
                js.append(job('tune', z, 'DeFT_P', row_args(z, 'DeFT_P'), p, m, rate, seed))
                js.append(job('tune', z, MAIN, row_args(z, MAIN), p, m, rate, seed))
            for row in TUNED:
                for b in (GRID if extra is None else extra.get((z, row), [])):
                    js.append(job('tune', z, tname(row, b), row_args(z, row, b), p, m, rate, seed))
    return js


def load_tune():
    R = {}
    for f in glob.glob(os.path.join(X.raw('tune'), '*.json')):
        (v, sp, m, rate, seed), d = MK.parse(f)
        z, p = sp.split('-')
        R[(v[:-3], z, p, m, rate, seed)] = (d['summary']['average_ip_throughput_flits_per_cycle_per_ip'], d['summary']['global_average_delay_cycles'])
    return R


def score(R, cfg, size):
    """(score, mean ln THR ratio, mean ln LAT1.0 ratio, mean ln LAT0.5 ratio) against DeFT-P, as experiments_v24_eval.score; None if a run is missing."""
    P = X24.lp()
    t, l1, l5 = [], [], []
    for p, m in X24.scenarios(size):
        lad = P[X.lkey(size, p, m)]['eval']
        for seed in TUNE_SEEDS:
            try:
                a = [R[(cfg, size, p, m, lad[i], seed)] for i in TUNE_LOADS]
                b = [R[('DeFT_P', size, p, m, lad[i], seed)] for i in TUNE_LOADS]
            except KeyError:
                return None
            t.append(math.log(max(x[0] for x in a) / max(x[0] for x in b)))
            l1.append(math.log(a[1][1] / b[1][1]))
            l5.append(math.log(a[0][1] / b[0][1]))
    n = len(t)
    return sum(t) / n - sum(l1) / n - sum(l5) / n, sum(t) / n, sum(l1) / n, sum(l5) / n


def next_extension(R):
    """{(size, row): [value]}: one more value where the largest score lies at an end of what has been run, and fewer than MAX_EXT steps were taken at that end."""
    out = {}
    for z in TUNE_SIZES:
        for row in TUNED:
            vs = grid_of(z, row, R)
            sc = {v: score(R, tname(row, v), z)[0] for v in vs}
            best = max(vs, key=lambda v: sc[v])
            if best == vs[-1] and sum(1 for v in vs if v > GRID[-1]) < MAX_EXT:
                out[(z, row)] = [vs[-1] * 2]
            elif best == vs[0] and sum(1 for v in vs if v < GRID[0]) < MAX_EXT:
                out[(z, row)] = [vs[0] / 2]
    return out


def tune(nproc):
    js = tune_jobs()
    print('tuning jobs: %d' % len(js), flush=True)
    t = time.time()
    res = EV26.run_seg(js, X.raw('tune'), X.width(nproc), 14400)
    print('grid done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    for step in range(1, MAX_EXT + 1):
        ext = next_extension(load_tune())
        if not ext:
            break
        js = tune_jobs(ext)
        print('extension step %d: %s; %d jobs' % (step, ', '.join('%s %s -> %s' % (z, row, fmt(v[0])) for (z, row), v in sorted(ext.items())), len(js)), flush=True)
        res = EV26.run_seg(js, X.raw('tune'), X.width(nproc), 14400)
        print('missing outputs: %d' % sum(1 for v in res.values() if v is None), flush=True)
    print('tuning runs done in %.0f s' % (time.time() - t), flush=True)


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def choose():
    R = load_tune()
    choice = {}
    L = ['# v27 Part B: tuning of `oracle_beta` (experiments_v27.py b_rule, b_tune, b_choose)', ''] + TUNING_RULE
    L += ['## Results', '', 'Scores are in natural-log units (0.01 is about 1 %); THR, LAT1.0 and LAT0.5 are the three terms as percentages against DeFT-P',
          '(100 x (exp(mean ln ratio) - 1); higher THR and lower LAT are better).', '']
    multi = 0
    for f in glob.glob(os.path.join(X.raw('tune'), '*.json')):
        if os.path.basename(f).split('__')[1].startswith('EB_'):
            l = json.load(open(f))['deft_lb']
            multi += l['hops_chip_multi'] + l['hops_ipos_multi']
    for z in TUNE_SIZES:
        choice[z] = {}
        ms = score(R, MAIN, z)
        choice[z][MAIN] = dict(score=ms[0])
        L += ['### %s' % z, '', '| row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | note |', '|---|---|---|---|---|---|---|',
              '| `%s` (frozen, not tuned here) | | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | |' % (MAIN, ms[0], pct(ms[1]), pct(ms[2]), pct(ms[3]))]
        for row in TUNED:
            vs = grid_of(z, row, R)
            sc = {v: score(R, tname(row, v), z) for v in vs}
            best = max(vs, key=lambda v: sc[v][0])
            ext = [v for v in vs if v not in GRID]
            choice[z][row] = dict(beta=best, score=sc[best][0], extended=ext, at_end=best in (vs[0], vs[-1]))
            for v in vs:
                note = []
                if v == best:
                    note.append('**chosen**')
                if v not in GRID:
                    note.append('extension')
                L.append('| `%s` | %s | %.4f | %+.1f %% | %+.1f %% | %+.1f %% | %s |' % (row, fmt(v), sc[v][0], pct(sc[v][1]), pct(sc[v][2]), pct(sc[v][3]), ', '.join(note)))
        L.append('')
    choice['3x3'] = json.loads(json.dumps(choice['4x4']))
    json.dump(choice, open(CHOICE, 'w'), indent=1)
    L += ['## Chosen values', '', '| size | `EB_vl` | `EB_route` | `EB_vl64` | score of the main row |', '|---|---|---|---|---|']
    for z in SIZES:
        c = choice[z]
        L.append('| %s%s | %s | %.4f |' % (z, ' (the 4x4 values)' if z == '3x3' else '', ' | '.join('%s (score %.4f)' % (fmt(c[r]['beta']), c[r]['score']) for r in TUNED), c[MAIN]['score']))
    ext = ['%s %s: %s' % (z, r, ', '.join(fmt(v) for v in choice[z][r]['extended'])) for z in TUNE_SIZES for r in TUNED if choice[z][r]['extended']]
    end = ['%s %s' % (z, r) for z in TUNE_SIZES for r in TUNED if choice[z][r]['at_end']]
    L += ['', 'Grid extensions: %s.' % ('; '.join(ext) if ext else 'none'),
          'Chosen value still at an end of what was run (after three extension steps): %s.' % (', '.join(end) if end else 'none'),
          'Hops of the `EB` tuning runs that offer more than one output (must be 0): %d.' % multi, 'Per-run values: `tune_runs.csv`.']
    wmd('tuning_v27.md', L)
    n = to_csv(X.raw('tune'), os.path.join(RES, 'tune_runs.csv'))
    if n == len(glob.glob(os.path.join(X.raw('tune'), '*.json'))) and multi == 0:
        shutil.rmtree(X.raw('tune'))
    return multi == 0


# ---- per-run CSV: the columns of results_v25_confirm/eval_runs.csv, then the counters of this round ----
def to_csv(raw_dir, out, expect=None):
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.json'))):
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
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=MK.COLS + ['vl_max_down', 'vl_max_up'] + list(EXTRA_FIELDS), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('%s: %d rows%s; dead ends %d' % (out, len(rows), '' if expect is None else ' (expected %d)' % expect, sum(int(r['dead_ends']) for r in rows)))
    return len(rows)


# =====================================================================================================================
# Part C: the evaluation; Part E: the early rows under random VL faults
# =====================================================================================================================
def drops():
    return json.load(open(DROPS))['dropped'] if os.path.exists(DROPS) else []


def rows_c():
    """The seven rows of the design; the anchor row joins them if it is not identical to DeFT_P (anchor.json)."""
    a = json.load(open(ANCHOR)) if os.path.exists(ANCHOR) else {'identical': True}
    return ROWS_C + ([] if a['identical'] else ['EB_lut'])


def kept_c(row, seed, d):
    """The pre-registered time rule: above 30 h for Parts C and E drop, in this order, Part E, EB_vl64, LB_noVLrep, seeds 166-170."""
    if row in d:
        return False
    return not ('seeds166_170' in d and seed >= 166)


def eval_jobs(seeds=SEEDS_C, loads=range(9), d=None):
    d = drops() if d is None else d
    P = lp()
    js = []
    for z in SIZES:
        for row in rows_c():
            a = row_args(z, row)
            for p, m in ff_scenarios(z):
                lad = P[X.lkey(z, p, m)]['eval']
                for i in loads:
                    js += [job('eval', z, row, a, p, m, lad[i], s) for s in seeds if kept_c(row, s, d)]
    return js


def e_masks():
    """The 48 masks of rate 4/16 of round 26."""
    return [e for e in X26.part_b() if e['rate'] == '4/16']


def fault_jobs(seeds=SEEDS_E, loads=range(4), entries=None, rows=ROWS_E, stage='fault', d=None, args=None):
    d = drops() if d is None else d
    if 'part_e' in d:
        return []
    P = EV26.lpf()
    js = []
    for e in (e_masks() if entries is None else entries):
        z, m = e['size'], e['mask']
        for p in EV26.PATTERNS:
            lad = P[EV26.key(z, p, m)]['eval']
            for row in rows:
                a = (args or row_args)(z, row)
                for i in loads:
                    js += [job(stage, z, row, a, p, m, lad[i], s) for s in seeds]
    return js


def ensure_tables():
    P = lp()
    for z in SIZES:
        for p, m in ff_scenarios(z):
            E5.gen_tables(z, p, P[X.lkey(z, p, m)]['eval'])
    P = EV26.lpf()
    for e in e_masks():
        for p in EV26.PATTERNS:
            E5.gen_tables(e['size'], p, P[EV26.key(e['size'], p, e['mask'])]['eval'])


def timing(nproc):
    """Part C: the seed-161 runs at the 2nd, 5th and 9th load of every cell. Part E: seed 151, the 1st and 4th load, masks 1-4 of every size.
    Both sets are runs of the designs (kept) and are timed one after the other, each with the machine to itself."""
    ensure_tables()
    nproc = X.width(nproc)
    jc = eval_jobs(seeds=(161,), loads=(1, 4, 8), d=[])
    je = fault_jobs(seeds=(151,), loads=(0, 3), entries=[e for e in e_masks() if e['index'] <= 4], d=[])
    full_c, full_e = eval_jobs(d=[]), fault_jobs(d=[])
    t = time.time()
    rc = run_jobs(jc, X.raw('eval'), nproc=nproc, timeout=14400)
    tc = time.time() - t
    t = time.time()
    re_ = run_jobs(je, X.raw('fault'), nproc=nproc, timeout=14400)
    te = time.time() - t
    per_c, per_e = tc / len(jc), te / len(je)
    est_c, est_e = per_c * len(full_c) / 3600, per_e * len(full_e) / 3600
    d, steps = [], []
    for name in ('part_e', 'EB_vl64', 'LB_noVLrep', 'seeds166_170'):
        tot = per_c * len(eval_jobs(d=d)) / 3600 + (0.0 if 'part_e' in d else est_e)
        if tot <= LIMIT_H:
            break
        d.append(name)
        steps.append(name)
    n_c, n_e = len(eval_jobs(d=d)), len(fault_jobs(d=d))
    est2 = per_c * n_c / 3600 + per_e * n_e / 3600
    json.dump(dict(dropped=d, nproc=nproc, timing_runs_c=len(jc), timing_seconds_c=tc, timing_runs_e=len(je), timing_seconds_e=te, estimate_hours_c=est_c, estimate_hours_e=est_e,
                   estimate_hours_after_drops=est2, runs_c=len(full_c), runs_e=len(full_e), runs_c_after_drops=n_c, runs_e_after_drops=n_e), open(DROPS, 'w'), indent=1)
    L = ['# Run-time estimate v27, Parts C and E (experiments_v27.py c_timing)', '',
         'Part C timing runs: the %d runs of seed 161 at the 2nd, 5th and 9th load (0.5, 1.2 and 2.4 x Lsat) of every (row, size, scenario) cell: %.0f s wall with %d processes;' % (len(jc), tc, nproc),
         '%d missing. Part E timing runs: the %d runs of seed 151 at the 1st and 4th load (0.5 and 2.0 x Lsat) of masks 1 to 4 of every size, the three rows and both traffic' % (
             sum(1 for x in rc.values() if x is None), len(je)),
         'patterns: %.0f s wall; %d missing. Both sets are runs of the designs and are kept; nothing of their results was looked at. Each set had the machine to itself.' % (
             te, sum(1 for x in re_.values() if x is None)), '',
         'Part C: %d runs, estimated **%.1f h**. Part E: %d runs, estimated **%.1f h**. Together **%.1f h**.' % (len(full_c), est_c, len(full_e), est_e, est_c + est_e), '',
         'Rule (pre-registered): above %.0f h in total drop, in this order: Part E; `EB_vl64`; `LB_noVLrep`; seeds 166-170.' % LIMIT_H, '',
         '**Dropped: %s.** Runs to do: %d (Part C) and %d (Part E), estimated %.1f h.' % (', '.join(d) if d else 'nothing', n_c, n_e, est2)]
    wmd('runtime_estimate.md', L)
    keep = {j[0] for j in eval_jobs()} | {j[0] for j in fault_jobs()}          # timing runs of dropped cells are removed
    for js_, stage in ((jc, 'eval'), (je, 'fault')):
        for j in js_:
            if j[0] not in keep:
                for ext in ('.json', '.log'):
                    f = os.path.join(X.raw(stage), j[0] + ext)
                    if os.path.exists(f):
                        os.remove(f)


def eb_multi(path):
    """Hops of the EB rows that offer more than one output, in a per-run CSV (the check that the binding is early; must be 0)."""
    n = 0
    for r in csv.DictReader(open(path)):
        if r['variant'].startswith('EB_'):
            n += int(r['hops_chip_multi'] or 0) + int(r['hops_ipos_multi'] or 0)
    return n


def finish(stage, jobs, fn):
    out = os.path.join(RES, fn)
    n = to_csv(X.raw(stage), out, expect=len(jobs))
    dead = sum(int(r['dead_ends']) for r in csv.DictReader(open(out)))
    multi = eb_multi(out)
    print('%s: %d rows of %d; dead-end events %d; hops of EB rows with more than one output %d' % (fn, n, len(jobs), dead, multi), flush=True)
    ok = n == len(jobs) and dead == 0 and multi == 0
    if ok:
        shutil.rmtree(X.raw(stage), ignore_errors=True)
    return ok


def reuse(nproc):
    """Part E: DeFT_P and the main row as round 26 defined them, on masks 1 and 2 of rate 4/16 of every size, with the new build, against
    the rows of results_v26_faults/fault_rate_runs.csv. Every column of that file is compared as text."""
    ensure_tables()
    ents = [e for e in e_masks() if e['index'] <= 2]
    js = fault_jobs(entries=ents, rows=['DeFT_P', MAIN], stage='reuse', d=[], args=X26.row_args)
    print('reuse jobs: %d' % len(js), flush=True)
    run_jobs(js, X.raw('reuse'), nproc=X.width(nproc), timeout=14400)
    tmp = os.path.join(X.RAW, 'reuse_check.csv')
    import experiments_v25_eval as EV25
    EV25.to_csv(X.raw('reuse'), tmp)
    old = {(r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']): r for r in csv.DictReader(open(os.path.join(X26.RES, 'fault_rate_runs.csv')))}
    new = list(csv.DictReader(open(tmp)))
    same, diff = 0, []
    for r in new:
        o = old.get((r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
        if o is not None and all(o[k] == r[k] for k in o):
            same += 1
        else:
            diff.append('%s %s %s %s s%s' % (r['variant'], r['pattern'], r['mask'], r['rate'], r['seed']))
    by = {}
    for r in new:
        k = (r['pattern'].split('-')[0], r['variant'])
        by[k] = by.get(k, 0) + 1
    L = ['# Part E: the reused rows are reproduced by the new build (experiments_v27.py e_reuse)', '',
         'DeFT_P and the main row `CI_heurLA_X_LF`, with the row definitions of round 26 (`experiments_v25.row_args`, no option of this round), on masks 1 and 2 of rate',
         '4/16 of every size: uniform and hotspot traffic, the four loads, seeds 151 and 152, run with the `bin/noxim` of this round. Compared with the rows of',
         '`results_v26_faults/fault_rate_runs.csv`: every column of that file, as text (accepted, latency, p99, injected, received, dead ends, the VL counts and the hop and',
         'lookahead counters).', '', '| size | row | runs |', '|---|---|---|'] + ['| %s | %s | %d |' % (k[0], k[1], v) for k, v in sorted(by.items())] + [
        '', '**%d / %d runs identical.**' % (same, len(js))] + (['', 'Different: ' + '; '.join(diff[:40])] if diff else [])
    wmd('reuse_check.md', L)
    ok = same == len(js) and len(new) == len(js)
    if ok:
        shutil.rmtree(X.raw('reuse'))
        os.remove(tmp)
    return ok


def run_stage(stage, nproc, extra):
    if stage == 'a2_anchor':
        sys.exit(0 if anchor(nproc) else 1)
    elif stage == 'a2_units':
        sys.exit(0 if units(nproc) else 1)
    elif stage == 'a2_drain':
        sys.exit(0 if drain(nproc, extra == 'tuned') else 1)
    elif stage == 'b_rule':
        wmd('tuning_v27.md', ['# v27 Part B: tuning of `oracle_beta` (experiments_v27.py b_rule, b_tune, b_choose)', ''] + TUNING_RULE + ['## Results', '', 'Not run yet.'])
    elif stage == 'b_tune':
        tune(nproc)
    elif stage == 'b_choose':
        sys.exit(0 if choose() else 1)
    elif stage == 'c_timing':
        timing(nproc)
    elif stage in ('c_eval', 'e_eval'):
        ensure_tables()
        js, raw_stage = (eval_jobs(), 'eval') if stage == 'c_eval' else (fault_jobs(), 'fault')
        print('%s jobs: %d' % (stage, len(js)), flush=True)
        t = time.time()
        res = EV26.run_seg(js, X.raw(raw_stage), X.width(nproc), 14400)
        print('done in %.0f s; missing outputs: %d' % (time.time() - t, sum(1 for v in res.values() if v is None)), flush=True)
    elif stage == 'c_check':
        sys.exit(0 if E19.check_raw(X.raw('eval'), eval_jobs(), 'eval') else 1)
    elif stage == 'e_check':
        sys.exit(0 if E19.check_raw(X.raw('fault'), fault_jobs(), 'eval') else 1)
    elif stage == 'c_csv':
        sys.exit(0 if finish('eval', eval_jobs(), 'eval_runs.csv') else 1)
    elif stage == 'e_csv':
        sys.exit(0 if finish('fault', fault_jobs(), 'fault_runs.csv') else 1)
    elif stage == 'e_reuse':
        sys.exit(0 if reuse(nproc) else 1)
    else:
        raise SystemExit(__doc__)
