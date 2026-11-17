"""v28, the time rule after the timing runs (results_v28_anchor/PREREGISTRATION.md, "Time rule").

  python3 restore_v28.py c    when the kept runs of Part C are done: seeds 176-180 of EB_best64 in Part C, if dropped
  python3 restore_v28.py d    when Part C is complete: the dropped items of Part D (rate 1/16, EB_best64, the anchor rows), in that order
  python3 restore_v28.py e    when Part D is complete: rates 1/16 and 2/16 of Part E, if dropped

Every item is taken back in the reverse of the drop order if it fits: if the time since the start of the timing runs plus the time of the
item is at most 30 h. The time of an item = its runs x the seconds per run its part needed in the timing runs, scaled by the speed of Part C
now against its timing runs. The start is the first number in ~/lbraw/v28/c_start.txt (seconds since the epoch, written by chain_v28c.sh); a
second number in that file is the time in seconds during which the chain was stopped and is not counted. The decision reads the clock and
the number of finished runs, no result. It rewrites drops.json (dropped, restored, time_rule) and appends to time_rule.md. An error leaves
drops.json as it is; the exit code is 0 either way, so the chain goes on with what the rule had kept.
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v28 as X  # noqa: E402
import experiments_v28_eval as EV  # noqa: E402

T0 = os.path.join(X.RAW, 'c_start.txt')
LOG = os.path.join(EV.RES, 'time_rule.md')
ITEMS = {'c': ['C_EB_best64_seeds176_180'], 'd': ['D_rate_1_16', 'D_EB_best64', 'D_anchors'], 'e': ['E_rates_1_2']}   # reverse of the drop order
NL = chr(10)


def done_c():
    """Finished runs of Part C: the JSON files of the raw folder, or the rows of eval_runs.csv once it is written."""
    raw = X.raw('eval')
    if os.path.isdir(raw):
        return len(glob.glob(os.path.join(raw, '*.json')))
    f = os.path.join(EV.RES, 'eval_runs.csv')
    return max(0, sum(1 for _ in open(f)) - 1) if os.path.exists(f) else 0


def runs_of(item, dropped):
    rest = [x for x in dropped if x != item]
    fn = {'C': EV.eval_jobs, 'D': EV.d_jobs, 'E': EV.e_jobs}[item[0]]
    return item[0], len(fn(d=rest)) - len(fn(d=dropped))


def decide(which, D, t0, stopped, now, n_done):
    dropped = list(D['dropped'])
    spent = (now - t0 - stopped) / 3600.0
    tm = D['timing']
    # seconds of one run of Part C so far: the time since the start, less the timing sets of Parts D and E, over the finished runs of Part C
    sec_c = (now - t0 - stopped - tm['D']['seconds'] - tm['E']['seconds']) / max(1, n_done)
    scale = sec_c / tm['C']['per_run']
    lines = ['## %s: the dropped items of %s' % (time.strftime('%Y-%m-%d %H:%M', time.localtime(now)), {'c': 'Part C', 'd': 'Part D', 'e': 'Part E'}[which]), '',
             'Time since the start of the timing runs: %.2f h%s. Finished runs of Part C: %d, %.1f s each with the processes of the chain (%.2f times its timing runs).' % (
                 spent, (' (%.2f h during which the chain was stopped are not counted)' % (stopped / 3600.0)) if stopped else '', n_done, sec_c, scale),
             'Dropped by the rule at this moment: %s.' % (', '.join(dropped) if dropped else 'nothing'), '']
    restored, rec = [], []
    todo = [x for x in ITEMS[which] if x in dropped]
    if todo and (n_done <= 0 or sec_c <= 0):
        lines += ['No finished run of Part C to measure the speed with: nothing is changed.', '']
        return dropped, restored, lines, rec
    for item in todo:
        part, n = runs_of(item, dropped)
        est = n * tm[part]['per_run'] * scale / 3600.0
        fits = spent + est <= EV.LIMIT_H
        lines.append('* `%s`: %d runs, about %.2f h at this speed; %.2f + %.2f = %.2f h, %s %.0f h: **%s**.' % (
            item, n, est, spent, est, spent + est, 'within' if fits else 'above', EV.LIMIT_H, 'taken back and run' if fits else 'stays dropped'))
        rec.append(dict(item=item, runs=n, estimate_hours=est, spent_hours=spent, fits=fits))
        if fits:
            dropped = [x for x in dropped if x != item]
            restored.append(item)
            spent += est
    if not todo:
        lines.append('Nothing to decide: no item of this part is dropped.')
    lines.append('')
    return dropped, restored, lines, rec


def main(which):
    if which not in ITEMS:
        raise SystemExit(__doc__)
    if not os.path.exists(EV.DROPS):
        print('restore_v28: no drops.json; nothing to do')
        return
    D = json.load(open(EV.DROPS))
    if not D['dropped']:
        print('restore_v28 %s: nothing was dropped' % which)
        return
    v = open(T0).read().split()
    t0, stopped = float(v[0]), float(v[1]) if len(v) > 1 else 0.0
    now = time.time()
    dropped, restored, lines, rec = decide(which, D, t0, stopped, now, done_c())
    head = [] if os.path.exists(LOG) else [
        '# v28: the time rule after the timing runs (restore_v28.py)', '',
        'The rule of `PREREGISTRATION.md`: what the 30 h rule dropped is run after all, in the reverse of the drop order, if the time since the start of the',
        'timing runs plus the time of the item at the speed measured until then is at most 30 h. The decisions below read the clock and the number of finished runs only.', '']
    open(LOG, 'a', newline=NL).write(NL.join(head + lines) + NL)
    print(NL.join(lines))
    D['dropped'] = dropped
    D['restored'] = D.get('restored', []) + restored
    D['time_rule'] = D.get('time_rule', []) + [dict(which=which, at=now, decisions=rec)]
    tmp = EV.DROPS + '.tmp'
    json.dump(D, open(tmp, 'w'), indent=1)
    os.replace(tmp, EV.DROPS)


if __name__ == '__main__':
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else '')
    except SystemExit:
        raise
    except Exception as e:      # the chain goes on with what the rule had kept
        print('restore_v28: ERROR %s: %s (drops.json is unchanged)' % (type(e).__name__, e))
    sys.exit(0)
