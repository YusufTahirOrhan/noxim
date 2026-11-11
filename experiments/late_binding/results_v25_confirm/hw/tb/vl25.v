// v25 F2: wrappers of the units for the Verilator vector checkers (vl_sel25.cpp, vl_front25.cpp). The same instances as
// in tb25.v: the generic unit and the units specialised by arrival direction (and VN), with and without a Hub port.
// sel picks the unit whose outputs are read. Units 0.. have a Hub port, the second half has none.

module vl_sel25 #(parameter ORDER_O = 0, parameter DBIAS = 0, parameter CUT_A = 0, parameter CUT_M = 0, parameter CUT_B = 0) (
    input clk, input [3:0] x, input [3:0] y, input [3:0] dx, input [3:0] dy, input [3:0] mask, input [2:0] last, input vn,
    input [1:0] def, input [2:0] rnd, input [29:0] occ_self,
    input [29:0] nb0, input [29:0] nb1, input [29:0] nb2, input [29:0] nb3, input [29:0] nb4,
    input [3:0] sel,
    output [4:0] off, output [19:0] pr, output [2:0] dec,
    output [39:0] cmin           // [o*8+:8]: least cost of a candidate kept by output o (ff: none)
);
    wire [149:0] occ_nb = {nb4, nb3, nb2, nb1, nb0};
    wire [12*5-1:0] off_all;
    wire [12*20-1:0] pr_all, o1h_all;
    wire [12*3-1:0] dec_all;
    wire [12*28-1:0] cost_all;
    wire [12*4-1:0] val_all;
    genvar hh, ll, o;
    generate
        for (hh = 0; hh < 2; hh = hh + 1) begin : h
            for (ll = 0; ll < 6; ll = ll + 1) begin : l
                localparam U = hh * 6 + ll;
                lb25_dec #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(ll - 1), .DBIAS(DBIAS), .W_SHIFT(1), .CUT_A(CUT_A), .CUT_M(CUT_M), .CUT_B(CUT_B), .TAGW(1)) d (
                    .clk(clk), .rst(1'b0), .v_i(1'b1), .tag_i(1'b0), .x(x), .y(y), .last_i(last), .vn_i(vn), .dst_x(dx), .dst_y(dy), .cand(mask),
                    .def_slot(def), .occ_self(occ_self), .occ_nb(occ_nb), .rnd(rnd), .offered(off_all[5*U+:5]), .pruned(pr_all[20*U+:20]),
                    .v_c(), .tag_c(), .dec_c(dec_all[3*U+:3]), .dbg_cost(cost_all[28*U+:28]), .dbg_valid(val_all[4*U+:4]), .dbg_o1h(o1h_all[20*U+:20]));
            end
        end
    endgenerate
    assign off = off_all[5*sel+:5];
    assign pr = pr_all[20*sel+:20];
    assign dec = dec_all[3*sel+:3];
    wire [27:0] cost = cost_all[28*sel+:28];
    wire [3:0] val = val_all[4*sel+:4];
    wire [19:0] o1h = o1h_all[20*sel+:20];
    generate
        for (o = 0; o < 5; o = o + 1) begin : m
            wire [7:0] c0 = (val[0] && o1h[o]) ? {1'b0, cost[6:0]} : 8'hff;
            wire [7:0] c1 = (val[1] && o1h[5+o]) ? {1'b0, cost[13:7]} : 8'hff;
            wire [7:0] c2 = (val[2] && o1h[10+o]) ? {1'b0, cost[20:14]} : 8'hff;
            wire [7:0] c3 = (val[3] && o1h[15+o]) ? {1'b0, cost[27:21]} : 8'hff;
            wire [7:0] a = (c1 < c0) ? c1 : c0;
            wire [7:0] b = (c3 < c2) ? c3 : c2;
            assign cmin[8*o+:8] = (b < a) ? b : a;
        end
    endgenerate
endmodule

module vl_front25 #(parameter ORDER_O = 0) (
    input [3:0] x, input [3:0] y, input [3:0] dx, input [3:0] dy, input [3:0] mask, input [2:0] last, input vn,
    input [2:0] stored, input [4:0] free, input [4:0] sel,
    output [4:0] off, output [19:0] pr, output single, output [2:0] only, output [2:0] fb
);
    wire [22*5-1:0] off_all;
    wire [22*20-1:0] pr_all;
    genvar hh, ll, vv;
    generate
        for (hh = 0; hh < 2; hh = hh + 1) begin : h
            lb25_rel #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(-1), .VNFIX(-1)) gen (.x(x), .y(y), .last_i(last), .vn(vn), .dst_x(dx), .dst_y(dy),
                .cand(mask), .offered(off_all[5*(hh*11)+:5]), .pruned(pr_all[20*(hh*11)+:20]), .mv(), .here(), .fl(), .yx());
            for (ll = 0; ll < 5; ll = ll + 1) begin : l
                for (vv = 0; vv < 2; vv = vv + 1) begin : v
                    localparam U = hh * 11 + 1 + ll * 2 + vv;
                    lb25_rel #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(ll), .VNFIX(vv)) sp (.x(x), .y(y), .last_i(3'd4), .vn(1'b0), .dst_x(dx),
                        .dst_y(dy), .cand(mask), .offered(off_all[5*U+:5]), .pruned(pr_all[20*U+:20]), .mv(), .here(), .fl(), .yx());
                end
            end
        end
    endgenerate
    assign off = off_all[5*sel+:5];
    assign pr = pr_all[20*sel+:20];
    lb25_single sg (.offered(off), .single(single), .only(only));
    lb25_fallback fbk (.stored(stored), .offered(off), .free(free), .req(fb));
endmodule
