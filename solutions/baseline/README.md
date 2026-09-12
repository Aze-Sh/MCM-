# 第一套：覆盖扫描基线（当前 v3）

本目录由原 `contest/2026/` 迁移而来。算法采用覆盖扫描、历史方向约束、逐步定位及清除；第二套是另一个独立方案，见 [adaptive](../adaptive/README.md)。

| 目录 / 文件 | 内容 |
| --- | --- |
| [python/main.py](python/main.py) | 本地模拟、演练、正式测试入口 |
| [python/b_strategy.py](python/b_strategy.py) | 第一套核心策略 |
| [python/b_simulation.py](python/b_simulation.py) | 本地合成模拟器 |
| [tests](tests/) | 几何、协议、策略、命令行及分析测试 |
| [paper](paper/) / [figures](figures/) | 论文源码及配图 |
| [output](output/) | 已有分析和实验报告；格式检查报告位于 `output/checks/` |
| [logs](logs/) | 动作日志和官方演练原始文件 |
| [releases/formal-v3-20260911](releases/formal-v3-20260911/) | 冻结代码和原 SHA-256 校验清单 |
| [result-manifest.yaml](result-manifest.yaml) | 实验、输出与参数的对应关系 |
| [docs/progress-history.md](docs/progress-history.md) | 迁移前的详细开发记录 |
| [docs/preflight.md](docs/preflight.md) | 第一套历史正式测试准备清单 |
| `AI工具使用详情.*` | 该方案的 AI 使用记录及导出文件 |

题目原件统一在 [problem](../../problem/README.md)，不再分别复制到每套算法中。

从**仓库根目录**运行：

```bash
python -m pip install -r solutions/baseline/python/requirements.txt pytest
python solutions/baseline/python/main.py simulate --cases 3 --seed 20260911
python scripts/check_repository.py --suite baseline
```

模拟结果自动写入本目录 `output/` 的独立文件。演练入口另有 `practice --problem 3 --confirm-practice --robot-id 队号`；具体使用前阅读[接口说明](../../problem/simulator-interface.md)。

论文编译的工作目录为 `solutions/baseline/paper/`，图形相对路径保留。冻结发布目录、已有日志与结果中的历史路径是当时记录，不会随本次迁移回写；原校验清单仍可用于核验文件内容。
