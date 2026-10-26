# v12 findings: energy (Part D)

Tables: `report/energy.md` (energy per delivered flit), `report/cost_table.md` (storage and wires). Figure:
`report/energy.{png,pdf}`. Per-run data: `energy_runs.csv` (180 runs). Decisions: `DECISIONS.md`.

## 1. Simulated energy (Noxim's power model; uniform, fault-free)
* **The model works on DEFT_2_5D, VLs included,** and enabling it leaves the statistics unchanged (9 / 9 identical runs).
* **Static energy dominates.** With the default technology parameters, leakage is about 95 % of the energy per
  delivered flit (for example 2x2 at 1.0 x Lsat: 540.6 of 573.4 pJ for DeFT(rho*)). It is charged per router and cycle,
  independent of the method. So **total energy per delivered flit is within 1 % of DeFT(rho*) for all methods that
  deliver the offered load**: MTR, RC, DeFT-Dis, DeFT_OE_G and our three variants, on all sizes and both loads.
* **Dynamic energy per delivered flit, against DeFT(rho*):**

  | method | 0.5 x Lsat | 1.0 x Lsat | note |
  |---|---|---|---|
  | our variants | -4.9 % to -9.7 % | -0.4 % to -3.2 % | |
  | MTR | -1 % to -4 % | -1 % to -4 % | |
  | RC | -3.5 % to -7 % | -3.5 % to -7 % | without its RC buffer |
  | DeFT-Dis | -4 % to -7 % | -4 % to -7 % | |
  | XY-SP | -5 % to -13 % | -5 % to -13 % | shortest pairs |
  | DeFT-Ran | +16 % to +24 % | +16 % to +24 % | longer paths |
* **Methods that saturate pay in static energy per flit.** At 1.0 x Lsat XY-SP (+40 % to +50 % total per flit) and
  DeFT-Ran on 2x2/3x3 (+14 % to +22 %) deliver fewer flits in the same time, so each flit carries more leakage.

## 2. Storage and wire cost (analytical; `report/cost_table.md`)
* **Header:** DeFT, MTR and RC carry 4 bits of routing information (exit and entry slot); CI 6 bits (exit slot + 4-bit
  entry mask); FULL 8 bits (two 4-bit masks).
* **Tables per chiplet router:**

  | method | 2x2 | 3x3 | 4x4 | note |
  |---|---|---|---|---|
  | DeFT LUT | 12 bits | 32 bits | 60 bits | |
  | CI | 6 bits | 16 bits | 30 bits | exit part only |
  | FULL | none | none | none | |
  | MTR NI table (paper's design) | 128 bits | 288 bits | 512 bits | plus 2 bits for the exit |
* **RC:** a 1024-bit RC buffer per boundary router (4 packets x 8 flits x 32 bits), 48 OPIC wires per chiplet, and
  counters.
* **Our learners:**
  - a Q table of C x 5 x 16 bits per router with an adaptive choice (2x2 320, 3x3 720, 4x4 1280 bits; CI only on the
    interposer);
  - 20 lookahead occupancy wires and 16 feedback wires per link direction.

  For scale, a baseline router has 1536 bits of input buffers and 6 credit wires per link direction. The learners' state
  is the largest added cost: on 4x4 the Q table is about 83 % of a router's input-buffer bits.
* **Not reflected in the simulated energy:** the RC buffer, the Q tables and the lookahead/feedback wires.

## Bottom line
* **Energy:** under Noxim's default power model, energy per delivered flit is dominated by leakage and is the same within
  1 % for every method that sustains the load. Late binding uses 1-10 % less dynamic energy per flit than DeFT(rho*).
  Methods that saturate (XY-SP, DeFT-Ran) cost up to 50 % more per flit.
* **Hardware:** the cost of late binding lies in storage (Q tables) and wires (lookahead / feedback), not in energy per
  flit. It is quantified analytically in the cost table.
