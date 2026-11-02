// v18 J2 (smoke test, not a vector check): one router of each method under random packets from all input ports. The outputs
// always return credits. Checks: every flit that enters leaves, packets stay contiguous per output VC, no X on a valid output.
`timescale 1ns/1ps
module tb_router;
    parameter METHOD = 0, LAYER = 0, HAS_HUB = 0, C = 4, GX = 2, XW = 3, KW = 2, F = 10, W_SHIFT = 1, BETA = 0, S1 = 5, S2 = 6, RS_PER_PORT = 0;
    parameter NPKT = 40;
    localparam P = HAS_HUB ? 6 : 5;
    localparam W = 32;
    localparam CW = 9 + F, GW = CW + 2;
    reg clk = 0, rst = 1;
    always #0.5 clk = !clk;
    reg [P*W-1:0] in_flit;
    reg [P-1:0] in_valid, in_vc;
    wire [2*P-1:0] in_credit;
    wire [P*W-1:0] out_flit;
    wire [P-1:0] out_valid, out_vc;
    reg [2*P-1:0] out_credit;
    wire pe_ready, rc_req_out;
    wire [15:0] rc_grant_out;
    wire [29:0] occ_report;
    wire [4:0] fbv;
    wire [5*GW-1:0] fbg;
    wire [5*KW-1:0] fbk;
    reg [2:0] cfg_we;
    reg [12:0] cfg_addr;
    reg [3:0] cfg_data;
    reg rc_grant_r;
    // positions: not a VL (5 ports), or the N slot of chiplet 0 (6 ports)
    wire [XW-1:0] mx = HAS_HUB ? 1 : 1;
    wire [XW-1:0] my = HAS_HUB ? 0 : 1;
    router_top #(.METHOD(METHOD), .LAYER(LAYER), .HAS_HUB(HAS_HUB), .C(C), .GX(GX), .XW(XW), .KW(KW), .F(F), .W_SHIFT(W_SHIFT), .BETA(BETA),
                 .S1(S1), .S2(S2), .RS_PER_PORT(RS_PER_PORT)) dut (
        .clk(clk), .rst(rst), .my_x(mx), .my_y(my), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .pe_ready(pe_ready),
        .occ_report(occ_report), .nb_report({5{occ_report}}), .fb_out_v(fbv), .fb_out_g(fbg), .fb_out_k(fbk),
        .fb_in_v(fbv), .fb_in_g(fbg), .fb_in_k(fbk), .rc_req_out(rc_req_out), .rc_grant_in(rc_grant_r),
        .rc_req_in({15'b0, rc_req_out}), .rc_grant_out(rc_grant_out), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data));

    // Sender state per input port.
    integer sent_pkts[0:5], left[0:5], cred[0:11], vcsel[0:5], pkt_dst[0:5], open_vc[0:11];
    integer flits_in, flits_out, p, v, i, t, bad, wait_pkts;
    reg [31:0] f;
    reg [3:0] dx, dy;
    reg v_cur;
    // Output checker: open packet per output VC.
    reg [11:0] open;
    integer delay[0:11];

    initial begin
        flits_in = 0;
        flits_out = 0;
        bad = 0;
        open = 12'b0;
        for (i = 0; i < 6; i = i + 1) begin sent_pkts[i] = 0; left[i] = 0; vcsel[i] = 0; end
        for (i = 0; i < 12; i = i + 1) begin cred[i] = 4; delay[i] = 0; end
        in_valid = 0;
        in_vc = 0;
        in_flit = 0;
        out_credit = 0;
        cfg_we = 3'b000;
        cfg_addr = 0;
        cfg_data = (METHOD == 2) ? 4'b0111 : 4'b1111;
        repeat (4) @(posedge clk);
        #0.1;
        // tables: every location written (slot 3, all VLs functional, all turns enabled)
        cfg_we = 3'b111;
        for (i = 0; i < 1024; i = i + 1) begin
            cfg_addr = i;
            @(posedge clk);
            #0.1;
        end
        cfg_we = 3'b000;
        repeat (3) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (40) @(posedge clk);    // Q table initialisation
        #0.1;
        for (t = 0; t < 40000; t = t + 1) begin
            // credits returned by the input buffers (seen before this cycle's sends)
            for (i = 0; i < 2 * P; i = i + 1)
                if (in_credit[i] === 1'b1) cred[i] = cred[i] + 1;
            in_valid = 0;
            for (p = 0; p < P; p = p + 1) begin
                if (LAYER == 1 && p == 4) continue;
                if (left[p] == 0 && sent_pkts[p] < NPKT && ($random & 3) == 0) begin
                    left[p] = 8;
                    vcsel[p] = $random & 1;
                    if (LAYER == 0 && p < 4 && (METHOD == 1 || METHOD == 2 || METHOD == 5 || METHOD >= 6)) vcsel[p] = 0;
                    dx = $random;
                    dy = $random;
                    if (XW == 3) begin dx[3] = 0; dy[3] = 0; end
                    if (GX == 3) begin
                        if (dx[3:2] == 3) dx[3:2] = 0;
                        if (dy[3:2] == 3) dy[3:2] = 0;
                    end
                    // RC: outbound only from the Local port, which holds a permit (no permit logic on the test's neighbours)
                    if (METHOD == 4 && LAYER == 0 && p != 4) begin dx[3:2] = 0; dy[3:2] = 0; end
                    pkt_dst[p] = {dx, dy};
                end
                if (left[p] > 0) begin
                    f = 0;
                    f[31:30] = (left[p] == 8) ? 2'b01 : (left[p] == 1) ? 2'b10 : 2'b00;
                    f[29:26] = pkt_dst[p] >> 4;
                    f[25:22] = pkt_dst[p];
                    f[21:18] = 4'b1111;
                    f[17:14] = 4'b1111;
                    f[5:0] = left[p];
                    // The Local port's VC comes from the NI: use the VC the NI would give this flit.
                    in_flit[p*W+:W] = f;
                    in_vc[p] = vcsel[p];
                    #0;
                    if (LAYER == 0 && p == 4) begin
                        in_valid[p] = 1'b1;
                        #0;
                        v_cur = dut.core_in_vc[4];
                        in_valid[p] = 1'b0;
                    end else begin
                        v_cur = vcsel[p];
                    end
                    if (cred[2*p+(v_cur === 1'b1 ? 1 : 0)] > 0 && !(LAYER == 0 && p == 4 && METHOD == 4 && !pe_ready)) begin
                        in_valid[p] = 1'b1;
                        cred[2*p+(v_cur === 1'b1 ? 1 : 0)] = cred[2*p+(v_cur === 1'b1 ? 1 : 0)] - 1;
                        left[p] = left[p] - 1;
                        flits_in = flits_in + 1;
                        if (left[p] == 0) sent_pkts[p] = sent_pkts[p] + 1;
                    end
                end
            end
            @(posedge clk);
            #0.1;
            rc_grant_r = 1'b0;
            if (HAS_HUB && METHOD == 4 && LAYER == 0) rc_grant_r = rc_grant_out[0];
            else if (METHOD == 4 && LAYER == 0) rc_grant_r = rc_req_out;
            // outputs
            out_credit = 0;
            for (p = 0; p < P; p = p + 1) begin
                if (out_valid[p] === 1'b1) begin
                    f = out_flit[p*W+:W];
                    v = out_vc[p] === 1'b1 ? 1 : 0;
                    flits_out = flits_out + 1;
                    if (^f[31:30] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X flit type at output %0d", p); end
                    if (f[30] === 1'b1) begin
                        if (open[2*p+v]) begin bad = bad + 1; if (bad < 5) $display("head in an open packet, output %0d VC %0d", p, v); end
                        open[2*p+v] = 1'b1;
                    end else if (!open[2*p+v]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("flit outside a packet, output %0d VC %0d", p, v);
                    end
                    if (f[31] === 1'b1) open[2*p+v] = 1'b0;
                    out_credit[2*p+v] = 1'b1;
                end
                if (out_valid[p] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X valid at output %0d", p); end
            end
            wait_pkts = 0;
            for (p = 0; p < P; p = p + 1) if (!(LAYER == 1 && p == 4) && sent_pkts[p] < NPKT) wait_pkts = 1;
            if (!wait_pkts && flits_out == flits_in) t = 40000;
        end
        $display("RESULT router method=%0d layer=%0d hub=%0d C=%0d per_port=%0d flits_in=%0d flits_out=%0d errors=%0d %s", METHOD, LAYER, HAS_HUB, C, RS_PER_PORT,
                 flits_in, flits_out, bad, (flits_in == flits_out && bad == 0 && flits_in > 0) ? "OK" : "FAIL");
        $finish;
    end
endmodule
