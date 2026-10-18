"""Traffic tables for the DEFT_LB experiments (Noxim TRAFFIC_TABLE_BASED format).

Line format: src dst pir [por t_on t_off t_period]; pir in packets/cycle.
Every source injects `rate` packets/cycle in total (offered load in
flits/node/cycle = rate * packet_size, packet_size = 8).

Instance: CX x CY chiplets of W x H routers (default 2 x 2 of 4 x 4: 64 chiplet routers,
chiplet c = (y // H) * CX + x // W), C = CX * CY chiplets, N chiplet routers.
Patterns:
  uniform     all other N - 1 routers equally
  localized   40 % to the other routers of the own chiplet, 60 % uniform to other chiplets
  hotspot     3 hotspot routers, at local (1, 1) of chiplets 0, 1 and CX (routers 9, 13, 41
              by default), each receive 10 % of every other source's traffic, rest uniform
  chipperm    chiplet c sends only to chiplet C - 1 - c (default: diagonal pairs 0<->3, 1<->2);
              with an odd C the middle chiplet sends to itself (to its other routers)
  movinghot   phases of T cycles; in phase k, 40 % of every source's traffic goes to hot chiplet
              HOT[k] (uniform over its routers), 60 % uniform; 4 phases repeat. HOT = the four
              corner chiplets 0, CX - 1, C - CX, C - 1 (default 0, 1, 2, 3)
Usage: python3 gen_traffic.py OUTDIR [half] [--chiplets CX CY] [--chiplet-size W H] [--upto RATE]
  half: only the odd multiples of 0.0005 (0.0005, 0.0015, ..., 0.0395), used by the v2
        evaluation for scenarios with a low saturation rate; the 0.001 grid is unchanged.
  --upto RATE: only rates <= RATE (keeps the larger instances' tables small).
  --rates R1,R2,...: write exactly these rates and nothing else (all patterns, or --patterns P1,P2).
"""
import os
import sys

CX, CY, CW, CH = 2, 2, 4, 4
FW = CX * CW
N = 64
C = 4
HOTSPOTS = [9, 13, 41]
HOT = [0, 1, 2, 3]
PHASE_T = 2000          # cycles per phase of movinghot


def set_size(cx, cy, cw, ch):
    global CX, CY, CW, CH, FW, N, C, HOTSPOTS, HOT
    CX, CY, CW, CH = cx, cy, cw, ch
    FW = cx * cw
    N = FW * cy * ch
    C = cx * cy
    HOTSPOTS = [router(c, 1, 1) for c in (0, 1, cx)]
    HOT = [0, cx - 1, C - cx, C - 1]
    assert len(set(HOTSPOTS)) == 3 and len(set(HOT)) == 4, 'size too small for hotspot/movinghot'


def router(c, lx, ly):
    return ((c // CX) * CH + ly) * FW + (c % CX) * CW + lx


def chiplet(r):
    return (r // FW // CH) * CX + (r % FW) // CW


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
    tgt = C - 1 - chiplet(src)
    ds = [d for d in range(N) if chiplet(d) == tgt and d != src]
    return {d: 1.0 / len(ds) for d in ds}


def movinghot_phase(src, k):
    hot = [d for d in range(N) if chiplet(d) == HOT[k] and d != src]
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
    argv = list(sys.argv[1:])
    size = [2, 2, 4, 4]
    for flag, idx in (('--chiplets', 0), ('--chiplet-size', 2)):
        if flag in argv:
            i = argv.index(flag)
            size[idx], size[idx + 1] = int(argv[i + 1]), int(argv[i + 2])
            del argv[i:i + 3]
    upto = 1.0
    if '--upto' in argv:
        i = argv.index('--upto')
        upto = float(argv[i + 1])
        del argv[i:i + 2]
    rates_only = None
    if '--rates' in argv:
        i = argv.index('--rates')
        rates_only = [round(float(x), 4) for x in argv[i + 1].split(',') if x]
        del argv[i:i + 2]
    pats = ['uniform', 'localized', 'hotspot', 'chipperm', 'movinghot']
    if '--patterns' in argv:
        i = argv.index('--patterns')
        pats = argv[i + 1].split(',')
        del argv[i:i + 2]
    set_size(*size)
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    if rates_only is not None:
        for pat in pats:
            for r in rates_only:
                path = os.path.join(out, f'{pat}_{r:.4f}.txt')
                if not os.path.exists(path):
                    write(path, pat, r)
        print('written', len(rates_only), 'rates x', len(pats), 'patterns to', out)
        sys.exit(0)
    if len(argv) > 1 and argv[1] == 'half':
        for pat in ['uniform', 'localized', 'hotspot', 'chipperm', 'movinghot']:
            for i in range(40):
                r = round(0.0005 * (2 * i + 1), 4)
                if r <= upto + 1e-12:
                    write(os.path.join(out, f'{pat}_{r:.4f}.txt'), pat, r)
        print('written 200 half-step tables to', out)
        sys.exit(0)
    rates = [r for r in (round(0.001 * i, 4) for i in range(1, 41)) if r <= upto + 1e-12]   # 0.001 .. 0.040
    for pat in ['uniform', 'localized', 'hotspot', 'chipperm', 'movinghot']:
        for r in rates:
            write(os.path.join(out, f'{pat}_{r:.4f}.txt'), pat, r)
    # all-pairs burst fixture for drain tests (Noxim hardcoded format, -1 ends a cycle)
    with open(os.path.join(out, 'allpairs_burst.txt'), 'w') as f:
        f.write(f'% All-pairs burst: in cycle k (1..{N - 1}) every chiplet router s sends one packet to (s+k) mod {N}.\n')
        for k in range(1, N):
            for s in range(N):
                f.write(f'{s} {(s + k) % N}\n')
            f.write('-1\n')
    print('written', len(rates) * 5, 'tables and allpairs_burst.txt to', out)
