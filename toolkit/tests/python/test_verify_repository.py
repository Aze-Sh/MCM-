from pathlib import Path

from tools import verify_repository as verifier


ROOT = Path(__file__).parents[2]


def test_repository_verifier_runs_all_required_groups(monkeypatch) -> None:
    def fake_run(group, command, cwd, log_dir, env=None):
        return {
            "group": group,
            "status": "passed",
            "returncode": 0,
            "command": command,
            "output_path": str(log_dir / f"{group}.log"),
            "stdout": "",
        }

    monkeypatch.setattr(verifier, "_run_command", fake_run)
    report = verifier.verify_repository(ROOT, include_matlab=False, include_latex=False)
    groups = set(report.metadata["groups"])
    assert {"sources", "cases", "methods", "python", "checkers", "skill"} <= groups
    assert report.passed
    statuses = {item["group"]: item["status"] for item in report.metadata["results"]}
    assert statuses["matlab"] == "skipped"
    assert statuses["latex"] == "skipped"


def test_repository_verifier_preserves_failed_exit_code(monkeypatch) -> None:
    def fake_run(group, command, cwd, log_dir, env=None):
        return {
            "group": group,
            "status": "failed" if group == "methods" else "passed",
            "returncode": 7 if group == "methods" else 0,
            "command": command,
            "output_path": str(log_dir / f"{group}.log"),
            "stdout": "failure",
        }

    monkeypatch.setattr(verifier, "_run_command", fake_run)
    report = verifier.verify_repository(ROOT, include_matlab=False, include_latex=False)
    assert not report.passed
    issue = next(item for item in report.issues if item.code == "verify.group_failed")
    assert "exit 7" in issue.message


def test_repository_verifier_exports_and_compares_matlab_fixtures(monkeypatch) -> None:
    commands = {}

    def fake_run(group, command, cwd, log_dir, env=None):
        commands[group] = command
        return {
            "group": group,
            "status": "passed",
            "returncode": 0,
            "command": command,
            "output_path": str(log_dir / f"{group}.log"),
            "stdout": "",
        }

    monkeypatch.setattr(verifier, "_run_command", fake_run)

    report = verifier.verify_repository(ROOT, include_matlab=True, include_latex=False)

    statuses = {item["group"]: item["status"] for item in report.metadata["results"]}
    assert statuses["matlab"] == "passed"
    assert statuses["cross-language"] == "passed"
    assert "export_matlab_results.m" in " ".join(commands["matlab"])
    assert "disp(results)" in " ".join(commands["matlab"])
    assert "compare_outputs.py" in " ".join(commands["cross-language"])
