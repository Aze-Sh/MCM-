"""Offline lower bounds from saved synthetic truth, never used by a policy.

Relax each clear location to its 20 m disk. Distances between consecutive
disks are optimized independently, ignoring sensing and disk-entry coupling.
An exact subset DP solves this optimistic open-path problem (no return leg).
Integer edge lengths are rounded down using exact rational squared distances.
"""

import argparse
from array import array
from fractions import Fraction
from itertools import permutations
import json
from math import isqrt
from pathlib import Path
from information import absence_lower

SCALE = 1000
INF = (1 << 63) - 1


def distance_floor(a, b):
    squared = sum((Fraction(x) - Fraction(y)) ** 2 for x, y in zip(a, b))
    scaled = squared * SCALE ** 2
    return isqrt(scaled.numerator // scaled.denominator)


def optimistic_edges(points):
    starts = [max(0, distance_floor((0, 0), p) - 20 * SCALE) for p in points]
    edges = [[max(0, distance_floor(p, q) - 40 * SCALE) for q in points] for p in points]
    return starts, edges


def shortest_open_path(starts, edges):
    n = len(starts)
    if not n:
        return 0
    if n > 16:
        raise ValueError("This evaluator is bounded to 16 sources.")
    full = (1 << n) - 1
    costs = array("q", [INF]) * ((1 << n) * n)
    for j, cost in enumerate(starts):
        costs[(1 << j) * n + j] = cost
    for mask in range(1, full + 1):
        current = mask
        while current:
            bit = current & -current
            i = bit.bit_length() - 1
            value = costs[mask * n + i]
            rest = full ^ mask
            while rest:
                next_bit = rest & -rest
                j = next_bit.bit_length() - 1
                index = (mask | next_bit) * n + j
                candidate = value + edges[i][j]
                if candidate < costs[index]:
                    costs[index] = candidate
                rest ^= next_bit
            current ^= bit
    return min(costs[full * n:(full + 1) * n])


def self_test():
    assert distance_floor((0, 0), (3, 4)) == 5000
    assert distance_floor((0, 0), (1, 1)) == 1414
    assert shortest_open_path([], []) == 0
    for points in [[(100, 0)], [(100, 0), (200, 0)],
                   [(0, 0), (10, 0), (0, 10)],
                   [(71, -30), (-80, 100), (300, 400), (0, -500), (110, 110), (900, 20)]]:
        starts, edges = optimistic_edges(points)
        brute = min(starts[order[0]] + sum(edges[i][j] for i, j in zip(order, order[1:]))
                    for order in permutations(range(len(points))))
        assert shortest_open_path(starts, edges) == brute
    starts, edges = optimistic_edges([(100, 0)])
    assert shortest_open_path(starts, edges) / SCALE / 5 + 5 == 21


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Self-checks passed: exact edge floors, empty/single cases, exhaustive route comparison.")
    if args.input is None:
        if not args.self_test:
            parser.error("input is required unless --self-test is supplied")
        return
    data = json.loads(args.input.read_text(encoding="utf-8"))
    results = []
    for case in data["cases"]:
        points = [s["position"] for s in case["source_truth"]]
        if not 10 <= len(points) <= 16 or case["cleared_count"] != len(points):
            raise ValueError("Expected a complete 10–16-source saved synthetic case.")
        starts, edges = optimistic_edges(points)
        distance_mm = shortest_open_path(starts, edges)
        lower = distance_mm / SCALE / 5 + 5 * len(points)
        actual = case["virtual_time_s"]
        information = absence_lower(case['problem'],len(points))
        combined = lower+information
        results.append(dict(problem=case["problem"], seed=case["seed"], source_count=len(points),
                            movement_lower_mm=distance_mm, total_time_lower_s=lower,
                            absence_operation_lower_s=information, combined_lower_s=combined,
                            actual_over_combined_lower=actual/combined,
                            saved_v7_virtual_time_s=actual, actual_over_lower=actual / lower,
                            interpretation="Loose oracle-relaxation comparison, not the measured optimality gap."))
    result = dict(kind="offline-clairvoyant-relaxation-lower-bounds", cases=results,
                  scope="Geometric relaxation plus necessary absent-channel operations; incomplete information-cost lower bound.")
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
