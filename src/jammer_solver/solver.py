from fractions import Fraction as fs
from itertools import combinations
import math
import time
from . import exact_geometry as g

qcbj = 19.8


def lxcd(start, points, end=None):
    path = [start] + list(points) + ([] if end is None else [end])
    return sum((math.dist(a, b) for a, b in zip(path, path[1:])))


def lxpx(start, points, end=None):
    if len(points) < 2:
        return list(points)
    rest = list(points)
    greedy = []
    p = start
    while rest:
        q = min(rest, key=lambda q: (math.dist(p, q), q))
        greedy.append(q)
        rest.remove(q)
        p = q
    order = min((list(points), greedy), key=lambda qs: lxcd(start, qs, end))
    for _ in range(8):
        bestdelta, bestpair = (0.0, None)
        for i in range(len(order) - 1):
            a = start if i == 0 else order[i - 1]
            for j in range(i + 1, len(order)):
                b = order[j + 1] if j + 1 < len(order) else end
                before = math.dist(a, order[i])
                after = math.dist(a, order[j])
                if b is not None:
                    before += math.dist(order[j], b)
                    after += math.dist(order[i], b)
                if after - before < bestdelta - 1e-08:
                    bestdelta, bestpair = (after - before, (i, j))
        if bestpair is None:
            break
        i, j = bestpair
        order[i : j + 1] = reversed(order[i : j + 1])
    return order


def zjqcd(polygon, current):
    if not polygon:
        return None
    radius = qcbj - 1e-06

    def feasible(p):
        return all(
            (math.hypot(p[0] - v[0], p[1] - v[1]) <= radius + 1e-10 for v in polygon)
        )

    if feasible(current):
        return current
    if any(
        (
            math.hypot(a[0] - b[0], a[1] - b[1]) > 2 * radius
            for a, b in combinations(polygon, 2)
        )
    ):
        return None
    best, zxjl = (None, float("inf"))

    def consider(p):
        nonlocal best, zxjl
        travel = math.hypot(current[0] - p[0], current[1] - p[1])
        if travel < zxjl and feasible(p):
            best, zxjl = (p, travel)

    for a in polygon:
        d = math.hypot(current[0] - a[0], current[1] - a[1])
        if d > radius:
            consider(
                (
                    a[0] + radius * (current[0] - a[0]) / d,
                    a[1] + radius * (current[1] - a[1]) / d,
                )
            )
    for a, b in combinations(polygon, 2):
        d = math.hypot(a[0] - b[0], a[1] - b[1])
        if d <= 1e-12 or d > 2 * radius:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        h = math.sqrt(max(0.0, radius * radius - d * d / 4))
        dx, dy = (-(b[1] - a[1]) / d * h, (b[0] - a[0]) / d * h)
        consider((mid[0] + dx, mid[1] + dy))
        consider((mid[0] - dx, mid[1] - dy))
    return best


def qclxyh(centers, radius, start, current, target, bsmax=24):

    def feasible(p):
        return all(
            (math.hypot(p[0] - c[0], p[1] - c[1]) <= radius + 1e-10 for c in centers)
        )

    if not centers or radius <= 0 or (not feasible(start)):
        return (start, dict(iterations=0, gap_m=None))
    corners = []
    for a, b in combinations(centers, 2):
        d = math.hypot(a[0] - b[0], a[1] - b[1])
        if d <= 1e-12 or d > 2 * radius:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        h = math.sqrt(max(0.0, radius * radius - d * d / 4))
        dx, dy = (-(b[1] - a[1]) * h / d, (b[0] - a[0]) * h / d)
        for p in ((mid[0] + dx, mid[1] + dy), (mid[0] - dx, mid[1] - dy)):
            if feasible(p):
                corners.append(p)
    point, steps, gap = (start, 0, None)
    for _ in range(bsmax):
        value = math.hypot(current[0] - point[0], current[1] - point[1]) + math.hypot(
            point[0] - target[0], point[1] - target[1]
        )
        if value - math.hypot(current[0] - target[0], current[1] - target[1]) <= 1e-07:
            gap = max(
                0.0, value - math.hypot(current[0] - target[0], current[1] - target[1])
            )
            break
        d1, d2 = (
            math.hypot(point[0] - current[0], point[1] - current[1]),
            math.hypot(point[0] - target[0], point[1] - target[1]),
        )
        if min(d1, d2) <= 1e-12:
            gap = 0.0
            break
        g = (
            (point[0] - current[0]) / d1 + (point[0] - target[0]) / d2,
            (point[1] - current[1]) / d1 + (point[1] - target[1]) / d2,
        )
        norm = math.hypot(*g)
        if norm <= 1e-12:
            gap = None
            break
        beixuan = corners + [point]
        for c in centers:
            cand = (c[0] - radius * g[0] / norm, c[1] - radius * g[1] / norm)
            if feasible(cand):
                beixuan.append(cand)
        support = min(beixuan, key=lambda p: g[0] * p[0] + g[1] * p[1])
        gap = max(0.0, g[0] * (point[0] - support[0]) + g[1] * (point[1] - support[1]))
        if gap <= 1e-05:
            break
        lo, hi = (0.0, 1.0)
        for _ in range(36):
            left, right = ((2 * lo + hi) / 3, (lo + 2 * hi) / 3)
            lp = (
                point[0] + left * (support[0] - point[0]),
                point[1] + left * (support[1] - point[1]),
            )
            rp = (
                point[0] + right * (support[0] - point[0]),
                point[1] + right * (support[1] - point[1]),
            )
            if math.hypot(current[0] - lp[0], current[1] - lp[1]) + math.hypot(
                lp[0] - target[0], lp[1] - target[1]
            ) <= math.hypot(current[0] - rp[0], current[1] - rp[1]) + math.hypot(
                rp[0] - target[0], rp[1] - target[1]
            ):
                hi = right
            else:
                lo = left
        cand = min(
            (
                point,
                support,
                (
                    point[0] + (lo + hi) / 2 * (support[0] - point[0]),
                    point[1] + (lo + hi) / 2 * (support[1] - point[1]),
                ),
            ),
            key=lambda p: (
                math.hypot(current[0] - p[0], current[1] - p[1])
                + math.hypot(p[0] - target[0], p[1] - target[1])
            ),
        )
        if not feasible(cand):
            break
        gain = value - (
            math.hypot(current[0] - cand[0], current[1] - cand[1])
            + math.hypot(cand[0] - target[0], cand[1] - target[1])
        )
        point = cand
        steps += 1
        gap = None
        if gain <= 1e-09:
            break
    return (point, dict(iterations=steps, gap_m=gap))


def zhipai(cost):
    n = len(cost)
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minimum = [float("inf")] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j] = cur
                        way[j] = j0
                    if minimum[j] < delta:
                        delta = minimum[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    succ = [0] * n
    for j in range(1, n + 1):
        succ[p[j] - 1] = j - 1
    return (sum((cost[i][j] for i, j in enumerate(succ))), succ)


def sscd(problem):
    if problem == 3:
        return [(0.0, 0.0)] + [
            (1125 * math.cos(k * math.pi / 3), 1125 * math.sin(k * math.pi / 3))
            for k in range(6)
        ]
    return (
        [(0.0, 0.0)]
        + [
            (998 * math.cos(k * math.pi / 4), 998 * math.sin(k * math.pi / 4))
            for k in range(8)
        ]
        + [
            (
                1868 * math.cos(k * math.pi / 6 + math.pi / 12),
                1868 * math.sin(k * math.pi / 6 + math.pi / 12),
            )
            for k in range(12)
        ]
    )


def pindao(jilu, status):
    return {c for c, s in jilu["channels"].items() if s["status"] in status}


def xjjl(problem, dzys=640):
    return dict(
        problem=problem,
        extra=dzys,
        coverage_nodes=20000,
        coverage_depth=14,
        channels={
            c: dict(
                status="unknown",
                radio=[],
                optical=[],
                records=[],
                pending=set(g.sswd()),
                source=None,
            )
            for c in range(1, 21)
        },
    )


def xjlx(points, seconds=0.25):
    return dict(
        points=list(points),
        seconds=seconds,
        signature=None,
        route=[],
        pending_stop=None,
    )


def xjzt(io, problem, jd=None, *, dzys=640, ghsj=0.2, qqsj=0.1):
    return dict(
        io=io,
        problem=problem,
        progress=jd,
        ledger=xjjl(problem, dzys),
        planner=dict(seconds=ghsj, problem=problem),
        request_seconds=qqsj,
        position=(0.0, 0.0),
        channel=1,
        virtual=0.0,
        travel=0.0,
        measures=0,
        clear_attempts=0,
        switches=0,
        entered=False,
        exit_confirmed=False,
        exit_attempted=False,
        completed=False,
        deadline=math.inf,
        max_virtual=360000.0,
        fallback_used=False,
        search_plan=xjlx(sscd(problem)),
    )


def qjj(poly, other):
    if len(other) < 3:
        return poly
    for a, b in zip(other, other[1:] + other[:1]):
        edge = (b[0] - a[0], b[1] - a[1])
        normal = (edge[1], -edge[0])
        poly = g.clip(poly, normal, normal[0] * a[0] + normal[1] * a[1])
        if not poly:
            break
    return poly


def xjyd(origin, bearing=None, problem=4):
    origin = g.point(origin)
    yuan = dict(
        origin=origin,
        bearing=bearing,
        points={},
        cells={},
        polygon=[],
        positives=[],
        negatives=[],
        anchor_point=origin,
        anchor_bearing=bearing or 0.0,
        anchor_radius=1500.0,
        rounds=0,
    )
    domain = g.juxing(-1800, -1800, 1800, 1800)
    if bearing is None:
        x, y = origin
        yuan["polygon"] = qjj(g.juxing(x - 5, y - 5, x + 5, y + 5), domain)
        yuan["points"] = {0: origin}
        yuan["cells"] = {0: yuan["polygon"]}
        yuan["anchor_radius"] = 5.0
    else:
        yuan["polygon"] = g.jcfw(domain, origin, fs(bearing))
        index = 0
        for row, y in enumerate((-25, 0, 25)):
            for k in range(61) if row % 2 == 0 else range(60, -1, -1):
                x = 25 * k
                bounds = (
                    max(0, x - fs(25, 2)),
                    max(-30, y - fs(25, 2)),
                    min(1500, x + fs(25, 2)),
                    min(30, y + fs(25, 2)),
                )
                cell = qjj(g.xzqj(origin, bearing, bounds), yuan["polygon"])
                q = g.xzd(origin, bearing, x, y)
                if cell:
                    if not g.ypbh(cell, q, fs(20)):
                        raise RuntimeError("Optical responsibility is not covered")
                    yuan["points"][index], yuan["cells"][index] = (q, cell)
                index += 1
    yuan["positives"].append(origin)
    if not yuan["polygon"] or not yuan["cells"]:
        raise RuntimeError("Known source lost all feasible responsibilities")
    if problem == 3:
        xdfw(yuan, qjj(yuan["polygon"], g.yfw()))
        yuan["anchor_radius"] = math.nextafter(
            max((float(g.jlsx(yuan["anchor_point"], p)) for p in yuan["polygon"])),
            math.inf,
        )
    return yuan


def xdfw(yuan, poly):
    if not poly:
        raise RuntimeError("Accepted evidence contradicts known source")
    yuan["cells"] = {i: out for i, p in yuan["cells"].items() if (out := qjj(p, poly))}
    yuan["polygon"] = poly
    if not yuan["polygon"] or not yuan["cells"]:
        raise RuntimeError("Known source lost all feasible responsibilities")


def gxyd(yuan, q, kind, bearing=None, problem=4):
    q = g.point(q)
    if kind == "direction":
        xdfw(yuan, g.jcfw(yuan["polygon"], q, fs(bearing)))
        yuan["positives"].append(q)
        yuan["anchor_point"], yuan["anchor_bearing"] = (q, bearing)
        yuan["anchor_radius"] = min(
            1500.0,
            math.nextafter(
                float(max((g.jlsx(q, v) for v in yuan["polygon"]))), math.inf
            ),
        )
        yuan["rounds"] += 1
    elif kind == "near":
        x, y = q
        xdfw(yuan, qjj(yuan["polygon"], g.juxing(x - 5, y - 5, x + 5, y + 5)))
        yuan["anchor_point"] = q
        yuan["anchor_radius"] = math.nextafter(
            float(max((g.jlsx(q, v) for v in yuan["polygon"]))), math.inf
        )
    elif kind == "no_signal":
        yuan["negatives"].append(q)
        if problem == 3:
            poly = yuan["polygon"]
            for p in yuan["positives"]:
                poly = g.clip(
                    poly,
                    (q[0] - p[0], q[1] - p[1]),
                    (q[0] * q[0] + q[1] * q[1] - (p[0] * p[0] + p[1] * p[1])) / 2,
                )
            xdfw(yuan, poly)
        yuan["cells"] = {
            i: p
            for i, p in yuan["cells"].items()
            if problem != 3 or not g.ypbh(p, q, fs(1000))
        }
        if not yuan["polygon"] or not yuan["cells"]:
            raise RuntimeError("Known source lost all feasible responsibilities")
    elif kind == "no_target_in_range":
        yuan["cells"] = {
            i: p for i, p in yuan["cells"].items() if not g.ypbh(p, q, fs(20))
        }
        if not yuan["polygon"] or not yuan["cells"]:
            raise RuntimeError("Known source lost all feasible responsibilities")
        yuan["polygon"] = g.hull((v for p in yuan["cells"].values() for v in p))


def syx(yuan, pos, a, b):
    if (
        pos not in yuan["positives"]
        or a not in yuan["negatives"]
        or b not in yuan["negatives"]
    ):
        raise RuntimeError("Pair contraction lacks its observed evidence")
    poly, changed = g.syxc(yuan["polygon"], pos, a, b)
    if changed:
        xdfw(yuan, poly)
        yuan["anchor_radius"] = min(
            yuan["anchor_radius"],
            math.nextafter(
                float(max((g.jlsx(yuan["anchor_point"], v) for v in poly))), math.inf
            ),
        )
    yuan["rounds"] += 1
    return changed


def syrw(jilu):
    return (
        sum(
            (
                len(s["pending"])
                for s in jilu["channels"].values()
                if s["status"] == "unknown"
            )
        )
        + sum(
            (
                len(s["source"]["cells"])
                for s in jilu["channels"].values()
                if s["status"] == "found"
            )
        )
        + 183 * (16 - len(pindao(jilu, ("found", "cleared"))))
        + jilu["extra"]
    )


def bjwy(jilu, c):
    s = jilu["channels"][c]
    s["status"] = "absent"
    s["pending"].clear()


def pdwy(jilu, c):
    s = jilu["channels"][c]
    if s["status"] != "unknown":
        return False
    if not s["pending"]:
        bjwy(jilu, c)
        return True
    if len(s["radio"]) < (6 if jilu["problem"] == 3 else 7) and (not s["optical"]):
        return False
    covered = g.fgpd(
        tuple(sorted(set(s["radio"]))),
        tuple(sorted(set(s["optical"]))),
        jilu["problem"],
        jilu["coverage_nodes"],
        jilu["coverage_depth"],
    )
    if covered:
        bjwy(jilu, c)
    return covered


def gxjl(jilu, path, q, c, huifu, pd=True):
    before = syrw(jilu)
    q = g.point(q)
    s = jilu["channels"][c]
    if s["status"] in ("cleared", "absent"):
        raise RuntimeError("Action targets a resolved channel")
    kind = huifu["measure_result" if path == "/measure" else "clear_result"]
    s["records"].append(
        dict(
            path=path,
            point=tuple((float(x) for x in q)),
            kind=kind,
            bearing=huifu.get("svd_deg"),
        )
    )
    if path == "/measure":
        if s["status"] == "unknown":
            if kind == "no_signal":
                s["radio"].append(q)
                s["pending"].discard(q)
                if pd:
                    pdwy(jilu, c)
            else:
                s["status"] = "found"
                s["pending"].clear()
                s["source"] = xjyd(
                    q,
                    huifu["svd_deg"] if kind == "direction" else None,
                    jilu["problem"],
                )
        elif kind == "direction":
            gxyd(s["source"], q, "direction", bearing=huifu["svd_deg"])
        elif kind == "near":
            gxyd(s["source"], q, "near")
        else:
            gxyd(s["source"], q, "no_signal", problem=jilu["problem"])
    elif kind == "success":
        s["status"] = "cleared"
        s["pending"].clear()
        s["source"] = None
    elif s["status"] == "unknown":
        s["optical"].append(q)
        if pd:
            pdwy(jilu, c)
    else:
        gxyd(s["source"], q, "no_target_in_range")
    if len(pindao(jilu, ("found", "cleared"))) > 16:
        raise RuntimeError("More than 16 distinct sources")
    if len(pindao(jilu, ("found", "cleared"))) == 16:
        for other in sorted(pindao(jilu, ("unknown",))):
            bjwy(jilu, other)
    if syrw(jilu) >= before:
        if jilu["extra"] <= 0:
            raise RuntimeError("An unproductive action had no reserved allowance")
        jilu["extra"] -= 1


def qbqc(jilu):
    return (
        not pindao(jilu, ("unknown",))
        and (not pindao(jilu, ("found",)))
        and (10 <= len(pindao(jilu, ("cleared",))) <= 16)
    )


def sysj(jilu, weizhi):
    p = g.point(weizhi)
    parts = [
        lxsj(gxpx(jilu["channels"][c]["source"], p), p, p)
        for c in pindao(jilu, ("found",))
    ]
    points = set(
        (q for c in pindao(jilu, ("unknown",)) for q in jilu["channels"][c]["pending"])
    )
    prev = p
    for q in g.sswd():
        if q in points:
            parts.append(math.nextafter(float(g.jlsx(prev, q) / 5), math.inf))
            prev = q
    requests = sum(
        (len(jilu["channels"][c]["pending"]) for c in pindao(jilu, ("unknown",)))
    )
    parts.append(6 * requests)
    parts.append(
        math.nextafter(
            1843.1
            * min(
                16 - len(pindao(jilu, ("found", "cleared"))),
                len(pindao(jilu, ("unknown",))),
            ),
            math.inf,
        )
    )
    return math.nextafter(math.fsum(parts), math.inf)


def lxqc(yuan, dq, target=None):
    polygon = [tuple((float(x) for x in p)) for p in yuan["polygon"]]
    cand = zjqcd(polygon, dq)
    if cand is None:
        return None
    options = [cand]
    if target is not None:
        q, _ = qclxyh(polygon, 19.8 - 1e-06, cand, dq, target)
        options.append(q)
    valid = [
        g.point(q) for q in options if g.ypbh(yuan["polygon"], g.point(q), fs("19.8"))
    ]
    if not valid:
        return None
    return min(
        valid,
        key=lambda q: (
            math.dist(dq, tuple((float(x) for x in q)))
            + (
                math.dist(tuple((float(x) for x in q)), target)
                if target is not None
                else 0
            )
        ),
    )


def gxpx(yuan, dq, mode="snake", cells=None):
    ids = set(yuan["cells"] if cells is None else cells)
    if mode == "snake":
        return [yuan["points"][i] for i in sorted(ids)]
    order = []
    p = g.point(dq)
    while ids:
        i = min(
            ids,
            key=lambda i: (
                (p[0] - yuan["points"][i][0]) * (p[0] - yuan["points"][i][0])
                + (p[1] - yuan["points"][i][1]) * (p[1] - yuan["points"][i][1]),
                i,
            ),
        )
        ids.remove(i)
        p = yuan["points"][i]
        order.append(p)
    return order


def lxsj(points, dq, target=None):
    p = g.point(dq)
    spent = fs(0)
    worst = fs(0)
    for q in points:
        spent += g.jlsx(p, q) / 5
        leave = g.jlsx(q, g.point(target)) / 5 if target is not None else 0
        worst = max(worst, spent + 5 + leave)
        spent += 3
        p = q
    return math.nextafter(float(worst), math.inf)


def xuduan(yuan, dq, cells=None):
    return min(
        (
            (lxsj(order, dq), mode, order)
            for mode in ("snake", "nearest")
            if (order := gxpx(yuan, dq, mode, cells))
        )
    )


def sdc(yuan, dq, ratio=0.5):
    length = fs(yuan["anchor_radius"])
    x = 5 + (length - 5) * fs(ratio)
    side = length / 50
    if len(yuan["positives"]) >= 2:
        u, _ = g.fangxiang(fs(yuan["anchor_bearing"]))
        dist = [
            (q[0] - yuan["anchor_point"][0]) * u[0]
            + (q[1] - yuan["anchor_point"][1]) * u[1]
            for q in yuan["polygon"]
        ]
        lo, hi = (min(dist), max(dist))
        x = (lo + hi) / 2
        side = max(fs(5), (hi - lo) / 20)
    points = [
        g.xzd(yuan["anchor_point"], yuan["anchor_bearing"], x, sign * side)
        for sign in (-1, 1)
    ]
    return tuple(
        sorted(
            points,
            key=lambda q: (
                (q[0] - g.point(dq)[0]) * (q[0] - g.point(dq)[0])
                + (q[1] - g.point(dq)[1]) * (q[1] - g.point(dq)[1])
            ),
        )
    )


def kdqy(yuan, polygon):
    if not polygon:
        return []
    return [i for i, cell in yuan["cells"].items() if qjj(cell, polygon)]


def sptz(yuan, dq, pair, problem, dl):
    a, b = pair
    start = float(g.jlsx(g.point(dq), a) / 5) + 6
    ceshi = [(a, start)]
    if problem == 4:
        ceshi.append((b, start + float(g.jlsx(a, b) / 5) + 5))
    worst = 0.0
    paths = 0
    for q, prefix in ceshi:
        for lo in range(0, 360, 60):
            if time.perf_counter() >= dl:
                return None
            region = g.jcfw(yuan["polygon"], q, fs(lo), hi=fs(lo + 60))
            ids = kdqy(yuan, region)
            if ids:
                upper, _, _ = xuduan(yuan, q, ids)
                worst = max(worst, prefix + upper)
                paths += 1
        worst = max(worst, prefix + 5)
        paths += 1
    if problem == 3:
        if not g.ypbh(yuan["polygon"], a, fs(1000)):
            worst = max(worst, start + xuduan(yuan, a)[0])
            paths += 1
    else:
        prefix = ceshi[-1][1]
        region, _ = g.syxc(yuan["polygon"], yuan["anchor_point"], a, b)
        ids = kdqy(yuan, region)
        if ids:
            worst = max(worst, prefix + xuduan(yuan, b, ids)[0])
            paths += 1
    return (worst, paths)


def gxjs(source):
    values = []
    for poly in source["cells"].values():
        points = [tuple((float(x) for x in p)) for p in poly]
        center = tuple((sum((p[k] for p in points)) / len(points) for k in (0, 1)))
        area = (
            abs(
                sum(
                    (
                        a[0] * b[1] - a[1] * b[0]
                        for a, b in zip(points, points[1:] + points[:1])
                    )
                )
            )
            / 2
        )
        values.append((center, area))
    zl = sum((w for _, w in values))
    return [(p, w / zl if zl > 1e-12 else 1 / len(values)) for p, w in values]


def gxjz(order, wz, worlds, target=None):
    elapsed = 0.0
    prev = wz
    rest = set(range(len(worlds)))
    mean = 0.0
    xout = yout = 0.0
    for q in order:
        q = tuple((float(x) for x in q))
        elapsed += math.dist(prev, q) / 5
        hits = [i for i in rest if math.dist(worlds[i][0], q) <= 20]
        for i in hits:
            mean += worlds[i][1] * (
                elapsed + 5 + (math.dist(q, target) / 5 if target is not None else 0)
            )
            xout += worlds[i][1] * q[0]
            yout += worlds[i][1] * q[1]
            rest.remove(i)
        prev = q
        elapsed += 3
    return (math.inf if rest else mean, (xout, yout))


def gxbx(source, wz, target=None):
    poly = source["polygon"]
    points = [tuple((float(x) for x in p)) for p in poly]
    angle = math.radians(source["anchor_bearing"])
    result = []
    worlds = None
    for theta in (angle, angle + math.pi / 2):
        u = (math.cos(theta), math.sin(theta))
        w = (-u[1], u[0])
        xs = [p[0] * u[0] + p[1] * u[1] for p in points]
        ys = [p[0] * w[0] + p[1] * w[1] for p in points]
        lo, hi = (min(xs) - 1e-06, max(xs) + 1e-06)
        mid = (min(ys) + max(ys)) / 2
        halfwidth = (max(ys) - min(ys)) / 2 + 1e-06
        if halfwidth >= 19.79:
            continue
        half = math.sqrt(19.79**2 - halfwidth**2)
        n = max(1, math.ceil((hi - lo) / (2 * half)))
        if not 2 <= n <= 8:
            continue
        centers = [lo + half + (hi - lo - 2 * half) * i / (n - 1) for i in range(n)]
        chain = [
            g.point((x * u[0] + mid * w[0], x * u[1] + mid * w[1])) for x in centers
        ]
        valid = True
        for q in chain:
            part = poly
            for other in chain:
                if q != other:
                    part = g.clip(
                        part,
                        (other[0] - q[0], other[1] - q[1]),
                        (
                            other[0] * other[0]
                            + other[1] * other[1]
                            - (q[0] * q[0] + q[1] * q[1])
                        )
                        / 2,
                    )
            if part and (not g.ypbh(part, q, fs("19.8"))):
                valid = False
                break
        if not valid:
            continue
        if worlds is None:
            worlds = gxjs(source)
        greedy = []
        left = list(chain)
        now = wz
        rest = set(range(len(worlds)))
        while left:
            q = min(
                left,
                key=lambda p: (
                    -sum(
                        (
                            worlds[i][1]
                            for i in rest
                            if math.dist(worlds[i][0], tuple((float(x) for x in p)))
                            <= 20
                        )
                    )
                    / (3 + math.dist(now, tuple((float(x) for x in p))) / 5),
                    (g.point(now)[0] - p[0]) * (g.point(now)[0] - p[0])
                    + (g.point(now)[1] - p[1]) * (g.point(now)[1] - p[1]),
                ),
            )
            greedy.append(q)
            left.remove(q)
            now = tuple((float(x) for x in q))
            rest = {i for i in rest if math.dist(worlds[i][0], now) > 20}
        for order in dict.fromkeys(
            (tuple(chain), tuple(reversed(chain)), tuple(greedy))
        ):
            mean, leave = gxjz(order, wz, worlds, target)
            if math.isfinite(mean):
                result.append((mean, order, leave, lxsj(order, wz, target)))
    return result


def gxxz(jihua, yuan, channel, wz, tuned, extra, event, target):
    if jihua["problem"] != 4 or event["method"] == "verified_continuous" or extra < 8:
        return event
    options = gxbx(yuan, wz, target)
    if not options:
        return event
    worlds = gxjs(yuan)
    q = tuple((float(x) for x in event["points"][0]))
    ideal = math.dist(wz, q) / 5 + 5 + (channel != tuned) + 5
    ideal += sum(
        (
            weight
            * (
                max(0, math.dist(q, source) - 19.8) / 5
                + (
                    max(0, math.dist(source, target) - 19.8) / 5
                    if target is not None
                    else 0
                )
            )
            for source, weight in worlds
        )
    )
    mean, order, leave, upper = min(options, key=lambda option: option[0])
    if mean < ideal:
        return dict(
            kind="optical_chain",
            channel=channel,
            points=order,
            estimate=mean,
            method="complete_cover_expected_first_success",
        )
    return event


def yddz(jihua, yuan, channel, dq, tuned, extra, target=None):
    q = lxqc(yuan, dq, target)
    if q is not None:
        return {
            "kind": "clear",
            "channel": channel,
            "points": (q,),
            "estimate": math.dist(dq, tuple((float(x) for x in q))) / 5 + 5,
            "method": "verified_continuous",
        }
    upper, mode, order = xuduan(yuan, dq)
    best = {
        "kind": "clear",
        "channel": channel,
        "points": (order[0],),
        "estimate": upper,
        "method": "complete_optical_" + mode,
    }
    if extra < 2 or yuan["anchor_radius"] <= 5 or yuan["rounds"] >= 12:
        return gxxz(jihua, yuan, channel, dq, tuned, extra, best, target)
    dl = time.perf_counter() + jihua["seconds"]
    for ratio in (0.5, 0.38, 0.62):
        pair = sdc(yuan, dq, ratio)
        jieguo = sptz(yuan, dq, pair, jihua["problem"], dl)
        if jieguo is None:
            break
        value, paths = jieguo
        if value < best["estimate"]:
            best = {
                "kind": "radio",
                "channel": channel,
                "points": pair,
                "estimate": value,
                "method": f"interval_rollout_{ratio:g}_{paths}_branches",
            }
    if best["kind"] == "clear" and len(yuan["cells"]) > 4:
        pair = sdc(yuan, dq)
        best = {
            "kind": "radio",
            "channel": channel,
            "points": pair,
            "estimate": best["estimate"],
            "method": "annular_proposal_with_guard",
        }
    best = bmcf(jihua, yuan, dq, best)
    best = gxxz(jihua, yuan, channel, dq, tuned, extra, best, target)
    return best


def bmcf(jihua, yuan, wz, event):
    if jihua["problem"] != 4 or event["kind"] != "radio":
        return event
    if not all((q in yuan["negatives"] for q in event["points"])):
        return event
    upper, _, order = xuduan(yuan, wz)
    return dict(
        event,
        kind="clear",
        points=(order[0],),
        estimate=upper,
        method="avoid_repeated_negative_pair",
    )


def pgsx(tu, order):
    if not order:
        return (0.0, [])
    costs = {i: (tu["start"][i], [i]) for i in tu["ids"][order[0]]}
    for job in order[1:]:
        costs = {
            j: min(
                (
                    (value + tu["edge"][i, j], path + [j])
                    for i, (value, path) in costs.items()
                )
            )
            for j in tu["ids"][job]
        }
    value, path = min(costs.values())
    return (value, [tu["modes"][i] for i in path])


def fpsx(tu):
    jobs = list(tu["ids"])
    n = len(jobs)
    cost = [[1000000000000.0] * (n + 1) for _ in range(n + 1)]
    for j, job in enumerate(jobs, 1):
        cost[0][j] = min((tu["start"][k] for k in tu["ids"][job]))
    for i, a in enumerate(jobs, 1):
        cost[i][0] = 0.0
        for j, b in enumerate(jobs, 1):
            if i != j:
                cost[i][j] = min(
                    (tu["edge"][x, y] for x in tu["ids"][a] for y in tu["ids"][b])
                )
    _, succ = zhipai(cost)

    def cycle(start):
        out = [start]
        q = succ[start]
        while q != start:
            out.append(q)
            q = succ[q]
        return out

    main = cycle(0)
    while len(main) < n + 1:
        other = cycle(next((i for i in range(n + 1) if i not in main)))
        a, b = min(
            ((a, b) for a in main for b in other),
            key=lambda ab: (
                cost[ab[0]][succ[ab[1]]]
                + cost[ab[1]][succ[ab[0]]]
                - cost[ab[0]][succ[ab[0]]]
                - cost[ab[1]][succ[ab[1]]]
            ),
        )
        succ[a], succ[b] = (succ[b], succ[a])
        main = cycle(0)
    return [jobs[i - 1] for i in main[1:]]


def aprw(jobs, wz, oldorder=()):
    modes = [m for opts in jobs.values() for m in opts]
    tu = dict(
        modes=modes,
        ids={job: [i for i, m in enumerate(modes) if m["job"] == job] for job in jobs},
        edge={
            (i, j): math.dist(a["exit"], b["entry"]) / 5 + b["service"]
            for i, a in enumerate(modes)
            for j, b in enumerate(modes)
            if a["job"] != b["job"]
        },
        start={
            i: math.dist(wz, m["entry"]) / 5 + m["service"] for i, m in enumerate(modes)
        },
    )
    old = [job for job in oldorder if job in jobs]
    old += [job for job in jobs if job not in old]
    rest = list(jobs)
    greedy = []
    last = None
    while rest:
        job = min(
            rest,
            key=lambda job: min(
                (
                    tu["start"][i] if last is None else tu["edge"][last, i]
                    for i in tu["ids"][job]
                )
            ),
        )
        last = min(
            tu["ids"][job],
            key=lambda i: tu["start"][i] if last is None else tu["edge"][last, i],
        )
        greedy.append(job)
        rest.remove(job)
    scans = [job for job in jobs if job[0] == "scan"]
    sources = [job for job in jobs if job[0] == "source"]
    seeds = [old, greedy, sources + scans, scans + sources, fpsx(tu)]
    scores = []
    for seed in seeds:
        value, opts = pgsx(tu, seed)
        scores.append((value, seed, opts))
    value, order, opts = min(scores, key=lambda e: e[0])
    index = {id(m): i for i, m in enumerate(modes)}
    for _ in range(2):
        before = value
        trials = []
        chosen = {m["job"]: index[id(m)] for m in opts}
        for i in range(len(order)):
            for j in range(len(order)):
                if i == j:
                    continue
                trial = list(order)
                item = trial.pop(i)
                trial.insert(j, item)
                seq = [chosen[job] for job in trial]
                score = tu["start"][seq[0]] + sum(
                    (tu["edge"][a, b] for a, b in zip(seq, seq[1:]))
                )
                if score < value - 1e-07:
                    trials.append((score, trial))
        for _, trial in sorted(trials, key=lambda x: x[0])[:16]:
            cand, plan = pgsx(tu, trial)
            if cand < value - 1e-07:
                value, order, opts = (cand, trial, plan)
        if value >= before - 1e-07:
            break
    return dict(estimate=value, order=order, modes=opts)


def xzdz(jihua, jilu, dq, tuned, sscd):
    jobs = {}
    for c in sorted(pindao(jilu, ("found",))):
        yuan = jilu["channels"][c]["source"]
        job = ("source", c)
        direct = lxqc(yuan, dq)
        if direct is not None:
            q = tuple((float(x) for x in direct))
            event = dict(
                kind="clear",
                channel=c,
                points=(direct,),
                estimate=5.0,
                method="service_direct_clear",
            )
            modes = [dict(job=job, entry=q, service=5.0, exit=q, event=event)]
        else:
            center = tuple(
                (
                    sum((float(q[k]) for q in yuan["polygon"])) / len(yuan["polygon"])
                    for k in (0, 1)
                )
            )
            modes = []
            for ratio in (0.38, 0.5, 0.62):
                pair = sdc(yuan, dq, ratio)
                for order in (pair, pair[::-1]) if jilu["problem"] == 4 else (pair,):
                    q = tuple((float(x) for x in order[0]))
                    cost = math.dist(q, center) / 5 + 15.0
                    event = dict(
                        kind="radio",
                        channel=c,
                        points=order,
                        estimate=cost,
                        method="service_entry_exit",
                    )
                    modes.append(
                        dict(job=job, entry=q, service=cost, exit=center, event=event)
                    )
        jobs[job] = modes
    for q in sscd:
        todo = [
            c
            for c in pindao(jilu, ("unknown",))
            if g.point(q) not in jilu["channels"][c]["radio"]
        ]
        if todo:
            job = ("scan", tuple(q))
            event = dict(
                kind="search",
                channel=min(todo, key=lambda c: (c != tuned, c)),
                points=(g.point(q),),
                estimate=6 * len(todo),
                method="service_search",
            )
            jobs[job] = [
                dict(job=job, entry=q, service=event["estimate"], exit=q, event=event)
            ]
    if not jobs:
        return None
    plan = aprw(jobs, dq, jihua.get("order", ()))
    jihua["order"] = plan["order"]
    event = plan["modes"][0]["event"]
    event["target"] = plan["modes"][1]["entry"] if len(plan["modes"]) > 1 else None
    if event["kind"] != "search":
        event = bmcf(jihua, jilu["channels"][event["channel"]]["source"], dq, event)
    return event


def gxlx(luxian, jilu, dq):
    if not pindao(jilu, ("unknown",)):
        return []
    common = set.intersection(
        *(set(jilu["channels"][c]["radio"]) for c in pindao(jilu, ("unknown",)))
    )
    sycd = [q for q in luxian["points"] if g.point(q) not in common]
    sig = (
        tuple(sorted(common)),
        tuple(sorted(pindao(jilu, ("unknown",)))),
        luxian["pending_stop"],
    )
    route = lxpx(dq, sycd)
    if sig == luxian["signature"]:
        return route
    luxian["signature"] = sig
    dl = time.perf_counter() + luxian["seconds"]

    def cost(qs):
        return lxcd(dq, qs) / 5 + 6 * len(pindao(jilu, ("unknown",))) * len(qs)

    for _ in range(3):
        old = cost(route)
        options = []
        for q in route:
            rest = [p for p in route if p != q]
            trial = lxpx(dq, rest)
            options.append((cost(trial), "delete", q, trial))
            if (
                luxian["pending_stop"] is not None
                and luxian["pending_stop"] not in rest
                and (g.point(luxian["pending_stop"]) not in common)
            ):
                trial = lxpx(dq, rest + [luxian["pending_stop"]])
                options.append((cost(trial), "replace", q, trial))
        improved = False
        for value, kind, removed, trial in sorted(options):
            if value >= old - 1e-06 or time.perf_counter() >= dl:
                break
            points = tuple(sorted(common | {g.point(q) for q in trial}))
            covered = g.fgpd(
                points,
                (),
                jilu["problem"],
                jilu["coverage_nodes"],
                jilu["coverage_depth"],
            )
            if covered:
                route = trial
                improved = True
                break
        if not improved:
            break
    luxian["points"] = route
    luxian["route"] = route
    luxian["pending_stop"] = None
    luxian["signature"] = (
        tuple(sorted(common)),
        tuple(sorted(pindao(jilu, ("unknown",)))),
        None,
    )
    return route


def bcsj(zt, event, **fields):
    data = dict(event=event, virtual_time_s=zt["virtual"], **fields)
    zt["io"]["record"](data)
    if zt["progress"]:
        zt["progress"](data)


def sycs(zt):
    l = zt["ledger"]
    return (
        sum((len(l["channels"][c]["pending"]) for c in pindao(l, ("unknown",))))
        + sum((len(l["channels"][c]["source"]["cells"]) for c in pindao(l, ("found",))))
        + 183
        * min(16 - len(pindao(l, ("found", "cleared"))), len(pindao(l, ("unknown",))))
        + 2
    )


def ysjc(zt, points):
    jilu = zt["ledger"]
    upper = sysj(jilu, zt["position"])
    p = zt["position"]
    dist = 0.0
    for q in points:
        dist += float(g.jlsx(g.point(p), g.point(q)))
        p = tuple((float(x) for x in q))
    m = min(16, len(pindao(jilu, ("found",))) + len(points))
    virtualok = (
        zt["virtual"] + upper + (2 * m + 2) * dist / 5 + 6 * len(points)
        < zt["max_virtual"] - 2
    )
    realok = (
        time.monotonic() + (sycs(zt) + len(points)) * zt["request_seconds"] + 30
        < zt["deadline"]
    )
    return virtualok and realok


def zhixing(zt, path, q, c, *, pd=True):
    jiekou = zt["io"]
    jilu = zt["ledger"]
    q = tuple((float(x) for x in g.point(q)))
    if jiekou["pending"] is not None:
        raise RuntimeError("Earlier request unresolved")
    if time.monotonic() >= zt["deadline"] - 2:
        raise TimeoutError("Real deadline reserve reached without completion")
    moved = math.dist(zt["position"], q)
    if zt["virtual"] + moved / 5 + 6 >= zt["max_virtual"] - 1:
        raise RuntimeError("Physical action exceeds virtual budget")
    sw = int(path == "/measure" and c != zt["channel"])
    huifu = jiekou["call"](path, q, c)
    zt["position"] = q
    zt["virtual"] = huifu["virtual_time_s"]
    zt["travel"] += moved
    if path == "/measure":
        zt["measures"] += 1
        zt["switches"] += sw
        zt["channel"] = c
    else:
        zt["clear_attempts"] += 1
    found = c in pindao(jilu, ("found", "cleared"))
    gxjl(jilu, path, q, c, huifu, pd=pd)
    if not found and c in pindao(jilu, ("found", "cleared")):
        bcsj(zt, "discovered", channel=c)
    if path == "/clear" and huifu["clear_result"] == "success":
        zt["search_plan"]["pending_stop"] = tuple(q)
        bcsj(zt, "cleared", channel=c, cleared_count=len(pindao(jilu, ("cleared",))))
    return huifu


def fxjd(p, q):
    if p[0] == q[0] and p[1] == q[1]:
        return [(0.0, 360.0)]
    angle = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    lo = (angle - 90) % 360
    return [(lo, min(360, lo + 180))] + ([(0, lo - 180)] if lo > 180 else [])


def jdjj(a, b):
    return [(max(x, u), min(y, w)) for x, y in a for u, w in b if max(x, u) < min(y, w)]


def jdcj(a, b):
    for lo, hi in b:
        a = [
            piece
            for x, y in a
            for piece in ((x, min(y, lo)), (max(x, hi), y))
            if piece[0] < piece[1]
        ]
    return a


def jdcd(spans):
    return sum((y - x for x, y in spans))


def spmx(record):
    src = record["source"]
    pos = []
    neg = []
    for obs in record["records"]:
        if obs["path"] != "/measure":
            continue
        (neg if obs["kind"] == "no_signal" else pos).append(obs["point"])
    zl = 0.0
    jiashuo = []
    for poly in src["cells"].values():
        points = [tuple((float(x) for x in q)) for q in poly]
        p = tuple((sum((q[k] for q in points)) / len(points) for k in (0, 1)))
        area = (
            abs(
                sum(
                    (
                        a[0] * b[1] - a[1] * b[0]
                        for a, b in zip(points, points[1:] + points[:1])
                    )
                )
            )
            / 2
        )
        lower = max([1000] + [math.dist(p, q) for q in pos])
        upper = 1500.0
        if lower >= upper or area <= 1e-12:
            continue
        valid = [(0.0, 360.0)]
        for q in pos:
            valid = jdjj(valid, fxjd(p, q))
        negs = [(math.dist(p, q), q) for q in neg]
        radii = sorted({lower, upper} | {d for d, q in negs if lower < d < upper})
        for lo, hi in zip(radii, radii[1:]):
            allowed = valid
            omni = True
            for d, q in negs:
                if d < (lo + hi) / 2:
                    allowed = jdcj(allowed, fxjd(p, q))
                    omni = False
            mass = area * (hi - lo) * (0.5 * omni + 0.5 * jdcd(allowed) / 360)
            if mass > 0:
                zl += mass
                jiashuo.append((p, lo, hi, allowed, omni, area))
    return (jiashuo, zl)


def spgl(fitted, q):
    jiashuo, zl = fitted
    if zl <= 0:
        return 0.5
    kejian = 0.0
    for p, lo, hi, allowed, omni, area in jiashuo:
        width = max(0, hi - max(lo, math.dist(p, q)))
        if width:
            kejian += (
                area
                * width
                * (0.5 * omni + 0.5 * jdcd(jdjj(allowed, fxjd(p, q))) / 360)
            )
    return min(1, max(0, kejian / zl))


def slcl(zt):
    jilu = zt["ledger"]
    wz = zt["position"]
    beixuan = []
    for c in sorted(pindao(jilu, ("found",))):
        yuan = jilu["channels"][c]["source"]
        tries = len(yuan["positives"]) + (
            len(yuan["negatives"]) if jilu["problem"] == 3 else 0
        )
        if tries >= 3 or g.point(wz) in yuan["positives"] + yuan["negatives"]:
            continue
        poly = [tuple((float(x) for x in p)) for p in yuan["polygon"]]
        center = tuple((sum((p[k] for p in poly)) / len(poly) for k in (0, 1)))
        if jilu["problem"] == 3:
            if math.dist(wz, center) > 1000:
                continue
        elif not g.ypbh(yuan["polygon"], g.point(wz), fs(999)):
            continue
        angle = math.radians(yuan["anchor_bearing"])
        u = (math.cos(angle), math.sin(angle))
        origin = tuple((float(x) for x in yuan["anchor_point"]))
        span = [(p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1] for p in poly]
        width = max(span) - min(span)
        ray = (center[0] - wz[0], center[1] - wz[1])
        dist = math.hypot(*ray)
        parallax = abs(u[0] * ray[1] - u[1] * ray[0]) / max(1.0, dist)
        after = min(width, 2 * math.radians(1.005) * dist / max(0.01, parallax))
        recv = spgl(spmx(jilu["channels"][c]), wz) if jilu["problem"] == 4 else 1
        gain = recv * (width - after) / 10 - 6
        if parallax >= 0.25 and gain > 0:
            beixuan.append((-gain, c))
    for score, c in sorted(beixuan):
        if jilu["extra"] < 2 or not ysjc(zt, (wz,)):
            return False
        zhixing(zt, "/measure", wz, c)
    return True


def plcl(zt, unknown):
    jilu = zt["ledger"]
    pd = [
        c
        for c in sorted(unknown & pindao(jilu, ("found",)))
        if len(jilu["channels"][c]["source"]["positives"]) == 1
    ]
    if len(pd) < 3 or jilu["extra"] < len(pd) + 2:
        return True
    wz = zt["position"]
    sources = []
    for c in pd:
        yuan = jilu["channels"][c]["source"]
        poly = [tuple((float(x) for x in p)) for p in yuan["polygon"]]
        center = tuple((sum((p[k] for p in poly)) / len(poly) for k in (0, 1)))
        angle = math.radians(yuan["anchor_bearing"])
        u = (math.cos(angle), math.sin(angle))
        origin = tuple((float(x) for x in yuan["anchor_point"]))
        span = [(p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1] for p in poly]
        sources.append((center, u, max(span) - min(span)))
    targets = [
        tuple(
            (
                sum((float(p[k]) for p in jilu["channels"][c]["source"]["polygon"]))
                / len(jilu["channels"][c]["source"]["polygon"])
                for k in (0, 1)
            )
        )
        for c in pindao(jilu, ("found",))
    ]
    target = min(targets, key=lambda q: math.dist(wz, q))
    fitted = (
        [spmx(jilu["channels"][c]) for c in pd]
        if jilu["problem"] == 4
        else [None] * len(pd)
    )
    radius = 350
    options = []
    for angle in range(0, 360, 30):
        q = (
            wz[0] + radius * math.cos(math.radians(angle)),
            wz[1] + radius * math.sin(math.radians(angle)),
        )
        gain = 0.0
        chosen = []
        for c, fit, (center, u, width) in zip(pd, fitted, sources):
            ray = (center[0] - q[0], center[1] - q[1])
            dist = math.hypot(*ray)
            parallax = abs(u[0] * ray[1] - u[1] * ray[0]) / max(1.0, dist)
            postwidth = min(width, 2 * math.radians(1.005) * dist / max(0.01, parallax))
            benefit = (width - postwidth) / 10.0
            if jilu["problem"] == 4:
                benefit = spgl(fit, q) * benefit - 6
            if jilu["problem"] == 3 or benefit > 0:
                gain += benefit
                chosen.append(c)
        detour = (radius + math.dist(q, target) - math.dist(wz, target)) / 5.0
        options.append((detour - gain, angle, q, gain, detour, chosen))
    score, angle, q, gain, detour, pd = min(options)
    if jilu["problem"] == 4 and (score >= 0 or not pd):
        return True
    for c in pd:
        if jilu["extra"] < 2 or not ysjc(zt, (q,)):
            return False
        zhixing(zt, "/measure", q, c)
    return True


def zxsj(zt, event):
    jilu = zt["ledger"]
    unknown = pindao(jilu, ("unknown",))
    if not zx(zt, event):
        return False
    if event["kind"] == "search":
        return plcl(zt, unknown) and slcl(zt)
    c = event["channel"]
    while c in pindao(jilu, ("found",)):
        if jilu["extra"] < 2:
            return False
        next = yddz(
            zt["planner"],
            jilu["channels"][c]["source"],
            c,
            zt["position"],
            zt["channel"],
            jilu["extra"],
            event.get("target"),
        )
        if not ysjc(zt, next["points"]) or not zx(zt, next):
            return False
    return slcl(zt)


def zx(zt, event):
    jilu = zt["ledger"]
    if event["kind"] == "optical_chain":
        if jilu["extra"] < len(event["points"]) or not ysjc(zt, event["points"]):
            return False
        for q in event["points"]:
            if event["channel"] not in pindao(jilu, ("found",)):
                return True
            zhixing(zt, "/clear", q, event["channel"])
        if event["channel"] in pindao(jilu, ("found",)):
            raise RuntimeError("Optical route exhausted without clearing the source")
        return True
    if event["kind"] == "search":
        q = event["points"][0]
        for c in sorted(
            pindao(jilu, ("unknown",)), key=lambda c: (c != zt["channel"], c)
        ):
            if c not in pindao(jilu, ("unknown",)) or q in jilu["channels"][c]["radio"]:
                continue
            if jilu["extra"] < 1 or not ysjc(zt, (q,)):
                return False
            zhixing(zt, "/measure", q, c)
        return True
    if event["kind"] == "clear":
        zhixing(zt, "/clear", event["points"][0], event["channel"])
        return True
    yuan = jilu["channels"][event["channel"]]["source"]
    pos = yuan["anchor_point"]
    a, b = event["points"]
    first = zhixing(zt, "/measure", a, event["channel"])
    if first["measure_result"] == "no_signal" and zt["problem"] == 4:
        second = zhixing(zt, "/measure", b, event["channel"])
        if second["measure_result"] == "no_signal":
            syx(yuan, pos, a, b)
    return True


def dzqcy(zt, c):
    jilu = zt["ledger"]
    yuan = jilu["channels"][c]["source"]
    order = [(i, yuan["points"][i]) for i in sorted(yuan["cells"])]
    for i, q in order:
        if c not in pindao(jilu, ("found",)):
            return
        if i in yuan["cells"]:
            zhixing(zt, "/clear", q, c, pd=False)
    if c in pindao(jilu, ("found",)):
        raise RuntimeError("Constructive optical cover exhausted without success")


def byqc(zt):
    jilu = zt["ledger"]
    zt["fallback_used"] = True
    upper = sysj(jilu, zt["position"])
    if zt["virtual"] + upper >= zt["max_virtual"] - 1:
        raise RuntimeError("Remaining virtual time is insufficient")
    origin = zt["position"]
    known = sorted(
        pindao(jilu, ("found",)),
        key=lambda c: lxsj(gxpx(jilu["channels"][c]["source"], origin), origin, origin),
    )
    for c in known:
        dzqcy(zt, c)
    for q in g.sswd():
        for c in sorted(
            pindao(jilu, ("unknown",)), key=lambda c: (c != zt["channel"], c)
        ):
            if (
                c not in pindao(jilu, ("unknown",))
                or q not in jilu["channels"][c]["pending"]
            ):
                continue
            zhixing(zt, "/measure", q, c, pd=False)
            if c in pindao(jilu, ("found",)):
                dzqcy(zt, c)
        if qbqc(jilu):
            break
    for c in sorted(pindao(jilu, ("unknown",))):
        pdwy(jilu, c)
    if not qbqc(jilu):
        raise RuntimeError(
            "Full fallback exhausted without a valid 10–16 source completion"
        )


def yunxing(zt):
    jiekou = zt["io"]
    jilu = zt["ledger"]
    huifu = jiekou["call"]("/enter")
    zt["entered"] = True
    zt["virtual"] = huifu["virtual_time_s"]
    zt["max_virtual"] = huifu["max_virtual_duration_s"]
    zt["deadline"] = time.monotonic() + huifu["remaining_real_duration_s"]
    jiekou["deadline"] = zt["deadline"]
    while not qbqc(jilu):
        if jilu["extra"] < 2:
            byqc(zt)
            break
        if time.monotonic() + sycs(zt) * zt["request_seconds"] + 30 >= zt["deadline"]:
            byqc(zt)
            break
        sslx = gxlx(zt["search_plan"], jilu, zt["position"])
        event = xzdz(zt["planner"], jilu, zt["position"], zt["channel"], sslx)
        if event is None or not ysjc(zt, event["points"]):
            byqc(zt)
            break
        if not zxsj(zt, event):
            byqc(zt)
            break
    zt["completed"] = qbqc(jilu)
    tuichu(zt)
    return huizong(zt)


def tuichu(zt):
    jiekou = zt["io"]
    if not zt["entered"] or zt["exit_attempted"]:
        return
    if jiekou["pending"] is not None:
        raise RuntimeError("Cannot exit while earlier request is unresolved")
    zt["exit_attempted"] = True
    jiekou["call"]("/exit")
    zt["exit_confirmed"] = True


def huizong(zt):
    jilu = zt["ledger"]
    cleared = sorted(pindao(jilu, ("cleared",)))
    return dict(
        problem=zt["problem"],
        completed=zt["completed"],
        exit_confirmed=zt["exit_confirmed"],
        virtual_time_s=zt["virtual"],
        moving_distance_m=zt["travel"],
        cleared_count=len(cleared),
        average_clear_time_s=zt["virtual"] / len(cleared) if cleared else None,
        cleared_channels=cleared,
        unknown_channels=sorted(pindao(jilu, ("unknown",))),
        pending_channels=sorted(pindao(jilu, ("found",))),
        measures=zt["measures"],
        clear_attempts=zt["clear_attempts"],
        switches=zt["switches"],
        fallback_used=zt["fallback_used"],
    )
