"""Space-time reservation table, segment locks, and safe intervals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, List, Optional, Set, Tuple

Node = Hashable
Interval = Tuple[int, int]  # [start, end)  end exclusive; inf as a large int


@dataclass
class ReservationTable:
    vertex: Dict[Tuple[Node, int], str] = field(default_factory=dict)
    edge: Dict[Tuple[Node, Node, int], str] = field(default_factory=dict)
    issued: Set[Node] = field(default_factory=set)
    issued_by: Dict[Node, str] = field(default_factory=dict)

    def occupy(self, node: Node, t: int, agent: str) -> bool:
        key = (node, t)
        holder = self.vertex.get(key)
        if holder is not None and holder != agent:
            return False
        self.vertex[key] = agent
        return True

    def occupy_edge(self, a: Node, b: Node, t: int, agent: str) -> bool:
        if self.edge.get((a, b, t)) not in (None, agent):
            return False
        if self.edge.get((b, a, t)) not in (None, agent):
            return False
        self.edge[(a, b, t)] = agent
        return True

    def free(self, node: Node, t: int, agent: str) -> None:
        if self.vertex.get((node, t)) == agent:
            del self.vertex[(node, t)]

    def issue_segment(self, nodes: List[Node], agent: str) -> bool:
        for n in nodes:
            holder = self.issued_by.get(n)
            if holder is not None and holder != agent:
                return False
        for n in nodes:
            self.issued.add(n)
            self.issued_by[n] = agent
        return True

    def release_segment(self, nodes: List[Node], agent: str) -> None:
        for n in nodes:
            if self.issued_by.get(n) == agent:
                self.issued.discard(n)
                self.issued_by.pop(n, None)

    def vertex_free(self, node: Node, t: int, agent: str) -> bool:
        holder = self.vertex.get((node, t))
        return holder is None or holder == agent

    def edge_free(self, a: Node, b: Node, t: int, agent: str) -> bool:
        return self.edge.get((a, b, t)) in (None, agent) and self.edge.get((b, a, t)) in (None, agent)

    def safe_intervals(self, node: Node, horizon: int, agent: str) -> List[Interval]:
        blocked = sorted(t for (n, t), who in self.vertex.items() if n == node and who != agent and t < horizon)
        intervals: List[Interval] = []
        start = 0
        for t in blocked:
            if t > start:
                intervals.append((start, t))
            start = t + 1
        if start < horizon:
            intervals.append((start, horizon))
        return intervals
