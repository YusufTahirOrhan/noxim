"""v23 Part C: cross-validation against CEA's noxim3.5d-sop (D3vKrish/noxim3.5d-sop, scratch clone ~/lbrev/cea, read-only).

Stages (python3 cea_crossval.py STAGE [nproc]):
  config   write results_v23_fidelity/cea/deft_2x2_rr.yaml and deft_2x2_bl.yaml: our 2x2 system (4 chiplets of 4x4 routers on an
           8x8 interposer, our VL slots) in CEA's MULTI_MESH format, the vertical-link selections from luts/v23/lut_2x2_0x0000.yaml
           -> cea/config_notes.md (what could and could not be expressed)
  smoke    one CEA run of each configuration, prints the statistics block
  sweep    CEA (rr and bl) and our DeFT-B (pipe_all 0), uniform fault-free, seed 101, the D1 grid (coarse, then fine where needed)
  eval     CEA (rr and bl), the 9 loads of DeFT-P's v23 ladder (2x2 uniform, pipe_all 0), seeds 91-93
  report   cea/cea_runs.csv, report/cea_crossval.md (Lsat of each simulator, the 9-load curves against eval_runs.csv, the verdict)
CEA runs: `noxim -config CFG -pir R poisson -traffic random -seed S -sim 10000 -warmup 2000` (Bernoulli injection with rate R per
cycle and node, 8-flit packets, 2 VCs, 4-flit buffers, as ours). Raw outputs under ~/lbraw/v23/cea.
"""
import csv
import glob
import json
import math
import os
import re
import subprocess
import sys
from multiprocessing import Pool

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v23 as X  # noqa: E402
from runner import common_args, run_jobs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v23_fidelity')
CEA_DIR = os.path.join(RES, 'cea')
OUT = os.path.join(RES, 'report')
CEA = os.path.expanduser('~/lbrev/cea/noxim3.5d-sop')
CEA_BIN = os.path.join(CEA, 'bin', 'noxim')
CEA_LIB = os.path.join(CEA, 'bin', 'systemc', '2.3.4', 'lib')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v23', 'cea')
LUT = X.lut23('2x2', '0x0000')
NL = chr(10)
# our 2x2 system: 2 x 2 chiplets of 4 x 4 routers, footprint 8 x 8; chiplet router id = footprint index (DeftTopology)
CX, CW, FW = 2, 4, 8
SLOT = {0: (1, 0), 1: (3, 1), 2: (2, 3), 3: (0, 2)}      # N, E, S, W: chiplet-local (x, y) (DeftTopology::slotLocalX/Y, 4x4 chiplets)
SEEDS_EVAL = (91, 92, 93)
VARIANTS = ('rr', 'bl')     # rr: DeFT's own round-robin VC choice; bl: the VC choice delegated to CEA's BUFFER_LEVEL selection


def chip_xy(c):
    return c % CX, c // CX


def vl_chip_local(vl):
    """(chiplet, chiplet-local router id) of a VL's chiplet endpoint."""
    c, s = divmod(vl, 4)
    lx, ly = SLOT[s]
    return c, ly * CW + lx


def vl_interposer_local(vl):
    c, s = divmod(vl, 4)
    cx, cy = chip_xy(c)
    lx, ly = SLOT[s]
    return (cy * CW + ly) * FW + cx * CW + lx


def router_chip_local(r):
    fx, fy = r % FW, r // FW
    return (fy // CW) * CX + fx // CW, (fy % CW) * CW + fx % CW


def majority(xs):
    return max(sorted(set(xs)), key=lambda v: xs.count(v))


def make_config(rr):
    d = yaml.safe_load(open(LUT))
    ent = {(e['key']['source_router_id'], e['key']['destination_chiplet_id']): e['value'] for e in d['entries'] if e['key']['fault_mask_id'].lower() == '0x0000'}
    notes = []
    down_sel = {c: [] for c in range(4)}
    exit_agree = 0
    for r in range(64):
        c, lid = router_chip_local(r)
        picks = [ent[(r, dc)]['source_exit']['selected_vl_id'] for dc in range(4) if dc != c and (r, dc) in ent]
        vl = majority(picks)
        exit_agree += len(set(picks)) == 1
        own = [v for v in range(c * 4, c * 4 + 4) if vl_chip_local(v)[1] == lid]
        if own and vl != own[0]:
            notes.append('router %d (chiplet %d, local %d): LUT exit VL %d, its own VL %d used instead (CEA asserts that a boundary source takes its own link)' % (r, c, lid, vl, own[0]))
            vl = own[0]
        down_sel[c].append([lid, vl_chip_local(vl)[1]])
    up_sel = {c: [] for c in range(4)}
    entry_cells = entry_agree = 0
    for v in range(16):
        for dc in range(4):
            if dc == v // 4:
                continue
            picks = [ent[(r, dc)]['destination_entry']['selected_vl_id'] for r in range(64) if (r, dc) in ent and ent[(r, dc)]['source_exit']['selected_vl_id'] == v]
            if not picks:
                continue
            entry_cells += 1
            entry_agree += len(set(picks)) == 1
            up_sel[dc].append([vl_interposer_local(v), vl_interposer_local(majority(picks))])
    base = yaml.safe_load(open(os.path.join(CEA, 'config_examples', '2D5MultiMeshBaseline.yaml')))
    mm = {'I': {'dim_x': FW, 'dim_y': FW, 'dim_z': 1, 'n_virtual_channels': 2, 'custom_pe': [0],
                'vertical_links_placement': {'up': {'C%d' % c: [[vl_interposer_local(v), vl_chip_local(v)[1]] for v in range(c * 4, c * 4 + 4)] for c in range(4)}},
                'vertical_links_selection': {'up': {'C%d' % c: up_sel[c] for c in range(4)}}}}
    for c in range(4):
        mm['C%d' % c] = {'dim_x': CW, 'dim_y': CW, 'dim_z': 1, 'n_virtual_channels': 2,
                         'vertical_links_placement': {'down': [[vl_chip_local(v)[1], vl_interposer_local(v)] for v in range(c * 4, c * 4 + 4)]},
                         'vertical_links_selection': {'down': down_sel[c]}}
    base['multi_mesh'] = mm
    base.update({'routing_algorithm': 'DEFT', 'selection_strategy': 'BUFFER_LEVEL' if not rr else 'RANDOM', 'route_using_selection_strategy': not rr,
                 'n_virtual_channels': 2, 'buffer_depth': 4, 'flit_size': 32, 'min_packet_size': 8, 'max_packet_size': 8,
                 'traffic_distribution': 'TRAFFIC_RANDOM', 'simulation_time': 10000, 'stats_warm_up_time': 2000, 'packet_injection_rate': 0.005,
                 'probability_of_retransmission': 0.005})
    stats = dict(exit_agree=exit_agree, entry_cells=entry_cells, entry_agree=entry_agree, overrides=notes)
    return base, stats


def cfg_path(var):
    return os.path.join(CEA_DIR, 'deft_2x2_%s.yaml' % var)


def config():
    os.makedirs(CEA_DIR, exist_ok=True)
    for var in VARIANTS:
        base, st = make_config(var == 'rr')
        with open(cfg_path(var), 'w', newline=NL) as f:
            f.write('# v23 Part C: our 2x2 DEFT_2_5D system in CEA noxim3.5d-sop format (generated by cea_crossval.py config)' + NL)
            yaml.safe_dump(base, f, default_flow_style=None, sort_keys=False, width=200)
    L = ['# Part C: the configuration given to CEA\'s simulator (cea_crossval.py config)', '',
         '* Topology: interposer `I` 8 x 8 (our footprint model), chiplets `C0`..`C3` 4 x 4 (chiplet c at footprint (c mod 2, c div 2)), '
         '4 vertical links per chiplet at our slots N (1,0), E (3,1), S (2,3), W (0,2), each to the interposer router under it. 2 VCs, 4-flit '
         'buffers, 8-flit packets, 32-bit flits; uniform random traffic (CEA `TRAFFIC_RANDOM`, injection `-pir R poisson`: Bernoulli with rate R '
         'per cycle and PE, as our tables). **Deviation:** CEA cannot run a mesh without processing elements (`custom_pe` must name at least one '
         'valid node) and its table-based traffic keys sources by mesh-local ids, so the interposer carries one PE at its corner router 0 '
         '(`custom_pe: [0]`): 65 PEs instead of 64, about 1.5 % of the sources and destinations on the interposer.',
         '* `routing_algorithm: DEFT` (CEA\'s Routing_DEFT: the paper\'s Algorithm 1 and Rules 1-3). Variant `rr`: `route_using_selection_strategy: false`, '
         'so the VC at the boundary round-robin point is DeFT\'s own round-robin (`selectVCOut`); variant `bl`: `true` with `selection_strategy: BUFFER_LEVEL`, '
         'CEA\'s adaptive VC choice among the offered VN0/VN1.',
         '* Exit selection (`vertical_links_selection: down`, one VL per source router, consulted once at the source): the exit of '
         '`luts/v23/lut_2x2_0x0000.yaml` (`entries`, the v1-v21 exit used by every DeFT variant of this repository). CEA keys the exit by the source '
         'router alone, our LUT by (source router, destination chiplet): %d of 64 routers have the same exit for all 3 destination chiplets; the '
         'majority is used elsewhere.' % st['exit_agree'],
         '* Entry selection (`vertical_links_selection: up`, per interposer router and destination chiplet, consulted once at the interposer '
         'router where the packet lands): the `destination_entry` of the LUT\'s `entries` for the pairs whose exit lands there (the v1-v21 '
         'entry = DeFT-B\'s): %d of %d (landing router, destination chiplet) cells have a single entry over those pairs. **The paper\'s '
         'per-destination-router entry (DeFT-P, `entries_by_destination`) cannot be expressed in CEA\'s format**, whose entry is a function of '
         'the landing router and the destination chiplet; the cross-validation reference is therefore DeFT-B (same VN rules as DeFT-P), and '
         'DeFT-P is shown next to it.' % (st['entry_agree'], st['entry_cells']),
         '* Interposer routers that are not landing routers keep CEA\'s default (nearest VL); they are never consulted for an entry.',
         '* Overrides (CEA asserts that a boundary source takes its own link): %s' % ('none' if not st['overrides'] else '; '.join(st['overrides'])),
         '* Both simulators record the latency of the head flit from its generation timestamp (`Stats::receivedFlit`, identical code), so the latencies '
         'compare directly. CEA divides the per-IP throughput by all 128 routers; it is recomputed here per chiplet router from the network throughput. '
         'The router pipelines differ in detail (CEA imposes no 2-cycle head rule), which the saturation-load band absorbs.']
    open(os.path.join(CEA_DIR, 'config_notes.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


# ---- runs ----
def cea_cmd(var, rate, seed):
    return ['./noxim', '-config', cfg_path(var), '-pir', '%.4f' % rate, 'poisson', '-traffic', 'random', '-seed', str(seed), '-sim', '10000', '-warmup', '2000']


def run_cea(arg):
    name, var, rate, seed = arg
    out = os.path.join(RAW, name + '.txt')
    if os.path.exists(out):
        return name, True
    env = dict(os.environ, LD_LIBRARY_PATH=CEA_LIB)
    with open(out + '.tmp', 'w') as f:
        rc = subprocess.call(cea_cmd(var, rate, seed), cwd=os.path.join(CEA, 'bin'), stdout=f, stderr=subprocess.STDOUT, env=env)
    if rc == 0 and 'Global average delay' in open(out + '.tmp').read():
        os.rename(out + '.tmp', out)
        return name, True
    os.rename(out + '.tmp', out + '.fail')
    return name, False


def parse(path):
    t = open(path).read()
    g = lambda pat: float(re.search(pat, t).group(1))  # noqa: E731
    return dict(latency=g(r'Global average delay \(cycles\): (\S+)'), max_delay=g(r'Max delay \(cycles\): (\S+)'),
                net_thr=g(r'Network throughput \(flits/cycle\): (\S+)'), received=int(g(r'Total received packets: (\d+)')),
                accepted=g(r'Network throughput \(flits/cycle\): (\S+)') / 64.0)


def cea_jobs(stage, rates, seeds):
    return [('%s__cea_%s__2x2-uniform__0x0000__%.4f__s%d' % (stage, var, r, s), var, r, s) for var in VARIANTS for r in rates for s in seeds]


def run_many(jobs, nproc):
    os.makedirs(RAW, exist_ok=True)
    with Pool(nproc) as pool:
        res = pool.map(run_cea, jobs, chunksize=1)
    bad = [n for n, ok in res if not ok]
    print('%d runs, %d failed' % (len(jobs), len(bad)), bad[:5])
    return not bad


def cea_lat(stage, var, rate, seed=101):
    return parse(os.path.join(RAW, '%s__cea_%s__2x2-uniform__0x0000__%.4f__s%d.txt' % (stage, var, rate, seed)))['latency']


def our_job(rate, seed):
    name = 'ceasweep__DeFT_B-p0__2x2-uniform__0x0000__%.4f__s%d' % (rate, seed)
    args = common_args(seed, '0x0000', traffic=E5.REL + 'traffic/uniform_%.4f.txt' % rate, lut=LUT) + X.methods('2x2')['DeFT_B'] + X.TRNG + E5.SIM
    return name, args


def our_lat(rate):
    return json.load(open(os.path.join(RAW, 'ours', our_job(rate, 101)[0] + '.json')))['summary']['global_average_delay_cycles']


def lsat_of(lat, rates_coarse, l0):
    """The D1 rule on a latency function: largest swept rate before the latency first exceeds 3 x L0."""
    lsat = None
    for r in rates_coarse:
        if lat(r) > 3 * l0:
            return lsat, r
        lsat = r
    return lsat, None


def fine_grid(lat, l0):
    lsat, nxt = lsat_of(lat, E5.SAT_RATES, l0)
    if lsat is None or nxt is None or lsat > E5.LOW_LSAT:
        return []
    return [round(E5.FINE * i, 4) for i in range(1, int(round(nxt / E5.FINE)) + 1)]


def sweep(nproc):
    rates = E5.SAT_RATES + [E5.L0_RATE]
    E5.gen_tables('2x2', 'uniform', rates)
    ok = run_many(cea_jobs('sweep', rates, [101]), nproc)
    run_jobs([our_job(r, 101) for r in rates], os.path.join(RAW, 'ours'), nproc=nproc, timeout=3600)
    fine = set()
    for var in VARIANTS:
        fine |= set(fine_grid(lambda r: cea_lat('sweep', var, r), cea_lat('sweep', var, E5.L0_RATE)))
    fine_ours = set(fine_grid(our_lat, our_lat(E5.L0_RATE)))
    E5.gen_tables('2x2', 'uniform', sorted(fine | fine_ours))
    if fine:
        ok = run_many(cea_jobs('sweep', sorted(fine), [101]), nproc) and ok
    if fine_ours:
        run_jobs([our_job(r, 101) for r in sorted(fine_ours)], os.path.join(RAW, 'ours'), nproc=nproc, timeout=3600)
    print('sweep done', ok)


def ladder():
    P = json.load(open(os.path.join(RES, 'load_points_v23.json')))
    return P['2x2__uniform__0x0000__p0']['eval']


def evaluate(nproc):
    run_many(cea_jobs('eval', ladder(), SEEDS_EVAL), nproc)


def lsat_from_runs(lat, l0):
    fine = fine_grid(lat, l0)
    grid, rates = (E5.FINE, fine) if fine else (E5.GRID, E5.SAT_RATES)
    lsat = None
    for r in rates:
        if lat(r) > 3 * l0:
            break
        lsat = r
    return lsat, grid


def report():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, '*.txt'))):
        stage, var, p, m, rate, seed = os.path.basename(f)[:-4].split('__')
        d = parse(f)
        rows.append(dict(stage=stage, variant=var, pattern=p, mask=m, rate=rate, seed=int(seed[1:]), latency=d['latency'], max_delay=d['max_delay'],
                         accepted=repr(d['accepted']), received=d['received']))
    with open(os.path.join(CEA_DIR, 'cea_runs.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    for f in sorted(glob.glob(os.path.join(RAW, 'ours', '*.json'))):
        pass
    L = ['# Part C: cross-validation against CEA\'s noxim3.5d-sop (cea_crossval.py report)', '',
         'Configuration: `cea/deft_2x2_rr.yaml`, `cea/deft_2x2_bl.yaml`, `cea/config_notes.md`. Uniform traffic, fault-free 2x2 system. '
         'Both simulators record the head latency from the generation timestamp (identical `Stats::receivedFlit`). Accepted throughput per chiplet '
         'router = CEA network throughput / 64.', '']
    # Lsat
    L += ['## Saturation load (D1 rule: L0 at 0.0002, Lsat = largest swept rate before the latency first exceeds 3 x L0; seed 101)', '',
          '| simulator | L0 | Lsat | grid | Lsat / ours (DeFT-B) |', '|---|---|---|---|---|']
    ls = {}
    for var in VARIANTS:
        l0 = cea_lat('sweep', var, E5.L0_RATE)
        ls[var] = lsat_from_runs(lambda r: cea_lat('sweep', var, r), l0) + (l0,)
    l0o = our_lat(E5.L0_RATE)
    ls['ours'] = lsat_from_runs(our_lat, l0o) + (l0o,)
    P = json.load(open(os.path.join(RES, 'load_points_v23.json')))['2x2__uniform__0x0000__p0']
    for k, nm in (('rr', 'CEA DeFT (rr)'), ('bl', 'CEA DeFT (bl)'), ('ours', 'ours, DeFT-B (pipe_all 0)')):
        lsat, grid, l0 = ls[k]
        L.append('| %s | %.1f | %s | %s | %.2f |' % (nm, l0, lsat, grid, lsat / ls['ours'][0]))
    L.append('| ours, DeFT-P (D1) | %.1f | %s | %s | %.2f |' % (P['l0'], P['lsat'], P['grid'], P['lsat'] / ls['ours'][0]))
    # curves
    import report_v4 as R4
    R = R4.load_csv(os.path.join(RES, 'eval_runs.csv'))
    lad = ladder()
    L += ['', '## Latency and accepted throughput against load (9 loads of DeFT-P\'s ladder; geometric mean of seeds 91-93)', '',
          '| load (x Lsat) | rate | CEA rr: lat | CEA bl: lat | ours DeFT-B: lat | ours DeFT-P: lat | CEA rr: acc | CEA bl: acc | ours DeFT-B: acc | ours DeFT-P: acc |',
          '|---|---|---|---|---|---|---|---|---|---|']
    ratio, shape = [], []
    for i, r in enumerate(lad):
        cells = []
        vals = {}
        for var in VARIANTS:
            ds = [parse(os.path.join(RAW, 'eval__cea_%s__2x2-uniform__0x0000__%.4f__s%d.txt' % (var, r, s))) for s in SEEDS_EVAL
                  if os.path.exists(os.path.join(RAW, 'eval__cea_%s__2x2-uniform__0x0000__%.4f__s%d.txt' % (var, r, s)))]
            vals[var] = (gm([d['latency'] for d in ds]), mean([d['accepted'] for d in ds])) if ds else (float('nan'), float('nan'))
        for v in ('DeFT_B-p0', 'DeFT_P-p0'):
            ds = [R[(v, '2x2-uniform', '0x0000', r, s)] for s in SEEDS_EVAL if (v, '2x2-uniform', '0x0000', r, s) in R]
            vals[v] = (gm([d['latency'] for d in ds]), mean([d['accepted'] for d in ds])) if ds else (float('nan'), float('nan'))
        order = ['rr', 'bl', 'DeFT_B-p0', 'DeFT_P-p0']
        L.append('| %.1f | %.4f | %s | %s |' % (X.MULTS9[i], r, ' | '.join('%.1f' % vals[k][0] for k in order), ' | '.join('%.4f' % vals[k][1] for k in order)))
        if not math.isnan(vals['rr'][0]) and not math.isnan(vals['DeFT_B-p0'][0]):
            ratio.append(vals['rr'][0] / vals['DeFT_B-p0'][0])
            shape.append((vals['rr'][0], vals['DeFT_B-p0'][0]))
    dev = abs(ls['rr'][0] / ls['ours'][0] - 1)
    verdict = 'within' if dev <= 0.15 else 'outside'
    L += ['', '## Verdict', '',
          '* Saturation load: CEA (rr) %s against ours (DeFT-B) %s, deviation %.0f %% (%s the 15 %% band). CEA (bl): %s.' % (ls['rr'][0], ls['ours'][0], 100 * dev, verdict, ls['bl'][0]),
          '* Curve shape: CEA (rr) / ours (DeFT-B) latency ratio over the 9 loads %s; '
          'both curves %s monotone in load up to saturation.' % (', '.join('%.2f' % x for x in ratio), 'are' if all(shape[i][0] <= shape[i + 1][0] and shape[i][1] <= shape[i + 1][1] for i in range(len(shape) - 1)) else 'are not'),
          '* The comparison validates the DeFT mechanics shared by both simulators (VN rules, round-robin, exit and entry tables) under the same topology, buffers and traffic. '
          'It does not validate the paper\'s per-destination-router entry (not expressible in CEA\'s format) nor our late-binding modes.']
    open(os.path.join(OUT, 'cea_crossval.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def mean(xs):
    return sum(xs) / len(xs)


def smoke():
    env = dict(os.environ, LD_LIBRARY_PATH=CEA_LIB)
    for var in VARIANTS:
        out = subprocess.run(cea_cmd(var, 0.004, 1), cwd=os.path.join(CEA, 'bin'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, universal_newlines=True).stdout
        print(var, NL.join(l for l in out.split(NL) if l.startswith('%') or 'rror' in l or 'ssert' in l)[:3000])


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    {'config': config, 'smoke': smoke, 'sweep': lambda: sweep(nproc), 'eval': lambda: evaluate(nproc), 'report': report}[stage]()
