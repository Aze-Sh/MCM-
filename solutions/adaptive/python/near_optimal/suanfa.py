from fractions import Fraction as F
import math
import time
from protocol import validate_reply, UncertainAction
from coverage import design
from planning import open_route, route_length
from posterior import nearest_clear_point
from routing import improve_clear_route
from service_graph import assignment
from . import geometry as g

STRATEGY = "event-rollout-certified-completion-v8"
REVISION = "20260912-shared-service-r4"


def search_points(problem):
    if problem == 3:
        return design(3)
    return (
        [(0.0, 0.0)]
        + [(998 * math.cos(k * math.pi / 4), 998 * math.sin(k * math.pi / 4)) for k in range(8)]
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


def xin_jilu(problem, extra_actions=640, *, coverage_nodes=4096, coverage_depth=12, geometry_version=1):
    if problem not in (3, 4) or type(extra_actions) is not int or extra_actions < 0:
        raise ValueError("Invalid problem or extra action allowance")
    if geometry_version not in (1, 2):
        raise ValueError("Unknown source geometry version")
    return dict(
        problem=problem,
        extra=extra_actions,
        coverage_nodes=coverage_nodes,
        coverage_depth=coverage_depth,
        geometry_version=geometry_version,
        receipts=[],
        certificates=[],
        channels={
            c: dict(
                status="unknown",
                radio=[],
                optical=[],
                records=[],
                pending=set(g.search_grid()),
                source=None,
                proof=None,
            )
            for c in range(1, 21)
        },
    )


def xin_luxian(points, seconds=0.25):
    return dict(
        points=list(points),
        seconds=seconds,
        signature=None,
        route=[],
        proofs=0,
        deletions=0,
        replacements=0,
        pending_stop=None,
    )


def xin_zhuangtai(
    transport,
    problem,
    progress=None,
    *,
    extra_actions=640,
    planning_seconds=0.2,
    request_seconds=0.1,
    fallback_only=False,
):
    if not math.isfinite(request_seconds) or request_seconds <= 0:
        raise ValueError("A positive assumed request latency is required")
    if not math.isfinite(planning_seconds) or planning_seconds < 0:
        raise ValueError("Invalid planning budget")
    return dict(
        io=transport,
        problem=problem,
        progress=progress,
        ledger=xin_jilu(
            problem,
            extra_actions,
            coverage_nodes=20000,
            coverage_depth=14,
            geometry_version=2 if problem == 3 else 1,
        ),
        planner=dict(
            seconds=planning_seconds,
            problem=problem,
            statistics=dict(
                decisions=0,
                rollout_candidates=0,
                rollout_timeouts=0,
                continuous_clears=0,
                radio_events=0,
            ),
        ),
        request_seconds=request_seconds,
        fallback_only=fallback_only,
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
        certificate=False,
        reason="not_started",
        started=None,
        deadline=math.inf,
        max_virtual=360000.0,
        fallback_used=False,
        initial_upper=None,
        search_plan=xin_luxian(search_points(problem)),
        guard_checks=0,
    )


def intersection(poly, other):
    if len(other) < 3:
        return poly
    for a, b in zip(other, other[1:] + other[:1]):
        edge = g.sub(b, a)
        normal = (edge[1], -edge[0])
        poly = g.clip(poly, normal, g.dot(normal, a))
        if not poly:
            break
    return poly


def xin_yuan(origin, bearing=None, geometry_version=1):
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
    domain = g.rectangle(-1800, -1800, 1800, 1800)
    if bearing is None:
        x, y = origin
        yuan["polygon"] = intersection(g.rectangle(x - 5, y - 5, x + 5, y + 5), domain)
        yuan["points"] = {0: origin}
        yuan["cells"] = {0: yuan["polygon"]}
        yuan["anchor_radius"] = 5.0
    else:
        yuan["polygon"] = g.apply_bearing(domain, origin, F(bearing))
        index = 0
        for row, y in enumerate((-25, 0, 25)):
            for k in range(61) if row % 2 == 0 else range(60, -1, -1):
                x = 25 * k
                bounds = (
                    max(0, x - F(25, 2)),
                    max(-30, y - F(25, 2)),
                    min(1500, x + F(25, 2)),
                    min(30, y + F(25, 2)),
                )
                cell = intersection(g.transformed_box(origin, bearing, bounds), yuan["polygon"])
                q = g.rotated_point(origin, bearing, x, y)
                if cell:
                    if not g.disk_contains(cell, q, F(20)):
                        raise RuntimeError("Optical responsibility is not covered")
                    yuan["points"][index], yuan["cells"][index] = (q, cell)
                index += 1
    yuan["positives"].append(origin)
    if not yuan["polygon"] or not yuan["cells"]:
        raise RuntimeError("Known source lost all feasible responsibilities")
    if geometry_version == 2:
        xianding_fanwei(yuan, intersection(yuan["polygon"], g.source_domain()))
        yuan["anchor_radius"] = math.nextafter(
            max(float(g.ceil_distance(yuan["anchor_point"], p)) for p in yuan["polygon"]), math.inf
        )
    return yuan


def xianding_fanwei(yuan, poly):
    if not poly:
        raise RuntimeError("Accepted evidence contradicts known source")
    yuan["cells"] = {i: out for i, p in yuan["cells"].items() if (out := intersection(p, poly))}
    yuan["polygon"] = poly
    if not yuan["polygon"] or not yuan["cells"]:
        raise RuntimeError("Known source lost all feasible responsibilities")


def gengxin_yuan(yuan, q, kind, bearing=None, problem=4):
    q = g.point(q)
    if kind == "direction":
        xianding_fanwei(yuan, g.apply_bearing(yuan["polygon"], q, F(bearing)))
        yuan["positives"].append(q)
        yuan["anchor_point"], yuan["anchor_bearing"] = (q, bearing)
        yuan["anchor_radius"] = min(
            1500.0,
            math.nextafter(float(max((g.ceil_distance(q, v) for v in yuan["polygon"]))), math.inf),
        )
        yuan["rounds"] += 1
    elif kind == "near":
        x, y = q
        xianding_fanwei(yuan, intersection(yuan["polygon"], g.rectangle(x - 5, y - 5, x + 5, y + 5)))
        yuan["anchor_point"] = q
        yuan["anchor_radius"] = math.nextafter(
            float(max((g.ceil_distance(q, v) for v in yuan["polygon"]))), math.inf
        )
    elif kind == "no_signal":
        yuan["negatives"].append(q)
        if problem == 3:
            poly = yuan["polygon"]
            for p in yuan["positives"]:
                poly = g.clip(poly, g.sub(q, p), (g.dot(q, q) - g.dot(p, p)) / 2)
            xianding_fanwei(yuan, poly)
        yuan["cells"] = {
            i: p for i, p in yuan["cells"].items() if problem != 3 or not g.disk_contains(p, q, F(1000))
        }
        if not yuan["polygon"] or not yuan["cells"]:
            raise RuntimeError("Known source lost all feasible responsibilities")
    elif kind == "no_target_in_range":
        yuan["cells"] = {i: p for i, p in yuan["cells"].items() if not g.disk_contains(p, q, F(20))}
        if not yuan["polygon"] or not yuan["cells"]:
            raise RuntimeError("Known source lost all feasible responsibilities")
        yuan["polygon"] = g.hull((v for p in yuan["cells"].values() for v in p))


def shuang_yinxing(yuan, positive, a, b):
    if positive not in yuan["positives"] or a not in yuan["negatives"] or b not in yuan["negatives"]:
        raise RuntimeError("Pair contraction lacks its observed evidence")
    poly, changed = g.verified_pair_cut(yuan["polygon"], positive, a, b)
    if changed:
        xianding_fanwei(yuan, poly)
        yuan["anchor_radius"] = min(
            yuan["anchor_radius"],
            math.nextafter(
                float(max((g.ceil_distance(yuan["anchor_point"], v) for v in poly))), math.inf
            ),
        )
    yuan["rounds"] += 1
    return changed


def shengyu_renwu(jilu):
    return (
        sum((len(s["pending"]) for s in jilu["channels"].values() if s["status"] == "unknown"))
        + sum((len(s["source"]["cells"]) for s in jilu["channels"].values() if s["status"] == "found"))
        + 183 * (16 - len(pindao(jilu, ("found", "cleared"))))
        + jilu["extra"]
    )


def biaoji_wuyuan(jilu, c, basis, **details):
    s = jilu["channels"][c]
    if s["status"] != "unknown":
        raise RuntimeError("Cannot mark a discovered source absent")
    s["status"] = "absent"
    s["pending"].clear()
    s["proof"] = dict(channel=c, basis=basis, **details)
    jilu["certificates"].append(s["proof"])


def zhengming_wuyuan(jilu, c, max_nodes=None):
    s = jilu["channels"][c]
    if s["status"] != "unknown":
        return False
    if not s["pending"]:
        biaoji_wuyuan(jilu, c, "exact_600m_grid_template", radio_count=len(s["radio"]))
        return True
    if len(s["radio"]) < (6 if jilu["problem"] == 3 else 7) and (not s["optical"]):
        return False
    if max_nodes is None:
        max_nodes = jilu["coverage_nodes"]
    proved, nodes, box, leaves = g.coverage_certificate(
        tuple(sorted(set(s["radio"]))),
        tuple(sorted(set(s["optical"]))),
        jilu["problem"],
        max_nodes,
        jilu["coverage_depth"],
    )
    if proved:
        biaoji_wuyuan(
            jilu,
            c,
            "rational_continuous_coverage",
            radio_count=len(s["radio"]),
            optical_count=len(s["optical"]),
            nodes=nodes,
            leaf_count=len(leaves),
            max_nodes=max_nodes,
            max_depth=jilu["coverage_depth"],
            radio=[g.floating(q) for q in s["radio"]],
            optical=[g.floating(q) for q in s["optical"]],
        )
    return proved


def gengxin_jilu(jilu, path, q, c, huifu, prove=True):
    before = shengyu_renwu(jilu)
    q = g.point(q)
    s = jilu["channels"][c]
    if s["status"] in ("cleared", "absent"):
        raise RuntimeError("Action targets a resolved channel")
    kind = huifu["measure_result" if path == "/measure" else "clear_result"]
    s["records"].append(dict(path=path, point=g.floating(q), kind=kind, bearing=huifu.get("svd_deg")))
    if path == "/measure":
        if s["status"] == "unknown":
            if kind == "no_signal":
                s["radio"].append(q)
                s["pending"].discard(q)
                if prove:
                    zhengming_wuyuan(jilu, c)
            else:
                s["status"] = "found"
                s["pending"].clear()
                s["source"] = xin_yuan(
                    q, huifu["svd_deg"] if kind == "direction" else None, jilu["geometry_version"]
                )
        elif kind == "direction":
            gengxin_yuan(s["source"], q, "direction", bearing=huifu["svd_deg"])
        elif kind == "near":
            gengxin_yuan(s["source"], q, "near")
        else:
            gengxin_yuan(s["source"], q, "no_signal", problem=jilu["problem"])
    elif kind == "success":
        s["status"] = "cleared"
        s["pending"].clear()
        s["source"] = None
    elif s["status"] == "unknown":
        s["optical"].append(q)
        if prove:
            zhengming_wuyuan(jilu, c)
    else:
        gengxin_yuan(s["source"], q, "no_target_in_range")
    if len(pindao(jilu, ("found", "cleared"))) > 16:
        raise RuntimeError("More than 16 distinct sources")
    if len(pindao(jilu, ("found", "cleared"))) == 16:
        for other in sorted(pindao(jilu, ("unknown",))):
            biaoji_wuyuan(jilu, other, "source_count_upper_bound")
    if shengyu_renwu(jilu) >= before:
        if jilu["extra"] <= 0:
            raise RuntimeError("An unproductive action had no reserved allowance")
        jilu["extra"] -= 1
    after = shengyu_renwu(jilu)
    if after >= before or after < 0:
        raise RuntimeError("Completion rank failed to decrease")
    receipt = dict(
        before=before, after=after, extra_remaining=jilu["extra"], channel=c, path=path, result=kind
    )
    jilu["receipts"].append(receipt)
    return receipt


def quanbu_qingchu(jilu):
    return (
        not pindao(jilu, ("unknown",))
        and (not pindao(jilu, ("found",)))
        and (10 <= len(pindao(jilu, ("cleared",))) <= 16)
    )


def shengyu_shangjie(jilu, weizhi):
    p = g.point(weizhi)
    components = [
        chain_bound(optical_order(jilu["channels"][c]["source"], p), p, p)
        for c in pindao(jilu, ("found",))
    ]
    points = set((q for c in pindao(jilu, ("unknown",)) for q in jilu["channels"][c]["pending"]))
    previous = p
    for q in g.search_grid():
        if q in points:
            components.append(math.nextafter(float(g.ceil_distance(previous, q) / 5), math.inf))
            previous = q
    requests = sum((len(jilu["channels"][c]["pending"]) for c in pindao(jilu, ("unknown",))))
    components.append(6 * requests)
    components.append(
        math.nextafter(
            1843.1 * min(16 - len(pindao(jilu, ("found", "cleared"))), len(pindao(jilu, ("unknown",)))),
            math.inf,
        )
    )
    return math.nextafter(math.fsum(components), math.inf)


def jilu_zhaiyao(jilu):
    return dict(
        discovered_channels=sorted(pindao(jilu, ("found", "cleared"))),
        cleared_channels=sorted(pindao(jilu, ("cleared",))),
        unknown_channels=sorted(pindao(jilu, ("unknown",))),
        pending_channels=sorted(pindao(jilu, ("found",))),
        absent_channels=[c for c, s in jilu["channels"].items() if s["status"] == "absent"],
        extra_actions_remaining=jilu["extra"],
        completion_rank=shengyu_renwu(jilu),
        rank_receipts=len(jilu["receipts"]),
        absence_certificates=jilu["certificates"],
    )


def continuous_clear(yuan, dangqian, target=None):
    polygon = [g.floating(p) for p in yuan["polygon"]]
    candidate = nearest_clear_point(polygon, dangqian)
    if candidate is None:
        return None
    options = [candidate]
    if target is not None:
        q, _ = improve_clear_route(polygon, 19.8 - 1e-06, candidate, dangqian, target)
        options.append(q)
    valid = [g.point(q) for q in options if g.disk_contains(yuan["polygon"], g.point(q), F("19.8"))]
    if not valid:
        return None
    return min(
        valid,
        key=lambda q: (
            math.dist(dangqian, g.floating(q))
            + (math.dist(g.floating(q), target) if target is not None else 0)
        ),
    )


def optical_order(yuan, dangqian, mode="snake", cells=None):
    ids = set(yuan["cells"] if cells is None else cells)
    if mode == "snake":
        return [yuan["points"][i] for i in sorted(ids)]
    order = []
    p = g.point(dangqian)
    while ids:
        i = min(ids, key=lambda i: (g.squared(p, yuan["points"][i]), i))
        ids.remove(i)
        p = yuan["points"][i]
        order.append(p)
    return order


def chain_bound(points, dangqian, target=None):
    p = g.point(dangqian)
    spent = F(0)
    worst = F(0)
    for q in points:
        spent += g.ceil_distance(p, q) / 5
        leave = g.ceil_distance(q, g.point(target)) / 5 if target is not None else 0
        worst = max(worst, spent + 5 + leave)
        spent += 3
        p = q
    return math.nextafter(float(worst), math.inf)


def continuations(yuan, dangqian, cells=None):
    return min(
        (
            (chain_bound(order, dangqian), mode, order)
            for mode in ("snake", "nearest")
            if (order := optical_order(yuan, dangqian, mode, cells))
        )
    )


def pair_points(yuan, dangqian, fraction=0.5):
    length = F(yuan["anchor_radius"])
    x = 5 + (length - 5) * F(fraction)
    side = length / 50
    if len(yuan["positives"]) >= 2:
        u, _ = g.direction(F(yuan["anchor_bearing"]))
        distance = [g.dot(g.sub(q, yuan["anchor_point"]), u) for q in yuan["polygon"]]
        lo, hi = min(distance), max(distance)
        x = (lo + hi) / 2
        side = max(F(5), (hi - lo) / 20)
    points = [
        g.rotated_point(yuan["anchor_point"], yuan["anchor_bearing"], x, sign * side) for sign in (-1, 1)
    ]
    return tuple(sorted(points, key=lambda q: g.squared(q, g.point(dangqian))))


def possible_cells(yuan, polygon):
    if not polygon:
        return []
    return [i for i, cell in yuan["cells"].items() if intersection(cell, polygon)]


def radio_rollout(yuan, dangqian, pair, problem, deadline):
    a, b = pair
    start = float(g.ceil_distance(g.point(dangqian), a) / 5) + 6
    ceshi = [(a, start)]
    if problem == 4:
        ceshi.append((b, start + float(g.ceil_distance(a, b) / 5) + 5))
    worst = 0.0
    branches = 0
    for q, prefix in ceshi:
        for lo in range(0, 360, 60):
            if time.perf_counter() >= deadline:
                return None
            region = g.apply_bearing(yuan["polygon"], q, F(lo), hi=F(lo + 60))
            ids = possible_cells(yuan, region)
            if ids:
                upper, _, _ = continuations(yuan, q, ids)
                worst = max(worst, prefix + upper)
                branches += 1
        worst = max(worst, prefix + 5)
        branches += 1
    if problem == 3:
        if not g.disk_contains(yuan["polygon"], a, F(1000)):
            worst = max(worst, start + continuations(yuan, a)[0])
            branches += 1
    else:
        prefix = ceshi[-1][1]
        region, _ = g.verified_pair_cut(yuan["polygon"], yuan["anchor_point"], a, b)
        ids = possible_cells(yuan, region)
        if ids:
            worst = max(worst, prefix + continuations(yuan, b, ids)[0])
            branches += 1
    return (worst, branches)


def optical_hypotheses(source):
    values = []
    for poly in source["cells"].values():
        points = [g.floating(p) for p in poly]
        center = tuple(sum(p[k] for p in points) / len(points) for k in (0, 1))
        area = abs(sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(points, points[1:] + points[:1]))) / 2
        values.append((center, area))
    total = sum(w for _, w in values)
    return [(p, w / total if total > 1e-12 else 1 / len(values)) for p, w in values]


def optical_mean_cost(order, position, worlds, target=None):
    elapsed = 0.0
    previous = position
    remaining = set(range(len(worlds)))
    mean = 0.0
    exit_x = exit_y = 0.0
    for q in order:
        q = g.floating(q)
        elapsed += math.dist(previous, q) / 5
        hits = [i for i in remaining if math.dist(worlds[i][0], q) <= 20]
        for i in hits:
            mean += worlds[i][1] * (
                elapsed + 5 + (math.dist(q, target) / 5 if target is not None else 0)
            )
            exit_x += worlds[i][1] * q[0]
            exit_y += worlds[i][1] * q[1]
            remaining.remove(i)
        previous = q
        elapsed += 3
    return (math.inf if remaining else mean), (exit_x, exit_y)


def optical_offers(source, position, target=None):
    poly = source["polygon"]
    points = [g.floating(p) for p in poly]
    angle = math.radians(source["anchor_bearing"])
    result = []
    worlds = None
    for theta in (angle, angle + math.pi / 2):
        u = (math.cos(theta), math.sin(theta))
        w = (-u[1], u[0])
        xs = [p[0] * u[0] + p[1] * u[1] for p in points]
        ys = [p[0] * w[0] + p[1] * w[1] for p in points]
        lo, hi = min(xs) - 1e-6, max(xs) + 1e-6
        mid = (min(ys) + max(ys)) / 2
        half_width = (max(ys) - min(ys)) / 2 + 1e-6
        if half_width >= 19.79:
            continue
        half = math.sqrt(19.79**2 - half_width**2)
        n = max(1, math.ceil((hi - lo) / (2 * half)))
        if not 2 <= n <= 8:
            continue
        centers = [lo + half + (hi - lo - 2 * half) * i / (n - 1) for i in range(n)]
        chain = [g.point((x * u[0] + mid * w[0], x * u[1] + mid * w[1])) for x in centers]
        valid = True
        for q in chain:
            part = poly
            for other in chain:
                if q != other:
                    part = g.clip(part, g.sub(other, q), (g.dot(other, other) - g.dot(q, q)) / 2)
            if part and not g.disk_contains(part, q, F("19.8")):
                valid = False
                break
        if not valid:
            continue
        if worlds is None:
            worlds = optical_hypotheses(source)
        greedy = []
        left = list(chain)
        position_now = position
        remaining = set(range(len(worlds)))
        while left:
            q = min(
                left,
                key=lambda p: (
                    -sum(worlds[i][1] for i in remaining if math.dist(worlds[i][0], g.floating(p)) <= 20)
                    / (3 + math.dist(position_now, g.floating(p)) / 5),
                    g.squared(g.point(position_now), p),
                ),
            )
            greedy.append(q)
            left.remove(q)
            position_now = g.floating(q)
            remaining = {i for i in remaining if math.dist(worlds[i][0], position_now) > 20}
        for order in dict.fromkeys((tuple(chain), tuple(reversed(chain)), tuple(greedy))):
            mean, leave = optical_mean_cost(order, position, worlds, target)
            if math.isfinite(mean):
                result.append((mean, order, leave, chain_bound(order, position, target)))
    return result


def optical_choice(jihua, yuan, channel, position, tuned, extra, event, target):
    if jihua["problem"] != 4 or event["method"] == "verified_continuous" or extra < 8:
        return event
    options = optical_offers(yuan, position, target)
    if not options:
        return event
    worlds = optical_hypotheses(yuan)
    q = g.floating(event["points"][0])
    ideal = math.dist(position, q) / 5 + 5 + (channel != tuned) + 5
    ideal += sum(
        weight
        * (
            max(0, math.dist(q, source) - 19.8) / 5
            + (max(0, math.dist(source, target) - 19.8) / 5 if target is not None else 0)
        )
        for source, weight in worlds
    )
    mean, order, leave, upper = min(options, key=lambda option: option[0])
    if mean < ideal:
        return dict(
            kind="optical_chain",
            channel=channel,
            points=order,
            estimate=mean,
            certificate_upper_s=upper,
            method="complete_cover_expected_first_success",
        )
    return event


def yuan_dongzuo(jihua, yuan, channel, dangqian, tuned, extra, target=None):
    q = continuous_clear(yuan, dangqian, target)
    if q is not None:
        jihua["statistics"]["continuous_clears"] += 1
        return {
            "kind": "clear",
            "channel": channel,
            "points": (q,),
            "estimate": math.dist(dangqian, g.floating(q)) / 5 + 5,
            "method": "verified_continuous",
        }
    upper, mode, order = continuations(yuan, dangqian)
    best = {
        "kind": "clear",
        "channel": channel,
        "points": (order[0],),
        "estimate": upper,
        "method": "complete_optical_" + mode,
    }
    if extra < 2 or yuan["anchor_radius"] <= 5 or yuan["rounds"] >= 12:
        return optical_choice(jihua, yuan, channel, dangqian, tuned, extra, best, target)
    deadline = time.perf_counter() + jihua["seconds"]
    for fraction in (0.5, 0.38, 0.62):
        pair = pair_points(yuan, dangqian, fraction)
        jieguo = radio_rollout(yuan, dangqian, pair, jihua["problem"], deadline)
        if jieguo is None:
            jihua["statistics"]["rollout_timeouts"] += 1
            break
        value, branches = jieguo
        jihua["statistics"]["rollout_candidates"] += 1
        if value < best["estimate"]:
            best = {
                "kind": "radio",
                "channel": channel,
                "points": pair,
                "estimate": value,
                "method": f"interval_rollout_{fraction:g}_{branches}_branches",
            }
    if best["kind"] == "clear" and len(yuan["cells"]) > 4:
        pair = pair_points(yuan, dangqian)
        best = {
            "kind": "radio",
            "channel": channel,
            "points": pair,
            "estimate": best["estimate"],
            "method": "annular_proposal_with_guard",
        }
    best = bimian_chongfu(jihua, yuan, dangqian, best)
    best = optical_choice(jihua, yuan, channel, dangqian, tuned, extra, best, target)
    jihua["statistics"]["radio_events"] += best["kind"] == "radio"
    return best


def bimian_chongfu(jihua, yuan, position, event):
    if jihua["problem"] != 4 or event["kind"] != "radio":
        return event
    if not all(q in yuan["negatives"] for q in event["points"]):
        return event
    stats = jihua["statistics"]
    stats["repeated_negative_pairs_skipped"] = stats.get("repeated_negative_pairs_skipped", 0) + 1
    upper, _, order = continuations(yuan, position)
    return dict(
        event, kind="clear", points=(order[0],), estimate=upper, method="avoid_repeated_negative_pair"
    )


def pinggu_shunxu(tu, order):
    tu["evaluations"] += 1
    if not order:
        return 0.0, []
    costs = {i: (tu["start"][i], [i]) for i in tu["ids"][order[0]]}
    for job in order[1:]:
        costs = {
            j: min((value + tu["edge"][i, j], path + [j]) for i, (value, path) in costs.items())
            for j in tu["ids"][job]
        }
    value, path = min(costs.values())
    return value, [tu["modes"][i] for i in path]


def fenpei_shunxu(tu):
    jobs = list(tu["ids"])
    n = len(jobs)
    cost = [[1e12] * (n + 1) for _ in range(n + 1)]
    for j, job in enumerate(jobs, 1):
        cost[0][j] = min(tu["start"][k] for k in tu["ids"][job])
    for i, a in enumerate(jobs, 1):
        cost[i][0] = 0.0
        for j, b in enumerate(jobs, 1):
            if i != j:
                cost[i][j] = min(tu["edge"][x, y] for x in tu["ids"][a] for y in tu["ids"][b])
    _, successor = assignment(cost)

    def cycle(start):
        out = [start]
        q = successor[start]
        while q != start:
            out.append(q)
            q = successor[q]
        return out

    main = cycle(0)
    while len(main) < n + 1:
        other = cycle(next(i for i in range(n + 1) if i not in main))
        a, b = min(
            ((a, b) for a in main for b in other),
            key=lambda ab: (
                cost[ab[0]][successor[ab[1]]]
                + cost[ab[1]][successor[ab[0]]]
                - cost[ab[0]][successor[ab[0]]]
                - cost[ab[1]][successor[ab[1]]]
            ),
        )
        successor[a], successor[b] = successor[b], successor[a]
        main = cycle(0)
    return [jobs[i - 1] for i in main[1:]]


def anpai_renwu(jobs, position, incumbent=()):
    modes = [m for variants in jobs.values() for m in variants]
    tu = dict(
        modes=modes,
        ids={job: [i for i, m in enumerate(modes) if m["job"] == job] for job in jobs},
        edge={
            (i, j): math.dist(a["exit"], b["entry"]) / 5 + b["service"]
            for i, a in enumerate(modes)
            for j, b in enumerate(modes)
            if a["job"] != b["job"]
        },
        start={i: math.dist(position, m["entry"]) / 5 + m["service"] for i, m in enumerate(modes)},
        evaluations=0,
    )
    old = [job for job in incumbent if job in jobs]
    old += [job for job in jobs if job not in old]
    remaining = list(jobs)
    greedy = []
    last = None
    while remaining:
        job = min(
            remaining,
            key=lambda job: min(
                tu["start"][i] if last is None else tu["edge"][last, i] for i in tu["ids"][job]
            ),
        )
        last = min(tu["ids"][job], key=lambda i: tu["start"][i] if last is None else tu["edge"][last, i])
        greedy.append(job)
        remaining.remove(job)
    scans = [job for job in jobs if job[0] == "scan"]
    sources = [job for job in jobs if job[0] == "source"]
    seeds = [old, greedy, sources + scans, scans + sources, fenpei_shunxu(tu)]
    evaluated = []
    for seed in seeds:
        value, variants = pinggu_shunxu(tu, seed)
        evaluated.append((value, seed, variants))
    value, order, variants = min(evaluated, key=lambda e: e[0])
    index = {id(m): i for i, m in enumerate(modes)}
    for _ in range(2):
        before = value
        trials = []
        chosen = {m["job"]: index[id(m)] for m in variants}
        for i in range(len(order)):
            for j in range(len(order)):
                if i == j:
                    continue
                trial = list(order)
                item = trial.pop(i)
                trial.insert(j, item)
                seq = [chosen[job] for job in trial]
                score = tu["start"][seq[0]] + sum(tu["edge"][a, b] for a, b in zip(seq, seq[1:]))
                if score < value - 1e-7:
                    trials.append((score, trial))
        for _, trial in sorted(trials, key=lambda x: x[0])[:16]:
            candidate, proposed = pinggu_shunxu(tu, trial)
            if candidate < value - 1e-7:
                value, order, variants = candidate, trial, proposed
        if value >= before - 1e-7:
            break
    return dict(estimate=value, order=order, modes=variants, evaluations=tu["evaluations"])


def xuan_dongzuo(jihua, jilu, dangqian, tuned, search_points):
    jihua["statistics"]["decisions"] += 1
    jobs = {}
    for c in sorted(pindao(jilu, ("found",))):
        yuan = jilu["channels"][c]["source"]
        job = ("source", c)
        direct = continuous_clear(yuan, dangqian)
        if direct is not None:
            q = g.floating(direct)
            event = dict(
                kind="clear", channel=c, points=(direct,), estimate=5.0, method="service_direct_clear"
            )
            modes = [dict(job=job, entry=q, service=5.0, exit=q, event=event)]
        else:
            center = tuple(
                sum(float(q[k]) for q in yuan["polygon"]) / len(yuan["polygon"]) for k in (0, 1)
            )
            modes = []
            for fraction in (0.38, 0.5, 0.62):
                pair = pair_points(yuan, dangqian, fraction)
                for order in (pair, pair[::-1]) if jilu["problem"] == 4 else (pair,):
                    q = g.floating(order[0])
                    cost = math.dist(q, center) / 5 + 15.0
                    event = dict(
                        kind="radio", channel=c, points=order, estimate=cost, method="service_entry_exit"
                    )
                    modes.append(dict(job=job, entry=q, service=cost, exit=center, event=event))
        jobs[job] = modes
    for q in search_points:
        todo = [c for c in pindao(jilu, ("unknown",)) if g.point(q) not in jilu["channels"][c]["radio"]]
        if todo:
            job = ("scan", tuple(q))
            event = dict(
                kind="search",
                channel=min(todo, key=lambda c: (c != tuned, c)),
                points=(g.point(q),),
                estimate=6 * len(todo),
                method="service_search",
            )
            jobs[job] = [dict(job=job, entry=q, service=event["estimate"], exit=q, event=event)]
    if not jobs:
        return None
    plan = anpai_renwu(jobs, dangqian, jihua.get("order", ()))
    jihua["order"] = plan["order"]
    event = plan["modes"][0]["event"]
    event["target"] = plan["modes"][1]["entry"] if len(plan["modes"]) > 1 else None
    if event["kind"] != "search":
        event = bimian_chongfu(jihua, jilu["channels"][event["channel"]]["source"], dangqian, event)
    return event


def gengxin_luxian(luxian, jilu, dangqian):
    if not pindao(jilu, ("unknown",)):
        return []
    common = set.intersection(*(set(jilu["channels"][c]["radio"]) for c in pindao(jilu, ("unknown",))))
    remaining = [q for q in luxian["points"] if g.point(q) not in common]
    signature = (
        tuple(sorted(common)),
        tuple(sorted(pindao(jilu, ("unknown",)))),
        luxian["pending_stop"],
    )
    route = open_route(dangqian, remaining)
    if signature == luxian["signature"]:
        return route
    luxian["signature"] = signature
    deadline = time.perf_counter() + luxian["seconds"]

    def cost(qs):
        return route_length(dangqian, qs) / 5 + 6 * len(pindao(jilu, ("unknown",))) * len(qs)

    for _ in range(3):
        old = cost(route)
        options = []
        for q in route:
            rest = [p for p in route if p != q]
            trial = open_route(dangqian, rest)
            options.append((cost(trial), "delete", q, trial))
            if (
                luxian["pending_stop"] is not None
                and luxian["pending_stop"] not in rest
                and (g.point(luxian["pending_stop"]) not in common)
            ):
                trial = open_route(dangqian, rest + [luxian["pending_stop"]])
                options.append((cost(trial), "replace", q, trial))
        improved = False
        for value, kind, removed, trial in sorted(options):
            if value >= old - 1e-06 or time.perf_counter() >= deadline:
                break
            luxian["proofs"] += 1
            points = tuple(sorted(common | {g.point(q) for q in trial}))
            proved = g.coverage_certificate(
                points, (), jilu["problem"], jilu["coverage_nodes"], jilu["coverage_depth"]
            )[0]
            if proved:
                route = trial
                improved = True
                luxian["deletions"] += kind == "delete"
                luxian["replacements"] += kind == "replace"
                break
        if not improved:
            break
    luxian["points"] = route
    luxian["route"] = route
    luxian["pending_stop"] = None
    luxian["signature"] = (tuple(sorted(common)), tuple(sorted(pindao(jilu, ("unknown",)))), None)
    return route


def baocun_shijian(zhuangtai, event, **fields):
    data = dict(event=event, virtual_time_s=zhuangtai["virtual"], **fields)
    zhuangtai["io"].record(data)
    if zhuangtai["progress"]:
        zhuangtai["progress"](data)


def shengyu_cishu(zhuangtai):
    l = zhuangtai["ledger"]
    return (
        sum((len(l["channels"][c]["pending"]) for c in pindao(l, ("unknown",))))
        + sum((len(l["channels"][c]["source"]["cells"]) for c in pindao(l, ("found",))))
        + 183 * min(16 - len(pindao(l, ("found", "cleared"))), len(pindao(l, ("unknown",))))
        + 2
    )


def yusuan_jiancha(zhuangtai, points):
    jilu = zhuangtai["ledger"]
    zhuangtai["guard_checks"] += 1
    upper = shengyu_shangjie(jilu, zhuangtai["position"])
    p = zhuangtai["position"]
    distance = 0.0
    for q in points:
        distance += float(g.ceil_distance(g.point(p), g.point(q)))
        p = g.floating(q)
    m = min(16, len(pindao(jilu, ("found",))) + len(points))
    virtual_ok = (
        zhuangtai["virtual"] + upper + (2 * m + 2) * distance / 5 + 6 * len(points)
        < zhuangtai["max_virtual"] - 2
    )
    real_ok = (
        time.monotonic() + (shengyu_cishu(zhuangtai) + len(points)) * zhuangtai["request_seconds"] + 30
        < zhuangtai["deadline"]
    )
    return virtual_ok and real_ok


def zhixing(zhuangtai, path, q, c, *, prove=True):
    jiekou = zhuangtai["io"]
    jilu = zhuangtai["ledger"]
    q = g.floating(g.point(q))
    if getattr(jiekou, "pending", None) is not None:
        raise UncertainAction("Earlier request unresolved")
    if time.monotonic() >= zhuangtai["deadline"] - 2:
        raise TimeoutError("Real deadline reserve reached without completion")
    moved = math.dist(zhuangtai["position"], q)
    if zhuangtai["virtual"] + moved / 5 + 6 >= zhuangtai["max_virtual"] - 1:
        raise RuntimeError("Physical action exceeds virtual budget")
    switching = int(path == "/measure" and c != zhuangtai["channel"])
    huifu = jiekou.call(path, q, c)
    validate_reply(path, huifu)
    before = zhuangtai["virtual"]
    zhuangtai["position"] = q
    zhuangtai["virtual"] = huifu["virtual_time_s"]
    zhuangtai["travel"] += moved
    if path == "/measure":
        zhuangtai["measures"] += 1
        zhuangtai["switches"] += switching
        zhuangtai["channel"] = c
        cost = 5 + switching
    else:
        zhuangtai["clear_attempts"] += 1
        cost = 5 if huifu["clear_result"] == "success" else 3
    if abs(zhuangtai["virtual"] - before - moved / 5 - cost) > 5e-05:
        raise RuntimeError("Accepted response violates documented virtual costs")
    discovered = c in pindao(jilu, ("found", "cleared"))
    baocun_shijian(
        zhuangtai, "evidence_observation", path=path, point=q, channel=c, reply=huifu, prove=prove
    )
    receipt = gengxin_jilu(jilu, path, q, c, huifu, prove=prove)
    baocun_shijian(zhuangtai, "rank_receipt", **receipt)
    if not discovered and c in pindao(jilu, ("found", "cleared")):
        baocun_shijian(zhuangtai, "discovered", channel=c)
    if path == "/clear" and huifu["clear_result"] == "success":
        zhuangtai["search_plan"]["pending_stop"] = tuple(q)
        baocun_shijian(zhuangtai, "cleared", channel=c, cleared_count=len(pindao(jilu, ("cleared",))))
    return huifu


def direction_arcs(p, q):
    if p[0] == q[0] and p[1] == q[1]:
        return [(0.0, 360.0)]
    angle = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    lo = (angle - 90) % 360
    return [(lo, min(360, lo + 180))] + ([(0, lo - 180)] if lo > 180 else [])


def arc_intersection(a, b):
    return [(max(x, u), min(y, w)) for x, y in a for u, w in b if max(x, u) < min(y, w)]


def arc_difference(a, b):
    for lo, hi in b:
        a = [piece for x, y in a for piece in ((x, min(y, lo)), (max(x, hi), y)) if piece[0] < piece[1]]
    return a


def arc_length(intervals):
    return sum(y - x for x, y in intervals)


def radio_model(record):
    src = record["source"]
    positive = []
    negative = []
    for obs in record["records"]:
        if obs["path"] != "/measure":
            continue
        (negative if obs["kind"] == "no_signal" else positive).append(obs["point"])
    total = 0.0
    hypotheses = []
    for poly in src["cells"].values():
        points = [g.floating(q) for q in poly]
        p = tuple(sum(q[k] for q in points) / len(points) for k in (0, 1))
        area = abs(sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(points, points[1:] + points[:1]))) / 2
        lower = max([1000] + [math.dist(p, q) for q in positive])
        upper = 1500.0
        if lower >= upper or area <= 1e-12:
            continue
        valid = [(0.0, 360.0)]
        for q in positive:
            valid = arc_intersection(valid, direction_arcs(p, q))
        negatives = [(math.dist(p, q), q) for q in negative]
        radii = sorted({lower, upper} | {d for d, q in negatives if lower < d < upper})
        for lo, hi in zip(radii, radii[1:]):
            allowed = valid
            omni = True
            for d, q in negatives:
                if d < (lo + hi) / 2:
                    allowed = arc_difference(allowed, direction_arcs(p, q))
                    omni = False
            mass = area * (hi - lo) * (0.5 * omni + 0.5 * arc_length(allowed) / 360)
            if mass > 0:
                total += mass
                hypotheses.append((p, lo, hi, allowed, omni, area))
    return hypotheses, total


def radio_probability(fitted, q):
    hypotheses, total = fitted
    if total <= 0:
        return 0.5
    visible = 0.0
    for p, lo, hi, allowed, omni, area in hypotheses:
        width = max(0, hi - max(lo, math.dist(p, q)))
        if width:
            visible += (
                area
                * width
                * (0.5 * omni + 0.5 * arc_length(arc_intersection(allowed, direction_arcs(p, q))) / 360)
            )
    return min(1, max(0, visible / total))


def shunlu_celiang(zhuangtai):
    jilu = zhuangtai["ledger"]
    position = zhuangtai["position"]
    candidates = []
    for c in sorted(pindao(jilu, ("found",))):
        yuan = jilu["channels"][c]["source"]
        attempts = len(yuan["positives"]) + (len(yuan["negatives"]) if jilu["problem"] == 3 else 0)
        if attempts >= 3 or g.point(position) in yuan["positives"] + yuan["negatives"]:
            continue
        poly = [g.floating(p) for p in yuan["polygon"]]
        center = tuple(sum(p[k] for p in poly) / len(poly) for k in (0, 1))
        if jilu["problem"] == 3:
            if math.dist(position, center) > 1000:
                continue
        elif not g.disk_contains(yuan["polygon"], g.point(position), F(999)):
            continue
        angle = math.radians(yuan["anchor_bearing"])
        u = (math.cos(angle), math.sin(angle))
        origin = g.floating(yuan["anchor_point"])
        interval = [(p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1] for p in poly]
        width = max(interval) - min(interval)
        ray = (center[0] - position[0], center[1] - position[1])
        distance = math.hypot(*ray)
        parallax = abs(u[0] * ray[1] - u[1] * ray[0]) / max(1.0, distance)
        after = min(width, 2 * math.radians(1.005) * distance / max(0.01, parallax))
        reception = (
            radio_probability(radio_model(jilu["channels"][c]), position) if jilu["problem"] == 4 else 1
        )
        gain = reception * (width - after) / 10 - 6
        if parallax >= 0.25 and gain > 0:
            candidates.append((-gain, c))
    for score, c in sorted(candidates):
        if jilu["extra"] < 2 or not yusuan_jiancha(zhuangtai, (position,)):
            return False
        baocun_shijian(
            zhuangtai,
            "shared_station_selected",
            channel=c,
            point=position,
            estimated_gain_s=-score,
            scope="heuristic; reception is established only by the actual reply",
        )
        zhixing(zhuangtai, "/measure", position, c)
    return True


def piliang_celiang(zhuangtai, unknown):
    jilu = zhuangtai["ledger"]
    channels = [
        c
        for c in sorted(unknown & pindao(jilu, ("found",)))
        if len(jilu["channels"][c]["source"]["positives"]) == 1
    ]
    if len(channels) < 3 or jilu["extra"] < len(channels) + 2:
        return True
    position = zhuangtai["position"]
    sources = []
    for c in channels:
        yuan = jilu["channels"][c]["source"]
        poly = [g.floating(p) for p in yuan["polygon"]]
        center = tuple(sum(p[k] for p in poly) / len(poly) for k in (0, 1))
        angle = math.radians(yuan["anchor_bearing"])
        u = (math.cos(angle), math.sin(angle))
        origin = g.floating(yuan["anchor_point"])
        interval = [(p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1] for p in poly]
        sources.append((center, u, max(interval) - min(interval)))
    targets = [
        tuple(
            sum(float(p[k]) for p in jilu["channels"][c]["source"]["polygon"])
            / len(jilu["channels"][c]["source"]["polygon"])
            for k in (0, 1)
        )
        for c in pindao(jilu, ("found",))
    ]
    target = min(targets, key=lambda q: math.dist(position, q))
    fitted = (
        [radio_model(jilu["channels"][c]) for c in channels]
        if jilu["problem"] == 4
        else [None] * len(channels)
    )
    radius = 350
    options = []
    for angle in range(0, 360, 30):
        q = (
            position[0] + radius * math.cos(math.radians(angle)),
            position[1] + radius * math.sin(math.radians(angle)),
        )
        gain = 0.0
        selected = []
        for c, fit, (center, u, width) in zip(channels, fitted, sources):
            ray = (center[0] - q[0], center[1] - q[1])
            distance = math.hypot(*ray)
            parallax = abs(u[0] * ray[1] - u[1] * ray[0]) / max(1.0, distance)
            posterior_width = min(width, 2 * math.radians(1.005) * distance / max(0.01, parallax))
            benefit = (width - posterior_width) / 10.0
            if jilu["problem"] == 4:
                benefit = radio_probability(fit, q) * benefit - 6
            if jilu["problem"] == 3 or benefit > 0:
                gain += benefit
                selected.append(c)
        detour = (radius + math.dist(q, target) - math.dist(position, target)) / 5.0
        options.append((detour - gain, angle, q, gain, detour, selected))
    score, angle, q, gain, detour, channels = min(options)
    if jilu["problem"] == 4 and (score >= 0 or not channels):
        return True
    baocun_shijian(
        zhuangtai,
        "batch_observation_selected",
        channels=channels,
        point=q,
        angle=angle,
        radius=radius,
        estimated_gain_s=gain,
        estimated_detour_s=detour,
        reception_weighted=jilu["problem"] == 4,
    )
    for c in channels:
        if jilu["extra"] < 2 or not yusuan_jiancha(zhuangtai, (q,)):
            return False
        zhixing(zhuangtai, "/measure", q, c)
    return True


def zhixing_shijian(zhuangtai, event):
    jilu = zhuangtai["ledger"]
    unknown = pindao(jilu, ("unknown",))
    if not zhixing_yici(zhuangtai, event):
        return False
    if event["kind"] == "search":
        return piliang_celiang(zhuangtai, unknown) and shunlu_celiang(zhuangtai)
    c = event["channel"]
    while c in pindao(jilu, ("found",)):
        if jilu["extra"] < 2:
            return False
        next_event = yuan_dongzuo(
            zhuangtai["planner"],
            jilu["channels"][c]["source"],
            c,
            zhuangtai["position"],
            zhuangtai["channel"],
            jilu["extra"],
            event.get("target"),
        )
        if not yusuan_jiancha(zhuangtai, next_event["points"]) or not zhixing_yici(
            zhuangtai, next_event
        ):
            return False
    return shunlu_celiang(zhuangtai)


def zhixing_yici(zhuangtai, event):
    jilu = zhuangtai["ledger"]
    if event["kind"] == "optical_chain":
        if jilu["extra"] < len(event["points"]) or not yusuan_jiancha(zhuangtai, event["points"]):
            return False
        baocun_shijian(
            zhuangtai,
            "optical_chain_selected",
            channel=event["channel"],
            points=[g.floating(q) for q in event["points"]],
            upper_s=event["certificate_upper_s"],
            mean_s=event["estimate"],
            scope="hypothesis-weighted ranking; complete Voronoi disk cover certifies success",
        )
        for q in event["points"]:
            if event["channel"] not in pindao(jilu, ("found",)):
                return True
            zhixing(zhuangtai, "/clear", q, event["channel"])
        if event["channel"] in pindao(jilu, ("found",)):
            raise RuntimeError("Certified optical chain exhausted")
        return True
    baocun_shijian(
        zhuangtai,
        "event_selected",
        kind=event["kind"],
        channel=event["channel"],
        points=[g.floating(q) for q in event["points"]],
        method=event["method"],
        candidate_estimate_s=event["estimate"],
        estimate_scope="candidate ranking; not a global optimality bound",
    )
    if event["kind"] == "search":
        q = event["points"][0]
        for c in sorted(pindao(jilu, ("unknown",)), key=lambda c: (c != zhuangtai["channel"], c)):
            if c not in pindao(jilu, ("unknown",)) or q in jilu["channels"][c]["radio"]:
                continue
            if jilu["extra"] < 1 or not yusuan_jiancha(zhuangtai, (q,)):
                return False
            zhixing(zhuangtai, "/measure", q, c)
        return True
    if event["kind"] == "clear":
        zhixing(zhuangtai, "/clear", event["points"][0], event["channel"])
        return True
    yuan = jilu["channels"][event["channel"]]["source"]
    positive = yuan["anchor_point"]
    a, b = event["points"]
    first = zhixing(zhuangtai, "/measure", a, event["channel"])
    if first["measure_result"] == "no_signal" and zhuangtai["problem"] == 4:
        second = zhixing(zhuangtai, "/measure", b, event["channel"])
        if second["measure_result"] == "no_signal":
            before = shengyu_renwu(jilu)
            changed = shuang_yinxing(yuan, positive, a, b)
            baocun_shijian(
                zhuangtai,
                "verified_negative_pair",
                channel=event["channel"],
                changed=changed,
                positive=g.floating(positive),
                a=g.floating(a),
                b=g.floating(b),
                rank_before=before,
                rank_after=shengyu_renwu(jilu),
            )
    return True


def qingchu_yuan(zhuangtai, c):
    jilu = zhuangtai["ledger"]
    yuan = jilu["channels"][c]["source"]
    order = [(i, yuan["points"][i]) for i in sorted(yuan["cells"])]
    for i, q in order:
        if c not in pindao(jilu, ("found",)):
            return
        if i in yuan["cells"]:
            zhixing(zhuangtai, "/clear", q, c, prove=False)
    if c in pindao(jilu, ("found",)):
        raise RuntimeError("Constructive optical cover exhausted without success")


def beiyong_qingchu(zhuangtai):
    jilu = zhuangtai["ledger"]
    zhuangtai["fallback_used"] = True
    upper = shengyu_shangjie(jilu, zhuangtai["position"])
    if zhuangtai["virtual"] + upper >= zhuangtai["max_virtual"] - 1:
        raise RuntimeError("No certified completion fits the remaining virtual budget")
    baocun_shijian(
        zhuangtai,
        "fallback_committed",
        remaining_upper_s=upper,
        requests_upper=shengyu_cishu(zhuangtai),
        real_time_condition=f"requires sufficient actual latency; assumed {zhuangtai['request_seconds']:g} s/request",
    )
    origin = zhuangtai["position"]
    known = sorted(
        pindao(jilu, ("found",)),
        key=lambda c: chain_bound(optical_order(jilu["channels"][c]["source"], origin), origin, origin),
    )
    for c in known:
        qingchu_yuan(zhuangtai, c)
    for q in g.search_grid():
        for c in sorted(pindao(jilu, ("unknown",)), key=lambda c: (c != zhuangtai["channel"], c)):
            if c not in pindao(jilu, ("unknown",)) or q not in jilu["channels"][c]["pending"]:
                continue
            zhixing(zhuangtai, "/measure", q, c, prove=False)
            if c in pindao(jilu, ("found",)):
                qingchu_yuan(zhuangtai, c)
        if quanbu_qingchu(jilu):
            break
    for c in sorted(pindao(jilu, ("unknown",))):
        zhengming_wuyuan(jilu, c)
    if not quanbu_qingchu(jilu):
        raise RuntimeError("Full fallback exhausted without a valid 10–16 source completion")


def yunxing(zhuangtai):
    jiekou = zhuangtai["io"]
    jilu = zhuangtai["ledger"]
    zhuangtai["started"] = time.monotonic()
    huifu = jiekou.call("/enter")
    validate_reply("/enter", huifu)
    zhuangtai["entered"] = True
    zhuangtai["virtual"] = huifu["virtual_time_s"]
    zhuangtai["max_virtual"] = huifu["max_virtual_duration_s"]
    zhuangtai["deadline"] = time.monotonic() + huifu["remaining_real_duration_s"]
    jiekou.deadline = zhuangtai["deadline"]
    zhuangtai["initial_upper"] = shengyu_shangjie(jilu, zhuangtai["position"])
    zhuangtai["reason"] = "running"
    baocun_shijian(
        zhuangtai,
        "v8_started",
        problem=zhuangtai["problem"],
        policy_revision=REVISION,
        extra_actions=jilu["extra"],
        coverage_nodes=jilu["coverage_nodes"],
        coverage_depth=jilu["coverage_depth"],
        geometry_version=jilu["geometry_version"],
        max_virtual_s=zhuangtai["max_virtual"],
    )
    while not quanbu_qingchu(jilu):
        if zhuangtai["fallback_only"] or jilu["extra"] < 2:
            beiyong_qingchu(zhuangtai)
            break
        if (
            time.monotonic() + shengyu_cishu(zhuangtai) * zhuangtai["request_seconds"] + 30
            >= zhuangtai["deadline"]
        ):
            beiyong_qingchu(zhuangtai)
            break
        search_route = gengxin_luxian(zhuangtai["search_plan"], jilu, zhuangtai["position"])
        event = xuan_dongzuo(
            zhuangtai["planner"], jilu, zhuangtai["position"], zhuangtai["channel"], search_route
        )
        if event is None or not yusuan_jiancha(zhuangtai, event["points"]):
            beiyong_qingchu(zhuangtai)
            break
        if not zhixing_shijian(zhuangtai, event):
            beiyong_qingchu(zhuangtai)
            break
    zhuangtai["certificate"] = quanbu_qingchu(jilu)
    zhuangtai["reason"] = "certified_all_cleared" if zhuangtai["certificate"] else "incomplete"
    baocun_shijian(zhuangtai, "completion_checked", certified=zhuangtai["certificate"])
    tuichu(zhuangtai)
    return huizong(zhuangtai)


def tuichu(zhuangtai):
    jiekou = zhuangtai["io"]
    if not zhuangtai["entered"] or zhuangtai["exit_attempted"]:
        return
    if getattr(jiekou, "pending", None) is not None:
        raise UncertainAction("Cannot exit while earlier request is unresolved")
    zhuangtai["exit_attempted"] = True
    huifu = jiekou.call("/exit")
    validate_reply("/exit", huifu)
    if abs(huifu["virtual_time_s"] - zhuangtai["virtual"]) > 5e-05:
        raise RuntimeError("Exit unexpectedly changed virtual time")
    zhuangtai["exit_confirmed"] = True


def huizong(zhuangtai):
    jilu = zhuangtai["ledger"]
    return dict(
        strategy=STRATEGY,
        policy_revision=REVISION,
        problem=zhuangtai["problem"],
        reason=zhuangtai["reason"],
        completion_certified=zhuangtai["certificate"],
        exit_confirmed=zhuangtai["exit_confirmed"],
        virtual_time_s=zhuangtai["virtual"],
        moving_distance_m=zhuangtai["travel"],
        average_clear_time_s=zhuangtai["virtual"] / len(pindao(jilu, ("cleared",)))
        if pindao(jilu, ("cleared",))
        else None,
        measures=zhuangtai["measures"],
        clear_attempts=zhuangtai["clear_attempts"],
        switches=zhuangtai["switches"],
        initial_fallback_upper_s=zhuangtai["initial_upper"],
        fallback_used=zhuangtai["fallback_used"],
        budget_guard_checks=zhuangtai["guard_checks"],
        planner=zhuangtai["planner"]["statistics"],
        search_plan=dict(
            proofs=zhuangtai["search_plan"]["proofs"],
            deletions=zhuangtai["search_plan"]["deletions"],
            replacements=zhuangtai["search_plan"]["replacements"],
        ),
        real_time_guarantee="conditional on execution and request latency; not unconditional",
        **jilu_zhaiyao(jilu),
    )
