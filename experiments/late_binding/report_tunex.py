"""Exploratory CI tuning beyond the v2 grid edges (results_v3/tuning_explore.md).

Criterion as in v2: geometric mean of the mean latency over the 16 tuning runs (4 cells x 2
loads x seeds 101, 102). Configurations shared with v2 (heur w2/b0, w2/b4, CI_ql alpha 0.005)
are compared run by run with the v2 tuning outputs (determinism check).
Usage: python3 report_tunex.py
"""
import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def runs(d):
    out = {}
    for f in glob.glob(os.path.join(HERE, d, '*.json')):
        parts = os.path.basename(f)[:-5].split('__')
        out[(parts[1],) + tuple(parts[2:])] = json.load(open(f))['summary']['global_average_delay_cycles']
    return out


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def table(r):
    by = {}
    for k, v in r.items():
        by.setdefault(k[0], []).append(v)
    return {n: (gm(v), len(v)) for n, v in by.items()}


def main():
    r3, r2 = runs('results_v3/tunex_raw'), runs('results_v2/tune_raw')
    t3, t2 = table(r3), table(r2)
    shared = [k for k in r3 if k in r2]
    same = sum(1 for k in shared if r3[k] == r2[k])
    L = ['# Exploratory CI tuning beyond the v2 grid edges (secondary; seeds 101, 102; not used in v3 runs)', '',
         'Criterion as in v2: geometric-mean latency over 16 tuning runs per configuration (lower is better).',
         f'Determinism check: {same} of {len(shared)} runs shared with the v2 tuning are identical.', '']
    for fam, title, v2best in (('CI-heur-', 'CI heuristic: w {2, 4, 8} x busy {0, 4}', 'CI-heur-w2.0-b0.0'),
                               ('CI-ql-', 'CI_ql: alpha {0.001, 0.002, 0.005}, key = chiplet, w/busy = 2/0', 'CI-ql-a0.005-k1')):
        rows = sorted((v[0], n, v[1]) for n, v in t3.items() if n.startswith(fam))
        L += [f'## {title}', '', '| config | runs | geo-mean latency | vs v2 choice |', '|---|---|---|---|']
        ref = t3[v2best][0]
        for g, n, k in rows:
            L.append(f'| {n}{" (v2 choice)" if n == v2best else ""} | {k} | {g:.2f} | {100 * (g / ref - 1):+.2f} % |')
        best = rows[0]
        v2_grid = {n: v for n, v in t2.items() if n.startswith(fam)}
        L += ['', f'Best: {best[1]} ({best[0]:.2f}). v2 choice: {v2best} ({ref:.2f}); '
                  f'change of the criterion: {100 * (best[0] / ref - 1):+.2f} %. '
                  f'The optimum {"moves" if best[1] != v2best else "does not move"}.',
              f'(v2 grid for reference: best {min(v2_grid.items(), key=lambda x: x[1][0])[0]} '
              f'{min(v[0] for v in v2_grid.values()):.2f}.)', '']
    L += ['Tuning differences of a few per cent on 2 seeds are within the seed-to-seed noise seen in v2 '
          '(e.g. non-monotone alpha rankings), so a moved optimum is weak evidence on its own.']
    out = os.path.join(HERE, 'results_v3', 'tuning_explore.md')
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
