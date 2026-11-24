# Decisions v29

Where the prompt (`PROMPT.md`) left a choice, the option that does not favour our methods was taken: in doubt the references and the
early rows are favoured. Each entry says what was open, what was chosen and why. Entries are in the order in which they came up.

## A0: regression before any change
* **Reference build.** `build_ref.sh e7569b1` exports the last commit of round 28 with `git archive` and builds it in a separate tree:
  `~/lbbin/noxim_e7569b1`, md5 dbeabbc7557f3db9be4105ddda8fe7a6, the same file as the `bin/noxim` that round 28 left. The regression
  compares against that build and, as every round, against the reference of the round before (b164e9e).
* **The two files that were placed in the repository** (`results_v29_review/PROMPT.md`, `formal/lb_cdg_check.py`) are committed with A0,
  unchanged.

## A1: the new options
* **`-buffer 5`, `-buffer 6` stopped the simulator before this round.** Noxim's power table (`bin/power.yaml`) has buffer depths 2, 4, 8,
  16, 32 and 64, and `Power::configureRouter` asserted that the depth is in it (`-buffer 5` with the e7569b1 build: assertion at
  `Power.cpp:88`). The table is not changed. For a depth that the table does not have, the four buffer entries (leakage, push, front, pop)
  are now interpolated linearly between the nearest tabulated depths below and above it with the same flit size (5, 6 and 7 between 4
  and 8). A depth in the table is read as before, so the 84 configurations are untouched. Only the three energy fields of the statistics
  depend on these entries; no comparison of this round uses them.
* **`-buffer_ipos N`: which buffers.** "Every input buffer of an interposer router, the one that receives from a Down VL included" is read
  as all six input ports of the router object (N, E, S, W, the Down-VL port, and the local port, which no packet uses on the interposer).
  The chiplet routers keep `-buffer` on every port, the port that receives from an Up VL included. The option is a global parameter
  (`buffer_depth_ipos` in the YAML, default 0 = as `-buffer`), valid for the DEFT_2_5D topology only.
* **Nothing in the statistics file says that `-buffer_ipos` was given.** A2 asks that `-buffer_ipos 4` with `-buffer 4` is byte-identical
  to the option absent, so the option writes no field. To check that the depths are the real ones there is a diagnostic,
  `-deft_lb buffer_stats 1` (off by default, observation only): the capacity and the largest fill of the input buffers per layer, taken at
  every flit that is written into a buffer. It is used in the gate `buffer_checks.md` and in no row.
* **Everything the selection reads follows the real depth without a change of the selection:** the occupancy term reads the neighbour's
  buffer (`Size()`), the full status and the fallback read `IsFull()` of that buffer, and both are per buffer. Nothing in the routing,
  the VN rules or the selection reads the global `-buffer` value (the one place that does, `Router::inCongestion`, belongs to the DyAD
  routing of the original Noxim and is not used here). The weights of the selection are not rescaled for deeper buffers: `LB_d6` is the
  frozen main row with `-buffer 6`, nothing retuned.
* **`entry_commit first`: when the commit is made.** The main row computes its decision for a router when the head leaves the router
  before it (lookahead routing). `first` is made at that moment, as `entry_commit down` is: when a head is forwarded to an interposer
  router at which the routing function offers it more than one output (with the entry mask it has after the move), the costs of the main
  row's selection for those outputs are computed from that router's state (lookahead term and `lut_bias` included, the busy term read as
  for a decision computed ahead), the output of least cost is selected with the selection's own tie rule (a draw from `rand()`), and the
  entry mask is reduced to one candidate among those that the selected output keeps: the one of least cost through that output (the cost
  the selection gives the output for a head with that one candidate, plus `lut_bias` if the candidate is not DeFT-P's entry VL while that
  VL is in the mask, as `entry_commit down` charges it), ties drawn as `entry_commit down` draws them. The head therefore reaches its
  commit router with one candidate and is offered one output there.
  * *What this reading leaves out:* the fallback of the main row cannot act at the commit router (a head with one candidate has no other
    output to ask for). The other reading, to keep the full mask until the head has left the commit router through whatever output the
    fallback gave it, would give the row one more late decision. The prompt says that the cost is "computed when the main row computes its
    decision for that router" and that the candidate is taken "through the selected output", and it calls the option "like `entry_commit
    down`", which has the same property; and the gate of A2 ("the committed VL is a candidate of least cost of the main row's selection
    at that router") can hold for every head only if the commit follows the selection and not the fallback. So the text decides for the
    first reading, although the second would be the more favourable one for the early row. The missing fallback at the commit router is
    named as a limit where `EB_first` is reported.
  * *"At most one hop with more than one offered output per head"* is checked with a counter per packet (the number of commits of one
    head, kept in a table of the packets in flight; its maximum must be 1) and with the hop counters of round 20 (no hop of an `EB_first`
    run may offer more than one output with the mask the head carries when it leaves a router).
  * *The anchor.* With `lut_bias 1e9` every commit takes DeFT-P's entry VL, but a commit draws twice from `rand()`, from which the routers'
    crossbar arbitration draws. As for the anchors of round 28 the gate compares the row with DeFT_P as it is and with the diagnostic
    `tie_stream 1`, for which both draws of a commit go to the stream of the tie-breaks.
* **The three traffic patterns.** `tornado` is defined on the chiplet layer as a whole (router (x, y) of the FW x FH grid, wrapping
  around in x), so a quarter of the sources of 2x2 send inside their own chiplet (x = 0 and x = 4) and none on 3x3 and 4x4. `neighbour`
  takes "adjacent in the chiplet grid" as sharing an edge (two to four chiplets); the rate of a source is spread evenly over all routers of
  those chiplets. `randperm` draws with a fresh `random.Random(2901)` per size: `shuffle` on `list(range(N))`, shuffled again with the same
  generator until no router maps to itself; the permutation is written to `randperm_<size>.txt` by the gate that checks the tables.
  The three patterns are written only when asked for with `--patterns`, as `chiptrans` is.

## A2: gates
* **Depth 5 is tested too.** The prompt names the drain tests for `-buffer 6` and `-buffer_ipos 7`; the rows `X_d5` run with `-buffer 5`, so
  the same tests are made for it (24 more drain tests).
* **Order of the drain tests on the new patterns.** They are asked for at 0.5 and 1.0 x Lsat, and Lsat of a new pattern is the result of
  B0. So the order is: the other gates, the pre-registration, B0 (DeFT_P with seed 101 only), the drain tests on the three patterns, the
  timing runs, B1. No evaluation run of a new pattern is made before its drain tests have passed.
* **The referee's script and `python3 -I`.** `lb_cdg_check.py` needs `networkx`, which this machine has only under `~/lbpkgs` (WSL has no
  pip). `-I` ignores `PYTHONPATH`. The script is therefore started as `python3 -I -c WRAP ~/lbpkgs formal/lb_cdg_check.py MODE`: the
  interpreter is isolated as asked (no environment variables, no user site, the script's folder not on the path), WRAP appends the one
  folder with `networkx` to the end of `sys.path` and runs the unchanged script with `runpy`. The script was read before it was run: it
  builds graphs and prints; it opens no file and no connection.
* **Reuse checks: which runs.** "Two scenarios per size at 1.0 x Lsat, the first two seeds of that round": round 25 uniform and
  movinghot (one scenario of the tuning, one that it did not see), seeds 121 and 122; round 26 mask 1 of the rate 4/16 with uniform
  traffic and mask 1 of the rate 1/16 with hotspot traffic, seeds 151 and 152; round 28 uniform and chiptrans, seeds 171 and 172, and
  there also the three tuned early rows that Part F is compared with (`EB_best`, `EB_best64`, `EB_down_t`), because they are reused as
  well. Every column of the earlier round's per-run file is compared as text.

## Part F: tuning runs
* **400 runs, not 800, for `EB_first`.** The prompt gives 800 runs for the grid {0, 1, 2, 4, 8}. By the rule of round 24 as rounds 27 and
  28 applied it (2x2 and 4x4, five scenarios, four loads, two seeds: 80 runs per configuration) five values are 400 runs. The rule is
  kept; DeFT-P and the main row are run again on the same cells (160 runs) and must equal the rows of round 27; the extension rule of
  `EB_down_t` in round 28 (16, 32, 64 if the best value is the largest) is taken over, which can add 40 runs per value and size.
