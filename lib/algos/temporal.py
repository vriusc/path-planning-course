"""Time-expanded A* and SIPP."""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from lib.reservation import ReservationTable
from lib.search import SearchResult


def _rebuild(came, state):
    path = []
    cur = state
    while cur is not None:
        path.append(cur[0])
        cur = came[cur]
    path.reverse()
    return path


def time_astar(
    graph,
    start,
    goal,
    table: Optional[ReservationTable] = None,
    agent: str = "a",
    horizon: int = 80,
    record: bool = False,
    require_goal: bool = True,
) -> SearchResult:
    table = table or ReservationTable()
    heap = []
    g = {(start, 0): 0.0}
    came = {(start, 0): None}
    heapq.heappush(heap, (graph.heuristic(start, goal), 0, start, 0))
    expanded = 0
    seen = set()
    best_partial = None
    best_h = float("inf")
    while heap:
        _f, cost, node, t = heapq.heappop(heap)
        state = (node, t)
        if state in seen:
            continue
        seen.add(state)
        expanded += 1
        h = graph.heuristic(node, goal)
        if h < best_h or (h == best_h and t > 0):
            best_h = h
            best_partial = state
        if node == goal:
            path = _rebuild(came, state)
            return SearchResult(path, float(cost), expanded, [], True)
        if t >= horizon:
            continue
        candidates = [(node, 1.0)] + list(graph.neighbors(node))  # wait + moves
        for nxt, step_cost in candidates:
            nt = t + 1
            if not table.vertex_free(nxt, nt, agent):
                continue
            if nxt != node and not table.edge_free(node, nxt, t, agent):
                continue
            ns = (nxt, nt)
            ng = cost + step_cost
            if ng < g.get(ns, float("inf")):
                g[ns] = ng
                came[ns] = state
                heapq.heappush(heap, (ng + graph.heuristic(nxt, goal), ng, nxt, nt))
    if not require_goal and best_partial is not None:
        path = _rebuild(came, best_partial)
        return SearchResult(path, float(g[best_partial]), expanded, [], True, {"partial": True})
    return SearchResult([], float("inf"), expanded, [], False)


def sipp(
    graph,
    start,
    goal,
    table: Optional[ReservationTable] = None,
    agent: str = "a",
    horizon: int = 80,
) -> SearchResult:
    """Safe-interval search. State = (node, interval_index, arrive_time)."""
    table = table or ReservationTable()
    intervals = {start: table.safe_intervals(start, horizon, agent)}

    def ivals(n):
        if n not in intervals:
            intervals[n] = table.safe_intervals(n, horizon, agent)
        return intervals[n]

    heap = []
    start_iv = None
    for i, (lo, hi) in enumerate(ivals(start)):
        if lo <= 0 < hi:
            start_iv = i
            break
    if start_iv is None:
        return SearchResult([], float("inf"), 0, [], False)
    g = {(start, start_iv): 0}
    came = {(start, start_iv): None}
    heapq.heappush(heap, (graph.heuristic(start, goal), 0, start, start_iv))
    expanded = 0
    seen = set()
    while heap:
        _f, arr, node, ii = heapq.heappop(heap)
        state = (node, ii)
        if state in seen:
            continue
        seen.add(state)
        expanded += 1
        lo, hi = ivals(node)[ii]
        if node == goal:
            path_states = []
            cur = state
            times = {state: arr}
            # reconstruct via came; we also store arr in g
            chain = []
            while cur is not None:
                chain.append(cur)
                cur = came[cur]
            chain.reverse()
            path = [c[0] for c in chain]
            # expand waits: g[state] is arrival
            return SearchResult(path, float(g[state]), expanded, [], True, {"states": expanded})
        for nxt, step in graph.neighbors(node):
            move_t = arr + 1  # unit time topology/grid
            for jj, (nlo, nhi) in enumerate(ivals(nxt)):
                if move_t >= nhi:
                    continue
                earliest = max(move_t, nlo)
                if earliest >= nhi:
                    continue
                if not table.edge_free(node, nxt, earliest - 1, agent):
                    continue
                ns = (nxt, jj)
                if earliest < g.get(ns, float("inf")):
                    g[ns] = earliest
                    came[ns] = state
                    heapq.heappush(heap, (earliest + graph.heuristic(nxt, goal), earliest, nxt, jj))
        # wait in place until interval end is already encoded by staying in interval
    return SearchResult([], float("inf"), expanded, [], False, {"states": expanded})
