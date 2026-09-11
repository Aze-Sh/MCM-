"""Locate paper artifacts and read the text actually checked by each stage."""

from pathlib import Path
import re

from pypdf import PdfReader


def paper_files(target: Path, stage: str = "draft") -> list[Path]:
    folders = (target, target / "paper")
    names = ("paper.pdf", "main.pdf") if stage == "submission" else (
        "paper.tex", "main.tex", "paper.md", "paper.txt", "paper.pdf", "main.pdf"
    )
    return [folder / name for folder in folders for name in names if (folder / name).is_file()]


def read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        if not text.strip():
            raise ValueError("PDF 没有可提取文字，请人工复核。")
        return text
    if path.suffix.lower() != ".tex":
        return path.read_text(encoding="utf-8", errors="replace")
    root = path.parent.resolve()

    def expand(source: Path, parents: tuple[Path, ...]) -> str:
        source = source.resolve()
        if not source.is_relative_to(root) or source in parents:
            raise ValueError("TeX 输入文件越出论文目录或出现循环引用。")
        text = re.sub(r"(?<!\\)%[^\n]*", "", source.read_text(encoding="utf-8", errors="replace"))

        def include(match: re.Match) -> str:
            child = root / match.group(1)
            if not child.suffix:
                child = child.with_suffix(".tex")
            return expand(child, (*parents, source))

        return re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", include, text)

    return expand(path, ())
