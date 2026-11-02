// Method-specific units other than the late-binding routing and selection (v18). Tables are flip-flops with a configuration
// write port. The routing units are combinational; NI units sit between the processing element and the Local input port.

// Flip-flop table: one configuration write port, NRD asynchronous read ports.
module cfg_table #(parameter N = 4, parameter W = 4, parameter AW = 2, parameter NRD = 1) (
    input clk, input cfg_we, input [AW-1:0] cfg_addr, input [W-1:0] cfg_data,
    input [NRD*AW-1:0] raddr, output [NRD*W-1:0] rdata
);
    reg [W-1:0] mem [0:N-1];
    always @(posedge clk) if (cfg_we) mem[cfg_addr] <= cfg_data;
    genvar r;
    generate
        for (r = 0; r < NRD; r = r + 1) begin : rd
            assign rdata[r*W+:W] = mem[raddr[r*AW+:AW]];
        end
    endgenerate
endmodule

// Plain XY towards a target. out: 0 N, 1 E, 2 S, 3 W; at = at the target.
module xy_dir (input [3:0] x, input [3:0] y, input [3:0] tx, input [3:0] ty, output [2:0] out, output at);
    wire e = tx > x, w = tx < x, s = ty > y, n = ty < y;
    assign at = !e && !w && !s && !n;
    assign out = e ? 3'd1 : w ? 3'd3 : s ? 3'd2 : 3'd0;
endmodule

// Reference router: plain XY; at the target Local, on a 6-port router Hub for packets of another chiplet / at the entry.
module rt_ref #(parameter XW = 3, parameter LAYER = 0, parameter HAS_HUB = 0) (
    input [XW-1:0] x_i, input [XW-1:0] y_i, input [XW-1:0] dst_x_i, input [XW-1:0] dst_y_i, output [2:0] port
);
    wire [3:0] x = x_i, y = y_i, dst_x = dst_x_i, dst_y = dst_y_i;
    wire [2:0] o;
    wire at;
    xy_dir d (.x(x), .y(y), .tx(dst_x), .ty(dst_y), .out(o), .at(at));
    wire other = x[3:2] != dst_x[3:2] || y[3:2] != dst_y[3:2];
    assign port = (HAS_HUB && !LAYER && other) ? 3'd5 : at ? (HAS_HUB && LAYER ? 3'd5 : 3'd4) : o;
endmodule

// Chiplet router of the methods with a fixed exit VL: XY to the exit VL in the source chiplet (Hub there), XY to the
// destination otherwise (Local there).
module rt_chip_xy #(parameter XW = 3, parameter HAS_HUB = 0) (
    input [XW-1:0] x_i, input [XW-1:0] y_i, input [XW-1:0] dst_x_i, input [XW-1:0] dst_y_i, input [1:0] exit_slot, output [2:0] port
);
`include "lb_funcs.vh"
    wire [3:0] x = x_i, y = y_i, dst_x = dst_x_i, dst_y = dst_y_i;
    wire same = x[3:2] == dst_x[3:2] && y[3:2] == dst_y[3:2];
    wire [1:0] lx = (exit_slot == 0) ? slot_lx(0) : (exit_slot == 1) ? slot_lx(1) : (exit_slot == 2) ? slot_lx(2) : slot_lx(3);
    wire [1:0] ly = (exit_slot == 0) ? slot_ly(0) : (exit_slot == 1) ? slot_ly(1) : (exit_slot == 2) ? slot_ly(2) : slot_ly(3);
    wire [3:0] tx = same ? dst_x : {x[3:2], lx};
    wire [3:0] ty = same ? dst_y : {y[3:2], ly};
    wire [2:0] o;
    wire at;
    xy_dir d (.x(x), .y(y), .tx(tx), .ty(ty), .out(o), .at(at));
    assign port = at ? ((same || !HAS_HUB) ? 3'd4 : 3'd5) : o;
endmodule

// Interposer router of the methods with a fixed entry VL: XY to the entry VL, Hub there.
module rt_ipos_xy #(parameter XW = 3, parameter HAS_HUB = 0) (
    input [XW-1:0] x_i, input [XW-1:0] y_i, input [XW-1:0] dst_x_i, input [XW-1:0] dst_y_i, input [1:0] entry_slot, output [2:0] port
);
`include "lb_funcs.vh"
    wire [3:0] x = x_i, y = y_i, dst_x = dst_x_i, dst_y = dst_y_i;
    wire [1:0] lx = (entry_slot == 0) ? slot_lx(0) : (entry_slot == 1) ? slot_lx(1) : (entry_slot == 2) ? slot_lx(2) : slot_lx(3);
    wire [1:0] ly = (entry_slot == 0) ? slot_ly(0) : (entry_slot == 1) ? slot_ly(1) : (entry_slot == 2) ? slot_ly(2) : slot_ly(3);
    wire [2:0] o;
    wire at;
    xy_dir d (.x(x), .y(y), .tx({dst_x[3:2], lx}), .ty({dst_y[3:2], ly}), .out(o), .at(at));
    assign port = at ? (HAS_HUB ? 3'd5 : 3'd4) : o;
endmodule

// DeFT's VN rules on one hop (DeftVirtualNetwork): output VN and the R1-R3 checks.
//  R1: no VN1 -> VN0 transition; R2: Up -> horizontal only in VN1; R3: horizontal -> Down only in VN0.
module vn_unit #(parameter LAYER = 0) (
    input [2:0] in_port, input [2:0] out_port, input vc, output ovc, output allowed
);
    wire arr_hub = in_port == 3'd5;
    wire out_hub = out_port == 3'd5;
    wire arr_hor = in_port < 3'd4;
    wire out_hor = out_port < 3'd4;
    assign ovc = LAYER ? (out_hub || vc) : (arr_hub || vc);
    wire r1 = !(vc && !ovc);
    wire r2 = LAYER || !(arr_hub && out_hor && !ovc);
    wire r3 = LAYER || !(arr_hor && out_hub && ovc);
    assign allowed = r1 && r2 && r3;
endmodule

// Source VN (assignSourceVirtualNetwork): round-robin for intra-chiplet packets and for a boundary-router source committed to
// its own VL (F1 fix), VN0 otherwise.
module ni_vn (input clk, input rst, input inject_head, input either, output vc);
    reg rr;
    assign vc = either ? rr : 1'b0;
    always @(posedge clk) begin
        if (rst) rr <= 1'b0;
        else if (inject_head && either) rr <= !rr;
    end
endmodule

// VC bit at injection for the methods without VN rules (Noxim draws it uniformly; here a toggle).
module ni_vcdraw (input clk, input rst, input inject_head, output reg vc);
    always @(posedge clk) begin
        if (rst) vc <= 1'b0;
        else if (inject_head) vc <= !vc;
    end
endmodule

// Nearest functional VL slot of a local position; ties: lowest slot (nearestMember). FIXED: fault-free, no mask input used.
module near_vl #(parameter FIXED = 0) (input [1:0] lx, input [1:0] ly, input [3:0] fmask, output reg [1:0] slot);
`include "lb_funcs.vh"
    function [2:0] vl_dist(input integer s);
        reg [1:0] ax, ay;
        begin
            ax = (lx > slot_lx(s)) ? lx - slot_lx(s) : slot_lx(s) - lx;
            ay = (ly > slot_ly(s)) ? ly - slot_ly(s) : slot_ly(s) - ly;
            vl_dist = ax + ay;
        end
    endfunction
    wire [3:0] f = FIXED ? 4'b1111 : fmask;
    reg [3:0] best;
    integer s;
    always @* begin
        best = 4'hf;
        slot = 2'd0;
        for (s = 0; s < 4; s = s + 1)
            if (f[s] && {1'b0, vl_dist(s)} < best) begin
                best = {1'b0, vl_dist(s)};
                slot = s;
            end
    end
endmodule

// Index of a chiplet from its grid position.
module chip_index #(parameter GX = 2, parameter KW = 2) (input [1:0] gx, input [1:0] gy, output [KW-1:0] idx);
    wire [3:0] v = gy * GX + gx;
    assign idx = v[KW-1:0];
endmodule

// ---- NI units ----
// Common injection fields: exit and entry fields of the head, its VC.

// DeFT: LUT of (C-1) x (2+2) bits, SCEN scenarios. Address: destination chiplet, own chiplet skipped.
module ni_deft #(parameter C = 4, parameter GX = 2, parameter KW = 2, parameter SCEN = 1, parameter AW = 4) (
    input clk, input rst, input cfg_we, input [AW-1:0] cfg_addr, input [3:0] cfg_data,
    input [3:0] scen_sel, input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input head,
    input own_vl, input [1:0] own_slot,
    output [1:0] exit_slot, output [1:0] entry_slot, output vc
);
    wire [KW-1:0] own, dk;
    chip_index #(.GX(GX), .KW(KW)) i0 (.gx(x[3:2]), .gy(y[3:2]), .idx(own));
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(dst_x[3:2]), .gy(dst_y[3:2]), .idx(dk));
    wire same = own == dk;
    wire [KW-1:0] a = (dk < own) ? dk : dk - 1'b1;
    wire [AW-1:0] addr = scen_sel * (C - 1) + a;
    wire [3:0] e;
    cfg_table #(.N(SCEN * (C - 1)), .W(4), .AW(AW), .NRD(1)) lut (.clk(clk), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
                                                                 .raddr(addr), .rdata(e));
    assign exit_slot = e[1:0];
    assign entry_slot = e[3:2];
    ni_vn vn (.clk(clk), .rst(rst), .inject_head(head), .either(same || (own_vl && e[1:0] == own_slot)), .vc(vc));
endmodule

// MTR: NI table of 16C entries x 2 bits (destination node -> entry boundary router), exit entry of 2 bits.
module ni_mtr #(parameter C = 4, parameter GX = 2, parameter KW = 2, parameter AW = 8) (
    input clk, input rst, input cfg_we, input cfg_we_exit, input [AW-1:0] cfg_addr, input [1:0] cfg_data,
    input [3:0] dst_x, input [3:0] dst_y, input head,
    output [1:0] exit_slot, output [1:0] entry_slot, output vc
);
    wire [KW-1:0] dk;
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(dst_x[3:2]), .gy(dst_y[3:2]), .idx(dk));
    wire [AW-1:0] addr = {dk, dst_y[1:0], dst_x[1:0]};
    cfg_table #(.N(16 * C), .W(2), .AW(AW), .NRD(1)) tbl (.clk(clk), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
                                                         .raddr(addr), .rdata(entry_slot));
    cfg_table #(.N(1), .W(2), .AW(1), .NRD(1)) ex (.clk(clk), .cfg_we(cfg_we_exit), .cfg_addr(1'b0), .cfg_data(cfg_data),
                                                  .raddr(1'b0), .rdata(exit_slot));
    ni_vcdraw vd (.clk(clk), .rst(rst), .inject_head(head), .vc(vc));
endmodule

// DeFT-Dis: nearest functional exit and entry VL, comparators in the NI; fault table of 4C bits.
module ni_dis #(parameter C = 4, parameter GX = 2, parameter KW = 2) (
    input clk, input rst, input cfg_we, input [KW-1:0] cfg_addr, input [3:0] cfg_data,
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input head, input own_vl, input [1:0] own_slot,
    output [1:0] exit_slot, output [1:0] entry_slot, output vc
);
    wire [KW-1:0] own, dk;
    chip_index #(.GX(GX), .KW(KW)) i0 (.gx(x[3:2]), .gy(y[3:2]), .idx(own));
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(dst_x[3:2]), .gy(dst_y[3:2]), .idx(dk));
    wire [7:0] f;
    cfg_table #(.N(C), .W(4), .AW(KW), .NRD(2)) faults (.clk(clk), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
                                                        .raddr({dk, own}), .rdata(f));
    near_vl #(.FIXED(0)) nx (.lx(x[1:0]), .ly(y[1:0]), .fmask(f[3:0]), .slot(exit_slot));
    near_vl #(.FIXED(0)) ne (.lx(dst_x[1:0]), .ly(dst_y[1:0]), .fmask(f[7:4]), .slot(entry_slot));
    ni_vn vn (.clk(clk), .rst(rst), .inject_head(head), .either(own == dk || (own_vl && exit_slot == own_slot)), .vc(vc));
endmodule

// LB-I: exit LUT of (C-1) x 2 bits; the entry mask is the functional mask of the destination chiplet (fault table of 4C bits).
module ni_lbi #(parameter C = 4, parameter GX = 2, parameter KW = 2) (
    input clk, input rst, input cfg_we_lut, input cfg_we_fault, input [KW-1:0] cfg_addr, input [3:0] cfg_data,
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input head, input own_vl, input [1:0] own_slot,
    output [1:0] exit_slot, output [3:0] entry_mask, output vc
);
    wire [KW-1:0] own, dk;
    chip_index #(.GX(GX), .KW(KW)) i0 (.gx(x[3:2]), .gy(y[3:2]), .idx(own));
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(dst_x[3:2]), .gy(dst_y[3:2]), .idx(dk));
    wire [KW-1:0] a = (dk < own) ? dk : dk - 1'b1;
    cfg_table #(.N(C - 1), .W(2), .AW(KW), .NRD(1)) lut (.clk(clk), .cfg_we(cfg_we_lut), .cfg_addr(cfg_addr), .cfg_data(cfg_data[1:0]),
                                                        .raddr(a), .rdata(exit_slot));
    cfg_table #(.N(C), .W(4), .AW(KW), .NRD(1)) faults (.clk(clk), .cfg_we(cfg_we_fault), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
                                                       .raddr(dk), .rdata(entry_mask));
    ni_vn vn (.clk(clk), .rst(rst), .inject_head(head), .either(own == dk || (own_vl && exit_slot == own_slot)), .vc(vc));
endmodule

// LB-F: both masks from the fault table of 4C bits, no LUT.
module ni_lbf #(parameter C = 4, parameter GX = 2, parameter KW = 2) (
    input clk, input rst, input cfg_we, input [KW-1:0] cfg_addr, input [3:0] cfg_data,
    input [3:0] x, input [3:0] y, input [3:0] dst_x, input [3:0] dst_y, input head, input own_vl, input [1:0] own_slot,
    output [3:0] exit_mask, output [3:0] entry_mask, output vc
);
    wire [KW-1:0] own, dk;
    chip_index #(.GX(GX), .KW(KW)) i0 (.gx(x[3:2]), .gy(y[3:2]), .idx(own));
    chip_index #(.GX(GX), .KW(KW)) i1 (.gx(dst_x[3:2]), .gy(dst_y[3:2]), .idx(dk));
    wire [7:0] f;
    cfg_table #(.N(C), .W(4), .AW(KW), .NRD(2)) faults (.clk(clk), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
                                                        .raddr({dk, own}), .rdata(f));
    assign exit_mask = f[3:0];
    assign entry_mask = f[7:4];
    // Committed to the own VL: the exit mask holds only this router's VL.
    wire commit = own_vl && (f[3:0] == (4'b0001 << own_slot));
    ni_vn vn (.clk(clk), .rst(rst), .inject_head(head), .either(own == dk || commit), .vc(vc));
endmodule

// ---- RC ----
// Node side of the injection permission: request and permit counters; a head of an outbound packet leaves only with a permit.
module rc_ni (input clk, input rst, input want, input head_sent, input grant, output req, output may_send);
    reg [2:0] requests, permits;
    assign may_send = permits != 3'd0;
    assign req = want && (requests == 3'd0) && !may_send;
    always @(posedge clk) begin
        if (rst) begin
            requests <= 3'd0;
            permits <= 3'd0;
        end else begin
            requests <= requests + (req ? 3'd1 : 3'd0) - (grant ? 3'd1 : 3'd0);
            permits <= permits + (grant ? 3'd1 : 3'd0) - (head_sent ? 3'd1 : 3'd0);
        end
    end
endmodule

// Boundary router side: a pending bit per chiplet node, used-slot counter, round-robin grant.
module rc_opic_br #(parameter NODES = 16, parameter SLOTS = 4) (
    input clk, input rst, input [NODES-1:0] req, input release_slot, output [NODES-1:0] grant
);
    reg [NODES-1:0] pending;
    reg [2:0] used;
    wire can = used < SLOTS;
    wire [NODES-1:0] g;
    rr_arb #(.N(NODES)) arb (.clk(clk), .rst(rst), .req(pending & {NODES{can}}), .adv(1'b1), .gnt(g));
    assign grant = g;
    wire any = |g;
    always @(posedge clk) begin
        if (rst) begin
            pending <= {NODES{1'b0}};
            used <= 3'd0;
        end else begin
            pending <= (pending | req) & ~g;
            used <= used + (any ? 3'd1 : 3'd0) - (release_slot ? 3'd1 : 3'd0);
        end
    end
endmodule

// RC buffer: 4 slots x 8 flits x 32 bits on the Hub output, one write bus. A packet holds a slot from head to tail and, on the
// Up link, its own VC from head to tail; slots are served round-robin. A free slot is guaranteed by the permission.
module rc_buffer #(parameter W = 32, parameter SLOTS = 4, parameter DEPTH = 8) (
    input clk, input rst,
    input wr, input wr_vc, input [W-1:0] din, output [1:0] credit_to_core,
    output reg [W-1:0] out_flit, output reg out_valid, output reg out_vc, input [1:0] out_credit, output release_slot
);
    // Write side: the slot each VC is filling.
    reg [1:0] wslot [0:1];
    reg [SLOTS-1:0] busy;
    reg [W-1:0] mem [0:SLOTS*DEPTH-1];
    reg [2:0] wp [0:SLOTS-1];
    reg [2:0] rp [0:SLOTS-1];
    reg [3:0] cnt [0:SLOTS-1];
    reg [SLOTS-1:0] slot_vc;
    reg [1:0] vc_slot [0:1];
    reg [1:0] vc_held;
    reg [2:0] occ [0:1];
    assign credit_to_core = {wr && wr_vc, wr && !wr_vc};
    wire head_in = din[30];
    wire tail_in = din[31];

    // First free slot for a new head.
    reg [1:0] free;
    integer a;
    always @* begin
        free = 2'd0;
        for (a = SLOTS - 1; a >= 0; a = a - 1)
            if (!busy[a]) free = a;
    end
    wire [1:0] target = head_in ? free : wslot[wr_vc];

    // Read side.
    wire [SLOTS-1:0] elig;
    genvar s;
    wire [W*SLOTS-1:0] heads;
    generate
        for (s = 0; s < SLOTS; s = s + 1) begin : e
            wire [W-1:0] f = mem[s*DEPTH + rp[s]];
            assign heads[s*W+:W] = f;
            wire v = slot_vc[s];
            wire cred = occ[v] != 3'd4;
            wire is_head = f[30];
            wire owner = vc_held[v] && vc_slot[v] == s;
            assign elig[s] = cnt[s] != 4'd0 && cred && (is_head ? !vc_held[v] : owner);
        end
    endgenerate
    wire [SLOTS-1:0] g;
    wire any = |g;
    rr_arb #(.N(SLOTS)) arb (.clk(clk), .rst(rst), .req(elig), .adv(1'b1), .gnt(g));
    wire [1:0] gi = g[3] ? 2'd3 : g[2] ? 2'd2 : g[1] ? 2'd1 : 2'd0;
    wire [W-1:0] gf = heads[gi*W+:W];
    wire gv = slot_vc[gi];
    wire tail_out = any && gf[31];
    assign release_slot = tail_out;
    integer k;
    always @(posedge clk) begin
        out_flit <= gf;
        out_vc <= gv;
        out_valid <= !rst && any;
        if (wr) mem[target*DEPTH + wp[target]] <= din;
        if (rst) begin
            busy <= {SLOTS{1'b0}};
            vc_held <= 2'b00;
            occ[0] <= 3'd0;
            occ[1] <= 3'd0;
            for (k = 0; k < SLOTS; k = k + 1) begin
                wp[k] <= 3'd0;
                rp[k] <= 3'd0;
                cnt[k] <= 4'd0;
            end
        end else begin
            if (wr) begin
                wp[target] <= wp[target] + 3'd1;
                if (head_in) begin
                    busy[target] <= 1'b1;
                    wslot[wr_vc] <= target;
                    slot_vc[target] <= wr_vc;
                end
            end
            if (any) begin
                rp[gi] <= rp[gi] + 3'd1;
                if (gf[30]) begin
                    vc_held[gv] <= 1'b1;
                    vc_slot[gv] <= gi;
                end
                if (gf[31]) begin
                    vc_held[gv] <= 1'b0;
                    busy[gi] <= 1'b0;
                end
            end
            for (k = 0; k < SLOTS; k = k + 1)
                cnt[k] <= cnt[k] + ((wr && target == k) ? 4'd1 : 4'd0) - ((any && gi == k) ? 4'd1 : 4'd0);
            occ[0] <= occ[0] + ((any && !gv) ? 3'd1 : 3'd0) - (out_credit[0] ? 3'd1 : 3'd0);
            occ[1] <= occ[1] + ((any && gv) ? 3'd1 : 3'd0) - (out_credit[1] ? 3'd1 : 3'd0);
        end
    end
endmodule

// ---- Q-learning storage ----
// One bank per output: C x 16 bits; read ports for the selection, one for the update, one write port from the update.
module q_bank #(parameter C = 4, parameter KW = 2, parameter NRD = 1) (
    input clk, input we, input [KW-1:0] waddr, input [15:0] wdata,
    input [NRD*KW-1:0] raddr, output [NRD*16-1:0] rdata, input [KW-1:0] uaddr, output [15:0] udata
);
    reg [15:0] mem [0:C-1];
    always @(posedge clk) if (we) mem[waddr] <= wdata;
    assign udata = mem[uaddr];
    genvar r;
    generate
        for (r = 0; r < NRD; r = r + 1) begin : rd
            assign rdata[r*16+:16] = mem[raddr[r*KW+:KW]];
        end
    endgenerate
endmodule

// Feedback registers on arrival: goal, key and valid per output direction.
module q_fb_regs #(parameter N = 5, parameter GW = 19, parameter KW = 2) (
    input clk, input rst, input [N-1:0] v_in, input [N*GW-1:0] g_in, input [N*KW-1:0] k_in,
    output reg [N-1:0] v_out, output reg [N*GW-1:0] g_out, output reg [N*KW-1:0] k_out
);
    always @(posedge clk) begin
        v_out <= rst ? {N{1'b0}} : v_in;
        g_out <= g_in;
        k_out <= k_in;
    end
endmodule

// Occupancy reports of the neighbours, registered on arrival. Per input direction the 5 x 2 x 3 reported bits arrive;
// the U-turn output (z = opposite of o) is never read, so 24 bits per direction are kept.
module occ_regs #(parameter NDIR = 5) (input clk, input [150-1:0] in, output [150-1:0] out);
    genvar o, z;
    generate
        for (o = 0; o < 5; o = o + 1) begin : d
            for (z = 0; z < 5; z = z + 1) begin : e
                if (o < NDIR && !(o < 4 && z == ((o + 2) % 4))) begin : k
                    reg [5:0] r;
                    always @(posedge clk) r <= in[(o*5+z)*6+:6];
                    assign out[(o*5+z)*6+:6] = r;
                end else begin : n
                    assign out[(o*5+z)*6+:6] = 6'd0;
                end
            end
        end
    endgenerate
endmodule
