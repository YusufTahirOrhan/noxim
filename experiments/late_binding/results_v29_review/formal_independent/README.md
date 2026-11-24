# A2: the referee's independent check (experiments_v29.py a2_formal)

`formal/lb_cdg_check.py` is the independent referee's re-implementation of the routing function, the VN rules and the channel dependency graph. It was placed
in the repository for this round and is not edited (sha256 662dfadf5a1ce1744722442e1fcdf7a2929dc37425dd5df43263253b5e8ed92f; `git status` of the file when this was written: clean, as committed).
Each mode is run with `python3 -I` (isolated: no environment variables, no user site, the script's folder not on the path). The script needs `networkx`,
which this machine has only under `~/lbpkgs`; so the interpreter is started as `python3 -I -c WRAP ~/lbpkgs formal/lb_cdg_check.py MODE`, where WRAP
appends that one folder to the end of `sys.path` and runs the script unchanged with `runpy` (`experiments_v29_gates.FORMAL_WRAP`). The outputs are
`main.txt`, `turnmodels.txt`, `rules.txt` and `placements.txt` in this folder, as printed.

| mode | exit code | seconds | configurations |
|---|---|---|---|
| main | 0 | 4 | 6 |
| turnmodels | 0 | 7 | 5 |
| rules | 0 | 0 | 3 |
| placements | 0 | 5 | 12 |

## What the prompt asks the check to report

* **`main`: no dead end, no path longer than d0, an acyclic CDG for XY and for the VN-split order on 4, 9 and 16 chiplets: yes.**

  | configuration | dead ends | paths > d0 | exits outside M0 | dependencies to a lower class | CDG acyclic |
  |---|---|---|---|---|---|
  | 2x2 chiplets, T(VN0)=XY, T(VN1)=XY, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |
  | 3x3 chiplets, T(VN0)=XY, T(VN1)=XY, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |
  | 4x4 chiplets, T(VN0)=XY, T(VN1)=XY, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |
  | 2x2 chiplets, T(VN0)=XY, T(VN1)=YX, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |
  | 3x3 chiplets, T(VN0)=XY, T(VN1)=YX, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |
  | 4x4 chiplets, T(VN0)=XY, T(VN1)=YX, variant=LB, (iii)=on | 0 | 0 | 0 | 0 | True |

* **`rules`: a cycle when R2, R3 or R1 is dropped: yes.**

  | configuration | dead ends | paths > d0 | dependencies to a lower class | CDG acyclic |
  |---|---|---|---|---|
  | 2x2 chiplets, T(VN0)=XY, T(VN1)=XY, variant=noR2, (iii)=on | 0 | 0 | 48 | False |
  | 2x2 chiplets, T(VN0)=XY, T(VN1)=XY, variant=noR3, (iii)=on | 0 | 0 | 48 | False |
  | 2x2 chiplets, T(VN0)=XY, T(VN1)=XY, variant=noR1, (iii)=on | 0 | 0 | 64 | False |

## The two other modes (stored; the prompt names no requirement for them)

| mode | configuration | dead ends | paths > d0 | CDG acyclic |
|---|---|---|---|---|
| turnmodels | 3x3 chiplets, T(VN0)=OE, T(VN1)=OE, variant=LB, (iii)=on | 0 | 0 | True |
| turnmodels | 3x3 chiplets, T(VN0)=WF, T(VN1)=WF, variant=LB, (iii)=on | 0 | 0 | True |
| turnmodels | 3x3 chiplets, T(VN0)=NL, T(VN1)=NL, variant=LB, (iii)=on | 0 | 0 | True |
| turnmodels | 3x3 chiplets, T(VN0)=OE, T(VN1)=OE, variant=LB, (iii)=off | 17154 | 0 | True |
| turnmodels | 3x3 chiplets, T(VN0)=WF, T(VN1)=NL, variant=LB, (iii)=on | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #0, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #0, XY/YX | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #1, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #1, XY/YX | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #2, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #2, XY/YX | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #3, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #3, XY/YX | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #4, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #4, XY/YX | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #5, XY/XY | 0 | 0 | True |
| placements | 3x3 chiplets, random VL placement per chiplet #5, XY/YX | 0 | 0 | True |

**The check reports what the prompt asks: yes.**
