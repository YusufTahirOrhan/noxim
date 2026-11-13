#!/bin/bash
# v26 Part A (results_v26_faults/PREREGISTRATION.md), unattended:
#   detach.sh v26formal bash chain_v26_formal.sh
# Waits for the exhaustive 2x2 check (its own session lb_v26a1, 10 processes), writes formal_all_2x2.csv, checks set 4 of A2 (the
# masks of Part B) on 3x3 and 4x4 first, then the four sets of both sizes and the second-half test. A failed check stops the chain;
# chain_v26_b.sh then stops Part B. ~/lbraw/v26/width.txt tells the stages of Part B how many processes they may use meanwhile.
# Every stage keeps what is finished, so the chain is restarted with the same command.
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local L=$HOME/lbraw/logs R=$HOME/lbraw/v26 N=${1:-6}
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    mkdir -p "$R"
    if [ ! -f results_v26_faults/formal_all_2x2.csv ]; then
        echo 2 > "$R/width.txt"
        while [ ! -f "$L/v26a1.exit" ]; do sleep 30; done
        if [ "$(cat "$L/v26a1.exit")" != "0" ]; then echo "A1 ended with exit $(cat "$L/v26a1.exit")"; exit 71; fi
        echo $((12 - N)) > "$R/width.txt"
        step python3 experiments_v26.py a1csv || exit 72
    fi
    echo $((12 - N)) > "$R/width.txt"
    if [ ! -f "$R/set4.ok" ]; then
        step python3 experiments_v26.py a2 "$N" 3x3:4 || exit 73
        step python3 experiments_v26.py a2 "$N" 4x4:4 || exit 74
        touch "$R/set4.ok"
    fi
    step python3 experiments_v26.py a2 "$N" 3x3 || exit 75
    step python3 experiments_v26.py a2 "$N" 4x4 || exit 76
    step python3 experiments_v26.py a2sub "$N" || exit 77
    echo 12 > "$R/width.txt"
    echo "=== $(date '+%F %T') formal chain complete"
}
main "$@"
