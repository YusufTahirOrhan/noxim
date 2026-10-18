#!/usr/bin/env python3
"""
Generate deterministic DeFT offline Vertical Link lookup tables.

The output follows the project schema `deft_vl_lut.v1`. This generator is
standalone by design: it mirrors the current DEFT_2_5D topology constants and
does not load, link, or modify the Noxim simulator runtime.

By default every inter-chiplet source/destination pair carries one unit of
demand. With --demand-table, the demand is read from a Noxim traffic table
(time-averaged over each line's on/off period) and weights the load-imbalance
terms of the cost; the distance term is unchanged. Equal weights reproduce the
default LUT exactly.

The instance size is parametric (--chiplets-x/--chiplets-y/--chiplet-w/--chiplet-h,
defaults 2, 2, 4, 4 as the Noxim DEFT_2_5D parameters); slot positions follow the
chiplet size as in src/DeftTopology.cpp. Optimisations with at most DP_MAX_POINTS
demand points use the exact dynamic programme below (every source-exit problem and
every problem of the default 2x2 instance, whose output is unchanged); larger ones
(destination entry on 3x3 and larger grids) are solved exactly as a mixed-integer
programme of the same objective (scipy.optimize.milp / HiGHS). Ties between equally
good assignments may then be broken differently than the DP would.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


TOPOLOGY = "DEFT_2_5D"
GENERATOR_NAME = "deft_vl_lut_generator.py"
GENERATOR_VERSION = "1"
SCHEMA = "deft_vl_lut.v1"
DEFAULT_RHO = "0.01"
DEFAULT_TRAFFIC_PROFILE_ID = "uniform-interchiplet-v1"

CHIPLET_GRID_WIDTH = 2
CHIPLET_GRID_HEIGHT = 2
CHIPLET_COUNT = CHIPLET_GRID_WIDTH * CHIPLET_GRID_HEIGHT
CHIPLET_LOCAL_WIDTH = 4
CHIPLET_LOCAL_HEIGHT = 4
FOOTPRINT_WIDTH = CHIPLET_GRID_WIDTH * CHIPLET_LOCAL_WIDTH
FOOTPRINT_HEIGHT = CHIPLET_GRID_HEIGHT * CHIPLET_LOCAL_HEIGHT
CHIPLET_ROUTER_COUNT = FOOTPRINT_WIDTH * FOOTPRINT_HEIGHT
INTERPOSER_ROUTER_COUNT = FOOTPRINT_WIDTH * FOOTPRINT_HEIGHT
VERTICAL_LINKS_PER_CHIPLET = 4
VERTICAL_LINK_COUNT = CHIPLET_COUNT * VERTICAL_LINKS_PER_CHIPLET
MAX_CONNECTED_FAULT_COUNT = VERTICAL_LINK_COUNT - CHIPLET_COUNT

SLOT_NAMES = ("NORTH", "EAST", "SOUTH", "WEST")
SLOT_LOCAL_X = (1, 3, 2, 0)
SLOT_LOCAL_Y = (0, 1, 3, 2)
DP_MAX_POINTS = 64


@dataclass(frozen=True)
class VerticalLink:
    vl_id: int
    owner_chiplet_id: int
    slot: str
    chiplet_endpoint_router_id: int
    interposer_endpoint_router_id: int
    footprint_x: int
    footprint_y: int


@dataclass(frozen=True)
class DemandPoint:
    key: Tuple[int, ...]
    footprint_x: int
    footprint_y: int


@dataclass(frozen=True)
class OptimizationResult:
    selected_by_key: Dict[Tuple[int, ...], int]
    demand_by_key: Dict[Tuple[int, ...], DemandPoint]
    candidate_vls: Tuple[VerticalLink, ...]
    counts_by_vl: Dict[int, int]
    load_cost_by_vl: Dict[int, Fraction]
    selected_distance_by_key: Dict[Tuple[int, ...], int]
    total_distance_cost: int
    load_imbalance_cost: Fraction
    total_cost: Fraction


def chiplet_router_id(chiplet_id: int, local_x: int, local_y: int) -> int:
    origin_x = (chiplet_id % CHIPLET_GRID_WIDTH) * CHIPLET_LOCAL_WIDTH
    origin_y = (chiplet_id // CHIPLET_GRID_WIDTH) * CHIPLET_LOCAL_HEIGHT
    return (origin_y + local_y) * FOOTPRINT_WIDTH + origin_x + local_x


def interposer_router_id(footprint_x: int, footprint_y: int) -> int:
    return CHIPLET_ROUTER_COUNT + footprint_y * FOOTPRINT_WIDTH + footprint_x


def build_vertical_links() -> Tuple[VerticalLink, ...]:
    links: List[VerticalLink] = []
    for chiplet_id in range(CHIPLET_COUNT):
        for slot_id in range(VERTICAL_LINKS_PER_CHIPLET):
            endpoint = chiplet_router_id(
                chiplet_id,
                SLOT_LOCAL_X[slot_id],
                SLOT_LOCAL_Y[slot_id],
            )
            footprint_x = endpoint % FOOTPRINT_WIDTH
            footprint_y = endpoint // FOOTPRINT_WIDTH
            links.append(
                VerticalLink(
                    vl_id=chiplet_id * VERTICAL_LINKS_PER_CHIPLET + slot_id,
                    owner_chiplet_id=chiplet_id,
                    slot=SLOT_NAMES[slot_id],
                    chiplet_endpoint_router_id=endpoint,
                    interposer_endpoint_router_id=interposer_router_id(
                        footprint_x,
                        footprint_y,
                    ),
                    footprint_x=footprint_x,
                    footprint_y=footprint_y,
                )
            )
    return tuple(links)


VERTICAL_LINKS = build_vertical_links()
LINK_BY_ID = {link.vl_id: link for link in VERTICAL_LINKS}


def set_size(chiplets_x: int, chiplets_y: int, chiplet_w: int, chiplet_h: int) -> None:
    """Re-derive every size constant (as DeftTopology::configure in Noxim)."""
    global CHIPLET_GRID_WIDTH, CHIPLET_GRID_HEIGHT, CHIPLET_COUNT, CHIPLET_LOCAL_WIDTH
    global CHIPLET_LOCAL_HEIGHT, FOOTPRINT_WIDTH, FOOTPRINT_HEIGHT, CHIPLET_ROUTER_COUNT
    global INTERPOSER_ROUTER_COUNT, VERTICAL_LINK_COUNT, MAX_CONNECTED_FAULT_COUNT
    global SLOT_LOCAL_X, SLOT_LOCAL_Y, VERTICAL_LINKS, LINK_BY_ID
    if chiplets_x < 1 or chiplets_y < 1 or chiplets_x * chiplets_y < 2:
        raise ValueError("need a chiplet grid with at least 2 chiplets")
    if chiplet_w < 3 or chiplet_h < 3:
        raise ValueError("chiplets must be at least 3x3 routers")
    if chiplets_x * chiplets_y * VERTICAL_LINKS_PER_CHIPLET > 64:
        raise ValueError("at most 64 vertical links (16 chiplets)")
    CHIPLET_GRID_WIDTH, CHIPLET_GRID_HEIGHT = chiplets_x, chiplets_y
    CHIPLET_COUNT = chiplets_x * chiplets_y
    CHIPLET_LOCAL_WIDTH, CHIPLET_LOCAL_HEIGHT = chiplet_w, chiplet_h
    FOOTPRINT_WIDTH = chiplets_x * chiplet_w
    FOOTPRINT_HEIGHT = chiplets_y * chiplet_h
    CHIPLET_ROUTER_COUNT = FOOTPRINT_WIDTH * FOOTPRINT_HEIGHT
    INTERPOSER_ROUTER_COUNT = FOOTPRINT_WIDTH * FOOTPRINT_HEIGHT
    VERTICAL_LINK_COUNT = CHIPLET_COUNT * VERTICAL_LINKS_PER_CHIPLET
    MAX_CONNECTED_FAULT_COUNT = VERTICAL_LINK_COUNT - CHIPLET_COUNT
    SLOT_LOCAL_X = (1, chiplet_w - 1, chiplet_w - 2, 0)
    SLOT_LOCAL_Y = (0, 1, chiplet_h - 1, chiplet_h - 2)
    VERTICAL_LINKS = build_vertical_links()
    LINK_BY_ID = {link.vl_id: link for link in VERTICAL_LINKS}


def chiplet_id_for_router(router_id: int) -> int:
    footprint_x = router_id % FOOTPRINT_WIDTH
    footprint_y = router_id // FOOTPRINT_WIDTH
    chiplet_x = footprint_x // CHIPLET_LOCAL_WIDTH
    chiplet_y = footprint_y // CHIPLET_LOCAL_HEIGHT
    return chiplet_y * CHIPLET_GRID_WIDTH + chiplet_x


def chiplet_routers(chiplet_id: int) -> Tuple[int, ...]:
    routers: List[int] = []
    for local_y in range(CHIPLET_LOCAL_HEIGHT):
        for local_x in range(CHIPLET_LOCAL_WIDTH):
            routers.append(chiplet_router_id(chiplet_id, local_x, local_y))
    return tuple(routers)


def links_for_chiplet(chiplet_id: int, functional_vl_ids: Sequence[int]) -> Tuple[VerticalLink, ...]:
    functional = set(functional_vl_ids)
    return tuple(
        link
        for link in VERTICAL_LINKS
        if link.owner_chiplet_id == chiplet_id and link.vl_id in functional
    )


def manhattan_distance(point: DemandPoint, link: VerticalLink) -> int:
    return abs(point.footprint_x - link.footprint_x) + abs(point.footprint_y - link.footprint_y)


def load_cost_for_counts(counts: Sequence[Fraction], demand_count: Fraction) -> Fraction:
    """Sum of relative deviations of the per-VL loads from their mean.

    `counts` are per-VL loads (assigned demand weight; unit weights give counts)
    and `demand_count` is the total weight."""
    if demand_count == 0:
        return Fraction(0, 1)

    average = Fraction(demand_count) / len(counts)
    if average == 0:
        return Fraction(0, 1)

    return sum(abs(Fraction(count) - average) / average for count in counts)


def optimize_assignments(
    demand_points: Sequence[DemandPoint],
    candidate_vls: Sequence[VerticalLink],
    rho: Fraction,
    weights: Dict[Tuple[int, ...], Fraction] | None = None,
) -> OptimizationResult:
    """Exact dynamic programme over per-VL load vectors.

    `weights` maps a demand point key to its demand (default: 1 for every
    point). Partial assignments with equal load vectors are merged keeping the
    smallest (distance, assignment), as in the unit-weight case."""
    if not candidate_vls:
        raise ValueError("cannot optimize without functional candidate VLs")
    if not demand_points:
        raise ValueError("cannot optimize without demand points")
    if len(demand_points) > DP_MAX_POINTS:
        return optimize_assignments_milp(demand_points, candidate_vls, rho, weights)

    candidates = tuple(sorted(candidate_vls, key=lambda link: link.vl_id))
    total_weight = (len(demand_points) if weights is None
                    else sum((weights[point.key] for point in demand_points), Fraction(0)))
    zero_counts = tuple(0 for _ in candidates)
    states: Dict[Tuple[int, ...], Tuple[int, Tuple[int, ...]]] = {zero_counts: (0, tuple())}

    for point in demand_points:
        next_states: Dict[Tuple[int, ...], Tuple[int, Tuple[int, ...]]] = {}
        for counts, state in states.items():
            distance_sum, assignment = state
            for candidate_index, link in enumerate(candidates):
                next_counts = list(counts)
                next_counts[candidate_index] += 1 if weights is None else weights[point.key]
                next_counts_tuple = tuple(next_counts)
                next_distance_sum = distance_sum + manhattan_distance(point, link)
                next_assignment = assignment + (link.vl_id,)
                existing = next_states.get(next_counts_tuple)
                if existing is None or (next_distance_sum, next_assignment) < existing:
                    next_states[next_counts_tuple] = (next_distance_sum, next_assignment)
        states = next_states

    best_counts: Tuple[int, ...] | None = None
    best_distance = 0
    best_assignment: Tuple[int, ...] = tuple()
    best_load_cost = Fraction(0, 1)
    best_total = Fraction(0, 1)
    best_key = None

    for counts, state in states.items():
        distance_sum, assignment = state
        load_cost = load_cost_for_counts(counts, total_weight)
        total = rho * distance_sum + load_cost
        ranking_key = (total, load_cost, distance_sum, assignment)
        if best_key is None or ranking_key < best_key:
            best_key = ranking_key
            best_counts = counts
            best_distance = distance_sum
            best_assignment = assignment
            best_load_cost = load_cost
            best_total = total

    assert best_counts is not None

    selected_by_key: Dict[Tuple[int, ...], int] = {}
    selected_distance_by_key: Dict[Tuple[int, ...], int] = {}
    demand_by_key: Dict[Tuple[int, ...], DemandPoint] = {}
    for point, selected_vl_id in zip(demand_points, best_assignment):
        selected_link = LINK_BY_ID[selected_vl_id]
        selected_by_key[point.key] = selected_vl_id
        selected_distance_by_key[point.key] = manhattan_distance(point, selected_link)
        demand_by_key[point.key] = point

    counts_by_vl = {
        link.vl_id: best_counts[index]
        for index, link in enumerate(candidates)
    }
    average_load = Fraction(total_weight) / len(candidates)
    load_cost_by_vl = {
        link.vl_id: (abs(Fraction(counts_by_vl[link.vl_id]) - average_load) / average_load
                     if average_load != 0 else Fraction(0, 1))
        for link in candidates
    }

    return OptimizationResult(
        selected_by_key=selected_by_key,
        demand_by_key=demand_by_key,
        candidate_vls=candidates,
        counts_by_vl=counts_by_vl,
        load_cost_by_vl=load_cost_by_vl,
        selected_distance_by_key=selected_distance_by_key,
        total_distance_cost=best_distance,
        load_imbalance_cost=best_load_cost,
        total_cost=best_total,
    )


def result_from_assignment(
    demand_points: Sequence[DemandPoint],
    candidates: Tuple[VerticalLink, ...],
    assignment: Sequence[int],
    rho: Fraction,
    weights: Dict[Tuple[int, ...], Fraction] | None,
) -> OptimizationResult:
    """OptimizationResult of a given assignment (same quantities as the DP path)."""
    weight = (lambda point: 1) if weights is None else (lambda point: weights[point.key])
    total_weight = (len(demand_points) if weights is None
                    else sum((weights[point.key] for point in demand_points), Fraction(0)))
    loads = {link.vl_id: Fraction(0) for link in candidates}
    selected_by_key: Dict[Tuple[int, ...], int] = {}
    selected_distance_by_key: Dict[Tuple[int, ...], int] = {}
    demand_by_key: Dict[Tuple[int, ...], DemandPoint] = {}
    distance_sum = 0
    for point, vl_id in zip(demand_points, assignment):
        loads[vl_id] += weight(point)
        selected_by_key[point.key] = vl_id
        d = manhattan_distance(point, LINK_BY_ID[vl_id])
        selected_distance_by_key[point.key] = d
        demand_by_key[point.key] = point
        distance_sum += d
    load_cost = load_cost_for_counts([loads[link.vl_id] for link in candidates], total_weight)
    average_load = Fraction(total_weight) / len(candidates)
    load_cost_by_vl = {
        link.vl_id: (abs(loads[link.vl_id] - average_load) / average_load
                     if average_load != 0 else Fraction(0, 1))
        for link in candidates
    }
    return OptimizationResult(
        selected_by_key=selected_by_key,
        demand_by_key=demand_by_key,
        candidate_vls=candidates,
        counts_by_vl=dict(loads),
        load_cost_by_vl=load_cost_by_vl,
        selected_distance_by_key=selected_distance_by_key,
        total_distance_cost=distance_sum,
        load_imbalance_cost=load_cost,
        total_cost=rho * distance_sum + load_cost,
    )


def optimize_assignments_milp(
    demand_points: Sequence[DemandPoint],
    candidate_vls: Sequence[VerticalLink],
    rho: Fraction,
    weights: Dict[Tuple[int, ...], Fraction] | None = None,
) -> OptimizationResult:
    """Exact optimum of rho * sum(distance) + sum_v |load_v - mean| / mean as a MILP.

    Variables: x[j, v] binary (point j uses VL v) and d[v] >= |load_v - mean|.
    Used for problems too large for the dynamic programme (> DP_MAX_POINTS points)."""
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    candidates = tuple(sorted(candidate_vls, key=lambda link: link.vl_id))
    n, m = len(demand_points), len(candidates)
    w = [1.0 if weights is None else float(weights[p.key]) for p in demand_points]
    # The objective is invariant to scaling all weights; normalising them to mean 1 makes
    # equal-weight demand the same problem as unit demand (same solution, same ties).
    if weights is not None and sum(w) > 0 and len(set(w)) == 1:
        w = [1.0] * n
    elif sum(w) > 0:
        scale = n / sum(w)
        w = [x * scale for x in w]
    total = sum(w)
    mean = total / m
    nx_ = n * m
    c = np.zeros(nx_ + m)
    for j, point in enumerate(demand_points):
        for v, link in enumerate(candidates):
            c[j * m + v] = float(rho) * manhattan_distance(point, link)
    rows, lo, hi = [], [], []
    for j in range(n):
        row = np.zeros(nx_ + m)
        row[j * m:(j + 1) * m] = 1.0
        rows.append(row)
        lo.append(1.0)
        hi.append(1.0)
    if mean > 0:
        c[nx_:] = 1.0 / mean
        for v in range(m):
            for sign in (1.0, -1.0):      # d_v - sign * (load_v - mean) >= 0
                row = np.zeros(nx_ + m)
                for j in range(n):
                    row[j * m + v] = -sign * w[j]
                row[nx_ + v] = 1.0
                rows.append(row)
                lo.append(-sign * mean)
                hi.append(np.inf)
    integrality = np.concatenate([np.ones(nx_), np.zeros(m)])
    upper = np.concatenate([np.ones(nx_), np.full(m, np.inf)])
    res = milp(c, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integrality,
               bounds=Bounds(np.zeros(nx_ + m), upper), options={"mip_rel_gap": 0.0, "time_limit": 3600})
    if res.x is None or not res.success:
        raise ValueError(f"MILP failed: {res.message}")
    assignment = []
    for j in range(n):
        v = int(np.argmax(res.x[j * m:(j + 1) * m]))
        assignment.append(candidates[v].vl_id)
    return result_from_assignment(demand_points, candidates, assignment, rho, weights)


def source_demand_points(chiplet_id: int) -> Tuple[DemandPoint, ...]:
    points: List[DemandPoint] = []
    for router_id in chiplet_routers(chiplet_id):
        points.append(
            DemandPoint(
                key=(router_id,),
                footprint_x=router_id % FOOTPRINT_WIDTH,
                footprint_y=router_id // FOOTPRINT_WIDTH,
            )
        )
    return tuple(points)


def destination_demand_points(
    destination_chiplet_id: int,
    source_results: Dict[int, OptimizationResult],
) -> Tuple[DemandPoint, ...]:
    points: List[DemandPoint] = []
    for source_chiplet_id in range(CHIPLET_COUNT):
        if source_chiplet_id == destination_chiplet_id:
            continue
        for source_router_id in chiplet_routers(source_chiplet_id):
            source_vl_id = source_results[source_chiplet_id].selected_by_key[(source_router_id,)]
            source_link = LINK_BY_ID[source_vl_id]
            points.append(
                DemandPoint(
                    key=(source_chiplet_id, source_router_id),
                    footprint_x=source_link.footprint_x,
                    footprint_y=source_link.footprint_y,
                )
            )
    return tuple(points)


def read_demand_table(path: Path) -> Dict[Tuple[int, int], Fraction]:
    """Time-averaged demand (packets/cycle) per (source, destination) router.

    Noxim activates a line in cycle c when t_on < c % t_period < t_off, so a
    line with timing fields is active (t_off - t_on - 1) / t_period of the
    time; a line without them is always active."""
    demand: Dict[Tuple[int, int], Fraction] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("%"):
            continue
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(f"demand table line without a rate: {raw}")
        src, dst, pir = int(fields[0]), int(fields[1]), Fraction(fields[2])
        if len(fields) >= 7:
            t_on, t_off, t_period = int(fields[4]), int(fields[5]), int(fields[6])
            pir *= Fraction(t_off - t_on - 1, t_period)
        elif len(fields) > 4:
            raise ValueError(f"unsupported partial timing fields: {raw}")
        if not (0 <= src < CHIPLET_ROUTER_COUNT and 0 <= dst < CHIPLET_ROUTER_COUNT):
            raise ValueError(f"demand table router id out of range: {raw}")
        demand[(src, dst)] = demand.get((src, dst), Fraction(0)) + pir
    return demand


def source_weights(
    chiplet_id: int, demand: Dict[Tuple[int, int], Fraction]
) -> Dict[Tuple[int, ...], Fraction]:
    """Inter-chiplet demand leaving each router of the chiplet."""
    return {
        (router_id,): sum(
            (rate for (src, dst), rate in demand.items()
             if src == router_id and chiplet_id_for_router(dst) != chiplet_id),
            Fraction(0),
        )
        for router_id in chiplet_routers(chiplet_id)
    }


def destination_weights(
    destination_chiplet_id: int, demand: Dict[Tuple[int, int], Fraction]
) -> Dict[Tuple[int, ...], Fraction]:
    """Demand from every other-chiplet router into the destination chiplet."""
    weights: Dict[Tuple[int, ...], Fraction] = {}
    for source_chiplet_id in range(CHIPLET_COUNT):
        if source_chiplet_id == destination_chiplet_id:
            continue
        for source_router_id in chiplet_routers(source_chiplet_id):
            weights[(source_chiplet_id, source_router_id)] = sum(
                (rate for (src, dst), rate in demand.items()
                 if src == source_router_id and chiplet_id_for_router(dst) == destination_chiplet_id),
                Fraction(0),
            )
    return weights


def parse_fraction(value: str) -> Fraction:
    try:
        parsed = Fraction(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid fraction: {value}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("rho must be non-negative")
    return parsed


def parse_fault_mask(value: str) -> int:
    try:
        mask = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid fault mask: {value}") from exc
    if mask < 0 or mask >= (1 << VERTICAL_LINK_COUNT):
        raise argparse.ArgumentTypeError(
            f"fault mask must fit {VERTICAL_LINK_COUNT} physical VL bits"
        )
    return mask


def parse_faulty_vls(value: str) -> int:
    if value.strip() == "":
        return 0

    faulty_ids: List[int] = []
    seen = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            vl_id = int(token, 0)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid VL id: {token}") from exc
        if vl_id < 0 or vl_id >= VERTICAL_LINK_COUNT:
            raise argparse.ArgumentTypeError(f"VL id out of range: {vl_id}")
        if vl_id in seen:
            raise argparse.ArgumentTypeError(f"duplicate VL id: {vl_id}")
        seen.add(vl_id)
        faulty_ids.append(vl_id)

    mask = 0
    for vl_id in faulty_ids:
        mask |= 1 << vl_id
    return mask


def faulty_vl_ids(mask: int) -> Tuple[int, ...]:
    return tuple(vl_id for vl_id in range(VERTICAL_LINK_COUNT) if mask & (1 << vl_id))


def functional_vl_ids(mask: int) -> Tuple[int, ...]:
    return tuple(vl_id for vl_id in range(VERTICAL_LINK_COUNT) if not mask & (1 << vl_id))


def format_fault_mask(mask: int) -> str:
    width = (VERTICAL_LINK_COUNT + 3) // 4
    return f"0x{mask:0{width}x}"


def validate_fault_mask(mask: int) -> None:
    faulty_per_chiplet = [0 for _ in range(CHIPLET_COUNT)]
    for vl_id in faulty_vl_ids(mask):
        chiplet_id = LINK_BY_ID[vl_id].owner_chiplet_id
        faulty_per_chiplet[chiplet_id] += 1
    for chiplet_id, fault_count in enumerate(faulty_per_chiplet):
        if fault_count >= VERTICAL_LINKS_PER_CHIPLET:
            raise ValueError(
                f"fault mask {format_fault_mask(mask)} disconnects chiplet {chiplet_id}"
            )


def masks_up_to_fault_count(max_fault_count: int) -> Iterable[int]:
    if max_fault_count < 0:
        raise ValueError("max fault count must be non-negative")
    if max_fault_count > MAX_CONNECTED_FAULT_COUNT:
        raise ValueError(
            f"max fault count {max_fault_count} exceeds connected-chiplet maximum "
            f"{MAX_CONNECTED_FAULT_COUNT}"
        )

    for fault_count in range(max_fault_count + 1):
        for combination in itertools.combinations(range(VERTICAL_LINK_COUNT), fault_count):
            mask = 0
            for vl_id in combination:
                mask |= 1 << vl_id
            try:
                validate_fault_mask(mask)
            except ValueError:
                continue
            yield mask


def ordered_fault_masks(
    explicit_masks: Sequence[int],
    explicit_fault_lists: Sequence[int],
    max_fault_count: int | None,
) -> Tuple[int, ...]:
    masks = set(explicit_masks)
    masks.update(explicit_fault_lists)
    if max_fault_count is not None:
        masks.update(masks_up_to_fault_count(max_fault_count))
    if not masks:
        masks.add(0)

    for mask in masks:
        validate_fault_mask(mask)
    return tuple(sorted(masks))


def inline_int_list(values: Sequence[int]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(str(value) for value in values) + "]"


def decimal_string(value: Fraction) -> str:
    return f"{float(value):.6f}"


def candidate_rank(
    point: DemandPoint,
    selected_vl_id: int,
    result: OptimizationResult,
    rho: Fraction,
) -> Tuple[int, ...]:
    remaining = []
    for link in result.candidate_vls:
        if link.vl_id == selected_vl_id:
            continue
        distance = manhattan_distance(point, link)
        load_cost = result.load_cost_by_vl[link.vl_id]
        total = rho * distance + load_cost
        remaining.append((total, load_cost, distance, link.vl_id))
    remaining.sort()
    return (selected_vl_id,) + tuple(item[3] for item in remaining)


def entry_cost(
    point: DemandPoint,
    selected_vl_id: int,
    result: OptimizationResult,
    rho: Fraction,
) -> Tuple[Fraction, int, Fraction]:
    distance = result.selected_distance_by_key[point.key]
    load_cost = result.load_cost_by_vl[selected_vl_id]
    total = rho * distance + load_cost
    return total, distance, load_cost


def generate_lut_text(
    fault_masks: Sequence[int],
    rho: Fraction = Fraction(DEFAULT_RHO),
    traffic_profile_id: str = DEFAULT_TRAFFIC_PROFILE_ID,
    include_costs: bool = True,
    demand: Dict[Tuple[int, int], Fraction] | None = None,
) -> str:
    lines: List[str] = []
    lines.append(f"schema: {SCHEMA}")
    lines.append(f"topology: {TOPOLOGY}")
    lines.append("topology_signature:")
    lines.append(f"  chiplet_count: {CHIPLET_COUNT}")
    lines.append(f"  chiplet_router_count: {CHIPLET_ROUTER_COUNT}")
    lines.append(f"  interposer_router_count: {INTERPOSER_ROUTER_COUNT}")
    lines.append(f"  physical_vertical_link_count: {VERTICAL_LINK_COUNT}")
    lines.append(f"  vertical_links_per_chiplet: {VERTICAL_LINKS_PER_CHIPLET}")
    lines.append("generation:")
    lines.append(f"  generator: {GENERATOR_NAME}")
    lines.append(f"  generator_version: {GENERATOR_VERSION}")
    lines.append("  objective: rho_distance_plus_load_imbalance")
    lines.append(f"  rho: {decimal_string(rho)}")
    lines.append(f"  traffic_profile_id: {traffic_profile_id}")
    if demand is None:
        lines.append("  traffic_assumption: uniform_unit_interchiplet_demand")
    else:
        lines.append("  traffic_assumption: demand_matrix_from_traffic_table_time_averaged")
    lines.append("  source_selection_model: exhaustive_dynamic_programming_per_chiplet")
    lines.append("  destination_entry_model: interposer_context_assignment_without_destination_router_id")
    lines.append("fault_scenarios:")

    for mask in fault_masks:
        functional = functional_vl_ids(mask)
        lines.append(f"  - fault_mask_id: \"{format_fault_mask(mask)}\"")
        lines.append(f"    faulty_vl_ids: {inline_int_list(faulty_vl_ids(mask))}")
        lines.append(f"    functional_vl_ids: {inline_int_list(functional)}")

    lines.append("entries:")

    for mask in fault_masks:
        functional = functional_vl_ids(mask)
        source_results: Dict[int, OptimizationResult] = {}
        for chiplet_id in range(CHIPLET_COUNT):
            source_results[chiplet_id] = optimize_assignments(
                source_demand_points(chiplet_id),
                links_for_chiplet(chiplet_id, functional),
                rho,
                None if demand is None else source_weights(chiplet_id, demand),
            )

        destination_results: Dict[int, OptimizationResult] = {}
        for chiplet_id in range(CHIPLET_COUNT):
            destination_results[chiplet_id] = optimize_assignments(
                destination_demand_points(chiplet_id, source_results),
                links_for_chiplet(chiplet_id, functional),
                rho,
                None if demand is None else destination_weights(chiplet_id, demand),
            )

        for source_chiplet_id in range(CHIPLET_COUNT):
            for source_router_id in chiplet_routers(source_chiplet_id):
                for destination_chiplet_id in range(CHIPLET_COUNT):
                    if destination_chiplet_id == source_chiplet_id:
                        continue

                    source_result = source_results[source_chiplet_id]
                    source_point = source_result.demand_by_key[(source_router_id,)]
                    source_vl_id = source_result.selected_by_key[(source_router_id,)]
                    source_link = LINK_BY_ID[source_vl_id]
                    source_rank = candidate_rank(source_point, source_vl_id, source_result, rho)

                    destination_result = destination_results[destination_chiplet_id]
                    destination_key = (source_chiplet_id, source_router_id)
                    destination_point = destination_result.demand_by_key[destination_key]
                    destination_vl_id = destination_result.selected_by_key[destination_key]
                    destination_link = LINK_BY_ID[destination_vl_id]
                    destination_rank = candidate_rank(
                        destination_point,
                        destination_vl_id,
                        destination_result,
                        rho,
                    )

                    lines.append("  - key:")
                    lines.append(f"      fault_mask_id: \"{format_fault_mask(mask)}\"")
                    lines.append(f"      source_chiplet_id: {source_chiplet_id}")
                    lines.append(f"      source_router_id: {source_router_id}")
                    lines.append(f"      destination_chiplet_id: {destination_chiplet_id}")
                    lines.append("    value:")
                    lines.append("      source_exit:")
                    lines.append(f"        selected_vl_id: {source_link.vl_id}")
                    lines.append(
                        f"        boundary_router_id: {source_link.chiplet_endpoint_router_id}"
                    )
                    lines.append(
                        "        interposer_endpoint_router_id: "
                        f"{source_link.interposer_endpoint_router_id}"
                    )
                    lines.append(f"        ranked_vl_ids: {inline_int_list(source_rank)}")
                    lines.append("      destination_entry:")
                    lines.append(f"        selected_vl_id: {destination_link.vl_id}")
                    lines.append(
                        "        boundary_router_id: "
                        f"{destination_link.chiplet_endpoint_router_id}"
                    )
                    lines.append(
                        "        interposer_endpoint_router_id: "
                        f"{destination_link.interposer_endpoint_router_id}"
                    )
                    lines.append(f"        ranked_vl_ids: {inline_int_list(destination_rank)}")
                    if include_costs:
                        source_total, source_distance, source_load = entry_cost(
                            source_point,
                            source_vl_id,
                            source_result,
                            rho,
                        )
                        destination_total, destination_distance, destination_load = entry_cost(
                            destination_point,
                            destination_vl_id,
                            destination_result,
                            rho,
                        )
                        lines.append("      cost:")
                        lines.append(
                            f"        source_exit_total: {decimal_string(source_total)}"
                        )
                        lines.append(f"        source_exit_distance: {source_distance}")
                        lines.append(
                            "        source_exit_load_imbalance: "
                            f"{decimal_string(source_load)}"
                        )
                        lines.append(
                            "        destination_entry_total: "
                            f"{decimal_string(destination_total)}"
                        )
                        lines.append(
                            f"        destination_entry_distance: {destination_distance}"
                        )
                        lines.append(
                            "        destination_entry_load_imbalance: "
                            f"{decimal_string(destination_load)}"
                        )

    lines.append("")
    return "\n".join(lines)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic DeFT offline VL LUT YAML.",
    )
    parser.add_argument("--chiplets-x", type=int, default=CHIPLET_GRID_WIDTH,
                        help="Chiplet grid width (default 2).")
    parser.add_argument("--chiplets-y", type=int, default=CHIPLET_GRID_HEIGHT,
                        help="Chiplet grid height (default 2).")
    parser.add_argument("--chiplet-w", type=int, default=CHIPLET_LOCAL_WIDTH,
                        help="Routers per chiplet row (default 4).")
    parser.add_argument("--chiplet-h", type=int, default=CHIPLET_LOCAL_HEIGHT,
                        help="Routers per chiplet column (default 4).")
    parser.add_argument(
        "--fault-mask",
        action="append",
        default=[],
        help="Fault mask bitset such as 0x0000 or 0x1111. May be repeated.",
    )
    parser.add_argument(
        "--faulty-vls",
        action="append",
        default=[],
        help="Comma-separated physical faulty VL IDs, such as 0,4,8,12.",
    )
    parser.add_argument(
        "--max-fault-count",
        type=int,
        default=None,
        help="Generate every valid connected-chiplet mask up to this physical fault count.",
    )
    parser.add_argument(
        "--rho",
        type=parse_fraction,
        default=Fraction(DEFAULT_RHO),
        help=f"Distance/load trade-off coefficient. Default: {DEFAULT_RHO}.",
    )
    parser.add_argument(
        "--traffic-profile-id",
        default=DEFAULT_TRAFFIC_PROFILE_ID,
        help=f"Traffic profile identifier recorded in the LUT. Default: {DEFAULT_TRAFFIC_PROFILE_ID}.",
    )
    parser.add_argument(
        "--demand-table",
        type=Path,
        default=None,
        help="Noxim traffic table whose time-averaged demand weights the load terms "
             "(default: uniform unit inter-chiplet demand).",
    )
    parser.add_argument(
        "--omit-costs",
        action="store_true",
        help="Omit optional per-entry inspectability cost fields.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output YAML path. Writes to standard output when omitted.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        set_size(args.chiplets_x, args.chiplets_y, args.chiplet_w, args.chiplet_h)
        # masks are converted after the size is known (their width depends on it)
        try:
            fault_masks = [parse_fault_mask(v) for v in args.fault_mask]
            fault_lists = [parse_faulty_vls(v) for v in args.faulty_vls]
        except argparse.ArgumentTypeError as exc:
            raise ValueError(str(exc)) from exc
        masks = ordered_fault_masks(fault_masks, fault_lists, args.max_fault_count)
        output = generate_lut_text(
            masks,
            rho=args.rho,
            traffic_profile_id=args.traffic_profile_id,
            include_costs=not args.omit_costs,
            demand=None if args.demand_table is None else read_demand_table(args.demand_table),
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.output is None:
        sys.stdout.write(output)
    else:
        args.output.write_text(output, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
