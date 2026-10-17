"""Checks for the traffic-matched DeFT LUTs (results_v2/lut_tm_check.md).

1. Without --demand-table the generator reproduces luts/lut_rho001.yaml byte for byte.
2. With the uniform traffic table as demand, only the traffic_assumption line differs.
3. Selected-VL differences of each traffic-matched LUT vs the uniform LUT.
4. Sanity runs: DeFT vs DeFT_tm (seeds 101, 102, tuning seeds) on hotspot and chipperm.
Usage: python3 check_lut_tm.py
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import common_args, run_jobs  # noqa: E402
import variants_v2 as V2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, '..', '..', 'other', 'deft_vl_lut_generator.py')
LUT = os.path.join(HERE, 'luts', 'lut_rho001.yaml')
REL = '../experiments/late_binding/'
SIM = ['-sim', '10000', '-warmup', '2000']


def selected(path):
    return [l.strip() for l in open(path) if 'selected_vl_id' in l]


def main():
    masks = []
    for m in open(os.path.join(HERE, 'drain_masks.txt')):
        if m.strip():
            masks += ['--fault-mask', m.strip()]
    out = ['# Traffic-matched LUT checks (check_lut_tm.py)', '']
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, 'default.yaml')
        u = os.path.join(tmp, 'uniform.yaml')
        subprocess.run([sys.executable, GEN] + masks + ['--output', d], check=True)
        subprocess.run([sys.executable, GEN] + masks + ['--demand-table', os.path.join(HERE, 'traffic', 'uniform_0.0100.txt'),
                                                        '--output', u], check=True)
        same = open(d, 'rb').read() == open(LUT, 'rb').read()
        out.append(f'1. default generation identical to luts/lut_rho001.yaml: {same}')
        a, b = open(LUT).read().splitlines(), open(u).read().splitlines()
        diff = [(x, y) for x, y in zip(a, b) if x != y]
        out.append(f'2. uniform demand table: {len(diff)} differing line(s), same length: {len(a) == len(b)}: '
                   + '; '.join(f'`{x.strip()}` -> `{y.strip()}`' for x, y in diff))
    out.append('')
    out.append('3. Selected-VL lines (exit and entry, 11 masks) differing from the uniform LUT:')
    base = selected(LUT)
    for p in V2.TM_PATTERNS:
        s = selected(V2.lut_for('DeFT_tm', p))
        out.append(f'   - {p}: {sum(1 for x, y in zip(base, s) if x != y)} of {len(base)}')
    out.append('')
    js = []
    for p, m, rate in (('hotspot', '0x0000', 0.008), ('chipperm', '0x0000', 0.005), ('chipperm', '0x9C63', 0.004),
                       ('hotspot', '0x9C63', 0.006)):
        for seed in (101, 102):
            for v in ('DeFT', 'DeFT_tm'):
                js.append((f'{v}__{p}__{m}__{rate:.4f}__s{seed}',
                           common_args(seed, m, traffic=REL + f'traffic/{p}_{rate:.4f}.txt', lut=V2.lut_for(v, p))
                           + V2.VARIANTS[v] + SIM))
    res = run_jobs(js, os.path.join(HERE, 'results_v2', 'lutcheck_raw'), nproc=8)
    out.append('4. Sanity runs (tuning seeds), mean latency / accepted throughput:')
    out.append('')
    out.append('| run | DeFT latency | DeFT_tm latency | DeFT accepted | DeFT_tm accepted |')
    out.append('|---|---|---|---|---|')
    for n in sorted(k for k in res if k.startswith('DeFT__')):
        a, b = res[n]['summary'], res['DeFT_tm' + n[4:]]['summary']
        out.append(f'| {n[6:]} | {a["global_average_delay_cycles"]:.1f} | {b["global_average_delay_cycles"]:.1f} | '
                   f'{a["average_ip_throughput_flits_per_cycle_per_ip"]:.4f} | {b["average_ip_throughput_flits_per_cycle_per_ip"]:.4f} |')
    open(os.path.join(HERE, 'results_v2', 'lut_tm_check.md'), 'w', newline='\n').write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
