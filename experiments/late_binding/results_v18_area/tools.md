# v18 tools

* Yosys with bundled ABC: Yosys 0.70+286 (git sha1 63eecf3dd, Release, Clang /usr/bin/clang++ 21.1.8) (OSS CAD Suite, release 2026-11-01).
* OpenSTA: 3.1.0, built from the OpenROAD project repository, without root.
* Icarus Verilog: Icarus Verilog version 14.0 (devel) (s20260301-794-gdfc800afd-dirty).
* Library: NanGate45 Open Cell Library, typical corner, `NangateOpenCellLibrary_typical.lib`, OpenROAD-flow-scripts `flow/platforms/nangate45/lib/`, md5 afe86ccefc885369314b77cface912f6.
* Clock target: 1 GHz (`abc -D 1000`, OpenSTA clock period 1 ns).
* ABC constraints: driving cell BUF_X2, load 2 fF.
