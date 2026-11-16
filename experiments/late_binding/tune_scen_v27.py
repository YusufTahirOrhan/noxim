"""v27 Part B, descriptive: the tuning runs by scenario (tuning seeds 101 and 102 only; no run of Parts C and E is read).

  python3 tune_scen_v27.py      results_v27_early/tune_runs.csv, tuning_choice_v27.json -> results_v27_early/tuning_by_scenario_v27.md

The rule of the tuning scores a value by its mean over the five tuning scenarios (tuning_v27.md). This file shows the five scenarios
one by one: the chosen values next to the main row, and the score of every value of the grid in every scenario. It changes no choice.
"""
import csv
import json
import math
import os
from collections import defaultdict

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results_v27_early')
MAIN, TUNED, SIZES, SEEDS = 'CI_heurLA_X_LF', ['EB_vl', 'EB_route', 'EB_vl64'], ['2x2', '4x4'], (101, 102)
ORDER = ['uniform', 'hotspot', 'chipperm', 'chiptrans']
NL = chr(10)


def num(x):
    return float(x) if x not in ('', None) else None


def load():
    R = defaultdict(dict)       # (row, size, pattern, mask, seed) -> {rate: row of the CSV}
    for r in csv.DictReader(open(os.path.join(RES, 'tune_runs.csv'))):
        z, p = r['pattern'].split('-')
        R[(r['variant'][:-3], z, p, r['mask'], int(r['seed']))][float(r['rate'])] = r
    return R


def terms(R, row, z, p, m):
    """Mean over the two seeds of ln(THR / THR_P), ln(LAT1.0 / LAT1.0_P), ln(LAT0.5 / LAT0.5_P); None if a run is missing."""
    t, l1, l5 = [], [], []
    for s in SEEDS:
        a, b = R.get((row, z, p, m, s), {}), R.get(('DeFT_P', z, p, m, s), {})
        ra = sorted(a)
        if len(ra) != 4 or ra != sorted(b):
            return None
        t.append(math.log(max(num(a[x]['accepted']) for x in ra) / max(num(b[x]['accepted']) for x in ra)))
        l1.append(math.log(num(a[ra[1]]['latency']) / num(b[ra[1]]['latency'])))
        l5.append(math.log(num(a[ra[0]]['latency']) / num(b[ra[0]]['latency'])))
    n = float(len(t))
    return sum(t) / n, sum(l1) / n, sum(l5) / n


def at_sat(R, row, z, p, m, f):
    """Mean over the two seeds of f(run at 1.0 x Lsat); None if f gives None."""
    v = []
    for s in SEEDS:
        a = R[(row, z, p, m, s)]
        x = f(a[sorted(a)[1]])
        if x is None:
            return None
        v.append(x)
    return sum(v) / len(v)


def pct(x):
    return 100.0 * (math.exp(x) - 1.0)


def cell(x, f='%.2f'):
    return '' if x is None else f % x


def main():
    R = load()
    C = json.load(open(os.path.join(RES, 'tuning_choice_v27.json')))
    grid = sorted({float(k[0].split('_b')[1]) for k in R if '_b' in k[0]})
    L = ['# v27 Part B: the tuning runs by scenario (tune_scen_v27.py; descriptive)', '',
         'From `tune_runs.csv` (seeds 101 and 102; two seeds per cell, so every number here is a pointer and no more). The rule of the tuning (`tuning_v27.md`) scores a',
         'value by its mean over the five tuning scenarios; nothing here changes a choice. THR, LAT1.0 and LAT0.5 are percentages against DeFT-P on the same seeds',
         '(100 x (exp(mean ln ratio) - 1)); score = ln THR ratio - ln LAT1.0 ratio - ln LAT0.5 ratio, in natural-log units.', '',
         '## The chosen values next to the main row', '',
         'The last four columns are means of the two runs at 1.0 x Lsat: the largest share of a chiplet\'s Up moves on one entry VL over the mean share (`vl_imbalance`;',
         'DeFT-P\'s value in brackets), head-flit forwards per delivered packet, the share of the Up moves on a VL that is not DeFT-P\'s entry VL, and the age of the',
         'choice at the Up move (mean time since generation at the Up move less the mean wait at the source; for the main row the time the packet has travelled).', '']
    for z in SIZES:
        scen = sorted({(k[2], k[3]) for k in R if k[1] == z}, key=lambda x: (ORDER.index(x[0]), x[1]))
        rows = [(MAIN, MAIN, 'frozen')] + [(r, '%s_b%g' % (r, C[z][r]['beta']), '%g' % C[z][r]['beta']) for r in TUNED]
        L += ['### %s' % z, '', '| scenario | row | oracle_beta | score | THR | LAT1.0 | LAT0.5 | vl_imbalance | hops per packet | not DeFT-P\'s VL | age at Up (cycles) |', '|---|---|---|---|---|---|---|---|---|---|---|']
        for p, m in scen:
            name = p + (', one faulty VL per chiplet' if int(m, 16) else '')
            imb_p = at_sat(R, 'DeFT_P', z, p, m, lambda x: num(x['vl_imbalance']))
            for label, cfg, beta in rows:
                t = terms(R, cfg, z, p, m)
                imb = at_sat(R, cfg, z, p, m, lambda x: num(x['vl_imbalance']))
                hop = at_sat(R, cfg, z, p, m, lambda x: (num(x['hops_chip']) + num(x['hops_ipos'])) / num(x['packets_measured']) if num(x['packets_measured']) else None)
                nd = at_sat(R, cfg, z, p, m, lambda x: num(x['entry_up_not_default']) / num(x['entry_up_moves']) if num(x['entry_up_moves']) else None)
                age = at_sat(R, cfg, z, p, m, lambda x: num(x['entry_up_age_mean']) - num(x['entry_inj_wait_mean']) if num(x['entry_up_age_mean']) is not None and num(x['entry_inj_wait_mean']) is not None else None)
                L.append('| %s | `%s` | %s | %+.3f | %+.1f %% | %+.1f %% | %+.1f %% | %s (%s) | %s | %s | %s |' % (
                    name, label, beta, t[0] - t[1] - t[2], pct(t[0]), pct(t[1]), pct(t[2]), cell(imb), cell(imb_p), cell(hop), cell(None if nd is None else 100 * nd, '%.0f %%'), cell(age, '%.0f')))
        L.append('')
    L += ['## The score of every value in every scenario', '',
          'One line per row and scenario; the largest score of the line is in bold. The last column is the value the rule chose for the row on that size (the largest mean',
          'over the five scenarios).', '']
    for z in SIZES:
        scen = sorted({(k[2], k[3]) for k in R if k[1] == z}, key=lambda x: (ORDER.index(x[0]), x[1]))
        L += ['### %s' % z, '', '| row | scenario | main row | %s | chosen |' % ' | '.join('%g' % b for b in grid), '|---|---|---|' + '---|' * len(grid) + '---|']
        for r in TUNED:
            for p, m in scen:
                name = p + (', one faulty VL per chiplet' if int(m, 16) else '')
                tm = terms(R, MAIN, z, p, m)
                sc = {}
                for b in grid:
                    t = terms(R, '%s_b%g' % (r, b), z, p, m)
                    sc[b] = None if t is None else t[0] - t[1] - t[2]
                best = max((b for b in grid if sc[b] is not None), key=lambda b: sc[b])
                L.append('| `%s` | %s | %+.3f | %s | %g |' % (r, name, tm[0] - tm[1] - tm[2], ' | '.join(
                    '' if sc[b] is None else ('**%+.3f**' if b == best else '%+.3f') % sc[b] for b in grid), C[z][r]['beta']))
        L.append('')
    open(os.path.join(RES, 'tuning_by_scenario_v27.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))


if __name__ == '__main__':
    main()
