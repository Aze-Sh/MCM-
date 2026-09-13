# 运行说明

Python 3.10或更高版本，无需安装第三方包。下列命令均在仓库根目录执行。第三、四题固定使用v8快速版（r4），第一、二题使用独立的离线几何入口。

## 离线检查与模拟

```bash
python check.py
python tools/validate.py --suite matched
```

第一条运行最终版相关的单元及集成测试；第二条复算四个固定案例，并核对与整理前v8快速版的请求和用时一致。完整30场验证用 `python tools/validate.py`，包含边界、密集、备用完成及全向、混合源输入。新日志保存在 `runs/validation-时间戳/`。

重新生成30场日志后，可只核查该目录：

```bash
python tools/validate.py --output runs/style-check
python tools/validate.py --verify-only --output runs/style-check
```

## Windows演练

1. 打开官方模拟器，在界面明确选择问题三或问题四的“演练测试”，等待接口就绪。
2. 在仓库根目录打开PowerShell。
3. 执行 `python run_robot.py --problem 4 --run-kind rehearsal --case-code 实际案例编码 --robot-id 队号 --connect`。问题三改为 `--problem 3`。

也可以运行：

```powershell
.\start_robot.ps1 -Problem 4 -RunKind rehearsal -CaseCode 实际案例编码 -RobotId 队号
```

该脚本会要求输入CONNECT，沿用原有的人工连接步骤。脚本不会启动模拟器、登录账号或选择测试模式。`--run-kind`只记录本地元数据，不能控制官方界面。

第三、四题默认就是 `20260912-shared-service-r4`。旧 `--v8`、`-V8`仍接受，作为兼容参数；v3～v7及baseline切换已经删除。原 `--v8-planning-seconds`、`--v8-extra-actions`兼容到现在的 `--planning-seconds`、`--extra-actions`，默认值仍为0.2和640。

## 每场记录保存在哪里

默认目录为 `runs/rehearsal_q4_时间戳/` 或 `runs/rehearsal_q3_时间戳/`，包含：

- `metadata.json`：题号、案例编码、测试类型、策略及 `policy_revision`。
- `actions.jsonl`：机器人侧明文动作、响应和证据记录。
- `summary.json`：正常完成后的总用时、清除与完成状态。

HTTP请求不自动重试。异常会直接抛出，已写入的日志保留，异常中止时不会生成 `summary.json`，也不会补发退出请求。算法和协议必要检查仍保留。

正常完成后的三份文件需要一起保存；官方导出的加密日志另行保留原文件名。不要把一次运行的摘要与另一次运行的动作文件混在一起。`runs/`不自动进入Git。

参数 `--output 路径`可以改变本地输出根目录，`--base-url`可以指定接口地址。不带 `--connect` 运行只检查参数，不发送请求。

## 第一、二题

```bash
python solve_questions.py --problem 1 输入.json --output 结果.json
python solve_questions.py --problem 2 输入.json --output 结果.json
```

第一题输入包含 `observations`，每条为 `x`、`y`、`bearing_deg`；可选 `epsilon_deg`。例如：

```json
{"observations":[{"x":0,"y":0,"bearing_deg":45},{"x":100,"y":0,"bearing_deg":135}]}
```

第二题输入包含 `first`、`bearing_deg`，以及给定的 `movement_m` 或希望达到的 `target_diameter_m`；可选 `current` 和 `query`。例如：

```json
{"first":[0,0],"bearing_deg":30,"movement_m":900}
```

这两个入口均不连接模拟器。第二题报告的是解析直径界下的计算结果及剩余间隙，不是物理问题精确最优的证明。
