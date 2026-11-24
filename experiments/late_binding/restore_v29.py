"""v29, the time rule after the timing runs (results_v29_review/PREREGISTRATION.md, "Time rule").

  python3 restore_v29.py                          at the end of a part: decide with the clock and the files as they are now
  python3 restore_v29.py --at "2026-11-24 22:30:11" --label "end of B1"
                                                  the same decision for a moment in the past (the end of a part at which nobody ran the
                                                  script): only files that existed at that moment are counted

What the 48 h rule dropped is taken back, in the reverse of the drop order, if it fits: when, at the end of a part, the time since the start
of the timing runs plus the estimate of what is still to run plus the item, at the speed measured until then, is at most 48 h.
  * time since the start: the clock minus the first number of ~/lbraw/v29/b_start.txt (written by chain_v29.sh when the timing runs start);
    a second number in that file is a time in seconds that is not counted (the chain stopped, or processors given to the hardware flow of
    Part E; DECISIONS.md says how it was computed);
  * speed measured until then: that time over the estimate of the runs finished in it (the seconds per run of the timing sets, by kind and
    size, as in runtime_estimate.md); finished runs = the rows of the per-run CSVs that exist and the JSON files of the raw folders;
  * what is still to run: the runs of the kept parts that are not finished, at the seconds per run of their timing set, times that speed;
  * an item: Part F2 as estimated in runtime_estimate.md, times that speed; Part G its limit of 3 h.
The decision reads the clock and counts files; it opens no result. It rewrites drops.json (dropped, restored, time_rule) and appends to
time_rule.md. An error leaves drops.json as it is; the exit code is 0 either way, so a chain goes on with what the rule had kept.
"""
import csv
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v24_eval as EV24  # noqa: E402
import experiments_v29 as X  # noqa: E402
import experiments_v29_eval as EV  # noqa: E402
import experiments_v29_rows as R  # noqa: E402

T0 = os.path.join(X.RAW, 'b_start.txt')
LOG = os.path.join(EV.RES, 'time_rule.md')
KIND = {'b1': 'B', 'b2': 'L', 'c1': 'L', 'c2': 'L', 'c3': 'F', 'd1': 'L', 'd2': 'P', 'e1': 'L'}      # the timing set that estimates a part
NL = chr(10)
SIZES = EV.SIZES


def size_of(name):
    return name.split('__')[2].split('-')[0]


def seconds(counts, kind, per):
    return sum(n * per[(kind, '2x2' if kind == 'P' else z)] for z, n in counts.items())


def zero():
    return {z: 0 for z in SIZES}


def json_names(folder, at):
    out = set()
    for f in glob.glob(os.path.join(folder, '*.json')):
        if os.path.getmtime(f) <= at:
            out.add(os.path.basename(f)[:-5])
    return out


def csv_sizes(path):
    c = zero()
    for r in csv.DictReader(open(path)):
        c[r['pattern'].split('-')[0]] += 1
    return c


def state(per, dropped, at):
    """(seconds, by the estimate, of the runs finished at the moment `at`; seconds, by the estimate, of the runs of the kept parts that are
    not finished; lines for the log)."""
    done = rem = 0.0
    L = []
    for part in ('b1', 'b2', 'c1', 'd2', 'e1', 'c3', 'd1', 'c2'):
        raw, name, jobs, _ = EV.PARTS[part]
        js = [n for n, _ in jobs(d=dropped)]
        path = os.path.join(EV.RES, name)
        if os.path.exists(path) and os.path.getmtime(path) <= at + 5:
            fin = set(js)
        else:
            have = json_names(X.raw(raw), at)
            fin = {n for n in js if n in have}
        cf, cr = zero(), zero()
        for n in js:
            (cf if n in fin else cr)[size_of(n)] += 1
        done += seconds(cf, KIND[part], per)
        rem += seconds(cr, KIND[part], per)
        L.append('%s %d of %d' % (part.upper(), len(fin), len(js)))
    # Part F1: the tuning runs at their grid, then one row on the design of round 28
    row = {z: len(R.ff_scenarios(z)) * 9 * len(EV.SEEDS_28) for z in SIZES}
    path = os.path.join(EV.RES, EV.PARTS['f1'][1])
    if os.path.exists(path) and os.path.getmtime(path) <= at + 5:
        done += seconds(row, 'L', per)
        fin_rows = sum(row.values())
    else:
        have = json_names(X.raw(EV.PARTS['f1'][0]), at)
        cf = zero()
        for n in have:
            cf[size_of(n)] += 1
        done += seconds(cf, 'L', per)
        rem += seconds({z: max(0, row[z] - cf[z]) for z in SIZES}, 'L', per)
        fin_rows = sum(cf.values())
    tune = zero()
    if os.path.exists(EV.CSV1) and os.path.getmtime(EV.CSV1) <= at + 5:
        tune = csv_sizes(EV.CSV1)
    else:
        for n in json_names(X.raw('tune1'), at):
            tune[size_of(n)] += 1
    done += seconds(tune, 'L', per)
    chosen = os.path.exists(R.CHOICE) and os.path.getmtime(R.CHOICE) <= at + 5 and 'EB_first' in json.load(open(R.CHOICE)).get('2x2', {})
    if not chosen:
        rem += seconds({z: max(0, EV.TUNE_F1_RUNS - tune[z]) if z in EV24.TUNE_SIZES else 0 for z in SIZES}, 'L', per)
    L.append('F1 %d of %d rows runs, %d tuning runs' % (fin_rows, sum(row.values()), sum(tune.values())))
    # the tuning and the rows of F2, if they have been taken back and run
    for folder in ('tune2', EV.PARTS['f2'][0]):
        c = zero()
        for n in json_names(X.raw(folder), at):
            c[size_of(n)] += 1
        done += seconds(c, 'L', per)
    return done, rem, L


def decide(D, t0, stopped, at, label):
    per = {tuple(k.split('_')): v['per_run'] for k, v in D['timing'].items()}
    dropped = list(D['dropped'])
    spent = (at - t0 - stopped) / 3600.0
    done, rem, L = state(per, dropped, at)
    scale = (at - t0 - stopped) / done
    rem_h = rem * scale / 3600.0
    lines = ['## %s%s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(at)), ': ' + label if label else ''), '',
             'Time since the start of the timing runs: %.2f h%s. Runs finished in it: %s; by the seconds per run of the timing sets they are %.2f h, so the speed is' % (
                 spent, (' (%.2f h are not counted, `DECISIONS.md`)' % (stopped / 3600.0)) if stopped else '', '; '.join(L), done / 3600.0),
             '%.3f times the estimate. Still to run of the kept parts: %.2f h at this speed. Dropped at this moment: %s.' % (
                 scale, rem_h, ', '.join(EV.DROP_TEXT[x] for x in dropped) if dropped else 'nothing'), '']
    restored, rec = [], []
    full = EV.estimate(per, [])
    for item in [x for x in reversed(EV.DROP_ORDER) if x in dropped]:
        if item == 'G':
            est = EV.G_HOURS
        elif item == 'F2':
            est = full['F2'][0] * scale
        else:                                # an item of Parts C or D: its runs at the speed of now
            kept, without = EV.estimate(per, [x for x in dropped if x != item]), EV.estimate(per, dropped)
            est = sum(kept[k][0] - without[k][0] for k in kept) * scale
        total = spent + rem_h + est
        fits = total <= EV.LIMIT_H
        lines.append('* %s: about %.2f h; %.2f + %.2f + %.2f = %.2f h, %s %.0f h: **%s**.' % (
            EV.DROP_TEXT[item], est, spent, rem_h, est, total, 'within' if fits else 'above', EV.LIMIT_H, 'taken back' if fits else 'stays dropped'))
        rec.append(dict(item=item, estimate_hours=est, spent_hours=spent, remaining_hours=rem_h, scale=scale, fits=fits))
        if not fits:
            break                            # the reverse of the drop order: an item is not taken back before the one dropped after it
        dropped = [x for x in dropped if x != item]
        restored.append(item)
        rem_h += est
    if not rec:
        lines.append('Nothing to decide: nothing is dropped.')
    lines.append('')
    return dropped, restored, lines, rec


def main(argv):
    at, label = None, ''
    if '--at' in argv:
        at = time.mktime(time.strptime(argv[argv.index('--at') + 1], '%Y-%m-%d %H:%M:%S'))
    if '--label' in argv:
        label = argv[argv.index('--label') + 1]
    if not os.path.exists(EV.DROPS):
        print('restore_v29: no drops.json; nothing to do')
        return
    D = json.load(open(EV.DROPS))
    v = open(T0).read().split()
    t0, stopped = float(v[0]), float(v[1]) if len(v) > 1 else 0.0
    dropped, restored, lines, rec = decide(D, t0, stopped, at if at is not None else time.time(), label)
    head = [] if os.path.exists(LOG) else [
        '# v29: the time rule after the timing runs (restore_v29.py)', '',
        'The rule of `PREREGISTRATION.md`: what the 48 h rule dropped is taken back, in the reverse of the drop order, if at the end of a part the time since the',
        'start of the timing runs plus the estimate of what is still to run plus the item, at the speed measured until then, is at most 48 h. Each entry below is',
        'one such moment; it reads the clock and counts finished runs, and opens no result.', '']
    open(LOG, 'a', newline=NL).write(NL.join(head + lines) + NL)
    print(NL.join(lines))
    D['dropped'] = dropped
    D['restored'] = D.get('restored', []) + restored
    D['time_rule'] = D.get('time_rule', []) + [dict(at=at if at is not None else time.time(), label=label, decisions=rec)]
    tmp = EV.DROPS + '.tmp'
    json.dump(D, open(tmp, 'w'), indent=1)
    os.replace(tmp, EV.DROPS)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception as e:      # a chain goes on with what the rule had kept
        print('restore_v29: ERROR %s: %s (drops.json is unchanged)' % (type(e).__name__, e))
    sys.exit(0)
