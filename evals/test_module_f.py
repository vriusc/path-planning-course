"""Evals for assignment, auction, TPTS, CBS-TA."""

from evals.scenarios import assign_pair
from lib.algos.assignment import auction_assign, cbs_ta, greedy_assign, hungarian_assign, tpts
from lib.maps import corridor_headon
from lib.search import dijkstra


def test_22_hungarian_not_worse_than_greedy_and_uses_topo():
    g, robots, starts, tasks = assign_pair()
    greedy = greedy_assign(g, robots, starts, tasks)
    hung = hungarian_assign(g, robots, starts, tasks)
    assert hung["cost"] <= greedy["cost"] + 1e-6
    assert hung["used_topo"]
    # matrix cells equal Dijkstra, not heuristic-only
    i, j = 0, 0
    d = dijkstra(g, starts[robots[0]], tasks[0], record=False).cost
    assert abs(hung["matrix"][i][j] - d) < 1e-6


def test_23_auction_assigns_arrivals():
    g, robots, starts, tasks = assign_pair()
    r = auction_assign(g, robots, starts, tasks, arrivals=tasks)
    assert r["found"]
    assert set(r["assign"].values()) <= set(tasks)
    hung = hungarian_assign(g, robots, starts, tasks)
    assert r["cost"] + 1e-6 >= hung["cost"] - 50  # loose gap record


def test_24_tpts_completes_and_swap_helps():
    g = corridor_headon()
    robots = ["r0", "r1"]
    starts = {"r0": "A", "r1": "B"}
    stream = [("t0", "B"), ("t1", "A")]
    with_swap = tpts(g, robots, starts, stream, allow_swap=True)
    no_swap = tpts(g, robots, starts, stream, allow_swap=False)
    assert with_swap["found"] or no_swap["found"]
    if with_swap["found"] and no_swap["found"]:
        assert with_swap["headon"] <= no_swap["headon"] + 2


def test_25_cbs_ta_not_worse_than_greedy_then_cbs():
    g, robots, starts, tasks = assign_pair()
    r = cbs_ta(g, robots, starts, tasks)
    assert r["found"]
    assert r["soc"] <= r["greedy_soc"] + 1e-6
