# 路径规划课程

课本式教程：从「图是什么」写到 CBS / 任务指派。每课是 **手算 → 一段一段写代码并解释 → 打印搜索过程 → 最后才用调度台播放**，不是只看前端演示。

覆盖单车寻路、多智能体避撞（MAPF）和任务分配。网格和有向拓扑两种场地。

## 环境

```bash
cd path-planning-course
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install numpy networkx jupyter notebook ipykernel anywidget traitlets pytest
# 或: pip install -e .   （只打包 lib/）
python -m pytest evals/ -q
jupyter notebook notebooks/00_overview.ipynb
```

依赖：`numpy` `networkx` `jupyter` `notebook` `ipykernel` `anywidget` `traitlets` `pytest`。匈牙利算法是自实现的，不需要 SciPy。

调度台用 **anywidget + Canvas**。若控件是空白：

1. `pip install anywidget`
2. 刷新 notebook，重新跑第一个代码格
3. 算法仍然能 `print` 路径；eval 不依赖 UI

## 怎么学

按单元格顺序 Shift+Enter，不要跳过手算和打印格。调度台在每课后半段，用来核对你刚写的算法。

先 `01`→`09`（自己写出 BFS / Dijkstra / A* / 锁 / 时间 A* / SIPP），再 `10`→`18`（多车），然后 `19`→`25`，`26`→`27` 连续空间，`28` 收束。

| 课 | 文件 | 内容 |
|----|------|------|
| 00 | `00_overview.ipynb` | 三层问题、调度台 |
| 01–03 | BFS / Dijkstra / A* | 无权、带权、启发式 |
| 04–05 | 加权 A*、D* Lite | anytime、增量重规划 |
| 06 | JPS | 网格对称剪枝 |
| 07–09 | 锁、时间 A*、SIPP | 时空占用 |
| 10–14 | 联合 A*、HCA*、WHCA*、PBS、RHCR | 多车优先规划与窗口 |
| 15–18 | CBS / 增强 / ECBS / LNS | 冲突树与修解 |
| 19–21 | Push-and-Rotate、PIBT、LaCAM | 规则与构型搜索 |
| 22–25 | 匈牙利、拍卖、TPTS、CBS-TA | 任务分配 |
| 26–27 | RRT / RRT* | 连续空间采样 |
| 28 | 收束 | 如何叠这些算法 |

## 跑 eval

```bash
python -m pytest evals/ -q
python -m pytest evals/test_module_a.py -q
```

场景在 `evals/scenarios.py`，和 notebook 共用。

## 目录

```
lib/maps.py          网格 + 迷你有向院子
lib/search.py        BFS / Dijkstra / A*
lib/reservation.py   时空占用、段锁
lib/algos/           各算法实现
lib/studio/          PlannerStudio
evals/               pytest
notebooks/           课程
```
