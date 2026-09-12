"""Shared paper-scale plotting style with reproducible multi-format export."""

from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager


COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#7B61A8",
    "gray": "#666666",
}


def setup_paper_style() -> str:
    preferred = [
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}
    chosen = next((name for name in preferred if name in available), "DejaVu Sans")
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [chosen, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.figsize": (6.4, 4.2),
            "figure.dpi": 120,
            "savefig.dpi": 400,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "lines.linewidth": 1.4,
            "axes.linewidth": 0.9,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "cumcm-2026-b",
        }
    )
    return chosen


def export_figure(fig, output_stem: str | Path, *, include_svg: bool = True) -> list[Path]:
    """Export a figure as 400-DPI PNG and vector PDF/SVG."""
    stem = Path(output_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [stem.with_suffix(".png"), stem.with_suffix(".pdf")]
    fig.savefig(outputs[0], dpi=400, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(outputs[1], format="pdf", bbox_inches="tight", pad_inches=0.03)
    if include_svg:
        outputs.append(stem.with_suffix(".svg"))
        fig.savefig(outputs[-1], format="svg", bbox_inches="tight", pad_inches=0.03)
        svg_text = outputs[-1].read_text(encoding="utf-8")
        normalized = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
        outputs[-1].write_text(normalized, encoding="utf-8", newline="\n")
    return outputs
