#!/bin/bash
# v29, the later simulation parts (results_v29_review/PREREGISTRATION.md), unattended:
#   detach.sh v29c bash chain_v29c.sh c     after chain b: C3, D1, C2, then the tuning of Part F (F1, then F2) and its choices
#   detach.sh v29d bash chain_v29c.sh d     after the addendum with the tuned values of Part F: the drain tests of EB_first with its tuned
#                                           lut_bias, the evaluation of F1 and of F2, and Part G
# A failed drain test, a failed check of a raw folder or a dead-end event stops the chain. What the 48 h rule dropped (drops.json) is
# skipped by the stages themselves; at the end of every part restore_v29.py takes back what fits by then (time_rule.md). The run stages take their number of processes from ~/lbraw/v29/width.txt at every batch of runs.
# Resumable: finished stages and finished runs are skipped (the tuning keeps its state in ~/lbraw/v29/tune_state_f1.json and _f2.json).
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
    dropped() { grep -q "\"$1\"" <(python3 -c "import json; print(json.dumps(json.load(open('$V/drops.json'))['dropped']))"); }
    rule() {                               # the time rule at the end of a part: what was dropped is taken back if it fits (restore_v29.py)
        if ! grep -q ": $1\$" $V/time_rule.md 2>/dev/null; then step python3 restore_v29.py --label "$1"; fi
    }
    [ -f $V/drops.json ] || { echo "no drops.json (the timing runs of chain b)"; exit 90; }
    [ -f $V/nola_runs.csv ] || { echo "chain b is not complete (no nola_runs.csv)"; exit 90; }
    case "$1" in
    c)
        part c3 depth_fault_runs.csv depthfault 91
        rule "the end of C3"
        part d1 vc_static_runs.csv static 92
        rule "the end of D1"
        dropped C2 || part c2 ipos7_runs.csv ipos7 93
        rule "the end of C2"
        if [ ! -f $V/tune_first_runs.csv ] || [ -d "$R/tune1" ]; then
            [ -f $V/tuning_v29.md ] || step python3 experiments_v29.py f_rule || exit 94
            step python3 experiments_v29.py f1_tune 12 || exit 94
            step python3 experiments_v29.py f1_choose || exit 95
        fi
        if ! dropped F2 && { [ ! -f $V/tune_age_runs.csv ] || [ -d "$R/tune2" ]; }; then
            step python3 experiments_v29.py f2_tune 12 || exit 96
            step python3 experiments_v29.py f2_choose || exit 97
        fi
        ;;
    d)
        [ -f $V/tuning_choice_v29.json ] || { echo "no tuning choice"; exit 90; }
        grep -q "Addendum F" $V/PREREGISTRATION.md || { echo "the addendum with the tuned values of Part F is not in PREREGISTRATION.md"; exit 90; }
        [ -f $V/drain_first_tuned.csv ] && ! [ -d "$R/fdrain_tuned" ] || step python3 experiments_v29.py a2_fdrain 12 tuned || exit 98
        part f1 early_first_runs.csv first 99
        rule "the end of F1"
        if ! dropped F2; then              # F2 was kept, or taken back by the time rule
            if [ ! -f $V/tune_age_runs.csv ] || [ -d "$R/tune2" ]; then
                step python3 experiments_v29.py f2_tune 12 || exit 96
                step python3 experiments_v29.py f2_choose || exit 97
            fi
            grep -q "Addendum F2" $V/PREREGISTRATION.md || { echo "F2 is run: its tuned values are not in PREREGISTRATION.md yet (Addendum F2); add them and start chain d again"; exit 0; }
            part f2 early_age_runs.csv age 100
            rule "the end of F2"
        fi
        if ! dropped G && [ ! -f $V/trace_runs.csv ]; then
            step python3 experiments_v29.py g_find 12 || exit 101
            step python3 experiments_v29.py g_eval 12 || exit 102
            step python3 experiments_v29.py g_csv || exit 103
        fi
        ;;
    *)
        echo "usage: chain_v29c.sh c|d"; exit 9
        ;;
    esac
    echo "=== $(date '+%F %T') chain $1 complete"
}
main "$@"
