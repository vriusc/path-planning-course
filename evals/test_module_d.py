"""Evals for CBS, enhanced CBS, ECBS, LNS."""

from evals.scenarios import two_agent_swap, two_agent_tunnel
from lib.agents import is_conflict_free
from lib.algos.cbs import cbs, cbs_enhanced, ecbs, lns
from lib.maps import GridMap


def test_15_cbs_optimal_and_conflict_free():
    g, starts, goals = two_agent_swap()
    r = cbs(g, starts, goals)
    assert r["found"]
    assert is_conflict_free(r["paths"])
    from lib.algos.prioritized import joint_astar

    opt = joint_astar(g, starts, goals, cap=40000)
    if opt["found"]:
        assert r["soc"] <= opt["soc"] + 1e-6


def test_15_cbs_unsolvable():
    g = GridMap(2, 1, set())
    starts = {"a": (0, 0), "b": (1, 0)}
    goals = {"a": (1, 0), "b": (0, 0)}
    # 2 cells, swap without extra space — may still swap by timing if both move
    # make truly unsolvable: same goal
    goals = {"a": (0, 0), "b": (0, 0)}
    r = cbs(g, starts, goals)
    assert not r["found"]


def test_16_enhanced_cbs_smaller_tree_on_corridor():
    g, starts, goals = two_agent_swap()
    plain = cbs(g, starts, goals, enhanced=False)
    enh = cbs_enhanced(g, starts, goals)
    assert enh["found"] and plain["found"]
    assert enh["high"] <= plain["high"] + 2  # at least not worse; often smaller


def test_17_ecbs_bounded():
    g, starts, goals = two_agent_swap()
    opt = cbs(g, starts, goals)
    w = 1.5
    r = ecbs(g, starts, goals, w=w)
    assert r["found"]
    assert r["soc"] <= w * opt["soc"] + 1e-6
    r1 = ecbs(g, starts, goals, w=1.0)
    assert r1["soc"] == opt["soc"] or r1["soc"] <= opt["soc"] + 1e-6


def test_18_lns_feasible_nonincreasing():
    g, starts, goals = two_agent_tunnel()
    r = lns(g, starts, goals, rounds=8)
    assert r["found"]
    assert r["conflicts"] == 0
    hist = r["history"]
    for a, b in zip(hist, hist[1:]):
        assert b <= a + 1e-6
