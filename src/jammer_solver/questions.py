import argparse
import heapq
import json
import math
from itertools import combinations
from pathlib import Path as lj

eps = math.radians(1.005)


def hull(points):
    points = sorted(set(points))
    if len(points) <= 1:
        return points

    def chain(seq):
        out = []
        for p in seq:
            while (
                len(out) >= 2
                and (out[-1][0] - out[-2][0]) * (p[1] - out[-1][1])
                - (out[-1][1] - out[-2][1]) * (p[0] - out[-1][0])
                <= 0
            ):
                out.pop()
            out.append(p)
        return out

    return chain(points)[:-1] + chain(points[::-1])[:-1]


def zydd(vertices):
    n = len(vertices)
    if n == 1:
        return (vertices[0], vertices[0])
    if n == 2:
        return tuple(vertices)
    best = (vertices[0], vertices[1])
    bestd = math.dist(*best)
    j = 1
    for i in range(n):
        nxt = (i + 1) % n
        edge = (vertices[nxt][0] - vertices[i][0], vertices[nxt][1] - vertices[i][1])

        def area(k):
            return abs(
                edge[0] * (vertices[k][1] - vertices[i][1])
                - edge[1] * (vertices[k][0] - vertices[i][0])
            )

        steps = 0
        while area((j + 1) % n) > area(j) and steps < n:
            j = (j + 1) % n
            steps += 1
        for a in (i, nxt):
            for b in (j, (j + 1) % n):
                d = math.dist(vertices[a], vertices[b])
                if d > bestd:
                    best, bestd = ((vertices[a], vertices[b]), d)
    return best


def jhqy(gclb, wcjd=1.005):
    planes = []
    for obs in gclb:
        x, y, angle = (float(obs[k]) for k in ("x", "y", "bearing_deg"))
        if not all((math.isfinite(v) for v in (x, y, angle))):
            raise ValueError("Observations must be finite")
        lo, hi = (math.radians(angle - wcjd), math.radians(angle + wcjd))
        for nx, ny in ((math.sin(lo), -math.cos(lo)), (-math.sin(hi), math.cos(hi))):
            planes.append((nx, ny, nx * x + ny * y))
    base = dict(
        epsilon_deg=wcjd,
        diameter=None,
        vertices=[],
        numerical_method="float64; relative feasibility tolerance 1e-10",
    )
    if not planes:
        return dict(base, state="UNBOUNDED")

    def feasible(x, y):
        return all(
            (
                a * x + b * y - c <= 1e-10 * (1 + abs(a * x) + abs(b * y) + abs(c))
                for a, b, c in planes
            )
        )

    bx = []
    for (a, b, c), (d, e, f) in combinations(planes, 2):
        det = a * e - b * d
        if abs(det) <= 1e-14:
            continue
        x, y = ((c * e - b * f) / det, (a * f - c * d) / det)
        if not math.isfinite(x) or not math.isfinite(y):
            return dict(base, state="NUMERICALLY_UNRESOLVED")
        if feasible(x, y):
            bx.append((x, y))
    if not bx:
        return dict(base, state="EMPTY_OR_NUMERICALLY_UNRESOLVED")
    for a, b, _ in planes:
        for dx, dy in ((b, -a), (-b, a)):
            if all((u * dx + v * dy <= 1e-14 for u, v, _ in planes)):
                return dict(base, state="UNBOUNDED", feasible_point=bx[0])
    vertices = hull(bx)
    p, q = zydd(vertices)
    diameter = math.dist(p, q)
    center = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    radius = diameter / 2
    return dict(
        base,
        state={1: "POINT", 2: "SEGMENT"}.get(len(vertices), "POLYGON"),
        vertices=vertices,
        diameter=diameter,
        farthest_pair=(p, q),
        diameter_circle_center=center,
        diameter_circle_radius=radius,
        diameter_circle_covers=all(
            (math.dist(v, center) <= radius + 1e-09 * (1 + radius) for v in vertices)
        ),
    )


def ecdqy(first, bearing, query=None):
    centers = [tuple(first)]
    for sign in (1, -1):
        angle = math.radians(bearing) + sign * eps
        centers.append(
            (first[0] + 1000 * math.cos(angle), first[1] + 1000 * math.sin(angle))
        )
    normal = (math.cos(math.radians(bearing)), math.sin(math.radians(bearing)))
    result = dict(
        disk_centers=centers,
        disk_radii=[1000] * 3,
        forward_halfplane=dict(
            normal=normal, origin=first, relation="dot(normal, q-origin) >= 0"
        ),
        epsilon_deg=1.005,
        scope="Exact for relaxed radial prior [0,1500] within forward halfplane; conservative for actual r>5 and source domain",
    )
    if query is not None:
        if len(query) != 2 or not all((math.isfinite(v) for v in query)):
            raise ValueError("Query must contain two finite coordinates")
        result["query_in_region"] = (
            all((math.hypot(query[0] - c[0], query[1] - c[1]) <= 1000 for c in centers))
            and sum((normal[k] * (query[k] - first[k]) for k in (0, 1))) >= 0
        )
    return result


def zjsj(rho, theta):
    a, b = (rho * math.cos(theta), rho * math.sin(theta))
    dist = max(
        (
            math.sqrt(r * r + rho * rho - 2 * r * rho * math.cos(theta + eps))
            for r in (5.0, 1500.0)
        )
    )
    height = b * math.cos(eps) - a * math.sin(eps)
    return (djsj(dist, height), dist)


def djsj(dist, height):
    sine = max(0.0, min(1.0, height / max(dist, 1e-12)))
    gamma = math.asin(sine) - 2 * eps
    if gamma <= 0:
        return math.inf
    w1, w2 = (1500 * math.sin(eps), dist * math.sin(eps))
    return (
        2
        * math.sqrt(w1 * w1 + w2 * w2 + 2 * w1 * w2 * math.cos(gamma))
        / math.sin(gamma)
    )


def jdyh(rho, tol=0.02, jdmax=1024):
    if not 5 < rho < 1000:
        raise ValueError("A positive reception margin requires 5 < movement < 1000")
    lo = eps + 1e-08
    hi = math.acos(rho / 2000) - eps - 1e-08

    def lower(a, b):
        d = zjsj(rho, a)[1]
        h = rho * math.sin(b - eps)
        return max(0.0, djsj(d, h) - 1e-06)

    best = min(((zjsj(rho, t)[0], t) for t in (lo, (lo + hi) / 2, hi)))
    heap = [(lower(lo, hi), lo, hi)]
    nodes = 0
    prunelb = math.inf
    while heap and nodes < jdmax:
        lb, a, b = heapq.heappop(heap)
        if best[0] - lb <= tol:
            prunelb = min(prunelb, lb)
            break
        mid = (a + b) / 2
        for x, y in ((a, mid), (mid, b)):
            t = (x + y) / 2
            value = zjsj(rho, t)[0]
            nodes += 1
            if value < best[0]:
                best = (value, t)
            bound = lower(x, y)
            if bound < best[0]:
                heapq.heappush(heap, (bound, x, y))
            else:
                prunelb = min(prunelb, bound)
    boundlo = min(best[0], prunelb, min((entry[0] for entry in heap), default=math.inf))
    bound, theta = best
    a, b = (rho * math.cos(theta), rho * math.sin(theta))
    endpos = max(
        (
            math.dist((a, b), (1000 * math.cos(eps), s * 1000 * math.sin(eps)))
            for s in (-1, 1)
        )
    )
    return dict(
        movement_m=rho,
        a_m=a,
        b_m=b,
        diameter_upper_m=bound,
        angle_family_lower_m=boundlo,
        optimization_gap_m=bound - boundlo,
        reception_margin_m=1000 - max(rho, endpos),
        nodes=nodes,
        scope="entire_feasible_angle_interval_at_fixed_movement_radius",
    )


def zxdj(target=163.0, jdmax=6000, tol=0.1):
    seed = jdyh(900.0)
    if seed["diameter_upper_m"] > target:
        seed = jdyh(999.0)
    if seed["diameter_upper_m"] > target:
        raise ValueError(
            "No initial feasible design for this target; choose a larger diameter target"
        )
    best = (
        seed["movement_m"],
        math.atan2(seed["b_m"], seed["a_m"]),
        seed["diameter_upper_m"],
    )
    heap = []
    serial = 0
    nodes = 0

    def add(r0, r1, t0, t1):
        nonlocal serial
        r1 = min(r1, 2000 * math.cos(t0 + eps))
        t1 = min(t1, math.acos(r0 / 2000) - eps)
        if r0 >= r1 or t0 >= t1 or r0 >= best[0]:
            return
        dists = []
        for r in (5.0, 1500.0):
            rho = max(r0, min(r1, r * math.cos(t0 + eps)))
            dists.append(
                math.sqrt(
                    max(0.0, r * r + rho * rho - 2 * r * rho * math.cos(t0 + eps))
                )
            )
        lb = djsj(max(dists), r1 * math.sin(t1 - eps)) - 1e-06
        if lb > target:
            return
        serial += 1
        heapq.heappush(heap, (r0, serial, (r0, r1, t0, t1)))

    add(5.0001, best[0], eps + 1e-08, math.pi / 2 - eps - 1e-08)
    stoplb = None
    while heap and nodes < jdmax:
        lower, _, (r0, r1, t0, t1) = heapq.heappop(heap)
        if best[0] - lower <= tol:
            stoplb = lower
            break
        if lower >= best[0]:
            continue
        nodes += 1
        rm = (r0 + r1) / 2
        tm = (t0 + t1) / 2
        for rho, theta in ((rm, tm), (r1, tm), (rm, min(t1, max(t0, best[1])))):
            if rho < best[0] and rho < 1000 and (theta <= math.acos(rho / 2000) - eps):
                bound = zjsj(rho, theta)[0]
                if bound <= target - 1e-05:
                    best = (rho, theta, bound)
        if (r1 - r0) / 1000 > (t1 - t0) / (math.pi / 2):
            add(r0, rm, t0, t1)
            add(rm, r1, t0, t1)
        else:
            add(r0, r1, t0, tm)
            add(r0, r1, tm, t1)
    lower = min(
        [best[0]] + ([stoplb] if stoplb is not None else []) + [x[0] for x in heap]
    )
    rho, theta, bound = best
    a, b = (rho * math.cos(theta), rho * math.sin(theta))
    return dict(
        movement_m=rho,
        a_m=a,
        b_m=b,
        diameter_upper_m=bound,
        target_diameter_m=target,
        movement_lower_m=lower,
        movement_gap_m=rho - lower,
        nodes=nodes,
        reception_margin_m=1000
        - max(
            rho,
            max(
                (
                    math.dist((a, b), (1000 * math.cos(eps), s * 1000 * math.sin(eps)))
                    for s in (-1, 1)
                )
            ),
        ),
        scope="global_movement_bound_for_the_analytic_strip_criterion_not_exact_physical_diameter",
    )


def main():
    parser = argparse.ArgumentParser(description="前两问的离线几何计算；不连接任何接口")
    parser.add_argument(
        "input", type=lj, help="JSON：observations，或 first 与 bearing_deg"
    )
    parser.add_argument("--problem", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=lj)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    if args.problem == 1:
        result = jhqy(data["observations"], data.get("epsilon_deg", 1.005))
    else:
        design = (
            jdyh(data["movement_m"])
            if "movement_m" in data
            else zxdj(data.get("target_diameter_m", 163.0))
        )
        theta = math.radians(data["bearing_deg"])
        u = (math.cos(theta), math.sin(theta))
        v = (-u[1], u[0])
        options = [
            tuple(
                (
                    data["first"][i]
                    + design["a_m"] * u[i]
                    + sign * design["b_m"] * v[i]
                    for i in (0, 1)
                )
            )
            for sign in (1, -1)
        ]
        p = (
            min(options, key=lambda p: math.dist(p, data["current"]))
            if "current" in data
            else options[0]
        )
        result = dict(
            second_position=dict(x=p[0], y=p[1]),
            candidate_region=ecdqy(
                tuple(data["first"]), data["bearing_deg"], data.get("query")
            ),
            guaranteed_diameter_bound_m=design["diameter_upper_m"],
            optimization=design,
            selection_status="Minimum movement for the requested analytic diameter bound; certified remaining radius gap is reported"
            if "movement_m" not in data
            else "Analytic diameter bound optimized over the full feasible angle interval at the chosen movement radius",
            rule="movement_m is measured from first; nearest symmetric side if current supplied",
            scope="全向信号；首次方向有效；半径1000至1500米",
        )
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
