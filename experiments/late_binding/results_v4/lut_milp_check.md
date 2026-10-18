# MILP vs exact DP in the LUT generator (default 2x2 instance)

Optimisations compared: 264 (11 masks x 4 chiplets x source/destination x 3 demand profiles).
Largest |objective(DP) - objective(MILP)|: 0.000e+00.
Identical assignments: 126 of 264 (the rest are equally good alternatives).
Elapsed: 727 s.

The MILP reaches the DP optimum in every case, so it is used for problems with more than 64 demand points (destination entry on 3x3 and larger grids).
