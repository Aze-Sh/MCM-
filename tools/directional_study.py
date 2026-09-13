"""Compare source types with positions, radii and observation noise held fixed."""

import argparse
from dataclasses import replace
import importlib.util
import json
import math
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def worlds(benchmark, seed):
    rng = random.Random(seed)
    sources = []
    for channel in rng.sample(range(1, 21), 16):
        radius = 1800 * math.sqrt(rng.random())
        angle = rng.uniform(0, 2 * math.pi)
        sources.append(benchmark.Source(
            channel, (radius * math.cos(angle), radius * math.sin(angle)),
            rng.uniform(1000, 1500), rng.uniform(0, 360),
        ))
    for n in (14, 16):
        for directional in (0, n // 2, n):
            yield dict(
                name=f"q4-type-seed{seed}-n{n}-d{directional}",
                problem=4, seed=seed, extreme=False,
                sources=[replace(s, direction=s.direction if i < directional else None)
                         for i, s in enumerate(sources[:n])],
            )


def costs(events, sources):
    actual = {s.channel: s for s in sources}
    found = set()
    position = (0.0, 0.0)
    tuned = 1
    groups = {}
    no_signal = dict(unknown=0, known_omni=0, known_directional=0)
    unknown_stops = set()
    absent_measurements = 0
    for event in events:
        if event.get("event") != "offline_response" or not event["reply"].get("accepted"):
            continue
        path, request, reply = event["path"], event["request"], event["reply"]
        if path not in ("/measure", "/clear"):
            continue
        q = (request["position"]["x"], request["position"]["y"])
        channel = request["channel"]
        group = "clear" if path == "/clear" else "known_measure" if channel in found else "search"
        entry = groups.setdefault(group, dict(moving_s=0.0, operation_s=0.0, actions=0))
        entry["moving_s"] += math.dist(position, q) / 5
        entry["actions"] += 1
        if path == "/measure":
            entry["operation_s"] += 5 + (channel != tuned)
            tuned = channel
            if group == "search":
                unknown_stops.add(q)
            if channel not in actual:
                absent_measurements += 1
            if reply["measure_result"] == "no_signal":
                kind = "unknown" if channel not in found else (
                    "known_omni" if actual[channel].direction is None else "known_directional"
                )
                no_signal[kind] += 1
            else:
                found.add(channel)
        else:
            entry["operation_s"] += 5 if reply["clear_result"] == "success" else 3
        position = q
    return dict(groups=groups, no_signal=no_signal,
                unknown_search_stops=len(unknown_stops),
                absent_channel_measurements=absent_measurements)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026091301)
    parser.add_argument("--existing", action="store_true", help="Use six existing Q4 development cases")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    benchmark = load_module("directional_benchmark", Path(__file__).with_name("benchmark.py"))
    cases = [c for c in benchmark.cases("matched") + benchmark.cases("validation") if c["problem"] == 4]
    if not args.existing:
        cases = list(worlds(benchmark, args.seed))
    records = []
    for case in cases:
        result, events = benchmark.run_case(case, output=args.output, wall_limit=180)
        breakdown = costs(events, case["sources"])
        expected = sum(g["moving_s"] + g["operation_s"] for g in breakdown["groups"].values())
        if result["error"] is None and abs(expected - result["virtual_time_s"]) > 5e-5:
            raise AssertionError("Cost breakdown disagrees with the simulator")
        record = dict(name=result["name"], virtual_time_s=result["virtual_time_s"],
                      source_count=result["source_count"], cleared_count=result["cleared_count"],
                      directional_count=sum(s.direction is not None for s in case["sources"]),
                      error=result["error"], replay=result.get("replay"), costs=breakdown)
        records.append(record)
        print(json.dumps(record), flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "study.json").write_text(json.dumps(records, indent=2) + "\n")
    return int(any(r["error"] for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
