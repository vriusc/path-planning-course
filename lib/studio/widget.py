"""PlannerStudio: anywidget yard board."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import anywidget
import traitlets

from lib.maps import encode_node

_DIR = Path(__file__).parent


class PlannerStudio(anywidget.AnyWidget):
    _esm = _DIR / "widget.js"
    _css = _DIR / "widget.css"

    map = traitlets.Dict({}).tag(sync=True)
    frames = traitlets.List([]).tag(sync=True)
    step = traitlets.Int(0).tag(sync=True)
    metrics = traitlets.Dict({}).tag(sync=True)
    eval = traitlets.Dict({"status": "idle"}).tag(sync=True)
    algo = traitlets.Unicode("").tag(sync=True)
    title = traitlets.Unicode("调度台").tag(sync=True)
    click = traitlets.Dict({}).tag(sync=True)

    def show_search(self, graph_studio: dict, result, algo: str, eval_status: Optional[dict] = None):
        self.map = graph_studio
        self.algo = algo
        frames = result.frames if getattr(result, "frames", None) else []
        if not frames:
            frames = [
                {
                    "caption": "结果",
                    "path": [encode_node(n) for n in getattr(result, "path", [])],
                    "open": [],
                    "closed": [],
                }
            ]
        else:
            frames = list(frames)
            if getattr(result, "path", None) and frames:
                frames[-1] = dict(frames[-1])
                frames[-1]["path"] = [encode_node(n) for n in result.path]
        self.frames = frames
        self.step = 0
        self.metrics = {
            "found": bool(getattr(result, "found", False)),
            "cost": _num(getattr(result, "cost", None)),
            "expanded": getattr(result, "expanded", None),
        }
        self.eval = eval_status or {"status": "idle"}
        return self

    def show_multi(self, graph_studio: dict, payload: dict, algo: str, eval_status: Optional[dict] = None):
        self.map = graph_studio
        self.algo = algo
        paths = payload.get("paths") or {}
        frames = payload.get("frames")
        if not frames:
            frames = _agent_frames(paths, payload.get("caption", algo))
        self.frames = frames
        self.step = 0
        self.metrics = {
            "found": bool(payload.get("found")),
            "cost": _num(payload.get("soc") or payload.get("cost")),
            "expanded": payload.get("expanded") or payload.get("high"),
            "high": payload.get("high"),
            "conflicts": payload.get("conflicts"),
        }
        self.eval = eval_status or {"status": "idle"}
        return self

    def show_rrt(self, scene: dict, payload: dict, algo: str, eval_status: Optional[dict] = None):
        self.map = scene
        self.algo = algo
        self.frames = [
            {
                "caption": algo,
                "path": payload.get("path") or [],
                "rrt_nodes": payload.get("nodes") or [],
                "rrt_parent": payload.get("parent") or [],
            }
        ]
        self.step = 0
        self.metrics = {
            "found": bool(payload.get("found")),
            "cost": _num(payload.get("cost")),
            "expanded": len(payload.get("nodes") or []),
        }
        self.eval = eval_status or {"status": "idle"}
        return self


def frames_from_search(result) -> List[dict]:
    return list(getattr(result, "frames", []) or [])


def _agent_frames(paths: Dict[str, list], caption: str) -> List[dict]:
    if not paths:
        return [{"caption": caption, "agents": [], "path": []}]
    T = max(len(p) for p in paths.values())
    names = list(paths)
    frames = []
    for t in range(T):
        agents = []
        for i, a in enumerate(names):
            p = paths[a]
            pos = p[min(t, len(p) - 1)]
            trail = [encode_node(x) for x in p[: min(t + 1, len(p))]]
            agents.append({"id": a, "pos": encode_node(pos), "trail": trail})
        frames.append({"caption": f"{caption}  t={t}", "agents": agents, "path": []})
    return frames


def _num(x):
    if x is None:
        return None
    try:
        if x == float("inf"):
            return "inf"
        return round(float(x), 3)
    except (TypeError, ValueError):
        return x


def run_and_show(studio: PlannerStudio, algo: str, fn, studio_map: dict, eval_fn=None):
    t0 = time.perf_counter()
    result = fn()
    ms = round((time.perf_counter() - t0) * 1000, 2)
    status = {"status": "idle"}
    if eval_fn is not None:
        try:
            eval_fn(result)
            status = {"status": "pass"}
        except AssertionError as e:
            status = {"status": "fail", "detail": str(e)}
    if hasattr(result, "frames"):
        studio.show_search(studio_map, result, algo, status)
        met = dict(studio.metrics)
        met["ms"] = ms
        studio.metrics = met
    elif isinstance(result, dict) and "nodes" in result and "path" in result:
        studio.show_rrt(studio_map, result, algo, status)
        met = dict(studio.metrics)
        met["ms"] = ms
        studio.metrics = met
    else:
        studio.show_multi(studio_map, result if isinstance(result, dict) else {"found": False}, algo, status)
        met = dict(studio.metrics)
        met["ms"] = ms
        studio.metrics = met
    return result
