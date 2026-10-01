"""Wiki-style search lessons: BFS, Dijkstra, A*. Implementation is the core, not the UI."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_01():
    return "01_bfs", "01 BFS（广度优先搜索）：条目、证明要点、逐行实现", [
        md("""
本课按百科条目写：先定义，再数据结构，再完整手算，再 **一行一行写出算法**。调度台在最后，可跳过。

---

## 1. 定义

**广度优先搜索**（Breadth-First Search, BFS）在图上从起点出发，按「离起点的边数」从小到大访问顶点。

- 输入：图 \(G=(V,E)\)，起点 \(s\)，终点 \(t\)。本课每条边的长度都是 **1**（无权图，或等权图）。
- 输出：一条 \(s\) 到 \(t\) 的路径，边数最少；若不可达则失败。

它 1959 年前后由 Moore 以及 Lee（电路布线）给出。路径规划里，格子图「每步代价相同」时，BFS 就是最短路算法。

**不是** 最短路程算法：边有不同长度时要用 Dijkstra。

---

## 2. 和 DFS 差在哪

| | BFS | DFS（深度优先） |
|--|--|--|
| 待处理集合 | **队列** FIFO | **栈** LIFO / 递归 |
| 先处理谁 | 最早发现的、离起点近的 | 最新发现的、往深处扎 |
| 等权最短路 | 是 | 否 |
| 典型用途 | 最短步数、分层 | 拓扑、连通、迷宫「一条路走到底」 |

只换「从哪端取点」，行为完全不同。实现时用错 `pop()` / `popleft()` 是最常见的 bug。

---

## 3. 不变量（为什么对）

维护：

- `dist[v]`：从 \(s\) 到 \(v\) 的最少边数（已知）
- `came_from[v]`：那条最短路上 \(v\) 的前驱
- 队列里的点按 `dist` **非降** 排列

**引理：** 每个点第一次被发现（写入 `came_from` 并入队）时，`dist` 已经是最优边数。

理由：边权全是 1，先处理完所有 `dist = k` 的点，才会处理 `dist = k+1`。第一次碰到 \(t\) 时，不存在更短的没处理完的层。

因此：**发现终点就可以停**，不必把整张图扫完。这也是为什么「每个点只入队一次」。

---

## 4. 伪代码（与实现一一对应）

```
function BFS(G, s, t):
    queue ← 空队列
    enqueue(queue, s)
    came_from[s] ← NIL
    dist[s] ← 0
    while queue 非空:
        u ← dequeue(queue)          # 队头，最早入队的
        if u = t:
            return Reconstruct(came_from, t)
        for each 边 (u, v) in G:
            if v 从未出现在 came_from:
                came_from[v] ← u
                dist[v] ← dist[u] + 1
                enqueue(queue, v)
    return FAILURE
```

**何时标记「见过」：** 必须在 **入队时** 标记，不能等出队再标。否则同一点会进队多次，复杂度和正确性都坏。本实现用 `came_from` 兼作 visited。

**复杂度：** 每点最多入队一次，每条边最多看一次，时间 \(O(|V|+|E|)\)。网格里 \(|E|\\le 4|V|\)，即与格子数成正比。空间也是 \(O(|V|)\)。

---

## 5. 完整手算（请先算，再对答案）

地图 \(4\\times 3\)。坐标 **x 向右、y 向下**。墙在 (1,1)。S=(0,0)，G=(3,2)。邻居顺序：**右、左、下、上**。

```
列x  0 1 2 3
y=0  S . . .
y=1  . # . .
y=2  . . . G
```

每一行是一次 `dequeue`：

| 出队 u | dist | 新入队的邻居 | 队列（左=队头） | came_from 新写 |
|--------|------|----------------|-----------------|----------------|
| (0,0) | 0 | (1,0), (0,1) | (1,0),(0,1) | (1,0)←(0,0), (0,1)←(0,0) |
| (1,0) | 1 | (2,0) | (0,1),(2,0) | (2,0)←(1,0) |
| (0,1) | 1 | (0,2) | (2,0),(0,2) | (0,2)←(0,1) |
| (2,0) | 2 | (3,0),(2,1) | (0,2),(3,0),(2,1) | |
| (0,2) | 2 | (1,2) | (3,0),(2,1),(1,2) | |
| (3,0) | 3 | (3,1) | (2,1),(1,2),(3,1) | |
| (2,1) | 3 | | (1,2),(3,1) | (2,1) 的右是 (3,1) 已在队 |
| (1,2) | 3 | (2,2) | (3,1),(2,2) | |
| (3,1) | 4 | (3,2)=G | (2,2),(3,2) | G←(3,1) |
| (2,2) | 4 | | (3,2) | |
| **(3,2)** | **5** | 停 | | |

回溯：`(3,2)←(3,1)←(3,0)←(2,0)←(1,0)←(0,0)`，边数 5。  
另一条 `(0,0)-(0,1)-(0,2)-(1,2)-(2,2)-(3,2)` 也是 5 条边；先发现哪条取决于邻居顺序，**边数相同**。
"""),
        PATH,
        md("""
## 6. 实现：地图 API

下面四段代码组成完整 BFS。每段只做一件事。先把图变成「给一个点，能列出邻居」。
"""),
        code("""
from collections import deque
from lib.pretty import draw_grid, print_step

# GRID[y][x]：0 可走，1 墙。不要写成 GRID[x][y]，和图像习惯相反。
GRID = [
    [0, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
]
H, W = len(GRID), len(GRID[0])
START, GOAL = (0, 0), (3, 2)
OBSTACLES = {(x, y) for y in range(H) for x in range(W) if GRID[y][x] == 1}


def in_bounds(x, y):
    # 防止 x=-1 或 x=W 时 Python 用负数下标「绕到最后一列」——那是静默错路。
    return 0 <= x < W and 0 <= y < H


def passable(pos):
    x, y = pos
    return in_bounds(x, y) and GRID[y][x] == 0


def neighbors(pos):
    # 返回 [(邻点, 边权), ...]。本课边权恒 1。
    # 顺序写死：右、左、下、上。换顺序只换并列最短路的选择，不换边数。
    x, y = pos
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nxt = (x + dx, y + dy)
        if passable(nxt):
            out.append((nxt, 1))
    return out


print(draw_grid(W, H, obstacles=OBSTACLES, start=START, goal=GOAL))
print("S 的邻居应是 (1,0) 和 (0,1):", neighbors(START))
print("(1,0) 不能往下进墙:", neighbors((1, 0)))
"""),
        md("""
`in_bounds` 必须在读 `GRID[y][x]` **之前**调用。只写 `GRID[y][x]==0` 会在越界时抛异常或（若用 `arr[-1]`）走到错误格子。

`neighbors` 不返回墙、不返回界外。BFS 本体不再判断「能不能走」，只判断「见过没有」。职责分离：图 API vs 搜索。

---

## 7. 实现：回溯

不把整条路径跟着每个点复制。每个点只记一个父亲。终点找到后往回爬。

`came_from[s] is None` 是爬升终止条件。若忘记给起点赋值 `None`，回溯会 `KeyError` 或死循环。
"""),
        code("""
def reconstruct(came_from, goal):
    # 从 goal 沿 came_from 走到 start。因为是往回走，最后 reverse。
    node = goal
    path = [node]
    while came_from[node] is not None:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path


fake = {
    (0, 0): None,
    (1, 0): (0, 0),
    (2, 0): (1, 0),
    (3, 0): (2, 0),
    (3, 1): (3, 0),
    (3, 2): (3, 1),
}
print("应打印手算那条路径:", reconstruct(fake, (3, 2)))
"""),
        md("""
## 8. 实现：BFS 主循环（逐行）

| 行 | 代码在干什么 |
|----|----------------|
| `queue = deque([start])` | 双端队列。只在右边 `append`、左边 `popleft` ⇒ FIFO。 |
| `came_from = {start: None}` | 起点已发现；值 None 表示回溯到此结束。兼作 visited。 |
| `dist[start] = 0` | 起点边数 0。 |
| `while queue` | 还有没扩展的点。空了还没碰到 t ⇒ 不可达。 |
| `current = queue.popleft()` | **扩展**：第一次从队里取出该点。等权时 dist 已最优。 |
| `if current == goal` | 第一次取出终点即可返回。 |
| `for nxt, _ in neighbors` | 看所有出边。`_cost` 本课不用，留给 Dijkstra。 |
| `if nxt in came_from: continue` | 见过就丢。第一次见才是最短。 |
| 写入 came_from / dist 再 append | **先标记再入队**，防止同一点进队两次。 |

`deque` 来自 `collections`。列表 `pop(0)` 是 \(O(n)\)，不要用。
"""),
        code("""
def bfs(start, goal, verbose=True):
    queue = deque([start])
    came_from = {start: None}
    dist = {start: 0}
    step = 0
    while queue:
        current = queue.popleft()
        step += 1
        if verbose:
            print_step(
                step,
                f"扩展 {current}（dist={dist[current]}）",
                draw_grid(
                    W, H,
                    obstacles=OBSTACLES,
                    start=start,
                    goal=goal,
                    open_nodes=list(queue),
                    closed=list(came_from),
                    current=current,
                ),
                extra=f"queue={list(queue)}",
            )
        if current == goal:
            path = reconstruct(came_from, goal)
            if verbose:
                print("路径", path, "边数", dist[goal])
                print(draw_grid(W, H, obstacles=OBSTACLES, start=start, goal=goal, path=path))
            return path, dist[goal]
        for nxt, _cost in neighbors(current):
            if nxt in came_from:
                continue
            came_from[nxt] = current
            dist[nxt] = dist[current] + 1
            queue.append(nxt)
    if verbose:
        print("失败：队列空，终点从未入队。")
    return None, None


path, cost = bfs(START, GOAL)
"""),
        md("""对照第 5 节表：第 1 步扩展 (0,0)，队列变成 (1,0),(0,1)。字符图里 `o` 是队列，`x` 是已发现（含已扩展），`*` 是当前。

---

## 9. 失败、复杂度、常见 bug

**不可达：** 中间一堵墙。队列处理完左半边就空了。
"""),
        code("""
def reachable(start, goal, walls, w=3, h=3):
    def ok(p):
        x, y = p
        return 0 <= x < w and 0 <= y < h and p not in walls
    q = deque([start])
    seen = {start}
    while q:
        c = q.popleft()
        if c == goal:
            return True
        x, y = c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if ok(n) and n not in seen:
                seen.add(n)
                q.append(n)
    return False


print("竖墙隔开:", reachable((0, 1), (2, 1), {(1, 0), (1, 1), (1, 2)}))
print("去掉中间墙:", reachable((0, 1), (2, 1), {(1, 0), (1, 2)}))
"""),
        md("""**常见 bug**

1. 用栈 `list.pop()` 当队列 → 变成 DFS，边数不必最短。
2. 出队才写入 visited → 同一点多次入队，最坏指数级。
3. `GRID[x][y]` 写反。
4. 越界不检查，`GRID[-1]` 取到最后一行。
5. 边权不是常数还用 BFS。

**库实现对照：** `lib/search.py` 的 `bfs()` 与上面相同，多了 `frames` 给调度台。`graph.neighbors(u)` 就是本课的 `neighbors`。
"""),
        code("""
from lib.maps import grid_open
from lib.search import bfs as bfs_lib
from lib.studio.widget import PlannerStudio

g = grid_open(8, 8)
result = bfs_lib(g, (0, 0), (7, 7))
print("空 8x8 最短边数应为 14:", result.cost, "扩展", result.expanded)

studio = PlannerStudio()
studio.show_search({**g.to_studio(), "start": [0, 0], "goal": [7, 7]}, result, "BFS")
studio
"""),
        md("""## 10. 条目小结

| 项目 | 内容 |
|------|------|
| 保证 | 等权图上边数最优、有限图完备 |
| 不保证 | 不等权最短路 |
| 结构 | FIFO 队列 + 入队时标记 |
| 时间 | \(O(V+E)\) |
| 下一课 | 边权不同 → Dijkstra，队列换成堆 |

## 练习

1. 邻居改成上、下、左、右，边数变不变？路径点列变不变？
2. 八连通（含斜向，代价仍 1）从 (0,0) 到 (3,2) 最少几步？`neighbors` 要加哪四个偏移？
3. 证明：若某点以 dist=k 入队，则不存在边数 < k 的 s–该点路径。（对 k 归纳。）
"""),
    ]


def lesson_02():
    return "02_dijkstra", "02 Dijkstra：带权最短路（松弛、堆、有向边）", [
        md("""
本课把 BFS 的 FIFO 换成 **按已付代价 g 排序的优先队列**。边可以有不同正长度，图可以有向。

---

## 1. 定义

**Dijkstra 算法**（Dijkstra, 1959）计算加权图上从 \(s\) 到各点（或到 \(t\)）的最短路。

要求：**边权 \(w(u,v)\\ge 0\)**。有负权边时结论不成立，应改 Bellman–Ford。

记 \(g(v)\) 为目前已知的 \(s\\leadsto v\) 代价上界。开始 \(g(s)=0\)，其余 \(+\\infty\)。反复：

1. 在「尚未关闭」的点里选 \(g\) 最小的 \(u\) **关闭**（出堆）。
2. 对每条出边 \(u\\to v\) 做 **松弛**：若 \(g(u)+w(u,v) < g(v)\)，则更新 \(g(v)\) 并把 \(v\) 的前驱设为 \(u\)。

**定理（非负权）：** \(u\) 被关闭时，\(g(u)\) 等于真正最短路长 \(\\delta(s,u)\)。

直觉：若还存在更短的 \(s\\leadsto u\)，这条路上第一个未关闭点 \(x\) 会有 \(g(x)<g(u)\)，堆会先弹出 \(x\) 而不是 \(u\)。非负权保证路上代价不会越走越便宜到「后面的点比前面还小」。

---

## 2. BFS 错在哪（数值例子）

```
s --1--> a --1--> t     总长 2，两步
s --10--> t             总长 10，一步
```

BFS 按步数先看见 `s→t`，宣布最短，错。Dijkstra 先关闭 s，松弛得 \(g(a)=1, g(t)=10\)；再关闭 a（g=1 更小），松弛 \(g(t)=\\min(10,1+1)=2\)。正确。

等权时 Dijkstra 与 BFS **选出的代价相同**（实现仍用堆，常数更大）。

---

## 3. 优先队列：两种实现

教科书常写 decrease-key：v 的 g 变小就改堆里那个元素。Python `heapq` **没有** decrease-key。

教学与工程常用 **惰性堆**：

- 每次 g 变小就 `heappush` 一个新 `(g, v)`，旧的更大 g 留在堆里。
- 弹出时若 `v` 已经关闭（或弹出的 g 不是当前 `g_score[v]`），跳过。

正确性不变，最坏堆里 \(O(E)\) 个条目，时间 \(O(E\\log E)\)，稀疏图可接受。

元组写成 `(g, counter, node)`：`counter` 是单调整数，避免 `g` 相同去比较 `node`（点可能是坐标元组，能比；若是不可比对象会崩）。

---

## 4. 伪代码（惰性堆，与下面 Python 一致）

```
function Dijkstra(G, s, t):
    g[s] ← 0; 其余视为 ∞
    came_from[s] ← NIL
    push heap (0, s)
    closed ← ∅
    while heap 非空:
        (gu, u) ← pop 最小 g
        if u ∈ closed: continue
        closed.add(u)
        if u = t: return Reconstruct(came_from, t)
        for each 边 (u, v, w):
            alt ← gu + w
            if alt < g[v]:          # 松弛成功
                g[v] ← alt
                came_from[v] ← u
                push heap (alt, v)
    return FAILURE
```

有向图：循环只扫 **出边**。没有反向边就不会走回去。把无向边存成两条有向边。

复杂度：二叉堆 \(O((V+E)\\log V)\)（经典 decrease-key 版）或惰性堆 \(O(E\\log E)\)。

---

## 5. 手算（有向）

课程图 `topo_oneway`：环 I0→I1→I2→I3→I4→I5→I0，另有 I1→I4，I4↔G0，I2↔G1。边权 1。求 I0→G1。

一种最短路：I0–I1–I2–G1，g=3。I1 不能一步到 I0。请先打印邻居再手填 g。
"""),
        PATH,
        code("""
from lib.maps import topo_oneway

g = topo_oneway()
print("出边列表（有向）：")
for name in sorted(g.nodes):
    print(f"  {name}: {g.neighbors(name)}")
"""),
        md("""
## 6. 逐行实现

松弛那四行是算法心脏：`tentative = g_cur + cost` 就是 \(g(u)+w(u,v)\)；只有严格更小才改前驱。相等时不改，保持先发现的父亲（稳定）。
"""),
        code("""
import heapq


def reconstruct(came_from, goal):
    node = goal
    path = [node]
    while came_from[node] is not None:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path


def dijkstra(graph, start, goal, verbose=True):
    heap = []
    counter = 0
    g_score = {start: 0.0}
    came_from = {start: None}
    heapq.heappush(heap, (0.0, counter, start))
    closed = set()
    step = 0
    while heap:
        g_cur, _, current = heapq.heappop(heap)
        if current in closed:
            # 惰性堆：过期条目。更小的 g 已经处理过 current。
            continue
        closed.add(current)
        step += 1
        if verbose:
            print(f"关闭 {current:3}  g={g_cur:.1f}  closed={sorted(closed, key=str)}")
        if current == goal:
            path = reconstruct(came_from, goal)
            if verbose:
                print("路径", path, "代价", g_cur)
            return path, g_cur
        for nxt, cost in graph.neighbors(current):
            # graph.neighbors 只给合法出边：有向、不碰墙都在图 API 里处理完了
            tentative = g_cur + cost
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                counter += 1
                heapq.heappush(heap, (tentative, counter, nxt))
                if verbose:
                    print(f"    松弛 {current} -{cost}-> {nxt}  新g={tentative:.1f}")
    if verbose:
        print("不可达")
    return None, float("inf")


path, cost = dijkstra(g, "I0", "G1")
"""),
        md("""
关闭顺序应接近：I0(g=0) → I1(1) → I2 与 I4(2) → G1(3)… 具体并列谁先由 counter 决定。

**负权为何失败：** 关闭 u 之后，若存在 u 经一条负边绕到更便宜，定理的「路上 g 递增」破了，已关闭点的 g 还可能再降，算法不会回去改。

---

## 7. 与 BFS、库函数对照
"""),
        code("""
from lib.maps import grid_open
from lib.search import bfs, dijkstra as dijkstra_lib

grid = grid_open(8, 8)
b = bfs(grid, (0, 0), (7, 7), record=False)
d = dijkstra_lib(grid, (0, 0), (7, 7), record=False)
print("等权网格 BFS 边数", b.cost, "Dijkstra", d.cost, "相等?", b.cost == d.cost)
print("I1 的出边有没有 I0（应为没有）:", [n for n, _ in g.neighbors("I1")])
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.search import dijkstra as dijkstra_lib
from lib.maps import grid_wall

gw = grid_wall()
r = dijkstra_lib(gw, (0, 0), (7, 7))
print("墙图代价", r.cost, "扩展", r.expanded)
studio = PlannerStudio()
studio.show_search({**gw.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "Dijkstra")
studio
"""),
        md("""库 `lib/search.py` 的 `best_first(..., heuristic=lambda a,b:0)` 就是 Dijkstra：按 `g + 0` 出队。下一课把 0 换成 h。

## 条目小结

| 项目 | 内容 |
|------|------|
| 前提 | \(w\\ge 0\) |
| 操作 | 关最小 g 点 + 松弛出边 |
| 堆 | 惰性插入，过期弹出跳过 |
| 有向 | 只迭代出边 |
| 下一课 | \(f=g+h\) → A* |

## 练习

1. 纸上跑 `s-1-a-1-t` 与 `s-10-t`，写出每次关闭和松弛。
2. 若 `tentative == g_score[nxt]` 也更新 came_from，路径对不对？唯一吗？
3. 从 G1 搜回 I0，必须绕环，不能走 I2←I1。打印路径验证。
"""),
    ]


def lesson_03():
    return "03_astar", "03 A*：启发搜索（可采纳、一致、与 Dijkstra 的一行之差）", [
        md("""
A*（Hart, Nilsson, Raphael, 1968）是带启发的 Dijkstra。百科式写法如下。

---

## 1. 定义

对每个顶点维护

\[
f(n)=g(n)+h(n)
\]

- \(g(n)\)：从起点到 n 的已知代价（与 Dijkstra 相同）
- \(h(n)\)：从 n 到终点的 **估计**（启发）
- 优先队列按 **f** 取最小，而不是按 g

直观：g 管「已经花了多少」（避免贪地乱走），h 管「还剩多少」（避免往远离终点的方向扩）。

特例：

| h | 算法 |
|---|------|
| \(h=0\) | Dijkstra / 一致代价搜索 UCS |
| 只用 h、忽略 g | 贪心最佳优先，**不必最优** |
| 等权 + 队列不用 f | BFS |

---

## 2. 可采纳（admissible）

\(h\) **可采纳**：对任意 n，\(h(n)\\le h^*(n)\)，其中 \(h^*\) 是 n 到目标的真实最短剩余。即 **从不高估**。另有 \(h(\\text{goal})=0\)。

**定理：** h 可采纳 ⇒ A* 返回的路径最优（图有限、边权非负；见下节「关闭」细节）。

证明梗概：设 A* 返回路径 P 代价 \(w(P)\)，最优为 \(w^*\\)。若 \(w(P)>w^*\)，看最优路上第一个还在 open 里的点 n。因 h 可采纳，\(f(n)=g^*(n)+h(n)\\le w^* < w(P)\\)。A* 应先扩展 n 而不是把 P 的终点弹出。矛盾。

构造可采纳 h 的标准办法：解一个 **放宽问题** 的最优剩余。例如网格去掉墙，剩余就是曼哈顿距离。

---

## 3. 一致 / 单调（consistent / monotonic）

\(h\) **一致**：对每条边 \(u\\to v\)，

\[
h(u)\\le w(u,v)+h(v)
\]

即三角不等式。一致 ⇒ 可采纳。

一致时：一个点 **弹出 open 之后** g 不会再变小，可以放进 closed **永不重开**。  
只可采纳不一致时：可能必须把已关闭点重新放回 open（Wikipedia 伪代码备注）。惰性堆 + `if current in done: continue` 在不一致时 **可能不最优**。本课网格曼哈顿是一致的，关闭即可。

---

## 4. 网格上的 h

四连通、每步代价 1：

\[
h_{\\mathrm{man}}((x,y),(x',y'))=|x-x'|+|y-y'|
\]

一步最多让曼哈顿减 1，故 \(h\\le h^*\)，且对边权 1 一致。

若边权是欧氏长度、又可任意方向走，欧氏距离 \(\\sqrt{dx^2+dy^2}\) 可采纳。四连通却用欧氏：仍可采纳（欧氏 ≤ 曼哈顿 ≤ 真实四连通剩余），但偏乐观，扩展会多一点。

**不可采纳例子：** \(h=50\) 常数，或 \(h=10\\times\) 曼哈顿。A* 会过分往终点冲，可能错过真最短。

---

## 5. 伪代码

与 Dijkstra 只有 **堆键** 和 **松弛后的 f** 不同：

```
f[s] ← h(s)
push (f[s], s)
while heap:
    u ← pop 最小 f
    if u 已关闭: continue
    关闭 u
    if u = t: return 路径
    for v in 邻居(u):
        alt ← g[u] + w(u,v)
        if alt < g[v]:
            g[v] ← alt
            came_from[v] ← u
            push (alt + h(v), v)     # 唯一多出来的 +h(v)
```

时间仍取决于堆，最坏与 Dijkstra 同阶；h 越好，实际扩展越少。最坏启发 h=0 时退回 Dijkstra 的扩展集。

---

## 6. 手算要点

墙在 x=3、y=0..6，缺口 (3,7)。S=(0,0)，G=(7,7)。\(h(S)=14\)。

A* 会优先扩展 f 小的：同样 g 时更靠近 G（h 小）的先出。墙挡住直线，仍必须先绕到 y=7，但墙左侧向下的点 f 大，会少扩展。下一格代码会打印每个弹出点的 g/h/f。
"""),
        PATH,
        code("""
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


print("h(S,G) =", manhattan((0, 0), (7, 7)))
print("缺口 (3,7) 的 h =", manhattan((3, 7), (7, 7)))
print("墙左下 (0,7) 的 h =", manhattan((0, 7), (7, 7)), "（离 G 仍远，f 会偏大）")
"""),
        md("""
## 7. 从 Dijkstra 改 A*：只改出队键

把 `heappush(heap, (tentative, ...))` 改成 `(tentative + h(nxt, goal), ...)`。第一次 push 起点用 `h(start,goal)`。其余松弛、came_from、惰性跳过，一字不改。
"""),
        code("""
import heapq
from lib.maps import grid_wall


def reconstruct(came_from, goal):
    node = goal
    path = [node]
    while came_from[node] is not None:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path


def astar(graph, start, goal, h=manhattan, verbose=False):
    heap = []
    counter = 0
    g_score = {start: 0.0}
    came_from = {start: None}
    heapq.heappush(heap, (h(start, goal), counter, start))
    closed = set()
    expanded = 0
    while heap:
        _f, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        g_cur = g_score[current]
        if verbose:
            hn = h(current, goal)
            print(f"弹出 {current}  g={g_cur:.0f}  h={hn:.0f}  f={g_cur+hn:.0f}")
        if current == goal:
            return reconstruct(came_from, goal), g_cur, expanded
        for nxt, cost in graph.neighbors(current):
            tentative = g_cur + cost
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                counter += 1
                # 与 Dijkstra 的唯一差别：键是 g+h 不是 g
                heapq.heappush(heap, (tentative + h(nxt, goal), counter, nxt))
    return None, float("inf"), expanded


graph = grid_wall()
path, cost, n_exp = astar(graph, (0, 0), (7, 7), verbose=True)
print("代价", cost, "扩展", n_exp)
"""),
        md("""
看打印：f 小的点先弹出。墙右边的点要等绕过缺口之后 g 才有限。

---

## 8. 实验：h=0、曼哈顿、胡乱 h
"""),
        code("""
from lib.search import astar as astar_lib, dijkstra

d = dijkstra(graph, (0, 0), (7, 7), record=False)
a = astar_lib(graph, (0, 0), (7, 7), record=False)
a0 = astar(graph, (0, 0), (7, 7), h=lambda p, q: 0)
bad = astar(graph, (0, 0), (7, 7), h=lambda p, q: 50)

print("Dijkstra     代价", d.cost, "扩展", d.expanded)
print("A* 曼哈顿    代价", a.cost, "扩展", a.expanded, "应==Dijkstra代价")
print("A* h=0       代价", a0[1], "扩展", a0[2], "应接近 Dijkstra 扩展")
print("A* h=50 乱估 代价", bad[1], "扩展", bad[2], "可能 > 最优")
"""),
        md("""库 `lib.search.best_first` 用参数 `weight`：键是 `g + weight*h`。`weight=1` 即本课 A*。源码里搜 `weight * heuristic` 那一行。
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.search import astar as astar_lib

r = astar_lib(graph, (0, 0), (7, 7))
studio = PlannerStudio()
studio.show_search({**graph.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "A*")
studio
"""),
        md("""单步：波前不是 Dijkstra 的菱形匀速扩散，而是被 h 拉成朝向 G 的一瓣（有墙时会变形）。

## 条目小结

| 项目 | 内容 |
|------|------|
| 公式 | \(f=g+h\) |
| 最优 | h 可采纳（关闭策略在一致时最简单） |
| 网格 h | 四连通 → 曼哈顿 |
| 实现差 | 相对 Dijkstra 只改堆键 |
| 退化 | h=0 → Dijkstra；等权 FIFO → BFS |

## 练习

1. 证明四连通、步长 1 时曼哈顿可采纳。
2. 一致条件 \(h(u)\\le 1+h(v)\) 对相邻格是否成立？曼哈顿差最多 1。
3. 用 `h=0` 跑墙图，扩展次数应与 Dijkstra 同阶。
"""),
    ]
