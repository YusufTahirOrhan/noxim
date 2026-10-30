# Q-table cost with the tested entry width (v16; update of results_v12_energy/report/cost_table.md)

Entry width B = 16 bits (no tested width was equivalent everywhere; 16 bits kept). Q table per router with an adaptive choice: C destination-chiplet keys x 5 outputs x B bits. A router's input buffers: 1536 bits (6 ports x 2 VCs x 4 flits x 32 bits).

| size | Q table (bits) | share of the input-buffer bits | at 16 bits |
|---|---|---|---|
| 2x2 | 320 | 21 % | 320 (21 %) |
| 3x3 | 720 | 47 % | 720 (47 %) |
| 4x4 | 1280 | 83 % | 1280 (83 %) |
