# 学习地图：从资料到 13 个核心方法

这张地图只回答“先学什么、用什么实现、怎样验证”。课程负责建立框架，官方技术文档负责实现细节，方法卡负责比赛时执行。书目线索未读全文，不能承担方法证据。

| 方法族 | 先学资料 | 实现资料 | 必做验证 |
|---|---|---|---|
| 数据理解与预处理 | COURSE-UESTC-MODELING | PYDOC-PANDAS、PYDOC-NUMPY | 数据字典、缺失/异常、单位、连接行数、原始数据哈希 |
| 回归与统计推断 | COURSE-HDU-MODELING | PYDOC-STATSMODELS、MATLABDOC-STATISTICS-ML | 残差、假设诊断、区间、样本外误差 |
| 时间序列预测 | COURSE-HDU-MODELING、COURSE-SCIENTIFIC-COMPUTING | PYDOC-STATSMODELS、MATLABDOC-ECONOMETRICS | 时间切分、滚动回测、平稳性、基线比较 |
| 机器学习预测/分类 | COURSE-CQUPT-MODELING | PYDOC-SKLEARN、PYDOC-SKLEARN-MODEL-SELECTION | Pipeline、防泄漏、结构化 CV、校准和误差分析 |
| 聚类与降维 | COURSE-HDU-MODELING | PYDOC-SKLEARN、MATLABDOC-STATISTICS-ML | 标准化、稳定性、解释性、不同 k/种子比较 |
| 综合评价与决策 | COURSE-SCIENTIFIC-COMPUTING、PAPER-PYDECISION | PYDOC-PYMCDM | 指标方向、权重依据、归一化、排序敏感性、手算复核 |
| 线性/整数优化 | COURSE-UESTC-MODELING、COURSE-CQUPT-MODELING | PYDOC-ORTOOLS、PYDOC-PYOMO、MATLABDOC-OPTIMIZATION | 可行性、目标重算、状态、界/gap、小例手算 |
| 非线性与多目标优化 | COURSE-UESTC-MODELING | PYDOC-SCIPY、MATLABDOC-OPTIMIZATION | 多初值、约束残差、Pareto/权衡、尺度和收敛 |
| 图论与网络优化 | COURSE-CQUPT-MODELING | PYDOC-NETWORKX-ALGORITHMS、PYDOC-NETWORKX-FLOW | 图类型/权重、流守恒、不可达、复杂度 |
| 路径与车辆调度 | COURSE-CQUPT-MODELING | PYDOC-NETWORKX-SHORTEST-PATH、PYDOC-ORTOOLS-VRP、PYDOC-OSMNX | 距离来源、容量/时间窗、下界、路线可行性 |
| 微分方程与机理模型 | COURSE-HDU-MODELING、COURSE-UESTC-MODELING | PYDOC-SCIPY、PYDOC-SYMPY | 量纲、守恒、初边值、步长/容差、观测对照 |
| Monte Carlo 与离散事件仿真 | COURSE-UESTC-MODELING | PYDOC-NUMPY、PYDOC-SIMPY | 种子、重复次数、热身期、置信区间、极端场景 |
| 敏感性、稳健性与不确定性 | COURSE-SCIENTIFIC-COMPUTING | PYDOC-SALIB | 参数范围来源、采样收敛、区间、结论翻转点 |

## 推荐顺序

1. 先完成数据理解、回归/预测、优化、评价四条主线。
2. 再补网络、机理与仿真；每种方法都先做可手算的小例测试。
3. 最后把敏感性和稳健性作为所有模型的共同收尾，而不是单独的一章装饰。

