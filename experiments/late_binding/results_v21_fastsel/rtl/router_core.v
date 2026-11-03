// Minimal reference wormhole router (v18): buffers, credit counters, separable round-robin allocators, crossbar.
// The routing and selection logic is outside (router_top.v) and talks to the core through the rt_* interface.
//
// Flit: [31:30] type (01 head, 00 body, 10 tail, 11 head and tail), [29:26] dst_x, [25:22] dst_y,
//       [21:18] exit field, [17:14] entry field, [13:7] static estimate, [6] static valid, [5:0] payload.
// Ports: 0 N, 1 E, 2 S, 3 W, 4 Local, 5 Hub (as Noxim). VCs per port: 2. Input VC index = 2 * port + vc.

module rr_arb #(parameter N = 4) (
    input clk, input rst, input [N-1:0] req, input adv, output reg [N-1:0] gnt
);
    // Rotating priority: the pointer moves past the last granted requester when adv is set.
    function integer clog2(input integer v);
        integer i;
        begin
            clog2 = 0;
            for (i = v - 1; i > 0; i = i >> 1) clog2 = clog2 + 1;
        end
    endfunction
    localparam PW = (N > 1) ? clog2(N) : 1;
    reg [PW-1:0] ptr;
    // Two lowest-set-bit searches: requests at or above the pointer first, then all requests.
    reg [N-1:0] mask;
    integer k;
    always @* begin
        for (k = 0; k < N; k = k + 1) mask[k] = (k >= ptr);
    end
    wire [N-1:0] rm = req & mask;
    wire [N-1:0] g_m = rm & (~rm + 1'b1);
    wire [N-1:0] g_r = req & (~req + 1'b1);
    always @* gnt = (|rm) ? g_m : g_r;
    integer j;
    always @(posedge clk) begin
        if (rst) ptr <= {PW{1'b0}};
        else if (adv && |gnt)
            for (j = 0; j < N; j = j + 1)
                if (gnt[j]) ptr <= (j == N - 1) ? {PW{1'b0}} : j + 1;
    end
endmodule

// One VC FIFO of flip-flops.
module ibuf #(parameter W = 32, parameter DEPTH = 4) (
    input clk, input rst, input wr, input [W-1:0] din, input rd,
    output [W-1:0] dout, output empty
);
    reg [W-1:0] mem [0:DEPTH-1];
    reg [1:0] wp, rp;
    reg [2:0] cnt;
    assign dout = mem[rp];
    assign empty = (cnt == 3'd0);
    always @(posedge clk) begin
        if (wr) mem[wp] <= din;
    end
    always @(posedge clk) begin
        if (rst) begin
            wp <= 2'd0;
            rp <= 2'd0;
            cnt <= 3'd0;
        end else begin
            if (wr) wp <= wp + 2'd1;
            if (rd) rp <= rp + 2'd1;
            cnt <= cnt + (wr ? 3'd1 : 3'd0) - (rd ? 3'd1 : 3'd0);
        end
    end
endmodule

// State of one input VC: idle -> route -> VC allocation -> active until the tail leaves.
module ivc_ctrl #(parameter HDRW = 0, parameter ADAPTIVE = 0) (
    input clk, input rst,
    input empty, input [1:0] front_type,
    output rt_req, input rt_ack, input [2:0] rt_port, input rt_ovc, input [HDRW:0] rt_hdr,
    output va_req, input va_gnt,
    output sa_req_raw, input pop, input tail_pop,
    output reg [2:0] out_port, output reg out_vc, output reg [HDRW:0] hdr
);
    localparam S_IDLE = 2'd0, S_VA = 2'd1, S_ACT = 2'd2;
    reg [1:0] st;
    assign rt_req = (st == S_IDLE) && !empty && front_type[0];
    assign va_req = (st == S_VA);
    assign sa_req_raw = (st == S_ACT) && !empty;
    always @(posedge clk) begin
        if (rst) st <= S_IDLE;
        else case (st)
            S_IDLE: if (rt_ack) st <= S_VA;
            S_VA: if (va_gnt) st <= S_ACT;
                  else if (ADAPTIVE) st <= S_IDLE;   // re-decide, as the simulator does every cycle
            default: if (tail_pop) st <= S_IDLE;
        endcase
    end
    always @(posedge clk) begin
        if (rt_ack) begin
            out_port <= rt_port;
            out_vc <= rt_ovc;
            hdr <= rt_hdr;
        end
    end
endmodule

// One arbiter per output VC; an output VC stays busy from the grant until its tail has left.
module vc_alloc #(parameter P = 5) (
    input clk, input rst,
    input [2*P-1:0] va_req, input [3*2*P-1:0] va_port, input [2*P-1:0] va_vc,
    input [2*P-1:0] release_ovc,
    output [2*P-1:0] va_gnt, output [2*P-1:0] busy
);
    reg [2*P-1:0] busy_r;
    assign busy = busy_r;
    wire [2*P*2*P-1:0] gnt_all;
    genvar o, i;
    generate
        for (o = 0; o < 2 * P; o = o + 1) begin : ovc
            wire [2*P-1:0] req;
            for (i = 0; i < 2 * P; i = i + 1) begin : in
                assign req[i] = va_req[i] && (va_port[3*i+:3] == o / 2) && (va_vc[i] == o % 2) && !busy_r[o];
            end
            rr_arb #(.N(2*P)) arb (.clk(clk), .rst(rst), .req(req), .adv(1'b1), .gnt(gnt_all[o*2*P+:2*P]));
        end
        for (i = 0; i < 2 * P; i = i + 1) begin : g
            wire [2*P-1:0] col;
            for (o = 0; o < 2 * P; o = o + 1) begin : c
                assign col[o] = gnt_all[o*2*P+i];
            end
            assign va_gnt[i] = |col;
        end
        for (o = 0; o < 2 * P; o = o + 1) begin : b
            always @(posedge clk) begin
                if (rst) busy_r[o] <= 1'b0;
                else if (|gnt_all[o*2*P+:2*P]) busy_r[o] <= 1'b1;
                else if (release_ovc[o]) busy_r[o] <= 1'b0;
            end
        end
    endgenerate
endmodule

// Input-first separable switch allocator. Input stage: one VC per port. Output stage: one port per output.
module sw_alloc #(parameter P = 5) (
    input clk, input rst,
    input [2*P-1:0] sa_req, input [3*2*P-1:0] sa_port,
    output [2*P-1:0] sa_gnt,          // per input VC
    output [P*P-1:0] xsel             // [o*P+i]: output o takes input port i
);
    wire [2*P-1:0] in_gnt;
    wire [P*P-1:0] out_req, out_gnt;
    genvar i, o;
    generate
        for (i = 0; i < P; i = i + 1) begin : inp
            wire [1:0] g;
            wire [2:0] port = g[1] ? sa_port[3*(2*i+1)+:3] : sa_port[3*(2*i)+:3];
            wire any = |g;
            wire won;
            rr_arb #(.N(2)) arb (.clk(clk), .rst(rst), .req(sa_req[2*i+:2]), .adv(won), .gnt(g));
            assign in_gnt[2*i+:2] = g;
            for (o = 0; o < P; o = o + 1) begin : r
                assign out_req[o*P+i] = any && (port == o);
            end
            wire [P-1:0] col;
            for (o = 0; o < P; o = o + 1) begin : c
                assign col[o] = out_gnt[o*P+i];
            end
            assign won = |col;
            assign sa_gnt[2*i+:2] = g & {2{won}};
        end
        for (o = 0; o < P; o = o + 1) begin : outp
            rr_arb #(.N(P)) arb (.clk(clk), .rst(rst), .req(out_req[o*P+:P]), .adv(1'b1), .gnt(out_gnt[o*P+:P]));
        end
    endgenerate
    assign xsel = out_gnt;
endmodule

// Occupancy of the downstream VC buffers, per output VC: +1 on a flit sent, -1 on a credit returned.
module credit_ctrs #(parameter P = 5, parameter DEPTH = 4) (
    input clk, input rst, input [2*P-1:0] send, input [2*P-1:0] credit,
    output [3*2*P-1:0] occ, output [2*P-1:0] full
);
    genvar v;
    generate
        for (v = 0; v < 2 * P; v = v + 1) begin : c
            reg [2:0] n;
            assign occ[3*v+:3] = n;
            assign full[v] = (n == DEPTH);
            always @(posedge clk) begin
                if (rst) n <= 3'd0;
                else n <= n + (send[v] ? 3'd1 : 3'd0) - (credit[v] ? 3'd1 : 3'd0);
            end
        end
    endgenerate
endmodule

// Crossbar with output registers.
module xbar #(parameter P = 5, parameter W = 32) (
    input clk, input rst, input [P*W-1:0] in, input [P-1:0] in_vc, input [P*P-1:0] sel,
    output [P*W-1:0] out, output [P-1:0] out_valid, output [P-1:0] out_vc
);
    genvar o;
    generate
        for (o = 0; o < P; o = o + 1) begin : op
            reg [W-1:0] m;
            reg mv;
            integer i;
            always @* begin
                m = {W{1'b0}};
                mv = 1'b0;
                for (i = 0; i < P; i = i + 1)
                    if (sel[o*P+i]) begin
                        m = m | in[i*W+:W];
                        mv = mv | in_vc[i];
                    end
            end
            reg [W-1:0] r;
            reg rv, rc;
            assign out[o*W+:W] = r;
            assign out_valid[o] = rv;
            assign out_vc[o] = rc;
            always @(posedge clk) begin
                r <= m;
                rc <= mv;
                rv <= rst ? 1'b0 : (|sel[o*P+:P]);
            end
        end
    endgenerate
endmodule

module router_core #(parameter P = 5, parameter W = 32, parameter HDRW = 0, parameter HDRLSB = 14, parameter ADAPTIVE = 0) (
    input clk, input rst,
    input [P*W-1:0] in_flit, input [P-1:0] in_valid, input [P-1:0] in_vc, output [2*P-1:0] in_credit,
    output [P*W-1:0] out_flit, output [P-1:0] out_valid, output [P-1:0] out_vc, input [2*P-1:0] out_credit,
    output [2*P-1:0] rt_req, output [2*P*W-1:0] rt_front,
    input [2*P-1:0] rt_ack, input [3*2*P-1:0] rt_port, input [2*P-1:0] rt_ovc, input [(HDRW+1)*2*P-1:0] rt_hdr,
    output [3*2*P-1:0] occ, output [2*P-1:0] busy, output [2*P-1:0] tail_pop_o, output [2*P-1:0] empty_o
);
    wire [2*P-1:0] empty, pop, va_req, va_gnt, sa_raw, sa_req, sa_gnt, full, ovc_v, tail_pop, release_ovc, send;
    wire [3*2*P-1:0] port_v;
    wire [(HDRW+1)*2*P-1:0] hdr_v;
    wire [P*P-1:0] xsel;
    assign pop = sa_gnt;
    assign in_credit = pop;
    assign tail_pop_o = tail_pop;
    assign empty_o = empty;

    wire [P*W-1:0] port_flit;
    wire [P-1:0] port_ovc;
    genvar p, v;
    generate
        for (p = 0; p < P; p = p + 1) begin : ip
            for (v = 0; v < 2; v = v + 1) begin : vc
                localparam I = 2 * p + v;
                wire [W-1:0] front;
                wire wr = in_valid[p] && (in_vc[p] == v);
                ibuf #(.W(W), .DEPTH(4)) buf_i (.clk(clk), .rst(rst), .wr(wr), .din(in_flit[p*W+:W]), .rd(pop[I]),
                                                .dout(front), .empty(empty[I]));
                assign rt_front[I*W+:W] = front;
                assign tail_pop[I] = pop[I] && front[31];
                wire [2:0] o;
                wire ovc;
                ivc_ctrl #(.HDRW(HDRW), .ADAPTIVE(ADAPTIVE)) ctl (.clk(clk), .rst(rst), .empty(empty[I]),
                    .front_type(front[31:30]), .rt_req(rt_req[I]), .rt_ack(rt_ack[I]), .rt_port(rt_port[3*I+:3]),
                    .rt_ovc(rt_ovc[I]), .rt_hdr(rt_hdr[(HDRW+1)*I+:HDRW+1]), .va_req(va_req[I]), .va_gnt(va_gnt[I]),
                    .sa_req_raw(sa_raw[I]), .pop(pop[I]), .tail_pop(tail_pop[I]), .out_port(o), .out_vc(ovc),
                    .hdr(hdr_v[(HDRW+1)*I+:HDRW+1]));
                assign port_v[3*I+:3] = o;
                assign ovc_v[I] = ovc;
                assign sa_req[I] = sa_raw[I] && !full[2*o+ovc];
            end
            // Flit of the VC that won this port; the head leaves with its rewritten fields.
            wire sel1 = sa_gnt[2*p+1];
            wire [W-1:0] f0 = rt_front[(2*p)*W+:W];
            wire [W-1:0] f1 = rt_front[(2*p+1)*W+:W];
            wire [W-1:0] f = sel1 ? f1 : f0;
            assign port_ovc[p] = sel1 ? ovc_v[2*p+1] : ovc_v[2*p];
            if (HDRW > 0) begin : rw
                wire [HDRW:0] h = sel1 ? hdr_v[(HDRW+1)*(2*p+1)+:HDRW+1] : hdr_v[(HDRW+1)*(2*p)+:HDRW+1];
                wire [W-1:0] fw = f;
                reg [W-1:0] fo;
                always @* begin
                    fo = fw;
                    if (fw[30]) fo[HDRLSB+:HDRW] = h[HDRW-1:0];
                end
                assign port_flit[p*W+:W] = fo;
            end else begin : norw
                assign port_flit[p*W+:W] = f;
            end
        end
        // Flits sent and released per output VC.
        for (v = 0; v < 2 * P; v = v + 1) begin : ov
            wire [2*P-1:0] s, t;
            integer k;
            for (p = 0; p < 2 * P; p = p + 1) begin : m
                assign s[p] = sa_gnt[p] && (port_v[3*p+:3] == v / 2) && (ovc_v[p] == v % 2);
                assign t[p] = s[p] && tail_pop[p];
            end
            assign send[v] = |s;
            assign release_ovc[v] = |t;
        end
    endgenerate

    vc_alloc #(.P(P)) va (.clk(clk), .rst(rst), .va_req(va_req), .va_port(port_v), .va_vc(ovc_v),
                          .release_ovc(release_ovc), .va_gnt(va_gnt), .busy(busy));
    sw_alloc #(.P(P)) sa (.clk(clk), .rst(rst), .sa_req(sa_req), .sa_port(port_v), .sa_gnt(sa_gnt), .xsel(xsel));
    credit_ctrs #(.P(P), .DEPTH(4)) cc (.clk(clk), .rst(rst), .send(send), .credit(out_credit), .occ(occ), .full(full));
    xbar #(.P(P), .W(W)) xb (.clk(clk), .rst(rst), .in(port_flit), .in_vc(port_ovc), .sel(xsel),
                             .out(out_flit), .out_valid(out_valid), .out_vc(out_vc));
endmodule
