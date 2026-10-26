# Decisions taken without the author (v11, Part C)

1. **Masks:** k faulty VLs drawn uniformly per chiplet (k of its 4 slots), independently for every chiplet, with
   `random.Random(3110)`; duplicates rejected; recorded in `masks.json` before any run.
2. **LUTs:** one file per mask with DeFT's rho* uniform model (`luts/v11/`, regenerable, not in git), passed to every
   method of the run. CI uses it for its exit, DeFT_OE_G for its pair, and DeFT for routing.
3. **Load points:** the fault-free v5 load points of uniform and hotspot. With faults the networks saturate earlier;
   LAT is taken at the 4th load as measured, and saturated cells are flagged.
4. **Unit of the test:** a (mask, seed) pair, averaged over the two patterns (10 units, 9 df). Masks and seeds are the
   independent replications; patterns are averaged as in v5-v10.
5. **Safety:** every method was drain-tested on every mask used (all-pairs burst, seed 1): 360 / 360 PASS. MTR and RC
   are excluded, as pre-registered.
6. **Binary:** md5 01c7e9d0 (Netrace mode present, off). Regression against the Part B binary: 84 / 84 identical
   (`regression.md`: the 66-configuration set + the six v10 baselines on every size).
7. **Figure:** k = 1-3 only; the fault-free points (k = 0) are on other seeds (v9/v10) and are not mixed in.
