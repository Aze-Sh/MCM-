# 离线工具

这些工具不连接官方接口，使用Python标准库。

| 文件 | 功能 |
|---|---|
| `validate.py` | 重跑或回放整理前冻结的30场v8快速版输入；核对全清、用时、请求指纹、源码哈希和完整光学链 |
| `benchmark.py` | 运行固定、边界、密集、验证及备用场景，保存模拟输入和完整协议记录 |
| `simulator.py` | 合成源和计费环境，源真值不传给求解器 |
| `verify_optical.py` | 连续覆盖、试探额度、完整事件预算和光学成功前缀审计 |
| `verification.py` | 证据回放和有限问题精确校准 |
| `compare_baseline.py` | 复算正文20场v7对照，检查是否重现历史时间 |
| `lower_bounds.py` | 不存在频道的必要操作成本下界 |

从仓库根目录运行：

```bash
python tools/validate.py --verify-only
python tools/validate.py --suite matched
python tools/validate.py --output runs/style-check
python tools/validate.py --verify-only --output runs/style-check
python tools/benchmark.py --suite stress --output runs/stress-check
```

Windows缺少SIGALRM时使用事件边界的协作式截止检查；单次长计算可能越过截止。POSIX保留硬计时器。模拟值是虚拟操作与移动时间，不能当作程序现实运行时间。
