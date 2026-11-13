"""v26 B5: reachability of MTR and RC under VL faults at four rates (static; results_v26_faults/PREREGISTRATION.md).

The analysis of reach_v10.py (its functions are used unchanged) with the rate 8/16 added:
* rates 1/16, 2/16, 4/16: the masks of reach_v10.py, drawn with random.Random(2210) in its order, so that its numbers must come
  again (checked against results_v10/report/reachability.csv);
* rate 8/16: up to 1,000 masks per size from a random.Random(2611) of its own;
* the 16 masks of Part B per (size, rate), from masks_v26.json.
Reported per (size, rate, mask set) for MTR and RC: the share of inter-chiplet source-destination pairs that can be delivered, mean and
worst case over the masks, and the same over all pairs. For DeFT and the late-binding rows the delivered share comes from the drain
tests (drain_v26.csv), when that file exists.
Usage: python3 reach_v26.py   -> results_v26_faults/reachability_v26.csv, reachability_v26.md
"""
import csv
import hashlib
import json
import math
import os
import random

import experiments_v10 as E10
import experiments_v26 as X
import reach_v10 as R

NL = chr(10)
RATES8 = [(8, 16)]
METHODS = ['MTR', 'RC']


def summarise(size, rate, kind, ms, tables):
    rows = []
    for method in METHODS:
        vals = [R.reach(size, m, method, tables) for m in ms]
        rows.append(dict(size=size, fault_rate='%d/%d' % rate, faulty_vls=len(next(iter(ms))), mask_set=kind, n_masks=len(ms), method=method,
                         mean_inter=sum(v[1] for v in vals) / len(vals), worst_inter=min(v[1] for v in vals), best_inter=max(v[1] for v in vals),
                         masks_all_delivered=sum(1 for v in vals if v[1] == 1.0), mean_all=sum(v[0] for v in vals) / len(vals), worst_all=min(v[0] for v in vals)))
    return rows


def main():
    table = os.path.join(R.R10, 'mtr_config.json')
    assert os.path.samefile(table, E10.MTR_TABLE), 'the MTR runs do not use results_v10/mtr_config.json any more'
    md5 = hashlib.md5(open(table, 'rb').read()).hexdigest()
    tables = R.local_reach(json.load(open(table)))
    rows = []
    rnd10 = random.Random(R.DRAW_SEED)                 # the stream of reach_v10.py: sizes x rates 1/16, 2/16, 4/16
    rnd26 = random.Random(X.MASK_SEED)                 # rate 8/16
    pb = X.part_b()
    for size in R.SIZES:
        nvl = 4 * R.SIZES[size][0] * R.SIZES[size][1]
        sets = []
        for rate in [(1, 16), (2, 16), (4, 16)]:
            sets.append((rate, R.masks(size, int(math.floor(rate[0] * nvl / float(rate[1]))), rnd10)))
        for rate in RATES8:
            sets.append((rate, R.masks(size, int(math.floor(rate[0] * nvl / float(rate[1]))), rnd26)))
        for rate, ms in sets:
            rows += summarise(size, rate, 'random', ms, tables)
            mb = [X.mask_set(e['mask']) for e in pb if e['size'] == size and e['rate'] == '%d/%d' % rate]
            rows += summarise(size, rate, 'Part B', mb, tables)
    # check against reach_v10's own table (the three old rates, the random sets)
    old = {(r['size'], '%.4f' % float(r['fault_rate']), r['method']): r for r in csv.DictReader(open(os.path.join(R.R10, 'report', 'reachability.csv')))}
    same, n = 0, 0
    for r in rows:
        a, b = (int(x) for x in r['fault_rate'].split('/'))
        k = (r['size'], '%.4f' % (a / float(b)), r['method'])
        if r['mask_set'] == 'random' and k in old:
            n += 1
            o = old[k]
            same += (int(o['n_masks']) == r['n_masks'] and o['mean_inter'] == '%.6f' % r['mean_inter'] and o['worst_inter'] == '%.6f' % r['worst_inter'] and
                     o['mean_all'] == '%.6f' % r['mean_all'] and o['worst_all'] == '%.6f' % r['worst_all'])
    cols = list(rows[0])
    with open(os.path.join(X.RES, 'reachability_v26.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator=NL)
        w.writeheader()
        for r in rows:
            w.writerow({k: ('%.6f' % v if isinstance(v, float) else v) for k, v in r.items()})
    L = ['# v26 B5: reachability of MTR and RC under VL faults (reach_v26.py; static analysis, no simulation)', '',
         'The analysis of `reach_v10.py`, unchanged, with the rate 8/16 added. A pair is delivered if a legal path exists under the method: MTR with the turn',
         'restrictions the MTR runs use (`results_v10/mtr_config.json`, md5 %s), a source using any functional boundary router it can reach and a destination' % md5,
         'being entered through any functional boundary router that can reach it; RC with its permission tree, a source using only the RC buffer of its nearest',
         'boundary router. Share = delivered inter-chiplet (source, destination) pairs over all inter-chiplet pairs. Masks: up to 1,000 random masks per (size, rate) with',
         'exactly n faulty VLs and a functional VL in every chiplet (rates 1/16 to 4/16: the masks of `reach_v10.py`; 8/16: `random.Random(%d)`), and the 16 masks of' % X.MASK_SEED,
         'Part B.', '',
         'Check: the %d rows of the three old rates equal `results_v10/report/reachability.csv` (masks, mean and worst share): **%d of %d**.' % (n, same, n), '',
         '## Inter-chiplet pairs delivered: mean (worst mask) over the masks', '',
         '| size | rate | faulty VLs | method | random masks | mean (worst) | masks with every pair delivered | Part B masks: mean (worst) | masks with every pair delivered |',
         '|---|---|---|---|---|---|---|---|---|']
    for size in R.SIZES:
        for rate in ('1/16', '2/16', '4/16', '8/16'):
            for method in METHODS:
                a = [r for r in rows if r['size'] == size and r['fault_rate'] == rate and r['method'] == method and r['mask_set'] == 'random'][0]
                b = [r for r in rows if r['size'] == size and r['fault_rate'] == rate and r['method'] == method and r['mask_set'] == 'Part B'][0]
                L.append('| %s | %s | %d | %s | %d | %.2f %% (%.2f %%) | %d | %.2f %% (%.2f %%) | %d of %d |' % (
                    size, rate, a['faulty_vls'], method, a['n_masks'], 100 * a['mean_inter'], 100 * a['worst_inter'], a['masks_all_delivered'],
                    100 * b['mean_inter'], 100 * b['worst_inter'], b['masks_all_delivered'], b['n_masks']))
    drain = os.path.join(X.RES, 'drain_v26.csv')
    if os.path.exists(drain):
        d = list(csv.DictReader(open(drain)))
        L += ['', '## DeFT and the late-binding rows: the all-pairs drain tests on the 192 masks of Part B (`drain_v26.csv`)', '',
              'One burst with every source-destination pair, simulated until the network is empty. Delivered share = received / injected packets, over all masks of the rate.', '',
              '| row | rate | drain tests | pass | packets injected | delivered | delivered share | dead-end events |', '|---|---|---|---|---|---|---|---|']
        for row in X.ROWS:
            for rate in ('1/16', '2/16', '4/16', '8/16'):
                tag = '-r%s-' % rate.split('/')[0]
                r = [x for x in d if x['variant'] == row + '-p2' and tag in x['size-mask']]
                if not r:
                    continue
                inj, rec = sum(int(x['injected']) for x in r), sum(int(x['received']) for x in r)
                L.append('| %s | %s | %d | %d | %d | %d | %.4f %% | %d |' % (row, rate, len(r), sum(1 for x in r if x['result'] == 'PASS'), inj, rec, 100.0 * rec / inj,
                                                                         sum(int(x['dead_end_events']) for x in r)))
        L += ['', 'All %d drain tests pass: %s. With a functional VL in every chiplet these rows deliver every pair on every mask; MTR and RC lose pairs as soon as a VL fails.' % (
            len(d), 'yes' if all(x['result'] == 'PASS' for x in d) else 'NO')]
    open(os.path.join(X.RES, 'reachability_v26.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L))
    return same == n


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
