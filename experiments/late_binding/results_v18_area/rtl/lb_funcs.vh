// Combinational helpers of the late-binding units. Coordinates are footprint coordinates, 4 bits (zero-extended).
// Directions: 0 N, 1 E, 2 S, 3 W; last = last move direction, 4 = none (injected or vertical arrival).

// Candidate flags: sign and small magnitude of the coordinate differences target - current.
localparam F_EGT0 = 0, F_EGE2 = 1, F_EGE3 = 2, F_ELT0 = 3, F_ELEM2 = 4, F_NLT0 = 5, F_NLEM2 = 6, F_NGT0 = 7, F_NGE2 = 8;

function [8:0] flags_of(input [3:0] x, input [3:0] y, input [3:0] tx, input [3:0] ty);
    reg signed [5:0] dx, dy;
    begin
        dx = $signed({2'b00, tx}) - $signed({2'b00, x});
        dy = $signed({2'b00, ty}) - $signed({2'b00, y});
        flags_of[F_EGT0] = dx > 0;
        flags_of[F_EGE2] = dx >= 2;
        flags_of[F_EGE3] = dx >= 3;
        flags_of[F_ELT0] = dx < 0;
        flags_of[F_ELEM2] = dx <= -2;
        flags_of[F_NLT0] = dy < 0;
        flags_of[F_NLEM2] = dy <= -2;
        flags_of[F_NGT0] = dy > 0;
        flags_of[F_NGE2] = dy >= 2;
    end
endfunction

// Minimal odd-even moves (closed form of movesMask with TM_OE): bit d = direction d.
function [3:0] oe_moves(input even, input [2:0] last, input e_gt0, input e_ge2, input e_lt0, input n_lt0, input n_gt0);
    reg vert_ok;
    begin
        vert_ok = !(even && last == 3'd1) && (!e_lt0 || even);
        oe_moves[0] = n_lt0 && last != 3'd2 && vert_ok;
        oe_moves[1] = e_gt0 && last != 3'd3 && (!(n_lt0 || n_gt0) || e_ge2 || even);
        oe_moves[2] = n_gt0 && last != 3'd0 && vert_ok;
        oe_moves[3] = e_lt0 && last != 3'd1 && !(!even && (last == 3'd0 || last == 3'd2));
    end
endfunction

// Minimal XY moves (movesMask with TM_XY) on reachable states.
function [3:0] xy_moves(input [2:0] last, input e_gt0, input e_lt0, input n_lt0, input n_gt0);
    reg xdone;
    begin
        xdone = !e_gt0 && !e_lt0;
        xy_moves[0] = xdone && n_lt0 && last != 3'd2;
        xy_moves[1] = e_gt0 && last != 3'd3 && last != 3'd0 && last != 3'd2;
        xy_moves[2] = xdone && n_gt0 && last != 3'd0;
        xy_moves[3] = e_lt0 && last != 3'd1 && last != 3'd0 && last != 3'd2;
    end
endfunction

function [4:0] manh(input [3:0] x, input [3:0] y, input [3:0] tx, input [3:0] ty);
    reg [3:0] ax, ay;
    begin
        ax = (x > tx) ? x - tx : tx - x;
        ay = (y > ty) ? y - ty : ty - y;
        manh = ax + ay;
    end
endfunction

// VL slot positions inside a 4x4 chiplet: N (1,0), E (3,1), S (2,3), W (0,2).
function [1:0] slot_lx(input integer s);
    slot_lx = (s == 0) ? 2'd1 : (s == 1) ? 2'd3 : (s == 2) ? 2'd2 : 2'd0;
endfunction
function [1:0] slot_ly(input integer s);
    slot_ly = (s == 0) ? 2'd0 : (s == 1) ? 2'd1 : (s == 2) ? 2'd3 : 2'd2;
endfunction

// Unsigned minimum over a mask (empty mask: all ones), as a tree.
function [7:0] min2(input [7:0] a, input [7:0] b);
    min2 = (b < a) ? b : a;
endfunction
function [7:0] min4m(input [31:0] v, input [3:0] m);
    reg [7:0] a, b, c, d;
    begin
        a = m[0] ? v[7:0] : 8'hff;
        b = m[1] ? v[15:8] : 8'hff;
        c = m[2] ? v[23:16] : 8'hff;
        d = m[3] ? v[31:24] : 8'hff;
        min4m = min2(min2(a, b), min2(c, d));
    end
endfunction
