# 获奖导向但不神化的证据模式

## 怎样理解“为什么能得奖”

国赛官方评审标准关注假设合理性、建模创造性、结果正确性和表述清晰程度。官方讲评能说明命题意图与常见问题；官方展示论文能提供可观察正例；只有颁奖词或明确评语才可直接支持某队的官方评价。以下三类证据绝不混写：

具体样本的页码、正文/附录边界、图表布局和 2026 B 题当前稿差距见 [官方展示论文的结构与排版基准](award-paper-structure-layout.md)。

- 官方评价：组委会规则、专家讲评或颁奖词明示。
- 论文观察：能在官方展示论文具体页面看到，但不冒充评委意见。
- 分析推断：把跨年观察与官方评审标准连接成行动规则；它是仓库作者的综合判断。

## 跨年特征矩阵

| 维度 | 强答卷可观察信号 | 弱答卷常见信号 | 训练动作 |
|---|---|---|---|
| 问题理解 | 每问输入、状态、目标、约束、输出明确 | 复述题面后直接列算法 | 先写任务分解表 |
| 基线 | 简单模型先跑通且可比较 | 第一版就是复杂黑箱 | 设最小可用基线 |
| 模型递进 | 每次加复杂度都解决一个残差或新约束 | 堆叠算法无消融 | 记录“为什么升级” |
| 领域机制 | 量纲、守恒、几何、信息时序明确 | 只凭相关关系讲因果 | 增加机制检查表 |
| 数据处理 | 缺失、异常、单位、粒度有审计 | 一键标准化 | 固化 data-audit 输出 |
| 验证 | 回测、残差、可行性、敏感性齐全 | 只报拟合优度 | 每类模型设最低验证 |
| 可解释性 | 参数、约束与决策含义对应 | “模型效果好”无解释 | 写结果—决策翻译 |
| 创新 | 对任务痛点的必要改进 | 新奇算法名 | 创新必须配消融 |
| 写作 | 摘要量化回答每问，图表服务证据 | 公式/图堆积 | 用结论—证据结构 |
| 复现 | 结果表与代码一一对应 | 手工转录、随机性无种子 | 自动导出与清单 |

## 可执行结论

- 结论：评阅优先看合理假设、创造性、正确结果与清晰表达，复杂算法本身不是独立评分项。类型：官方评价；来源：[OFF-CUMCM-NATIONAL-JUDGING]
- 结论：先做可复算基线，再解释为什么升级模型，能减少“复杂但无法证明必要”的风险。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：几何与机理题的第一竞争力是坐标、单位、守恒和约束正确，而不是优化器名气。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：预测题若没有时间顺序回测，训练拟合再好也不能支持未来决策。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：优化题必须同时报告目标值、最大约束违约量和独立复算结果。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：概率与仿真题同时给解析/手算小例和蒙特卡洛置信区间，能更直接证明实现无误。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：数据题必须按主体或时间划分训练验证，随机拆行可能造成泄漏。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：所谓创新应能指出修复了哪个基线失败，并由消融、残差或压力测试证明增益。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：跨问复用统一状态、参数和符号，比每问单独换模型更容易形成闭环。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：摘要应对每问给出方法、关键结果、验证证据和决策含义，而非只列算法名。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：图表的价值在于暴露结构、比较基线、显示残差和验证稳健性，装饰性三维图不构成证据。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：模型局限应说明失效方向和影响范围，并给出可执行改进，不等于泛泛自我否定。类型：分析推断；来源：[OFF-CUMCM-NATIONAL-JUDGING, OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：官方展示身份只能证明论文被展示，不能证明网页顺序、算法或图表是获奖原因。类型：官方评价；来源：[OFF-CUMCM-2021-PAPERS, OFF-CUMCM-2022-PAPERS, OFF-CUMCM-2023-PAPERS, OFF-CUMCM-2024-PAPERS, OFF-CUMCM-2025-PAPERS]
- 结论：2023 多维学习页把赛题、展示论文、专家讲评和颁奖词分成不同入口，说明这些证据应分层使用。类型：论文观察；来源：[OFF-CUMCM-2023-MULTI-LEARNING]

## 反例提醒

- 随机森林、神经网络、遗传算法不是“高级”的同义词；没有基线、验证和任务必要性时，它们会降低可解释性。
- AHP/熵权/TOPSIS 不是所有评价题的默认答案；指标可替代、权重无证据或排序不稳定时应停用。
- 高拟合优度不代表预测好；最优目标值不代表可执行；统计显著不代表业务重要；相关不代表因果。
