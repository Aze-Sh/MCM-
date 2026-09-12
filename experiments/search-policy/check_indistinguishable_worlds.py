"""Two indistinguishable-history examples, not a localization benchmark.

The trace is a hypothetical completed observation/clear history with ten known
sources. Its clear coordinates are prescribed fixtures, not a search policy.
Compare whether adding an eleventh hidden source changes any interface output.
Uses only the existing local simulator; never connects to a network service.
"""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "solutions/baseline/python"))
from b_simulation import Source, SyntheticSimulator


def execute(sources, trace):
    world = SyntheticSimulator(sources, error_seed=42)
    responses = []
    for i, (path, point, channel) in enumerate(trace):
        request = dict(request_id=f"fixture-{i}", robot_id="offline-example")
        if point is not None:
            request.update(position=dict(x=point[0], y=point[1]), channel=channel)
        status, response = world.transport(path, json.dumps(request).encode())
        assert status == 200 and response["accepted"]
        responses.append({k: v for k, v in response.items() if k != "real_timestamp_ms"})
    return world, responses


def example(problem):
    known = [Source(i + 1, (100 * math.cos(i * math.pi / 5),
                             100 * math.sin(i * math.pi / 5)),
                    1000, 180 if problem == 4 and i == 0 else None)
             for i in range(10)]
    hidden = Source(11, (1790, 0), 1000) if problem == 3 else Source(11, (200, 0), 1000, 0)
    trace = [("/enter", None, None)]
    trace.extend(("/measure", (0, 0), c) for c in range(1, 21))
    trace.extend(("/clear", source.position, source.channel) for source in known)
    trace.append(("/exit", None, None))
    first, observations = execute(known, trace)
    second, alternate = execute(known + [hidden], trace)
    assert observations == alternate
    assert len(first.cleared) == len(second.cleared) == 10
    assert len(first.sources) == 10 and len(second.sources) == 11
    return dict(
        problem=problem,
        identical_interface_history_except_wall_timestamp=True,
        actions=len(trace),
        world_a=dict(source_count=10, cleared_count=10, all_cleared=True),
        world_b=dict(source_count=11, cleared_count=10, all_cleared=False),
        added_source=dict(channel=11, position=hidden.position,
                          radius=hidden.radius, direction=hidden.direction),
        reason=("No tested point can receive the additional source at its radius."
                if problem == 3 else
                "The additional source is nearby but faces away from every tested point."),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = dict(kind="logical-counterexamples-not-performance-results",
                  scope="Fixed local traces; general reasoning is explained in the accompanying note.",
                  examples=[example(3), example(4)])
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
