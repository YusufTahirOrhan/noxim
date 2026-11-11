// One interposer router of the v25 design: the reference core (core25.v) plus the late-binding units (lb25_units.v).
//
// MECH 0, LF (lookahead routing with the fallback), one decision unit per input port:
//   * the unit works on a head while it is on the link (stage A reads the header from the link) and its result is stored
//     per input VC, two entries per VC (packets have at least two flits, so a 4-flit buffer holds at most two heads);
//   * at the buffer front the route stage evaluates the relation only (offered outputs) and the VC-allocation stage asks
//     for an output: the only one, or the stored one with the fallback, every cycle until the allocator grants it;
//   * with XY a head that arrives from N or S has one candidate left (a chiplet has one VL per column), so those two
//     ports have no decision unit (ORDER_O = 0).
// MECH 1, DLY (the decision at the buffer front): a hop with one offered output is routed in the first cycle; otherwise
//   the head waits for the decision, 1 + CUT_A + CUT_M + CUT_B cycles. RS_PER_PORT 1: one unit per input port; 0: one unit
//   per router behind a round-robin over the input VCs (LF has no such form: heads arrive on several links in one cycle).
// ORDER_O: 0 XY, 1 the order of the VN (XY in VN0, YX in VN1). DBIAS: default-VL penalty (2 on 2x2, else 0).
// NOSEL 1: the relation without a selection (the first offered output is taken): the cost of the relation alone.
// The interposer keeps the VN of a packet on every output (the paper's Up rule), so the output VC is the input VC.
// The Local port of an interposer router carries no packets; as in every design of round 18 it has its buffers and a
// route unit (here the relation, no decision unit).
module router25_top #(
    parameter MECH = 0, parameter ORDER_O = 0, parameter DBIAS = 0, parameter HAS_HUB = 0, parameter RS_PER_PORT = 1,
    parameter CUT_A = 0, parameter CUT_M = 0, parameter CUT_B = 0, parameter XW = 3, parameter W_SHIFT = 1, parameter NOSEL = 0,
    // derived
    parameter P = HAS_HUB ? 6 : 5, parameter W = 32
) (
    input clk, input rst, input [XW-1:0] my_x, input [XW-1:0] my_y,
    input [P*W-1:0] in_flit, input [P-1:0] in_valid, input [P-1:0] in_vc, output [2*P-1:0] in_credit,
    output [P*W-1:0] out_flit, output [P-1:0] out_valid, output [P-1:0] out_vc, input [2*P-1:0] out_credit,
    // occupancy reports: own to the neighbours, the neighbours' (N, E, S, W, the boundary router above) registered on arrival
    output [29:0] occ_report, input [149:0] nb_report
);
    localparam HDRW = 4, HDRLSB = 14, LOCAL = 4, HUB = 5;
    localparam LATE = (MECH == 0);
    localparam NCUT = CUT_A + CUT_M + CUT_B;
    wire [3:0] x = my_x, y = my_y;
    wire [2*P-1:0] rt_req, rt_ack, rt_ovc, va_ok, tail_pop, pop, busy;
    wire [2*P*W-1:0] rt_front;
    wire [3*2*P-1:0] rt_port, va_port, occ;
    wire [(HDRW+1)*2*P-1:0] rt_hdr, va_hdr;

    router_core25 #(.P(P), .W(W), .HDRW(HDRW), .HDRLSB(HDRLSB), .ADAPTIVE(1), .LATE(LATE)) core (
        .clk(clk), .rst(rst), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit),
        .rt_req(rt_req), .rt_front(rt_front), .rt_ack(rt_ack), .rt_port(rt_port), .rt_ovc(rt_ovc), .rt_hdr(rt_hdr),
        .va_ok(va_ok), .va_port(va_port), .va_hdr(va_hdr), .occ(occ), .busy(busy), .pop_o(pop), .tail_pop_o(tail_pop));

    // ---- occupancy and VC state as the units see them: outputs N, E, S, W, Hub ----
    wire [29:0] occ5;
    wire [9:0] busy5, full5;
    assign occ5[23:0] = occ[23:0];
    assign busy5[7:0] = busy[7:0];
    generate
        if (HAS_HUB) begin : oh
            assign occ5[29:24] = occ[3*2*HUB+:6];
            assign busy5[9:8] = busy[2*HUB+:2];
        end else begin : ono
            assign occ5[29:24] = 6'd0;
            assign busy5[9:8] = 2'd0;
        end
    endgenerate
    genvar q;
    generate
        for (q = 0; q < 10; q = q + 1) begin : fl
            assign full5[q] = occ5[3*q+:3] == 3'd4;
        end
    endgenerate
    assign occ_report = occ5;
    wire [149:0] nb_r;
    generate
        if (NOSEL != 0) begin : noreg
            assign nb_r = 150'd0;
        end else begin : rg
            occ_regs25 #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O)) regs (.clk(clk), .in(nb_report), .out(nb_r));
        end
    endgenerate

    // tie-break state: free-running small LFSR
    (* v25r *) reg [2:0] rnd;
    always @(posedge clk) rnd <= rst ? 3'd1 : {rnd[1:0], rnd[2] ^ rnd[1]};

    genvar p, v, b, k2;
    generate
        if (MECH == 0) begin : lf
            for (p = 0; p < P; p = p + 1) begin : port
                // last move of a head that arrived on port p (N port: it moved south), 4 over the Down link (and for the Local port)
                localparam LASTP = (p == 0) ? 2 : (p == 1) ? 3 : (p == 2) ? 0 : (p == 3) ? 1 : 4;
                localparam DEC = (NOSEL == 0) && (p != LOCAL) && (ORDER_O || p == 1 || p == 3 || p == HUB);
                if (1) begin : lk
                    wire [5:0] st_dec;       // per VC: the stored decision of the head at the front
                    wire [1:0] st_val;
                    if (DEC) begin : dec
                        wire [W-1:0] lfl = in_flit[p*W+:W];
                        wire arr = in_valid[p] && lfl[30];
                        wire avc = in_vc[p];
                        (* v25r *) reg [1:0] wsel;            // per VC: entry of the next arriving head
                        (* v25r *) reg [1:0] rsel;            // per VC: entry of the head at the front
                        wire [1:0] tag_i = {avc, avc ? wsel[1] : wsel[0]};
                        wire v_c;
                        wire [1:0] tag_c;
                        wire [2:0] dec_c;
                        lb25_dec #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(LASTP), .DBIAS(DBIAS), .W_SHIFT(W_SHIFT), .CUT_A(CUT_A),
                                   .CUT_M(CUT_M), .CUT_B(CUT_B), .TAGW(2)) u (
                            .clk(clk), .rst(rst), .v_i(arr), .tag_i(tag_i), .x(x), .y(y), .last_i(3'd4), .vn_i(avc), .dst_x(lfl[29:26]),
                            .dst_y(lfl[25:22]), .cand(lfl[17:14]), .def_slot(lfl[13:12]), .occ_self(occ5), .occ_nb(nb_r), .rnd(rnd),
                            .offered(), .pruned(), .v_c(v_c), .tag_c(tag_c), .dec_c(dec_c), .dbg_cost(), .dbg_valid(), .dbg_o1h());
                        (* v25r *) reg [2:0] dmem [0:3];      // [{vc, entry}]
                        (* v25r *) reg [3:0] dval;
                        wire [1:0] hp = {pop[2*p+1] && rt_front[(2*p+1)*W+30], pop[2*p] && rt_front[(2*p)*W+30]};   // a head leaves
                        // a head with one offered output may leave before its decision is ready: that decision is dropped
                        wire kill = (NCUT != 0) && (tag_c[1] ? (hp[1] && rsel[1] == tag_c[0]) : (hp[0] && rsel[0] == tag_c[0]));
                        always @(posedge clk) begin
                            if (v_c) dmem[tag_c] <= dec_c;
                            if (rst) begin
                                wsel <= 2'b00;
                                rsel <= 2'b00;
                                dval <= 4'b0000;
                            end else begin
                                if (arr) wsel[avc] <= !wsel[avc];
                                if (hp[0]) begin
                                    rsel[0] <= !rsel[0];
                                    dval[{1'b0, rsel[0]}] <= 1'b0;
                                end
                                if (hp[1]) begin
                                    rsel[1] <= !rsel[1];
                                    dval[{1'b1, rsel[1]}] <= 1'b0;
                                end
                                // after the clears: a head may arrive in the cycle in which the head that used its entry leaves
                                if (v_c && !kill) dval[tag_c] <= 1'b1;
                            end
                        end
                        assign st_dec = {dmem[{1'b1, rsel[1]}], dmem[{1'b0, rsel[0]}]};
                        assign st_val = {dval[{1'b1, rsel[1]}], dval[{1'b0, rsel[0]}]};
                    end else begin : nodec
                        assign st_dec = 6'd0;
                        assign st_val = 2'b11;
                    end
                    for (v = 0; v < 2; v = v + 1) begin : vc
                        localparam I = 2 * p + v;
                        wire [W-1:0] fr = rt_front[I*W+:W];
                        wire [4:0] offered;
                        wire [19:0] pruned;
                        lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(LASTP), .VNFIX(v)) r (.x(x), .y(y), .last_i(3'd4), .vn(1'b0),
                            .dst_x(fr[29:26]), .dst_y(fr[25:22]), .cand(fr[17:14]), .offered(offered), .pruned(pruned),
                            .mv(), .here(), .fl(), .yx());
                        // route stage: the offered outputs of the head at the front
                        (* v25r *) reg [4:0] off_r;
                        always @(posedge clk) if (rt_req[I]) off_r <= offered;
                        assign rt_ack[I] = rt_req[I];
                        assign rt_ovc[I] = v;
                        assign rt_port[3*I+:3] = 3'd0;
                        assign rt_hdr[(HDRW+1)*I+:HDRW+1] = {(HDRW+1){1'b0}};
                        // VC-allocation stage: the only output, or the stored one with the fallback
                        wire single;
                        wire [2:0] only, fb;
                        lb25_single sg (.offered(off_r), .single(single), .only(only));
                        wire [4:0] free = {!busy5[8+v] && !full5[8+v], !busy5[6+v] && !full5[6+v], !busy5[4+v] && !full5[4+v],
                                           !busy5[2+v] && !full5[2+v], !busy5[0+v] && !full5[0+v]};
                        lb25_fallback f (.stored(st_dec[3*v+:3]), .offered(off_r), .free(free), .req(fb));
                        wire [2:0] sel = (single || !DEC) ? only : fb;
                        assign va_ok[I] = single || st_val[v];
                        assign va_port[3*I+:3] = (sel == 3'd4) ? 3'd5 : sel;
                        assign va_hdr[(HDRW+1)*I+:HDRW+1] = {1'b0, pruned[sel*4+:4]};
                    end
                end
            end
        end else begin : dly
            localparam NB = RS_PER_PORT ? P : 1;      // route units
            localparam G = RS_PER_PORT ? 2 : 2 * P;   // input VCs per unit
            assign va_ok = {2*P{1'b0}};
            assign va_port = {3*2*P{1'b0}};
            assign va_hdr = {(HDRW+1)*2*P{1'b0}};
            for (b = 0; b < NB; b = b + 1) begin : unit
                localparam BASE = RS_PER_PORT ? 2 * b : 0;
                localparam LASTB = !RS_PER_PORT ? -1 : (b == 0) ? 2 : (b == 1) ? 3 : (b == 2) ? 0 : (b == 3) ? 1 : 4;
                // with XY a head from N or S has one candidate left; the Local port carries no packets: the relation is enough there
                localparam RELONLY = (NOSEL != 0) || (RS_PER_PORT && (b == LOCAL || (!ORDER_O && (b == 0 || b == 2))));
                if (1) begin : u
                    (* v25r *) reg [G-1:0] infl;      // the head whose decision is in the pipeline
                    wire held = |infl;
                    wire [G-1:0] g_new;
                    rr_arb #(.N(G)) arb (.clk(clk), .rst(rst), .req(rt_req[BASE+:G] & {G{!held}}), .adv(1'b1), .gnt(g_new));
                    wire [G-1:0] g = held ? infl : g_new;
                    // the selected head, its input port and VC
                    reg [W-1:0] fr;
                    reg [2:0] ip;
                    reg vc_in;
                    integer k;
                    always @* begin
                        fr = {W{1'b0}};
                        ip = 3'd0;
                        vc_in = 1'b0;
                        for (k = 0; k < G; k = k + 1)
                            if (g[k]) begin
                                fr = fr | rt_front[(BASE+k)*W+:W];
                                ip = ip | ((BASE + k) / 2);
                                vc_in = vc_in | ((BASE + k) % 2);
                            end
                    end
                    wire [2:0] last = (ip == 3'd0) ? 3'd2 : (ip == 3'd1) ? 3'd3 : (ip == 3'd2) ? 3'd0 : (ip == 3'd3) ? 3'd1 : 3'd4;
                    wire [4:0] offered;
                    wire [19:0] pruned;
                    wire single, v_c;
                    wire [2:0] only, dec_c;
                    wire tag_c;
                    lb25_single sg (.offered(offered), .single(single), .only(only));
                    wire submit = !RELONLY && |g_new && !single;
                    if (RELONLY) begin : relonly
                        lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(LASTB), .VNFIX(-1)) r (.x(x), .y(y), .last_i(last), .vn(vc_in),
                            .dst_x(fr[29:26]), .dst_y(fr[25:22]), .cand(fr[17:14]), .offered(offered), .pruned(pruned),
                            .mv(), .here(), .fl(), .yx());
                        assign v_c = 1'b0;
                        assign tag_c = 1'b0;
                        assign dec_c = 3'd0;
                    end else begin : full
                        lb25_dec #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(LASTB), .DBIAS(DBIAS), .W_SHIFT(W_SHIFT), .CUT_A(CUT_A),
                                   .CUT_M(CUT_M), .CUT_B(CUT_B), .TAGW(1)) d (
                            .clk(clk), .rst(rst), .v_i(submit), .tag_i(1'b0), .x(x), .y(y), .last_i(last), .vn_i(vc_in), .dst_x(fr[29:26]),
                            .dst_y(fr[25:22]), .cand(fr[17:14]), .def_slot(fr[13:12]), .occ_self(occ5), .occ_nb(nb_r), .rnd(rnd),
                            .offered(offered), .pruned(pruned), .v_c(v_c), .tag_c(tag_c), .dec_c(dec_c), .dbg_cost(), .dbg_valid(), .dbg_o1h());
                    end
                    always @(posedge clk) begin
                        if (rst) infl <= {G{1'b0}};
                        else if (v_c) infl <= {G{1'b0}};
                        else if (submit && NCUT != 0) infl <= g_new;
                    end
                    wire done = (|g_new && (single || RELONLY)) || v_c;
                    wire [2:0] sel = v_c ? dec_c : only;
                    wire [2:0] o = (sel == 3'd4) ? 3'd5 : sel;
                    for (k2 = 0; k2 < G; k2 = k2 + 1) begin : dd
                        assign rt_ack[BASE+k2] = g[k2] && done;
                        assign rt_port[3*(BASE+k2)+:3] = o;
                        assign rt_ovc[BASE+k2] = vc_in;
                        assign rt_hdr[(HDRW+1)*(BASE+k2)+:HDRW+1] = {1'b0, pruned[sel*4+:4]};
                    end
                end
            end
        end
    endgenerate
endmodule
