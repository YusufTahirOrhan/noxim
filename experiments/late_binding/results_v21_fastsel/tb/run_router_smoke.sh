#!/bin/bash
# v21: router-level smoke test of the fast methods, every router type, form and cut. Output: ../router_smoke.txt
# The test bench is v18's with the new ports added: the router's value on the links comes back to it, its VL works.
export PATH=~/eda/oss-cad-suite/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
R21=$HERE/..
R18=$R21/../results_v18_area/rtl
OUT=$R21/router_smoke.txt
: > $OUT
V=~/lbraw/v21_smoke
mkdir -p $V
sed -e 's/parameter NPKT = 40;/parameter NPKT = 40; parameter CUT = 0;/' \
    -e 's/\.RS_PER_PORT(RS_PER_PORT)) dut (/.RS_PER_PORT(RS_PER_PORT), .CUT(CUT)) dut (.l_out(l_out), .l_in({5{l_out}}), .hub_ok(1'"'"'b1),/' \
    -e 's/^    wire \[29:0\] occ_report;/    wire [29:0] occ_report;\n    wire [7:0] l_out;/' \
    $R18/tb/tb_router.v > $V/tb_router.v
SRC="$R18/lb_units.v $R18/method_units.v $R21/rtl/router_core.v $R21/rtl/fast_units.v $R21/rtl/router_top.v $V/tb_router.v"
for cfg in "4 2 3 2 10 1 0 7 9" "16 4 4 4 8 0 4 5 6"; do
    set -- $cfg
    C=$1; GX=$2; XW=$3; KW=$4; F=$5; WS=$6; B=$7; S1=$8; S2=$9
    for m in 10 11 12 13; do for l in 0 1; do for h in 0 1; do for pp in 0 1; do for cut in 0 1; do
        if [ $pp = 1 ] && [ $m -le 11 ] && [ $l = 0 ]; then continue; fi
        iverilog -g2012 -I$R18 -s tb_router -Ptb_router.METHOD=$m -Ptb_router.LAYER=$l -Ptb_router.HAS_HUB=$h -Ptb_router.C=$C -Ptb_router.GX=$GX \
            -Ptb_router.XW=$XW -Ptb_router.KW=$KW -Ptb_router.F=$F -Ptb_router.W_SHIFT=$WS -Ptb_router.BETA=$B -Ptb_router.S1=$S1 -Ptb_router.S2=$S2 \
            -Ptb_router.RS_PER_PORT=$pp -Ptb_router.CUT=$cut -o $V/tbr.vvp $SRC 2>&1 | grep -v sorry | head -5
        echo "cut=$cut $(vvp $V/tbr.vvp | grep -v finish | tail -3)" | tee -a $OUT | tail -4
    done; done; done; done; done
done
echo "OK lines: $(grep -c ' OK$' $OUT), FAIL lines: $(grep -c ' FAIL$' $OUT)" | tee -a $OUT
