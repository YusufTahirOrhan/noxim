"""Merge per-shard per-run CSVs (same columns) into one file (v10, runner --shard).

Rows are keyed by (variant, pattern, mask, rate, seed) when those columns exist, otherwise by the whole row.
Identical duplicates are kept once; conflicting duplicates (same key, different values) abort the merge.
Usage: python3 merge_csv.py OUT.csv IN1.csv IN2.csv [...]
"""
import csv
import sys

KEY = ['variant', 'pattern', 'mask', 'rate', 'seed']


def main():
    out, ins = sys.argv[1], sys.argv[2:]
    header, rows = None, {}
    for path in ins:
        with open(path, newline='') as f:
            r = csv.DictReader(f)
            if header is None:
                header = r.fieldnames
            elif r.fieldnames != header:
                raise SystemExit(f'{path}: columns differ from {ins[0]}')
            key_cols = [c for c in KEY if c in header] if all(c in header for c in KEY) else header
            for row in r:
                k = tuple(row[c] for c in key_cols)
                if k in rows and rows[k] != row:
                    raise SystemExit(f'conflicting rows for {k} ({path})')
                rows[k] = row
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator='\n')
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])
    print(f'{out}: {len(rows)} rows from {len(ins)} files')


if __name__ == '__main__':
    main()
