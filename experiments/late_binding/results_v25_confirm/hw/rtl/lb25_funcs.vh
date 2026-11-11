// Helpers of the v25 late-binding units. Coordinates are footprint coordinates, 4 bits (zero-extended).
// Directions: 0 N, 1 E, 2 S, 3 W, 4 Hub. last = last move of the head (0..3), 4 = none (it arrived over the Down link).

// VL slot positions inside a 4x4 chiplet: N (1,0), E (3,1), S (2,3), W (0,2).
function [1:0] slot_lx(input integer s);
    slot_lx = (s == 0) ? 2'd1 : (s == 1) ? 2'd3 : (s == 2) ? 2'd2 : 2'd0;
endfunction
function [1:0] slot_ly(input integer s);
    slot_ly = (s == 0) ? 2'd0 : (s == 1) ? 2'd1 : (s == 2) ? 2'd3 : 2'd2;
endfunction

function [1:0] absd2(input [1:0] a, input [1:0] b);
    absd2 = (a > b) ? a - b : b - a;
endfunction
