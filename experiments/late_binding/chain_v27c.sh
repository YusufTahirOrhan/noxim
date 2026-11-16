#!/bin/bash
# v27 Parts C and E (results_v27_early/PREREGISTRATION.md and its addendum), unattended:
#   detach.sh v27c bash chain_v27c.sh
# after the tuning choice, the drain tests of the tuned rows and the addendum. Order: the timing runs and the 30 h rule (drops.json),
# the kept runs of Part C, the time rule again for what was dropped of Part C (restore_v27.py c), Part C to its CSV, the time rule for
# Part E (restore_v27.py e), Part E. The start of the timing runs is written to ~/lbraw/v27/c_start.txt.
# The run stages take their number of processes from ~/lbraw/v27/width.txt at every batch of runs (experiments_v27.width).
# Resumable: finished stages and finished runs are skipped. A timing stage that was interrupted must be run again in full: delete its
# outputs (the raw folders eval and fault, drops.json) and c_start.txt first; it times one call and skips finished runs. If the chain was
# stopped for a while, add the seconds it was stopped as a second number to c_start.txt.
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
    [ -f $V/tuning_choice_v27.json ] || { echo "no tuning choice"; exit 90; }
    [ -f $V/drain_v27_tuned.csv ] || { echo "no drain tests of the tuned rows"; exit 90; }
    grep -q "Addendum" $V/PREREGISTRATION.md || { echo "the addendum with the chosen values is not in PREREGISTRATION.md"; exit 90; }
    mkdir -p "$R"
    if [ ! -f $V/drops.json ]; then
        date +%s > "$R/c_start.txt"
        step python3 experiments_v27.py c_timing 12 || exit 91
    fi
    [ -f "$R/c_start.txt" ] || { echo "no c_start.txt"; exit 90; }
    if [ ! -f $V/eval_runs.csv ] || [ -d "$R/eval" ]; then
        step python3 experiments_v27.py c_eval 12 || exit 92
        step python3 restore_v27.py c
        step python3 experiments_v27.py c_eval 12 || exit 92
        step python3 experiments_v27.py c_check || exit 93
        step python3 experiments_v27.py c_csv || exit 94
    fi
    if [ ! -f $V/fault_runs.csv ] || [ -d "$R/fault" ]; then
        step python3 restore_v27.py e
        step python3 experiments_v27.py e_eval 12 || exit 95
        step python3 experiments_v27.py e_check || exit 96
        step python3 experiments_v27.py e_csv || exit 97
    fi
    echo "=== $(date '+%F %T') chain c complete"
}
main "$@"
