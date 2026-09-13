# 论文计算依据

这里只保留正文实际使用的数据与复现依赖。

| 文件或目录 | 内容 |
|---|---|
| `expected-fast.json` | 30场完整源输入、噪声、参数、预期请求指纹和成本 |
| `current/` | 与当前r4核心源码对应的30场离线结果及完整事件记录 |
| `performance-comparison.json` | 正文20场同输入v7/v8比较，包含一场变慢的结果 |
| `baseline_v7/` | 上述v7对照所必需的依赖代码，仅通过离线模拟器调用 |
| `comparison_records/` | 重新离线复算的20场v7结果、日志和验证汇总；不是正式日志，也不是历史原始日志副本 |
| `questions-check.json` | 第一、二题样例输入、计算结果及一致性检查 |

复核30场现有记录：`python tools/validate.py --verify-only`。重新计算：`python tools/validate.py`，输出放本地`runs/`。

复算20场v7对照：`python tools/compare_baseline.py`。已复算的20场全部清除且虚拟时间与正文历史表一致。所有输入都为离线合成，不连接官方接口。

离线日志的`offline-v8`是固定占位标识，不是参赛队号。源真值只供离线环境和事后审计使用，求解器通过模拟通信接口获取观测。
