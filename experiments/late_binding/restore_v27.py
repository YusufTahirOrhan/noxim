"""v27, the time rule after the timing runs (results_v27_early/PREREGISTRATION.md, addendum; DECISIONS.md, "The time rule on a shared machine").

  python3 restore_v27.py c    when the kept runs of Part C are done: the dropped items of Part C are taken back into the design if they fit
                              into the 30 h, in the reverse of the drop order (seeds 166-170, LB_noVLrep, EB_vl64)
  python3 restore_v27.py e    when Part C is complete: the same for Part E

An item fits if the time since the start of the timing runs plus the time of the item at the speed measured until now is at most 30 h.
The start is the first number in ~/lbraw/v27/c_start.txt (seconds since the epoch, written by chain_v27c.sh); a second number in that file is
the time in seconds during which the chain was stopped and is not counted. The decision reads the clock and the number of finished runs,
no result. It rewrites drops.json (dropped, restored, time_rule) and appends to time_rule.md. An error leaves drops.json as it is; the
exit code is 0 either way, so the chain goes on with what the rule had kept.
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v27 as X  # noqa: E402
import experiments_v27_eval as EV  # noqa: E402

T0 = os.path.join(X.RAW, 'c_start.txt')
LOG = os.path.join(EV.RES, 'time_rule.md')
ORDER_C = ['seeds166_170', 'LB_noVLrep', 'EB_vl64']        # the reverse of the drop order; Part E comes after them
NL = chr(10)


def done_c():
    """Finished runs of Part C: the JSON files of the raw folder, or the rows of eval_runs.csv once it is written."""
    raw = X.raw('eval')
    if os.path.isdir(raw):
        return len(glob.glob(os.path.join(raw, '*.json')))
    f = os.path.join(EV.RES, 'eval_runs.csv')
    return max(0, sum(1 for _ in open(f)) - 1) if os.path.exists(f) else 0


def decide(which, D, t0, stopped, now, n_done):
    """The decision for the items of Part C (which = c) or for Part E (which = e). D = drops.json. Returns (dropped, restored, lines, record)."""
    dropped = list(D['dropped'])
    spent = (now - t0 - stopped) / 3600.0
    # seconds of one run of Part C so far: the time since the start, less the timing set of Part E, over the finished runs of Part C
    sec_c = (now - t0 - stopped - D['timing_seconds_e']) / max(1, n_done)
    lines = ['## %s: %s' % (time.strftime('%Y-%m-%d %H:%M', time.localtime(now)), 'the dropped items of Part C' if which == 'c' else 'Part E'), '',
             'Time since the start of the timing runs: %.2f h%s. Finished runs of Part C: %d, %.1f s each with the processes of the chain (the timing set of Part E' % (
                 spent, (' (%.2f h during which the chain was stopped are not counted)' % (stopped / 3600.0)) if stopped else '', n_done, sec_c),
             'not counted). Dropped by the rule at this moment: %s.' % (', '.join(dropped) if dropped else 'nothing'), '']
    restored, rec = [], []
    if n_done <= 0 or sec_c <= 0:
        lines += ['No finished run of Part C to measure the speed with: nothing is changed.', '']
        return dropped, restored, lines, rec
    todo = [x for x in ORDER_C if x in dropped] if which == 'c' else [x for x in ['part_e'] if x in dropped]
    for item in todo:
        if item == 'part_e':
            n = len(EV.fault_jobs(d=[]))
            per_e, per_c = D['timing_seconds_e'] / D['timing_runs_e'], D['timing_seconds_c'] / D['timing_runs_c']
            est = n * per_e * (sec_c / per_c) / 3600.0       # the timing runs of Part E, scaled by the speed of Part C now against its timing runs
        else:
            rest = [x for x in dropped if x != item]
            n = len(EV.eval_jobs(d=rest)) - len(EV.eval_jobs(d=dropped))
            est = n * sec_c / 3600.0
        fits = spent + est <= EV.LIMIT_H
        lines.append('* `%s`: %d runs, about %.2f h at this speed; %.2f + %.2f = %.2f h, %s %.0f h: **%s**.' % (
            item, n, est, spent, est, spent + est, 'within' if fits else 'above', EV.LIMIT_H, 'taken back and run' if fits else 'stays dropped'))
        rec.append(dict(item=item, runs=n, estimate_hours=est, spent_hours=spent, fits=fits))
        if fits:
            dropped = [x for x in dropped if x != item]
            restored.append(item)
            spent += est
    if not todo:
        lines.append('Nothing to decide: %s.' % ('no item of Part C is dropped' if which == 'c' else 'Part E is not dropped'))
    lines.append('')
    return dropped, restored, lines, rec


def main(which):
    if not os.path.exists(EV.DROPS):
        print('restore_v27: no drops.json; nothing to do')
        return
    D = json.load(open(EV.DROPS))
    if not D['dropped']:
        print('restore_v27 %s: nothing was dropped' % which)
        return
    v = open(T0).read().split()
    t0, stopped = float(v[0]), float(v[1]) if len(v) > 1 else 0.0
    now = time.time()
    dropped, restored, lines, rec = decide(which, D, t0, stopped, now, done_c())
    head = [] if os.path.exists(LOG) else [
        '# v27: the time rule after the timing runs (restore_v27.py)', '',
        'The rule of the addendum of `PREREGISTRATION.md`: what the 30 h rule dropped is run after all, in the reverse of the drop order, if the time since the start of the',
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
    except Exception as e:      # the chain goes on with what the rule had kept
        print('restore_v27: ERROR %s: %s (drops.json is unchanged)' % (type(e).__name__, e))
    sys.exit(0)
