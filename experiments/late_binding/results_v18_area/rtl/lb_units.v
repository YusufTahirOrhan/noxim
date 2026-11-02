// Late-binding routing and selection units (v18). All purely combinational except the tie-break state in lb_block.
// Definitions follow src/DeftLateBinding.cpp; checked against it by the vectors of tb/export_vectors.cpp.

// Routing relation for up to 4 candidates under odd-even: offered moves and pruned masks.
module lb_route #(parameter HAS_HUB = 1) (
    input [3:0] x, input [3:0] y, input [2:0] last,
    input [15:0] cx, input [15:0] cy, input [3:0] cand,
    output [4:0] offered,        // N, E, S, W, Hub
    output [19:0] pruned,        // [o*4+:4]: mask after output o
    output [35:0] flags, output [3:0] here
);
`include "lb_funcs.vh"
    wire even = !x[0];
    wire [15:0] m;               // [s*4+:4]: moves towards candidate s
    genvar s, d;
    generate
        for (s = 0; s < 4; s = s + 1) begin : c
            wire [8:0] f = flags_of(x, y, cx[4*s+:4], cy[4*s+:4]);
            assign flags[9*s+:9] = f;
            assign here[s] = cx[4*s+:4] == x && cy[4*s+:4] == y;
            assign m[4*s+:4] = oe_moves(even, last, f[F_EGT0], f[F_EGE2], f[F_ELT0], f[F_NLT0], f[F_NGT0]);
        end
        for (d = 0; d < 4; d = d + 1) begin : o
            for (s = 0; s < 4; s = s + 1) begin : p
                assign pruned[d*4+s] = cand[s] && !here[s] && m[4*s+d];
            end
            assign offered[d] = |pruned[d*4+:4];
        end
    endgenerate
    assign pruned[19:16] = HAS_HUB ? here : 4'b0;
    assign offered[4] = HAS_HUB ? |(cand & here) : 1'b0;
endmodule

// Interposer router: the candidates are the entry VLs of the destination chiplet.
module lb_route_ipos #(parameter XW = 3, parameter HAS_HUB = 1) (
    input [XW-1:0] x_i, input [XW-1:0] y_i, input [2:0] last, input [XW-1:0] dst_x_i, input [XW-1:0] dst_y_i, input [3:0] entry,
    output [4:0] offered, output [19:0] pruned, output [35:0] flags, output [3:0] here,
    output [15:0] cx, output [15:0] cy
);
`include "lb_funcs.vh"
    wire [3:0] x = x_i, y = y_i, dst_x = dst_x_i, dst_y = dst_y_i;
    genvar s;
    generate
        for (s = 0; s < 4; s = s + 1) begin : c
            assign cx[4*s+:4] = {dst_x[3:2], slot_lx(s)};
            assign cy[4*s+:4] = {dst_y[3:2], slot_ly(s)};
        end
    endgenerate
    lb_route #(.HAS_HUB(HAS_HUB)) r (.x(x), .y(y), .last(last), .cx(cx), .cy(cy), .cand(entry), .offered(offered),
                                     .pruned(pruned), .flags(flags), .here(here));
endmodule

// Chiplet router (LB-F): source phase towards the exit candidates; destination and intra-chiplet phase towards the
// destination (one candidate, the masks stay as they are).
module lb_route_chip #(parameter XW = 3, parameter HAS_HUB = 1) (
    input [XW-1:0] x_i, input [XW-1:0] y_i, input [2:0] last, input [XW-1:0] dst_x_i, input [XW-1:0] dst_y_i, input [3:0] exit_mask,
    output same_chip, output at_dst,
    output [4:0] offered, output [19:0] pruned, output [35:0] flags, output [3:0] here,
    output [15:0] cx, output [15:0] cy, output [3:0] cand
);
`include "lb_funcs.vh"
    wire [3:0] x = x_i, y = y_i, dst_x = dst_x_i, dst_y = dst_y_i;
    assign same_chip = x[3:2] == dst_x[3:2] && y[3:2] == dst_y[3:2];
    assign at_dst = x == dst_x && y == dst_y;
    assign cand = same_chip ? 4'b0001 : exit_mask;
    genvar s;
    generate
        for (s = 0; s < 4; s = s + 1) begin : c
            assign cx[4*s+:4] = same_chip ? dst_x : {x[3:2], slot_lx(s)};
            assign cy[4*s+:4] = same_chip ? dst_y : {y[3:2], slot_ly(s)};
        end
    endgenerate
    wire [4:0] off;
    lb_route #(.HAS_HUB(HAS_HUB)) r (.x(x), .y(y), .last(last), .cx(cx), .cy(cy), .cand(cand), .offered(off),
                                     .pruned(pruned), .flags(flags), .here(here));
    assign offered = {off[4] && !same_chip, off[3:0]};
endmodule

// Selection: Eq. (1) with lookahead, plus the learned residual when USE_Q is set; the comparator tree; the value and goal
// for the Q update of the previous router. LAYER 1 = interposer, 0 = chiplet. CHIP_OE: turn model on the chiplets (for the
// lookahead through a Hub move). Costs are signed, F fractional bits (F = 0 without Q).
module lb_sel #(parameter LAYER = 1, parameter W_SHIFT = 1, parameter BETA = 0, parameter USE_Q = 0, parameter F = 0,
                parameter HAS_HUB = 1, parameter CHIP_OE = 1,
                parameter CW = 9 + F, parameter GW = CW + 2) (
    input [3:0] x, input [3:0] y, input [2:0] last, input arr_hub, input vc, input [3:0] dst_x, input [3:0] dst_y,
    input [15:0] cx, input [15:0] cy, input [3:0] entry, input same_chip, input at_dst,
    input [4:0] offered, input [19:0] pruned, input [35:0] flags, input [3:0] here,
    input [29:0] occ_self,       // [(o*2+vc)*3+:3]: flits in the downstream buffer of output o, VC vc
    input [9:0] busy_self,       // [o*2+vc]: output VC held by another packet
    input [149:0] occ_nb,        // [(o*5+z)*6+vc*3+:3]: the same, reported by the neighbour behind o, for its output z
    input [79:0] q,              // [o*16+:16]: learned residuals for the current key
    input [2:0] rnd, input [6:0] static_in,
    output [5*CW-1:0] cost_all, output reg [2:0] idx, output [CW-1:0] vmin, output [GW-1:0] goal, output [6:0] static_out
);
`include "lb_funcs.vh"
    localparam SUB = LAYER ? 2 : 1;
    wire even = !x[0];

    // ---- remaining-path totals per candidate ----
    wire [31:0] T;               // [s*8+:8]
    wire [31:0] R_e;             // chiplet: 1 + distance entry candidate -> destination
    genvar s, t, o, z;
    generate
        if (LAYER) begin : ti
            for (s = 0; s < 4; s = s + 1) begin : c
                assign T[8*s+:8] = 2 * manh(x, y, cx[4*s+:4], cy[4*s+:4]) + 1 + manh(cx[4*s+:4], cy[4*s+:4], dst_x, dst_y);
            end
        end else begin : tc
            wire [15:0] ex, ey;
            for (t = 0; t < 4; t = t + 1) begin : e
                assign ex[4*t+:4] = {dst_x[3:2], slot_lx(t)};
                assign ey[4*t+:4] = {dst_y[3:2], slot_ly(t)};
                assign R_e[8*t+:8] = 1 + manh(ex[4*t+:4], ey[4*t+:4], dst_x, dst_y);
            end
            for (s = 0; s < 4; s = s + 1) begin : c
                wire [31:0] A;
                for (t = 0; t < 4; t = t + 1) begin : a
                    assign A[8*t+:8] = 2 * manh(cx[4*s+:4], cy[4*s+:4], ex[4*t+:4], ey[4*t+:4]) + R_e[8*t+:8];
                end
                wire [7:0] rest = min4m(A, entry);
                wire [7:0] dcur = manh(x, y, cx[4*s+:4], cy[4*s+:4]);
                assign T[8*s+:8] = same_chip ? dcur : dcur + 1 + rest;
            end
        end
    endgenerate

    // ---- output VCs ----
    wire [4:0] vcout;
    assign vcout[3:0] = (!LAYER && arr_hub) ? 4'b1111 : {4{vc}};
    assign vcout[4] = LAYER ? 1'b1 : ((arr_hub) ? 1'b1 : vc);

    // ---- best continuation behind each output ----
    wire [39:0] BC;              // [o*8+:8]
    generate
        for (o = 0; o < 4; o = o + 1) begin : hor
            wire even_n = (o == 1 || o == 3) ? !even : even;
            wire [3:0] pmask = pruned[o*4+:4];
            wire [15:0] mn;
            wire [3:0] here_n;
            for (s = 0; s < 4; s = s + 1) begin : c
                wire [8:0] f = flags[9*s+:9];
                wire eg0 = (o == 1) ? f[F_EGE2] : (o == 3) ? 1'b0 : f[F_EGT0];
                wire eg2 = (o == 1) ? f[F_EGE3] : (o == 3) ? 1'b0 : f[F_EGE2];
                wire el0 = (o == 3) ? f[F_ELEM2] : (o == 1) ? 1'b0 : f[F_ELT0];
                wire nl0 = (o == 0) ? f[F_NLEM2] : (o == 2) ? 1'b0 : f[F_NLT0];
                wire ng0 = (o == 2) ? f[F_NGE2] : (o == 0) ? 1'b0 : f[F_NGT0];
                assign mn[4*s+:4] = oe_moves(even_n, o, eg0, eg2, el0, nl0, ng0);
                assign here_n[s] = !eg0 && !el0 && !nl0 && !ng0;
            end
            wire [39:0] term;
            for (z = 0; z < 4; z = z + 1) begin : zz
                wire [3:0] pr = {pmask[3] && !here_n[3] && mn[12+z], pmask[2] && !here_n[2] && mn[8+z],
                                 pmask[1] && !here_n[1] && mn[4+z], pmask[0] && !here_n[0] && mn[0+z]};
                wire vz = vcout[o];
                wire [2:0] oc = occ_nb[(o*5+z)*6+(vz ? 3 : 0)+:3];
                wire [7:0] mt = min4m(T, pr);
                assign term[8*z+:8] = (|pr) ? mt - SUB + ({5'b0, oc} << W_SHIFT) : 8'hff;
            end
            wire [3:0] pr4 = pmask & here_n;
            wire vz4 = LAYER ? 1'b1 : vcout[o];
            wire [2:0] oc4 = occ_nb[(o*5+4)*6+(vz4 ? 3 : 0)+:3];
            wire [7:0] mt4 = min4m(T, pr4);
            // chiplet, destination phase: the neighbour is the destination, nothing is left
            assign term[39:32] = !(|pr4) ? 8'hff : (!LAYER && same_chip) ? 8'd0 : mt4 - SUB + ({5'b0, oc4} << W_SHIFT);
            assign BC[o*8+:8] = min2(min2(min2(term[7:0], term[15:8]), min2(term[23:16], term[31:24])), term[39:32]);
        end
        if (!HAS_HUB) begin : nohub
            assign BC[39:32] = 8'hff;
        end else if (LAYER) begin : hubi
            // Up link: the neighbour is the boundary router, arrival on its Hub port
            wire [8:0] g = flags_of(x, y, dst_x, dst_y);
            wire at = !g[F_EGT0] && !g[F_ELT0] && !g[F_NLT0] && !g[F_NGT0];
            wire [3:0] mz = CHIP_OE ? oe_moves(even, 3'd4, g[F_EGT0], g[F_EGE2], g[F_ELT0], g[F_NLT0], g[F_NGT0])
                                    : xy_moves(3'd4, g[F_EGT0], g[F_ELT0], g[F_NLT0], g[F_NGT0]);
            wire [31:0] oz = {5'b0, occ_nb[(4*5+3)*6+3+:3], 5'b0, occ_nb[(4*5+2)*6+3+:3],
                              5'b0, occ_nb[(4*5+1)*6+3+:3], 5'b0, occ_nb[(4*5+0)*6+3+:3]};
            wire [7:0] mo = min4m(oz, mz);
            wire [7:0] dd = manh(x, y, dst_x, dst_y);
            assign BC[39:32] = at ? 8'd0 : dd + (mo << W_SHIFT);
        end else begin : hubc
            // Down link: the neighbour is the interposer router below, all entry candidates still open
            wire [39:0] tz;
            wire [15:0] mz;
            wire [31:0] ah;
            for (t = 0; t < 4; t = t + 1) begin : e
                wire [3:0] ex = {dst_x[3:2], slot_lx(t)};
                wire [3:0] ey = {dst_y[3:2], slot_ly(t)};
                wire [8:0] g = flags_of(x, y, ex, ey);
                assign mz[4*t+:4] = oe_moves(even, 3'd4, g[F_EGT0], g[F_EGE2], g[F_ELT0], g[F_NLT0], g[F_NGT0]);
                assign ah[8*t+:8] = 2 * manh(x, y, ex, ey) + R_e[8*t+:8];
            end
            for (z = 0; z < 4; z = z + 1) begin : zz
                wire [3:0] pr = {entry[3] && mz[12+z], entry[2] && mz[8+z], entry[1] && mz[4+z], entry[0] && mz[0+z]};
                wire [2:0] oc = occ_nb[(4*5+z)*6+(vcout[4] ? 3 : 0)+:3];
                wire [7:0] mt = min4m(ah, pr);
                assign tz[8*z+:8] = (|pr) ? mt + ({5'b0, oc} << W_SHIFT) : 8'hff;
            end
            assign BC[39:32] = min2(min2(tz[7:0], tz[15:8]), min2(tz[23:16], tz[31:24]));
        end
    endgenerate

    // ---- cost per output ----
    wire [34:0] statics;
    generate
        for (o = 0; o < 5; o = o + 1) begin : cst
            wire [2:0] fl = occ_self[(o*2+(vcout[o] ? 1 : 0))*3+:3];
            wire bz = busy_self[o*2+(vcout[o] ? 1 : 0)];
            wire [7:0] bc = BC[o*8+:8];
            wire [7:0] cint = ({5'b0, fl} << W_SHIFT) + (bz ? BETA : 0) + 1 + bc;
            assign statics[o*7+:7] = 1 + bc[6:0];
            if (USE_Q) begin : wq
                wire signed [CW-1:0] c = $signed({1'b0, cint, {F{1'b0}}}) + $signed(q[o*16+:16]);
                assign cost_all[o*CW+:CW] = c;
            end else begin : nq
                assign cost_all[o*CW+:CW] = {1'b0, cint};
            end
        end
    endgenerate

    // ---- comparator tree ----
    wire [CW-1:0] maxv = {1'b0, {(CW-1){1'b1}}};
    wire [5*CW-1:0] cg;
    genvar g;
    generate
        for (g = 0; g < 5; g = g + 1) begin : gt
            assign cg[g*CW+:CW] = offered[g] ? cost_all[g*CW+:CW] : maxv;
        end
    endgenerate
    function [CW-1:0] smin(input [CW-1:0] a, input [CW-1:0] b);
        smin = ($signed(b) < $signed(a)) ? b : a;
    endfunction
    assign vmin = smin(smin(smin(cg[0*CW+:CW], cg[1*CW+:CW]), smin(cg[2*CW+:CW], cg[3*CW+:CW])), cg[4*CW+:CW]);

    // Ties: rotating priority from a small random state (the simulator draws a random tie break).
    wire [4:0] tie;
    generate
        for (g = 0; g < 5; g = g + 1) begin : tg
            assign tie[g] = offered[g] && cg[g*CW+:CW] == vmin;
        end
    endgenerate
    integer k, ix;
    reg done;
    always @* begin
        idx = 3'd0;
        done = 1'b0;
        for (k = 0; k < 5; k = k + 1) begin
            ix = rnd + k;
            if (ix >= 5) ix = ix - 5;
            if (ix >= 5) ix = ix - 5;
            if (!done && tie[ix]) begin
                idx = ix;
                done = 1'b1;
            end
        end
    end
    assign static_out = statics[idx*7+:7];

    // Goal for the previous router's update: 1 + v_here - its static estimate.
    wire [CW-1:0] vh = at_dst ? {CW{1'b0}} : vmin;
    assign goal = $signed({vh[CW-1], vh[CW-1], vh}) + $signed({1'b0, 1'b1, {F{1'b0}}}) -
                  $signed({1'b0, static_in, {F{1'b0}}});
endmodule

// Eq. (2) update: q + alpha (goal - q), alpha = 2^-S1 + 2^-S2 (S1 < S2), round to nearest, saturate to 16 bits.
module q_update #(parameter GW = 19, parameter S1 = 4, parameter S2 = 5) (
    input [15:0] q_i, input [GW-1:0] goal_i, output [15:0] q_new
);
    localparam XW = GW + S2 + 3;
    wire signed [XW-1:0] q = $signed(q_i);
    wire signed [XW-1:0] g = $signed(goal_i);
    wire signed [XW-1:0] d = g - q;
    wire signed [XW-1:0] x = (q <<< S2) + (d <<< (S2 - S1)) + d + (1 << (S2 - 1));
    wire signed [XW-1:0] r = x >>> S2;
    wire over = r > 32767;
    wire under = r < -32768;
    assign q_new = over ? 16'h7fff : under ? 16'h8000 : r[15:0];
endmodule

// LB-I, boundary router, Q-learning variant: the value of a head arriving from the interposer (no table on chiplet routers,
// so the residual is 0), and the goal returned to the interposer. XY in the destination chiplet.
module lbi_fb_chip #(parameter W_SHIFT = 1, parameter BETA = 0, parameter F = 8, parameter CW = 9 + F, parameter GW = CW + 2) (
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y,
    input [29:0] occ_self, input [9:0] busy_self, input [149:0] occ_nb, input [6:0] static_in,
    output [CW-1:0] vhere, output [GW-1:0] goal
);
`include "lb_funcs.vh"
    wire [8:0] g = flags_of(x, y, dst_x, dst_y);
    wire at = !g[F_EGT0] && !g[F_ELT0] && !g[F_NLT0] && !g[F_NGT0];
    wire [3:0] m = xy_moves(3'd4, g[F_EGT0], g[F_ELT0], g[F_NLT0], g[F_NGT0]);
    wire [1:0] o = m[0] ? 2'd0 : m[1] ? 2'd1 : m[2] ? 2'd2 : 2'd3;
    wire [7:0] dd = manh(x, y, dst_x, dst_y);
    // flags at the neighbour behind o
    wire eg0 = (o == 1) ? g[F_EGE2] : (o == 3) ? 1'b0 : g[F_EGT0];
    wire el0 = (o == 3) ? g[F_ELEM2] : (o == 1) ? 1'b0 : g[F_ELT0];
    wire nl0 = (o == 0) ? g[F_NLEM2] : (o == 2) ? 1'b0 : g[F_NLT0];
    wire ng0 = (o == 2) ? g[F_NGE2] : (o == 0) ? 1'b0 : g[F_NGT0];
    wire [3:0] mz = xy_moves({1'b0, o}, eg0, el0, nl0, ng0);
    wire [1:0] z = mz[0] ? 2'd0 : mz[1] ? 2'd1 : mz[2] ? 2'd2 : 2'd3;
    wire next_at = !eg0 && !el0 && !nl0 && !ng0;
    wire [2:0] oc_n = occ_nb[({1'b0, o}*5+z)*6+3+:3];
    wire [7:0] bc = next_at ? 8'd0 : (dd - 1) + ({5'b0, oc_n} << W_SHIFT);
    wire [2:0] fl = occ_self[({1'b0, o}*2+1)*3+:3];
    wire bz = busy_self[{1'b0, o}*2+1];
    wire [7:0] cint = ({5'b0, fl} << W_SHIFT) + (bz ? BETA : 0) + 1 + bc;
    assign vhere = at ? {CW{1'b0}} : {1'b0, cint, {F{1'b0}}};
    assign goal = $signed({vhere[CW-1], vhere[CW-1], vhere}) + $signed({1'b0, 1'b1, {F{1'b0}}}) -
                  $signed({1'b0, static_in, {F{1'b0}}});
endmodule
