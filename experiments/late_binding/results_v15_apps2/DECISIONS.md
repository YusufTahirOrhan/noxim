# Decisions taken without the author (v15, Part G)

1. **Overlay on all 64 nodes:** each application keeps all 64 nodes, unlike DeFT's 32 cores per application. Netrace
   traces cannot be split onto 32 nodes, because each trace's caches and directories are spread over all 64 nodes.
   Details are in `APPS2_DESIGN.md`.
2. **All 10 Part B methods:** the task says "all 9"; Part B has 10, and all 10 are run.
3. **Compression:** the 8-cycle post-dependency delay (Netrace `L2_LATENCY`) is kept in simulation cycles, not
   compressed. This is the conservative reading: it keeps the dependency chain as strict as possible.
4. **Primary latency metric:** Noxim's global mean and p99 over all delivered packets, as in v13.
   - The per-application latencies are measured at each packet's tail arrival. They are reported as extra columns
     only.
5. **Regression:** compared the whole stats JSON file byte by byte (84 / 84 identical; `regression.md`). This is
   stricter than v10/v11, which compared the `summary` and `deft_lb` blocks.
   - The new binary contains the v16 code as well (one build for G and H), so this regression also covers
     `ql_bits 0`.
6. **v13 check:** first run with the development build of the G code, then repeated with the final `bin/noxim`. Both
   gave 9 / 9 identical.
7. **s rule:** the timing test estimated 3.3 h for s = 1 and 2.4 h for s = 2, 5.8 h in total, which is within 8 h.
   Both s = 1 and s = 2 are run (`runtime_estimate.md`, `compress_choice.json`).
8. **Overlapping run:** the v16 reuse check (20 short runs, 3 processes) ran while this evaluation was running.
   - The simulator is deterministic, so this affects wall-clock time only.
