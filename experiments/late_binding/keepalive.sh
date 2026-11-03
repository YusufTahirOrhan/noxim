#!/bin/bash
# Holds the WSL distro open while detached evaluations run. Started on the Windows side, outside the Claude Code process tree:
#   Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='wsl.exe -e bash /mnt/c/.../keepalive.sh'}
# Ends when ~/lbraw/keepalive.stop exists, or after 6 days.
stop=~/lbraw/keepalive.stop
rm -f "$stop"
for _ in $(seq 1 8640); do
    [ -e "$stop" ] && exit 0
    sleep 60
done
