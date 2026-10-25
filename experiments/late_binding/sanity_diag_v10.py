"""v10 A5: investigation of the sanity check (DeFT(rho*) slower than MTR and RC on 2x2 uniform).

Diagnostic runs (2x2 uniform, fault-free, 0.8-1.4 x Lsat, seeds 1001-1003; not evaluation seeds):
* DeFT_LUT_noVN: DeFT's LUT pair and XY (the DeFT relation) with DeFT's VN rules off (vn_rules 0): what DeFT's routes
  cost without the VN separation. Diagnostic only: without the VNs this relation is not deadlock-free in general.
* MTR_VN: MTR's routes with DeFT's VN rules on: the VN cost on MTR's routes.
* DeFT_Dis_noVN: nearest exit / entry (RC's routes) without VN rules and without the RC buffer.
* the evaluated configurations DeFT(rho*), MTR, RC, DeFT_Dis for reference.
Also the VL usage imbalance (DEFT_LB runs; DeFT via its LUT proxy).
Usage: python3 sanity_diag_v10.py [nproc]
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.join(HERE, 'results_v10')
RAW = os.path.join(R10, 'sanitydiag_raw')
LOADS = (2, 3, 4, 5)
MULT = {2: 0.8, 3: 1.0, 4: 1.2, 5: 1.4}
SEEDS = (1001, 1002, 1003)


def configs():
    m = E10.methods('2x2')
    lut_pair = E10.lb('lut', 'lut') + E10.XY
    mtr_vn = [a for a in m['MTR']]
    k = mtr_vn.index('vn_rules')
    mtr_vn[k + 1] = '1'
    dis_novn = E10.lb('near', 'near') + E10.XY + ['-deft_lb', 'vn_rules', '0']
    return {'DeFT': m['DeFT'], 'MTR': m['MTR'], 'RC': m['RC'], 'DeFT_Dis': m['DeFT_Dis'],
            'DeFT_LUT_noVN': lut_pair + ['-deft_lb', 'vn_rules', '0'], 'MTR_VN': mtr_vn, 'DeFT_Dis_noVN': dis_novn,
            'DeFT_proxy': lut_pair + ['-deft_lb', 'count_vl', '1']}


def main():
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    cf = configs()
    js = []
    for v, va in cf.items():
        for i in LOADS:
            r = E10.LP5['2x2__uniform__0x0000']['eval'][i]
            js += [E5.job('sd', '2x2', v, va, 'uniform', '0x0000', r, s, E10.lut('2x2', 'DeFT', 'uniform')) for s in SEEDS]
    res = run_jobs(js, RAW, nproc=nproc, timeout=7200)
    out = {}
    for v in cf:
        for i in LOADS:
            r = E10.LP5['2x2__uniform__0x0000']['eval'][i]
            ds = [res[f'sd__{v}__2x2-uniform__0x0000__{r:.4f}__s{s}'] for s in SEEDS]
            lat = sum(d['summary']['global_average_delay_cycles'] for d in ds) / 3
            acc = sum(d['summary']['average_ip_throughput_flits_per_cycle_per_ip'] for d in ds) / 3
            imb = []
            for d in ds:
                c = [a + b for a, b in zip(d['deft_lb']['vl_down_packets'], d['deft_lb']['vl_up_packets'])]
                if sum(c):
                    imb.append(max(c) / (sum(c) / len(c)))
            dead = sum(d['deft_lb']['dead_end_events'] for d in ds)
            out[(v, MULT[i])] = (lat, acc, sum(imb) / len(imb) if imb else float('nan'), dead)
    json.dump({f'{k[0]}|{k[1]}': v for k, v in out.items()}, open(os.path.join(R10, 'sanity_diag.json'), 'w'), indent=1)
    for k, v in sorted(out.items()):
        print(k, [round(x, 4) for x in v])
    shutil.rmtree(RAW)


if __name__ == '__main__':
    main()
