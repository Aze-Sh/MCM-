# v8快速版论文

[30页论文 PDF](main.pdf) · [完整源码包](manuscript-source.zip) · [可编辑 LaTeX](main.tex) · [待补清单](fill-in.md) · [AI工具使用详情](AI工具使用详情.pdf)

题目：**基于连续覆盖证书与观测共享调度的无线电干扰源自动定位与清除**。

本稿对应 `20260912-shared-service-r4`，以代码整理提交 `5d789f1` 为实现依据。采用此前仓库工作流、绘图规则和获奖论文结构审读记录组织，材料来源及具体借鉴范围见 [reference-notes.md](reference-notes.md)。这是总计30页的完整初稿，包含摘要、四问推导与求解、数据分析、检验、结论和参考文献；未测数据留空。完整程序清单附录尚未合并。

## 文件

| 文件 | 用途 |
|---|---|
| `main.tex`、`main.pdf` | 论文主稿，PDF恰好30页 |
| `table_q3.tex`、`table_q4.tex`、`table_practice.tex` | 三份数据表，由汇总记录生成 |
| `figures/` | 九幅图的矢量PDF和预览PNG |
| `results.json` | 离线30场、历史20组同输入对照、演练截图及计算结果 |
| `figure-data.json` | 实际光学链决策的精确源域、清除点和来源散列 |
| `ai-usage.tex`、`AI工具使用详情.pdf` | 两页支撑材料草稿，人工核验项待填 |
| `fill-in.md` | 未测数据、人工核验和定稿待办 |
| `outline.md`、`reference-notes.md` | 论证结构与写作依据 |
| `build.py`、`build-report.json` | 编译脚本及PDF页数、缺字、溢出、引用检查结果 |
| `make_tables.py`、`make_figures.py` | 表格及图形生成脚本 |
| `manuscript-source.zip` | 当前主稿、图表及支撑说明的可下载源码包 |

旧版论文已从当前目录移除；需要查阅历史内容时可通过Git历史恢复。

## 修改和编译

使用 TeX Live 或 MiKTeX 的 XeLaTeX，安装 `ctex`、`xeCJK` 和 Fandol 字体。仓库根目录运行：

```bash
python paper/build.py
```

也可把论文源码包上传 Overleaf，选 XeLaTeX、主文件 `main.tex`。源码包用于独立编译，重新计算图形时需放回本仓库。图和表已生成，正常编译不需要Python绘图库或模拟器。正文、公式、表格和图注均可直接编辑。

重新生成表格只需Python标准库：

```bash
python paper/make_tables.py
```

重新绘图还需要本仓库的 `src/jammer_solver`、NumPy和Matplotlib。脚本读取保存的光学决策快照，不要求本地存在被Git忽略的原始运行目录：

```bash
python paper/make_figures.py
```

Linux默认寻找Droid Sans Fallback，Windows寻找黑体；也可设置 `MCM_PAPER_FONT` 指向中文TrueType字体。模型与结果表已冻结为本稿使用范围，重新绘图不运行比赛测试。辅助绘图依赖不改变求解器仅使用标准库的要求。

构建脚本把中间文件放入 `.build/`，两遍编译解决交叉引用，检查缺字和越界；若安装了 `pdfinfo`，还会核对主稿30页、AI说明2页。编辑后溢页应调整实际内容及版面，不通过删除论证或缩到难读的字号满足页数。

## 数据边界

当前离线验证、截图演练与待测正式结果分别呈现；本次写作没有开启官方模拟器或进行正式测试。参赛队应按待补清单填写真实结果和人工核验情况，再依赛事要求补齐源程序附录。
