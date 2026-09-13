import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from jammer_solver.protocol import xin_jiekou
from jammer_solver import solver


def main():
    parser = argparse.ArgumentParser(description="2026 B题：v8 快速版")
    parser.add_argument("--problem", type=int, choices=(3, 4), required=True)
    parser.add_argument("--case-code", required=True, help="模拟器界面显示的案例编码")
    parser.add_argument("--robot-id", default="202612001024")
    parser.add_argument("--base-url", default="http://127.0.0.1:2026")
    parser.add_argument(
        "--run-kind", choices=("rehearsal", "formal"), default="rehearsal"
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent / "runs"
    )
    parser.add_argument("--connect", action="store_true", help="连接已就绪的接口")
    parser.add_argument("--v8", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--planning-seconds", "--v8-planning-seconds", type=float, default=0.2
    )
    parser.add_argument("--extra-actions", "--v8-extra-actions", type=int, default=640)
    canshu = parser.parse_args()
    if not canshu.connect:
        print("未连接。确认模拟器处于对应演练模式且接口就绪后，加 --connect 运行。")
        return 0

    mulu = (
        canshu.output
        / f"{canshu.run_kind}_q{canshu.problem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    )
    mulu.mkdir(parents=True)
    xinxi = dict(
        problem=canshu.problem,
        case_code=canshu.case_code,
        run_kind=canshu.run_kind,
        strategy=solver.STRATEGY,
        policy_revision=solver.REVISION,
        robot_id=canshu.robot_id,
        base_url=canshu.base_url,
        note="题号、测试类型和案例编码由操作者提供；接口不返回这些信息。",
    )
    (mulu / "metadata.json").write_text(
        json.dumps(xinxi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def jindu(shijian):
        if shijian["event"] == "cleared":
            print(
                f"已清除频道 {shijian['channel']}，累计 {shijian['cleared_count']} 个，虚拟时间 {shijian['virtual_time_s']:.3f} 秒",
                flush=True,
            )
        elif shijian["event"] == "search_point_done":
            print(
                f"搜索点已完成 {shijian['visited']}，剩余 {shijian['remaining']}",
                flush=True,
            )

    with (mulu / "actions.jsonl").open("x", encoding="utf-8") as rizhi:
        jiekou = xin_jiekou(canshu.robot_id, rizhi, canshu.base_url)
        zhuangtai = solver.xin_zhuangtai(
            jiekou,
            canshu.problem,
            jindu,
            planning_seconds=canshu.planning_seconds,
            extra_actions=canshu.extra_actions,
        )
        jieguo = solver.yunxing(zhuangtai)
        jieguo.update(xinxi)
        jieguo.update(error=None, unresolved_request=jiekou["pending"])
        (mulu / "summary.json").write_text(
            json.dumps(jieguo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(jieguo, ensure_ascii=False, indent=2))
    print(f"本地记录：{mulu}")
    return 0 if zhuangtai["certificate"] and zhuangtai["exit_confirmed"] else 2


if __name__ == "__main__":
    sys.exit(main())
