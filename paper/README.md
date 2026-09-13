# 论文源文件与完整程序附录

[论文PDF](../submission/论文.pdf) · [支撑材料](../submission/支撑材料.zip) · [缺项清单](../submission/待补清单.md) · [AI使用详情](../AI工具使用详情.pdf)

论文采用v8快速版r4，正文、参考文献和材料索引共30页。其后附全部使用的程序源文件，附录按实际代码自动生成，不截断函数，也不省略旧版对照所需的依赖。

| 文件 | 用途 |
|---|---|
| `main.tex` | 论文正文和附录入口 |
| `appendix_sources.tex`、`source_manifest.json` | 完整程序清单及文件行数、SHA256索引 |
| `figures/` | 正文使用的九幅矢量PDF图 |
| `results.json`、`figure-data.json` | 正文数据汇总、光学决策快照及来源 |
| `table_*.tex` | 已有离线与演练数据表 |
| `formal_q3.tex`、`formal_q4.tex` | 从正式CSV生成，未测仍为空 |
| `ai-usage.tex` | AI详情源稿，人工核验待实际填写 |
| `build.py`、`build-report.json` | 编译脚本，页数、缺字、溢出、引用、源文件一致性核查 |
| `generate_appendix.py`、`make_formal_tables.py` | 自动同步完整源码与正式数据表 |
| `make_tables.py`、`make_figures.py` | 重生成既有表格及图形 |

仓库根目录执行`python paper/build.py`，需要XeLaTeX、ctex、fvextra、Fandol字体。脚本编译两遍并检查正文页数不超过30。总PDF包含完整代码附录，因此总页数超过30。

支撑ZIP保留完整相对目录，解压后同样可以运行上述命令。使用Overleaf时上传支撑ZIP，主文件选`paper/main.tex`，编译器选XeLaTeX；完整代码附录依赖ZIP内的`src/`等目录，不能只上传这一文件夹。

重新绘图需NumPy和Matplotlib；中文字体使用Droid Sans Fallback或黑体，也可设置`MCM_PAPER_FONT`指定TrueType字体。正常论文编译直接使用已生成的PDF图，不需要绘图库。重生成图形执行`python paper/make_figures.py`，不会进行比赛测试。

未测项见`submission_inputs/README.md`。现有30场合成验证、20场v7/v8对照与10行演练截图结果分开呈现，不能互相代替。原始正式日志尚缺，人工核验并未自动宣布完成。
