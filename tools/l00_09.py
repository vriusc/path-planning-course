"""Textbook lessons 00–09: graphs through SIPP. Built in the notebook, not imported as a black box."""

from tools.nb import BOOT, code, md
from tools.l_search_wiki import lesson_01, lesson_02, lesson_03
from tools.l_wiki_04_09 import (
    lesson_04, lesson_05, lesson_06, lesson_07, lesson_08, lesson_09,
)

PATH = code(BOOT)


def lesson_00():
    return "00_overview", "00 这门课在学什么：图、路径、三层问题", [
        md("""
本课目标：弄清「找路」到底是什么问题，以及后面每一课在哪一层。

你不需要任何路径规划基础。需要会一点 Python：变量、列表、`for`、`if`、函数。数据结构（队列、堆）我们会当场讲。

## 1. 问题长什么样

一台车（或机器人、游戏角色）在一张地图上，要从 **起点 S** 走到 **终点 G**，不能穿墙。

「走」的规则要先说死，否则算法没法写：

- 地图被切成格子，或被抽象成若干命名点（路口、工位）。
- 相邻且中间没墙，才能一步走过去。
- 每一步有代价：格子图常常是 1；拓扑图常常是边的长度。

一条 **路径** 就是一串点：`S → … → G`，每相邻两点都合法。

## 2. 图：后面所有算法的共同语言

**图** = 点（顶点）+ 点之间的连线（边）。

| 现实 | 图里叫什么 |
|------|------------|
| 格子 / 路口 / 工位 | 顶点 |
| 「可以从 A 走到 B」 | 边 A→B |
| 这一步有多远、多费时 | 边的权重 |
| 单行道 | 只有 A→B，没有 B→A |

网格是一种特殊的图：每个格子连上、下、左、右（四连通）。后面 Dijkstra、A*、多车算法，都是在图上搜。

## 3. 三层问题（不要混在一起）

1. **单车最短路**：只有一台车，找一条合法、尽量短的路。01–09。
2. **多车不撞**：多台车同时走，点、边、时间不能抢。10–21。
3. **任务指派**：哪台车去哪个目标。22–25。

先把第 1 层写会，第 2 层只是「在第 1 层外面再套约束」。

## 4. 怎么读后面的课

每课按百科条目写，结构固定：

1. **定义**：输入、输出、历史。
2. **和谁相邻**：跟上一课、下一课差在哪。
3. **不变量 / 定理**：为什么对、保证什么、不保证什么。
4. **伪代码**：和后面 Python 一一对应。
5. **手算表**：先自己填，再对打印。
6. **一段一段写代码**，每段上面说明；用打印看搜索过程。
7. **常见 bug**、对照库、练习。调度台在最后，可跳过。

请按单元格顺序 Shift+Enter。不要跳过手算和打印。
"""),
        PATH,
        md("""先确认环境。下面这格只做两件事：打印课程根目录、画一张 8×8 空网格。还没有任何寻路。"""),
        code("""
from lib.maps import grid_open
from lib.pretty import draw_grid

print("课程根目录:", ROOT)
g = grid_open(8, 8)
print(draw_grid(g.width, g.height, start=(0, 0), goal=(7, 7)))
print("\\n每个点是一个格子。S 是起点，G 是终点，点是空地。下一课我们在这种图上写 BFS。")
"""),
        md("""有向拓扑长这样：点有名字，边有方向。金色箭头的含义到第 02 课再讲；现在只要知道「图不一定是格子」。"""),
        code("""
from lib.maps import topo_oneway
g = topo_oneway()
print("顶点:", sorted(g.nodes))
print("从 I0 能直接走到:", g.neighbors("I0"))
print("从 I1 能直接走到:", g.neighbors("I1"))
print("注意：I1 的邻居里没有 I0 —— 这是单行。")
"""),
        md("""## 练习

1. 用纸画 3×3 格子，标出 (0,0) 的四个邻居。角上的格子为什么只有两个邻居？
2. 若规定「只能向右或向上」，图还是无向的吗？

下一课：用队列一层一层扩，写出第一个完整寻路算法 BFS。
"""),
    ]


LESSONS_00_09 = [
    lesson_00(),
    lesson_01(),
    lesson_02(),
    lesson_03(),
    lesson_04(),
    lesson_05(),
    lesson_06(),
    lesson_07(),
    lesson_08(),
    lesson_09(),
]
