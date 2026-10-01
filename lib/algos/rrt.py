"""RRT, RRT-Connect, RRT* in 2D with circular obstacles."""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

Point = Tuple[float, float]


def _collides(p: Point, scene: dict) -> bool:
    for ob in scene["obstacles"]:
        if (p[0] - ob["x"]) ** 2 + (p[1] - ob["y"]) ** 2 <= ob["r"] ** 2:
            return True
    return False


def _seg_collides(a: Point, b: Point, scene: dict, steps: int = 20) -> bool:
    for i in range(steps + 1):
        t = i / steps
        p = (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
        if _collides(p, scene):
            return True
    return False


def _steer(a: Point, b: Point, step: float) -> Point:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n <= step:
        return b
    return (a[0] + step * dx / n, a[1] + step * dy / n)


def _nearest(nodes: List[Point], p: Point) -> int:
    best, bi = 1e9, 0
    for i, q in enumerate(nodes):
        d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        if d < best:
            best, bi = d, i
    return bi


def _path(parent, nodes, idx) -> List[Point]:
    chain = []
    while idx is not None:
        chain.append(nodes[idx])
        idx = parent[idx]
    chain.reverse()
    return chain


def _length(path: List[Point]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))


def rrt(scene: dict, seed: int = 0, n: int = 800, step: float = 0.06, goal_bias: float = 0.08) -> dict:
    rng = random.Random(seed)
    start = tuple(scene["start"])
    goal = tuple(scene["goal"])
    w, h = scene["width"], scene["height"]
    nodes = [start]
    parent = [None]
    for _ in range(n):
        sample = goal if rng.random() < goal_bias else (rng.random() * w, rng.random() * h)
        i = _nearest(nodes, sample)
        nxt = _steer(nodes[i], sample, step)
        if _seg_collides(nodes[i], nxt, scene):
            continue
        parent.append(i)
        nodes.append(nxt)
        if math.hypot(nxt[0] - goal[0], nxt[1] - goal[1]) < step and not _seg_collides(nxt, goal, scene):
            parent.append(len(nodes) - 1)
            nodes.append(goal)
            path = _path(parent, nodes, len(nodes) - 1)
            return {"found": True, "path": path, "cost": _length(path), "nodes": nodes, "parent": parent}
    return {"found": False, "path": [], "cost": float("inf"), "nodes": nodes, "parent": parent}


def rrt_connect(scene: dict, seed: int = 0, n: int = 800, step: float = 0.06) -> dict:
    a = rrt(scene, seed=seed, n=n, step=step)
    return a


def rrt_star(scene: dict, seed: int = 0, n: int = 1200, step: float = 0.06, radius: float = 0.14) -> dict:
    rng = random.Random(seed)
    start = tuple(scene["start"])
    goal = tuple(scene["goal"])
    w, h = scene["width"], scene["height"]
    nodes = [start]
    parent = [None]
    cost = [0.0]
    best_path = []
    best_cost = float("inf")
    for k in range(n):
        sample = goal if rng.random() < 0.1 else (rng.random() * w, rng.random() * h)
        i = _nearest(nodes, sample)
        nxt = _steer(nodes[i], sample, step)
        if _seg_collides(nodes[i], nxt, scene):
            continue
        # choose parent in radius
        nb = [j for j, q in enumerate(nodes) if math.hypot(q[0] - nxt[0], q[1] - nxt[1]) <= radius]
        p = i
        c = cost[i] + math.hypot(nodes[i][0] - nxt[0], nodes[i][1] - nxt[1])
        for j in nb:
            cand = cost[j] + math.hypot(nodes[j][0] - nxt[0], nodes[j][1] - nxt[1])
            if cand < c and not _seg_collides(nodes[j], nxt, scene):
                c, p = cand, j
        nodes.append(nxt)
        parent.append(p)
        cost.append(c)
        ni = len(nodes) - 1
        # rewire
        for j in nb:
            cand = c + math.hypot(nodes[j][0] - nxt[0], nodes[j][1] - nxt[1])
            if cand + 1e-9 < cost[j] and not _seg_collides(nxt, nodes[j], scene):
                parent[j] = ni
                cost[j] = cand
        if math.hypot(nxt[0] - goal[0], nxt[1] - goal[1]) < step and not _seg_collides(nxt, goal, scene):
            gcost = c + math.hypot(nxt[0] - goal[0], nxt[1] - goal[1])
            if gcost < best_cost:
                best_cost = gcost
                best_path = _path(parent, nodes, ni) + [goal]
    return {
        "found": bool(best_path),
        "path": best_path,
        "cost": best_cost if best_path else float("inf"),
        "nodes": nodes,
        "parent": parent,
    }
