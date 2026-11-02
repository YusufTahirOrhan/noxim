#!/bin/bash
# v18: router-level smoke test of every method and router type. Appends to router_smoke.txt.
export PATH=~/eda/oss-cad-suite/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
RTL=$HERE/..
OUT=$RTL/../router_smoke.txt
: > $OUT
SRC="$RTL/lb_units.v $RTL/method_units.v $RTL/router_core.v $RTL/router_top.v $HERE/tb_router.v"
for cfg in "4 2 3 2 10 1 0 7 9" "16 4 4 4 8 0 4 5 6"; do
    set -- $cfg
    C=$1; GX=$2; XW=$3; KW=$4; F=$5; WS=$6; B=$7; S1=$8; S2=$9
    for m in 0 1 2 3 4 5 6 7 8 9; do for l in 0 1; do for h in 0 1; do for pp in 0 1; do
        if [ $pp = 1 ] && [ $m -lt 6 ]; then continue; fi
        if [ $pp = 1 ] && [ $m -le 7 ] && [ $l = 0 ]; then continue; fi
        iverilog -g2012 -I$RTL -s tb_router -Ptb_router.METHOD=$m -Ptb_router.LAYER=$l -Ptb_router.HAS_HUB=$h -Ptb_router.C=$C -Ptb_router.GX=$GX \
            -Ptb_router.XW=$XW -Ptb_router.KW=$KW -Ptb_router.F=$F -Ptb_router.W_SHIFT=$WS -Ptb_router.BETA=$B -Ptb_router.S1=$S1 -Ptb_router.S2=$S2 \
            -Ptb_router.RS_PER_PORT=$pp -o /tmp/tbr.vvp $SRC 2>&1 | grep -v sorry | head -5
        vvp /tmp/tbr.vvp | grep -v finish | tee -a $OUT | tail -4
    done; done; done; done
done
echo "OK lines: $(grep -c ' OK$' $OUT), FAIL lines: $(grep -c ' FAIL$' $OUT)" | tee -a $OUT
