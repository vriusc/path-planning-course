"""Plain-text traces so a lesson can be read without the studio widget."""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

Pos = Tuple[int, int]


def draw_grid(
    width: int,
    height: int,
    *,
    obstacles: Iterable[Pos] = (),
    start: Optional[Pos] = None,
    goal: Optional[Pos] = None,
    path: Sequence[Pos] = (),
    open_nodes: Iterable[Pos] = (),
    closed: Iterable[Pos] = (),
    current: Optional[Pos] = None,
) -> str:
    obs = set(obstacles)
    op = set(open_nodes)
    cl = set(closed)
    pa = set(path)
    rows = []
    legend = "S起点 G终点 #墙 .空 o待扩展 x已扩展 *当前 @路径"
    rows.append(legend)
    for y in range(height):
        line = []
        for x in range(width):
            p = (x, y)
            if p == current:
                ch = "*"
            elif start is not None and p == start and p not in pa:
                ch = "S"
            elif goal is not None and p == goal and p not in pa:
                ch = "G"
            elif p in pa:
                ch = "@"
            elif p in obs:
                ch = "#"
            elif p in op:
                ch = "o"
            elif p in cl:
                ch = "x"
            else:
                ch = "."
            line.append(ch)
        rows.append("".join(line))
    return "\n".join(rows)


def print_step(i: int, caption: str, grid: str, extra: str = "") -> None:
    print(f"\n—— 第 {i} 步：{caption} ——")
    print(grid)
    if extra:
        print(extra)
