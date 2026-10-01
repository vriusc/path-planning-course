from lib.agents import is_conflict_free, soc
from lib.search import path_cost


def assert_path(graph, result, start, goal):
    assert result.found, "no path"
    assert result.path[0] == start
    assert result.path[-1] == goal
    assert path_cost(graph, result.path) == result.cost or abs(path_cost(graph, result.path) - result.cost) < 1e-6


def assert_directed(graph, result):
    for a, b in zip(result.path, result.path[1:]):
        nbrs = dict(graph.neighbors(a))
        assert b in nbrs, f"illegal reverse or missing edge {a}->{b}"


def assert_conflict_free(paths):
    assert is_conflict_free(paths), "paths collide"
