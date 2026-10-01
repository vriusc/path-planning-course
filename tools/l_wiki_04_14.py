"""Wiki-style lessons 04–14."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_04():
    return "04_weighted_astar", "04 加权 A*：有界次优（w-admissible）", [
        md("""
## 1. 定义

**加权 A\\***（Weighted A\\*，Pohl 1970 一带）把 A\\* 的键改成

\\[
f(n)=g(n)+w\\,h(n),\\qquad w\\ge 1
\\]

- \(w=1\)：普通 A\\*，可采纳 h 时最优。
- \(w>1\)：更听信启发，少扩展、路径可能更长。

**有界次优：** h 可采纳且一致时，返回代价 \(\\le w\\cdot OPT\)。

Anytime A\\*：先大 w 很快出解，再把 w 降到 1 改善（ARA\\* 等）。本课只实现固定 w。

---

## 2. 和 A\\* / 贪心的关系

| 算法 | 堆键 | 保证 |
|------|------|------|
| Dijkstra | \(g\) | 最优 |
| A\\* | \(g+h\) | h 可采纳 ⇒ 最优 |
| 加权 A\\* | \(g+w h\) | \(\\le w\\cdot OPT\) |
| 贪心最佳优先 | \(h\) | 无 |

\(w\\to\\infty\) 时行为接近贪心。

---

## 3. 不变量

设 h 可采纳。弹出终点 n 时，open 里任意最优路上的点 m 满足 \(f(m)\\le w\\cdot OPT\)（证明把 A\\* 最优证明里的 \(h\\le h^*\) 换成 \(w h\)）。因此返回值不会超过 \(w\\cdot OPT\)。

**注意：** 网上有的实现写 \(f=g/w+h\) 或 \(f=g+(2w-1)h\)，界限陈述不同。本仓库与 Wikipedia 常见形式一致：`g + w*h`。

---

## 4. 伪代码

与 A\\* 完全相同，只改一处：

```
push (g[s] + w * h(s), s)
...
push (alt + w * h(v), v)
```

复杂度同 A\\*；w 越大实际扩展越少，最坏仍 \(O(E\\log V)\)。

---

## 5. 手算

同一条边权 1 的路，h 曼哈顿。某点 g=4、h=6：

- w=1：f=10
- w=1.5：f=13
- w=3：f=22

更靠近终点、h 小的点会被提前弹出，哪怕绕路使 g 变大。
"""),
        PATH,
        md("""## 6. 实现：就是 A\\* 加参数 w

`lib.search.astar(..., weight=w)` 在松弛后：

`heapq.heappush(heap, (tentative + weight * heuristic(nxt, goal), ...))`

自己写时从第 03 课的 `astar` 把这一行改掉即可。
"""),
        code("""
from lib.maps import grid_wall
from lib.search import astar

g = grid_wall()
s, t = (0, 0), (7, 7)
opt = astar(g, s, t, record=False)
print("OPT", opt.cost, "扩展", opt.expanded)
for w in (1.0, 1.5, 3.0):
    r = astar(g, s, t, weight=w, record=False)
    ok = r.cost <= w * opt.cost + 1e-6
    print(f"w={w:3}  代价={r.cost:5}  上限={w*opt.cost:5.1f}  扩展={r.expanded:4}  界限成立={ok}")
"""),
        md("""## 7. 逐行（相对 A\\*）

| 位置 | 干什么 |
|------|--------|
| `weight=1` 默认 | 退回 A\\* |
| `tentative + weight * h` | 唯一改动 |
| 返回的 `result.cost` | 仍是真实 g，不是 f |

## 常见 bug

- 用 f 当路径代价打印，会把 h 算进去，数字偏大。
- w<1 没有「优于最优」这回事，会破坏可采纳证明。
- 以为加权 A\\* 总比 A\\* 短：恰恰相反，通常更长、更快。
"""),
        code("""
from lib.studio.widget import PlannerStudio

r = astar(g, s, t, weight=1.5)
studio = PlannerStudio()
studio.show_search({**g.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "weighted A*")
studio
"""),
        md("""## 练习

1. 证明或反驳：w 越大路径单调变长。
2. 连续两次：先 w=3 再 w=1，第二次不应比最优差。
"""),
    ]


def lesson_05():
    return "05_dstar_lite", "05 D* Lite：从目标往回的增量最短路", [
        md("""
## 1. 定义

**D\\* Lite**（Koenig & Likhachev, 2002）在 **边权变化** 后重修最短路，而不必从当前点重新 A\\*。机器人向目标走时前方突然堵住，是典型场景。名字来自 Stentz 的 D\\*；Lite 是更简单的维护方式。

它从 **目标** 向全图传播「还要花多少」，类似反向 Dijkstra，但用 rhs/g 两套值支持局部更新。

---

## 2. 和 A\\* / D\\* 的关系

| | A\\* | D\\* Lite |
|--|--|--|
| 搜索方向 | 从起点向前 | 从目标向后 |
| 图变化 | 整棵树作废 | 只更新受影响点 |
| 一次查询 | 强 | 多次重规划时更强 |

---

## 3. 不变量

每个点 u：

- \(g(u)\)：目前记下的、u 到目标的代价
- \(rhs(u)=\\min_{v\\in succs(u)}\\big(c(u,v)+g(v)\\big)\)（目标的 rhs=0）

若 \(g=rhs\)，该点 **局部一致**。堆 U 里是不一致的点。主循环直到起点局部一致，且堆顶键不优于起点的键。

此时从 start 每步走到使 \(c+g(v)\) 最小的邻居，得到最短路。

边被删/加后：提高 \(km\)（避免重排整个堆），对受影响点 `UpdateVertex`，再 `ComputeShortestPath`。

---

## 4. 伪代码（与 `DStarLite` 类对应）

```
rhs[goal] ← 0;  U.insert(goal, Key(goal))
ComputeShortestPath:
    while U.TopKey < Key(start) 或 rhs[start] ≠ g[start]:
        u ← U.pop()
        if g[u] > rhs[u]:
            g[u] ← rhs[u]
            对每个前驱 s: UpdateVertex(s)
        else:
            g[u] ← ∞
            UpdateVertex(u) 及前驱
UpdateVertex(u):
    若 u≠goal: rhs[u] ← min_v c(u,v)+g[v]
    从 U 删除 u
    若 g[u]≠rhs[u]: U.insert(u, Key(u))
Key(u) = (min(g,rhs) + h(start,u) + km,  min(g,rhs))
```

边变化：`km += h(last, start)`，然后 UpdateVertex 两端。

---

## 5. 实现对照（`lib/algos/single_agent.py`）

| 方法 | 干什么 |
|------|--------|
| `_key` | 二元组优先级，h 用当前 start |
| `_insert` | 教学用列表排序，不是二叉堆 |
| `_update_vertex` | 重算 rhs，不一致则入 U |
| `_predecessors` | 网格=邻居；有向图扫谁指向 u |
| `compute` | 直到 start 一致 |
| `_extract_path` | 沿 c+g(v) 下降走到 goal |
| `edge_blocked` | 图已改完后调用 |

教学实现的 U 是排序列表，最坏较慢；论文用堆。
"""),
        PATH,
        code("""
from lib.maps import grid_maze
from lib.algos.single_agent import DStarLite
from lib.search import astar
from lib.pretty import draw_grid

g = grid_maze()
s, t = (0, 0), (7, 7)
planner = DStarLite(g, s, t)
r1 = planner.compute()
print("静态 D* Lite", r1.cost, "A*", astar(g, s, t, record=False).cost)
print(draw_grid(g.width, g.height, obstacles=g.obstacles, start=s, goal=t, path=r1.path))

mid = r1.path[len(r1.path) // 2]
print("封掉", mid)
g.block(mid)
planner.edge_blocked(r1.path[r1.path.index(mid) - 1], mid)
r2 = planner.compute()
print("新代价", r2.cost, "还经过 mid?", mid in r2.path)
print(draw_grid(g.width, g.height, obstacles=g.obstacles, start=s, goal=t, path=r2.path))
"""),
        md("""## 常见 bug

- 封边后忘了改图、只调 `edge_blocked`：rhs 仍按旧邻居算。
- 有向图用 `neighbors` 当前驱：更新会漏。
- 提取路径时不防环：g 未一致时可能转圈。

## 练习

打开 `compute` 的 `if g>rhs` / `else` 两支，用自己的话注释「过一致」和「欠一致」。
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
## 1. 定义

**Jump Point Search**（Harabor & Grastien, AAAI 2011）在 **均匀代价规则网格** 上加速 A\\*：直线上的对称最短路不进堆，只把「跳点」当后继。

跳点：沿一个方向走，直到终点、被迫邻居（墙角必须转弯），或本课教学版的「此方向走不下去的最后一格」。

---

## 2. 为何能剪

空地从 (0,0) 到 (3,2)，先右后上与先上后右边数相同。A\\* 会扩展中间所有排列。JPS 向右一直跳，直到该方向没有新信息。

**只适用于规则网格。** 任意拓扑没有「沿轴跳」的几何，本仓库对 `TopoMap` 返回 `inapplicable`。

---

## 3. 伪代码

```
function JPS(grid, s, t):
    同 A*，但 Successors(u) 不是四邻居，而是：
    for 方向 d in {右,左,下,上}:
        jp ← Jump(u, d)
        if jp ≠ nil: 产生 jp，代价 = 曼哈顿(u,jp)

Jump(x, d):
    n ← 沿 d 走一步
    若出界或墙: return 教学策略下的「当前格或 nil」
    若 n = t 或 Forced(n,d): return n
    return Jump(n, d)   # 继续跳
```

本课 `jps()`：`jump` 若前方无跳点则返回该方向最后一个可走格（保证四连通完备），再在跳点之间把直线格子填回路径。

---

## 4. 实现表（`lib/algos/single_agent.py` 的 `jps`）

| 函数 | 作用 |
|------|------|
| `forced` | 墙在侧面、前方斜侧可走 ⇒ 必须在此转向 |
| `jump` | 沿 (dx,dy) 递归直到 forced/目标/堵住 |
| `successors` | 四方向各 jump 一次 |
| 主循环 | 标准 A\\* 堆，g 用跳步的曼哈顿长度 |
| 填格子 | 两跳点间按方向逐步插入 |

复杂度：最坏仍可能扩很多点；空地或长走廊上远小于 A\\*。
"""),
        PATH,
        code("""
from lib.maps import grid_wall, topo_oneway
from lib.algos.single_agent import jps
from lib.search import astar

g = grid_wall()
s, t = (0, 0), (7, 7)
a = astar(g, s, t, record=False)
j = jps(g, s, t, record=False)
print("A* 扩展", a.expanded, "JPS 扩展", j.expanded, "代价", a.cost, j.cost)
print("拓扑图应 inapplicable:", jps(topo_oneway(), "I0", "G1").extra)
"""),
        md("""## 常见 bug

- 忘了把跳点之间的格子填回去，路径会「瞬移」。
- 八连通 JPS 的 forced 规则与四连通不同，不要混。
- 把 JPS 用在路口拓扑上。

## 练习

空 8×8、无墙，JPS 扩展应明显小于 A\\*。改 `grid_open` 试一次。
"""),
        code("""
from lib.studio.widget import PlannerStudio
r = jps(g, s, t)
studio = PlannerStudio()
studio.show_search({**g.to_studio(), "start": [0, 0], "goal": [7, 7]}, r, "JPS")
studio
"""),
    ]


def lesson_07():
    return "07_reservation_lock", "07 资源锁：时空占用表", [
        md("""
## 1. 定义

**占用表 / 预约表**（reservation table）记录「谁在何时占用哪」。多车、动态障碍的底层数据结构。不是搜索算法，但是后面时间 A\\* / SIPP / HCA\\* 的输入。

三类键：

| 锁 | 键 | 禁止 |
|----|----|------|
| 顶点 | (v, t) | 两智能体同一时刻同一点 |
| 边 | (u,v,t) | t 拍从 u 走到 v 时，对向 (v,u,t) 也占用 |
| 段 issued | v | 已承诺给某车、尚未走完的点 |

---

## 2. 不变量

- `occupy` 失败 ⇒ 表不变（不覆盖别人）。
- 自己占的格 `vertex_free` 对本人仍为真（可停留）。
- 边锁同时挡 (a,b,t) 与 (b,a,t)，防止对向换位。

---

## 3. 伪代码

```
occupy(v,t,agent):
    if table[v,t] 存在且 ≠ agent: return false
    table[v,t] ← agent; return true

vertex_free(v,t,agent):
    return table[v,t] 空 或 = agent

issue_segment(nodes, agent):
    若任一 node 已被别人 issued: return false
    全部标成 agent
```

`safe_intervals(v, horizon, agent)`：把 0..horizon 里被别人占的时刻挖掉，得到空闲半开区间 [lo,hi)，SIPP 要用。
"""),
        PATH,
        md("""## 4. 自己写最小顶点表（逐行）
"""),
        code("""
class MiniTable:
    def __init__(self):
        self.vertex = {}

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


table = MiniTable()
print("a 占 C2@t=1", table.occupy("C2", 1, "a"))
print("b 同键", table.occupy("C2", 1, "b"))
print("b 占 t=2", table.occupy("C2", 2, "b"))
table.free("C2", 1, "a")
print("释放后 b 占 t=1", table.occupy("C2", 1, "b"))
"""),
        md("""| 行 | 作用 |
|----|------|
| `key=(node,t)` | 空间×时间，缺一不可 |
| 先 get 再写 | 避免覆盖 |
| 本人可再 occupy | 允许在自己的预约上等待 |

库 `ReservationTable` 再加 `occupy_edge`、`issue_segment`、`safe_intervals`。
"""),
        code("""
from lib.reservation import ReservationTable
t = ReservationTable()
print("a 下发 P0-P2", t.issue_segment(["P0", "P1", "P2"], "a"))
print("b 抢 P2", t.issue_segment(["P2", "P3"], "b"))
t.release_segment(["P0", "P1", "P2"], "a")
print("释放后", t.issue_segment(["P2", "P3"], "b"))
print("C2 空闲区间", t.safe_intervals("C2", 8, "me"))
t.occupy("C2", 2, "x")
print("占 t=2 后", t.safe_intervals("C2", 8, "me"))
"""),
        md("""## 常见 bug

- 只锁点不锁边：对向擦肩会漏检。
- 解锁时 agent 名写错，别人的锁被删。
- `safe_intervals` 用闭区间导致 SIPP 在占用拍仍插入。

## 练习

车路径 A,C1,C2 从 t=0 每步一格，列出全部 (点,t)。另一车从 B 出发，哪些键禁止。
"""),
    ]


def lesson_08():
    return "08_time_astar", "08 时间扩展 A*：状态 (点, 时刻)", [
        md("""
## 1. 定义

**时间扩展 A\\***：把时间离散进状态。状态 \(s=(v,t)\)，动作：

- 移动到邻居，\(t'=t+1\)（本课一步一拍）
- **等待**：\(v'=v, t'=t+1\)

下一格在 \(t'\) 被占用表禁止则动作非法。

输入：图、起终点、`ReservationTable`、horizon T。  
输出：点列（重复点=等待），代价含等待。

---

## 2. 和普通 A\\* 的关系

普通 A\\* 状态=点。时间扩展状态=点×时间，图变大，但每拍占用不同。  
h 仍用空间启发（曼哈顿等），可采纳，因为等待只让 g 变大。

若 `require_goal=False`（WHCA 窗口），返回 horizon 内 h 最小的部分路径。

---

## 3. 不变量

- 返回路径上每个 (path[t], t) 对 agent 顶点空闲。
- 相邻移动满足边空闲。
- 代价 ≥ 空间最短路。

---

## 4. 伪代码（对照 `time_astar`）

```
g[s,0] ← 0
push (h(s), 0, s, 0)          # 键 f, 然后 g, node, t
while heap:
    (f, cost, u, t) ← pop
    if (u,t) 见过: continue
    标记见过
    if u = goal: 回溯点列
    if t ≥ horizon: continue
    for (v, w) in {(u, wait)} ∪ 邻居:
        t2 ← t+1
        if 顶点 (v,t2) 或 边 (u,v,t) 被占: continue
        alt ← cost + w
        松弛 (v,t2)，push (alt+h(v), alt, v, t2)
```

回溯 `came[(v,t2)] = (u,t)`，抽出点列（可含重复）。

复杂度：状态最多 \(O(|V|\\cdot T)\)。
"""),
        PATH,
        md("""## 5. 手算

走廊 A–C1–C2–C3–B。C2 在 t=0,1,2 被占。空间最短 4 拍。t=2 不能进 C2，须在 C1 等待或晚到。
"""),
        code("""
from lib.maps import corridor_headon
from lib.reservation import ReservationTable
from lib.algos.temporal import time_astar
from lib.search import astar

g = corridor_headon()
print("空间", astar(g, "A", "B", record=False).path)
table = ReservationTable()
for t in range(3):
    table.occupy("C2", t, "blocker")
r = time_astar(g, "A", "B", table=table, agent="me")
print("时空", r.path, "代价", r.cost)
print("C2 下标（应 ≥3）", [i for i, n in enumerate(r.path) if n == "C2"])
"""),
        md("""## 6. 实现表（`lib/algos/temporal.py`）

| 行 | 作用 |
|----|------|
| 状态 `(node,t)` | 同一点不同时刻是不同状态 |
| `candidates = [(node,1)] + neighbors` | 等待的边权 1（一拍） |
| `vertex_free` / `edge_free` | 查占用 |
| `seen` | 关闭 (node,t)，一致 h 下不必重开 |
| `horizon` | 防止无限等 |
| `require_goal=False` | 窗口规划返回 best_partial |

路径里相邻相同 ⇒ 等待。

## 常见 bug

- 忘记等待动作：被挡就失败，其实可以等。
- 用空间点当 closed，不同时刻互相杀掉。
- 边冲突检查用 t+1 而不是离开的那一拍 t。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_search(g.to_studio(), r, "time A*")
studio
"""),
    ]


def lesson_09():
    return "09_sipp", "09 SIPP：安全间隔上的 A*", [
        md("""
## 1. 定义

**Safe Interval Path Planning**（Phillips & Likhachev, 2011）：不把每个时刻当状态，而把每个点的空闲时间收成区间 \([lo,hi)\)。

状态 = (点, 第几个空闲区间)。区间内何时到达只记一个到达时刻。

---

## 2. 为何比时间扩展更省

时间扩展：状态 \(O(|V|T)\)。  
SIPP：每点区间数 ≤ 占用次数+1，通常远小于 T。空表时每点一个区间 [0,T)，接近普通 A\\*。

---

## 3. 不变量

- 到达时刻 `arr` 落在所选区间内：`lo ≤ arr < hi`。
- `arr' = max(arr+step, nlo)`：不能早于邻居区间开始进入。
- 空占用表时代价 = 时间扩展 A\\*。

---

## 4. 伪代码

```
intervals[v] ← SafeIntervals(v)     # 由占用表挖洞
选包含 t=0 的起点区间 i0
push (h(s), 0, s, i0)
while heap:
    (f, arr, u, i) ← pop
    if u = goal: return
    [lo,hi] ← intervals[u][i]
    for v in 邻居(u):
        move ← arr+1
        for 区间 j=[nlo,nhi] of v:
            if move ≥ nhi: continue
            earliest ← max(move, nlo)
            if earliest ≥ nhi: continue
            若边在 earliest-1 被占: continue
            松弛 (v,j) 的到达 earliest
```

`safe_intervals`：占用时刻排序，相邻占用之间的空隙即区间。
"""),
        PATH,
        code("""
from lib.maps import corridor_headon
from lib.reservation import ReservationTable
from lib.algos.temporal import sipp, time_astar

g = corridor_headon()
table = ReservationTable()
print("空表 C2", table.safe_intervals("C2", 20, "me"))
for t in range(3):
    table.occupy("C2", t, "blk")
print("占 0,1,2 后", table.safe_intervals("C2", 20, "me"))
ta = time_astar(g, "A", "B", table=table, agent="me")
si = sipp(g, "A", "B", table=table, agent="me")
print("timeA*", ta.cost, ta.expanded, "SIPP", si.cost, si.expanded)
"""),
        md("""## 5. 实现表（`sipp`）

| 块 | 作用 |
|----|------|
| `ivals(n)` | 惰性缓存该点区间 |
| 起点选含 0 的区间 | 否则无解 |
| 双重循环 邻居×区间 | 尝试插入 |
| `earliest=max(move,nlo)` | 早到则等到区间开门 |
| 键 `earliest+h(v)` | 仍是 A\\* |

## 常见 bug

- 区间用闭区间，占用拍被当成空闲。
- 忘记边在 `earliest-1` 的换位检查。
- 把区间编号和到达时刻当成同一个数。

## 练习

占用 {1,2,5}、horizon=8，手写 `safe_intervals`。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_search(g.to_studio(), si, "SIPP")
studio
"""),
    ]


def lesson_10():
    return "10_joint_astar", "10 联合 A*：联合状态空间", [
        md("""
## 1. 定义

k 台智能体的 **联合状态** 是位置元组 \((p_1,\\ldots,p_k)\)。联合 A\\* 在此图上搜最短路（常最小化 SOC 或 makespan）。

后继：每台车选走或停，笛卡尔积，再删

- 顶点冲突：两车同一格
- 边冲突：对向交换

---

## 2. 复杂度

每步分支约 \(5^k\)（四连通+等待）。深度 d 时树 \(5^{kd}\)。这就是后面要拆开搜的原因。

完备且最优（单位代价、有限图），但只适合 k 很小。

---

## 3. 伪代码

```
start ← (s1,...,sk); goal ← (g1,...,gk)
g[start]←0; push (h_sum, start)
while heap:
    S ← pop
    if S = goal: 回溯每车路径
    for 每车动作组合 C:
        if 顶点或边冲突: skip
        松弛 C
h_sum = Σ manhattan(pi, gi)
```

`cap` 限制扩展，防止卡死。
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.prioritized import joint_astar
from lib.maps import grid_open
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_swap()
r = joint_astar(g, starts, goals, cap=20000)
print("2车 found", r["found"], "SOC", r["soc"], "扩展", r["expanded"])

g3 = grid_open(5, 5)
r3 = joint_astar(g3, {"a": (0, 0), "b": (4, 0), "c": (0, 4)},
                 {"a": (4, 4), "b": (0, 4), "c": (4, 0)}, cap=400)
print("3车 cap400 扩展", r3["expanded"], "capped", r3.get("capped"))
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "joint A*")
studio
"""),
        md("""## 实现表（`joint_astar`）

| 行 | 作用 |
|----|------|
| `itertools.product` | 各车动作的笛卡尔积 |
| `occupied` 字典 | 检测两车同一后继格 |
| 双重循环 i<j | 检测对向换位 |
| `ng` 非等待步数和 | 教学 SOC |

## 常见 bug

- 漏边冲突：对向穿过。
- 漏等待：死锁无法「谁先停」。
- closed 用位置不含「谁」，多车会乱（本实现状态已是全元组）。
"""),
    ]


def lesson_11():
    return "11_hca", "11 HCA*：层次协作 A*（优先规划）", [
        md("""
## 1. 定义

**HCA\\***（Hierarchical Cooperative A\\*，Silver 2005）= 固定全序上的优先规划：

1. 按序处理每台车  
2. 对该车做 **时间 A\\***，占用表里已有更高优先级的路径  
3. 成功则把路径写入占用表  

WHCA\\* 是其窗口版。游戏和仓储常用。

---

## 2. 保证

- **不必最优**：顺序差 SOC 会差。
- **不完全**：有向窄廊对头时，两种全序都可能失败（双方都要对方先让，但先走的车占死终点）。
- 若空间足够且允许等待，许多无向网格实例能行。

---

## 3. 伪代码

```
table ← 空
for agent in order:
    π ← TimeA*(start[a], goal[a], table)
    if 失败: return FAILURE
    Reserve(table, π)
return {π}
Reserve: 对路径每个 (v,t) occupy；对每步 occupy_edge
```

FIFO 调度 = 用「谁先请求」当 order 的 HCA\\*。
"""),
        PATH,
        md("""## 4. 自己写外层循环
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.reservation import ReservationTable
from lib.algos.temporal import time_astar
from lib.algos.prioritized import _reserve_path
from lib.agents import is_conflict_free, soc


def hca_simple(graph, starts, goals, order):
    table = ReservationTable()
    paths = {}
    for agent in order:
        res = time_astar(graph, starts[agent], goals[agent], table=table, agent=agent)
        print(agent, "found", res.found, "cost", res.cost, "path", res.path)
        if not res.found:
            return {"found": False, "paths": paths}
        paths[agent] = res.path
        _reserve_path(table, res.path, agent)
    return {"found": is_conflict_free(paths), "paths": paths, "soc": soc(paths)}


g, starts, goals = two_agent_tunnel()
print("序 a,b", hca_simple(g, starts, goals, ["a", "b"])["found"])
"""),
        md("""| 行 | 作用 |
|----|------|
| 同一 `table` 贯穿 | 后车看见前车预约 |
| `_reserve_path` | 把整条时空轨迹锁上 |
| `is_conflict_free` | 用 stay-at-target 再验一次 |

## 常见 bug

- 预约时不锁边。
- 终点无限 stay 占死别人起点（交换任务时经典坑）。
- 每台车一张新表，等于没有协作。
"""),
        code("""
from lib.algos.prioritized import hca
from lib.maps import directed_deadlock_map
from lib.studio.widget import PlannerStudio
r = hca(g, starts, goals, order=["a", "b"])
print("有向死锁", hca(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"})["found"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "HCA*")
studio
"""),
    ]


def lesson_12():
    return "12_whca", "12 WHCA*：窗口化优先规划", [
        md("""
## 1. 定义

**WHCA\\***：HCA\\* 只保证未来 w 拍无冲突。窗口外不管。Silver 2005 与 HCA\\* 同文。

适合目标会变、只下发即将执行的一小段。

---

## 2. 和 HCA\\* / RHCR

HCA\\*：w=∞，一次预约到目标。  
WHCA\\*：一次窗口。  
RHCR：执行一步后再 WHCA（下一课）。

窗口内无冲突；窗口外可能仍交叉。不完全、不最优，与 HCA 相同。

---

## 3. 伪代码

```
for agent in order:
    π ← TimeA*(..., horizon=w, require_goal=False)
    clip π 到长度 ≤ w+1
    Reserve(clip)
```

`require_goal=False`：到不了目标就返回窗口内离目标最近的前缀（08 课 `best_partial`）。
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import whca
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = whca(g, starts, goals, window=3)
print("窗内无冲突", r["found"], r["window_paths"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "WHCA*")
studio
"""),
        md("""## 实现表

| 参数 | 作用 |
|------|------|
| `horizon=window` | 状态 t 不超过 w |
| `require_goal=False` | 允许部分路径 |
| `pad` | 对齐长度以便查窗内冲突 |

## 常见 bug

- horizon 小于到目标的最短步数且 require_goal=True ⇒ 全失败。必须关 require_goal。
- 窗口路径不 pad，冲突检测对不齐时间。
"""),
    ]


def lesson_13():
    return "13_pbs", "13 PBS：在优先级偏序上搜索", [
        md("""
## 1. 定义

**Priority-Based Search**（Ma et al., AAAI 2019）：不要预先固定全序。高层在 **成对优先级约束** 上 DFS/搜索；底层仍是 HCA\\*。

撞车 (a,b) 时分支：

- 子节点：a 优先于 b
- 子节点：b 优先于 a

约束组成 DAG，拓扑排序得到全序再 HCA。

---

## 2. 保证

比固定 FIFO 更能找到可行序。底层仍是优先规划 ⇒ **不完全**（有向死锁）。不保证 SOC 最优（本实现取搜到的可行解中较好者）。

---

## 3. 伪代码

```
search(constraints):
    order ← 拓扑排序(constraints ∪ 车)
    若有环: return
    r ← HCA(order)
    若 r 可行: 记录若更好则更新 best; return
    (a,b) ← r 中第一对冲突
    search(constraints ∪ {a≺b})
    search(constraints ∪ {b≺a})
```

`seen` + `depth` 防无限递归。
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import pbs, hca
from lib.maps import directed_deadlock_map
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = pbs(g, starts, goals)
print("PBS", r["found"], r["soc"], r.get("constraints"))
print("有向死锁 HCA", hca(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"})["found"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "PBS")
studio
"""),
        md("""## 实现表（`pbs.search`）

| 块 | 作用 |
|----|------|
| indeg / 队列 | Kahn 拓扑排序 |
| 环 | 互相要求对方先走 |
| vertex_conflicts | 从失败的 HCA 路径找要分支的一对 |

## 常见 bug

- 约束写成无向，无法排序。
- 不记 seen，同一偏序重复搜。
"""),
    ]


def lesson_14():
    return "14_rhcr", "14 RHCR：滚动时域消冲突", [
        md("""
## 1. 定义

**Rolling-Horizon Collision Resolution**（Li et al., AAAI 2021）：把终身/在线 MAPF 拆成一串窗口 MAPF。

```
每 h 拍（本课 h=1）:
    以当前真实位置为起点
    只对未来 w 拍消冲突（WHCA/CBS/PBS 均可）
    执行第 1 步（或下发 ≤ w 的段）
```

执行层：未锁的段不能走。

---

## 2. 保证

无完备、无最优。窗口短则快、短视；窗口长则接近一次性规划。目标中途改变时不必作废整条路。

---

## 3. 伪代码（本仓库 `rhcr`）

```
pos ← starts
重复 steps 次或全部到达:
    plan ← WHCA(pos, goals, window=w)
    对每车: 执行 plan 的第 1 步，更新 pos
    记录 issued 段长度 ≤ w
```
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import rhcr
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = rhcr(g, starts, goals, window=3, steps=20)
print("到齐", r["found"], "单次下发≤", r["max_issue"])
print("轨迹 a", r["paths"]["a"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "RHCR")
studio
"""),
        md("""## 实现表

| 行 | 作用 |
|----|------|
| `pos` | 模拟器里的当前格 |
| `seg[min(1,...)]` | 每轮只前进一步 |
| `max_issue` | eval：不得超过 window |

## 常见 bug

- 每轮 WHCA 的 table 不空：应只用当前窗口内的车。
- 执行了窗口内全部点却不重规划，失去滚动意义。
"""),
    ]
