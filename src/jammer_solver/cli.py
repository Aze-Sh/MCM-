"""Run the final v8 fast policy against a simulator started by the operator."""

import argparse
from datetime import datetime
import json
import math
from pathlib import Path

from .protocol import HttpTransport
from . import solver


def main():
    parser = argparse.ArgumentParser(description="2026 B题最终策略：v8 快速版")
    parser.add_argument("--problem", type=int, choices=(3, 4), required=True)
    parser.add_argument("--case-code", required=True, help="模拟器界面显示的案例编码")
    parser.add_argument("--robot-id", default="202612001024")
    parser.add_argument("--base-url", default="http://127.0.0.1:2026")
    parser.add_argument("--run-kind", choices=("rehearsal", "formal"), default="rehearsal")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    parser.add_argument("--connect", action="store_true", help="连接已就绪的接口；程序不能识别界面测试模式")
    parser.add_argument("--v8", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--planning-seconds", "--v8-planning-seconds", type=float, default=0.2)
    parser.add_argument("--extra-actions", "--v8-extra-actions", type=int, default=640)
    args = parser.parse_args()
    if args.extra_actions < 0 or not math.isfinite(args.planning_seconds) or args.planning_seconds < 0:
        parser.error("budgets must be finite and nonnegative")
    if not args.case_code.strip():
        parser.error("case-code cannot be empty")
    if not args.connect:
        parser.exit(0, "未连接。确认模拟器处于对应演练模式且接口就绪后，加 --connect 运行。\n")

    output = args.output / f"{args.run_kind}_q{args.problem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    output.mkdir(parents=True)
    metadata = dict(
        problem=args.problem, case_code=args.case_code, run_kind=args.run_kind,
        strategy=solver.STRATEGY, policy_revision=solver.REVISION,
        robot_id=args.robot_id, base_url=args.base_url,
        note="题号、测试类型和案例编码由操作者提供；接口不返回这些信息。",
    )
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def progress(event):
        if event["event"] == "cleared":
            print(f"已清除频道 {event['channel']}，累计 {event['cleared_count']} 个，虚拟时间 {event['virtual_time_s']:.3f} 秒", flush=True)
        elif event["event"] == "search_point_done":
            print(f"搜索点已完成 {event['visited']}，剩余 {event['remaining']}", flush=True)

    transport = HttpTransport(args.robot_id, output / "actions.jsonl", args.base_url)
    state = solver.xin_zhuangtai(transport, args.problem, progress,
                                planning_seconds=args.planning_seconds, extra_actions=args.extra_actions)
    error = None
    try:
        solver.yunxing(state)
    except (Exception, KeyboardInterrupt) as exc:
        error = f"{type(exc).__name__}: {exc}"
        state["reason"] = error
        try:
            solver.tuichu(state)
        except Exception as exit_exc:
            error += f"; exit: {type(exit_exc).__name__}: {exit_exc}"
    finally:
        result = solver.huizong(state)
        result.update(metadata)
        result.update(error=error, unresolved_request=transport.pending)
        (output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        transport.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"本地记录：{output}")
    return 0 if error is None and state["certificate"] and state["exit_confirmed"] else 2
