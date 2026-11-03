"""v20 (Part L): decision-delay sensitivity (results_v20_delay/).

Stages (python3 experiments_v20.py STAGE [nproc]; --shard i/n accepted):
  drain    drain tests of the 3 variants with -deft_vn_rr 1 -deft_lb decision_delay 4 (v10 protocol and masks) -> drain_summary.csv
  eval     CI_heurLA_G, CI_qlLA_G, FULL_qlLA_G with -deft_vn_rr 1 at N = 1, 2, 4: all sizes, the K4 load points, uniform, hotspot and chipperm fault-free, uniform with
           one faulty VL per chiplet, seeds 61-65
  csv      delay_runs.csv; raw outputs deleted
  n0check  N = 0 given explicitly, whole stats files against the K5 runs; before experiments_v19.py csv deletes them -> n0_check.md
  sanity   latency against N at very low load, against N x (multi-output hops per packet) -> delay_sanity.md
  check    integrity of the eval outputs; prints no results
  pre      L3: timing only, terms computed in the previous cycle (rtl_pre/; extra = number of designs, for a test)
  precsv   L3: pre_runs.csv
N = 0 and the DeFT(rho*) reference come from results_v19_vnrr/eval_runs.csv (same binary, seeds, loads).
"""
import csv
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_jobs  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v20_delay')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v20')
SIZES = ['2x2', '3x3', '4x4']
VARIANTS = ['CI_heurLA_G', 'CI_qlLA_G', 'FULL_qlLA_G']
DELAYS = (1, 2, 4)
SEEDS = range(61, 66)
NL = chr(10)


def scenarios(z):
    return [('uniform', E5.FREE[z]), ('hotspot', E5.FREE[z]), ('chipperm', E5.FREE[z]), ('uniform', E5.NORTH[z])]


def delay_args(n):
    return E19.RR + ['-deft_lb', 'decision_delay', str(n)]


def eval_jobs():
    P = E19.lp()
    js = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            for n in DELAYS:
                a0 = list(mm[v]) + delay_args(n)
                for p, m in scenarios(z):
                    for r in P[E5.key(z, p, m)]['eval']:
                        js += [E5.job('delay', z, f'{v}-N{n}', a0, p, m, r, s, E10.lut(z, v, p)) for s in SEEDS]
    return js


def to_csv():
    import make_eval_csv as MK
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, 'eval', '*.json'))):
        (v, p, m, rate, seed), d = MK.parse(f)
        s, l = d['summary'], d['deft_lb']
        var, n = v.rsplit('-N', 1)
        rows.append(dict(variant=var, delay=int(n), pattern=p, mask=m, rate=repr(rate), seed=seed, accepted=repr(s['average_ip_throughput_flits_per_cycle_per_ip']),
                         latency=repr(s['global_average_delay_cycles']), p99=repr(l['delay_p99']), injected=s['total_injected_packets'], received=s['total_received_packets'],
                         dead_ends=l['dead_end_events'], hops_chip=l['hops_chip'], hops_chip_multi=l['hops_chip_multi'], hops_ipos=l['hops_ipos'], hops_ipos_multi=l['hops_ipos_multi']))
    with open(os.path.join(RES, 'delay_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(f'delay_runs.csv: {len(rows)} rows; dead ends {sum(r["dead_ends"] for r in rows)}')
    return len(rows)


# ---- checks of the option ----
def n0check(nproc):
    """N = 0 given explicitly, with the round-robin: whole stats files against the K5 runs (before the K5 raw outputs are deleted)."""
    P = E19.lp()
    js = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            a0 = list(mm[v]) + delay_args(0) + ['-deft_lb', 'hop_stats', '0']
            r = P[E5.key(z, 'uniform', E5.FREE[z])]['eval'][3]
            js.append(E5.job('eval', z, v, a0, 'uniform', E5.FREE[z], r, 61, E10.lut(z, v, 'uniform')))
    out = os.path.join(RAW, 'n0check')
    run_jobs(js, out, nproc=nproc, timeout=14400)
    same = [n for n, _ in js if open(os.path.join(out, n + '.json'), 'rb').read() == open(os.path.join(E19.raw('eval'), n + '.json'), 'rb').read()]
    L = ['# v20: N = 0 against the K5 runs', '', f'CI_heurLA_G, CI_qlLA_G and FULL_qlLA_G with `-deft_vn_rr 1 -deft_lb decision_delay 0 -deft_lb hop_stats 0`, every size, uniform at 1.0 x Lsat, seed 61; whole stats file against the K5 run.', '',
         f'**{len(same)} / {len(js)} byte-identical.**']
    open(os.path.join(RES, 'n0_check.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)
    return len(same) == len(js)


def sanity(nproc):
    """At very low load a head waits exactly N extra cycles on each multi-output hop, so the latency must rise by N x (multi-output hops per packet)."""
    js = []
    for z in SIZES:
        mm = E10.methods(z)
        for v in VARIANTS:
            for n in (0,) + DELAYS:
                a0 = list(mm[v]) + delay_args(n) + ['-deft_lb', 'hop_stats', '1']
                js.append(E5.job('sane', z, f'{v}-N{n}', a0, 'uniform', E5.FREE[z], E5.L0_RATE, 1001, E10.lut(z, v, 'uniform')))
    out = os.path.join(RAW, 'sanity')
    res = run_jobs(js, out, nproc=nproc, timeout=14400)
    L = ['# v20: the decision delay at very low load', '', f'Uniform, fault-free, rate {E5.L0_RATE}, seed 1001 (not an evaluation seed). A head waits exactly N extra cycles on a multi-output hop when nothing else holds it, so latency(N) - latency(0) should be N x h, with h = multi-output hops per received packet.', '',
         '| size | variant | h (N = 1) | latency N = 0 | N = 1: rise / N x h | N = 2: rise / N x h | N = 4: rise / N x h |', '|---|---|---|---|---|---|---|']
    worst = 0.0
    for z in SIZES:
        for v in VARIANTS:
            get = {n: next(d for nm, d in res.items() if nm.startswith(f'sane__{v}-N{n}__{z}-')) for n in (0,) + DELAYS}
            lat = {n: get[n]['summary']['global_average_delay_cycles'] for n in get}
            cells = []
            for n in DELAYS:
                l = get[n]['deft_lb']
                h = (l['hops_chip_multi'] + l['hops_ipos_multi']) / get[n]['summary']['total_received_packets']
                rise = lat[n] - lat[0]
                worst = max(worst, abs(rise - n * h) / (n * h))
                cells.append(f'{rise:.2f} / {n * h:.2f}')
            l1 = get[1]['deft_lb']
            L.append(f'| {z} | {v} | {(l1["hops_chip_multi"] + l1["hops_ipos_multi"]) / get[1]["summary"]["total_received_packets"]:.2f} | {lat[0]:.2f} | ' + ' | '.join(cells) + ' |')
    L += ['', f'Largest relative difference between the rise and N x h: {100 * worst:.1f} %. Each run has only about 100 packets, and the chosen paths change with N (h is measured per N), so single cells are noisy; the agreement is closest at N = 4, where the rise is largest.']
    open(os.path.join(RES, 'delay_sanity.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    shutil.rmtree(out)


# ---- L3: terms computed in the previous cycle (timing only; results_v20_delay/rtl_pre) ----
PRE_RTL = os.path.join(RES, 'rtl_pre')
PRE_LEVELS = {0: 'as simulated', 1: 'w f + beta b and w occ registered (same function, occupancy one cycle old)', 2: 'also the lookahead minimum and the path totals per destination chiplet (a different function)'}


def pre_run(arg):
    import re
    import subprocess
    import synth_v18 as S
    d, pre = arg
    n = S.tag(*d) + f'__pre{pre}'
    odir = os.path.join(RAW, 'pre')
    os.makedirs(odir, exist_ok=True)
    if os.path.exists(os.path.join(odir, n + '.sta.txt')):
        return n, True
    ys = S.yosys_script(d, True, odir, pipe=0, name=n)
    for f in ('lb_units.v', 'router_top.v'):
        ys = ys.replace(os.path.join(S.RTL, f), os.path.join(PRE_RTL, f))
    ys, k = re.subn(r'-set PIPE 0', f'-set PIPE 0 -set PRE {pre}', ys)
    assert k == 1
    open(os.path.join(odir, n + '.ys'), 'w').write(ys)
    r = subprocess.run([S.YOSYS, '-q', '-l', os.path.join(odir, n + '.log'), '-s', os.path.join(odir, n + '.ys')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return n, False
    tcl = S.STA_TCL.format(lib=S.LIB, net=os.path.join(odir, n + '.net.v'), period=S.CLOCK_PS / 1000.0)
    tcl = tcl.replace('report_checks -to [get_ports fb_out_g*]', 'rep PRE_OCC {*sel.pre_f* *sel.pre_la* *sel.pre_oc*}' + NL + 'rep PRE_TAB {*sel.pre_t* *sel.pre_ah*}' + NL + 'report_checks -to [get_ports fb_out_g*]')
    tf = os.path.join(odir, n + '.tcl')
    open(tf, 'w').write(tcl)
    with open(os.path.join(odir, n + '.sta.txt'), 'w') as o:
        subprocess.run([S.STA, '-no_init', '-no_splash', '-exit', tf], stdout=o, stderr=subprocess.STDOUT, timeout=3600)
    return n, True


def pre_designs():
    import synth_v18 as S
    ds = [d for d in S.PIPE_DESIGNS if d[3] == 0]
    return [(d, p) for d in ds for p in (1, 2)] + [(ds[0], 0), (ds[-1], 0)]


def pre_csv():
    import math
    import re
    import synth_v18 as S
    areas = S.lib_areas()
    rows = []

    def group(txt, g):
        m = re.search(r'GROUP ' + g + r' (\d+)(.*?)(GROUP|\Z)', txt, re.S)
        d = re.search(r'(-?[0-9.]+)\s+data arrival time', m.group(2)) if m and int(m.group(1)) > 0 else None
        s = re.search(r'(-?[0-9.]+)\s+slack', m.group(2)) if m and int(m.group(1)) > 0 else None
        return (float(d.group(1)), float(s.group(1))) if d and s else (None, None)
    for d, p in pre_designs():
        n = S.tag(*d) + f'__pre{p}'
        txt = open(os.path.join(RAW, 'pre', n + '.sta.txt')).read()
        ar, sr = group(txt, 'ROUTE_REG')
        ao, so = group(txt, 'OVC_REG')
        slack = min(x for x in (sr, so) if x is not None)
        tot = S.parse_hier(os.path.join(RAW, 'pre', n + '.stat.json'), areas)
        aocc, socc = group(txt, 'PRE_OCC')
        atab, stab = group(txt, 'PRE_TAB')
        rows.append(dict(method=S.METHODS[d[0]], rtype=d[1], size=d[2], form='P' if d[3] else 'S', pre=p, arrival_decision_ns=max(x for x in (ar, ao) if x is not None), slack_decision_ns=slack,
                         cycles_at_1ghz=math.ceil(1.0 - slack), arrival_occ_terms_ns=aocc, arrival_tables_ns=atab, area_flat_um2=round(sum(x['area'] for x in tot.values()), 1)))
    with open(os.path.join(RES, 'pre_runs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    print(f'pre_runs.csv: {len(rows)} rows')


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'n0check':
        sys.exit(0 if n0check(nproc) else 1)
    elif stage == 'sanity':
        sanity(nproc)
    elif stage == 'pre':
        import synth_v18 as S
        from multiprocessing import Pool
        S.constr_file()
        ds = pre_designs()[:int(sys.argv[3])] if len(sys.argv) > 3 else pre_designs()
        with Pool(nproc) as pool:
            res = pool.map(pre_run, ds, chunksize=1)
        print('failed:', [n for n, ok in res if not ok], flush=True)
    elif stage == 'precsv':
        pre_csv()
    elif stage == 'check':
        sys.exit(0 if E19.check_raw(os.path.join(RAW, 'eval'), eval_jobs(), 'delay') else 1)
    elif stage == 'drain':
        d = os.path.join(RAW, 'drain')
        res = run_jobs(E19.drain_jobs(methods=VARIANTS, extra=delay_args(4)), d, nproc=nproc, timeout=14400)
        fails = E19.drain_report(res, os.path.join(RES, 'drain_summary.csv'))
        if not fails:
            shutil.rmtree(d)
        sys.exit(1 if fails else 0)
    elif stage == 'eval':
        js = eval_jobs()
        print('delay jobs:', len(js), flush=True)
        res = run_jobs(js, os.path.join(RAW, 'eval'), nproc=nproc, timeout=14400)
        print('done; missing outputs:', sum(1 for v in res.values() if v is None), flush=True)
    elif stage == 'csv':
        n = to_csv()
        if n == len(eval_jobs()):
            shutil.rmtree(os.path.join(RAW, 'eval'))
    else:
        raise SystemExit(__doc__)
