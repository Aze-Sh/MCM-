import argparse
import json
from pathlib import Path
from protocol import validate_reply
from . import geometry as g
from .suanfa import (
    xin_jilu,
    pindao,
    gengxin_jilu,
    shengyu_renwu,
    shuang_yinxing,
    zhengming_wuyuan,
    quanbu_qingchu,
    jilu_zhaiyao,
)
from collections import deque
from fractions import Fraction as F
import math


def build_graph(worlds, positions, radius=1000, clear_radius=20):
    worlds = tuple((tuple((F(x) for x in w)) for w in worlds))
    positions = tuple((F(x) for x in positions))
    if not worlds or not worlds[0] or any((len(w) != len(worlds[0]) for w in worlds)):
        raise ValueError("Finite calibration requires a fixed, positive source count")
    if not positions or len(set(positions)) != len(positions):
        raise ValueError("Positions must be nonempty and distinct")
    if any((not any((abs(x - p) <= clear_radius for p in positions)) for w in worlds for x in w)):
        raise ValueError("Finite action family cannot clear every candidate source")
    n = len(worlds[0])
    full = (1 << n) - 1
    root = (tuple(range(len(worlds))), 0, -1, 0)
    queue = deque([root])
    graph = {}
    terminals = set()
    while queue:
        state = queue.popleft()
        if state in graph:
            continue
        belief, cleared, at, tuned = state
        graph[state] = {}
        if cleared == full:
            terminals.add(state)
            continue
        dangqian = F(0) if at < 0 else positions[at]
        for c in range(n):
            if cleared >> c & 1:
                continue
            for j, q in enumerate(positions):
                for kind in ("measure", "clear"):
                    groups = {}
                    for w in belief:
                        x = worlds[w][c]
                        d = abs(q - x)
                        if kind == "clear":
                            observation = "success" if d <= clear_radius else "miss"
                        elif d > radius:
                            observation = "no_signal"
                        elif d <= 5:
                            observation = "near"
                        else:
                            observation = "right" if x > q else "left"
                        groups.setdefault(observation, []).append(w)
                    successors = []
                    for observation, ids in sorted(groups.items()):
                        new_cleared = cleared | 1 << c if observation == "success" else cleared
                        nxt = (tuple(ids), new_cleared, j, c if kind == "measure" else tuned)
                        fee = (
                            5 + (c != tuned)
                            if kind == "measure"
                            else 5
                            if observation == "success"
                            else 3
                        )
                        cost = abs(dangqian - q) / 5 + fee
                        successors.append((observation, cost, nxt))
                        if nxt not in graph:
                            queue.append(nxt)
                    graph[state][kind, c, j] = tuple(successors)
    return (root, graph, terminals)


def solve(graph, terminals):
    values = {s: F(0) if s in terminals else math.inf for s in graph}
    policy = {}
    for iteration in range(len(graph) + 1):
        changed = False
        updated = dict(values)
        for s, actions in graph.items():
            if s in terminals:
                continue
            choices = [
                (max((cost + values[t] for _, cost, t in successors)), a)
                for a, successors in actions.items()
            ]
            if not choices:
                continue
            value, action = min(choices)
            if value < values[s]:
                changed = True
                updated[s] = value
                policy[s] = action
        values = updated
        if not changed:
            return (values, policy, iteration + 1)
    raise ArithmeticError("Positive-cost finite policy iteration did not stabilize")


def optical_continuation(graph, terminals, order):
    values = {s: F(0) if s in terminals else math.inf for s in graph}
    for action in reversed(order):
        updated = dict(values)
        for s, actions in graph.items():
            if s in terminals or action not in actions:
                continue
            updated[s] = max((cost + values[t] for _, cost, t in actions[action]))
        values = updated
    return values


def rollout(graph, terminals, baseline, depth):
    values = dict(baseline)
    policy = {}
    for _ in range(depth):
        updated = dict(values)
        for s, actions in graph.items():
            if s in terminals:
                continue
            value, action = min(
                ((max((cost + values[t] for _, cost, t in nexts)), a) for a, nexts in actions.items())
            )
            if value < updated[s]:
                updated[s] = value
                policy[s] = action
        values = updated
    return (values, policy)


def calibrate(worlds, positions, depths=(0, 1, 2, 3), **kwargs):
    root, graph, terminals = build_graph(worlds, positions, **kwargs)
    exact, policy, iterations = solve(graph, terminals)
    n = len(worlds[0])
    forward = [("clear", c, j) for c in range(n) for j in range(len(positions))]
    reverse = [("clear", c, j) for c in reversed(range(n)) for j in reversed(range(len(positions)))]
    first, second = [optical_continuation(graph, terminals, order) for order in (forward, reverse)]
    baseline = {s: min(first[s], second[s]) for s in graph}
    results = []
    for depth in depths:
        values, _ = rollout(graph, terminals, baseline, depth)
        results.append(
            dict(depth=depth, upper_s=float(values[root]), gap_s=float(values[root] - exact[root]))
        )
    return dict(
        worlds=len(worlds),
        sources_per_world=n,
        states=len(graph),
        exact_time_s=float(exact[root]),
        exact_fraction=str(exact[root]),
        first_action=policy[root],
        bellman_passes=iterations,
        rollout=results,
        scope="exact only for these finite worlds and actions; fixed known N",
    )


def replay(events):
    jilu = None
    weizhi = (0.0, 0.0)
    tuned = 1
    virtual = 0.0
    receipt = None
    completed = False
    actions = 0
    for event in events:
        kind = event.get("event")
        if kind == "v8_started":
            if jilu is not None:
                raise RuntimeError("Duplicate start")
            jilu = xin_jilu(
                event["problem"],
                event["extra_actions"],
                coverage_nodes=event.get("coverage_nodes", 4096),
                coverage_depth=event.get("coverage_depth", 12),
                geometry_version=event.get("geometry_version", 1),
            )
            virtual = event["virtual_time_s"]
        elif kind == "evidence_observation":
            if jilu is None or completed or receipt is not None:
                raise RuntimeError("Observation outside an active run")
            path, q, c, huifu = (event["path"], tuple(event["point"]), event["channel"], event["reply"])
            validate_reply(path, huifu)
            cost = (
                5 + (c != tuned)
                if path == "/measure"
                else 5
                if huifu["clear_result"] == "success"
                else 3
            )
            expected = virtual + math.dist(weizhi, q) / 5 + cost
            if abs(expected - huifu["virtual_time_s"]) > 5e-05:
                raise RuntimeError("Replayed virtual cost mismatch")
            virtual = huifu["virtual_time_s"]
            weizhi = q
            if path == "/measure":
                tuned = c
            receipt = gengxin_jilu(jilu, path, q, c, huifu, prove=event["prove"])
            actions += 1
        elif kind == "rank_receipt":
            if receipt is None or any((event.get(k) != v for k, v in receipt.items())):
                raise RuntimeError("Logged rank receipt disagrees with evidence")
            receipt = None
        elif kind == "verified_negative_pair":
            yuan = jilu["channels"][event["channel"]]["source"]
            before = shengyu_renwu(jilu)
            changed = shuang_yinxing(
                yuan, g.point(event["positive"]), g.point(event["a"]), g.point(event["b"])
            )
            if (
                changed != event["changed"]
                or before != event["rank_before"]
                or shengyu_renwu(jilu) != event["rank_after"]
            ):
                raise RuntimeError("Replayed negative pair proof mismatch")
        elif kind == "completion_checked":
            for c in sorted(pindao(jilu, ("unknown",))):
                if not jilu["channels"][c]["pending"]:
                    zhengming_wuyuan(jilu, c)
            completed = quanbu_qingchu(jilu)
            if not completed or event["certified"] is not True:
                raise RuntimeError("Completion claim lacks sufficient evidence")
    if jilu is None or not completed or receipt is not None:
        raise RuntimeError("Incomplete evidence stream")
    return dict(verified=True, actions=actions, virtual_time_s=virtual, **jilu_zhaiyao(jilu))


def main():
    parser = argparse.ArgumentParser(description="重放 v8 日志，核查动作计费、剩余任务和全清依据")
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    result = replay((json.loads(line) for line in args.log.read_text().splitlines() if line.strip()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
