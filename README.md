# B题：干扰源搜索、定位与清除

第一、二问采用离线几何计算；第三、四问通过模拟器接口执行搜索、测向和清除。程序使用Python 3.10及以上版本，求解和打包无需第三方库。

## 运行

先在官方模拟器中选择对应题目的**演练测试**，等待接口就绪，然后在仓库根目录执行：

```bash
python run_robot.py --problem 4 --run-kind rehearsal --case-code 实际案例编码 --robot-id 队号 --connect
```

问题三把`--problem 4`改为`--problem 3`。Windows也可使用`start_robot.ps1`。第一、二问的输入格式及运行方法见[运行说明](docs/running.md)。

## 文件用途

| 文件或目录 | 用途 |
|---|---|
| `src/jammer_solver/` | 四问求解、几何计算和接口通信 |
| `run_robot.py`、`start_robot.ps1` | 第三、四问启动入口 |
| `solve_questions.py` | 第一、二问JSON输入输出入口 |
| `docs/` | 运行方法与算法说明 |
| `paper/` | 论文源文件、结果数据、图表和完整程序附录 |
| `submission_inputs/` | 正式日志目录、成绩表及待测数据空位 |
| `submission/` | 论文PDF、支撑材料ZIP及待补清单 |
| `prepare_submission.py` | 按提交目录生成支撑材料ZIP |
| `AI工具使用详情.pdf` | AI辅助范围及待填写的实际使用记录 |

## 提交材料

使用[论文PDF](submission/论文.pdf)和[支撑材料ZIP](submission/支撑材料.zip)。当前正式结果及部分实验数据尚未补齐，位置见[待填材料说明](submission_inputs/README.md)，不要把空栏当作已完成结果。

修改论文、代码或正式成绩表后，执行：

```bash
python paper/build.py
python prepare_submission.py
```

论文编译需要XeLaTeX、ctex、fvextra和Fandol字体。支撑材料含完整源码、论文源文件和AI使用详情；不要把整个Git目录压缩上传。

队号只在运行时输入，源码中不保存队号、密码或个人学校信息。本地运行记录在`runs/`，不进入Git和支撑包。官方原始`.jlog`放入`submission_inputs/formal/`的对应目录，保留原文件名和内容；这些日志不推送到公开仓库，需自行备份。加入正式日志后的支撑包用于比赛提交。

生成MD5前备份最终PDF和ZIP；生成后保持文件不变，改动后须重新生成并提交MD5。
