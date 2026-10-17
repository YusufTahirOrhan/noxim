"""Checks for the ql_lookahead change in src/DeftLateBinding.cpp (results_v2/qlla_check.md).

(a) DEFT_QL with ql_lookahead 1 and ql_alpha 0 reproduces DEFT_HEUR with heur_lookahead 1
    exactly (same local weights): 2 patterns x 3 seeds on FULL (required) and on CI.
(b) The refactor (lookahead term moved into a shared function) does not change any
    existing variant: binaries before and after the change, identical summary and
    deft_lb blocks (apart from the new ql_lookahead field).
(c) With alpha > 0 the learner does learn (updates happen, results differ from (a)).
Usage: python3 check_qlla.py BIN_BEFORE BIN_AFTER
"""
import itertools
import json
import os
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN, ENV, common_args  # noqa: E402
import variants as V  # noqa: E402
from variants import CI, FULL, kv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results_v2', 'qllacheck_raw')
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
W, B = 2.0, 4.0
CELLS = [('uniform', '0x0000', 0.010), ('hotspot', '0x1111', 0.008)]
KEYS = ['delay_mean', 'delay_p99', 'vl_down_packets', 'vl_up_packets', 'adaptive_decisions',
        'packets_measured', 'dead_end_events']


def heurLA(base):
    return base + ['-sel', 'DEFT_HEUR'] + kv(heur_w=W, heur_busy=B, heur_lookahead=1)


def qlLA(base, alpha):
    return base + ['-sel', 'DEFT_QL'] + kv(ql_w=W, ql_busy=B, ql_alpha=alpha, ql_key=1, ql_eps=0.0, ql_lookahead=1)


def run(job):
    binary, name, args = job
    out = os.path.join(OUT, name + '.json')
    if not os.path.exists(out):
        subprocess.run([binary] + args + ['-stats_file', out], cwd=BIN, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
    try:
        return name, json.load(open(out))
    except Exception:
        return name, None


def args(pat, mask, rate, seed, va):
    return common_args(seed, mask, traffic=REL + f'traffic/{pat}_{rate:.4f}.txt') + va + SIM


def main():
    before, after = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    jobs = []
    for (pat, mask, rate), seed, (scope, base) in itertools.product(CELLS, (1, 2, 3), (('FULL', FULL), ('CI', CI))):
        tag = f'{scope}__{pat}__{mask}__s{seed}'
        jobs.append((after, 'a_heurLA__' + tag, args(pat, mask, rate, seed, heurLA(base))))
        jobs.append((after, 'a_qlLA0__' + tag, args(pat, mask, rate, seed, qlLA(base, 0.0))))
        jobs.append((after, 'c_qlLA02__' + tag, args(pat, mask, rate, seed, qlLA(base, 0.2))))
    refs = {'DeFT': V.VARIANTS['DeFT'], 'FULL_heur': V.VARIANTS['FULL_heur'], 'FULL_heurLA': V.VARIANTS['FULL_heurLA'],
            'FULL_ql': V.VARIANTS['FULL_ql'], 'CI_ql': V.VARIANTS['CI_ql'], 'A_oracle': V.VARIANTS['A_oracle']}
    for (pat, mask, rate), seed, (v, va) in itertools.product(CELLS, (1, 2), refs.items()):
        for tag, b in (('old', before), ('new', after)):
            jobs.append((b, f'b_{tag}__{v}__{pat}__{mask}__s{seed}', args(pat, mask, rate, seed, va)))
    with Pool(11) as pool:
        res = dict(pool.map(run, jobs, chunksize=1))

    lines = ['# ql_lookahead checks (check_qlla.py)', '',
             f'Local weights for (a)/(c): w = {W}, busy = {B}; ql_key = 1, eps = 0.', '',
             '## (a) QL-LA with alpha = 0 vs DEFT_HEUR with lookahead (summary block + deft_lb delays, '
             'VL counts, decisions)', '']
    ok_a = {'FULL': 0, 'CI': 0}
    for n in sorted(k for k in res if k.startswith('a_heurLA__')):
        a, b = res[n], res['a_qlLA0__' + n[len('a_heurLA__'):]]
        same = a['summary'] == b['summary'] and all(a['deft_lb'][k] == b['deft_lb'][k] for k in KEYS)
        scope = n.split('__')[1]
        ok_a[scope] += same
        lines.append(f'- {"IDENTICAL" if same else "DIFFERENT"} {n[len("a_heurLA__"):]}: latency '
                     f'{a["summary"]["global_average_delay_cycles"]:.3f} vs {b["summary"]["global_average_delay_cycles"]:.3f}; '
                     f'ql_updates {b["deft_lb"]["ql_updates"]}, ql_lookahead {b["deft_lb"]["ql_lookahead"]}')
    lines += ['', f'FULL: {ok_a["FULL"]}/6 identical (required check); CI: {ok_a["CI"]}/6 identical.', '',
              '## (b) existing variants, binary before vs after the change', '']
    ok_b = tot_b = 0
    for n in sorted(k for k in res if k.startswith('b_old__')):
        a, b = res[n], res['b_new__' + n[len('b_old__'):]]
        la, lb = dict(a['deft_lb']), dict(b['deft_lb'])
        lb.pop('ql_lookahead', None)
        same = a['summary'] == b['summary'] and la == lb
        ok_b += same
        tot_b += 1
        lines.append(f'- {"IDENTICAL" if same else "DIFFERENT"} {n[len("b_old__"):]}')
    lines += ['', f'{ok_b}/{tot_b} identical.', '', '## (c) QL-LA with alpha = 0.2 learns', '']
    for n in sorted(k for k in res if k.startswith('c_qlLA02__')):
        c, a = res[n], res['a_qlLA0__' + n[len('c_qlLA02__'):]]
        lines.append(f'- {n[len("c_qlLA02__"):]}: ql_updates {c["deft_lb"]["ql_updates"]}, latency '
                     f'{c["summary"]["global_average_delay_cycles"]:.3f} (alpha 0: {a["summary"]["global_average_delay_cycles"]:.3f})')
    open(os.path.join(HERE, 'results_v2', 'qlla_check.md'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
