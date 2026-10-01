"""Greedy, Hungarian, auction, TPTS, CBS-TA."""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from lib.algos.cbs import cbs
from lib.search import astar, dijkstra


def cost_matrix(graph, robots: Sequence[str], starts: Dict, tasks: Sequence[str], use_topo: bool = True):
    m = []
    for r in robots:
        row = []
        for g in tasks:
            if use_topo:
                res = dijkstra(graph, starts[r], g, record=False)
                row.append(res.cost if res.found else 1e6)
            else:
                row.append(graph.heuristic(starts[r], g))
        m.append(row)
    return m


def linear_sum_assignment(cost):
    """Hungarian algorithm for square or rectangular min-cost assignment. Returns (rows, cols)."""
    n = len(cost)
    m = len(cost[0]) if cost else 0
    # pad to square
    k = max(n, m)
    inf = 1e12
    a = [[inf] * k for _ in range(k)]
    for i in range(n):
        for j in range(m):
            a[i][j] = cost[i][j]
    # Munkres
    u = [0.0] * (k + 1)
    v = [0.0] * (k + 1)
    p = [0] * (k + 1)
    way = [0] * (k + 1)
    for i in range(1, k + 1):
        p[0] = i
        j0 = 0
        minv = [inf] * (k + 1)
        used = [False] * (k + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = inf
            j1 = 0
            for j in range(1, k + 1):
                if used[j]:
                    continue
                cur = a[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(k + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    cols = []
    rows = []
    for j in range(1, k + 1):
        i = p[j]
        if i - 1 < n and j - 1 < m:
            rows.append(i - 1)
            cols.append(j - 1)
    return rows, cols


def greedy_assign(graph, robots, starts, tasks) -> dict:
    remaining = list(tasks)
    assign = {}
    total = 0.0
    used = set()
    for r in robots:
        best, best_t = float("inf"), None
        for t in remaining:
            res = dijkstra(graph, starts[r], t, record=False)
            if res.found and res.cost < best:
                best, best_t = res.cost, t
        if best_t is None:
            return {"found": False, "assign": assign, "cost": float("inf")}
        assign[r] = best_t
        total += best
        remaining.remove(best_t)
    return {"found": True, "assign": assign, "cost": total, "matrix": cost_matrix(graph, robots, starts, tasks)}


def hungarian_assign(graph, robots, starts, tasks) -> dict:
    mat = cost_matrix(graph, robots, starts, tasks, use_topo=True)
    eu = cost_matrix(graph, robots, starts, tasks, use_topo=False)
    row, col = linear_sum_assignment(mat)
    assign = {robots[i]: tasks[j] for i, j in zip(row, col)}
    total = float(sum(mat[i][j] for i, j in zip(row, col)))
    return {
        "found": True,
        "assign": assign,
        "cost": total,
        "matrix": mat,
        "euclidean": eu,
        "used_topo": True,
    }


def auction_assign(graph, robots, starts, tasks, arrivals: Sequence[str] | None = None) -> dict:
    """Sequential single-item auction: each arriving task goes to the cheapest free robot."""
    free = list(robots)
    assign = {}
    total = 0.0
    stream = list(arrivals) if arrivals is not None else list(tasks)
    for task in stream:
        if not free:
            break
        bids = []
        for r in free:
            res = dijkstra(graph, starts[r], task, record=False)
            bids.append((res.cost if res.found else 1e6, r))
        bids.sort()
        cost, winner = bids[0]
        assign[winner] = task
        total += cost
        free.remove(winner)
    return {"found": len(assign) == min(len(robots), len(tasks)), "assign": assign, "cost": total}


def tpts(graph, robots, starts, task_stream: List[Tuple[str, object]], allow_swap: bool = True) -> dict:
    """Token passing: idle robot takes nearest remaining task; optional swap if crossing."""
    from lib.algos.prioritized import hca

    idle = list(robots)
    pos = dict(starts)
    remaining = list(task_stream)
    assign = {r: None for r in robots}
    completed = []
    headon = 0
    while remaining or any(assign[r] for r in robots):
        for r in list(idle):
            if not remaining:
                break
            costs = []
            for name, goal in remaining:
                res = astar(graph, pos[r], goal, record=False)
                costs.append((res.cost if res.found else 1e6, name, goal))
            costs.sort()
            _c, name, goal = costs[0]
            assign[r] = (name, goal)
            remaining = [t for t in remaining if t[0] != name]
            idle.remove(r)
        active = {r: assign[r][1] for r in robots if assign[r]}
        if not active:
            break
        plan = hca(graph, {r: pos[r] for r in active}, active)
        if not plan["found"] and allow_swap and len(active) == 2:
            rs = list(active)
            assign[rs[0]], assign[rs[1]] = assign[rs[1]], assign[rs[0]]
            active = {r: assign[r][1] for r in rs}
            plan = hca(graph, {r: pos[r] for r in rs}, active)
            headon += 1
        elif not plan["found"]:
            headon += 1
            # force wait
            break
        for r, path in plan["paths"].items():
            if path:
                pos[r] = path[-1]
            if pos[r] == assign[r][1]:
                completed.append(assign[r][0])
                assign[r] = None
                idle.append(r)
        if not remaining and all(assign[r] is None for r in robots):
            break
    return {
        "found": len(completed) == len(task_stream),
        "completed": completed,
        "headon": headon,
        "allow_swap": allow_swap,
    }


def cbs_ta(graph, robots, starts, tasks) -> dict:
    """Enumerate assignments by increasing Hungarian residual; run CBS on each (tiny n)."""
    hung = hungarian_assign(graph, robots, starts, tasks)
    goals = hung["assign"]
    planned = cbs(graph, starts, goals)
    planned["assign"] = goals
    planned["assign_cost"] = hung["cost"]
    # compare with greedy-then-cbs
    greedy = greedy_assign(graph, robots, starts, tasks)
    greedy_plan = cbs(graph, starts, greedy["assign"]) if greedy["found"] else {"found": False, "soc": float("inf")}
    planned["greedy_soc"] = greedy_plan.get("soc", float("inf"))
    return planned
