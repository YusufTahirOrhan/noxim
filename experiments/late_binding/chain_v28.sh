#!/bin/bash
# v28 (results_v28_anchor/PREREGISTRATION.md), unattended, in three parts (the third in chain_v28c.sh):
#   detach.sh v28a bash chain_v28.sh a     the gates: the anchors, v27 reproduced, the unit checks, the drain tests of the new rows, and the
#                                          reuse check of the rows of round 26 (Parts D and E); a failed gate stops the chain
#   detach.sh v28b bash chain_v28.sh b     after the pre-registration: the tuning (B1, B3, then B2), its choice, the drain tests of the tuned rows
#   detach.sh v28c bash chain_v28c.sh      after the addendum with the chosen configurations: the timing runs, Parts C, D and E
# The run stages take their number of processes from ~/lbraw/v28/width.txt at every batch of runs (experiments_v28.width).
# Resumable: finished stages and finished runs are skipped (the tuning keeps its state in ~/lbraw/v28/tune_state.json).
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local R=$HOME/lbraw/v28 V=results_v28_anchor
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    case "$1" in
    a)
        [ -f $V/regression.md ] || { echo "no regression.md (A1)"; exit 70; }
        [ -f $V/anchor.md ] && ! [ -d "$R/anchor" ] || step python3 experiments_v28.py a2_anchor 12 || exit 71
        [ -f $V/repro_v27.md ] && ! [ -d "$R/repro" ] || step python3 experiments_v28.py a2_repro 12 || exit 72
        [ -f $V/unit_checks.md ] && ! [ -d "$R/units" ] || step python3 experiments_v28.py a2_units 12 || exit 73
        [ -f $V/drain_v28.csv ] && ! [ -d "$R/drain" ] || step python3 experiments_v28.py a2_drain 12 || exit 74
        [ -f $V/reuse_check.md ] && ! [ -d "$R/reuse" ] || step python3 experiments_v28.py d_reuse 12 || exit 75
        ;;
    b)
        [ -f $V/PREREGISTRATION.md ] || { echo "no PREREGISTRATION.md"; exit 80; }
        if [ ! -f $V/tune_runs.csv ] || [ -d "$R/tune" ]; then
            step python3 experiments_v28.py b_tune 12 || exit 82
            step python3 experiments_v28.py b_choose || exit 83
        fi
        [ -f $V/drain_v28_tuned.csv ] && ! [ -d "$R/drain_tuned" ] || step python3 experiments_v28.py a2_drain 12 tuned || exit 84
        ;;
    *)
        echo "usage: chain_v28.sh a|b   (Parts C, D and E: chain_v28c.sh)"; exit 9
        ;;
    esac
    echo "=== $(date '+%F %T') chain $1 complete"
}
main "$@"
