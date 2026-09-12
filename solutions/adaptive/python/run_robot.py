"""User-operated entry point; without --connect this program sends no requests."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
from protocol import HttpTransport
from solver import Solver
from cooperative import CooperativeSolver, STRATEGY as V4_STRATEGY
from adaptive import AdaptiveSolver, STRATEGY as V5_STRATEGY
from adaptive_v6 import SolverV6, STRATEGY as V6_STRATEGY
from adaptive_v7 import SolverV7, STRATEGY
from near_optimal.solver import SolverV8, STRATEGY as V8_STRATEGY


def main():
    parser = argparse.ArgumentParser(description="2026 B题机器狗：仅在你开启对应测试并确认接口就绪后连接")
    parser.add_argument("--problem", type=int, choices=(3, 4), required=True)
    parser.add_argument("--case-code", required=True, help="界面显示的案例编码")
    parser.add_argument("--robot-id", default="202612001024")
    parser.add_argument("--base-url", default="http://127.0.0.1:2026")
    parser.add_argument("--run-kind", choices=("rehearsal", "formal"), default="rehearsal")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results" / "runs")
    parser.add_argument("--connect", action="store_true", help="连接你已开启的测试；程序无法辨认界面模块")
    versions = parser.add_mutually_exclusive_group()
    versions.add_argument("--baseline", action="store_true", help="使用原乘法基线")
    versions.add_argument("--v3", action="store_true", help="复现已演练的第三版策略")
    versions.add_argument("--v4", action="store_true", help="使用保留的第四版策略")
    versions.add_argument("--v5", action="store_true", help="使用保留的第五版策略")
    versions.add_argument("--v6", action="store_true", help="使用已演练的第六版策略")
    versions.add_argument("--v8", action="store_true", help="使用新增的证据账本与事件前瞻实验版")
    parser.add_argument("--v8-planning-seconds", type=float, default=.20, help="v8 每次局部前瞻预算")
    parser.add_argument("--v8-extra-actions", type=int, default=640, help="v8 不可重置的试探动作额度")
    args = parser.parse_args()
    if (args.v8_extra_actions < 0 or not math.isfinite(args.v8_planning_seconds)
            or args.v8_planning_seconds < 0):
        parser.error("v8 budgets must be finite and nonnegative")
    if not args.connect:
        parser.exit(0, "未连接。确认模拟器题号、测试类型和接口就绪后，由你添加 --connect 运行。\n")
    if not args.case_code.strip():
        parser.error("case-code cannot be empty")
    output = args.output / f"{args.run_kind}_q{args.problem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    output.mkdir(parents=True)
    metadata = dict(problem=args.problem, case_code=args.case_code, run_kind=args.run_kind,
                    strategy=("midpoint-v1" if args.baseline else "annular-history-route-v3" if args.v3
                              else V4_STRATEGY if args.v4 else V5_STRATEGY if args.v5 else V6_STRATEGY if args.v6
                              else V8_STRATEGY if args.v8 else STRATEGY),
                    robot_id=args.robot_id, base_url=args.base_url,
                    note="题号、类型、案例编码由操作者提供；HTTP接口不返回这些信息。")
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def progress(event):
        if event["event"] == "cleared":
            print(f"已清除频道 {event['channel']}，累计 {event['cleared_count']} 个，虚拟时间 {event['virtual_time_s']:.3f} 秒", flush=True)
        elif event["event"] == "search_point_done":
            print(f"搜索点已完成 {event['visited']}，剩余 {event['remaining']}", flush=True)

    transport = HttpTransport(args.robot_id, output / "actions.jsonl", args.base_url)
    solver = (Solver(transport,args.problem,progress,use_history=not args.baseline)
              if args.baseline or args.v3 else
              CooperativeSolver(transport,args.problem,progress) if args.v4 else
              AdaptiveSolver(transport,args.problem,progress) if args.v5 else
              SolverV6(transport,args.problem,progress) if args.v6 else
              SolverV8(transport,args.problem,progress,planning_seconds=args.v8_planning_seconds,
                       extra_actions=args.v8_extra_actions) if args.v8 else
              SolverV7(transport,args.problem,progress))
    failure = None
    try:
        solver.run()
    except (Exception, KeyboardInterrupt) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        solver.reason = failure
        # Never send a new action if the last action may already have executed.
        try:
            solver.exit()
        except Exception as exit_exc:
            failure += f"; exit: {type(exit_exc).__name__}: {exit_exc}"
    finally:
        result = solver.summary()
        result.update(metadata)
        result["error"] = failure
        result["unresolved_request"] = transport.pending
        (output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        transport.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"本地记录：{output}\n官方日志仍需你从模拟器导出，保留原文件名。")
    return 0 if failure is None and solver.certificate and solver.exit_confirmed else 2


if __name__ == "__main__":
    raise SystemExit(main())
