"""Secondary sensitivity for v4 (not pre-registered): saturation throughput without chipperm.

Same statistic as the primary THR test, over the 6 non-chipperm scenarios of each size.
Usage: python3 sensitivity_v4.py   -> results_v4/report/sensitivity_thr_no_chipperm.txt
"""
import os

import report_v4 as R

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    runs = R.load_csv(os.path.join(HERE, 'results_v4', 'eval_runs.csv'))
    lines = ['# Secondary sensitivity (not pre-registered): THR without the chipperm scenario',
             '(mean over the 6 other scenarios of each size; unadjusted; not a significance claim)', '']
    for z in R.SIZES:
        d = R.Data(runs, R.scen(z), R.ladder, range(1, 11))
        sc = [s for s in R.scen(z) if 'chipperm' not in s[0]]
        for a, b in R.PRIMARY:
            xs = d.per_seed(a, b, 'THR', sc)
            e, lo, hi = R.pct(xs)
            lines.append(f'{z} {a} vs {b}: {e:+.2f} % [{lo:+.2f}, {hi:+.2f}]  p (unadjusted) = {R.ttest(xs):.2g}')
    out = os.path.join(HERE, 'results_v4', 'report', 'sensitivity_thr_no_chipperm.txt')
    open(out, 'w', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
