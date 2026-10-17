"""Variant definitions shared by the drain tests, tuning and evaluation runs.

Each variant is a list of Noxim arguments (routing, policies, selection).
Direction A: injection-time VL choice (DeFT relation, fixed pair).
Direction B: late binding + Q-learning selection (DEFT_QL).
Direction C: late binding + stateless local heuristic (DEFT_HEUR).
Controls: late binding + RANDOM selection (adaptivity without information).
Scopes: FULL = exit and entry late (odd-even on chiplets and interposer);
        CI   = exit fixed by the DeFT table, entry late on the interposer (odd-even).
"""

FULL = ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'late', '-deft_lb', 'entry', 'late',
        '-deft_lb', 'chip_tm', 'OE', '-deft_lb', 'ipos_tm', 'OE']
CI = ['-routing', 'DEFT_LB', '-deft_lb', 'exit', 'lut', '-deft_lb', 'entry', 'late',
      '-deft_lb', 'chip_tm', 'XY', '-deft_lb', 'ipos_tm', 'OE']


def inj(policy):
    return ['-routing', 'DEFT_LB', '-deft_lb', 'exit', policy, '-deft_lb', 'entry', policy]


def kv(**params):
    out = []
    for k, v in params.items():
        out += ['-deft_lb', k, str(v)]
    return out


# Frozen parameters, chosen on tuning seeds 101, 102 (results/tuning_choice.json,
# results/tuning_heur.txt, tuning_oracle.txt, tuning_ql.txt; budget in README).
HEUR = kv(heur_w=1.0, heur_busy=0.0)
QL = kv(ql_w=1.0, ql_busy=0.0, ql_alpha=0.05, ql_key=1, ql_eps=0.0)

VARIANTS = {
    'DeFT':        ['-routing', 'DEFT'],
    'A_mindist':   inj('mindist'),
    'A_random':    inj('random'),
    'A_oracle':    inj('oracle') + kv(oracle_beta=0.5),
    'CI_random':   CI + ['-sel', 'RANDOM'],
    'CI_heur':     CI + ['-sel', 'DEFT_HEUR'] + HEUR,
    'CI_ql':       CI + ['-sel', 'DEFT_QL'] + QL,
    'FULL_random': FULL + ['-sel', 'RANDOM'],
    'FULL_heur':   FULL + ['-sel', 'DEFT_HEUR'] + HEUR,
    'FULL_heurLA': FULL + ['-sel', 'DEFT_HEUR'] + HEUR + kv(heur_lookahead=1),
    'FULL_ql':     FULL + ['-sel', 'DEFT_QL'] + QL,
}
