// v18 J2: unit testbenches. Each reads vectors exported by export_vectors.cpp from +vec=FILE, compares and prints a summary line:
//   RESULT <name> vectors=<n> mismatches=<m>

// Routing unit (interposer or chiplet, LB relation). HAS_HUB = 0 is checked on the routers without a VL only.
module tb_route;
    parameter IPOS = 1, HAS_HUB = 1, XW = 4;
    reg [3:0] x, y, mask, dx, dy, pr0, pr1, pr2, pr3, pr4;
    reg [2:0] last;
    reg source, atd, hub;
    reg [4:0] off;
    wire [4:0] offered;
    wire [19:0] pruned;
    wire at_dst_r, same_r;
    generate
        if (IPOS) begin : u
            lb_route_ipos #(.XW(XW), .HAS_HUB(HAS_HUB)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]),
                .entry(mask), .offered(offered), .pruned(pruned), .flags(), .here(), .cx(), .cy());
            assign at_dst_r = atd;
            assign same_r = 1'b0;
        end else begin : u
            lb_route_chip #(.XW(XW), .HAS_HUB(HAS_HUB)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]),
                .exit_mask(mask), .same_chip(same_r), .at_dst(at_dst_r), .offered(offered), .pruned(pruned), .flags(), .here(),
                .cx(), .cy(), .cand());
        end
    endgenerate
    integer fd, n, bad, r, o;
    reg [8*200:1] vec;
    reg ok;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n", x, y, last, mask, dx, dy, source, atd, hub, off, pr0, pr1, pr2, pr3, pr4);
            if (r != 15) break;
            if (!(HAS_HUB == 0 && hub)) begin
                #1;
                n = n + 1;
                ok = offered === off;
                if (!IPOS) ok = ok && at_dst_r === atd && same_r === !source;
                if (IPOS || source) begin
                    if (off[0]) ok = ok && pruned[3:0] === pr0;
                    if (off[1]) ok = ok && pruned[7:4] === pr1;
                    if (off[2]) ok = ok && pruned[11:8] === pr2;
                    if (off[3]) ok = ok && pruned[15:12] === pr3;
                    if (off[4]) ok = ok && pruned[19:16] === pr4;
                end
                if (!ok) begin
                    bad = bad + 1;
                    if (bad < 10) $display("MISMATCH pos %0d,%0d last %0d mask %b dst %0d,%0d src %b: offered %b exp %b pruned %h exp %h %h %h %h %h",
                                           x, y, last, mask, dx, dy, source, offered, off, pruned, pr0, pr1, pr2, pr3, pr4);
                end
            end
        end
        $display("RESULT route ipos=%0d has_hub=%0d xw=%0d vectors=%0d mismatches=%0d", IPOS, HAS_HUB, XW, n, bad);
        $finish;
    end
endmodule

// Selection: routing unit + lb_sel, comparison of every offered output's cost, the choice, the value and the goal.
module tb_sel;
    parameter IPOS = 1, HAS_HUB = 1, XW = 4, W_SHIFT = 1, BETA = 0, USE_Q = 0, F = 0, CHIP_OE = 1;
    localparam CW = 9 + F, GW = CW + 2;
    reg [3:0] x, y, dx, dy, entry, exit_m;
    reg [2:0] last, rnd;
    reg arr_hub, vc, atd;
    reg [29:0] occ_self;
    reg [9:0] busy;
    reg [149:0] occ_nb;
    reg [79:0] q;
    reg [6:0] static_in;
    reg [4:0] off;
    reg [31:0] c0, c1, c2, c3, c4, s0, s1, s2, s3, s4, ev, eg;
    wire [4:0] offered;
    wire [19:0] pruned;
    wire [35:0] flags;
    wire [3:0] here;
    wire [15:0] cx, cy;
    wire same, at_d;
    generate
        if (IPOS) begin : rg
            lb_route_ipos #(.XW(XW), .HAS_HUB(HAS_HUB)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]),
                .entry(entry), .offered(offered), .pruned(pruned), .flags(flags), .here(here), .cx(cx), .cy(cy));
            assign same = 1'b0;
            assign at_d = 1'b0;
        end else begin : rg
            lb_route_chip #(.XW(XW), .HAS_HUB(HAS_HUB)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .last(last), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]),
                .exit_mask(exit_m), .same_chip(same), .at_dst(at_d), .offered(offered), .pruned(pruned), .flags(flags), .here(here),
                .cx(cx), .cy(cy), .cand());
        end
    endgenerate
    wire [5*CW-1:0] cost;
    wire [2:0] idx;
    wire [CW-1:0] vmin;
    wire [GW-1:0] goal;
    wire [6:0] st;
    lb_sel #(.LAYER(IPOS), .W_SHIFT(W_SHIFT), .BETA(BETA), .USE_Q(USE_Q), .F(F), .HAS_HUB(HAS_HUB), .CHIP_OE(CHIP_OE)) u (
        .x(x), .y(y), .last(last), .arr_hub(arr_hub), .vc(vc), .dst_x(dx), .dst_y(dy), .cx(cx), .cy(cy), .entry(entry),
        .same_chip(same), .at_dst(at_d), .offered(offered), .pruned(pruned), .flags(flags), .here(here), .occ_self(occ_self),
        .busy_self(busy), .occ_nb(occ_nb), .q(q), .rnd(rnd), .static_in(static_in), .cost_all(cost), .idx(idx), .vmin(vmin),
        .goal(goal), .static_out(st));
    integer fd, nv, bad, r, o, skipped;
    reg [8*200:1] vec;
    reg ok;
    reg [31:0] ec [0:4];
    reg [31:0] es [0:4];
    reg [31:0] minc;
    function [31:0] sx(input [CW-1:0] v);
        sx = {{(32-CW){v[CW-1]}}, v};
    endfunction
    function [31:0] gx(input [GW-1:0] v);
        gx = {{(32-GW){v[GW-1]}}, v};
    endfunction
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        nv = 0;
        bad = 0;
        skipped = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                        x, y, last, arr_hub, vc, dx, dy, entry, exit_m, occ_self, busy, occ_nb, q, static_in, off,
                        c0, c1, c2, c3, c4, s0, s1, s2, s3, s4, ev, eg, atd);
            if (r != 28) break;
            if (HAS_HUB == 0 && (off[4] || here != 0)) begin
                #1;
                if (off[4] || here != 0) begin
                    skipped = skipped + 1;
                    continue;
                end
            end
            ec[0] = c0; ec[1] = c1; ec[2] = c2; ec[3] = c3; ec[4] = c4;
            es[0] = s0; es[1] = s1; es[2] = s2; es[3] = s3; es[4] = s4;
            rnd = $random;
            #1;
            nv = nv + 1;
            ok = offered === off;
            for (o = 0; o < 5; o = o + 1)
                if (off[o]) ok = ok && sx(cost[o*CW+:CW]) === ec[o];
            if (off != 0 && !atd) begin
                minc = sx(vmin);
                ok = ok && minc === ev;
                ok = ok && off[idx] && ec[idx] === ev;
                ok = ok && {25'b0, st} === es[idx];
            end
            if (USE_Q) ok = ok && gx(goal) === eg;
            if (!ok) begin
                bad = bad + 1;
                if (bad < 6) begin
                    $display("MISMATCH pos %0d,%0d last %0d arrhub %b vc %b dst %0d,%0d entry %b exit %b off %b exp %b atd %b idx %0d",
                             x, y, last, arr_hub, vc, dx, dy, entry, exit_m, offered, off, atd, idx);
                    for (o = 0; o < 5; o = o + 1)
                        $display("  o%0d cost %0d exp %0d static_exp %0d", o, $signed(sx(cost[o*CW+:CW])), $signed(ec[o]), es[o]);
                    $display("  vmin %0d exp %0d st %0d goal %0d exp %0d", $signed(sx(vmin)), $signed(ev), st, $signed(gx(goal)), $signed(eg));
                end
            end
        end
        $display("RESULT sel ipos=%0d has_hub=%0d xw=%0d w_shift=%0d beta=%0d use_q=%0d f=%0d vectors=%0d skipped=%0d mismatches=%0d",
                 IPOS, HAS_HUB, XW, W_SHIFT, BETA, USE_Q, F, nv, skipped, bad);
        $finish;
    end
endmodule

module tb_qupd;
    parameter F = 8, S1 = 4, S2 = 5;
    localparam GW = 11 + F;
    reg [15:0] qo, qn;
    reg [31:0] g;
    wire [15:0] out;
    q_update #(.GW(GW), .S1(S1), .S2(S2)) u (.q_i(qo), .goal_i(g[GW-1:0]), .q_new(out));
    integer fd, n, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h\n", qo, g, qn);
            if (r != 3) break;
            #1;
            n = n + 1;
            if (out !== qn) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH q %0d goal %0d new %0d exp %0d", $signed(qo), $signed(g), $signed(out), $signed(qn));
            end
        end
        $display("RESULT qupd f=%0d s1=%0d s2=%0d vectors=%0d mismatches=%0d", F, S1, S2, n, bad);
        $finish;
    end
endmodule

module tb_xy;
    parameter IPOS = 0, XW = 3;
    reg [3:0] x, y, dx, dy;
    reg [1:0] slot;
    reg hub;
    reg [2:0] exp;
    wire [2:0] port;
    generate
        if (IPOS) begin : u
            rt_ipos_xy #(.XW(XW), .HAS_HUB(1)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]), .entry_slot(slot), .port(port));
        end else begin : u
            rt_chip_xy #(.XW(XW), .HAS_HUB(1)) d (.x_i(x[XW-1:0]), .y_i(y[XW-1:0]), .dst_x_i(dx[XW-1:0]), .dst_y_i(dy[XW-1:0]), .exit_slot(slot), .port(port));
        end
    endgenerate
    integer fd, n, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h\n", x, y, dx, dy, slot, hub, exp);
            if (r != 7) break;
            #1;
            n = n + 1;
            if (port !== exp) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH pos %0d,%0d dst %0d,%0d slot %0d: %0d exp %0d", x, y, dx, dy, slot, port, exp);
            end
        end
        $display("RESULT xy ipos=%0d vectors=%0d mismatches=%0d", IPOS, n, bad);
        $finish;
    end
endmodule

module tb_vn;
    reg layer, vc, eo, ea;
    reg [2:0] in, out;
    wire o0, a0, o1, a1;
    vn_unit #(.LAYER(0)) u0 (.in_port(in), .out_port(out), .vc(vc), .ovc(o0), .allowed(a0));
    vn_unit #(.LAYER(1)) u1 (.in_port(in), .out_port(out), .vc(vc), .ovc(o1), .allowed(a1));
    integer fd, n, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h\n", layer, in, out, vc, eo, ea);
            if (r != 6) break;
            #1;
            n = n + 1;
            if ((layer ? o1 : o0) !== eo || (layer ? a1 : a0) !== ea) begin
                bad = bad + 1;
                if (bad < 40) $display("MISMATCH layer %0d in %0d out %0d vc %0d: ovc %b exp %b allowed %b exp %b", layer, in, out, vc, layer ? o1 : o0, eo, layer ? a1 : a0, ea);
            end
        end
        $display("RESULT vn vectors=%0d mismatches=%0d", n, bad);
        $finish;
    end
endmodule

module tb_near;
    reg [1:0] lx, ly, es;
    reg [3:0] m;
    wire [1:0] s;
    near_vl #(.FIXED(0)) u (.lx(lx), .ly(ly), .fmask(m), .slot(s));
    integer fd, n, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h\n", lx, ly, m, es);
            if (r != 4) break;
            #1;
            n = n + 1;
            if (s !== es) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH %0d,%0d mask %b: %0d exp %0d", lx, ly, m, s, es);
            end
        end
        $display("RESULT near vectors=%0d mismatches=%0d", n, bad);
        $finish;
    end
endmodule

module tb_fb;
    parameter W_SHIFT = 1, BETA = 0, F = 8;
    localparam CW = 9 + F, GW = CW + 2;
    reg [3:0] x, y, dx, dy;
    reg [29:0] occ_self;
    reg [9:0] busy;
    reg [149:0] occ_nb;
    reg [6:0] static_in;
    reg [31:0] ev, eg;
    wire [CW-1:0] v;
    wire [GW-1:0] g;
    lbi_fb_chip #(.W_SHIFT(W_SHIFT), .BETA(BETA), .F(F)) u (.x(x), .y(y), .dst_x(dx), .dst_y(dy), .occ_self(occ_self), .busy_self(busy),
        .occ_nb(occ_nb), .static_in(static_in), .vhere(v), .goal(g));
    integer fd, n, bad, r;
    reg [8*200:1] vec;
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0;
        bad = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h\n", x, y, dx, dy, occ_self, busy, occ_nb, static_in, ev, eg);
            if (r != 10) break;
            #1;
            n = n + 1;
            if ({{(32-CW){v[CW-1]}}, v} !== ev || {{(32-GW){g[GW-1]}}, g} !== eg) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH pos %0d,%0d dst %0d,%0d: v %0d exp %0d goal %0d exp %0d", x, y, dx, dy, v, ev, g, eg);
            end
        end
        $display("RESULT fb w_shift=%0d beta=%0d f=%0d vectors=%0d mismatches=%0d", W_SHIFT, BETA, F, n, bad);
        $finish;
    end
endmodule
