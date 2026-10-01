"""Wiki-style lessons 04–09: weighted A*, D* Lite, JPS, locks, time A*, SIPP."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_04():
    return "04_weighted_astar", "04 加权 A*：有界次优（w-admissible）", [
        md("""
本课按百科条目写：先定义，再界限定理，再从第 03 课的 A* **只改一行** 写出加权 A*。调度台在最后，可跳过。

---

## 1. 定义

**加权 A\\***（Weighted A\\*，Pohl 1970 前后；也叫 \(w\)-A\\*、inflated A\\*）把 A\\* 的键改成

\\[
f_w(n)=g(n)+w\\,h(n),\\qquad w\\ge 1
\\]

- 输入：图、起点、终点、可采纳启发 \(h\)、权重 \(w\\ge 1\)。
- 输出：一条 \(s\\leadsto t\) 路径，其代价 \(\\mathrm{cost}\\le w\\cdot OPT\)（见第 3 节）。路径的 **真实代价仍是 \(g(t)\)**，不是 \(f_w(t)\)。

直观：\(w>1\) 时更听信「还剩多少」，堆会更早弹出靠近终点的点，扩展更少，路可能更绕。

Anytime / ARA\\*：先用大 \(w\) 很快出解，再把 \(w\) 降到 1 改善。本课只实现 **固定 \(w\)**。

---

## 2. 和 A* / Dijkstra / 贪心的关系

| 算法 | 堆键 | 保证 |
|------|------|------|
| Dijkstra / UCS | \(g\) | 最优（\(w\\ge 0\)） |
| A\\* | \(g+h\) | \(h\) 可采纳 ⇒ 最优 |
| 加权 A\\* | \(g+w h\) | \(h\) 可采纳 ⇒ \(\\le w\\cdot OPT\) |
| 贪心最佳优先 | \(h\) | 无 |

\(w=1\) 就是 A\\*。\(w\\to\\infty\) 时 \(g\) 相对可忽略，行为接近贪心。

网上还有 \(f=g/w+h\) 或 \(f=g+(2w-1)h\)。界限陈述不同。本仓库与 Wikipedia 常见形式一致：`g + w*h`。

---

## 3. 不变量（w-admissible）

设 \(h\) 可采纳（从不高估剩余）。加权 A\\* 弹出终点时：

\\[
g(t)\\le w\\cdot OPT
\\]

证明梗概（对照 03 课 A\\* 最优证明）：最优路上第一个还在 open 的点 \(n\) 满足 \(g(n)=g^*(n)\)，且 \(h(n)\\le h^*(n)\)，于是

\\[
f_w(n)=g^*(n)+w h(n)\\le w\\big(g^*(n)+h^*(n)\\big)=w\\cdot OPT
\\]

堆先弹 \(f_w\) 最小的。若返回的 \(g(t)>w\\cdot OPT\)，则当时 \(f_w(t)\\ge g(t)>w\\cdot OPT\\ge f_w(n)\)，应先扩展 \(n\) 而不是终点。矛盾。

**注意：**

- \(w<1\) 没有「比最优还短」这回事，证明直接坏掉（\(w h\) 可能比真剩余还小得过头，堆序乱）。
- 不一致但可采纳的 \(h\) 加上「关闭后永不重开」，界限仍常被引用，严格证明要更小心。本课网格曼哈顿是一致的。
- 返回值必须读 **g**，不要把 \(f_w\) 当路径长。

---

## 4. 伪代码（与下面 Python 只差一个 \(w\)）

```
function WeightedAStar(G, s, t, h, w):
    g[s] ← 0;  came_from[s] ← NIL
    push heap (w * h(s), s)
    closed ← ∅
    while heap 非空:
        (f, u) ← pop 最小 f
        if u ∈ closed: continue          # 惰性堆过期条目
        关闭 u
        if u = t: return Reconstruct(came_from, t)
        for each 边 (u, v, c):
            alt ← g[u] + c
            if alt < g[v]:
                g[v] ← alt
                came_from[v] ← u
                push heap (alt + w * h(v), v)
    return FAILURE
```

复杂度同 A\\*：惰性堆 \(O(E\\log E)\)。\(w\) 越大 **实际** 扩展越少，最坏仍可能扫全图（\(h=0\) 或墙把启发「骗」没了）。

---

## 5. 手算（同一点、三个 w）

四连通、步长 1，曼哈顿。某点 \(g=4\)，\(h=6\)：

| w | f = g+w h | 含义 |
|---|-----------|------|
| 1 | 10 | 普通 A\\* |
| 1.5 | 13 | 略偏信启发 |
| 3 | 22 | 很偏信启发 |

另一个更靠近终点的点 \(g=8\)，\(h=1\)：

- w=1：f=9，比上面的 10 还小，A\\* 会先扩这个「已经走远但离终点近」的点。
- w=3：f=11，而第一点 f=22，堆会 **更早** 扩第二点——哪怕它的 g 更大。

墙图 S=(0,0)、G=(7,7)、竖墙 x=3 且 y=0..6、缺口 (3,7)：\(h(S)=14\)。w 越大，搜索越贴着「看起来朝 G」的格子，可能早早钻进死胡同再绕回来，路径变长、扩展变少。
"""),
        PATH,
        md("""
## 6. 实现：从第 03 课的 A* 加参数 w

下面这段就是 03 课的 `astar`，只多一个 `weight`，松弛后的堆键写成 `tentative + weight * h(...)`。
"""),
        code("""
import heapq
from lib.maps import grid_wall
from lib.pretty import draw_grid


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct(came_from, goal):
    node = goal
    path = [node]
    while came_from[node] is not None:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path


def weighted_astar(graph, start, goal, weight=1.0, h=manhattan, verbose=False):
    # weight=1 必须退回普通 A*。不要把 weight 写进 g。
    heap = []
    counter = 0
    g_score = {start: 0.0}
    came_from = {start: None}
    heapq.heappush(heap, (weight * h(start, goal), counter, start))
    closed = set()
    expanded = 0
    while heap:
        _f, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        g_cur = g_score[current]
        if verbose and expanded <= 8:
            hn = h(current, goal)
            print(f"弹出 {current}  g={g_cur:.0f}  h={hn:.0f}  f={g_cur + weight * hn:.1f}")
        if current == goal:
            return reconstruct(came_from, goal), g_cur, expanded
        for nxt, cost in graph.neighbors(current):
            tentative = g_cur + cost
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                counter += 1
                # 相对 A* 的唯一改动：键是 g + w*h
                heapq.heappush(heap, (tentative + weight * h(nxt, goal), counter, nxt))
    return None, float("inf"), expanded


graph = grid_wall()
s, t = (0, 0), (7, 7)
print(draw_grid(graph.width, graph.height, obstacles=graph.obstacles, start=s, goal=t))
print("w=1 前 8 次弹出：")
p1, c1, e1 = weighted_astar(graph, s, t, weight=1.0, verbose=True)
print("路径代价(g)", c1, "扩展", e1)
"""),
        md("""
## 7. 逐行（相对 A*）

| 位置 | 干什么 |
|------|--------|
| `weight=1` 默认 | 退回 A\\*，便于对照 |
| 起点键 `weight * h(s)` | g(s)=0，f=w h |
| `tentative = g_cur + cost` | 真实代价，**不含** w |
| `push (tentative + weight * h(nxt))` | 唯一改动 |
| 返回 `g_cur` | 给评测、给「是否 ≤ w·OPT」 |

---

## 8. 实验：界限成立吗？扩展少了吗？
"""),
        code("""
opt_path, opt, opt_e = weighted_astar(graph, s, t, weight=1.0)
print("OPT", opt, "扩展", opt_e)
for w in (1.0, 1.5, 3.0, 10.0):
    path, cost, n_exp = weighted_astar(graph, s, t, weight=w)
    bound = w * opt
    ok = cost <= bound + 1e-9
    print(f"w={w:4}  代价={cost:5}  上限={bound:6.1f}  扩展={n_exp:4}  界限={ok}  比OPT长={cost - opt:.0f}")
"""),
        md("""
你应看到：w 变大 → 扩展下降（这张墙图上很明显），代价 **不小于** OPT，且不超过 `w*OPT`。

「w 越大路径单调变长」**不成立**：堆序一变，可能碰巧走出和 OPT 一样的路，也可能某次中间 w 更绕。界限是上界，不是单调性。

---

## 9. 常见 bug

1. 把 \(f_w\) 当路径长打印：数字里含 h，看起来「比 Dijkstra 还长一截」，其实没走那么远。
2. `w<1`：证明作废，还可能比「可采纳 A\\*」扩得更怪。
3. 以为加权 A\\* 路径更短：通常 **更长、更快**。
4. 用不可采纳 h 再乘 w：连 \(w\\cdot OPT\) 都不保证。
5. 和 anytime 搞混：固定 w 跑一次就结束，不会自动降 w。

**库对照：** `lib.search.astar(..., weight=w)` 与上面同一行。`lib.algos.single_agent.weighted_astar` 只是它的别名。
"""),
        code("""
from lib.search import astar as astar_lib

r = astar_lib(graph, s, t, weight=1.5, record=False)
print("库 weight=1.5 代价", r.cost, "扩展", r.expanded, "extra", r.extra)
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.search import astar as astar_lib

r = astar_lib(graph, s, t, weight=1.5)
studio = PlannerStudio()
studio.show_search({**graph.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "weighted A*")
studio
"""),
        md("""单步：波前比 w=1 更尖、更朝 G。墙右侧仍要等绕过缺口。

## 条目小结

| 项目 | 内容 |
|------|------|
| 公式 | \(f=g+w h\)，\(w\\ge 1\) |
| 保证 | h 可采纳 ⇒ 代价 \(\\le w\\cdot OPT\) |
| 实现差 | 相对 A\\* 只改堆键 |
| 退化 | w=1 → A\\*；w 很大 → 接近贪心 |
| 下一课 | 图中途变了 → D\\* Lite，不必每次重跑 A\\* |

## 练习

1. 证明或举反例：w 越大，返回路径的 g **单调**变长。
2. 连续两次：先 w=3 再 w=1。第二次不应比 OPT 差。自己跑。
3. 把 `return` 改成返回 `_f` 而不是 `g_cur`，w=3 时数字会怎样？为什么评测会误判？
"""),
    ]


def lesson_05():
    return "05_dstar_lite", "05 D* Lite：从目标往回的增量最短路", [
        md("""
本课按百科条目写。D\\* Lite 是「地图会变」时的增量最短路，不是又一种 A\\* 启发。调度台在最后。

---

## 1. 定义

**D\\* Lite**（Koenig & Likhachev, AAAI 2002 / 后续期刊）在 **边权变化** 后重修最短路，尽量复用上一次的 g 值。机器人向目标走、前方突然堵住，是典型场景。

名字来自 Stentz 的 D\\*（Dynamic A\\*）；Lite 用一套更简单的 rhs/g 维护，效果同类。

它从 **目标** 向全图传播「还要花多少」，类似反向 Dijkstra，但每个点留两个数，好做局部更新。

- 输入：图、当前起点 `start`、目标 `goal`。之后可多次：改边权 / 封格子，再 `compute`。
- 输出：当前 start 到 goal 的一条最短路（边权非负时）。

---

## 2. 和 A* / 普通重规划

| | 再跑一次 A\\* | D\\* Lite |
|--|--|--|
| 搜索方向 | 从当前点向前 | 从目标向后 |
| 图变化 | 整棵搜索树作废 | 只把受影响点标成不一致，再传播 |
| 一次查询 | 更简单、常数小 | 多次重规划、变化局部时更强 |
| 实现 | 03 课就会 | 要维护 rhs、U、km |

若地图只规划一次，用 A\\*。若每走一步前方都可能多一堵墙，才值得 D\\* Lite。

---

## 3. 不变量：g 与 rhs

每个点 u：

- \(g(u)\)：目前记下的、u 到目标的代价（可能过期）。
- \(rhs(u)=\\min_{v\\in succs(u)}\\big(c(u,v)+g(v)\\big)\)。目标规定 \(rhs(goal)=0\)。

含义：rhs 是「假如下一步走到某个后继，再用那个后继已记下的 g」的一拍前瞻。

| 关系 | 名称 | 算法做什么 |
|------|------|------------|
| \(g=rhs\) | 局部一致 | 这个点的值可信 |
| \(g>rhs\) | 过一致 over-consistent | 发现了更好的，把 g 降到 rhs，再通知前驱 |
| \(g<rhs\) | 欠一致 under-consistent | 某条便宜边没了，把 g 抬到 ∞ 再重算 |

优先队列 U 里是 **不一致** 的点。键是二元组（教学版用列表排序）：

\\[
k(u)=\\big(\\min(g,rhs)+h(start,u)+km,\\; \\min(g,rhs)\\big)
\\]

\(h(start,u)\) 把更新从当前机器人位置「拉」过来。\(km\) 是机器人移动后的启发修正，避免每次重排整个堆。

**主循环停：** U 空，或堆顶键不优于 `Key(start)`，且 start 已局部一致。此时从 start 每步走到使 \(c+g(v)\) 最小的邻居，得到最短路。

---

## 4. 伪代码（对照下面 MiniDStar 与库 `DStarLite`）

```
rhs[goal] ← 0;  g 其余视为 ∞
U.insert(goal, Key(goal))

ComputeShortestPath:
    while U 非空 且 (U.TopKey < Key(start) 或 rhs[start] ≠ g[start]):
        u ← U.pop()
        if g[u] > rhs[u]:          # 过一致：变好了
            g[u] ← rhs[u]
            对每个前驱 s: UpdateVertex(s)
        else:                      # 欠一致：变坏了
            g[u] ← ∞
            UpdateVertex(u) 以及每个前驱

UpdateVertex(u):
    若 u ≠ goal: rhs[u] ← min_v c(u,v)+g[v]
    从 U 删掉 u
    若 g[u] ≠ rhs[u]: U.insert(u, Key(u))

边/格变化后:
    km ← km + h(last, start)
    UpdateVertex(受影响点)
    ComputeShortestPath
```

网格无向：前驱 = 邻居。有向图必须扫「谁指向 u」，否则更新会漏。

教学实现的 U 用列表排序，最坏较慢；论文用堆。正确性不依赖堆实现，只依赖键的顺序。

---

## 5. 手算（三个点的线）

格子 `S=A=G` 横排，边权 1：

```
S --1-- A --1-- G
```

从 G 往回：

1. 插入 G，rhs(G)=0，g(G)=∞ → 过一致。弹出 G，g(G)←0，通知 A。
2. rhs(A)=c(A,G)+g(G)=1，g(A)=∞ → 弹出 A，g(A)←1，通知 S。
3. rhs(S)=1+g(A)=2，弹出 S，g(S)←2。

提取：S 选使 c+g 最小的邻居 → A → G。路长 2。

现在封掉 A–G（或把 A 变成墙，S 只能……本课下一步用「把中间格设成障碍」）。rhs(A) 变成 ∞（没有后继到 G），A 欠一致，g(A) 被抬起来，S 跟着变。若图上另有绕路，rhs 会改走那条。
"""),
        PATH,
        md("""
## 6. 实现：最小 D* Lite（无向网格）

先在 **一行三格** 上把 rhs/g 打出来。障碍用 `blocked` 集合；邻居函数不返回障碍。
"""),
        code("""
from lib.pretty import draw_grid

# 一行三格：S=(0,0) A=(1,0) G=(2,0)。稍后把 A 封掉。
CELLS = [(0, 0), (1, 0), (2, 0)]
START, GOAL = (0, 0), (2, 0)
blocked = set()


def nbrs(u):
    x, y = u
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        v = (x + dx, y + dy)
        if v in CELLS and v not in blocked:
            out.append((v, 1.0))
    return out


def h(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class MiniDStar:
    def __init__(self, start, goal):
        self.start = start
        self.goal = goal
        self.g = {}
        self.rhs = {}
        self.U = []
        self.km = 0.0
        self.last = start
        self.rhs[goal] = 0.0
        self._insert(goal)

    def _key(self, u):
        gg = min(self.g.get(u, float("inf")), self.rhs.get(u, float("inf")))
        return (gg + h(self.start, u) + self.km, gg)

    def _insert(self, u):
        self.U = [(k, x) for k, x in self.U if x != u]
        self.U.append((self._key(u), u))
        self.U.sort(key=lambda item: item[0])

    def update_vertex(self, u):
        if u != self.goal:
            best = float("inf")
            for v, c in nbrs(u):
                best = min(best, c + self.g.get(v, float("inf")))
            self.rhs[u] = best
        self.U = [(k, x) for k, x in self.U if x != u]
        if self.g.get(u, float("inf")) != self.rhs.get(u, float("inf")):
            self._insert(u)

    def compute(self, verbose=True):
        steps = 0
        while self.U and (
            self.U[0][0] < self._key(self.start)
            or self.rhs.get(self.start, float("inf")) != self.g.get(self.start, float("inf"))
        ):
            _k, u = self.U.pop(0)
            steps += 1
            gu, ru = self.g.get(u, float("inf")), self.rhs.get(u, float("inf"))
            if verbose:
                print(f"弹出 {u}  g={gu} rhs={ru}  {'过一致' if gu > ru else '欠一致或其它'}")
            if gu > ru:
                self.g[u] = ru
                # 无向：前驱=邻居
                for s, _c in nbrs(u):
                    self.update_vertex(s)
            else:
                self.g[u] = float("inf")
                self.update_vertex(u)
                for s, _c in nbrs(u):
                    self.update_vertex(s)
        if verbose:
            print("compute 结束，弹出次数", steps, "g(S)=", self.g.get(self.start), "rhs(S)=", self.rhs.get(self.start))

    def extract(self):
        if self.rhs.get(self.start, float("inf")) == float("inf"):
            return []
        path = [self.start]
        cur = self.start
        seen = {cur}
        while cur != self.goal:
            best, nxt = float("inf"), None
            for v, c in nbrs(cur):
                val = c + self.g.get(v, float("inf"))
                if val < best:
                    best, nxt = val, v
            if nxt is None or nxt in seen:
                return []
            path.append(nxt)
            seen.add(nxt)
            cur = nxt
        return path


planner = MiniDStar(START, GOAL)
planner.compute()
print("静态路径", planner.extract())
"""),
        md("""
对照第 5 节：应先弹出 G（过一致），再 A，再 S，路径 `[(0,0),(1,0),(2,0)]`。

## 7. 逐行

| 块 | 作用 |
|----|------|
| `rhs[goal]=0`，其余 g 缺省 ∞ | 只有终点一开始不一致 |
| `_key` 二元组 | 先比「还剩多少+h+km」，再比 min(g,rhs) |
| `update_vertex` | 重算 rhs；不一致才进 U |
| `g>rhs` 支 | 变好：采纳 rhs，向前驱传好消息 |
| else 支 | 变坏：g←∞，自己和前驱都要重算 |
| `extract` | 沿 c+g(v) 下降；`seen` 防环 |

---

## 8. 封掉中间格再 compute
"""),
        code("""
print("封掉中间格 A=(1,0)")
blocked.add((1, 0))
planner.km += h(planner.last, planner.start)
planner.update_vertex((0, 0))
planner.update_vertex((1, 0))
planner.update_vertex((2, 0))
planner.compute()
print("新路径（一行被切断应失败）", planner.extract())
print(draw_grid(3, 1, obstacles=blocked, start=START, goal=GOAL, path=planner.extract()))
"""),
        md("""
一行被切断后没有绕路，extract 返回空。换迷宫：库实现会在封路后改走另一条，代价与重新 A\\* 相同。
"""),
        code("""
from lib.maps import grid_maze
from lib.algos.single_agent import DStarLite
from lib.search import astar
from lib.pretty import draw_grid

g = grid_maze()
s, t = (0, 0), (7, 7)
planner = DStarLite(g, s, t)
r1 = planner.compute()
a1 = astar(g, s, t, record=False)
print("静态 D* Lite", r1.cost, "A*", a1.cost, "应相等", r1.cost == a1.cost)
print(draw_grid(g.width, g.height, obstacles=g.obstacles, start=s, goal=t, path=r1.path))

mid = r1.path[len(r1.path) // 2]
print("封掉路径中点", mid)
g.block(mid)
prev = r1.path[r1.path.index(mid) - 1]
planner.edge_blocked(prev, mid)
r2 = planner.compute()
print("新代价", r2.cost, "还经过 mid?", mid in r2.path)
print(draw_grid(g.width, g.height, obstacles=g.obstacles, start=s, goal=t, path=r2.path))
"""),
        md("""
## 常见 bug

1. 封格后只调 `edge_blocked` / `update_vertex`，**忘了改图**（`g.block`）：邻居列表仍含旧边，rhs 算错。
2. 有向图用 `neighbors` 当全部前驱：反向边的点收不到「变坏」消息。
3. extract 不设 `seen`：g 尚未一致时可能转圈。
4. 把 D\\* Lite 的 g 当成「从 start 出发的正向 g」。这里 g 是 **到目标** 的。
5. 机器人已经走到新格子，却不更新 `start` 和 `km`：键过期，U 顺序错。

## 条目小结

| 项目 | 内容 |
|------|------|
| 方向 | 从 goal 反向 |
| 核心 | 局部一致 g=rhs；U 装不一致点 |
| 变化 | UpdateVertex 受影响点，再 Compute |
| 何时用 | 多次重规划；一次查询用 A\\* 即可 |
| 下一课 | 均匀网格上用跳点减少 A\\* 扩展 |

## 练习

1. 用自己的话注释 `g>rhs` / else 两支：「过一致」和「欠一致」各对应「发现捷径」还是「捷径被拆」。
2. 静态迷宫上 D\\* Lite 代价必须等于 A\\*。若不等，先查 extract 是否走了 g 仍为 ∞ 的点。
3. 有向环 I0→I1→I2… 上封一条边，为什么必须扫 `graph.edges` 找前驱？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_search({**g.to_studio(), "start": [0, 0], "goal": [7, 7]}, r2, "D* Lite")
studio
"""),
    ]


def lesson_06():
    return "06_jps", "06 JPS：网格对称剪枝", [
        md("""
本课按百科条目写。Jump Point Search 只加速 **均匀代价的规则网格**，拓扑路网不要用。调度台在最后。

---

## 1. 定义

**Jump Point Search**（Harabor & Grastien, AAAI 2011）在四连通或八连通均匀网格上跑 A\\*，但后继不是「四个邻居」，而是沿直线 **跳** 到下一个有决策价值的格子（跳点）。

跳点：沿方向 d 走，直到

- 碰到终点，或
- **被迫邻居**（forced neighbour）：旁边有墙，使得不在此处转弯就会错过某条最短路，或
- 本课教学策略：这个方向走不下去时，返回 **最后一格可走格子**（保证四连通完备；论文原版在无 forced 时返回空，再靠自然邻居递归）。

输入：`GridMap`、起终点。输出：与 A\\* 相同代价的格子路径（中间被跳过的格子要填回去）。

---

## 2. 为何能剪、何时不能用

空地从 (0,0) 到 (3,2)：先右后下、先下后右，边数相同。A\\* 会把中间所有排列都扩一遍。JPS 向右一直跳，直到该方向出现墙角或终点。

**只适用于规则网格。** 任意拓扑没有「沿轴跳」的几何，本仓库对 `TopoMap` 返回 `inapplicable`。边权不均为 1 时，跳过的格子代价对不上，也不要用。

八连通 JPS 的 forced 规则与四连通不同（对角移动会「擦」墙角）。本课只写 **四连通**。

---

## 3. 不变量

- 跳点之间是直线、中间无墙。
- 填回直线格子后，路径合法，边数 = A\\* 最优边数（教学版返回最后一格，完备）。
- 扩展次数 ≤ A\\*（空地、长走廊上少很多；迷宫墙多时优势变小）。

---

## 4. 伪代码

```
function JPS(grid, s, t):
    同 A*，但 Successors(u) =
        for 方向 d in {右,左,下,上}:
            jp ← Jump(u, d)
            if jp ≠ nil 且 jp ≠ u: 产生 jp，代价 = 曼哈顿(u, jp)

Jump(x, d):
    n ← 沿 d 走一步
    若出界或墙: return nil（或教学：没有下一步就停在上一格由调用方处理）
    若 n = t 或 Forced(n, d): return n
    further ← Jump(n, d)
    若 further ≠ nil: return further
    return n                 # 教学：此方向最后一格

Forced(n, d) 对水平 d=(±1,0):
    上侧是墙 且 右上/左上（沿 d）可走，或下侧对称
竖直方向对换 x/y。
```

主循环结束后：`came_from` 只记跳点。输出前在相邻跳点间按方向逐步插入中间格。

---

## 5. 手算 forced

```
. . .
# n .
. . .
```

在 n 向右走（d=+x）。n 的 **上方是墙**，右上若可走，则「只继续向右」会错过经右上的路 → n 是跳点，必须在此把右上当成后继（四连通没有斜向，forced 仍标记「这里要停，让 A\\* 换方向」）。

空 8×8、无墙、S 左上 G 右下：向右跳会一口气跳到右边界附近，扩展远小于 A\\*。
"""),
        PATH,
        md("""
## 6. 实现：forced / jump / 填格子

在 8×8 空网格上自己写。邻居顺序仍是右左下上。
"""),
        code("""
import heapq
from lib.maps import grid_open, grid_wall, topo_oneway
from lib.pretty import draw_grid

grid = grid_open(8, 8)
START, GOAL = (0, 0), (7, 7)


def blocked(x, y):
    return not grid.passable((x, y))


def forced(nx, ny, dx, dy):
    # 墙在侧面、沿前进方向的「斜侧」可走 ⇒ 必须在此转向
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
    if (nx, ny) == GOAL or forced(nx, ny, dx, dy):
        return (nx, ny)
    further = jump(nx, ny, dx, dy)
    if further is not None:
        return further
    return (nx, ny)


def successors(node):
    x, y = node
    succs = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        jp = jump(x, y, dx, dy)
        if jp and jp != node:
            succs.append(jp)
    return succs


print("S 的跳点（空地应是沿四轴跳到边界前）:", successors(START))
print("中点 (3,3) 的跳点:", successors((3, 3)))
"""),
        md("""
空地上 `jump` 会走到该方向最后一格（教学完备策略），所以 S 向右的跳点是 (7,0)，向下是 (0,7)。不是四邻居。

## 7. 主循环 = A*，后继换成跳点
"""),
        code("""
def reconstruct_jumps(came, goal):
    node = goal
    path = [node]
    while came[node] is not None:
        node = came[node]
        path.append(node)
    path.reverse()
    return path


def fill_straight(path):
    # 跳点之间可能隔了好几格。按轴逐步插入，否则路径「瞬移」。
    filled = [path[0]]
    for a, b in zip(path, path[1:]):
        dx = 0 if b[0] == a[0] else (1 if b[0] > a[0] else -1)
        dy = 0 if b[1] == a[1] else (1 if b[1] > a[1] else -1)
        p = a
        while p != b:
            p = (p[0] + dx, p[1] + dy)
            filled.append(p)
    return filled


def jps_search(start, goal, verbose=True):
    heap = []
    g = {start: 0.0}
    came = {start: None}
    heapq.heappush(heap, (grid.heuristic(start, goal), start))
    closed = set()
    expanded = 0
    while heap:
        _f, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if verbose and expanded <= 12:
            print(f"扩展跳点 {cur}  g={g[cur]:.0f}  后继={successors(cur)}")
        if cur == goal:
            jumps = reconstruct_jumps(came, goal)
            filled = fill_straight(jumps)
            return filled, float(len(filled) - 1), expanded, jumps
        for jp in successors(cur):
            step = abs(jp[0] - cur[0]) + abs(jp[1] - cur[1])
            ng = g[cur] + step
            if ng < g.get(jp, float("inf")):
                g[jp] = ng
                came[jp] = cur
                heapq.heappush(heap, (ng + grid.heuristic(jp, goal), jp))
    return None, float("inf"), expanded, []


path, cost, n_exp, jumps = jps_search(START, GOAL)
print("跳点序列", jumps)
print("填格后边数", cost, "扩展", n_exp)
print(draw_grid(8, 8, start=START, goal=GOAL, path=path, closed=jumps))
"""),
        md("""
| 行 | 作用 |
|----|------|
| `successors` | 四方向各 jump 一次，不是四邻居 |
| `step = 曼哈顿(cur,jp)` | 中间直线代价=格数 |
| `fill_straight` | 给执行层连续格子 |
| 关闭集合 | 仍是跳点，不是每一个中间格 |

空 8×8 最优边数 14。JPS 扩展应明显小于 A\\*（A\\* 大约几十，JPS 往往十几或更少）。
"""),
        code("""
from lib.search import astar
from lib.algos.single_agent import jps as jps_lib

g_open = grid_open(8, 8)
a = astar(g_open, START, GOAL, record=False)
print("空地 A* 扩展", a.expanded, "代价", a.cost, "本课 JPS 扩展", n_exp, "代价", cost)

gw = grid_wall()
aw = astar(gw, START, GOAL, record=False)
jw = jps_lib(gw, START, GOAL, record=False)
print("墙图 A*", aw.expanded, aw.cost, "库JPS", jw.expanded, jw.cost)
print("拓扑应 inapplicable:", jps_lib(topo_oneway(), "I0", "G1").extra)
"""),
        md("""
## 常见 bug

1. 忘了 `fill_straight`：路径从跳点瞬移，执行器会穿墙或一步走多格。
2. 八连通 forced 抄到四连通（或反过来）。
3. 把 JPS 用在路口拓扑、不等权边。
4. `jump` 前方无跳点就返回 None，四连通可能不完备；本课返回最后一格。
5. 比较扩展次数时用了 `record=True` 的 A\\* 和不同地图。

## 条目小结

| 项目 | 内容 |
|------|------|
| 适用 | 均匀规则网格 |
| 核心 | 直线跳过对称路径 |
| 保证 | 教学版完备，代价=A\\* |
| 不适用 | 拓扑、不等权、任意多边形 |
| 下一课 | 多车之前先把「谁在何时占哪」锁清楚 |

## 练习

1. 空 8×8，S=(0,0)，G=(7,0) 同一行。JPS 第一次向右跳到哪？扩展几次？
2. 在 (3,1) 放一堵墙，(3,0) 向右走时 forced 会不会为真？画上下侧。
3. 证明：跳点间填直线后，边数等于曼哈顿（无墙）或不少于曼哈顿（有墙）。
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.algos.single_agent import jps as jps_lib

r = jps_lib(gw, START, GOAL)
studio = PlannerStudio()
studio.show_search({**gw.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "JPS")
studio
"""),
    ]


def lesson_07():
    return "07_reservation_lock", "07 资源锁：时空占用表", [
        md("""
本课按百科条目写。占用表 **不是** 搜索算法，但是时间 A\\* / SIPP / HCA\\* / CBS 底层的共同输入。调度台可跳过。

---

## 1. 定义

**占用表 / 预约表**（reservation table）记录「谁在何时占用哪」。多车、动态障碍、已下发路段，都先写成表上的键。

三类键：

| 锁 | 键 | 禁止 |
|----|----|------|
| 顶点 | \((v,t)\) | 两智能体同一时刻同一点 |
| 边 | \((u,v,t)\) | t 拍从 u 走到 v；对向 \((v,u,t)\) 同时占用 |
| 段 issued | \(v\) | 已承诺给某车、尚未走完的点（不带时间，执行层互斥） |

输入：占/释放请求。输出：成功或失败；查询 `vertex_free` / `edge_free`；SIPP 还要 `safe_intervals`。

时间离散成整数拍。一步移动或等待都消耗 1 拍（本课约定，与 08 一致）。

---

## 2. 和「空间最短路」的关系

普通 A\\* 的状态是点。加上占用表之后，同一点在 t=1 空闲、t=2 被占，必须当成不同资源。下一课把时间写进状态；本课先把表写对。

CBS 的「约束」底层也是往这张表里写 block。HCA\\* 则是高优先级车的整条时空轨迹。

---

## 3. 不变量

- `occupy` 失败 ⇒ **表不变**（不覆盖别人）。
- 自己占的格，`vertex_free` 对本人仍为真（允许在自己的预约上等待）。
- 边锁同时挡 \((a,b,t)\) 与 \((b,a,t)\)，防止对向换位擦肩。
- `issue_segment` 要么整段成功要么整段失败（不能锁一半）。
- `safe_intervals(v, T, agent)` 返回半开区间 \([lo,hi)\)，别人占用的整数拍不落在任何区间里。

---

## 4. 伪代码

```
occupy(v, t, agent):
    if table[v,t] 存在且 ≠ agent: return false
    table[v,t] ← agent; return true

vertex_free(v, t, agent):
    return table[v,t] 为空 或 = agent

occupy_edge(a, b, t, agent):
    若 (a,b,t) 或 (b,a,t) 被别人占: return false
    两向都记下 agent（或至少挡对向查询）

issue_segment(nodes, agent):
    若任一 node 已被别人 issued: return false
    全部标成 agent

safe_intervals(v, horizon, agent):
    blocked ← 别人占用 v 的时刻，排序，且 < horizon
    从 0 起，每个 blocked 拍把区间切开
    区间均为 [lo, hi) 半开
```

---

## 5. 手算

走廊点 C2。horizon=8。无人占用：一个区间 `[0, 8)`。

占 t=2（别人）：切开成 `[0, 2)` 和 `[3, 8)`。注意 **t=2 本身不在任何空闲区间**。SIPP 若误用闭区间，会在占用拍插入。

车路径 A,C1,C2 从 t=0 每步一格，顶点键：`(A,0),(C1,1),(C2,2)`。另一车从 B 对向走，禁止与这些键冲突，也禁止在相应拍走对向边。
"""),
        PATH,
        md("""
## 6. 自己写最小表：顶点 + 边 + 区间
"""),
        code("""
class MiniTable:
    def __init__(self):
        self.vertex = {}
        self.edge = {}
        self.issued_by = {}

    def occupy(self, node, t, agent):
        key = (node, t)
        holder = self.vertex.get(key)
        if holder is not None and holder != agent:
            return False
        self.vertex[key] = agent
        return True

    def free(self, node, t, agent):
        if self.vertex.get((node, t)) == agent:
            del self.vertex[(node, t)]

    def vertex_free(self, node, t, agent):
        holder = self.vertex.get((node, t))
        return holder is None or holder == agent

    def occupy_edge(self, a, b, t, agent):
        if self.edge.get((a, b, t)) not in (None, agent):
            return False
        if self.edge.get((b, a, t)) not in (None, agent):
            return False
        self.edge[(a, b, t)] = agent
        self.edge[(b, a, t)] = agent
        return True

    def edge_free(self, a, b, t, agent):
        return self.edge.get((a, b, t)) in (None, agent) and self.edge.get((b, a, t)) in (None, agent)

    def issue_segment(self, nodes, agent):
        for n in nodes:
            holder = self.issued_by.get(n)
            if holder is not None and holder != agent:
                return False
        for n in nodes:
            self.issued_by[n] = agent
        return True

    def release_segment(self, nodes, agent):
        for n in nodes:
            if self.issued_by.get(n) == agent:
                del self.issued_by[n]

    def safe_intervals(self, node, horizon, agent):
        blocked = sorted(
            t for (n, t), who in self.vertex.items()
            if n == node and who != agent and t < horizon
        )
        intervals = []
        start = 0
        for t in blocked:
            if t > start:
                intervals.append((start, t))
            start = t + 1
        if start < horizon:
            intervals.append((start, horizon))
        return intervals


table = MiniTable()
print("a 占 C2@t=1", table.occupy("C2", 1, "a"))
print("b 同键应失败", table.occupy("C2", 1, "b"))
print("b 占 t=2", table.occupy("C2", 2, "b"))
print("a 在自己的 t=1 仍 free", table.vertex_free("C2", 1, "a"))
print("b 在 t=1 不 free", table.vertex_free("C2", 1, "b"))
table.free("C2", 1, "a")
print("释放后 b 占 t=1", table.occupy("C2", 1, "b"))
print("空闲区间 horizon=8", table.safe_intervals("C2", 8, "me"))
"""),
        md("""
对照手算：别人占了 t=1 和 t=2 之后，`me` 的区间应是 `[0,1)` 与 `[3,8)`。

## 7. 逐行

| 行 | 作用 |
|----|------|
| `key=(node,t)` | 空间×时间，缺一不可 |
| 先 get 再写 | 失败不覆盖 |
| 本人可再 occupy | 允许在自己的预约上等待 |
| 边写两向 | `edge_free` 对向也挡 |
| `issue` 先全检查再全写 | 禁止锁一半 |
| 区间半开、blocked 拍跳过 | 给 SIPP 用 |

库 `ReservationTable` 字段名相同：`vertex` / `edge` / `issued_by`。
"""),
        code("""
from lib.reservation import ReservationTable

t = ReservationTable()
print("a 下发 P0-P2", t.issue_segment(["P0", "P1", "P2"], "a"))
print("b 抢 P2", t.issue_segment(["P2", "P3"], "b"))
t.release_segment(["P0", "P1", "P2"], "a")
print("释放后 b", t.issue_segment(["P2", "P3"], "b"))

t2 = ReservationTable()
print("空表 C2", t2.safe_intervals("C2", 8, "me"))
t2.occupy("C2", 2, "x")
print("占 t=2 后", t2.safe_intervals("C2", 8, "me"))

print("边：a 占 A->C1 @t=0", t2.occupy_edge("A", "C1", 0, "a"))
print("对向 C1->A 同时", t2.occupy_edge("C1", "A", 0, "b"))
print("边空闲查询对向", t2.edge_free("C1", "A", 0, "b"))
"""),
        md("""
## 常见 bug

1. 只锁点不锁边：对向在同一拍互换格子，顶点冲突检测在「各走各的下一格」时可能漏（取决于你是否先移动）。边锁一次挡住。
2. 解锁时 agent 名写错，把别人的锁删了。
3. `safe_intervals` 用闭区间，占用拍被当成空闲。
4. issued 锁忘了释放，后面的车永远过不了路口。
5. 时间键用了「到达拍」还是「离开拍」和 08 课边检查不一致。本课约定：`occupy_edge(u,v,t)` 表示 **t 拍正在从 u 走向 v**，下一课 `edge_free(u,v,t)` 用离开的那一拍。

## 条目小结

| 项目 | 内容 |
|------|------|
| 顶点键 | (点, 时刻) |
| 边键 | (u,v,t) 及对向 |
| 段锁 | 执行层互斥，不带时间 |
| 区间 | [lo,hi) 半开 |
| 下一课 | 状态改成 (点,时刻)，查这张表 |

## 练习

1. 车路径 A,C1,C2 从 t=0 每步一格，列出全部顶点键和边键。
2. 占用 {1,2,5}、horizon=8，手写 `safe_intervals`（agent 是别人）。
3. 为什么 `occupy` 失败必须整表不变？举一个「写了一半」导致死锁的例子。
"""),
    ]


def lesson_08():
    return "08_time_astar", "08 时间扩展 A*：状态 (点, 时刻)", [
        md("""
本课按百科条目写。把第 07 课的表接到 A\\* 上：状态从「点」变成「点×时间」。调度台在最后。

---

## 1. 定义

**时间扩展 A\\***（time-expanded A\\*，时空 A\\*）把时间离散进状态。状态

\\[
s=(v,t)
\\]

动作（本课一步一拍、边权即耗时）：

- **移动**：到空间邻居 \(v'\)，\(t'=t+1\)
- **等待**：\(v'=v\)，\(t'=t+1\)

若占用表禁止 \((v',t')\) 的顶点，或禁止边 \((v,v',t)\)，则该动作非法。

- 输入：图、起终点、`ReservationTable`、智能体名、horizon T。
- 输出：点列（相邻重复 = 等待），代价含等待。

WHCA 窗口规划会设 `require_goal=False`：到不了终点就返回窗口内离终点最近的前缀。

---

## 2. 和普通 A* 的关系

| | 普通 A\\* | 时间扩展 A\\* |
|--|--|--|
| 状态 | 点 | (点, t) |
| 等待 | 无（原地边会成自环且无收益） | 一等动作 |
| closed | 每个点一次 | 每个 (点,t) 一次 |
| h | 空间启发 | 仍用空间启发（可采纳：等待只让 g 变大） |
| 规模 | \(O(V)\) | \(O(V\\cdot T)\) |

空占用表、允许等待时，最优代价 = 空间最短路（没有人逼你等）。有人挡路时代价 ≥ 空间最短路。

---

## 3. 不变量

- 返回路径上每个 `(path[t], t)` 对该 agent `vertex_free`。
- 相邻若移动，则离开拍 `edge_free(path[t], path[t+1], t)`。
- 第一次弹出终点时 g 最优（h 一致、非负边权、关闭后不重开）。
- `t` 超过 horizon 不再扩展，防止无限等。

---

## 4. 伪代码（对照下面 `time_astar_mini`）

```
g[s,0] ← 0
push (h(s), 0, s, 0)          # 键 f，然后 g, node, t
while heap:
    (f, cost, u, t) ← pop
    if (u,t) 已关闭: continue
    关闭 (u,t)
    if u = goal: 回溯点列
    if t ≥ horizon: continue
    for (v, w) in {(u, wait_cost=1)} ∪ 邻居(u):
        t2 ← t+1
        if 顶点 (v,t2) 被占: continue
        if v≠u 且 边 (u,v,t) 被占: continue
        alt ← cost + w
        松弛 (v,t2)，push (alt + h(v), alt, v, t2)
```

回溯：`came[(v,t2)] = (u,t)`，抽出点列（可含重复）。

`require_goal=False`：全程记 h 最小的已关闭状态，失败时回溯它。

---

## 5. 手算

走廊 `A—C1—C2—C3—B`，每边 1。空间最短 A→B 四步。现把 C2 在 t=0,1,2 占住。

t=2 不能进 C2。一种合法策略：A(0)–C1(1)–C1(2 等待)–C2(3)–C3(4)–B(5)。C2 下标应 ≥ 3。

若不允许等待，可能宣告失败——其实等一拍就行。这是最常见的实现漏洞。
"""),
        PATH,
        md("""
## 6. 实现：状态 (node, t)，含等待
"""),
        code("""
import heapq
from lib.maps import corridor_headon
from lib.reservation import ReservationTable
from lib.search import astar


def rebuild(came, state):
    path = []
    cur = state
    while cur is not None:
        path.append(cur[0])
        cur = came[cur]
    path.reverse()
    return path


def time_astar_mini(graph, start, goal, table, agent="me", horizon=40, require_goal=True, verbose=True):
    heap = []
    g = {(start, 0): 0.0}
    came = {(start, 0): None}
    heapq.heappush(heap, (graph.heuristic(start, goal), 0.0, start, 0))
    seen = set()
    expanded = 0
    best_partial = None
    best_h = float("inf")
    while heap:
        _f, cost, node, t = heapq.heappop(heap)
        state = (node, t)
        if state in seen:
            continue
        seen.add(state)
        expanded += 1
        hn = graph.heuristic(node, goal)
        if hn < best_h or (hn == best_h and t > 0):
            best_h = hn
            best_partial = state
        if verbose and expanded <= 15:
            print(f"关闭 {node:3} t={t} g={cost:.0f} h={hn:.0f}")
        if node == goal:
            path = rebuild(came, state)
            if verbose:
                print("到达", path, "代价", cost, "扩展", expanded)
            return path, cost, expanded
        if t >= horizon:
            continue
        candidates = [(node, 1.0)] + list(graph.neighbors(node))
        for nxt, step_cost in candidates:
            nt = t + 1
            if not table.vertex_free(nxt, nt, agent):
                continue
            if nxt != node and not table.edge_free(node, nxt, t, agent):
                continue
            ns = (nxt, nt)
            ng = cost + step_cost
            if ng < g.get(ns, float("inf")):
                g[ns] = ng
                came[ns] = state
                heapq.heappush(heap, (ng + graph.heuristic(nxt, goal), ng, nxt, nt))
    if not require_goal and best_partial is not None:
        path = rebuild(came, best_partial)
        return path, g[best_partial], expanded
    if verbose:
        print("失败，扩展", expanded)
    return None, float("inf"), expanded


g = corridor_headon()
print("空间最短", astar(g, "A", "B", record=False).path)
table = ReservationTable()
for t in range(3):
    table.occupy("C2", t, "blocker")
path, cost, n_exp = time_astar_mini(g, "A", "B", table)
print("C2 出现的下标（应>=3）", [i for i, n in enumerate(path or []) if n == "C2"])
"""),
        md("""
## 7. 逐行

| 行 | 作用 |
|----|------|
| 状态 `(node,t)` | 同一点不同时刻是不同状态 |
| `candidates = [(node,1)] + neighbors` | 等待边权 1 |
| `vertex_free(nxt, t+1)` | 进入下一拍的格子 |
| `edge_free(node, nxt, t)` | **离开的这一拍** 占用边 |
| `seen` | 关闭 (node,t)，一致 h 下不必重开 |
| `horizon` | 防止一直等 |
| `require_goal=False` | 窗口规划返回 best_partial |

路径里相邻相同 ⇒ 等待。
"""),
        code("""
from lib.algos.temporal import time_astar

r = time_astar(g, "A", "B", table=table, agent="me")
print("库", r.path, "代价", r.cost, "扩展", r.expanded)

# 窗口：horizon 太短且必须到终点会失败；关掉 require_goal 则返回前缀
short = time_astar(g, "A", "B", table=table, agent="me", horizon=3, require_goal=True)
part = time_astar(g, "A", "B", table=table, agent="me", horizon=3, require_goal=False)
print("horizon=3 必须到终点 found", short.found)
print("horizon=3 允许部分", part.found, part.path, part.extra)
"""),
        md("""
## 常见 bug

1. 忘记等待：被挡就失败。
2. closed 只用空间点：t=1 走过 C1，t=3 再也不能进 C1。
3. 边冲突检查用 `t+1` 而不是离开拍 `t`。
4. 不等长路径比较冲突时没 pad（那是多车层；单车这里只要自己的 (v,t) 合法）。
5. horizon 小于最短步数且 `require_goal=True` ⇒ 全失败。WHCA 必须关 require_goal。

## 条目小结

| 项目 | 内容 |
|------|------|
| 状态 | (点, t) |
| 动作 | 走或等，都 +1 拍 |
| 规模 | O(V T) |
| 保证 | 表合法前提下最优 |
| 下一课 | 把时刻收成安全区间，状态更少 |

## 练习

1. 不许等待（candidates 去掉原地），这张占 C2@0..2 的走廊还找不找得到路？
2. 自己占的格 `vertex_free` 为真。若 blocker 也叫 `me`，会发生什么？
3. 画出 (C1,t) 哪些 t 会关闭。等一拍对应哪次关闭？
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.algos.temporal import time_astar

r = time_astar(g, "A", "B", table=table, agent="me")
studio = PlannerStudio()
studio.show_search(g.to_studio(), r, "time A*")
studio
"""),
    ]


def lesson_09():
    return "09_sipp", "09 SIPP：安全间隔上的 A*", [
        md("""
本课按百科条目写。SIPP 用「空闲时间段」代替每一个时刻，状态更少，最优性仍在。调度台在最后。

---

## 1. 定义

**Safe Interval Path Planning**（Phillips & Likhachev, ICRA 2011）：不把每个整数时刻当状态，而把每个点被别人挖洞之后剩下的空闲时间收成区间 \([lo,hi)\)。

状态 = (点, 第几个空闲区间)。区间内何时到达只记一个到达时刻 `arr`（同一区间内更晚到达绝不会更好——非负等待）。

- 输入：图、起终点、占用表、horizon。
- 输出：与时间扩展 A\\* 相同代价的路径（空表时扩展接近普通 A\\*）。

---

## 2. 为何比时间扩展更省

时间扩展：状态 \(O(|V|T)\)。  
SIPP：每点区间数 ≤ 占用次数 + 1，通常远小于 T。空表时每点一个区间 `[0,T)`，行为接近空间 A\\*（仍允许在区间内等待，但等不会单独产生新状态）。

有交通时，SIPP 扩展应 **少于** 时间 A\\*，代价相同。

---

## 3. 不变量

- 到达时刻落在所选区间：`lo ≤ arr < hi`。
- 进入邻居：`arr' = max(arr + step, nlo)`，不能早于邻居区间开门；且 `arr' < nhi`。
- 边在离开拍 `arr'-1`（本课 step=1 时即 `earliest-1`）必须空闲。
- 空占用表时代价 = 时间扩展 A\\* = 空间最短路。

---

## 4. 伪代码

```
intervals[v] ← SafeIntervals(v)
选包含 t=0 的起点区间 i0
g[s,i0] ← 0
push (h(s), 0, s, i0)
while heap:
    (f, arr, u, i) ← pop
    if (u,i) 已关闭: continue
    关闭
    if u = goal: return
    [lo,hi] ← intervals[u][i]
    for v in 邻居(u):          # 等待已编码在区间内，不必单独等
        move ← arr + 1
        for 区间 j = [nlo, nhi] of v:
            if move ≥ nhi: continue
            earliest ← max(move, nlo)
            if earliest ≥ nhi: continue
            若边在 earliest-1 被占: continue
            松弛 (v,j) 的到达 earliest
```

`safe_intervals`：占用时刻排序，相邻占用之间的空隙即区间。半开。

---

## 5. 手算区间

占用 {1,2,5}，horizon=8，别人占的：

```
t:  0 1 2 3 4 5 6 7
    . # # . . # . .
```

切开：`[0,1)`, `[3,5)`, `[6,8)`。

从某点 t=0 出发，一步到该点：move=1，但 1 落在占用里，不能进第一段；最早 `max(1,3)=3` 进第二段。
"""),
        PATH,
        md("""
## 6. 实现：先写区间，再写 SIPP 主循环
"""),
        code("""
from lib.maps import corridor_headon
from lib.reservation import ReservationTable


def safe_intervals_mini(blocked_times, horizon):
    # blocked_times: 别人占用该点的时刻
    blocked = sorted(t for t in blocked_times if t < horizon)
    intervals = []
    start = 0
    for t in blocked:
        if t > start:
            intervals.append((start, t))
        start = t + 1
    if start < horizon:
        intervals.append((start, horizon))
    return intervals


print("占用 {1,2,5} horizon=8 ->", safe_intervals_mini({1, 2, 5}, 8))
print("空 ->", safe_intervals_mini(set(), 8))
"""),
        code("""
import heapq
from lib.search import astar
from lib.algos.temporal import time_astar, sipp


def sipp_mini(graph, start, goal, table, agent="me", horizon=40, verbose=True):
    cache = {}

    def ivals(n):
        if n not in cache:
            cache[n] = table.safe_intervals(n, horizon, agent)
        return cache[n]

    start_iv = None
    for i, (lo, hi) in enumerate(ivals(start)):
        if lo <= 0 < hi:
            start_iv = i
            break
    if start_iv is None:
        print("起点 t=0 不空闲")
        return None, float("inf"), 0

    heap = []
    g = {(start, start_iv): 0}
    came = {(start, start_iv): None}
    heapq.heappush(heap, (graph.heuristic(start, goal), 0, start, start_iv))
    seen = set()
    expanded = 0
    while heap:
        _f, arr, node, ii = heapq.heappop(heap)
        state = (node, ii)
        if state in seen:
            continue
        seen.add(state)
        expanded += 1
        if verbose:
            lo, hi = ivals(node)[ii]
            print(f"关闭 {node:3} 区间{ii}{ivals(node)[ii]} 到达={arr}")
        if node == goal:
            chain = []
            cur = state
            while cur is not None:
                chain.append(cur[0])
                cur = came[cur]
            chain.reverse()
            if verbose:
                print("节点列", chain, "到达", arr, "扩展", expanded)
            return chain, float(arr), expanded
        for nxt, _step in graph.neighbors(node):
            move_t = arr + 1
            for jj, (nlo, nhi) in enumerate(ivals(nxt)):
                if move_t >= nhi:
                    continue
                earliest = max(move_t, nlo)
                if earliest >= nhi:
                    continue
                if not table.edge_free(node, nxt, earliest - 1, agent):
                    continue
                ns = (nxt, jj)
                if earliest < g.get(ns, float("inf")):
                    g[ns] = earliest
                    came[ns] = state
                    heapq.heappush(heap, (earliest + graph.heuristic(nxt, goal), earliest, nxt, jj))
    return None, float("inf"), expanded


g = corridor_headon()
table = ReservationTable()
print("空表 C2", table.safe_intervals("C2", 20, "me"))
for t in range(3):
    table.occupy("C2", t, "blk")
print("占 0,1,2 后 C2", table.safe_intervals("C2", 20, "me"))

print("--- SIPP ---")
sp, sc, se = sipp_mini(g, "A", "B", table)
print("--- 对照 ---")
ta = time_astar(g, "A", "B", table=table, agent="me")
si = sipp(g, "A", "B", table=table, agent="me")
print("本课", sc, "扩展", se)
print("timeA*", ta.cost, "扩展", ta.expanded)
print("库SIPP", si.cost, "扩展", si.expanded)
print("空表时 SIPP 应接近空间 A*", astar(g, "A", "B", record=False).cost)
"""),
        md("""
## 7. 逐行

| 块 | 作用 |
|----|------|
| `ivals(n)` | 惰性缓存该点区间 |
| 起点选含 0 的区间 | 否则无解 |
| 双重循环 邻居×区间 | 尝试插入 |
| `earliest=max(move,nlo)` | 早到则等到区间开门 |
| 键 `earliest+h(v)` | 仍是 A\\* |
| 等待 | 不单独产生状态，早到等于在区间开头等 |

有占用时 SIPP 扩展应 ≤ 时间 A\\*，代价相同。

## 常见 bug

1. 区间用闭区间，占用拍被当成空闲。
2. 忘记边在 `earliest-1` 的换位检查。
3. 把区间编号和到达时刻当成同一个数。
4. 起点 t=0 已被占却没处理「无起始区间」。
5. 回溯只记下节点、没把等待展开：执行层时间对不齐。教学版库返回的是节点列，到达时刻在 cost 里。

## 条目小结

| 项目 | 内容 |
|------|------|
| 状态 | (点, 区间编号) |
| 相对时间 A\\* | 状态少，代价同 |
| 空表 | 接近普通 A\\* |
| 下一课 | 多车：联合状态 vs 优先规划 |

## 练习

1. 占用 {1,2,5}、horizon=8，手写区间，与 `safe_intervals_mini` 对照。
2. 空表跑 SIPP 与时间 A\\*，扩展谁更大？为什么 SIPP 往往更小？
3. `earliest = max(move, nlo)` 对应「等到开门」。若写成 `move` 不管 nlo，会怎样？
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.algos.temporal import sipp

si = sipp(g, "A", "B", table=table, agent="me")
studio = PlannerStudio()
studio.show_search(g.to_studio(), si, "SIPP")
studio
"""),
    ]
