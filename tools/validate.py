"""Run or replay frozen v8 fast cases and check that layout changes preserve requests."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from benchmark import ROOT, case_from_record, run_case
from jammer_solver import solver
from verification import replay
from verify_optical import audit_optical_chains


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(record, result, events, log, policy_hashes):
    if result["error"] or result["cleared_count"] != record["source_count"]:
        raise ValueError(f"Incomplete case: {record['name']}")
    if result["source_truth"] != record["source_truth"]:
        raise ValueError(f"Source inputs differ: {record['name']}")
    if result["policy_source_sha256"] != policy_hashes or digest(log) != result["log_sha256"]:
        raise ValueError(f"Policy or log hash differs: {record['name']}")
    requests = [(e["path"], e["request"]) for e in events if e.get("event") == "offline_response"]
    request_hash = hashlib.sha256(json.dumps(requests, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if request_hash != record["request_sha256"]:
        raise ValueError(f"Requests changed from the selected v8 fast version: {record['name']}")
    if abs(result["virtual_time_s"] - record["virtual_time_s"]) > 1e-6 or result["counts"] != record["counts"]:
        raise ValueError(f"Costs changed from the selected v8 fast version: {record['name']}")
    replayed = replay(events)
    optical = audit_optical_chains(events)
    return dict(name=record["name"], suite=record["suite"], source_count=result["source_count"],
                cleared_count=result["cleared_count"], virtual_time_s=result["virtual_time_s"],
                identical_requests=True, request_sha256=request_hash, log_sha256=result["log_sha256"],
                replay=replayed, optical_audit=optical)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", default="all", choices=("all", "matched", "validation", "fresh", "stress", "fallback"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--wall-limit", type=int, default=180)
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT / "validation" / "current" if args.verify_only else ROOT / "runs" / f"validation-{datetime.now():%Y%m%d-%H%M%S-%f}"
    args.output.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((ROOT / "validation/expected-fast.json").read_text(encoding="utf-8"))
    records = [r for r in frozen["cases"] if args.suite == "all" or r["suite"] == args.suite]
    if not records:
        raise ValueError("No frozen cases selected")
    policy_hashes = {p.name: digest(p) for p in sorted(Path(solver.__file__).parent.glob("*.py"))}
    checked = []
    for record in records:
        path = args.output / f"v8-{record['name']}.json"
        if args.verify_only:
            result = json.loads(path.read_text(encoding="utf-8"))
            events = [json.loads(line) for line in path.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines()]
        else:
            result, events = run_case(case_from_record(record), planning_seconds=record["planning_seconds"],
                                     extra_actions=record["extra_actions"], fallback_only=record["fallback_only"],
                                     wall_limit=args.wall_limit, output=args.output)
            # JSON represents positions as arrays on both sides of the comparison.
            result = json.loads(path.read_text(encoding="utf-8"))
        checked.append(verify(record, result, events, path.with_suffix(".jsonl"), policy_hashes))
        print(json.dumps({k: checked[-1][k] for k in ("name", "cleared_count", "virtual_time_s", "identical_requests")}), flush=True)
    report = dict(scope="Offline synthetic only; no official simulator connected",
                  policy_revision=solver.REVISION, policy_source_sha256=policy_hashes,
                  expected_cases_sha256=digest(ROOT / "validation/expected-fast.json"),
                  cases=checked, verified_cases=len(checked),
                  optical_chains=sum(len(r["optical_audit"]["chains"]) for r in checked),
                  identical_requests_to_selected_fast=all(r["identical_requests"] for r in checked))
    (args.output / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(checked)} cases, {report['optical_chains']} optical chains.")


if __name__ == "__main__":
    main()
