"""Priority-queue search primitives shared by BFS / Dijkstra / A* family."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Sequence, Tuple

Node = Hashable


@dataclass
class SearchResult:
    path: List[Node]
    cost: float
    expanded: int
    frames: List[dict] = field(default_factory=list)
    found: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.path:
            self.found = False


def reconstruct(came_from: Dict[Node, Optional[Node]], goal: Node) -> List[Node]:
    path = [goal]
    while came_from.get(path[-1]) is not None:
        path.append(came_from[path[-1]])  # type: ignore[arg-type]
    path.reverse()
    return path


def snapshot(open_nodes, closed, current, g_map, h_fn, goal, came_from, caption: str) -> dict:
    def pack(n):
        g = g_map.get(n, 0.0)
        h = h_fn(n, goal) if goal is not None else 0.0
        return {
            "id": n if not isinstance(n, tuple) else list(n),
            "g": round(float(g), 3),
            "h": round(float(h), 3),
            "f": round(float(g + h), 3),
            "parent": (
                None
                if came_from.get(n) is None
                else (list(came_from[n]) if isinstance(came_from[n], tuple) else came_from[n])
            ),
        }

    return {
        "open": [pack(n) for n in open_nodes],
        "closed": [pack(n) for n in closed],
        "current": pack(current) if current is not None else None,
        "caption": caption,
        "path": [],
    }


def bfs(graph, start: Node, goal: Node, record: bool = True) -> SearchResult:
    q = deque([start])
    came_from: Dict[Node, Optional[Node]] = {start: None}
    g = {start: 0.0}
    closed = []
    frames = []
    expanded = 0
    while q:
        cur = q.popleft()
        expanded += 1
        closed.append(cur)
        if record:
            frames.append(
                snapshot(list(q), closed, cur, g, lambda a, b: 0.0, goal, came_from, f"扩展 {cur}")
            )
        if cur == goal:
            path = reconstruct(came_from, goal)
            if frames:
                frames[-1]["path"] = [list(p) if isinstance(p, tuple) else p for p in path]
            return SearchResult(path, g[cur], expanded, frames, True)
        for nxt, _cost in graph.neighbors(cur):
            if nxt in came_from:
                continue
            came_from[nxt] = cur
            g[nxt] = g[cur] + 1.0
            q.append(nxt)
    return SearchResult([], float("inf"), expanded, frames, False)


def dijkstra(graph, start: Node, goal: Node, record: bool = True) -> SearchResult:
    return best_first(graph, start, goal, heuristic=lambda a, b: 0.0, weight=1.0, record=record)


def astar(
    graph,
    start: Node,
    goal: Node,
    heuristic: Optional[Callable] = None,
    weight: float = 1.0,
    record: bool = True,
) -> SearchResult:
    h = heuristic or graph.heuristic
    return best_first(graph, start, goal, heuristic=h, weight=weight, record=record)


def best_first(
    graph,
    start: Node,
    goal: Node,
    heuristic: Callable,
    weight: float = 1.0,
    record: bool = True,
) -> SearchResult:
    heap: List[Tuple[float, int, Node]] = []
    counter = 0
    g = {start: 0.0}
    came_from: Dict[Node, Optional[Node]] = {start: None}
    heapq.heappush(heap, (weight * heuristic(start, goal), counter, start))
    open_set = {start}
    closed = []
    frames = []
    expanded = 0
    visited_pop = set()
    while heap:
        _f, _, cur = heapq.heappop(heap)
        if cur in visited_pop:
            continue
        visited_pop.add(cur)
        open_set.discard(cur)
        expanded += 1
        closed.append(cur)
        if record:
            frames.append(
                snapshot(
                    list(open_set),
                    closed,
                    cur,
                    g,
                    lambda a, b: weight * heuristic(a, b),
                    goal,
                    came_from,
                    f"扩展 {cur}  g={g[cur]:.1f}",
                )
            )
        if cur == goal:
            path = reconstruct(came_from, goal)
            if frames:
                frames[-1]["path"] = [list(p) if isinstance(p, tuple) else p for p in path]
            return SearchResult(path, g[cur], expanded, frames, True, {"weight": weight})
        for nxt, cost in graph.neighbors(cur):
            tentative = g[cur] + cost
            if tentative < g.get(nxt, float("inf")):
                came_from[nxt] = cur
                g[nxt] = tentative
                counter += 1
                f = tentative + weight * heuristic(nxt, goal)
                heapq.heappush(heap, (f, counter, nxt))
                open_set.add(nxt)
    return SearchResult([], float("inf"), expanded, frames, False, {"weight": weight})


def path_cost(graph, path: Sequence[Node]) -> float:
    if not path or len(path) == 1:
        return 0.0 if path else float("inf")
    total = 0.0
    for a, b in zip(path, path[1:]):
        costs = {n: c for n, c in graph.neighbors(a)}
        if b not in costs:
            return float("inf")
        total += costs[b]
    return total



