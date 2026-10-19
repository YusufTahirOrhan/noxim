# DeFT LUT objective vs system size (uniform LUT, rho = 0.01, fault-free)

Objective of every LUT optimisation: rho * sum(distance) + sum_v |load_v - mean| / mean (deft_vl_lut_generator.py).
The balance term is normalised by the mean load and is at most about 2 regardless of the number of demand
points n, while the distance term grows linearly with n. So the larger the problem, the less balance is
worth against distance.

| size | exit problem: points | exit: distance term | exit: balance term | exit: mean hops | entry problem: points | entry: distance term | entry: balance term | entry: mean hops | analytic VL imbalance (max/mean) | CV |
|---|---|---|---|---|---|---|---|---|---|---|
| 2x2 | 16 | 0.120 | 0.000 | 0.75 | 48 | 2.560 | 0.000 | 5.33 | 1.000 | 0.000 |
| 3x3 | 16 | 0.120 | 0.000 | 0.75 | 128 | 9.653 | 0.000 | 7.54 | 1.000 | 0.000 |
| 4x4 | 16 | 0.120 | 0.000 | 0.75 | 240 | 23.360 | 0.600 | 9.73 | 1.400 | 0.158 |

Terms are means over the chiplets of a size (one exit and one entry problem per chiplet). The distance
term is rho times the total Manhattan distance (in hops) of the problem's points to their VLs. The analytic
imbalance uses the uniform traffic table: each VL carries the down traffic of the sources whose exit it
is plus the up traffic of the flows whose entry it is.

Measured in v4 (DEFT_LB proxy with the uniform-pattern LUT, uniform traffic, ~1.0 x Lsat, fault-free):
VL imbalance 1.07 (2x2, v2), 1.06 (3x3), 1.43 (4x4). The entry problem grows from 48 points (2x2) to 240
(4x4), while its balance term stays bounded.

## Reading
* **On 2x2 and 3x3 the rho = 0.01 LUT is perfectly balanced** (balance term 0 in every problem, analytic
  imbalance 1.00). The measured 1.06-1.07 is the stochastic spread of the traffic around a balanced
  assignment.
* **On 4x4 the entry problems give up balance for distance.** With 240 points the distance term
  (23.4) dwarfs the attainable balance gain, so the optimum accepts a balance term of 0.60 per
  problem. The resulting analytic imbalance, 1.40, matches the measured 1.43. The LUT itself explains
  the 4x4 imbalance of DeFT_tm seen in v4.
* **The exit problems** (16 points per chiplet at every size) are balanced and short (0.75 hops) at
  all sizes.
* This supports the hypothesis that rho = 0.01, which was never tuned, handicaps DeFT on 4x4. Step 2
  tunes rho per size.
