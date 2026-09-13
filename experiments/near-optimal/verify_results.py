import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "solutions/adaptive/python"))
from near_optimal.jiaozhun import replay
from verify_optical import audit_optical_chains


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(old, new):
    fields = ("problem", "seed", "source_truth", "noise")
    if any(old[k] != new[k] for k in fields):
        raise ValueError("Comparison inputs differ")
    if old["error"] or new["error"]:
        raise ValueError("An algorithm did not finish successfully")
    saved = old["virtual_time_s"] - new["virtual_time_s"]
    return dict(name=new["name"], problem=new["problem"], sources=new["source_count"],
                v7_s=old["virtual_time_s"], v8_s=new["virtual_time_s"], saved_s=saved,
                meets_500_s=saved >= 500, same_inputs=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--require-current-policy", action="store_true")
    args = parser.parse_args()
    results = args.results.resolve()
    policy_hashes = {p.name: digest(p) for p in sorted((ROOT / "solutions/adaptive/python/near_optimal").glob("*.py"))}
    suites = [("matched", 4), ("validation", 8), ("stress", 8), ("fallback", 2)]
    performance_suites = ["matched", "validation"]
    if (results / "current-fresh").exists():
        suites.append(("fresh", 8))
        performance_suites.append("fresh")
    verified = []
    for suite, expected in suites:
        paths = sorted((results / f"current-{suite}").glob("v8-q*.json"))
        if len(paths) != expected:
            raise ValueError(f"Expected {expected} {suite} cases, found {len(paths)}")
        for path in paths:
            result = read(path)
            matches_policy = result.get("policy_source_sha256") == policy_hashes
            if args.require_current_policy and not matches_policy:
                raise ValueError(f"Result was not recorded with current policy files: {path}")
            log = path.with_suffix(".jsonl")
            if result["error"] or result["cleared_count"] != result["source_count"]:
                raise ValueError(f"Incomplete case: {path}")
            if digest(log) != result["log_sha256"]:
                raise ValueError(f"Changed log: {log}")
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            audit = replay(events)
            optical_audit = audit_optical_chains(events)
            verified.append(dict(suite=suite, name=result["name"], log=str(log.relative_to(ROOT)),
                                 policy_revision=result.get("policy_revision"),
                                 matches_current_policy_files=matches_policy,
                                 optical_audit=optical_audit,
                                 log_sha256=digest(log), **audit))
    comparisons = {}
    for suite in performance_suites:
        comparisons[suite] = []
        for path in sorted((results / f"current-{suite}").glob("v8-q*.json")):
            baseline = results / ("v7" if suite == "matched" else f"current-{suite}") / path.name.replace("v8-", "v7-", 1)
            old = read(baseline)
            if digest(baseline.with_suffix(".jsonl")) != old["log_sha256"]:
                raise ValueError(f"Changed baseline log: {baseline}")
            comparisons[suite].append(compare(old, read(path)))
    historical = []
    for path in sorted((ROOT / "experiments/near-optimal/results/validation-20260912").glob("v8-*.jsonl")):
        audit = replay(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
        historical.append(dict(log=str(path.relative_to(ROOT)), log_sha256=digest(path), **audit))
    if len(historical) != 14:
        raise ValueError("The expected 14 historical logs were not verified")
    source = list((ROOT / "solutions/adaptive/python/near_optimal").glob("*.py"))
    source += [ROOT / "solutions/adaptive/python/run_robot.py", Path(__file__).with_name("benchmark.py")]
    source += [Path(__file__), Path(__file__).with_name("verify_optical.py")]
    report = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope="Offline synthetic verification; no official simulator used",
                  source_sha256={str(p.relative_to(ROOT)): digest(p) for p in sorted(source)},
                  comparisons=comparisons, current_replay=verified, historical_replay=historical,
                  matched_target_met=all(r["meets_500_s"] for r in comparisons["matched"]),
                  validation_target_met=all(r["meets_500_s"] for r in comparisons["validation"]),
                  fresh_target_met=all(r["meets_500_s"] for r in comparisons["fresh"]) if "fresh" in comparisons else None,
                  all_results_match_current_policy_files=all(r["matches_current_policy_files"] for r in verified),
                  screenshot_cases_verified=False,
                  outstanding="Original screenshot case codes/logs unavailable; 500 s target not fully achieved")
    package = [ast.parse(p.read_text()) for p in source if p.parent.name == "near_optimal"]
    report["package_style"] = dict(files=len(package),
                                  classes=sum(isinstance(n, ast.ClassDef) for t in package for n in ast.walk(t)),
                                  functions=sum(isinstance(n, ast.FunctionDef) for t in package for n in ast.walk(t)))
    (results / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(current_verified=len(verified), historical_verified=len(historical),
                          comparisons=comparisons, matched_target_met=report["matched_target_met"],
                          validation_target_met=report["validation_target_met"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
