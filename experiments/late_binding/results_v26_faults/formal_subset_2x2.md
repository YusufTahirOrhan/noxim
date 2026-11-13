# v26 A2: the second half of the argument for set 2, tested on 2x2 (experiments_v26.py a2sub)

For 1000 masks of A1 with faults in at least two chiplets (drawn with `random.Random(2611)`), both relations and each chiplet c: the reachable states of the packets with a
destination in chiplet c under the mask must be a subset of those under the mask that keeps only the faults of chiplet c. A state is the model's search node:
(phase, router, last move, candidate masks, VN, destination) and the channel it arrived on.

| relation | comparisons (mask, chiplet) | subset holds | states under the mask: mean | states under the restricted mask: mean | the two sets are equal | comparisons with faults elsewhere |
|---|---|---|---|---|---|---|
| CI_XY_XY | 4000 | 4000 | 6696 | 11629 | 0 | 4000 |
| CI_XY_O1 | 4000 | 4000 | 6698 | 11631 | 0 | 4000 |

**8000 comparisons, the subset holds in every one: yes.** Wall time 382 s with 6 processes.
