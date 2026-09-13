# 最终版目录与清理记录

整理日期：2026-09-13。用户明确选定已推送的v8快速版（提交8b2d232，内部标识r4）作为最终代码，本次据此清理工作目录、统一命名，并把默认启动策略改为v8快速版。

## 当前目录

```text
MCM-/
├── run_robot.py          # Q3/Q4唯一启动入口
├── start_robot.ps1       # Windows启动
├── solve_questions.py    # Q1/Q2离线计算
├── check.py              # 最终版测试入口
├── src/jammer_solver/    # 当前算法、协议及必要依赖
├── tools/                # 离线模拟、校准下界和回放工具
├── tests/                # 当前算法、协议、入口和几何检查
├── validation/           # 最终30场验证与必要历史摘要
├── problem/              # 原题、附件、提取文本和接口要求
├── paper/                # 当前v8快速版的30页论文、图表与源码
└── docs/                 # 运行、算法、验证和本说明
```

新运行输出统一进入 `runs/`，由Git忽略。输入材料只放 `problem/`，论文只放 `paper/`，运行实现只放 `src/jammer_solver/`。文件名按职责使用小写英文和下划线；版本记录在 `policy_revision`，不再复制“最新版”“提速版”等平行代码目录。

## 主要路径变更

| 原位置 | 新位置 |
|---|---|
| `solutions/adaptive/python/run_robot.py` | 根目录 `run_robot.py`；命令行实现已合入根目录入口 |
| `near_optimal/suanfa.py` | `src/jammer_solver/solver.py` |
| `near_optimal/geometry.py` | `src/jammer_solver/exact_geometry.py` |
| `near_optimal/jiaozhun.py` | `tools/verification.py` |
| 旧 `coverage.py`、`planning.py`、`service_graph.py` 等 | 只提取当前依赖，现已合入 `src/jammer_solver/solver.py` |
| `solutions/adaptive/python/solve_geometry.py` | 根目录 `solve_questions.py`；实现为 `src/jammer_solver/questions.py` |
| `experiments/near-optimal/`中的有效工具 | `tools/` |
| 多轮实验输出 | 最终依据集中到 `validation/`，新输出为 `runs/` |
| `problem/raw/`和`problem/processed/` | 题目及附件直接放 `problem/`，提取稿放 `problem/text/` |

完整对应关系见 [file-mapping.json](../validation/file-mapping.json)。旧路径已移除，应更新自己的启动快捷方式。旧版本选择参数已删除；`--v8`、`-V8`和两项v8预算参数作为兼容别名保留，均运行同一v8快速版。

## 删除与保留范围

从工作目录移除了：未选用的本地r5改动和对应新试验、第一套旧求解器及发布副本、第二套v3～v7策略入口及不再依赖的实现、无关通用建模工具库、旧版本专项测试、废弃研究原型、失败试验、重复历史模拟输出、过期运行说明和开发讨论记录。

保留了：用户选定的v8快速版算法和实际依赖、第一二题离线求解、题目原件和附件、已有论文草稿、当前安全与几何测试、30场完整回归记录、原性能比较及十份官方附件的安全元数据。题目及论文文件的字节哈希见 [materials-sha256.json](../validation/materials-sha256.json)。

旧代码里并非所有辅助文件都是可直接删除的旧版本。本次单独提取了v8快速版使用的指派函数、路径排序和清除投影，从而解除对旧策略整条继承链的依赖。主算法、几何和协议均以用户选定的Git提交8b2d232为准，没有加入r5策略；第一二题也保留原计算方法。

## 整理前备份

已在仓库外建立：

`../backups/mcm-before-final-layout-20260913-025419.tar.gz`

SHA256：`6471523a8675053d71a6cf056532cc5cdb284cb8a3090f850b1a0eaf51873d99`。

归档含清理前代码、当时未提交的r5改动、原有材料及历史实验数据；不包含Git对象、本地虚拟环境和缓存。这个备份位于当前工作机，**不会随仓库推送到GitHub**。如需恢复，解压到另一个目录后取回需要的文件，避免直接覆盖最终版。

Git历史保留，未做历史清除或强制推送。`.venv/`是本机被忽略的环境，本次保留；工作树变小不等于Git历史和本地环境同步变小。

## 验证

整理前后已核对109个顶层函数/类的抽象语法树保持一致；另一个Q2函数只去掉无用局部变量绑定，保留原参数验证调用。主包文件的导入路径按新目录调整，详情见 [migration.json](../validation/migration.json)。

第一、二题各一个相同输入在新旧入口输出完全一致，记录为 [questions-check.json](../validation/questions-check.json)。上一次目录整理时的48项测试通过，包含默认启动v8快速版、无连接标志不创建HTTP接口、请求重试、几何、全清证据、预算和离线超时等检查。

Q3/Q4以整理前选定v8快速版的30场输入做整场回归，结果及每条协议请求指纹核查见 [validation.md](validation.md)。这些检查用于确认整理没有改变选定算法，不能当成一次新的算法提速。

## 清理后的规模

不含Git历史、本地虚拟环境及缓存，文件由1869个减少到122个，内容体积由约133.97 MiB减少到8.94 MiB。只保留当前30场完整验证，不再把多轮失败与重复试验留在主目录。统计见 [cleanup-summary.json](../validation/cleanup-summary.json)。

## 本次代码风格合并

按用户提供的文档，运行包进一步由16个文件合并为5个；启动流程合入根入口，离线回放移至工具目录，运行代码改为无类、无注释、无类型标注的过程式写法。接口取消捕获与重试，保留证明和协议必要检查。最新文件映射、行为变化和验证记录见 [code_style.md](code_style.md)。上文的109个函数核对、48项测试和122个文件统计属于此前目录整理的历史记录。
