"""Evals for RRT / RRT*."""

from lib.algos.rrt import rrt, rrt_star
from lib.maps import continuous_scene


def test_26_rrt_finds_path_fixed_seed():
    scene = continuous_scene()
    r = rrt(scene, seed=1, n=1500, step=0.05)
    assert r["found"]
    assert r["path"][0] == tuple(scene["start"]) or list(r["path"][0]) == scene["start"]


def test_27_rrt_star_not_worse_than_rrt_same_seed():
    scene = continuous_scene()
    a = rrt(scene, seed=2, n=900, step=0.05)
    b = rrt_star(scene, seed=2, n=1400, step=0.05)
    assert b["found"]
    if a["found"]:
        assert b["cost"] <= a["cost"] + 1e-6
    more = rrt_star(scene, seed=2, n=2000, step=0.05)
    assert more["cost"] <= b["cost"] + 1e-6
