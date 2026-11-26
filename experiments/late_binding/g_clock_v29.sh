#!/bin/bash
# v29: the clock of Part G. The part has at most 3 h (results_v29_review/PROMPT.md; PREREGISTRATION.md, "Part G (optional, at most
# 3 h)"), and chain_v29c.sh d has no clock for it. This watcher stops chain d when the limit has passed since the start of g_find and
# the chain has not ended by then.
#   detach.sh v29g bash g_clock_v29.sh [LIMIT_SECONDS]        (default 10800)
# It ends with nothing done when chain d ends first (its exit file appears) or when its session is gone.
# After a stop ~/lbraw/logs/v29g_stopped.txt has the two times; the finished runs stay in ~/lbraw/v29/trace.
# For a dry run: V29_LOGS=<folder with a stand-in v29d.log> V29_DRY=1 bash g_clock_v29.sh 60
main() {
    local L=${V29_LOGS:-$HOME/lbraw/logs} limit=${1:-10800} dry=${V29_DRY:-0} s t0 now seen=0
    say() { echo "=== $(date '+%F %T') $*"; }
    say "the clock of Part G: limit $limit s from the start of g_find"
    while :; do
        if [ -s "$L/v29d.exit" ]; then say "chain d has ended with code $(cat "$L/v29d.exit"): nothing to stop"; exit 0; fi
        s=$(tr '\r' '\n' < "$L/v29d.log" 2>/dev/null | grep -m1 'start: python3 experiments_v29.py g_find' | cut -c5-23)
        if [ -n "$s" ]; then
            t0=$(date -d "$s" +%s) || { say "cannot read the start time '$s'"; exit 1; }
            now=$(date +%s)
            if [ "$seen" = "0" ]; then say "g_find started at $s; the limit ends at $(date -d "@$((t0 + limit))" '+%F %T')"; seen=1; fi
            if [ $((now - t0)) -ge "$limit" ]; then
                say "Part G has run $((now - t0)) s since $s: chain d is stopped"
                if [ "$dry" = "1" ]; then say "dry run: nothing stopped"; exit 0; fi
                tmux kill-session -t lb_v29d 2>/dev/null
                pkill -x noxim
                echo "g_find started $s; chain d stopped $(date '+%F %T') after $((now - t0)) s (limit $limit s)" > "$L/v29g_stopped.txt"
                exit 0
            fi
        fi
        if [ "$dry" != "1" ] && ! tmux has-session -t lb_v29d 2>/dev/null && [ ! -s "$L/v29d.exit" ]; then
            sleep 5
            [ -s "$L/v29d.exit" ] || { say "the session of chain d is gone and it left no exit code: nothing to stop"; exit 0; }
        fi
        sleep 20
    done
}
main "$@"
