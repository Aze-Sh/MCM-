# 第二套：自适应几何与任务规划（当前 v7）

本目录由原 `最新版/` 迁移而来，默认策略为 `obligation-service-interception-v7`。通过历史观测收缩候选区域，联合安排搜索与已知源清除，并在成本界允许时增加信息测量。

| 目录 / 文件 | 内容 |
| --- | --- |
| [python](python/README.md) | 算法、协议与命令行入口；含模块阅读顺序 |
| [tests](tests/) / [run_tests.py](run_tests.py) | 当前仓库实际包含的离线单元测试及统一入口 |
| [paper/main.tex](paper/main.tex) / [paper/main.pdf](paper/main.pdf) | 上传的 v7 论文源码与 PDF |
| [docs/running.md](docs/running.md) | 实际可用的运行、输出和汇总命令 |
| [docs/v7-evidence.md](docs/v7-evidence.md) | 上传的 v7 算法说明及证据范围说明 |
| [docs/history](docs/history/README.md) | v4～v6 文档、旧工程说明与未分类占位文件 |
| [results](results/README.md) | 后续运行记录与整理后的实验结果 |

从**仓库根目录**运行，Python 3.10+，无需第三方依赖：

```bash
python solutions/adaptive/run_tests.py
python solutions/adaptive/python/run_robot.py --help
```

运行脚本支持 `--v8`、`--v6`、`--v5`、`--v4`、`--v3` 和 `--baseline`，不指定时使用 v7。新增 v8 实验版实现证据账本、有限备用完成、事件前瞻和小问题精确校准；具体机制与成绩见 [v8 实现说明](docs/v8-implementation.md)。这里的 `--baseline` 是本方案内部的早期 midpoint 策略，与 `solutions/baseline/` 的第一套不同。

v7 通过继承复用了 v6、v5、v4、v3 的实现，因此 `solver.py`、`cooperative.py`、`adaptive.py`、`adaptive_v6.py` 仍是当前运行依赖。它们与 v7 模块保留在同一个 `python/` 目录；历史**说明文档**另放 `docs/history/`。

目前包含 62 项离线测试：34 项原有测试和 28 项 v8 几何、证据、校准及完整运行检查。它们不能替代 v7 专项测试；上传说明提及的 12 项 v7 检查及早期演练原始记录并未随代码上传。后续优先事项见[改进路线](../../docs/algorithm-development.md)。

编译论文时进入 `solutions/adaptive/paper/` 后运行两次 `xelatex main.tex`；需要本机的 XeLaTeX 与相应中文字体。
