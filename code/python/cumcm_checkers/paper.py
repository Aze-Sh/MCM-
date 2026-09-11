"""Objective paper-format checks; subjective writing quality is intentionally excluded."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from cumcm_py.types import CheckReport

from .reporting import config_value, issue, make_report, rule_sources


IDENTITY_PATTERNS = ("学校名称", "参赛队员", "指导教师", "作者姓名", "作者单位")
TEXT_SUFFIXES = {".tex", ".md", ".txt"}


def _paper_files(target: Path) -> list[Path]:
    preferred = [folder / name for folder in (target, target / "paper") for name in ("paper.pdf", "paper.tex", "paper.md", "main.pdf", "main.tex")]
    return [path for path in preferred if path.is_file()]


def run_check(target: str | Path, config: Mapping[str, Any]) -> CheckReport:
    target = Path(target)
    max_pages = int(config_value(config, "max_pages", 30))
    max_bytes = int(config_value(config, "max_bytes", 20 * 1024 * 1024))
    issues = []
    files = _paper_files(target)
    if not files:
        issues.append(issue("paper.missing", "未找到 paper/main 的 PDF、TeX 或 Markdown 文件。", path=str(target), source_ids=rule_sources(config)))
        return make_report("paper", issues, {"files_checked": 0})

    for path in files:
        relative = str(path.relative_to(target))
        if path.stat().st_size > max_bytes:
            issues.append(issue("paper.file_size", f"论文文件超过 {max_bytes} 字节限制。", path=relative, source_ids=rule_sources(config, "max_bytes")))

        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "\\tableofcontents" in text or re.search(r"(?m)^\s*#+\s*目录\s*$", text):
                issues.append(issue("paper.contents_page", "检测到目录命令或目录页标题。", path=relative, source_ids=rule_sources(config, "forbid_contents")))
            for pattern in IDENTITY_PATTERNS:
                if pattern in text:
                    issues.append(issue("paper.identity", f"检测到可能泄露身份的字段：{pattern}。", path=relative, source_ids=rule_sources(config, "anonymous")))
                    break

        if path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(path)
            except Exception as exc:  # corrupted PDFs must fail closed
                issues.append(issue("paper.invalid_pdf", f"PDF 无法解析：{exc}", path=relative, source_ids=rule_sources(config)))
                continue
            if len(reader.pages) > max_pages:
                issues.append(issue("paper.page_limit", f"正文共 {len(reader.pages)} 页，超过 {max_pages} 页限制。", path=relative, source_ids=rule_sources(config, "max_pages")))
            metadata = reader.metadata or {}
            author = str(metadata.get("/Author", "")).strip()
            if author:
                issues.append(issue("paper.identity", "PDF 作者元数据非空。", path=relative, source_ids=rule_sources(config, "anonymous")))
            extracted = "\n".join((page.extract_text() or "") for page in reader.pages[:3])
            if re.search(r"(?m)^\s*目\s*录\s*$", extracted):
                issues.append(issue("paper.contents_page", "PDF 前三页检测到目录标题。", path=relative, source_ids=rule_sources(config, "forbid_contents")))
            if any(pattern in extracted for pattern in IDENTITY_PATTERNS):
                issues.append(issue("paper.identity", "PDF 正文检测到可能的身份字段。", path=relative, source_ids=rule_sources(config, "anonymous")))

    return make_report("paper", issues, {"files_checked": len(files), "max_pages": max_pages, "max_bytes": max_bytes})
