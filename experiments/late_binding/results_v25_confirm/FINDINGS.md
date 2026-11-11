# Findings v25: confirmatory round for late binding with XY, and the hardware of the final design

Status: **in progress.** Done: Part A (gates), the pre-registration, Part F (hardware; `hw/FINDINGS_hw.md`), the model check
of the fault-sweep masks. Running: Part B (18,900 runs), the drain tests and ladders of Part C. To follow, unattended and in
the pre-registered order (`chain_v25.sh`, `chain_v25_add.sh`): the fault sweep, the application traces, the one-cycle router
model, the addendum row. No evaluation result has been read yet; the answers below that need one say so.

Nothing is tuned in this round: the configuration is the one round 24 chose on seeds 101-102, the simulator is the ce6ab6a
build, and the analysis is fixed in `PREREGISTRATION.md` (Parts B and C) and `PREREGISTRATION_addendum.md`.

## Gates
* **Regression** (`regression.md`): the 84-configuration set is byte-identical to a fresh build of ce6ab6a in all three
  comparisons (the 8d84634 build, `bin/noxim` with the options absent, `bin/noxim` with every option of rounds 23-24 given
  explicitly off). No simulator source changed in this round.
* **The rows of this round are the rows of round 24** (`reuse_check.md`): 24 of 24 evaluation runs of round 24, drawn at
  random over the four frozen rows and DeFT_P, DeFT_B, MTR and RC, are reproduced field by field with this round's driver.
* **Ladders** (`load_points_v25.md`): the three scenarios the tuning did not see (localized, movinghot, hotspot with one
  faulty VL per chiplet) got their ladders again by the D1 rule; all nine equal the ladders round 23 had made for them.
* **Drain tests of the frozen rows** (`drain_summary.csv`): 336 of 336 pass, 0 dead-end events: the four frozen rows at
  pipe_all 2 and the two late-binding rows of Part E at pipe_all 0, each with the v10 protocol and masks on the three sizes
  and with over-saturated 4x4 runs on localized and movinghot.
* **Model check of the fault-sweep masks** (`formal_faults.md`): 27 masks (k = 1, 2, 3 faulty VLs in every chiplet; all nine
  masks of every size, the 4x4 ones included), relations `CI_XY_XY` and `CI_XY_O1` with the paper's Up rule: 54 of 54 pass
  (acyclic CDG, no dead-end state, no livelock; longest path at most 24 / 32 / 40 hops).
* **Drain tests on the fault-sweep masks** (`drain_faults.csv`): 162 / 162 pass (the six rows of the sweep on each of the 27 masks,
  all-pairs burst: every packet delivered, 4,032 / 20,592 / 65,280 on 2x2 / 3x3 / 4x4, no dead-end event).
* **Run-time rule** (`runtime_estimate.md`): 26.5 h estimated for Part B with 10 processes; nothing was dropped.
* **Hardware checks** (`hw/FINDINGS_hw.md`, F2): 6.12 M, 6.21 M and 4.97 M vectors from simulator runs against the RTL of the
  three designs, 0 mismatches; every instrumented simulator run byte-identical to `bin/noxim`; 23 of 25 mutations caught (the
  two others change logic no reachable input exercises); 140 of 140 router configurations pass the router-level test.

## The ten questions

### 1. Primary family of Part B: how many supported, which against?
Pending (Part B is running).

### 2. Per scenario: where are the gains and the losses? The three scenarios not seen in tuning against the five that were?
Pending.

### 3. Against each reference row separately
Pending.

### 4. Fault sweep: the family of Part C, the trend over k, and the k = 3 check
Pending.

### 5. Q-learning against the heuristic on all eight scenarios
Pending.

### 6. DLY against LF
Pending.

### 7. Application traces
Pending.

### 8. One-cycle router model (Part E): what changes?
Pending.

### 9. Hardware: area, timing, header bits; which mechanism can be built, and what the evaluated row of that mechanism achieves
Details and tables: `hw/FINDINGS_hw.md`, `report/summary_F.md`. Flow of rounds 18 and 21 (Yosys + ABC, NanGate45, OpenSTA,
pre-layout); DeFT's router and round 18's late-binding router are synthesised again in the same run.

* **What is built.** The interposer router of the three heuristic rows: lookahead routing with the fallback (LF) for XY
  (the main row) and for the VN-split order (the second row), and the decision at the buffer front (DLY) for XY. Buffers,
  allocators and crossbar are the reference core of round 18. The chiplet router is DeFT's with the exit LUT (round 18's),
  on 2x2 with a 96-bit table of the default entry VL.
* **The lookahead needs no bit in the head and no wire between routers.** The decision unit of an input port reads the head
  on the link and its result is stored in the router (two entries per input VC). The price: the decision has two cycles
  (link and route), not the three of W = pipe_all + 1 that a request from the upstream router would give.
* **Header bits.** Two more than DeFT (the 4-bit mask of entry candidates replaces the 2-bit entry VL), four more on 2x2
  (2 bits of default entry VL for the penalty D = 2). The same for all three designs.
* **Area, relative to DeFT** (hierarchy kept / router core kept as one module / flattened; the first is the primary figure
  and an upper bound, the last favours the design):

  | design | interposer router (4x4) | under a VL | all routers of a 2x2 system | of a 4x4 system |
  |---|---|---|---|---|
  | **main row: LF, XY, one register in the decision unit** | 1.41 / 1.23 / 1.12 | 1.48 / 1.31 / 1.20 | 1.25 / 1.16 / 1.10 | 1.22 / 1.13 / 1.08 |
  | second row: LF, VN-split order | 1.66 / 1.40 / 1.32 | 1.70 / 1.46 / 1.38 | 1.38 / 1.24 / 1.20 | 1.34 / 1.21 / 1.17 |
  | DLY, XY, one unit per input port, two registers | 1.33 / 1.22 / 1.17 | 1.40 / 1.29 / 1.26 | 1.21 / 1.16 / 1.13 | 1.18 / 1.13 / 1.10 |
  | round 18: LB-I heuristic, one unit per router | 1.33 / 1.22 / 1.20 | 1.28 / 1.20 / 1.20 | 1.16 / 1.11 / 1.09 | 1.16 / 1.11 / 1.11 |
  | round 18: LB-I heuristic, one unit per input port | 2.44 / 1.68 / 1.70 | 2.46 / 1.75 / 1.76 | 1.74 / 1.32 / 1.33 | 1.71 / 1.35 / 1.36 |

  Chiplet router 1.01-1.02 x DeFT's on 3x3 and 4x4, 1.05-1.06 x on 2x2. In absolute terms (hierarchy kept) all routers of a
  2x2 system take 2.35 mm^2 with DeFT and 2.94 mm^2 with the main row; of a 4x4 system 9.54 and 11.63 mm^2. The VN-split
  order costs a decision unit on every link port instead of on E, W and the Down link only.
* **Timing.** No router of this flow meets 1 ns; the reference pipeline's period is 1.27-1.32 ns (T_ref, DeFT's switch
  allocation). The main row's decision takes **two cycles at T_ref** (one register, margin +0.23 ns; VN-split order
  +0.18 ns) and three at 1 ns (margin +0.07 ns, inside the 0.13 ns spread of the flow). A hop with one offered output keeps
  the four cycles of the reference pipeline; its route stage is shorter than DeFT's (0.66-0.73 ns against 0.86-0.97 ns); the
  fallback sits in the VC-allocation stage (1.08-1.20 ns against DeFT's 1.20-1.26 ns). The longest stage of the main row's
  router is 0.90-0.96 x T_ref: the design does not lengthen the clock.
* **Which mechanism can be built.** **LF with residual delay 0, at the period of the reference pipeline**: every head takes
  four cycles per hop in RTL simulation, so `CI_heurLA_X_LF` as evaluated in Part B is the mechanism that is built, and
  `CI_heurLA_O_LF` likewise. Two conditions: the first decision stage reads the head on the link and leaves 0.28-0.42 ns of
  the link cycle to the wire (DeFT's router leaves 0.82-0.90 ns), and the clock is the reference's, not 1 ns. If either
  fails, the same RTL has one residual cycle for heads with a choice. That row (`CI_heurLA_X_LF1`) was not among the
  evaluated ones and is run as a pre-registered addendum.
* **DLY** fits the reference period only with one unit per input port and without margin (+0.00 ns with one register,
  +0.06 ns with the two of the evaluated row); with one unit per router it does not fit (0.28 ns over).
* **What the evaluated rows of the mechanism achieve:** pending (Part B for residual 0, the addendum for residual 1).

### 10. Low-load latency and the accepted throughput beyond the peak: as in v24?
Pending.
