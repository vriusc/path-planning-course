"""Weighted A*, D* Lite, Jump Point Search."""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from lib.maps import GridMap
from lib.search import SearchResult, astar, reconstruct


def weighted_astar(graph, start, goal, weight: float = 1.5, record: bool = True) -> SearchResult:
    return astar(graph, start, goal, weight=weight, record=record)


# ----- D* Lite (Koenig & Likhachev), grid / graph with unit or weighted edges -----

class DStarLite:
    def __init__(self, graph, start, goal):
        self.graph = graph
        self.start = start
        self.goal = goal
        self.g: Dict = {}
        self.rhs: Dict = {}
        self.U = []
        self.km = 0.0
        self.expanded = 0
        self.last = start
        inf = float("inf")
        self.g[goal] = inf
        self.rhs[goal] = 0.0
        self._insert(goal, self._key(goal))

    def _h(self, a, b):
        return self.graph.heuristic(a, b)

    def _key(self, u):
        g = min(self.g.get(u, float("inf")), self.rhs.get(u, float("inf")))
        return (g + self._h(self.start, u) + self.km, g)

    def _insert(self, u, key):
        self.U.append((key, u))
        self.U.sort(key=lambda x: x[0])

    def _update_vertex(self, u):
        if u != self.goal:
            best = float("inf")
            for v, c in self.graph.neighbors(u):
                best = min(best, c + self.g.get(v, float("inf")))
            # also consider reverse neighbors for rhs: we need predecessors
            # On an undirected grid, neighbors == predecessors.
            self.rhs[u] = best
        self.U = [(k, x) for k, x in self.U if x != u]
        if self.g.get(u, float("inf")) != self.rhs.get(u, float("inf")):
            self._insert(u, self._key(u))

    def _predecessors(self, u):
        # For directed graphs, scan all nodes that list u as neighbor.
        if hasattr(self.graph, "edges"):
            preds = []
            for a, nbrs in self.graph.edges.items():
                if u in nbrs:
                    preds.append((a, nbrs[u]))
            return preds
        return self.graph.neighbors(u)

    def compute(self) -> SearchResult:
        while self.U and (
            self.U[0][0] < self._key(self.start)
            or self.rhs.get(self.start, float("inf")) != self.g.get(self.start, float("inf"))
        ):
            k_old, u = self.U.pop(0)
            self.expanded += 1
            if k_old < self._key(u):
                self._insert(u, self._key(u))
            elif self.g.get(u, float("inf")) > self.rhs.get(u, float("inf")):
                self.g[u] = self.rhs[u]
                for s, _c in self._predecessors(u):
                    self._update_vertex(s)
            else:
                self.g[u] = float("inf")
                self._update_vertex(u)
                for s, _c in self._predecessors(u):
                    self._update_vertex(s)
        path = self._extract_path()
        cost = 0.0
        if path:
            for a, b in zip(path, path[1:]):
                cost += dict(self.graph.neighbors(a)).get(b, float("inf"))
        return SearchResult(path, cost, self.expanded, [], bool(path), {"g": dict(self.g)})

    def _extract_path(self) -> List:
        if self.rhs.get(self.start, float("inf")) == float("inf"):
            return []
        path = [self.start]
        cur = self.start
        seen = {cur}
        while cur != self.goal:
            best, nxt = float("inf"), None
            for v, c in self.graph.neighbors(cur):
                val = c + self.g.get(v, float("inf"))
                if val < best:
                    best, nxt = val, v
            if nxt is None or nxt in seen:
                return []
            path.append(nxt)
            seen.add(nxt)
            cur = nxt
        return path

    def edge_blocked(self, a, b):
        """Call after the graph has already been mutated (edge removed / cell blocked)."""
        self.km += self._h(self.last, self.start)
        self.last = self.start
        self._update_vertex(a)
        if hasattr(self.graph, "edges"):
            self._update_vertex(b)


def dstar_lite(graph, start, goal) -> SearchResult:
    planner = DStarLite(graph, start, goal)
    return planner.compute()


# ----- Jump Point Search on 4-connected grids (Harabor & Grastien) -----

def _dir(a, b):
    return (0 if b[0] == a[0] else (1 if b[0] > a[0] else -1),
            0 if b[1] == a[1] else (1 if b[1] > a[1] else -1))


def jps(grid: GridMap, start, goal, record: bool = True) -> SearchResult:
    if not isinstance(grid, GridMap):
        return SearchResult([], float("inf"), 0, [], False, {"inapplicable": True})

    def blocked(x, y):
        return not grid.passable((x, y))

    def forced(nx, ny, dx, dy):
        if dx != 0 and dy == 0:
            return (blocked(nx, ny - 1) and not blocked(nx + dx, ny - 1)) or (
                blocked(nx, ny + 1) and not blocked(nx + dx, ny + 1)
            )
        if dy != 0 and dx == 0:
            return (blocked(nx - 1, ny) and not blocked(nx - 1, ny + dy)) or (
                blocked(nx + 1, ny) and not blocked(nx + 1, ny + dy)
            )
        return False

    def jump(x, y, dx, dy):
        nx, ny = x + dx, y + dy
        if blocked(nx, ny):
            return None
        if (nx, ny) == goal or forced(nx, ny, dx, dy):
            return (nx, ny)
        further = jump(nx, ny, dx, dy)
        if further is not None:
            return further
        return (nx, ny)

    def successors(node, parent):
        x, y = node
        succs = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jp = jump(x, y, dx, dy)
            if jp and jp != node:
                succs.append(jp)
        return succs

    import heapq

    heap = []
    g = {start: 0.0}
    came = {start: None}
    heapq.heappush(heap, (grid.heuristic(start, goal), start))
    expanded = 0
    closed: Set = set()
    frames = []
    while heap:
        _f, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        parent = came[cur]
        if record:
            frames.append(
                {
                    "open": [],
                    "closed": [list(c) for c in closed],
                    "current": {"id": list(cur), "g": g[cur], "h": grid.heuristic(cur, goal), "f": 0, "parent": None},
                    "caption": f"JPS 扩展 {cur}",
                    "path": [],
                }
            )
        if cur == goal:
            path = reconstruct(came, goal)
            # fill skipped cells between jump points
            filled = [path[0]]
            for a, b in zip(path, path[1:]):
                dx = 0 if b[0] == a[0] else (1 if b[0] > a[0] else -1)
                dy = 0 if b[1] == a[1] else (1 if b[1] > a[1] else -1)
                p = a
                while p != b:
                    p = (p[0] + dx, p[1] + dy)
                    filled.append(p)
            if frames:
                frames[-1]["path"] = [list(p) for p in filled]
            return SearchResult(filled, float(len(filled) - 1), expanded, frames, True)
        for jp in successors(cur, parent):
            step = abs(jp[0] - cur[0]) + abs(jp[1] - cur[1])
            ng = g[cur] + step
            if ng < g.get(jp, float("inf")):
                g[jp] = ng
                came[jp] = cur
                heapq.heappush(heap, (ng + grid.heuristic(jp, goal), jp))
    return SearchResult([], float("inf"), expanded, frames, False)
