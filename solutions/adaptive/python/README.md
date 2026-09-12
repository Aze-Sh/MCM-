# 第二套代码导航

本目录只放运行代码和启动脚本，测试位于上一级的 `tests/`。使用方法见[运行说明](../docs/running.md)。

建议先读 `run_robot.py → solver.py → cooperative.py → adaptive.py → adaptive_v6.py → adaptive_v7.py`，理解调用链，再按下表查看具体算法。

| 功能 | 模块 |
| --- | --- |
| 运行与接口 | `run_robot.py`、`start_robot.ps1`、`protocol.py` |
| 基础几何、环带收缩、历史候选区 | `geometry.py`、`strategy.py`、`posterior.py`、`refinement.py` |
| 位置、半径和发射方向的联合约束 | `evidence.py`、`joint_belief.py` |
| 搜索覆盖与后期调整 | `coverage.py`、`coverage_v7.py`、`tail_search.py` |
| 路径和全体任务排序 | `routing.py`、`planning.py`、`service_graph.py` |
| 观测、成本界与光学清除决策 | `decision.py`、`decision_v6.py`、`probe_frontier.py`、`interception.py`、`optical_v7.py` |
| 策略继承链 | `solver.py`（v3）、`cooperative.py`（v4）、`adaptive.py`（v5）、`adaptive_v6.py`、`adaptive_v7.py` |
| 问题一、二离线求解 | `solve_geometry.py`、`q2_design.py`、`q2_budget.py` |
| 结果整理与观测分析 | `collect_results.py`、`observed_state_analysis.py` |

现有模块使用同目录导入，暂不重命名这些 Python 文件。版本号表示实现演进或兼容入口；其中的早期模块不是可随意移除的备份。
