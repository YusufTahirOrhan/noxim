#!/bin/bash
# v28 Parts C, D and E (results_v28_anchor/PREREGISTRATION.md and its addendum), unattended:
#   detach.sh v28c bash chain_v28c.sh
# after the tuning choice, the drain tests of the tuned rows and the addendum. Order: the timing runs and the 30 h rule (drops.json), the kept
# runs of Part C, the time rule for what was dropped of Part C (restore_v28.py c), Part C to its CSV, the time rule for Part D (restore_v28.py
# d), Part D to its CSV, the time rule for Part E (restore_v28.py e), Part E to its CSV. The start of the timing runs is written to
# ~/lbraw/v28/c_start.txt. The run stages take their number of processes from ~/lbraw/v28/width.txt at every batch of runs.
# Resumable: finished stages and finished runs are skipped. A timing stage that was interrupted must be run again in full: delete its outputs
# (the raw folders eval, fault and novlrep, drops.json) and c_start.txt first; it times one call per part and skips finished runs. If the
# chain was stopped for a while, add the seconds it was stopped as a second number to c_start.txt.
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
    [ -f $V/tuning_choice_v28.json ] || { echo "no tuning choice"; exit 90; }
    [ -f $V/drain_v28_tuned.csv ] || { echo "no drain tests of the tuned rows"; exit 90; }
    grep -q "Addendum" $V/PREREGISTRATION.md || { echo "the addendum with the chosen configurations is not in PREREGISTRATION.md"; exit 90; }
    mkdir -p "$R"
    if [ ! -f $V/drops.json ]; then
        date +%s > "$R/c_start.txt"
        step python3 experiments_v28.py c_timing 12 || exit 91
    fi
    [ -f "$R/c_start.txt" ] || { echo "no c_start.txt"; exit 90; }
    if [ ! -f $V/eval_runs.csv ] || [ -d "$R/eval" ]; then
        step python3 experiments_v28.py c_eval 12 || exit 92
        step python3 restore_v28.py c
        step python3 experiments_v28.py c_eval 12 || exit 92
        step python3 experiments_v28.py c_check || exit 93
        step python3 experiments_v28.py c_csv || exit 94
    fi
    if [ ! -f $V/fault_runs.csv ] || [ -d "$R/fault" ]; then
        step python3 restore_v28.py d
        step python3 experiments_v28.py d_eval 12 || exit 95
        step python3 experiments_v28.py d_check || exit 96
        step python3 experiments_v28.py d_csv || exit 97
    fi
    if [ ! -f $V/novlrep_runs.csv ] || [ -d "$R/novlrep" ]; then
        step python3 restore_v28.py e
        step python3 experiments_v28.py e_eval 12 || exit 98
        step python3 experiments_v28.py e_check || exit 99
        step python3 experiments_v28.py e_csv || exit 100
    fi
    echo "=== $(date '+%F %T') chain c complete"
}
main "$@"
