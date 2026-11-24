# A2: the tables of the three new traffic patterns (experiments_v29.py a2_traffic)

`gen_traffic.py --patterns tornado,neighbour,randperm`. Checked on every table of the three patterns that exists in the traffic folders when the stage is run
(the table at 0.0050 packets/cycle/source, written for this check, and the tables of the ladders once B0 has made them), read back from the files:
*sources*: every router of the chiplet layer sends; *sum*: the rates of a source add up to the nominal rate of the table (largest deviation over the sources,
in packets/cycle; the tables have nine decimals per line); *pattern*: `tornado`: one destination per source, in the same row, ((x + FW / 2 - 1) mod FW, y);
`neighbour`: the destinations of a source are exactly the routers of the chiplets that share an edge with its chiplet, each with the same rate; `randperm`:
one destination per source, the destinations are a permutation of the routers, no router sends to itself, and the table is the one of
`gen_traffic.randperm_table()` (`random.Random(2901)`), which is written to `randperm_<size>.txt`.

| size | pattern | tables | routers | sources | largest deviation of a sum | pattern | destinations in the own chiplet |
|---|---|---|---|---|---|---|---|
| 2x2 | tornado | 1 | 64 | all | 0.0e+00 | yes | 25.0 % |
| 2x2 | neighbour | 1 | 64 | all | 0.0e+00 | yes | 0.0 % |
| 2x2 | randperm | 1 | 64 | all | 0.0e+00 | yes | 23.4 % |
| 3x3 | tornado | 1 | 144 | all | 0.0e+00 | yes | 0.0 % |
| 3x3 | neighbour | 1 | 144 | all | 1.6e-08 | yes | 0.0 % |
| 3x3 | randperm | 1 | 144 | all | 0.0e+00 | yes | 9.7 % |
| 4x4 | tornado | 1 | 256 | all | 0.0e+00 | yes | 0.0 % |
| 4x4 | neighbour | 1 | 256 | all | 1.6e-08 | yes | 0.0 % |
| 4x4 | randperm | 1 | 256 | all | 0.0e+00 | yes | 5.9 % |

**All tables pass: yes.**
