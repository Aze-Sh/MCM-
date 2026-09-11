"""Check the official 2026 declaration and supporting AI-use report."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cumcm_py.types import CheckReport

from .documents import paper_files, read_document
from .reporting import config_value, issue, make_report, rule_sources


FIELDS = ("工具与模型", "使用目的", "主要提示方式", "使用过程", "采纳情况", "人工修改", "人工核验")
PLACEHOLDERS = re.compile(r"待填写|待确认|待核验|TODO|TBD|\[填写", re.IGNORECASE)
USED_PHRASE = "本参赛队在竞赛过程中使用了AI工具"
UNUSED_PHRASE = "本参赛队在竞赛过程中未使用任何AI工具"


def _field_values(text: str) -> dict[str, str]:
    lines = [re.sub(r"[ \t\u3000]+", "", line) for line in text.splitlines()]
    out: dict[str, str] = {}
    table_headers: list[str] | None = None
    for line in lines:
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if any(field in item for field in FIELDS for item in cells):
                table_headers = [next((field for field in FIELDS if field in item), "") for item in cells]
                continue
            if table_headers and len(cells) == len(table_headers):
                for field, value in zip(table_headers, cells):
                    if field:
                        out[field] = value.strip("：: ")
                table_headers = None
                continue
        for field in FIELDS:
            if line.startswith(field):
                out[field] = line[len(field):].lstrip("：:|* ").strip()
                break
    return out


def _relative(path: Path, target: Path) -> str:
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def run_check(target: str | Path, config: Mapping[str, Any]) -> CheckReport:
    target = Path(target)
    # Preserve the original library contract for callers that do not opt into
    # the 2026 stage-aware checks. The CLI exposes --stage explicitly.
    if "stage" not in config and not (target / "paper.md").is_file():
        candidates = [target / "AI工具使用详情.md", target / "ai-usage.md", target / "AI-use.md"]
        path = next((item for item in candidates if item.is_file()), None)
        if path is None:
            return make_report("ai_usage", [issue("ai.missing_log", "缺少 AI 工具使用详情文件。", path=str(target), source_ids=rule_sources(config))])
        text = path.read_text(encoding="utf-8", errors="replace")
        fields = ("工具与模型", "使用目的", "关键提示词", "关键回复", "采纳情况", "人工修改")
        missing = [issue("ai.missing_field", f"AI 使用记录缺少字段：{field}。", path=path.name, source_ids=rule_sources(config)) for field in fields if field not in text]
        return make_report("ai_usage", missing, {"required_fields": list(fields), "log": path.name})
    stage = str(config.get("stage", "draft"))
    source_ids = rule_sources(config) or ("OFF-CUMCM-2026-AI-RULES",)
    problems = []

    def add(code: str, message: str, path: Path | None = None) -> None:
        problems.append(issue(code, message, path=_relative(path, target) if path else None, source_ids=source_ids))

    papers = paper_files(target, stage)
    if not papers:
        add("ai.paper_pdf_missing" if stage == "submission" else "ai.declaration_missing", "提交检查需要论文 PDF。" if stage == "submission" else "找不到论文及 AI 工具使用声明。")
        return make_report("ai_usage", problems, {"stage": stage, "ai_used": None})
    paper = papers[0]
    try:
        text = read_document(paper)
    except Exception as exc:
        add("ai.invalid_pdf" if paper.suffix.lower() == ".pdf" else "ai.unreadable_paper", f"无法读取论文：{exc}", paper)
        return make_report("ai_usage", problems, {"stage": stage, "ai_used": None})

    compact = re.sub(r"\s+", "", text)
    marker = compact.find("AI工具使用声明")
    ref_match = re.search(r"参考文献|\\begin\{thebibliography\}|\\bibliography\{", compact)
    if marker < 0:
        declaration = ""
    else:
        end = ref_match.start() if ref_match and ref_match.start() > marker else len(compact)
        declaration = compact[marker:end]
    used = USED_PHRASE in declaration
    unused = UNUSED_PHRASE in declaration
    if marker < 0 or not (used or unused):
        add("ai.declaration_missing", "需在参考文献前设置 AI工具使用声明，并明确已使用或未使用。", paper)
    if ref_match is None or (marker >= 0 and marker > ref_match.start()):
        add("ai.declaration_order", "无法确认 AI 工具使用声明位于参考文献之前。", paper)
    if used and unused:
        add("ai.declaration_conflict", "已使用与未使用声明同时存在，必须据实选择。", paper)
    if PLACEHOLDERS.search(declaration):
        add("ai.placeholder", "AI 声明仍含待填写或待确认内容。", paper)
    purpose_match = re.search(r"主要用于([^，。；}]+)", declaration)
    purpose = purpose_match.group(1).strip() if purpose_match else ""
    if used and (not purpose or PLACEHOLDERS.search(purpose)):
        add("ai.purpose_missing" if not purpose else "ai.placeholder", "已使用声明必须说明简要用途。" if not purpose else "AI 声明用途仍含占位内容。", paper)

    details_names = ("AI工具使用详情.pdf",) if stage == "submission" else ("AI工具使用详情.md", "ai-usage.md", "AI-use.md", "AI工具使用详情.pdf")
    details = [folder / name for folder in (target, target / "support") for name in details_names if (folder / name).is_file()]
    if unused and not used:
        evidence_names = ("AI工具使用详情.md", "ai-usage.md", "AI-use.md", "AI工具使用详情.pdf")
        evidence = [folder / name for folder in (target, target / "support") for name in evidence_names if (folder / name).is_file()]
        for path in evidence:
            try:
                values = _field_values(read_document(path))
            except Exception as exc:
                add("ai.invalid_pdf", f"无法核实现有 AI 材料：{exc}", path)
                continue
            tool = values.get("工具与模型", "")
            if tool and not PLACEHOLDERS.search(tool) and tool not in {"无", "未使用", "不适用"}:
                add("ai.declaration_conflict", "未使用声明与已填写的 AI 使用材料矛盾，请人工核实。", path)
        return make_report("ai_usage", problems, {"stage": stage, "ai_used": False, "paper": _relative(paper, target)})

    if used:
        if not details:
            add("ai.details_pdf_missing" if stage == "submission" else "ai.missing_log", "缺少 AI工具使用详情.pdf。" if stage == "submission" else "缺少 AI 使用详情编辑稿。", paper)
        else:
            path = details[0]
            try:
                detail_text = read_document(path)
            except Exception as exc:
                add("ai.invalid_pdf" if path.suffix.lower() == ".pdf" else "ai.unreadable_log", f"AI 使用详情无法读取：{exc}", path)
            else:
                values = _field_values(detail_text)
                polishing_only = purpose in {"仅语言润色", "仅限语言润色"} and values.get("使用目的", "") in {"仅语言润色", "仅限语言润色"}
                required = FIELDS[:4] if polishing_only else FIELDS
                for field in required:
                    if field not in values:
                        add("ai.missing_field", f"详情缺少字段：{field}。", path)
                    elif not values[field]:
                        add("ai.empty_field", f"详情字段未填写：{field}。", path)
                    elif PLACEHOLDERS.search(values[field]):
                        add("ai.placeholder", f"详情字段仍含占位内容：{field}。", path)

    return make_report("ai_usage", problems, {"stage": stage, "ai_used": used, "paper": _relative(paper, target), "manual_review_required": True})
