"""v26 (results_v26_faults/): fault coverage. The model check on all fault patterns, the conformance of the model with the simulator, and
the performance under random VL faults at four rates.

Stages (python3 experiments_v26.py STAGE [nproc] [extra]; --shard i/n accepted by the run stages):
  regress   A0: the 84-configuration set, bin/noxim with every option absent and explicitly off, against the ee0e247 build
            (~/lbbin/noxim_ee0e247, made by build_ref.sh) and the ce6ab6a build; whole stats JSON byte by byte -> regression.md
  masks     B1 and A2: the 192 masks of Part B and the mask sets of A2 -> masks_v26.json, masks_v26.md
  luts      one LUT per mask of Part B (the generator settings of v23) -> luts/v23/lut_<size>_<mask>.yaml (not in the repository)
The other parts live in their own modules and are dispatched from here:
  Part A, model check (a1, a1csv, a2, a2sub, aneg)     experiments_v26_formal.py
  Part A3, conformance (a3_*)                          experiments_v26_conf.py
  Part B (b_*)                                         experiments_v26_eval.py
Nothing is tuned in this round and no row is changed: the row definitions are those of experiments_v25.row_args. Raw outputs stay
under ~/lbraw/v26 (not in the repository). Every method runs with DeFT-P's VN options and -traffic_rng 1; LUTs luts/v23, one per mask.
"""
import json
import math
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import BIN  # noqa: E402
import experiments_v5 as E5  # noqa: E402
import experiments_v10 as E10  # noqa: E402
import experiments_v19 as E19  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v24 as X24  # noqa: E402
import experiments_v25 as X25  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v26_faults')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v26')
REF_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_ee0e247')     # the build this round's results must stay identical to
OLD_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_ce6ab6a')     # the reference of the v25 regression
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)
MAIN, SECOND = X25.MAIN, X25.SECOND
REFS = ['DeFT_P', 'DeFT_B', 'DeFT_Dis', 'DeFT_Ran']
ROWS = REFS + [MAIN, SECOND]
row_args, job, lb = X25.row_args, X24.job, X24.lb

# ---- masks (PREREGISTRATION.md, B1 and A2) ----
MASK_SEED = 2611
RATES = [(1, 16), (2, 16), (4, 16), (8, 16)]          # faulty share of all VLs
N_MASKS = 16
A2_RANDOM = {'3x3': 200, '4x4': 60}
MASK_FILE = os.path.join(RES, 'masks_v26.json')


def raw(stage):
    return os.path.join(RAW, stage)


WIDTH_FILE = os.path.join(RAW, 'width.txt')


def width(default):
    """The number of processes of the next batch of runs: the number in ~/lbraw/v26/width.txt if that file exists, else the stage's
    argument. The unattended chains write the file so that the model checks and the simulations share the machine."""
    try:
        return max(1, int(open(WIDTH_FILE).read().split()[0]))
    except Exception:
        return default


def nchip(size):
    cx, cy = E5.SIZES[size]
    return cx * cy


def mask_hex(size, vls):
    """The mask string of a set of faulty VL indices: bit v = VL v (VL v belongs to chiplet v // 4), one hex digit per chiplet."""
    return '0x%0*X' % (nchip(size), sum(1 << v for v in vls))


def mask_set(m):
    b = int(m, 16)
    return frozenset(v for v in range(64) if b >> v & 1)


def per_chiplet(size, m):
    b = int(m, 16)
    return [bin(b >> (4 * c) & 15).count('1') for c in range(nchip(size))]


def rate_name(r):
    return '%d/%d' % r


def n_faulty(size, r):
    return int(math.floor(r[0] * 4 * nchip(size) / float(r[1])))


def draw_part_b():
    """16 distinct masks per (size, rate), uniform among the masks with exactly n faulty VLs and a functional VL in every chiplet:
    rejection sampling with one random.Random(2611), sizes and rates in the order of SIZES and RATES. 2x2 at n = 1: all 16 masks."""
    rnd = random.Random(MASK_SEED)
    out = []
    for size in SIZES:
        nc, nvl = nchip(size), 4 * nchip(size)
        for r in RATES:
            n = n_faulty(size, r)
            if math.comb(nvl, n) == N_MASKS:
                ms = [frozenset([v]) for v in range(nvl)]
            else:
                ms, seen = [], set()
                while len(ms) < N_MASKS:
                    m = frozenset(rnd.sample(range(nvl), n))
                    if m in seen or any(all(4 * c + s in m for s in range(4)) for c in range(nc)):
                        continue
                    seen.add(m)
                    ms.append(m)
            for i, m in enumerate(ms):
                h = mask_hex(size, m)
                pc = per_chiplet(size, h)
                out.append(dict(size=size, rate=rate_name(r), n_faulty=n, index=i + 1, mask=h, faults_per_chiplet=pc, max_faults_in_a_chiplet=max(pc),
                                chiplets_with_one_functional_vl=sum(1 for x in pc if x == 3)))
    return out


def draw_a2():
    """The mask sets of A2 on 3x3 and 4x4. Set 1: fault-free. Set 2: every fault combination of one chiplet (14 patterns that leave it a
    functional VL), all other chiplets fault-free. Set 3: every chiplet draws one of its 15 patterns uniformly; its own random.Random(2611),
    3x3 first, then 4x4. Set 4 is the masks of Part B of the size."""
    rnd = random.Random(MASK_SEED)
    out = {}
    for size in ('3x3', '4x4'):
        nc = nchip(size)
        s2 = ['0x%0*X' % (nc, p << (4 * c)) for c in range(nc) for p in range(1, 15)]
        s3 = []
        while len(s3) < A2_RANDOM[size]:
            h = '0x%0*X' % (nc, sum(rnd.randrange(15) << (4 * c) for c in range(nc)))
            if h not in s3:
                s3.append(h)
        out[size] = dict(set1=[E5.FREE[size]], set2=s2, set3=s3)
    return out


def make_masks():
    pb, a2 = draw_part_b(), draw_a2()
    os.makedirs(RES, exist_ok=True)
    json.dump(dict(seed=MASK_SEED, note='bit v of a mask = VL v faulty (both directions); VL v belongs to chiplet v // 4; one hex digit per chiplet, chiplet 0 last',
                   part_b=pb, a2=a2), open(MASK_FILE, 'w'), indent=1)
    L = ['# Masks of v26 (experiments_v26.py masks; `masks_v26.json`)', '',
         'Part B: 16 distinct masks per (size, rate), drawn uniformly among the masks with exactly n faulty VLs and at least one functional VL in every chiplet',
         '(rejection sampling, `random.Random(%d)`, sizes and rates in the order of the table; 2x2 at 1/16: all 16 masks, in VL order). n = floor(rate x number of VLs).' % MASK_SEED,
         'A mask is a hex number with one digit per chiplet (chiplet 0 is the last digit); a set bit is a faulty VL, in both directions.', '',
         '| size | rate | faulty VLs | # | mask | faults per chiplet | largest number in one chiplet | chiplets with one functional VL |', '|---|---|---|---|---|---|---|---|']
    for e in pb:
        L.append('| %s | %s | %d | %d | %s | %s | %d | %d |' % (e['size'], e['rate'], e['n_faulty'], e['index'], e['mask'], ' '.join(str(x) for x in e['faults_per_chiplet']),
                                                           e['max_faults_in_a_chiplet'], e['chiplets_with_one_functional_vl']))
    L += ['', 'A2, per size: set 1 = the fault-free mask; set 2 = every fault combination of one chiplet with all other chiplets fault-free (%d masks on 3x3, %d on 4x4);' % (
        len(a2['3x3']['set2']), len(a2['4x4']['set2'])),
          'set 3 = random masks from the whole space, every chiplet drawing one of its 15 patterns uniformly (its own `random.Random(%d)`, 3x3 first: %d masks on 3x3, %d on 4x4);' % (
              MASK_SEED, len(a2['3x3']['set3']), len(a2['4x4']['set3'])),
          'set 4 = the 64 masks of Part B of the size. The masks of sets 2 and 3 are listed in `masks_v26.json`.']
    open(os.path.join(RES, 'masks_v26.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[:12]))
    print('part B masks: %d; distinct (size, mask): %d' % (len(pb), len({(e['size'], e['mask']) for e in pb})))
    for size in SIZES:
        for r in RATES:
            es = [e for e in pb if e['size'] == size and e['rate'] == rate_name(r)]
            print(size, rate_name(r), 'n', es[0]['n_faulty'], 'masks', len(es), 'max faults in a chiplet:', sorted({e['max_faults_in_a_chiplet'] for e in es}),
                  'chiplets with one functional VL (mean): %.2f' % (sum(e['chiplets_with_one_functional_vl'] for e in es) / float(len(es))))


def masks_file():
    return json.load(open(MASK_FILE))


def part_b():
    """The 192 entries of Part B, in the order of the file."""
    return masks_file()['part_b']


def b_masks(size=None, rate=None):
    return [e for e in part_b() if (size is None or e['size'] == size) and (rate is None or e['rate'] == rate)]


# ---- LUTs ----
def luts(nproc):
    from multiprocessing import Pool
    os.makedirs(X23.LUTD, exist_ok=True)
    jobs = [(e['size'], e['mask']) for e in part_b()]
    with Pool(nproc) as pool:
        res = pool.map(X23._gen, jobs, chunksize=1)
    new = [t for _, t in res if t > 0]
    print('%d LUTs (%d generated now); generation seconds: mean %.0f, max %.0f' % (len(res), len(new), sum(new) / max(1, len(new)), max(new or [0])))
    missing = [j for j in jobs if not os.path.exists(X23.lut23(*j))]
    print('missing:', missing)
    return not missing


# ---- A0: regression ----
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
    L = ['# A0: regression before round 26 (experiments_v26.py regress)', '',
         'Reference: the ee0e247 build (the last commit of round 25), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 %s.' % md['ref'],
         'Current binary `bin/noxim`: md5 %s (%s the reference build). The ce6ab6a build (round 24, the reference of the v25 regression): md5 %s.' % (
             md['new'], 'the same file as' if md['new'] == md['ref'] else '**not the same file as**', md['old']),
         'Configurations: %d = the 84-configuration set of v14-v25. Comparison: the whole stats JSON file, byte by byte, against the ee0e247 build.' % len(cf), '',
         '* ce6ab6a build: **%d / %d byte-identical**.' % (ok['old'], len(cf)),
         '* `bin/noxim`, options absent: **%d / %d byte-identical**.' % (ok['new'], len(cf)),
         '* `bin/noxim`, `%s` given: **%d / %d byte-identical**.' % (' '.join(X24.EXPLICIT_OFF), ok['explicit'], len(cf)), ''] + (diffs or ['No differences.'])
    import subprocess
    changed = subprocess.run(['git', '-C', os.path.join(HERE, '..', '..'), 'diff', '--name-only', 'ee0e247', '--', 'src', 'bin/Makefile'],
                             capture_output=True, text=True).stdout.split()
    L += ['', 'Simulator sources against ee0e247 when this file was written (`git diff --name-only ee0e247 -- src bin/Makefile`): %s.' % (
        'no difference' if not changed else 'changed: ' + ', '.join(changed))]
    open(os.path.join(RES, 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if not diffs:
        shutil.rmtree(out)
    return not diffs


MODULES = {'a1': 'experiments_v26_formal', 'a1csv': 'experiments_v26_formal', 'a2': 'experiments_v26_formal', 'a2md': 'experiments_v26_formal',
           'a2sub': 'experiments_v26_formal', 'aneg': 'experiments_v26_formal', 'a3': 'experiments_v26_conf', 'b': 'experiments_v26_eval'}

if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(nproc) else 1)
    elif stage == 'masks':
        make_masks()
    elif stage == 'luts':
        sys.exit(0 if luts(nproc) else 1)
    else:
        import importlib
        pre = stage.split('_', 1)[0]
        importlib.import_module(MODULES[pre]).run_stage(stage, nproc, extra)
