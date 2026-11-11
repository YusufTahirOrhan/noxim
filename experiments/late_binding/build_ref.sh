#!/bin/bash
# Reference build of a commit: build_ref.sh COMMIT
# The commit is exported with `git archive` into ~/lbref/COMMIT (sources and bin/Makefile only), bin/libs is linked to the
# repository's libraries, and the binary is built with the repository's Makefile into a fresh object directory.
# Result: ~/lbbin/noxim_COMMIT. Builds are deterministic, so the md5 identifies the code.
set -eu
c=$1
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
ref=~/lbref/$c
rm -rf "$ref"
mkdir -p "$ref" ~/lbbin
(cd "$repo" && git archive "$c" src bin/Makefile bin/Makefile.deps) | tar -x -C "$ref"
ln -s "$repo/bin/libs" "$ref/bin/libs"
make -C "$ref/bin" -j"${2:-12}" MODULE="noxim_$c" > "$ref/build.log" 2>&1
cp "$ref/bin/noxim_$c" ~/lbbin/"noxim_$c"
md5sum ~/lbbin/"noxim_$c" "$repo/bin/noxim"
