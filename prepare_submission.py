"""打包源程序、论文材料和正式日志。"""

import csv
from pathlib import Path as lj
import zipfile

root = lj(__file__).resolve().parent


def main():
    output = root / "submission"
    output.mkdir(exist_ok=True)
    files = [
        root / n
        for n in (
            "README.md",
            "run_robot.py",
            "solve_questions.py",
            "start_robot.ps1",
            "prepare_submission.py",
            "AI工具使用详情.pdf",
        )
    ]
    for folder in ("src", "docs", "paper", "submission_inputs"):
        files.extend(
            p
            for p in sorted((root / folder).rglob("*"))
            if p.is_file()
            and not p.is_symlink()
            and not any(
                x.startswith(".") or x == "__pycache__"
                for x in p.relative_to(root).parts
            )
            and p.suffix in (".py", ".md", ".json", ".csv", ".tex", ".pdf", ".jlog")
        )
    files.extend((root / "submission_inputs").rglob(".gitkeep"))
    with zipfile.ZipFile(
        output / "支撑材料.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for p in sorted(files):
            item = zipfile.ZipInfo(
                p.relative_to(root).as_posix(), date_time=(2026, 1, 1, 0, 0, 0)
            )
            item.external_attr = 0o100644 << 16
            archive.writestr(
                item,
                p.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    pending = []
    with (root / "submission_inputs/formal_results.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for row in csv.DictReader(f):
            name = f"问题{row['problem']}第{row['test']}次"
            folder = (
                root / f"submission_inputs/formal/q{row['problem']}/test_{row['test']}"
            )
            if not any(folder.glob("*.jlog")):
                pending.append(f"{name}：补入原始正式日志")
            if any(
                not row.get(k, "").strip()
                for k in (
                    "case_code",
                    "cleared_count",
                    "virtual_time_s",
                    "real_time_s",
                    "log_filename",
                )
            ):
                pending.append(f"{name}：补填正式成绩表")
    lines = ["# 待补材料", "", "打包完成不表示缺少的数据已经补齐。", ""]
    lines += [f"- [ ] {x}" for x in pending]
    lines += [
        "- [ ] 按实际结果补充正文、图表中的空栏。",
        "- [ ] 据实填写AI工具使用详情中的待填内容。",
        "- [ ] 保留官方日志的原始文件名和原始内容。",
        "",
        "修改论文或源码后，先编译论文，再重新打包。",
        "生成提交MD5前备份最终PDF和ZIP；生成后保持这两个文件不变。",
    ]
    (output / "待补清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已生成 submission/支撑材料.zip 和 submission/待补清单.md")


if __name__ == "__main__":
    main()
