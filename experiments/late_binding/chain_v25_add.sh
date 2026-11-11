#!/bin/bash
# v25 addendum (results_v25_confirm/PREREGISTRATION_addendum.md), unattended, after the chain of Parts B-E:
#   detach.sh v25add bash chain_v25_add.sh
# Waits for chain_v25.sh (lb_v25chain) to end without error, then runs the drain tests of the addendum row (a FAIL stops),
# the row on the Part B design, the check of the raw folder and the CSV. Resumable.
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local L=$HOME/lbraw/logs R=results_v25_confirm N=${1:-12}
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    while [ ! -f "$L/v25chain.exit" ]; do sleep 60; done
    if [ "$(cat "$L/v25chain.exit")" != "0" ]; then echo "the chain of Parts B-E ended with exit $(cat "$L/v25chain.exit"): the addendum does not start"; exit 61; fi
    if [ ! -f $R/addendum_runs.csv ] || [ -d "$HOME/lbraw/v25/aeval" ]; then
        if [ ! -f $R/drain_summary_addendum.csv ] || grep -q FAIL $R/drain_summary_addendum.csv || [ -d "$HOME/lbraw/v25/adrain" ]; then
            step python3 experiments_v25_add.py drain "$N" || exit 62
        fi
        step python3 experiments_v25_add.py eval "$N" || exit 63
        step python3 experiments_v25_add.py check || exit 64
        step python3 experiments_v25_add.py csv || exit 65
    fi
    echo "=== $(date '+%F %T') addendum complete"
}
main "$@"
