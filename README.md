# MCM B题：最终算法 v8快速版（r4）

第三、四题默认使用 **`20260912-shared-service-r4`**。仓库只保留这一套运行策略；第一、二题的离线几何计算也保留。Python 3.10+，运行与测试仅使用标准库。

| 内容 | 位置 |
|---|---|
| 第三、四题启动 | [run_robot.py](run_robot.py)，Windows可用 [start_robot.ps1](start_robot.ps1) |
| 第一、二题计算 | [solve_questions.py](solve_questions.py) |
| 最终代码 | [src/jammer_solver](src/jammer_solver/) |
| 使用说明 | [docs/running.md](docs/running.md) |
| 算法及模块说明 | [docs/algorithm.md](docs/algorithm.md) |
| 本次代码风格整理 | [docs/code_style.md](docs/code_style.md) |
| 测试结果与局限 | [docs/validation.md](docs/validation.md) |
| 题目和附件 | [problem](problem/README.md) |
| 30页论文草稿与源码 | [paper](paper/README.md) |
| 安全与几何测试 | [tests](tests/)；统一入口 [check.py](check.py) |
| 离线模拟与核查工具 | [tools](tools/README.md) |
| 保留的验证数据 | [validation](validation/README.md) |

从仓库根目录先运行离线检查：

```bash
python check.py
python tools/validate.py --suite matched
```

这些命令不连接官方模拟器。完整30场验证使用 `python tools/validate.py`；新输出写入被Git忽略的 `runs/`，不会覆盖保留的数据。

连接你已打开并选好题号的**演练测试**：

```bash
python run_robot.py --problem 4 --run-kind rehearsal --case-code 当前案例编码 --robot-id 队号 --connect
```

已经默认运行v8快速版，无需再选 `--v8`。`--run-kind rehearsal`只记录类型，不能替你切换官方界面。未加 `--connect` 时不会连接。

整理后的目录、旧路径对应和删除范围见 [docs/layout.md](docs/layout.md)。旧版本及废弃实验已移出当前目录；本次整理没有重写Git历史。
