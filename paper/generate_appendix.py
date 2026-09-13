"""Generate complete listings and hashes from the actual submitted source files."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_files(root=ROOT):
    paths = [
        root / name
        for name in (
            "run_robot.py",
            "solve_questions.py",
            "start_robot.ps1",
            "check.py",
            "prepare_submission.py",
        )
    ]
    for directory in (
        "src/jammer_solver",
        "tools",
        "tests",
        "validation/baseline_v7",
        "paper",
    ):
        paths.extend(sorted((root / directory).glob("*.py")))
    return paths


def manifest(root=ROOT):
    return [
        dict(
            path=p.relative_to(root).as_posix(),
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            lines=len(p.read_text(encoding="utf-8").splitlines()),
        )
        for p in source_files(root)
    ]


def generate(root=ROOT):
    records = manifest(root)
    lines = [
        r"\section*{附录：完整程序清单}",
        "下列程序按提交时的实际文件逐字列出，未省略函数或实现。"
        "主运行策略为v8快速版r4；v7仅用于复算正文保留的历史对照，不能从比赛入口切换。"
        "支撑压缩包保留相同目录，文件散列见程序清单索引。",
        f"共{len(records)}个源文件、{sum(r['lines'] for r in records)}行。",
        r"\begingroup\linespread{1.0}\selectfont",
    ]
    for record in records:
        name = record["path"]
        lines += [
            r"\subsection*{\texttt{\detokenize{" + name + "}}}",
            f"文件行数：{record['lines']}。",
        ]
        if record["lines"]:
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
    (root / "paper/source_manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return records


if __name__ == "__main__":
    generate()
