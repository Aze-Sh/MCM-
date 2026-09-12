# v8 离线评价与精确小问题校准

[`benchmark.py`](benchmark.py) 只调用仓库内的合成模拟器，不连接官方接口。运行策略只取得接口回调；源真值只在这里用于生成场景、核对全清与保存评价输入。

从仓库根目录运行：

```bash
python experiments/near-optimal/benchmark.py --suite matched
python experiments/near-optimal/benchmark.py --suite stress
python experiments/near-optimal/benchmark.py --suite fallback --extra-actions 0
python experiments/near-optimal/benchmark.py --suite calibration
```

可加 `--algorithm v7` 在相同输入上重新运行旧版。默认输出到 `results/`；归档验证记录位于 `results/validation-20260912/`，开发中的中间成绩位于 `results/development/`。本次匹配对照中的 v7 耗时取自已有保存结果，不是新的官方或重新演练成绩。

- `matched`：此前四个固定世界，保留完全相同的源位置、频道、半径、朝向和误差种子。
- `stress`：Q3/Q4、10/16 源、靠近域边界/密集分布的 8 个组合。半径固定 1000 m，Q4 全部朝外发射，方向误差固定为坐标决定的 ±1° 后再舍入。
- `fallback`：强制承诺完整备用流程，检查零试探额度、光学失败处理、实际全清和费用上界。
- `calibration`：有限世界与动作上的精确 Bellman 值，以及多种完整接续下不同前瞻深度的上界。源数在每个小问题内固定且已知，不能把这里的最优值当成连续原题的下界。

每个完整 v8 案例还会重新播放证据日志，核查费用、势函数下降、双阴性证明和停止依据。JSON 记录输入真值、模拟器噪声、参数、错误、实际耗时及动作日志 SHA-256。对同一输入的后续运行会受规划墙钟预算与机器负载影响，应保存独立输出目录。

完整解释和本次匹配结果见 [v8 实现说明](../../solutions/adaptive/docs/v8-implementation.md)。
