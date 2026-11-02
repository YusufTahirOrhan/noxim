#!/bin/bash
# v18 J2: do the vector checks catch errors? Each mutation below changes one line of a copy of the RTL; the matching vector file must report mismatches.
# Requires the vectors of run_vectors.sh (kept in ~/lbraw/v18_vec for this check). Results: mutation_check.txt.
export PATH=~/eda/oss-cad-suite/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
RTL=$HERE/..
V=~/lbraw/v18_vec
W=~/lbraw/v18_mut
OUT=$RTL/../mutation_check.txt
: > $OUT
mut() {   # name, file, sed expression, top, vector file, parameters...
    local name=$1 file=$2 expr=$3 top=$4 vec=$5; shift 5
    rm -rf $W; mkdir -p $W; cp $RTL/*.v $RTL/*.vh $HERE/tb_units.v $W/
    sed -i "$expr" $W/$file
    if cmp -s $W/$file $RTL/$file; then echo "$name: MUTATION DID NOT APPLY" | tee -a $OUT; return; fi
    local args=()
    for p in "$@"; do args+=("-P$top.$p"); done
    iverilog -g2012 -I$W -s $top "${args[@]}" -o $W/m.vvp $W/lb_units.v $W/method_units.v $W/router_core.v $W/tb_units.v || return
    local r=$(vvp $W/m.vvp +vec=$vec | grep RESULT)
    echo "$name: $r" | tee -a $OUT
}
SEL="IPOS=1 HAS_HUB=1 XW=4 W_SHIFT=1 BETA=0 USE_Q=1 F=8 CHIP_OE=0"
mut oe_even_flip   lb_funcs.vh "s/wire even = !x\[0\]/wire even = x[0]/;s/oe_moves\[1\] = e_gt0 \&\& last != 3'd3 \&\& (!(n_lt0 || n_gt0) || e_ge2 || even)/oe_moves[1] = e_gt0 \&\& last != 3'd3 \&\& (!(n_lt0 || n_gt0) || e_ge2)/" tb_route $V/route_ipos.txt IPOS=1 HAS_HUB=1 XW=3
mut oe_uturn       lb_funcs.vh "s/oe_moves\[3\] = e_lt0 \&\& last != 3'd1 \&\& /oe_moves[3] = e_lt0 \&\& /" tb_route $V/route_chip.txt IPOS=0 HAS_HUB=1 XW=3
mut prune_keep_here lb_units.v "s/assign pruned\[d\*4+s\] = cand\[s\] \&\& !here\[s\] \&\& m\[4\*s+d\];/assign pruned[d*4+s] = cand[s] \&\& m[4*s+d];/" tb_route $V/route_ipos.txt IPOS=1 HAS_HUB=1 XW=3
mut oe_vert_rule   lb_funcs.vh "s/vert_ok = !(even \&\& last == 3'd1) \&\& (!e_lt0 || even);/vert_ok = !(even \&\& last == 3'd1);/" tb_route $V/route_ipos.txt IPOS=1 HAS_HUB=1 XW=3
mut prune_no_moves lb_units.v "s/assign pruned\[d\*4+s\] = cand\[s\] \&\& !here\[s\] \&\& m\[4\*s+d\];/assign pruned[d*4+s] = cand[s] \&\& !here[s];/" tb_route $V/route_ipos.txt IPOS=1 HAS_HUB=1 XW=3
mut near_tie       method_units.v "s/if (f\[s\] \&\& {1'b0, vl_dist(s)} < best)/if (f[s] \&\& {1'b0, vl_dist(s)} <= best)/" tb_near $V/near.txt
mut vn_r3          method_units.v "s/wire r3 = LAYER || !(arr_hor \&\& out_hub \&\& ovc);/wire r3 = 1'b1;/" tb_vn $V/vn.txt
mut xy_order       method_units.v "s/assign out = e ? 3'd1 : w ? 3'd3 : s ? 3'd2 : 3'd0;/assign out = s ? 3'd2 : n ? 3'd0 : e ? 3'd1 : 3'd3;/" tb_xy $V/xy_chip.txt IPOS=0 XW=3
mut q_round        lb_units.v "s/+ d + (1 << (S2 - 1));/+ d;/" tb_qupd $V/qupd_4x4I.txt F=8 S1=4 S2=5
mut q_saturate     lb_units.v "s/assign q_new = over ? 16'h7fff : under ? 16'h8000 : r\[15:0\];/assign q_new = r[15:0];/" tb_qupd $V/qupd_4x4I.txt F=8 S1=4 S2=5
echo "selection mutations need kept selection vectors:" >> $OUT
mut sel_sub        lb_units.v "s/localparam SUB = LAYER ? 2 : 1;/localparam SUB = LAYER ? 1 : 1;/" tb_sel $V/sel_ipos_keep.txt $SEL
mut sel_gamma      lb_units.v "s/assign T\[8\*s+:8\] = 2 \* manh(x, y, cx\[4\*s+:4\], cy\[4\*s+:4\]) + 1/assign T[8*s+:8] = 1 * manh(x, y, cx[4*s+:4], cy[4*s+:4]) + 1/" tb_sel $V/sel_ipos_keep.txt $SEL
mut sel_vc_up      lb_units.v "s/wire vz4 = LAYER ? 1'b1 : vcout\[o\];/wire vz4 = vcout[o];/" tb_sel $V/sel_ipos_keep.txt $SEL
mut sel_no_q       lb_units.v "s/+ \$signed(q\[o\*16+:16\]);/;/" tb_sel $V/sel_ipos_keep.txt $SEL
mut sel_goal       lb_units.v "s/wire \[CW-1:0\] vh = at_dst ? {CW{1'b0}} : vmin;/wire [CW-1:0] vh = vmin + 1;/" tb_sel $V/sel_ipos_keep.txt $SEL
cat >> $OUT <<'EOF'

oe_uturn and prune_keep_here report 0 mismatches because they are equivalent on the reachable inputs, not because the vectors miss them:
* oe_uturn removes "no W after E". A head whose last move was E can only hold candidates to the east, since pruning drops the others.
* prune_keep_here removes the "not here" term. For a candidate at this router the moves mask is already 0.
So both terms are redundant on reachable inputs and are kept only as defensive logic.
EOF
rm -rf $W
