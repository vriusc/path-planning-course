"""Joint A*, HCA*, WHCA*, PBS, RHCR + segment lock."""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Sequence, Tuple

from lib.agents import is_conflict_free, pad, soc
from lib.reservation import ReservationTable
from lib.search import SearchResult, astar
from lib.algos.temporal import time_astar


def _reserve_path(table: ReservationTable, path: List, agent: str, stay: int = 0) -> None:
    for t, node in enumerate(path):
        table.occupy(node, t, agent)
        if t + 1 < len(path):
            table.occupy_edge(node, path[t + 1], t, agent)
    if path and stay:
        for t in range(len(path), len(path) + stay):
            table.occupy(path[-1], t, agent)


def hca(graph, starts: Dict[str, object], goals: Dict[str, object], order: Optional[List[str]] = None) -> dict:
    order = order or list(starts)
    table = ReservationTable()
    paths = {}
    expanded = 0
    for agent in order:
        res = time_astar(graph, starts[agent], goals[agent], table=table, agent=agent)
        expanded += res.expanded
        if not res.found:
            return {"found": False, "paths": paths, "expanded": expanded, "soc": float("inf")}
        paths[agent] = res.path
        _reserve_path(table, res.path, agent)
    return {
        "found": is_conflict_free(paths),
        "paths": paths,
        "expanded": expanded,
        "soc": soc(paths),
        "order": order,
    }


def whca(
    graph,
    starts: Dict[str, object],
    goals: Dict[str, object],
    window: int = 4,
    order: Optional[List[str]] = None,
) -> dict:
    """Plan only the next `window` steps, treating later collisions as out of scope."""
    order = order or list(starts)
    table = ReservationTable()
    paths = {a: [starts[a]] for a in order}
    expanded = 0
    for agent in order:
        res = time_astar(
            graph,
            starts[agent],
            goals[agent],
            table=table,
            agent=agent,
            horizon=window,
            require_goal=False,
        )
        expanded += res.expanded
        if not res.found:
            # still keep a truncated wait
            paths[agent] = [starts[agent]] * (window + 1)
            continue
        clip = res.path[: window + 1]
        paths[agent] = clip
        _reserve_path(table, clip, agent)
    window_paths = {a: pad(p, window + 1)[: window + 1] for a, p in paths.items()}
    return {
        "found": is_conflict_free(window_paths),
        "paths": paths,
        "window_paths": window_paths,
        "expanded": expanded,
        "window": window,
    }


def joint_astar(graph, starts: Dict[str, object], goals: Dict[str, object], cap: int = 20000) -> dict:
    import heapq

    agents = list(starts)
    start_s = tuple(starts[a] for a in agents)
    goal_s = tuple(goals[a] for a in agents)
    heap = [(0, 0, start_s)]
    g = {start_s: 0}
    came = {start_s: None}
    expanded = 0
    while heap and expanded < cap:
        _f, cost, state = heapq.heappop(heap)
        expanded += 1
        if state == goal_s:
            path_states = []
            cur = state
            while cur is not None:
                path_states.append(cur)
                cur = came[cur]
            path_states.reverse()
            paths = {a: [st[i] for st in path_states] for i, a in enumerate(agents)}
            return {"found": True, "paths": paths, "expanded": expanded, "soc": soc(paths)}
        moves = []
        for i, a in enumerate(agents):
            opts = [state[i]] + [n for n, _ in graph.neighbors(state[i])]
            moves.append(opts)
        for combo in itertools.product(*moves):
            occupied = {}
            ok = True
            for i, node in enumerate(combo):
                if node in occupied:
                    ok = False
                    break
                occupied[node] = i
            if not ok:
                continue
            # edge swap
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    if combo[i] == state[j] and combo[j] == state[i] and combo[i] != state[i]:
                        ok = False
            if not ok:
                continue
            ng = cost + sum(0 if combo[i] == state[i] else 1 for i in range(len(agents)))
            if ng < g.get(combo, float("inf")):
                g[combo] = ng
                came[combo] = state
                h = sum(graph.heuristic(combo[i], goal_s[i]) for i in range(len(agents)))
                heapq.heappush(heap, (ng + h, ng, combo))
    return {"found": False, "paths": {}, "expanded": expanded, "soc": float("inf"), "capped": expanded >= cap}


def pbs(graph, starts: Dict[str, object], goals: Dict[str, object]) -> dict:
    """Depth-first search over pairwise priorities; low level is HCA*."""
    agents = list(starts)
    best = None
    seen = set()

    def search(order_constraints: List[Tuple[str, str]], remaining: List[str], depth: int = 0):
        nonlocal best
        if depth > 12:
            return
        key = tuple(sorted(order_constraints))
        if key in seen:
            return
        seen.add(key)
        # topological order from constraints
        from collections import defaultdict, deque

        succ = defaultdict(list)
        indeg = {a: 0 for a in agents}
        for hi, lo in order_constraints:
            succ[hi].append(lo)
            indeg[lo] += 1
        q = deque([a for a in agents if indeg[a] == 0])
        order = []
        while q:
            n = q.popleft()
            order.append(n)
            for s in succ[n]:
                indeg[s] -= 1
                if indeg[s] == 0:
                    q.append(s)
        if len(order) != len(agents):
            return  # cycle
        result = hca(graph, starts, goals, order=order)
        if result["found"]:
            if best is None or result["soc"] < best["soc"]:
                best = result
                best["constraints"] = list(order_constraints)
            return
        # find first collision between two agents and branch
        from lib.agents import vertex_conflicts, edge_conflicts

        paths = result.get("paths") or {}
        if len(paths) < 2:
            return
        confs = vertex_conflicts(paths) + [
            (a, b, u, t) for a, b, u, v, t in edge_conflicts(paths)
        ]
        if not confs:
            return
        a, b = confs[0][0], confs[0][1]
        for pair in ((a, b), (b, a)):
            search(order_constraints + [pair], remaining, depth + 1)

    search([], agents)
    if best is None:
        return {"found": False, "paths": {}, "soc": float("inf")}
    return best


def rhcr(
    graph,
    starts: Dict[str, object],
    goals: Dict[str, object],
    window: int = 4,
    steps: int = 12,
) -> dict:
    """Rolling window: each iteration issue <= window nodes and simulate them."""
    pos = dict(starts)
    issued_log = []
    full_paths = {a: [starts[a]] for a in starts}
    for _ in range(steps):
        plan = whca(graph, pos, goals, window=window)
        issued = {}
        for a, path in plan["paths"].items():
            seg = path[: window]
            issued[a] = seg
            if len(seg) > 1:
                pos[a] = seg[min(1, len(seg) - 1)]
                full_paths[a].append(pos[a])
            if pos[a] == goals[a] and full_paths[a][-1] != goals[a]:
                full_paths[a].append(goals[a])
        issued_log.append(issued)
        if all(pos[a] == goals[a] for a in starts):
            break
    return {
        "found": all(full_paths[a][-1] == goals[a] for a in starts),
        "paths": full_paths,
        "issued": issued_log,
        "window": window,
        "max_issue": max((len(seg) for batch in issued_log for seg in batch.values()), default=0),
    }
