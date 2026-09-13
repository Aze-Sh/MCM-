# B题提交材料：v8快速版 r4

主运行算法固定为 **20260912-shared-service-r4**。本仓库只保留提交材料及复现论文所需的程序、数据和说明。缺少的真实数据仍为空，当前不能直接作为完成稿提交。

## 提交出口

- [论文PDF（含完整程序附录）](submission/论文.pdf)
- [支撑材料ZIP](submission/支撑材料.zip)
- [待补清单](submission/待补清单.md)
- [AI工具使用详情](AI工具使用详情.pdf)

正式上传使用 `submission/论文.pdf` 和 `submission/支撑材料.zip` 两个文件。不要把整个Git目录压缩上传。支撑材料ZIP已包含本仓库的必要源码、论文源文件、数据、文件散列清单及AI说明。

| 目录或文件 | 用途 |
|---|---|
| `submission/` | 可下载的论文、支撑压缩包和缺项检查 |
| `submission_inputs/` | 六次正式日志空目录、成绩表、待测实验与人工核验记录 |
| `paper/` | 可编辑论文、图表、完整程序附录索引与编译脚本 |
| `src/jammer_solver/` | 四问最终算法；比赛入口只运行v8快速版 |
| `run_robot.py`、`start_robot.ps1` | 第三、四题入口，队号必须运行时输入 |
| `solve_questions.py` | 第一、二题离线计算入口 |
| `validation/` | 论文实际使用的离线记录、固定输入及v7对照复算 |
| `tools/`、`tests/`、`check.py` | 复现实验和核查算法结论 |
| `docs/` | 必要的运行方法和算法说明 |

`validation/baseline_v7/`仅为正文20场对照提供复现依据，不能从比赛入口切换。其他旧版本、无关测试、参考论文、官方安装包及整理过程记录不在当前提交目录中。

## 克隆后怎样使用

Python 3.10+；算法、检查及打包只用标准库。仓库已固定文本换行，避免Windows克隆时改变源码及日志散列。先执行：

```bash
python check.py
python tools/validate.py --verify-only
python prepare_submission.py
```

这些命令不连接官方模拟器。最后一条生成支撑包并更新缺项清单；有空栏时仍允许生成草稿。使用 `python prepare_submission.py --check` 只检查，缺项或错误时返回退出码2。文件检查通过也不能替代人工理解、核实和提交操作。

成绩到位后，按 [待填材料说明](submission_inputs/README.md) 放入原始日志、填写CSV、更新正文及AI说明，再执行：

```bash
python paper/build.py
python prepare_submission.py
python prepare_submission.py --check
```

编译需TeX Live或MiKTeX的XeLaTeX、ctex、fvextra和Fandol字体。不修改论文或代码时可直接使用已经编译的PDF。代码变化后必须重编译，确保完整程序附录与源码一致。

## 匿名材料与原始日志

源程序不保存真实队号、密码、姓名或学校；连接时用 `--robot-id` 临时传入队号。运行输出只存在本地的 `runs/`，不会进入Git或支撑包。不要在论文、注释、文件名或人工核验记录中填写个人与学校信息。

官方 `.jlog` 的系统头可能含队号，且为签名/加密产物。按题目要求保留原文件名和字节，不自行删改；六份正式日志放入指定目录后由打包程序纳入支撑包。原始 `.jlog` 被Git忽略，不能从公开仓库恢复；请自行备份。演练原始日志不是本次待补的六份正式日志，不能替代。

`AI工具使用详情.pdf`如实保留AI参与记录，人工审核项尚未预填。填好后须重新编译、打包。自动匿名检查只能发现部分明显模式，最终还须人工检查PDF、元数据和新增材料。

生成提交MD5前备份最终PDF、ZIP。MD5生成后不要更改这两个文件；若内容或打包结果变化，需在规定时间内重新生成并提交MD5。
