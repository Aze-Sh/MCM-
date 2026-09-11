from pathlib import Path

from tools.init_project import initialize_project


def test_initializer_creates_both_language_entries(tmp_path: Path) -> None:
    destination = tmp_path / "contest"
    report = initialize_project(destination, ["python", "matlab"])
    assert report.passed
    assert (destination / "python" / "main.py").exists()
    assert (destination / "matlab" / "main.m").exists()
    assert (destination / "AI工具使用详情.md").exists()
    assert (destination / "data" / "raw" / ".gitkeep").exists()


def test_initializer_refuses_nonempty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "contest"
    destination.mkdir()
    (destination / "private.csv").write_text("secret", encoding="utf-8")
    report = initialize_project(destination, ["python"])
    assert not report.passed
    assert (destination / "private.csv").read_text(encoding="utf-8") == "secret"
    assert not (destination / "python" / "main.py").exists()


def test_force_never_overwrites_existing_user_file(tmp_path: Path) -> None:
    destination = tmp_path / "contest"
    (destination / "python").mkdir(parents=True)
    main = destination / "python" / "main.py"
    main.write_text("# user work", encoding="utf-8")
    report = initialize_project(destination, ["python"], force=True)
    assert report.passed
    assert main.read_text(encoding="utf-8") == "# user work"
    assert any(issue.code == "init.skipped_existing" for issue in report.issues)


def test_initializer_includes_complete_paper_and_disclosure_sources(tmp_path: Path) -> None:
    destination = tmp_path / "contest"
    assert initialize_project(destination, ["python", "matlab"]).passed
    assert (destination / "paper/main.tex").is_file()
    assert (destination / "paper/cumcm2026.sty").is_file()
    assert (destination / "paper/sections/model.tex").is_file()
    assert (destination / "AI工具使用详情.tex").is_file()
    assert (destination / "figure-styles/python_style.py").is_file()
    assert not (destination / "paper/main.pdf").exists()
