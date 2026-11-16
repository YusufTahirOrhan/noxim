# Findings v27: early against late binding

Status: **in progress.** Done: the regression before and after the code change, the anchor row, the unit checks of the new
options, the drain tests of the new rows; the pre-registration is committed. Not started: the tuning (Part B), the
evaluation (Part C), the fault runs (Part E). Every answer below says whether it is final.

**The question of the round.** Every reference of rounds 23 to 26 chooses the entry VL without looking at the network. So
those rounds cannot say how much of the main row's gain over DeFT comes from binding the entry VL late, on the interposer,
and how much from choosing it by congestion at all. This round adds rows that choose by congestion but bind early: at
injection (`EB_vl`, `EB_route`, `EB_vl64`) or at the Down move (`EB_down`); and the main row without the occupancy reports
across the VLs (`LB_noVLrep`). Nothing of the frozen configuration is retuned and no existing row is changed.

## Safety of the new rows (A3)
**No new proof and no new model check are needed, and after reading the code path I agree with that.** Each new row either
restricts the checked relation or leaves it unchanged.
* **`EB_vl`, `EB_route`, `EB_vl64`.** `chooseMasks` gives the head one exit VL (the LUT's, a functional VL of the source
  chiplet) and one entry VL chosen among the functional VLs of the destination chiplet. With one-candidate masks and XY in
  both layers the relation is the fixed-pair relation `A_fixed_XY` of the formal model, which explores every functional
  (exit, entry) pair: it is the relation of DeFT with any injection-time choice. The three options change which functional
  entry VL is chosen (`oracle_beta`, `oracle_scope`, `oracle_period` only enter the cost), never the set it is chosen from.
* **`EB_down`.** Until the Down move the head is a head of the main row. The entry mask is not read in the source chiplet:
  the moves there depend on the exit mask, and the virtual network is assigned from the exit mask alone
  (`assignSourceVirtualNetwork`, `sourceCanUseEitherVirtualNetwork`). At the Down move the mask is replaced by one of its
  own members (`commitEntry` only ever writes `bit(v)` for a candidate v of the mask), and the stored lookahead decision is
  computed for the reduced mask. From there the head is a fixed-pair head with that entry VL. So every path of `EB_down` is
  a path of `A_fixed_XY`. It is also a path of the main row's relation `CI_XY_XY`: with fewer candidates a head is offered
  a subset of the moves it is offered with more (the monotonicity that round 26 tested on every mask of 2x2), and the one
  remaining candidate is reachable by XY from every interposer router.
* **`LB_noVLrep`.** The relation is the main row's, unchanged. The option changes one term of the cost by which the
  selection orders the offered outputs; the offered outputs are the same.
* What was checked by simulation: no hop of an `EB` run offers more than one output (every run of the unit checks; this is
  checked again in every run of Parts B, C and E), and the drain tests below.

## The thirteen questions

### 1. Regression and gates: all pass? Is the anchor row identical to DeFT_P?
*Final for the gates before the tuning; the drain tests of the tuned rows with their chosen values follow after Part B.*
**All pass, and the anchor row is identical to DeFT_P.**
* **Regression** (`regression_before.md`, `regression.md`): 84 / 84 byte-identical to the d641861 build before the change,
  and after it with the options absent and with every option given at its default.
* **Anchor** (`anchor.md`): **identical.** DEFT_LB with both VLs from the LUT, XY in both layers and DeFT-P's options gives
  DeFT_P's results in 18 of 18 runs (six fault-free scenarios, three sizes, 1.0 x Lsat, seed 101): every performance field
  of the summary, the delay statistics and the packets per VL. Only the energy fields differ, because the power model
  charges the routing function by its name.
* **Unit checks** (`unit_checks.md`): all pass. `entry_stats` changes no statistic of the main row (18 / 18 runs
  identical). `entry_commit down` changes nothing when every chiplet has one functional VL (3 / 3 runs identical). Where
  D = 0 (3x3, 4x4) the output of the committed candidate is a cheapest output of the main row's selection at the same
  router and moment in 12,000 of 12,000 sampled heads (554 of them ties, where the two may break the tie differently); on
  2x2, where D = 2 is charged to a different thing, in 5,977 of 6,000.
* **Drain tests** (`drain_v27.csv`): the five new rows on six masks per size (fault-free, the same VL faulty in every
  chiplet, mask 1 of each of the four fault rates of round 26): **90 / 90 pass**, every packet delivered, the network
  empties, no dead-end event.
* **The binding is early:** no hop of an `EB` run offers more than one output, in every run so far (unit checks and drain
  tests).
* **`EB_vl` with `oracle_beta 0`** (description): the entry VL of fewest hops is DeFT-P's entry VL for 51 to 53 % of the
  packets in five of the six scenarios and for 41 to 46 % under hotspot traffic. So "nearest" and DeFT-P's LUT agree for
  about half of the packets.

### 2. The tuned `oracle_beta` of `EB_vl`, `EB_route` and `EB_vl64`, and their scores next to the main row's
*Pending.*

### 3. Primary family: how many of 18 supported, which against?
*Pending.*

### 4. Which share of the main row's gain over DeFT_P does each early row reach, in THR and in LAT, per size?
*Pending.*

### 5. Which of `EB_vl` and `EB_route` is better, and where?
*Pending.*

### 6. Per scenario: where is an early row level with or ahead of the main row?
*Pending.*

### 7. Latency below saturation (0.2, 0.5, 0.8 x Lsat): all rows
*Pending.*

### 8. `EB_vl64` against `EB_vl`: what does the age of the information cost?
*Pending.*

### 9. Why do the injection-time rows lose or win: balance over the entry VLs, path length, age of the choice
*Pending.*

### 10. `EB_down`: is it different from DeFT_P?
*Pending.*

### 11. `LB_noVLrep`: what do the reports across the VLs buy?
*Pending.*

### 12. Part D: the table, and whether it agrees with the numbers above
*Pending.*

### 13. Part E: do the early rows behave differently under faults?
*Pending.*
