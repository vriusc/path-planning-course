"""Multi-agent helpers: conflicts, SOC, stay-at-target padding."""

from __future__ import annotations

from typing import Dict, Hashable, List, Sequence, Tuple

Node = Hashable
Path = List[Node]


def pad(path: Path, length: int) -> Path:
    if not path:
        return path
    if len(path) >= length:
        return path[:length]
    return path + [path[-1]] * (length - len(path))


def makespan(paths: Dict[str, Path]) -> int:
    return max((len(p) - 1 for p in paths.values()), default=0)


def soc(paths: Dict[str, Path]) -> int:
    total = 0
    for p in paths.values():
        t = len(p) - 1
        while t > 0 and p[t] == p[t - 1]:
            t -= 1
        total += t
    return total


def vertex_conflicts(paths: Dict[str, Path]) -> List[Tuple[str, str, Node, int]]:
    agents = list(paths)
    T = max((len(p) for p in paths.values()), default=0)
    padded = {a: pad(paths[a], T) for a in agents}
    hits = []
    for i, a in enumerate(agents):
        for b in agents[i + 1 :]:
            for t in range(T):
                if padded[a][t] == padded[b][t]:
                    hits.append((a, b, padded[a][t], t))
    return hits


def edge_conflicts(paths: Dict[str, Path]) -> List[Tuple[str, str, Node, Node, int]]:
    agents = list(paths)
    T = max((len(p) for p in paths.values()), default=0)
    padded = {a: pad(paths[a], T) for a in agents}
    hits = []
    for i, a in enumerate(agents):
        for b in agents[i + 1 :]:
            for t in range(T - 1):
                if padded[a][t] == padded[b][t + 1] and padded[a][t + 1] == padded[b][t]:
                    hits.append((a, b, padded[a][t], padded[a][t + 1], t))
    return hits


def is_conflict_free(paths: Dict[str, Path]) -> bool:
    return not vertex_conflicts(paths) and not edge_conflicts(paths)
