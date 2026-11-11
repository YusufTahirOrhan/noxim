// v25: routing relation and selection of an interposer router for late entry binding without path adaptivity
// (CI_heurLA_X, CI_heurLA_O). Definitions follow src/DeftLateBinding.cpp (legalMoves, nextMasks, selectHeuristic with
// heur_lookahead 1, hop_weight_ipos 1, heur_busy 0, lut_bias D) and src/Router.cpp (the lookahead fallback); checked
// against vectors dumped from simulator runs (tb/).
//
// With one dimension order per packet every candidate has exactly one minimal move at a router, so the selection is
// computed per candidate (4 of them) and not per output:
//   C(s) = T(s) + w (f(o_s) + g(o_s, z_s)) + D [o_s drops the default VL]
// T(s): remaining hops through candidate s; o_s: the move towards s; z_s: the move at the router behind o_s; f: flits in
// the downstream buffer of o_s; g: flits in the buffer behind the neighbour's output z_s. The cost of an output is the
// minimum of C over the candidates it keeps (the simulator's w f + 1 + bestContinuation + lutBias), and the chosen output
// is the move of a candidate of least C.
//
// Registers carry the attribute v25r so that their names survive flattening (the timing groups are found by name).

// A register stage that is a wire when ON = 0.
module pipe25 #(parameter W = 1, parameter ON = 0) (input clk, input [W-1:0] d, output [W-1:0] q);
    generate
        if (ON) begin : g
            (* v25r *) reg [W-1:0] r;
            always @(posedge clk) r <= d;
            assign q = r;
        end else begin : g
            assign q = d;
        end
    endgenerate
endmodule

// One entry candidate (VL slot SLOT of the destination chiplet) seen from an interposer router at (x, y): the minimal
// legal move towards it. ORDER_O = 0: XY. ORDER_O = 1: the order of the packet's VN, XY in VN0 and YX in VN1.
module lb25_cmove #(parameter SLOT = 0, parameter ORDER_O = 0, parameter VNFIX = -1) (
    input [3:0] x, input [3:0] y, input [2:0] last, input vn, input [3:0] dst_x, input [3:0] dst_y,
    output [3:0] mv,     // one-hot N E S W (none: the candidate is here, or no legal move)
    output here,         // the candidate's VL is at this router
    output [3:0] fl,     // {ylt, ygt, xlt, xgt}: where the candidate lies
    output yx            // the head is routed Y first
);
`include "lb25_funcs.vh"
    wire [3:0] tx = {dst_x[3:2], slot_lx(SLOT)};
    wire [3:0] ty = {dst_y[3:2], slot_ly(SLOT)};
    wire xgt = tx > x, xlt = tx < x, ygt = ty > y, ylt = ty < y;
    wire xz = !xgt && !xlt, yz = !ygt && !ylt;
    assign here = xz && yz;
    assign fl = {ylt, ygt, xlt, xgt};
    wire ln = last == 3'd0, le = last == 3'd1, ls = last == 3'd2, lw = last == 3'd3;
    wire lx = le || lw, ly = ln || ls;
    assign yx = !ORDER_O ? 1'b0 : (VNFIX >= 0) ? (VNFIX != 0) : vn;
    // legalTurn: no U-turn; XY: no X move after a Y move; YX: no Y move after an X move
    wire mn = yx ? (ylt && !ls && !lx) : (xz && ylt && !ls);
    wire me = yx ? (yz && xgt && !lw) : (xgt && !lw && !ly);
    wire ms = yx ? (ygt && !ln && !lx) : (xz && ygt && !ln);
    wire mw = yx ? (yz && xlt && !le) : (xlt && !le && !ly);
    assign mv = {mw, ms, me, mn};
endmodule

// The terms of the selection for one candidate: the move at the router behind its move, and the hops left through it.
module lb25_cterm #(parameter SLOT = 0) (
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input [3:0] mv, input [3:0] fl, input yx,
    output [4:0] zv,     // the move at the neighbour, one-hot N E S W Hub
    output [5:0] T       // hops to the VL, the Up link, and from the VL to the destination
);
`include "lb25_funcs.vh"
    wire [3:0] tx = {dst_x[3:2], slot_lx(SLOT)};
    wire [3:0] ty = {dst_y[3:2], slot_ly(SLOT)};
    wire xgt = fl[0], xlt = fl[1], ygt = fl[2], ylt = fl[3];
    wire [3:0] ax = xgt ? tx - x : x - tx;
    wire [3:0] ay = ygt ? ty - y : y - ty;
    wire x2 = ax >= 4'd2, y2 = ay >= 4'd2;      // the dimension is not done after one more step
    wire xz = !xgt && !xlt, yz = !ygt && !ylt;
    wire mn = mv[0], me = mv[1], ms = mv[2], mw = mv[3];
    wire xmove = me || mw, ymove = mn || ms;
    // at the neighbour: straight on, else the second dimension of the order, else the Up link
    assign zv[0] = (mn && y2) || (xmove && !x2 && !yx && ylt);
    assign zv[1] = (me && x2) || (ymove && !y2 && yx && xgt);
    assign zv[2] = (ms && y2) || (xmove && !x2 && !yx && ygt);
    assign zv[3] = (mw && x2) || (ymove && !y2 && yx && xlt);
    assign zv[4] = (xmove && !x2 && (yx || yz)) || (ymove && !y2 && (!yx || xz));
    wire [2:0] rloc = {1'b0, absd2(slot_lx(SLOT), dst_x[1:0])} + {1'b0, absd2(slot_ly(SLOT), dst_y[1:0])};
    assign T = {2'b0, ax} + {2'b0, ay} + 6'd1 + {3'b0, rloc};
endmodule

// The routing relation: offered outputs and the candidate mask after each of them (legalMoves, nextMasks).
// LAST >= 0 fixes the arrival direction (one unit per input port); VNFIX >= 0 fixes the VN (one unit per input VC).
module lb25_rel #(parameter HAS_HUB = 1, parameter ORDER_O = 0, parameter LAST = -1, parameter VNFIX = -1) (
    input [3:0] x, input [3:0] y, input [2:0] last_i, input vn, input [3:0] dst_x, input [3:0] dst_y, input [3:0] cand,
    output [4:0] offered,        // N, E, S, W, Hub
    output [19:0] pruned,        // [o*4+:4]: the mask after output o
    output [15:0] mv, output [3:0] here, output [15:0] fl, output yx
);
    wire [2:0] last = (LAST >= 0) ? LAST : last_i;
    wire [3:0] yxs;
    assign yx = yxs[0];
    genvar s, d;
    generate
        for (s = 0; s < 4; s = s + 1) begin : c
            lb25_cmove #(.SLOT(s), .ORDER_O(ORDER_O), .VNFIX(VNFIX)) u (.x(x), .y(y), .last(last), .vn(vn), .dst_x(dst_x), .dst_y(dst_y),
                .mv(mv[4*s+:4]), .here(here[s]), .fl(fl[4*s+:4]), .yx(yxs[s]));
        end
        for (d = 0; d < 4; d = d + 1) begin : o
            for (s = 0; s < 4; s = s + 1) begin : p
                assign pruned[d*4+s] = cand[s] && !here[s] && mv[4*s+d];
            end
            assign offered[d] = |pruned[d*4+:4];
        end
    endgenerate
    assign pruned[19:16] = HAS_HUB ? (cand & here) : 4'b0;
    assign offered[4] = HAS_HUB ? |(cand & here) : 1'b0;
endmodule

// The decision. Stages: A relation and static terms; M occupancies of each candidate; B candidate costs; C comparison and
// tie break. CUT_A / CUT_M / CUT_B place a register after stage A / M / B; the result of stage C is combinational and is
// registered by the user (the stored-decision array, or the route register), so a decision takes 1 + CUT_A + CUT_M + CUT_B
// cycles. The occupancies are read in stage M. dec: 0 N, 1 E, 2 S, 3 W, 4 Hub.
module lb25_dec #(parameter HAS_HUB = 1, parameter ORDER_O = 0, parameter LAST = -1, parameter DBIAS = 0, parameter W_SHIFT = 1,
                  parameter CUT_A = 0, parameter CUT_M = 0, parameter CUT_B = 0, parameter TAGW = 2) (
    input clk, input rst, input v_i, input [TAGW-1:0] tag_i,
    input [3:0] x, input [3:0] y, input [2:0] last_i, input vn_i, input [3:0] dst_x, input [3:0] dst_y, input [3:0] cand,
    input [1:0] def_slot,        // DeFT-P's entry VL of the destination (carried in the head; used with DBIAS > 0)
    input [29:0] occ_self,       // [(o*2+vc)*3+:3]: flits in the downstream buffer of output o, VC vc (own credit counters)
    input [149:0] occ_nb,        // [(o*5+z)*6+vc*3+:3]: the same for output z of the router behind output o (its report)
    input [2:0] rnd,
    output [4:0] offered, output [19:0] pruned,
    output v_c, output [TAGW-1:0] tag_c, output [2:0] dec_c,
    output [27:0] dbg_cost, output [3:0] dbg_valid, output [19:0] dbg_o1h
);
    // ---- stage A: relation and static terms ----
    wire [15:0] mv, fl;
    wire [3:0] here;
    wire yx;
    lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(LAST), .VNFIX(-1)) rel (.x(x), .y(y), .last_i(last_i), .vn(vn_i), .dst_x(dst_x),
        .dst_y(dst_y), .cand(cand), .offered(offered), .pruned(pruned), .mv(mv), .here(here), .fl(fl), .yx(yx));
    wire [19:0] zv;              // [s*5+:5]
    wire [23:0] T;               // [s*6+:6]
    wire [19:0] o1h;             // [s*5+:5]: the output of candidate s
    wire [3:0] val, bias;
    wire [4:0] drop;             // the output drops the default VL from the mask
    // behind the Up link: the XY move of the boundary router above towards the destination (none: it is the destination)
    wire dxgt = dst_x > x, dxlt = dst_x < x, dygt = dst_y > y, dylt = dst_y < y;
    wire dxz = !dxgt && !dxlt;
    wire [3:0] zh = {dxlt, dxz && dygt, dxgt, dxz && dylt};
    genvar s, t, o;
    generate
        for (o = 0; o < 5; o = o + 1) begin : bo
            assign drop[o] = (DBIAS != 0) && cand[def_slot] && !pruned[o*4+def_slot];
        end
        for (s = 0; s < 4; s = s + 1) begin : ca
            lb25_cterm #(.SLOT(s)) ct (.x(x), .y(y), .dst_x(dst_x), .dst_y(dst_y), .mv(mv[4*s+:4]), .fl(fl[4*s+:4]), .yx(yx),
                .zv(zv[5*s+:5]), .T(T[6*s+:6]));
            assign o1h[5*s+:5] = {HAS_HUB ? here[s] : 1'b0, mv[4*s+:4]};
            assign val[s] = cand[s] && |o1h[5*s+:5];
            assign bias[s] = |(o1h[5*s+:5] & drop);
        end
    endgenerate
    localparam WA = 20 + 20 + 4 + 24 + 4 + 4 + 1 + TAGW;
    wire [19:0] o1h_a, zv_a;
    wire [3:0] zh_a, val_a, bias_a;
    wire [23:0] T_a;
    wire vn_a, v_a;
    wire [TAGW-1:0] tag_a;
    pipe25 #(.W(WA), .ON(CUT_A)) ra (.clk(clk), .d({o1h, zv, zh, T, val, bias, vn_i, tag_i}), .q({o1h_a, zv_a, zh_a, T_a, val_a, bias_a, vn_a, tag_a}));
    pipe25 #(.W(1), .ON(CUT_A)) va (.clk(clk), .d(v_i && !rst), .q(v_a));

    // ---- stage M: the occupancies each candidate meets ----
    wire [15:0] occ;             // [s*4+:4]: own occupancy of its output plus the occupancy behind the neighbour's output
    generate
        for (s = 0; s < 4; s = s + 1) begin : cm
            wire [4:0] o1 = o1h_a[5*s+:5];
            wire [4:0] z1 = zv_a[5*s+:5];
            reg [2:0] fs, gs;
            integer oo, zz;
            always @* begin
                fs = 3'd0;
                gs = 3'd0;
                for (oo = 0; oo < 5; oo = oo + 1)
                    if (o1[oo]) fs = fs | (vn_a ? occ_self[(oo*2+1)*3+:3] : occ_self[(oo*2)*3+:3]);
                for (oo = 0; oo < 4; oo = oo + 1)
                    for (zz = 0; zz < 5; zz = zz + 1)
                        if (o1[oo] && z1[zz]) gs = gs | (vn_a ? occ_nb[(oo*5+zz)*6+3+:3] : occ_nb[(oo*5+zz)*6+:3]);
                // behind the Up link the packet is in VN1 (no move there when the boundary router is the destination)
                for (zz = 0; zz < 4; zz = zz + 1)
                    if (o1[4] && zh_a[zz]) gs = gs | occ_nb[(4*5+zz)*6+3+:3];
            end
            assign occ[4*s+:4] = {1'b0, fs} + {1'b0, gs};
        end
    endgenerate
    localparam WM = 16 + 20 + 24 + 4 + 4 + TAGW;
    wire [15:0] occ_m;
    wire [19:0] o1h_m;
    wire [23:0] T_m;
    wire [3:0] val_m, bias_m;
    wire v_m;
    wire [TAGW-1:0] tag_m;
    pipe25 #(.W(WM), .ON(CUT_M)) rm (.clk(clk), .d({occ, o1h_a, T_a, val_a, bias_a, tag_a}), .q({occ_m, o1h_m, T_m, val_m, bias_m, tag_m}));
    pipe25 #(.W(1), .ON(CUT_M)) vm (.clk(clk), .d(v_a && !rst), .q(v_m));

    // ---- stage B: the cost of each candidate ----
    wire [27:0] cost;            // [s*7+:7]
    generate
        for (s = 0; s < 4; s = s + 1) begin : cb
            assign cost[7*s+:7] = {1'b0, T_m[6*s+:6]} + ({3'b0, occ_m[4*s+:4]} << W_SHIFT) + (bias_m[s] ? DBIAS : 0);
        end
    endgenerate
    localparam WB = 28 + 4 + 20 + TAGW;
    wire [27:0] cost_b;
    wire [3:0] val_b;
    wire [19:0] o1h_b;
    wire v_b;
    wire [TAGW-1:0] tag_b;
    pipe25 #(.W(WB), .ON(CUT_B)) rb (.clk(clk), .d({cost, val_m, o1h_m, tag_m}), .q({cost_b, val_b, o1h_b, tag_b}));
    pipe25 #(.W(1), .ON(CUT_B)) vb (.clk(clk), .d(v_m && !rst), .q(v_b));

    // ---- stage C: candidates of least cost, their outputs, the tie break among those outputs ----
    wire [3:0] ismin;
    wire [4:0] tie;
    generate
        for (s = 0; s < 4; s = s + 1) begin : cc
            wire [3:0] ok;
            for (t = 0; t < 4; t = t + 1) begin : k
                assign ok[t] = (s == t) || !val_b[t] || (cost_b[7*s+:7] <= cost_b[7*t+:7]);
            end
            assign ismin[s] = val_b[s] && &ok;
        end
        for (o = 0; o < 5; o = o + 1) begin : to
            assign tie[o] = (ismin[0] && o1h_b[o]) || (ismin[1] && o1h_b[5+o]) || (ismin[2] && o1h_b[10+o]) || (ismin[3] && o1h_b[15+o]);
        end
    endgenerate
    // rotating priority: the first output of least cost at or after position rnd mod 5, wrapping (the simulator draws at random)
    wire [4:0] ge = (rnd == 3'd0 || rnd == 3'd5) ? 5'b11111 : (rnd == 3'd1 || rnd == 3'd6) ? 5'b11110 :
                    (rnd == 3'd2 || rnd == 3'd7) ? 5'b11100 : (rnd == 3'd3) ? 5'b11000 : 5'b10000;
    wire [4:0] hi = tie & ge;
    wire [4:0] pk = (|hi) ? hi : tie;
    assign dec_c = pk[0] ? 3'd0 : pk[1] ? 3'd1 : pk[2] ? 3'd2 : pk[3] ? 3'd3 : 3'd4;
    assign v_c = v_b;
    assign tag_c = tag_b;
    assign dbg_cost = cost_b;
    assign dbg_valid = val_b;
    assign dbg_o1h = o1h_b;
endmodule

// Lookahead fallback (Router::selectionFunction): a head that holds no output asks for the stored output if it is free,
// else for the first other offered output that is free (offer order: Hub, N, E, S, W), else for the stored one.
// free[o]: the output VC is not held by another packet and the downstream buffer of that VC is not full.
module lb25_fallback (input [2:0] stored, input [4:0] offered, input [4:0] free, output [2:0] req);
    wire [4:0] st1 = 5'b00001 << stored;
    wire stored_free = |(st1 & free);
    wire [4:0] alt = offered & free & ~st1;
    wire [2:0] first = alt[4] ? 3'd4 : alt[0] ? 3'd0 : alt[1] ? 3'd1 : alt[2] ? 3'd2 : 3'd3;
    assign req = (stored_free || !(|alt)) ? stored : first;
endmodule

// The only offered output of a hop without a choice (and whether there is exactly one).
module lb25_single (input [4:0] offered, output single, output [2:0] only);
    assign single = (offered == 5'b00001) || (offered == 5'b00010) || (offered == 5'b00100) || (offered == 5'b01000) || (offered == 5'b10000);
    assign only = offered[0] ? 3'd0 : offered[1] ? 3'd1 : offered[2] ? 3'd2 : offered[3] ? 3'd3 : 3'd4;
endmodule

// Occupancy reports of the neighbours, registered on arrival. Only the (output, neighbour output, VC) triples the relation
// can ask for are kept: with XY the neighbour goes straight on, turns from X to Y or goes up; with the VN-split order the
// VN0 triples are those of XY and the VN1 triples those of YX. Behind the Up link the packet is in VN1.
module occ_regs25 #(parameter HAS_HUB = 1, parameter ORDER_O = 0) (input clk, input [149:0] in, output [149:0] out);
    function integer need(input integer o, input integer z, input integer vc);
        integer ox, zx, xy, yx;
        begin
            ox = (o == 1 || o == 3);
            zx = (z == 1 || z == 3);
            if (o == 4) need = HAS_HUB && z < 4 && vc == 1;
            else if (z == 4) need = 1;
            else begin
                xy = (z == o) || (ox && !zx);          // straight on, or X then Y
                yx = (z == o) || (!ox && zx);          // straight on, or Y then X
                need = ORDER_O ? (vc == 0 ? xy : yx) : xy;
            end
        end
    endfunction
    genvar o, z, v;
    generate
        for (o = 0; o < 5; o = o + 1) begin : d
            for (z = 0; z < 5; z = z + 1) begin : e
                for (v = 0; v < 2; v = v + 1) begin : c
                    if (need(o, z, v)) begin : k
                        (* v25r *) reg [2:0] r;
                        always @(posedge clk) r <= in[(o*5+z)*6+v*3+:3];
                        assign out[(o*5+z)*6+v*3+:3] = r;
                    end else begin : n
                        assign out[(o*5+z)*6+v*3+:3] = 3'd0;
                    end
                end
            end
        end
    endgenerate
endmodule
