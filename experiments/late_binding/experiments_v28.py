"""v28 (results_v28_anchor/): the strongest early binder we can build. An injection-time family that contains DeFT (an anchor at DeFT-P's
entry VL with a threshold, a count of the packets already bound to each VL, ideal information), a tuned commit at the Down move, and the
late-binding row without the occupancy reports across the VLs under random VL faults.

Stages (python3 experiments_v28.py STAGE [nproc] [extra]):
  regress   A0 (extra = before) and A1 (extra = after): the 84-configuration set, bin/noxim with every option absent and explicitly off,
            against the b164e9e build (~/lbbin/noxim_b164e9e, made by build_ref.sh) and the d641861 build; whole stats JSON byte by byte
            -> regression_before.md / regression.md
The gates of the new rows (a2_*), the tuning (b_*), the evaluation (c_*), the fault runs (d_*) and the reports across the VLs under faults
(e_*) live in experiments_v28_eval.py and are dispatched from here.
Nothing of the frozen configuration is retuned and no existing row is changed: DeFT_P and the main row are built by
experiments_v25.row_args. Raw outputs stay under ~/lbraw/v28 (not in the repository). Every method runs with DeFT-P's VN options and
-traffic_rng 1; LUTs luts/v23.
"""
import os
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
import experiments_v27 as X27  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v28_anchor')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v28')
REF_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_b164e9e')     # the build this round's results must stay identical to
OLD_BIN = os.path.join(os.path.expanduser('~'), 'lbbin', 'noxim_d641861')     # the reference of the v27 regression
REF_COMMIT = 'b164e9e'
SIZES = ['2x2', '3x3', '4x4']
NL = chr(10)
MAIN = X25.MAIN
job, lb, lkey = X24.job, X24.lb, X24.lkey

# ---- the options of this round, each at its default (A1) ----
NEW_OFF = lb('oracle_bias', 0, 'oracle_pending', 0, 'pending_check', 0)
EXPLICIT_OFF = X27.EXPLICIT_OFF + NEW_OFF


def raw(stage):
    return os.path.join(RAW, stage)


WIDTH_FILE = os.path.join(RAW, 'width.txt')


def width(default):
    """The number of processes of the next batch of runs: the number in ~/lbraw/v28/width.txt if that file exists, else the stage's
    argument (so the width can be changed while a chain runs)."""
    try:
        return max(1, int(open(WIDTH_FILE).read().split()[0]))
    except Exception:
        return default


# ---- A0 / A1: regression ----
def regress(nproc, which):
    """which = before (A0: the build of b164e9e, before any change of this round) or after (A1: with the new options in the binary)."""
    import check_stats_regression as CSR
    from multiprocessing import Pool
    import subprocess
    out = raw('regress_' + which)
    os.makedirs(out, exist_ok=True)
    cf = list(CSR.configs())
    for size in SIZES:
        mm = E10.methods(size)
        r = E10.LP5['%s__uniform__%s' % (size, E5.FREE[size])]['eval'][3]
        for v in E10.NEW:
            n, a = E5.job('x', size, v, mm[v], 'uniform', E5.FREE[size], r, 7, E10.lut(size, v, 'uniform'))
            cf.append(('%s__%s' % (v, size), a))
    new = os.path.join(BIN, 'noxim')
    explicit = EXPLICIT_OFF if which == 'after' else X27.EXPLICIT_OFF
    tags = [('ref', REF_BIN, []), ('old', OLD_BIN, []), ('new', new, []), ('explicit', new, explicit)]
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
    changed = subprocess.run(['git', '-C', os.path.join(HERE, '..', '..'), 'diff', '--name-only', REF_COMMIT, '--', 'src', 'bin/Makefile'],
                             capture_output=True, text=True).stdout.split()
    head = ('# A0: regression before any change of round 28 (experiments_v28.py regress 12 before)' if which == 'before' else
            '# A1: regression with the options of round 28 in the binary (experiments_v28.py regress 12 after)')
    L = [head, '',
         'Reference: the %s build (the last commit of round 27), exported with `git archive` and built in a separate tree by `build_ref.sh`, md5 %s.' % (REF_COMMIT, md['ref']),
         'Binary under test `bin/noxim`: md5 %s (%s the reference build). The d641861 build (round 26, the reference of the v27 regression): md5 %s.' % (
             md['new'], 'the same file as' if md['new'] == md['ref'] else 'not the same file as', md['old']),
         'Configurations: %d = the 84-configuration set of v14-v27. Comparison: the whole stats JSON file, byte by byte, against the %s build.' % (len(cf), REF_COMMIT), '',
         '* d641861 build: **%d / %d byte-identical**.' % (ok['old'], len(cf)),
         '* `bin/noxim`, options absent: **%d / %d byte-identical**.' % (ok['new'], len(cf)),
         '* `bin/noxim`, `%s` given: **%d / %d byte-identical**.' % (' '.join(explicit), ok['explicit'], len(cf)), ''] + (diffs or ['No differences.'])
    L += ['', 'Simulator sources against %s when this file was written (`git diff --name-only %s -- src bin/Makefile`): %s.' % (
        REF_COMMIT, REF_COMMIT, 'no difference' if not changed else 'changed: ' + ', '.join(changed))]
    open(os.path.join(RES, 'regression_before.md' if which == 'before' else 'regression.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    if not diffs:
        shutil.rmtree(out)
    return not diffs


if __name__ == '__main__':
    stage = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(RES, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    if stage == 'regress':
        sys.exit(0 if regress(nproc, extra or 'after') else 1)
    else:
        import experiments_v28_eval as EV
        EV.run_stage(stage, nproc, extra)
