#!/bin/bash
# Run an evaluation detached from the calling session, in a tmux session of WSL.
#   detach.sh NAME COMMAND...      from experiments/late_binding, with PYTHONPATH=~/lbpkgs
# Log: ~/lbraw/logs/NAME.log. Exit code: ~/lbraw/logs/NAME.exit, written when the command ends.
# The runners skip completed runs, so a stopped job is restarted with the same command.
# The distro stops when no wsl.exe is attached, so a detached Windows-side wsl.exe must hold it open: see keepalive.sh.
set -u
name=$1
shift
logs=~/lbraw/logs
mkdir -p "$logs"
if tmux has-session -t "lb_$name" 2>/dev/null; then
    echo "session lb_$name is already running" >&2
    exit 1
fi
rm -f "$logs/$name.exit"
here=$(cd "$(dirname "$0")" && pwd)
printf -v cmd '%q ' "$@"
tmux new-session -d -s "lb_$name" -x 200 -y 50 \
    "cd '$here' && export PYTHONPATH=\$HOME/lbpkgs; date >> '$logs/$name.log'; $cmd >> '$logs/$name.log' 2>&1; echo \$? > '$logs/$name.exit'; date >> '$logs/$name.log'"
echo "started lb_$name; log $logs/$name.log"
