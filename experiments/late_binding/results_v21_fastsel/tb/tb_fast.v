// v21 F2: test benches of the DEFT_FAST units against vectors from the simulator (export_fast.cpp).

// Stage A + decision: offered outputs, the cost of each offered output, the choice is a minimum.
module tb_fast;
    parameter IPOS = 1, HAS_HUB = 1, XW = 4, USE_Q = 0, F = 0, CUT = 0;
    localparam CW = 9 + F;
    reg [3:0] x, y, dx, dy, entry, exit_m;
    reg [2:0] last, rnd;
    reg arr_hub, vc, rr, atd;
    reg [79:0] pre_f, q;
    reg [39:0] pre_l;
    reg [4:0] off;
    reg [31:0] c0, c1, c2, c3, c4;
    wire [4:0] offered;
    wire [19:0] pruned;
    wire same, at_d;
    wire [31:0] T;
    wire [39:0] h;
    fast_stage_a #(.LAYER(IPOS), .HAS_HUB(HAS_HUB), .XW(XW)) a (.x(x), .y(y), .last(last), .dst_x(dx), .dst_y(dy), .exit_mask(exit_m), .entry(entry),
        .offered(offered), .pruned(pruned), .same_chip(same), .at_dst(at_d), .T(T));
    reg clk = 0;
    wire [4:0] offered_c;
    // as router_top: the VN of each output with -deft_vn_rr 1
    wire arr_hor = last < 3'd4;
    wire [4:0] vcout;
    assign vcout[3:0] = (!IPOS && arr_hub) ? 4'b1111 : {4{vc}};
    assign vcout[4] = IPOS ? 1'b1 : arr_hub ? 1'b1 : (arr_hor && !vc) ? rr : vc;
    wire [5*CW-1:0] cost;
    wire [2:0] idx;
    // as router_top: registered w f + beta b + L
    wire [89:0] pre_p;
    genvar po, pv;
    generate
        for (po = 0; po < 5; po = po + 1) begin : ps
            for (pv = 0; pv < 2; pv = pv + 1) begin : v
                assign pre_p[(po*2+pv)*9+:9] = pre_f[(po*2+pv)*8+:8] + pre_l[po*8+:8];
            end
        end
    endgenerate
    fast_decide #(.USE_Q(USE_Q), .F(F), .CUT(CUT)) d (.clk(clk), .pre_p(pre_p), .T(T), .pruned(pruned), .q(q), .offered(offered), .vcout(vcout), .rnd(rnd),
        .h(h), .cost_all(cost), .offered_c(offered_c), .idx(idx));
    integer fd, nv, bad, r, o, skipped;
    reg [8*200:1] vec;
    reg ok;
    reg [31:0] ec [0:4];
    reg [31:0] minc;
    function [31:0] sx(input [CW-1:0] v);
        sx = USE_Q ? {{(32-CW){v[CW-1]}}, v} : {{(32-CW){1'b0}}, v};
    endfunction
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        nv = 0;
        bad = 0;
        skipped = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                        x, y, last, arr_hub, vc, dx, dy, entry, exit_m, pre_f, pre_l, q, rr, off, c0, c1, c2, c3, c4, atd);
            if (r != 20) break;
            if (HAS_HUB == 0 && off[4]) begin
                skipped = skipped + 1;
                continue;
            end
            ec[0] = c0; ec[1] = c1; ec[2] = c2; ec[3] = c3; ec[4] = c4;
            rnd = $random;
            #1 clk = 1;
            #1 clk = 0;
            #1;
            if (HAS_HUB == 0 && |pruned[19:16]) begin
                skipped = skipped + 1;
                continue;
            end
            nv = nv + 1;
            ok = offered === off;
            minc = 32'h7fffffff;
            for (o = 0; o < 5; o = o + 1)
                if (off[o]) begin
                    ok = ok && sx(cost[o*CW+:CW]) === ec[o];
                    if ($signed(ec[o]) < $signed(minc)) minc = ec[o];
                end
            if (off != 0 && !atd)
                ok = ok && off[idx] && ec[idx] === minc;
            if (!ok) begin
                bad = bad + 1;
                if (bad < 6) begin
                    $display("MISMATCH pos %0d,%0d last %0d arrhub %b vc %b rr %b dst %0d,%0d entry %b exit %b off %b exp %b atd %b idx %0d",
                             x, y, last, arr_hub, vc, rr, dx, dy, entry, exit_m, offered, off, atd, idx);
                    for (o = 0; o < 5; o = o + 1)
                        $display("  o%0d cost %0d exp %0d h %0d", o, $signed(sx(cost[o*CW+:CW])), $signed(ec[o]), h[o*8+:8]);
                end
            end
        end
        $display("RESULT fast ipos=%0d has_hub=%0d xw=%0d use_q=%0d f=%0d cut=%0d vectors=%0d skipped=%0d mismatches=%0d", IPOS, HAS_HUB, XW, USE_Q, F, CUT, nv, skipped, bad);
        $finish;
    end
endmodule

// fast_regs: the registered terms and the value on the links.
module tb_fast_regs;
    parameter W_SHIFT = 1, BETA = 0, GX = 2;
    reg clk = 0;
    reg [3:0] x, y;
    reg hub;
    reg [29:0] occ;
    reg [9:0] busy;
    reg [79:0] ef;
    reg [7:0] el;
    wire [79:0] pre_f, pre_f_d;
    wire [7:0] l_out;
    fast_regs #(.W_SHIFT(W_SHIFT), .BETA(BETA), .GX(GX)) u (.clk(clk), .x(x), .y(y), .hub_ok(hub), .occ_self(occ), .busy_self(busy), .pre_f(pre_f), .pre_f_d(pre_f_d), .l_out(l_out));
    integer fd, nv, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        nv = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h\n", x, y, hub, occ, busy, ef, el);
            if (r != 7) break;
            #1 clk = 1;
            #1 clk = 0;
            #1;
            nv = nv + 1;
            if (pre_f !== ef || l_out !== el) begin
                bad = bad + 1;
                if (bad < 6) $display("MISMATCH pos %0d,%0d hub %b occ %h busy %h: pre_f %h exp %h, l %0d exp %0d", x, y, hub, occ, busy, pre_f, ef, l_out, el);
            end
        end
        $display("RESULT fast_regs w_shift=%0d beta=%0d gx=%0d vectors=%0d mismatches=%0d", W_SHIFT, BETA, GX, nv, bad);
        $finish;
    end
endmodule

// LB-I boundary router: value and goal of a head arriving from the interposer.
module tb_fast_fb;
    parameter F = 8;
    localparam CW = 9 + F, GW = CW + 2;
    reg [3:0] x, y, dx, dy;
    reg [79:0] pre_f;
    reg [39:0] pre_l;
    reg [6:0] st;
    reg [31:0] ev, eg;
    wire [CW-1:0] vh;
    wire [GW-1:0] goal;
    lbi_fb_fast #(.F(F)) u (.x(x), .y(y), .dst_x(dx), .dst_y(dy), .pre_f(pre_f), .pre_l(pre_l), .static_in(st), .vhere(vh), .goal(goal));
    integer fd, nv, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        nv = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h\n", x, y, dx, dy, pre_f, pre_l, st, ev, eg);
            if (r != 9) break;
            #1;
            nv = nv + 1;
            if ({{(32-CW){vh[CW-1]}}, vh} !== ev || {{(32-GW){goal[GW-1]}}, goal} !== eg) begin
                bad = bad + 1;
                if (bad < 6) $display("MISMATCH pos %0d,%0d dst %0d,%0d: v %0d exp %0d goal %0d exp %0d", x, y, dx, dy, vh, ev, $signed(goal), $signed(eg));
            end
        end
        $display("RESULT fast_fb f=%0d vectors=%0d mismatches=%0d", F, nv, bad);
        $finish;
    end
endmodule
