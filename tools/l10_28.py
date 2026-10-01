"""Lessons 10–28: wiki bodies plus wrap-up."""

from tools.nb import BOOT, code, md
from tools.l_wiki_10_14 import lesson_10, lesson_11, lesson_12, lesson_13, lesson_14
from tools.l_wiki_15_21 import (
    lesson_15,
    lesson_16,
    lesson_17,
    lesson_18,
    lesson_19,
    lesson_20,
    lesson_21,
)
from tools.l_wiki_22_27 import (
    lesson_22,
    lesson_23,
    lesson_24,
    lesson_25,
    lesson_26,
    lesson_27,
)

PATH = code(BOOT)


def lesson_28():
    return "28_wrapup", "28 收束：这些算法怎么叠在一起", [
        md("""
## 一张地图

| 你要解决的事 | 先用 | 再升级 |
|--------------|------|--------|
| 网格、边权 1 | BFS（01） | A*（03） |
| 边有长度 / 有向 | Dijkstra（02） | A* + 可采纳 h（03） |
| 要更快、可差一点 | 加权 A*（04） | anytime 降 w |
| 地图中途变了 | 重新 A* | D* Lite（05） |
| 有别人占用 | 时间 A*（08） | SIPP（09） |
| 多车、要快 | HCA*（11） | PBS（13）、窗口 RHCR（14） |
| 多车、要最优 | CBS（15） | 增强 / ECBS（16–17） |
| 已有可行解要修 | LNS（18） | |
| 逐步协调 | PIBT（20） | LaCAM（21） |
| 谁去哪个目标 | 贪心 | 匈牙利 / 拍卖 / TPTS / CBS-TA（22–25） |
| 连续无格子 | RRT（26） | RRT*（27） |

主线是 **图搜索**：队列 → 堆 → 启发 → 时间 → 多车约束。采样和规则法是旁支。

每课结构相同：定义、和谁相邻、不变量、伪代码、实现表、常见 bug。库代码在 `lib/algos/`，与伪代码对照着读。

## 巩固

1. 空白 notebook 重写 01 的 `neighbors` / `reconstruct` / `bfs`。
2. Dijkstra 改 A*：只改堆键。
3. 占用表挡住第二台车，跑时间 A*。
4. `python -m pytest evals/ -q`
"""),
        PATH,
        code("""
print("从 notebooks/01_bfs.ipynb 再走一遍手算表。")
print("评测在 evals/。调度台只是把搜索帧画出来。")
"""),
    ]


LESSONS_10_28 = [
    lesson_10(),
    lesson_11(),
    lesson_12(),
    lesson_13(),
    lesson_14(),
    lesson_15(),
    lesson_16(),
    lesson_17(),
    lesson_18(),
    lesson_19(),
    lesson_20(),
    lesson_21(),
    lesson_22(),
    lesson_23(),
    lesson_24(),
    lesson_25(),
    lesson_26(),
    lesson_27(),
    lesson_28(),
]
