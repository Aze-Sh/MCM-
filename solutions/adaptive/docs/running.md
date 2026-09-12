# 第二套运行说明

以下命令从**仓库根目录**执行。Python 3.10+，算法本身仅用标准库。

## 离线检查

```bash
python solutions/adaptive/run_tests.py
python solutions/adaptive/python/run_robot.py --help
python solutions/adaptive/python/run_robot.py --problem 3 --case-code OFFLINE-CHECK
```

最后一条未传 `--connect`，只检查参数并退出。默认版本为 v7；`--v6`、`--v5`、`--v4`、`--v3`、`--baseline` 互斥。这里的 `--baseline` 是第二套内部的早期策略。

## 问题三、四演练

在 Windows PowerShell 中，手动打开对应题号的模拟器演练模块，取得案例编码后运行：

```powershell
.\solutions\adaptive\python\start_robot.ps1 -Problem 3 -RunKind rehearsal -RobotId "你的队号"
```

脚本会询问案例编码、显示题号与策略，输入 `CONNECT` 后才向本地模拟器发送动作。问题四将 `-Problem 3` 改为 `-Problem 4`。如需指定 Python，可添加 `-Python "C:\Python312\python.exe"`；默认使用 PATH 中的 `python`，不再依赖上传者的个人运行时路径。

也可以直接使用 Python 入口；将以下占位内容替换为实际信息：

```bash
python solutions/adaptive/python/run_robot.py --problem 3 --run-kind rehearsal --case-code "界面案例编码" --robot-id "你的队号" --connect
```

默认接口为 `http://127.0.0.1:2026`。正式测试由 `--run-kind formal` 区分，应与模拟器当前模块一致。

每次输出位于 `solutions/adaptive/results/runs/rehearsal_q3_时间戳/` 等独立目录，包含动作、元数据和总结。`--output` 可覆盖默认输出根目录。异常时保留完整记录；若 `unresolved_request` 非空，程序尚未确定上次动作结果，目前不支持跨进程断点续跑。

## 前两问离线几何

准备自己的输入 JSON，例如问题一：

```json
{"observations":[{"x":0,"y":0,"bearing_deg":30}],"epsilon_deg":1.005}
```

```bash
python solutions/adaptive/python/solve_geometry.py --problem 1 input.json
```

单条观测通常不足以形成有界定位区；实际求解应填写题目给出的全部观测。

问题二输入示例为 `{"first":[0,0],"bearing_deg":30}`：

```bash
python solutions/adaptive/python/solve_geometry.py --problem 2 input.json
```

可设置 `target_diameter_m`（默认 163）或显式给 `movement_m`。精度目标约束的是代码使用的解析直径上界；`current` 只用于选择较近的对称侧，移动距离相对 `first` 计算。

## 整理实际结果

把 `实际运行目录` 替换为已经存在、包含完整记录的目录：

```bash
python solutions/adaptive/python/collect_results.py "实际运行目录" --output solutions/adaptive/results/summary --strategy v7
```

可一次传多个运行目录。脚本写出汇总 JSON、Markdown 和正式结果表；正式表只采用所选版本且 `run_kind=formal` 的记录。更新论文时可额外指定 `--paper solutions/adaptive/paper/main.tex`。

官方总源数、运行时间等补充值应来自模拟器记录，存为该次运行目录的 `official_observation.json`，字段包括 `source_total_from_simulator`、`official_program_runtime_s`、`official_log_filename`；未取得的值留空，不根据代码估计补写。

原上传说明里的 `.cmd` 双击入口、旧版本快照与部分测试记录未包含在仓库中，当前使用以上实际存在的入口。
