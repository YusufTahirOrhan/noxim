#!/bin/bash
# v29 Part E, the hardware steps (results_v29_review/hw/), unattended, next to the simulation chains:
#   detach.sh v29h bash chain_v29h.sh e3      E3: the buffer depths of the reference core, synthesis, area and system ratios
#   detach.sh v29h bash chain_v29h.sh e2      E2: the two RTL variants against vectors, router tests, synthesis and timing
#   detach.sh v29h bash chain_v29h.sh e4      E4: port loads from the instrumented simulator, power
#   detach.sh v29h bash chain_v29h.sh all     the three, in this order
# Every stage runs in its own process group and is stopped (SIGSTOP) while the timing runs of the 48 h rule run in the simulation
# chain (experiments_v29.py t_timing in ~/lbraw/logs/v29b.log), so that they are timed on a machine with nothing else of the round on
# it; it goes on (SIGCONT) when they are done. Threads: the second argument (default 3). Resumable: finished runs are skipped.
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local N=${2:-3}
    timing_active() {
        local last
        last=$(grep '^=== ' "$HOME/lbraw/logs/v29b.log" 2>/dev/null | tail -1)
        case "$last" in *"start: python3 experiments_v29.py t_timing"*) return 0 ;; esac
        return 1
    }
    step() {
        echo "=== $(date '+%F %T') start: $*"
        setsid "$@" &
        local pid=$! paused=0 rc
        while kill -0 $pid 2>/dev/null; do
            if timing_active; then
                if [ $paused = 0 ]; then kill -STOP -- -$pid 2>/dev/null; paused=1; echo "=== $(date '+%F %T') paused: the timing runs have the machine"; fi
            elif [ $paused = 1 ]; then
                kill -CONT -- -$pid 2>/dev/null; paused=0; echo "=== $(date '+%F %T') resumed"
            fi
            sleep 5
        done
        wait $pid
        rc=$?
        echo "=== $(date '+%F %T') exit $rc: $*"
        return $rc
    }
    e3() {
        grep -q "both controls fail: yes" results_v29_review/hw/buffer_core_check.txt 2>/dev/null || step python3 experiments_v29.py e3_tb || exit 61
        step python3 experiments_v29.py e3_synth "$N" || exit 62
        step python3 experiments_v29.py e3_csv || exit 63
    }
    e2() {
        [ -x "$HOME/lbbin/noxim_v29_vec" ] || step python3 experiments_v29.py e2_build "$N" || exit 64
        step python3 experiments_v29.py e2_vec "$N" || exit 65
        step python3 experiments_v29.py e2_smoke "$N" || exit 66
        step python3 experiments_v29.py e2_lat "$N" || exit 67
        step python3 experiments_v29.py e2_synth "$N" || exit 68
        step python3 experiments_v29.py e2_csv || exit 69
    }
    e4() {
        [ -x "$HOME/lbbin/noxim_v29_vec" ] || step python3 experiments_v29.py e2_build "$N" || exit 64
        step python3 experiments_v29.py e4_loads "$N" || exit 70
        step python3 experiments_v29.py e4_power "$N" || exit 71
    }
    case "$1" in
    e3) e3 ;;
    e2) e2 ;;
    e4) e4 ;;
    all) e3; e2; e4 ;;
    *) echo "usage: chain_v29h.sh e3|e2|e4|all [threads]"; exit 9 ;;
    esac
    echo "=== $(date '+%F %T') chain h $1 complete"
}
main "$@"
