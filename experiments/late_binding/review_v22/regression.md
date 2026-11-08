# Regression of the review binary with its options off

Same arguments, 2x2 uniform at 1.0 x Lsat, seed 1001; whole stats JSON compared byte by byte.

- DeFT_rr: byte-identical
- MTR: byte-identical
- CI_fastQL: byte-identical

## Second build (noxim_review2: decision delay counts from the end of the pipe_all wait)

Same check, 2x2 uniform at 1.0 x Lsat, seed 1001, whole stats JSON byte by byte against bin/noxim:

- DeFT_rr: byte-identical
- CI_fastQL (decision_delay 3, fast_stale 2, pipe_all 0): byte-identical
