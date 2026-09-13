"""生成论文中的完整程序附录。"""

from pathlib import Path as lj

root = lj(__file__).resolve().parents[1]


def shengcheng():
    files = [
        root / n
        for n in (
            "run_robot.py",
            "solve_questions.py",
            "start_robot.ps1",
            "prepare_submission.py",
        )
    ]
    for folder in ("src/jammer_solver", "paper"):
        files.extend(sorted((root / folder).glob("*.py")))
    lines = [
        r"\section*{附录：完整程序清单}",
        "以下列出求解、运行、绘图与论文编译所用的完整程序。支撑材料保留相同目录。",
        r"\begingroup\linespread{1.0}\selectfont",
    ]
    for p in files:
        name = p.relative_to(root).as_posix()
        lines.append(r"\subsection*{\texttt{\detokenize{" + name + "}}}")
        if p.stat().st_size:
            lines.append(
                r"\VerbatimInput[fontsize=\fontsize{8.5}{10.5}\selectfont,"
                r"breaklines=true,breakanywhere=true,numbers=left,numbersep=4pt,"
                r"xleftmargin=17pt,tabsize=4]{\RepoRoot/" + name + "}"
            )
        else:
            lines.append("该文件为空，用于标记Python包。")
    lines.append(r"\endgroup")
    (root / "paper/appendix_sources.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    shengcheng()
