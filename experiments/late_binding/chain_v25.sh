#!/bin/bash
# v25: the steps that follow Part B's runs, unattended and in the pre-registered order.
#   detach.sh v25chain bash chain_v25.sh
# Waits for the detached Part B job (lb_v25b: timing, eval, check), then:
#   B  csv, sanity (the observation-only options change nothing)
#   C  the fault sweep on all threads (its gates - model check, drain tests, ladders - ran beside Part B; the sweep that
#      started on two threads is stopped and resumed), check, csv
#   D  application traces: eval, check, csv
#   E  pipe_all 0: eval, check, csv
# Every runner skips completed runs, so the chain can be started again after a stop. It stops at the first failed step
# (a drain-test FAIL, a failed check or a missing run); the exit code names the step.
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
    # ---- Part B ----
    while [ ! -f "$L/v25b.exit" ]; do sleep 60; done
    if [ "$(cat "$L/v25b.exit")" != "0" ]; then echo "Part B ended with exit $(cat "$L/v25b.exit"): the chain stops"; exit 21; fi
    if [ ! -f $R/eval_runs.csv ] || [ -d "$HOME/lbraw/v25/eval" ]; then
        step python3 experiments_v25.py csv || exit 22
    fi
    [ -f $R/eval_runs.csv ] && [ ! -d "$HOME/lbraw/v25/eval" ] || { echo "eval_runs.csv incomplete: the chain stops"; exit 22; }
    step python3 experiments_v25.py sanity "$N" || exit 23
    # ---- Part C ----
    if [ ! -f $R/fault_runs.csv ]; then
        while tmux has-session -t lb_v25c 2>/dev/null && [ ! -f $R/load_points_faults.json ]; do sleep 60; done
        if [ ! -f $R/load_points_faults.json ]; then echo "Part C gates did not pass (exit $(cat "$L/v25c.exit" 2>/dev/null)): the chain stops"; exit 31; fi
        # the sweep started on two threads: stop it (its finished runs are kept, the runs in flight are repeated)
        tmux kill-session -t lb_v25c 2>/dev/null
        sleep 3
        pkill -f 'experiments_v25.py c_eval'
        pkill -f 'lbraw/v25/ceval/'
        while pgrep -f 'lbraw/v25/ceval/' > /dev/null; do sleep 2; done
        step python3 experiments_v25.py c_eval "$N" || exit 32
        step python3 experiments_v25.py c_check || exit 33
        step python3 experiments_v25.py c_csv || exit 34
        [ -f $R/fault_runs.csv ] || exit 34
    fi
    # ---- Part D ----
    if [ ! -f $R/app_runs.csv ] || [ ! -f $R/pair_runs.csv ] || [ -d "$HOME/lbraw/v25/app" ]; then
        step python3 experiments_v25.py d_eval "$N" || exit 41
        step python3 experiments_v25.py d_check || exit 42
        step python3 experiments_v25.py d_csv || exit 43
    fi
    # ---- Part E ----
    if [ ! -f $R/pipe0_runs.csv ] || [ -d "$HOME/lbraw/v25/pipe0" ]; then
        step python3 experiments_v25.py e_eval "$N" || exit 51
        step python3 experiments_v25.py e_check || exit 52
        step python3 experiments_v25.py e_csv || exit 53
    fi
    echo "=== $(date '+%F %T') chain complete"
}
main "$@"
