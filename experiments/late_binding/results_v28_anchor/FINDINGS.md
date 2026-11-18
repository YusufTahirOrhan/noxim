# Findings v28: the strongest early binder

Status: **Parts A, B and C are complete; Parts D and E are running.** The gates, the pre-registration, the tuning (Part B, 8,800 runs),
the addendum with the frozen configurations and the evaluation without faults (Part C, 11,340 runs) are done: no run is missing, nothing
was dropped by the time rule, there is no dead-end event in any run, and no hop of an early row offers more than one output. Answers 1 to
9 below are final. Answers 10 to 12 (the early rows under faults, the reports across the VLs under faults, the paragraph) are open.

**The question of the round.** Round 27's early rows were a weak class of early binders: their family did not contain DeFT, and they
herded. This round builds the strongest early binder we can (ideal information, a count of the packets already bound to each VL, an
anchor at DeFT-P's entry VL with a threshold, so that the family contains DeFT_P) and gives it the same tuning as the main row. How much of
the main row's gain can a congestion-aware choice reach if it is bound early? Also: the reports across the VLs under faults.

## The answer in short (so far: without faults)
**Without faults the strongest early binder reaches the main row on 2x2, where it is slightly ahead, and most of the main row's gain on 3x3
and 4x4: 66 and 75 % of the throughput gain over DeFT_P and 93 and 82 % of the latency gain at 1.0 x Lsat. Round 27's answer ("without
faults the gain comes from binding late") was an answer about early binders that herd. It does not hold for an early binder that counts the
packets already bound to each VL. What stays true is narrower: the main row gets from local information, at the routers on the way, what
an early choice gets only from knowing the whole network at the moment of injection.**
* **Primary family 1: 10 of 12 supported, 2 against** (question 3). The two against are the tests against `EB_best` on 2x2, where the early
  row has 0.9 % more throughput than the main row and 3.7 % less latency. On 3x3 and 4x4 the main row is ahead of `EB_best` by 4.4 and 2.9 %
  in THR and by 3.0 and 7.8 % in LAT; of `EB_down_t` it is ahead on every size (THR 1.8 to 7.1 %, LAT 17 to 22 %).
* **Shares of the main row's gain over DeFT_P** (question 4; THR / LAT at 1.0 x Lsat, 2x2 / 3x3 / 4x4): `EB_best` 113 / 66 / 75 % and 109 /
  93 / 82 %. Under hotspot traffic alone 93 to 96 % and 97 to 102 %; in the other five scenarios together 129 / 58 / 66 % and 114 / 90 / 74 %.
* **`EB_best` is not DeFT with a correction for hot spots** (question 7). It leaves DeFT-P's entry VL for a quarter of the packets on 2x2 and
  for half of them on 3x3 and 4x4, in every scenario alike and nearly as often at half the saturation load, and it is ahead of DeFT_P in
  every scenario on every size.
* **What makes it strong is the count of the packets already bound, not the anchor** (question 2). Without the count the best member of the
  family scores +0.20 and +0.22 with a large anchor and -0.60 and -0.12 without one (round 27's rows). With the count every member scores
  +0.35 to +0.55, and the anchor adds +0.02 and +0.01.
* **That knowledge is the price** (questions 8 and 9). `EB_best` reads every buffer at the entry VLs and every packet already bound, without
  delay and without wires. With the same state up to 64 cycles old (`EB_best64`) it reaches 82 / 46 / 58 % of the THR gain and 72 / 48 / 51 %
  of the LAT gain. With what the main row knows at its first decision on the interposer, bound there (`EB_down_t`), 74 / 46 / 46 % and 56 /
  58 / 43 %. No tuned row is behind DeFT_P on any size.
* **What the strongest early binder does not reach**: on 3x3 and 4x4 a third and a quarter of the THR gain (the main row carries on above
  DeFT-P's saturation load, where `EB_best` has 18 to 47 % more latency), and a small lead of the main row at low load (1 to 2.4 % at 0.2 and
  0.5 x Lsat; question 6). On 2x2 nothing.

## Safety of the new rows (A3)
**No new proof and no new model check are needed, and after reading the code I agree with that.** Every new row binds one functional
entry VL, at injection (`EB_best`, `EB_best64`, the anchor `EB_inf`) or at the Down move (`EB_down_t`, `EB_down_inf`); the options change
which one, never the set it is chosen from.
* **The injection-time rows.** `oracle_bias` and `oracle_pending` enter the cost in `chooseMasks` and nothing else. The candidates are the
  pairs (v, e) with v the LUT's exit VL (a functional VL of the source chiplet) and e a functional VL of the destination chiplet
  (`functionalMask`); the pick is one of them, and from there the head has one exit and one entry candidate. With XY in both layers that
  is the fixed-pair relation `A_fixed_XY` of the formal model, which explores every functional (exit, entry) pair: the relation of DeFT with
  any injection-time choice. `oracle_period` with `oracle_scope route` changes which buffer fills the cost reads (the sample instead of the
  live ones), not the candidates. The pending counters are read in the cost and nowhere else.
* **`EB_down_t` and `EB_down_inf`.** `lut_bias` enters the cost of the commit (`commitEntry`) and the selection's `lutBias` term. For these
  rows the selection never has a choice: in the source chiplet the exit is the LUT's (one output per hop), and from the Down move on the
  entry mask has one candidate. The commit writes `bit(v)` for a member v of the entry mask, so round 27's argument
  (`results_v27_early/FINDINGS.md`, A3) holds for any `lut_bias`, 1e9 included.
* **The diagnostics** read only (`pending_check`: unit check 2, 12 / 12 runs identical with and without it) or move a tie-break to another
  random stream (`tie_stream`; used in the anchor gate only, in no row).
* **Checked by simulation** in every run of the round: no hop of an early row offers more than one output, and there is no dead-end event;
  the drain tests of the new rows (90 / 90) and of the tuned rows (54 / 54) pass, with every pending counter 0 at the end.

## The twelve questions

### 1. Regression and gates: all pass? Are both anchor rows identical to DeFT_P? Is v27 reproduced?
*Final.* **All gates pass and round 27 is reproduced. Neither anchor row is byte-identical to DeFT_P, for a reason the gate pins down: both
take DeFT-P's entry VL for every packet and differ from DeFT_P only by the sequence of the random draws of the crossbar arbitration.**
* **Regression** (`regression_before.md`, `regression.md`): 84 / 84 byte-identical to the b164e9e build before the change, and after it with
  the options absent and with every option of rounds 23 to 28 given at its default (`oracle_bias 0`, `oracle_pending 0`, `pending_check 0`,
  `tie_stream 0` included).
* **The anchors** (`anchor.md`, 21 runs each: the six fault-free scenarios at 1.0 x Lsat with seed 101 and uniform traffic on mask 1 of
  rate 4/16 with seed 151, on three sizes). `EB_inf` = EBf(route, 1, 1, infinity) and `EB_down_inf` = `EB_down` with `lut_bias 1e9` take
  DeFT-P's entry VL for every measured packet in all 21 runs, and are identical to DeFT_P in **0 / 21** runs. The reason: every router's
  crossbar arbitration draws from `rand()` (`Router.cpp`, `rand() % reservations.size()`), and the injection-time choice draws from it once
  per packet even when one candidate is the cheapest (the commit once per commit), so every later arbitration draw is shifted. With the tie
  breaks on a stream of their own (the diagnostic `tie_stream 1`) both rows are identical to DeFT_P in **21 / 21** runs. So DeFT_P's routing
  and timing are members of both families exactly; the anchor rows are DeFT_P with another arbitration sequence (mean of the 21 runs
  against DeFT_P: THR -0.04 % and -0.13 %, LAT -0.9 % and -0.2 %; single runs near saturation differ by up to 10 % in LAT). As the prompt
  asks for that case, the anchor rows join Parts C and D and the tuned rows are compared with them as well as with DeFT_P.
* **The anchor rows in Part C** (`report/summary_C.md` C.4; 1,620 runs each on seeds 171-180): level with DeFT_P on every size. `EB_inf` THR
  0.0 / 0.0 / 0.0 %, LAT at 1.0 x Lsat -1.1 / -1.6 / +0.1 %; `EB_down_inf` THR 0.0 / +0.1 / +0.1 %, LAT -0.7 / -0.7 / -0.2 %; every interval
  includes 0. At 0.2 and 0.5 x Lsat they are within 0.01 % of DeFT_P. Per scenario 4 of their 72 THR and LAT cells have an unadjusted
  interval that excludes 0 (the largest: `EB_inf`, LAT -6.8 % under hotspot traffic on 2x2), about what chance gives. So the comparison of
  a tuned row with DeFT_P is not an effect of the random stream, and the comparison with its anchor says the same (question 4).
* **At T = infinity nothing else matters:** EBf(vl, 0, 0.5, infinity) with `oracle_period 64` is identical to EBf(route, 1, 1, infinity) in
  21 / 21 runs, so one anchor row (`EB_inf`) stands for the T = infinity member of every sub-family, of `EB_best` and of `EB_best64`.
* **v27 reproduced** (`repro_v27.md`): `EB_vl_b1` and `EB_route_b4` with the arguments of this round (`oracle_pending 0` and `oracle_bias 0`
  given explicitly), and DeFT_P and the main row: **320 / 320** tuning runs identical to `results_v27_early/tune_runs.csv` in every column.
* **Unit checks** (`unit_checks.md`): the pending counters equal a scan of the network that does not use them (every head of an
  inter-chiplet packet that has not moved Up, in a buffer or on a link, with its packet length, per entry VL) at three cycles, in total and
  per VL, in **12 / 12** runs on three sizes; `pending_check` reads only (12 / 12 identical); `oracle_period 64` takes one sample every 64
  cycles.
* **Drain tests:** the five new rows of the gates (EBf(route, 1, 1, 4), EBf(vl, 1, 1, 4), the same two with `oracle_period 64`, `EB_down`
  with `lut_bias 4`) on six masks per size, **90 / 90** pass (`drain_v28.csv`); the three tuned rows, **54 / 54** (`drain_v28_tuned.csv`).
  Every packet delivered, no dead-end event, no hop that offers more than one output, every pending counter 0 at the end.
* **Reuse check** (`reuse_check.md`): DeFT_P and the main row as round 26 defined them, on masks 1 and 2 of every rate and size, **768 / 768**
  runs identical to `results_v26_faults/fault_rate_runs.csv`.

### 2. The tuning: `EB_best` per size, the best of each sub-family, `EB_best64`, `EB_down_t`; their scores; what the anchor and the pending count buy
*Final* (`tuning_v28.md`, `tuning_choice_v28.json`, `paper_data/tuning_v28.csv`; 8,800 runs of this round on seeds 101 and 102, DeFT_P,
the main row and the P = 0, T = 0 members from round 27; no dead-end event, no hop of an early row with more than one output). **Every chosen
configuration has a finite T and a positive score, so DeFT_P is not the best member of either family. `EB_best` scores about as much as the
main row on 2x2 (+0.551 against +0.530) and three quarters of it on 4x4 (+0.494 against +0.648).** Scores in natural-log units against
DeFT-P (0.01 is about 1 %); THR and the latencies are the three terms of the score against DeFT-P over the five tuning scenarios.

| size | row | configuration | score | THR | LAT at 1.0 x Lsat | LAT at 0.5 x Lsat |
|---|---|---|---|---|---|---|
| 2x2 | main row (frozen) | | **+0.530** | +10.6 % | -33.4 % | -2.3 % |
| 2x2 | `EB_best` | S vl, P 1, B 0.5, T 8 | **+0.551** | +10.7 % | -33.9 % | -3.4 % |
| 2x2 | `EB_best64` | S vl, P 1, B 0.5, T 32, period 64 | +0.347 | +8.4 % | -23.0 % | -0.5 % |
| 2x2 | `EB_down_t` | `lut_bias` 4 | +0.260 | +6.6 % | -17.3 % | -0.5 % |
| 4x4 (and 3x3) | main row (frozen) | | **+0.648** | +17.5 % | -37.3 % | -2.0 % |
| 4x4 (and 3x3) | `EB_best` | S vl, P 1, B 1, T 2 | **+0.494** | +12.9 % | -30.8 % | -0.4 % |
| 4x4 (and 3x3) | `EB_best64` | S vl, P 1, B 1, T 16, period 64 | +0.345 | +10.9 % | -21.3 % | -0.2 % |
| 4x4 (and 3x3) | `EB_down_t` | `lut_bias` 4 | +0.225 | +6.7 % | -14.6 % | -0.3 % |

**The best of each sub-family** (S, P):

| size | (vl, 0) | (vl, 1) | (route, 0) | (route, 1) |
|---|---|---|---|---|
| 2x2 | B 0.25, T 16: +0.171 | **B 0.5, T 8: +0.551** | B 2, T 16: +0.204 | B 0.5, T 8: +0.520 |
| 4x4 | B 0.5, T 16: +0.066 | **B 1, T 2: +0.494** | B 2, T 32: +0.219 | B 0.5, T 4: +0.474 |

* **What the pending count buys: most of it.** At T = 0 (no anchor) the best member with the count scores +0.530 (2x2) and +0.484 (4x4); the
  best without it, which is round 27's rows, -0.597 and -0.116. The count is worth +1.13 and +0.60. With it, every member of (vl, 1) and
  (route, 1) has a positive score, whatever B and T: +0.35 to +0.55 for the 50 members on 2x2, +0.41 to +0.49 for the 45 on 4x4.
* **What the anchor buys: much without the count, little with it.** Without the count the anchor lifts the best member from -0.597 to
  +0.204 (2x2, T = 16) and from -0.116 to +0.219 (4x4, T = 32): an early binder that herds needs to be held at DeFT-P's table. With the count
  the anchor adds +0.021 (2x2) and +0.009 (4x4) to the best member at T = 0. So round 27's early rows lost because they herded (every source
  saw the same empty VL and nothing counted the packets already on their way), not because their family left DeFT-P's table.
* **Which occupancy:** with the count, the occupancy at the entry VL (S = vl) is slightly better than the queues on the route; without it the
  route is better, as in round 27.
* **By scenario** (`tuning_v28.md`; two seeds per cell, so pointers): `EB_best` is ahead of DeFT-P in every tuning scenario on both sizes. On
  2x2 it is level with the main row or ahead (uniform +0.360 against +0.291, hotspot +1.080 against +1.045, uniform with one faulty VL per
  chiplet +0.458 against +0.426; chipperm +0.515 against +0.530, chiptrans +0.339 against +0.359). On 4x4 it is close under hotspot (+0.686
  against +0.729) and chipperm traffic (+0.339 against +0.361) and behind under uniform (+0.488 against +0.642), chiptrans (+0.415 against
  +0.777) and uniform traffic with faults (+0.540 against +0.730).
* **`EB_best64`** needs a larger anchor (T 32 and 16) and loses about a third of `EB_best`'s score (+0.347 and +0.345). **`EB_down_t`** with
  its own `lut_bias` of 4 scores +0.260 and +0.225; with the main row's `lut_bias` (round 27's `EB_down`) it scored -0.242 (2x2, D = 2) and
  -1.409 (4x4, D = 0).
* No chosen value is at the end of what was run: the grid was extended where the rule asked (T to 32 and 64, B to 0.25 and 8; `tuning_v28.md`).
* I had expected `EB_best` from (route, 1) with a score of +0.05 to +0.20 on 4x4 and 0 to +0.10 on 2x2, and the anchor to buy more than the
  count. The tuning showed the reverse on all three points before Part C; the expectations were left as written.

### 3. Primary family 1: how many of 12 supported, which against?
*Final (`report/summary_C.md` C.1, `report/primary_C.csv`; computed a second time by `check_v28_family.py`, which shares no code with the
report: 12 tests, 0 different).* **10 of 12 supported, 2 against, none not significant. The two against are both tests against `EB_best` on
2x2: there the early row has 0.9 % more throughput than the main row and 3.7 % less latency at 1.0 x Lsat.** Effect of the main row
against the early row with its 95 % interval over the ten seeds; p adjusted by Holm over the 12:

| size | early row | THR | p (Holm) | verdict | LAT at 1.0 x Lsat | p (Holm) | verdict |
|---|---|---|---|---|---|---|---|
| 2x2 | `EB_best` | -0.9 [-1.3, -0.5] | 0.00043 | **against** | +3.9 [+2.9, +4.9] | 2.6e-05 | **against** |
| 2x2 | `EB_down_t` | +1.8 [+1.5, +2.1] | 1.1e-06 | supported | -17.7 [-19.6, -15.8] | 7.6e-08 | supported |
| 3x3 | `EB_best` | +4.4 [+4.1, +4.8] | 1.2e-09 | supported | -3.0 [-3.8, -2.1] | 7.1e-05 | supported |
| 3x3 | `EB_down_t` | +7.1 [+6.6, +7.7] | 2.3e-09 | supported | -17.1 [-18.8, -15.3] | 7.6e-08 | supported |
| 4x4 | `EB_best` | +2.9 [+2.6, +3.1] | 2.3e-08 | supported | -7.8 [-9.1, -6.6] | 1.2e-06 | supported |
| 4x4 | `EB_down_t` | +6.4 [+6.0, +6.7] | 5.5e-11 | supported | -22.5 [-24.0, -20.9] | 3.7e-09 | supported |

* **Against `EB_down_t` the main row is ahead in all six tests**, by 1.8 to 7.1 % in THR and by 17 to 22 % in LAT.
* **Against `EB_best` it is ahead on 3x3 and 4x4**, by 4.4 and 2.9 % in THR and by 3.0 and 7.8 % in LAT. These are supported and small:
  both rows gain 9 to 14 % in THR and 31 to 36 % in LAT over DeFT_P there.
* **On 2x2 `EB_best` is ahead of the main row in both metrics.** In each of the ten seeds its THR gain over DeFT_P is larger than the main
  row's (the smallest per-seed share is 102 %, question 4).
* For comparison, round 27: 18 of 18 supported, with the main row 7 to 43 % ahead in THR.

### 4. The share of the main row's gain over DeFT_P that `EB_best`, `EB_best64` and `EB_down_t` reach without faults
*Final (`report/summary_C.md` C.2 and C.4, `paper_data/early_best_effects.csv`).* **`EB_best` reaches all of the main row's gain on 2x2 (113 %
of the THR gain, 109 % of the LAT gain) and most of it on 3x3 and 4x4: 66 and 75 % in THR, 93 and 82 % in LAT. Under hotspot traffic alone
it reaches 93 to 96 % (THR) and 97 to 102 % (LAT); in the other five scenarios together 129 / 58 / 66 % and 114 / 90 / 74 %. `EB_best64`
reaches 82 / 46 / 58 % and 72 / 48 / 51 % over the six scenarios, `EB_down_t` 74 / 46 / 46 % and 56 / 58 / 43 %.** Share = (mean log ratio of the
row against DeFT_P) / (mean log ratio of the main row against DeFT_P), in %, 2x2 / 3x3 / 4x4:

| row | all six: THR | LAT | hotspot alone: THR | LAT | the other five: THR | LAT |
|---|---|---|---|---|---|---|
| `EB_best` | **113 / 66 / 75** | **109 / 93 / 82** | 96 / 93 / 95 | 102 / 98 / 97 | 129 / 58 / 66 | 114 / 90 / 74 |
| `EB_best64` | 82 / 46 / 58 | 72 / 48 / 51 | 97 / 93 / 95 | 94 / 95 / 95 | 70 / 31 / 40 | 56 / 21 / 29 |
| `EB_down_t` | 74 / 46 / 46 | 56 / 58 / 43 | 83 / 65 / 55 | 80 / 72 / 72 | 66 / 41 / 41 | 37 / 50 / 29 |

The smallest and the largest of the ten per-seed shares over the six scenarios: `EB_best` THR 102-133 / 62-71 / 70-80, LAT 105-113 / 87-97 /
77-86; `EB_best64` THR 79-93 / 40-52 / 51-65, LAT 59-79 / 35-61 / 34-59; `EB_down_t` THR 65-80 / 40-55 / 36-51, LAT 34-69 / 47-62 / 30-50.

The effects behind the shares: every row against DeFT_P, in %, 2x2 / 3x3 / 4x4 (intervals in the report):

| row | THR | LAT at 1.0 x Lsat | P99 at 1.0 x Lsat |
|---|---|---|---|
| main row | +7.2 / +13.7 / +12.0 | -35.5 / -35.7 / -36.0 | -54.2 / -64.1 / -63.2 |
| `EB_best` | +8.2 / +8.8 / +8.9 | -37.9 / -33.8 / -30.6 | -58.1 / -63.0 / -58.2 |
| `EB_best64` | +5.9 / +6.0 / +6.8 | -27.1 / -19.0 / -20.4 | -44.4 / -47.9 / -47.7 |
| `EB_down_t` | +5.3 / +6.1 / +5.3 | -21.6 / -22.5 / -17.5 | -32.6 / -39.5 / -33.4 |
| `EB_inf` (anchor) | 0.0 / 0.0 / 0.0 | -1.1 / -1.6 / +0.1 | -2.4 / -3.6 / +1.6 |
| `EB_down_inf` (anchor) | 0.0 / +0.1 / +0.1 | -0.7 / -0.7 / -0.2 | -0.9 / -1.6 / +0.7 |

* **No tuned row is behind DeFT_P**, on any size, in THR, LAT or P99, over the six scenarios, under hotspot traffic or in the other five
  together. In round 27 every early row was behind DeFT_P in THR over the six scenarios, `EB_down` on 2x2 excepted (+0.6 %).
* **`EB_best` gains about the same over DeFT_P on every size** (THR +8.2 / +8.8 / +8.9 %); the main row gains more on the larger networks
  (+7.2 / +13.7 / +12.0 %). So the share falls from 2x2 to 3x3 and 4x4 because the main row's gain grows, not because the early row's shrinks.
* **The share is larger in LAT than in THR on 3x3 and 4x4.** LAT is measured at DeFT-P's saturation load, where `EB_best` is nearly as fast
  as the main row. THR is reached above it, and there the main row carries on while `EB_best` saturates earlier (question 6: at 1.2 x Lsat
  it has 39 and 35 % more latency than the main row on 3x3 and 4x4, at 1.4 x Lsat 47 and 18 % more).
* **Against its own anchor** each tuned row shows the same effects in THR and LAT as against DeFT_P, within 1.3 points (C.4): `EB_best` against `EB_inf`
  THR +8.2 / +8.8 / +8.9 %, LAT -37.2 / -32.7 / -30.6 %; `EB_down_t` against `EB_down_inf` THR +5.3 / +6.0 / +5.2 %, LAT -21.0 / -22.0 / -17.3 %.
* No chosen configuration scored below 0 in the tuning, so no share of "the better of the row and DeFT_P" is needed.

### 5. Per scenario: where is an early row level with or ahead of the main row?
*Final (`report/summary_C.md` C.6, `paper_data/early_best_per_scenario.csv`). Descriptive: unadjusted 95 % intervals over the ten seeds. Below,
"ahead" and "behind" mean that the interval excludes 0, "level" that it includes 0.* **In 42 of the 162 cells (size x scenario x tuned early
row x THR, LAT, P99) an early row is ahead of the main row (24) or level with it (18). `EB_best` is ahead of the main row in THR and LAT under
uniform and localized traffic on 2x2 and in LAT under hotspot and movinghot traffic there. On 3x3 and 4x4 it is behind in every scenario
except movinghot (level in THR on both, ahead in LAT on 3x3) and chipperm on 4x4 (level in LAT). `EB_down_t` is ahead in THR under movinghot
traffic on every size.**

`EB_best` against the main row, THR / LAT at 1.0 x Lsat in % ("a" = `EB_best` ahead, "b" = behind, no letter = the interval includes 0):

| scenario | 2x2 | 3x3 | 4x4 |
|---|---|---|---|
| uniform | **+3.2 a / -3.2 a** | -4.2 b / +6.0 b | -6.6 b / +6.6 b |
| localized | **+4.8 a / -3.9 a** | -2.1 b / +3.8 b | -3.5 b / +6.3 b |
| hotspot | -0.8 / **-2.0 a** | -1.2 b / +1.8 b | -1.1 b / +2.3 b |
| chipperm | -1.5 b / +2.6 b | -13.8 b / +11.4 b | -0.8 b / +0.1 |
| chiptrans | -0.7 b / +2.6 b | -3.1 b / +2.3 b | -4.6 b / +38.9 b |
| movinghot | +0.8 / **-16.9 a** | -0.5 / **-6.3 a** | +0.2 / +1.3 |

* **`EB_best`: 22 of its 54 cells are not behind (13 ahead, 9 level).** On 2x2 it is ahead where the traffic is spread over the chiplets
  (uniform, localized) and behind, by 0.7 to 1.5 % in THR and 2.6 % in LAT, under the two chiplet-to-chiplet patterns (chipperm, chiptrans).
  On 3x3 and 4x4 its largest deficits are chipperm on 3x3 (THR -13.8 %: the main row gains 34.0 % over DeFT_P there, `EB_best` 15.4 %),
  uniform traffic on 4x4 (THR -6.6 %) and chiptrans on 4x4 (LAT +38.9 %: the main row is 52 % faster than DeFT_P there, `EB_best` 34 %).
  Under hotspot traffic it is within 1.2 % in THR and 2.3 % in LAT of the main row on every size.
* **Under movinghot traffic the early rows are level with the main row or ahead of it on every size.** `EB_best`: THR +0.8 / -0.5 / +0.2 %
  (level), LAT -16.9 / -6.3 / +1.3 %, P99 41 / 31 / 22 % lower. `EB_down_t`: THR +1.1 / +1.8 / +2.6 % (ahead), LAT +2.5 / -3.0 / -3.6 % (level,
  level, ahead). In round 27 this was the scenario in which the early rows fell behind DeFT_P again. No row gains much in THR over DeFT_P
  there (the main row +3.1 / +1.6 / +2.0 %).
* **`EB_down_t`: 11 of 54 cells (7 ahead, 4 level):** movinghot as above; on 2x2 also ahead in THR under localized traffic (+3.7 %) and level
  under uniform traffic (+0.4 %), with 7 and 9 % more latency.
* **`EB_best64`: 9 of 54 cells (4 ahead, 5 level):** on 2x2 ahead in THR under localized traffic (+2.2 %) and level in THR under uniform,
  hotspot and movinghot traffic; level in THR under hotspot traffic on 4x4; P99 under movinghot traffic 17 to 18 % lower than the main
  row's on every size. In LAT it is behind the main row in 17 of 18 cells.
* **Against DeFT_P by scenario:** `EB_best` is ahead in THR and LAT in 34 of the 36 cells and level in two (THR under movinghot on 3x3, LAT
  under movinghot on 4x4). `EB_best64` is ahead except under movinghot traffic on 3x3 (level) and 4x4 (THR level, LAT 8.3 % behind).
  `EB_down_t` is level with DeFT_P in THR under chipperm and chiptrans traffic (-0.1 to +0.4 %; chipperm on 3x3 excepted, +6.8 %) and ahead
  elsewhere.

### 6. Latency below saturation (0.2, 0.5, 0.8 x Lsat): all rows
*Final (`report/summary_C.md` C.7, C.8 and C.10).* **Below saturation no tuned early row costs anything worth naming: at 0.2 and 0.5 x Lsat
each is within 0.9 % of DeFT_P or faster. At 0.8 x Lsat `EB_best` is as fast as the main row (6 to 10 % faster than DeFT_P). At 0.2 and
0.5 x Lsat the main row keeps a lead of its own on 3x3 and 4x4, 1.2 to 2.4 % over `EB_best`, which no early row has.** Mean latency against
DeFT_P in %, 2x2 / 3x3 / 4x4 (mean over the six scenarios and the ten seeds; the intervals are in the report, at 0.2 and 0.5 x Lsat at most
0.4 points wide):

| row | 0.2 x Lsat | 0.5 x Lsat | 0.8 x Lsat |
|---|---|---|---|
| main row | -1.7 / -2.8 / -2.2 | -2.0 / -2.2 / -1.5 | -7.1 / -7.0 / -6.8 |
| `EB_best` | -1.3 / -0.4 / -0.3 | -2.9 / -0.6 / -0.4 | -9.6 / -6.4 / -7.0 |
| `EB_best64` | 0.0 / -0.1 / 0.0 | -0.2 / +0.9 / +0.9 | -3.0 / +2.6 / 0.0 |
| `EB_down_t` | -0.1 / 0.0 / 0.0 | -0.3 / -0.3 / -0.2 | -2.7 / -2.4 / -2.4 |
| `EB_inf`, `EB_down_inf` (anchors) | 0.0 / 0.0 / 0.0 | 0.0 / 0.0 / 0.0 | +0.1 / 0.0 / 0.0 |

In cycles at 0.2 / 0.5 / 0.8 x Lsat on 4x4: DeFT_P 63.1 / 68.4 / 87.1, the main row 61.7 / 67.5 / 81.5, `EB_best` 62.9 / 68.2 / 80.9, `EB_best64`
63.0 / 69.1 / 87.6, `EB_down_t` 63.0 / 68.3 / 84.9.

* **0.2 and 0.5 x Lsat.** The main row is 1.5 to 2.8 % faster than DeFT_P, about one cycle, as in rounds 25 and 27. `EB_best` has that on
  2x2 (-1.3 and -2.9 %; at 0.5 x Lsat it is 0.9 % faster than the main row) and not on 3x3 and 4x4 (-0.3 to -0.6 %), where it is 1.2 to 2.4 %
  slower than the main row. The reason is path length. At 0.5 x Lsat the packets of `EB_best` take 2.9 and 2.3 % more hops than DeFT_P's on
  3x3 and 4x4 (11.52 against 11.20, 14.67 against 14.34) and those of the main row 1.3 and 0.8 % fewer (11.05, 14.22): with T = 2 flits, 44 %
  of its packets leave DeFT-P's entry VL at half the saturation load already (question 7), and they pay in hops what they save in waiting.
  On 2x2 (T = 8 flits) 19 % leave and the paths are as long as DeFT_P's (8.25 against 8.27).
* **`EB_best64` and `EB_down_t` stay at DeFT-P's table at low load** (1 % of the packets off DeFT-P's entry VL at 0.5 x Lsat; `EB_best64` 11 %
  on 3x3 and 4x4) and are within 0.3 % of DeFT_P, with one exception: `EB_best64` is 0.9 % slower than DeFT_P at 0.5 x Lsat on 3x3 and 4x4
  and 2.6 % slower at 0.8 x Lsat on 3x3. A tenth of its packets leave the table for a VL that was better up to 64 cycles earlier.
* **0.8 x Lsat.** `EB_best` -9.6 / -6.4 / -7.0 % against DeFT_P, the main row -7.1 / -7.0 / -6.8 %; `EB_best` against the main row -2.7 [-3.0,
  -2.4] / +0.7 [+0.5, +0.9] / -0.2 [-0.6, +0.2] %. `EB_down_t` is 2.4 to 2.7 % faster than DeFT_P.
* **Above saturation** (1.2 and 1.4 x Lsat of DeFT-P, in the report): every tuned row is faster than DeFT_P, by 10 to 57 %, and the main row
  pulls away from the early rows on 3x3 and 4x4. `EB_best` has 39 and 35 % more latency than the main row at 1.2 x Lsat and 47 and 18 % more
  at 1.4 x Lsat; on 2x2 +5.2 % and -3.5 %. This is where the THR difference of question 3 comes from.
* Round 27's early rows were slower than DeFT_P from 0.5 x Lsat on (+3 to +22 %; `EB_down` on 2x2 excepted) and up to 3.3 times slower at
  0.8 x Lsat.

### 7. How often does `EB_best` leave DeFT-P's entry VL, and in which scenarios?
*Final (`report/summary_C.md` C.8).* **For a quarter of the packets on 2x2 and for half of them on 3x3 and 4x4, in every scenario alike, and
nearly as often at half the saturation load. So `EB_best` is more than DeFT with a correction for hot spots: it balances the VLs under
every traffic pattern, uses DeFT-P's table as little more than a tie-break, and gains in the other five scenarios too.** Share of the
packets that move Up on a VL that is not DeFT-P's entry VL for their destination, at 1.0 x Lsat, in %:

| size | row | uniform | localized | hotspot | chipperm | chiptrans | movinghot | all six | all six at 0.5 x Lsat |
|---|---|---|---|---|---|---|---|---|---|
| 2x2 | `EB_best` | 25 | 25 | 29 | 24 | 23 | 23 | 24.6 | 19.2 |
| 2x2 | main row | 35 | 35 | 30 | 39 | 39 | 40 | 36.4 | 21.3 |
| 3x3 | `EB_best` | 51 | 51 | 49 | 50 | 48 | 48 | 49.4 | 44.2 |
| 3x3 | main row | 57 | 57 | 59 | 55 | 56 | 58 | 56.7 | 52.2 |
| 4x4 | `EB_best` | 51 | 51 | 45 | 50 | 49 | 49 | 49.4 | 43.6 |
| 4x4 | main row | 57 | 57 | 60 | 58 | 57 | 59 | 57.9 | 53.1 |

* **Hotspot traffic is not where it leaves the table most.** On 2x2 the hotspot share is the largest by 4 points; on 4x4 it is the smallest.
* **The tuned anchor is weak:** T = 8 flits on 2x2 (one packet) and T = 2 flits on 3x3 and 4x4 (a quarter of a packet). With the count the
  best member with T = 0 scores 0.021 and 0.009 less than `EB_best` (question 2), and for the S and B of `EB_best` the score is nearly flat
  in T: +0.51 to +0.55 on 2x2 and +0.45 to +0.49 on 4x4 for T from 0 to 16 (`paper_data/tuning_v28.csv`).
* **It balances the VLs better than the main row.** The busiest VL over the mean VL at 1.0 x Lsat: `EB_best` 1.28 / 1.32 / 1.40, the main row
  1.30 / 1.52 / 1.67, DeFT_P 1.33 / 1.50 / 1.77. Under hotspot traffic: 1.18 / 1.39 / 1.79 against 1.28 / 1.66 / 2.32 and 1.60 / 2.57 / 3.98.
* **Its paths are longer than the main row's on 3x3 and 4x4** (11.71 and 14.86 hops per packet at 1.0 x Lsat against 11.50 and 14.70;
  DeFT_P 11.18 and 14.26) and shorter on 2x2 (8.37 against 8.64; DeFT_P 8.27).
* **Its choice is old when it takes effect, and that no longer hurts.** The packets of `EB_best` move Up 64 / 77 / 122 cycles after their
  entry VL was bound (mean at 1.0 x Lsat). Round 27 read the failure of its injection-time rows as sources that pile onto the same VL
  before any of them sees the others arrive. With the count every later source sees the earlier choices at once, so the age of a choice
  costs little.
* **It gains in the other five scenarios:** THR +5.9 / +7.1 / +6.2 % and LAT -29.1 / -26.4 / -23.0 % against DeFT_P (the main row +4.6 /
  +12.5 / +9.6 % and -26.1 / -28.7 / -29.9 %); scenario by scenario it is ahead of DeFT_P in 34 of 36 cells and level in two (question 5).
* **The rows that know less do stay near the table:** `EB_best64` leaves it for 10 / 31 / 29 % of the packets at 1.0 x Lsat and 1 / 11 / 11 %
  at 0.5 x Lsat, `EB_down_t` for 6 / 5 / 3 % and about 1 %.
* The prompt expected `EB_best` to be DeFT-P's table with a correction for hot spots, and so did I (5 to 25 % of the packets off the table,
  under 10 % outside hotspot traffic). Both were wrong.

### 8. `EB_best64` against `EB_best`: what does old information cost a binder that is anchored?
*Final (`report/summary_C.md` C.5, C.2, C.7, C.8).* **A quarter to a half of its gain. With occupancies and counts up to 64 cycles old the
binder loses 1.9 to 2.6 % of throughput and has 15 to 22 % more latency at 1.0 x Lsat than with fresh ones; it keeps 69 to 77 % of
`EB_best`'s THR gain over DeFT_P and 51 to 66 % of its LAT gain. Nearly all of the cost is outside hotspot traffic. It never falls behind
DeFT_P over the six scenarios, which round 27's row with old information did by 10.5 to 16.5 % in THR.**

| | THR | LAT at 1.0 x Lsat | P99 |
|---|---|---|---|
| `EB_best64` against `EB_best`, all six | -2.1 [-2.4, -1.9] / -2.6 [-3.0, -2.2] / -1.9 [-2.2, -1.6] | +17.4 [+16.4, +18.3] / +22.3 [+20.9, +23.6] / +14.7 [+13.5, +15.9] | +32.7 / +41.0 / +25.2 |
| hotspot alone | +0.2 / 0.0 / +0.1 | +9.6 / +3.3 / +2.0 | |
| the other five | -2.6 / -3.1 / -2.3 | +19.0 / +26.5 / +17.4 | |
| the main row against `EB_best64`, all six | +1.2 / +7.2 / +4.9 | -11.5 / -20.6 / -19.6 | -17.6 / -31.0 / -29.8 |

* **Share of the main row's gain:** 82 / 46 / 58 % in THR and 72 / 48 / 51 % in LAT (`EB_best`: 113 / 66 / 75 % and 109 / 93 / 82 %). Under
  hotspot traffic 93 to 97 % and 94 to 95 %: the hot spot does not move, so a picture that is 64 cycles old is still right. In the other
  five scenarios 70 / 31 / 40 % and 56 / 21 / 29 %.
* **The tuning gave it a stronger anchor** (T = 32 and 16 flits instead of 8 and 2): old information is trusted less. It leaves DeFT-P's entry
  VL for 10 / 31 / 29 % of the packets at 1.0 x Lsat (`EB_best` 25 / 49 / 49 %).
* **Where the picture changes fast it gains little or nothing:** under movinghot traffic it is level with DeFT_P on 3x3 and has 8.3 % more
  latency than DeFT_P on 4x4 (question 5). Below saturation it is level with DeFT_P or up to 2.6 % slower (question 6).
* **So the anchor makes old information safe, not good.** Round 27's `EB_vl64` (no anchor, no count) was 10.5 to 16.5 % behind DeFT_P in THR.
  `EB_best64` is 5.9 to 6.8 % ahead of it in THR and 19 to 27 % in LAT, on every size.
* A period of 64 cycles is short next to what a real network could distribute to every source. `EB_best64` is still an ideal: it stands for
  what the same global knowledge is worth when it is not instantaneous.

### 9. `EB_down_t`: which `lut_bias`, and what does a commit at the Down move reach with it?
*Final (`tuning_v28.md`; `report/summary_C.md` C.1 to C.3, C.6, C.8).* **`lut_bias` 4 on every size (the frozen main row has 2 on 2x2 and 0 on
3x3 and 4x4). With it a commit at the Down move is ahead of DeFT_P on every size (THR +5.3 / +6.1 / +5.3 %, LAT -21.6 / -22.5 / -17.5 %) and
reaches 74 / 46 / 46 % of the main row's THR gain and 56 / 58 / 43 % of its LAT gain. The main row is ahead of it in all six primary tests.**
* **Round 27's `EB_down` was this row with the main row's `lut_bias`,** and it was level with DeFT_P on 2x2 and 14 and 22 % behind it in THR
  on 3x3 and 4x4. So what round 27 called its cleanest evidence measured a commit with a bias that suits a late binder and not a commit:
  with a bias of 0 (3x3, 4x4) or 2 (2x2) the commit follows the picture of the moment closely, and the main row can afford that only
  because it may change its mind at the next hop. With 4 flits of bias the commit keeps DeFT-P's entry VL for 94 to 97 % of the packets at
  1.0 x Lsat (99 % at 0.5 x Lsat) and leaves it only where the local picture is clear.
* **What that reaches:** under hotspot traffic 83 / 65 / 55 % of the main row's THR gain and 80 / 72 / 72 % of its LAT gain; in the other five
  scenarios 66 / 41 / 41 % and 37 / 50 / 29 %. Under the chiplet-to-chiplet patterns (chipperm, chiptrans) it gains nothing in THR over
  DeFT_P (chipperm on 3x3 excepted); under movinghot traffic it is ahead of the main row in THR on every size (question 5).
* **What it lacks is what the main row does after the Down move:** changing the entry VL hop by hop on the interposer. Against this row
  that is worth 1.8 / 7.1 / 6.4 % of throughput and 17.7 / 17.1 / 22.5 % of latency at 1.0 x Lsat (question 3), with the same information.
* **In the tuning** it scored +0.260 and +0.225 (the main row +0.530 and +0.648). The step is sharp: `lut_bias` 2 scores -0.24 and -0.25,
  4 scores best, 8 scores +0.20 and +0.14 and 16 is nearly DeFT_P (+0.05, +0.01), so the best value is inside the grid (`tuning_v28.md`).
* I had expected a large `lut_bias` (8 or more on 4x4) and a score near 0. It chose 4 and reaches about half of the main row's gain.

### 10. Primary family 2 (faults): how many of 24 supported, which against? The shares under faults
*Open: Part D is running (6,912 runs).*

### 11. Part E: are the reports across the VLs unnecessary under faults, by the stated margin?
*Open: Part E runs after Part D (3,072 runs).*

### 12. How much of the main row's gain needs late binding, without faults and with faults, and how sure is that?
*Open until Parts D and E are done. Without faults: see "The answer in short".*

## Compared with what I stated in advance (so far: Parts B and C)
The expectations are in `stated_in_advance.md` (commit ffe51de, before any performance result of a new row) and unchanged in
`PREREGISTRATION.md`. **I underestimated the early binder on nearly every point.** In round 27 I had overestimated the early rows without
faults; this time I expected the anchor to do the work and the count of the bound packets to add little, and it is the other way round.
The prompt's expectation (DeFT-P's table with a correction for hot spots, a share well below 100 %) is not what the runs show either; its
other branch applies: the early binder reaches the main row on 2x2, and that is reported as a result.

| what I expected | what the runs show |
|---|---|
| `EB_best` from the sub-family (route, P = 1), T between 4 and 32, B between 1 and 4 | **No.** (vl, P = 1) on both sizes: B 0.5, T 8 on 2x2 and B 1, T 2 on 4x4. The best of (route, 1) is close behind (+0.520, +0.474). |
| its tuning score positive and far below the main row's: +0.05 to +0.20 on 4x4, 0 to +0.10 on 2x2 | **No.** +0.494 on 4x4 (main row +0.648) and +0.551 on 2x2 (main row +0.530). |
| the anchor buys most: the best T > 0 at least 0.1 above the best T = 0 | **No.** +0.021 and +0.009 over the family. Only without the count does the anchor buy much (+0.80 and +0.33). |
| the pending count buys less than 0.05 in score with the anchor | **No.** It buys the most: at the chosen S, B and T the member without it scores +0.096 and -1.077 (with it +0.551 and +0.494); the best member without it scores +0.20 and +0.22. |
| `EB_best64`: T at least as large as `EB_best`'s, score within 0.05 of it | **T yes** (32 and 16 against 8 and 2). **Score no:** 0.20 and 0.15 below. |
| `EB_down_t`: `lut_bias` 8 or more on 4x4, score between -0.05 and +0.10 | **No.** 4 on both sizes, +0.260 and +0.225. |
| family 1: 12 of 12 supported, the main row 4 to 10 % ahead of `EB_best` in THR and 20 to 35 % in LAT | **No.** 10 of 12; ahead by -0.9 / +4.4 / +2.9 % in THR and -3.7 / +3.0 / +7.8 % in LAT (negative: `EB_best` ahead). |
| tests most at risk: THR against `EB_best` on 3x3 and 4x4 | **No.** Those are supported; the two against are on 2x2, where I saw no risk. |
| share of `EB_best`: 15 to 40 % (THR), 10 to 40 % (LAT) | **No.** 113 / 66 / 75 % and 109 / 93 / 82 %. |
| 70 to 100 % under hotspot traffic alone | **Yes.** 93 to 96 % (THR), 97 to 102 % (LAT). |
| 0 to 20 % in the other five scenarios | **No.** 129 / 58 / 66 % (THR), 114 / 90 / 74 % (LAT). |
| share of `EB_down_t`: 0 to 25 % | **No.** 74 / 46 / 46 % (THR), 56 / 58 / 43 % (LAT). |
| an early row level with the main row in THR only under hotspot traffic on 3x3 and 4x4; ahead nowhere | **No.** Ahead of the main row with an interval that excludes 0 in 24 cells, level in 18; under hotspot traffic on 3x3 and 4x4 `EB_best` is 1.2 and 1.1 % behind in THR. |
| `EB_best` within 1 % of DeFT_P at 0.2 and 0.5 x Lsat | **Yes on 3x3 and 4x4** (-0.3 to -0.6 %); **no on 2x2** (-1.3 and -2.9 %). |
| the main row 1.5 to 2.5 % faster than DeFT_P at 0.2 and 0.5 x Lsat | **Yes.** 1.5 to 2.8 %. |
| `EB_best` leaves DeFT-P's entry VL for 5 to 25 % of the packets, 30 to 60 % under hotspot traffic, under 10 % elsewhere | **No.** 25 / 49 / 49 %, the same in every scenario. |
| `EB_best64` against `EB_best`: THR within 1.5 %, LAT 2 to 10 % higher | **No.** THR -1.9 to -2.6 %, LAT +15 to +22 %. |
| nearly no cost of old information under hotspot traffic | **Yes.** THR 0.0 to +0.2 %, LAT +2.0 to +9.6 %. |
| Part D, Part E, the sentence at the end | *open* |

## Limits (so far: Parts B and C)
* **`EB_best` is the strongest early binder we could build, not the strongest there is.** The family has one form of cost (hops, the
  occupancy at the entry VL or on the route, the count of the bound packets, the anchor) and takes its minimum. A binder that predicts,
  that reserves, or that randomizes among candidates that are nearly as good is outside it. So the shares are lower bounds on what an
  early binder with global knowledge can reach.
* **The comparison of `EB_best` with the main row mixes time and information.** The main row binds late with local information; `EB_best`
  binds early with global, instantaneous information. No row binds late with global information, so the round does not say what binding
  late would add to the knowledge of `EB_best`. It says that the local, late choice is worth as much as the global, early one on 2x2 and
  more on 3x3 and 4x4. The comparison with equal information is `EB_down_t` against the main row.
* **`EB_best` needs what no source has:** the fill of every buffer at the entry VLs of the destination chiplet and the count of all packets
  bound to them by every source of the network, at the instant of injection, without wires. `EB_best64` relaxes the age only.
* **Tuning on two seeds and five scenarios**, four of which are also evaluation scenarios (on other seeds), for the early rows as for the
  main row in round 24. The early rows are tuned on 2x2 and 4x4; 3x3 takes the 4x4 choice, as the main row does, and it is the size with
  the smallest THR share of `EB_best` (66 %).
* **THR is a lower bound in 40 to 72 % of the cells:** the largest accepted throughput is at the last load (2.4 x Lsat) in 24 to 43 of the
  60 scenario-seed cells per size and row (`report/summary_C.md` C.9), for every row alike.
* **The early rows draw from the random stream that the routers' arbitration uses.** The anchor rows measure what that alone does: nothing
  in THR (within 0.1 %) and at most 1.6 % in LAT at 1.0 x Lsat, every interval including 0.
* **One packet length (8 flits), one buffer depth, pipe_all 2, no faults in Part C.** T and the count are in flits; other packet lengths
  were not run.
* **Why the count works is a reading.** The counters are totals over a run. That later sources see earlier choices, and so do not pile onto
  the same VL, is what the sub-family table of the tuning suggests (with the count every member scores above +0.35 whatever B and T;
  without it the members with T = 0 score -0.12 to -1.5); it is not measured directly.
