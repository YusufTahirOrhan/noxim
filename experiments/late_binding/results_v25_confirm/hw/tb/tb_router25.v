// v25 F2 (router-level test, not a vector check): one interposer router of the v25 design under random packets on all link
// ports, random neighbour reports and randomly delayed credits. Every head is a consistent state of the relation (each
// candidate of its mask has a legal move for its arrival port). Checks: every flit that enters leaves; packets stay
// contiguous per output VC; no X on a valid output; every head leaves through an output the relation offers for it, on its
// own VC, with the candidate mask the relation gives for that output.
`timescale 1ns/1ps
module tb_router25;
    parameter MECH = 0, ORDER_O = 0, DBIAS = 0, HAS_HUB = 0, RS_PER_PORT = 1, CUT_A = 0, CUT_M = 0, CUT_B = 0, XW = 4, NOSEL = 0;
    parameter NPKT = 300, MINLEN = 2, SEED = 1;
    localparam P = HAS_HUB ? 6 : 5;
    localparam W = 32;
    reg clk = 0, rst = 1;
    always #0.5 clk = !clk;
    reg [P*W-1:0] in_flit;
    reg [P-1:0] in_valid, in_vc;
    wire [2*P-1:0] in_credit;
    wire [P*W-1:0] out_flit;
    wire [P-1:0] out_valid, out_vc;
    reg [2*P-1:0] out_credit;
    wire [29:0] occ_report;
    reg [149:0] nb_report;
    // an interposer router under the N slot of chiplet (1, 1), or the router east of it (no VL)
    wire [XW-1:0] mx = HAS_HUB ? 5 : 6;
    wire [XW-1:0] my = 4;
    router25_top #(.MECH(MECH), .ORDER_O(ORDER_O), .DBIAS(DBIAS), .HAS_HUB(HAS_HUB), .RS_PER_PORT(RS_PER_PORT), .CUT_A(CUT_A), .CUT_M(CUT_M),
                   .CUT_B(CUT_B), .XW(XW), .W_SHIFT(1), .NOSEL(NOSEL)) dut (
        .clk(clk), .rst(rst), .my_x(mx), .my_y(my), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .occ_report(occ_report), .nb_report(nb_report));

    // the relation of a head, for drawing consistent heads and for the checker
    reg [3:0] hx, hy, hmask;
    reg [2:0] hlast;
    reg hvn;
    wire [4:0] hoff;
    wire [19:0] hpr;
    lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(-1), .VNFIX(-1)) hrel (.x({{(4-XW){1'b0}}, mx}), .y({{(4-XW){1'b0}}, my}), .last_i(hlast),
        .vn(hvn), .dst_x(hx), .dst_y(hy), .cand(hmask), .offered(hoff), .pruned(hpr), .mv(), .here(), .fl(), .yx());

    integer sent_pkts[0:5], left[0:5], cred[0:11], vcsel[0:5], pkt_len[0:5], pending[0:11];
    reg [31:0] pkt_hdr[0:5];
    reg [4:0] exp_off[0:4095];
    reg [19:0] exp_pr[0:4095];
    reg exp_vc[0:4095];
    integer flits_in, flits_out, p, v, i, t, bad, wait_pkts, next_id, tries, d, heads_multi, seed;
    reg [31:0] f;
    reg [3:0] reach;
    reg [11:0] open;
    reg [11:0] id;

    initial begin
        seed = SEED;
        flits_in = 0; flits_out = 0; bad = 0; open = 12'b0; next_id = 0; heads_multi = 0;
        for (i = 0; i < 6; i = i + 1) begin sent_pkts[i] = 0; left[i] = 0; vcsel[i] = 0; end
        for (i = 0; i < 12; i = i + 1) begin cred[i] = 4; pending[i] = 0; end
        in_valid = 0; in_vc = 0; in_flit = 0; out_credit = 0; nb_report = 0;
        repeat (4) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (4) @(posedge clk);
        #0.1;
        for (t = 0; t < 400000; t = t + 1) begin
            for (i = 0; i < 2 * P; i = i + 1)
                if (in_credit[i] === 1'b1) cred[i] = cred[i] + 1;
            in_valid = 0;
            for (i = 0; i < 5; i = i + 1) nb_report[30*i+:30] = $random(seed);
            // occupancy values are 0..4
            for (i = 0; i < 50; i = i + 1) if (nb_report[3*i+:3] > 3'd4) nb_report[3*i+:3] = 3'd4;
            for (p = 0; p < P; p = p + 1) begin
                if (p == 4) continue;
                if (left[p] == 0 && sent_pkts[p] < NPKT && ($random(seed) & 3) != 0 && next_id < 4096) begin
                    // draw a head with at least one candidate that has a legal move after arriving on this port
                    hlast = (p == 0) ? 3'd2 : (p == 1) ? 3'd3 : (p == 2) ? 3'd0 : (p == 3) ? 3'd1 : 3'd4;
                    reach = 4'b0;
                    for (tries = 0; tries < 50 && reach == 4'b0; tries = tries + 1) begin
                        hx = $random(seed);
                        hy = $random(seed);
                        if (XW == 3) begin hx[3] = 0; hy[3] = 0; end
                        hvn = $random(seed);
                        hmask = 4'b1111;
                        #0;
                        reach = hpr[3:0] | hpr[7:4] | hpr[11:8] | hpr[15:12] | hpr[19:16];
                        // a head from the Down link belongs to another chiplet than the one above this router
                        if (p == 5 && hx[3:2] == mx[XW-1:2] && hy[3:2] == my[XW-1:2]) reach = 4'b0;
                    end
                    if (reach != 4'b0) begin
                        hmask = reach & $random(seed);
                        if (hmask == 4'b0) hmask = reach;
                        #0;
                        id = next_id;
                        next_id = next_id + 1;
                        exp_off[id] = hoff;
                        exp_pr[id] = hpr;
                        exp_vc[id] = hvn;
                        if (hoff & (hoff - 5'd1)) heads_multi = heads_multi + 1;
                        f = 0;
                        f[29:26] = hx;
                        f[25:22] = hy;
                        f[17:14] = hmask;
                        f[13:12] = $random(seed);
                        f[11:0] = id;
                        pkt_hdr[p] = f;
                        vcsel[p] = hvn;
                        pkt_len[p] = MINLEN + ({$random(seed)} % (9 - MINLEN));
                        left[p] = pkt_len[p];
                    end
                end
                if (left[p] > 0) begin
                    f = pkt_hdr[p];
                    f[31:30] = (left[p] == pkt_len[p]) ? 2'b01 : (left[p] == 1) ? 2'b10 : 2'b00;
                    in_flit[p*W+:W] = f;
                    in_vc[p] = vcsel[p];
                    if (cred[2*p+vcsel[p]] > 0 && ($random(seed) & 7) != 0) begin
                        in_valid[p] = 1'b1;
                        cred[2*p+vcsel[p]] = cred[2*p+vcsel[p]] - 1;
                        left[p] = left[p] - 1;
                        flits_in = flits_in + 1;
                        if (left[p] == 0) sent_pkts[p] = sent_pkts[p] + 1;
                    end
                end
            end
            @(posedge clk);
            #0.1;
            out_credit = 0;
            for (p = 0; p < P; p = p + 1) begin
                if (out_valid[p] === 1'b1) begin
                    f = out_flit[p*W+:W];
                    v = out_vc[p] === 1'b1 ? 1 : 0;
                    d = (p == 5) ? 4 : p;
                    flits_out = flits_out + 1;
                    if (^f[31:30] === 1'bx || ^f[17:0] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X in a flit at output %0d", p); end
                    if (f[30] === 1'b1) begin
                        if (open[2*p+v]) begin bad = bad + 1; if (bad < 5) $display("head in an open packet, output %0d VC %0d", p, v); end
                        open[2*p+v] = 1'b1;
                        id = f[11:0];
                        if (p == 4 || !exp_off[id][d]) begin bad = bad + 1; if (bad < 5) $display("packet %0d left through output %0d, not offered (%b)", id, p, exp_off[id]); end
                        else if (f[17:14] !== exp_pr[id][4*d+:4]) begin bad = bad + 1; if (bad < 5) $display("packet %0d: mask %b after output %0d, expected %b", id, f[17:14], p, exp_pr[id][4*d+:4]); end
                        if (v != exp_vc[id]) begin bad = bad + 1; if (bad < 5) $display("packet %0d left on VC %0d", id, v); end
                    end else if (!open[2*p+v]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("flit outside a packet, output %0d VC %0d", p, v);
                    end
                    if (f[31] === 1'b1) open[2*p+v] = 1'b0;
                    pending[2*p+v] = pending[2*p+v] + 1;
                end
                if (out_valid[p] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X valid at output %0d", p); end
            end
            // credits come back after a random delay, so that outputs fill up and VCs stay held
            for (i = 0; i < 2 * P; i = i + 1)
                if (pending[i] > 0 && ($random(seed) & 3) == 0) begin
                    out_credit[i] = 1'b1;
                    pending[i] = pending[i] - 1;
                end
            wait_pkts = 0;
            for (p = 0; p < P; p = p + 1) if (p != 4 && sent_pkts[p] < NPKT && next_id < 4096) wait_pkts = 1;
            for (p = 0; p < P; p = p + 1) if (left[p] > 0) wait_pkts = 1;
            if (!wait_pkts && flits_out == flits_in) t = 400000;
        end
        $display("RESULT router25 mech=%0d order_o=%0d dbias=%0d hub=%0d per_port=%0d cuts=%0d%0d%0d nosel=%0d xw=%0d packets=%0d with_choice=%0d flits_in=%0d flits_out=%0d errors=%0d %s",
                 MECH, ORDER_O, DBIAS, HAS_HUB, RS_PER_PORT, CUT_A, CUT_M, CUT_B, NOSEL, XW, next_id, heads_multi, flits_in, flits_out, bad,
                 (flits_in == flits_out && bad == 0 && flits_in > 0) ? "OK" : "FAIL");
        $finish;
    end
endmodule
