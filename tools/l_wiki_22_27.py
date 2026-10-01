"""Wiki-style lessons 22–27: assignment and sampling."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_22():
    return "22_hungarian", "22 匈牙利算法：最小权匹配指派", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**指派问题**（assignment problem）：n 个机器人、n 个任务，代价矩阵 \\(C\\)。\\(C_{ij}\\) 是第 i 个机器人去做第 j 个任务的代价。求一个一一对应 \\(\\pi\\)（置换 / 完美匹配），使总代价最小：

\\[
\\min_\\pi \\sum_{i=0}^{n-1} C_{i,\\pi(i)}.
\\]

- **输入**：有向图 \\(G=(V,E)\\)；名单 `robots`；起点字典 `starts[r]`；任务节点列表 `tasks`。通常 \\(|robots|=|tasks|=n\\)。矩形（车数 ≠ 任务数）时库会补成方阵。
- **输出**：`assign[r] = task`，以及匹配总代价。该代价是各对 **单车最短路之和**，不含多车互相等待。

路径规划里 \\(C_{ij}\\) **必须**是有向最短路 \\(\\mathrm{Dijkstra}(s_i, t_j)\\)，不是欧氏/曼哈顿。不可达填 \\(10^6\\)。

**贪心指派**：按名单顺序，每人领剩余任务里当前代价最小者。局部最优，**整体不必最优**。

**匈牙利算法**（Kuhn 1955 / Munkres 1957）：二分图最小权完美匹配的多项式算法。库 `linear_sum_assignment` 用顶标 \\(u,v\\) 做 Munkres（约 80 行）。本课 **不**把这 80 行当第一份作业：n=2 穷举两种置换 **就是** 最优。

---

## 2. 和谁相邻

| 方法 | 何时用 | 保证 |
|------|--------|------|
| 贪心 | 只要快，或必须按车序立刻定任务 | 无 |
| 匈牙利 / KM | 离线、任务已齐、要最优匹配代价 | 匹配代价最优 |
| 拍卖（23） | 任务一个个到达 | 在线；竞争比可任意差 |
| TPTS（24） | 终身 MAPF：任务流 + 走路 | 启发式 |
| CBS-TA（25） | 匹配之后还要无碰撞路径 | 联合 SOC，不是纯矩阵和 |

匈牙利 **不走路**，只决定谁去哪。几何近 ≠ 有向路近。匹配和也不含等待；SOC 可能让另一匹配更好（25 课）。

---

## 3. 不变量 / 定理

记 \\(\\mathcal{M}\\) 为全部完美匹配。**定理：** 匈牙利的 \\(\\pi^*\\) 满足 \\(\\sum_i C_{i,\\pi^*(i)} \\le \\sum_i C_{i,\\sigma(i)}\\) 对任意 \\(\\sigma\\in\\mathcal{M}\\)。贪心没有这条（第 6 节反例）。

**n=2 推论：** 完美匹配只有两种，穷举取小者 = 匈牙利。这是本课自己写的版本。

**对偶直觉（不必手写 Munkres）：** 顶标 \\(u_i,v_j\\) 保持 \\(C_{ij}-u_i-v_j\\ge 0\\)。约化为 0 的边组成相等子图；其上的完美匹配即最优（互补松弛）。库数组 `u,v` 就是这对变量。

**补方阵：** n 车 m 任务、\\(n\\ne m\\) 时令 \\(k=\\max(n,m)\\)，空位填 \\(+\\infty\\)（库用 `1e12`）。返回的 (row, col) 丢掉虚拟下标。

---

## 4. 完整伪代码（与下面 Python 一一对应）

```
function CostMatrix(G, robots, starts, tasks):
    for i, r in enumerate(robots):
        for j, t in enumerate(tasks):
            res ← Dijkstra(G, starts[r], t)
            C[i][j] ← res.cost if res.found else 1e6
    return C

function GreedyTwo(robots, tasks, C):
    remaining ← {0,1,...,n-1}
    assign ← {};  total ← 0
    for i, r in enumerate(robots):          # 按名单，不回头
        j* ← argmin_{j in remaining} C[i][j]
        assign[r] ← tasks[j*]
        total ← total + C[i][j*]
        remaining.remove(j*)
    return assign, total

function BruteTwo(robots, tasks, C):        # n=2：两种置换
    π0: assign r0-t0, r1-t1,  cost = C[0][0]+C[1][1]
    π1: assign r0-t1, r1-t0,  cost = C[0][1]+C[1][0]
    return 代价更小者（相等取 π0）
```

库：`linear_sum_assignment(C)` 补方阵 → Munkres → `(rows, cols)`。学生调用，不抄 80 行。

---

## 5. 复杂度

填矩阵 \\(n^2\\) 次 Dijkstra，通常比匹配更贵。贪心（矩阵已在）\\(O(n^2)\\)。n=2 穷举 2 次；一般 \\(n!\\)。KM 是 \\(O(n^3)\\)，n 是车数不是格子数。

---

## 6. 完整手算 / 小表

课程图 `assign_cross_map`：R0/R1 — J — G0/G1，边权 1 双向。每条 R→J→G 都是 2 步。

|  | G0 | G1 | 说明 |
|--|----|----|------|
| r0@R0 | 2 | 2 | Dijkstra |
| r1@R1 | 2 | 2 | 全相等 |
| 欧氏 r0 | 2.000 | 2.236 | 坐标 (0,1)→(2,1)/(2,0) |
| 欧氏 r1 | 2.236 | 2.000 | 几何近 ≠ 图上近 |

π0：r0–G0 + r1–G1 = 4；π1：r0–G1 + r1–G0 = 4。贪心先 r0 取下标更小的 G0，得到 π0，碰巧最优。

**贪心失败 2×2：** C=[[2,3],[4,10]]。先 R0 取 T0=2，R1 剩 T1=10，合计 **12**。另一置换 3+4=**7**。穷举选 7。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

先在真实地图上填 2×2，再实现 `greedy_two` 与 `brute_two`。n=2 的穷举 **就是** 最优匹配。
"""),
        code("""
from evals.scenarios import assign_pair
from lib.search import dijkstra

g, robots, starts, tasks = assign_pair()
print("robots", robots)
print("starts", starts, "tasks", tasks)

C = []
print("Dijkstra 2x2（有向最短路，不是欧氏）:")
for r in robots:
    row = []
    for t in tasks:
        res = dijkstra(g, starts[r], t, record=False)
        cij = res.cost if res.found else 1e6
        row.append(cij)
        print(f"  {r} {starts[r]} -> {t}  cost={cij}  path={res.path}")
    C.append(row)
print("C =", C)

def greedy_two(robots, tasks, C):
    remaining = list(range(len(tasks)))
    assign, total = {}, 0.0
    for i, r in enumerate(robots):
        best_j = min(remaining, key=lambda j: C[i][j])
        assign[r] = tasks[best_j]
        total += C[i][best_j]
        remaining.remove(best_j)
        print(f"greedy {r} 取 {assign[r]}  本步={C[i][best_j]}  累计={total}  剩余下标={remaining}")
    return assign, total

def brute_two(robots, tasks, C):
    # n=2 只有两种置换；这就是最优，不要在这里抄 80 行 Munkres
    cand = [
        ({robots[0]: tasks[0], robots[1]: tasks[1]}, C[0][0] + C[1][1]),
        ({robots[0]: tasks[1], robots[1]: tasks[0]}, C[0][1] + C[1][0]),
    ]
    for a, cost in cand:
        print("brute 匹配", a, "代价", cost)
    return min(cand, key=lambda x: x[1])

print("--- greedy_two ---")
print("结果", greedy_two(robots, tasks, C))
print("--- brute_two ---")
print("结果", brute_two(robots, tasks, C))
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `dijkstra(..., record=False)` | 只要 cost/path |
| `found else 1e6` | 不可达写大数，避免 inf 加法 |
| `remaining` 列下标 | 当前行在剩余列上 `min` |
| `brute_two` 两条 | π0 对角线、π1 反对角线；相等取 π0 |

下面用贪心失败的数字矩阵对照库。
"""),
        code("""
from lib.algos.assignment import linear_sum_assignment, hungarian_assign, greedy_assign, cost_matrix

C_bad = [
    [2.0, 3.0],
    [4.0, 10.0],
]
rb, tb = ["R0", "R1"], ["T0", "T1"]
print("C_bad 贪心", greedy_two(rb, tb, C_bad))
print("C_bad 穷举", brute_two(rb, tb, C_bad))
rows, cols = linear_sum_assignment(C_bad)
print("库 KM rows, cols", rows, cols)
print("库 KM 匹配", {rb[i]: tb[j] for i, j in zip(rows, cols)})
print("库 KM 代价", sum(C_bad[i][j] for i, j in zip(rows, cols)))

print("--- 对照真实地图上的库函数 ---")
print("greedy_assign", greedy_assign(g, robots, starts, tasks))
hung = hungarian_assign(g, robots, starts, tasks)
print("hungarian_assign", hung["assign"], "cost", hung["cost"])
print("Dijkstra 矩阵", hung["matrix"])
print("欧氏矩阵  ", hung["euclidean"])
print("used_topo", hung["used_topo"])
print("cost_matrix topo", cost_matrix(g, robots, starts, tasks, use_topo=True))
print("cost_matrix 启发", cost_matrix(g, robots, starts, tasks, use_topo=False))
"""),
        md("""
## 9. 常见 bug

1. **用欧氏 / 曼哈顿填 C。** 本图欧氏不是全 2；有向路网更会错。必须 Dijkstra。
2. **矩形不补方阵。** 2 车 3 任务直接跑方阵 KM 会越界或丢任务。库先 pad 再解。
3. **把匹配代价当成 SOC。** 匹配和 = 各走各的最短路。CBS 在 J 口等待后 SOC 可以是 5，不是 4（25 课）。
4. **不可达写成 inf 又拿去加。** `inf+3` 仍是 inf，排序也别扭。约定 `1e6`。
5. **贪心按任务循环而不是按车。** 与本课伪代码不一致，反例数字会对不上。

## 10. 对照库

`cost_matrix` / `greedy_assign` / `linear_sum_assignment` / `hungarian_assign` 都在 `lib/algos/assignment.py`。KM 补方阵并返回下标；`used_topo=True` 表示 C 来自 Dijkstra。eval `test_22`：匈牙利代价 ≤ 贪心。本图两者都是 4。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.map = g.to_studio()
studio.algo = "assignment"
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 问题 | 二分图最小权完美匹配 |
| \\(C_{ij}\\) | **有向** Dijkstra，不是欧氏 |
| 贪心 | 按车序领剩余最小；不必最优 |
| n=2 | 两种置换穷举 = 最优 |
| 匈牙利 | Kuhn 1955 / Munkres 1957，\\(O(n^3)\\) |
| 不保证 | 含等待的 SOC 最优（那是 CBS-TA） |

## 练习

1. 纸上跑 `C_bad=[[2,3],[4,10]]`：写出贪心步骤与两种置换。最优是哪一个？
2. 若 `C[0][1]` 不可达改成 `1e6`，穷举会选哪对？把 `1e6` 错写成 `0` 会怎样？
3. 证明：n=2 时比较两条对角线（两种置换）就是最小权完美匹配。n=3 要比较几条？
"""),
    ]


def lesson_23():
    return "23_auction", "23 拍卖指派：在线单物品", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**顺序单物品拍卖**（sequential single-item auction）是一种 **在线** 指派：任务按到达序列一个个出现。每来一个任务，所有 **空闲** 机器人报一次价，价 = 从自己当前位置（本课即起点）到该任务的有向最短路；**最低者中标**，变为忙碌，不再参与后面的出价。

- **输入**：图 G，`robots`，`starts`，到达序列 `arrivals`（任务节点流）。
- **输出**：`assign[winner] = task`，以及各次中标代价之和。

它 **不是** 匈牙利。匈牙利要一次看见全部任务；拍卖在任务到达的那一刻就必须把该任务派出去，不能反悔。到达顺序不同，匹配可以不同，总价也可以不同。

历史：多机器人任务分配（MRTA）里大量用拍卖作通信协议（Gerkey、Dias、Zlot 等）。注意名字冲突：**Bertsekas 拍卖算法** 是离线解指派问题的对偶迭代，和本课「任务一个个来、最低价拿走」不是同一件事。本仓库 `auction_assign` 是后者。

---

## 2. 和谁相邻

|  | 拍卖（本课） | 匈牙利 | 贪心（22） |
|--|--------------|--------|------------|
| 看见全部任务？ | 否，在线 | 是 | 是（按车序扫） |
| 决策键 | 到达顺序 | 全局矩阵 | 机器人名单顺序 |
| 最优匹配代价 | 否 | 是 | 否 |
| 通信图像 | 每任务一次招标 | 中心算一次 | 中心按车扫 |

和 TPTS（24）：拍卖只决定谁去哪，不走路、不对头交换。TPTS 把「领最近任务」嵌进终身 MAPF。  
和 CBS-TA（25）：拍卖不管碰撞。

---

## 3. 不变量 / 定理

每来一个任务 t：

- 只有 `free` 里的车出价（忙碌车不投标）。
- 中标者 \\(r^* = \\arg\\min_{r \\in \\mathrm{free}} \\mathrm{Dijkstra}(s_r, t)\\)（并列取名单更前）。
- 中标后 `free.remove(r*)`，该车再也不出价。

**没有**「最终匹配代价最优」不变量。只有逐步的局部规则。

**竞争比：** 相对离线最优（匈牙利）的比值。理论上可以 **任意坏**：存在 2×2 实例，在线先来「大家都便宜」的任务，把本该留给另一任务的车提前锁死，剩下的车面对巨大代价。第 6 节数字是 101 / 2.2。没有与 n 无关的常数竞争比。

实践中任务代价比较均匀时，拍卖常常接近匈牙利，所以仍常用：不等齐、实现简单、可分布式。

---

## 4. 完整伪代码（与 `auction_simple` 对应）

```
function AuctionSimple(G, robots, starts, arrivals):
    free ← copy(robots)
    assign ← {};  total ← 0
    for task in arrivals:
        if free 空: break
        bids ← []
        for r in free:
            res ← Dijkstra(G, starts[r], task)
            bid ← res.cost if res.found else 1e6
            bids.append((bid, r))
            print 本轮出价
        sort bids 升序                 # 先比价，再比名字稳定性取决于元组
        cost, winner ← bids[0]
        assign[winner] ← task
        total ← total + cost
        free.remove(winner)
    return assign, total
```

出价必须 Dijkstra，与 22 课填 C 同一套。

---

## 5. 复杂度

k 个到达、最多 n 车。第 t 个任务有 \\(n-t+1\\) 人出价，每人一次 Dijkstra：共 \\(O(n^2)\\) 次最短路，与离线填整张矩阵同阶，但 **不能** 事后再换匹配。无堆可优化「谁该中标」——人少，扫一遍即可。

---

## 6. 完整手算 / 小表

**地图上的到达顺序。** 仍用 `assign_pair`，Dijkstra 全是 2。

| 到达 | 空闲 | 出价 | 中标 | 累计 |
|------|------|------|------|------|
| G0 | r0,r1 | r0:2, r1:2 | r0（名单更前） | 2 |
| G1 | r1 | r1:2 | r1 | 4 |
| **逆序 G1** | r0,r1 | 都是 2 | r0 得 G1 | 2 |
| 然后 G0 | r1 | r1:2 | r1 得 G0 | 4 |

总价相同，**匹配对调**。在线顺序改的是谁去哪，本图碰巧钱一样。

**竞争比任意坏的 2×2**（纯数字，下面会跑）：

|  | T0 | T1 |
|--|----|----|
| r0 | 1.0 | 1.1 |
| r1 | 1.1 | 100 |

- 离线匈牙利：r0–T1（1.1）+ r1–T0（1.1）= **2.2**（另一对 1+100=101）。
- 先到 T0：r0 出 1 赢走 T0，r1 被迫接 T1=100，在线合计 **101**。
- 先到 T1：r0 出 1.1 赢走 T1，r1 接 T0=1.1，合计 **2.2**。

同一矩阵，只换到达顺序，从最优变成 40 多倍。这就是「竞争比无常数上界」的最小例子。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

先实现 `auction_simple`：每个到达打印全体出价。再在真实地图上跑 `arrivals=tasks` 与逆序，对照匈牙利离线代价。最后用数字矩阵看竞争比。
"""),
        code("""
from evals.scenarios import assign_pair
from lib.search import dijkstra

g, robots, starts, tasks = assign_pair()


def auction_simple(graph, robots, starts, arrivals):
    free = list(robots)
    assign = {}
    total = 0.0
    for task in arrivals:
        if not free:
            print("无空闲车，丢弃", task)
            break
        bids = []
        for r in free:
            res = dijkstra(graph, starts[r], task, record=False)
            bid = res.cost if res.found else 1e6
            bids.append((bid, r))
            print(f"  到达 {task}: {r} 出价 {bid}")
        bids.sort()
        cost, winner = bids[0]
        assign[winner] = task
        total += cost
        free.remove(winner)
        print(f"  中标 {winner}  cost={cost}  累计={total}  仍空闲 {free}")
    return assign, total


print("=== arrivals = tasks", tasks, "===")
print("结果", auction_simple(g, robots, starts, tasks))
print("=== arrivals 逆序", list(reversed(tasks)), "===")
print("结果", auction_simple(g, robots, starts, list(reversed(tasks))))
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `free = list(robots)` | 复制。中标后从副本删，不动原名单 |
| `if not free: break` | 任务多于车时丢掉后续到达 |
| 只对 `free` 跑 Dijkstra | 忙碌车禁止出价（常见 bug 之一） |
| `bid = cost if found else 1e6` | 与 22 课不可达约定一致 |
| `bids.sort()` | 元组 (bid, name) 先比价；价同比名字 |
| `free.remove(winner)` | 中标即锁死，后面的任务看不见它 |

数字矩阵版：把 Dijkstra 换成查表，专门看顺序效应。
"""),
        code("""
from lib.algos.assignment import auction_assign, hungarian_assign


def auction_on_matrix(robots, tasks, C, arrivals):
    # arrivals 是任务名序列；C[i][j] 已是 r_i 对 t_j 的价
    idx = {t: j for j, t in enumerate(tasks)}
    free = list(range(len(robots)))
    assign = {}
    total = 0.0
    for task in arrivals:
        j = idx[task]
        bids = [(C[i][j], i) for i in free]
        print(f"到达 {task} 出价", [(robots[i], c) for c, i in bids])
        bids.sort()
        cost, i = bids[0]
        assign[robots[i]] = task
        total += cost
        free.remove(i)
        print(f"  中标 {robots[i]} 累计 {total}")
    return assign, total


C_online = [
    [1.0, 1.1],
    [1.1, 100.0],
]
rb, tb = ["r0", "r1"], ["T0", "T1"]
print("先 T0 再 T1（坏顺序）", auction_on_matrix(rb, tb, C_online, ["T0", "T1"]))
print("先 T1 再 T0（好顺序）", auction_on_matrix(rb, tb, C_online, ["T1", "T0"]))
print("匈牙利离线应取 1.1+1.1=2.2")

print("--- 库：地图顺序 vs 逆序 vs 匈牙利 ---")
print("auction tasks", auction_assign(g, robots, starts, tasks, arrivals=tasks))
print("auction rev  ", auction_assign(g, robots, starts, tasks, arrivals=list(reversed(tasks))))
print("hungarian    ", hungarian_assign(g, robots, starts, tasks)["cost"])
"""),
        md("""
## 9. 常见 bug

1. **忙碌车继续出价。** 一人两标，后面的任务抢不到车，或一人被派两个目标。
2. **出价用欧氏距离。** 与 22 课同一类错：单行道上「直线近」的车其实绕远。
3. **把拍卖总价拿去和匈牙利比，发现更大就以为实现写错。** 在线本来就可以更差；先检查是否真的只让空闲车出价。
4. **到达里有重复任务、不从 free 删除。** 同一车中两次。
5. **和 Bertsekas 拍卖对拍。** 那是离线对偶，会收敛到最优匹配；本课算法不会。

## 10. 对照库

`lib/algos/assignment.py` 的 `auction_assign(..., arrivals=)` 即上面的循环。默认 `arrivals is None` 时用 `tasks` 原顺序。eval `test_23` 只要求指派成功、总价不低于匈牙利太多（松弛记录）。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.map = g.to_studio()
studio.algo = "assignment"
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 模型 | 任务流上的单物品最低价拍卖 |
| 出价 | 空闲车的有向 Dijkstra |
| 与匈牙利 | 离线最优；在线顺序可改匹配与总价 |
| 竞争比 | 可任意坏（本课 101 vs 2.2） |
| 不是 | Bertsekas 离线拍卖 |

## 练习

1. 用 `C_online` 再手算两种到达顺序的出价表，核对 101 与 2.2。
2. 若错误地让已中标的车继续出价，先到 T0 再 T1 会变成什么匹配？
3. 改一格数字，使「坏顺序 / 匈牙利」比值超过 100。哪一格最敏感？
"""),
    ]


def lesson_24():
    return "24_tpts", "24 TPTS：令牌传递与任务交换", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**Token Passing with Task Swaps**（TPTS，Ma 等，终身 MAPF / 在线取送，AAMAS 2017 一带）：任务以流的形式到达，不是一次 n 对 n。系统里有一张 **令牌** = 规划权。

规则：

1. **空闲** 机器人拿到令牌后，在剩余任务里领 **对自己当前位姿最近** 的一个（最近 = 有向 A\\* / Dijkstra 代价），变为执行中。
2. 所有「手上有任务」的车一起做 **HCA\\***（优先规划，11 课）：按顺序时间 A\\*，前人路径写入占用表。
3. 若 HCA 失败且 `allow_swap` 且恰好两车对头： **交换两人的任务** 再 HCA 一次。走廊两端互换目标时，交换后每人已经站在新目标上，冲突消失。

- **输入**：图 G；`robots`；当前位姿 `starts`；任务流 `task_stream = [(name, goal), ...]`；开关 `allow_swap`。
- **输出**：是否全部完成、完成顺序、发生过几次对头/交换。

它面向 **终身** 场景：做完一个再领下一个，位姿要随着路径更新。一次性匈牙利管不了「做完之后人在哪」。

---

## 2. 和谁相邻

|  | TPTS | 匈牙利 / 拍卖 | HCA\\* / WHCA | CBS-TA |
|--|------|----------------|---------------|--------|
| 任务模型 | 流、可终身 | 一批静态 | 目标已给定 | 一批静态 + 最优路径 |
| 走路 | 有，HCA | 无 | 有 | CBS |
| 对头 | 可选 swap | 无 | 失败或绕路等待 | 约束树 |
| 最优 | 否 | 匹配层 / 在线 | 否 | 联合 SOC |

令牌传递（不带 swap 的 TP）已经能跑大型仓库启发式；swap 专门打「两车在窄廊对穿」这种 HCA 死结。

---

## 3. 不变量 / 定理

- 只有 `idle` 里的车能领任务；执行中的车不重新招标（和拍卖的 free 类似，但领的是 **对自己最近**，不是「刚到达的那一个」）。
- 领完后 `remaining` 去掉该任务名，避免两人领同一单。
- HCA 以 **当前** `pos[r]` 为起点，不是出生点。走完一截必须 `pos[r] = path[-1]`。
- 到达 `pos[r] == assign[r][1]` 则任务完成，车回到 idle。
- swap 交换的是 `assign` 里的 (name, goal) 对，不是物理传送。下一轮 HCA 仍从当前 pos 出发。

**没有完备、没有最优。** 对头且 `allow_swap=False` 时本实现直接停。若到达条件没把 `assign` 置空，while 会转无限圈——这是第 9 节的 bug。

走廊定理（教学）：A—C1—C2—C3—B 是一条宽 1 的无向廊。r0 在 A 要去 B，r1 在 B 要去 A，HCA 无论谁优先都会在廊里堵死（后车被前车占用表挡住且无法侧让）。交换目标后，r0 的目标变成 A（已在）、r1 的目标变成 B（已在），HCA 返回原地路径，SOC=0。

---

## 4. 完整伪代码（与实现对应）

```
function SwapIfHeadon(G, pos, assign):
    active ← {r: assign[r].goal for r in assign if assign[r]}
    plan ← HCA(G, pos_of_active, active)
    print before
    if plan.found:
        return plan, assign
    if not allow_swap or |active| != 2:
        return FAILURE
    a, b ← 两车
    assign[a], assign[b] ← assign[b], assign[a]
    active ← 交换后的目标
    plan ← HCA(G, pos, active)
    print after
    return plan, assign

function TPTS(G, robots, starts, stream, allow_swap):
    idle ← copy(robots);  pos ← copy(starts)
    remaining ← copy(stream);  assign[r] ← None
    while remaining 非空 or 有人在执行:
        for r in idle:
            领 remaining 里对 pos[r] 最近的任务
            idle.remove(r)
        plan ← HCA；失败则按上面 swap 一次
        沿 plan.paths 更新 pos；到达则 assign=None、回 idle
```

本课 **自己写** 的是中间那块：已经有两个目标、HCA 失败、交换再试。完整终身循环看库 `tpts`。

---

## 5. 复杂度

每领一次任务：对每个剩余任务一次 A\\*，\\(O(|T_{\\mathrm{left}}|\\cdot T_{A^*})\\)。每次规划一次 HCA（各车一次时间 A\\*）。swap 最多再加一次 HCA。终身则与任务流长度成正比。无指数搜索，也无最优证明。

---

## 6. 完整手算 / 小表

走廊 `corridor_headon`：

```
A -- C1 -- C2 -- C3 -- B
```

边权 1、双向。r0 在 A，r1 在 B。

**强制对穿（本课手写 swap 的输入）：** 目标 r0→B、r1→A。

| 步骤 | 内容 |
|------|------|
| HCA 先 r0 | r0 路径 A,C1,C2,C3,B，占用整廊 |
| 再 r1 | r1 从 B 出发，前方全被占，时间 A\\* 失败 |
| found | False，paths 往往只有先规划的那辆 |
| 交换 | r0 目标改 A，r1 目标改 B |
| 再 HCA | r0 已在 A → `['A']`；r1 已在 B → `['B']`；SOC=0 |

**库 TPTS 领最近：** 流 `[("t0","B"),("t1","A")]`。

| 车 | 当前位置 | 剩余任务代价 | 领取 |
|----|----------|--------------|------|
| r0 | A | t0@B=4，t1@A=0 | **t1**（已经站在目标） |
| r1 | B | 只剩 t0@B=0 | **t0** |

两人各领了自己脚下的任务，HCA 不需要对穿，`headon=0`，`allow_swap` 真假都 `found=True`。教学含义：最近任务启发式 **有时已经避免对头**；swap 留给「两人最近的都是对面」那种流。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

给定两个目标与一次失败的 HCA，交换再试。打印交换前后的目标、found、路径。
"""),
        code("""
from lib.maps import corridor_headon
from lib.algos.prioritized import hca

g = corridor_headon()
robots = ["r0", "r1"]
pos = {"r0": "A", "r1": "B"}
assign = {"r0": ("t0", "B"), "r1": ("t1", "A")}
print("走廊节点", sorted(g.nodes))
print("交换前 assign", assign)


def goals_of(assign):
    return {r: assign[r][1] for r in assign}


def swap_retry(graph, pos, assign):
    goals = goals_of(assign)
    plan = hca(graph, pos, goals)
    print("HCA 前 found=", plan["found"], "paths=", plan.get("paths"), "soc=", plan.get("soc"))
    if plan["found"]:
        return plan, assign
    rs = list(assign)
    print("HCA 失败，交换", rs[0], "<->", rs[1])
    assign = dict(assign)
    assign[rs[0]], assign[rs[1]] = assign[rs[1]], assign[rs[0]]
    print("交换后 assign", assign)
    plan2 = hca(graph, pos, goals_of(assign))
    print("HCA 后 found=", plan2["found"], "paths=", plan2.get("paths"), "soc=", plan2.get("soc"))
    return plan2, assign


plan, assign2 = swap_retry(g, pos, assign)
print("最终目标", goals_of(assign2), "成功", plan["found"])
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `assign[r] = (name, goal)` | 名字用于完成列表，goal 给 HCA |
| `hca(graph, pos, goals)` | 起点必须是 **当前 pos**，不是出生点 |
| `if plan["found"]: return` | 能走就不换，避免无故打乱任务 |
| `rs = list(assign)` | 恰好两车才对头交换（与库 `len(active)==2` 一致） |
| 元组对调 | 换任务不换人、不瞬移 |
| 第二次 HCA | 仍从原 pos 出发；本例每人已在新目标上 |

库的终身循环还要：领最近、沿路径写 pos、到达后 `assign[r]=None` 回 idle。
"""),
        code("""
from lib.algos.assignment import tpts

stream = [("t0", "B"), ("t1", "A")]
starts = {"r0": "A", "r1": "B"}
print("tpts allow_swap=True ", tpts(g, robots, starts, stream, True))
print("tpts allow_swap=False", tpts(g, robots, starts, stream, False))
print("注意：领最近后两人已在目标上，headon 常为 0；对穿例子看上一格 swap_retry")
"""),
        md("""
## 9. 常见 bug

1. **交换后仍用旧起点。** HCA 的 starts 必须是更新后的 `pos`。本例碰巧 pos 没变；走了几步再 swap 就会错。
2. **交换后不改 `assign` 只改局部 `goals`。** 下一轮又用旧任务，无限对头。
3. **到达不清空 assign。** `while remaining or any(assign)` 永远真，死循环。库在 `pos==goal` 时 `assign[r]=None; idle.append(r)`。
4. **swap 不限制两车。** 三人乱换没有对头语义。
5. **令牌发给忙碌车。** 一人两单，HCA 目标字典冲突。

## 10. 对照库

`tpts` 在 `lib/algos/assignment.py`：idle 领最近 → HCA → 失败且 `allow_swap` 则交换一次 → 用路径末点更新 pos。eval `test_24` 要求至少一种开关能完成，且 swap 的 headon 不比不换更糟。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.show_multi(g.to_studio(), plan, "TPTS-swap")
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 场景 | 终身 / 任务流 MAPF |
| 令牌 | 空闲车的规划权；领对自己最近的剩余任务 |
| 行走 | 当前有任务的车跑 HCA |
| swap | 两车对头失败则换目标再试 |
| 走廊 | 对穿 → 交换 → 各留在原地 |

## 练习

1. 把强制对穿的目标写成 r0→B、r1→A，不交换时 HCA 的 `found` 是什么？交换后路径应是什么？
2. 若 `allow_swap=False` 且 HCA 失败，库选择 `break`。改成「原地等待一拍再试」会怎样？可能活，也可能永远等。
3. 为什么领最近有时让本课这条流根本不触发 swap？换一条流使两人最近的都是对面。
"""),
    ]


def lesson_25():
    return "25_cbs_ta", "25 CBS-TA：联合目标分配与路径", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**CBS-TA**（Conflict-Based Search with Task Assignment，Hönig 等）：同时选择指派 \\(\\pi\\) 和一组 **无碰撞** 路径，优化 SOC（各车到达时间之和），不是只优化矩阵和。

- **输入**：图 G，`robots`，`starts`，`tasks`（与 22 课相同的一批静态任务）。
- **输出**：匹配 `assign`，无碰撞 `paths`，以及两套数字：`assign_cost`（矩阵和）与 `soc`（含等待）。

完整算法在 **指派树** 上枚举匹配（下一最优匹配 / Murty 一类），每个匹配当作 CBS 的一组目标；高层仍按 SOC 最佳优先。本仓库教学实现更小：先匈牙利得 \\(\\pi_H\\)，跑一遍 CBS；再贪心得 \\(\\pi_G\\)，再跑一遍 CBS；报告两者 SOC。n=2 时这两种已经覆盖全部完美匹配。

**关键句：** 「先匈牙利再 CBS」给出的是 **该 \\(\\pi\\) 下** 的 SOC 最优路径，不是所有 \\(\\pi\\) 里 SOC 最小的那个。等待可以让矩阵更优的匹配在时空里更差。

---

## 2. 和谁相邻

|  | 匈牙利 | 匈牙利+CBS | CBS-TA | 贪心+CBS |
|--|--------|------------|--------|----------|
| 决策 | 只匹配 | 匹配固定再消撞 | 匹配与路径一起搜 | 匹配次优再消撞 |
| 目标函数 | \\(\\sum C_{ij}\\) | 该 π 的 SOC | 全局 SOC | 该 π 的 SOC |
| 碰撞 | 不管 | 管 | 管 | 管 |

和 22：矩阵最优 ≠ 时空最优。  
和 15 课 CBS：CBS 的目标是给定的；本课目标本身是搜索变量。  
和 TPTS：TPTS 在线启发式；CBS-TA 离线、小 n、求质量。

---

## 3. 不变量 / 定理

两套代价，不要混：

| 符号 | 定义 | 含等待？ |
|------|------|----------|
| 矩阵和 `assign_cost` | \\(\\sum_i \\mathrm{Dijkstra}(s_i, \\pi(i))\\) | 否 |
| SOC | \\(\\sum_i T_i^{\\mathrm{arr}}\\)（路径时间戳，含 wait） | 是 |

**引理（固定 π）：** CBS 在该目标下返回的 SOC 最优（经典离散 MAPF、stay-at-target 约定与 15 课相同）。

**不是引理：** 矩阵最优的 \\(\\pi_H\\) 的 SOC ≤ 其他 \\(\\pi\\) 的 SOC。反例结构：

|  | T0 | T1 |
|--|----|----|
| r0 | 1 | 5 |
| r1 | 5 | 2 |

匈牙利取 r0–T0、r1–T1，矩阵和 3。若这两条最短路在同一格对撞，CBS 让一车等待 10 拍，SOC=13。另一匹配矩阵和 10，但各走各的互不挡，SOC=10，**SOC 更好**。本课地图更温和：两种匹配矩阵和都是 4，CBS 后 SOC 都是 5（都要抢 J）。

**单射：** \\(\\pi\\) 必须一人一任务。两车同一目标 ⇒ stay-at-target 下终点永远顶点冲突，CBS 会把 cap 用完。

---

## 4. 完整伪代码（与下面 Python 对应）

```
function CompareAssignThenCBS(G, robots, starts, tasks):
    πH, cH ← Hungarian(G, ...)          # 矩阵最优
    πG, cG ← Greedy(G, ...)
    rH ← CBS(G, starts, πH)             # 该 π 的无碰撞路径
    rG ← CBS(G, starts, πG)
    print 矩阵和 cH, cG
    print SOC rH.soc, rG.soc
    print 路径（看哪一拍在等待）
    return rH, rG

function CBS_TA_lib(...):               # 本仓库
    hung ← Hungarian
    planned ← CBS(starts, hung.assign)
    planned.assign_cost ← hung.cost
    planned.greedy_soc ← CBS(greedy.assign).soc
    return planned
```

完整文献 CBS-TA 还要：从匈牙利开始生成下一最优匹配，CBS 高层节点带「当前 π」，直到 SOC 下界证明没有更好 π。n=2 穷举两种匹配已经穷尽。

---

## 5. 复杂度

匹配个数最多 n!。每个匹配一次 CBS，CBS 最坏对冲突数指数。教学 n=2：2 次 CBS。填矩阵仍是 \\(n^2\\) 次 Dijkstra。所以「先匹配再 CBS」的代价几乎全在 CBS，不在匈牙利。

---

## 6. 完整手算 / 小表

`assign_cross_map`，r0@R0、r1@R1，任务 G0/G1。矩阵全 2，两种匹配矩阵和都是 4。

两人去右侧都必须经过 J。一种无碰撞时间表（库 CBS 实际输出）：

| t | r0 | r1 |
|---|----|----|
| 0 | R0 | R1 |
| 1 | R0（等） | J |
| 2 | J | G1 |
| 3 | G0 | G1 |

SOC = 3+2 = 5。矩阵和 4，多出来的 1 就是 r0 在 R0 的等待。交叉匹配 r0–G1、r1–G0 同样抢 J，SOC 仍是 5。

**数字反例（概念，不必在本图上出现）：** 矩阵最优 3 但等待 +10 ⇒ SOC 13；另一匹配 10、无等待 ⇒ SOC 10。比较算法时必须说清比的是哪一列。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

自己算两种指派，各跑一遍库 CBS，打印矩阵和与 SOC。不要把两列数字比来比去当 bug。
"""),
        code("""
from evals.scenarios import assign_pair
from lib.algos.assignment import greedy_assign, hungarian_assign, cbs_ta
from lib.algos.cbs import cbs

g, robots, starts, tasks = assign_pair()

hung = hungarian_assign(g, robots, starts, tasks)
greed = greedy_assign(g, robots, starts, tasks)
print("匈牙利 π", hung["assign"], "矩阵和", hung["cost"])
print("贪心   π", greed["assign"], "矩阵和", greed["cost"])

r_h = cbs(g, starts, hung["assign"])
r_g = cbs(g, starts, greed["assign"])
print("匈牙利+CBS  found", r_h["found"], "SOC", r_h["soc"], "paths", r_h["paths"])
print("贪心+CBS    found", r_g["found"], "SOC", r_g["soc"], "paths", r_g["paths"])
print("差值：矩阵和 4、SOC 5 ⇒ 有一拍等待（看路径里重复的点）")
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `hungarian_assign` / `greedy_assign` | 只产出 π 与矩阵和，不消撞 |
| `cbs(g, starts, π)` | 目标字典必须是车→节点，且单射 |
| `r["soc"]` | 含等待；与 `hung["cost"]` 单位都是边权时间，但不是同一个量 |
| 打印 `paths` | 连续两个相同节点 = 等待 |
| 两种 π 都跑 | n=2 即穷尽完美匹配；本图 SOC 相同 |

同目标实验：两车都去 G0 时 CBS 往往失败或用尽 cap。
"""),
        code("""
bad = cbs(g, starts, {"r0": "G0", "r1": "G0"})
print("两车同一目标 found", bad["found"], "SOC", bad.get("soc"), "high", bad.get("high"))

r = cbs_ta(g, robots, starts, tasks)
print("库 cbs_ta 指派", r["assign"], "SOC", r["soc"], "矩阵和", r["assign_cost"], "贪心CBS", r["greedy_soc"])
"""),
        md("""
## 9. 常见 bug

1. **拿矩阵和跟 SOC 比大小当对错。** 4 对 5 在本图是等待，不是实现错。
2. **两车同一目标丢给 CBS。** 终点占用冲突，搜索爆炸或失败。指派必须单射。
3. **以为匈牙利+CBS 就是 CBS-TA。** 它只对 **一个** π 最优。完整 CBS-TA 还要换 π。
4. **CBS 的 starts 写成任务点。** 人还在码头。
5. **比较时一个用欧氏矩阵、一个用 Dijkstra 矩阵。** 先统一 C。

## 10. 对照库

`cbs_ta` 先 `hungarian_assign` 再 `cbs`，并附 `greedy_soc`。eval `test_25`：`soc <= greedy_soc`。完整指派树（下一最优匹配）不在本课作业里。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "CBS-TA")
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 问题 | 联合选 π 与无碰撞路径，目标 SOC |
| 匈牙利+CBS | 该 π 的路径最优，不必全局 SOC 最优 |
| 两套代价 | 矩阵和（无等待）vs SOC（有等待） |
| 本图 | 矩阵 4，SOC 5，两种 π 相同 |
| n=2 | 两种匹配穷尽 |

## 练习

1. 在打印出的 paths 里标出等待的 (车, 时刻, 节点)。等待发生在 J 还是起点？
2. 用第 3 节那张 1/5/5/2 的表，说明为什么「矩阵最优」可以 SOC 更差。
3. 若强制两车都去 G0，CBS 的 `found` 是什么？指派层应如何拒绝？
"""),
    ]


def lesson_26():
    return "26_rrt", "26 RRT：随机树探索连续空间", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**RRT**（Rapidly-exploring Random Tree，LaValle 1998）在 **连续** 状态空间里长一棵树，用随机采样把树拉进未探索区域。本课状态就是平面点 \\((x,y)\\in[0,1]^2\\)，障碍是圆。没有格子、没有现成邻居列表。

- **输入**：场景 `{width,height,obstacles,start,goal}`；迭代上限 n；步长 \\(\\varepsilon\\)；目标偏置 `goal_bias`；随机种子。
- **输出：** `found`，折线 `path`，代价（折线欧氏长），树的 `nodes` 与 `parent`。

一轮迭代：

1. **Sample：** 以概率 `goal_bias` 取 goal，否则在矩形里均匀随机。
2. **Nearest：** 树上离样本最近的节点 \\(x_{\\mathrm{near}}\\)（教学用暴力扫）。
3. **Steer：** 从 \\(x_{\\mathrm{near}}\\) 向样本走至多 \\(\\varepsilon\\) 得到 \\(x_{\\mathrm{new}}\\)。
4. **Collision：** 检查 **线段** \\(x_{\\mathrm{near}}x_{\\mathrm{new}}\\) 是否穿障，不是只查两个端点。
5. 无碰则把 \\(x_{\\mathrm{new}}\\) 入树。若它离 goal 不到 \\(\\varepsilon\\) 且连 goal 的线段也自由，把 goal 挂上，成功。

---

## 2. 和谁相邻

|  | RRT | Dijkstra / A\\* | PRM | RRT\\*（27） |
|--|-----|-----------------|-----|--------------|
| 空间 | 连续 | 已离散的图 | 连续，先建路网再搜 | 连续 |
| 邻居 | steer 造出来 | 图的出边 | 半径内连边 | steer + Near |
| 最优 | 否 | 是（非负权） | 取决于路网 | 渐近最优 |
| 完备 | 概率完备 | 图连通则完备 | 概率完备 | 概率完备 |

**已经是路网 / 格子就不要用 RRT**，那是 Dijkstra 的活。RRT 用在没有 \\(V,E\\) 的连续障碍空间。Voronoi 偏向让树伸进开阔地，而不是像 BFS 一圈圈胀。

---

## 3. 不变量 / 定理

- 树上每条边都是曾经通过线段碰撞检查的 steer 段。因此整条根到叶的折线（在「线段检测不漏」的前提下）不碰圆。
- **概率完备：** 障碍之间的缝有正宽度、\\(\\varepsilon\\) 足够小、n→∞ 时成功概率 → 1。不是有限 n 的保证。
- **不必最优。** 先碰到 goal 的那条折线往往锯齿、绕远。换 seed 路径形状会变。
- 检测不变量：若只查端点，存在整段穿过圆、两端在圆外的假阴性（第 6 节）。

线段检测：段上 21 点（`i=0..20`，\\(t=i/20\\)），任一点进圆则撞。圆相对步长不太小时够用。

---

## 4. 完整伪代码（与 `mini_rrt` 对应）

```
function PointInCircle(p, ox, oy, r):
    return hypot(p-center) <= r

function SegCollides(a, b, steps=20):
    for i in 0..steps:
        p ← (1-t)*a + t*b,  t=i/steps
        if PointInCircle(p): return True
    return False

function Steer(a, b, ε):
    d ← hypot(b-a)
    if d <= ε: return b
    return a + ε * (b-a)/d

function MiniRRT(start, goal, n, ε, seed):
    rng ← Random(seed)
    nodes ← [start];  parent ← [None]
    for k in 1..n:
        sample ← goal if rng.random() < goal_bias else Uniform([0,1]^2)
        i ← argmin_j ||nodes[j]-sample||
        x_new ← Steer(nodes[i], sample, ε)
        if x_new 出界 or SegCollides(nodes[i], x_new): continue
        parent.append(i); nodes.append(x_new)
        if hypot(x_new, goal) < ε and not SegCollides(x_new, goal):
            parent.append(len(nodes)-1); nodes.append(goal)
            return SUCCESS, Reconstruct, Length
    return FAILURE
```

---

## 5. 复杂度

暴力最近邻合计 \\(O(n^2)\\)，每次碰撞 \\(O(\\mathrm{steps}\\cdot|\\mathrm{obs}|)\\)。KD 树可到约 \\(O(n\\log n)\\)。\\(\\varepsilon\\) 太大穿不过细缝，太小则 n=400 爬不到 goal。

---

## 6. 完整手算 / 小表

单位方、一圆心 (0.5,0.5) 半径 0.2。起点 (0.1,0.1)，终点 (0.9,0.9)。直线穿过圆，所以成功路径必须绕上或绕下。

**只查端点会漏的线段：** a=(0.2,0.5)，b=(0.8,0.5)。

| 检查 | 结果 |
|------|------|
| a 在圆内？ | hypot 到圆心=0.3 > 0.2，否 |
| b 在圆内？ | 同样 0.3 > 0.2，否 |
| 中点 (0.5,0.5) | 圆心，**在圆内** |
| 20 点采样 | 必能抓到中点附近 |

所以碰撞函数必须采样线段。下面代码先打印这张表，再跑 n=400、ε=0.08、seed=0 的整棵树。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

从碰撞、steer、最近邻写到主循环。打印是否找到、代价、节点数；前几个新节点也打印。
"""),
        code("""
import math
import random

START, GOAL = (0.1, 0.1), (0.9, 0.9)
OX, OY, ORAD = 0.5, 0.5, 0.2
STEP, N, GOAL_BIAS = 0.08, 400, 0.08

def point_in_circle(p):
    return math.hypot(p[0] - OX, p[1] - OY) <= ORAD

def seg_collides(a, b, steps=20):
    # 含端点 i=0 与 i=steps
    for i in range(steps + 1):
        t = i / steps
        p = (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
        if point_in_circle(p):
            return True
    return False

def steer(a, b, step):
    dx, dy = b[0] - a[0], b[1] - a[1]
    dist = math.hypot(dx, dy)
    if dist <= step:
        return b
    return (a[0] + step * dx / dist, a[1] + step * dy / dist)

def nearest_idx(nodes, p):
    best, bi = 1e9, 0
    for i, q in enumerate(nodes):
        d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        if d < best:
            best, bi = d, i
    return bi

a, b = (0.2, 0.5), (0.8, 0.5)
print("端点碰撞", point_in_circle(a), point_in_circle(b), "线段采样", seg_collides(a, b))

def reconstruct(parent, nodes, idx):
    chain = []
    while idx is not None:
        chain.append(nodes[idx])
        idx = parent[idx]
    chain.reverse()
    return chain

def path_cost(path):
    return sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(path, path[1:]))

def mini_rrt(n=N, step=STEP, seed=0, goal_bias=GOAL_BIAS, verbose=True):
    rng = random.Random(seed)
    nodes, parent = [START], [None]
    for k in range(n):
        sample = GOAL if rng.random() < goal_bias else (rng.random(), rng.random())
        i = nearest_idx(nodes, sample)
        nxt = steer(nodes[i], sample, step)
        if not (0.0 <= nxt[0] <= 1.0 and 0.0 <= nxt[1] <= 1.0):
            continue
        if seg_collides(nodes[i], nxt):
            continue
        parent.append(i)
        nodes.append(nxt)
        if verbose and len(nodes) <= 6:
            print(f"  add #{len(nodes)-1} {nxt}  parent={i}")
        if math.hypot(nxt[0] - GOAL[0], nxt[1] - GOAL[1]) < step and not seg_collides(nxt, GOAL):
            parent.append(len(nodes) - 1)
            nodes.append(GOAL)
            path = reconstruct(parent, nodes, len(nodes) - 1)
            return {"found": True, "path": path, "cost": path_cost(path), "nodes": nodes, "parent": parent}
    return {"found": False, "path": [], "cost": float("inf"), "nodes": nodes, "parent": parent}

r = mini_rrt()
print("found", r["found"], "cost", r["cost"], "nodes", len(r["nodes"]))
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `Random(seed)` | 可复现 |
| `goal_bias` | 否则很难采到终点邻域 |
| `nearest` 平方距离 | 比大小不必开方 |
| `steer` 截到 ε | 新边有上限 |
| `seg_collides` 21 点 | 只查端点会穿过圆 |
| 近 goal 再查最后一跳 | 那一段也要无碰 |

seed=0、n=400、ε=0.08 应找到；代价约 1.52（直线 \\(\\sqrt{2}\\approx 1.41\\)）。
"""),
        code("""
from lib.maps import continuous_scene
from lib.algos.rrt import rrt

coarse = mini_rrt(n=400, step=0.5, seed=0, verbose=False)
fine = mini_rrt(n=400, step=0.01, seed=0, verbose=False)
print("ε=0.5 过粗 found", coarse["found"], "nodes", len(coarse["nodes"]))
print("ε=0.01 过细 found", fine["found"], "nodes", len(fine["nodes"]))

scene = continuous_scene()
lib = rrt(scene, seed=1, n=1500)
print("库 rrt seed=1 n=1500 found", lib["found"], "cost", lib["cost"], "nodes", len(lib["nodes"]))
"""),
        md("""
## 9. 常见 bug

1. **只检查端点。** 水平穿过圆心的线段两端都自由，树会穿障。
2. **ε 太大。** 一步跳过窄缝，或新段太长很难绕圆；本课 0.5 往往树很稀。
3. **ε 太小。** n 不够，爬不到 (0.9,0.9)。
4. **没有 goal bias。** 均匀采样打中终点邻域的概率是面积阶，收敛慢。
5. **已离散路网还跑 RRT。** 浪费，且不最优；用 Dijkstra。

## 10. 对照库

`lib/algos/rrt.py`：`_collides` 多圆、`_seg_collides` 20 步、`_steer`、`_nearest` 暴力、`rrt(..., seed, n, step, goal_bias)`。`continuous_scene()` 是单位方、三圆、start [0.08,0.08]、goal [0.92,0.92]。eval `test_26` 固定 seed=1、n=1500 必须找到。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.show_rrt(scene, lib, "RRT")
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 空间 | 连续，邻居靠 steer 生成 |
| 保证 | 概率完备，**非**最优 |
| 碰撞 | 线段采样，不只端点 |
| 复杂度 | 暴力最近邻 \\(O(n^2)\\) |
| 下一课 | 选父 + rewire → RRT\\* |

## 练习

1. 证明 a=(0.2,0.5)、b=(0.8,0.5) 两端在 r=0.2 的圆外、中点在圆内。只查端点的 RRT 会怎样？
2. 把 ε 改成 0.5 和 0.01（n=400, seed=0），记录 found 与节点数。
3. 为何 `topo_oneway` 这种有向路网不该改写成 RRT？
"""),
    ]


def lesson_27():
    return "27_rrt_star", "27 RRT*：渐近最优采样", [
        md("""
本课按百科条目写：先定义……调度台在最后，可跳过。

---

## 1. 定义

**RRT\\***（Karaman & Frazzoli, IJRR 2011）在 RRT 接受 \\(x_{\\mathrm{new}}\\) 之后多两步：

1. **选父（choose parent）：** 在半径 r 的邻域 Near 里，选使 \\(g(x)+\\|x-x_{\\mathrm{new}}\\|\\) 最小、且连线无碰的节点当父亲。不再固定「几何最近」。
2. **重接（rewire）：** 对 Near 里每个邻居 x，若走 \\(x_{\\mathrm{new}}\\) 再走到 x 更便宜、且线段无碰，则把 x 的父指针改到 \\(x_{\\mathrm{new}}\\)，并更新 \\(g(x)\\)。

- **输入：** 与 RRT 相同，外加邻域半径 r（本课 **固定** r，便于手算）。
- **输出：** 同样的树 + 各点代价 g；成功时路径代价随样本变多 **几乎必然趋向最优**（渐近最优）。

理论半径随 n 缩小，约 \\(\\gamma(\\log n / n)^{1/d}\\)。教学用常数 r，例如库默认 0.14。

---

## 2. 和谁相邻

|  | RRT | RRT\\* | A\\* |
|--|-----|--------|------|
| 改已有边 | 否，边一旦加上就冻住 | 要 rewire | 图的边本来就在 |
| 最优 | 否 | 渐近（n→∞） | 有限图一次弹出即最优 |
| 邻域 | 只 nearest 一个 | 半径 r 内一批 | 图邻居 |
| 适用 | 先尽快找到一条 | 还想把路径拉直、拉短 | 已有离散图 |

RRT 先碰到 goal 就停（本库如此）。RRT\\* 通常继续采样，用更好的 g 刷新到 goal 的路径。本库 `rrt_star` 跑满 n 次，保留 `best_path`。

---

## 3. 不变量 / 定理

- 每个节点的 g 是 **当前树** 上根到该点的折线长。rewire 只在 `cand + 1e-9 < cost[j]` 且线段无碰时改父。
- **渐近最优：** 在合适的 r(n)、缝有正宽度等条件下，n→∞ 时解的代价以概率 1 趋向最优代价。有限 n 只保证「不差于同一前缀树的 RRT 行为」，不保证已经最优。
- **碰撞不变量：** 选父和 rewire **每一条候选边** 都要线段检测。省掉则树会穿障，g 再小也非法。
- 教学局限：本课与库只更新被 rewire 的那个邻居的 g，不沿其子树向下推。节点很少时影响小；严格实现应递减子树。

---

## 4. 完整伪代码（增量，接在 RRT 接受 x_new 之后）

```
# nodes, parent, cost 已有；x_new 尚未入树
Near ← { j | hypot(nodes[j], x_new) <= r }

p ← nearest 的下标
c ← cost[p] + dist(nodes[p], x_new)
for j in Near:
    cand ← cost[j] + dist(nodes[j], x_new)
    if cand < c and not SegCollides(nodes[j], x_new):
        c, p ← cand, j

nodes.append(x_new); parent.append(p); cost.append(c)
ni ← |nodes|-1

for j in Near:
    cand ← c + dist(x_new, nodes[j])
    if cand < cost[j] and not SegCollides(x_new, nodes[j]):
        parent[j] ← ni
        cost[j] ← cand
```

与下面 4 点例子逐行相同；例子里空场，碰撞恒假。

---

## 5. 复杂度

每点扫 Near。若 Near=全体节点，每次 \\(O(n)\\) 次距离+碰撞，总计 \\(O(n^2)\\)（再乘线段采样）。半径缩小后 Near 期望更小；再加 KD 树可接近 \\(O(n\\log n)\\)。**不要**在大 n 时把 Near 定义成全部节点还声称这是 RRT\\* 的标准复杂度。

---

## 6. 完整手算 / 小表

空场四点（插入前三个、再插入第四个）。半径 r=2.5。

| idx | 点 | parent | g |
|-----|----|--------|---|
| 0 | (0,0) 起点 | None | 0 |
| 1 | (4,0) | 0 | 4 |
| 2 | (2,1) | 1 | 4+√5 ≈ 6.236 |

插入 \\(x_{\\mathrm{new}}=(0,1)\\)：

| j | dist(j, new) | 在 Near？ | 经 j 到 new 的 cand |
|---|--------------|-----------|---------------------|
| 0 | 1 | 是 | 0+1=1 |
| 1 | √17≈4.123 | 否（>2.5） | — |
| 2 | 2 | 是 | 6.236+2=8.236 |

选父：j=0，g(new)=1。new 成为 idx=3。

Rewire：

| j | 旧 g | 经 new 的 cand | 动作 |
|---|------|----------------|------|
| 0 | 0 | 1+1=2 | 不改（更大） |
| 2 | 6.236 | 1+2=**3** | **parent[2]=3，g=3** |

点 2 原来绕道 (4,0)，现在经 (0,1) 更短。这就是 rewire 的全部几何。
"""),
        PATH,
        md("""
## 7. 分步实现（自己写，print traces）

把第 6 节的表写成代码：打印插入前后的 parent/cost。空场不碰撞；真实 RRT\\* 必须把 `seg_collides` 填回去。
"""),
        code("""
import math

nodes = [(0.0, 0.0), (4.0, 0.0), (2.0, 1.0)]
parent = [None, 0, 1]
cost = [0.0, 4.0, 4.0 + math.hypot(2.0, 1.0)]
radius = 2.5
x_new = (0.0, 1.0)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dump(title):
    print(title)
    for i, p in enumerate(nodes):
        print(f"  idx={i}  p={p}  parent={parent[i]}  g={cost[i]:.3f}")


dump("插入前")
nb = [j for j, q in enumerate(nodes) if dist(q, x_new) <= radius]
print("Near", nb, "半径", radius)

p = min(nb, key=lambda j: cost[j] + dist(nodes[j], x_new))
c = cost[p] + dist(nodes[p], x_new)
print(f"选父 p={p}  g_new={c:.3f}")

nodes.append(x_new)
parent.append(p)
cost.append(c)
ni = len(nodes) - 1

for j in nb:
    cand = c + dist(nodes[j], x_new)
    # 真 RRT* 这里还要 not seg_collides(x_new, nodes[j])
    if cand + 1e-9 < cost[j]:
        print(f"rewire {j}: parent {parent[j]} -> {ni}, g {cost[j]:.3f} -> {cand:.3f}")
        parent[j] = ni
        cost[j] = cand

dump("插入后")
print("点 2 的父应从 1 变成 3，g 从 6.236 变成 3")
"""),
        md("""
## 8. 逐行实现表

| 行 | 作用 |
|----|------|
| `nb = [j if dist<=r]` | Near；本例不含点 1 |
| 选父 `min(nb, key=g+dist)` | 不是几何 nearest（nearest 碰巧也是 0） |
| 先 append 再 rewire | `ni` 必须是 new 的下标 |
| `cand + 1e-9 < cost[j]` | 严格变好才改，避免数值抖动来回接 |
| 注释里的 `seg_collides` | 空场省略；有障省掉就会穿墙抄近路 |
| 不更新点 2 的孩子 | 本例点 2 无孩子；有孩子时应下推 g |

库在 `rrt_star` 里对每个新点做这两段，并在靠近 goal 时刷新 `best_path`。
"""),
        code("""
from lib.maps import continuous_scene
from lib.algos.rrt import rrt, rrt_star

scene = continuous_scene()
a = rrt(scene, seed=2, n=900)
b = rrt_star(scene, seed=2, n=1400)
print("RRT    found", a["found"], "cost", a["cost"], "nodes", len(a["nodes"]))
print("RRT*   found", b["found"], "cost", b["cost"], "nodes", len(b["nodes"]))
print("RRT* 代价应 <= RRT:", b["cost"] <= a["cost"] + 1e-6)
"""),
        md("""
## 9. 常见 bug

1. **rewire 不做线段碰撞。** g 变小的边可能穿过圆，路径非法。
2. **Near = 全部节点。** 正确但 \\(O(n^2)\\)；n 到万级会卡。半径 / KD 树是正道。
3. **选父仍只用几何最近。** 那就还是 RRT，没有渐近最优。
4. **rewire 改了 parent 却不改 cost。** 以后选父用过期 g，树会越改越乱。
5. **有限 n 就声称最优。** 只是渐近；同 seed 比较时应有 RRT\\* 代价 ≤ RRT（eval `test_27`）。

## 10. 对照库

`rrt_star` 默认 `n=1200, step=0.06, radius=0.14`，goal bias 0.1。选父与 rewire 都调用 `_seg_collides`。同 seed 下再加大 n，代价应非增。
"""),
        code("""
from lib.studio.widget import PlannerStudio

studio = PlannerStudio()
studio.show_rrt(scene, b, "RRT*")
studio
"""),
        md("""
## 条目小结

| 项目 | 内容 |
|------|------|
| 增量 | 选父（半径内最小 g+dist）+ rewire |
| 保证 | 渐近最优；有限 n 不保证已最优 |
| 半径 | 理论随 n 变；本课固定 |
| 碰撞 | 候选边每条都查线段 |
| 对照 | 同 seed，RRT\\* 代价 ≤ RRT |

## 练习

1. 不看代码，根据第 6 节表写出插入后四行 parent/g。点 2 的父是谁？
2. 若 Near 误设为全部节点，本例点 1 会不会被 rewire？cand 是多少？
3. 在圆心与 (0,1)–(2,1) 之间放一个圆，rewire 到点 2 的边可能撞。此时应保持 parent[2]=1。缺碰撞检查会怎样？
"""),
    ]
