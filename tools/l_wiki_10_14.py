"""Wiki-style lessons 10–14: joint A*, HCA*, WHCA*, PBS, RHCR."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_10():
    return "10_joint_astar", "10 联合 A*：联合状态空间", [
        md("""
本课按百科条目写。多车问题第一次正面出现：把 k 台车的位置绑成一个状态再搜。调度台在最后。

---

## 1. 定义

k 台智能体的 **联合状态** 是位置元组 \(S=(p_1,\\ldots,p_k)\)。**联合 A\\*** 在这张隐式图上做 A\\*，通常最小化 SOC（各车到达时间和）或 makespan（最慢车）。

后继：每台车选「走一个邻居」或「停」，做笛卡尔积，再删掉

- **顶点冲突**：两车同一格
- **边冲突 / 换位**：A 走到 B 刚才的格子，同时 B 走到 A 刚才的格子

- 输入：图、各车起终点、扩展上限 `cap`。
- 输出：每车一条同步的点列（同一下标 = 同一拍），或因 cap 失败。

单位代价、有限图上 **完备且最优**。只适合 k 很小。

---

## 2. 和单车 A* / 后面各课

| | 单车 A\\* | 联合 A\\* | HCA\\* / CBS |
|--|--|--|--|
| 状态 | 一个点 | k 个点的元组 | 单车 + 约束或优先级 |
| 最优 | 是 | 是（SOC/makespan 看你怎么写 g） | HCA 否；CBS 是 |
| 分支 | ≤4 | \(\\approx 5^k\) | 单车级 |

联合 A\\* 是正确性的「金标准」：两车小图上，后面任何最优算法的 SOC 都不应更差。它不是工程方案。

---

## 3. 不变量

- g(S) = 从起点联合状态走到 S 的累计移动次数和（本课等待不计 SOC，与库 `soc` 去掉终点停留一致）。
- 弹出目标联合状态时 g 最优。
- 每个后继必须 `_config_ok`：位置两两不同，且无对向换位。

**复杂度：** 每步分支约 \(5^k\)（四连通+等待）。深度 d 时树 \(5^{kd}\)。3 车在 5×5 上空跑，cap 几百就会触顶。

---

## 4. 伪代码

```
start ← (s1,...,sk); goal ← (g1,...,gk)
g[start]←0; push (h_sum, start)
while heap 且 expanded < cap:
    S ← pop
    if S = goal: 回溯，拆成每车路径
    for 每车动作组合 C:          # product
        if 顶点冲突或换位: skip
        ng ← g[S] + (非等待步数)
        松弛 C，h = Σ manhattan(pi, gi)
```

---

## 5. 手算（为什么必须能等待）

两车在两格走廊对换：

```
A: a→  ←b :B     目标互换
```

若不许等待，同时迈步只能换位 → 边冲突，被删。允许一台等、另一台……仍然过不去，因为没有第三格。这张图联合 A\\* 应失败（无解），不是 bug。

换到 3×2 空网格，a 从 (0,0) 到 (2,0)，b 从 (2,1) 到 (0,1)，两人各走对边，不必相遇。联合状态起点 `((0,0),(2,1))`，目标 `((2,0),(0,1))`。
"""),
        PATH,
        md("""
## 6. 实现：两车联合 A*（从零写）
"""),
        code("""
import heapq
import itertools
from lib.maps import grid_open
from lib.pretty import draw_grid
from lib.agents import soc, is_conflict_free


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def joint_astar_tiny(graph, starts, goals, cap=5000, verbose=True):
    # starts/goals: 长度为 2 的元组，顺序固定 (a, b)
    start_s, goal_s = starts, goals
    heap = [(0, 0, start_s)]
    g = {start_s: 0}
    came = {start_s: None}
    expanded = 0
    while heap and expanded < cap:
        _f, cost, state = heapq.heappop(heap)
        expanded += 1
        if verbose and expanded <= 12:
            print(f"扩展#{expanded} {state} g={cost}")
        if state == goal_s:
            chain = []
            cur = state
            while cur is not None:
                chain.append(cur)
                cur = came[cur]
            chain.reverse()
            paths = {"a": [st[0] for st in chain], "b": [st[1] for st in chain]}
            return paths, soc(paths), expanded
        moves = []
        for i in range(2):
            opts = [state[i]] + [n for n, _ in graph.neighbors(state[i])]
            moves.append(opts)
        for combo in itertools.product(*moves):
            if combo[0] == combo[1]:
                continue
            # 对向换位
            if combo[0] == state[1] and combo[1] == state[0] and combo[0] != state[0]:
                continue
            ng = cost + sum(0 if combo[i] == state[i] else 1 for i in range(2))
            if ng < g.get(combo, float("inf")):
                g[combo] = ng
                came[combo] = state
                h = manhattan(combo[0], goal_s[0]) + manhattan(combo[1], goal_s[1])
                heapq.heappush(heap, (ng + h, ng, combo))
    return None, float("inf"), expanded


g = grid_open(3, 2)
print(draw_grid(3, 2, start=(0, 0), goal=(2, 0)))
print("b 从 (2,1) 到 (0,1)，与 a 错开一行")
paths, cost, n_exp = joint_astar_tiny(g, ((0, 0), (2, 1)), ((2, 0), (0, 1)))
print("路径 a", paths["a"])
print("路径 b", paths["b"])
print("SOC", cost, "扩展", n_exp, "无冲突", is_conflict_free(paths))
"""),
        md("""
## 7. 逐行

| 行 | 作用 |
|----|------|
| `state` 二元组 | 联合位置，可哈希，能进 dict |
| `opts = [自己] + 邻居` | 等待 |
| `itertools.product` | 两车动作笛卡尔积 |
| `combo[0]==combo[1]` | 顶点冲突 |
| 换位三项 | 对向穿过 |
| `ng` 非等待步数和 | 教学 SOC |
| `h` 两车曼哈顿和 | 可采纳（忽略相互阻挡，放宽问题） |

---

## 8. 库对照：2 车能解，3 车 cap 就爆
"""),
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.prioritized import joint_astar

g2, starts, goals = two_agent_swap()
r = joint_astar(g2, starts, goals, cap=20000)
print("2车 found", r["found"], "SOC", r["soc"], "扩展", r["expanded"])

g3 = grid_open(5, 5)
r3 = joint_astar(
    g3,
    {"a": (0, 0), "b": (4, 0), "c": (0, 4)},
    {"a": (4, 4), "b": (0, 4), "c": (4, 0)},
    cap=400,
)
print("3车 cap400 扩展", r3["expanded"], "capped", r3.get("capped"), "found", r3["found"])
"""),
        md("""
3 车 cap=400 几乎必然 `capped=True`。这就是后面要拆开搜的原因：HCA 按优先级、CBS 按冲突分支，状态不再是 \(5^k\)。

## 常见 bug

1. 漏边冲突：对向穿过，顶点在下一拍已经错开。
2. 漏等待：死锁无法「谁先停」。
3. closed 只用单车位置。
4. 启发用欧氏、图却是四连通：仍可采纳，但偏松。
5. 不计 cap，3 车会把内核跑死。

## 条目小结

| 项目 | 内容 |
|------|------|
| 状态 | 位置元组 |
| 保证 | 单位代价有限图上最优完备 |
| 代价 | \(5^k\) 分支 |
| 下一课 | 放弃联合状态，改成「谁先规划」 |

## 练习

1. 两格走廊对换，手写所有后继，确认全被冲突删掉。
2. 把等待从 opts 拿掉，3×2 例子还能否解？
3. 为何 h=各车曼哈顿之和可采纳？提示：真实 SOC ≥ 无视其它车的最短路之和。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g2.to_studio(), r, "joint A*")
studio
"""),
    ]


def lesson_11():
    return "11_hca", "11 HCA*：层次协作 A*（优先规划）", [
        md("""
本课按百科条目写。HCA\\* 是仓储/游戏里最常见的多车实用算法：固定全序，后车把前车当移动障碍。调度台在最后。

---

## 1. 定义

**HCA\\***（Hierarchical Cooperative A\\*，Silver, AIIDE 2005）= 固定全序上的优先规划：

1. 按 `order` 处理每台车。
2. 对该车做 **时间 A\\***（08 课），占用表里已有更高优先级的路径。
3. 成功则把路径写入占用表（顶点+边）。

WHCA\\* 是其窗口版（下一课）。FIFO 调度 ≈ 用「谁先请求」当 order 的 HCA\\*。

- 输入：图、起终点、全序。
- 输出：每车一条时空路径，或某台失败。

---

## 2. 保证（务必读）

- **不必最优**：顺序差，SOC 会差。先走堵路口的车，后面全绕。
- **不完全**：有向窄廊对头时，两种全序都可能失败（双方都要对方先让，但先走的车占死通道）。这不是实现 bug，是算法能力边界。
- 无向网格、空位足够、允许等待时，许多实例能行。

对比：联合 A\\* 最优但爆；CBS 最优且常更快；HCA 最快但不保证。

---

## 3. 不变量

- 处理完前 i 台后，这 i 条路径彼此无顶点/边冲突（后车看见了前车的表）。
- 预约必须锁边，否则对向擦肩漏检。
- 终点是否 **无限 stay**：库默认只锁路径上的有限拍。交换任务时若把终点锁到 horizon 末尾，会把别人的起点占死。

---

## 4. 伪代码

```
table ← 空
for agent in order:
    π ← TimeA*(start[a], goal[a], table)
    if 失败: return FAILURE
    Reserve(table, π)
return {π}

Reserve:
    对路径每个 (v,t): occupy 顶点
    对每步 (v, v', t): occupy_edge
```

---

## 5. 手算

开网格两车各走一行，互不相交：任意序都成功，SOC = 两段曼哈顿之和。

有向 `L→M→R`，a 在 L 要去 R，b 在 R 要去 L：b 根本没有出边离开 R，HCA 无论谁先都失败。联合 A\\* / CBS 也失败——图本身无解。HCA 的不完全性出现在 **无向可解、但错误优先级把通道占死** 的图上；教学负例用有向死锁即可。
"""),
        PATH,
        md("""
## 6. 实现：外层循环（底层复用 08 课时间 A*）
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.reservation import ReservationTable
from lib.algos.temporal import time_astar
from lib.algos.prioritized import _reserve_path
from lib.agents import is_conflict_free, soc
from lib.maps import directed_deadlock_map
from lib.pretty import draw_grid


def hca_simple(graph, starts, goals, order):
    table = ReservationTable()
    paths = {}
    for agent in order:
        res = time_astar(graph, starts[agent], goals[agent], table=table, agent=agent)
        print(agent, "found", res.found, "cost", res.cost, "path", res.path)
        if not res.found:
            return {"found": False, "paths": paths, "order": order}
        paths[agent] = res.path
        _reserve_path(table, res.path, agent)
    return {"found": is_conflict_free(paths), "paths": paths, "soc": soc(paths), "order": order}


g, starts, goals = two_agent_tunnel()
print(draw_grid(g.width, g.height, start=starts["a"], goal=goals["a"]))
print("a", starts["a"], "->", goals["a"], "b", starts["b"], "->", goals["b"])
print("序 a,b", hca_simple(g, starts, goals, ["a", "b"])["found"])
print("序 b,a", hca_simple(g, starts, goals, ["b", "a"])["found"])
"""),
        md("""
## 7. 逐行

| 行 | 作用 |
|----|------|
| 同一 `table` 贯穿 | 后车看见前车预约 |
| `time_astar(..., agent=agent)` | 本人的锁对自己 free |
| `_reserve_path` | 顶点+边整条锁上 |
| `is_conflict_free` | 用 stay-at-target pad 再验一次 |

错误写法：每台车 `table = ReservationTable()` ——等于没有协作。
"""),
        code("""
from lib.algos.prioritized import hca

r = hca(g, starts, goals, order=["a", "b"])
print("库 HCA found", r["found"], "SOC", r["soc"], "order", r["order"])

dead = directed_deadlock_map()
print(
    "有向死锁",
    hca(dead, {"a": "L", "b": "R"}, {"a": "R", "b": "L"})["found"],
)
"""),
        md("""
## 常见 bug

1. 预约时不锁边。
2. 终点无限 stay 占死别人起点（交换任务经典坑）。
3. 每台车一张新表。
4. 底层不用时间维、不能等待。
5. 把失败当成「地图无解」——先换个 order 再下结论。

## 条目小结

| 项目 | 内容 |
|------|------|
| 思想 | 全序 + 时间 A\\* + 占用表 |
| 最优 | 否 |
| 完备 | 否（有向/窄廊） |
| 下一课 | 只保证未来 w 拍 |

## 练习

1. 把 `_reserve_path` 改成只 occupy 顶点，造一个对向擦肩的反例。
2. 为何 FIFO（谁先叫车谁优先）在仓储里够用、在对换任务里不够？
3. 三车全序有 6 种。HCA 会试几种？PBS 下一课怎么处理。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "HCA*")
studio
"""),
    ]


def lesson_12():
    return "12_whca", "12 WHCA*：窗口化优先规划", [
        md("""
本课按百科条目写。WHCA\\* 把 HCA\\* 的「一次预约到目标」改成「只保证未来 w 拍」。调度台在最后。

---

## 1. 定义

**WHCA\\***（Windowed HCA\\*，与 HCA\\* 同文，Silver 2005）：仍按全序做时间 A\\*，但

- `horizon = w`
- `require_goal = False`（08 课的部分路径）
- 只把长度 ≤ w+1 的前缀写入占用表

适合目标会变、只下发即将执行的一小段。RHCR（14 课）在外层循环里反复调用它。

---

## 2. 和 HCA* / RHCR

| | HCA\\* | WHCA\\* | RHCR |
|--|--|--|--|
| 窗口 | ∞ | 一次 w 拍 | 每步重规划 w 拍 |
| 到终点 | 必须 | 不必须 | 靠滚动慢慢到 |
| 冲突保证 | 全程 | 仅窗内 | 仅每窗执行的那一步来自无冲突窗 |

不完全、不最优，与 HCA 相同。窗口外路径仍可能交叉——那是下一窗口的事。

---

## 3. 不变量

- `window_paths` pad 到同一长度后，窗内 `is_conflict_free`。
- 单车前缀长度 ≤ w+1（含起点）。
- 远目标：空间最短路 > w 时，必须 `require_goal=False`，否则全员失败。

---

## 4. 伪代码

```
table ← 空
for agent in order:
    π ← TimeA*(..., horizon=w, require_goal=False)
    clip ← π 的前 w+1 个点（失败则原地 pad）
    Reserve(clip)
return window_paths（pad 对齐后再验冲突）
```

---

## 5. 手算

两车各走一行，目标 5 步远，w=3。每人只规划 3 步，停在半路。窗内无交叉。下一窗口从新位置再规划——那是 RHCR。单独跑一次 WHCA **不必**到达。
"""),
        PATH,
        md("""
## 6. 实现：裁窗口 + 对齐
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.reservation import ReservationTable
from lib.algos.temporal import time_astar
from lib.algos.prioritized import _reserve_path
from lib.agents import is_conflict_free, pad


def whca_simple(graph, starts, goals, order, window=3):
    table = ReservationTable()
    paths = {}
    for agent in order:
        res = time_astar(
            graph, starts[agent], goals[agent],
            table=table, agent=agent, horizon=window, require_goal=False,
        )
        print(agent, "found", res.found, "path", res.path, "partial", res.extra)
        if not res.found:
            paths[agent] = [starts[agent]] * (window + 1)
            continue
        clip = res.path[: window + 1]
        paths[agent] = clip
        _reserve_path(table, clip, agent)
    window_paths = {a: pad(p, window + 1)[: window + 1] for a, p in paths.items()}
    return {
        "found": is_conflict_free(window_paths),
        "paths": paths,
        "window_paths": window_paths,
        "window": window,
    }


g, starts, goals = two_agent_tunnel()
r = whca_simple(g, starts, goals, ["a", "b"], window=3)
print("窗内无冲突", r["found"])
print("窗路径", r["window_paths"])
"""),
        md("""
## 7. 逐行

| 参数 | 作用 |
|------|------|
| `horizon=window` | 状态 t 不超过 w |
| `require_goal=False` | 允许部分路径 |
| `clip[:window+1]` | 含起点共 w+1 个点 = w 步 |
| `pad` | 对齐长度再查窗内冲突 |

对比：同样窗口若 `require_goal=True`，到不了的车会失败。
"""),
        code("""
from lib.algos.prioritized import whca
from lib.algos.temporal import time_astar
from lib.reservation import ReservationTable

lib_r = whca(g, starts, goals, window=3)
print("库 WHCA found", lib_r["found"], lib_r["window_paths"])

# 反例：必须到终点 + 短窗口
bad = time_astar(g, starts["a"], goals["a"], horizon=3, require_goal=True)
print("a 要走 5 步、horizon=3、require_goal 时 found", bad.found)
"""),
        md("""
## 常见 bug

1. horizon 小于最短步数且 require_goal=True ⇒ 全失败。
2. 窗口路径不 pad，冲突检测对不齐时间。
3. 把窗内前缀当成全程解，评测「到没到终点」会误判。
4. 窗口外不管，却用全程 `is_conflict_free` 当成功标准。

## 条目小结

| 项目 | 内容 |
|------|------|
| 窗口 | 只保证未来 w 拍 |
| 到终点 | 不要求 |
| 下一课 | 优先级不要预先固定 → PBS |

## 练习

1. w=1 时每车只走一步。两车对头在无向走廊，w=1 够不够换位？
2. 解释 `window+1`：w 步为什么有 w+1 个点。
3. 为何 RHCR 每步重规划，而不是一次 WHCA 把窗内全走完？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), lib_r, "WHCA*")
studio
"""),
    ]


def lesson_13():
    return "13_pbs", "13 PBS：在优先级偏序上搜索", [
        md("""
本课按百科条目写。PBS 不预先固定全序，在「谁优先于谁」的约束上搜索。调度台在最后。

---

## 1. 定义

**Priority-Based Search**（Ma et al., AAAI 2019）：高层在 **成对优先级约束** 上 DFS/搜索；底层仍是 HCA\\*。

撞车 (a,b) 时分支：

- 子节点：a 优先于 b（a≺b 表示 a 先规划）
- 子节点：b 优先于 a

约束组成 DAG，拓扑排序得到全序再跑 HCA。出现环（互相要求对方先走）则剪枝。

- 输入：图、起终点。
- 输出：某个可行全序下的 HCA 路径，以及用到的成对约束。

---

## 2. 保证

比固定 FIFO 更能找到可行序。底层仍是优先规划 ⇒ **不完全**（有向死锁、空位不够）。**不保证 SOC 最优**（本实现记下搜到的可行解中较好者，不是 CBS 那种可采纳高层）。

对比：CBS 在时空约束上分支，最优；PBS 在优先级上分支，更快但不最优。

---

## 3. 不变量

- 约束集只增不减。
- 拓扑排序失败 ⇔ 约束有环 ⇔ 该支剪掉。
- `seen` 避免同一偏序重复搜。

k 车全序 k! 种，PBS 通常只展开「真发生冲突」的那几对，远小于 k!。

---

## 4. 伪代码

```
search(constraints):
    order ← Kahn拓扑(constraints)
    若有环: return
    r ← HCA(order)
    若 r 可行: 记录若更好则更新 best; return
    (a,b) ← r 中第一对冲突
    search(constraints ∪ {a≺b})
    search(constraints ∪ {b≺a})
```

两车时退化为：先试一种序，失败再试反过来——下面就先写这个。

---

## 5. 手算

两车开网格平行走：HCA 第一种序就成功，PBS 不分支。

两车必须「谁让谁」才过得去：第一种序失败，冲突对 (a,b)，分支后某序成功。

有向 L→R 对头：两种序都失败，PBS 也失败。
"""),
        PATH,
        md("""
## 6. 实现：两车先穷举序，再看一般约束搜索
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import hca
from lib.maps import directed_deadlock_map


def pbs_two(graph, starts, goals):
    agents = list(starts)
    a, b = agents[0], agents[1]
    best = None
    for order in ([a, b], [b, a]):
        r = hca(graph, starts, goals, order=order)
        print("试序", order, "found", r["found"], "SOC", r.get("soc"))
        if r["found"] and (best is None or r["soc"] < best["soc"]):
            best = r
            best["constraints"] = [(order[0], order[1])]
    if best is None:
        return {"found": False, "paths": {}, "soc": float("inf")}
    return best


g, starts, goals = two_agent_tunnel()
r2 = pbs_two(g, starts, goals)
print("两车 PBS", r2["found"], r2["soc"], r2.get("constraints"))
print(
    "有向死锁",
    pbs_two(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"})["found"],
)
"""),
        md("""
两车版已经能说明「失败就换序」。k>2 时不能枚举 k!，要用约束 DFS + Kahn。
"""),
        code("""
from collections import defaultdict, deque
from lib.agents import vertex_conflicts, edge_conflicts


def kahn(agents, constraints):
    # constraints: 列表 (hi, lo)，hi 先走
    succ = defaultdict(list)
    indeg = {a: 0 for a in agents}
    for hi, lo in constraints:
        succ[hi].append(lo)
        indeg[lo] += 1
    q = deque([a for a in agents if indeg[a] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for s in succ[n]:
            indeg[s] -= 1
            if indeg[s] == 0:
                q.append(s)
    if len(order) != len(agents):
        return None
    return order


print("a≺b, b≺c =>", kahn(["a", "b", "c"], [("a", "b"), ("b", "c")]))
print("环 a≺b, b≺a =>", kahn(["a", "b"], [("a", "b"), ("b", "a")]))
"""),
        code("""
from lib.algos.prioritized import pbs

r = pbs(g, starts, goals)
print("库 PBS", r["found"], r["soc"], r.get("constraints"))
"""),
        md("""
## 7. 逐行（库 `pbs.search`）

| 块 | 作用 |
|----|------|
| indeg / 队列 | Kahn 拓扑 |
| 环 | 互相要求对方先走 |
| vertex_conflicts | 从失败的 HCA 路径找要分支的一对 |
| seen + depth | 防同一偏序、防无限递归 |

## 常见 bug

1. 约束写成无向，无法排序。
2. 不记 seen，同一偏序重复搜。
3. 冲突双方已经有优先级仍再分支，造环。
4. 把 PBS 当最优算法去比 CBS 的 SOC。

## 条目小结

| 项目 | 内容 |
|------|------|
| 高层 | 成对优先级 DAG |
| 底层 | HCA\\* |
| 最优 | 否 |
| 完备 | 否（同 HCA） |
| 下一课 | 窗口滚起来：RHCR |

## 练习

1. 三车约束 a≺b、c≺b，写出所有合法全序。
2. 为何「HCA 失败才分支」比「预先枚举全序」省？
3. 有向死锁上 PBS 失败，换 CBS 会成功吗？先想再跑 15 课。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "PBS")
studio
"""),
    ]


def lesson_14():
    return "14_rhcr", "14 RHCR：滚动时域消冲突", [
        md("""
本课按百科条目写。RHCR 把终身/在线 MAPF 拆成一串窗口规划。调度台在最后。

---

## 1. 定义

**Rolling-Horizon Collision Resolution**（Li et al., AAAI 2021）：执行层只走一小段，规划层反复对未来 w 拍消冲突。

```
每 h 拍（本课 h=1）:
    以当前真实位置为起点
    只对未来 w 拍消冲突（WHCA / CBS / PBS 均可）
    执行第 1 步（或下发 ≤ w 的段）
```

本仓库 `rhcr` 窗口规划用 WHCA，每轮只前进一步。

终身 MAPF：任务中途出现、目标会变。一次 HCA 到终点的假设不成立，滚动是默认架构。

---

## 2. 保证

无完备、无最优。窗口短则快、短视（可能把车引进死胡同）；窗口长则接近一次性规划、更慢。目标中途改变时不必作废整条路。

执行层：未锁的段不能走。评测看 `max_issue ≤ window`。

---

## 3. 不变量

- 每轮 `pos` 是模拟器里的当前格。
- 下发段长度 ≤ w。
- 到齐：所有 `pos[a]==goals[a]` 则停。
- 每轮 WHCA 的占用表应是 **这一窗的车**，不要把上轮旧锁留着（本实现每轮新建 WHCA，表是新的）。

---

## 4. 伪代码（本仓库）

```
pos ← starts
重复 steps 次或全部到达:
    plan ← WHCA(pos, goals, window=w)
    对每车: 执行 plan 的第 1 步，更新 pos
    记录 issued 段
```

---

## 5. 手算

两车平行、目标 5 步、w=3。第 1 轮 WHCA 给出 3 步前缀，只执行第 1 步。第 2 轮从新位置再规划 3 步。约 5 轮到齐。`max_issue` 是某轮下发的最长段，教学实现 `seg[:window]` 再只走 1 步，issued 长度仍 ≤ w。
"""),
        PATH,
        md("""
## 6. 实现：滚动循环
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import whca


def rhcr_simple(graph, starts, goals, window=3, steps=20):
    pos = dict(starts)
    full_paths = {a: [starts[a]] for a in starts}
    issued_log = []
    for step in range(steps):
        if all(pos[a] == goals[a] for a in starts):
            break
        plan = whca(graph, pos, goals, window=window)
        issued = {}
        for a, path in plan["paths"].items():
            seg = path[:window]
            issued[a] = seg
            if len(seg) > 1:
                pos[a] = seg[1]
                full_paths[a].append(pos[a])
        issued_log.append(issued)
        print(f"t={step} pos={pos} issue_len={ {a: len(s) for a, s in issued.items()} }")
    found = all(full_paths[a][-1] == goals[a] for a in starts)
    max_issue = max((len(seg) for batch in issued_log for seg in batch.values()), default=0)
    return {"found": found, "paths": full_paths, "max_issue": max_issue, "window": window}


g, starts, goals = two_agent_tunnel()
r = rhcr_simple(g, starts, goals, window=3, steps=20)
print("到齐", r["found"], "max_issue", r["max_issue"], "应<=", r["window"])
print("轨迹 a", r["paths"]["a"])
print("轨迹 b", r["paths"]["b"])
"""),
        md("""
## 7. 逐行

| 行 | 作用 |
|----|------|
| `pos` | 模拟器当前格，当下一轮 WHCA 的起点 |
| `seg[1]` | 每轮只前进一步（h=1） |
| `max_issue` | eval：不得超过 window |
| 每轮新 WHCA | 占用表不跨窗残留 |

库 `rhcr` 同样结构。窗口规划可换成 CBS（论文常见），教学用 WHCA 更快。
"""),
        code("""
from lib.algos.prioritized import rhcr

lib_r = rhcr(g, starts, goals, window=3, steps=20)
print("库 到齐", lib_r["found"], "max_issue", lib_r["max_issue"])
print("轨迹 a", lib_r["paths"]["a"])
"""),
        md("""
## 常见 bug

1. 每轮 WHCA 的 table 不空：旧锁把当前车自己锁死。
2. 执行了窗口内全部点却不重规划，失去滚动意义。
3. 用「单次 WHCA 是否到终点」当 RHCR 成功标准。
4. window=1 且两车必须换位：一步窗口可能永远对顶，要加大 w 或换 PBS/CBS 当窗规划器。

## 条目小结

| 项目 | 内容 |
|------|------|
| 架构 | 规划窗 + 执行 1 步 + 重规划 |
| 保证 | 无 |
| 用途 | 终身 / 在线 / 目标会变 |
| 下一课 | 要 SOC 最优 → CBS 冲突树 |

## 练习

1. w=1 与 w=5 到齐轮数、短视程度如何变？
2. 执行 h=w（把窗内全走完再规划）和 h=1 各有什么风险？
3. 新任务在 t=3 出现，RHCR 要改哪一行？HCA 一次规划为什么麻烦？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), lib_r, "RHCR")
studio
"""),
    ]
