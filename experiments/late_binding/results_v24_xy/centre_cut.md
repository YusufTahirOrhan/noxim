# A4: flits on the interposer channels that cross the centre (experiments_v24.py cut)

4x4 chipperm at 0.8 x Lsat of DeFT-P (rate 0.0040, offered 0.0320 flits/node/cycle), pipe_all 0, DeFT-P VN options, `-traffic_rng 1`, seeds 101-102, `-deft_lb vc_stats`.
The footprint is 16 x 16. A cut is crossed by 16 interposer channels in each direction: the vertical cut between columns 7 and 8 (one channel per row), the
horizontal cut between rows 7 and 8 (one channel per column). Values: flits per cycle over the measured window, both VCs, mean of the two seeds. A channel
carries at most 0.5 flits per cycle (one flit per two cycles).

| method | accepted (offered 0.0320) | latency | saturated | largest flit rate of any interposer channel (router x, y, direction) | of any Down VL | of any Up VL |
|---|---|---|---|---|---|---|
| DeFT_Dis | 0.0318 | 68.3 | no | 0.301 (5, 12, E) | 0.160 | 0.156 |
| DeFT_Dis_OE_heur | 0.0204 | 864.9 | yes | 0.435 (9, 7, S) | 0.158 | 0.150 |
| DeFT_Dis_O1 | 0.0318 | 69.4 | no | 0.295 (7, 8, N) | 0.159 | 0.157 |
| CI_qlLA_X | 0.0318 | 77.9 | no | 0.449 (3, 7, S) | 0.160 | 0.309 |


## What limits each method

Under chipperm on 4x4 every chiplet sends to the chiplet in the opposite quadrant, so every packet crosses both centre cuts. At this load 128 nodes
x 0.032 = 4.1 flits per cycle cross each cut in each direction; the 16 channels of a cut carry at most 8, so a perfectly balanced network is at 51 % of
the cut (64 % at DeFT-P's Lsat, and the cut is full at an offered load of 0.0625 flits/node/cycle).

* **DeFT_Dis (fixed VLs, XY): nothing limits it at this load.** The run delivers what is offered (0.0318, latency 68). Every cut channel carries
  0.22-0.28 flits per cycle, max / mean at most 1.10, and the head flits wait 0.1-0.2 cycles per flit. XY takes the horizontal part along the row of the
  exit VL and the vertical part along the column of the entry VL, and the four VLs of a chiplet sit in four different rows and four different columns, so
  fixed VLs spread the load over all 16 channels of a cut. Its limit at a higher load is the cut itself and the VLs (largest VL rate 0.16 of 0.5).
* **DeFT_Dis with odd-even paths and the v10 heuristic: saturated at 0.8 x Lsat by the vertical channels of the odd columns.** It accepts 0.0204 of 0.0320
  (64 %), latency 865. The horizontal cut is crossed mostly on odd columns: in the east half the odd columns 9, 11, 13 carry 0.25-0.42 flits per cycle and
  the even columns 8, 10, 12, 14 carry 0.01-0.11, max / mean 2.4-2.7; column 7 carries 0.32-0.40. The fullest channel of the interposer is at 0.435 of 0.5.
  The odd-even rules forbid the turns East -> North and East -> South in even columns, so an east-bound packet that has moved east can turn to the vertical
  only in an odd column (its other choice is to take the vertical part first, in the column of its exit VL): the odd columns do most of the vertical
  work of the east-bound traffic. With those channels full, packets stay blocked across several routers (8-flit
  packets in 4-flit buffers, one VC per VN on the interposer), and the blocking reaches the traffic that does not need the odd columns: the westward
  crossing of the vertical cut carries 1.49 flits per cycle instead of 4.1, with 13.4 waiting cycles per flit. The VLs are not the limit (0.15-0.16, as
  for XY). The measurement agrees with the review's item 1 (0.0214 accepted with its random selection; pile-up on every other column of the east half,
  max / mean 2.3-2.6). Which packets block which is read from the turn rules and the waiting counts; the statistics do not separate east-bound from
  west-bound flits, so that part is an interpretation.
* **DeFT_Dis with the VN-split order (O1): nothing limits it at this load.** 0.0318 accepted, latency 69, every cut channel 0.23-0.28, max / mean at
  most 1.10, VN0 : VN1 = 50 : 50 on every cut. With fixed VLs the YX half of the packets takes the vertical part along the column of the exit VL and the
  horizontal part along the row of the entry VL, which is again one row and one column per VL.
* **CI_qlLA_X (late entry, XY, v10 parameters): not saturated, but the entry choice puts the vertical crossings on half of the columns.** 0.0318 accepted,
  latency 78 (10 cycles more than DeFT_Dis). The vertical cut is exactly as for DeFT_Dis (the horizontal part runs along the row of the exit VL, which
  late binding of the entry does not change). The horizontal cut is not: eight columns carry 0.34-0.44 flits per cycle and the other eight 0.03-0.20,
  max / mean 1.66-1.75, and the fullest Up VL carries 0.31 (DeFT_Dis: 0.16). With the hop weight gamma = 2 the selection takes the two entry VLs of the
  destination chiplet that are nearest on the interposer, and with XY the vertical part runs in the column of the chosen entry VL. So at 0.8 x Lsat its
  fullest channels are already at 0.44 of 0.5 and it pays latency for it; at higher load the occupancy terms move packets to the other two entry VLs
  (seed 91, pipe_all 0, the A0 rows against DeFT-P's v23 runs: 10,469 packets at latency 99 against 10,492 at 102 at 1.0 x Lsat, and 0.0525 accepted
  against 0.0475 at 1.4 x Lsat, so it does not saturate earlier). This is the low-load cost of gamma = 2 that C2 tunes.

## DeFT_Dis (fixed nearest VLs, XY on the interposer)

| cut and direction | the 16 channels (row 0-15 for the vertical cut, column 0-15 for the horizontal cut) | sum | max | max / mean | VN0 : VN1 | wait cycles per flit |
|---|---|---|---|---|---|---|
| vertical cut, eastward (x 7 -> 8) | 0.25 0.25 0.25 0.24 0.26 0.25 0.26 0.27 0.24 0.27 0.25 0.27 0.27 0.27 0.24 0.25 | 4.11 | 0.274 | 1.07 | 50 : 50 | 0.14 |
| vertical cut, westward (x 8 -> 7) | 0.26 0.25 0.24 0.26 0.24 0.25 0.26 0.26 0.25 0.27 0.26 0.25 0.27 0.24 0.25 0.24 | 4.03 | 0.272 | 1.08 | 50 : 50 | 0.11 |
| horizontal cut, southward (y 7 -> 8) | 0.25 0.27 0.24 0.25 0.25 0.26 0.25 0.23 0.26 0.25 0.22 0.25 0.28 0.26 0.26 0.26 | 4.04 | 0.275 | 1.09 | 50 : 50 | 0.22 |
| horizontal cut, northward (y 8 -> 7) | 0.24 0.24 0.26 0.26 0.24 0.25 0.26 0.27 0.26 0.26 0.28 0.24 0.26 0.26 0.26 0.25 | 4.09 | 0.281 | 1.10 | 50 : 50 | 0.23 |

## DeFT_Dis with `ipos_tm OE` and `-sel DEFT_HEUR` (fixed VLs, odd-even paths chosen by the v10 heuristic)

| cut and direction | the 16 channels (row 0-15 for the vertical cut, column 0-15 for the horizontal cut) | sum | max | max / mean | VN0 : VN1 | wait cycles per flit |
|---|---|---|---|---|---|---|
| vertical cut, eastward (x 7 -> 8) | 0.06 0.19 0.27 0.18 0.26 0.33 0.35 0.30 0.26 0.28 0.32 0.23 0.19 0.28 0.22 0.06 | 3.78 | 0.350 | 1.48 | 50 : 50 | 1.25 |
| vertical cut, westward (x 8 -> 7) | 0.07 0.06 0.06 0.05 0.05 0.07 0.07 0.10 0.15 0.17 0.15 0.12 0.10 0.10 0.10 0.08 | 1.49 | 0.174 | 1.87 | 55 : 45 | 13.43 |
| horizontal cut, southward (y 7 -> 8) | 0.09 0.11 0.10 0.10 0.12 0.14 0.16 0.32 0.11 0.41 0.05 0.35 0.03 0.25 0.02 0.11 | 2.48 | 0.413 | 2.67 | 51 : 49 | 6.20 |
| horizontal cut, northward (y 8 -> 7) | 0.11 0.16 0.13 0.16 0.18 0.23 0.20 0.40 0.04 0.42 0.03 0.34 0.01 0.25 0.02 0.09 | 2.78 | 0.423 | 2.43 | 53 : 47 | 4.61 |

## DeFT_Dis with `ipos_tm O1` (fixed VLs, XY in VN0 and YX in VN1)

| cut and direction | the 16 channels (row 0-15 for the vertical cut, column 0-15 for the horizontal cut) | sum | max | max / mean | VN0 : VN1 | wait cycles per flit |
|---|---|---|---|---|---|---|
| vertical cut, eastward (x 7 -> 8) | 0.26 0.24 0.25 0.26 0.26 0.25 0.26 0.27 0.25 0.26 0.27 0.26 0.26 0.26 0.25 0.25 | 4.11 | 0.272 | 1.06 | 50 : 50 | 0.17 |
| vertical cut, westward (x 8 -> 7) | 0.25 0.27 0.24 0.25 0.24 0.26 0.26 0.27 0.26 0.26 0.25 0.25 0.26 0.24 0.24 0.25 | 4.03 | 0.267 | 1.06 | 50 : 50 | 0.15 |
| horizontal cut, southward (y 7 -> 8) | 0.26 0.27 0.24 0.25 0.25 0.26 0.25 0.24 0.26 0.24 0.23 0.25 0.25 0.26 0.26 0.26 | 4.05 | 0.272 | 1.07 | 50 : 50 | 0.19 |
| horizontal cut, northward (y 8 -> 7) | 0.25 0.25 0.26 0.24 0.24 0.25 0.26 0.28 0.26 0.27 0.27 0.24 0.26 0.26 0.24 0.27 | 4.10 | 0.283 | 1.10 | 50 : 50 | 0.19 |

## CI_qlLA_X (late entry, XY on the interposer, v10 parameters)

| cut and direction | the 16 channels (row 0-15 for the vertical cut, column 0-15 for the horizontal cut) | sum | max | max / mean | VN0 : VN1 | wait cycles per flit |
|---|---|---|---|---|---|---|
| vertical cut, eastward (x 7 -> 8) | 0.25 0.25 0.25 0.24 0.26 0.25 0.26 0.27 0.24 0.27 0.25 0.27 0.27 0.27 0.24 0.25 | 4.11 | 0.274 | 1.07 | 50 : 50 | 0.14 |
| vertical cut, westward (x 8 -> 7) | 0.26 0.25 0.24 0.26 0.24 0.25 0.26 0.26 0.25 0.27 0.26 0.25 0.27 0.24 0.25 0.24 | 4.03 | 0.272 | 1.08 | 50 : 50 | 0.11 |
| horizontal cut, southward (y 7 -> 8) | 0.07 0.38 0.12 0.43 0.06 0.39 0.11 0.43 0.41 0.41 0.03 0.14 0.40 0.44 0.04 0.17 | 4.05 | 0.442 | 1.75 | 50 : 50 | 0.43 |
| horizontal cut, northward (y 8 -> 7) | 0.20 0.03 0.42 0.34 0.20 0.04 0.42 0.36 0.40 0.17 0.39 0.09 0.37 0.18 0.38 0.09 | 4.09 | 0.424 | 1.66 | 50 : 50 | 0.33 |

