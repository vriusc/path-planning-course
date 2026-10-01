"""Evals for lessons 01-06."""

import pytest

from evals.harness import assert_directed, assert_path
from evals.scenarios import grid_maze, grid_open, grid_wall, topo_oneway
from lib.algos.single_agent import dstar_lite, jps, weighted_astar
from lib.maps import GridMap, topo_oneway as make_topo
from lib.search import astar, bfs, dijkstra


def test_01_bfs_unweighted_shortest():
    g, s, t = grid_open()
    r = bfs(g, s, t, record=False)
    assert_path(g, r, s, t)
    assert r.cost == 14


def test_01_bfs_blocked_empty():
    g = GridMap(3, 3, {(1, 0), (1, 1), (1, 2)})
    r = bfs(g, (0, 0), (2, 0), record=False)
    assert not r.found


def test_01_bfs_directed_no_reverse():
    g = make_topo()
    r = bfs(g, "I0", "G1", record=False)
    assert r.found
    assert_directed(g, r)
    r2 = bfs(g, "I1", "I0", record=False)
    # I1 cannot go back to I0 directly; around the loop it can
    if r2.found:
        assert_directed(g, r2)


def test_02_dijkstra_weighted_and_directed():
    g, s, t = topo_oneway()
    r = dijkstra(g, s, t, record=False)
    assert r.found
    assert_directed(g, r)
    r_bad = dijkstra(g, "G1", "I0", record=False)
    # G1 only connects to I2, then the one-way loop can reach I0? I2→I3→I4→I5→I0 yes
    if r_bad.found:
        assert_directed(g, r_bad)


def test_02_dijkstra_unreachable():
    g = GridMap(3, 3, {(1, 0), (1, 1), (1, 2)})
    r = dijkstra(g, (0, 1), (2, 1), record=False)
    assert not r.found
    assert r.path == []


def test_03_astar_matches_dijkstra():
    g, s, t = grid_wall()
    d = dijkstra(g, s, t, record=False)
    a = astar(g, s, t, record=False)
    assert d.found and a.found
    assert a.cost == d.cost
    assert a.expanded <= d.expanded


def test_03_inadmissible_may_be_suboptimal():
    g, s, t = grid_wall()
    opt = dijkstra(g, s, t, record=False).cost
    r = astar(g, s, t, heuristic=lambda a, b: 50.0, record=False)
    assert r.found
    assert r.cost >= opt


def test_04_weighted_astar_bound():
    g, s, t = grid_wall()
    opt = astar(g, s, t, record=False).cost
    w1 = weighted_astar(g, s, t, weight=1.0, record=False)
    assert w1.cost == opt
    w = 1.5
    r = weighted_astar(g, s, t, weight=w, record=False)
    assert r.found
    assert r.cost <= w * opt + 1e-6


def test_05_dstar_static_equals_astar():
    g, s, t = grid_maze()
    a = astar(g, s, t, record=False)
    d = dstar_lite(g, s, t)
    assert d.found
    assert d.cost == a.cost


def test_05_dstar_replans_after_block():
    from lib.algos.single_agent import DStarLite

    g, s, t = grid_maze()
    planner = DStarLite(g, s, t)
    first = planner.compute()
    assert first.found
    # block a cell on the path (not start/goal)
    mid = first.path[len(first.path) // 2]
    if mid in (s, t):
        mid = first.path[2]
    g.block(mid)
    planner.start = s
    planner.edge_blocked(first.path[first.path.index(mid) - 1], mid)
    second = planner.compute()
    assert second.found
    assert mid not in second.path
    opt = astar(g, s, t, record=False)
    assert second.cost == opt.cost
    assert second.expanded < 8 * 8 * 4


def test_06_jps_matches_astar_fewer_expansions():
    g, s, t = grid_wall()
    a = astar(g, s, t, record=False)
    j = jps(g, s, t, record=False)
    assert j.found
    assert j.cost == a.cost
    assert j.expanded < a.expanded


def test_06_jps_inapplicable_on_topo():
    g, s, t = topo_oneway()
    r = jps(g, s, t)
    assert r.extra.get("inapplicable")
    assert not r.found
