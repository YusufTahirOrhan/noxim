#!/bin/bash
# v29: the hand-over from chain c (it ends with the tuning of Part F) to chain d, if nobody does it by hand.
#   detach.sh v29w bash after_c_v29.sh [GRACE_SECONDS]        (default 1800)
# By hand the hand-over is: stop this script (tmux kill-session -t lb_v29w); python3 addendum_v29.py; read the addenda; commit and push;
# detach.sh v29d bash chain_v29c.sh d.
# The script waits until chain c has ended with code 0, then GRACE_SECONDS for chain d to be started by hand (its log or its session
# appears). If it was not, it writes the addenda with addendum_v29.py (the record of what the tuning rule chose; refused if an evaluation
# run of the rows exists), commits what chain c left in results_v29_review (no push: WSL holds no credentials) and starts chain d.
# A chain c that ended with another code, or a failed addendum, ends the script with nothing started.
# For a dry run: V29_LOGS=<folder with stand-in logs> V29_DRY=1 bash after_c_v29.sh 2
main() {
    cd "$(dirname "$0")" || exit 9
    export PYTHONPATH=$HOME/lbpkgs
    local L=${V29_LOGS:-$HOME/lbraw/logs} V=results_v29_review grace=${1:-1800} dry=${V29_DRY:-0} t=0 f an ae
    say() { echo "=== $(date '+%F %T') $*"; }
    by_hand() { [ -f "$L/v29d.log" ] || tmux has-session -t lb_v29d 2>/dev/null; }
    # chain c runs in the session of restore_watch.sh (log v29r.log), or, started by hand, as v29c
    until grep -q "chain c complete" "$L/v29r.log" "$L/v29c.log" 2>/dev/null; do
        for f in v29r v29c; do
            if [ -s "$L/$f.exit" ] && [ "$(cat "$L/$f.exit")" != "0" ]; then say "$f ended with code $(cat "$L/$f.exit"): nothing is started here"; exit 1; fi
        done
        if by_hand; then say "chain d exists already: nothing to do"; exit 0; fi
        sleep 30
    done
    say "chain c is complete; $grace s for chain d to be started by hand"
    while [ "$t" -lt "$grace" ]; do
        if by_hand; then say "chain d was started by hand: nothing to do"; exit 0; fi
        sleep 10
        t=$((t + 10))
    done
    if by_hand; then say "chain d was started by hand: nothing to do"; exit 0; fi
    say "nobody started chain d: the addenda are written here"
    if [ "$dry" = "1" ]; then
        python3 addendum_v29.py --print | head -5
        say "dry run: no file written, no commit, chain d not started"
        exit 0
    fi
    python3 addendum_v29.py || { say "addendum_v29.py failed: chain d is not started"; exit 1; }
    grep -q "## Addendum F1" $V/PREREGISTRATION.md || { say "no Addendum F1 in PREREGISTRATION.md: chain d is not started"; exit 1; }
    an=$(git log -1 --format=%an)
    ae=$(git log -1 --format=%ae)
    git add $V
    if git -c user.name="$an" -c user.email="$ae" commit -q -F - <<'EOF'
v29: the addenda with the tuned values of Part F, written by after_c_v29.sh before chain d

Nobody was at the keyboard when chain c ended. addendum_v29.py wrote the choices of the
tuning rule into PREREGISTRATION.md; this commit holds them with what chain c left in the
results folder. No evaluation run of the tuned rows exists at this moment.

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
EOF
    then say "committed: $(git log --oneline -1)"; else say "the commit failed: the addenda are in the working tree, written before this line"; fi
    bash detach.sh v29d bash chain_v29c.sh d
    say "chain d started"
}
main "$@"
