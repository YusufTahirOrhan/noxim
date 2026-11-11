// v25: the reference router core of round 18 (results_v18_area/rtl/router_core.v: rr_arb, ibuf, vc_alloc, sw_alloc,
// credit_ctrs, xbar are used unchanged) with one addition: LATE = 1 lets the output port be chosen in the VC-allocation
// stage (the lookahead fallback asks for an output there, every cycle, until the allocator grants one).
// With LATE = 0 router_core25 is router_core.
//
// Flit: [31:30] type (01 head, 00 body, 10 tail, 11 head and tail), [29:26] dst_x, [25:22] dst_y, [21:18] exit field,
//       [17:14] entry mask, [13:12] default entry slot (designs with a default-VL penalty), rest payload.
// Ports: 0 N, 1 E, 2 S, 3 W, 4 Local, 5 Hub. VCs per port: 2. Input VC index = 2 * port + vc.

// State of one input VC: idle -> route -> VC allocation -> active until the tail leaves.
module ivc_ctrl25 #(parameter HDRW = 0, parameter ADAPTIVE = 0, parameter LATE = 0) (
    input clk, input rst,
    input empty, input [1:0] front_type,
    output rt_req, input rt_ack, input [2:0] rt_port, input rt_ovc, input [HDRW:0] rt_hdr,
    input va_ok, input [2:0] va_port_i, input [HDRW:0] va_hdr_i,     // LATE: the request of this cycle
    output va_req, input va_gnt, output [2:0] va_port_o,
    output sa_req_raw, input pop, input tail_pop,
    (* v25r *) output reg [2:0] out_port, (* v25r *) output reg out_vc, (* v25r *) output reg [HDRW:0] hdr
);
    localparam S_IDLE = 2'd0, S_VA = 2'd1, S_ACT = 2'd2;
    (* v25r *) reg [1:0] st;
    assign rt_req = (st == S_IDLE) && !empty && front_type[0];
    assign va_req = (st == S_VA) && (LATE ? va_ok : 1'b1);
    assign va_port_o = LATE ? va_port_i : out_port;
    assign sa_req_raw = (st == S_ACT) && !empty;
    always @(posedge clk) begin
        if (rst) st <= S_IDLE;
        else case (st)
            S_IDLE: if (rt_ack) st <= S_VA;
            S_VA: if (va_gnt) st <= S_ACT;
                  else if (ADAPTIVE && !LATE) st <= S_IDLE;   // re-decide, as the simulator does every cycle
            default: if (tail_pop) st <= S_IDLE;
        endcase
    end
    always @(posedge clk) begin
        if (rt_ack) begin
            out_vc <= rt_ovc;
            if (!LATE) begin
                out_port <= rt_port;
                hdr <= rt_hdr;
            end
        end
        if (LATE && st == S_VA && va_gnt) begin
            out_port <= va_port_i;
            hdr <= va_hdr_i;
        end
    end
endmodule

module router_core25 #(parameter P = 5, parameter W = 32, parameter HDRW = 0, parameter HDRLSB = 14, parameter ADAPTIVE = 0,
                       parameter LATE = 0) (
    input clk, input rst,
    input [P*W-1:0] in_flit, input [P-1:0] in_valid, input [P-1:0] in_vc, output [2*P-1:0] in_credit,
    output [P*W-1:0] out_flit, output [P-1:0] out_valid, output [P-1:0] out_vc, input [2*P-1:0] out_credit,
    output [2*P-1:0] rt_req, output [2*P*W-1:0] rt_front,
    input [2*P-1:0] rt_ack, input [3*2*P-1:0] rt_port, input [2*P-1:0] rt_ovc, input [(HDRW+1)*2*P-1:0] rt_hdr,
    input [2*P-1:0] va_ok, input [3*2*P-1:0] va_port, input [(HDRW+1)*2*P-1:0] va_hdr,
    output [3*2*P-1:0] occ, output [2*P-1:0] busy, output [2*P-1:0] pop_o, output [2*P-1:0] tail_pop_o
);
    wire [2*P-1:0] empty, pop, va_req, va_gnt, sa_raw, sa_req, sa_gnt, full, ovc_v, tail_pop, release_ovc, send;
    wire [3*2*P-1:0] port_v, vaport_v;
    wire [(HDRW+1)*2*P-1:0] hdr_v;
    wire [P*P-1:0] xsel;
    assign pop = sa_gnt;
    assign in_credit = pop;
    assign tail_pop_o = tail_pop;
    assign pop_o = pop;

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
                ivc_ctrl25 #(.HDRW(HDRW), .ADAPTIVE(ADAPTIVE), .LATE(LATE)) ctl (.clk(clk), .rst(rst), .empty(empty[I]),
                    .front_type(front[31:30]), .rt_req(rt_req[I]), .rt_ack(rt_ack[I]), .rt_port(rt_port[3*I+:3]),
                    .rt_ovc(rt_ovc[I]), .rt_hdr(rt_hdr[(HDRW+1)*I+:HDRW+1]),
                    .va_ok(va_ok[I]), .va_port_i(va_port[3*I+:3]), .va_hdr_i(va_hdr[(HDRW+1)*I+:HDRW+1]),
                    .va_req(va_req[I]), .va_gnt(va_gnt[I]), .va_port_o(vaport_v[3*I+:3]),
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
            for (p = 0; p < 2 * P; p = p + 1) begin : m
                assign s[p] = sa_gnt[p] && (port_v[3*p+:3] == v / 2) && (ovc_v[p] == v % 2);
                assign t[p] = s[p] && tail_pop[p];
            end
            assign send[v] = |s;
            assign release_ovc[v] = |t;
        end
    endgenerate

    vc_alloc #(.P(P)) va (.clk(clk), .rst(rst), .va_req(va_req), .va_port(vaport_v), .va_vc(ovc_v),
                          .release_ovc(release_ovc), .va_gnt(va_gnt), .busy(busy));
    sw_alloc #(.P(P)) sa (.clk(clk), .rst(rst), .sa_req(sa_req), .sa_port(port_v), .sa_gnt(sa_gnt), .xsel(xsel));
    credit_ctrs #(.P(P), .DEPTH(4)) cc (.clk(clk), .rst(rst), .send(send), .credit(out_credit), .occ(occ), .full(full));
    xbar #(.P(P), .W(W)) xb (.clk(clk), .rst(rst), .in(port_flit), .in_vc(port_ovc), .sel(xsel),
                             .out(out_flit), .out_valid(out_valid), .out_vc(out_vc));
endmodule
