"""One-command verification for the CUMCM repository."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml

from cumcm_py.types import CheckReport, ValidationIssue


def _decode(output: bytes) -> str:
    for encoding in ("utf-8", "gb18030"):
        try:
            return output.decode(encoding)
        except UnicodeDecodeError:
            continue
    return output.decode("utf-8", errors="replace")


def _run_command(
    group: str,
    command: Sequence[str],
    cwd: Path,
    log_dir: Path,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    log_dir.mkdir(parents=True, exist_ok=True)
    command_list = list(command)
    if "pytest" in command_list:
        # Use a fresh run-specific directory. Older sandbox runs may leave
        # fixed basetemp directories with handles/ACLs that pytest cannot
        # remove, which turns otherwise passing tests into cleanup errors.
        temp_root = log_dir.parents[1] / "tmp/verify" / f"pytest-{group}-{os.getpid()}"
        temp_root.parent.mkdir(parents=True, exist_ok=True)
        command_list.extend(["--basetemp", str(temp_root), "-p", "no:cacheprovider"])
    merged_env = os.environ.copy()
    merged_env["PYTHONUTF8"] = "1"
    if env:
        merged_env.update(env)
    completed = subprocess.run(
        command_list,
        cwd=cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = _decode(completed.stdout)
    log_path = log_dir / f"{group}.log"
    log_path.write_text(output, encoding="utf-8")
    return {
        "group": group,
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "command": command_list,
        "output_path": str(log_path),
        "stdout": output,
    }


def _coverage_result(root: Path, log_dir: Path) -> tuple[dict[str, object], list[ValidationIssue]]:
    path = root / "validation/coverage-matrix.yaml"
    issues: list[ValidationIssue] = []
    if not path.exists():
        issues.append(ValidationIssue("coverage.missing", "error", "缺少覆盖矩阵。", str(path)))
        return {"group": "coverage", "status": "failed", "returncode": 1, "command": [], "output_path": str(path)}, issues
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    requirements = data.get("requirements", [])
    for item in requirements:
        requirement_id = item.get("id", "unknown")
        if item.get("status") not in {"verified", "implemented-runtime-blocked"}:
            issues.append(ValidationIssue("coverage.requirement_missing", "error", f"需求 {requirement_id} 未验证。", str(path)))
        for relative in item.get("files", []):
            if not (root / relative).exists():
                issues.append(ValidationIssue("coverage.file_missing", "error", f"需求 {requirement_id} 的证据文件不存在。", relative))
    status = "passed" if not issues else "failed"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "coverage.log"
    log_path.write_text(f"requirements={len(requirements)}\nissues={len(issues)}\n", encoding="utf-8")
    return {
        "group": "coverage",
        "status": status,
        "returncode": 0 if status == "passed" else 1,
        "command": ["validate", "validation/coverage-matrix.yaml"],
        "output_path": str(log_path),
    }, issues


def verify_repository(root: Path, include_matlab: bool, include_latex: bool) -> CheckReport:
    root = root.resolve()
    log_dir = root / "validation/logs"
    python = sys.executable
    python_tests = sorted(
        str(path.relative_to(root))
        for path in (root / "tests/python").glob("test_*.py")
        if path.name != "test_verify_repository.py"
    )
    commands = [
        ("sources", [python, "-m", "pytest", "tests/content/test_catalog_notes.py", "tests/content/test_repository_audit.py", "tests/content/test_rules_provenance.py", "tests/content/test_schemas.py", "-q"], root),
        ("cases", [python, "-m", "pytest", "tests/content/test_problem_cards.py", "tests/content/test_knowledge_provenance.py", "-q"], root),
        ("methods", [python, "-m", "pytest", "tests/content/test_method_cards.py", "tests/content/test_paper_template.py", "tests/content/test_workflows.py", "-q"], root),
        ("python", [python, "-m", "pytest", *python_tests, "-q"], root),
        ("checkers", [python, "-m", "pytest", "tests/checkers", "-q"], root),
        ("skill", [python, "-m", "pytest", "tests/skill", "-q"], root),
        ("git-policy", ["git", "ls-files", "private-sources", "tmp"], root),
    ]
    validator = Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py"
    if validator.exists():
        commands.append(("skill-validator", [python, str(validator), "skill/cumcm-assistant"], root))

    results: list[dict[str, object]] = []
    issues: list[ValidationIssue] = []
    for group, command, cwd in commands:
        result = _run_command(group, command, cwd, log_dir)
        stdout = str(result.pop("stdout", ""))
        if group == "git-policy" and stdout.strip():
            result["status"] = "failed"
            result["returncode"] = 1
        results.append(result)
        if result["status"] == "failed":
            issues.append(
                ValidationIssue(
                    "verify.group_failed",
                    "error",
                    f"验证组 {group} 失败（exit {result['returncode']}）。",
                    str(result["output_path"]),
                )
            )

    if include_matlab:
        result = _run_command(
            "matlab",
            [
                "matlab",
                "-batch",
                "addpath('code/matlab'); "
                "results=runtests('tests/matlab'); disp(results); "
                "assertSuccess(results); "
                "run('tools/export_matlab_results.m')",
            ],
            root,
            log_dir,
        )
        result.pop("stdout", None)
        results.append(result)
        if result["status"] == "failed":
            issues.append(ValidationIssue("verify.group_failed", "error", f"验证组 matlab 失败（exit {result['returncode']}）。", str(result["output_path"])))
            results.append(
                {
                    "group": "cross-language",
                    "status": "skipped",
                    "returncode": None,
                    "command": [],
                    "output_path": str(result["output_path"]),
                }
            )
        else:
            cross_result = _run_command(
                "cross-language",
                [
                    python,
                    "tools/compare_outputs.py",
                    "--expected-dir",
                    "code/fixtures/expected",
                    "--matlab-dir",
                    "validation/output/matlab",
                    "--manifest",
                    "code/fixtures/manifest.yaml",
                    "--json",
                    "validation/cross-language-test-report.json",
                ],
                root,
                log_dir,
            )
            cross_result.pop("stdout", None)
            results.append(cross_result)
            if cross_result["status"] == "failed":
                issues.append(
                    ValidationIssue(
                        "verify.group_failed",
                        "error",
                        f"验证组 cross-language 失败（exit {cross_result['returncode']}）。",
                        str(cross_result["output_path"]),
                    )
                )
    else:
        results.append({"group": "matlab", "status": "skipped", "returncode": None, "command": [], "output_path": "environment/compatibility.md"})
        results.append({"group": "cross-language", "status": "skipped", "returncode": None, "command": [], "output_path": "validation/cross-language.md"})

    if include_latex:
        latex_code = "import subprocess,sys; c=['xelatex','-interaction=nonstopmode','-halt-on-error','main.tex']; a=subprocess.run(c).returncode; b=subprocess.run(c).returncode if a==0 else a; sys.exit(b)"
        result = _run_command("latex", [python, "-c", latex_code], root / "templates/paper", log_dir)
        result.pop("stdout", None)
        results.append(result)
        if result["status"] == "failed":
            issues.append(ValidationIssue("verify.group_failed", "error", f"验证组 latex 失败（exit {result['returncode']}）。", str(result["output_path"])))
    else:
        results.append({"group": "latex", "status": "skipped", "returncode": None, "command": [], "output_path": "validation/paper-template.md"})

    coverage, coverage_issues = _coverage_result(root, log_dir)
    results.append(coverage)
    issues.extend(coverage_issues)
    results.sort(key=lambda item: str(item["group"]))
    return CheckReport(
        "repository",
        not any(issue.severity == "error" for issue in issues),
        tuple(issues),
        {"groups": [str(item["group"]) for item in results], "results": results},
    )


def _auto_matlab(root: Path) -> bool:
    compatibility = (root / "environment/compatibility.md").read_text(encoding="utf-8", errors="replace")
    return shutil.which("matlab") is not None and "runtime-blocked" not in compatibility


def _report_dict(report: CheckReport) -> dict[str, object]:
    return {
        "checker": report.checker,
        "passed": report.passed,
        "issues": [
            {
                "code": item.code,
                "severity": item.severity,
                "message": item.message,
                "path": item.path,
                "source_ids": list(item.source_ids),
            }
            for item in report.issues
        ],
        "metadata": dict(report.metadata),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matlab", choices=("auto", "yes", "no"), default="auto")
    parser.add_argument("--latex", choices=("auto", "yes", "no"), default="auto")
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    include_matlab = _auto_matlab(root) if args.matlab == "auto" else args.matlab == "yes"
    include_latex = shutil.which("xelatex") is not None if args.latex == "auto" else args.latex == "yes"
    report = verify_repository(root, include_matlab=include_matlab, include_latex=include_latex)
    for result in report.metadata["results"]:
        print(f"{result['group']}: {str(result['status']).upper()} ({result['output_path']})")
    if args.json_path:
        path = args.json_path if args.json_path.is_absolute() else root / args.json_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_report_dict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
