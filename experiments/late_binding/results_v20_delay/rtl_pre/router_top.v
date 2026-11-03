// One router of one method (v18): the reference core plus the method's units.
// METHOD: 0 reference, 1 DeFT, 2 DeFT with all 14 fault scenarios, 3 MTR, 4 RC, 5 DeFT-Dis, 6 LB-I heuristic, 7 LB-I Q-learning,
//         8 LB-F heuristic, 9 LB-F Q-learning.
// LAYER: 0 chiplet, 1 interposer. HAS_HUB: 6 ports (boundary router / interposer router with a VL) or 5.
// RS_PER_PORT: 0 one routing + selection unit per router, 1 one per input port (late-binding methods only).
module router_top #(
    parameter METHOD = 0, parameter LAYER = 0, parameter HAS_HUB = 0, parameter C = 4, parameter GX = 2, parameter XW = 3,
    parameter KW = 2, parameter F = 10, parameter W_SHIFT = 1, parameter BETA = 0, parameter S1 = 5, parameter S2 = 6,
    parameter RS_PER_PORT = 0, parameter PIPE = 0, parameter PRE = 0,
    // derived
    parameter P = HAS_HUB ? 6 : 5, parameter W = 32,
    parameter CW = 9 + F, parameter GW = CW + 2
) (
    input clk, input rst, input [XW-1:0] my_x, input [XW-1:0] my_y,
    // links; the Local port takes the processing element's flits through the NI
    input [P*W-1:0] in_flit, input [P-1:0] in_valid, input [P-1:0] in_vc, output [2*P-1:0] in_credit,
    output [P*W-1:0] out_flit, output [P-1:0] out_valid, output [P-1:0] out_vc, input [2*P-1:0] out_credit,
    output pe_ready,
    // occupancy reports: own to the neighbours, the neighbours' registered on arrival
    output [29:0] occ_report, input [149:0] nb_report,
    // learning feedback: returned towards the previous router; received from the next routers (N, E, S, W, Hub)
    output [4:0] fb_out_v, output [5*GW-1:0] fb_out_g, output [5*KW-1:0] fb_out_k,
    input [4:0] fb_in_v, input [5*GW-1:0] fb_in_g, input [5*KW-1:0] fb_in_k,
    // RC permission lines
    output rc_req_out, input rc_grant_in, input [15:0] rc_req_in, output [15:0] rc_grant_out,
    // table configuration
    input [2:0] cfg_we, input [12:0] cfg_addr, input [3:0] cfg_data
);
    function integer clog2(input integer v);
        integer i;
        begin
            clog2 = 0;
            for (i = v - 1; i > 0; i = i >> 1) clog2 = clog2 + 1;
        end
    endfunction
    localparam LBI = (METHOD == 6 || METHOD == 7);
    localparam LBF = (METHOD == 8 || METHOD == 9);
    localparam USE_Q = (METHOD == 7 || METHOD == 9);
    localparam LB_HERE = LBF || (LBI && LAYER == 1);   // the routing + selection logic lives on this router
    localparam VN = (METHOD == 1 || METHOD == 2 || METHOD == 5 || LBI || LBF);
    localparam LBI_FB = (METHOD == 7 && LAYER == 0 && HAS_HUB);
    localparam RCB = (METHOD == 4 && LAYER == 0 && HAS_HUB);
    localparam HDRW = !LB_HERE ? 0 : USE_Q ? (LBF ? 16 : 12) : (LBF ? 8 : 4);
    localparam HDRLSB = USE_Q ? 6 : 14;
    localparam LOCAL = 4, HUB = 5;

    wire [3:0] x = my_x, y = my_y;
    wire [2*P-1:0] rt_req, rt_ack, rt_ovc, tail_pop, busy;
    wire [2*P*W-1:0] rt_front;
    wire [3*2*P-1:0] rt_port, occ;
    wire [(HDRW+1)*2*P-1:0] rt_hdr;

    // ---- own slot of a boundary router ----
    wire own_vl = (LAYER == 0) && HAS_HUB;
    wire [1:0] lx = x[1:0], ly = y[1:0];
    wire [1:0] own_slot = (lx == 2'd1 && ly == 2'd0) ? 2'd0 : (lx == 2'd3 && ly == 2'd1) ? 2'd1 : (lx == 2'd2 && ly == 2'd3) ? 2'd2 : 2'd3;

    // ---- NI on chiplet routers: fills the head's routing fields and the VC ----
    wire [W-1:0] pe_flit = in_flit[LOCAL*W+:W];
    wire pe_valid = in_valid[LOCAL];
    wire pe_head = pe_valid && pe_flit[30];
    wire [3:0] pd_x = pe_flit[26+:XW], pd_y = pe_flit[22+:XW];
    wire [3:0] ni_exit, ni_entry;
    wire ni_vc_head;
    wire ni_stall;      // RC: the head waits for its permit
    generate
        if (LAYER == 1) begin : ni_none
            assign ni_exit = pe_flit[21:18];
            assign ni_entry = pe_flit[17:14];
            assign ni_vc_head = in_vc[LOCAL];
            assign ni_stall = 1'b0;
        end else if (METHOD == 0) begin : ni_ref
            assign ni_exit = pe_flit[21:18];
            assign ni_entry = pe_flit[17:14];
            ni_vcdraw vd (.clk(clk), .rst(rst), .inject_head(pe_head), .vc(ni_vc_head));
            assign ni_stall = 1'b0;
        end else if (METHOD == 1 || METHOD == 2) begin : ni_d
            localparam SCEN = (METHOD == 2) ? 14 : 1;
            localparam AW = clog2(SCEN * (C - 1));
            wire [1:0] ex, en;
            wire [3:0] scen;
            generate_scen #(.ON(METHOD == 2)) sc (.clk(clk), .we(cfg_we[1]), .d(cfg_data), .q(scen));
            ni_deft #(.C(C), .GX(GX), .KW(KW), .SCEN(SCEN), .AW(AW)) n (.clk(clk), .rst(rst), .cfg_we(cfg_we[0]), .cfg_addr(cfg_addr[AW-1:0]),
                .cfg_data(cfg_data), .scen_sel(scen), .x(x), .y(y), .dst_x(pd_x), .dst_y(pd_y), .head(pe_head), .own_vl(own_vl),
                .own_slot(own_slot), .exit_slot(ex), .entry_slot(en), .vc(ni_vc_head));
            assign ni_exit = {2'b0, ex};
            assign ni_entry = {2'b0, en};
            assign ni_stall = 1'b0;
        end else if (METHOD == 3) begin : ni_m
            wire [1:0] ex, en;
            ni_mtr #(.C(C), .GX(GX), .KW(KW), .AW(KW + 4)) n (.clk(clk), .rst(rst), .cfg_we(cfg_we[0]), .cfg_we_exit(cfg_we[1]),
                .cfg_addr(cfg_addr[KW+3:0]), .cfg_data(cfg_data[1:0]), .dst_x(pd_x), .dst_y(pd_y), .head(pe_head),
                .exit_slot(ex), .entry_slot(en), .vc(ni_vc_head));
            assign ni_exit = {2'b0, ex};
            assign ni_entry = {2'b0, en};
            assign ni_stall = 1'b0;
        end else if (METHOD == 4) begin : ni_r
            wire [1:0] ex, en;
            near_vl #(.FIXED(1)) nx (.lx(x[1:0]), .ly(y[1:0]), .fmask(4'hf), .slot(ex));
            near_vl #(.FIXED(1)) ne (.lx(pd_x[1:0]), .ly(pd_y[1:0]), .fmask(4'hf), .slot(en));
            ni_vcdraw vd (.clk(clk), .rst(rst), .inject_head(pe_head && !ni_stall), .vc(ni_vc_head));
            wire other = x[3:2] != pd_x[3:2] || y[3:2] != pd_y[3:2];
            wire may;
            rc_ni rn (.clk(clk), .rst(rst), .want(pe_head && other), .head_sent(pe_head && other && may), .grant(rc_grant_in),
                      .req(rc_req_out), .may_send(may));
            assign ni_stall = pe_head && other && !may;
            assign ni_exit = {2'b0, ex};
            assign ni_entry = {2'b0, en};
        end else if (METHOD == 5) begin : ni_s
            wire [1:0] ex, en;
            ni_dis #(.C(C), .GX(GX), .KW(KW)) n (.clk(clk), .rst(rst), .cfg_we(cfg_we[0]), .cfg_addr(cfg_addr[KW-1:0]), .cfg_data(cfg_data),
                .x(x), .y(y), .dst_x(pd_x), .dst_y(pd_y), .head(pe_head), .own_vl(own_vl), .own_slot(own_slot),
                .exit_slot(ex), .entry_slot(en), .vc(ni_vc_head));
            assign ni_exit = {2'b0, ex};
            assign ni_entry = {2'b0, en};
            assign ni_stall = 1'b0;
        end else if (LBI) begin : ni_i
            wire [1:0] ex;
            ni_lbi #(.C(C), .GX(GX), .KW(KW)) n (.clk(clk), .rst(rst), .cfg_we_lut(cfg_we[0]), .cfg_we_fault(cfg_we[1]),
                .cfg_addr(cfg_addr[KW-1:0]), .cfg_data(cfg_data), .x(x), .y(y), .dst_x(pd_x), .dst_y(pd_y), .head(pe_head), .own_vl(own_vl),
                .own_slot(own_slot), .exit_slot(ex), .entry_mask(ni_entry), .vc(ni_vc_head));
            assign ni_exit = {2'b0, ex};
            assign ni_stall = 1'b0;
        end else begin : ni_f
            ni_lbf #(.C(C), .GX(GX), .KW(KW)) n (.clk(clk), .rst(rst), .cfg_we(cfg_we[0]), .cfg_addr(cfg_addr[KW-1:0]), .cfg_data(cfg_data),
                .x(x), .y(y), .dst_x(pd_x), .dst_y(pd_y), .head(pe_head), .own_vl(own_vl), .own_slot(own_slot),
                .exit_mask(ni_exit), .entry_mask(ni_entry), .vc(ni_vc_head));
            assign ni_stall = 1'b0;
        end
        if (!(METHOD == 4 && LAYER == 0)) begin : no_rcni
            assign rc_req_out = 1'b0;
        end
    endgenerate
    assign pe_ready = !ni_stall;

    // The VC of a packet's head holds for its body and tail.
    reg vc_hold;
    always @(posedge clk) if (pe_head && !ni_stall) vc_hold <= ni_vc_head;
    wire pe_vc = pe_flit[30] ? ni_vc_head : vc_hold;
    reg [P*W-1:0] core_in_flit;
    reg [P-1:0] core_in_valid, core_in_vc;
    always @* begin
        core_in_flit = in_flit;
        core_in_valid = in_valid;
        core_in_vc = in_vc;
        if (LAYER == 0) begin
            core_in_flit[LOCAL*W+21:LOCAL*W+14] = pe_flit[30] ? {ni_exit, ni_entry} : pe_flit[21:14];
            core_in_vc[LOCAL] = pe_vc;
            core_in_valid[LOCAL] = pe_valid && !ni_stall;
        end
    end

    // ---- RC buffer on the Hub output of a boundary router ----
    wire [P*W-1:0] core_out_flit;
    wire [P-1:0] core_out_valid, core_out_vc;
    wire [2*P-1:0] core_credit;
    generate
        if (RCB) begin : rcb
            wire [W-1:0] rf;
            wire rv, rc;
            wire [1:0] cc;
            wire rel;
            rc_buffer #(.W(W)) b (.clk(clk), .rst(rst), .wr(core_out_valid[HUB]), .wr_vc(core_out_vc[HUB]),
                .din(core_out_flit[HUB*W+:W]), .credit_to_core(cc), .out_flit(rf), .out_valid(rv), .out_vc(rc),
                .out_credit(out_credit[2*HUB+:2]), .release_slot(rel));
            rc_opic_br br (.clk(clk), .rst(rst), .req(rc_req_in), .release_slot(rel), .grant(rc_grant_out));
            assign out_flit = {rf, core_out_flit[HUB*W-1:0]};
            assign out_valid = {rv, core_out_valid[HUB-1:0]};
            assign out_vc = {rc, core_out_vc[HUB-1:0]};
            assign core_credit = {cc, out_credit[2*HUB-1:0]};
        end else begin : norcb
            assign out_flit = core_out_flit;
            assign out_valid = core_out_valid;
            assign out_vc = core_out_vc;
            assign core_credit = out_credit;
            assign rc_grant_out = 16'b0;
        end
    endgenerate

    router_core #(.P(P), .W(W), .HDRW(HDRW), .HDRLSB(HDRLSB), .ADAPTIVE(LB_HERE)) core (
        .clk(clk), .rst(rst), .in_flit(core_in_flit), .in_valid(core_in_valid), .in_vc(core_in_vc), .in_credit(in_credit),
        .out_flit(core_out_flit), .out_valid(core_out_valid), .out_vc(core_out_vc), .out_credit(core_credit),
        .rt_req(rt_req), .rt_front(rt_front), .rt_ack(rt_ack), .rt_port(rt_port), .rt_ovc(rt_ovc), .rt_hdr(rt_hdr),
        .occ(occ), .busy(busy), .tail_pop_o(tail_pop));

    // ---- occupancy as the selection and the neighbours see it: N, E, S, W, Hub ----
    wire [29:0] occ5;
    wire [9:0] busy5;
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
    assign occ_report = occ5;

    wire [149:0] nb_r;
    generate
        if (LB_HERE) begin : rp
            occ_regs #(.NDIR(HAS_HUB ? 5 : 4)) regs (.clk(clk), .in(nb_report), .out(nb_r));
        end else if (LBI_FB) begin : rpf
            occ_regs #(.NDIR(4)) regs (.clk(clk), .in(nb_report), .out(nb_r));
        end else begin : rno
            assign nb_r = 150'd0;
        end
    endgenerate

    // ---- routing ----
    genvar p, v, b, k2, d5;
    generate
        if (!LB_HERE) begin : det
            // one simple routing unit per input port
            wire [2*P-1:0] fb_g;
            for (p = 0; p < P; p = p + 1) begin : port
                wire [1:0] g;
                rr_arb #(.N(2)) arb (.clk(clk), .rst(rst), .req(rt_req[2*p+:2]), .adv(1'b1), .gnt(g));
                assign fb_g[2*p+:2] = g;
                wire [W-1:0] fr = g[1] ? rt_front[(2*p+1)*W+:W] : rt_front[(2*p)*W+:W];
                wire [XW-1:0] dx = fr[26+:XW], dy = fr[22+:XW];
                wire vc_in = g[1];
                wire [2:0] o;
                if (METHOD == 0) begin : r0
                    rt_ref #(.XW(XW), .LAYER(LAYER), .HAS_HUB(HAS_HUB)) r (.x_i(my_x), .y_i(my_y), .dst_x_i(dx), .dst_y_i(dy), .port(o));
                end else if (LAYER == 0) begin : rc
                    rt_chip_xy #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(my_x), .y_i(my_y), .dst_x_i(dx), .dst_y_i(dy),
                        .exit_slot(fr[19:18]), .port(o));
                end else begin : ri
                    rt_ipos_xy #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(my_x), .y_i(my_y), .dst_x_i(dx), .dst_y_i(dy),
                        .entry_slot(fr[15:14]), .port(o));
                end
                wire ov, ok;
                localparam [2:0] PI = p;
                if (VN) begin : vn
                    vn_unit #(.LAYER(LAYER)) u (.in_port(PI), .out_port(o), .vc(vc_in), .ovc(ov), .allowed(ok));
                end else if (METHOD == 3 && LAYER == 0 && HAS_HUB) begin : turn
                    // MTR: turn-enable bits at boundary routers (4 inbound + 4 outbound)
                    wire [7:0] te;
                    cfg_table #(.N(2), .W(4), .AW(1), .NRD(2)) ten (.clk(clk), .cfg_we(cfg_we[2]), .cfg_addr(cfg_addr[0]),
                        .cfg_data(cfg_data), .raddr(2'b10), .rdata(te));
                    wire inbound = (p == HUB) && o < 3'd4;
                    wire outbound = (p < 4) && o == 3'd5;
                    wire [2:0] i1 = {1'b0, o[1:0]};
                    wire [2:0] i2 = 3'd4 + PI[1:0];
                    assign ov = vc_in;
                    assign ok = inbound ? te[i1] : outbound ? te[i2] : 1'b1;
                end else begin : novn
                    assign ov = vc_in;
                    assign ok = 1'b1;
                end
                assign rt_ack[2*p+:2] = g & {2{ok}};
                assign rt_port[3*(2*p)+:3] = o;
                assign rt_port[3*(2*p+1)+:3] = o;
                assign rt_ovc[2*p+:2] = {2{ov}};
            end
            assign rt_hdr = {(HDRW+1)*2*P{1'b0}};
            if (LBI_FB) begin : fbchip
                // LB-I, Q-learning: value of a head that arrives from the interposer, sent back on the Hub sideband.
                reg [1:0] sent;
                wire [1:0] gh = fb_g[2*HUB+:2];
                wire [W-1:0] fr = gh[1] ? rt_front[(2*HUB+1)*W+:W] : rt_front[(2*HUB)*W+:W];
                wire [3:0] dxx = fr[26+:XW], dyy = fr[22+:XW];
                wire [CW-1:0] vh;
                wire [GW-1:0] gl;
                wire [KW-1:0] kk;
                lbi_fb_chip #(.W_SHIFT(W_SHIFT), .BETA(BETA), .F(F)) f (.x(x), .y(y), .dst_x(dxx), .dst_y(dyy), .occ_self(occ5),
                    .busy_self(busy5), .occ_nb(nb_r), .static_in(fr[13:7]), .vhere(vh), .goal(gl));
                chip_index #(.GX(GX), .KW(KW)) ki (.gx(dxx[3:2]), .gy(dyy[3:2]), .idx(kk));
                assign fb_out_g = {gl, {4*GW{1'b0}}};
                assign fb_out_k = {kk, {4*KW{1'b0}}};
                wire send = |(gh & ~sent) && fr[6];
                assign fb_out_v = {send, 4'b0};
                always @(posedge clk) begin
                    if (rst) sent <= 2'b00;
                    else sent <= (sent | (gh & rt_ack[2*HUB+:2])) & ~tail_pop[2*HUB+:2];
                end
            end else begin : nofb
                assign fb_out_v = 5'd0;
                assign fb_out_g = {5*GW{1'b0}};
                assign fb_out_k = {5*KW{1'b0}};
            end
        end else begin : lb
            localparam NB = RS_PER_PORT ? P : 1;      // routing + selection units
            localparam G = RS_PER_PORT ? 2 : 2 * P;   // input VCs per unit
            // tie-break state: free-running small LFSR
            reg [2:0] rnd;
            always @(posedge clk) rnd <= rst ? 3'd1 : {rnd[1:0], rnd[2] ^ rnd[1]};
            wire [NB*KW-1:0] rd_key;
            wire [NB*5*16-1:0] rd_q;
            reg [2*P-1:0] fb_sent;
            wire [2*P-1:0] fb_set;
            always @(posedge clk) begin
                if (rst) fb_sent <= {2*P{1'b0}};
                else fb_sent <= (fb_sent | fb_set) & ~tail_pop;
            end
            wire [NB*5-1:0] fbv_all;
            wire [NB*GW-1:0] fbg_all;
            wire [NB*KW-1:0] fbk_all;
            for (b = 0; b < NB; b = b + 1) begin : unit
                localparam BASE = RS_PER_PORT ? 2 * b : 0;
                wire [G-1:0] g;
                rr_arb #(.N(G)) arb (.clk(clk), .rst(rst), .req(rt_req[BASE+:G]), .adv(1'b1), .gnt(g));
                // the selected head, its input port and VC
                reg [W-1:0] fr;
                reg [2:0] ip;
                reg vc_in;
                reg already;
                integer k;
                always @* begin
                    fr = {W{1'b0}};
                    ip = 3'd0;
                    vc_in = 1'b0;
                    already = 1'b0;
                    for (k = 0; k < G; k = k + 1)
                        if (g[k]) begin
                            fr = fr | rt_front[(BASE+k)*W+:W];
                            ip = ip | ((BASE + k) / 2);
                            vc_in = vc_in | ((BASE + k) % 2);
                            already = already | fb_sent[BASE+k];
                        end
                end
                wire [2:0] last = (ip == 3'd0) ? 3'd2 : (ip == 3'd1) ? 3'd3 : (ip == 3'd2) ? 3'd0 : (ip == 3'd3) ? 3'd1 : 3'd4;
                wire arr_hub = ip == 3'd5;
                wire [XW-1:0] dx = fr[26+:XW], dy = fr[22+:XW];
                wire [3:0] dxx = dx, dyy = dy;
                wire [3:0] exit_f = fr[21:18], entry_f = fr[17:14];
                wire [4:0] offered;
                wire [19:0] pruned;
                wire [35:0] flags;
                wire [3:0] here, cand;
                wire [15:0] cx, cy;
                wire same, at_dst;
                if (LAYER) begin : ri
                    lb_route_ipos #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(my_x), .y_i(my_y), .last(last), .dst_x_i(dx), .dst_y_i(dy),
                        .entry(entry_f), .offered(offered), .pruned(pruned), .flags(flags), .here(here), .cx(cx), .cy(cy));
                    assign same = 1'b0;
                    assign at_dst = 1'b0;
                    assign cand = entry_f;
                end else begin : rc
                    lb_route_chip #(.XW(XW), .HAS_HUB(HAS_HUB)) r (.x_i(my_x), .y_i(my_y), .last(last), .dst_x_i(dx), .dst_y_i(dy),
                        .exit_mask(exit_f), .same_chip(same), .at_dst(at_dst), .offered(offered), .pruned(pruned), .flags(flags),
                        .here(here), .cx(cx), .cy(cy), .cand(cand));
                end
                wire [2:0] idx;
                wire [6:0] st_out;
                wire [GW-1:0] goal;
                wire [5*CW-1:0] cost_unused;
                wire [CW-1:0] vmin_unused;
                wire [KW-1:0] key;
                chip_index #(.GX(GX), .KW(KW)) ki (.gx(dxx[3:2]), .gy(dyy[3:2]), .idx(key));
                // timing experiment: the table is read in the stage of the costs
                wire [KW-1:0] key_a, key_b, key_c;
                pipe_reg #(.W(KW), .ON(PIPE & 1)) kp0 (.clk(clk), .d(key), .q(key_a));
                pipe_reg #(.W(KW), .ON((PIPE >> 1) & 1)) kp1 (.clk(clk), .d(key_a), .q(key_b));
                pipe_reg #(.W(KW), .ON((PIPE >> 2) & 1)) kp2 (.clk(clk), .d(key_b), .q(key_c));
                assign rd_key[b*KW+:KW] = key_c;
                lb_sel #(.LAYER(LAYER), .W_SHIFT(W_SHIFT), .BETA(BETA), .USE_Q(USE_Q), .F(F), .HAS_HUB(HAS_HUB), .CHIP_OE(LBF), .PIPE(PIPE), .PRE(PRE), .GX(GX)) sel (
                    .clk(clk), .x(x), .y(y), .last_i(last), .arr_hub_i(arr_hub), .vc_i(vc_in), .dst_x_i(dxx), .dst_y_i(dyy), .cx_i(cx), .cy_i(cy),
                    .entry_i(entry_f), .same_chip_i(same), .at_dst_i(at_dst), .offered_i(offered), .pruned_i(pruned), .flags_i(flags), .here_i(here),
                    .occ_self(occ5), .busy_self(busy5), .occ_nb(nb_r), .q(rd_q[b*80+:80]), .rnd(rnd), .static_in_i(fr[13:7]),
                    .cost_all(cost_unused), .idx(idx), .vmin(vmin_unused), .goal(goal), .static_out(st_out));
                // chosen output: Local at the destination (chiplet), Hub for index 4
                wire [2:0] o = at_dst ? 3'd4 : (idx == 3'd4) ? 3'd5 : idx;
                wire ov, ok;
                vn_unit #(.LAYER(LAYER)) vn (.in_port(ip), .out_port(o), .vc(vc_in), .ovc(ov), .allowed(ok));
                // next masks
                wire [3:0] pr = pruned[idx*4+:4];
                wire [3:0] next_exit = (LAYER || same) ? exit_f : pr;
                wire [3:0] next_entry = LAYER ? pr : entry_f;
                wire [15:0] hdr_all = {next_exit, next_entry, st_out, 1'b1};
                wire [HDRW:0] hdr = hdr_all >> (USE_Q ? 0 : 8);
                for (k2 = 0; k2 < G; k2 = k2 + 1) begin : d
                    assign rt_ack[BASE+k2] = g[k2] && ok;
                    assign rt_port[3*(BASE+k2)+:3] = o;
                    assign rt_ovc[BASE+k2] = ov;
                    assign rt_hdr[(HDRW+1)*(BASE+k2)+:HDRW+1] = hdr;
                    assign fb_set[BASE+k2] = g[k2];
                end
                // learning feedback: once per head, to the router it came from
                wire send = USE_Q && |g && !already && fr[6] && ip != 3'd4;
                assign fbv_all[b*5+:5] = !send ? 5'd0 : (ip == 3'd5) ? 5'b10000 : (5'b00001 << ip);
                assign fbg_all[b*GW+:GW] = goal;
                assign fbk_all[b*KW+:KW] = key;
            end
            if (USE_Q) begin : q
                wire [4:0] rv;
                wire [5*GW-1:0] rg;
                wire [5*KW-1:0] rk;
                q_fb_regs #(.N(5), .GW(GW), .KW(KW)) regs (.clk(clk), .rst(rst), .v_in(fb_in_v), .g_in(fb_in_g), .k_in(fb_in_k),
                    .v_out(rv), .g_out(rg), .k_out(rk));
                // table initialisation after reset: one write per address on all banks
                reg [KW:0] init;
                wire init_on = !init[KW];
                always @(posedge clk) begin
                    if (rst) init <= {(KW+1){1'b0}};
                    else if (init_on) init <= init + 1'b1;
                end
                for (v = 0; v < 5; v = v + 1) begin : bank
                    wire [15:0] ud, nd;
                    wire [NB*16-1:0] rd;
                    wire [KW-1:0] uk = rk[v*KW+:KW];
                    q_bank #(.C(C), .KW(KW), .NRD(NB)) m (.clk(clk), .we(init_on || rv[v]), .waddr(init_on ? init[KW-1:0] : uk),
                        .wdata(init_on ? 16'd0 : nd), .raddr(rd_key), .rdata(rd), .uaddr(uk), .udata(ud));
                    q_update #(.GW(GW), .S1(S1), .S2(S2)) u (.q_i(ud), .goal_i(rg[v*GW+:GW]), .q_new(nd));
                    for (b = 0; b < NB; b = b + 1) begin : rp
                        assign rd_q[(b*5+v)*16+:16] = rd[b*16+:16];
                    end
                end
            end else begin : noq
                assign rd_q = {NB*5*16{1'b0}};
            end
            // sidebands of the units towards the previous routers
            wire [5*NB-1:0] fbv = fbv_all;
            for (d5 = 0; d5 < 5; d5 = d5 + 1) begin : dirs
                localparam PORT = (d5 < 4) ? d5 : 5;
                localparam U = RS_PER_PORT ? ((PORT < P) ? PORT : 0) : 0;
                wire [NB-1:0] col;
                for (b = 0; b < NB; b = b + 1) begin : c
                    assign col[b] = fbv[b*5+d5];
                end
                assign fb_out_v[d5] = |col;
                assign fb_out_g[d5*GW+:GW] = fbg_all[U*GW+:GW];
                assign fb_out_k[d5*KW+:KW] = fbk_all[U*KW+:KW];
            end
        end
    endgenerate
endmodule

module generate_scen #(parameter ON = 0) (input clk, input we, input [3:0] d, output [3:0] q);
    generate
        if (ON) begin : s
            reg [3:0] r;
            always @(posedge clk) if (we) r <= d;
            assign q = r;
        end else begin : n
            assign q = 4'd0;
        end
    endgenerate
endmodule
