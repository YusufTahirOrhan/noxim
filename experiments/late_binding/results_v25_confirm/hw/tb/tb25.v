// v25 F2: unit testbenches for the vectors dumped from simulator runs (vecdump.inc). Each reads +vec=FILE and prints
//   RESULT <name> ... vectors=<n> mismatches=<m>
// Every vector is applied to the generic unit (arrival direction as an input) and to the unit specialised for its arrival
// direction (one unit per input port), with and without a Hub port where the router has no VL. Units 0.. have a Hub port,
// the second half has none.

// The decision unit: offered outputs, pruned masks, the cost of every offered output, the choice.
// The tie break of the simulator is random; the vector's choice is given to the unit as the start of its rotating priority,
// so the unit must return that output if and only if it is one of the outputs of least cost.
module tb_sel25;
    parameter ORDER_O = 0, DBIAS = 0, CUT_A = 0, CUT_M = 0, CUT_B = 0;
    localparam NCUT = CUT_A + CUT_M + CUT_B;
    reg clk;
    reg [3:0] x, y, dx, dy, mask, pr0, pr1, pr2, pr3, pr4;
    reg [2:0] last, def, choice;
    reg vn, hub, kind, hascost;
    reg [2:0] f0, f1, f2, f3, f4;
    reg [2:0] g [0:24];
    reg [4:0] off;
    reg [7:0] c0, c1, c2, c3, c4;
    reg [29:0] occ_self;
    reg [149:0] occ_nb;
    wire [12*5-1:0] off_all;
    wire [12*20-1:0] pr_all, o1h_all;
    wire [12*3-1:0] dec_all;
    wire [12*28-1:0] cost_all;
    wire [12*4-1:0] val_all;
    genvar hh, ll;
    generate
        for (hh = 0; hh < 2; hh = hh + 1) begin : h
            for (ll = 0; ll < 6; ll = ll + 1) begin : l
                localparam U = hh * 6 + ll;
                lb25_dec #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(ll - 1), .DBIAS(DBIAS), .W_SHIFT(1), .CUT_A(CUT_A), .CUT_M(CUT_M), .CUT_B(CUT_B), .TAGW(1)) d (
                    .clk(clk), .rst(1'b0), .v_i(1'b1), .tag_i(1'b0), .x(x), .y(y), .last_i(last), .vn_i(vn), .dst_x(dx), .dst_y(dy), .cand(mask),
                    .def_slot(def[1:0]), .occ_self(occ_self), .occ_nb(occ_nb), .rnd(choice), .offered(off_all[5*U+:5]), .pruned(pr_all[20*U+:20]),
                    .v_c(), .tag_c(), .dec_c(dec_all[3*U+:3]), .dbg_cost(cost_all[28*U+:28]), .dbg_valid(val_all[4*U+:4]), .dbg_o1h(o1h_all[20*U+:20]));
            end
        end
    endgenerate
    integer fd, n, bad, r, i, o, s, u, uu, multi, nodef, cnt;
    integer multi_last [0:4];
    reg [8*400:1] vec;
    reg ok;
    reg [7:0] ec [0:4];
    reg [3:0] ep [0:4];
    reg [7:0] cm;
    reg [4:0] offered;
    reg [19:0] pruned, o1h;
    reg [27:0] cost;
    reg [3:0] val;
    reg [2:0] dec;
    integer units [0:3];
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0; bad = 0; multi = 0; nodef = 0; clk = 0;
        for (i = 0; i < 5; i = i + 1) multi_last[i] = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h", kind, x, y, last, vn, dx, dy, mask, hub, def);
            if (r != 10) begin
                r = -1;
            end else begin
                r = $fscanf(fd, "%h %h %h %h %h", f0, f1, f2, f3, f4);
                for (i = 0; i < 25; i = i + 1) r = r + $fscanf(fd, "%h", g[i]);
                r = r + $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h %h %h %h\n", off, pr0, pr1, pr2, pr3, pr4, hascost, c0, c1, c2, c3, c4, choice);
                if (r != 43) r = -1;
            end
            if (r < 0) begin
                $display("RESULT sel order_o=%0d dbias=%0d cuts=%0d%0d%0d vectors=%0d mismatches=%0d multi=%0d multi_by_last=%0d,%0d,%0d,%0d,%0d no_default=%0d",
                         ORDER_O, DBIAS, CUT_A, CUT_M, CUT_B, n, bad, multi, multi_last[0], multi_last[1], multi_last[2], multi_last[3], multi_last[4], nodef);
                $finish;
            end
            // the other VC carries the complement, so that a read of the wrong VC shows
            for (o = 0; o < 5; o = o + 1) begin
                cm = (o == 0) ? f0 : (o == 1) ? f1 : (o == 2) ? f2 : (o == 3) ? f3 : f4;
                occ_self[(o*2+0)*3+:3] = vn ? ~cm[2:0] : cm[2:0];
                occ_self[(o*2+1)*3+:3] = vn ? cm[2:0] : ~cm[2:0];
                for (i = 0; i < 5; i = i + 1) begin
                    cm = g[o*5+i];
                    if (o == 4 || vn) begin
                        occ_nb[(o*5+i)*6+3+:3] = cm[2:0];
                        occ_nb[(o*5+i)*6+:3] = ~cm[2:0];
                    end else begin
                        occ_nb[(o*5+i)*6+:3] = cm[2:0];
                        occ_nb[(o*5+i)*6+3+:3] = ~cm[2:0];
                    end
                end
            end
            ec[0] = c0; ec[1] = c1; ec[2] = c2; ec[3] = c3; ec[4] = c4;
            ep[0] = pr0; ep[1] = pr1; ep[2] = pr2; ep[3] = pr3; ep[4] = pr4;
            #1;
            for (i = 0; i < NCUT; i = i + 1) begin
                clk = 1; #1; clk = 0; #1;
            end
            n = n + 1;
            cnt = 0;
            for (o = 0; o < 5; o = o + 1) if (off[o]) cnt = cnt + 1;
            if (cnt > 1) begin
                multi = multi + 1;
                multi_last[last] = multi_last[last] + 1;
            end
            if (DBIAS != 0 && def == 3'd7) nodef = nodef + 1;
            units[0] = 0; units[1] = 1 + last; units[2] = 6; units[3] = 7 + last;
            ok = 1;
            for (uu = 0; uu < (hub ? 2 : 4); uu = uu + 1) begin
                u = units[uu];
                offered = off_all[5*u+:5];
                pruned = pr_all[20*u+:20];
                o1h = o1h_all[20*u+:20];
                cost = cost_all[28*u+:28];
                val = val_all[4*u+:4];
                dec = dec_all[3*u+:3];
                if (offered !== off) ok = 0;
                for (o = 0; o < 5; o = o + 1)
                    if (off[o]) begin
                        if (pruned[4*o+:4] !== ep[o]) ok = 0;
                        if (hascost) begin
                            cm = 8'hff;
                            for (s = 0; s < 4; s = s + 1)
                                if (val[s] && o1h[5*s+o] && {1'b0, cost[7*s+:7]} < cm) cm = {1'b0, cost[7*s+:7]};
                            if (cm !== ec[o]) ok = 0;
                        end
                    end
                if (dec !== choice) ok = 0;
            end
            if (!ok) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH kind %0d pos %0d,%0d last %0d vn %0d dst %0d,%0d mask %b hub %0d def %0d: offered %b exp %b dec %0d exp %0d cost %h exp %0d %0d %0d %0d %0d",
                                       kind, x, y, last, vn, dx, dy, mask, hub, def, off_all[4:0], off, dec_all[2:0], choice, cost_all[27:0], c0, c1, c2, c3, c4);
            end
        end
    end
endmodule

// The buffer front: the relation (offered outputs, pruned masks), the only output of a hop without a choice, and with
// lookahead routing the output asked through the fallback.
module tb_front25;
    parameter ORDER_O = 0;
    reg [3:0] x, y, dx, dy, mask, pr0, pr1, pr2, pr3, pr4;
    reg [2:0] last, stored, held, result;
    reg vn, hub, fbon;
    reg [4:0] off, free;
    wire [22*5-1:0] off_all;
    wire [22*20-1:0] pr_all;
    genvar hh, ll, vv;
    generate
        for (hh = 0; hh < 2; hh = hh + 1) begin : h
            lb25_rel #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(-1), .VNFIX(-1)) gen (.x(x), .y(y), .last_i(last), .vn(vn), .dst_x(dx), .dst_y(dy),
                .cand(mask), .offered(off_all[5*(hh*11)+:5]), .pruned(pr_all[20*(hh*11)+:20]), .mv(), .here(), .fl(), .yx());
            for (ll = 0; ll < 5; ll = ll + 1) begin : l
                for (vv = 0; vv < 2; vv = vv + 1) begin : v
                    localparam U = hh * 11 + 1 + ll * 2 + vv;
                    lb25_rel #(.HAS_HUB(1 - hh), .ORDER_O(ORDER_O), .LAST(ll), .VNFIX(vv)) sp (.x(x), .y(y), .last_i(3'd4), .vn(1'b0), .dst_x(dx),
                        .dst_y(dy), .cand(mask), .offered(off_all[5*U+:5]), .pruned(pr_all[20*U+:20]), .mv(), .here(), .fl(), .yx());
                end
            end
        end
    endgenerate
    reg [4:0] offered;
    reg [19:0] pruned;
    wire single;
    wire [2:0] only, fb;
    lb25_single sg (.offered(offered), .single(single), .only(only));
    lb25_fallback fbk (.stored(stored), .offered(offered), .free(free), .req(fb));
    integer fd, n, bad, r, o, u, uu, n_single, n_fb, n_fb_other, n_held, n_sel;
    integer units [0:3];
    reg [8*400:1] vec;
    reg ok;
    reg [3:0] ep [0:4];
    initial begin
        if (!$value$plusargs("vec=%s", vec)) $finish;
        fd = $fopen(vec, "r");
        n = 0; bad = 0; n_single = 0; n_fb = 0; n_fb_other = 0; n_held = 0; n_sel = 0;
        while (1) begin
            r = $fscanf(fd, "%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n", x, y, last, vn, dx, dy, mask, hub, stored, held,
                        off, pr0, pr1, pr2, pr3, pr4, free, fbon, result);
            if (r != 19) begin
                $display("RESULT front order_o=%0d vectors=%0d mismatches=%0d one_output=%0d fallback_checked=%0d fallback_took_other=%0d head_holds_output=%0d decided_by_selection=%0d",
                         ORDER_O, n, bad, n_single, n_fb, n_fb_other, n_held, n_sel);
                $finish;
            end
            ep[0] = pr0; ep[1] = pr1; ep[2] = pr2; ep[3] = pr3; ep[4] = pr4;
            n = n + 1;
            units[0] = 0; units[1] = 1 + last * 2 + vn; units[2] = 11; units[3] = 12 + last * 2 + vn;
            ok = 1;
            #1;
            for (uu = 0; uu < (hub ? 2 : 4); uu = uu + 1) begin
                u = units[uu];
                offered = off_all[5*u+:5];
                pruned = pr_all[20*u+:20];
                #1;
                if (offered !== off) ok = 0;
                for (o = 0; o < 5; o = o + 1)
                    if (off[o] && pruned[4*o+:4] !== ep[o]) ok = 0;
                if (held != 3'd7) begin
                    // the head already holds an output: no request is made (with the fallback the simulator returns that output)
                    if (fbon && !single && result !== held) ok = 0;
                end else if (single) begin
                    if (only !== result) ok = 0;
                end else if (fbon && stored != 3'd7) begin
                    if (fb !== result) ok = 0;
                end
            end
            if (held != 3'd7) n_held = n_held + 1;
            else if (single) n_single = n_single + 1;
            else if (fbon && stored != 3'd7) begin
                n_fb = n_fb + 1;
                if (result != stored) n_fb_other = n_fb_other + 1;
            end else n_sel = n_sel + 1;
            if (!ok) begin
                bad = bad + 1;
                if (bad < 10) $display("MISMATCH front pos %0d,%0d last %0d vn %0d dst %0d,%0d mask %b hub %0d stored %0d held %0d: offered %b exp %b free %b result %0d (fallback %0d, only %0d)",
                                       x, y, last, vn, dx, dy, mask, hub, stored, held, off_all[4:0], off, free, result, fb, only);
            end
        end
    end
endmodule
