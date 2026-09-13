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
from near_optimal import suanfa as v8


def main():
    mingling = argparse.ArgumentParser(
        description="2026 B题机器狗：仅在你开启对应测试并确认接口就绪后连接"
    )
    mingling.add_argument("--problem", type=int, choices=(3, 4), required=True)
    mingling.add_argument("--case-code", required=True, help="界面显示的案例编码")
    mingling.add_argument("--robot-id", default="202612001024")
    mingling.add_argument("--base-url", default="http://127.0.0.1:2026")
    mingling.add_argument("--run-kind", choices=("rehearsal", "formal"), default="rehearsal")
    mingling.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "results" / "runs"
    )
    mingling.add_argument(
        "--connect", action="store_true", help="连接你已开启的测试；程序无法辨认界面模块"
    )
    banben_xuanxiang = mingling.add_mutually_exclusive_group()
    banben_xuanxiang.add_argument("--baseline", action="store_true", help="使用原乘法基线")
    banben_xuanxiang.add_argument("--v3", action="store_true", help="复现已演练的第三版策略")
    banben_xuanxiang.add_argument("--v4", action="store_true", help="使用保留的第四版策略")
    banben_xuanxiang.add_argument("--v5", action="store_true", help="使用保留的第五版策略")
    banben_xuanxiang.add_argument("--v6", action="store_true", help="使用已演练的第六版策略")
    banben_xuanxiang.add_argument("--v8", action="store_true", help="使用新增的证据账本与事件前瞻实验版")
    mingling.add_argument("--v8-planning-seconds", type=float, default=0.2, help="v8 每次局部前瞻预算")
    mingling.add_argument("--v8-extra-actions", type=int, default=640, help="v8 不可重置的试探动作额度")
    canshu = mingling.parse_args()
    if (
        canshu.v8_extra_actions < 0
        or not math.isfinite(canshu.v8_planning_seconds)
        or canshu.v8_planning_seconds < 0
    ):
        mingling.error("v8 budgets must be finite and nonnegative")
    if not canshu.connect:
        mingling.exit(0, "未连接。确认模拟器题号、测试类型和接口就绪后，由你添加 --connect 运行。\n")
    if not canshu.case_code.strip():
        mingling.error("case-code cannot be empty")
    peizhi = {
        "baseline": (Solver, "midpoint-v1"),
        "v3": (Solver, "annular-history-route-v3"),
        "v4": (CooperativeSolver, V4_STRATEGY),
        "v5": (AdaptiveSolver, V5_STRATEGY),
        "v6": (SolverV6, V6_STRATEGY),
        "v7": (SolverV7, STRATEGY),
        "v8": (None, v8.STRATEGY),
    }
    banben = "v7"
    for mingcheng in ("baseline", "v3", "v4", "v5", "v6", "v8"):
        if getattr(canshu, mingcheng):
            banben = mingcheng
    qiujie_leixing, celue = peizhi[banben]
    baocun = canshu.output / f"{canshu.run_kind}_q{canshu.problem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    baocun.mkdir(parents=True)
    xinxi = dict(
        problem=canshu.problem,
        case_code=canshu.case_code,
        run_kind=canshu.run_kind,
        strategy=celue,
        robot_id=canshu.robot_id,
        base_url=canshu.base_url,
        note="题号、类型、案例编码由操作者提供；HTTP接口不返回这些信息。",
    )
    (baocun / "metadata.json").write_text(
        json.dumps(xinxi, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    def progress(event):
        if event["event"] == "cleared":
            print(
                f"已清除频道 {event['channel']}，累计 {event['cleared_count']} 个，虚拟时间 {event['virtual_time_s']:.3f} 秒",
                flush=True,
            )
        elif event["event"] == "search_point_done":
            print(f"搜索点已完成 {event['visited']}，剩余 {event['remaining']}", flush=True)

    jiekou = HttpTransport(canshu.robot_id, baocun / "actions.jsonl", canshu.base_url)
    if canshu.v8:
        zhuangtai = v8.xin_zhuangtai(
            jiekou,
            canshu.problem,
            progress,
            planning_seconds=canshu.v8_planning_seconds,
            extra_actions=canshu.v8_extra_actions,
        )
    elif banben in ("baseline", "v3"):
        qiujie = qiujie_leixing(jiekou, canshu.problem, progress, use_history=not canshu.baseline)
    else:
        qiujie = qiujie_leixing(jiekou, canshu.problem, progress)
    cuowu = None
    try:
        if canshu.v8:
            v8.yunxing(zhuangtai)
        else:
            qiujie.run()
    except (Exception, KeyboardInterrupt) as exc:
        cuowu = f"{type(exc).__name__}: {exc}"
        if canshu.v8:
            zhuangtai["reason"] = cuowu
        else:
            qiujie.reason = cuowu
        try:
            if canshu.v8:
                v8.tuichu(zhuangtai)
            else:
                qiujie.exit()
        except Exception as exit_exc:
            cuowu += f"; exit: {type(exit_exc).__name__}: {exit_exc}"
    finally:
        jieguo = v8.huizong(zhuangtai) if canshu.v8 else qiujie.summary()
        jieguo.update(xinxi)
        jieguo["error"] = cuowu
        jieguo["unresolved_request"] = jiekou.pending
        (baocun / "summary.json").write_text(
            json.dumps(jieguo, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        jiekou.close()
    print(json.dumps(jieguo, ensure_ascii=False, indent=2))
    print(f"本地记录：{baocun}\n官方日志仍需你从模拟器导出，保留原文件名。")
    quanbu_wancheng = zhuangtai["certificate"] if canshu.v8 else qiujie.certificate
    yijing_tuichu = zhuangtai["exit_confirmed"] if canshu.v8 else qiujie.exit_confirmed
    return 0 if cuowu is None and quanbu_wancheng and yijing_tuichu else 2


if __name__ == "__main__":
    raise SystemExit(main())
