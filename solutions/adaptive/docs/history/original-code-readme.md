# B题第七版代码

默认策略：`obligation-service-interception-v7`。Python 3.10+，运行代码仅用标准库。第七版尚无真实演练成绩。

## 人工运行

双击完整项目根目录“开始问题三演练.cmd”或“开始问题四演练.cmd”。模拟器由你自行打开，脚本显示案例和版本，只有你输入 CONNECT 后才连接。队号默认202612001024。日志保存在同一项目“运行结果”。详细步骤见根目录“第七版实测操作.md”。

Python参数 `--v6` 使用已演练第六版，`--v5`、`--v4`、`--v3`、`--baseline` 使用更早版本；选项互斥，默认第七版。PowerShell对应 `-V6`、`-V5`、`-V4`、`-V3`、`-Baseline`。旧版本快照在 `versions`。

不加 `--connect` 时程序不连接。异常后保留完整运行目录；若 `unresolved_request` 非空，上次动作结果未知，不要在同一会话盲目重启。尚不支持跨进程断点续跑。

## 前两问离线入口

`python solve_geometry.py --problem 1 input.json`：输入 `{"observations":[{"x":0,"y":0,"bearing_deg":30}],"epsilon_deg":1.005}`。计算前向楔形交、直径及同直径圆能否覆盖，不依靠人为大矩形。近退化未决不能当作数据矛盾。

`python solve_geometry.py --problem 2 input.json`：输入 `{"first":[0,0],"bearing_deg":30}`，可加 `current:[x,y]`。默认要求解析直径上界不超过163米，最小化移动距离，得到886.3434米；解析优化间隙小于0.0820米。可用 `target_diameter_m` 调整精度目标，过严且无可行种子时明确报错；显式给 `movement_m` 则在固定移动距离内优化角度。

`current` 仅选择较近对称侧；移动距离相对 `first` 定义。`query` 判定保证接收区域，`--output` 保存JSON。优化范围是解析带交判据，不是精确物理直径的全局极小极大。

## 新模块

- `service_graph.py`：全部当前已知源与剩余扫描，实际首测点入口、整个清除区域出口，指派松弛与模式动态规划。
- `probe_frontier.py`：整个候选区域的最近保证收缩测点；问题四另证全部相容方向可见。
- `interception.py`：主动信息位置及至多24个完整示向区间，两项成本界来自同一延续策略。
- `optical_v7.py`：条件首次成功分支、无用尝试省略及双预算重规划。
- `coverage_v7.py`：替换与删点分别保留名额，按进度释放证明预算。
- `adaptive_v7.py`：完成一个任务后重规划，记录服务成本和源等待。
- `q2_budget.py`：精度约束下最短移动的二维分支定界。
- `observed_state_analysis.py`：真实首批观测的只读政策界分析，运输对象禁止执行动作。
- `collect_results.py`：默认只将第七版正式记录写入正式表，`--strategy v6` 选择旧版；`--paper` 更新对应结果标记区。

新字段：`global_obligation_plans`、`service_receipts`、`regional_probe_count`、`active_information_reads`、`stationary_information_reads`、`source_waits`、`max_pending_sources`。服务记录中的后续段表示从真实结束位置出发可行，没有声称已经到达。旧 `route_episodes` 字段只为兼容保留。

动作上界仍为300／772。12项必要固定输入检查通过，记录在完整项目“测试记录/v7_必要离线验证_20260912”。旧版检查保留原记录，本次没有生成物理环境或连接模拟器。

已有四次真实演练属于第三、六版。第六版问题三、四分别清除13、14源，虚拟时间4889.664、8753.575秒；官方总源数未知，不能填100%清除率。本地耗时不代替官方程序运行时间，计划界下降不当作真实整局提速。
