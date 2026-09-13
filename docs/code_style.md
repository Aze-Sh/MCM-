# v8 快速版代码整理

本次按《代码去ai化方法.docx》整理当前运行代码。算法基准仍为提交 `8b2d232` 的 `20260912-shared-service-r4`，整理前的完整仓库提交为 `fae3c1a`。

## 具体调整

运行包从16个Python文件合并为5个，其中 `__init__.py` 为空包标记。加上两个根目录启动文件，运行代码由18个文件变为7个，函数定义由126个减少到115个，源码字节数由106076减少到93990。统计包含从运行包移至离线工具的回放代码；不包含测试与离线模拟器。拆开原来一行挤在一起的多条语句后，物理行数略有增加。

- 用字典保存接口状态，用函数完成请求和日志写入，移除运行代码中的5个类。
- 合并布局、路线、指派和清除辅助函数，移除未使用的旧Q4布局、Q2报告入口及参数验证专用对象。
- 启动流程直接放在 `run_robot.py`，第一、二题计算集中到 `questions.py`，回放和有限问题校准移至 `tools/verification.py`。
- 使用 `canshu`、`mulu`、`xinxi`、`jiekou`、`qingqiu`、`beixuan`、`jiashuo` 等拼音名称；协议字段和已有日志字段保留，便于继续核查历史数据。
- 运行代码没有注释、文档字符串、类型标注或 `try/except`。说明放在Markdown文档中。只使用Python标准库；精确几何继续使用有理数，缓存继续避免重复计算。

## 异常流程的变化

HTTP请求只发送一次，网络异常直接由Python抛出；入口不再捕获异常、补发退出请求或生成异常摘要。文件通过 `with` 关闭，已写入的元数据、动作意图及响应日志保留。`summary.json` 在正常完成后生成。

保留接受状态、时间与预算、证据一致性、连续覆盖以及全清条件的检查。这些是决定能否执行动作、接受观测和宣告完成的算法约束，违反时直接停止。文档中的“不要有错误处理”在这里落实为移除捕获、重试和补救流程，**没有删去这些正确性检查**。

离线模拟器和测试中的类、异常断言、超时机制继续服务于独立验证，不属于交付的机器人运行流程。

## 文件对应

| 原文件 | 现位置 |
|---|---|
| `cli.py` | 根目录 `run_robot.py` |
| `search_design.py`、`route_planning.py`、`assignment.py`、`clearance.py`、`clear_route.py` | `src/jammer_solver/solver.py` |
| `bearing_geometry.py`、`geometry.py`、`q2_design.py`、`q2_budget.py` | 所需计算合入 `src/jammer_solver/questions.py`；Q3/Q4距离函数合入 `solver.py` |
| `verification.py` | `tools/verification.py` |
| `protocol.py` | 原位置，改为过程式接口 |
| `exact_geometry.py` | 原位置，保留精确几何计算 |

## 核验方法

运行 `python check.py` 检查计算、完成证据、默认入口和模拟HTTP交互。整场对照使用：

```bash
python tools/validate.py --output runs/style-check
python tools/validate.py --verify-only --output runs/style-check
```

核对30场固定输入的完整请求指纹、操作次数和虚拟时间，并独立回放证据、检查光学链的连续覆盖。接口测试使用内存中的模拟响应，不连接官方模拟器。

本次结果见 [style-refactor.json](../validation/style-refactor.json)。旧 [recorded](../validation/recorded/) 是上一次目录整理的历史记录，源码哈希对应当时的提交；本次不覆盖其哈希或原结论。
