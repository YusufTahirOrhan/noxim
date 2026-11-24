// v29 E3 (functional check of the buffer depths, not an area or timing run): the router core of rtl/router_core29.v with the
// depths BD (input buffers), CD (the buffers behind the N, E, S, W and Local outputs) and CH (behind the vertical-link output)
// under random packets on every input port and credits that come back late and in bursts, so that the output VCs fill and
// the input buffers fill behind them. The routing is a trivial responder: the head names its output port and output VC.
// Checks: every flit that enters leaves; the flits of a packet leave in order on the port and VC the head named; packets
// stay contiguous per output VC; the unreturned flits of an output VC never exceed the depth of the buffer behind it; and
// both that depth and the depth of the input buffers are reached (so the test did exercise the last slot).
// The macros BUF_DEPTH, CRED_DEPTH and CRED_DEPTH_HUB must be given to the compiler with the same values as BD, CD and CH.
`timescale 1ns/1ps
module tb_core29;
    parameter HAS_HUB = 1, BD = 4, CD = 4, CH = 4, NPKT = 400, SEED = 1;
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
    wire [2*P-1:0] rt_req;
    wire [2*P*W-1:0] rt_front;
    wire [3*2*P-1:0] rt_port;
    wire [2*P-1:0] rt_ovc;
    wire [3*2*P-1:0] occ;
    wire [2*P-1:0] busy, tail_pop;
    genvar g;
    generate
        for (g = 0; g < 2 * P; g = g + 1) begin : rt
            assign rt_port[3*g+:3] = rt_front[g*W+27+:3];
            assign rt_ovc[g] = rt_front[g*W+26];
        end
    endgenerate
    router_core #(.P(P), .W(W), .HDRW(0)) dut (.clk(clk), .rst(rst), .in_flit(in_flit), .in_valid(in_valid), .in_vc(in_vc), .in_credit(in_credit),
        .out_flit(out_flit), .out_valid(out_valid), .out_vc(out_vc), .out_credit(out_credit), .rt_req(rt_req), .rt_front(rt_front), .rt_ack(rt_req),
        .rt_port(rt_port), .rt_ovc(rt_ovc), .rt_hdr({(2*P){1'b0}}), .occ(occ), .busy(busy), .tail_pop_o(tail_pop));

    integer sent_pkts[0:5], left[0:5], vcsel[0:5], pkt_len[0:5], cred[0:11], pending[0:11], stall[0:11], exp_seq[0:11];
    reg [31:0] pkt_hdr[0:5];
    reg [11:0] cur_id[0:11];
    reg [11:0] open;
    integer flits_in, flits_out, p, v, i, t, bad, wait_pkts, next_id, seed, max_in, max_link, max_hub, depth_o;
    reg [31:0] f;

    initial begin
        seed = SEED;
        flits_in = 0; flits_out = 0; bad = 0; open = 12'b0; next_id = 0; max_in = 0; max_link = 0; max_hub = 0;
        for (i = 0; i < 6; i = i + 1) begin sent_pkts[i] = 0; left[i] = 0; vcsel[i] = 0; end
        for (i = 0; i < 12; i = i + 1) begin cred[i] = BD; pending[i] = 0; stall[i] = 0; exp_seq[i] = 0; end
        in_valid = 0; in_vc = 0; in_flit = 0; out_credit = 0;
        repeat (4) @(posedge clk);
        #0.1;
        rst = 0;
        repeat (4) @(posedge clk);
        #0.1;
        for (t = 0; t < 2000000; t = t + 1) begin
            for (i = 0; i < 2 * P; i = i + 1)
                if (in_credit[i] === 1'b1) cred[i] = cred[i] + 1;
            in_valid = 0;
            for (p = 0; p < P; p = p + 1) begin
                if (left[p] == 0 && sent_pkts[p] < NPKT && ($random(seed) & 3) != 0) begin
                    f = 0;
                    f[29:27] = {$random(seed)} % P;          // output port
                    f[26] = $random(seed);                   // output VC
                    f[25:14] = next_id;
                    next_id = next_id + 1;
                    pkt_hdr[p] = f;
                    vcsel[p] = {$random(seed)} % 2;
                    pkt_len[p] = 2 + ({$random(seed)} % 7);
                    left[p] = pkt_len[p];
                end
                if (left[p] > 0) begin
                    f = pkt_hdr[p];
                    f[31:30] = (left[p] == pkt_len[p]) ? 2'b01 : (left[p] == 1) ? 2'b10 : 2'b00;
                    f[13:10] = pkt_len[p] - left[p];         // position of the flit in its packet
                    in_flit[p*W+:W] = f;
                    in_vc[p] = vcsel[p];
                    if (cred[2*p+vcsel[p]] > 0 && ($random(seed) & 7) != 0) begin
                        in_valid[p] = 1'b1;
                        cred[2*p+vcsel[p]] = cred[2*p+vcsel[p]] - 1;
                        if (BD - cred[2*p+vcsel[p]] > max_in) max_in = BD - cred[2*p+vcsel[p]];
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
                    i = 2 * p + v;
                    flits_out = flits_out + 1;
                    if (^f === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X in a flit at output %0d", p); end
                    if (f[29:27] != p || f[26] != v) begin bad = bad + 1; if (bad < 5) $display("flit of packet %0d at output %0d VC %0d, asked for %0d VC %0d", f[25:14], p, v, f[29:27], f[26]); end
                    if (f[30] === 1'b1) begin
                        if (open[i]) begin bad = bad + 1; if (bad < 5) $display("head in an open packet, output %0d VC %0d", p, v); end
                        open[i] = 1'b1;
                        cur_id[i] = f[25:14];
                        exp_seq[i] = 0;
                    end else if (!open[i]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("flit outside a packet, output %0d VC %0d", p, v);
                    end
                    if (f[25:14] !== cur_id[i] || f[13:10] != exp_seq[i]) begin
                        bad = bad + 1;
                        if (bad < 5) $display("output %0d VC %0d: flit %0d of packet %0d, expected flit %0d of packet %0d", p, v, f[13:10], f[25:14], exp_seq[i], cur_id[i]);
                    end
                    exp_seq[i] = exp_seq[i] + 1;
                    if (f[31] === 1'b1) open[i] = 1'b0;
                    pending[i] = pending[i] + 1;
                    depth_o = (p == 5) ? CH : CD;
                    if (pending[i] > depth_o) begin bad = bad + 1; if (bad < 5) $display("output %0d VC %0d: %0d flits not returned, depth %0d", p, v, pending[i], depth_o); end
                    if (p == 5) begin if (pending[i] > max_hub) max_hub = pending[i]; end
                    else if (pending[i] > max_link) max_link = pending[i];
                end
                if (out_valid[p] === 1'bx) begin bad = bad + 1; if (bad < 5) $display("X valid at output %0d", p); end
            end
            // credits come back after a random delay; now and then an output VC returns none for a while, so that it fills
            for (i = 0; i < 2 * P; i = i + 1) begin
                if (stall[i] > 0) stall[i] = stall[i] - 1;
                else if (({$random(seed)} % 200) == 0) stall[i] = 30 + ({$random(seed)} % 40);
                if (stall[i] == 0 && pending[i] > 0 && ($random(seed) & 3) == 0) begin
                    out_credit[i] = 1'b1;
                    pending[i] = pending[i] - 1;
                end
            end
            wait_pkts = 0;
            for (p = 0; p < P; p = p + 1) if (sent_pkts[p] < NPKT || left[p] > 0) wait_pkts = 1;
            if (!wait_pkts && flits_out == flits_in) t = 2000000;
        end
        if (max_in != BD || max_link != CD || (HAS_HUB && max_hub != CH)) bad = bad + 1;
        $display("RESULT core29 hub=%0d bd=%0d cd=%0d ch=%0d packets=%0d flits_in=%0d flits_out=%0d max_fill_in=%0d max_unreturned_link=%0d max_unreturned_hub=%0d errors=%0d %s",
                 HAS_HUB, BD, CD, CH, next_id, flits_in, flits_out, max_in, max_link, max_hub, bad, (flits_in == flits_out && bad == 0 && flits_in > 0) ? "OK" : "FAIL");
        $finish;
    end
endmodule
