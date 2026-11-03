#!/bin/bash
# v21 F2: builds the exporter, writes the vectors, runs them on the RTL. Results: ../functional_check.txt
# Usage: run_fast_vectors.sh OBJDIR [nvec_per_config]
set -u
export PATH=~/eda/oss-cad-suite/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
R21=$HERE/..
NOX=$(cd "$HERE/../../../.." && pwd)
R18=$R21/../results_v18_area/rtl
OBJ=${1:-$NOX/bin/build}
NV=${2:-20000}
V=~/lbraw/v21_vec
mkdir -p $V
export LD_LIBRARY_PATH=$NOX/bin/libs/systemc-2.3.1/lib-linux64:$NOX/bin/libs/yaml-cpp/lib
export SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1
OBJS=$(find $OBJ -name '*.o' | grep -v -E '/(Main|DeftLateBinding)\.o$')
g++ -O2 -std=c++11 -DSC_NO_WRITE_CHECK -w -I$NOX/src -isystem $NOX/bin/libs/systemc-2.3.1/include -I$NOX/bin/libs/yaml-cpp/include \
    $HERE/export_fast.cpp $OBJS -L$NOX/bin/libs/systemc-2.3.1/lib-linux64 -L$NOX/bin/libs/yaml-cpp/lib -lsystemc -lm -lyaml-cpp -o $V/export_fast || exit 1
EX=$V/export_fast
SRC="$R21/rtl/fast_units.v $R18/lb_units.v $HERE/tb_fast.v"
RES=$R21/functional_check.txt
: > $RES
run() {   # top, parameters..., vector file
    local top=$1; shift
    local vec=${!#}
    local params=("${@:1:$#-1}")
    local args=()
    for p in "${params[@]}"; do args+=("-P$top.$p"); done
    iverilog -g2012 -I$R18 -s $top "${args[@]}" -o $V/$$.vvp $SRC || exit 1
    vvp $V/$$.vvp +vec=$vec | tee -a $RES | tail -6
}
#          size scope xw w_shift beta f gx
# the tuned weights (tuning_choice.json)
for cfg in "2x2 I 3 1 4 10 2" "2x2 F 3 1 4 10 2" "3x3 I 4 2 4 8 3" "3x3 F 4 1 4 8 3" "4x4 I 4 1 4 8 4" "4x4 F 4 2 4 8 4"; do
    set -- $cfg
    Z=$1; S=$2; XW=$3; WS=$4; B=$5; F=$6; GX=$7
    export FAST_W=$((1 << WS)) FAST_BETA=$B
    for Q in 0 1; do
        FF=$([ $Q = 1 ] && echo $F || echo 0)
        $EX sel_ipos $Z $S $Q $V/ipos.txt $NV
        for C in 0 1; do
            run tb_fast IPOS=1 HAS_HUB=1 XW=$XW USE_Q=$Q F=$FF CUT=$C $V/ipos.txt
            run tb_fast IPOS=1 HAS_HUB=0 XW=$XW USE_Q=$Q F=$FF CUT=$C $V/ipos.txt
        done
        if [ $S = F ]; then
            $EX sel_chip $Z $S $Q $V/chip.txt $NV
            for C in 0 1; do
                run tb_fast IPOS=0 HAS_HUB=1 XW=$XW USE_Q=$Q F=$FF CUT=$C $V/chip.txt
                run tb_fast IPOS=0 HAS_HUB=0 XW=$XW USE_Q=$Q F=$FF CUT=$C $V/chip.txt
            done
        fi
    done
    $EX regs $Z $S 0 $V/regs.txt 2000
    run tb_fast_regs W_SHIFT=$WS BETA=$B GX=$GX $V/regs.txt
    if [ $S = I ]; then
        $EX fb $Z $S 1 $V/fb.txt $NV
        run tb_fast_fb F=$F $V/fb.txt
    fi
done
grep RESULT $RES | awk '{for(i=1;i<=NF;i++){if($i~/^vectors=/){split($i,a,"=");n+=a[2]} if($i~/^mismatches=/){split($i,b,"=");m+=b[2]}}} END{print "total vectors",n,"mismatches",m}' | tee -a $RES
rm -f $V/*.txt $V/$$.vvp $V/export_fast
