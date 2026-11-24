# Stated in advance (v29)

Written on 24 Nov 2026 at about 14:55, after the code change of A1 was built and while its regression ran: before any gate of A2, before
any ladder of the new traffic patterns and before any run of Parts B to G. It is copied unchanged into `PREREGISTRATION.md`.

**What I had seen of the new options when I wrote this** (six smoke runs of the new binary, made to see that the options are accepted; seed
121, pipe_all 2):
* DeFT_P on 2x2 under uniform traffic at 2.4 x Lsat: accepted throughput 0.1205 flits/node/cycle with 4-flit buffers, 0.1263 with
  `-buffer 5` (+4.8 %), 0.1283 with `-buffer_ipos 7` (+6.5 %). One run each, far above saturation.
* The main row with `entry_commit first` and the main row's own `lut_bias`, uniform traffic at 1.0 x Lsat: on 2x2 the same accepted
  throughput as the main row and a mean latency of 66.5 cycles against 61.0; on 4x4 a mean latency of 108.0 cycles (no run of the main row
  next to it). Of the heads that were bound, 34 % (2x2) and 21 % (4x4) were bound at the router below the exit VL.

Nothing else: no run of a new traffic pattern, of a row at depth 6, of `LB_b0`, `LB_noLA`, `MTR_static` or `RC_static` at pipe_all 2 in
this round, and no tuning run.

## Part B: scenarios never used

**The prompt's expectation**, quoted: "the main row is ahead of DeFT_P in all three scenarios on every size. Against the best reference I
expect about zero on 2x2 and a few percent on 3x3 and 4x4 for `tornado` and `randperm`, and nothing for `neighbour`, whose paths are
short. `LB_b0` loses less than 1 % of throughput on 2x2."

**Mine:**
* **Against DeFT_P, over the three new scenarios:** the main row is ahead on every size, THR +5 to +12 % and LAT at 1.0 x Lsat -25 to
  -40 %; ahead in each of the nine cells of scenario and size in both metrics. The smallest gain is under `neighbour` (THR +3 to +10 %).
  All six tests (a) of family 1 supported.
* **Against the best of the five references, over the three new scenarios:**

  | size | THR | LAT at 1.0 x Lsat |
  |---|---|---|
  | 2x2 | -2 to +2 %, more likely below 0 than above | -8 to +5 % |
  | 3x3 | +1 to +6 % | -12 to 0 % |
  | 4x4 | +2 to +7 % | -15 to -2 % |

  So of the six tests (b) I expect the four on 3x3 and 4x4 supported (the LAT test on 3x3 is the one of them I am least sure of) and the
  two on 2x2 not supported, the THR test there possibly against. **Family 1: 9 or 10 of 12 supported, at most one against.**
* **Per scenario against the best reference** (THR; 2x2 / 3x3 and 4x4): `tornado` 0 to +5 % / +3 to +10 %; `randperm` -3 to +2 % /
  +2 to +8 %; `neighbour` -5 to 0 % / -1 to +6 %. I do not expect "nothing" for `neighbour` on 4x4: every packet of it crosses two VLs and
  has four entry candidates, which is what the main row works on; I expect a loss on 2x2, as under localized traffic in round 25.
* **Which reference is the best:** MTR or RC for THR and LAT in most of the nine cells; a DeFT variant under `tornado` on 4x4 (as under
  chipperm traffic in round 25).
* **The five scenarios that the tuning never saw, taken together** (the mean of the five per-scenario effects against the best reference):
  THR -3 to 0 % on 2x2, 0 to +3 % on 3x3, +1 to +5 % on 4x4; LAT at 1.0 x Lsat 0 to +5 % on 2x2 and 3x3 (the main row slower) and -5 to
  +3 % on 4x4. That is: behind on 2x2, level on 3x3, a little ahead on 4x4. Against the two references that tolerate VL faults (the best
  of DeFT_P and DeFT_B) ahead on every size in both metrics.
* **`LB_b0` on 2x2:** within 1 % of the main row in THR in every group of scenarios (the three new ones, the four of the tuning, the other
  two of round 25). LAT at 1.0 x Lsat 1 to 4 % higher than the main row on the four tuning scenarios (that difference is why the tuning
  chose 2) and within 2 % elsewhere. Against the best reference it gives the same picture as the main row. So I expect the answer "the
  paper can use one configuration for all sizes, for a few per cent of latency on the tuning scenarios of 2x2".

## Part C: references with the area of the main row

**The prompt's expectation**, quoted: "6-flit buffers give a reference 3 to 8 % more throughput, 5-flit buffers about half of that. The
main row stays ahead of the DeFT variants at depth 5 and 6 on 3x3 and 4x4 and is about level on 2x2; against MTR and RC at depth 6 it is
level or behind in throughput on every size, at depth 5 about level, and its latency at DeFT's Lsat is no longer lower."

**Mine** (the smoke runs above moved me upwards from the prompt's 3 to 8 %):
* **What the buffers buy a reference** (against itself at depth 4, over the six scenarios): THR +5 to +10 % at depth 6 and +3 to +5 % at
  depth 5; LAT at 1.0 x Lsat of DeFT_P -20 to -40 % for DeFT_P and DeFT_B (they sit on their knee at that load) and -10 to -25 % for MTR
  and RC. `X_i7` buys about what `X_d6` buys (the interposer is where the buffers count).
* **Family 2, the main row at depth 4 against the best of `DeFT_P_d6` and `DeFT_B_d6` (a):** THR -3 to +2 % on 2x2 (not supported),
  +2 to +8 % on 3x3 and +1 to +6 % on 4x4 (both supported); LAT -10 to +10 % on 2x2 (not supported) and -15 to +5 % on 3x3 and 4x4
  (I expect one of the two supported).
* **Against the best of the four references at depth 6 (b):** THR -8 to -3 % on 2x2 (against), -3 to +2 % on 3x3 and 4x4 (not
  significant, or against); LAT +5 to +25 % on every size (against).
* **Family 2 in numbers: 2 to 4 of 12 supported, 4 to 6 against.** The paper's sentence would then be the one the prompt writes: the gain
  over MTR and RC does not survive equal area.
* **At depth 5** (about the main row's area with the core kept): against the best of the four references THR -4 to -1 % on 2x2, 0 to
  +4 % on 3x3 and 4x4; LAT within -5 to +10 %. Against the DeFT variants at depth 5 ahead on 3x3 and 4x4 in both metrics, level on 2x2.
* **`LB_d6`:** THR +4 to +8 % against the main row; against the best reference at depth 6 about what the main row has against the best
  reference at depth 4 or a little less (THR -1 / +5 / +5 % on 2x2 / 3x3 / 4x4): the gain of late binding holds with deeper buffers on both
  sides. The weights of the selection were tuned for 4-flit buffers, so a smaller gain would not surprise me.
* **C3, under faults:** against the best of `DeFT_P_d6` and `DeFT_B_d6` the main row at depth 4 is behind in THR at the rate 4/16 on every
  size (-6 to -1 %) and level to behind at 1/16 (-3 to +2 %); in LAT between -5 and +15 %. At depth 4 it was ahead by 3 to 9 % in THR and
  17 to 20 % in LAT (round 26).

## The other parts (not asked for; one line each, so that they can be held against the results)
* **D1:** the per-hop VC choice gives MTR and RC +2 to +5 % THR and -5 to -15 % LAT at 1.0 x Lsat against one VC per packet. Against the
  best of DeFT_P, DeFT_B, `MTR_static`, `RC_static` and XY_SP the main row is about two points further ahead in THR than against the
  per-hop rows.
* **D2:** DeFT_P has the lowest latency of DeFT_P, MTR and RC only at the lowest loads (up to 0.3 to 0.5 x Lsat) against the per-hop rows,
  and up to 0.6 to 0.8 x Lsat under uniform traffic against the static rows; under hotspot traffic at no load above 0.3 x Lsat; the same
  at pipe_all 0.
* **E1:** `LB_noLA` against the main row: THR -1 to -2 %, LAT at 1.0 x Lsat +4 to +10 %.
* **F1:** `EB_first` reaches 50 to 80 % of the main row's THR gain and of its LAT gain, more than `EB_down_t` on 3x3 and 4x4; its tuned
  `lut_bias` is 2 or 4.
* **F2:** the share of the main row's gain falls with the age of the information on every size: with 16 cycles between `EB_best` and
  `EB_best64`, with 256 cycles 10 to 25 points below `EB_best64`.
