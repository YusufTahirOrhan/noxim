// v25: chiplet router of the final design where the default-VL penalty is used (2x2, D = 2).
// It is the LB-I chiplet router of round 18 (results_v18_area/rtl/router_top.v with METHOD 6: exit LUT of (C - 1) x 2 bits,
// fault table of 4 C bits, XY, DeFT's VN rules) plus one table: the default entry VL of a packet is DeFT-P's entry VL of
// its destination router, which the source cannot compute (it depends on the fault scenario), so the NI reads it from a
// table of 16 (C - 1) entries of 2 bits (destination router of another chiplet -> slot) and writes it into the head
// (bits [13:12]). Routers pass the two bits on unchanged; the interposer routers read them.
// On 3x3 and 4x4 the penalty is 0: no table, no header bits, and the chiplet router is the round-18 router itself.
module chip25_top #(
    parameter HAS_HUB = 0, parameter C = 4, parameter GX = 2, parameter XW = 3, parameter KW = 2, parameter F = 10,
    parameter P = HAS_HUB ? 6 : 5, parameter W = 32, parameter CW = 9 + F, parameter GW = CW + 2
) (
    input clk, input rst, input [XW-1:0] my_x, input [XW-1:0] my_y,
    input [P*W-1:0] in_flit, input [P-1:0] in_valid, input [P-1:0] in_vc, output [2*P-1:0] in_credit,
    output [P*W-1:0] out_flit, output [P-1:0] out_valid, output [P-1:0] out_vc, input [2*P-1:0] out_credit,
    output pe_ready,
    output [29:0] occ_report, input [149:0] nb_report,
    output [4:0] fb_out_v, output [5*GW-1:0] fb_out_g, output [5*KW-1:0] fb_out_k,
    input [4:0] fb_in_v, input [5*GW-1:0] fb_in_g, input [5*KW-1:0] fb_in_k,
    output rc_req_out, input rc_grant_in, input [15:0] rc_req_in, output [15:0] rc_grant_out,
    input [3:0] cfg_we, input [12:0] cfg_addr, input [3:0] cfg_data
);
    localparam LOCAL = 4;
    wire [3:0] x = my_x, y = my_y;
    wire [W-1:0] pe = in_flit[LOCAL*W+:W];
    wire [3:0] pd_x = pe[26+:XW], pd_y = pe[22+:XW];
    wire [KW-1:0] own, dk;
    chip_index #(.GX(GX), .KW(KW)) i0 (.gx(x[3:2]), .gy(y[3:2]), .idx(own));
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(pd_x[3:2]), .gy(pd_y[3:2]), .idx(dk));
    wire [KW-1:0] a = (dk < own) ? dk : dk - 1'b1;
    wire [1:0] def_slot;
    cfg_table #(.N(16 * (C - 1)), .W(2), .AW(KW + 4), .NRD(1)) deftab (.clk(clk), .cfg_we(cfg_we[3]), .cfg_addr(cfg_addr[KW+3:0]),
        .cfg_data(cfg_data[1:0]), .raddr({a, pd_y[1:0], pd_x[1:0]}), .rdata(def_slot));
    reg [P*W-1:0] flit_i;
    always @* begin
        flit_i = in_flit;
        if (pe[30]) flit_i[LOCAL*W+12+:2] = def_slot;
    end
    router_top #(.METHOD(6), .LAYER(0), .HAS_HUB(HAS_HUB), .C(C), .GX(GX), .XW(XW), .KW(KW), .F(F)) r (
        .clk(clk), .rst(rst), .my_x(my_x), .my_y(my_y), .in_flit(flit_i), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .pe_ready(pe_ready),
        .occ_report(occ_report), .nb_report(nb_report), .fb_out_v(fb_out_v), .fb_out_g(fb_out_g), .fb_out_k(fb_out_k),
        .fb_in_v(fb_in_v), .fb_in_g(fb_in_g), .fb_in_k(fb_in_k), .rc_req_out(rc_req_out), .rc_grant_in(rc_grant_in),
        .rc_req_in(rc_req_in), .rc_grant_out(rc_grant_out), .cfg_we(cfg_we[2:0]), .cfg_addr(cfg_addr), .cfg_data(cfg_data));
endmodule
