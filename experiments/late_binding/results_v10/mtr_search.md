# MTR configuration (formal/mtr_search.py)

One 4x4 chiplet, XY routing, boundary routers = the 4 DeFT VL routers N (1,0), E (3,1), S (2,3), W (0,2).

Inbound turn candidates: 12 (N: ['E', 'S', 'W'], E: ['N', 'S', 'W'], S: ['E', 'N', 'W'], W: ['E', 'N', 'S']); outbound turn candidates: 12 (N: ['E', 'N', 'W'], E: ['E', 'N', 'S'], S: ['E', 'S', 'W'], W: ['N', 'S', 'W']).
Horizontal turns at boundary routers (X->Y, all used by intra-chiplet XY routes, so excluded by the connectivity constraint): 8: E:E->N, E:E->S, N:E->S, N:W->S, S:E->N, S:W->N, W:W->N, W:W->S.

Exhaustive search over 4096 inbound subsets (maximal outbound set each).

**Chosen configuration:** objective Average_distance / Average_reachability = 1.6000 (Average_distance 1.0000, Average_reachability 0.6250); 6 prohibited turns: in E W, in N E, in N W, in S E, in S W, in W E.

| boundary | allowed inbound (Down->) | allowed outbound (->Up, by direction of arrival) | InR | OutR | inbound nodes assigned | outbound nodes assigned |
|---|---|---|---|---|---|---|
| N (1, 0) | ['S'] | ['E', 'N', 'W'] | 4/16 | 16/16 | 4 | 4 |
| E (3, 1) | ['N', 'S'] | ['E', 'N', 'S'] | 4/16 | 16/16 | 4 | 4 |
| S (2, 3) | ['N'] | ['E', 'S', 'W'] | 4/16 | 16/16 | 4 | 4 |
| W (0, 2) | ['N', 'S'] | ['N', 'S', 'W'] | 4/16 | 16/16 | 4 | 4 |

Tables (rows y = 0..3, columns x = 0..3; entry = boundary router used):

Outbound (source -> exit):
```
N N N E
W N E E
W W S E
W S S S
```

Inbound (destination -> entry):
```
W N S E
W N S E
W N S E
W N S E
```

