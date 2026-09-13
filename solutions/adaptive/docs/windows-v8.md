# Windows 本地 v8 模拟与演练

2026-09-13：当前提速版标识为 `20260912-shared-service-r4`，已保留 Windows 离线计时兼容修复。默认仍为 v7，连接入口必须显式加 `--v8`；PowerShell 启动脚本对应参数为 `-V8`。

在 PowerShell 进入仓库（Python 3.10+，第二套运行本身只使用标准库）：

```powershell
Set-Location 'C:\Users\37828\Desktop\国赛'
python solutions/adaptive/run_tests.py
```

## 离线模拟：不连接官方模拟器

每次使用独立输出目录，避免覆盖历史报告。

```powershell
$v8Output = 'solutions/adaptive/results/runs/offline-v8-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
python experiments/near-optimal/benchmark.py --algorithm v8 --suite matched --wall-limit 180 --output $v8Output
```

`matched` 为 4 局（问题三、四各两局）；将其换成 `stress` 可运行 8 局边界/密集压力案例。`fallback --extra-actions 0` 用于验证备用流程。

报告包含 `cleared_count`、`source_count`、`virtual_time_s`、`error`、`replay` 等字段。完整通过需清除数等于总数、error 为 null、重放 verified 为 true，并正常退出。合成结果不是官方成绩。

Windows 兼容修复：没有 SIGALRM 时，在动作/事件记录边界检查 wall-limit；单次长计算可能越过该期限，不能把它当成 Windows 强制终止计时器。POSIX 保留原 alarm。

## 官方演练：先在界面选择演练测试

1. 登录模拟器，选择对应问题的“演练测试”，等待显示“等待机器狗进入”。
2. 从当前界面复制案例编码。
3. 执行以下命令，按提示填写队号和案例编码：

```powershell
$v8Team = Read-Host '队号'
$v8Case = Read-Host '当前演练案例编码'
python solutions/adaptive/python/run_robot.py --v8 --problem 3 --run-kind rehearsal --robot-id $v8Team --case-code $v8Case --connect
```

问题四将 `--problem 3` 改为 `--problem 4`。不需要输入登录密码。程序不能识别界面是否为正式测试，运行前必须确认界面为演练；`--run-kind rehearsal` 仅记录类型，不能替你切换界面。

结果默认保存至 `solutions/adaptive/results/runs/rehearsal_q3_时间戳/`（或 q4），包含 metadata.json、actions.jsonl、summary.json。检查 error、unresolved_request、完成证据及退出状态；原始官方日志仍从模拟器按原名导出。

v8 为实验版，已取得同输入提速结果，但尚未在所有案例达到比 v7 至少省500秒。完整结果及未达标案例见 [v8 提速方法与同输入对比](v8-optimization.md)；合成结果不能替代截图对应的官方演练核验。
