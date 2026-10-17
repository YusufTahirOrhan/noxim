"""Choose frozen parameters from the tuning runs (seeds 101, 102 only).

Criterion: geometric mean of the mean packet latency over every tuning run of a
configuration (4 cells x 2 loads x 2 seeds = 16 runs). Lowest wins.
Usage: python3 choose_tuning.py heur   -> writes heur_w, heur_busy, oracle_beta
       python3 choose_tuning.py ql     -> adds ql_alpha, ql_key, ql_eps
Both write results/tuning_choice.json and results/tuning_<family>.txt.
"""
import collections
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import load_runs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CHOICE = os.path.join(HERE, 'results', 'tuning_choice.json')

FAMILIES = {
    'heur': re.compile(r'^heur_w(?P<heur_w>[\d.]+)_b(?P<heur_busy>[\d.]+)$'),
    'oracle': re.compile(r'^oracle_b(?P<oracle_beta>[\d.]+)$'),
    'ql': re.compile(r'^ql_a(?P<ql_alpha>[\d.]+)_k(?P<ql_key>\d)_e(?P<ql_eps>[\d.]+)$'),
}


def rank(runs, family):
    by = collections.defaultdict(list)
    for r in runs:
        if FAMILIES[family].match(r['variant']):
            by[r['variant']].append(r)
    table = []
    for name, rs in by.items():
        gm = math.exp(sum(math.log(r['latency']) for r in rs) / len(rs))
        table.append((gm, name, len(rs), sum(r['dead_ends'] for r in rs)))
    table.sort()
    return table


def params(family, name):
    p = FAMILIES[family].match(name).groupdict()
    return {k: (int(v) if k == 'ql_key' else float(v)) for k, v in p.items()}


if __name__ == '__main__':
    stage = sys.argv[1]
    runs = load_runs('tune')
    choice = json.load(open(CHOICE)) if os.path.exists(CHOICE) else {}
    for family in (('heur', 'oracle') if stage == 'heur' else ('ql',)):
        table = rank(runs, family)
        lines = [f'# {family}: geometric mean latency over tuning runs (seeds 101, 102)',
                 f'{"config":<24} {"runs":>4} {"geo_mean_latency":>17} {"dead_ends":>9}']
        lines += [f'{n:<24} {k:>4} {gm:>17.2f} {d:>9}' for gm, n, k, d in table]
        lines.append(f'chosen: {table[0][1]} ({len(table)} configurations, {sum(t[2] for t in table)} runs)')
        open(os.path.join(HERE, 'results', f'tuning_{family}.txt'), 'w').write('\n'.join(lines) + '\n')
        print('\n'.join(lines))
        choice.update(params(family, table[0][1]))
    json.dump(choice, open(CHOICE, 'w'), indent=2)
    print('tuning_choice.json:', choice)
