# v8 代码整理与阅读说明

整理日期：2026-09-12。范围是当前 v8 和启动入口，依据提供的《代码去ai化方法.docx》调整写法。第一套、v3～v7 的算法实现以及通用建模工具库没有重构。

本文记录首先完成的代码组织与表达方式整理。随后根据“比v7至少省500秒”的要求又修改了算法；当前性能改动与实测差距见 [v8 提速记录](v8-optimization.md)。下文“逐请求一致”、69个函数和189项测试是纯整理阶段的历史快照，不是对当前优化版行为或参数不变的声明。原有验证文件及哈希保持原样。

## 1. 文件怎么找

| 文件 | 内容 | 建议先读 |
| --- | --- | --- |
| [`run_robot.py`](../python/run_robot.py) | 读取命令行参数、选择版本、保存运行结果 | `main` |
| [`suanfa.py`](../python/near_optimal/suanfa.py) | v8 的状态、观测处理、决策与执行 | `xin_zhuangtai`、`yunxing` |
| [`geometry.py`](../python/near_optimal/geometry.py) | 多边形裁剪、距离界、方向约束、连续覆盖核查 | `apply_bearing`、`coverage_certificate` |
| [`jiaozhun.py`](../python/near_optimal/jiaozhun.py) | 有限世界精确校准、日志回放 | `calibrate`、`replay` |
| [`start_robot.ps1`](../python/start_robot.ps1) | Windows 启动脚本，增加 `-V8` 选项 | 参数区和末尾启动命令 |

`near_optimal/__init__.py` 是空的包入口。因此该目录共有 4 个 Python 文件，实际内容集中在 3 个文件中。

原来的 `state.py`、`planner.py`、`search_plan.py`、`solver.py` 合并进 `suanfa.py`；`finite_policy.py` 和 `replay.py` 合并进 `jiaozhun.py`。仓库内的实验和测试入口已同步修改。外部脚本如果直接导入过旧模块，需要参照下表调整。

| 原写法 | 当前写法 |
| --- | --- |
| `SolverV8(io, problem)` | `zhuangtai = v8.xin_zhuangtai(io, problem)` |
| `solver.run()` | `v8.yunxing(zhuangtai)` |
| `solver.summary()` | `v8.huizong(zhuangtai)` |
| `solver.exit()` | `v8.tuichu(zhuangtai)` |
| `Ledger(problem, extra_actions)` | `v8.xin_jilu(problem, extra_actions)` |
| `Source.found(origin, bearing)` | `v8.xin_yuan(origin, bearing)` |
| `ledger.observe(...)` | `v8.gengxin_jilu(jilu, ...)` |
| 源对象的方向、near、阴性和光学失败更新 | `v8.gengxin_yuan(yuan, q, kind, ...)` |
| `near_optimal.finite_policy.calibrate` | `near_optimal.jiaozhun.calibrate` |
| `near_optimal.replay.replay` | `near_optimal.jiaozhun.replay` |

这里的 `v8` 对应 `from near_optimal import suanfa as v8`。旧的自定义 `EvidenceError` 类也已合并为 `RuntimeError`；仓库测试已适配。

## 2. 主流程怎样读

1. `xin_zhuangtai` 创建状态字典，包括当前位置、频道、时间、观测记录、规划参数和备用路线。
2. `yunxing` 进入运行循环。每轮先判断 `quanbu_qingchu`，再看是否应该切换到 `beiyong_qingchu`。
3. `gengxin_luxian` 根据已取得的观测调整未来搜索路线。路线变短需要通过覆盖核查，但计划中的测量不会算作已取得的证据。
4. `xuan_dongzuo` 选择处理哪个源或哪个搜索点；`yuan_dongzuo` 比较一次 RF 前瞻和完整光学接续。
5. `yusuan_jiancha` 核查做完候选动作后是否仍能完成备用流程。
6. `zhixing_shijian` 执行完整事件，`zhixing` 负责实际请求和计费核对，`gengxin_jilu` 更新频道记录和剩余任务。
7. 全清有依据后才退出，`huizong` 产生原有格式的摘要。

例如 Q4 的某频道已被发现，却在新测点收到 `no_signal`：`gengxin_jilu` 先记录这次阴性；`zhixing_shijian` 随后完成同一事件中的第二次测量。第二次仍是阴性时，`shuang_yinxing` 核查真实的正、负观测，再决定能否缩小可行域。单次阴性不会直接变成“这里没有源”。

常见变量的含义：`zhuangtai` 是整场状态，`jilu` 是频道观测账本，`yuan` 是单个干扰源的可行域，`weizhi` / `dangqian` 是位置，`jihua` 是规划配置，`luxian` 是搜索路线，`huifu` 是接口响应，`jiekou` 是接口对象。

字典字段和日志字段保留现有英文名称，便于核对归档结果：

| 数据 | 字段 | 含义 |
| --- | --- | --- |
| `zhuangtai` | `position`、`channel`、`virtual` | 当前位置、接收频道、虚拟时间 |
| `zhuangtai` | `ledger`、`planner`、`search_plan` | 观测账本、事件规划参数、后续搜索安排 |
| `jilu` | `channels`、`extra`、`receipts` | 20 个频道的记录、剩余试探额度、任务减少记录 |
| 单个频道 | `status` | `unknown` 未知、`found` 已发现、`cleared` 已清除、`absent` 已排除 |
| 单个频道 | `pending`、`source` | 未完成的固定搜索责任，以及已发现源的状态 |
| `yuan` | `polygon`、`cells`、`points` | 外包可行域、剩余光学责任块、对应清除点 |
| `yuan` | `positives`、`negatives` | 实际取得的正、负 RF 测点 |

## 3. 文档中的写法要求如何落实

统计范围为 `near_optimal/` 下全部 Python 文件，函数数包含嵌套函数：

| 项目 | 整理前 | 整理后 |
| --- | ---: | ---: |
| Python 文件 | 8 | 4 |
| 自定义类 | 8 | 0 |
| 函数 | 82 | 69 |
| `#` 注释 | 35 | 0 |
| 类型标注 | 23 | 0 |
| 文档字符串 | 26 | 0 |

状态改为字典，处理过程改为普通函数；相近的观测更新合并到一个函数，重复的光学链费用计算合并。主流程和入口的部分变量改为拼音。几何中的 `dot`、`cross`、`hull` 等常见名称保留，避免数学表达变得难认。

v8 和 Python 入口内不放注释、文档字符串或类型标注，解释放在本文及算法说明。多行字典、分支和表达式按可读性展开，所以物理行数没有作为压缩目标。

没有增加运行依赖。保留标准库 `fractions.Fraction` 和有界缓存：前者支撑边界的精确判定，后者避免重复计算昂贵的几何证明。已有协议、路线和连续位置优化模块继续复用。

“不要有错误处理”没有机械地应用到所有检查。v8 主体已经没有 `try/except`，规划超时用返回值表示；仍保留非法参数、证据矛盾、错误计费和未确认请求等会影响正确性的检查。Python 启动入口也保留异常记录与退出处理，避免运行中断后丢失证据或重复发出未确认动作。该取舍服从此前“确保找全”和文档“在保证能够完成任务的前提下”的要求。

必要的几何函数、执行函数和回放函数没有强行展开成一段长脚本。日志和测试也保留，它们承担复核运行结果的作用。

## 4. 重构验证

对照基准为提交 `6a682bc`。机器可读记录见 [`validation.json`](../../../experiments/near-optimal/results/refactor-20260912/validation.json)，包含代码哈希、案例哈希、每例对照、历史回放和检查结果。

- 全仓原有测试：**189 项通过**，其中自适应方案 62、基线方案 40、工具库 87。基线绘图仍有原有的中文字体缺失警告。
- **14 份历史动作日志全部回放通过**，计费、任务减少、双阴性和全清依据保持兼容；归档文件未被覆盖。
- **4 个完整合成案例逐请求一致**，共 934 条请求，包含进入和退出。两个版本均实际清除全部源；比较时只移除响应中的真实时间戳。
- **3 个有限世界校准结果完全一致**，精确值仍为 34、37、49 s。
- Python 入口的帮助、默认 v7 和显式 v8 的不连接模式通过；默认 v7 与 v8 还分别通过用合成接口替代 HTTP 的完整入口检查，包含结果文件和退出状态。
- v8、Python 入口与适配后的 v8 测试通过格式和未定义名称检查。

逐请求对照时，两侧仅冻结局部规划模块的 `perf_counter`，让有限候选完整展开；执行截止时间仍使用真实 `monotonic`。这样可以排除机器负载导致的候选截断差异。四例虚拟耗时如下，两个版本完全相同：

| 案例 | 源数 | 请求数（含进入、退出） | 虚拟耗时 / s |
| --- | ---: | ---: | ---: |
| Q3 / 20260911 | 16 | 119 | 4092.430 |
| Q3 / 20260912 | 10 | 142 | 3560.665 |
| Q4 / 20260911 | 16 | 201 | 7381.410 |
| Q4 / 20260912 | 10 | 472 | 11121.078 |

上述固定计时仅用于行为对照，没有加入运行代码。正常运行仍有原来的每次规划时间预算，因此不能据此声称每台机器上的每次路线都相同，也不能把表中耗时当作一次算法提速。有限案例一致不能替代对所有连续场景的数学证明。

本次没有运行官方模拟器，也没有进行正式测试。Windows 的 `-V8` 参数已接入，但当前 Linux 环境没有 PowerShell，尚未实机执行该脚本。

## 5. 本地复核命令

在仓库根目录执行：

```bash
python scripts/check_repository.py --suite all
python solutions/adaptive/python/run_robot.py --v8 --problem 4 --case-code YOUR_CASE_CODE
python experiments/near-optimal/benchmark.py --suite calibration --output /tmp/v8-calibration-check
PYTHONPATH=solutions/adaptive/python python -m near_optimal.jiaozhun experiments/near-optimal/results/validation-20260912/v8-q4-seed20260911.jsonl
```

第二条命令没有 `--connect`，只检查启动参数并退出。默认算法仍为 v7，选择 v8 仍需 `--v8`；Windows 脚本对应 `-V8`。纯整理阶段没有修改算法预算；当前优化版的覆盖预算、布局、定位和任务顺序调整见提速记录。
