// v29 E4 (activity for the power estimate; not a check of the routing): one interposer router of the main row or of a variant
// of E2 (router25_top) under random 8-flit packets. The flit rate of every input port, the share of the heads that go up
// here, the share of VC 1 and the time until a credit comes back are parameters; experiments_v29_hw2.py (e4_act) sets them
// from the counts of a simulator run (hw/port_loads.csv). Every head is a consistent state of the relation, drawn as in
// tb_router25.v of round 25 (each candidate of its mask has a legal move for its arrival port). The reports of the five
// neighbours are this router's own report (under uniform traffic the neighbours carry the same load). Body and tail flits
// carry random bits. Without GATE the RTL is simulated; with GATE the top is the synthesised netlist (the relation that draws
// the heads is then still the RTL unit, outside the router). Checks: no X on a valid output, packets contiguous per output
// VC, flits in - flits out within the capacity of the router. +vcd=FILE: the nets of the router from cycle WARM to the end.
`timescale 1ns/1ps
module tb_act25;
    parameter MECH = 0, ORDER_O = 0, DBIAS = 0, HAS_HUB = 0, RS_PER_PORT = 1, CUT_A = 0, CUT_M = 0, CUT_B = 0, XW = 4, NOSEL = 0;
    parameter MX = 6, MY = 4;                       // position (footprint coordinates); with HAS_HUB a slot position
    parameter Q_MESH = 0, Q_HUB = 0;                // start of a packet on an idle port, per cycle, in 1 / 65536
    parameter S_VC1_MESH = 0, S_VC1_HUB = 0;        // share of the packets on VC 1, in 1 / 256
    parameter S_VERT = 0;                           // share of the heads from a mesh port that go up here, in 1 / 256
    parameter PR_MESH = 65536, PR_HUB = 65536;      // a credit comes back DMIN cycles after the flit plus a geometric number (success 1 / 65536 units)
    parameter DMIN = 2;
    parameter WARM = 2000, NCYC = 10000, LEN = 8, SEED = 1;
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
    wire [XW-1:0] mx = MX, my = MY;
`ifdef GATE
    router25_top dut (
`else
    router25_top #(.MECH(MECH), .ORDER_O(ORDER_O), .DBIAS(DBIAS), .HAS_HUB(HAS_HUB), .RS_PER_PORT(RS_PER_PORT), .CUT_A(CUT_A), .CUT_M(CUT_M),
                   .CUT_B(CUT_B), .XW(XW), .W_SHIFT(1), .NOSEL(NOSEL)) dut (
`endif
        .clk(clk), .rst(rst), .my_x(mx), .my_y(my), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .occ_report(occ_report), .nb_report(nb_report));

    // the relation of a head, for drawing consistent heads
    reg [3:0] hx, hy, hmask;
    reg [2:0] hlast;
    reg hvn;
    wire [4:0] hoff;
    wire [19:0] hpr;
    lb25_rel #(.HAS_HUB(HAS_HUB), .ORDER_O(ORDER_O), .LAST(-1), .VNFIX(-1)) hrel (.x({{(4-XW){1'b0}}, mx}), .y({{(4-XW){1'b0}}, my}), .last_i(hlast),
        .vn(hvn), .dst_x(hx), .dst_y(hy), .cand(hmask), .offered(hoff), .pruned(hpr), .mv(), .here(), .fl(), .yx());

    wire [1:0] own_cx = MX >> 2, own_cy = MY >> 2, own_lx = MX & 3, own_ly = MY & 3;
    wire [1:0] own_slot = (own_lx == 2'd1 && own_ly == 2'd0) ? 2'd0 : (own_lx == 2'd3 && own_ly == 2'd1) ? 2'd1 : (own_lx == 2'd2 && own_ly == 2'd3) ? 2'd2 : 2'd3;

    integer left[0:5], cred[0:11], vcsel[0:5], npk[0:5], nin[0:5], nout[0:5];
    reg [31:0] pkt_hdr[0:5];
    integer crt[0:383], chead[0:11], ctail[0:11];
    integer flits_in, flits_out, p, v, i, t, bad, seed, tries, g, q, win_in, win_out, heads_multi, heads_up;
    reg [31:0] f, r;
    reg [3:0] reach;
    reg [11:0] open;
    reg [1023:0] vcdname;

    initial begin
        seed = SEED;
        flits_in = 0; flits_out = 0; bad = 0; open = 12'b0; win_in = 0; win_out = 0; heads_multi = 0; heads_up = 0;
        for (i = 0; i < 6; i = i + 1) begin left[i] = 0; vcsel[i] = 0; npk[i] = 0; nin[i] = 0; nout[i] = 0; end
        for (i = 0; i < 12; i = i + 1) begin cred[i] = 4; chead[i] = 0; ctail[i] = 0; end
        in_valid = 0; in_vc = 0; in_flit = 0; out_credit = 0; nb_report = 0;
        hx = 0; hy = 0; hmask = 0; hlast = 0; hvn = 0;
        repeat (4) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (8) @(posedge clk);
        #0.1;
        for (t = 0; t < WARM + NCYC; t = t + 1) begin
            if (t == WARM && $value$plusargs("vcd=%s", vcdname)) begin
                $dumpfile(vcdname);
                $dumpvars(0, dut);
            end
            for (i = 0; i < 2 * P; i = i + 1)
                if (in_credit[i] === 1'b1) cred[i] = cred[i] + 1;
            in_valid = 0;
            nb_report = {5{occ_report}};
            for (p = 0; p < P; p = p + 1) begin
                if (p == 4) continue;
                q = (p < 4) ? Q_MESH : Q_HUB;
                if (left[p] == 0 && ({$random(seed)} % 65536) < q) begin
                    hlast = (p == 0) ? 3'd2 : (p == 1) ? 3'd3 : (p == 2) ? 3'd0 : (p == 3) ? 3'd1 : 3'd4;
                    hvn = (p == 5) ? (({$random(seed)} % 256) < S_VC1_HUB) : (({$random(seed)} % 256) < S_VC1_MESH);
                    reach = 4'b0;
                    if (p < 4 && HAS_HUB && ({$random(seed)} % 256) < S_VERT) begin
                        // up here: a head for the chiplet above whose only candidate is this router's VL
                        r = $random(seed);
                        hx = {own_cx, r[1:0]};
                        hy = {own_cy, r[3:2]};
                        hmask = 4'b0001 << own_slot;
                        #0;
                        if (hoff == 5'b10000) reach = hmask;
                    end
                    for (tries = 0; tries < 50 && reach == 4'b0; tries = tries + 1) begin
                        hx = $random(seed);
                        hy = $random(seed);
                        if (XW == 3) begin hx[3] = 0; hy[3] = 0; end
                        hmask = 4'b1111;
                        #0;
                        reach = hpr[3:0] | hpr[7:4] | hpr[11:8] | hpr[15:12] | hpr[19:16];
                        // a head from the Down link belongs to another chiplet than the one above this router
                        if (p == 5 && hx[3:2] == own_cx && hy[3:2] == own_cy) reach = 4'b0;
                        if (reach != 4'b0) begin
                            hmask = reach & $random(seed);
                            if (hmask == 4'b0) hmask = reach;
                        end
                    end
                    if (reach != 4'b0) begin
                        #0;
                        if (hoff & (hoff - 5'd1)) heads_multi = heads_multi + 1;
                        if (hoff[4]) heads_up = heads_up + 1;
                        f = $random(seed);
                        f[31:30] = 2'b01;
                        f[29:26] = hx;
                        f[25:22] = hy;
                        f[21:18] = 4'b0;
                        f[17:14] = hmask;
                        pkt_hdr[p] = f;
                        vcsel[p] = hvn;
                        left[p] = LEN;
                        npk[p] = npk[p] + 1;
                    end
                end
                if (left[p] > 0) begin
                    if (left[p] == LEN) f = pkt_hdr[p];
                    else begin f = $random(seed); f[29:22] = pkt_hdr[p][29:22]; end
                    f[31:30] = (left[p] == LEN) ? 2'b01 : (left[p] == 1) ? 2'b10 : 2'b00;
                    in_flit[p*W+:W] = f;
                    in_vc[p] = vcsel[p];
                    if (cred[2*p+vcsel[p]] > 0) begin
                        in_valid[p] = 1'b1;
                        cred[2*p+vcsel[p]] = cred[2*p+vcsel[p]] - 1;
                        left[p] = left[p] - 1;
                        flits_in = flits_in + 1;
                        nin[p] = nin[p] + 1;
                        if (t >= WARM) win_in = win_in + 1;
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
                    flits_out = flits_out + 1;
                    nout[p] = nout[p] + 1;
                    if (t >= WARM) win_out = win_out + 1;
                    if (^f[31:30] === 1'bx || ^f[17:14] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X in a flit at output %0d", p); end
                    if (p == 4) begin bad = bad + 1; if (bad < 5) $display("a flit left through the Local output"); end
                    if (f[30] === 1'b1) begin
                        if (open[2*p+v]) begin bad = bad + 1; if (bad < 5) $display("head in an open packet, output %0d VC %0d", p, v); end
                        open[2*p+v] = 1'b1;
                    end else if (!open[2*p+v]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("flit outside a packet, output %0d VC %0d", p, v);
                    end
                    if (f[31] === 1'b1) open[2*p+v] = 1'b0;
                    g = DMIN;
                    q = (p == 5) ? PR_HUB : PR_MESH;
                    for (tries = 0; tries < 200 && ({$random(seed)} % 65536) >= q; tries = tries + 1) g = g + 1;
                    crt[(2*p+v)*32 + (ctail[2*p+v] % 32)] = t + g;
                    ctail[2*p+v] = ctail[2*p+v] + 1;
                end
                if (out_valid[p] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X valid at output %0d", p); end
            end
            for (i = 0; i < 2 * P; i = i + 1)
                if (chead[i] != ctail[i] && crt[i*32 + (chead[i] % 32)] <= t) begin
                    out_credit[i] = 1'b1;
                    chead[i] = chead[i] + 1;
                end
        end
        if (flits_in - flits_out < 0 || flits_in - flits_out > 2 * P * 8 + 2 * P) bad = bad + 1;
        $display("RESULT act25 dbias=%0d hub=%0d cuts=%0d%0d%0d cycles=%0d window=%0d packets=%0d,%0d,%0d,%0d,%0d,%0d with_choice=%0d up_offered=%0d in=%0d,%0d,%0d,%0d,%0d,%0d out=%0d,%0d,%0d,%0d,%0d,%0d flits_in=%0d flits_out=%0d win_in=%0d win_out=%0d errors=%0d %s",
                 DBIAS, HAS_HUB, CUT_A, CUT_M, CUT_B, WARM + NCYC, NCYC, npk[0], npk[1], npk[2], npk[3], npk[4], npk[5], heads_multi, heads_up,
                 nin[0], nin[1], nin[2], nin[3], nin[4], nin[5], nout[0], nout[1], nout[2], nout[3], nout[4], nout[5], flits_in, flits_out,
                 win_in, win_out, bad, (bad == 0 && flits_in > 0) ? "OK" : "FAIL");
        $finish;
    end
endmodule
