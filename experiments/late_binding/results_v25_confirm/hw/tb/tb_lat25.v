// v25 F4 (cycle count, not a vector check): the latency of a head through one idle interposer router of the v25 design, in
// clock cycles from the cycle the head is on the input link to the cycle it is on the output link. Two-flit packets are
// sent one at a time into the idle router (free outputs, credits returned at once, neighbour reports 0), so the head goes
// straight to the buffer front: the case in which a decision that is computed ahead has the least time.
// Reported separately for heads with one offered output and heads with a choice.
`timescale 1ns/1ps
module tb_lat25;
    parameter MECH = 0, ORDER_O = 0, DBIAS = 0, HAS_HUB = 0, RS_PER_PORT = 1, CUT_A = 0, CUT_M = 0, CUT_B = 0, XW = 4, NOSEL = 0;
    parameter NPKT = 2000, SEED = 1;
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
    wire [XW-1:0] mx = HAS_HUB ? 5 : 6;
    wire [XW-1:0] my = 4;
    router25_top #(.MECH(MECH), .ORDER_O(ORDER_O), .DBIAS(DBIAS), .HAS_HUB(HAS_HUB), .RS_PER_PORT(RS_PER_PORT), .CUT_A(CUT_A), .CUT_M(CUT_M),
                   .CUT_B(CUT_B), .XW(XW), .W_SHIFT(1), .NOSEL(NOSEL)) dut (
        .clk(clk), .rst(rst), .my_x(mx), .my_y(my), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .occ_report(occ_report), .nb_report(nb_report));

    reg [3:0] hx, hy, hmask;
    reg [2:0] hlast;
    reg hvn;
    wire [4:0] hoff;
    wire [19:0] hpr;
    lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(-1), .VNFIX(-1)) hrel (.x({{(4-XW){1'b0}}, mx}), .y({{(4-XW){1'b0}}, my}), .last_i(hlast),
        .vn(hvn), .dst_x(hx), .dst_y(hy), .cand(hmask), .offered(hoff), .pruned(hpr), .mv(), .here(), .fl(), .yx());

    integer cyc, thead, tail_seen, n, p, q, tries, seed, bad, tin, lat, guard, multi, sent;
    integer cnt[0:1], lmin[0:1], lmax[0:1];
    reg [31:0] f, g;
    reg [3:0] reach;

    // one clock cycle: outputs are looked at after the edge; a flit seen on an output gets its credit back in the same cycle
    task tick;
        begin
            @(posedge clk);
            #0.1;
            cyc = cyc + 1;
            out_credit = 0;
            for (q = 0; q < P; q = q + 1)
                if (out_valid[q] === 1'b1) begin
                    g = out_flit[q*W+:W];
                    if (g[30] === 1'b1) thead = cyc;
                    if (g[31] === 1'b1) tail_seen = 1;
                    out_credit[2*q + (out_vc[q] === 1'b1 ? 1 : 0)] = 1'b1;
                end
        end
    endtask

    initial begin
        seed = SEED;
        cyc = 0; bad = 0; sent = 0;
        cnt[0] = 0; cnt[1] = 0; lmin[0] = 999; lmin[1] = 999; lmax[0] = 0; lmax[1] = 0;
        in_valid = 0; in_vc = 0; in_flit = 0; out_credit = 0; nb_report = 0;
        repeat (4) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (4) tick;
        for (n = 0; n < NPKT; n = n + 1) begin
            p = {$random(seed)} % P;
            if (p == 4) p = 1;
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
                if (p == 5 && hx[3:2] == mx[XW-1:2] && hy[3:2] == my[XW-1:2]) reach = 4'b0;
            end
            if (reach != 4'b0) begin
                hmask = reach & $random(seed);
                if (hmask == 4'b0) hmask = reach;
                #0;
                multi = (hoff & (hoff - 5'd1)) != 5'd0;
                f = 0;
                f[29:26] = hx;
                f[25:22] = hy;
                f[17:14] = hmask;
                f[13:12] = $random(seed);
                thead = -1;
                tail_seen = 0;
                // the head on the link
                f[31:30] = 2'b01;
                in_flit[p*W+:W] = f;
                in_vc[p] = hvn;
                in_valid = 0;
                in_valid[p] = 1'b1;
                tin = cyc;
                tick;
                // the tail on the link
                f[31:30] = 2'b10;
                in_flit[p*W+:W] = f;
                tick;
                in_valid = 0;
                for (guard = 0; guard < 60 && !tail_seen; guard = guard + 1) tick;
                if (!tail_seen || thead < 0) begin
                    bad = bad + 1;
                    if (bad < 5) $display("packet %0d did not leave (port %0d)", n, p);
                end else begin
                    lat = thead - tin;
                    cnt[multi] = cnt[multi] + 1;
                    if (lat < lmin[multi]) lmin[multi] = lat;
                    if (lat > lmax[multi]) lmax[multi] = lat;
                end
                sent = sent + 1;
                repeat (4) tick;
            end
        end
        $display("RESULT lat25 mech=%0d order_o=%0d dbias=%0d hub=%0d per_port=%0d cuts=%0d%0d%0d nosel=%0d xw=%0d packets=%0d one_output=%0d min=%0d max=%0d choice=%0d min=%0d max=%0d errors=%0d",
                 MECH, ORDER_O, DBIAS, HAS_HUB, RS_PER_PORT, CUT_A, CUT_M, CUT_B, NOSEL, XW, sent, cnt[0], lmin[0], lmax[0], cnt[1], lmin[1], lmax[1], bad);
        $finish;
    end
endmodule
