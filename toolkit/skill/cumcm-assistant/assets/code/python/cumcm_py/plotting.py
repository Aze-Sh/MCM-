"""Reproducible figure export."""

from pathlib import Path
from typing import Any, Mapping

from matplotlib.figure import Figure

from .types import ModelResult


def save_figure(
    fig: Figure,
    path: Path | str,
    metadata: Mapping[str, Any] | None = None,
    *,
    dpi: int = 300,
) -> ModelResult:
    """Save a figure with a 300-DPI raster minimum and explicit metadata."""

    if not isinstance(fig, Figure):
        raise TypeError("fig must be a matplotlib Figure")
    if dpi < 300:
        raise ValueError("raster exports require at least 300 dpi")
    target = Path(path)
    if not target.suffix:
        raise ValueError("path must include an output extension")
    target.parent.mkdir(parents=True, exist_ok=True)
    save_options: dict[str, Any] = {"bbox_inches": "tight"}
    if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        save_options["dpi"] = dpi
    fig.savefig(target, **save_options)
    return ModelResult(
        method="scientific-plotting",
        values={"path": str(target.resolve()), "dpi": dpi, "metadata": dict(metadata or {})},
        diagnostics={"exists": target.exists(), "format": target.suffix.lower().lstrip(".")},
        assumptions=("Figure data and labels were prepared by the caller.",),
    )
