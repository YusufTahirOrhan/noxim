#!/bin/bash
# v21 F1: builds rom_check against a build directory and runs it per size, scope and fault mask. Output: ../rom_check.txt
# Usage: run_rom_check.sh OBJDIR
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
NOX=$(cd "$HERE/../../../.." && pwd)
OBJ=${1:-$NOX/bin/build}
V=~/lbraw/v21_rom
mkdir -p $V
export LD_LIBRARY_PATH=$NOX/bin/libs/systemc-2.3.1/lib-linux64:$NOX/bin/libs/yaml-cpp/lib
export SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1
OBJS=$(find $OBJ -name '*.o' | grep -v -E '/(Main|DeftLateBinding)\.o$')
g++ -O2 -std=c++11 -DSC_NO_WRITE_CHECK -w -I$NOX/src -isystem $NOX/bin/libs/systemc-2.3.1/include -I$NOX/bin/libs/yaml-cpp/include \
    $HERE/rom_check.cpp $OBJS -L$NOX/bin/libs/systemc-2.3.1/lib-linux64 -L$NOX/bin/libs/yaml-cpp/lib -lsystemc -lm -lyaml-cpp -o $V/rom_check || exit 1
OUT=$HERE/../rom_check.txt
: > $OUT
fail=0
#            size mask: fault-free, one faulty VL per chiplet, and the first v11 mask with k = 2 and k = 3
for cfg in "2x2 0 0x1111 0x9C63 0x7BDE" "3x3 0 0x111111111 K2 K3" "4x4 0 0x1111111111111111 K2 K3"; do
    set -- $cfg
    z=$1; shift
    for m in "$@"; do
        if [ "${m:0:1}" = K ]; then
            m=$(python3 -c "import json; print(json.load(open('$NOX/experiments/late_binding/results_v11/masks.json'))['${z}__k${m:1}'][0])")
        fi
        for s in I F; do
            $V/rom_check $z $s $m >> $OUT 2>&1 || fail=1
        done
    done
done
echo "ROM check exit status: $fail" | tee -a $OUT
rm -f $V/rom_check
exit $fail
