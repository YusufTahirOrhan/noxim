# Decisions v27

Choices the prompt left open. Where there was a choice, the option that does not favour our methods was taken.

## A0 / A1: regression and the new options
* **Reference.** The d641861 build (the last commit of round 26), exported with `git archive` and built in a separate tree
  (`build_ref.sh d641861`). No simulator source changed between ce6ab6a and d641861, so it has the md5 of the two earlier
  reference builds. The regression is run twice: before any change (`regression_before.md`) and with the new options in the
  binary (`regression.md`). The three comparisons are those of round 26: the previous reference build (ee0e247), `bin/noxim`
  with the options absent, and `bin/noxim` with every option given explicitly at its default. The explicit list of the second
  run is the list of round 24 plus `oracle_scope vl`, `oracle_period 0`, `entry_commit off`, `up_report 1`, `entry_stats 0`.
* **`oracle_scope route`, which buffers.** As the prompt lists them: for every hop of the XY route on the interposer, the
  input buffer of the router the hop leads to at the port it arrives through, and the Up input buffer of the chiplet router
  above the candidate. The buffer in which the head arrives at the interposer router below the exit VL is not counted: the
  exit VL is fixed by the LUT, so that buffer is the same for every candidate and cannot change the choice. The option is
  rejected unless the exit is `lut`, the entry `oracle` and `ipos_tm` XY.
* **`oracle_period P`, when the sample is taken.** At the first process of a cycle that is a multiple of P: the routers call
  the sampling function at the top of their two processes (where `fastTick` is called), and the injection-time choice calls
  it too, for a source that runs before every router of the cycle. A source does not change a router buffer in the same
  cycle (it writes a signal), so the sample is the state of the buffers at the start of the cycle whichever process comes
  first. Before the first sample the occupancies are 0 (the network is empty during reset). One sample per VL holds both
  the entry and the exit occupancy; the rows of this round use the entry only. `oracle_period 1` is not `oracle_period 0`:
  0 reads the buffers at the moment of the choice inside the cycle, 1 at the start of the cycle.
* **`entry_commit down`, details the prompt left open.**
  * It is defined for `-sel DEFT_HEUR` and rejected with another selection: the cost is the heuristic's.
  * The head is not in the interposer router below when it is forwarded Down, so the busy term of the cost is read as for a
    decision computed ahead, exactly as the main row's lookahead reads it for the same router at the same moment.
  * The penalty D is charged to a candidate that is not the default entry VL only while the default VL is a candidate
    (as `lut_bias` stops charging once the default VL is gone).
  * A candidate whose one-candidate mask offers no output in the head's virtual network is skipped; with a turn model
    that offers more than one output for one candidate the cheapest is taken. Neither happens with XY on the interposer.
  * The entry mask is only ever reduced to a subset of itself, and only at this one move.
* **`up_report 0`.** Exactly as specified: in the lookahead term of the Up output of an interposer router the occupancy part
  of every continuation is 0. Rejected with `-sel DEFT_FAST`, which has its own lookahead values.
* **`entry_stats 1` (not in the prompt).** An option that only counts, added for two of the secondary items: the share of
  packets whose entry VL is not DeFT-P's, and the age of the injection-time choice. It counts the Up moves of heads in the
  measured window, those on a VL that is not the LUT's entry VL for the destination router, and two sums of
  (cycle - generation cycle of the packet): at the Up move and at the injection. The new rows carry it. So does the main
  row in Parts B and C; it is otherwise built by `experiments_v25.row_args`, and unit check 1 (`unit_checks.md`) compares the
  main row with and without the option on 18 runs. The reuse check of Part E runs the main row without it.
* **The age of the choice, with counters only.** The prompt allows a counter and nothing more. So the age is not measured
  per packet. It is the difference of two means over the measured window: the mean time since generation at the Up move,
  minus the mean time since generation at the injection of the head (which is when the choice is made). The two means are
  not over exactly the same packets at the two ends of the window; it is an estimate.
* **`commit_check N` (not in the prompt).** A diagnostic option for the unit check of `entry_commit`: for the first N bound
  heads of the measured window it computes the costs the main row's selection gives the outputs of the same router from the
  same state. It compares sets of cheapest outputs and draws no random number, so "what the main row would choose" is
  reported as: the committed output is the one cheapest output, is one of several cheapest outputs (a tie), or is not a
  cheapest output (a difference).
* **Selection of the injection-time rows.** The definition of `EB_vl` names none, so Noxim's default applies. It is never
  asked: no hop of these rows offers more than one output (checked in every run).
* **`-deft_lut_entry dst` is not given to the `EB` rows.** Their entry VL is not from the LUT. Their exit VL is the LUT's
  `source_exit` with or without the option, as for the main row.

## A2: gates
* **Anchor.** Compared are all fields of the `summary` block except the three energy fields, and the delay statistics of the
  `deft_lb` block. The power model charges the routing function by its name, so the energy of `-routing DEFT` and of
  `-routing DEFT_LB` may differ while every packet takes the same path at the same time; the file says in how many runs
  the energy is equal too.
* **Drain tests twice for the tuned rows.** A2 comes before the tuning, so `EB_vl`, `EB_route` and `EB_vl64` are drained
  first with `oracle_beta 1` (`drain_v27.csv`) and again with their chosen values before Part C (`drain_v27_tuned.csv`).
  The choice of `oracle_beta` cannot change the relation (one candidate either way), but the rows are tested as they run.
* **The mask with the same VL faulty in every chiplet** is the mask of rounds 9 to 26 (0x1111, 0x111111111,
  0x1111111111111111).
* **"One candidate" in unit check 2:** the first mask (in hex order) of round 25 that leaves every chiplet one functional VL.

## Before the pre-registration
* **A smoke run of every new row was looked at.** To see that the options run, one run of each new row was made on 2x2 and
  on 4x4 (uniform, 1.0 x Lsat, seed 101, `oracle_beta` 0 and 1) and its numbers were read. Seed 101 is a tuning seed, not an
  evaluation seed, and these runs are not part of any design; but the expectations in the pre-registration were written
  after them, and it says so.
