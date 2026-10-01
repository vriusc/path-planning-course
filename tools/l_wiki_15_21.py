"""Wiki-style lessons 15–21: CBS family and rule-based MAPF."""

from tools.nb import BOOT, code, md

PATH = code(BOOT)


def lesson_15():
    return "15_cbs", "15 CBS：冲突树最优 MAPF", [
        md("""
本课按百科条目写。CBS 是离散 MAPF 求 SOC 最优的主流精确算法。调度台在最后。

---

## 1. 定义

**Conflict-Based Search**（Sharon, Stern, Felner, Sturtevant, AIJ 2015）：两层搜索。

- **高层**：冲突树 CT。每个节点 = 约束集合 + 一组单车路径。
- **底层**：对某个智能体，在该节点的约束下做时间 A\\*（本仓库；也可以 SIPP）。

根节点：各车 **独立** 最短路（普通 A\\*，互不理睬）。若两路径在 (点, t) 或换边冲突，分裂：

- 左孩子：禁止 A 在该 (点, t)（或禁止走那条边拍）
- 右孩子：禁止 B 在该 (点, t)

高层按 SOC（各车到达时间和）做最佳优先。弹出的 **第一个无冲突叶** 即经典离散 MAPF 的 SOC 最优解。

- 输入：图、各车起终点、高层 cap。
- 输出：无冲突路径字典，SOC，高层/底层扩展数。

---

## 2. 和 HCA* / 联合 A*

| | 联合 A\\* | HCA\\* | CBS |
|--|--|--|--|
| 状态 | 联合位置 | 单车 + 全序 | 单车 + 约束集 |
| 最优 | 是 | 否 | 是（SOC） |
| 分支 | \(5^k\) | 1 条全序 | 每个冲突 2 叉 |
| 何时快 | k≤2 | 几乎总是 | 冲突少时远快于联合 A\\* |

CBS 只在 **真发生的冲突** 上分支，底层仍是单车搜索。冲突少（空旷、错开）时树很小；全员挤窄廊时树仍指数。MAPF 是 NP-hard，最坏躲不掉。

---

## 3. 不变量（为何最优）

- CT 节点的约束只增不减。
- 底层路径满足该节点全部约束（约束写成占用表里的 block）。
- **可采纳：** 节点的 SOC = 各车在 **当前约束下** 的最优代价之和，是该支任何可行解的下界（再加约束只会更差或持平）。
- 高层堆先弹 SOC 最小者。第一个可行叶：不存在 SOC 更小的可行解，否则它的下界更小，应先被弹出。

stay-at-target：先到的车停在终点，后面的拍仍占该格。`vertex_conflicts` 用 `pad` 把短路径补成终点停留再比。

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

边冲突类似，约束写成禁止走某有向边拍。`cap` 限制高层弹出次数，无解时避免死循环。

---

## 5. 手算

1 宽走廊两车对换。独立最短路在中点同一拍相遇。

| CT 节点 | 约束 | 路径要点 | SOC |
|---------|------|----------|-----|
| 根 | ∅ | 对头，中点冲突 | 2×长度 |
| 左 | a 不能占中点@t* | a 等一拍 | +1 |
| 右 | b 不能占中点@t* | b 等一拍 | +1 |

任一孩子无冲突即可返回。最优 SOC = 独立和 + 1（一人等）。
"""),
        PATH,
        md("""
## 6. 实现：冲突检测 + 两车 CBS
"""),
        code("""
from lib.agents import pad, soc, vertex_conflicts, edge_conflicts, is_conflict_free


def first_conflict(paths):
    # 先顶点、后换边。返回 ('vertex', a, b, loc, t) 或 ('edge', a, b, (u, v), t)
    vc = vertex_conflicts(paths)
    if vc:
        a, b, loc, t = vc[0]
        return ("vertex", a, b, loc, t)
    ec = edge_conflicts(paths)
    if ec:
        a, b, u, v, t = ec[0]
        return ("edge", a, b, (u, v), t)
    return None


paths = {"a": [(0, 1), (1, 1), (2, 1)], "b": [(2, 1), (1, 1), (0, 1)]}
print("手写冲突", first_conflict(paths))
print("库顶点", vertex_conflicts(paths))
print("库换边", edge_conflicts(paths))
cross = {"a": [(0, 0), (1, 0)], "b": [(1, 0), (0, 0)]}
print("对向穿过（无同格、有换边）", first_conflict(cross), edge_conflicts(cross))
"""),
        code("""
from lib.search import astar
from lib.algos.temporal import time_astar
from lib.reservation import ReservationTable
from evals.scenarios import two_agent_swap


def replan(graph, start, goal, constraints, agent):
    # 约束 (kind, loc, t, who)；只执行属于自己的
    table = ReservationTable()
    for kind, loc, t, who in constraints:
        if who != agent:
            continue
        if kind == "vertex":
            table.occupy(loc, t, "block")
        elif kind == "edge":
            a, b = loc
            table.occupy_edge(a, b, t, "block")
    return time_astar(graph, start, goal, table=table, agent=agent)


def cbs_two(graph, starts, goals, cap=80, verbose=True):
    agents = list(starts)
    paths = {}
    for a in agents:
        r = astar(graph, starts[a], goals[a], record=False)
        if not r.found:
            return {"found": False, "paths": {}}
        paths[a] = r.path
    nodes = [(soc(paths), [], paths)]
    high = 0
    while nodes and high < cap:
        nodes.sort(key=lambda x: x[0])
        cost, cons, paths = nodes.pop(0)
        high += 1
        conf = first_conflict(paths)
        if verbose:
            print(f"高层#{high} SOC={cost} 约束数={len(cons)} 冲突{conf}")
        if conf is None:
            return {"found": True, "paths": paths, "soc": cost, "high": high}
        kind, a, b, loc, t = conf
        if kind == "vertex":
            branches = [("vertex", loc, t, a), ("vertex", loc, t, b)]
        else:
            u, v = loc
            branches = [("edge", (u, v), t, a), ("edge", (v, u), t, b)]
        for ck, cloc, ct, who in branches:
            new_cons = cons + [(ck, cloc, ct, who)]
            new_paths = dict(paths)
            r = replan(graph, starts[who], goals[who], new_cons, who)
            if not r.found:
                continue
            new_paths[who] = r.path
            nodes.append((soc(new_paths), new_cons, new_paths))
    return {"found": False, "paths": {}, "high": high}


g, starts, goals = two_agent_swap()
r = cbs_two(g, starts, goals)
print("found", r["found"], "SOC", r.get("soc"), "高层", r.get("high"))
print("无冲突", is_conflict_free(r["paths"]) if r["found"] else None)
print("a", r["paths"].get("a"))
print("b", r["paths"].get("b"))
"""),
        md("""
## 7. 逐行

| 块 | 作用 |
|----|------|
| 根节点 `astar` 各车 | 无约束最短路，下界 |
| `first_conflict` | 先顶点、后换边；漏换边会宣布「无冲突」其实对向穿过 |
| `replan` | 约束 → 占用表 block → 时间 A\\* |
| 两叉 | 顶点禁同一 (点,t)；换边禁 (u,v,t) 与 (v,u,t) |
| 按 SOC 弹出 | 高层可采纳 |

库 `cbs` 同样处理边冲突、`cap`、增强开关。只查顶点时，两车对换会在「各走各的下一格」漏检。
"""),
        code("""
from lib.algos.cbs import cbs

lib_r = cbs(g, starts, goals)
print("库 found", lib_r["found"], "SOC", lib_r["soc"], "高层", lib_r["high"], "底层扩展", lib_r["low"])
"""),
        md("""
## 常见 bug

1. 底层不用时间维，无法等待消冲突。
2. 冲突只拆一次就停，没把新路径再送回高层。
3. stay-at-target 与 disappear 混用，终点占用不一致。
4. 约束没写进表，底层仍走原路，树无限长。
5. 无 cap：无解实例（两车换位却只有一格）会转到内存耗尽。
6. 只查顶点、不查换边：两车对向穿过会被当成无冲突。

## 条目小结

| 项目 | 内容 |
|------|------|
| 高层 | 冲突树 + SOC 最佳优先 |
| 底层 | 约束下的时间 A\\* |
| 保证 | SOC 最优（经典离散 MAPF） |
| 下一课 | 少分支：基数冲突与 bypass |

## 练习

1. 根节点 SOC 为什么是下界？加约束后 SOC 会变小吗？
2. 用纸画出 two_agent_swap 根节点两条路径，标出第一冲突的 (点,t)。
3. 若只分支 a、不分支 b，还保证最优吗？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), lib_r, "CBS")
studio
"""),
    ]


def lesson_16():
    return "16_cbs_enhanced", "16 CBS 增强：基数冲突与 bypass", [
        md("""
本课按百科条目写。朴素 CBS 见冲突就二分，树肥。增强（ICBS 等）少分支、仍最优。调度台在最后。

---

## 1. 定义

工业 CBS（ICBS、CBSH 等）在分裂前给冲突分类：

- **基数冲突（cardinal）：** 无论让 A 还是让 B，SOC **都上升**。应优先拆，否则树在无关冲突上浪费。
- **semi-cardinal：** 只有一方 SOC 上升。
- **non-cardinal：** 双方 SOC 都不升（有另一条同样长的路）。
- **bypass：** 某个孩子 SOC 不变且冲突数下降，用它 **替换** 当前节点，不把兄弟推进堆。
- **对称性**（走廊、矩形）：一次加一串约束，避免沿着走廊逐步等。

本仓库 `enhanced=True`：生成两个孩子后，若存在 SOC 不增的，只压那个（简化 bypass）。没有完整 cardinal MDDs。

---

## 2. 不变量

增强 **不放松最优性**：仍先弹出 SOC 最小可行叶。只减少扩展。bypass 的孩子 SOC=父 SOC，下界不变。

若 bypass 不检查冲突是否真下降，可能在两个等 SOC 节点间循环——库用「只压一个孩子、约束仍增加」避免原地踏步。

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
    全部 push         # 双方都变贵 ≈ cardinal
```

完整 ICBS 还要用 MDD（该代价下的所有路径）判定 cardinal，并优先拆 cardinal。

---

## 4. 手算

父 SOC=10。孩子 A：SOC=10（另找一条等长路躲开冲突）。孩子 B：SOC=12。

bypass：只保留 A，不把 B 进堆。若 A 仍有别的冲突，下一轮再拆。最优性：B 的 12 不会比「沿 A 继续」的任何 ≤10 的解更好。
"""),
        PATH,
        md("""
## 6. 实现：bypass 决策（先看数字，再跑整树）
"""),
        code("""
def bypass_or_branch(parent_soc, children):
    # children: 列表 (label, soc, n_conflicts)
    same = [c for c in children if c[1] == parent_soc]
    if same:
        pick = min(same, key=lambda c: c[2])
        return "bypass", pick
    return "branch", children


print("等 SOC 少冲突", bypass_or_branch(10, [("A", 10, 1), ("B", 12, 0)]))
print("双方都涨", bypass_or_branch(10, [("A", 11, 0), ("B", 12, 0)]))
print("双方都不涨", bypass_or_branch(10, [("A", 10, 2), ("B", 10, 1)]))
"""),
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.cbs import cbs, cbs_enhanced

g, starts, goals = two_agent_swap()
plain = cbs(g, starts, goals)
enh = cbs_enhanced(g, starts, goals)
print("朴素高层", plain["high"], "树", plain.get("tree"), "SOC", plain["soc"])
print("增强高层", enh["high"], "树", enh.get("tree"), "SOC", enh["soc"])
print("SOC 应相同", plain["soc"] == enh["soc"])
"""),
        md("""
## 7. 逐行（库 `enhanced=True`）

| 行 | 作用 |
|----|------|
| 先生成全部孩子 | 才能比较 SOC |
| `same = [c for c in children if c[2]==node.cost]` | 不涨价的孩子 |
| 只 push `same[0]` | 简化 bypass |
| else 全 push | 近似 cardinal 全拆 |

读 `cbs(..., enhanced=True)` 的 `if same:`。工业代码还有 WDG 启发式（pairwise 依赖图当高层 h）。

## 常见 bug

1. bypass 时没检查冲突数是否真下降，可能循环。
2. 把非基数冲突当基数，乱加约束——本实现不加额外约束，只少压节点，不破坏最优。
3. 以为增强可以次优换速度——那是 ECBS，下一课。

## 条目小结

| 项目 | 内容 |
|------|------|
| 目标 | 少扩展、仍最优 |
| bypass | 等 SOC 孩子替换当前 |
| cardinal | 双方都涨价的冲突优先 |
| 下一课 | 允许 w·OPT 换速度 |

## 练习

1. 为何 bypass 不破坏最优？用下界说话。
2. 两个孩子 SOC 都不涨，选冲突更少的那个。为什么？
3. 走廊对称冲突若一次只禁一格，树会怎样长？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), enh, "CBS+")
studio
"""),
    ]


def lesson_17():
    return "17_ecbs", "17 ECBS / 有界次优 CBS", [
        md("""
本课按百科条目写。实时系统常要「保证不太差」而不是「保证最优」。调度台在最后。

---

## 1. 定义

**ECBS**（Barer, Sharon, Stern, Felner, SoCS 2014）允许

\\[
SOC \\le w\\cdot OPT,\\qquad w\\ge 1
\\]

高层、底层都用 **focal search**：在 f ≤ w·当前最优下界 的节点里，优先扩「冲突少」的，而不是严格最小 f。

**EECBS**（Li et al., AAAI 2021）：高层换 Explicit Estimation Search，界限同类。

本仓库教学版：先 CBS 得 OPT，若 HCA 种子落在 w·OPT 内就用种子，否则退回 CBS。用来理解 **界限**，不是完整 focal。请诚实对待：运行时你事先不知道 OPT；真 ECBS 用各车 focal 下界之和当 LB。

---

## 2. 和 CBS / 加权 A*

| | 加权 A\\* | ECBS |
|--|--|--|
| 对象 | 单车路径 | 多车 SOC |
| 键 | g+w h | 高层 focal + 底层 focal |
| w=1 | A\\* 最优 | 必须回到 CBS 最优 |

「超时返回当前最好」没有 w·OPT 证明。有界次优的价值是 **证明**，不是感觉。

---

## 3. 不变量

- w=1 ⇒ 与 CBS 同解（教学版用 CBS 本身）。
- 返回的 SOC ≤ w·OPT（教学版：种子通过才用种子，否则 OPT）。
- 真 ECBS 的 LB 是可采纳的，不依赖先算出 OPT。

---

## 4. 伪代码

完整 ECBS 概念：

```
底层：focal A*，在 g+h ≤ w·lb 的点里扩冲突最少的
高层：focal 于 SOC 下界 ≤ w·全局下界 的 CT 节点
第一个可行解即 w-次优
```

本课教学：

```
opt ← CBS(...)
seed ← HCA(...)
if seed.soc ≤ w * opt.soc: return seed
else: return opt
```

---

## 5. 手算

OPT=12，HCA 种子=16。

- w=1：16 ≰ 12，返回 CBS。
- w=1.5：上限 18，16≤18，可用种子。
- w=3：同样可用种子。
"""),
        PATH,
        md("""
## 6. 实现：界限检查
"""),
        code("""
from evals.scenarios import two_agent_swap
from lib.algos.cbs import cbs
from lib.algos.prioritized import hca


def ecbs_teach(graph, starts, goals, w=1.5):
    opt = cbs(graph, starts, goals)
    seed = hca(graph, starts, goals)
    bound = w * opt["soc"]
    print("OPT", opt["soc"], "HCA种子", seed.get("soc"), "上限", bound)
    if seed["found"] and seed["soc"] <= bound + 1e-9:
        seed["w"] = w
        seed["bound"] = bound
        seed["optimal_soc"] = opt["soc"]
        seed["used"] = "hca"
        return seed
    opt["w"] = w
    opt["bound"] = bound
    opt["optimal_soc"] = opt["soc"]
    opt["used"] = "cbs"
    return opt


g, starts, goals = two_agent_swap()
for w in (1.0, 1.5, 3.0):
    r = ecbs_teach(g, starts, goals, w=w)
    print(f"w={w} used={r['used']} SOC={r['soc']} 上限={r['bound']}")
"""),
        code("""
from lib.algos.cbs import ecbs, cbs

opt = cbs(g, starts, goals)
for w in (1.0, 1.5):
    r = ecbs(g, starts, goals, w=w)
    print(f"库 w={w} SOC={r['soc']} 上限={w * opt['soc']:.1f} 应成立 {r['soc'] <= w * opt['soc'] + 1e-9}")
"""),
        md("""
## 常见 bug

1. 用真实 OPT 当运行时下界（你事先不知道 OPT）。真正 ECBS 用各车 fmin 之和。
2. w=1 却用了 inadmissible 底层。
3. 把 HCA 种子直接当 ECBS，不检查界限。
4. 和 anytime CBS（先出可行再改善）搞混：anytime 无 w 证明。

## 条目小结

| 项目 | 内容 |
|------|------|
| 保证 | SOC ≤ w·OPT |
| w=1 | 最优 |
| 教学版 | CBS + 可选 HCA 种子 |
| 下一课 | 已有可行解再抠质量：LNS |

## 练习

1. 为何实时系统更爱「w-次优」而不是「超时返回当前最好」？
2. 若 HCA 种子比 w·OPT 还差，教学版退回 CBS。真 ECBS 会怎样？
3. 单车加权 A\\* 的 w 和 ECBS 的 w 能直接比较吗？一个管路径，一个管 SOC。
"""),
        code("""
from lib.studio.widget import PlannerStudio
from lib.algos.cbs import ecbs
r = ecbs(g, starts, goals, w=1.5)
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "ECBS")
studio
"""),
    ]


def lesson_18():
    return "18_lns", "18 LNS / LNS2：大邻域搜索修解", [
        md("""
本课按百科条目写。LNS 不从零证明最优，而是「已有可行解再抠」。调度台在最后。

---

## 1. 定义

**Large Neighborhood Search** 用于 MAPF（Li et al. 的 MAPF-LNS / LNS2）：

1. 用 HCA 等快速得到可行解（可很丑）。
2. **Destroy**：抽 k 台车（随机或按冲突/延迟）。
3. **Repair**：其余车路径当障碍，只重规划这 k 台。
4. 更好且可行则接受。重复。

LNS2 可以从 **仍有碰撞** 的路径集开始修到无碰撞。本仓库从可行 HCA 出发，保证历史 SOC 非增。

- 输入：图、起终点、轮数。
- 输出：路径、SOC、`history` 列表。

---

## 2. 保证

无最优、无完备。经验上 SOC 非增（只接受更好或持平）。适合「已经能跑再抠质量」。k 太大 = 重跑 HCA；k=1 邻域太小，改善慢。

---

## 3. 不变量

- 接受条件：新路径无冲突 **且** SOC ≤ 当前。
- `history` 单调非增，给 eval 用。
- frozen 车写入占用表，subset 车看不见彼此以外的自由——它们按某种序时间 A\\*。

---

## 4. 伪代码

```
current ← HCA(...)
for round:
    subset ← 随机 k 车
    frozen ← 其余车路径写入 table
    按某种序对 subset 做 TimeA*
    若无冲突且 SOC ≤ current: current ← 新路径
```

---

## 5. 手算

两车平行、HCA 已经最优。Destroy 任一台再修，SOC 不能再降。`history` 应全是同一个数。改善出现在「HCA 顺序很差、绕路很多」的实例。
"""),
        PATH,
        md("""
## 6. 实现：一轮 destroy / repair
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.prioritized import hca, _reserve_path
from lib.reservation import ReservationTable
from lib.algos.temporal import time_astar
from lib.agents import is_conflict_free, soc


def one_repair(graph, starts, goals, current_paths, subset):
    frozen = {a: p for a, p in current_paths.items() if a not in subset}
    table = ReservationTable()
    for a, p in frozen.items():
        _reserve_path(table, p, a)
    new_paths = dict(frozen)
    for a in subset:
        r = time_astar(graph, starts[a], goals[a], table=table, agent=a)
        print("  重规划", a, "found", r.found, "cost", r.cost)
        if not r.found:
            return None
        new_paths[a] = r.path
        _reserve_path(table, r.path, a)
    if is_conflict_free(new_paths):
        return new_paths
    return None


g, starts, goals = two_agent_tunnel()
cur = hca(g, starts, goals)
print("初始 HCA SOC", cur["soc"])
repaired = one_repair(g, starts, goals, cur["paths"], ["a"])
if repaired:
    print("修 a 后 SOC", soc(repaired), "非增", soc(repaired) <= cur["soc"])
else:
    print("本轮修失败，保留原解")
"""),
        code("""
from lib.algos.cbs import lns

r = lns(g, starts, goals, rounds=8)
print("found", r["found"], "SOC", r["soc"], "历史", r["history"])
print("历史非增", all(r["history"][i] <= r["history"][i - 1] for i in range(1, len(r["history"]))))
"""),
        md("""
## 7. 逐行

| 块 | 作用 |
|----|------|
| 初始 HCA 失败则反序再试 | 库提高可行率 |
| `frozen` occupy | 邻域外当移动墙 |
| 只接受 ≤ | anytime 单调 |
| `history` | eval 检查非增 |

## 常见 bug

1. 接受更差解却不记录（破坏 anytime 单调）。
2. destroy 抽全部车 = 重跑 HCA，邻域太大。
3. frozen 不锁边，repair 与 frozen 对向擦肩。
4. 从不可行解出发却用「SOC≤」当唯一接受条件（LNS2 要先把冲突数降下来）。

## 条目小结

| 项目 | 内容 |
|------|------|
| 思想 | destroy + repair |
| 保证 | 无；SOC 非增 |
| 下一课 | 不搜树，按规则推开挡路者 |

## 练习

1. k=1 与 k=n 的邻域各是什么？
2. 为何随机种子要固定才能让 eval 可重复？
3. 把接受条件改成「无冲突即可、允许 SOC 变差」，history 还单调吗？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "LNS")
studio
"""),
    ]


def lesson_19():
    return "19_push_rotate", "19 Push-and-Rotate：规则式重排", [
        md("""
本课按百科条目写。规则法不维护冲突树，按「挡住就推开」走。调度台在最后。

---

## 1. 定义

**Push-and-Rotate**（de Wilde et al.）及更早 Push-and-Swap：不搜 CT，按规则

- **Push**：沿最短路走，挡路者被推到空邻格
- **Swap / Rotate**：在环上轮转换位

无向、空位数 ≥ 2 时一类图上完备。本课教学子集 **只 push**：空位不够或有向无反边则 `stuck` / `directed`。

---

## 2. 和搜索法

| | CBS | Push |
|--|--|--|
| 对象 | 整条时空路径 | 当前构型上的一步规则 |
| 最优 | SOC 最优 | 否 |
| 有向窄廊 | 能等（若图可解） | 没旁格可推则失败 |

规则法常数小、好做执行层；失败要换搜索。

---

## 3. 不变量

- 每步之后两车不同格。
- 无向网格：邻居可双向走。
- 有向图缺反向边：本实现直接 `found=False`（必看负例）。

---

## 4. 伪代码（只 push）

```
重复直到都到达或卡住:
    for 未到目标的车 a:
        nxt ← A*(pos[a], goal[a]) 的下一步
        if nxt 空: 走
        else: 把占 nxt 的车推到它的空邻居；成功则 a 再走
```

完整论文还有 rotate 检测环。教学版空位不够会 `stuck`。

---

## 5. 手算

4×3 空网格，a 在 (0,0) 去 (0,2)，b 在 (3,0) 去 (3,2)。各走各列，push 用不上，几步到齐。

有向 `L→M→R` 对头：没有「旁边」可推，也不能换边。算法应报告失败，不是 bug。
"""),
        PATH,
        md("""
## 6. 实现：逐步 push
"""),
        code("""
from lib.maps import grid_open, directed_deadlock_map
from lib.search import astar
from lib.pretty import draw_grid
from lib.agents import soc


def push_simple(graph, starts, goals, steps=40, verbose=True):
    pos = dict(starts)
    paths = {a: [starts[a]] for a in starts}
    occupied = {v: k for k, v in pos.items()}
    for t in range(steps):
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
                        if verbose:
                            print(f"t={t} {a} 推开 {other} -> {cand}，自己到 {nxt}")
                        break
        if verbose:
            print(f"t={t} pos={pos}")
        if not progressed:
            return {"found": False, "paths": paths, "reason": "stuck"}
    return {"found": all(pos[a] == goals[a] for a in starts), "paths": paths}


g = grid_open(4, 3)
print(draw_grid(4, 3, start=(0, 0), goal=(0, 2)))
r = push_simple(g, {"a": (0, 0), "b": (3, 0)}, {"a": (0, 2), "b": (3, 2)})
print("无向 found", r["found"], "SOC", r.get("soc"))
"""),
        code("""
from lib.algos.rules import push_and_rotate

print("库无向", push_and_rotate(g, {"a": (0, 0), "b": (3, 0)}, {"a": (0, 2), "b": (3, 2)})["found"])
print("库有向", push_and_rotate(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"}))
"""),
        md("""
## 常见 bug

1. 对向推形成振荡（A 推 B，B 又推回 A）。本实现会 stuck。
2. 有向图当无向 push。
3. 推到别人目标上把别人锁死，没有 rotate 就解不开。

## 条目小结

| 项目 | 内容 |
|------|------|
| 动作 | push（教学）/ rotate（论文） |
| 完备 | 无向 + 足够空位 |
| 有向 | 应失败 |
| 下一课 | 每拍抢格：PIBT |

## 练习

1. 两车对头、中间无空格，push 为何振荡？
2. 空位数=1 的环上，为何需要 rotate 而不是 push？
3. 有向死锁失败是图的问题还是算法的问题？两者都是。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), r, "Push-and-Rotate")
studio
"""),
    ]


def lesson_20():
    return "20_pibt", "20 PIBT：逐步抢格与优先级继承", [
        md("""
本课按百科条目写。PIBT 每拍为所有车选下一步，不搜整条路径。调度台在最后。

---

## 1. 定义

**Priority Inheritance with Backtracking**（Okumura et al., 2022）：每拍为所有车选下一格。

1. 按优先级从高到低。
2. 候选格按离自己目标的启发排序（含原地）。
3. 若格上有尚未决策的车：把优先级 **借** 给它，让它先让开（继承，类似 OS 优先级反转）。
4. 让不开则试下一候选；全失败则等待。

时间每拍大约 \(O(k \\log k)\) 量级（实现还含递归）。无最优。无向可换位场景常常成功。有向窄廊可死锁。不完全。

LaCAM（下一课）用 PIBT 当后继生成器。

---

## 2. 不变量

- 每拍结束 `decided` 每人一格，且两两不同。
- `forbidden` 禁止把对方推到自己脚下造成互换死锁。
- 到达目标后优先级不再涨（库：未到达每拍 +1，到达 +0），让还在路上的车逐渐变高优先。

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

---

## 4. 手算（一拍）

a 在 (0,0) 要去右，b 在 (1,0) 挡路、自己也要去右。a 先决策，想进 (1,0)，发现 b 未决策 → 继承：b 先走 (2,0)，然后 a 进 (1,0)。一拍两车都右移。
"""),
        PATH,
        md("""
## 6. 实现：单拍 plan
"""),
        code("""
from lib.maps import grid_open
from lib.pretty import draw_grid


def pibt_step(graph, pos, goals, pri, verbose=True):
    agents = list(pos)
    occupied_next = {}
    decided = {}

    def dist(a, node):
        ga = goals[a]
        return abs(node[0] - ga[0]) + abs(node[1] - ga[1])

    def plan(a, forbidden):
        if a in decided:
            return decided[a] is not None
        cands = [n for n, _ in graph.neighbors(pos[a])] + [pos[a]]
        cands.sort(key=lambda n: (0 if n == goals[a] else 1, dist(a, n), str(n)))
        if verbose:
            print(f"  {a} 候选", cands, "forbidden", forbidden)
        for n in cands:
            if n in forbidden or n in occupied_next:
                continue
            holder = next((b for b, p in pos.items() if b != a and p == n), None)
            if holder is not None and holder not in decided:
                pri[holder] = pri[a] + 0.01
                if verbose:
                    print(f"    继承: {holder} 先让开 {n}")
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
    if verbose:
        print("decided", decided)
    return decided


g = grid_open(4, 1)
print(draw_grid(4, 1, start=(0, 0), goal=(3, 0)))
pos = {"a": (0, 0), "b": (1, 0)}
goals = {"a": (3, 0), "b": (3, 0)}
pri = {"a": 2.0, "b": 1.0}
print("一拍", pibt_step(g, pos, goals, pri))
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.maps import directed_deadlock_map
from lib.algos.rules import pibt

g2, starts, goals = two_agent_tunnel()
r = pibt(g2, starts, goals, steps=80)
print("开网格", r["found"], r["soc"])
print("有向", pibt(directed_deadlock_map(), {"a": "L", "b": "R"}, {"a": "R", "b": "L"}, steps=20)["found"])
"""),
        md("""
## 7. 逐行

| 行 | 作用 |
|----|------|
| 候选按离目标排序 | 贪心朝目标 |
| holder 未 decided | 优先级继承 + 递归 |
| `forbidden ∪ {pos[a]}` | 不许对方踏进自己脚 |
| 全失败则原地 | 等待 |

## 常见 bug

1. 没有 forbidden，两车互换占格死循环。
2. 已下发、不能后退的段让「让开」失败。
3. 两车同一目标格：后到的人会一直想挤进去。本例 b 的目标也是 (3,0)，教学只演示一拍。

## 条目小结

| 项目 | 内容 |
|------|------|
| 粒度 | 每拍 |
| 核心 | 继承 + 回溯候选 |
| 最优 | 否 |
| 下一课 | 用 PIBT 当联合搜索的后继生成器 |

## 练习

1. 用 OS 优先级反转类比：低优先占着高优先要的格，为何要借优先级？
2. forbidden 拿掉后，两车对头会怎样？
3. PIBT 成功不代表 SOC 最优。造一个「能到但绕远」的直觉例子。
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g2.to_studio(), r, "PIBT")
studio
"""),
    ]


def lesson_21():
    return "21_lacam", "21 LaCAM / LaCAM*：懒惰构型搜索", [
        md("""
本课按百科条目写。LaCAM 在联合构型图上搜，但后继不枚举 \(5^k\)。调度台在最后。

---

## 1. 定义

**LaCAM**（Lazy Constraints Addition search for MAPF，Okumura, AAAI 2023）：在 **联合构型图** 上搜，后继用 PIBT（等）作 **configuration generator**，需要时再补后继（lazy）。

**LaCAM\\***：anytime，继续搜，代价不增，累加转移代价下可趋向最优。

- 输入：图、起终点、扩展 cap。
- 输出：构型序列拆成的各车路径。

---

## 2. 和联合 A* / PIBT

| | 联合 A\\* | PIBT | LaCAM |
|--|--|--|--|
| 后继 | 全枚举 \(5^k\) | 无搜索，逐步贪心 | PIBT 给一个 + 少量补边 |
| 死锁 | 能搜出来（若可解） | 可能卡 | 搜其它构型逃出 |
| 最优 | 是 | 否 | LaCAM 否；LaCAM\\* anytime |

---

## 3. 不变量

- 栈上是联合位置元组。
- `came` 防重复构型。
- `_config_ok`：同一格不能两车。
- LaCAM\\* 的 `history` 非增。

---

## 4. 伪代码（教学版）

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

---

## 5. 手算

两车已在目标：栈弹出即停，expanded=1。

PIBT 一步就会死锁的构型：生成器返回原地，came 挡住，单车挪一步的补边可能把其中一车让到旁边，搜索继续。
"""),
        PATH,
        md("""
## 6. 实现：构型栈 + PIBT 一步
"""),
        code("""
from evals.scenarios import two_agent_tunnel
from lib.algos.rules import pibt
from lib.agents import soc


def lacam_tiny(graph, starts, goals, cap=200, verbose=True):
    agents = list(starts)
    start = tuple(starts[a] for a in agents)
    goal = tuple(goals[a] for a in agents)
    stack = [start]
    came = {start: None}
    expanded = 0
    while stack and expanded < cap:
        cur = stack.pop()
        expanded += 1
        if verbose and expanded <= 8:
            print(f"弹出构型#{expanded}", cur, "栈长", len(stack))
        if cur == goal:
            chain = []
            x = cur
            while x is not None:
                chain.append(x)
                x = came[x]
            chain.reverse()
            paths = {a: [st[i] for st in chain] for i, a in enumerate(agents)}
            return {"found": True, "paths": paths, "soc": soc(paths), "expanded": expanded}
        dummy = {a: cur[i] for i, a in enumerate(agents)}
        step = pibt(graph, dummy, goals, steps=1)
        nxt = tuple(step["paths"][a][-1] for a in agents)
        if nxt not in came:
            came[nxt] = cur
            stack.append(nxt)
        if expanded < cap // 2:
            for i, a in enumerate(agents):
                for n, _ in list(graph.neighbors(cur[i])) + [(cur[i], 0)]:
                    cfg = list(cur)
                    cfg[i] = n
                    tcfg = tuple(cfg)
                    if tcfg not in came and len(set(tcfg)) == len(tcfg):
                        came[tcfg] = cur
                        stack.append(tcfg)
    return {"found": False, "paths": {}, "expanded": expanded}


g, starts, goals = two_agent_tunnel()
r = lacam_tiny(g, starts, goals)
print("tiny found", r["found"], "SOC", r.get("soc"), "expanded", r["expanded"])
"""),
        code("""
from lib.algos.rules import lacam, lacam_star

lib_r = lacam(g, starts, goals)
print("LaCAM", lib_r["found"], lib_r["soc"], lib_r["expanded"])
star = lacam_star(g, starts, goals)
print("LaCAM* 历史", star["history"])
print("非增", all(star["history"][i] <= star["history"][i - 1] + 1e-9 for i in range(1, len(star["history"]))))
"""),
        md("""
## 7. 逐行

| 块 | 作用 |
|----|------|
| 构型元组 | 联合位置 |
| `pibt(..., steps=1)` | 一个后继 |
| 单车挪一步枚举 | 小图完备 |
| `lacam_star` 多轮 PIBT | anytime 非增 |

## 常见 bug

1. 生成器总返回同一构型，搜索原地打转（came 可挡，但要有补边否则停住）。
2. 把 LaCAM 当 PIBT 逐步执行器，忘了高层栈。
3. 构型用 list 当 dict 键——必须 tuple。

## 条目小结

| 项目 | 内容 |
|------|------|
| 图 | 联合构型 |
| 后继 | lazy（PIBT） |
| LaCAM\\* | anytime |
| 下一课 | 谁去哪个目标：指派 |

## 练习

1. 为何 PIBT 生成器「一个后继」不够完备？补边在补什么？
2. LaCAM\\* 历史非增，最优性要 n→∞ 还是 cap→∞？
3. 3 车时联合 A\\* cap 400 失败，LaCAM 为什么还能走？
"""),
        code("""
from lib.studio.widget import PlannerStudio
studio = PlannerStudio()
studio.show_multi(g.to_studio(), lib_r, "LaCAM")
studio
"""),
    ]
