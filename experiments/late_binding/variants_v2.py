"""Variant definitions for the second evaluation (results_v2/).

Differences from variants.py:
  * DeFT_tm: DeFT routing with the LUT generated from the demand matrix of the
    traffic pattern being run (other/deft_vl_lut_generator.py --demand-table);
    uniform uses the default LUT. DeFT itself always uses the default LUT.
  * CI_heurLA, CI_qlLA, FULL_qlLA: lookahead heuristic on CI, and the
    information-matched learner (ql_lookahead 1) on both scopes.
  * Parameters are tuned per scope (CI and FULL separately) on seeds 101, 102;
    the frozen values below are written by experiments_v2.py tune stages
    (results_v2/tuning_choice.json) and FROZEN is set once tuning is done.
  * CI variants take their exit VL from the default (uniform) LUT, as in v1.
"""
import os

from variants import CI, FULL, inj, kv

HERE = os.path.dirname(os.path.abspath(__file__))
LUT_DIR = os.path.join(HERE, 'luts')
TM_PATTERNS = ('localized', 'hotspot', 'chipperm', 'movinghot')

FROZEN = False

# Per-scope frozen parameters (placeholders until tuning; see FROZEN).
PARAMS = {
    'CI': dict(heur_w=1.0, heur_busy=0.0, heurLA_w=1.0, heurLA_busy=0.0,
               ql_alpha=0.05, ql_key=1, qlLA_alpha=0.05, qlLA_key=1),
    'FULL': dict(heur_w=1.0, heur_busy=0.0, heurLA_w=1.0, heurLA_busy=0.0,
                 ql_alpha=0.05, ql_key=1, qlLA_alpha=0.05, qlLA_key=1),
}
ORACLE_BETA = 0.5   # v1 tuning (seeds 101, 102); not re-tuned


def heur(w, busy, lookahead=0):
    return ['-sel', 'DEFT_HEUR'] + kv(heur_w=w, heur_busy=busy) + (kv(heur_lookahead=1) if lookahead else [])


def ql(w, busy, alpha, key, lookahead=0):
    # local weights equal to the heuristic of the same information budget, eps = 0
    return ['-sel', 'DEFT_QL'] + kv(ql_w=w, ql_busy=busy, ql_alpha=alpha, ql_key=key, ql_eps=0.0) + \
        (kv(ql_lookahead=1) if lookahead else [])


def scope_variants(scope, base, p):
    return {
        f'{scope}_heur': base + heur(p['heur_w'], p['heur_busy']),
        f'{scope}_heurLA': base + heur(p['heurLA_w'], p['heurLA_busy'], 1),
        f'{scope}_ql': base + ql(p['heur_w'], p['heur_busy'], p['ql_alpha'], p['ql_key']),
        f'{scope}_qlLA': base + ql(p['heurLA_w'], p['heurLA_busy'], p['qlLA_alpha'], p['qlLA_key'], 1),
    }


def build():
    v = {
        'DeFT': ['-routing', 'DEFT'],
        'DeFT_tm': ['-routing', 'DEFT'],
        'A_oracle': inj('oracle') + kv(oracle_beta=ORACLE_BETA),
    }
    v.update(scope_variants('CI', CI, PARAMS['CI']))
    v.update(scope_variants('FULL', FULL, PARAMS['FULL']))
    return v


VARIANTS = build()


def lut_for(variant, pattern):
    """LUT file for a run (None = runner default, the uniform LUT)."""
    if variant == 'DeFT_tm' and pattern in TM_PATTERNS:
        return os.path.join(LUT_DIR, f'lut_rho001_tm_{pattern}.yaml')
    return None
