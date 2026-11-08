# B1: head latency against -pipe_all (experiments_v23.py probe)

One source-destination pair at rate 0.0005, DEFT routing, 2x2 fault-free; latency = head latency from generation (cycles). Without the option a hop costs 2 cycles (link + router) and the PE-to-router and router-to-PE links 2 each; -pipe_all N must add N per router on the path.

| pair (routers on the path) | pipe_all 0 | pipe_all 2 | pipe_all 3 | per-router increment at 2 / 3 |
|---|---|---|---|---|
| 1hop (2 routers) | 4.0 | 8.0 | 10.0 | 2.00 / 3.00 |
| 3hop (4 routers) | 8.0 | 16.0 | 20.0 | 2.00 / 3.00 |
| 16hop (17 routers) | 34.0 | 68.0 | 85.0 | 2.00 / 3.00 |
