"""Check that DEFT_QL with ql_alpha = 0 reproduces DEFT_HEUR exactly (frozen local weights).

Usage: python3 check_alpha0.py   (run from this directory)
"""
import json, os, sys
sys.path.insert(0, os.getcwd())
from runner import common_args, run_jobs
import variants as V
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']
ql0 = V.FULL + ['-sel', 'DEFT_QL'] + V.kv(ql_w=1.0, ql_busy=0.0, ql_alpha=0.0, ql_key=1, ql_eps=0.0)


def main():
    js = []
    for pat, mask, rate in (('uniform', '0x0000', 0.010), ('hotspot', '0x1111', 0.008), ('movinghot', '0x9C63', 0.006)):
        for seed in (1, 2):
            for v, va in (('heur', V.VARIANTS['FULL_heur']), ('ql0', ql0)):
                js.append((f'{v}__{pat}__{mask}__{seed}', common_args(seed, mask, traffic=REL + f'traffic/{pat}_{rate:.4f}.txt') + va + SIM))
    res = run_jobs(js, os.path.join(os.getcwd(), 'results', 'alpha0_raw'), nproc=11)
    keys = ['delay_mean', 'delay_p99', 'vl_down_packets', 'vl_up_packets', 'adaptive_decisions', 'packets_measured']
    ok = 0
    for n in sorted(k for k in res if k.startswith('heur')):
        a, b = res[n], res['ql0' + n[4:]]
        same = a['summary'] == b['summary'] and all(a['deft_lb'][k] == b['deft_lb'][k] for k in keys)
        ok += same
        print('IDENTICAL' if same else 'DIFFERENT', n[6:], round(a['summary']['global_average_delay_cycles'], 3), round(b['summary']['global_average_delay_cycles'], 3))
    print(f'{ok}/{len(js)//2} identical (summary block + deft_lb delays, VL counts, decisions)')


if __name__ == '__main__':
    main()
