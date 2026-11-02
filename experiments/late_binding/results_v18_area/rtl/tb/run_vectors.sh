#!/bin/bash
# v18 J2: builds the exporter, writes the vectors, runs them on the RTL. Vectors go to /tmp (not kept). Results: functional_check.txt.
# Usage: run_vectors.sh [nvec_per_config]
set -u
export PATH=~/eda/oss-cad-suite/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
RTL=$HERE/..
NOX=$(cd "$HERE/../../../../.." && pwd)
V=~/lbraw/v18_vec
mkdir -p $V
NV=${1:-20000}
export LD_LIBRARY_PATH=$NOX/bin/libs/systemc-2.3.1/lib-linux64:$NOX/bin/libs/yaml-cpp/lib
export SYSTEMC_DISABLE_COPYRIGHT_MESSAGE=1
OBJS=$(ls $NOX/bin/build/*.o $NOX/bin/build/routingAlgorithms/*.o $NOX/bin/build/selectionStrategies/*.o | grep -v -E '/(Main|DeftLateBinding)\.o$')
echo "== build exporter"
g++ -O2 -std=c++11 -DSC_NO_WRITE_CHECK -w -I$NOX/src -isystem $NOX/bin/libs/systemc-2.3.1/include -I$NOX/bin/libs/yaml-cpp/include \
    $HERE/export_vectors.cpp $OBJS -L$NOX/bin/libs/systemc-2.3.1/lib-linux64 -L$NOX/bin/libs/yaml-cpp/lib -lsystemc -lm -lyaml-cpp -o $V/export_vectors || exit 1
EX=$V/export_vectors
SRC="$RTL/lb_units.v $RTL/method_units.v $RTL/router_core.v $HERE/tb_units.v"
RES=$RTL/../functional_check.txt
: > $RES
run() {   # top, parameters..., vector file
    local top=$1; shift
    local vec=${!#}
    local params=("${@:1:$#-1}")
    local args=()
    for p in "${params[@]}"; do args+=("-P$top.$p"); done
    iverilog -g2012 -I$RTL -s $top "${args[@]}" -o $V/$$.vvp $SRC || exit 1
    vvp $V/$$.vvp +vec=$vec | tee -a $RES | tail -8
}

echo "== routing: every reachable input, 8x8 interposer, one 4x4 chiplet"
$EX route_ipos 2x2 F 0 $V/route_ipos.txt
$EX route_chip 2x2 F 0 $V/route_chip.txt
run tb_route IPOS=1 HAS_HUB=1 XW=3 $V/route_ipos.txt
run tb_route IPOS=1 HAS_HUB=0 XW=3 $V/route_ipos.txt
run tb_route IPOS=0 HAS_HUB=1 XW=3 $V/route_chip.txt
run tb_route IPOS=0 HAS_HUB=0 XW=3 $V/route_chip.txt
wc -l $V/route_ipos.txt $V/route_chip.txt | tee -a $RES

echo "== deterministic units"
$EX xy_chip 2x2 I 0 $V/xy_chip.txt
$EX xy_ipos 2x2 I 0 $V/xy_ipos.txt
$EX vn 2x2 I 0 $V/vn.txt
$EX near 2x2 I 0 $V/near.txt
run tb_xy IPOS=0 XW=3 $V/xy_chip.txt
run tb_xy IPOS=1 XW=3 $V/xy_ipos.txt
run tb_vn $V/vn.txt
run tb_near $V/near.txt

echo "== selection (random), Q update (random), boundary feedback (random)"
#          size scope xw w_shift beta f s1 s2
for cfg in "2x2 I 3 0 4 10 5 6" "2x2 F 3 1 0 10 7 9" "3x3 I 4 1 0 8 4 5" "3x3 F 4 1 0 8 6 8" "4x4 I 4 1 0 8 4 5" "4x4 F 4 0 4 8 5 6"; do
    set -- $cfg
    Z=$1; S=$2; XW=$3; WS=$4; B=$5; F=$6; S1=$7; S2=$8
    OE=$([ $S = F ] && echo 1 || echo 0)
    for Q in 0 1; do
        FF=$([ $Q = 1 ] && echo $F || echo 0)
        $EX sel_ipos $Z $S $Q $V/sel_ipos_$Z$S$Q.txt $NV
        run tb_sel IPOS=1 HAS_HUB=1 XW=$XW W_SHIFT=$WS BETA=$B USE_Q=$Q F=$FF CHIP_OE=$OE $V/sel_ipos_$Z$S$Q.txt
        run tb_sel IPOS=1 HAS_HUB=0 XW=$XW W_SHIFT=$WS BETA=$B USE_Q=$Q F=$FF CHIP_OE=$OE $V/sel_ipos_$Z$S$Q.txt
        if [ $S = F ]; then
            $EX sel_chip $Z $S $Q $V/sel_chip_$Z$S$Q.txt $NV
            run tb_sel IPOS=0 HAS_HUB=1 XW=$XW W_SHIFT=$WS BETA=$B USE_Q=$Q F=$FF CHIP_OE=1 $V/sel_chip_$Z$S$Q.txt
            run tb_sel IPOS=0 HAS_HUB=0 XW=$XW W_SHIFT=$WS BETA=$B USE_Q=$Q F=$FF CHIP_OE=1 $V/sel_chip_$Z$S$Q.txt
        fi
        rm -f $V/sel_*_$Z$S$Q.txt
    done
    $EX qupd $Z $S 1 $V/qupd_$Z$S.txt $NV
    run tb_qupd F=$F S1=$S1 S2=$S2 $V/qupd_$Z$S.txt
    if [ $S = I ]; then
        $EX fb $Z $S 1 $V/fb_$Z$S.txt $NV
        run tb_fb W_SHIFT=$WS BETA=$B F=$F $V/fb_$Z$S.txt
    fi
done
echo "== summary"
grep -c RESULT $RES
grep RESULT $RES | awk '{for(i=1;i<=NF;i++){if($i~/^vectors=/){split($i,a,"=");n+=a[2]} if($i~/^mismatches=/){split($i,b,"=");m+=b[2]}}} END{print "total vectors",n,"mismatches",m}' | tee -a $RES
rm -f $V/$$.vvp
