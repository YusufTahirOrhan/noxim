"""v29 Part F: the addenda of results_v29_review/PREREGISTRATION.md with the tuned values, written before any evaluation run of the rows.

  python3 addendum_v29.py            adds "Addendum F1" (the lut_bias of EB_first) and "Addendum F2" (T of EB_best16 and EB_best256), each
                                     only if its choice is in tuning_choice_v29.json and the addendum is not in the file yet
  python3 addendum_v29.py --print    the same text on the screen; the file is not touched

The text is the record of what f1_choose and f2_choose chose by the rule of tuning_v29.md: values, scores, the values run, whether a score is
below 0. Nothing is chosen here. An addendum is refused (exit 1, nothing written) if an evaluation run of its rows exists already: no file
may be in the raw folder of the part and its per-run CSV may not exist. The addenda go in front of the section "Stated in advance", which
the pre-registration says runs to the end of the file. after_c_v29.sh runs this script when chain c has ended and nobody is there.
"""
import csv
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results_v29_review')
RAW = os.path.join(os.path.expanduser('~'), 'lbraw', 'v29')
PRE = os.path.join(RES, 'PREREGISTRATION.md')
CHOICE = os.path.join(RES, 'tuning_choice_v29.json')
V28 = os.path.join(HERE, 'results_v28_anchor', 'tuning_choice_v28.json')
NL = chr(10)
MARK = NL + '---' + NL + NL + '## Stated in advance' + NL
SIZES = ('2x2', '3x3', '4x4')
HEAD = '| row | 2x2 | 3x3 (the 4x4 choice) | 4x4 |'


def g(x):
    return '%g' % x


def runs_of(name):
    """(rows, dead-end events) of a per-run CSV of the tuning."""
    p = os.path.join(RES, name)
    if not os.path.exists(p):
        return 0, 0
    rows = list(csv.DictReader(open(p)))
    return len(rows), sum(int(r.get('dead_ends') or 0) for r in rows)


def no_eval(raw, name):
    return not glob.glob(os.path.join(RAW, raw, '*.json')) and not os.path.exists(os.path.join(RES, name))


def grid_line(ch, row, base, what):
    out = []
    for z in ('2x2', '4x4'):
        gr = ch[z]['grids'][row]
        ext = [x for x in gr if x not in base]
        key = 'D' if row == 'EB_first' else 'T'
        end = ch[z][row][key] == max(gr)
        out.append('%s {%s}%s, chosen %s%s' % (z, ', '.join(g(x) for x in gr), (' (extension: %s)' % ', '.join(g(x) for x in ext)) if ext else '', g(ch[z][row][key]),
                                               ': **the largest value run**' if end else ''))
    return '* Values of %s that were run: %s.' % (what, '; '.join(out))


def below_line(ch, rows, inf):
    b = ['`%s` on %s' % (r, z) for r in rows for z in ('2x2', '4x4') if ch[z][r]['below_zero']]
    if not b:
        return '* No chosen value scores below 0, so the rule for a best member at %s does not apply and no "better of the row and DeFT_P" share is reported.' % inf
    return ('* **Score below 0: %s.** By the rule DeFT_P is then the best member of the family; that is said first where the row is reported, the finite value stays the row, '
            'and every share is also reported for the better of the row and DeFT_P.' % ', '.join(b))


def f1_text(ch, stamp):
    n, dead = runs_of('tune_first_runs.csv')
    c = lambda z, r: ch[z][r]  # noqa: E731
    L = ['---', '', '## Addendum F1 (%s): the tuned `lut_bias` of `EB_first`, frozen before any evaluation run of the row' % stamp,
         'Written by `addendum_v29.py` from `tuning_choice_v29.json`: the choice of `experiments_v29.py f1_choose` by the rule of `tuning_v29.md` ("The rule", committed on',
         '25 November before any tuning run). Tuning runs: %d rows in `tune_first_runs.csv` (seeds 101 and 102: the values of `lut_bias`, DeFT-P and the main row), dead-end' % n,
         'events %d. No evaluation run of `EB_first` existed at this moment (no file in its raw folder, no `early_first_runs.csv`). Scores against DeFT-P in natural-log' % dead,
         'units, higher is better; DeFT_P scores 0.', '', HEAD, '|---|---|---|---|',
         '| `EB_first` | %s |' % ' | '.join('`lut_bias` %s; score %+.4f' % (g(c(z, 'EB_first')['D']), c(z, 'EB_first')['score']) for z in SIZES),
         '| main row (frozen, not tuned) | %s |' % ' | '.join('score %+.4f' % c(z, 'main')['score'] for z in SIZES), '',
         grid_line(ch, 'EB_first', (0, 1, 2, 4, 8), '`lut_bias`'),
         below_line(ch, ['EB_first'], '`lut_bias` = infinity (DeFT_P)')]
    for k in ('repro', 'multi'):
        if k in ch.get('notes', {}):
            L.append('* ' + ch['notes'][k])
    L += ['* The drain tests of `EB_first` are run again with these values before its evaluation (`drain_first_tuned.csv`, `chain_v29c.sh d`); a failure stops the round',
          '  before the evaluation of the row.',
          '* What I had stated in advance: "its tuned `lut_bias` is 2 or 4".', '']
    return L


def f2_text(ch, stamp):
    n, dead = runs_of('tune_age_runs.csv')
    old = json.load(open(V28))
    c = lambda z, r: ch[z][r]  # noqa: E731
    b = lambda z: old[z]['EB_best']  # noqa: E731

    def cell(z, r):
        return 'S %s, P %d, B %s, T %s (`oracle_bias` %s), `oracle_period %s`; score %+.4f' % (
            b(z)['S'], b(z)['P'], g(b(z)['B']), g(c(z, r)['T']), g(b(z)['B'] * c(z, r)['T']), r[7:], c(z, r)['score'])
    L = ['---', '', '## Addendum F2 (%s): the tuned T of `EB_best16` and `EB_best256`, frozen before any evaluation run of the two rows' % stamp,
         'Written by `addendum_v29.py` from `tuning_choice_v29.json`: the choice of `experiments_v29.py f2_choose` by the rule of `tuning_v29.md` (B2 of round 28, unchanged:',
         'S, P and B of `EB_best`, T tuned for each age). Tuning runs: %d rows in `tune_age_runs.csv` (seeds 101 and 102), dead-end events %d. No evaluation run of the two rows' % (n, dead),
         'existed at this moment (no file in their raw folder, no `early_age_runs.csv`). Part F2 is run because the user lifted the limit of 48 h on 25 November',
         '(`DECISIONS.md`, `time_rule.md`); its definition above is unchanged. Scores as in Addendum F1.', '', HEAD, '|---|---|---|---|']
    for r in ('EB_best16', 'EB_best256'):
        L.append('| `%s` | %s |' % (r, ' | '.join(cell(z, r) for z in SIZES)))
    L += ['| for comparison, round 28: `EB_best` (age 0) | %s |' % ' | '.join('T %s; score %+.4f' % (g(old[z]['EB_best']['T']), old[z]['EB_best']['score']) for z in SIZES),
          '| `EB_best64` (age 64) | %s |' % ' | '.join('T %s; score %+.4f' % (g(old[z]['EB_best64']['T']), old[z]['EB_best64']['score']) for z in SIZES),
          '| main row (frozen, not tuned) | %s |' % ' | '.join('score %+.4f' % c(z, 'main')['score'] for z in SIZES), '']
    for r in ('EB_best16', 'EB_best256'):
        L.append(grid_line(ch, r, (0, 2, 4, 8, 16, 32), 'T for `%s`' % r))
    L.append(below_line(ch, ['EB_best16', 'EB_best256'], 'T = infinity (DeFT_P)'))
    if 'multi' in ch.get('notes', {}):
        L.append('* ' + ch['notes']['multi'])
    L += ['* What I had stated in advance: the share of the main row\'s gain falls with the age of the information on every size.', '']
    return L


def main(argv):
    show = '--print' in argv
    if not os.path.exists(CHOICE):
        print('addendum_v29: no tuning_choice_v29.json')
        return 1
    ch = json.load(open(CHOICE))
    text = open(PRE, encoding='utf-8', newline='').read()
    if MARK not in text:
        print('addendum_v29: the section "Stated in advance" is not found in PREREGISTRATION.md; nothing written')
        return 1
    stamp = time.strftime('%d %b %Y, %H:%M').lstrip('0')
    rc, add = 0, []
    if 'EB_first' in ch.get('2x2', {}) and '## Addendum F1' not in text:
        if no_eval('first', 'early_first_runs.csv') or show:
            add += f1_text(ch, stamp)
        else:
            print('addendum_v29: ERROR evaluation runs of EB_first exist already; Addendum F1 is not written')
            rc = 1
    if all(r in ch.get('2x2', {}) for r in ('EB_best16', 'EB_best256')) and '## Addendum F2' not in text:
        if no_eval('age', 'early_age_runs.csv') or show:
            add += f2_text(ch, stamp)
        else:
            print('addendum_v29: ERROR evaluation runs of EB_best16 or EB_best256 exist already; Addendum F2 is not written')
            rc = 1
    if not add:
        print('addendum_v29: nothing to add (F1 in the file: %s, F2 in the file: %s)' % ('## Addendum F1' in text, '## Addendum F2' in text))
        return rc
    block = NL.join(add)
    if show:
        print(block)
        return rc
    i = text.index(MARK)
    new = text[:i] + NL + block.rstrip(NL) + NL + text[i:]
    tmp = PRE + '.tmp'
    open(tmp, 'w', encoding='utf-8', newline='').write(new)
    os.replace(tmp, PRE)
    print('addendum_v29: wrote %s' % ', '.join(x[3:x.index(' (')] for x in add if x.startswith('## Addendum')))
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
