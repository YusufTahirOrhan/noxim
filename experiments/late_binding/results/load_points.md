# Load points (from `experiments.py sat` + `analyze.py sat`, DeFT, seed 101, mask 0x0000)

Rates are packets/cycle/source (offered load in flits/node/cycle = 8 x rate), all on the
0.001 grid of `gen_traffic.py`. Sweep: 0.001 steps up to 0.016, then 0.018, 0.020, 0.024.

Lsat criterion: the largest swept rate whose mean latency is at most 3x the zero-load
latency L0 (latency at rate 0.001). At every Lsat below, accepted/offered >= 0.97.

| pattern   | L0 (cycles) | Lsat  | lat/L0 at Lsat | lat/L0 at next rate |
|-----------|-------------|-------|----------------|---------------------|
| uniform   | 20.8        | 0.011 | 2.84           | 4.45                |
| localized | 18.3        | 0.013 | 2.60           | 3.12                |
| hotspot   | 19.6        | 0.007 | 1.97           | 3.45                |
| chipperm  | 28.3        | 0.004 | 1.76           | 4.14                |
| movinghot | 21.0        | 0.007 | 2.76           | 6.38                |

Tuning points: [~0.8 Lsat, ~1.1 Lsat] rounded to the grid. Where 1.1 Lsat rounds back to
Lsat (chipperm, hotspot, movinghot), the next grid rate above Lsat is used so that one
tuning point is past the knee: chipperm 0.005 (1.25x), hotspot/movinghot 0.008 (1.14x).

Evaluation points: 7 rates from ~0.2x to ~1.6x Lsat, denser near the knee:
uniform 0.18-1.64x, localized 0.23-1.62x, hotspot/movinghot 0.29-1.57x.
chipperm has a low Lsat (0.004), so the 0.001 grid only allows 0.25x-1.75x.

Caveats: Lsat is from one seed on the fault-free network. The faulty scenarios
(0x1111, 0x9C63) use the same rates and saturate earlier, so more of their points lie
beyond saturation. Above saturation the fixed-window mean latency grows with the window
and is not a steady-state value; comparisons there use accepted throughput.
