"""Graph reports with explicit path reconstruction."""

from typing import Any

import networkx as nx

from .types import ModelResult


def shortest_path_report(
    graph: nx.Graph, source: Any, target: Any, weight: str = "weight"
) -> ModelResult:
    """Return a shortest path and independently summed edge cost."""

    if source not in graph or target not in graph:
        raise ValueError("source and target must exist in graph")
    try:
        path = nx.shortest_path(graph, source, target, weight=weight)
    except nx.NetworkXNoPath as error:
        raise ValueError("no path between source and target") from error
    cost = 0.0
    for left, right in zip(path, path[1:]):
        cost += float(graph.edges[left, right].get(weight, 1.0))
    return ModelResult(
        method="graph-flow-routing",
        values={"path": path, "cost": cost},
        diagnostics={"reachable": True, "edge_count": len(path) - 1},
        assumptions=("Edge weights are additive and nonnegative.",),
    )

