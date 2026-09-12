# 搜索策略探索

本目录保存搜索范式的独立分析与离线例子，当前不改变第二套默认策略。

```bash
python experiments/search-policy/check_indistinguishable_worlds.py --output experiments/search-policy/indistinguishable-worlds.json
```

脚本用现有本地模拟器构造两组观测记录：同样的合法动作与接口反馈，可以对应“10 个源全部清完”，也可以对应“实际有 11 个源，还漏了一个”。问题三的额外源超出接收距离；问题四的额外源在接收距离内，但朝向相反。

这是停止条件的反例，使用预设动作轨迹；它不是新的搜索策略，也不是算法性能测试。通用论证和改进方案见[跳出固定覆盖点的思考](../../docs/beyond-fixed-coverage.md)。
