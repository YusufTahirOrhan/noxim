"""v29: the rows of the round and what the gates and the evaluation share (results_v29_review/PROMPT.md, "Rows").

Existing rows are built by the code of the round that defined them and are not changed:
  DeFT_P, DeFT_B, MTR, RC, XY_SP, CI_heurLA_X_LF (main)   experiments_v25.row_args (round 25)
  MTR_static, RC_static                                    experiments_v23.methods (round 23: MTR and RC without -vc_per_hop)
New rows, each an existing row with one change:
  LB_b0        the main row with lut_bias 0 (it differs from the main row on 2x2 only, where the frozen value is 2)
  LB_noLA      the main row with heur_lookahead 0 (CI_heur_X of round 24 in mechanism LF)
  LB_d6        the main row with -buffer 6
  X_d5, X_d6   reference X (DeFT_P, DeFT_B, MTR, RC) with -buffer 5 or -buffer 6; RC keeps rc_slots 4
  X_i7         reference X with -buffer_ipos 7 (7-flit input buffers in the interposer routers, 4-flit buffers in the chiplet routers)
  EB_first     the main row with -deft_lb entry_commit first and its own tuned lut_bias (tuning_choice_v29.json)
  EB_best16, EB_best256   EB_best of round 28 (S, P, B of results_v28_anchor/tuning_choice_v28.json) with oracle_period 16 or 256 and T
               tuned again (tuning_choice_v29.json)
Row names carry the pipe depth as a suffix in the run names (-p2, -p0).
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v25 as X25  # noqa: E402
import experiments_v27_eval as EV27  # noqa: E402
import experiments_v28_eval as EV28  # noqa: E402
import experiments_v29 as X  # noqa: E402
import make_eval_csv as MK  # noqa: E402

RES, SIZES, NL, MAIN = X.RES, X.SIZES, X.NL, X.MAIN
lb = X.lb
ES = EV27.ES                                   # -deft_lb entry_stats 1: observation only (results_v27_early/unit_checks.md)
INF = 1e9
REFS4 = ['DeFT_P', 'DeFT_B', 'MTR', 'RC']
REFS5 = REFS4 + ['XY_SP']
VN_ROWS = ('DeFT_P', 'DeFT_B', MAIN)           # the rows with VN rules that tolerate VL faults
DEPTH = {'d5': ['-buffer', '5'], 'd6': ['-buffer', '6'], 'i7': ['-buffer_ipos', '7']}
NEW_PATTERNS = ('tornado', 'neighbour', 'randperm')
CHOICE = os.path.join(RES, 'tuning_choice_v29.json')
LP_FILE = os.path.join(RES, 'load_points_v29.json')
ENERGY = EV27.ENERGY
V29_FIELDS = ('entry_commit_first_bound', 'entry_commit_first_below', 'entry_commit_first_max_per_head')
EXTRA_FIELDS = EV28.EXTRA_FIELDS + V29_FIELDS  # the counters of rounds 24, 27, 28 and 29
V25_COLS = MK.COLS + ['vl_max_down', 'vl_max_up'] + list(EV24.EXTRA_FIELDS)     # the columns of results_v25_confirm/eval_runs.csv


def fmt(x):
    return '%g' % x


def set_arg(args, key, value):
    """The arguments with the value after the one occurrence of key replaced."""
    a = list(args)
    assert a.count(key) == 1, (key, a)
    a[a.index(key) + 1] = str(value)
    return a


def first_args(size, D, tie=False, check=0):
    """EB_first: the main row with entry_commit first and lut_bias D (D >= INF: 1e9). tie: the diagnostic tie_stream 1 (anchor gate
    only). check: commit_check N (unit check only)."""
    a = set_arg(X25.row_args(size, MAIN), 'lut_bias', fmt(INF if D >= INF else D)) + lb('entry_commit', 'first')
    if tie:
        a += lb('tie_stream', 1)
    if check:
        a += lb('commit_check', check)
    return a + ES


def choice():
    return json.load(open(CHOICE))


def lp():
    """The ladders of the three new scenarios (B0)."""
    return json.load(open(LP_FILE))


def depth_row(row):
    """(base row, depth tag) of X_d5 / X_d6 / X_i7 / LB_d6, else None."""
    if row == 'LB_d6':
        return MAIN, 'd6'
    if row[-3:] in ('_d5', '_d6', '_i7') and row[:-3] in REFS4:
        return row[:-3], row[-2:]
    return None


def row_args(size, row):
    """Noxim arguments of a row of this round, without the pipe depth and -traffic_rng (job() adds both)."""
    if row in REFS5 or row == MAIN:
        return X25.row_args(size, row)
    if row == 'LB_b0':
        return set_arg(X25.row_args(size, MAIN), 'lut_bias', '0')
    if row == 'LB_noLA':
        return set_arg(X25.row_args(size, MAIN), 'heur_lookahead', '0')
    d = depth_row(row)
    if d:
        return X25.row_args(size, d[0]) + DEPTH[d[1]]
    if row in ('MTR_static', 'RC_static'):
        return list(X23.methods(size)[row])
    if row == 'EB_first':
        return first_args(size, choice()[size]['EB_first']['D'])
    if row in ('EB_best16', 'EB_best256'):
        b = EV28.choice()[size]['EB_best']
        return EV28.ebf_args(b['S'], b['P'], b['B'], choice()[size][row]['T'], period=int(row[7:]))
    raise ValueError(row)


def ff_scenarios(size):
    """The six fault-free scenarios of round 25."""
    return [(p, m) for p, m in X25.scenarios(size) if not X25.faulty(m)]


def new_scenarios(size):
    """The three scenarios that no earlier round ran (Part B)."""
    return [(p, E5.FREE[size]) for p in NEW_PATTERNS]


def job(stage, size, name, args, p, m, rate, seed, extra=(), pipe=2):
    return X.job(stage, size, name, args, pipe, p, m, rate, seed, extra)


def strip(d, drop):
    return {k: v for k, v in d.items() if k not in drop}


def stats4(d):
    s = d['summary']
    return (s['average_ip_throughput_flits_per_cycle_per_ip'], s['global_average_delay_cycles'], d['deft_lb']['delay_p99'], s['total_received_packets'])


def multi_hops(d):
    l = d['deft_lb']
    return int(l.get('hops_chip_multi', 0)) + int(l.get('hops_ipos_multi', 0))


def wmd(name, L):
    path = os.path.join(RES, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


def to_csv(raw_dir, out, expect=None, cols=None):
    """Per-run CSV: the columns of results_v25_confirm/eval_runs.csv, then (unless cols is given) the counters of rounds 27, 28 and 29."""
    fields = list(cols) if cols else MK.COLS + ['vl_max_down', 'vl_max_up'] + list(EXTRA_FIELDS)
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
        rows.append({k: row[k] for k in fields})
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print('%s: %d rows%s; dead ends %d' % (out, len(rows), '' if expect is None else ' (expected %d)' % expect, sum(int(r['dead_ends']) for r in rows)))
    return len(rows)
