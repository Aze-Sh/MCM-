from pathlib import Path

from matplotlib.figure import Figure

from cumcm_py.plotting import save_figure


def test_save_figure_exports_requested_file(tmp_path: Path) -> None:
    fig = Figure()
    ax = fig.subplots()
    ax.plot([0, 1], [0, 1])
    result = save_figure(fig, tmp_path / "line.png", metadata={"purpose": "test"})
    assert Path(result.values["path"]).exists()
    assert result.values["dpi"] >= 300
