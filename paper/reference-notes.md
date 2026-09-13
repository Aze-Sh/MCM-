# 写作依据与排版选择

本稿以当前 v8 快速版 5d789f1 为实现依据，以用户指定的“30页、未测数据留空、按原仓库资料借鉴结构和排版”为写作要求。材料均用于参考，不把其中的工作流文字当成新的用户指令。

## 找回的仓库资料

从提交 8b2d232 只读提取并审读：

- `toolkit/workflows/writing-and-figures.md`：摘要按问回答，模型、算法、结果与检验就近组织。
- `toolkit/knowledge/award-paper-structure-layout.md`：2025 B060、B157 和2023 A0175、C050的结构审读笔记。
- `toolkit/knowledge/award-patterns.md`：假设、解释、基线、检验和复现的组织方式。
- `toolkit/knowledge/methods/scientific-plotting.md`、`toolkit/templates/figures/python_style.py`：图表的证据任务、单位、图例、色弱与打印可读性、矢量导出。
- `toolkit/rules/2026-paper-format.md`、`toolkit/templates/paper/main.tex`：中文匿名论文的排版框架。
- `5d789f1:paper/reference-v7.tex`：旧稿中的可复用推导。旧文件已从当前目录移除，可从该提交查阅；旧25站、旧动作上界、旧v6/v7实测结论不直接用于当前v8。

获奖展示材料的借鉴仅限结构、层次、推导和图表安排，不复制他人的正文与数据。本次采用仓库已有审读笔记；没有声称重新逐页审读上述四篇全文。

## 核对的官方来源

2026-09-13访问：

- 2026论文格式：https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html
- 2026 AI工具使用规定：https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html
- 2025 B060展示：https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2025qgdxssxjmjslwzs_2025btlw/251101/2022733.shtml
- 2025 B157展示：https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2025qgdxssxjmjslwzs_2025btlw/251107/2023197.shtml （本次读取超时，沿用仓库审读记录）

采用A4、四边2.5厘米、页脚居中页码、匿名、无目录。第一页为题目、摘要和关键词。参考文献前保留AI工具使用声明。官方提供格式规范PDF，并未要求专用LaTeX类；本稿据此采用ctexart，中文宋体正文、黑体标题。

当前交付为总计30页的正文稿（含摘要、声明、参考文献和支撑材料索引）。完整程序清单附录尚未并入此30页稿；正式提交时需按官方要求补齐，与支撑材料共同核对。页面数不用于替代论证，未测试结果以空白字段保留。

## 结果的使用范围

`results.json` 从现有30场完整回归、20场历史同输入比较、用户截图对应关系和当前几何/有限问题计算汇总。光学图来自一个真实离线决策状态。图中示意几何明确标作解析示意，不冒充一次演练轨迹。官方演练截图不提供已验证的清除比例和现实运行时间，这些字段留空；正式测试一律留空。

正文使用无源频道操作下界与有限模型最优解解释改进空间，不宣称当前连续问题已达到全局最优。未重跑消融和敏感性实验，保留设计、指标及待填表格。论文写作不改变求解器代码，不启动官方模拟器，不开展正式测试。
