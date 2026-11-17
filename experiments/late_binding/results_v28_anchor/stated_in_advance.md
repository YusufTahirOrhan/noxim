## Stated in advance
Written on 17 Nov 2026 at about 03:35, before any run of a new row whose performance I looked at: the smoke runs of A1 (`DECISIONS.md`) were
read for identity with DeFT_P and for the pending check only, and the description run of the unit checks (check 4) had not run yet.

**The prompt's expectation**, quoted from the task of this round: `EB_best` will be DeFT-P's table with a correction for hot spots. It gets
most of the main row's gain under hotspot traffic and little in the other five scenarios, so a positive share without faults that is well
below 100 %, and a larger share under faults. If it reaches the main row, that is a result and is reported as such.

**Mine:**
* **Tuning (B1).** `EB_best` comes from the sub-family (route, P = 1) on both sizes, with a finite T between 4 and 32 and B between 1 and
  4. Its score is positive and far below the main row's: about +0.05 to +0.20 on 4x4 (main row +0.65) and 0 to +0.10 on 2x2 (main row
  +0.53). On 2x2 a best score below 0 would not surprise me. **The anchor buys most of the distance to round 27** (round 27's members with
  T = 0 scored -0.1 to -1.3, so the best T > 0 should be at least 0.1 above the best T = 0 on each size). **The pending count buys less**:
  with the anchor, P = 1 against P = 0 should differ by less than 0.05 in score at the chosen S, B and T, more for S = vl than for S =
  route, and more at small T than at large T.
* **B2.** `EB_best64` chooses a T at least as large as `EB_best`'s (old information should count less) and scores within 0.05 of it.
* **B3.** `EB_down_t` chooses a large `lut_bias` (8 or more on 4x4) and scores near 0 (between -0.05 and +0.10): the commit at the Down
  move knows less than the oracle.
* **Part C, family 1: 12 of 12 supported**; the main row is ahead of `EB_best` by 4 to 10 % in THR and 20 to 35 % in LAT at 1.0 x Lsat on
  every size. The tests most at risk: THR against `EB_best` on 3x3 and 4x4, where the hotspot share is largest.
* **Share of the main row's gain without faults:** `EB_best` 15 to 40 % in THR and 10 to 40 % in LAT over the six scenarios; 70 to 100 %
  under hotspot traffic alone; 0 to 20 % in the other five together (it should no longer be negative there: the anchor keeps it near
  DeFT-P's table). `EB_down_t` 0 to 25 %.
* **Per scenario:** an early row is level with the main row in THR only under hotspot traffic on 3x3 and 4x4, as in round 27; ahead of it
  nowhere with an interval that excludes 0.
* **Below saturation:** `EB_best` within 1 % of DeFT_P at 0.2 and 0.5 x Lsat (at low load the anchor keeps DeFT-P's entry VL); the main row
  1.5 to 2.5 % faster than DeFT_P there, as in rounds 25 and 27.
* **How often `EB_best` leaves DeFT-P's entry VL:** 5 to 25 % of the packets at 1.0 x Lsat over the six scenarios, most under hotspot
  traffic (30 to 60 %) and under 10 % in the other five. So it is DeFT with a correction for hot spots, not more.
* **`EB_best64` against `EB_best`:** THR within 1.5 %, LAT at 1.0 x Lsat 2 to 10 % higher; under hotspot traffic nearly no cost (the hot
  spot does not move).
* **Part D, family 2: 20 to 23 of 24 supported, none against.** At the rate 1/16 every test supported. At 4/16 the THR tests against
  `EB_best` on 3x3 and 4x4 are at risk of not being significant (round 27's `EB_route` was within 1.1 and 0.5 % of the main row there,
  and `EB_best` is at least as strong); the LAT tests should be supported. `EB_down_t` behind the main row in every test. Shares of the
  main row's THR gain under faults: `EB_best` 60 to 100 % at 4/16 and 30 to 70 % at 1/16; larger under hotspot than under uniform traffic.
* **Part E:** the reports across the VLs are unnecessary by the stated margin at every size and rate; if a cell misses the margin, it is
  8/16 on 2x2 (few masks with a free choice, wide intervals), and the loss sits in masks with a chiplet that is left one functional VL.
* **In one sentence:** without faults an early binder with ideal information and an anchor at DeFT gets the hotspot part of the gain and
  little else, so most of the gain still needs late binding; under faults it gets most of the throughput gain and part of the latency gain.
