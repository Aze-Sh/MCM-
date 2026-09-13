# 运行说明

Python 3.10或更高版本，无需安装第三方包。下列命令均在仓库根目录执行。第一、二题使用离线几何入口，第三、四题连接模拟器接口。

## Windows演练

1. 打开官方模拟器，在界面明确选择问题三或问题四的“演练测试”，等待接口就绪。
2. 在仓库根目录打开PowerShell。
3. 执行 `python run_robot.py --problem 4 --run-kind rehearsal --case-code 实际案例编码 --robot-id 队号 --connect`。问题三改为 `--problem 3`。

也可以运行：

```powershell
.\start_robot.ps1 -Problem 4 -RunKind rehearsal -CaseCode 实际案例编码 -RobotId 队号
```

该脚本会要求输入CONNECT，确认后开始发送动作。脚本不会启动模拟器、登录账号或选择测试模式。`--run-kind`只记录本地元数据，不能控制官方界面。

规划时间`--planning-seconds`默认为0.2秒，可选动作额度`--extra-actions`默认为640次。

## 每场记录保存在哪里

默认目录为 `runs/rehearsal_q4_时间戳/` 或 `runs/rehearsal_q3_时间戳/`，包含：

- `metadata.json`：题号、案例编码、测试类型和接口地址。
- `actions.jsonl`：机器人侧动作、响应与清除进度。
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

队号没有默认值，连接时必须通过`--robot-id`或PowerShell提示输入。提交源码不要写入队号或密码。`runs/`为本地原始记录，可能包含队号，不进入支撑包；正式`.jlog`的放置方法见`submission_inputs/README.md`。
