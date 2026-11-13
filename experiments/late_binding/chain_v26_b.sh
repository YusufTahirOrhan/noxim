#!/bin/bash
# v26 Part B (results_v26_faults/PREREGISTRATION.md), unattended:
#   detach.sh v26b bash chain_v26_b.sh
# Drain tests of every row on the 192 masks (a FAIL stops), the ladders, the load points, then, once the masks of Part B have
# passed the model check (~/lbraw/v26/set4.ok, written by chain_v26_formal.sh), the timing runs, the evaluation, the check of the
# raw folder and the CSV. Stops if the formal chain failed. The stages take their number of processes from ~/lbraw/v26/width.txt
# at every batch of runs (experiments_v26.width), so the two chains share the machine. Resumable: finished runs are kept.
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local L=$HOME/lbraw/logs R=$HOME/lbraw/v26 V=results_v26_faults
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    guard() {
        if [ -f "$L/v26formal.exit" ] && [ "$(cat "$L/v26formal.exit")" != "0" ]; then
            echo "=== $(date '+%F %T') the formal chain ended with exit $(cat "$L/v26formal.exit"): Part B stops"
            exit 80
        fi
    }
    if [ ! -f $V/fault_rate_runs.csv ] || [ -d "$R/beval" ]; then
        if [ ! -f $V/drain_v26.csv ] || grep -q FAIL $V/drain_v26.csv || [ -d "$R/bdrain" ]; then
            guard
            step python3 experiments_v26.py b_drain 12 || exit 81
        fi
        if [ ! -f $V/load_points_v26.json ]; then
            guard
            step python3 experiments_v26.py b_sat 12 || exit 82
            step python3 experiments_v26.py b_points || exit 83
        fi
        while [ ! -f "$R/set4.ok" ]; do guard; sleep 60; done
        if [ ! -f $V/drops.json ]; then
            guard
            step python3 experiments_v26.py b_timing 12 || exit 84
        fi
        guard
        step python3 experiments_v26.py b_eval 12 || exit 85
        step python3 experiments_v26.py b_check || exit 86
        step python3 experiments_v26.py b_csv || exit 87
    fi
    echo "=== $(date '+%F %T') Part B complete"
}
main "$@"
