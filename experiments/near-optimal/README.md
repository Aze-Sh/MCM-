# v8 离线评价与精确小问题校准

[`benchmark.py`](benchmark.py) 只调用仓库内的合成模拟器，不连接官方接口。运行策略只取得接口回调；源真值只在这里用于生成场景、核对全清与保存评价输入。

从仓库根目录运行：

```bash
python experiments/near-optimal/benchmark.py --suite matched
python experiments/near-optimal/benchmark.py --suite stress
python experiments/near-optimal/benchmark.py --suite fallback --extra-actions 0
python experiments/near-optimal/benchmark.py --suite calibration
```

可加 `--algorithm v7` 在相同输入上重新运行旧版。默认输出到 `results/`；最初归档位于 `results/validation-20260912/`，本轮优化位于 `results/optimization-20260912/`。其中 `round4/current-*` 是当前r4整合版，根目录 `current-*`、`round2/current-*` 和 `round3/current-*` 保留前几轮快照；`trial*` 是开发过程中的独立变体，不能按案例择优拼接。当前固定对照的 v7 已重跑；所有结果均为离线合成测试。

- `matched`：此前四个固定世界，保留完全相同的源位置、频道、半径、朝向和误差种子。
- `validation`：前轮生成的8个固定验证世界，Q3/Q4各含10、12、14、16源；本轮已用它们比较候选。Q4全部为定向源，是扩展压力对照。
- `fresh`：冻结r3后新增的8个世界，源数同上，Q4包含全向和定向源；本轮规则冻结后重新验证，未据此调参；该批上轮已经查看，不是封存测试集。
- `stress`：Q3/Q4、10/16 源、靠近域边界/密集分布的 8 个组合。半径固定 1000 m，Q4 全部朝外发射，方向误差固定为坐标决定的 ±1° 后再舍入。
- `fallback`：强制承诺完整备用流程，检查零试探额度、光学失败处理、实际全清和费用上界。
- `calibration`：有限世界与动作上的精确 Bellman 值，以及多种完整接续下不同前瞻深度的上界。源数在每个小问题内固定且已知，不能把这里的最优值当成连续原题的下界。

每个完整 v8 案例还会重新播放证据日志，核查费用、势函数下降、双阴性证明和停止依据。JSON 记录输入真值、模拟器噪声、参数、错误、实际耗时及动作日志 SHA-256。当前v8结果另记策略版本和策略文件哈希。`verify_optical.py` 进一步核查新光学链的全区域覆盖、预算、实际执行点序及费用。对同一输入的后续运行会受规划墙钟预算与机器负载影响，应保存独立输出目录。

完整解释和本次匹配结果见 [v8 实现说明](../../solutions/adaptive/docs/v8-implementation.md)。

当前校准和回放入口合并到 `near_optimal/jiaozhun.py`。回放归档日志可运行：

```bash
PYTHONPATH=solutions/adaptive/python python -m near_optimal.jiaozhun experiments/near-optimal/results/validation-20260912/v8-q4-seed20260911.jsonl
```

过程式重构的验证结果单独记在 [v8 代码整理说明](../../solutions/adaptive/docs/v8-style-refactor.md)，归档成绩保持原样。

当前算法解释、完整性能对比及未达目标见 [v8 提速记录](../../solutions/adaptive/docs/v8-optimization.md)。复核本轮保存的30场全清记录、14份历史日志和同输入对比：

```bash
python experiments/near-optimal/verify_results.py --results experiments/near-optimal/results/optimization-20260912/round4 --require-current-policy
```
