"""生成支撑材料文件列表和完整程序附录。"""

from pathlib import Path as lj

root = lj(__file__).resolve().parents[1]


def shengcheng():
    groups = [
        (
            "问题一、二代码",
            [
                ("solve_questions.py", "问题一、二的JSON输入输出入口"),
                (
                    "src/jammer_solver/questions.py",
                    "问题一交会区域计算与问题二第二测点选择",
                ),
            ],
        ),
        (
            "问题三、四代码",
            [
                ("run_robot.py", "问题三、四的模拟器运行入口"),
                ("start_robot.ps1", "Windows交互启动脚本"),
                ("src/jammer_solver/solver.py", "多源搜索、定位、调度与清除算法"),
                ("src/jammer_solver/exact_geometry.py", "可行域与光学覆盖所用几何运算"),
                ("src/jammer_solver/protocol.py", "模拟器通信与运行记录"),
                ("src/jammer_solver/__init__.py", "Python包标记文件，内容为空"),
            ],
        ),
        (
            "图表与材料生成代码",
            [
                ("paper/make_tables.py", "生成离线结果和演练成绩表"),
                ("paper/make_formal_tables.py", "从正式成绩CSV生成论文表格"),
                ("paper/make_figures.py", "绘制论文图形"),
                ("paper/generate_appendix.py", "生成材料文件列表及完整程序附录"),
                ("paper/build.py", "编译论文与AI工具使用详情"),
                ("prepare_submission.py", "打包支撑材料并列出待补事项"),
            ],
        ),
    ]
    rows = [
        ("AI工具使用详情.pdf", "AI工具使用环节、用途与人工核验待填记录"),
        ("paper/results.json", "已有离线计算结果及演练成绩汇总"),
        (
            "submission_inputs/practice_results.csv",
            "问题三、四演练成绩；未取得的字段留空",
        ),
        (
            "submission_inputs/formal_results.csv",
            "问题三、四各三次正式成绩表，待实测填写",
        ),
        ("paper/cases.json", "30场离线合成案例输入"),
        ("paper/figure-data.json", "光学清除图的可行域和清除点数据"),
    ]
    for _, files in groups:
        rows.extend(files)
    rows += [
        ("README.md", "材料目录及使用说明"),
        ("docs/running.md", "安装、运行与模拟测试操作说明"),
        ("docs/algorithm.md", "算法流程与模块说明"),
        ("paper/", "论文源文件、表格、AI说明及编译说明"),
        ("paper/figures/", "正文使用的8幅PDF图形"),
        ("submission_inputs/README.md", "待补结果的字段和存放规则"),
        ("submission_inputs/ablation/", "消融实验材料预留目录，待补"),
        ("submission_inputs/sensitivity/", "敏感性实验材料预留目录，待补"),
        (
            "submission_inputs/practice_details/",
            "演练清除数量与现实运行时间明细，待补",
        ),
    ]
    for q in (3, 4):
        pending = []
        for n in (1, 2, 3):
            folder = root / f"submission_inputs/formal/q{q}/test_{n}"
            logs = sorted(folder.glob("*.jlog"))
            if logs:
                rows.extend(
                    (p.relative_to(root).as_posix(), f"问题{q}第{n}次正式测试原始日志")
                    for p in logs
                )
            else:
                pending.append(str(n))
        if pending:
            rows.append(
                (
                    f"submission_inputs/formal/q{q}/",
                    f"问题{q}第{'、'.join(pending)}次正式日志待补",
                )
            )
    lines = [
        r"\begin{center}{\Large\heiti\bfseries 附\quad 录}\end{center}",
        r"\section*{附录1：支撑材料文件列表}",
        "表中路径相对于支撑材料压缩包根目录，以“/”结尾的项为目录。正式日志待实测补入，保留原始文件名及内容；共用程序只在对应附录列出一次。",
        r"\begingroup\small\linespread{1.0}\selectfont",
        r"\setlength{\tabcolsep}{5pt}\renewcommand{\arraystretch}{1.18}",
        r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{.49\linewidth}>{\raggedright\arraybackslash}p{\dimexpr.51\linewidth-10pt\relax}@{}}",
        r"\caption{支撑材料文件列表}\label{tab:materials}\\",
        r"\toprule[1pt]\multicolumn{1}{c}{文件名} & \multicolumn{1}{c}{说明}\\\midrule\endfirsthead",
        r"\multicolumn{2}{c}{表\thetable\quad 支撑材料文件列表（续）}\\",
        r"\toprule[1pt]\multicolumn{1}{c}{文件名} & \multicolumn{1}{c}{说明}\\\midrule\endhead",
        r"\bottomrule[1pt]\endfoot",
    ]
    for name, desc in rows:
        cell = (
            r"\path{" + name + "}"
            if name.isascii()
            else r"\texttt{\detokenize{" + name + "}}"
        )
        lines.append(cell + " & " + desc + r"\\")
    lines += [r"\end{longtable}", r"\endgroup"]
    for n, (title, files) in enumerate(groups, 2):
        lines += [r"\clearpage", rf"\section*{{附录{n}：{title}}}"]
        for name, desc in files:
            lines.append(r"\subsection*{\texttt{\detokenize{" + name + "}}}")
            lines.append(desc + "。")
            if (root / name).stat().st_size:
                lines.append(
                    r"\begingroup\linespread{1.0}\selectfont"
                    r"\VerbatimInput[fontsize=\fontsize{8.5}{10.5}\selectfont,"
                    r"breaklines=true,breakanywhere=true,numbers=left,numbersep=4pt,"
                    r"xleftmargin=17pt,tabsize=4]{\RepoRoot/" + name + r"}\endgroup"
                )
    (root / "paper/appendix_sources.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    shengcheng()
