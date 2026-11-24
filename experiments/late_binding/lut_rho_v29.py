"""v29 Part H (ARTIFACT.md): for which masks of the paper do DeFT's tables on 4x4 differ between rho = 0.001 and rho = 0.01?

Every round generates the 4x4 tables with rho = 0.001 and the 2x2 and 3x3 tables with rho = 0.01 (results_v5/tuning_choice.json,
experiments_v23._gen). This script generates the 4x4 table of every mask of the paper again with both values
(other/deft_vl_lut_generator.py --entry-model both), checks that the one with rho = 0.001 has the selections of the table in luts/v23
that the runs used, and counts the entries whose selected VL differs between the two values:
  exit            entries[source router, destination chiplet].source_exit            (DeFT_P, DeFT_B and every row with `exit lut`)
  entry (dst)     entries_by_destination[destination router]                           (DeFT_P: -deft_lut_entry dst)
  entry (src)     entries[source router, destination chiplet].destination_entry      (DeFT_B)
Masks: fault-free, the same VL faulty in every chiplet (the scenarios with faults of round 25), and the 64 masks of round 26.
Usage: python3 lut_rho_v29.py [nproc]   ->  results_v29_review/lut_rho_4x4.md, lut_rho_4x4.csv   (tables under ~/lbraw/v29/lutcmp, deleted)
"""
import csv
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments_v5 as E5  # noqa: E402
import experiments_v23 as X23  # noqa: E402
import experiments_v26 as X26  # noqa: E402
import experiments_v29 as X  # noqa: E402

SIZE = '4x4'
RHOS = ('0.001', '0.01')
WD = os.path.join(X.RAW, 'lutcmp')
NL = chr(10)


def masks():
    out = [('fault-free', E5.FREE[SIZE]), ('one faulty VL per chiplet (round 25)', E5.NORTH[SIZE])]
    for e in X26.part_b():
        if e['size'] == SIZE:
            out.append(('round 26, rate %s, mask %d' % (e['rate'], e['index']), e['mask']))
    return out


def selections(path):
    """({(source router, destination chiplet): exit VL}, {the same key: entry VL by source}, {destination router: entry VL})."""
    ex, es, ed = {}, {}, {}
    sec = sub = None
    key = {}
    for line in open(path):
        s = line.strip()
        if not line.startswith(' '):
            sec = s.rstrip(':') if s.rstrip(':') in ('entries', 'entries_by_destination') else None
            continue
        if sec is None:
            continue
        if s == '- key:':
            key, sub = {}, None
        elif s in ('source_exit:', 'destination_entry:'):
            sub = s.rstrip(':')
        elif ':' in s:
            k, v = s.split(':', 1)
            v = v.strip()
            if k in ('source_router_id', 'destination_chiplet_id', 'destination_router_id'):
                key[k] = int(v)
            elif k == 'selected_vl_id':
                if sec == 'entries':
                    (ex if sub == 'source_exit' else es)[(key['source_router_id'], key['destination_chiplet_id'])] = int(v)
                else:
                    ed[key['destination_router_id']] = int(v)
    return ex, es, ed


def one(arg):
    name, mask = arg
    sel = {}
    for rho in RHOS:
        out = os.path.join(WD, 'lut_%s_%s_rho%s.yaml' % (SIZE, mask, rho))
        if not os.path.exists(out):
            subprocess.run([sys.executable, X23.GEN, '--chiplets-x', '4', '--chiplets-y', '4', '--rho', rho, '--fault-mask', mask, '--entry-model', 'both',
                            '--output', out + '.tmp'], check=True, stdout=subprocess.DEVNULL)
            os.replace(out + '.tmp', out)
        sel[rho] = selections(out)
    used = selections(X23.lut23(SIZE, mask))
    same_as_used = all(a == b for a, b in zip(sel['0.001'], used))
    d = [sum(1 for k in a if a[k] != b[k]) for a, b in zip(sel['0.001'], sel['0.01'])]
    n = [len(a) for a in sel['0.001']]
    for rho in RHOS:
        os.remove(os.path.join(WD, 'lut_%s_%s_rho%s.yaml' % (SIZE, mask, rho)))
    return dict(mask_name=name, mask=mask, rho_0001_equals_table_used=int(same_as_used), exit_entries=n[0], exit_differ=d[0], entry_dst_entries=n[2], entry_dst_differ=d[2],
                entry_src_entries=n[1], entry_src_differ=d[1])


def main(nproc):
    from multiprocessing import Pool
    os.makedirs(WD, exist_ok=True)
    with Pool(nproc) as pool:
        rows = pool.map(one, masks(), chunksize=1)
    shutil.rmtree(WD, ignore_errors=True)
    with open(os.path.join(X.RES, 'lut_rho_4x4.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator=NL)
        w.writeheader()
        w.writerows(rows)
    dp = [r for r in rows if r['exit_differ'] or r['entry_dst_differ']]
    db = [r for r in rows if r['exit_differ'] or r['entry_src_differ']]
    L = ['# DeFT\'s tables on 4x4 with rho = 0.001 and with rho = 0.01 (lut_rho_v29.py; for ARTIFACT.md)', '',
         'Every round uses rho = 0.001 on 4x4 and rho = 0.01 on 2x2 and 3x3 (`results_v5/tuning_choice.json`). For each mask of the paper on 4x4 the table was generated',
         'with both values (`other/deft_vl_lut_generator.py --entry-model both`) and the selected VLs were compared entry by entry. Exit: per source router and',
         'destination chiplet (%d entries; every row with a table-driven exit VL). Entry by destination router (%d entries): DeFT_P. Entry by source router and' % (rows[0]['exit_entries'], rows[0]['entry_dst_entries']),
         'destination chiplet (%d entries): DeFT_B.' % rows[0]['entry_src_entries'], '',
         'The table generated here with rho = 0.001 has the selections of the table in `luts/v23` that the runs used: %d of %d masks.' % (sum(r['rho_0001_equals_table_used'] for r in rows), len(rows)), '',
         '**DeFT_P (exit and entry by destination): the two values give different tables for %d of the %d masks; DeFT_B (exit and entry by source): for %d.**' % (len(dp), len(rows), len(db)), '',
         '| mask | | exit entries that differ | entry (by destination) entries that differ | entry (by source) entries that differ |', '|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %d | %d | %d |' % (r['mask_name'], r['mask'], r['exit_differ'], r['entry_dst_differ'], r['entry_src_differ']))
    open(os.path.join(X.RES, 'lut_rho_4x4.md'), 'w', newline=NL).write(NL.join(L) + NL)
    print(NL.join(L[:12]))
    print('...', len(rows), 'masks')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
