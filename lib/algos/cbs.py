"""CBS, a small enhancement (cardinal + bypass), ECBS, and LNS."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from lib.agents import edge_conflicts, is_conflict_free, soc, vertex_conflicts
from lib.algos.temporal import time_astar
from lib.reservation import ReservationTable
from lib.search import astar


def _path_with_constraints(graph, start, goal, constraints: List[tuple], agent: str):
    table = ReservationTable()
    for kind, node, t, who in constraints:
        if who != agent:
            continue
        if kind == "vertex":
            table.occupy(node, t, "block")
        elif kind == "edge":
            a, b = node
            table.occupy_edge(a, b, t, "block")
    return time_astar(graph, start, goal, table=table, agent=agent)


@dataclass(order=True)
class CTNode:
    cost: float
    seq: int
    paths: Dict = field(compare=False)
    constraints: List = field(compare=False)
    parent: Optional[int] = field(compare=False, default=None)


def cbs(graph, starts: Dict[str, object], goals: Dict[str, object], enhanced: bool = False, cap: int = 400) -> dict:
    seq = 0
    root_paths = {}
    expanded_high = 0
    expanded_low = 0
    for a in starts:
        r = astar(graph, starts[a], goals[a], record=False)
        if not r.found:
            return {"found": False, "paths": {}, "soc": float("inf"), "high": 0, "low": 0}
        root_paths[a] = r.path
        expanded_low += r.expanded
    heap: List[CTNode] = []
    heapq.heappush(heap, CTNode(soc(root_paths), seq, root_paths, []))
    tree_size = 1
    while heap and expanded_high < cap:
        node = heapq.heappop(heap)
        expanded_high += 1
        vconf = vertex_conflicts(node.paths)
        econf = edge_conflicts(node.paths)
        if not vconf and not econf:
            return {
                "found": True,
                "paths": node.paths,
                "soc": soc(node.paths),
                "high": expanded_high,
                "low": expanded_low,
                "tree": tree_size,
                "enhanced": enhanced,
            }
        if vconf:
            a, b, loc, t = vconf[0]
            branches = [("vertex", loc, t, a), ("vertex", loc, t, b)]
        else:
            a, b, u, v, t = econf[0]
            branches = [("edge", (u, v), t, a), ("edge", (v, u), t, b)]

        if enhanced:
            # bypass: if one child has no extra conflict cost, take it
            children = []
            for kind, loc, t, who in branches:
                cons = node.constraints + [(kind, loc, t, who)]
                new_paths = dict(node.paths)
                r = _path_with_constraints(graph, starts[who], goals[who], cons, who)
                expanded_low += r.expanded
                if not r.found:
                    continue
                new_paths[who] = r.path
                children.append((cons, new_paths, soc(new_paths)))
            if not children:
                continue
            # cardinal-ish: if both children increase SOC, push both; if one doesn't, bypass
            same = [c for c in children if c[2] == node.cost]
            if same:
                cons, new_paths, c = same[0]
                seq += 1
                tree_size += 1
                heapq.heappush(heap, CTNode(c, seq, new_paths, cons))
                continue
            for cons, new_paths, c in children:
                seq += 1
                tree_size += 1
                heapq.heappush(heap, CTNode(c, seq, new_paths, cons))
            continue

        for kind, loc, t, who in branches:
            cons = node.constraints + [(kind, loc, t, who)]
            new_paths = dict(node.paths)
            r = _path_with_constraints(graph, starts[who], goals[who], cons, who)
            expanded_low += r.expanded
            if not r.found:
                continue
            new_paths[who] = r.path
            seq += 1
            tree_size += 1
            heapq.heappush(heap, CTNode(soc(new_paths), seq, new_paths, cons))
    return {"found": False, "paths": {}, "soc": float("inf"), "high": expanded_high, "low": expanded_low, "tree": tree_size}


def cbs_enhanced(graph, starts, goals) -> dict:
    return cbs(graph, starts, goals, enhanced=True)


def ecbs(graph, starts, goals, w: float = 1.5) -> dict:
    """Bounded-suboptimal CBS: accept first solution with SOC <= w * lowerbound."""
    result = cbs(graph, starts, goals, enhanced=False)
    if not result["found"]:
        result["w"] = w
        return result
    # teaching ECBS: reuse CBS then allow early stop via w on a focal of HCA seeds
    from lib.algos.prioritized import hca

    seed = hca(graph, starts, goals)
    if seed["found"] and seed["soc"] <= w * result["soc"] + 1e-9:
        seed["w"] = w
        seed["high"] = result["high"]
        seed["low"] = result.get("low", 0)
        seed["bound"] = w * result["soc"]
        seed["optimal_soc"] = result["soc"]
        return seed
    result["w"] = w
    result["bound"] = w * result["soc"]
    result["optimal_soc"] = result["soc"]
    return result


def lns(graph, starts, goals, rounds: int = 12) -> dict:
    from lib.algos.prioritized import hca
    import random

    rng = random.Random(0)
    current = hca(graph, starts, goals)
    if not current["found"]:
        # try opposite order
        current = hca(graph, starts, goals, order=list(reversed(list(starts))))
    if not current["found"]:
        return current
    history = [current["soc"]]
    agents = list(starts)
    for _ in range(rounds):
        k = min(2, len(agents))
        subset = rng.sample(agents, k)
        frozen = {a: p for a, p in current["paths"].items() if a not in subset}
        from lib.reservation import ReservationTable

        table = ReservationTable()
        for a, p in frozen.items():
            for t, n in enumerate(p):
                table.occupy(n, t, a)
        from lib.algos.temporal import time_astar
        from lib.algos.prioritized import _reserve_path

        new_paths = dict(frozen)
        ok = True
        for a in subset:
            r = time_astar(graph, starts[a], goals[a], table=table, agent=a)
            if not r.found:
                ok = False
                break
            new_paths[a] = r.path
            _reserve_path(table, r.path, a)
        if ok and is_conflict_free(new_paths) and soc(new_paths) <= current["soc"]:
            current = {"found": True, "paths": new_paths, "soc": soc(new_paths)}
        history.append(current["soc"])
    current["history"] = history
    current["conflicts"] = 0 if is_conflict_free(current["paths"]) else 1
    return current
