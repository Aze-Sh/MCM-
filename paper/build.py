"""编译论文、完整程序附录和AI使用详情。"""

import argparse
from pathlib import Path as lj
import shutil
import subprocess

from generate_appendix import shengcheng
from make_formal_tables import generate as biaoge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="xelatex")
    parser.add_argument("--format", help="预编译的XeLaTeX格式文件")
    args = parser.parse_args()
    paper = lj(__file__).resolve().parent
    root = paper.parent
    build = paper / ".build"
    build.mkdir(exist_ok=True)
    (root / "submission").mkdir(exist_ok=True)
    engine = shutil.which(args.engine)
    if engine is None:
        raise SystemExit(
            "请安装含XeLaTeX、ctex、fvextra和Fandol字体的TeX Live或MiKTeX。"
        )
    biaoge(root)
    shengcheng()
    cmd = [engine]
    if args.format:
        cmd += [f"-fmt={lj(args.format).resolve()}", "-progname=xelatex"]
    cmd += ["-interaction=nonstopmode", "-halt-on-error", "-output-directory=.build"]
    for name, target in (
        ("main", "submission/论文.pdf"),
        ("ai-usage", "AI工具使用详情.pdf"),
    ):
        for _ in range(2):
            with (build / f"{name}-compile.log").open("w", encoding="utf-8") as output:
                subprocess.run(
                    cmd + [name + ".tex"],
                    cwd=paper,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
        shutil.copyfile(build / f"{name}.pdf", root / target)
        print(f"已生成 {target}")


if __name__ == "__main__":
    main()
