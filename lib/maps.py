"""Grid and directed topology maps used by algorithms, evals, and the studio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

Node = Union[Tuple[int, int], str]
GridPos = Tuple[int, int]


@dataclass
class GridMap:
    width: int
    height: int
    obstacles: set = field(default_factory=set)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, node: GridPos) -> bool:
        x, y = node
        return self.in_bounds(x, y) and (x, y) not in self.obstacles

    def neighbors(self, node: GridPos) -> List[Tuple[GridPos, float]]:
        x, y = node
        out: List[Tuple[GridPos, float]] = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (x + dx, y + dy)
            if self.passable(nxt):
                out.append((nxt, 1.0))
        return out

    def heuristic(self, a: GridPos, b: GridPos) -> float:
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def block(self, node: GridPos) -> None:
        self.obstacles.add(node)

    def unblock(self, node: GridPos) -> None:
        self.obstacles.discard(node)

    def to_studio(self) -> dict:
        return {
            "kind": "grid",
            "width": self.width,
            "height": self.height,
            "obstacles": [list(p) for p in sorted(self.obstacles)],
        }


@dataclass
class TopoNode:
    id: str
    x: float
    y: float
    kind: str = "normal"


@dataclass
class TopoMap:
    """Directed topology. An edge a→b does not imply b→a."""

    nodes: Dict[str, TopoNode] = field(default_factory=dict)
    edges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    no_pass: set = field(default_factory=set)

    def add_node(self, node_id: str, x: float, y: float, kind: str = "normal") -> None:
        self.nodes[node_id] = TopoNode(node_id, x, y, kind)
        self.edges.setdefault(node_id, {})

    def add_edge(self, a: str, b: str, cost: Optional[float] = None, bidir: bool = False) -> None:
        na, nb = self.nodes[a], self.nodes[b]
        if cost is None:
            cost = ((na.x - nb.x) ** 2 + (na.y - nb.y) ** 2) ** 0.5
        self.edges.setdefault(a, {})[b] = float(cost)
        if bidir:
            self.edges.setdefault(b, {})[a] = float(cost)

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        return list(self.edges.get(node, {}).items())

    def heuristic(self, a: str, b: str) -> float:
        na, nb = self.nodes[a], self.nodes[b]
        return ((na.x - nb.x) ** 2 + (na.y - nb.y) ** 2) ** 0.5

    def reverse_exists(self, a: str, b: str) -> bool:
        return a in self.edges.get(b, {})

    def to_studio(self) -> dict:
        edges = []
        for a, nbrs in self.edges.items():
            for b, cost in nbrs.items():
                edges.append(
                    {
                        "from": a,
                        "to": b,
                        "cost": round(cost, 3),
                        "bidir": self.reverse_exists(a, b),
                    }
                )
        return {
            "kind": "topo",
            "nodes": [
                {
                    "id": n.id,
                    "x": n.x,
                    "y": n.y,
                    "kind": n.kind,
                    "no_pass": n.id in self.no_pass,
                }
                for n in self.nodes.values()
            ],
            "edges": edges,
        }


def grid_open(w: int = 8, h: int = 8) -> GridMap:
    return GridMap(w, h, set())


def grid_wall() -> GridMap:
    obs = {(3, y) for y in range(0, 7)}
    return GridMap(8, 8, obs)


def grid_maze() -> GridMap:
    cells = """
........
.###.##.
.#......
.#.##.#.
....#.#.
.##.#.#.
.#......
........
"""
    rows = [r for r in cells.strip().splitlines()]
    obs = {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"}
    return GridMap(len(rows[0]), len(rows), obs)


def topo_oneway() -> TopoMap:
    m = TopoMap()
    coords = {
        "I0": (0, 2),
        "I1": (2, 2),
        "I2": (4, 2),
        "I3": (4, 0),
        "I4": (2, 0),
        "I5": (0, 0),
        "G0": (2, -1),
        "G1": (4, 3),
    }
    for i, (x, y) in coords.items():
        m.add_node(i, x, y, "goal" if i.startswith("G") else "intersection")
    for a, b in (("I0", "I1"), ("I1", "I2"), ("I2", "I3"), ("I3", "I4"), ("I4", "I5"), ("I5", "I0")):
        m.add_edge(a, b, cost=1.0)
    m.add_edge("I1", "I4", cost=1.0)
    m.add_edge("I4", "G0", cost=1.0, bidir=True)
    m.add_edge("I2", "G1", cost=1.0, bidir=True)
    m.no_pass.add("G0")
    return m


def corridor_headon() -> TopoMap:
    m = TopoMap()
    names = ["A", "C1", "C2", "C3", "B"]
    for i, n in enumerate(names):
        m.add_node(n, float(i), 0.0, "goal" if n in ("A", "B") else "normal")
    for i in range(len(names) - 1):
        m.add_edge(names[i], names[i + 1], cost=1.0, bidir=True)
    return m


def issued_segment_map() -> TopoMap:
    m = TopoMap()
    for i, name in enumerate(["P0", "P1", "P2", "P3", "P4", "P5"]):
        kind = "intersection" if name in ("P0", "P2", "P5") else "normal"
        m.add_node(name, float(i), 0.0, kind)
    m.add_node("S", 2.0, 1.0, "dock")
    for a, b in (("P0", "P1"), ("P1", "P2"), ("P2", "P3"), ("P3", "P4"), ("P4", "P5")):
        m.add_edge(a, b, cost=1.0, bidir=True)
    m.add_edge("P2", "S", cost=1.0, bidir=True)
    return m


def assign_cross_map() -> TopoMap:
    m = TopoMap()
    m.add_node("R0", 0, 1, "dock")
    m.add_node("R1", 0, 0, "dock")
    m.add_node("J", 1, 0.5, "intersection")
    m.add_node("G0", 2, 1, "goal")
    m.add_node("G1", 2, 0, "goal")
    for a, b in (("R0", "J"), ("R1", "J"), ("J", "G0"), ("J", "G1")):
        m.add_edge(a, b, cost=1.0, bidir=True)
    return m


def cbs_cardinal_map() -> GridMap:
    return GridMap(5, 3, {(1, 0), (1, 2), (3, 0), (3, 2)})


def pibt_swap_map() -> GridMap:
    return GridMap(4, 3, {(1, 1), (2, 1)})


def directed_deadlock_map() -> TopoMap:
    m = TopoMap()
    m.add_node("L", 0, 0, "goal")
    m.add_node("M", 1, 0, "normal")
    m.add_node("R", 2, 0, "goal")
    m.add_edge("L", "M", cost=1.0)
    m.add_edge("M", "R", cost=1.0)
    return m


def continuous_scene() -> dict:
    return {
        "kind": "continuous",
        "width": 1.0,
        "height": 1.0,
        "obstacles": [
            {"x": 0.5, "y": 0.5, "r": 0.18},
            {"x": 0.25, "y": 0.7, "r": 0.12},
            {"x": 0.75, "y": 0.3, "r": 0.12},
        ],
        "start": [0.08, 0.08],
        "goal": [0.92, 0.92],
    }


def encode_node(node: Node) -> Union[str, List[int]]:
    if isinstance(node, tuple):
        return [int(node[0]), int(node[1])]
    return str(node)
