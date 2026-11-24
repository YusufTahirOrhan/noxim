#!/bin/bash
# v29: the time rule at the ends of the parts of chain b that were still to come when restore_v29.py was written (C1, D2, E1), then
# chain c. Started with: detach.sh v29r bash restore_watch.sh
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local L=$HOME/lbraw/logs/v29b.log E=$HOME/lbraw/logs/v29b.exit p
    for p in c1 d2 e1; do
        until grep -q "exit 0: python3 experiments_v29.py ${p}_csv" "$L" 2>/dev/null; do
            if [ -f "$E" ] && [ "$(cat "$E")" != "0" ]; then echo "=== $(date '+%F %T') chain b ended with code $(cat "$E"): nothing more is decided here"; exit 1; fi
            sleep 20
        done
        echo "=== $(date '+%F %T') $p has ended"
        python3 restore_v29.py --label "the end of $(echo $p | tr a-z A-Z)"
    done
    until [ -f "$E" ]; do sleep 5; done
    [ "$(cat "$E")" = "0" ] || { echo "=== chain b ended with code $(cat "$E")"; exit 1; }
    echo "=== $(date '+%F %T') chain b is complete: chain c starts"
    exec bash chain_v29c.sh c
}
main "$@"
