from jammer_solver import solver as v8
from jammer_solver import exact_geometry as g
from fractions import Fraction as F


def audit_optical_chains(events):
    if not any(e.get("event") == "optical_chain_selected" for e in events):
        return dict(verified=True, chains=[])
    ledger = None
    position = (0.0, 0.0)
    virtual = 0.0
    active = None
    chains = []
    for event in events:
        kind = event.get("event")
        if kind == "v8_started":
            ledger = v8.xin_jilu(
                event["problem"], event["extra_actions"],
                coverage_nodes=event.get("coverage_nodes", 4096),
                coverage_depth=event.get("coverage_depth", 12),
                geometry_version=event.get("geometry_version", 1),
            )
            virtual = event["virtual_time_s"]
            limit = event["max_virtual_s"]
        elif kind == "optical_chain_selected":
            if active is not None:
                raise ValueError("A new chain interrupted an unfinished chain")
            points = [g.point(q) for q in event["points"]]
            if not 2 <= len(points) <= 8 or len(set(points)) != len(points):
                raise ValueError("Invalid optical chain length or repeated points")
            polygon = ledger["channels"][event["channel"]]["source"]["polygon"]
            for q in points:
                cell = polygon
                for other in points:
                    if q != other:
                        cell = g.clip(cell, g.sub(other, q), (g.dot(other, other) - g.dot(q, q)) / 2)
                if cell and not g.disk_contains(cell, q, F("19.8")):
                    raise ValueError("Optical chain leaves feasible source positions uncovered")
            previous = g.point(position)
            distance = F(0)
            for q in points:
                distance += g.ceil_distance(previous, q)
                previous = q
            found = min(16, len(v8.pindao(ledger, ("found",))) + len(points))
            required = (virtual + v8.shengyu_shangjie(ledger, position)
                        + float((2 * found + 2) * distance / 5) + 6 * len(points))
            if ledger["extra"] < len(points) or required >= limit - 2:
                raise ValueError("The complete optical event does not fit its reserved budget")
            if v8.chain_bound(points, position) > event["upper_s"] + 1e-6:
                raise ValueError("The recorded optical upper bound is too small")
            active = dict(channel=event["channel"], start_s=virtual, points=points, count=0,
                          upper_s=event["upper_s"], budget_required_s=required)
        elif kind == "evidence_observation":
            q = tuple(event["point"])
            if active is not None:
                index = active["count"]
                if (event["path"] != "/clear" or event["channel"] != active["channel"]
                        or index >= len(active["points"]) or g.point(q) != active["points"][index]):
                    raise ValueError("Execution departed from the certified optical chain")
                active["count"] += 1
            v8.gengxin_jilu(ledger, event["path"], q, event["channel"], event["reply"], prove=event["prove"])
            position = q
            virtual = event["reply"]["virtual_time_s"]
            if active is not None and event["reply"]["clear_result"] == "success":
                elapsed = virtual - active["start_s"]
                if elapsed > active["upper_s"] + 1e-5:
                    raise ValueError("The actual optical prefix exceeded its upper bound")
                chains.append(dict(channel=active["channel"], points=len(active["points"]),
                                   actions=active["count"], actual_s=elapsed, upper_s=active["upper_s"],
                                   budget_required_s=active["budget_required_s"]))
                active = None
        elif kind == "verified_negative_pair":
            v8.shuang_yinxing(ledger["channels"][event["channel"]]["source"],
                             g.point(event["positive"]), g.point(event["a"]), g.point(event["b"]))
    if active is not None or ledger is None or not v8.quanbu_qingchu(ledger):
        raise ValueError("Optical audit ended without actual full clearance")
    return dict(verified=True, chains=chains)
