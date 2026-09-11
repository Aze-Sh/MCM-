import networkx as nx
import pytest

from cumcm_py.graph import shortest_path_report


def test_shortest_path_report_recomputes_cost() -> None:
    graph = nx.Graph()
    graph.add_weighted_edges_from([("a", "b", 1.0), ("b", "c", 2.0), ("a", "c", 5.0)])
    result = shortest_path_report(graph, "a", "c")
    assert result.values["path"] == ["a", "b", "c"]
    assert result.values["cost"] == 3.0


def test_shortest_path_report_rejects_disconnected() -> None:
    graph = nx.Graph([(1, 2)])
    graph.add_node(3)
    with pytest.raises(ValueError, match="no path"):
        shortest_path_report(graph, 1, 3)

