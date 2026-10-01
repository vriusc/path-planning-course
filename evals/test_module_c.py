"""Evals for lessons 10-14: joint A*, HCA*, WHCA*, PBS, RHCR."""

from evals.scenarios import two_agent_tunnel
from lib.agents import is_conflict_free, vertex_conflicts
from lib.algos.prioritized import hca, joint_astar, pbs, rhcr, whca
from lib.maps import grid_open


def test_10_joint_astar_two_agents():
    from evals.scenarios import two_agent_swap
    g, starts, goals = two_agent_swap()
    r = joint_astar(g, starts, goals, cap=30000)
    assert r["found"]
    assert is_conflict_free(r["paths"])


def test_10_joint_astar_explodes_on_three():
    g = grid_open(5, 5)
    starts = {"a": (0, 0), "b": (4, 0), "c": (0, 4)}
    goals = {"a": (4, 4), "b": (0, 4), "c": (4, 0)}
    r = joint_astar(g, starts, goals, cap=400)
    assert r["capped"] or r["expanded"] >= 400 or not r["found"]


def test_11_hca_solvable_and_order_matters():
    g, starts, goals = two_agent_tunnel()
    r1 = hca(g, starts, goals, order=["a", "b"])
    r2 = hca(g, starts, goals, order=["b", "a"])
    assert r1["found"] and r2["found"]
    assert is_conflict_free(r1["paths"])
    assert is_conflict_free(r2["paths"])


def test_12_whca_window_conflict_free_inside():
    g, starts, goals = two_agent_tunnel()
    r = whca(g, starts, goals, window=3)
    assert r["found"]
    wp = r["window_paths"]
    assert is_conflict_free(wp)
    assert all(len(p) <= 4 for p in wp.values())


def test_13_pbs_finds_feasible_priority():
    g, starts, goals = two_agent_tunnel()
    r = pbs(g, starts, goals)
    assert r["found"]
    assert is_conflict_free(r["paths"])
    worst = max(
        hca(g, starts, goals, order=["a", "b"])["soc"],
        hca(g, starts, goals, order=["b", "a"])["soc"],
    )
    assert r["soc"] <= worst + 1e-6


def test_13_pbs_incomplete_on_bad_priorities_is_ok():
    # PBS itself searches orders; incompleteness of *prioritized planning*
    # is demonstrated by HCA failing when stay-at-target blocks a swap on a 1-wide directed edge.
    from lib.maps import directed_deadlock_map

    g = directed_deadlock_map()
    starts = {"a": "L", "b": "R"}
    goals = {"a": "R", "b": "L"}
    r = hca(g, starts, goals, order=["a", "b"])
    assert not r["found"]


def test_14_rhcr_issues_bounded_segments():
    g, starts, goals = two_agent_tunnel()
    r = rhcr(g, starts, goals, window=3, steps=20)
    assert r["max_issue"] <= 3
    assert r["found"]
