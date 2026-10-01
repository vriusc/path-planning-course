"""Evals for lessons 07-09: locks, time A*, SIPP."""

from lib.algos.temporal import sipp, time_astar
from lib.maps import corridor_headon
from lib.reservation import ReservationTable
from lib.search import astar


def test_07_lock_conflict_and_release():
    table = ReservationTable()
    assert table.occupy("C1", 1, "a")
    assert not table.occupy("C1", 1, "b")
    table.free("C1", 1, "a")
    assert table.occupy("C1", 1, "b")


def test_07_issued_segment_exclusive():
    table = ReservationTable()
    assert table.issue_segment(["P0", "P1", "P2"], "a")
    assert not table.issue_segment(["P2", "P3"], "b")
    table.release_segment(["P0", "P1", "P2"], "a")
    assert table.issue_segment(["P2", "P3"], "b")


def test_08_time_astar_conflict_free_wait_or_detour():
    g = corridor_headon()
    table = ReservationTable()
    first = astar(g, "A", "B", record=False)
    for t in range(0, 3):
        table.occupy("C2", t, "a")
    r = time_astar(g, "A", "B", table=table, agent="b", horizon=40)
    assert r.found
    assert r.cost >= first.cost
    for t, n in enumerate(r.path):
        if n == "C2":
            assert t >= 3


def test_09_sipp_matches_time_astar_empty():
    g = corridor_headon()
    ta = time_astar(g, "A", "B", horizon=40)
    si = sipp(g, "A", "B", horizon=40)
    assert ta.found and si.found
    assert si.cost == ta.cost
    assert si.expanded <= ta.expanded + 5


def test_09_sipp_fewer_states_with_traffic():
    g = corridor_headon()
    table = ReservationTable()
    for t in range(0, 3):
        table.occupy("C2", t, "blocker")
    ta = time_astar(g, "A", "B", table=table, agent="b", horizon=40)
    si = sipp(g, "A", "B", table=table, agent="b", horizon=40)
    assert ta.found and si.found
    assert si.extra.get("states", si.expanded) <= ta.expanded
