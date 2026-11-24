// v29 E4 (activity for the power estimate; not a check of the routing): one router of round 18 (router_top: DeFT's four routers and
// the chiplet routers of the main row) under random 8-flit packets. The flit rate of every input port, the share of the heads
// that end here or take the vertical link here, the share of VC 1 and the time until a credit comes back are parameters;
// experiments_v29_hw2.py (e4_act) sets them from the counts of a simulator run (hw/port_loads.csv). The heads are consistent
// with XY routing: a head that arrives from the north has its target in this column and to the south, and so on. Body and
// tail flits carry random bits. Without GATE the RTL is simulated (the parameters are passed on); with GATE the top is the
// synthesised netlist. Checks: no X on a valid output, packets contiguous per output VC, flits in - flits out within the
// capacity of the router. +vcd=FILE: the nets of the router are dumped from cycle WARM to the end.
`timescale 1ns/1ps
module tb_act18;
    parameter METHOD = 1, LAYER = 0, HAS_HUB = 0, C = 16, GX = 4, XW = 4, KW = 4, F = 8, W_SHIFT = 1, BETA = 0, S1 = 5, S2 = 6, RS_PER_PORT = 0,
              PIPE = 0;
    parameter MX = 5, MY = 5;                       // position (footprint coordinates); a VL router sits on a slot position
    parameter Q_MESH = 0, Q_LOCAL = 0, Q_HUB = 0;   // start of a packet on an idle port, per cycle, in 1 / 65536
    parameter S_VC1_MESH = 0, S_VC1_HUB = 0;        // share of the packets on VC 1, in 1 / 256
    parameter S_EJECT = 0;                          // chiplet router: share of the heads from a mesh or vertical port that end here, 1 / 256
    parameter S_VERT = 0;                           // share of the heads from a mesh port that take the vertical link here, 1 / 256
    parameter PR_MESH = 65536, PR_HUB = 65536;      // a credit comes back DMIN cycles after the flit plus a geometric number (success 1 / 65536 units)
    parameter DMIN = 2, EXIT_SLOT = 0;
    parameter WARM = 2000, NCYC = 10000, LEN = 8, SEED = 1;
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
    wire [XW-1:0] mx = MX, my = MY;
`ifdef GATE
    router_top dut (
`else
    router_top #(.METHOD(METHOD), .LAYER(LAYER), .HAS_HUB(HAS_HUB), .C(C), .GX(GX), .XW(XW), .KW(KW), .F(F), .W_SHIFT(W_SHIFT), .BETA(BETA),
                 .S1(S1), .S2(S2), .RS_PER_PORT(RS_PER_PORT), .PIPE(PIPE)) dut (
`endif
        .clk(clk), .rst(rst), .my_x(mx), .my_y(my), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .pe_ready(pe_ready),
        .occ_report(occ_report), .nb_report({5{occ_report}}), .fb_out_v(fbv), .fb_out_g(fbg), .fb_out_k(fbk),
        .fb_in_v(5'b0), .fb_in_g({5*GW{1'b0}}), .fb_in_k({5*KW{1'b0}}), .rc_req_out(rc_req_out), .rc_grant_in(1'b0),
        .rc_req_in(16'b0), .rc_grant_out(rc_grant_out), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data));

    // VL slot positions inside a 4x4 chiplet: N (1,0), E (3,1), S (2,3), W (0,2)
    function [1:0] slot_lx(input integer s);
        slot_lx = (s == 0) ? 2'd1 : (s == 1) ? 2'd3 : (s == 2) ? 2'd2 : 2'd0;
    endfunction
    function [1:0] slot_ly(input integer s);
        slot_ly = (s == 0) ? 2'd0 : (s == 1) ? 2'd1 : (s == 2) ? 2'd3 : 2'd2;
    endfunction
    // may a head that arrives on port p have the target (tx, ty) under XY routing? (never this router: that is a class of its own)
    function xy_ok(input integer p, input [3:0] tx, input [3:0] ty);
        begin
            case (p)
                0: xy_ok = (tx == MX) && (ty > MY);                      // from the north, moving south
                2: xy_ok = (tx == MX) && (ty < MY);                      // from the south, moving north
                1: xy_ok = (tx < MX) || (tx == MX && ty != MY);          // from the east, moving west
                3: xy_ok = (tx > MX) || (tx == MX && ty != MY);          // from the west, moving east
                default: xy_ok = !(tx == MX && ty == MY);                // from the processing element or the vertical link
            endcase
        end
    endfunction

    wire [1:0] own_cx = MX >> 2, own_cy = MY >> 2, own_lx = MX & 3, own_ly = MY & 3;
    wire [1:0] own_slot = (own_lx == 2'd1 && own_ly == 2'd0) ? 2'd0 : (own_lx == 2'd3 && own_ly == 2'd1) ? 2'd1 : (own_lx == 2'd2 && own_ly == 2'd3) ? 2'd2 : 2'd3;

    integer left[0:5], cred[0:11], vcsel[0:5], npk[0:5], nin[0:5], nout[0:5];
    reg [31:0] pkt_hdr[0:5];
    integer crt[0:383], chead[0:11], ctail[0:11];
    integer flits_in, flits_out, p, v, i, t, bad, seed, lout, tries, g, q, win_in, win_out;
    reg [31:0] f, r;
    reg [3:0] dx, dy, tx, ty;
    reg [1:0] s, cx, cy;
    reg ok, vc1;
    reg [11:0] open;
    reg [1023:0] vcdname;

    // a head for input port p: sets f (the header), vc1, ok
    task draw_head(input integer p);
        begin
            ok = 1'b0;
            f = 32'd0;
            r = $random(seed);
            f[13:0] = r[13:0];
            vc1 = 1'b0;
            if (LAYER == 1) begin
                // interposer: the target is the entry VL of the destination chiplet
                vc1 = (p == 5) ? (({$random(seed)} % 256) < S_VC1_HUB) : (({$random(seed)} % 256) < S_VC1_MESH);
                if (p < 4 && HAS_HUB && ({$random(seed)} % 256) < S_VERT) begin
                    cx = own_cx; cy = own_cy; s = own_slot; ok = 1'b1;       // Up here
                end else begin
                    for (tries = 0; tries < 400 && !ok; tries = tries + 1) begin
                        r = $random(seed);
                        cx = r[1:0]; cy = r[3:2]; s = r[5:4];
                        if (GX == 3 && (cx == 2'd3 || cy == 2'd3)) ok = 1'b0;
                        else if (GX == 2 && (cx > 2'd1 || cy > 2'd1)) ok = 1'b0;
                        else if (p == 5 && cx == own_cx && cy == own_cy) ok = 1'b0;      // a head from the Down link belongs to another chiplet
                        else ok = xy_ok(p, {cx, slot_lx(s)}, {cy, slot_ly(s)});
                    end
                end
                r = $random(seed);
                f[29:26] = {cx, r[1:0]};
                f[25:22] = {cy, r[3:2]};
                f[19:18] = r[5:4];
                f[15:14] = s;
                if (METHOD != 1) begin f[21:18] = 4'b1111; f[17:14] = 4'b0001 << s; end
            end else if (p == 4) begin
                // injection: any other router; the NI fills the routing fields and the VC
                for (tries = 0; tries < 400 && !ok; tries = tries + 1) begin
                    r = $random(seed);
                    dx = r[3:0]; dy = r[7:4];
                    ok = !(dx == MX && dy == MY) && !(GX == 3 && (dx[3:2] == 2'd3 || dy[3:2] == 2'd3)) && !(GX == 2 && (dx[3] || dy[3]));
                end
                f[29:26] = dx;
                f[25:22] = dy;
            end else begin
                // chiplet layer, from a mesh port or from the Up link
                vc1 = (p == 5) ? (({$random(seed)} % 256) < S_VC1_HUB) : (({$random(seed)} % 256) < S_VC1_MESH);
                q = {$random(seed)} % 256;
                s = $random(seed);
                if (q < S_EJECT) begin
                    dx = MX; dy = MY; ok = 1'b1;                                 // ends here
                end else if (p < 4 && HAS_HUB && q < S_EJECT + S_VERT) begin
                    vc1 = 1'b0;                                                  // Down here: VN0, another chiplet, the own VL as exit
                    for (tries = 0; tries < 400 && !ok; tries = tries + 1) begin
                        r = $random(seed);
                        dx = r[3:0]; dy = r[7:4];
                        ok = !(dx[3:2] == own_cx && dy[3:2] == own_cy) && !(GX == 3 && (dx[3:2] == 2'd3 || dy[3:2] == 2'd3)) && !(GX == 2 && (dx[3] || dy[3]));
                    end
                    s = own_slot;
                end else begin
                    if (p < 4 && !vc1) begin
                        // on its way out of the chiplet in VN0: towards another VL of this chiplet
                        for (tries = 0; tries < 100 && !ok; tries = tries + 1) begin
                            r = $random(seed);
                            dx = r[3:0]; dy = r[7:4]; s = r[9:8];
                            ok = !(dx[3:2] == own_cx && dy[3:2] == own_cy) && !(GX == 3 && (dx[3:2] == 2'd3 || dy[3:2] == 2'd3)) && !(GX == 2 && (dx[3] || dy[3])) &&
                                 xy_ok(p, {own_cx, slot_lx(s)}, {own_cy, slot_ly(s)});
                        end
                    end
                    // towards a router of this chiplet (VN1 after the Up link, or a packet that stays in the chiplet)
                    for (tries = 0; tries < 400 && !ok; tries = tries + 1) begin
                        r = $random(seed);
                        dx = {own_cx, r[1:0]}; dy = {own_cy, r[3:2]};
                        ok = xy_ok(p, dx, dy);
                    end
                end
                f[29:26] = dx;
                f[25:22] = dy;
                f[19:18] = s;
                r = $random(seed);
                f[15:14] = r[1:0];
                if (METHOD != 1) f[17:14] = 4'b1111;
            end
        end
    endtask

    initial begin
        seed = SEED;
        flits_in = 0; flits_out = 0; bad = 0; open = 12'b0; lout = 0; win_in = 0; win_out = 0;
        for (i = 0; i < 6; i = i + 1) begin left[i] = 0; vcsel[i] = 0; npk[i] = 0; nin[i] = 0; nout[i] = 0; end
        for (i = 0; i < 12; i = i + 1) begin cred[i] = 4; chead[i] = 0; ctail[i] = 0; end
        in_valid = 0; in_vc = 0; in_flit = 0; out_credit = 0;
        cfg_we = 3'b000; cfg_addr = 0; cfg_data = 4'b0000;
        repeat (4) @(posedge clk);
        #0.1;
        // tables of the NI: the exit VL of every destination chiplet (and, DeFT, an entry VL per destination chiplet); all VLs functional
        cfg_we = 3'b001;
        for (i = 0; i < 16; i = i + 1) begin
            cfg_addr = i;
            cfg_data = (METHOD == 1) ? {i[1:0], EXIT_SLOT[1:0]} : {2'b00, EXIT_SLOT[1:0]};
            @(posedge clk);
            #0.1;
        end
        cfg_we = 3'b010;
        cfg_data = 4'b1111;
        for (i = 0; i < 16; i = i + 1) begin
            cfg_addr = i;
            @(posedge clk);
            #0.1;
        end
        cfg_we = 3'b000;
        repeat (3) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (8) @(posedge clk);
        #0.1;
        for (t = 0; t < WARM + NCYC; t = t + 1) begin
            if (t == WARM && $value$plusargs("vcd=%s", vcdname)) begin
                $dumpfile(vcdname);
                $dumpvars(1, dut);       // the nets of the router itself (in a netlist: every net)
            end
            for (i = 0; i < 2 * P; i = i + 1)
                if (in_credit[i] === 1'b1) begin
                    cred[i] = cred[i] + 1;
                    if (i == 8 || i == 9) lout = lout - 1;
                end
            in_valid = 0;
            for (p = 0; p < P; p = p + 1) begin
                if (LAYER == 1 && p == 4) continue;
                q = (p < 4) ? Q_MESH : (p == 4) ? Q_LOCAL : Q_HUB;
                if (left[p] == 0 && ({$random(seed)} % 65536) < q) begin
                    draw_head(p);
                    if (ok) begin
                        pkt_hdr[p] = f;
                        vcsel[p] = vc1;
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
                    // the Local port's VC is chosen by the NI: at most one buffer of flits is on its way there
                    if ((LAYER == 0 && p == 4) ? (lout < 4) : (cred[2*p+vcsel[p]] > 0)) begin
                        in_valid[p] = 1'b1;
                        if (LAYER == 0 && p == 4) lout = lout + 1;
                        else cred[2*p+vcsel[p]] = cred[2*p+vcsel[p]] - 1;
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
                    if (^f[31:30] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X flit type at output %0d", p); end
                    if (f[30] === 1'b1) begin
                        if (open[2*p+v]) begin bad = bad + 1; if (bad < 5) $display("head in an open packet, output %0d VC %0d", p, v); end
                        open[2*p+v] = 1'b1;
                    end else if (!open[2*p+v]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("flit outside a packet, output %0d VC %0d", p, v);
                    end
                    if (f[31] === 1'b1) open[2*p+v] = 1'b0;
                    // the credit of this flit: at once from the processing element, later from a router
                    g = (p == 4) ? 0 : DMIN;
                    if (p != 4) begin
                        q = (p == 5) ? PR_HUB : PR_MESH;
                        for (tries = 0; tries < 200 && ({$random(seed)} % 65536) >= q; tries = tries + 1) g = g + 1;
                    end
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
        $display("RESULT act18 method=%0d layer=%0d hub=%0d cycles=%0d window=%0d packets=%0d,%0d,%0d,%0d,%0d,%0d in=%0d,%0d,%0d,%0d,%0d,%0d out=%0d,%0d,%0d,%0d,%0d,%0d flits_in=%0d flits_out=%0d win_in=%0d win_out=%0d errors=%0d %s",
                 METHOD, LAYER, HAS_HUB, WARM + NCYC, NCYC, npk[0], npk[1], npk[2], npk[3], npk[4], npk[5], nin[0], nin[1], nin[2], nin[3], nin[4], nin[5],
                 nout[0], nout[1], nout[2], nout[3], nout[4], nout[5], flits_in, flits_out, win_in, win_out, bad,
                 (bad == 0 && flits_in > 0) ? "OK" : "FAIL");
        $finish;
    end
endmodule
