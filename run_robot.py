import argparse
from datetime import datetime
import json
from pathlib import Path as lj
import sys

sys.path.insert(0, str(lj(__file__).resolve().parent / "src"))
from jammer_solver.protocol import xjjk
from jammer_solver import solver


def main():
    parser = argparse.ArgumentParser(description="2026 B题：v8 快速版")
    parser.add_argument("--problem", type=int, choices=(3, 4), required=True)
    parser.add_argument(
        "--case-code", required=True, help="模拟器界面显示的案例编码", dest="al"
    )
    parser.add_argument(
        "--robot-id", help="运行时输入当前登录的队号，不写入提交源码", dest="dh"
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:2026", dest="url")
    parser.add_argument(
        "--run-kind", choices=("rehearsal", "formal"), default="rehearsal", dest="lx"
    )
    parser.add_argument(
        "--output", type=lj, default=lj(__file__).resolve().parent / "runs"
    )
    parser.add_argument("--connect", action="store_true", help="连接已就绪的接口")
    parser.add_argument("--v8", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--planning-seconds",
        "--v8-planning-seconds",
        type=float,
        default=0.2,
        dest="ghsj",
    )
    parser.add_argument(
        "--extra-actions", "--v8-extra-actions", type=int, default=640, dest="dzys"
    )
    cs = parser.parse_args()
    if not cs.connect:
        print("未连接。确认模拟器处于对应演练模式且接口就绪后，加 --connect 运行。")
        return 0
    if not cs.dh or not cs.dh.strip():
        parser.error("连接模拟器时必须通过 --robot-id 输入当前登录的队号")
    mulu = cs.output / f"{cs.lx}_q{cs.problem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    mulu.mkdir(parents=True)
    xx = dict(
        problem=cs.problem,
        case_code=cs.al,
        run_kind=cs.lx,
        strategy=solver.celue,
        policy_revision=solver.banben,
        robot_id=cs.dh,
        base_url=cs.url,
        note="题号、测试类型和案例编码由操作者提供；接口不返回这些信息。",
    )
    (mulu / "metadata.json").write_text(
        json.dumps(xx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def jd(sj):
        if sj["event"] == "cleared":
            print(
                f"已清除频道 {sj['channel']}，累计 {sj['cleared_count']} 个，虚拟时间 {sj['virtual_time_s']:.3f} 秒",
                flush=True,
            )
        elif sj["event"] == "search_point_done":
            print(f"搜索点已完成 {sj['visited']}，剩余 {sj['remaining']}", flush=True)

    with (mulu / "actions.jsonl").open("x", encoding="utf-8") as rizhi:
        jk = xjjk(cs.dh, rizhi, cs.url)
        zt = solver.xjzt(jk, cs.problem, jd, ghsj=cs.ghsj, dzys=cs.dzys)
        jieguo = solver.yunxing(zt)
        jieguo.update(xx)
        jieguo.update(error=None, unresolved_request=jk["pending"])
        (mulu / "summary.json").write_text(
            json.dumps(jieguo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(jieguo, ensure_ascii=False, indent=2))
    print(f"本地记录：{mulu}")
    return 0 if zt["certificate"] and zt["exit_confirmed"] else 2


if __name__ == "__main__":
    sys.exit(main())
