#!/bin/bash
# v29 (results_v29_review/PROMPT.md, PREREGISTRATION.md), unattended, in parts (the later parts in chain_v29c.sh):
#   detach.sh v29a bash chain_v29.sh a     the gates after the code change (A2): the buffer options, entry_commit first, the tables of the three
#                                          new traffic patterns, the referee's check, the reuse of the rows of rounds 25, 26 and 28
#   detach.sh v29b bash chain_v29.sh b     after the pre-registration: B0 (ladders), the tables and the drain tests on the three patterns, the
#                                          timing runs and the 48 h rule, then B1, B2, C1 (depth 6 first), D2, E1
# A failed gate, a failed drain test, a failed check of a raw folder or a dead-end event stops the chain (exit code of the stage).
# The run stages take their number of processes from ~/lbraw/v29/width.txt at every batch of runs (experiments_v29.width).
# Resumable: finished stages and finished runs are skipped. The timing stage must not be resumed half-way: if it was interrupted, delete
# drops.json, the raw folders heldout, depth, depthfault and deftpaper and ~/lbraw/v29/b_start.txt, and start the chain again. If the
# chain was stopped for a while after the timing runs, add the seconds it was stopped as a second number to b_start.txt.
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local R=$HOME/lbraw/v29 V=results_v29_review
    step() {
        echo "=== $(date '+%F %T') start: $*"
        "$@"
        local rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    part() {                               # part NAME CSV RAW CODE: the runs of a part, the check of its raw folder, its per-run CSV
        if [ ! -f "$V/$2" ] || [ -d "$R/$3" ]; then
            step python3 experiments_v29.py "$1_eval" 12 || exit "$4"
            step python3 experiments_v29.py "$1_check" || exit "$4"
            step python3 experiments_v29.py "$1_csv" || exit "$4"
        fi
    }
    mkdir -p "$R"
    case "$1" in
    a)
        grep -q "84 / 84 byte-identical" $V/regression.md 2>/dev/null || { echo "no regression.md (A1)"; exit 70; }
        [ -f $V/buffer_checks.md ] && ! [ -d "$R/bufid" ] || step python3 experiments_v29.py a2_bufid 12 || exit 71
        [ -f $V/anchor_first.md ] && ! [ -d "$R/fanchor" ] || step python3 experiments_v29.py a2_fanchor 12 || exit 72
        [ -f $V/unit_checks_first.md ] && ! [ -d "$R/funits" ] || step python3 experiments_v29.py a2_funits 12 || exit 73
        [ -f $V/traffic_checks.md ] || step python3 experiments_v29.py a2_traffic || exit 74
        [ -f $V/reuse_check.md ] && ! [ -d "$R/reuse" ] || step python3 experiments_v29.py a2_reuse 12 || exit 75
        [ -f $V/drain_first.csv ] && ! [ -d "$R/fdrain" ] || step python3 experiments_v29.py a2_fdrain 12 || exit 76
        [ -f $V/drain_buffers.csv ] && ! [ -d "$R/bufdrain" ] || step python3 experiments_v29.py a2_bufdrain 12 || exit 77
        [ -f $V/formal_independent/README.md ] || step python3 experiments_v29.py a2_formal || exit 78
        ;;
    b)
        [ -f $V/PREREGISTRATION.md ] || { echo "no PREREGISTRATION.md"; exit 80; }
        grep -q "Every reused row is reproduced: yes" $V/reuse_check.md 2>/dev/null || { echo "the reuse check has not passed (reuse_check.md)"; exit 80; }
        if [ ! -f $V/load_points_v29.json ]; then
            step python3 experiments_v29.py b_sat 12 || exit 81
            step python3 experiments_v29.py b_points || exit 81
        fi
        if [ ! -f $V/drain_traffic.csv ] || [ -d "$R/tdrain" ]; then
            step python3 experiments_v29.py a2_traffic || exit 82
            step python3 experiments_v29.py a2_tdrain 12 || exit 83
        fi
        if [ ! -f $V/drops.json ]; then
            date +%s > "$R/b_start.txt"
            step python3 experiments_v29.py t_timing 12 || exit 84
        fi
        part b1 heldout_runs.csv heldout 85
        part b2 lb_b0_runs.csv lbb0 86
        part c1 depth_runs.csv depth 87
        part d2 deft_setup_runs.csv deftpaper 88
        part e1 nola_runs.csv nola 89
        ;;
    *)
        echo "usage: chain_v29.sh a|b   (the later parts: chain_v29c.sh)"; exit 9
        ;;
    esac
    echo "=== $(date '+%F %T') chain $1 complete"
}
main "$@"
