"""Evals for Push-and-Rotate, PIBT, LaCAM."""

from evals.scenarios import two_agent_tunnel
from lib.algos.rules import lacam, lacam_star, pibt, push_and_rotate
from lib.maps import directed_deadlock_map, grid_open


def test_19_push_rotate_undirected_ok():
    g = grid_open(4, 3)
    starts = {"a": (0, 0), "b": (3, 0)}
    goals = {"a": (0, 2), "b": (3, 2)}
    r = push_and_rotate(g, starts, goals)
    assert r["found"]


def test_19_push_rotate_directed_fails():
    g = directed_deadlock_map()
    r = push_and_rotate(g, {"a": "L", "b": "R"}, {"a": "R", "b": "L"})
    assert not r["found"]


def test_20_pibt_sparse_reaches():
    g, starts, goals = two_agent_tunnel()
    r = pibt(g, starts, goals, steps=200)
    assert r["found"]


def test_20_pibt_directed_deadlock():
    g = directed_deadlock_map()
    r = pibt(g, {"a": "L", "b": "R"}, {"a": "R", "b": "L"}, steps=20)
    assert not r["found"]


def test_21_lacam_small_complete():
    g, starts, goals = two_agent_tunnel()
    r = lacam(g, starts, goals, cap=8000)
    assert r["found"]


def test_21_lacam_star_nonincreasing():
    g, starts, goals = two_agent_tunnel()
    r = lacam_star(g, starts, goals, rounds=4)
    assert r["found"]
    hist = r["history"]
    for a, b in zip(hist, hist[1:]):
        assert b <= a + 1e-6
