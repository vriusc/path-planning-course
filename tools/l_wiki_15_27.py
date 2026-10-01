"""Wiki-style lessons 15–27."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_15():
    return "15_cbs", "15 CBS：冲突树最优 MAPF", [
        md("""
## 1. 定义

**Conflict-Based Search**（Sharon et al., AIJ 2015）：两层搜索。

- **高层**：冲突树 CT。每个节点 = 约束集合 + 一组单车路径。
- **底层**：对某个智能体，在约束下做时间 A\\* / SIPP（本仓库用时间 A\\*）。

根节点：各车独立最短路。若两路径在 (点,t) 或换边冲突，分裂：

- 左孩子：禁止 A 在该 (点,t)
- 右孩子：禁止 B 在该 (点,t)

高层按 SOC（各车到达时间和）做最佳优先。第一个无冲突叶即 **SOC 最优**（经典离散 MAPF）。

---

## 2. 和 HCA\\* / 联合 A\\*

HCA\\* 预先定全序，不必最优、不完全。  
联合 A\\* 搜联合状态，最优但爆。  
CBS 只在 **真发生的冲突** 上分支，底层仍是单车搜索。

---

## 3. 不变量

- CT 节点的约束只增不减。
- 底层路径满足该节点全部约束。
- 可采纳：SOC 下界 = 当前各车路径代价和（每车已是约束下最优）。弹出的第一个可行节点最优。

NP-hard，最坏指数；冲突少时远快于联合 A\\*。

---

## 4. 伪代码

```
root.paths ← 各车 A*
root.constraints ← ∅
push (SOC(root), root)
while heap:
    N ← pop 最小 SOC
    if N.paths 无冲突: return N.paths
    (a,b,v,t) ← 第一冲突
    for who in {a,b}:
        C ← N.constraints ∪ {who 不能在 (v,t)}
        π ← TimeA*(who, C)
        若成功: 更新该车路径，push 新节点
```

边冲突类似，约束写成禁止走某有向边拍。
"""),
        PATH,
        code("""
from lib.agents import vertex_conflicts, edge_conflicts

paths = {"a": [(0, 1), (1, 1), (2, 1)], "b": [(2, 1), (1, 1), (0, 1)]}
print("顶点冲突", vertex_conflicts(paths))
print("换边", edge_conflicts(paths))
"""),
        md("""`vertex_conflicts`：对齐长度（终点停留）后扫每一拍是否同格。
"""),
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.cbs import cbs
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_swap()
r = cbs(g, starts, goals)
print("found", r["found"], "SOC", r["soc"], "高层", r["high"], "底层扩展", r["low"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "CBS")
studio
"""),
        md("""## 5. 实现表（`cbs`）

| 块 | 作用 |
|----|------|
| 根节点 `astar` 各车 | 无约束最短路 |
| `CTNode` 按 cost 进堆 | 高层 A\\* |
| `_path_with_constraints` | 约束变成占用表里的 block |
| `cap` | 无解时避免死循环 |

## 常见 bug

- 底层不用时间维，无法等待消冲突。
- 冲突只拆一次就停，没把新路径再送回高层。
- stay-at-target 与 disappear 混用，终点占用不一致。
"""),
    ]


def lesson_16():
    return "16_cbs_enhanced", "16 CBS 增强：基数冲突与 bypass", [
        md("""
## 1. 定义

朴素 CBS 见冲突就二分，树肥。增强（ICBS 等）：

- **基数冲突（cardinal）**：无论让 A 还是 B，SOC 都上升。应优先拆。
- **semi / non-cardinal**：只有一方或双方 SOC 不变。
- **bypass**：某个孩子 SOC 不变且冲突减少，用它替换当前节点，不分支。
- **对称性**（走廊、矩形）：一次加一串约束。

本仓库 `enhanced=True`：生成两个孩子后，若存在 SOC 不增的，只压那个（简化 bypass）。

---

## 2. 不变量

增强不放松最优性：仍先弹出 SOC 最小可行叶。只减少扩展。

---

## 3. 伪代码（本课实现）

```
children ← []
for 每个分支约束:
    重搜该车，得 new_paths, new_soc
    children.append(...)
if 存在 new_soc == 当前 soc:
    只 push 那一个   # bypass
else:
    全部 push
```
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.cbs import cbs, cbs_enhanced
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_swap()
plain = cbs(g, starts, goals)
enh = cbs_enhanced(g, starts, goals)
print("朴素高层", plain["high"], "增强", enh["high"], "SOC", plain["soc"], enh["soc"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), enh, "CBS+")
studio
"""),
        md("""读 `cbs(..., enhanced=True)` 的 `if same:`。工业代码还有 WDG 启发式（pairwise 依赖图）。

## 常见 bug

- bypass 时没检查冲突数是否真下降，可能循环。
- 把非基数冲突当基数，乱加约束破坏最优。
"""),
    ]


def lesson_17():
    return "17_ecbs", "17 ECBS / 有界次优 CBS", [
        md("""
## 1. 定义

**ECBS**（Barer et al., SoCS 2014）：允许

\\[
SOC \\le w\\cdot OPT
\\]

高层、底层都用 focal search：在 f ≤ w·最优下界的节点里，优先扩「冲突少」的。

**EECBS**（Li et al., AAAI 2021）：高层换 Explicit Estimation Search，界限同类。

本仓库教学版：先 CBS 得 OPT，若 HCA 种子落在 w·OPT 内就用种子，否则退回 CBS。用来理解 **界限**，不是完整 focal。

---

## 2. 和 CBS / 加权 A\\*

加权 A\\* 是单车 w-次优。ECBS 是多车 SOC 的 w-次优。`w=1` 必须回到最优。

---

## 3. 伪代码（完整 ECBS 概念，对照论文）

```
底层：focal A*，在 g+h ≤ w·lb 的点里扩冲突最少的
高层：focal 于 SOC 下界 ≤ w·全局下界 的 CT 节点
第一个可行解即 w-次优
```
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.cbs import cbs, ecbs
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_swap()
opt = cbs(g, starts, goals)
for w in (1.0, 1.5):
    r = ecbs(g, starts, goals, w=w)
    print(f"w={w} SOC={r['soc']} 上限={w*opt['soc']:.1f}")
studio = PlannerStudio()
studio.show_multi(g.to_studio(), ecbs(g, starts, goals, w=1.5), "ECBS")
studio
"""),
        md("""## 常见 bug

- 用真实 OPT 当运行时下界（你事先不知道 OPT）。真正 ECBS 用各车 fmin 之和。
- w=1 却用了 inadmissible 底层。

## 练习

为何实时系统更爱「w-次优」而不是「超时返回当前最好」？前者有证明，后者没有。
"""),
    ]


def lesson_18():
    return "18_lns", "18 LNS / LNS2：大邻域搜索修解", [
        md("""
## 1. 定义

**Large Neighborhood Search** 用于 MAPF（Li et al. 的 MAPF-LNS / LNS2）：

1. 用 HCA 等快速得到可行解（可很丑）。
2. **Destroy**：抽 k 台车（随机或按冲突）。
3. **Repair**：其余车路径当障碍，只重规划这 k 台。
4. 更好且可行则接受。重复。

LNS2 可以从 **仍有碰撞** 的路径集开始修到无碰撞。

---

## 2. 保证

无最优、无完备。经验上 SOC 非增。适合「已经能跑再抠质量」。

---

## 3. 伪代码（本仓库 `lns`）

```
current ← HCA(...)
for round:
    subset ← 随机 k 车
    frozen ← 其余车路径写入 table
    按某种序对 subset 做 TimeA*
    若无冲突且 SOC ≤ current: current ← 新路径
```
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.cbs import lns
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = lns(g, starts, goals, rounds=8)
print("found", r["found"], "SOC", r["soc"], "历史", r["history"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "LNS")
studio
"""),
        md("""## 实现表

| 块 | 作用 |
|----|------|
| 初始 HCA 失败则反序再试 | 提高可行率 |
| `frozen` occupy | 邻域外当墙 |
| `history` | eval 检查非增 |

## 常见 bug

- 接受更差解却不记录（破坏 anytime 单调）。
- destroy 抽全部车 = 重跑 HCA，邻域太大。
"""),
    ]


def lesson_19():
    return "19_push_rotate", "19 Push-and-Rotate：规则式重排", [
        md("""
## 1. 定义

**Push-and-Rotate**（de Wilde et al.）及更早 Push-and-Swap：不搜冲突树，按规则

- **Push**：沿最短路走，挡路者被推到空邻格
- **Swap / Rotate**：在环上轮转换位

无向、空位数 ≥ 2 时一类图上完备。

---

## 2. 有向失败（必看负例）

单行 `L→M→R` 两车对头：没有「旁边」可推，也不能换边。算法应报告失败，不是 bug。

---

## 3. 伪代码（本课简化版：只 push）

```
重复直到都到达或卡住:
    for 未到目标的车 a:
        nxt ← A*(pos[a], goal[a]) 的下一步
        if nxt 空: 走
        else: 把占 nxt 的车推到它的空邻居；成功则 a 再走
```

完整论文还有 rotate 检测环。教学版空位不够会 `stuck`。
"""),
        PATH,
        code("""
from lib.maps import grid_open, directed_deadlock_map
from lib.algos.rules import push_and_rotate
from lib.studio.widget import PlannerStudio

g = grid_open(4, 3)
r = push_and_rotate(g, {"a": (0, 0), "b": (3, 0)}, {"a": (0, 2), "b": (3, 2)})
print("无向", r["found"])
print("有向", push_and_rotate(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"}))
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "Push-and-Rotate")
studio
"""),
        md("""## 常见 bug

- 对向推形成振荡（本实现会 stuck）。
- 有向图当无向 push。
"""),
    ]


def lesson_20():
    return "20_pibt", "20 PIBT：逐步抢格与优先级继承", [
        md("""
## 1. 定义

**Priority Inheritance with Backtracking**（Okumura et al., 2022）：每拍为所有车选下一步，不搜整条路径。

1. 按优先级从高到低。
2. 候选格按离自己目标的启发排序（含原地）。
3. 若格上有尚未决策的车：把优先级 **借** 给它，让它先让开（继承，类似 OS 优先级反转）。
4. 让不开则试下一候选；全失败则等待。

时间 \(O(k \\log k)\) 每拍量级（实现还含递归）。

---

## 2. 保证

无最优。无向可换位场景常常成功。有向窄廊可死锁。不完全。

---

## 3. 伪代码

```
每拍:
    decided ← {}
    function plan(a, forbidden):
        if a 已 decided: return
        for v in 邻居∪{pos[a]} 按 dist-to-goal 排序:
            if v in forbidden 或 v 已被别人 decided 占用: continue
            if 有车 b 现在在 v 且未 decided:
                pri[b] ← pri[a]+ε
                plan(b, forbidden ∪ {pos[a]})
            if v 仍空: decided[a]←v; return
        decided[a]←pos[a]
    for a in 优先级降序: plan(a, ∅)
    全体走到 decided[a]
```

`forbidden` 禁止把对方推到自己脚下造成互换死锁。
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.maps import directed_deadlock_map
from lib.algos.rules import pibt
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = pibt(g, starts, goals, steps=80)
print("开网格", r["found"], r["soc"])
print("有向", pibt(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"}, steps=20)["found"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "PIBT")
studio
"""),
        md("""读 `pibt` 里递归 `plan`。时间轴上看错步。

## 常见 bug

- 没有 forbidden，两车互换占格死循环。
- 已下发、不能后退的段让「让开」失败。
"""),
    ]


def lesson_21():
    return "21_lacam", "21 LaCAM / LaCAM*：懒惰构型搜索", [
        md("""
## 1. 定义

**LaCAM**（Lazy Constraints Addition search for MAPF，Okumura, AAAI 2023）：在 **联合构型图** 上搜，但后继不枚举 \(5^k\) 个，而用 PIBT（等）作 **configuration generator**，需要时再补后继（lazy）。

**LaCAM\\***：anytime，继续搜，代价不增，累加转移代价下可趋向最优。

---

## 2. 和联合 A\\* / PIBT

联合 A\\*：后继全枚举。  
PIBT：无搜索，逐步贪心，可能死锁。  
LaCAM：PIBT 给后继 + 系统搜索逃出局部死锁。

---

## 3. 伪代码（教学版）

```
stack ← [start_config]
came[start] ← nil
while stack:
    Q ← pop
    if Q = goal: 回溯
    Q' ← PIBT 一步(Q)          # 生成器
    if Q' 未见过: 入栈
    可选：枚举单车一步补完备性
```

LaCAM*：找到解后继续，接受更好的 PIBT 全轨迹。
"""),
        PATH,
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.rules import lacam, lacam_star
from lib.studio.widget import PlannerStudio

g, starts, goals = two_agent_tunnel()
r = lacam(g, starts, goals)
print("LaCAM", r["found"], r["soc"], r["expanded"])
print("LaCAM* 历史", lacam_star(g, starts, goals)["history"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "LaCAM")
studio
"""),
        md("""## 实现表

| 块 | 作用 |
|----|------|
| 构型元组 | 联合位置 |
| `pibt(..., steps=1)` | 一个后继 |
| 单车挪一步枚举 | 小图完备 |
| `lacam_star` 多轮 PIBT | anytime 非增 |

## 常见 bug

- 生成器总返回同一构型，搜索原地打转（came 可挡）。
- 把 LaCAM 当 PIBT 逐步执行器，忘了高层栈。
"""),
    ]


def lesson_22():
    return "22_hungarian", "22 匈牙利算法：最小权匹配指派", [
        md("""
## 1. 定义

**指派问题**：n 车 n 任务，代价矩阵 C，C_{ij}= 车 i 去任务 j 的代价。求一一匹配使 \(\\sum C_{i,\\pi(i)}\) 最小。

**匈牙利算法**（Kuhn 1955，Munkres 1957）多项式时间求最优匹配。本仓库 `linear_sum_assignment` 是 Kuhn–Munkres 的势函数实现。

**贪心**：按车顺序各取剩余最小。不必最优。

---

## 2. 代价必须来自最短路

\\(C_{ij}=\\mathrm{Dijkstra}(s_i, t_j)\\)（有向）。欧氏距离会在单行绕路上骗人。

---

## 3. 不变量

最优匹配代价 ≤ 任何其它完美匹配（含贪心）。不可达写成大数 1e6。

---

## 4. 贪心伪代码 vs 匈牙利

```
贪心:
    对每辆还没派的车:
        选剩余任务里 Dijkstra 最小者

匈牙利:
    把 C 补成方阵
    用顶标 u,v 找相等子图的完备匹配
    返回 (row, col) 对
```

教学不必手推顶标；要会 **填矩阵** 和 **读匹配结果**。
"""),
        PATH,
        code("""
from evals.scenarios import assign_pair
from lib.search import dijkstra
from lib.algos.assignment import greedy_assign, hungarian_assign

g, robots, starts, tasks = assign_pair()
print("Dijkstra 矩阵:")
for r in robots:
    for t in tasks:
        print(f"  {r}->{t}", dijkstra(g, starts[r], t, record=False).cost)
print("贪心", greedy_assign(g, robots, starts, tasks))
print("匈牙利", hungarian_assign(g, robots, starts, tasks))
"""),
        md("""## 实现表

| 函数 | 作用 |
|------|------|
| `cost_matrix(..., use_topo=True)` | 填 Dijkstra |
| `use_topo=False` | 填启发，仅对照 |
| `linear_sum_assignment` | 返回行、列下标 |

## 常见 bug

- 用直线距离填 C。
- n 车 m 任务不补方阵。
- 把匹配代价当成含等待的 SOC（那是路径层）。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.map = g.to_studio()
studio.algo = "assignment"
studio
"""),
    ]


def lesson_23():
    return "23_auction", "23 拍卖指派：在线单物品", [
        md("""
## 1. 定义

任务一个个到达。每来一个，空闲车报「到该点的有向最短路」，最低者中标。

这是贪心在线算法，不是匈牙利。同一批若到达顺序不同，匹配可能不同。

---

## 2. 伪代码

```
free ← 所有车
for task in arrivals:
    bids ← [(Dijkstra(pos[r], task), r) for r in free]
    cost, winner ← min(bids)
    assign[winner] ← task
    free.remove(winner)
```

---

## 3. 与匈牙利

同时知道全部任务时匈牙利更优。在线拍卖不必等齐。竞争比在最坏情况下可以任意差；实践中常接近。
"""),
        PATH,
        code("""
from evals.scenarios import assign_pair
from lib.algos.assignment import auction_assign, hungarian_assign

g, robots, starts, tasks = assign_pair()
print("顺序", tasks, auction_assign(g, robots, starts, tasks, arrivals=tasks))
print("逆序", list(reversed(tasks)), auction_assign(g, robots, starts, tasks, arrivals=list(reversed(tasks))))
print("匈牙利", hungarian_assign(g, robots, starts, tasks)["cost"])
"""),
        md("""## 常见 bug

- 忙碌车也参与出价。
- 出价用欧氏距离。
"""),
    ]


def lesson_24():
    return "24_tpts", "24 TPTS：令牌传递与任务交换", [
        md("""
## 1. 定义

**Token Passing with Task Swaps**（Ma et al., AAMAS 2017 一带终身 MAPF）：

1. 空闲车领剩余任务中对自己最近者（令牌=规划权）。
2. 有任务的车 HCA 行走。
3. 对头且 `allow_swap`：交换目标再走。

面向任务流，不是一次性 n 对 n。

---

## 2. 为何换任务

走廊两端互换目标 = 空间上必须穿过。交换后各回自己现在这头，冲突消失。

---

## 3. 伪代码

```
while 还有任务或有人在执行:
    空闲车领取最近剩余任务
    HCA(当前有任务的车)
    if 失败 and allow_swap and 恰好两车:
        交换 assign 再 HCA
    沿路径更新位置；到达则变空闲
```
"""),
        PATH,
        code("""
from lib.maps import corridor_headon
from lib.algos.assignment import tpts

g = corridor_headon()
stream = [("t0", "B"), ("t1", "A")]
print("换", tpts(g, ["r0", "r1"], {"r0": "A", "r1": "B"}, stream, True))
print("不换", tpts(g, ["r0", "r1"], {"r0": "A", "r1": "B"}, stream, False))
"""),
        md("""看 `found` 与 `headon`。实现里 HCA 失败才 swap 一次，不是最优任务分配。

## 常见 bug

- 交换后位置当起点忘了更新。
- 无限 while：到达条件没把 assign 置空。
"""),
    ]


def lesson_25():
    return "25_cbs_ta", "25 CBS-TA：联合目标分配与路径", [
        md("""
## 1. 定义

**CBS-TA**（Hönig et al.）：目标分配 π 与无碰撞路径一起优化。先匈牙利再 CBS 只是「给定 π 的最优路径」，换 π 可能 SOC 更小。

完整 CBS-TA 在分配树上搜索；本课：匈牙利 π 上跑 CBS，并与贪心 π + CBS 比较。

---

## 2. 两个代价

- 矩阵代价：\(\\sum d(s_i,t_{\\pi i})\) 不含避让。
- SOC：含等待。所以「矩阵最优」不必「SOC 最优」。

---

## 3. 伪代码（教学）

```
π_h ← Hungarian(Dijkstra 矩阵)
paths_h ← CBS(starts, π_h)
π_g ← Greedy(...)
paths_g ← CBS(starts, π_g)
比较 SOC
```
"""),
        PATH,
        code("""
from evals.scenarios import assign_pair
from lib.algos.assignment import cbs_ta
from lib.studio.widget import PlannerStudio

g, robots, starts, tasks = assign_pair()
r = cbs_ta(g, robots, starts, tasks)
print("指派", r["assign"], "SOC", r["soc"], "贪心CBS", r["greedy_soc"])
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "CBS-TA")
studio
"""),
        md("""## 常见 bug

- 比较矩阵代价与 SOC。
- 分配不一一对应（两车同一目标）就丢给 CBS。
"""),
    ]


def lesson_26():
    return "26_rrt", "26 RRT：随机树探索连续空间", [
        md("""
## 1. 定义

**RRT**（LaValle, 1998）：在连续状态空间采样长树。状态是实数坐标，没有现成邻居列表。

```
T ← {start}
重复 n 次:
    x_rand ← 均匀随机（以 p 概率直接取 goal）
    x_near ← T 中离 x_rand 最近
    x_new ← 从 x_near 向 x_rand 走一步长 ε（steer）
    若线段不碰障碍: T 加边
    若 x_new 靠近 goal: 成功
```

---

## 2. 保证

**概率完备**：缝隙有正宽度、n→∞ 时成功概率→1。  
**不必最优**。不适合已经离散好的路网（用 Dijkstra）。

---

## 3. 实现表（`lib/algos/rrt.py`）

| 函数 | 作用 |
|------|------|
| `_collides` | 点是否在圆障碍内 |
| `_seg_collides` | 线段采样若干点 |
| `_steer` | 步长 ε 截断 |
| `_nearest` | 暴力最近（教学；KD 树可加速） |
| `goal_bias` | 偶尔采样终点，加快命中 |
"""),
        PATH,
        code("""
from lib.maps import continuous_scene
from lib.algos.rrt import rrt
from lib.studio.widget import PlannerStudio

scene = continuous_scene()
r = rrt(scene, seed=1, n=1500)
print("found", r["found"], "代价", r["cost"], "节点", len(r["nodes"]))
studio = PlannerStudio()
studio.show_rrt(scene, r, "RRT")
studio
"""),
        md("""换 seed 路径形状会变。

## 常见 bug

- 只查端点碰撞，线段穿过圆。
- ε 太大跳过窄缝，太小树涨得慢。
"""),
    ]


def lesson_27():
    return "27_rrt_star", "27 RRT*：渐近最优采样", [
        md("""
## 1. 定义

**RRT\\***（Karaman & Frazzoli, IJRR 2011）：RRT + 选父 + rewire，使代价随样本变多 **几乎必然 → 最优**（渐近最优）。

1. 新点 x_new 附近半径 r 内，选从起点过来 **g 最小** 且连线无碰的当父亲（不只几何最近）。
2. **Rewire**：若经 x_new 到某邻居更便宜，改该邻居的父指针。

---

## 2. 和 RRT / A\\*

RRT 不改已有边。A\\* 在有限图上一次弹出即最优。RRT\\* 在连续空间靠变密逼近。

半径 r 理论与 \(\\gamma(\\log n / n)^{1/d}\) 有关；本课固定 r 便于教学。

---

## 3. 伪代码增量

```
在 RRT 接受 x_new 之后:
    父 ← argmin_{x in Near} g(x)+dist(x,x_new) 且无碰
    g[x_new] ← 该代价
    for x in Near:
        if g[x_new]+dist(x_new,x) < g[x] 且无碰:
            parent[x] ← x_new
```
"""),
        PATH,
        code("""
from lib.maps import continuous_scene
from lib.algos.rrt import rrt, rrt_star
from lib.studio.widget import PlannerStudio

scene = continuous_scene()
a = rrt(scene, seed=2, n=900)
b = rrt_star(scene, seed=2, n=1400)
print("RRT", a["cost"], "RRT*", b["cost"])
studio = PlannerStudio()
studio.show_rrt(scene, b, "RRT*")
studio
"""),
        md("""同种子下 RRT\\* 代价应 ≤ RRT。n 再增大代价不增。

## 常见 bug

- rewire 不检查碰撞。
- Near 用全体节点且 n 很大 ⇒ \(O(n^2)\)。
"""),
    ]
