from pathlib import Path
import json

PAPER = Path(__file__).resolve().parent
data = json.loads((PAPER / "results.json").read_text(encoding="utf-8"))


def case_label(case):
    name = case["name"]
    count = case["source_count"]
    suite = case["suite"]
    if suite == "matched":
        return "M" + ("1" if "20260911" in name else "2")
    if suite == "validation":
        return f"V{count}"
    if suite == "fresh":
        return f"F{count}"
    if suite == "fallback":
        return f"R{count}"
    return ("B" if "boundary" in name else "C") + str(count)


for problem in (3, 4):
    rows = [r for r in data["cases"] if r["name"].startswith(f"q{problem}-")]
    if problem == 3:
        header = r"案例 & 源数 & 总时间/s & 平均时间/(s/源) & $M$ & $K_f$"
        specs = "crrrrr"
    else:
        header = r"案例 & 全向/定向 & 总时间/s & 平均时间/(s/源) & $K_f$"
        specs = "ccrrr"
    lines = [
        r"\begin{table}[H]\centering\caption{问题"
        + str(problem)
        + r"的15场离线固定输入结果}\label{tab:q"
        + str(problem)
        + "}",
        r"\small\setlength{\tabcolsep}{7pt}",
        r"\begin{tabular}{" + specs + r"}\toprule",
        header + r"\\\midrule",
    ]
    for case in rows:
        n, t, counts = case["source_count"], case["virtual_time_s"], case["counts"]
        failure = counts["clear"] - counts["successful_clear"]
        if problem == 3:
            line = f"{case_label(case)} & {n} & {t:.2f} & {t / n:.2f} & {counts['measure']} & {failure}"
        else:
            d = case["directional_count"]
            line = (
                f"{case_label(case)} & {n - d}/{d} & {t:.2f} & {t / n:.2f} & {failure}"
            )
        lines.append(line + r"\\")
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    (PAPER / f"table_q{problem}.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

lines = [
    r"\begin{table}[H]\centering\caption{十次演练截图的成绩汇总}\label{tab:practice}",
    r"\small\setlength{\tabcolsep}{4pt}\begin{tabular}{cccrr}\toprule",
    r"题号/次序 & 案例编码 & 报告全向/定向 & 报告个数 & 总时间（约）/s\\\midrule",
]
for problem in (3, 4):
    for i, row in enumerate(
        [r for r in data["practice"] if r["problem"] == problem], 1
    ):
        lines.append(
            f"{problem}/{i} & {row['case_code']} & "
            f"{row['reported_omnidirectional']}/{row['reported_directional']} & "
            f"{row['reported_source_count']} & {row['reported_virtual_time_s']}" + r"\\"
        )
lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
(PAPER / "table_practice.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
