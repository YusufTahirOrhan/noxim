// DEFT_FAST units (v21). Definitions follow selectFast and fastHops of src/DeftLateBinding.cpp; checked against them by tb/export_fast.cpp.
//
// The stages of a head:
//   stage A, while the head is on the link or moves to the buffer front: the routing relation, the path total per candidate, the Q residuals;
//   decision: H(o), the minimum of the totals over the candidates kept by o; cost(o) = w f + beta b + L + H [+ R]; the choice.
//   CUT = 1 registers the costs inside the decision, so it takes two cycles.
// f, b are registered every cycle, and L is registered at the receiving router, one cycle older (fast_regs).

// Stage A: the path total through each candidate. For a fixed router (x, y are constants in synthesis) the totals are a ROM on the
// destination, and with late exit on the entry mask of the source phase.
module fast_stage_a #(parameter LAYER = 1, parameter HAS_HUB = 1, parameter XW = 4) (
    input [3:0] x, input [3:0] y, input [2:0] last, input [3:0] dst_x, input [3:0] dst_y, input [3:0] exit_mask, input [3:0] entry,
    output [4:0] offered, output [19:0] pruned, output same_chip, output at_dst, output [31:0] T
);
`include "lb_funcs.vh"
    wire [35:0] flags;
    wire [3:0] here;
    wire [15:0] cx, cy;
    genvar s, t;
    generate
        if (LAYER) begin : ri
            lb_route_ipos #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dst_x[XW-1:0]), .dst_y_i(dst_y[XW-1:0]),
                .entry(entry), .offered(offered), .pruned(pruned), .flags(flags), .here(here), .cx(cx), .cy(cy));
            assign same_chip = 1'b0;
            assign at_dst = 1'b0;
            for (s = 0; s < 4; s = s + 1) begin : c
                assign T[8*s+:8] = 2 * manh(x, y, cx[4*s+:4], cy[4*s+:4]) + 1 + manh(cx[4*s+:4], cy[4*s+:4], dst_x, dst_y);
            end
        end else begin : rc
            wire [3:0] cand;
            lb_route_chip #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dst_x[XW-1:0]), .dst_y_i(dst_y[XW-1:0]),
                .exit_mask(exit_mask), .same_chip(same_chip), .at_dst(at_dst), .offered(offered), .pruned(pruned), .flags(flags),
                .here(here), .cx(cx), .cy(cy), .cand(cand));
            wire [15:0] ex, ey;
            wire [31:0] R_e;
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
endmodule

// The decision: registered inputs to the chosen output. All comparisons in parallel, so that the depth does not grow with the outputs as a
// chain of minima does. LAYER and the VN rules decide vcout outside this module.
module fast_decide #(parameter USE_Q = 0, parameter F = 0, parameter CUT = 0, parameter CW = 9 + F) (
    input clk,
    input [89:0] pre_p,          // [(o*2+v)*9+:9]: w f + beta b + L, summed in the previous cycle
    input [31:0] T,              // [s*8+:8]: path total through candidate s
    input [19:0] pruned,         // [o*4+:4]: candidates kept by o
    input [79:0] q,              // [o*16+:16]: R
    input [4:0] offered, input [4:0] vcout, input [2:0] rnd,
    output [39:0] h, output [5*CW-1:0] cost_all, output [4:0] offered_c, output reg [2:0] idx
);
`include "lb_funcs.vh"
    genvar o, j;
    wire [4:0] win;
    wire [5*CW-1:0] cost_d;
    // the comparisons of the candidates' totals, shared by all outputs; each bit: the lower-numbered candidate wins (also on equal totals)
    wire [5:0] le;
    assign le[0] = T[6:0] <= T[30:24];      // 0 against 3
    assign le[1] = T[14:8] <= T[30:24];     // 1 against 3
    assign le[2] = T[22:16] <= T[30:24];    // 2 against 3
    assign le[3] = T[6:0] <= T[22:16];      // 0 against 2
    assign le[4] = T[14:8] <= T[22:16];     // 1 against 2
    assign le[5] = T[6:0] <= T[14:8];       // 0 against 1
    generate
        for (o = 0; o < 5; o = o + 1) begin : c
            // H(o): the smallest total among the candidates kept by o, from the shared comparisons
            wire [3:0] m = pruned[4*o+:4];
            wire [3:0] best = {m[3] && (!m[0] || !le[0]) && (!m[1] || !le[1]) && (!m[2] || !le[2]),
                               m[2] && (!m[0] || !le[3]) && (!m[1] || !le[4]) && (!m[3] || le[2]),
                               m[1] && (!m[0] || !le[5]) && (!m[2] || le[4]) && (!m[3] || le[1]),
                               m[0] && (!m[1] || le[5]) && (!m[2] || le[3]) && (!m[3] || le[0])};
            // an output that keeps no candidate is not offered: its H is not read. The totals fit 7 bits (largest: 74, on 4x4).
            assign h[o*8+:8] = {1'b0, ({7{best[0]}} & T[6:0]) | ({7{best[1]}} & T[14:8]) | ({7{best[2]}} & T[22:16]) | ({7{best[3]}} & T[30:24])};
            // Value ranges: w f + beta b + L fits 6 bits and H 7 on the grids of the tuning.
            wire [8:0] p = {3'b0, pre_p[(o*2+(vcout[o] ? 1 : 0))*9+:6]};
            wire [8:0] hh = {2'b0, h[o*8+:7]};
            if (USE_Q) begin : wq
                // a carry-save step, then one carry chain: the fractional bits of R need no addition
                wire [CW-1:0] qs = $signed(q[o*16+:16]);
                wire [8:0] qi = qs[CW-1:F];
                wire [8:0] sum = p ^ hh ^ qi;
                wire [8:0] car = (p & hh) | (p & qi) | (hh & qi);
                wire [8:0] top = sum + {car[7:0], 1'b0};
                assign cost_d[o*CW+:CW] = {top, qs[F-1:0]};
            end else begin : nq
                assign cost_d[o*CW+:CW] = p + hh;
            end
        end
        if (CUT) begin : cr
            reg [5*CW-1:0] cost_r;
            reg [4:0] off_r;
            always @(posedge clk) begin
                cost_r <= cost_d;
                off_r <= offered;
            end
            assign cost_all = cost_r;
            assign offered_c = off_r;
        end else begin : nc
            assign cost_all = cost_d;
            assign offered_c = offered;
        end
        for (o = 0; o < 5; o = o + 1) begin : w
            wire [4:0] not_less;
            for (j = 0; j < 5; j = j + 1) begin : p
                if (j == o) begin : same
                    assign not_less[j] = 1'b1;
                end else if (USE_Q) begin : sg
                    assign not_less[j] = !offered_c[j] || !($signed(cost_all[j*CW+:CW]) < $signed(cost_all[o*CW+:CW]));
                end else begin : us
                    assign not_less[j] = !offered_c[j] || !(cost_all[j*CW+:CW] < cost_all[o*CW+:CW]);
                end
            end
            assign win[o] = offered_c[o] && &not_less;
        end
    endgenerate
    // Ties: one of two priority orders, from a small random state (the simulator draws a random tie break).
    wire [2:0] idx_up = win[0] ? 3'd0 : win[1] ? 3'd1 : win[2] ? 3'd2 : win[3] ? 3'd3 : 3'd4;
    wire [2:0] idx_down = win[4] ? 3'd4 : win[3] ? 3'd3 : win[2] ? 3'd2 : win[1] ? 3'd1 : 3'd0;
    always @* idx = rnd[0] ? idx_down : idx_up;
endmodule

// f, b registered per output and VC; the value this router sends over its links: the minimum of the registered terms over the outputs that
// exist. The receiving router registers it, so L is one cycle older than f, b there.
module fast_regs #(parameter W_SHIFT = 1, parameter BETA = 0, parameter GX = 2) (
    input clk, input [3:0] x, input [3:0] y, input hub_ok, input [29:0] occ_self, input [9:0] busy_self,
    output reg [79:0] pre_f, output [79:0] pre_f_d, output [7:0] l_out
);
`include "lb_funcs.vh"
    localparam MAXC = GX * 4 - 1;
    wire [4:0] exists = {hub_ok, x != 4'd0, y != MAXC[3:0], x != MAXC[3:0], y != 4'd0};
    wire [79:0] gated;
    genvar o, v;
    generate
        for (o = 0; o < 5; o = o + 1) begin : po
            for (v = 0; v < 2; v = v + 1) begin : pv
                assign pre_f_d[(o*2+v)*8+:8] = exists[o] ? ({5'b0, occ_self[(o*2+v)*3+:3]} << W_SHIFT) + (busy_self[o*2+v] ? BETA : 0) : 8'd0;
                assign gated[(o*2+v)*8+:8] = exists[o] ? pre_f[(o*2+v)*8+:8] : 8'hff;
            end
        end
    endgenerate
    always @(posedge clk) pre_f <= pre_f_d;
    wire [7:0] m0 = min2(gated[7:0], gated[15:8]), m1 = min2(gated[23:16], gated[31:24]), m2 = min2(gated[39:32], gated[47:40]);
    wire [7:0] m3 = min2(gated[55:48], gated[63:56]), m4 = min2(gated[71:64], gated[79:72]);
    wire [7:0] m = min2(min2(min2(m0, m1), min2(m2, m3)), m4);
    assign l_out = m == 8'hff ? 8'd0 : m;
endmodule

// LB-I boundary router, Q-learning: value of a head arriving from the interposer. XY offers one output and chiplet routers have no table.
module lbi_fb_fast #(parameter F = 8, parameter CW = 9 + F, parameter GW = CW + 2) (
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input [79:0] pre_f, input [39:0] pre_l, input [6:0] static_in,
    output [CW-1:0] vhere, output [GW-1:0] goal
);
`include "lb_funcs.vh"
    wire [8:0] g = flags_of(x, y, dst_x, dst_y);
    wire at = !g[F_EGT0] && !g[F_ELT0] && !g[F_NLT0] && !g[F_NGT0];
    wire [3:0] m = xy_moves(3'd4, g[F_EGT0], g[F_ELT0], g[F_NLT0], g[F_NGT0]);
    wire [2:0] o = m[0] ? 3'd0 : m[1] ? 3'd1 : m[2] ? 3'd2 : 3'd3;
    wire [7:0] dd = manh(x, y, dst_x, dst_y);
    wire [8:0] cint = pre_f[(o*2+1)*8+:8] + dd + pre_l[o*8+:8];
    assign vhere = at ? {CW{1'b0}} : {cint, {F{1'b0}}};
    assign goal = $signed({vhere[CW-1], vhere[CW-1], vhere}) + $signed({1'b0, 1'b1, {F{1'b0}}}) -
                  $signed({1'b0, static_in, {F{1'b0}}});
endmodule
