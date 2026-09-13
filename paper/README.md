# 论文与图表

[论文PDF](../submission/论文.pdf)包含30页正文与参考文献，后附支撑材料文件列表和完整程序。正式数据及部分实验结果仍有空栏。

附录1以“文件名—说明”三线表列出材料；附录2收录问题一、二代码，附录3收录问题三、四代码，附录4收录图表与材料生成代码。共用模块只列一次，文件路径与支撑材料ZIP保持一致。正式日志尚未取得时列出待补目录，补入原始日志并重新编译后，文件列表会显示实际文件名。

| 文件 | 用途 |
|---|---|
| `main.tex` | 论文正文 |
| `appendix_sources.tex` | 支撑材料文件列表及完整程序附录 |
| `results.json`、`cases.json` | 论文已有计算结果及合成案例输入 |
| `figure-data.json` | 光学清除图使用的可行域和清除点 |
| `figures/` | 正文使用的PDF图 |
| `table_*.tex` | 离线结果和演练成绩表 |
| `formal_q3.tex`、`formal_q4.tex` | 从正式成绩CSV生成的表格 |
| `ai-usage.tex` | AI工具使用详情源文件 |
| `build.py`、`generate_appendix.py` | 编译论文并生成程序附录 |
| `make_tables.py`、`make_formal_tables.py` | 生成结果表格 |
| `make_figures.py` | 绘制论文图形 |

在仓库根目录运行`python paper/build.py`，需要XeLaTeX、ctex、fvextra和Fandol字体。图形已提供PDF，正常编译不需要绘图库。重新绘图执行`python paper/make_figures.py`，需要NumPy、Matplotlib和中文字体；可用`MCM_PAPER_FONT`指定字体文件。

Overleaf编译时上传完整支撑ZIP，主文件选`paper/main.tex`，编译器选XeLaTeX。程序附录会读取`src/`等目录，不能只上传`paper/`。

合成结果与官方演练、正式测试分开呈现。填写正式成绩CSV后重新编译，并根据实际结果补充摘要、分析和结论。
