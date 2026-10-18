# Decisions taken without the author (v4: parametric topology and larger systems)

## Step 1: parametrisation (C++)
1. **The topology constants became run-time `int` variables with the same names**
   (DeftTopology::ChipletGridWidth, ..., VerticalLinkCount, LayoutHeight), set together by
   `DeftTopology::configure()`. Existing uses keep compiling and read the current values.
   `VerticalLinksPerChiplet` stays a compile-time 4 (as instructed), and `MaxVerticalLinkCount`
   is 64.
2. **Configuration order:** YAML (`deft_chiplets_x`, `deft_chiplets_y`, `deft_chiplet_w`,
   `deft_chiplet_h`; defaults 2, 2, 4, 4), then the command line (`-deft_chiplets_x`, ...),
   then `configure()`. It runs before `checkConfiguration()` and sets mesh_dim_x/y and
   n_delta_tiles from the footprint.
3. **Supported sizes:** at least 2 chiplets, chiplets of at least 3x3 routers, at most 64 VLs
   (16 chiplets). The slot positions are N=(1,0), E=(w-1,1), S=(w-2,h-1), W=(0,h-2), which is the
   fixed layout for 4x4 chiplets. They are distinct for every w, h >= 3.
4. **DeftLateBinding.cpp:** the namespace-scope copies (W, H, NVL, NROUTERS, NCHIP_ROUTERS)
   became `const int &` references to the topology variables. A copy would have been
   initialised with the default values at static-initialisation time. The router registry,
   the VL counters and the reach cache became vectors sized on first use (the reach cache
   is a pure memo). The Q table was already sized at run time.
5. **VL masks are uint64_t** (Packet, RouteData, Flit, DeftLateBinding through the `VlMask`
   alias, DeftVirtualNetwork, the LUT fault masks). `Flit::operator==` does not compare
   the masks, so signal-event behaviour is unaffected.
6. **Fault-mask ids** are "0x" plus ceil(VLs / 4) hex digits: 0x0000 for 16 VLs (as
   before), 9 digits for 36 VLs, 16 digits for 64 VLs. The LUT parser requires exactly this
   width.
7. **The JSON `config` block gains `deft_size`** for DEFT_2_5D runs. The `summary` and `deft_lb`
   blocks are unchanged, which is what the step-2 regression compares.
8. **No routing or selection logic was changed.** The only edits in DeftLateBinding.cpp are
   types, array sizing and the references of item 4.
