"""Traffic tables for the DEFT_LB experiments (Noxim TRAFFIC_TABLE_BASED format).

Line format: src dst pir [por t_on t_off t_period]; pir in packets/cycle.
Every source injects `rate` packets/cycle in total (offered load in
flits/node/cycle = rate * packet_size, packet_size = 8).

Patterns (64 chiplet routers, 4 chiplets of 4x4, chiplet c = (y//4)*2 + x//4):
  uniform     all other 63 routers equally
  localized   40 % to the 15 other routers of the own chiplet, 60 % uniform to other chiplets
  hotspot     routers 9, 13, 41 each receive 10 % of every other source's traffic, rest uniform
  chipperm    100 % inter-chiplet; chiplet c sends only to chiplet 3-c (diagonal pairs 0<->3, 1<->2)
  movinghot   phases of T cycles; in phase k, 40 % of every source's traffic goes to chiplet k
              (uniform over its 16 routers), 60 % uniform; 4 phases repeat
Usage: python3 gen_traffic.py OUTDIR
"""
import os
import sys

N = 64
HOTSPOTS = [9, 13, 41]
PHASE_T = 2000          # cycles per phase of movinghot


def chiplet(r):
    return (r // 8 // 4) * 2 + (r % 8) // 4


def uniform(src):
    return {d: 1.0 / (N - 1) for d in range(N) if d != src}


def localized(src):
    same = [d for d in range(N) if d != src and chiplet(d) == chiplet(src)]
    other = [d for d in range(N) if chiplet(d) != chiplet(src)]
    w = {d: 0.4 / len(same) for d in same}
    w.update({d: 0.6 / len(other) for d in other})
    return w


def hotspot(src):
    hs = [h for h in HOTSPOTS if h != src]
    w = {h: 0.10 for h in hs}
    rest = [d for d in range(N) if d != src and d not in hs]
    for d in rest:
        w[d] = (1.0 - 0.10 * len(hs)) / len(rest)
    return w


def chipperm(src):
    tgt = 3 - chiplet(src)
    ds = [d for d in range(N) if chiplet(d) == tgt]
    return {d: 1.0 / len(ds) for d in ds}


def movinghot_phase(src, k):
    hot = [d for d in range(N) if chiplet(d) == k and d != src]
    w = {d: 0.4 / len(hot) for d in hot}
    rest = [d for d in range(N) if d != src]
    for d in rest:
        w[d] = w.get(d, 0.0) + 0.6 / len(rest)
    return w


def write(path, pattern, rate):
    with open(path, 'w') as f:
        f.write(f'% DEFT_LB traffic: pattern={pattern} rate={rate} packets/cycle/source\n')
        for s in range(N):
            if pattern == 'movinghot':
                # Noxim activates a line when t_on < (cycle % t_period) < t_off and
                # requires t_period > t_off; phase k covers cycles [kT, (k+1)T) mod 4T
                # (one-cycle gaps at 0 and 4T-1 are negligible).
                period = 4 * PHASE_T
                for k in range(4):
                    t_on = 0 if k == 0 else k * PHASE_T - 1
                    t_off = period - 1 if k == 3 else (k + 1) * PHASE_T
                    for d, p in sorted(movinghot_phase(s, k).items()):
                        f.write(f'{s} {d} {rate * p:.9f} {rate * p:.9f} {t_on} {t_off} {period}\n')
            else:
                w = globals()[pattern](s)
                for d, p in sorted(w.items()):
                    f.write(f'{s} {d} {rate * p:.9f}\n')


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    rates = [round(0.001 * i, 4) for i in range(1, 41)]   # 0.001 .. 0.040 packets/cycle
    for pat in ['uniform', 'localized', 'hotspot', 'chipperm', 'movinghot']:
        for r in rates:
            write(os.path.join(out, f'{pat}_{r:.4f}.txt'), pat, r)
    # all-pairs burst fixture for drain tests (Noxim hardcoded format, -1 ends a cycle)
    with open(os.path.join(out, 'allpairs_burst.txt'), 'w') as f:
        f.write('% All-pairs burst: in cycle k (1..63) every chiplet router s sends one packet to (s+k) mod 64.\n')
        for k in range(1, 64):
            for s in range(N):
                f.write(f'{s} {(s + k) % N}\n')
            f.write('-1\n')
    print('written', len(rates) * 5, 'tables and allpairs_burst.txt to', out)
