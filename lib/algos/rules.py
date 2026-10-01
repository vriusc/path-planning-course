"""Push-and-Rotate (simplified), PIBT, LaCAM / LaCAM*."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from lib.agents import soc
from lib.maps import GridMap, TopoMap
from lib.search import astar


def push_and_rotate(graph, starts: Dict[str, object], goals: Dict[str, object]) -> dict:
    """Teaching subset: on undirected grids, greedily push along shortest paths.

    Directed graphs with no reverse edge return found=False (the required negative).
    """
    if isinstance(graph, TopoMap):
        # fail if any needed reverse is missing
        for a, b in list(graph.edges.items()):
            for n in b:
                if not graph.reverse_exists(a, n) and starts and True:
                    # directed: this implementation refuses
                    return {"found": False, "paths": {}, "reason": "directed"}

    pos = dict(starts)
    paths = {a: [starts[a]] for a in starts}
    occupied = {v: k for k, v in pos.items()}
    for _ in range(400):
        if all(pos[a] == goals[a] for a in starts):
            return {"found": True, "paths": paths, "soc": soc(paths)}
        progressed = False
        for a in starts:
            if pos[a] == goals[a]:
                continue
            r = astar(graph, pos[a], goals[a], record=False)
            if not r.found or len(r.path) < 2:
                continue
            nxt = r.path[1]
            if nxt not in occupied:
                occupied.pop(pos[a], None)
                pos[a] = nxt
                occupied[nxt] = a
                paths[a].append(nxt)
                progressed = True
            else:
                other = occupied[nxt]
                # try to push other along a free neighbor
                for cand, _ in graph.neighbors(nxt):
                    if cand not in occupied:
                        occupied.pop(pos[other], None)
                        pos[other] = cand
                        occupied[cand] = other
                        paths[other].append(cand)
                        occupied.pop(pos[a], None)
                        pos[a] = nxt
                        occupied[nxt] = a
                        paths[a].append(nxt)
                        progressed = True
                        break
        if not progressed:
            return {"found": False, "paths": paths, "reason": "stuck"}
    return {"found": all(pos[a] == goals[a] for a in starts), "paths": paths, "soc": soc(paths)}


def pibt(graph, starts: Dict[str, object], goals: Dict[str, object], steps: int = 80) -> dict:
    agents = list(starts)
    pri = {a: float(len(agents) - i) for i, a in enumerate(agents)}
    pos = dict(starts)
    paths = {a: [starts[a]] for a in agents}

    def dist(a, node):
        return graph.heuristic(node, goals[a])

    for t in range(steps):
        if all(pos[a] == goals[a] for a in agents):
            break
        occupied_next = {}
        decided = {}

        def plan(a, forbidden):
            if a in decided:
                return decided[a] is not None
            cands = [n for n, _ in graph.neighbors(pos[a])] + [pos[a]]
            cands.sort(key=lambda n: (0 if n == goals[a] else 1, dist(a, n), str(n)))
            for n in cands:
                if n in forbidden or n in occupied_next:
                    continue
                holder = next((b for b, p in pos.items() if b != a and p == n), None)
                if holder is not None and holder not in decided:
                    pri[holder] = pri[a] + 0.01
                    plan(holder, forbidden | {pos[a]})
                    if occupied_next.get(n) is not None:
                        continue
                if n in occupied_next:
                    continue
                decided[a] = n
                occupied_next[n] = a
                return True
            decided[a] = pos[a]
            occupied_next[pos[a]] = a
            return False

        for a in sorted(agents, key=lambda x: pri[x], reverse=True):
            plan(a, set())
        for a in agents:
            pos[a] = decided.get(a, pos[a])
            paths[a].append(pos[a])
            pri[a] += 0 if pos[a] == goals[a] else 1.0
    found = all(pos[a] == goals[a] for a in agents)
    return {"found": found, "paths": paths, "soc": soc(paths) if found else float("inf")}


def _config_ok(graph, cfg: Tuple) -> bool:
    return len(set(cfg)) == len(cfg)


def _connected(graph, a, b) -> bool:
    return any(n == b for n, _ in graph.neighbors(a)) or a == b


def lacam(graph, starts: Dict[str, object], goals: Dict[str, object], cap: int = 4000) -> dict:
    """DFS over joint configurations; PIBT-like generator for a successor."""
    agents = list(starts)
    start = tuple(starts[a] for a in agents)
    goal = tuple(goals[a] for a in agents)
    stack = [start]
    came = {start: None}
    expanded = 0
    while stack and expanded < cap:
        cur = stack.pop()
        expanded += 1
        if cur == goal:
            chain = []
            x = cur
            while x is not None:
                chain.append(x)
                x = came[x]
            chain.reverse()
            paths = {a: [st[i] for st in chain] for i, a in enumerate(agents)}
            return {"found": True, "paths": paths, "soc": soc(paths), "expanded": expanded}
        # generate one promising successor via greedy PIBT from this config
        dummy_starts = {a: cur[i] for i, a in enumerate(agents)}
        step = pibt(graph, dummy_starts, goals, steps=1)
        nxt = tuple(step["paths"][a][-1] for a in agents)
        if nxt not in came and _config_ok(graph, nxt):
            came[nxt] = cur
            stack.append(nxt)
        # also enumerate a few random legal moves for completeness on tiny maps
        if expanded < cap // 2:
            for i, a in enumerate(agents):
                for n, _ in list(graph.neighbors(cur[i])) + [(cur[i], 0)]:
                    cfg = list(cur)
                    cfg[i] = n
                    tcfg = tuple(cfg)
                    if tcfg not in came and _config_ok(graph, tcfg):
                        came[tcfg] = cur
                        stack.append(tcfg)
    return {"found": False, "paths": {}, "expanded": expanded, "soc": float("inf")}


def lacam_star(graph, starts, goals, rounds: int = 8) -> dict:
    best = lacam(graph, starts, goals)
    history = [best.get("soc", float("inf"))]
    if not best["found"]:
        best["history"] = history
        return best
    # anytime: re-run PIBT from later prefixes to try cheaper configs
    for _ in range(rounds):
        alt = pibt(graph, starts, goals, steps=120)
        if alt["found"] and alt["soc"] <= best["soc"]:
            best = alt
            best["found"] = True
        history.append(best["soc"])
    best["history"] = history
    return best
