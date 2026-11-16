#!/bin/bash
# v27 (results_v27_early/PREREGISTRATION.md), unattended, in three parts:
#   detach.sh v27a bash chain_v27.sh a     the gates of the new rows: anchor, unit checks, drain tests (a failed gate stops)
#   detach.sh v27b bash chain_v27.sh b     after the pre-registration: the reuse check of Part E, the tuning of oracle_beta, its choice,
#                                          and the drain tests of the tuned rows with their chosen values
#   detach.sh v27c bash chain_v27.sh c     after the addendum with the chosen values: the timing runs, Part C, Part E
# The run stages take their number of processes from ~/lbraw/v27/width.txt at every batch of runs (experiments_v27.width).
# Resumable: finished stages and finished runs are skipped. (A timing stage that was interrupted must be run again in full: delete
# its outputs first; it times one call and skips finished runs.)
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local R=$HOME/lbraw/v27 V=results_v27_early
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    case "$1" in
    a)
        [ -f $V/anchor.md ] || step python3 experiments_v27.py a2_anchor 12 || exit 71
        [ -f $V/unit_checks.md ] && ! [ -d "$R/units" ] || step python3 experiments_v27.py a2_units 12 || exit 72
        [ -f $V/drain_v27.csv ] && ! [ -d "$R/drain" ] || step python3 experiments_v27.py a2_drain 12 || exit 73
        ;;
    b)
        [ -f $V/PREREGISTRATION.md ] || { echo "no PREREGISTRATION.md"; exit 80; }
        [ -f $V/reuse_check.md ] && ! [ -d "$R/reuse" ] || step python3 experiments_v27.py e_reuse 12 || exit 81
        if [ ! -f $V/tune_runs.csv ] || [ -d "$R/tune" ]; then
            step python3 experiments_v27.py b_tune 12 || exit 82
            step python3 experiments_v27.py b_choose || exit 83
        fi
        [ -f $V/drain_v27_tuned.csv ] && ! [ -d "$R/drain_tuned" ] || step python3 experiments_v27.py a2_drain 12 tuned || exit 84
        ;;
    c)
        [ -f $V/tuning_choice_v27.json ] || { echo "no tuning choice"; exit 90; }
        grep -q "Addendum" $V/PREREGISTRATION.md || { echo "the addendum with the chosen values is not in PREREGISTRATION.md"; exit 90; }
        [ -f $V/drops.json ] || step python3 experiments_v27.py c_timing 12 || exit 91
        if [ ! -f $V/eval_runs.csv ] || [ -d "$R/eval" ]; then
            step python3 experiments_v27.py c_eval 12 || exit 92
            step python3 experiments_v27.py c_check || exit 93
            step python3 experiments_v27.py c_csv || exit 94
        fi
        if [ ! -f $V/fault_runs.csv ] || [ -d "$R/fault" ]; then
            step python3 experiments_v27.py e_eval 12 || exit 95
            step python3 experiments_v27.py e_check || exit 96
            step python3 experiments_v27.py e_csv || exit 97
        fi
        ;;
    *)
        echo "usage: chain_v27.sh a|b|c"; exit 9
        ;;
    esac
    echo "=== $(date '+%F %T') chain $1 complete"
}
main "$@"
