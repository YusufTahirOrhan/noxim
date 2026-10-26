# Decisions taken without the author (v12, Part D)

1. **Power model:** Noxim's own model with its default `bin/power.yaml`. It works on DEFT_2_5D: the model is loaded on
   every run, and enabling `-power` explicitly leaves the summary block identical (9 / 9 runs: latency, throughput,
   energy).
   - VL hops are charged as router-to-hub links: bit-line energy of the configured r2h link length, dynamic per flit
     and leakage per cycle.
   - Every router is charged leakage for its buffers and links every cycle, whether a link exists or not.
2. **Not modelled:**
   - the RC buffer (4 x 8 x 32 bits per boundary router; it favours RC);
   - Q tables, lookahead and feedback wires (they favour our learners);
   - LUTs and MTR tables.

   The analytical cost table (`report/cost_table.md`) gives their size instead.
3. **Interval:** warm-up 0 for the energy runs, so that energy (accumulated from the end of reset) and delivered flits
   cover the same 10000 cycles. The latencies of these runs include the cold start; they are not used as latency
   results.
4. **Per delivered flit:** dynamic, static and total energy divided by the flits delivered in the run, mean over seeds
   41-43, uniform fault-free, 0.5 and 1.0 x Lsat, all methods of Part B, all sizes (180 runs).
5. **Cost table assumptions** (`cost_v12.py`):
   - 16-bit learned values (the simulator uses float32);
   - 4-bit occupancy fields (2 VCs x 4 flits);
   - header bits beyond the source and destination ids;
   - one fault scenario held in the DeFT LUT;
   - MTR's NI table sized as in the MTR paper (destination id -> boundary router).
